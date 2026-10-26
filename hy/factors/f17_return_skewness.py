"""F17 Bond return skewness (rank 17). Spec docs/factors/F17-return-skewness.md; methodology Section 8 (a control of
the S1 residual and of the S8 IPCA forecast, not a standalone signal). Source: Kelly, Palhares, Pruitt (2021), "Modeling
Corporate Bond Returns" (KPP), SSRN 3720789, Table A.I item 24 (p. 55). Result: Table I (p. 16), IPCA impact Table IX
(p. 31). Pages are PDF pages.

    r~_i,m   = total_i,m - tsy_i,m                                  one-month credit excess return (p. 14)
    Skew_i,t = sqrt(n(n-1))/(n-2) m3 / m2^(3/2)                     returns ending t-59 .. t, n >= 24 (p. 55)
    score    = -Skew_i,t                                            buy low skew, sell high skew (Sharpe -0.67, p. 16)

Intuition: a bond with a left-skewed history carries crash risk and pays for it. A right-skewed bond is a lottery
and pays less.

Control, not signal. The characteristic loses its significance once the other KPP characteristics enter: IPCA
impact 0.05, not significant (Table IX, p. 31). Use the score as a control column until the production evaluation
passes.

One definition. The skewness is the F01 characteristic `bond_skew`: this module calls `f01.bond_return_history` and
`f01.bond_return_features`, so window (`f01.SKEW_MONTHS` = 60) and minimum (`f01.SKEW_MIN` = 24) cannot drift. The
estimator is pandas rolling skew, the bias-adjusted G1 (spec open question 1).

Inputs. `bond_panel` only. Without it the result is empty (columns COLS). Universe: `f01.screen` at as_of
(eligible, spread 50 to 2000 bp, duration >= 0.25 years, p. 15).
"""

from __future__ import annotations

from typing import Mapping

import numpy as np
import pandas as pd

from hy.backtest import decision_time
from hy.factors.f01_ipca import (SKEW_MIN, SKEW_MONTHS, bond_return_features, bond_return_history, rank_scale,
                                 screen)

HOLD = 1                   # one-month horizon of the managed portfolio returns (p. 14)
FLAT_SD = 1e-12            # window sd at or below this: skew is 0 / 0, so NaN (our choice; pandas returns 0)

META = {
    "rank": 17,
    "name": "Bond return skewness",
    "level": "bond",
    "horizon_months": HOLD,
    "needs": ["bond_panel"],
    "spec": "docs/factors/F17-return-skewness.md",
    "section": "8",
}

COLS = ["date", "cusip", "score", "available_at", "gvkey", "bond_skew", "rank", "n_ret", "bond_vol", "g_spread",
        "mod_dur"]


# ---------------------------------------------------------------- formula helpers


def skew_score(skew: pd.Series) -> pd.Series:
    """score = -Skew (spec section 3). The Table I Sharpe of the skew-weighted portfolio is -0.67 (p. 16), so low
    skew is long. NaN stays NaN. Intuition: pay for crash risk, sell the lottery."""
    return -skew.astype(float)


def skew_history(panel: pd.DataFrame, as_of: pd.Timestamp, dt: pd.Timestamp) -> pd.DataFrame:
    """bond_skew, bond_vol and n_ret per cusip at month end as_of (spec build steps 2 to 4; Table A.I item 24, p. 55).

    `panel` must hold only rows with available_at <= dt. The skew uses the one-month returns r~ that end in the 60
    month ends as_of-59 .. as_of, NaN below 24 (the F01 helpers). n_ret counts those returns. A bond whose window
    returns do not vary has NaN skew: the ratio is 0 / 0."""
    rr = bond_return_history(panel, dt)
    if rr.empty:
        return pd.DataFrame(columns=["bond_skew", "bond_vol", "n_ret"])
    months = pd.date_range(end=as_of, periods=SKEW_MONTHS, freq="ME")
    g = rr[(rr["date"] + pd.offsets.MonthEnd(1)).isin(months)].groupby("cusip")["r_tilde"]
    feats = bond_return_features(rr, months)
    feats = feats[feats["date"] == as_of].set_index("cusip")[["bond_skew", "bond_vol"]]
    out = feats.join(g.size().rename("n_ret"), how="outer")
    flat = g.std(ddof=0).reindex(out.index) <= FLAT_SD
    out["bond_skew"] = out["bond_skew"].astype(float).mask(flat)
    return out


# ---------------------------------------------------------------- compute


def compute(panels: Mapping[str, pd.DataFrame], as_of: pd.Timestamp) -> pd.DataFrame:
    """Skewness score per screened bond at as_of (spec build steps 1 to 6). One row per cusip.

    score = -bond_skew, NaN with fewer than 24 returns or constant returns. rank = bond_skew ranked over the scored
    bonds and mapped to [-0.5, 0.5] (p. 15). Empty frame (columns COLS) without bond_panel. Higher score = long."""
    as_of = pd.Timestamp(as_of) + pd.offsets.MonthEnd(0)
    p = panels.get("bond_panel")
    if p is None or len(p) == 0:
        return pd.DataFrame(columns=COLS)
    dt = decision_time(as_of)
    p = p[p["available_at"] <= dt].copy()
    p["date"] = pd.to_datetime(p["date"])
    p = p[p["date"] <= as_of]

    # universe at as_of (step 5)
    now = p[p["date"] == as_of].drop_duplicates("cusip", keep="last")
    now = now[screen(now)]
    if now.empty:
        return pd.DataFrame(columns=COLS)

    # skewness from the F01 helpers (steps 2 to 4)
    hist = p[p["date"] >= as_of - pd.offsets.MonthEnd(SKEW_MONTHS)]
    out = now[["cusip", "gvkey", "g_spread", "mod_dur"]].set_index("cusip").join(skew_history(hist, as_of, dt))
    out["n_ret"] = out["n_ret"].fillna(0).astype(int)
    out["bond_skew"] = out["bond_skew"].astype(float).where(np.isfinite(out["bond_skew"].astype(float)))

    # score and rank (step 6)
    out = out.reset_index()
    out["date"] = as_of
    out["available_at"] = dt
    out["score"] = skew_score(out["bond_skew"])
    out["rank"] = rank_scale(out, ["bond_skew"])["bond_skew"].where(out["bond_skew"].notna())
    return out[COLS].astype({"score": float, "bond_skew": float, "rank": float, "bond_vol": float}) \
        .reset_index(drop=True)
