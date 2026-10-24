"""Historical, firm-level test of the Wolfe Trahan claims on EBITDA, margin, sales growth, and leverage.

Decision page: docs/decisions/2026-10-24-wt-relationship-tests.md (Phase 1, historical study). Methodology 5.2.
Run:
    PYTHONPATH=. python3 scripts/wt_tests.py              # every claim
    PYTHONPATH=. python3 scripts/wt_tests.py --claim H2   # one claim

Inputs (vendor data stays under data/raw/, out of git):
- data/raw/compustat/fundq_nonfin.parquet  comp.fundq, US non-financial firms (GICS sectors except 40 and 60), 1992-.
- data/raw/macro/bos_dif.csv  Philadelphia Fed Manufacturing Business Outlook Survey, SA diffusion indexes, 1968-.
- data/raw/macro/<FRED id>.csv  BAA10Y, DRTSCILM, CPIAUCNS, WTISPLC, HOUST, PCOPPUSDM, SPASTT01KRM661N, GS10, TB3MS.

Unit of observation: one firm in one calendar quarter. Every firm counts once (equal weight), so small and mid-size
firms (the HY-like part of the market) weigh as much as the largest ones.

Three tests per claim:
A. Average firm. The equal-weighted mean of a firm outcome in the claimed group, one value per quarter. Event count,
   Newey-West regression with controls, Clark-West holdout race, cycle windows. Also on high-leverage firms only.
B. Cross-section, relative. The mean outcome of the claimed group minus that of the comparison group in the same
   quarter. The common cycle drops out, so the test reads only how the claimed group differs. Equivalent to a firm
   panel with quarter fixed effects and a group-times-signal term.
C. Cross-section, firm exposure. Each quarter, estimate each firm's own sensitivity b_i to the signal from its past
   data only (outcomes known by q). Then regress the firm outcomes of quarter q on b_i across all firms: slope
   lambda_q. If firm exposures persist, lambda_q moves with the signal: regress lambda_q on z_q (Fama-MacBeth).
   A slope near 1 means the past sensitivity carries over in full; near 0 means it does not carry over.

Point in time: each macro series enters with its release lag (CPI and housing starts one month), so a quarter's
value uses only months published by the quarter end. Firm outcomes cover quarters q+1 ... q+k, all after the signal.
Limits: comp.fundq is the current view, not point in time (outcomes after restatements). Survey seasonal factors are
revised each year. GICS codes are the current ones from comp.company.
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
HL_LEVERAGE = 4.0  # debt / LTM EBITDA above this marks a high-leverage (HY-like) firm
MIN_LTM_SALES = 40.0  # USD millions
MIN_FIRMS = 20
DECLINE = 0.20  # EBITDA decline event: EBITDA_{q+4} < 0.8 EBITDA_q

# Monthly series: (file, column, release lag in months). Lag = months after the reference month before publication.
MONTHLY = {
    "cpi": ("CPIAUCNS.csv", None, 1),
    "oil": ("WTISPLC.csv", None, 0),
    "houst": ("HOUST.csv", None, 1),
    "copper": ("PCOPPUSDM.csv", None, 0),
    "kospi": ("SPASTT01KRM661N.csv", None, 0),
    "gs10": ("GS10.csv", None, 0),
    "tb3ms": ("TB3MS.csv", None, 0),
}

# Group membership from current GICS codes.
GROUPS = {
    "Energy": ("gsector", ["10"]),
    "Materials": ("gsector", ["15"]),
    "Industrials": ("gsector", ["20"]),
    "Consumer Discretionary": ("gsector", ["25"]),
    "Commodity (Energy + Materials)": ("gsector", ["10", "15"]),
    "Transport": ("gind", ["203010", "203020", "203030", "203040", "203050"]),
    "Autos": ("gind", ["251010", "251020"]),
    "Housing (homebuilders + building products)": ("housing", None),
    "All": ("all", None),
}

# Claim table of the decision page. sign = +1: the outcome rises when the signal is high. Leads are fixed here.
# signal: (raw series, transform). Transform "level": z of the level against its history to date. "change2": z of the
# 2-quarter change. Relative tests: (target, comparison, outcome, sign); comparison "rest" = all other firms.
CLAIMS = {
    "H1": {"rows": [38, 54, 153], "text": "Rising factory input prices squeeze margins at once and cut sales 6 to 9 months later",
           "signal": ("PPC", "level"),
           "tests": [(g, o, s) for g in ("Industrials", "Materials", "Consumer Discretionary")
                     for o, s in (("dv_k2", +1), ("dsg_k4", -1))],
           "relative": [(g, "rest", o, s) for g in ("Industrials", "Materials", "Consumer Discretionary")
                        for o, s in (("dv_k2", +1), ("dsg_k4", -1))]},
    "H1c": {"rows": [38, 54, 153], "text": "H1 with the 2-quarter change of prices paid (the first run's signal)",
            "signal": ("PPC", "change2"), "robustness_of": "H1",
            "tests": [(g, o, s) for g in ("Industrials", "Materials", "Consumer Discretionary")
                      for o, s in (("dv_k2", +1), ("dsg_k4", -1))],
            "relative": []},
    "H2": {"rows": [73, 82, 96], "text": "Rising consumer inflation hurts consumer companies and helps commodity producers about 6 months later",
           "signal": ("cpi_yoy", "level"),
           "tests": [("Consumer Discretionary", "debitda_k4", -1), ("Consumer Discretionary", "dmargin_k4", -1),
                     ("Commodity (Energy + Materials)", "debitda_k4", +1)],
           "relative": [("Consumer Discretionary", "Commodity (Energy + Materials)", "debitda_k4", -1),
                        ("Consumer Discretionary", "Commodity (Energy + Materials)", "dmargin_k4", -1)]},
    "H3": {"rows": [52, 78], "text": "Rising oil lifts energy EBITDA and squeezes fuel users",
           "signal": ("oil_yoy", "level"),
           "tests": [("Energy", "debitda_k4", +1), ("Transport", "dv_k2", +1), ("Consumer Discretionary", "dv_k2", +1)],
           "relative": [("Energy", "Consumer Discretionary", "debitda_k4", +1), ("Transport", "rest", "dv_k2", +1)]},
    "H4": {"rows": [58, 133, 134], "text": "Housing activity leads housing-linked companies by 6 to 12 months",
           "signal": ("houst_yoy", "level"),
           "tests": [("Housing (homebuilders + building products)", "debitda_k4", +1),
                     ("Housing (homebuilders + building products)", "dsg_k4", +1)],
           "relative": [("Housing (homebuilders + building products)", "rest", "debitda_k4", +1),
                        ("Housing (homebuilders + building products)", "rest", "dsg_k4", +1)]},
    "H5": {"rows": [42, 49], "text": "Copper gives a real-time read of global demand",
           "signal": ("copper_yoy", "level"),
           "tests": [("Materials", "dsg_k2", +1), ("Industrials", "dsg_k2", +1)],
           "relative": [("Materials", "rest", "dsg_k2", +1), ("Industrials", "rest", "dsg_k2", +1)]},
    "H5k": {"rows": [50], "text": "The Korean stock market gives a real-time read of global demand",
            "signal": ("kospi_yoy", "level"), "robustness_of": "H5",
            "tests": [("Materials", "dsg_k2", +1), ("Industrials", "dsg_k2", +1)],
            "relative": [("Materials", "rest", "dsg_k2", +1), ("Industrials", "rest", "dsg_k2", +1)]},
    "H6": {"rows": [2, 4], "text": "Rising factory new orders lead sales and earnings of manufacturing-linked companies",
           "signal": ("NOC", "level"),
           "tests": [(g, o, +1) for g in ("Industrials", "Materials", "Autos") for o in ("dsg_k2", "debitda_k4")],
           "relative": [(g, "rest", o, +1) for g in ("Industrials", "Materials", "Autos") for o in ("dsg_k2", "debitda_k4")]},
    "H7": {"rows": [112], "text": "A steep real yield curve (10-year minus CPI) means fewer EBITDA declines a year ahead",
           "signal": ("real_curve", "level"),
           "tests": [("All", "decline_k4", -1)], "relative": []},
    "H7n": {"rows": [110], "text": "Comparator for H7: the nominal curve (10-year minus 3-month)",
            "signal": ("nominal_curve", "level"), "robustness_of": "H7",
            "tests": [("All", "decline_k4", -1)], "relative": []},
    "H8a": {"rows": [90], "text": "Control: a widening Baa spread means more EBITDA declines a year ahead",
            "signal": ("dbaa", "raw"), "tests": [("All", "decline_k4", +1)], "relative": []},
    "H8b": {"rows": [], "text": "Control: tighter bank lending standards mean more EBITDA declines a year ahead",
            "signal": ("sloos", "raw"), "tests": [("All", "decline_k4", +1)], "relative": []},
    "H8c": {"rows": [], "text": "Control: stronger factory activity (PMI proxy) means fewer EBITDA declines a year ahead",
            "signal": ("gac", "raw"), "tests": [("All", "decline_k4", -1)], "relative": []},
}
CONTROL_COLS = ("gac", "dbaa", "sloos")


# ---------------------------------------------------------------------------
# Macro inputs
# ---------------------------------------------------------------------------


def load_survey(path: Path) -> pd.DataFrame:
    """Monthly survey diffusion indexes. The survey is released in its own month, so month m is known by month end."""
    df = pd.read_csv(path)
    df["month"] = pd.to_datetime(df["DATE"], format="%b-%y")
    df.loc[df["month"].dt.year > 2060, "month"] -= pd.DateOffset(years=100)  # %y maps 68 to 2068
    return df.set_index(df["month"].dt.to_period("M")).drop(columns=["DATE", "month"]).astype(float)


def load_fred_monthly(path: Path, lag_months: int = 0) -> pd.Series:
    """Monthly FRED series re-dated to the month it was published: value of month m sits at m + lag."""
    df = pd.read_csv(path, na_values=".")
    s = pd.Series(df.iloc[:, 1].astype(float).to_numpy(), index=pd.to_datetime(df.iloc[:, 0]).dt.to_period("M"))
    s.index = s.index + lag_months
    return s


def to_quarter(monthly: pd.DataFrame | pd.Series) -> pd.DataFrame | pd.Series:
    """Quarter average of complete quarters. All three months are known at the quarter end."""
    q = monthly.groupby(monthly.index.asfreq("Q"))
    out = q.mean()
    return out[q.size() == 3]


def signal_z(x: pd.Series, lag: int = 2, min_obs: int = 20) -> pd.Series:
    """z_q = (x_q - x_{q-lag}) / sd(changes up to q). Methodology 5.2 candidate lead. Uses no later data."""
    d = x - x.shift(lag)
    return d / d.expanding(min_periods=min_obs).std()


def level_z(x: pd.Series, min_obs: int = 20) -> pd.Series:
    """z_q = (x_q - mean of x to q) / sd of x to q. Intuition: how high the series is against its own history to date."""
    return (x - x.expanding(min_periods=min_obs).mean()) / x.expanding(min_periods=min_obs).std()


def build_macro(macro_dir: Path) -> pd.DataFrame:
    """Quarterly raw macro series, each built only from months published by the quarter end."""
    sv = to_quarter(load_survey(macro_dir / "bos_dif.csv"))
    m = {k: load_fred_monthly(macro_dir / f, lag) for k, (f, _, lag) in MONTHLY.items()}
    q = {k: to_quarter(v) for k, v in m.items()}
    yoy = lambda s: 100 * np.log(s / s.shift(4))  # noqa: E731
    baa = pd.read_csv(macro_dir / "BAA10Y.csv", na_values=".")
    baa_q = baa.groupby(pd.to_datetime(baa.iloc[:, 0]).dt.to_period("Q")).agg({baa.columns[1]: "mean"}).iloc[:, 0]
    sl = pd.read_csv(macro_dir / "DRTSCILM.csv", na_values=".")
    sl_q = pd.Series(sl.iloc[:, 1].astype(float).to_numpy(), index=pd.to_datetime(sl.iloc[:, 0]).dt.to_period("Q"))
    out = pd.DataFrame({
        "PPC": sv["PPC"], "NOC": sv["NOC"], "gac": sv["GAC"],
        "cpi_yoy": yoy(q["cpi"]), "oil_yoy": yoy(q["oil"]), "houst_yoy": yoy(q["houst"]),
        "copper_yoy": yoy(q["copper"]), "kospi_yoy": yoy(q["kospi"]),
        "dbaa": baa_q - baa_q.shift(2), "sloos": sl_q,
    })
    out["real_curve"] = q["gs10"] - out["cpi_yoy"]
    out["nominal_curve"] = q["gs10"] - q["tb3ms"]
    return out


def make_signal(macro: pd.DataFrame, name: str, transform: str) -> pd.Series:
    x = macro[name].dropna()
    if transform == "level":
        return level_z(x)
    if transform == "change2":
        return signal_z(x)
    if transform == "raw":
        return (x - x.expanding(20).mean()) / x.expanding(20).std()
    raise ValueError(transform)


# ---------------------------------------------------------------------------
# Firm matrices and outcomes
# ---------------------------------------------------------------------------


def firm_matrices(fq: pd.DataFrame) -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    """Wide firm x quarter matrices of LTM sales, COGS, EBITDA and debt, plus each firm's GICS codes.

    LTM is a rolling 4-quarter sum on consecutive calendar quarters; a gap leaves NaN. Debt = dlttq + dlcq at q.
    """
    df = fq.dropna(subset=["datacqtr"]).copy()
    df["q"] = pd.PeriodIndex(df["datacqtr"].str.replace("Q", "-Q"), freq="Q")
    df = df.sort_values("datadate").drop_duplicates(["gvkey", "q"], keep="last")
    df["debt"] = df["dlttq"].fillna(0.0) + df["dlcq"].fillna(0.0)
    cols = pd.period_range(df["q"].min(), df["q"].max(), freq="Q")
    W = {}
    for c, name in (("saleq", "S"), ("cogsq", "C"), ("oibdpq", "E")):
        w = df.pivot(index="gvkey", columns="q", values=c).reindex(columns=cols)
        W[name] = w.T.rolling(4, min_periods=4).sum().T
    W["D"] = df.pivot(index="gvkey", columns="q", values="debt").reindex(columns=cols)
    big = W["S"] > MIN_LTM_SALES
    for k in W:
        W[k] = W[k].where(big)
    info = df.sort_values("datadate").groupby("gvkey")[["gsector", "gind", "gsubind"]].last()
    return W, info


def _winsor(x: pd.DataFrame, p: float = 0.01) -> pd.DataFrame:
    lo, hi = x.quantile(p), x.quantile(1 - p)
    return x.clip(lower=lo, upper=hi, axis=1)


def firm_outcomes(W: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Firm outcomes at signal quarter q over q..q+k (Section 5.2 drivers). Columns are quarters q.

    dv_k2       cost ratio COGS / sales, change q -> q+2
    dmargin_k4  EBITDA / sales, change q -> q+4
    debitda_k4  (EBITDA_{q+4} - EBITDA_q) / sales_q; scaled by sales so that small or negative EBITDA stays finite
    dsg_k4      log sales growth over q..q+4 minus over q-4..q (dsg_k2: same over 2 quarters)
    dlev_k4     debt / LTM EBITDA (EBITDA > 0, capped at 20x), change q -> q+4
    decline_k4  1 if EBITDA_{q+4} < 0.8 EBITDA_q, for firms with EBITDA_q > 0
    Continuous outcomes are winsorised at 1% and 99% within each quarter.
    """
    S, C, E, D = W["S"], W["C"], W["E"], W["D"]
    f = lambda X, k: X.shift(-k, axis=1)  # noqa: E731  value at q+k
    b = lambda X, k: X.shift(k, axis=1)  # noqa: E731   value at q-k
    v, m = C / S, E / S
    lev = (D / E).where(E > 0).clip(upper=20.0)
    ls = np.log(S)
    out = {
        "dv_k2": f(v, 2) - v,
        "dmargin_k4": f(m, 4) - m,
        "debitda_k4": (f(E, 4) - E) / S,
        "dsg_k4": (f(ls, 4) - ls) - (ls - b(ls, 4)),
        "dsg_k2": (f(ls, 2) - ls) - (ls - b(ls, 2)),
        "dlev_k4": f(lev, 4) - lev,
    }
    out = {k: _winsor(x) for k, x in out.items()}
    e4 = f(E, 4)
    out["decline_k4"] = (e4 < (1 - DECLINE) * E).astype(float).where((E > 0) & e4.notna())
    return out


def high_leverage(W: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """True where debt / LTM EBITDA > HL_LEVERAGE with EBITDA > 0 at q: the HY-like firms."""
    return (W["E"] > 0) & (W["D"] / W["E"] > HL_LEVERAGE)


def group_members(info: pd.DataFrame, group: str) -> pd.Series:
    key, codes = GROUPS[group]
    if key == "all":
        return pd.Series(True, index=info.index)
    if key == "housing":
        return (info["gsubind"] == "25201030") | (info["gind"] == "201020")
    return info[key].isin(codes)


def group_mean(Y: pd.DataFrame, rows: pd.Series, cell_mask: pd.DataFrame | None = None) -> pd.Series:
    """Equal-weighted mean outcome per quarter over the firms in `rows` (and in `cell_mask` when given)."""
    X = Y.loc[rows.reindex(Y.index, fill_value=False)]
    if cell_mask is not None:
        X = X.where(cell_mask.reindex_like(X).fillna(False))
    n = X.notna().sum()
    return X.mean().where(n >= MIN_FIRMS)


# ---------------------------------------------------------------------------
# Time-series statistics on a quarterly outcome series
# ---------------------------------------------------------------------------


def horizon(outcome: str) -> int:
    return int(outcome.rsplit("_k", 1)[1])


def event_count(z: pd.Series, y: pd.Series, sign: int, thr: float = 1.0, center: float = 0.0) -> dict:
    """Share of signal quarters (z > thr) after which sign * (y - center) > 0, against the other quarters."""
    d = pd.DataFrame({"z": z, "y": y}).dropna()
    on = d["z"] > thr
    hit = sign * (d["y"] - center) > 0
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
    """Claim-signed mean of z * (y - mean y) inside each cycle window. Positive = the claim held there."""
    d = pd.DataFrame({"z": z, "y": y}).dropna()
    d["y"] = d["y"] - d["y"].mean()
    out = {}
    for c, (a, b) in CYCLE_WINDOWS.items():
        sel = d[(d.index >= pd.Period(a, "Q")) & (d.index <= pd.Period(b, "Q"))]
        out[c] = float((sign * sel["z"] * sel["y"]).mean()) if len(sel) else float("nan")
    return out


def holm_threshold(alpha: float = 0.05, m: int = N_CLAIMS) -> float:
    """Strictest Holm level: alpha / m. A test that clears it passes whatever the other claims show."""
    return alpha / m


def run_outcome(z: pd.Series, controls: pd.DataFrame, y: pd.Series, name: str, sign: int) -> dict:
    """All time-series statistics for one quarterly outcome series and the pass rule of the decision page."""
    k = horizon(name)
    lag_y = y.shift(k).rename("y_lag")  # the outcome over q-k..q, known at q
    X = pd.concat([z.rename("z"), controls, lag_y], axis=1)
    y = y.reindex(X.index)
    base = X.drop(columns="z")
    claim, hold = X.index <= NOTE_CUT, X.index >= HOLDOUT_START
    reg = {"full": hac_regression(y, X, k), "claim_period": hac_regression(y[claim], X[claim], k),
           "holdout": hac_regression(y[hold], X[hold], k)}
    cw = clark_west(y, base, X, k)
    cyc = cycle_means(z, y, sign)
    center = float(y.median()) if name.startswith("decline") else 0.0
    hb = reg["holdout"]["b"]
    holdout_sign_ok = bool(np.isfinite(hb) and np.sign(hb) == sign)
    n_cycles = sum(v > 0 for v in cyc.values() if np.isfinite(v))
    n_post = sum(cyc[c] > 0 for c in (2015, 2020, 2022) if np.isfinite(cyc[c]))
    passed = holdout_sign_ok and np.isfinite(cw["p"]) and cw["p"] < holm_threshold() and n_cycles >= 3 and n_post >= 2
    return {"outcome": name, "sign_claimed": sign, "horizon_q": k, "events": event_count(z, y, sign, center=center),
            "regression": reg, "clark_west": cw, "cycles": cyc, "holdout_sign_ok": holdout_sign_ok,
            "cycles_as_claimed": int(n_cycles), "post_note_cycles_as_claimed": int(n_post), "pass": bool(passed)}


# ---------------------------------------------------------------------------
# Test C: firm exposures (Fama-MacBeth)
# ---------------------------------------------------------------------------


def past_betas(Y: pd.DataFrame, z: pd.Series, k: int, min_obs: int = 16) -> pd.DataFrame:
    """b_i(q): OLS slope of firm i's outcome on z over quarters t <= q - k (outcomes known at q). No later data."""
    zz = z.reindex(Y.columns)
    M = Y.notna() & zz.notna().to_numpy()[None, :]
    y0 = Y.where(M, 0.0).to_numpy()
    z0 = np.where(M, zz.fillna(0.0).to_numpy()[None, :], 0.0)
    cs = lambda a: np.cumsum(a, axis=1)  # noqa: E731
    n, sz, szz, sy, syz = cs(M.to_numpy().astype(float)), cs(z0), cs(z0 * z0), cs(y0), cs(y0 * z0)
    with np.errstate(invalid="ignore", divide="ignore"):
        b = (syz - sy * sz / n) / (szz - sz * sz / n)
    b = np.where(n >= min_obs, b, np.nan)
    B = pd.DataFrame(b, index=Y.index, columns=Y.columns).shift(k, axis=1)  # at q use data through q - k
    return _winsor(B)


def fama_macbeth(Y: pd.DataFrame, z: pd.Series, k: int, min_firms: int = 100) -> dict:
    """lambda_q = cross-sectional slope of y_iq on b_i(q); then lambda_q on z_q with Newey-West errors (k lags)."""
    B = past_betas(Y, z, k)
    lam = {}
    for q in Y.columns:
        y, b = Y[q], B[q]
        ok = y.notna() & b.notna()
        if ok.sum() < min_firms or b[ok].var() == 0:
            continue
        bc = b[ok] - b[ok].mean()
        lam[q] = float((bc * (y[ok] - y[ok].mean())).sum() / (bc * bc).sum())
    lam = pd.Series(lam)
    out = {"n_quarters": int(len(lam)), "median_firms": int(B.notna().sum()[lam.index].median()) if len(lam) else 0}
    for name, sel in (("full", lam.index == lam.index), ("holdout", lam.index >= HOLDOUT_START)):
        d = pd.concat([lam[sel].rename("lam"), z.rename("z")], axis=1).dropna()
        if len(d) < 20:
            out[name] = {"n": len(d), "coef": np.nan, "t": np.nan}
            continue
        r = sm.OLS(d["lam"], sm.add_constant(d["z"])).fit(cov_type="HAC", cov_kwds={"maxlags": k})
        out[name] = {"n": int(len(d)), "coef": float(r.params["z"]), "t": float(r.tvalues["z"])}
    return out


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def run_claim(cid: str, macro: pd.DataFrame, outcomes: dict, info: pd.DataFrame, hl: pd.DataFrame) -> dict:
    spec = CLAIMS[cid]
    sig_name, transform = spec["signal"]
    z = make_signal(macro, sig_name, transform)
    controls = macro[[c for c in CONTROL_COLS if c != sig_name]]
    res = {"claim": cid, "text": spec["text"], "rows": spec["rows"], "signal": f"{sig_name} ({transform})",
           "robustness_of": spec.get("robustness_of"), "A": [], "A_high_leverage": [], "B": [], "C": []}
    for group, oname, sign in spec["tests"]:
        Y = outcomes[oname]
        rows = group_members(info, group)
        y_all = group_mean(Y, rows)
        res["A"].append({"group": group, "n_firms_median": float(Y.loc[rows.reindex(Y.index, fill_value=False)].notna().sum().median()),
                         **run_outcome(z, controls, y_all, oname, sign)})
        res["A_high_leverage"].append({"group": group, **run_outcome(z, controls, group_mean(Y, rows, hl), oname, sign)})
    for target, comp, oname, sign in spec["relative"]:
        Y = outcomes[oname]
        t_rows = group_members(info, target)
        c_rows = ~t_rows if comp == "rest" else group_members(info, comp)
        diff = group_mean(Y, t_rows) - group_mean(Y, c_rows)
        res["B"].append({"target": target, "comparison": comp, **run_outcome(z, controls, diff, oname, sign)})
    for oname in sorted({o for _, o, _ in spec["tests"]}):
        res["C"].append({"outcome": oname, **fama_macbeth(outcomes[oname], z, horizon(oname))})
    return res


def _line(label: str, o: dict) -> str:
    e, h, c, cw = o["events"], o["regression"]["holdout"], o["regression"]["claim_period"], o["clark_west"]
    return (f"  {label:58s} {o['outcome']:10s} {o['sign_claimed']:+d} | ep {e['n_episodes']:2d} hit {e['episode_hit_rate']:.2f} "
            f"| sig {e['hit_rate_signal']:.2f} oth {e['hit_rate_other']:.2f} | to2011 t {c['t']:+5.2f} | from2012 b "
            f"{h['b']:+.4f} t {h['t']:+5.2f} | CW p {cw['p']:.3f} | cyc {o['cycles_as_claimed']}/4 "
            f"{'PASS' if o['pass'] else 'fail'}")


def print_summary(r: dict) -> None:
    print(f"\n{r['claim']}: {r['text']}  [signal {r['signal']}]")
    for o in r["A"]:
        print(_line(f"A {o['group']} (firms ~{o['n_firms_median']:.0f})", o))
    for o in r["A_high_leverage"]:
        print(_line(f"A-HL {o['group']}", o))
    for o in r["B"]:
        print(_line(f"B {o['target']} minus {o['comparison']}", o))
    for o in r["C"]:
        h = o["holdout"]
        print(f"  C firm exposure {o['outcome']:10s} | firms ~{o['median_firms']} | full coef {o['full']['coef']:+.2f} "
              f"t {o['full']['t']:+5.2f} | from2012 coef {h['coef']:+.2f} t {h['t']:+5.2f}")


def _json_default(x):
    if isinstance(x, (np.floating, float)):
        return None if not np.isfinite(x) else float(x)
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.bool_,)):
        return bool(x)
    return str(x)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--claim", default=None, choices=sorted(CLAIMS))
    a = ap.parse_args()
    macro = build_macro(ROOT / "data/raw/macro")
    W, info = firm_matrices(pd.read_parquet(ROOT / "data/raw/compustat/fundq_nonfin.parquet"))
    outcomes, hl = firm_outcomes(W), high_leverage(W)
    print(f"firms: {len(info)}; firm-quarters with LTM sales > {MIN_LTM_SALES:.0f}m: {int(W['S'].notna().sum().sum())}")
    ids = [a.claim] if a.claim else list(CLAIMS)
    out_dir = ROOT / "data/raw/backtest"
    out_dir.mkdir(parents=True, exist_ok=True)
    for cid in ids:
        r = run_claim(cid, macro, outcomes, info, hl)
        (out_dir / f"wt_firm_{cid}.json").write_text(json.dumps(r, indent=1, default=_json_default))
        print_summary(r)
    print(f"\nwrote {out_dir}/wt_firm_*.json")


if __name__ == "__main__":
    main()
