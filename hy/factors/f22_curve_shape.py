"""F22 Credit curve shape against level, the term premium or "directionless slope" (rank 22). Spec
docs/factors/F22-curve-shape.md; methodology Section 8 (S4 capital structure relative value). Sources: the user's
Credit Factor Framework v0.85 (`Factors/Credit Factor Framework`, same text in `Factor_Model_Related (1).pdf`), PDF
pp. 14 to 15; the Credit RV business plan xls, sheet `Tools`, items 1 to 4 and 7; the Alaph business plan docx,
"Credit Relative Value", Trade Identification. Curvature fit: Elton et al. (2004), eq. 2, PDF p. 5.

    shat_i(T)   = a0 + a1 (1 - e^(-0.4 T)) / (0.4 T)          F06 issuer curve on par-adjusted spreads (imported)
    Sl_i        = shat_i(10) - shat_i(5),  L_i = shat_i(2)      5s10s slope and 2y level (Framework p. 15)
    Sl_i        = alpha_c + beta_c L_i + eps_i                  OLS across issuers, one month, rating class cell c
    score_i     = e_i = Sl_i - alphahat_c - betahat_c L_i       the "directionless slope", z_i = e_i / sigmahat_c
    curvature   = s5 - 0.5 (s2 + s10)                           tent form (our choice; p. 15 writes + 0.5 s2)

Intuition: the slope that the front-end level does not explain pays for the issuer's long end. "Higher TP rankings
... should imply higher returns on duration" (p. 15). Score = +e: long the long end of a curve steep for its level
(our choice of sign; the flag `inverted` keeps the distress reading testable).

No source holds a backtest. The xls hit ratios (0.75 curve trades, 0.9 HY curve roll, sheet `Budget 2009`) are
budget assumptions.

Inputs. The F06 panels: `bond_panel` (required; also `years`, `mod_dur`, `g_spread`), optional `treasury_curve`,
`bond_terms`, `ratings`, `leverage`, `gics`. Without `bond_panel` the result is an empty frame. The source
instrument is the single-name CDS curve. We lack it and build the curve from bonds.
"""

from __future__ import annotations

from typing import Mapping

import numpy as np
import pandas as pd

from hy.backtest import decision_time, eligible
from hy.factors import f06_issuer_curve_residual as f6

TENORS = (2.0, 5.0, 10.0)   # curve points: 2y level, 5s10s slope (Framework p. 15), 2s10s (eq. 1, p. 14)
MIN_BONDS = 3               # bonds a curve needs: "at least 3 different tenors" (xls `Tools`, Curve Tool(s))
MAX_SHORT = 5.0             # the shortest bond matures within 5 years (our choice: keeps s(2) near data)
MIN_LONG = 7.0              # the longest bond has 7 years or more (our choice: keeps s(10) near data)
MIN_NS_BONDS = 4            # bonds the three-term curvature fit needs (our choice: one dof after 3 terms)
MIN_REG = 10                # issuers a regression cell needs, else the pooled fit (our choice)
N_BUCKETS = 5               # spread buckets of the level for z_bucket (our choice; xls item 2)
MIN_BUCKET = 3              # issuers a bucket needs for a z (our choice)
VOL_MONTHS = 12             # months of issuer spread changes for spread_vol (our choice; xls item 4)
VOL_MIN_OBS = 6             # monthly changes spread_vol needs (our choice)
HISTORY = 12                # month ends of own slope history; all required: "at least 1yr of data" (xls `Tools`)
HOLD = 3                    # holding period in months (our choice: no source horizon; readers B-F13, A1-F7)

META = {
    "rank": 22,
    "name": "Credit curve shape against level (term premium)",
    "level": "issuer",
    "horizon_months": HOLD,
    "needs": ["bond_panel", "treasury_curve", "bond_terms", "ratings", "leverage", "gics"],
    "spec": "docs/factors/F22-curve-shape.md",
    "section": "8",
}

COLS = ["date", "gvkey", "score", "available_at", "status", "seniority", "n_bonds", "min_years", "max_years", "s2",
        "s5", "s10", "level", "slope", "slope_2s10s", "curvature", "beta", "reg_cell", "resid", "z", "z_bucket",
        "spread_vol", "resid_vol", "z_own", "inverted", "long_cusip", "short_cusip", "hedge_ratio"]


# ---------------------------------------------------------------- formula helpers


def tenor_spreads(a0: float, a1: float, tenors=TENORS, lam: float = f6.SHOCK_LAMBDA) -> np.ndarray:
    """Fitted spread shat(T) = a0 + a1 x(T) at each tenor, x the F06 shock basis (spec Section 3; JPM p. 22)."""
    return a0 + a1 * f6.shock_basis(np.asarray(tenors, dtype=float), lam)


def curvature(s2: float, s5: float, s10: float, form: str = "tent") -> float:
    """Fly of the curve (spec Section 3). "tent": s5 - 0.5 (s2 + s10), our choice. "as_written": s5 - 0.5 s10 +
    0.5 s2 (Framework p. 15). Intuition: the belly against the wings, a control for PC3."""
    if form == "as_written":
        return s5 - 0.5 * s10 + 0.5 * s2
    return s5 - 0.5 * (s2 + s10)


def ns_curvature(T: np.ndarray, s: np.ndarray, form: str = "tent", lam: float = f6.SHOCK_LAMBDA) -> float:
    """Curvature of a Nelson-Siegel fit s = a0 + a1 x(T) + a2 (x(T) - e^(-lam T)) (Elton et al. eq. 2, p. 5).

    lam is the F06 value, so the fit is OLS. Needs MIN_NS_BONDS bonds and a full-rank design, else NaN. Intuition:
    the two-term F06 curve has no free hump, so its fly is a fixed multiple of its slope."""
    T, s = np.asarray(T, dtype=float), np.asarray(s, dtype=float)
    if len(s) < MIN_NS_BONDS:
        return np.nan
    x = f6.shock_basis(T, lam)
    X = np.column_stack([np.ones_like(x), x, x - np.exp(-lam * T)])
    if np.linalg.matrix_rank(X) < 3:
        return np.nan
    coef, *_ = np.linalg.lstsq(X, s, rcond=None)
    xt = f6.shock_basis(np.asarray(TENORS), lam)
    fit = coef[0] + coef[1] * xt + coef[2] * (xt - np.exp(-lam * np.asarray(TENORS)))
    return curvature(*fit, form=form)


def _fit(y: np.ndarray, X: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
    """OLS of y on X (X holds the constant). Returns coefficients, residuals and the residual standard error."""
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    e = y - X @ coef
    dof = len(y) - X.shape[1]
    return coef, e, float(np.sqrt(np.sum(e ** 2) / dof)) if dof > 0 else np.nan


def slope_residual(slope, level, cell=None, controls=None, min_n: int = MIN_REG) -> pd.DataFrame:
    """Cross-section OLS Sl = alpha_c + beta_c L (+ controls) + eps per cell c (spec Section 3; Framework p. 15).

    A cell with fewer than `min_n` issuers takes the pooled fit over all issuers. Fewer than `min_n` in total: NaN.
    Returns `resid`, `z` (resid over the cell standard error), `beta`, `reg_cell`. Intuition: the slope that the
    level does not explain."""
    sl = pd.Series(np.asarray(slope, dtype=float))
    lv = pd.Series(np.asarray(level, dtype=float))
    cl = pd.Series(list(cell) if cell is not None else ["all"] * len(sl), dtype=object)
    ct = np.column_stack([np.asarray(c, dtype=float) for c in controls]) if controls else np.empty((len(sl), 0))
    out = pd.DataFrame({"resid": np.nan, "z": np.nan, "beta": np.nan, "reg_cell": None}, index=sl.index)
    ok = sl.notna() & lv.notna() & pd.Series(np.isfinite(ct).all(axis=1) if ct.shape[1] else True, index=sl.index)

    def run(idx, name):
        X = np.column_stack([np.ones(len(idx)), lv[idx].to_numpy(), ct[idx]])
        coef, e, se = _fit(sl[idx].to_numpy(), X)
        return coef, e, se, name

    fits = {}
    if ok.sum() >= min_n:
        fits["pooled"] = run(ok[ok].index.to_numpy(), "pooled")
    for c, g in cl[ok].groupby(cl[ok].astype(str)):
        if len(g) >= min_n and c not in ("None", "nan", "all"):
            fits[c] = run(g.index.to_numpy(), c)
    for i in ok[ok].index:
        key = str(cl[i]) if str(cl[i]) in fits else "pooled"
        if key not in fits:
            continue
        coef, _, se, name = fits[key]
        x = np.concatenate([[1.0, lv[i]], ct[i]])
        e = sl[i] - float(x @ coef)
        out.loc[i, ["resid", "z", "beta", "reg_cell"]] = [e, e / se if se and se > 0 else np.nan, coef[1], name]
    return out


def bucket_z(slope, level, n_buckets: int = N_BUCKETS, min_n: int = MIN_BUCKET) -> np.ndarray:
    """z of the slope within its spread bucket, `n_buckets` quantile buckets of the level (xls `Tools` item 2;
    bucket count our choice). A bucket with fewer than `min_n` issuers gives NaN."""
    d = pd.DataFrame({"sl": np.asarray(slope, dtype=float), "lv": np.asarray(level, dtype=float)})
    ok = d.dropna()
    z = pd.Series(np.nan, index=d.index)
    if len(ok) < min_n:
        return z.to_numpy()
    b = pd.qcut(ok["lv"].rank(method="first"), min(n_buckets, len(ok)), labels=False)
    for _, g in ok.groupby(b):
        if len(g) >= min_n and g["sl"].std(ddof=1) > 0:
            z[g.index] = (g["sl"] - g["sl"].mean()) / g["sl"].std(ddof=1)
    return z.to_numpy()


def own_history_z(current: float, past, min_obs: int = HISTORY) -> float:
    """z of the slope against its own last `min_obs` month ends (xls `Tools` item 7, "1yr of data"). Needs all
    `min_obs` past values. Intuition: steepest or flattest on own history."""
    p = np.asarray(past, dtype=float)
    p = p[np.isfinite(p)]
    if len(p) < min_obs or not np.isfinite(current):
        return np.nan
    sd = float(np.std(p, ddof=1))
    return (current - float(np.mean(p))) / sd if sd > 0 else np.nan


def spread_vol(panel: pd.DataFrame, as_of: pd.Timestamp, months: int = VOL_MONTHS,
               min_obs: int = VOL_MIN_OBS) -> pd.Series:
    """Per gvkey: standard deviation of the monthly change of the issuer median G-spread over the last `months`
    changes (xls `Tools` item 4; window our choice). Fewer than `min_obs` changes gives NaN."""
    start = as_of - pd.offsets.MonthEnd(months)
    p = panel[(pd.to_datetime(panel["date"]) >= start) & (pd.to_datetime(panel["date"]) <= as_of)]
    p = p[eligible(p)]
    m = p.groupby(["gvkey", pd.to_datetime(p["date"])])["g_spread"].median().sort_index()
    ch = m.groupby(level=0).diff().dropna()
    n = ch.groupby(level=0).size()
    sd = ch.groupby(level=0).std(ddof=1)
    return sd.where(n >= min_obs)


def dts_hedge(s_long: float, d_long: float, s_short: float, d_short: float) -> float:
    """Short-end notional per unit of long-end notional for a DTS-neutral curve trade: s_L D_L / (s_S D_S) (spec
    Section 7; docx "duration neutral, beta neutral"; DTS our choice)."""
    den = s_short * d_short
    return s_long * d_long / den if np.isfinite(den) and den > 0 else np.nan


# ---------------------------------------------------------------- panel steps


def _filtered(panels: Mapping[str, pd.DataFrame], dt: pd.Timestamp) -> dict[str, pd.DataFrame]:
    """Every panel cut to `available_at` <= dt once, so the history refits see no later row either."""
    return {k: (v[v["available_at"] <= dt] if v is not None and "available_at" in v else v) for k, v in panels.items()}


def _shapes(panels: Mapping[str, pd.DataFrame], as_of: pd.Timestamp, slope_def: str, curvature_form: str,
            measure: str) -> pd.DataFrame:
    """Curve shape per gvkey at as_of from the F06 bonds (spec build steps 1 to 4)."""
    bonds = f6.compute(panels, as_of, measure=measure)
    if bonds.empty:
        return pd.DataFrame()
    panel = panels["bond_panel"]
    cur = panel[pd.to_datetime(panel["date"]) == as_of].drop_duplicates("cusip", keep="last")
    bonds = bonds.merge(cur[["cusip", "years", "mod_dur"]], on="cusip", how="left")
    ok = bonds[(bonds["status"] == "ok") & np.isfinite(bonds["pas"].astype(float))]
    rows = []
    for g, gb in bonds.groupby("gvkey"):
        row = {"gvkey": g, "status": "no_curve", "n_bonds": 0}
        go = ok[ok["gvkey"] == g]
        if len(go):
            n = go.groupby("seniority").size().sort_index()
            sen = n.idxmax()
            c = go[go["seniority"] == sen].sort_values("years")
            T, s = c["years"].to_numpy(float), c["pas"].to_numpy(float)
            row.update(seniority=sen, n_bonds=len(c), min_years=T.min(), max_years=T.max())
            if len(c) < MIN_BONDS:
                row["status"] = "few_bonds"
            elif T.min() > MAX_SHORT or T.max() < MIN_LONG:
                row["status"] = "short_span"
            else:
                a0, a1, _ = f6._ols(f6.shock_basis(T), s)
                s2, s5, s10 = tenor_spreads(a0, a1)
                lo, hi = c.iloc[0], c.iloc[-1]
                row.update(status="ok", s2=s2, s5=s5, s10=s10, level=s2,
                           slope=(s10 - s5) if slope_def == "5s10s" else (s10 - s2), slope_2s10s=s10 - s2,
                           curvature=ns_curvature(T, s, curvature_form),
                           long_cusip=hi["cusip"], short_cusip=lo["cusip"],
                           hedge_ratio=dts_hedge(hi["pas"], hi["mod_dur"], lo["pas"], lo["mod_dur"]))
        rows.append(row)
    out = pd.DataFrame(rows)
    out["available_at"] = bonds["available_at"].max()
    return out


def compute(panels: Mapping[str, pd.DataFrame], as_of: pd.Timestamp, slope_def: str = "5s10s",
            curvature_form: str = "tent", control_curvature: bool = False, history_months: int = 0,
            measure: str = "pas") -> pd.DataFrame:
    """F22 score per issuer at month end `as_of` (spec Sections 3 and 5; methodology Section 8 S4).

    score = residual of the issuer curve slope on its 2y level across issuers of its rating class. Higher score:
    long the long end against the DTS-hedged short end. `history_months` > 0 refits the past months for z_own."""
    as_of = pd.Timestamp(as_of)
    dt = decision_time(as_of)
    if panels.get("bond_panel") is None or len(panels["bond_panel"]) == 0:
        return pd.DataFrame(columns=COLS)
    fp = _filtered(panels, dt)
    sh = _shapes(fp, as_of, slope_def, curvature_form, measure)
    if sh.empty:
        return pd.DataFrame(columns=COLS)
    for col in COLS:
        if col not in sh:
            sh[col] = None if col in ("reg_cell", "seniority", "long_cusip", "short_cusip") else np.nan
    sh["rclass"] = sh["gvkey"].map(f6._issuer_rating(fp, dt, sh["gvkey"])["rclass"])

    ok = sh["status"] == "ok"
    s = sh[ok]
    reg = slope_residual(s["slope"], s["level"], s["rclass"],
                         controls=[s["curvature"]] if control_curvature else None)
    reg.index = s.index
    sh.loc[ok, ["resid", "z", "beta", "reg_cell"]] = reg[["resid", "z", "beta", "reg_cell"]]
    sh.loc[ok & sh["resid"].isna(), "status"] = "few_issuers"
    sh.loc[ok, "z_bucket"] = bucket_z(s["slope"], s["level"])

    vol = spread_vol(fp["bond_panel"], as_of)
    sh["spread_vol"] = sh["gvkey"].map(vol)
    v = sh[ok & sh["spread_vol"].notna()]
    rv = slope_residual(v["slope"], v["spread_vol"])
    sh.loc[v.index, "resid_vol"] = rv["resid"].to_numpy()

    if history_months > 0:
        past = []
        for k in range(1, history_months + 1):
            p = _shapes(fp, as_of - pd.offsets.MonthEnd(k), slope_def, curvature_form, measure)
            if not p.empty:
                past.append(p.loc[p["status"] == "ok", ["gvkey", "slope"]])
        hist = pd.concat(past) if past else pd.DataFrame(columns=["gvkey", "slope"])
        by = hist.groupby("gvkey")["slope"].apply(list)
        sh["z_own"] = [own_history_z(c, by.get(g, []), min(history_months, HISTORY))
                       for g, c in zip(sh["gvkey"], sh["slope"])]

    sh["inverted"] = (sh["slope_2s10s"] < 0).where(ok)
    sh["score"] = sh["resid"]
    sh["date"] = as_of
    return sh[COLS].reset_index(drop=True)
