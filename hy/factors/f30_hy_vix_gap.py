"""F30 HY spread against VIX gap (rank 30). Spec docs/factors/F30-hy-vix-gap.md; methodology Section 8 (S7
replacement candidate) and Section 3.6 (macro inputs). Source: CARV Quantitative Strategies, "HY vs VIX Stnd Perf"
screen, pricing date 2011-10-06, file HY_VIX (2).pdf: scatter of CDX HY on the VIX level with an OLS line per window
(1M and 3M p. 1, 6M p. 2, 12M and 24M p. 3), and Z = (Last - Mean) / StdDev per series (12M table p. 3).

    s_d     = a_t + b_t VIX_d + e_d,   d in (t - 12 months, t]       OLS of the index spread on the VIX level (p. 3)
    gap_t   = s_t - (a_t + b_t VIX_t)                                 spread above the VIX line
    score   = gap_t / sd(e),  sd with the n - 2 divisor              residual z-score (our choice of scale)
    z_gap   = z(s_t) - z(VIX_t) over the same window                  reader-block form, a column only

Intuition: equity volatility prices the common risk, so a spread above the VIX line is credit cheap against
equity. Positive score = long HY (our choice: the source states no direction).

Inputs. `hy_index` (`date`, `available_at`, `spread` decimal; wiring 4.5) and the optional long panel `macro_series`
(`series_id`, `date`, `value`, `available_at`; the schema of F25 section 4) with series_id "VIXCLS" (CBOE VIX close,
index points, public date + 1 day). Without either panel, or without VIXCLS rows, the result is an empty frame.

The source is a one-day screen. It has no backtest, no rule and no return result. Window, minimum count, sign and
horizon are our choices.
"""

from __future__ import annotations

from typing import Mapping

import numpy as np
import pandas as pd

from hy.backtest import decision_time

KEY = "US_HY"            # value of the `index` key column (spec header)
VIX_ID = "VIXCLS"        # series_id of the VIX close in `macro_series` (F25 section 4)
WINDOW_MONTHS = 12       # regression window in calendar months (source shows 1, 3, 6, 12, 24; our choice 12)
MIN_OBS = 120            # matched daily dates the fit needs (our choice: about half of a 12-month window)
STALE_DAYS = 7           # last matched date must be this close to as_of (our choice, as F26)
RESID_DDOF = 2           # residual sd divisor n - 2, the OLS standard error (our choice: the source is silent)
Z_DDOF = 1               # sample sd for z(spread) and z(VIX) (our choice: p. 3 rounding cannot tell the divisor)
HOLD = 3                 # evaluation horizon in months (reader block A1-F16; the source gives none)

META = {
    "rank": 30,
    "name": "HY spread against VIX gap",
    "level": "index",
    "horizon_months": HOLD,
    "needs": ["hy_index", "macro_series"],
    "spec": "docs/factors/F30-hy-vix-gap.md",
    "section": "8",
}

COLS = ["date", "index", "score", "available_at", "signal_date", "n_obs", "spread", "vix", "alpha", "beta", "r2",
        "fitted", "gap", "resid_sd", "z_spread", "z_vix", "z_gap", "status"]


# ---------------------------------------------------------------- formula helpers


def _last_vintage(df: pd.DataFrame, col: str, dt: pd.Timestamp, as_of: pd.Timestamp) -> pd.Series:
    """Series `col` by date from rows with available_at <= dt and date <= as_of. Last vintage per date wins."""
    d = df[df["available_at"] <= dt].copy()
    d["date"] = pd.to_datetime(d["date"])
    d = d[d["date"] <= as_of].sort_values("available_at").drop_duplicates("date", keep="last")
    return d.set_index("date")[col].astype(float).dropna().sort_index()


def matched_series(panels: Mapping[str, pd.DataFrame], as_of: pd.Timestamp, dt: pd.Timestamp) -> pd.DataFrame | None:
    """Spread and VIX on common dates (spec build steps 1 and 2). Columns `spread`, `vix`, index `date`.

    None when `hy_index` or `macro_series` is missing, or when no VIXCLS row is known at dt."""
    hy, macro = panels.get("hy_index"), panels.get("macro_series")
    if hy is None or len(hy) == 0 or macro is None or len(macro) == 0:
        return None
    vix = macro[macro["series_id"] == VIX_ID]
    if vix.empty:
        return None
    s, v = _last_vintage(hy, "spread", dt, as_of), _last_vintage(vix, "value", dt, as_of)
    if v.empty:
        return None
    return pd.concat([s.rename("spread"), v.rename("vix")], axis=1, join="inner")


def ols_fit(x: np.ndarray, y: np.ndarray, ddof: int = RESID_DDOF) -> tuple[float, float, float, float]:
    """OLS y = a + b x. Returns (a, b, R2, residual sd with divisor n - ddof) (spec definition; the source's
    "Y = a + b X; R2" label, p. 3). b = cov(x, y) / var(x), a = mean(y) - b mean(x). NaN when var(x) = 0."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    xm, ym = x.mean(), y.mean()
    sxx = ((x - xm) ** 2).sum()
    if len(x) <= ddof or sxx <= 0:
        return np.nan, np.nan, np.nan, np.nan
    b = ((x - xm) * (y - ym)).sum() / sxx
    a = ym - b * xm
    e = y - a - b * x
    syy = ((y - ym) ** 2).sum()
    r2 = 1.0 - (e ** 2).sum() / syy if syy > 0 else np.nan
    return float(a), float(b), float(r2), float(np.sqrt((e ** 2).sum() / (len(x) - ddof)))


def regression_gap(spread: float, vix: float, alpha: float, beta: float) -> tuple[float, float]:
    """Fitted spread a + b VIX and gap = spread - fitted (spec definition). Source 12M (p. 3): 221.51 + 12.5889 x
    40.82 = 735.39 bp, gap 863.70 - 735.39 = 128.31 bp."""
    fitted = alpha + beta * vix
    return float(fitted), float(spread - fitted)


def window_z(series: pd.Series, ddof: int = Z_DDOF) -> float:
    """z of the last value against the window: (Last - Mean) / StdDev (screen tables, p. 3: CDX HY (863.70 -
    493.91) / 100.72 = 3.67). NaN when the sd is 0 or the series is too short."""
    s = series.dropna()
    if len(s) <= ddof:
        return np.nan
    sd = s.std(ddof=ddof)
    return float((s.iloc[-1] - s.mean()) / sd) if sd > 0 else np.nan


# ---------------------------------------------------------------- compute


def _status(m: pd.DataFrame, as_of: pd.Timestamp, min_obs: int) -> str:
    """ok, too_few_obs or stale (spec build step 3)."""
    if len(m) < min_obs:
        return "too_few_obs"
    if m.index[-1] < as_of - pd.Timedelta(STALE_DAYS, unit="D"):
        return "stale"
    return "ok"


def compute(panels: Mapping[str, pd.DataFrame], as_of: pd.Timestamp, window_months: int = WINDOW_MONTHS,
            min_obs: int = MIN_OBS) -> pd.DataFrame:
    """One row for index US_HY at as_of (spec build steps 1 to 5). score = residual of the last matched date over
    the residual sd of a window_months OLS of spread on VIX, NaN unless status is "ok". Empty frame (columns COLS)
    when hy_index, macro_series or the VIXCLS rows are missing. Higher score = long the index."""
    as_of = pd.Timestamp(as_of)
    dt = decision_time(as_of)
    m = matched_series(panels, as_of, dt)
    if m is None:
        return pd.DataFrame(columns=COLS)
    m = m[m.index > as_of - pd.DateOffset(months=window_months)]
    status = _status(m, as_of, min_obs)
    row = dict.fromkeys(COLS, np.nan)
    row.update({"date": as_of, "index": KEY, "available_at": dt, "n_obs": len(m), "status": status,
                "signal_date": m.index[-1] if len(m) else pd.NaT})
    if status == "ok":
        a, b, r2, sd = ols_fit(m["vix"].to_numpy(), m["spread"].to_numpy())
        s_t, v_t = float(m["spread"].iloc[-1]), float(m["vix"].iloc[-1])
        fitted, gap = regression_gap(s_t, v_t, a, b)
        zs, zv = window_z(m["spread"]), window_z(m["vix"])
        row.update({"score": gap / sd if sd > 0 else np.nan, "spread": s_t, "vix": v_t, "alpha": a, "beta": b,
                    "r2": r2, "fitted": fitted, "gap": gap, "resid_sd": sd, "z_spread": zs, "z_vix": zv,
                    "z_gap": zs - zv})
    out = pd.DataFrame([row], columns=COLS)
    num = ["score", "spread", "vix", "alpha", "beta", "r2", "fitted", "gap", "resid_sd", "z_spread", "z_vix", "z_gap"]
    return out.astype({k: float for k in num}).astype({"n_obs": "Int64"})
