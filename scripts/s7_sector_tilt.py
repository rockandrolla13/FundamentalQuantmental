"""Signal S7, the macro-conditional sector tilt, tested on the TRACE HY panel (methodology Section 8, S7).

Decision page: docs/decisions/2026-10-24-s7-sector-tilt.md. The rules below are frozen before the first run.

Question: does a sector that trades wider than its macro state implies earn more over the next h months? The earlier
studies (wt_tests.py, s_tests.py) asked whether macro predicts EBITDA. This one asks whether the market prices macro
late. Only the second question is alpha.

Unit: one GICS sector j in one month end t, h in {3, 6} months.

Steps:
1. Bonds: rows of results_h{h}_full (scripts/backtest_alpha.py). Credit excess return x = total - tsy_ret over
   t..t+h. Cost = cost_rt (round trip). Sector at t from gics_history, point in time (s_tests.sector_at).
2. Sector spread effect: eta_{j,t} = median log G-spread of sector j at t minus the mean of those medians over the
   sectors at t. A sector needs MIN_BONDS bonds at t.
3. Macro vector m_t, known at t + 1 day: Baa spread level and 3-month change, SLOOS, Philadelphia Fed general activity
   (the PMI proxy), oil, copper and CPI year-on-year, and the 10-year minus 3-month curve (release lags as in
   wt_tests.MONTHLY).
4. eta_hat_{j,t}: per sector, ridge regression of eta_{j,s} on standardised m_s over months s <= t only, refit each
   month, at least MIN_TRAIN months. Both sides of row s are known at s, so the fit uses no later data.
5. S7_{j,t} = eta_{j,t} - eta_hat_{j,t}. The downside-weight term of Section 8 is set to 0 (theta = 0) because the
   Section 5.2 model failed tests S1-S4.
6. Outcome: y_{j,t} = sector mean of x minus the mean over sectors at t (relative credit excess return).

Pass rule (all three, pre-set):
 P1. The Fama-MacBeth slope on -eta_hat, with eta in the same monthly regression, is above 0 with an EWC t above 2.
     This isolates the macro part. eta alone is a sector value signal that needs no macro.
 P2. The mean monthly rank IC of S7 exceeds that of eta alone.
 P3. The top-minus-bottom tercile spread of S7, after the round-trip cost on both legs, is positive in every testable
     cycle window (hy.backtest.CYCLE_WINDOWS). The 2008 window falls inside the training period, so 3 windows test.

Run:
    PYTHONPATH=. python3 scripts/s7_sector_tilt.py          # writes data/raw/backtest/s7_sector_tilt.json
"""

from __future__ import annotations

import json
import sys
from collections.abc import Sequence
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from hy.backtest import CYCLE_WINDOWS  # noqa: E402
from s_tests import data_root, ewc_test, load_macro_monthly, sector_at  # noqa: E402
from wt_tests import MONTHLY, load_fred_monthly  # noqa: E402

HORIZONS = (3, 6)
MIN_BONDS = 10       # bonds per sector-month for a sector spread
MIN_TRAIN = 36       # months of history before eta_hat is used
RIDGE = 1.0          # ridge penalty on standardised macro inputs
MACRO_COLS = ("baa", "baa_chg3", "sloos", "pmi", "oil_yoy", "copper_yoy", "cpi_yoy", "curve")


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------


def load_macro(macro_dir: Path) -> pd.DataFrame:
    """m_t per month end t, each value known by t (Section 3.6 macro feed; release lags of wt_tests.MONTHLY)."""
    m = load_macro_monthly(macro_dir)
    for key, col in (("oil", "oil_yoy"), ("copper", "copper_yoy"), ("cpi", "cpi_yoy")):
        f, _, lag = MONTHLY[key]
        s = load_fred_monthly(macro_dir / f, lag)
        s.index = s.index.to_timestamp(how="end").normalize()
        m[col] = (100 * np.log(s / s.shift(12))).reindex(m.index)
    gs10 = load_fred_monthly(macro_dir / MONTHLY["gs10"][0], MONTHLY["gs10"][2])
    tb3 = load_fred_monthly(macro_dir / MONTHLY["tb3ms"][0], MONTHLY["tb3ms"][2])
    curve = gs10 - tb3
    curve.index = curve.index.to_timestamp(how="end").normalize()
    m["curve"] = curve.reindex(m.index)
    return m


def sector_month(bonds: pd.DataFrame, gics: pd.DataFrame) -> pd.DataFrame:
    """Per (date, sector): eta (relative median log spread), y (relative mean excess return), cost, bond count."""
    b = bonds.dropna(subset=["gvkey", "g_spread", "total", "tsy_ret"]).copy()
    b = b[b["g_spread"] > 0]
    b["gvkey"] = b["gvkey"].astype(str)
    b["tau"] = pd.to_datetime(b["date"]) + pd.Timedelta(1, unit="D")
    b["sector"] = sector_at(gics, b[["gvkey", "tau"]]).to_numpy()
    b = b[b["sector"] != "NA"]
    b["x"] = b["total"] - b["tsy_ret"]
    lo, hi = b["x"].quantile([0.01, 0.99])
    b["x"] = b["x"].clip(lo, hi)
    g = b.groupby(["date", "sector"])
    s = pd.DataFrame({"log_s": g["g_spread"].apply(lambda v: np.log(v).median()), "x": g["x"].mean(),
                      "cost": g["cost_rt"].mean(), "n": g.size()}).reset_index()
    s = s[s["n"] >= MIN_BONDS].copy()
    s["eta"] = s["log_s"] - s.groupby("date")["log_s"].transform("mean")
    s["y"] = s["x"] - s.groupby("date")["x"].transform("mean")
    return s


def eta_hat(panel: pd.DataFrame, macro: pd.DataFrame, cols: Sequence[str] = MACRO_COLS) -> pd.Series:
    """eta_hat_{j,t}: ridge fit of eta on standardised m over months <= t of sector j (Section 8, S7 eta_hat(m_t)).

    Standardisation uses means and sds of months <= t. Intuition: the sector spread the macro state explains,
    learned only from what a reader knew at t.
    """
    m = macro[list(cols)]
    out = pd.Series(np.nan, index=panel.index)
    for _, g in panel.groupby("sector"):
        g = g.sort_values("date")
        X_all = m.reindex(pd.to_datetime(g["date"])).to_numpy()
        y_all = g["eta"].to_numpy()
        for i in range(len(g)):
            ok = np.isfinite(X_all[: i + 1]).all(axis=1) & np.isfinite(y_all[: i + 1])
            if ok.sum() < MIN_TRAIN or not np.isfinite(X_all[i]).all():
                continue
            X, y = X_all[: i + 1][ok], y_all[: i + 1][ok]
            mu, sd = X.mean(axis=0), X.std(axis=0)
            sd[sd == 0] = 1.0
            Z = (X - mu) / sd
            Z1 = np.column_stack([np.ones(len(Z)), Z])
            pen = RIDGE * np.eye(Z1.shape[1])
            pen[0, 0] = 0.0
            beta = np.linalg.solve(Z1.T @ Z1 + pen, Z1.T @ y)
            out.loc[g.index[i]] = float(np.r_[1.0, (X_all[i] - mu) / sd] @ beta)
    return out


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------


def monthly_ic(df: pd.DataFrame, col: str) -> pd.Series:
    """Spearman rank IC of `col` against y per month, months with at least 5 sectors."""
    def ic(g):
        return spearmanr(g[col], g["y"]).statistic if len(g) >= 5 else np.nan
    return df.groupby("date").apply(ic, include_groups=False).dropna()


def fama_macbeth(df: pd.DataFrame) -> pd.DataFrame:
    """Per month: y on eta and -eta_hat (OLS with intercept). Rows are monthly slopes."""
    rows = {}
    for d, g in df.groupby("date"):
        if len(g) < 5:
            continue
        X = np.column_stack([np.ones(len(g)), g["eta"], -g["eta_hat"]])
        b = np.linalg.lstsq(X, g["y"].to_numpy(), rcond=None)[0]
        rows[d] = {"eta": b[1], "neg_eta_hat": b[2]}
    return pd.DataFrame(rows).T


def tercile_spread(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """Top-minus-bottom tercile of `col` per month: gross and net of the round-trip cost on both legs."""
    rows = {}
    for d, g in df.groupby("date"):
        if len(g) < 6:
            continue
        r = g[col].rank(pct=True)
        top, bot = g[r > 2 / 3], g[r <= 1 / 3]
        gross = top["y"].mean() - bot["y"].mean()
        rows[d] = {"gross": gross, "net": gross - top["cost"].mean() - bot["cost"].mean()}
    return pd.DataFrame(rows).T


def by_cycle(s: pd.Series) -> dict:
    out = {}
    for w, (a, b) in CYCLE_WINDOWS.items():
        v = s[(s.index >= pd.Timestamp(a)) & (s.index <= pd.Timestamp(b))]
        out[str(w)] = {"n": int(len(v)), "mean": float(v.mean()) if len(v) else None}
    return out


def run_horizon(bonds: pd.DataFrame, gics: pd.DataFrame, macro: pd.DataFrame, h: int) -> dict:
    sm = sector_month(bonds, gics).reset_index(drop=True)
    sm["eta_hat"] = eta_hat(sm, macro)
    sm["s7"] = sm["eta"] - sm["eta_hat"]
    t = sm.dropna(subset=["eta_hat"])
    # outcomes overlap for h > 1: sample every h-th month for the t statistics, keep all months for the means
    months = sorted(t["date"].unique())
    keep = set(months[::h])
    ic_s7, ic_eta = monthly_ic(t, "s7"), monthly_ic(t, "eta")
    fm = fama_macbeth(t)
    ls = tercile_spread(t, "s7")
    ls_eta = tercile_spread(t, "eta")
    sub = lambda s: s[s.index.isin(keep)]  # noqa: E731
    p1 = ewc_test(sub(fm["neg_eta_hat"]).to_numpy())
    cyc = by_cycle(ls["net"])
    testable = {w: v for w, v in cyc.items() if v["n"] > 0}
    res = {
        "h": h, "sector_months": int(len(t)), "months": int(len(months)), "first_month": str(months[0])[:10],
        "sectors": sorted(t["sector"].unique().tolist()),
        "ic_s7": {"mean": float(ic_s7.mean()), "ewc": ewc_test(sub(ic_s7).to_numpy())},
        "ic_eta": {"mean": float(ic_eta.mean()), "ewc": ewc_test(sub(ic_eta).to_numpy())},
        "fm_eta": {"mean": float(fm["eta"].mean()), "ewc": ewc_test(sub(fm["eta"]).to_numpy())},
        "fm_neg_eta_hat": {"mean": float(fm["neg_eta_hat"].mean()), "ewc": p1},
        "ls_s7": {"gross_mean": float(ls["gross"].mean()), "net_mean": float(ls["net"].mean()),
                  "net_ewc": ewc_test(sub(ls["net"]).to_numpy()), "cycles_net": cyc},
        "ls_eta": {"gross_mean": float(ls_eta["gross"].mean()), "net_mean": float(ls_eta["net"].mean()),
                   "cycles_net": by_cycle(ls_eta["net"])},
    }
    res["P1"] = bool(p1["t"] is not None and p1["mean"] > 0 and p1["t"] > 2)
    res["P2"] = bool(ic_s7.mean() > ic_eta.mean())
    res["P3"] = bool(testable and all(v["mean"] is not None and v["mean"] > 0 for v in testable.values()))
    res["pass"] = res["P1"] and res["P2"] and res["P3"]
    return res


def main() -> dict:
    root = data_root()
    gics = pd.read_parquet(root / "backtest" / "gics_history.parquet")
    macro = load_macro(root / "macro")
    out = {}
    for h in HORIZONS:
        bonds = pd.read_parquet(root / "backtest" / f"results_h{h}_full.parquet")
        out[str(h)] = run_horizon(bonds, gics, macro, h)
        r = out[str(h)]
        print(f"h={h}: IC s7 {r['ic_s7']['mean']:+.3f} vs eta {r['ic_eta']['mean']:+.3f}; "
              f"FM -eta_hat {r['fm_neg_eta_hat']['mean']:+.4f} (EWC t {r['fm_neg_eta_hat']['ewc']['t']:.2f}); "
              f"LS net {r['ls_s7']['net_mean'] * 100:+.2f}%; P1 {r['P1']} P2 {r['P2']} P3 {r['P3']}")
    path = root / "backtest" / "s7_sector_tilt.json"
    path.write_text(json.dumps(out, indent=1, default=str))
    return out


if __name__ == "__main__":
    main()
