"""F11 Change in option implied volatility, ΔImpVOL (rank 11). Spec docs/factors/F11-delta-implied-vol.md;
methodology Section 8 (S6 rating migration: the signal predicts downgrades) and Section 9.1 (event risk). Source:
Cao, Goyal, Xiao, Zhan (2023), Management Science 69(3), pp. 1378-1394. Pages are journal pages.

    CVOL_i,t    = ATM call IV, delta 0.5, 365 days, OptionMetrics volatility surface, month end (p. 1379)
    PVOL_i,t    = ATM put IV, delta -0.5, 365 days, same surface (p. 1379)
    ΔImpVOL_i,t = ((CVOL_t - CVOL_t-1) + (PVOL_t - PVOL_t-1)) / 2                           (p. 1383)
    score_b,t   = -ΔImpVOL_i(b),t, winsorised at 0.5% each tail (Table 1 notes, p. 1379)

Intuition: a bond is a short put on firm assets. A rise in expected volatility lowers the bond value, and bond
prices react late, so a rising IV predicts a low next-month bond return (pp. 1382, 1395).

Timing. The source takes IV one day before the bond price date (p. 1379). Our monthly panel has no per-bond price
date. Our choice: step back SKIP_DAYS IV trading days from the month's last IV date, then take the issuer's latest
row in the WINDOW_DAYS trading days that end there.

Inputs. A new optional panel `option_iv`: `gvkey`, `date` (trading day), `cvol`, `pvol` (decimal implied
volatility), `available_at` (date + 1 day). The export maps OptionMetrics secid to permno to gvkey. `bond_panel` is
required. Optional: `ratings` (extra column `rating_class`) and `equity_monthly` (extra column `lag_stock_ret`, the
stock return over month t: the control of Table 5, p. 1387). Without `option_iv` or `bond_panel` the result is an
empty frame. No proxy replaces the option data.
"""

from __future__ import annotations

from typing import Mapping

import numpy as np
import pandas as pd

from hy.backtest import decision_time, eligible
from hy.peers import equity_momentum, rating_at

SKIP_DAYS = 1        # IV trading days skipped before the month's last IV date (p. 1379: one day)
WINDOW_DAYS = 5      # IV trading days searched for the issuer's month-end row (our choice: the bond rule, p. 1378)
WINSOR = 0.005       # tail share clipped each side of the cross-section (Table 1 notes, p. 1379)
HOLD = 1             # months held: one month, monthly rebalance (p. 1380)

META = {
    "rank": 11,
    "name": "Change in option implied volatility (ΔImpVOL)",
    "level": "bond",
    "horizon_months": HOLD,
    "needs": ["bond_panel", "option_iv", "ratings", "equity_monthly"],
    "spec": "docs/factors/F11-delta-implied-vol.md",
    "section": "8",
}
REQUIRED = ("bond_panel", "option_iv")   # ratings and equity_monthly only fill extra columns

IV_COLS = ["gvkey", "cvol", "pvol", "iv_date"]
CHANGE_COLS = ["gvkey", "d_cvol", "d_pvol", "d_impvol", "impvol"]
COLS = ["date", "cusip", "score", "available_at", "gvkey", "d_cvol", "d_pvol", "d_impvol", "impvol", "rating_class",
        "lag_stock_ret"]


def month_end_iv(iv: pd.DataFrame, month_end: pd.Timestamp, skip_days: int = SKIP_DAYS,
                 window_days: int = WINDOW_DAYS) -> pd.DataFrame:
    """Month-end CVOL and PVOL per gvkey (spec build step 3; p. 1379, one-day skip).

    The IV trading days of the month are the distinct `date` values of `iv` in that month. Drop the last
    `skip_days` of them. Take the issuer's latest row with both cvol and pvol in the last `window_days` days that
    remain. An issuer without such a row has no month-end IV. `iv` must already pass the available_at filter.
    Columns IV_COLS."""
    month = pd.Timestamp(month_end).to_period("M")
    d = pd.to_datetime(iv["date"])
    m = iv[d.dt.to_period("M") == month].assign(date=d[d.dt.to_period("M") == month])
    days = np.sort(m["date"].unique())
    end = len(days) - skip_days
    if end <= 0:
        return pd.DataFrame(columns=IV_COLS)
    win = days[max(0, end - window_days):end]
    m = m[m["date"].isin(win)].dropna(subset=["cvol", "pvol"])
    m = m.sort_values(["date", "available_at"]).drop_duplicates("gvkey", keep="last")
    return m.rename(columns={"date": "iv_date"})[IV_COLS].reset_index(drop=True)


def iv_change(cur: pd.DataFrame, prev: pd.DataFrame) -> pd.DataFrame:
    """ΔCVOL, ΔPVOL, ΔImpVOL = (ΔCVOL + ΔPVOL)/2 and the level ImpVOL = (CVOL + PVOL)/2 at t (pp. 1379, 1383).

    One row per gvkey in `cur` or `prev`. NaN where either month is missing. Intuition: the common part of the
    call and put change is news about risk. Their difference is directional news and does not predict (p. 1382)."""
    j = cur.merge(prev, on="gvkey", how="outer", suffixes=("", "_prev"))
    d_c = j["cvol"].astype(float) - j["cvol_prev"].astype(float)
    d_p = j["pvol"].astype(float) - j["pvol_prev"].astype(float)
    return pd.DataFrame({"gvkey": j["gvkey"], "d_cvol": d_c, "d_pvol": d_p, "d_impvol": 0.5 * (d_c + d_p),
                         "impvol": 0.5 * (j["cvol"].astype(float) + j["pvol"].astype(float))})[CHANGE_COLS]


def winsorise(x: pd.Series, q: float = WINSOR) -> pd.Series:
    """Clip `x` at its q and 1-q cross-sectional quantiles, NaN kept (Table 1 notes, p. 1379: 0.5% each month)."""
    if x.notna().sum() == 0 or q <= 0:
        return x.astype(float)
    lo, hi = np.nanquantile(x.to_numpy(float), [q, 1.0 - q])
    return x.astype(float).clip(lo, hi)


def compute(panels: Mapping[str, pd.DataFrame], as_of: pd.Timestamp, skip_days: int = SKIP_DAYS,
            window_days: int = WINDOW_DAYS, winsor: float = WINSOR) -> pd.DataFrame:
    """-ΔImpVOL per eligible bond of bond_panel at as_of (spec build steps 2 to 6). One row per cusip. The issuer
    value goes to every bond of the issuer. score NaN where the issuer has no IV change. Empty frame (columns COLS)
    when option_iv or bond_panel is missing. Higher score = long (a falling IV)."""
    as_of = pd.Timestamp(as_of)
    if any(panels.get(k) is None or len(panels[k]) == 0 for k in REQUIRED):
        return pd.DataFrame(columns=COLS)
    dt = decision_time(as_of)
    iv = panels["option_iv"]
    iv = iv[(iv["available_at"] <= dt) & (pd.to_datetime(iv["date"]) <= as_of)]
    prev_end = as_of + pd.offsets.MonthEnd(0) - pd.offsets.MonthEnd(1)
    chg = iv_change(month_end_iv(iv, as_of, skip_days, window_days), month_end_iv(iv, prev_end, skip_days, window_days))
    p = panels["bond_panel"]
    p = p[(p["available_at"] <= dt) & (pd.to_datetime(p["date"]) == as_of)]
    p = p[eligible(p) & p["gvkey"].notna()].drop_duplicates("cusip", keep="last")
    if p.empty:
        return pd.DataFrame(columns=COLS)
    out = p[["cusip", "gvkey"]].merge(chg, on="gvkey", how="left")
    out["score"] = -winsorise(out["d_impvol"], winsor)
    r = panels.get("ratings")
    out["rating_class"] = out["gvkey"].map(rating_at(r, dt)) if r is not None and len(r) else None
    e = panels.get("equity_monthly")
    out["lag_stock_ret"] = out["gvkey"].map(equity_momentum(e, as_of, dt, months=1)) if e is not None and len(e) \
        else np.nan
    out["date"] = as_of
    out["available_at"] = dt
    return out[COLS].astype({"score": float, "lag_stock_ret": float}).reset_index(drop=True)
