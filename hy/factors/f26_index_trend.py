"""F26 HY index time-series trend (rank 26). Spec docs/factors/F26-index-trend.md; methodology Section 8 (S7
replacement candidate) and Section 9.2 (macro overlay, index beta). Source: J.P. Morgan, Kolanovic and Wei (2015),
"Momentum Strategies Across Asset Classes", p. 41 footnote 37 and p. 120 (Credit Europe Crossover Momentum rules).
Variants: SG "FX timing indicators" (2010), eqs. 1 to 4 p. 4, M and N p. 6. "Design and analysis of momentum
trading strategies", eq. 1 p. 4, EMA2 p. 7, eq. 18 and N = 20, 40 p. 11. Pages are printed pages (= PDF pages).

    STA_t = mean(L_t-4 .. L_t),  LTA_t = mean(L_t-49 .. L_t)            5-day and 50-day averages (p. 120 rule 1)
    d_t   = +1 if STA_t >= LTA_t else -1                                crossover (p. 120 rule 2)
    x_t   = clip(x_t-1 + 0.25 d_t, -1, 1)                               exposure in steps of 0.25x, cap 1x (rules 2, 3)
    score = x on the last index business day known at decision_time(as_of)

Intuition: credit spreads trend, and a 0.25 step lets the book react at once but caps the cost of a signal that
does not persist (rule 4).

Level. L_t rises when credit gains (our choice: the source does not say spread or price). With the optional panel
`hy_index_return` (`date`, `excess_return` daily index return over duration-matched Treasuries in decimal,
`available_at`, optional `name`), L_t = prod(1 + r). Else L_t = -spread_t from the required table `hy_index`
(`date`, `available_at`, `spread`, `distress`; wiring 4.5), so tightening = long. `distress` is not used.

Variants (columns, not the score). SG: slope S and curvature C of the M-day average, long if both > 0, short if
both < 0 (p. 4). EMA2: phi_n = (a + b) phi_n-1 - a b phi_n-2 + U_n on U_n = dL_n / sigma_n-1 (pp. 4, 7, 11),
scaled to unit variance under white-noise U (eq. 18 at M = 1).

Evidence is CDS index only: iTraxx Crossover 5Y, live Jan 2012 to Mar 2015, Sharpe 0.97 (p. 120). No cash bond test.
Without a daily level series the result is an empty frame (no panel) or a NaN score with a status (too few rows,
monthly rows, stale rows).
"""

from __future__ import annotations

from typing import Mapping

import numpy as np
import pandas as pd

from hy.backtest import decision_time

KEY = "US_HY"            # value of the `index` key column (spec header)
SHORT = 5                # STA window, index business days (JPM p. 41 fn. 37, p. 120 rule 1)
LONG = 50                # LTA window, index business days (p. 41 fn. 37, p. 120 rule 1)
STEP = 0.25              # exposure change per day (p. 120 rules 2, 3)
CAP = 1.0                # cap of 1x long and 1x short (p. 120 rule 2)
X0 = 0.0                 # start exposure on the first day with an LTA (our choice: the source is silent)
SG_M = 33                # SG slope parameter: best EUR/USD pair (SG p. 6; our choice for credit)
SG_N = 4                 # SG curvature parameter (SG p. 6)
EMA_FAST = 20            # EMA2 fast period N_alpha (Design p. 11)
EMA_SLOW = 40            # EMA2 slow period N_beta (Design p. 11)
VOL_N = 20               # EMA period of squared changes for sigma-hat (Design p. 11)
EMA_MIN_OBS = 3 * EMA_SLOW   # changes before the EMA2 signal counts (our choice: beta^120 ~ 0.05)
MAX_GAP_DAYS = 5         # median calendar gap of the last LONG dates for "daily" (our choice: weekends, holidays)
STALE_DAYS = 7           # last level must be this close to as_of (our choice)
HOLD = 1                 # evaluation horizon in months (our choice: the rule rebalances daily, p. 41)

META = {
    "rank": 26,
    "name": "HY index time-series trend",
    "level": "index",
    "horizon_months": HOLD,
    "needs": ["hy_index", "hy_index_return"],
    "spec": "docs/factors/F26-index-trend.md",
    "section": "8",
}

COLS = ["date", "index", "score", "available_at", "signal_date", "level_source", "n_obs", "sta", "lta",
        "jpm_signal", "sg_slope", "sg_curvature", "sg_position", "ema2_signal", "ema2_position", "status"]


# ---------------------------------------------------------------- formula helpers


def index_level(panels: Mapping[str, pd.DataFrame], dt: pd.Timestamp) -> tuple[pd.Series, pd.Series, str | None]:
    """Level L_t and change dL_t per market date from rows with available_at <= dt (spec build steps 1 and 2).

    `hy_index_return` wins: L = prod(1 + r), dL = r. Else `hy_index`: L = -spread, dL = -d spread (absolute
    changes, Design p. 4). The last vintage per date wins. Returns (L, dL, source); source None when no rows."""
    for name, col in (("hy_index_return", "excess_return"), ("hy_index", "spread")):
        df = panels.get(name)
        if df is None or len(df) == 0:
            continue
        d = df[df["available_at"] <= dt].copy()
        d["date"] = pd.to_datetime(d["date"])
        d = d.sort_values("available_at").drop_duplicates("date", keep="last").sort_values("date")
        s = d.set_index("date")[col].astype(float).dropna()
        if s.empty:
            continue
        if name == "hy_index_return":
            return (1.0 + s).cumprod().rename("level"), s.rename("dlevel"), "excess_return"
        return (-s).rename("level"), (-s).diff().rename("dlevel"), "spread"
    return pd.Series(dtype=float), pd.Series(dtype=float), None


def moving_average(level: pd.Series, n: int) -> pd.Series:
    """Simple n-day average of the last n rows, NaN before n rows (STA n = 5, LTA n = 50; JPM p. 120 rule 1)."""
    return level.rolling(n, min_periods=n).mean()


def crossover_signal(sta: pd.Series, lta: pd.Series) -> pd.Series:
    """d_t = +1 if STA >= LTA, -1 if STA < LTA, NaN where either is NaN (JPM p. 120 rule 2). A tie goes long."""
    d = pd.Series(np.where(sta >= lta, 1.0, -1.0), index=sta.index)
    return d.where(sta.notna() & lta.notna())


def step_exposure(signal: pd.Series, step: float = STEP, cap: float = CAP, x0: float = X0) -> pd.Series:
    """x_t = clip(x_t-1 + step d_t, -cap, cap), starting from x0 before the first valid d (JPM p. 120 rules 2, 3).

    A NaN d keeps the prior x (NaN before the first valid d). Intuition: each day moves the book a quarter of the
    way, so a one-day blip costs one step, not a full flip."""
    out = np.full(len(signal), np.nan)
    x = None
    for i, d in enumerate(signal.to_numpy(float)):
        if np.isfinite(d):
            x = float(np.clip((x0 if x is None else x) + step * d, -cap, cap))
        out[i] = np.nan if x is None else x
    return pd.Series(out, index=signal.index, name="x")


def sg_slope_curvature(level: pd.Series, m: int = SG_M, n: int = SG_N) -> tuple[pd.Series, pd.Series]:
    """SG slope S and curvature C (SG p. 4, eqs. 1 to 4).

    A_t = mean of f_t-M .. f_t (M + 1 points), S_t = A_t - A_t-1, D_t = mean of S_t-N .. S_t, C_t = D_t - D_t-1.
    Identity check (eq. 2): S_t = (f_t - f_t-M-1) / (M + 1). Intuition: first and second derivatives of a smooth
    trend, each smoothed once so the noise does not return."""
    a = level.rolling(m + 1, min_periods=m + 1).mean()
    s = a.diff()
    c = s.rolling(n + 1, min_periods=n + 1).mean().diff()
    return s.rename("sg_slope"), c.rename("sg_curvature")


def sg_position(slope: pd.Series, curvature: pd.Series) -> pd.Series:
    """+1 if S > 0 and C > 0, -1 if S < 0 and C < 0, else 0. NaN where either is NaN (SG p. 4)."""
    pos = np.where((slope > 0) & (curvature > 0), 1.0, np.where((slope < 0) & (curvature < 0), -1.0, 0.0))
    return pd.Series(pos, index=slope.index).where(slope.notna() & curvature.notna())


def risk_adjusted_changes(dlevel: pd.Series, vol_n: int = VOL_N) -> pd.Series:
    """U_n = dL_n / sigma_n-1 (Design eq. 1, p. 4). sigma^2 = EMA of dL^2 with decay 1 - 1/vol_n (p. 11, alpha
    convention p. 7), seeded at the first dL^2 (our choice). U is NaN for the first change and where sigma = 0."""
    dx = dlevel.dropna()
    var = (dx ** 2).ewm(alpha=1.0 / vol_n, adjust=False).mean()
    sd = np.sqrt(var).shift(1)
    return (dx / sd.where(sd > 0)).rename("u")


def ema2_filter(u: pd.Series, n_fast: int = EMA_FAST, n_slow: int = EMA_SLOW) -> pd.Series:
    """EMA2 signal phi_n = sum_j a_j U_n-j, a_j = (a^(j+1) - b^(j+1)) / (a - b), a = 1 - 1/n_fast, b = 1 - 1/n_slow
    (Design p. 7). Run as phi_n = (a + b) phi_n-1 - a b phi_n-2 + U_n from phi = 0. A NaN U adds nothing (our
    choice). Intuition: a double EMA of risk-scaled changes, smooth enough to have a finite path length (p. 8)."""
    a, b = 1.0 - 1.0 / n_fast, 1.0 - 1.0 / n_slow
    p1 = p2 = 0.0
    out = np.empty(len(u))
    for i, x in enumerate(u.to_numpy(float)):
        p1, p2 = (a + b) * p1 - a * b * p2 + (x if np.isfinite(x) else 0.0), p1
        out[i] = p1
    return pd.Series(out, index=u.index, name="phi")


def ema2_unit_sd(n_fast: int = EMA_FAST, n_slow: int = EMA_SLOW) -> float:
    """sqrt(R0), R0 = sum_j a_j^2 = (1 + a b) / ((1 - a b)(1 - a^2)(1 - b^2)) (Design eq. 18 at M = 1, p. 11).
    phi / sqrt(R0) has unit variance when U is white noise with unit variance."""
    a, b = 1.0 - 1.0 / n_fast, 1.0 - 1.0 / n_slow
    return float(np.sqrt((1 + a * b) / ((1 - a * b) * (1 - a ** 2) * (1 - b ** 2))))


# ---------------------------------------------------------------- compute


def _status(level: pd.Series, as_of: pd.Timestamp, long: int) -> str:
    """ok, too_few_obs, not_daily or stale (spec build step 3)."""
    if len(level) < long:
        return "too_few_obs"
    gaps = level.index[-long:].to_series().diff().dt.days.dropna()
    if gaps.median() > MAX_GAP_DAYS:
        return "not_daily"
    if level.index[-1] < as_of - pd.Timedelta(STALE_DAYS, unit="D"):
        return "stale"
    return "ok"


def compute(panels: Mapping[str, pd.DataFrame], as_of: pd.Timestamp, short: int = SHORT, long: int = LONG,
            step: float = STEP, cap: float = CAP, sg_m: int = SG_M, sg_n: int = SG_N, ema_fast: int = EMA_FAST,
            ema_slow: int = EMA_SLOW, vol_n: int = VOL_N) -> pd.DataFrame:
    """One row for index US_HY at as_of (spec build steps 1 to 5). score = the JPM step exposure x on the last
    market date known at decision_time(as_of), in -1 .. 1, NaN unless status is "ok". Empty frame (columns COLS)
    when neither hy_index nor hy_index_return gives a level. Higher score = long the index."""
    as_of = pd.Timestamp(as_of)
    dt = decision_time(as_of)
    level, dlevel, source = index_level(panels, dt)
    if source is None:
        return pd.DataFrame(columns=COLS)
    level = level[level.index <= as_of]
    dlevel = dlevel[dlevel.index <= as_of]
    status = _status(level, as_of, long) if len(level) else "too_few_obs"
    row = dict.fromkeys(COLS, np.nan)
    row.update({"date": as_of, "index": KEY, "available_at": dt, "level_source": source, "n_obs": len(level),
                "status": status, "signal_date": level.index[-1] if len(level) else pd.NaT})
    if status == "ok":
        sta, lta = moving_average(level, short), moving_average(level, long)
        d = crossover_signal(sta, lta)
        s, c = sg_slope_curvature(level, sg_m, sg_n)
        row.update({"score": step_exposure(d, step, cap).iloc[-1], "sta": sta.iloc[-1], "lta": lta.iloc[-1],
                    "jpm_signal": d.iloc[-1], "sg_slope": s.iloc[-1], "sg_curvature": c.iloc[-1],
                    "sg_position": sg_position(s, c).iloc[-1]})
        u = risk_adjusted_changes(dlevel, vol_n)
        if u.notna().sum() >= EMA_MIN_OBS:
            sig = ema2_filter(u, ema_fast, ema_slow).iloc[-1] / ema2_unit_sd(ema_fast, ema_slow)
            row.update({"ema2_signal": sig, "ema2_position": float(np.sign(sig))})
    out = pd.DataFrame([row], columns=COLS)
    num = ["score", "sta", "lta", "jpm_signal", "sg_slope", "sg_curvature", "sg_position", "ema2_signal",
           "ema2_position"]
    return out.astype({k: float for k in num}).astype({"n_obs": "Int64"})
