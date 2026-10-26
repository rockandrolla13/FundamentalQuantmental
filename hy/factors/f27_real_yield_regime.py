"""F27 Real-yield shock regime, with the spread-rate correlation regime (rank 27). Spec
docs/factors/F27-real-yield-regime.md; methodology Section 9.2 (the Treasury forecast needs a split) and Section 8
(S7 replacement candidate). Sources, PDF pages, all Deutsche Bank 2021: Reid "Yields & Credit Spreads" pp. 1, 3, 5;
Jezek "Macro Credit Brief" pp. 2 to 4; Nicol "Short dated BBs attractive" pp. 2 to 4 (repeated in "Global Leveraged
Finance Weekly" pp. 5 to 6); Credit Derivatives Strategy 1 Mar 2021 pp. 4 to 5.

    dy = y_t - y_t-h,  dr = r_t - r_t-h,  dpi = pi_t - pi_t-h,  h = 3 months    10y nominal, TIPS real, breakeven
    regime = inflation_selloff  if dy >= k and dpi > dr                          score +1 (Reid p. 1, Nicol p. 3)
             real_selloff       if dy >= k and dr >= dpi                         score -1 (Reid pp. 1, 3)
             rally              if dy <= -k                                      score -1 (Nicol p. 2)
             neutral            otherwise                                        score  0
    split_signal = -(dr / sd(dr) - dpi / sd(dpi))                                variant of reader F-F1
    rho = corr(d spread, d y5) over 12 weekly changes                            conditioner (Nicol p. 2)

Intuition: a rise in yields from growth and inflation expectations helps leveraged issuers, while a rise in real
yields raises their funding cost. No source tests the real-against-breakeven split: it rests on rolling-correlation
charts (Reid pp. 3, 5). Nicol p. 3 and Jezek p. 3 read a real-led rise as growth, the opposite sign.

Inputs. A new optional long panel `macro_series` (`series_id`, `date`, `value` in FRED percent, `available_at`;
the F25 schema) with DGS10, DFII10 (required), T10YIE, DGS5, BAMLH0A0HYM2, BAMLH0A1HYBB, BAMLH0A2HYB, BAMLH0A3HYC
(optional). The production `hy_index` (`date`, `spread` decimal, `available_at`) feeds the correlation first.
Without `macro_series` the result is an empty frame. Without DGS10 or DFII10 the score is NaN with a status.
"""

from __future__ import annotations

from typing import Mapping

import numpy as np
import pandas as pd

from hy.backtest import decision_time

KEY = "US_HY"            # value of the `index` key column (spec header)
NOMINAL, REAL, BREAKEVEN = "DGS10", "DFII10", "T10YIE"   # FRED 10y nominal, TIPS real, breakeven (spec Inputs)
RATE_5Y = "DGS5"         # 5y point, "most relevant for HY given duration" (Nicol p. 2)
HY_OAS = "BAMLH0A0HYM2"  # ICE BofA US HY OAS, FRED (spec Inputs)
BB, B, CCC = "BAMLH0A1HYBB", "BAMLH0A2HYB", "BAMLH0A3HYC"  # rating-bucket OAS, FRED (spec Inputs)
WINDOW = 3               # months of change: Reid uses 3-month changes (p. 3, Fig. 3)
SHOCK = 0.0040           # 40 bp sell-off or rally threshold (our choice: Fig. 4 low is 43 bp, Nicol p. 3)
Z_MONTHS = 24            # prior month ends for the sd of RYS and BES (our choice: Reid's 2-year window, p. 3)
Z_MIN = 12               # fewest changes for that sd (our choice)
CORR_WEEKS, CORR_WEEKS_MIN = 12, 8     # 12 weekly changes (Nicol p. 2); at least 8 (our choice)
CORR_MONTHS, CORR_MONTHS_MIN = 24, 12  # monthly fallback (our choice: Reid's 2-year window)
TROUGH_MONTHS = 3        # trough look-back of the quality state (reader F-F2, our choice)
COMPRESSION = 0.0040     # 40 bp rise from the trough (reader F-F2, Nicol p. 3 "30-40bps")
STALE_DAYS = 7           # an endpoint must be this close to its target date (our choice)
SD_FLOOR = 1e-12        # an sd at or below this counts as 0 (our choice: float noise)
HOLD = 1                 # evaluation horizon in months (reader F-F1 test)
REGIME_SCORES = {"inflation_selloff": 1.0, "real_selloff": -1.0, "rally": -1.0, "neutral": 0.0}  # spec Definition

META = {
    "rank": 27,
    "name": "Real-yield shock regime (with the spread-rate correlation regime)",
    "level": "index",
    "horizon_months": HOLD,
    "needs": ["macro_series", "hy_index"],
    "spec": "docs/factors/F27-real-yield-regime.md",
    "section": "9.2",
}

COLS = ["date", "index", "score", "available_at", "regime", "lead", "status", "signal_date", "window_months",
        "d_nominal", "d_real", "d_breakeven", "real_share", "split_gap", "be_source", "rys", "bes", "split_signal",
        "rho_nominal", "rho_real", "rho_source", "rho_freq", "rho_n", "rho_positive", "rate_tenor",
        "rise_from_trough", "compression_state", "quality_tilt", "b_bb_change", "ccc_b_change"]
NUM = ["score", "d_nominal", "d_real", "d_breakeven", "real_share", "split_gap", "rys", "bes", "split_signal",
       "rho_nominal", "rho_real", "rise_from_trough", "quality_tilt", "b_bb_change", "ccc_b_change"]


# ---------------------------------------------------------------- formula helpers


def macro_wide(macro: pd.DataFrame, dt: pd.Timestamp, as_of: pd.Timestamp) -> pd.DataFrame:
    """Date x series_id frame in decimal from rows with available_at <= dt and date <= as_of (spec build step 1).

    The last vintage per (series_id, date) wins. FRED percent values are divided by 100."""
    d = macro[(macro["available_at"] <= dt) & (pd.to_datetime(macro["date"]) <= as_of)].copy()
    if d.empty:
        return pd.DataFrame()
    d["date"] = pd.to_datetime(d["date"])
    d = d.sort_values("available_at").drop_duplicates(["series_id", "date"], keep="last")
    w = d.pivot(index="date", columns="series_id", values="value").astype(float).sort_index()
    return w / 100.0


def value_at(s: pd.Series, t: pd.Timestamp, tol_days: int = STALE_DAYS) -> float:
    """Last non-NaN value of `s` dated on or before t and at most tol_days before it, else NaN (spec Definition)."""
    s = s.dropna()
    s = s[(s.index <= t) & (s.index >= t - pd.Timedelta(tol_days, unit="D"))]
    return float(s.iloc[-1]) if len(s) else np.nan


def yield_split(nom: pd.Series, real: pd.Series, be: pd.Series | None, as_of: pd.Timestamp,
                months: int = WINDOW) -> dict[str, float]:
    """dy, dr, dpi over `months` month ends to as_of (spec Definition; Reid p. 3 uses 3-month changes).

    Without a breakeven series pi = nominal - real, so dy = dr + dpi exactly. `split_gap` = dy - dr - dpi.
    `real_share` = dr / (dr + dpi): the part of the move the real yield made."""
    t0 = as_of - pd.offsets.MonthEnd(months)
    if be is None:
        be = nom - real
    dy = value_at(nom, as_of) - value_at(nom, t0)
    dr = value_at(real, as_of) - value_at(real, t0)
    dpi = value_at(be, as_of) - value_at(be, t0)
    tot = dr + dpi
    share = dr / tot if np.isfinite(tot) and tot != 0 else np.nan
    return {"d_nominal": dy, "d_real": dr, "d_breakeven": dpi, "split_gap": dy - dr - dpi, "real_share": share}


def classify_regime(dy: float, dr: float, dpi: float, shock: float = SHOCK) -> tuple[str | None, str | None]:
    """(regime, lead) of a move (spec Definition). Regime: inflation_selloff, real_selloff, rally, neutral.

    Lead is "real" when the real yield made the larger part of the move in its direction, else "breakeven".
    A tie in a sell-off counts as real-led (our choice: the cautious side). NaN input gives (None, None)."""
    if not all(np.isfinite([dy, dr, dpi])):
        return None, None
    lead = "real" if np.sign(dy if dy != 0 else 1.0) * (dr - dpi) >= 0 else "breakeven"
    if dy >= shock:
        return ("real_selloff" if dr >= dpi else "inflation_selloff"), lead
    if dy <= -shock:
        return "rally", lead
    return "neutral", lead


def month_end_changes(s: pd.Series, as_of: pd.Timestamp, months: int, n: int) -> np.ndarray:
    """The `months`-month changes of `s` at the n month ends before as_of, oldest first (spec build step 4).

    The month end as_of itself is left out, so a shock does not set its own scale. NaN where an endpoint is stale."""
    ends = [as_of - pd.offsets.MonthEnd(k) for k in range(n, 0, -1)]
    return np.array([value_at(s, t) - value_at(s, t - pd.offsets.MonthEnd(months)) for t in ends])


def split_zscores(dr: float, dpi: float, real: pd.Series, be: pd.Series, as_of: pd.Timestamp,
                  months: int = WINDOW, n: int = Z_MONTHS, min_n: int = Z_MIN) -> tuple[float, float]:
    """RYS = dr / sd(dr), BES = dpi / sd(dpi), sd of the n prior month-end changes, ddof 1 (reader F-F1, our window).

    NaN when fewer than min_n changes exist or the sd is 0. Intuition: a 30 bp move is large in a calm year and
    small in 2022."""
    out = []
    for x, s in ((dr, real), (dpi, be)):
        h = month_end_changes(s, as_of, months, n)
        h = h[np.isfinite(h)]
        sd = float(np.std(h, ddof=1)) if len(h) >= max(min_n, 2) else np.nan
        out.append(x / sd if np.isfinite(sd) and sd > SD_FLOOR else np.nan)
    return out[0], out[1]


def change_corr(spread: pd.Series, rate: pd.Series, as_of: pd.Timestamp, freq: str, n: int,
                min_n: int) -> tuple[float, int]:
    """Correlation of the last n period changes of spread and rate up to as_of (Nicol p. 2: 12 weekly changes).

    `freq` "W-FRI" (week ends Friday) or "ME" (month end). Each series takes its last value per period. Periods
    with a missing value on either side drop out. Returns (rho, changes used); rho NaN below min_n or at zero sd."""
    lookback = pd.Timedelta(7 * (n + 1), unit="D") if freq == "W-FRI" else pd.offsets.MonthEnd(n + 1)
    start = as_of - lookback
    parts = []
    for s in (spread, rate):
        s = s.dropna()
        s = s[(s.index > start) & (s.index <= as_of)]
        parts.append(s.resample(freq).last().diff())
    d = pd.concat(parts, axis=1, keys=["s", "y"]).dropna().tail(n)
    if len(d) < min_n or d["s"].std() <= SD_FLOOR or d["y"].std() <= SD_FLOOR:
        return np.nan, len(d)
    return float(np.corrcoef(d["s"], d["y"])[0, 1]), len(d)


def rise_from_trough(rate: pd.Series, as_of: pd.Timestamp, months: int = TROUGH_MONTHS) -> float:
    """y(as_of) minus the lowest y in the `months` months to as_of (reader F-F2 state rule; Nicol p. 3 episodes)."""
    s = rate.dropna()
    s = s[(s.index > as_of - pd.offsets.MonthEnd(months)) & (s.index <= as_of)]
    now = value_at(rate, as_of)
    return now - float(s.min()) if len(s) and np.isfinite(now) else np.nan


# ---------------------------------------------------------------- compute


def _hy_spread(panels: Mapping[str, pd.DataFrame], dt: pd.Timestamp, as_of: pd.Timestamp) -> pd.Series | None:
    """`hy_index` spread per date, last vintage, available at dt (wiring 4.5). None when the table is absent."""
    h = panels.get("hy_index")
    if h is None or len(h) == 0:
        return None
    h = h[(h["available_at"] <= dt) & (pd.to_datetime(h["date"]) <= as_of)].copy()
    h["date"] = pd.to_datetime(h["date"])
    h = h.sort_values("available_at").drop_duplicates("date", keep="last")
    return h.set_index("date")["spread"].astype(float).sort_index()


def _rho(w: pd.DataFrame, hy: pd.Series | None, as_of: pd.Timestamp) -> dict[str, object]:
    """rho_nominal and rho_real from the first spread source and frequency with enough changes (spec step 5)."""
    rate_tenor = RATE_5Y if RATE_5Y in w else NOMINAL
    sources = [("hy_index", hy), (HY_OAS, w[HY_OAS] if HY_OAS in w else None)]
    for freq, n, min_n in (("W-FRI", CORR_WEEKS, CORR_WEEKS_MIN), ("ME", CORR_MONTHS, CORR_MONTHS_MIN)):
        for name, s in sources:
            if s is None:
                continue
            rho, used = change_corr(s, w[rate_tenor], as_of, freq, n, min_n)
            if np.isfinite(rho):
                rho_r, _ = change_corr(s, w[REAL], as_of, freq, n, min_n)
                return {"rho_nominal": rho, "rho_real": rho_r, "rho_source": name,
                        "rho_freq": "weekly" if freq == "W-FRI" else "monthly", "rho_n": used,
                        "rho_positive": bool(rho > 0)}
    return {"rho_source": None, "rho_freq": None, "rho_n": 0}


def _quality(w: pd.DataFrame, as_of: pd.Timestamp, months: int) -> dict[str, object]:
    """Quality-compression columns (spec Definition, reader F-F2; Nicol p. 3 Fig. 4)."""
    rate_tenor = RATE_5Y if RATE_5Y in w else NOMINAL
    rise = rise_from_trough(w[rate_tenor], as_of, TROUGH_MONTHS)
    out: dict[str, object] = {"rate_tenor": rate_tenor, "rise_from_trough": rise}
    if np.isfinite(rise):
        out["compression_state"] = bool(rise >= COMPRESSION)
        out["quality_tilt"] = 1.0 if rise >= COMPRESSION else 0.0
    t0 = as_of - pd.offsets.MonthEnd(months)
    for col, hi, lo in (("b_bb_change", B, BB), ("ccc_b_change", CCC, B)):
        if hi in w and lo in w:
            gap = w[hi] - w[lo]
            out[col] = value_at(gap, as_of) - value_at(gap, t0)
    return out


def compute(panels: Mapping[str, pd.DataFrame], as_of: pd.Timestamp, window_months: int = WINDOW,
            shock: float = SHOCK, regime_scores: Mapping[str, float] | None = None,
            rho_gate: bool = False) -> pd.DataFrame:
    """One row for index US_HY at as_of (spec build steps 1 to 6). score = the regime score of REGIME_SCORES
    (or `regime_scores`), NaN unless status is "ok". With rho_gate, a sell-off with rho > 0 scores -1 (Jezek
    p. 4). Empty frame (columns COLS) without `macro_series`. Higher score = long the HY index."""
    as_of = pd.Timestamp(as_of)
    dt = decision_time(as_of)
    macro = panels.get("macro_series")
    if macro is None or len(macro) == 0:
        return pd.DataFrame(columns=COLS)
    scores = {**REGIME_SCORES, **(regime_scores or {})}
    w = macro_wide(macro, dt, as_of)
    row = dict.fromkeys(COLS, np.nan)
    row.update({"date": as_of, "index": KEY, "available_at": dt, "window_months": window_months,
                "status": "missing_series", "regime": None, "lead": None, "rho_n": 0})
    if NOMINAL not in w or REAL not in w:
        return _frame(row)
    be = w[BREAKEVEN] if BREAKEVEN in w else None
    row["be_source"] = BREAKEVEN if be is not None else "derived"
    row["signal_date"] = w[NOMINAL].dropna().index.max()
    row.update(yield_split(w[NOMINAL], w[REAL], be, as_of, window_months))
    regime, lead = classify_regime(row["d_nominal"], row["d_real"], row["d_breakeven"], shock)
    row.update({"regime": regime, "lead": lead, "status": "ok" if regime is not None else "stale"})
    be_s = be if be is not None else w[NOMINAL] - w[REAL]
    rys, bes = split_zscores(row["d_real"], row["d_breakeven"], w[REAL], be_s, as_of, window_months)
    row.update({"rys": rys, "bes": bes, "split_signal": -(rys - bes)})
    row.update(_rho(w, _hy_spread(panels, dt, as_of), as_of))
    row.update(_quality(w, as_of, window_months))
    if regime is not None:
        s = scores[regime]
        if rho_gate and regime.endswith("selloff") and row.get("rho_positive") is True:
            s = -1.0
        row["score"] = s
    return _frame(row)


def _frame(row: dict) -> pd.DataFrame:
    out = pd.DataFrame([row], columns=COLS)
    return out.astype({k: float for k in NUM}).astype({"rho_n": "Int64", "window_months": "Int64"})
