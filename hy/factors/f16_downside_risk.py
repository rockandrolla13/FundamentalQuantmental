"""F16 Bond downside risk, 5% VaR (rank 16). Spec docs/factors/F16-downside-risk.md; methodology Section 8 (a risk
leg and a control of the S1 residual). Source: Bali, Goyal, Huang, Jiang and Wen (2022), SFI RP 20-110, Appendix B
items 6 to 9 (printed pp. 29 to 30), eq. 18 (printed p. 11). The measure is Bai, Bali and Wen (2019, JFE). That paper
is not in the folder: this module uses the definition as Bali et al. state it.

    r_i,m    = total_i,m - tsy_i,m                         monthly excess over the duration-matched Treasury
    k        = max(1, floor(q n + 0.5))                    k = 2 (q = 5%) and k = 4 (q = 10%) at n = 36
    VaR_q,iT = -r_i,(k)                                    k-th lowest of months T-35 .. T, sign flipped (p. 29)
    ES_q,iT  = -mean(r_i,(1) .. r_i,(k))                   mean of the k lowest, sign flipped (pp. 29 to 30)
    var5_ctrl = VaR5 - X b,  X = [1, rating dummies, mod_dur, S1 z, z missing]   cross-sectional OLS residual

Intuition: a bond that lost a lot in its bad months carries tail risk, and a holder asks a premium for it. The
control removes the part of that risk which the rating class, the duration and the S1 mispricing already explain.

Inputs. `bond_panel` and `ratings` are required. `leverage` is optional (implied class where no S&P rating is on
file). A new optional panel `s1_residual` (`date` month end, `cusip`, `z` the Section 7.3 residual, `available_at`)
adds z to the control. Without it the control is rating and duration only (column `ctrl`). Without `bond_panel` or
`ratings` the result is empty (columns COLS).

Returns. r_i,m reuses `f04.monthly_excess_returns` (beta 0). Stale and carried rows drop out. Only pairs of
consecutive month ends count (MAX_GAP = 1): a k-month return is not a monthly return.

Score. Percentile rank of var5_ctrl across the month's scored bonds, then `signals.standardise_by_date`. Higher VaR
means a higher expected return (Bali et al. footnote 17, p. 29). The columns var5, var10, es5 and es10 hold the raw
measures for the Fama-MacBeth test of the spec.
"""

from __future__ import annotations

from typing import Mapping

import numpy as np
import pandas as pd

from hy.backtest import MIN_BONDS, decision_time, eligible
from hy.factors.f04_bond_momentum import (DEFAULT_SYMBOLS, HY_CLASSES, monthly_excess_returns, rating_classes,
                                          vol_observations)
from hy.signals import neutralise, standardise_by_date

WINDOW = 36                # months T-35 .. T (Bali et al. items 6 to 9, p. 29)
MIN_OBS = 24               # fewest monthly returns a score needs (our choice, after item 34, p. 34: "24 to 36 months")
MAX_GAP = 1                # longest pair in months (our choice: monthly returns only)
Q5, Q10 = 0.05, 0.10       # tail shares: second and fourth lowest of 36 (p. 29)
HOLD = 1                   # one-month-ahead horizon (Bali et al. p. 16)
MIN_XS = MIN_BONDS         # fewest scored bonds for the control regression (hy.backtest, our choice)

META = {
    "rank": 16,
    "name": "Bond downside risk (5% VaR)",
    "level": "bond",
    "horizon_months": HOLD,
    "needs": ["bond_panel", "ratings", "leverage", "s1_residual"],
    "spec": "docs/factors/F16-downside-risk.md",
    "section": "8",
}
REQUIRED = ("bond_panel", "ratings")

COLS = ["date", "cusip", "score", "available_at", "gvkey", "var5", "var10", "es5", "es10", "var5_ctrl", "n_ret",
        "ctrl", "rclass", "g_spread", "mod_dur", "s1_z"]


# ---------------------------------------------------------------- formula helpers


def tail_count(n: int, q: float) -> int:
    """k = max(1, floor(q n + 0.5)), the rank of the VaR observation (spec section 3, our choice). It gives the source
    ranks at n = 36: k = 2 for q = 5% and k = 4 for q = 10% (p. 29). Intuition: keep the tail share near q."""
    return max(1, int(np.floor(q * n + 0.5)))


def value_at_risk(r: np.ndarray, q: float = Q5) -> float:
    """VaR_q = -(k-th lowest return), k = tail_count(n, q) (Bali et al. items 6 and 7, p. 29). NaN without data.
    Intuition: the loss of a bad month that comes about once in 1 / q months, as a positive number."""
    x = np.sort(np.asarray(r, float)[np.isfinite(np.asarray(r, float))])
    if not len(x):
        return np.nan
    return float(-x[tail_count(len(x), q) - 1])


def expected_shortfall(r: np.ndarray, q: float = Q5) -> float:
    """ES_q = -mean of the k lowest returns, k = tail_count(n, q) (Bali et al. items 8 and 9, pp. 29 to 30). The
    sign flip is our choice, so a higher ES means more downside. Intuition: the mean loss inside the tail."""
    x = np.sort(np.asarray(r, float)[np.isfinite(np.asarray(r, float))])
    if not len(x):
        return np.nan
    return float(-x[: tail_count(len(x), q)].mean())


def tail_measures(pairs: pd.DataFrame, months: pd.DatetimeIndex, min_obs: int = MIN_OBS) -> pd.DataFrame:
    """VaR5, VaR10, ES5, ES10 and n per cusip from the monthly r_ex pairs whose end month lies in `months` (spec build
    step 4). A pair longer than one month enters as r_ex / sqrt(gap_k) (`f04.vol_observations`). A bond with fewer
    than `min_obs` returns has NaN measures. Columns var5, var10, es5, es10, n_ret."""
    p = pairs[pairs["r_ex"].notna() & pairs["date"].isin(months)]
    obs = vol_observations(p, "r_ex") if len(p) else pd.Series(dtype=float)
    rows = {}
    for cusip, r in obs.groupby(p["cusip"]):
        x = r.to_numpy(float)
        ok = len(x) >= min_obs
        rows[cusip] = {"var5": value_at_risk(x, Q5) if ok else np.nan, "var10": value_at_risk(x, Q10) if ok else np.nan,
                       "es5": expected_shortfall(x, Q5) if ok else np.nan,
                       "es10": expected_shortfall(x, Q10) if ok else np.nan, "n_ret": len(x)}
    out = pd.DataFrame.from_dict(rows, orient="index", columns=["var5", "var10", "es5", "es10", "n_ret"])
    return out.astype({"n_ret": int}) if len(out) else out


def control_residual(y: pd.Series, rclass: pd.Series, mod_dur: pd.Series, z: pd.Series | None = None,
                     min_n: int = MIN_XS) -> pd.Series:
    """OLS residual of y on [1, rating class dummies, mod_dur, z, z missing] across one date (spec section 3; Section
    8 `signals.neutralise`). Without z the control is rating and duration. A missing z enters as 0 with the flag 1.
    Fewer than `min_n` rows with y gives NaN. Intuition: keep the tail risk that rating, duration and S1 miss."""
    ok = y.notna() & rclass.notna() & mod_dur.notna()
    out = pd.Series(np.nan, index=y.index, name="var5_ctrl")
    if ok.sum() < min_n:
        return out
    X = pd.get_dummies(rclass[ok].astype(str), drop_first=True, dtype=float)
    X["mod_dur"] = mod_dur[ok].astype(float)
    if z is not None:
        zz = z.reindex(y.index)[ok].astype(float)
        X["z"] = zz.fillna(0.0)
        if zz.isna().any():
            X["z_missing"] = zz.isna().astype(float)
    X = X.loc[:, X.std(ddof=0) > 0]                       # a constant column adds nothing to the intercept
    out[ok] = neutralise(y[ok].to_numpy(float), X.to_numpy(float)) if X.shape[1] else \
        y[ok].to_numpy(float) - y[ok].mean()
    return out


def _s1_at(s1: pd.DataFrame | None, as_of: pd.Timestamp, dt: pd.Timestamp) -> pd.Series | None:
    """S1 z per cusip at month end as_of, known at dt. None without the panel or without a row known at dt."""
    if s1 is None or not len(s1):
        return None
    s = s1[(s1["available_at"] <= dt) & (pd.to_datetime(s1["date"]) == as_of)]
    if s.empty:
        return None
    return s.sort_values("available_at").drop_duplicates("cusip", keep="last").set_index("cusip")["z"].astype(float)


# ---------------------------------------------------------------- compute


def compute(panels: Mapping[str, pd.DataFrame], as_of: pd.Timestamp, window: int = WINDOW, min_obs: int = MIN_OBS,
            max_gap: int = MAX_GAP) -> pd.DataFrame:
    """Downside risk score per bond of the HY universe at as_of (spec build steps 1 to 6). One row per cusip.

    Universe: an `eligible` row at as_of with a yield, rating class BB, B or CCC, and a raw S&P symbol other than
    D or SD (the F04 rule). score = standardised percentile rank of var5_ctrl, NaN where var5_ctrl is NaN. Empty
    frame (columns COLS) without bond_panel or ratings. Higher score = long."""
    as_of = pd.Timestamp(as_of) + pd.offsets.MonthEnd(0)
    if any(panels.get(k) is None or len(panels[k]) == 0 for k in REQUIRED):
        return pd.DataFrame(columns=COLS)
    dt = decision_time(as_of)
    p = panels["bond_panel"]
    p = p[p["available_at"] <= dt].copy()
    p["date"] = pd.to_datetime(p["date"])

    # universe at as_of (step 2)
    now = p[p["date"] == as_of].drop_duplicates("cusip", keep="last")
    now = now[eligible(now) & now["yield"].notna() & now["gvkey"].notna()]
    cls = rating_classes(panels["ratings"], panels.get("leverage"), as_of)
    now = now.assign(rclass=now["gvkey"].map(cls["rclass"]), raw=now["gvkey"].map(cls["raw"]))
    now = now[now["rclass"].isin(HY_CLASSES) & ~now["raw"].isin(DEFAULT_SYMBOLS)]
    if now.empty:
        return pd.DataFrame(columns=COLS)

    # monthly excess returns of months T-35 .. T (step 3)
    months = pd.date_range(end=as_of, periods=window, freq="ME")
    hist = p[(p["date"] >= months[0] - pd.offsets.MonthEnd(max_gap)) & (p["date"] <= as_of)]
    pairs = monthly_excess_returns(hist, dt, max_gap)

    # tail measures (step 4) and the control (step 5)
    out = now[["cusip", "gvkey", "rclass", "g_spread", "mod_dur"]].set_index("cusip")
    out = out.join(tail_measures(pairs, months, min_obs))
    out["n_ret"] = out["n_ret"].fillna(0).astype(int)
    z = _s1_at(panels.get("s1_residual"), as_of, dt)
    out["s1_z"] = z.reindex(out.index) if z is not None else np.nan
    out["ctrl"] = "rating+dur+s1" if z is not None else "rating+dur"
    out["var5_ctrl"] = control_residual(out["var5"], out["rclass"], out["mod_dur"], z)

    # rank, standardise (step 6)
    out = out.reset_index()
    out["date"] = as_of
    out["available_at"] = dt
    out["score"] = out["var5_ctrl"].rank(pct=True)
    out = standardise_by_date(out, ["score"])
    out["score"] = out["score"].where(out["var5_ctrl"].notna())
    return out[COLS].astype({"score": float, "var5": float, "var5_ctrl": float, "s1_z": float}).reset_index(drop=True)
