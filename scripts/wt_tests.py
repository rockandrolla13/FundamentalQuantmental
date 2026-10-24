"""Historical test of the Wolfe Trahan claims on sector EBITDA, margin, and leverage.

Decision page: docs/decisions/2026-10-24-wt-relationship-tests.md (Phase 1, historical study). Methodology 5.2.
Run:
    PYTHONPATH=. python3 scripts/wt_tests.py --claim H1

Inputs (vendor data stays under data/raw/, out of git):
- data/raw/macro/bos_dif.csv   Philadelphia Fed Manufacturing Business Outlook Survey, SA diffusion indexes, 1968-.
- data/raw/macro/BAA10Y.csv    FRED, Moody's Baa yield minus 10-year Treasury, daily.
- data/raw/macro/DRTSCILM.csv  FRED, SLOOS net share of banks tightening C&I loans to large and medium firms.
- data/raw/compustat/fundq_15_20_25.parquet  comp.fundq, US firms, GICS sectors 15, 20, 25, 1993-.

Steps:
1. Signal. Quarter average of the survey series. z_q = (x_q - x_{q-2}) / sd of all 2-quarter changes up to q.
   Intuition: a 6-month jump in prices paid, measured against its own history as known then.
2. Outcomes. Firm LTM sums (four consecutive quarters). Sector aggregates over the firms present at both ends of
   each window: cost ratio v = COGS / sales, EBITDA margin, EBITDA growth, sales growth change, leverage.
   The added quarters q+1 ... q+k all fall after the signal quarter, so no outcome leaks into the signal.
3. Event count: share of signal quarters (z > 1) after which the outcome moved the claimed way, against all other
   quarters. Episodes = first quarter of each run of signal quarters.
4. Regression of the outcome on z with controls (survey activity, Baa spread change, SLOOS, own lag).
   Newey-West errors with k lags. Full sample, claim period (to 2011Q4), holdout (2012Q1 on).
5. Holdout forecast race from 2012Q1: controls only against controls + z, expanding window fitted only on rows
   whose outcome was known at q. Clark-West (2007) statistic.
6. Claim-signed mean of z * outcome in each cycle window of hy.backtest.CYCLE_WINDOWS.

Limits: comp.fundq is the current view, not point in time. It measures what happened, after restatements.
The survey seasonal factors are revised each year. GICS sector is the current one from comp.company.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import norm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from hy.backtest import CYCLE_WINDOWS  # noqa: E402

NOTE_CUT = pd.Period("2011Q4", "Q")  # last quarter the 2011 notes could see
HOLDOUT_START = pd.Period("2012Q1", "Q")
N_CLAIMS = 8  # Holm family size of the decision page
SECTORS = {"15": "Materials", "20": "Industrials", "25": "Consumer Discretionary"}
HL_LEVERAGE = 4.0  # debt / LTM EBITDA above this marks a high-leverage (HY-like) firm

# Claim table of the decision page. sign = +1: the outcome rises after the signal rises. Leads are fixed here.
CLAIMS = {
    "H1": {
        "rows": [38, 54, 153],
        "text": "Rising factory input prices squeeze margins at once and cut sales 6 to 9 months later",
        "series": "PPC",
        "sectors": ["20", "15", "25"],
        "primary": {"dv_k2": +1, "dsg_k4": -1},
        "secondary": {"dmargin_k4": -1, "debitda_k4": -1, "dlev_k4": +1},
    },
}


# ---------------------------------------------------------------------------
# Macro inputs
# ---------------------------------------------------------------------------


def load_survey(path: Path) -> pd.DataFrame:
    """Monthly survey diffusion indexes. The survey is released in its own month, so month m is known by month end."""
    df = pd.read_csv(path)
    df["month"] = pd.to_datetime(df["DATE"], format="%b-%y")
    # %y maps 68 to 2068; the survey starts in 1968
    df.loc[df["month"].dt.year > 2060, "month"] -= pd.DateOffset(years=100)
    return df.set_index(df["month"].dt.to_period("M")).drop(columns=["DATE", "month"]).astype(float)


def to_quarter(monthly: pd.DataFrame) -> pd.DataFrame:
    """Quarter average of complete quarters. All three months are known at the quarter end."""
    q = monthly.groupby(monthly.index.asfreq("Q"))
    out = q.mean()
    return out[q.size() == 3]


def signal_z(x: pd.Series, lag: int = 2, min_obs: int = 20) -> pd.Series:
    """z_q = (x_q - x_{q-lag}) / sd(changes up to q). Methodology 5.2 candidate lead.

    Intuition: the size of a jump relative to the jumps an investor had seen by then. Uses no later data.
    """
    d = x - x.shift(lag)
    sd = d.expanding(min_periods=min_obs).std()
    return d / sd


def load_controls(macro_dir: Path, survey_q: pd.DataFrame) -> pd.DataFrame:
    """Controls known at quarter end: survey activity (PMI proxy), Baa spread 2-quarter change, SLOOS net tightening."""
    baa = pd.read_csv(macro_dir / "BAA10Y.csv", na_values=".")
    baa.columns = ["date", "baa"]
    baa["q"] = pd.to_datetime(baa["date"]).dt.to_period("Q")
    baa_q = baa.groupby("q")["baa"].mean()
    sl = pd.read_csv(macro_dir / "DRTSCILM.csv", na_values=".")
    sl.columns = ["date", "sloos"]
    # FRED dates the survey at the quarter start; the Board publishes it inside that quarter
    sl_q = sl.set_index(pd.to_datetime(sl["date"]).dt.to_period("Q"))["sloos"]
    out = pd.DataFrame({"gac": survey_q["GAC"], "dbaa": baa_q - baa_q.shift(2), "sloos": sl_q})
    return out


# ---------------------------------------------------------------------------
# Firm panel and sector outcomes
# ---------------------------------------------------------------------------


def firm_panel(fq: pd.DataFrame, min_sales: float = 10.0) -> pd.DataFrame:
    """Firm-quarter rows on the calendar quarter, with LTM sums over four consecutive quarters."""
    df = fq.dropna(subset=["datacqtr"]).copy()
    df["q"] = pd.PeriodIndex(df["datacqtr"].str.replace("Q", "-Q"), freq="Q")
    df = df.sort_values("datadate").drop_duplicates(["gvkey", "q"], keep="last").sort_values(["gvkey", "q"])
    df["debt"] = df["dlttq"].fillna(0.0) + df["dlcq"].fillna(0.0)
    g = df.groupby("gvkey")
    consecutive = (df["q"] - g["q"].shift(3)).apply(lambda x: getattr(x, "n", np.nan)) == 3
    for c in ("saleq", "cogsq", "oibdpq"):
        df[c + "_ltm"] = g[c].transform(lambda s: s.rolling(4, min_periods=4).sum()).where(consecutive)
    keep = (df["saleq_ltm"] > 4 * min_sales) & df["cogsq_ltm"].notna() & df["oibdpq_ltm"].notna()
    return df.loc[keep, ["gvkey", "q", "gsector", "saleq_ltm", "cogsq_ltm", "oibdpq_ltm", "debt"]]


def _wide(panel: pd.DataFrame, col: str) -> pd.DataFrame:
    return panel.pivot(index="gvkey", columns="q", values=col)


def sector_outcomes(panel: pd.DataFrame, sector: str, hl_only: bool = False) -> pd.DataFrame:
    """Matched-firm sector aggregates per signal quarter q (Section 5.2 drivers: v, margin, growth, leverage).

    dv_k2      change in COGS / sales from q to q+2 (LTM)
    dmargin_k4 change in EBITDA / sales from q to q+4
    debitda_k4 growth of summed LTM EBITDA from q to q+4
    dsg_k4     sales growth over q..q+4 minus sales growth over q-4..q
    dlev_k4    change in summed debt / summed LTM EBITDA from q to q+4
    `hl_only` keeps firms with debt / LTM EBITDA > HL_LEVERAGE (EBITDA > 0) at q.
    """
    p = panel[panel["gsector"] == sector]
    S, C, E, D = (_wide(p, c) for c in ("saleq_ltm", "cogsq_ltm", "oibdpq_ltm", "debt"))
    qs = S.columns
    rows = []
    for i, q in enumerate(qs):
        base = S[q].notna() & E[q].notna()
        if hl_only:
            lev = D[q] / E[q]
            base &= (E[q] > 0) & (lev > HL_LEVERAGE)
        r = {"q": q, "n": int(base.sum())}

        def at(qq):
            return qq if qq in S.columns else None

        q2, q4, qm4 = at(q + 2), at(q + 4), at(q - 4)
        if q2 is not None:
            m = base & S[q2].notna()
            if m.sum() >= 20:
                r["dv_k2"] = C.loc[m, q2].sum() / S.loc[m, q2].sum() - C.loc[m, q].sum() / S.loc[m, q].sum()
        if q4 is not None:
            m = base & S[q4].notna() & E[q4].notna()
            if m.sum() >= 20:
                r["dmargin_k4"] = E.loc[m, q4].sum() / S.loc[m, q4].sum() - E.loc[m, q].sum() / S.loc[m, q].sum()
                e0, e4 = E.loc[m, q].sum(), E.loc[m, q4].sum()
                r["debitda_k4"] = e4 / e0 - 1 if e0 > 0 else np.nan
                if e0 > 0 and e4 > 0:
                    r["dlev_k4"] = D.loc[m, q4].sum() / e4 - D.loc[m, q].sum() / e0
            if qm4 is not None:
                m3 = m & S[qm4].notna()
                if m3.sum() >= 20:
                    s_m4, s_0, s_4 = S.loc[m3, qm4].sum(), S.loc[m3, q].sum(), S.loc[m3, q4].sum()
                    r["dsg_k4"] = (s_4 / s_0 - 1) - (s_0 / s_m4 - 1)
        rows.append(r)
    return pd.DataFrame(rows).set_index("q")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def horizon(outcome: str) -> int:
    return int(outcome.rsplit("_k", 1)[1])


def event_count(z: pd.Series, y: pd.Series, sign: int, thr: float = 1.0) -> dict:
    """Share of signal quarters after which sign * y > 0, against the other quarters."""
    d = pd.DataFrame({"z": z, "y": y}).dropna()
    on = d["z"] > thr
    hit = sign * d["y"] > 0
    starts = on & ~on.shift(1, fill_value=False)
    episodes = [{"start": str(q), "z": round(float(d.at[q, "z"]), 2), "y": round(float(d.at[q, "y"]), 4),
                 "as_claimed": bool(hit.at[q])} for q in d.index[starts]]
    return {
        "n_signal_quarters": int(on.sum()),
        "n_episodes": int(starts.sum()),
        "hit_rate_signal": float(hit[on].mean()) if on.any() else np.nan,
        "hit_rate_other": float(hit[~on].mean()) if (~on).any() else np.nan,
        "mean_y_signal": float(d.loc[on, "y"].mean()) if on.any() else np.nan,
        "mean_y_other": float(d.loc[~on, "y"].mean()) if (~on).any() else np.nan,
        "episode_hit_rate": float(np.mean([e["as_claimed"] for e in episodes])) if episodes else np.nan,
        "episodes": episodes,
    }


def hac_regression(y: pd.Series, X: pd.DataFrame, lags: int) -> dict:
    """OLS of y on X with Newey-West errors (lags = horizon). Returns the coefficient and t of column 'z'."""
    d = pd.concat([y.rename("y"), X], axis=1).dropna()
    if len(d) < 20:
        return {"n": len(d), "b": np.nan, "t": np.nan}
    res = sm.OLS(d["y"], sm.add_constant(d.drop(columns="y"))).fit(cov_type="HAC", cov_kwds={"maxlags": lags})
    return {"n": int(len(d)), "b": float(res.params["z"]), "t": float(res.tvalues["z"]), "r2": float(res.rsquared)}


def clark_west(y: pd.Series, X_base: pd.DataFrame, X_full: pd.DataFrame, k: int,
               start: pd.Period = HOLDOUT_START, min_train: int = 24) -> dict:
    """Expanding-window race of nested models. At q, fit on rows t <= q - k (outcome known by q).

    Clark-West (2007): f = e_base^2 - (e_full^2 - (yhat_base - yhat_full)^2); t of mean(f) with Newey-West, k lags.
    One-sided p-value: the larger model forecasts better.
    """
    d = pd.concat([y.rename("y"), X_full], axis=1).dropna()
    base_cols = list(X_base.columns)
    out = []
    for q in d.index[d.index >= start]:
        tr = d[d.index <= q - k]
        if len(tr) < min_train:
            continue
        fb = sm.OLS(tr["y"], sm.add_constant(tr[base_cols], has_constant="add")).fit()
        ff = sm.OLS(tr["y"], sm.add_constant(tr.drop(columns="y"), has_constant="add")).fit()
        xb = sm.add_constant(d.loc[[q], base_cols], has_constant="add")
        xf = sm.add_constant(d.loc[[q]].drop(columns="y"), has_constant="add")
        out.append((q, d.at[q, "y"], float(fb.predict(xb).iloc[0]), float(ff.predict(xf).iloc[0])))
    if len(out) < 12:
        return {"n": len(out), "cw_t": np.nan, "p": np.nan, "oos_r2": np.nan}
    o = pd.DataFrame(out, columns=["q", "y", "yb", "yf"]).set_index("q")
    eb, ef = o["y"] - o["yb"], o["y"] - o["yf"]
    f = eb**2 - (ef**2 - (o["yb"] - o["yf"]) ** 2)
    res = sm.OLS(f.to_numpy(), np.ones(len(f))).fit(cov_type="HAC", cov_kwds={"maxlags": k})
    t = float(res.tvalues[0])
    return {"n": int(len(o)), "cw_t": t, "p": float(1 - norm.cdf(t)),
            "oos_r2": float(1 - (ef**2).sum() / (eb**2).sum())}


def cycle_means(z: pd.Series, y: pd.Series, sign: int) -> dict[int, float]:
    """Claim-signed mean of z * y over signal quarters inside each cycle window. Positive = the claim held there."""
    d = pd.DataFrame({"z": z, "y": y}).dropna()
    out = {}
    for c, (a, b) in CYCLE_WINDOWS.items():
        sel = d[(d.index >= pd.Period(a, "Q")) & (d.index <= pd.Period(b, "Q"))]
        out[c] = float((sign * sel["z"] * sel["y"]).mean()) if len(sel) else float("nan")
    return out


def holm_threshold(alpha: float = 0.05, m: int = N_CLAIMS) -> float:
    """Strictest Holm level: alpha / m. A claim that clears it passes whatever the other claims show."""
    return alpha / m


def run_outcome(z: pd.Series, controls: pd.DataFrame, y: pd.Series, name: str, sign: int) -> dict:
    k = horizon(name)
    lag_y = y.shift(k).rename("y_lag")  # the outcome over q-k..q, known at q
    X = pd.concat([z.rename("z"), controls, lag_y], axis=1)
    y = y.reindex(X.index)
    base = X.drop(columns="z")
    claim = X.index <= NOTE_CUT
    hold = X.index >= HOLDOUT_START
    reg = {
        "full": hac_regression(y, X, k),
        "claim_period": hac_regression(y[claim], X[claim], k),
        "holdout": hac_regression(y[hold], X[hold], k),
    }
    cw = clark_west(y, base, X, k)
    cyc = cycle_means(z, y, sign)
    holdout_sign_ok = bool(np.sign(reg["holdout"]["b"]) == sign) if np.isfinite(reg["holdout"]["b"]) else False
    n_cycles = sum(v > 0 for v in cyc.values() if np.isfinite(v))
    n_post = sum(cyc[c] > 0 for c in (2015, 2020, 2022) if np.isfinite(cyc[c]))
    passed = holdout_sign_ok and np.isfinite(cw["p"]) and cw["p"] < holm_threshold() and n_cycles >= 3 and n_post >= 2
    return {"outcome": name, "sign_claimed": sign, "horizon_q": k, "events": event_count(z, y, sign),
            "regression": reg, "clark_west": cw, "cycles": cyc, "holdout_sign_ok": holdout_sign_ok,
            "cycles_as_claimed": int(n_cycles), "post_note_cycles_as_claimed": int(n_post), "pass": bool(passed)}


def run_claim(claim_id: str, root: Path = ROOT) -> dict:
    spec = CLAIMS[claim_id]
    survey_q = to_quarter(load_survey(root / "data/raw/macro/bos_dif.csv"))
    z = signal_z(survey_q[spec["series"]])
    controls = load_controls(root / "data/raw/macro", survey_q)
    panel = firm_panel(pd.read_parquet(root / "data/raw/compustat/fundq_15_20_25.parquet"))
    result = {"claim": claim_id, "text": spec["text"], "rows": spec["rows"], "series": spec["series"], "sectors": {}}
    for sec in spec["sectors"]:
        for group, hl in (("all", False), ("high_leverage", True)):
            outc = sector_outcomes(panel, sec, hl_only=hl)
            res = {}
            for kind in ("primary", "secondary"):
                for name, sign in spec[kind].items():
                    if name in outc:
                        res[name] = {"kind": kind, **run_outcome(z, controls, outc[name], name, sign)}
            res["median_firms"] = float(outc["n"].median())
            result["sectors"].setdefault(SECTORS[sec], {})[group] = res
    return result


def print_summary(r: dict) -> None:
    print(f"{r['claim']}: {r['text']} (rows {r['rows']}, series {r['series']})")
    for sec, groups in r["sectors"].items():
        for group, res in groups.items():
            print(f"\n{sec} / {group} (median firms {res['median_firms']:.0f})")
            for name, o in res.items():
                if name == "median_firms":
                    continue
                e, h, cw = o["events"], o["regression"]["holdout"], o["clark_west"]
                print(f"  {name:11s} {o['kind'][:3]} sign {o['sign_claimed']:+d} | events {e['n_episodes']:2d} "
                      f"hit {e['episode_hit_rate']:.2f} | qtrs signal {e['hit_rate_signal']:.2f} vs other "
                      f"{e['hit_rate_other']:.2f} | b_claim {o['regression']['claim_period']['b']:+.4f} "
                      f"t {o['regression']['claim_period']['t']:+.2f} | b_hold {h['b']:+.4f} t {h['t']:+.2f} | "
                      f"CW t {cw['cw_t']:+.2f} p {cw['p']:.3f} | cycles {o['cycles_as_claimed']}/4 | "
                      f"{'PASS' if o['pass'] else 'fail'}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--claim", default="H1", choices=sorted(CLAIMS))
    a = ap.parse_args()
    r = run_claim(a.claim)
    out = ROOT / f"data/raw/backtest/wt_{a.claim}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(r, indent=1, default=lambda x: None if isinstance(x, float) and not np.isfinite(x) else str(x)))
    print_summary(r)
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
