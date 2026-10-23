"""Quarterly walk-forward of the full four-group analyst (methodology Section 11; decision page
2026-10-22-walkforward-2024).

At each quarter end t the whole process (scripts/process.py) runs as known at t + 1 day. The outcome is what the
issuer's bonds then earned over the next h months against the model's own hedges. This module holds the pure parts:
the decision dates, the point-in-time guard, the realised return of one bond, and the scoring statistics.

Conventions: spreads, yields and returns in decimals; durations in years; horizons in months; annualised figures
in bp a year (x 12 / h x 1e4), the unit of every prediction.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

import numpy as np
import pandas as pd
from scipy import stats

from hy.data.pit import LookAheadError, guard_times  # noqa: F401 - LookAheadError re-exported

FLAT_PRICE = 50.0      # below this a bond trades flat: no coupon accrues (hy.backtest uses the same rule)
END_WINDOW_DAYS = 10   # the end price is the last trade inside the 10 days to t + h, else the last trade after t
MIN_ISSUERS_IC = 5     # fewest issuers on a date for a rank IC


# One LookAheadError for the repo (hy.data.pit; review finding AR-DRY-002).


def decision_dates(first: str, data_end: str, min_months: int = 3) -> list[pd.Timestamp]:
    """Quarter ends from `first` while at least `min_months` of realised data follow (quarter end + min_months <=
    data_end). Intuition: a date counts only when its shortest outcome can be measured."""
    out, q = [], pd.Timestamp(first) + pd.offsets.QuarterEnd(0)
    while q + pd.DateOffset(months=min_months) <= pd.Timestamp(data_end):
        out.append(q)
        q = q + pd.offsets.QuarterEnd(1)
    return out


def decision_time(quarter_end: pd.Timestamp) -> pd.Timestamp:
    """Decision time for quarter end t: t + 1 day (the process rule: TRACE through t, filings as known the next day)."""
    return pd.Timestamp(quarter_end) + pd.Timedelta(1, unit="D")


def assert_pit(times: Iterable, decision: pd.Timestamp, what: str) -> None:
    """Raise LookAheadError when any time in `times` is after `decision` (delegates to `hy.data.pit.guard_times`)."""
    guard_times(times, decision, what)


def end_quote(quotes: pd.DataFrame, cusip: str, t: pd.Timestamp, end: pd.Timestamp,
              window_days: int = END_WINDOW_DAYS) -> dict | None:
    """The bond's exit quote for the period (t, end]: the last daily quote on or before `end` and after `t`.

    `early` is True when that quote is more than `window_days` before `end` (the bond stopped trading: exit at the
    last price, as hy.backtest does). None when the bond never traded after t. Only quotes inside (t, end] are read.
    """
    q = quotes[(quotes["cusip"] == cusip) & (quotes["trade_date"] > t) & (quotes["trade_date"] <= end)]
    if q.empty:
        return None
    r = q.sort_values("trade_date").iloc[-1]
    return {"date": r["trade_date"], "price": float(r["price_vw"]), "yield": float(r["yield_vw"]),
            "early": bool(r["trade_date"] < end - pd.Timedelta(window_days, unit="D"))}


def bond_realised(p0: float, p_end: float, coupon: float, tau: float, tsy0: float, tsy_end: float, dur: float,
                  s0: float, S0: float, S_end: float, beta: float, cost: float) -> dict[str, float]:
    """Realised hedged excess return of one bond over tau years (methodology 7.5 hedge; hy.backtest formula).

    total = (P_end - P_0 + 100 c tau) / P_0           clean price change plus coupon accrual (none if trading flat)
    tsy   = y_T,0 tau - D (y_T,end - y_T,0)           duration-matched Treasury
    bench = beta (S_0 tau - D (S_end - S_0))          high yield benchmark spread return; DTS beta = s_0 / S_0
    realised = total - tsy - bench;  net = realised - cost (round trip, decimal of price)
    Intuition: what a long bond, short its Treasury, short beta of the market's spread, actually earned.
    """
    accrual = 0.0 if (p0 < FLAT_PRICE or p_end < FLAT_PRICE) else 100.0 * coupon * tau
    total = (p_end - p0 + accrual) / p0
    tsy = tsy0 * tau - dur * (tsy_end - tsy0)
    bench = beta * (S0 * tau - dur * (S_end - S0))
    real = total - tsy - bench
    return {"total": total, "tsy": tsy, "bench": bench, "realised": real, "net": real - cost, "beta": beta, "s0": s0}


def numeric_or_nan(x) -> float:
    """A step output as a float for a numeric table: numbers pass, text (such as "no shortfall in 8 quarters") and None
    become NaN. The text stays in the step's basis field. Intuition: a column holds one type, so it can be saved."""
    return float(x) if isinstance(x, (int, float)) and not isinstance(x, bool) else float("nan")


def annualise_bp(x: float, months: float) -> float:
    """Return over `months` to bp a year (simple: x 12 / months x 1e4), the unit of the predictions."""
    return x * 12.0 / months * 1e4 if x == x and months else float("nan")


def rank_ic_by_date(df: pd.DataFrame, pred: str, real: str, date_col: str = "date",
                    min_n: int = MIN_ISSUERS_IC) -> pd.Series:
    """Spearman rank correlation of `pred` with `real` across issuers on each date with at least `min_n` pairs."""
    out = {}
    for d, g in df[[date_col, pred, real]].dropna().groupby(date_col):
        if len(g) >= min_n and g[pred].nunique() > 1 and g[real].nunique() > 1:
            out[d] = float(stats.spearmanr(g[pred], g[real]).statistic)
    return pd.Series(out, dtype=float)


def cluster_slope(df: pd.DataFrame, pred: str, real: str, date_col: str = "date") -> dict[str, float]:
    """OLS of real on pred (with intercept), standard errors clustered by date (CR0).
    Intuition: a slope of 1 means a 100 bp prediction earned 100 bp; dates share one market move, hence the clusters."""
    d = df[[date_col, pred, real]].dropna()
    if len(d) < 4 or d[pred].std() == 0:
        return {"slope": float("nan"), "se": float("nan"), "n": int(len(d))}
    X = np.column_stack([np.ones(len(d)), d[pred].to_numpy(float)])
    y = d[real].to_numpy(float)
    xtx_inv = np.linalg.inv(X.T @ X)
    beta = xtx_inv @ X.T @ y
    u = y - X @ beta
    meat = np.zeros((2, 2))
    for _, idx in d.groupby(date_col).indices.items():
        sc = X[idx].T @ u[idx]
        meat += np.outer(sc, sc)
    cov = xtx_inv @ meat @ xtx_inv
    return {"slope": float(beta[1]), "se": float(np.sqrt(cov[1, 1])), "intercept": float(beta[0]), "n": int(len(d))}


def score(df: pd.DataFrame, pred: str, real: str, date_col: str = "date") -> dict[str, float]:
    """One predictor against one outcome: mean quarterly rank IC with its t-statistic (across quarters), the share of
    quarters with a positive IC, the pooled rank IC, the hit rate (same sign), and the clustered slope.
    Intuition: does a higher number come before a better outcome, and is the size right?"""
    ic = rank_ic_by_date(df, pred, real, date_col)
    d = df[[pred, real]].dropna()
    pooled = float(stats.spearmanr(d[pred], d[real]).statistic) if len(d) >= 5 and d[pred].nunique() > 1 else float("nan")
    hit = float((np.sign(d[pred]) == np.sign(d[real])).mean()) if len(d) else float("nan")
    sl = cluster_slope(df, pred, real, date_col)
    n_q = len(ic)
    return {"ic_mean": float(ic.mean()) if n_q else float("nan"),
            "ic_t": float(ic.mean() / (ic.std(ddof=1) / np.sqrt(n_q))) if n_q > 2 and ic.std(ddof=1) > 0 else float("nan"),
            "ic_pos_share": float((ic > 0).mean()) if n_q else float("nan"), "n_quarters": n_q,
            "ic_pooled": pooled, "hit_rate": hit, "slope": sl["slope"], "slope_se": sl["se"], "n": int(len(d))}


def gate_outcomes(df: pd.DataFrame, call: str, direction: str, real: str) -> pd.DataFrame:
    """The gate's calls against what happened: per call and direction, the count, mean realised (bp a year), and
    the share that went the way the call implied (a cheap Watch should earn above zero, a rich one below).
    Intuition: a Watch call is a claim; this counts how often it came true."""
    d = df[[call, direction, real]].dropna(subset=[real]).copy()
    d["right"] = np.where(d[direction] == "cheap", d[real] > 0, d[real] < 0)
    return d.groupby([call, direction]).agg(n=(real, "size"), mean_bp_yr=(real, "mean"), right_share=("right", "mean")).reset_index()


EVENT_ITEMS = {  # 8-K item code -> short label (SEC Form 8-K item list); only items that move credit
    "1.03": "bankruptcy filing", "2.04": "debt acceleration", "3.01": "delisting notice", "2.01": "deal completed",
    "5.01": "change in control", "1.02": "agreement terminated",
}


def events_from_8k(rows: Sequence[tuple[str, str]], start: str, end: str) -> list[tuple[pd.Timestamp, str]]:
    """Credit events from 8-K item codes [(filing date, "1.01,2.03,...")] between `start` and `end`.
    1.01 together with 2.03 is labelled a new debt agreement (a refinancing or an exchange). Display only, never an
    input to a prediction. Intuition: the filing that announces the event marks the date on the timeline."""
    out = []
    for date, items in rows:
        d = pd.Timestamp(date)
        if not (pd.Timestamp(start) <= d <= pd.Timestamp(end)):
            continue
        codes = {c.strip() for c in str(items).split(",")}
        labels = [EVENT_ITEMS[c] for c in sorted(codes) if c in EVENT_ITEMS]
        if {"1.01", "2.03"} <= codes:
            labels.append("new debt agreement")
        if labels:
            out.append((d, "; ".join(dict.fromkeys(labels))))
    return out
