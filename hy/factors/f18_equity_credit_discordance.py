"""F18 Equity-credit discordance (rank 18). Spec docs/factors/F18-equity-credit-discordance.md; methodology Section 8
(short-horizon overlay on S2). Source: Kapadia and Pu (2012), JFE 105, "Limited arbitrage between equity and credit
markets", CapArb/limited arb.pdf: eqs. 2 and 3 (p. 546), Table 4 (p. 551), trade rule (p. 553), Tables 6 and 7
(pp. 554 to 555). Pages are journal pages (PDF page + 541). The source uses CDS. We use TRACE G-spreads.

    r_t      = P_t / P_{t-tau} - 1,  tau = 5 trading days                       stock return with dividends (p. 551)
    dS_t     = median over the issuer's bonds of g_spread_t - g_spread_{t-tau}   our choice: replaces dCDS
    D_t      = sign(r_t) 1[dS_t r_t > 0] 1[|r_t| > 3%]                           the entry rule (p. 553)
    kappa    = 4 k / (M (M - 1)) - 1,  k = #{date pairs with dS dP > 0}          Kendall form (eqs. 2 and 3, p. 546)
    kappa_z  = 0.5 ln((1 + kappa) / (1 - kappa))                                 Fisher z (p. 555)

Intuition: in the Merton model a stock rise always tightens the spread. A spread that moved with the stock is a price
gap. Expect the spread to catch up with the stock: D = +1 (stock up, spread wider) is long the bond, D = -1 short.

Weak evidence. HY firms, 1-month rule: -0.05% per trade before 2008 and 0.19% in 2008 to March 2009, before trading
costs (Table 6, p. 554). The source trades stock and CDS together and does not say which leg converges.

Inputs. `bond_panel` (required) gives the issuer key and the bonds to score. Daily mode needs two new optional panels,
the same as F02: `equity_daily` (gvkey, date, ret, available_at = trade day + 1 day) and `bond_daily` (cusip, date,
g_spread, available_at = trade day + 1 day). Monthly fallback (`freq_source` "monthly"): `equity_monthly` (gvkey,
datadate, ret) and the month-end g_spread of `bond_panel`, with a 6.73% threshold. An issuer without a daily score
takes the monthly one. Without any equity panel the result is an empty frame.
"""

from __future__ import annotations

from typing import Mapping

import numpy as np
import pandas as pd

from hy.backtest import decision_time, eligible

TAU = 5                     # tau: 5 business days, weekly (p. 553; Table 4 p. 551)
THRESHOLD = 0.03            # |dP/P| > 3% opens a trade (p. 553)
HOLD_MONTHS = {5: 1, 10: 2}  # tau = 5 holds 1 month, tau = 10 holds 2 months (p. 553)
KAPPA_DAYS = 63             # kappa window: one quarter of trading days. Our choice (source: a calendar quarter, p. 555)
MIN_PAIR_SHARE = 0.5        # kappa needs half of the M (M - 1) / 2 date pairs. Our choice
KAPPA_CLIP = 0.99           # clip kappa before the Fisher z, so +-1 stays finite. Our choice (Table 7 max |z| 2.20)
STALE_DAYS = 7              # last equity day at most 7 days before as_of. Our choice (F02 rule)
MAP_DAYS = 126              # cusip -> gvkey from bond_panel rows of the last 126 days. Our choice
LOOKBACK_DAYS = 130         # calendar days of daily rows read: kappa quarter plus tau, and the trade scan. Our choice
SCAN_MONTHS = 3             # the no-overlap trade scan starts 3 months before as_of. Our choice
MONTHLY_THRESHOLD = 0.0673  # fallback: mean |dP/P| of discordant 25-day moves, all firms (Table 4, p. 551). Our choice
MONTHLY_POINTS = 13         # fallback kappa: the last 13 month ends (M = 13, as the daily quarter). Our choice

META = {
    "rank": 18,
    "name": "Equity-credit discordance",
    "level": "bond",
    "horizon_months": 1,
    "needs": ["bond_panel", "equity_daily", "bond_daily", "equity_monthly"],
    "spec": "docs/factors/F18-equity-credit-discordance.md",
    "section": "8",
}

ISSUER_COLS = ["gvkey", "score", "freq_source", "stock_ret", "d_spread", "n_bonds", "discordant", "kappa", "kappa_z",
               "n_pairs", "open_dir", "open_since"]
COLUMNS = ["date", "cusip", "score", "available_at", "gvkey"] + ISSUER_COLS[2:]


# ---------------------------------------------------------------- formulas


def discordance_signal(r, d_spread, threshold: float = THRESHOLD) -> np.ndarray:
    """D = sign(r) 1[dS r > 0] 1[|r| > threshold] (spec Definition; entry rule p. 553). Values -1, 0, +1, and NaN
    where r or dS is missing. A zero product is not a discrepancy (p. 551). Intuition: trade only a large stock move
    that the spread contradicts, in the direction the spread must catch up."""
    r, ds = np.asarray(r, dtype=float), np.asarray(d_spread, dtype=float)
    d = np.sign(r) * ((r * ds) > 0) * (np.abs(r) > threshold)
    return np.where(np.isnan(r) | np.isnan(ds), np.nan, d + 0.0)


def issuer_spread_change(s_end, s_start) -> tuple[float, int]:
    """dS = median over bonds of s_end - s_start, with the count of bonds that have both (spec Definition, our
    choice: replaces dCDS). No bond with both ends gives (NaN, 0)."""
    d = np.asarray(s_end, dtype=float) - np.asarray(s_start, dtype=float)
    d = d[~np.isnan(d)]
    return (float(np.median(d)), len(d)) if len(d) else (np.nan, 0)


def kendall_kappa(price, spreads, min_pairs: int | None = None) -> tuple[float, int]:
    """kappa over all date pairs (eqs. 2 and 3, p. 546): 2 k / n - 1, k = pairs with dS dP > 0, n = valid pairs.

    `price` has M dates. `spreads` is M dates x bonds. A pair's dS is the median over bonds with both dates (our
    choice). With all M (M - 1) / 2 pairs valid this is 4 k / (M (M - 1)) - 1. NaN with fewer than `min_pairs` valid
    pairs (default: MIN_PAIR_SHARE of all pairs). Returns (kappa, n). Intuition: -1 is full Merton integration, 0 is
    no link, +1 means every pair moves against the model."""
    p = np.asarray(price, dtype=float)
    s = np.asarray(spreads, dtype=float).reshape(len(p), -1)
    a, b = np.triu_indices(len(p), k=1)
    dp = p[b] - p[a]
    diff = s[b] - s[a]
    has = ~np.isnan(diff).all(axis=1)
    ds = np.full(len(a), np.nan)
    ds[has] = np.nanmedian(diff[has], axis=1)
    ok = ~np.isnan(dp) & ~np.isnan(ds)
    n = int(ok.sum())
    need = MIN_PAIR_SHARE * len(a) if min_pairs is None else min_pairs
    if n == 0 or n < need:
        return np.nan, n
    k = int(((dp * ds)[ok] > 0).sum())
    return 2.0 * k / n - 1.0, n


def fisher_z(kappa, clip: float = KAPPA_CLIP) -> np.ndarray:
    """kappa_z = 0.5 ln((1 + kappa) / (1 - kappa)) (p. 555), with kappa clipped to +-clip first (our choice)."""
    k = np.clip(np.asarray(kappa, dtype=float), -clip, clip)
    return np.arctanh(k)


def trade_entries(dates, signal, hold_months: int = HOLD_MONTHS[TAU]) -> pd.DataFrame:
    """The source trade rule (p. 553): open on a nonzero D when no trade on the firm is open, close `hold_months`
    calendar months later. No stop loss (spec Definition, our choice). Columns entry, exit, direction."""
    rows, exit_ = [], None
    for t, d in zip(pd.to_datetime(dates), np.asarray(signal, dtype=float)):
        if exit_ is not None and t < exit_:
            continue
        exit_ = None
        if d == d and d != 0:
            exit_ = t + pd.DateOffset(months=hold_months)
            rows.append({"entry": t, "exit": exit_, "direction": int(d)})
    return pd.DataFrame(rows, columns=["entry", "exit", "direction"])


def _open_trade(trades: pd.DataFrame, t: pd.Timestamp) -> tuple[float, pd.Timestamp]:
    """Direction and entry of the trade open at t (entry <= t < exit), else (0, NaT)."""
    live = trades[(trades["entry"] <= t) & (trades["exit"] > t)]
    return (float(live["direction"].iloc[-1]), live["entry"].iloc[-1]) if len(live) else (0.0, pd.NaT)


# ---------------------------------------------------------------- daily mode


def _known(df: pd.DataFrame | None, dt: pd.Timestamp) -> pd.DataFrame | None:
    """Rows public at the decision time. None or empty gives None."""
    if df is None or len(df) == 0:
        return None
    return df[pd.to_datetime(df["available_at"]) <= dt]


def _daily_issuer(eq: pd.DataFrame, wide: pd.DataFrame, as_of: pd.Timestamp, tau: int, threshold: float,
                  hold: int) -> dict | None:
    """Daily D, kappa and the open trade for one issuer (spec build steps 2 to 5). `eq` holds the issuer's daily
    returns, `wide` its bonds' daily g_spread (dates x cusip). None when the last equity day is stale."""
    eq = eq.sort_values("date")
    dates = pd.DatetimeIndex(eq["date"])
    if len(dates) == 0 or (as_of - dates[-1]).days > STALE_DAYS:
        return None
    p = pd.Series(np.cumprod(1.0 + eq["ret"].fillna(0.0).to_numpy(dtype=float)), index=dates)
    s = wide.reindex(dates)
    r = (p / p.shift(tau) - 1.0).to_numpy()
    dsw = s - s.shift(tau)
    n_b = dsw.notna().sum(axis=1).to_numpy()
    ds = dsw.median(axis=1, skipna=True).to_numpy()
    sig = discordance_signal(r, ds, threshold)

    m = KAPPA_DAYS // tau + 1                                  # M = 13 sampled dates at tau = 5
    pos = np.arange(len(dates) - 1, -1, -tau)[:m][::-1]        # every tau-th day back from the last one
    kap, n_pairs = kendall_kappa(p.to_numpy()[pos], s.to_numpy()[pos], min_pairs=MIN_PAIR_SHARE * m * (m - 1) / 2)

    scan = dates > as_of - pd.DateOffset(months=SCAN_MONTHS)
    od, since = _open_trade(trade_entries(dates[scan], sig[scan], hold), dates[-1])
    last = sig[-1]
    return {"score": last, "freq_source": "daily", "stock_ret": r[-1], "d_spread": ds[-1], "n_bonds": int(n_b[-1]),
            "discordant": np.nan if np.isnan(last) else float(r[-1] * ds[-1] > 0), "kappa": kap,
            "n_pairs": n_pairs, "open_dir": od, "open_since": since}


def daily_scores(eqd: pd.DataFrame, bd: pd.DataFrame, cusip_map: pd.Series, as_of: pd.Timestamp, tau: int = TAU,
                 threshold: float = THRESHOLD) -> pd.DataFrame:
    """Per gvkey from `equity_daily` and `bond_daily` already filtered to the decision time (spec build steps 2 to
    5). Rows ISSUER_COLS. `cusip_map` maps cusip to gvkey."""
    lo = as_of - pd.Timedelta(LOOKBACK_DAYS, unit="D")
    e = eqd[(eqd["date"] > lo) & (eqd["date"] <= as_of)].sort_values("available_at") \
        .drop_duplicates(["gvkey", "date"], keep="last")
    b = bd[(bd["date"] > lo) & (bd["date"] <= as_of) & bd["cusip"].isin(cusip_map.index)]
    b = b.sort_values("available_at").drop_duplicates(["cusip", "date"], keep="last")
    wide = b.pivot(index="date", columns="cusip", values="g_spread")
    by_issuer = cusip_map.groupby(cusip_map).groups
    rows = []
    for gv, g in e[e["gvkey"].isin(by_issuer)].groupby("gvkey"):
        cols = [c for c in by_issuer[gv] if c in wide.columns]
        res = _daily_issuer(g, wide[cols], as_of, tau, threshold, HOLD_MONTHS.get(tau, HOLD_MONTHS[TAU]))
        if res is not None:
            rows.append({"gvkey": gv, **res})
    return _issuer_frame(rows)


# ---------------------------------------------------------------- monthly fallback


def monthly_scores(bonds: pd.DataFrame, eqm: pd.DataFrame, cusip_map: pd.Series, as_of: pd.Timestamp,
                   threshold: float = MONTHLY_THRESHOLD, points: int = MONTHLY_POINTS) -> pd.DataFrame:
    """Per gvkey from `equity_monthly` and month-end `bond_panel` g_spread, both filtered to the decision time
    (spec monthly fallback). r = the month's return, dS = median change over bonds with real rows at both month
    ends. kappa over the last `points` month ends. open_dir = D, since the hold is one month. Rows ISSUER_COLS."""
    ends = pd.date_range(end=as_of + pd.offsets.MonthEnd(0), periods=points, freq="ME")
    b = bonds[~bonds["carried"].astype(bool) & (bonds["g_spread"] > 0)].copy()
    b["date"] = pd.to_datetime(b["date"]) + pd.offsets.MonthEnd(0)
    b = b[b["date"].isin(ends)].sort_values("available_at").drop_duplicates(["cusip", "date"], keep="last")
    sw = b.pivot(index="date", columns="cusip", values="g_spread").reindex(ends)
    e = eqm.copy()
    e["datadate"] = pd.to_datetime(e["datadate"]) + pd.offsets.MonthEnd(0)
    e = e[e["datadate"].isin(ends)].sort_values("available_at").drop_duplicates(["gvkey", "datadate"], keep="last")
    rw = e.pivot(index="datadate", columns="gvkey", values="ret").reindex(ends)
    by_issuer = cusip_map.groupby(cusip_map).groups
    rows = []
    for gv in rw.columns.intersection(list(by_issuer)):
        ret = rw[gv]
        if pd.isna(ret.iloc[-1]):
            continue
        s = sw[[c for c in by_issuer[gv] if c in sw.columns]]
        ds, n_b = issuer_spread_change(s.iloc[-1], s.iloc[-2]) if len(ends) > 1 else (np.nan, 0)
        d = float(discordance_signal(ret.iloc[-1], ds, threshold))
        p = np.cumprod(1.0 + ret.fillna(0.0).to_numpy()[1:])
        kap, n_pairs = kendall_kappa(np.r_[1.0, p], s.to_numpy())
        rows.append({"gvkey": gv, "score": d, "freq_source": "monthly", "stock_ret": float(ret.iloc[-1]),
                     "d_spread": ds, "n_bonds": n_b,
                     "discordant": np.nan if np.isnan(d) else float(ret.iloc[-1] * ds > 0),
                     "kappa": kap, "n_pairs": n_pairs, "open_dir": d,
                     "open_since": as_of if d == d and d != 0 else pd.NaT})
    return _issuer_frame(rows)


def _issuer_frame(rows: list[dict]) -> pd.DataFrame:
    """Issuer rows with kappa_z added, in ISSUER_COLS order."""
    out = pd.DataFrame(rows, columns=[c for c in ISSUER_COLS if c != "kappa_z"])
    out["kappa_z"] = fisher_z(out["kappa"]) if len(out) else pd.Series(dtype=float)
    out["open_since"] = pd.to_datetime(out["open_since"])
    return out[ISSUER_COLS]


# ---------------------------------------------------------------- the factor


def compute(panels: Mapping[str, pd.DataFrame], as_of: pd.Timestamp, tau: int = TAU,
            threshold: float = THRESHOLD) -> pd.DataFrame:
    """F18 scores for the eligible bonds of `bond_panel` at month end `as_of` (spec build steps 1 to 7).

    score = the issuer's D in {-1, 0, +1}: +1 when the stock rose more than the threshold and the spread widened
    (long the bond), -1 when the stock fell and the spread tightened. NaN means no data, never zero. Daily first,
    monthly fallback flagged in `freq_source`. Empty frame (columns COLUMNS) without `bond_panel`, or without both
    the daily pair (`equity_daily`, `bond_daily`) and `equity_monthly`."""
    as_of = pd.Timestamp(as_of)
    dt = decision_time(as_of)
    pnl = _known(panels.get("bond_panel"), dt)
    eqd, bd, eqm = (_known(panels.get(k), dt) for k in ("equity_daily", "bond_daily", "equity_monthly"))
    has_daily = eqd is not None and bd is not None
    if pnl is None or not (has_daily or eqm is not None):
        return pd.DataFrame(columns=COLUMNS)
    pnl = pnl.assign(date=pd.to_datetime(pnl["date"]))
    recent = pnl[(pnl["date"] <= as_of) & (pnl["date"] > as_of - pd.Timedelta(MAP_DAYS, unit="D"))
                 & pnl["gvkey"].notna()]
    cusip_map = recent.sort_values(["date", "available_at"]).drop_duplicates("cusip", keep="last") \
        .set_index("cusip")["gvkey"]

    daily = daily_scores(eqd, bd, cusip_map, as_of, tau, threshold) if has_daily else _issuer_frame([])
    monthly = monthly_scores(pnl[pnl["date"] <= as_of], eqm, cusip_map, as_of) if eqm is not None \
        else _issuer_frame([])
    # daily wins where it has a score, then monthly, then a daily row without a score
    use_m = ~monthly["gvkey"].isin(daily.loc[daily["score"].notna(), "gvkey"])
    parts = [daily[daily["score"].notna()], monthly[use_m & monthly["score"].notna()],
             daily[daily["score"].isna()], monthly[use_m & monthly["score"].isna()]]
    parts = [x for x in parts if len(x)]
    iss = pd.concat(parts, ignore_index=True).drop_duplicates("gvkey", keep="first") if parts else _issuer_frame([])

    b = pnl[pnl["date"] == as_of]
    b = b[eligible(b) & b["gvkey"].notna()].drop_duplicates("cusip", keep="last")
    if b.empty:
        return pd.DataFrame(columns=COLUMNS)
    out = b[["cusip", "gvkey"]].merge(iss, on="gvkey", how="left")
    out["date"] = as_of
    out["available_at"] = dt
    return out[COLUMNS].astype({"score": float}).reset_index(drop=True)
