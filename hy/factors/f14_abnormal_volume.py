"""F14 Bond abnormal trading volume (rank 14). Spec docs/factors/F14-abnormal-volume.md; methodology Section 8 (new
signal) and Section 9.1 (pre-event feature of the earnings and rating review rows). Sources: Cao, Goyal, Xiao and
Zhan (Management Science 2023), Table 5 and text p. 1387, data p. 1378 (printed pages); "The Trading Dynamics of
Corporate Bonds and Bond ETFs" (dissertation), eq. (1) PDF p. 94, sample PDF p. 92, variables PDF p. 93.

    AbnVol_b,t = ln(1 + V_b,t) - ln(1 + mean_{k=1..K} V_b,t-k),  K = 12      log of volume over its trailing mean
    score      = AbnVol winsorised at 0.5% and 99.5% per month                 Cao et al. p. 1387, slope +0.034 (t 2.10)
    Abn_i,t    = X_i,t - mean(X_i, days -40 .. -6),  z = Abn / sd(X_i, -40 .. -6)   pre-event measure (PDF p. 94)

Intuition: a bond that suddenly trades much draws attention and buyers, so its price rises next month. Before an
event, trade above the bond's own normal level flags early positioning. Cao et al. use the measure as a control
only, IG and HY pooled, so the evidence is weak. Neither source in the folder gives the monthly window: K = 12 and
the log form are our choice (Gervais et al. 2001, the cited procedure, is not in the folder).

Inputs. `bond_panel` (required): `par_volume` and `n_trades` cover the last 7 days of the month. Optional
`bond_daily`: `cusip`, `date` (trade day), `par_volume`, `n_trades`, `available_at` (trade day + 1 day). It extends
the F02 panel of the same name. With it, V is the full calendar month (`volume_basis` "month") and the pre-event
columns fill. Optional new panel `events`: `gvkey`, `event_date`, `event_type` (a hy.events.EventType value),
`available_at` (the time the date is known). Without `bond_panel` the result is an empty frame.
"""

from __future__ import annotations

from typing import Mapping, Sequence

import numpy as np
import pandas as pd

from hy.backtest import decision_time, eligible
from hy.events import EventType
from hy.factors.f02_spread_to_d2d import winsorise

WINDOW = 12                 # K: trailing months of the mean (our choice, reader C-F3; the source gives no window)
MIN_HIST = 6                # history months the score needs out of K (our choice)
HOLD = 1                    # horizon in months: monthly Fama-MacBeth on future bond returns (Cao et al. p. 1387)
WINSOR = (0.005, 0.995)     # winsorise each month at 0.5% (Cao et al. p. 1387)
PRE_DAYS = (-5, -1)         # pre-event days, inside the [-5, +5] event window (dissertation PDF p. 94)
EST_DAYS = (-40, -6)        # estimation window, 35 trading days (dissertation PDF pp. 94, 98)
EVENT_DAYS = (-5, 5)        # event window of event_abnormal (dissertation PDF p. 94)
EVENT_TYPES = (EventType.EARNINGS.value, EventType.RATING_REVIEW.value)  # our choice: the source has neither

META = {
    "rank": 14,
    "name": "Bond abnormal trading volume",
    "level": "bond",
    "horizon_months": HOLD,
    "needs": ["bond_panel", "bond_daily", "events"],
    "spec": "docs/factors/F14-abnormal-volume.md",
    "section": "8",
}

COLS = ["date", "cusip", "score", "available_at", "gvkey", "abn_vol", "abn_ratio", "abn_trades", "n_hist",
        "volume_basis", "abn_vol_issuer", "n_bonds_issuer", "abn_vol_pre", "abn_vol_pre_z", "abn_trades_pre",
        "next_event_type", "days_to_event"]
EVENT_COLS = ["gvkey", "event_date", "event_type", "day0", "rel_day", "abn_vol", "abn_vol_z", "abn_trades",
              "n_bonds", "available_at"]


# ---------------------------------------------------------------- formula helpers


def abnormal_log_volume(v_now, v_mean):
    """AbnVol = ln(1 + V_t) - ln(1 + mean V_t-1..t-K) (spec Section 3; our form of Cao et al. p. 1387).

    Takes the log of the trailing mean, not the mean of logs, so a zero month does not dominate. Works on scalars
    and arrays. NaN stays NaN."""
    return np.log1p(np.asarray(v_now, dtype=float)) - np.log1p(np.asarray(v_mean, dtype=float))


def abnormal_measure(x_pre, x_est) -> tuple[float, float]:
    """Dissertation eq. (1), PDF p. 94: mean of x over the pre days minus the mean over the estimation window.
    z divides by the sample sd (ddof 1) of the estimation window (our choice, reader A1-F17). sd 0 gives z NaN."""
    pre, est = np.asarray(x_pre, dtype=float), np.asarray(x_est, dtype=float)
    if pre.size == 0 or est.size < 2:
        return np.nan, np.nan
    abn = float(pre.mean() - est.mean())
    sd = float(est.std(ddof=1))
    return abn, abn / sd if sd > 0 else np.nan


# ---------------------------------------------------------------- monthly volume


def _known(df: pd.DataFrame | None, dt: pd.Timestamp) -> pd.DataFrame | None:
    """Rows of `df` with available_at <= dt, or None when the panel is missing or empty."""
    if df is None or len(df) == 0:
        return None
    return df[df["available_at"] <= dt]


def _has_volume(daily: pd.DataFrame | None) -> bool:
    return daily is not None and {"cusip", "date", "par_volume", "n_trades"} <= set(daily.columns)


def monthly_volume(panel: pd.DataFrame, daily: pd.DataFrame | None, as_of: pd.Timestamp,
                   window: int = WINDOW) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
    """Monthly par volume V and trade count n per bond for months t-window .. t (spec build step 2).

    Both frames are months x cusip. Per bond, the counts come from the full-month sum of `daily` when the bond has
    daily rows ("month"), else from the 7-day `bond_panel` window ("window7"). A partial `bond_daily` therefore
    never zeroes a bond it does not cover. A month after the bond's first row with no trade, or a carried row, is
    0. A month before the first row is NaN. Inputs must already be point-in-time. Returns V, n and the basis."""
    as_of = pd.Timestamp(as_of)
    months = pd.date_range(end=as_of + pd.offsets.MonthEnd(0), periods=window + 1, freq="ME")
    p = panel.assign(date=pd.to_datetime(panel["date"]) + pd.offsets.MonthEnd(0))
    p = p[p["date"] <= months[-1]]
    live = ~p["carried"].astype(bool) if "carried" in p else pd.Series(True, index=p.index)
    q = p[live].sort_values("available_at").drop_duplicates(["date", "cusip"], keep="last")
    agg = q.set_index(["date", "cusip"])[["par_volume", "n_trades"]].astype(float)
    first = p.groupby("cusip")["date"].min()
    covered = pd.Index([])
    d = daily[pd.to_datetime(daily["date"]) <= as_of] if _has_volume(daily) else None
    if d is not None and len(d):
        d = d.assign(date=pd.to_datetime(d["date"]) + pd.offsets.MonthEnd(0))
        covered = pd.Index(d["cusip"].unique())
        first = pd.concat([first, d.groupby("cusip")["date"].min()]).groupby(level=0).min()
        dag = d.groupby(["date", "cusip"])[["par_volume", "n_trades"]].sum().astype(float)
        agg = pd.concat([agg[~agg.index.get_level_values("cusip").isin(covered)], dag])
    cols = first.index
    out = []
    for c in ("par_volume", "n_trades"):
        w = agg[c].unstack("cusip").reindex(index=months, columns=cols).fillna(0.0)
        out.append(w.where(np.greater_equal.outer(months.values, first.reindex(cols).values)))
    basis = pd.Series(np.where(cols.isin(covered), "month", "window7"), index=cols, name="volume_basis")
    return out[0], out[1], basis


def issuer_abnormal(v: pd.DataFrame, gvkey: pd.Series, full: pd.Index) -> pd.DataFrame:
    """Issuer AbnVol on the summed V of its bonds in `full` (spec Section 3, build step 5). `v` is months x cusip
    with month t last. `full` holds the scored bonds with a complete history, so the bond set stays fixed and a new
    issue does not inflate the measure. Columns gvkey, abn_vol_issuer, n_bonds_issuer."""
    cols = [c for c in full if c in v.columns]
    if not cols:
        return pd.DataFrame(columns=["gvkey", "abn_vol_issuer", "n_bonds_issuer"])
    s = v[cols].T.groupby(gvkey.reindex(cols)).sum().T
    abn = abnormal_log_volume(s.iloc[-1], s.iloc[:-1].mean())
    n = gvkey.reindex(cols).value_counts()
    return pd.DataFrame({"gvkey": s.columns, "abn_vol_issuer": abn, "n_bonds_issuer": n.reindex(s.columns).to_numpy()})


# ---------------------------------------------------------------- daily pre-event measure


def daily_issuer_measure(daily: pd.DataFrame, cusip_gvkey: pd.Series, cal: pd.DatetimeIndex, est: Sequence[int],
                         lo: int, hi: int, day0: int, col: str) -> pd.DataFrame:
    """X_i over trading days day0+lo .. day0+hi: the mean of `col` across the issuer's bonds, 0 on days without a
    trade (spec Open question 4). Members are the bonds with a trade in the estimation window day0+est. Returns
    days (relative day index) x gvkey, or an empty frame when the window leaves the calendar."""
    a, b = day0 + min(lo, est[0]), day0 + max(hi, est[1])
    if a < 0 or b >= len(cal):
        return pd.DataFrame()
    days = cal[a:b + 1]
    d = daily[daily["date"].isin(days)]
    if d.empty:
        return pd.DataFrame()
    rel = np.arange(a - day0, b - day0 + 1)
    w = d.pivot_table(index="date", columns="cusip", values=col, aggfunc="sum").reindex(days).fillna(0.0)
    trades = d.pivot_table(index="date", columns="cusip", values="n_trades", aggfunc="sum").reindex(days).fillna(0.0)
    w.index, trades.index = rel, rel
    members = trades.loc[est[0]:est[1]].sum(axis=0)
    members = [c for c in members[members > 0].index if c in cusip_gvkey.index]
    if not members:
        return pd.DataFrame()
    return w[members].T.groupby(cusip_gvkey.reindex(members)).mean().T


def _calendar(daily: pd.DataFrame) -> pd.DatetimeIndex:
    """Trading days: the dates in `bond_daily` (spec Section 3, our choice)."""
    return pd.DatetimeIndex(sorted(pd.to_datetime(daily["date"]).unique()))


def pre_event(daily: pd.DataFrame, cusip_gvkey: pd.Series, as_of: pd.Timestamp, pre: Sequence[int] = PRE_DAYS,
              est: Sequence[int] = EST_DAYS) -> pd.DataFrame:
    """Pre-event abnormal volume per gvkey at as_of (spec build step 6). Day 0 is the first trading day after
    as_of, so days pre[0] .. pre[1] are the last trading days on or before as_of. Abn of the daily mean par volume
    and trade count against est (dissertation eq. (1), PDF p. 94), averaged over the pre days, and z of the par
    volume. Columns gvkey, abn_vol_pre, abn_vol_pre_z, abn_trades_pre."""
    cols = ["gvkey", "abn_vol_pre", "abn_vol_pre_z", "abn_trades_pre"]
    d = daily.assign(date=pd.to_datetime(daily["date"]))
    d = d[d["date"] <= pd.Timestamp(as_of)]
    cal = _calendar(d)
    day0 = len(cal)  # day 0 lies after the calendar: only days before it are read
    vol = daily_issuer_measure(d, cusip_gvkey, cal, est, pre[0], pre[1], day0, "par_volume")
    if vol.empty:
        return pd.DataFrame(columns=cols)
    trd = daily_issuer_measure(d, cusip_gvkey, cal, est, pre[0], pre[1], day0, "n_trades")
    rows = []
    for g in vol.columns:
        av, zv = abnormal_measure(vol.loc[pre[0]:pre[1], g], vol.loc[est[0]:est[1], g])
        at, _ = abnormal_measure(trd.loc[pre[0]:pre[1], g], trd.loc[est[0]:est[1], g])
        rows.append({"gvkey": g, "abn_vol_pre": av, "abn_vol_pre_z": zv, "abn_trades_pre": at})
    return pd.DataFrame(rows, columns=cols)


def next_event(events: pd.DataFrame, as_of: pd.Timestamp, types: Sequence[str] = EVENT_TYPES) -> pd.DataFrame:
    """The issuer's next known event after as_of of a type in `types` (spec build step 6). Inputs must already be
    point-in-time. Columns gvkey, next_event_type, days_to_event (calendar days)."""
    e = events.assign(event_date=pd.to_datetime(events["event_date"]))
    e = e[(e["event_date"] > pd.Timestamp(as_of)) & e["event_type"].isin(list(types))]
    e = e.sort_values("event_date").drop_duplicates("gvkey", keep="first")
    return pd.DataFrame({"gvkey": e["gvkey"].to_numpy(), "next_event_type": e["event_type"].to_numpy(),
                         "days_to_event": (e["event_date"] - pd.Timestamp(as_of)).dt.days.to_numpy()})


def event_abnormal(daily: pd.DataFrame, events: pd.DataFrame, cusip_gvkey: pd.Series, as_of: pd.Timestamp,
                   types: Sequence[str] = EVENT_TYPES, days: Sequence[int] = EVENT_DAYS,
                   est: Sequence[int] = EST_DAYS) -> pd.DataFrame:
    """Source event study per past event (spec build step 7; dissertation eq. (1), PDF p. 94). Day 0 is the event
    date, or the next trading day. One row per event and relative day in `days`. A bond counts when it trades in
    the estimation window and in the event window (PDF p. 92). Only events whose whole window is known at
    decision_time(as_of) enter. For the Section 9 calibration on the production machine. Columns EVENT_COLS."""
    dt = decision_time(as_of)
    d, e = _known(daily, dt), _known(events, dt)
    if d is None or e is None or not _has_volume(d):
        return pd.DataFrame(columns=EVENT_COLS)
    d = d.assign(date=pd.to_datetime(d["date"]))
    d = d[d["date"] <= pd.Timestamp(as_of)]
    cal = _calendar(d)
    e = e.assign(event_date=pd.to_datetime(e["event_date"]))
    e = e[e["event_type"].isin(list(types))]
    rows = []
    for ev in e.itertuples(index=False):
        day0 = int(cal.searchsorted(ev.event_date, side="left"))
        if day0 + days[1] >= len(cal):
            continue
        bonds = cusip_gvkey[cusip_gvkey == ev.gvkey]
        win = d[d["cusip"].isin(bonds.index) & d["date"].isin(cal[max(day0 + days[0], 0):day0 + days[1] + 1])]
        traded = bonds[bonds.index.isin(win.loc[win["n_trades"] > 0, "cusip"])]
        if traded.empty:
            continue
        vol = daily_issuer_measure(d, traded, cal, est, days[0], days[1], day0, "par_volume")
        if vol.empty:
            continue
        trd = daily_issuer_measure(d, traded, cal, est, days[0], days[1], day0, "n_trades")
        est_win = d[d["cusip"].isin(traded.index) & d["date"].isin(cal[day0 + est[0]:day0 + est[1] + 1])]
        n_bonds = int(est_win.loc[est_win["n_trades"] > 0, "cusip"].nunique())
        x_est, t_est = vol.loc[est[0]:est[1], ev.gvkey], trd.loc[est[0]:est[1], ev.gvkey]
        for k in range(days[0], days[1] + 1):
            av, zv = abnormal_measure([vol.loc[k, ev.gvkey]], x_est)
            at, _ = abnormal_measure([trd.loc[k, ev.gvkey]], t_est)
            rows.append({"gvkey": ev.gvkey, "event_date": ev.event_date, "event_type": ev.event_type,
                         "day0": cal[day0], "rel_day": k, "abn_vol": av, "abn_vol_z": zv, "abn_trades": at,
                         "n_bonds": n_bonds, "available_at": dt})
    return pd.DataFrame(rows, columns=EVENT_COLS)


# ---------------------------------------------------------------- compute


def compute(panels: Mapping[str, pd.DataFrame], as_of: pd.Timestamp, window: int = WINDOW, min_hist: int = MIN_HIST,
            pre: Sequence[int] = PRE_DAYS, est: Sequence[int] = EST_DAYS,
            event_types: Sequence[str] = EVENT_TYPES) -> pd.DataFrame:
    """AbnVol per eligible bond of bond_panel at as_of (spec build steps 1 to 6). One row per cusip. score = the
    winsorised AbnVol, NaN with fewer than `min_hist` history months. Empty frame (columns COLS) without
    bond_panel. Higher score = long."""
    as_of = pd.Timestamp(as_of)
    dt = decision_time(as_of)
    p = _known(panels.get("bond_panel"), dt)
    if p is None:
        return pd.DataFrame(columns=COLS)
    daily, events = _known(panels.get("bond_daily"), dt), _known(panels.get("events"), dt)
    now = p[pd.to_datetime(p["date"]) == as_of]
    now = now[eligible(now) & now["gvkey"].notna()].sort_values("available_at").drop_duplicates("cusip", keep="last")
    if now.empty:
        return pd.DataFrame(columns=COLS)
    v, n, basis = monthly_volume(p, daily, as_of, window)
    v, n = v.reindex(columns=now["cusip"]), n.reindex(columns=now["cusip"])
    hist_v, hist_n = v.iloc[:-1], n.iloc[:-1]
    n_hist = hist_v.notna().sum(axis=0)
    mean_v = hist_v.mean(axis=0)
    ok = (n_hist >= min_hist).to_numpy()
    out = now[["cusip", "gvkey"]].reset_index(drop=True)
    out["abn_vol"] = np.where(ok, abnormal_log_volume(v.iloc[-1], mean_v), np.nan)
    out["abn_ratio"] = np.where(ok & (mean_v > 0).to_numpy(), v.iloc[-1] / mean_v.where(mean_v > 0), np.nan)
    out["abn_trades"] = np.where(ok, abnormal_log_volume(n.iloc[-1], hist_n.mean(axis=0)), np.nan)
    out["n_hist"] = n_hist.to_numpy()
    out["volume_basis"] = basis.reindex(out["cusip"]).to_numpy()
    out["score"] = winsorise(out["abn_vol"], *WINSOR)
    # issuer level: the scored bonds with a full history, summed
    gv = out.set_index("cusip")["gvkey"]
    iss = issuer_abnormal(v, gv, pd.Index(out.loc[out["n_hist"] == window, "cusip"]))
    out = out.merge(iss, on="gvkey", how="left")
    # pre-event columns for Section 9
    cg = p.sort_values("available_at").drop_duplicates("cusip", keep="last").set_index("cusip")["gvkey"].dropna()
    pe = pre_event(daily, cg, as_of, pre, est) if _has_volume(daily) else pd.DataFrame(
        columns=["gvkey", "abn_vol_pre", "abn_vol_pre_z", "abn_trades_pre"])
    ne = next_event(events, as_of, event_types) if events is not None else pd.DataFrame(
        columns=["gvkey", "next_event_type", "days_to_event"])
    out = out.merge(pe, on="gvkey", how="left").merge(ne, on="gvkey", how="left")
    out["date"] = as_of
    out["available_at"] = dt
    floats = ["score", "abn_vol", "abn_ratio", "abn_trades", "abn_vol_issuer", "abn_vol_pre", "abn_vol_pre_z",
              "abn_trades_pre", "days_to_event"]
    return out[COLS].astype({c: float for c in floats}).reset_index(drop=True)
