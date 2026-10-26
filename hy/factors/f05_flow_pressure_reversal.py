"""F05 Flow-induced selling pressure, same-issuer reversal (rank 5). Spec docs/factors/F05-flow-pressure-reversal.md;
methodology Section 8, S6 (forced flows) in the S4 within-issuer frame. Sources: Dannhauser and Hoseinzade (2021),
RFS, PDF pp. 4-5, 8, 11-12, 25-31; RFQ alpha spec sections 3, 7, 20. Pages are PDF pages.

    NS_i,d  = sum over customer trades u of (1{side_u = B} - 1{side_u = S}) Q_u      net customer sales, bond-day
    P_i,t   = sum_{d in W_t} NS_i,d / (|W_t| Vbar_i,t)                               pressure, share of normal volume
    RP_i,t  = P_i,t - sum_{j in a(i), j != i} DTS_j P_j,t / sum_{j != i} DTS_j      pressure in excess of siblings
    Trig    = 1{RP >= c_t} 1{P > 0} 1{M >= 2},  Exh = 1{RP^(10) <= 0},  F05 = Trig Exh RP

Intuition: the issuer's other bonds carry the same credit news, so sales in excess of theirs are a liquidity shock
that reverts over the next months (pp. 26-31).

Sign. TRACE `side` is the reporting dealer's side. `side = 'B'` with `contra_party_type = 'C'` is a customer sale to
the dealer (the `px_dealer_buy` rule of `trace_panel.month_sql`). Interdealer trades drop out. Positive NS means net
customer sales.

Inputs.
- `bond_panel` (production wiring 5): `date`, `cusip`, `gvkey`, `price`, `yield`, `years`, `g_spread`, `mod_dur`,
  `carried`, `available_at`. `gvkey` is the issuer key a(i).
- `trace_daily_flow` (new, optional): one row per bond and trade day. Columns `date` (trade day), `cusip`,
  `cust_sell_par`, `cust_buy_par`, `cust_sell_n`, `cust_buy_n` (customer trades of par >= 100,000 only) and
  `available_at` = trade day + `trace_bonds.DISSEMINATION_LAG`, plus the WRDS load lag in a live run.
  `daily_flow_from_trades` builds it from TRACE trades. Without this panel or `bond_panel` the result is empty.

Output. compute() returns one row per eligible bond of `bond_panel` at as_of. `score` is the mean of F05 over the
HOLD overlapped monthly cohorts formed at t-5 .. t (one sixth of the book per cohort). It is NaN when no cohort holds
the bond. Positive score = long the pressured bond. `pair_short` names the sibling with the lowest RP at as_of, the
short leg of the pair (spec build step 7). The count twin replaces Q_u by 1 (RFQ section 7).

Calendar. Trading days are weekdays (pandas business days). Holidays count as days with no trades. Our choice.
"""

from __future__ import annotations

from typing import Mapping

import numpy as np
import pandas as pd

from hy.backtest import FLAT_PRICE, decision_time, eligible
from hy.sources import trace_bonds as tb
from hy.sources.trace_panel import clean_trades

MIN_PAR = tb.MIN_PAR                 # institutional size only: par >= 100,000 (p. 8)
WINDOW = 63                          # W_t: trading days of the flow window, about 3 months (p. 11). Our choice
SHORT = 10                           # trading days of the exhaustion window RP^(10) (RFQ section 20). Our choice
VOL_WINDOW = 252                     # trading days of the lagged volume scale before W_t (p. 12). Our choice
Q_TRIGGER = 0.90                     # c_t percentile of RP (RFQ section 20.2 allows 0.80 or 0.90). Our choice
HIST_MONTHS = 36                     # months of RP history for c_t. Our choice
MIN_HIST_MONTHS = 12                 # fewest history months with RP before c_t exists. Our choice: spec is silent
MIN_MONTHS_SOLD = 2                  # persistence: 2 of the 3 calendar months of W_t with net sales. Our choice
MIN_TRADES = 5                       # fewest customer trades in W_t (spec build step 3). Our choice
HOLD = 6                             # months held, overlapped monthly cohorts (Tables 8-9, pp. 27-29). Our choice
WINSOR = (0.01, 0.99)                # RP winsorised per date, as the source winsorises spreads (p. 10)
MIN_YEARS = 1.0                      # fewest years to maturity (source drops bonds under 1y4m, p. 11). Our choice

META = {
    "rank": 5,
    "name": "Flow-induced selling pressure, same-issuer reversal",
    "level": "bond",
    "horizon_months": HOLD,
    "needs": ["bond_panel", "trace_daily_flow"],
    "spec": "docs/factors/F05-flow-pressure-reversal.md",
    "section": "8",
}

FLOW_COLS = ["date", "cusip", "cust_sell_par", "cust_buy_par", "cust_sell_n", "cust_buy_n", "available_at"]
MONTH_COLS = ["cusip", "gvkey", "dts", "pressure", "pressure_n", "pressure_short", "months_sold", "n_trades",
              "rel_pressure", "rel_pressure_n", "rel_short"]
BOND_COLS = ["date", "cusip", "score", "available_at", "gvkey", "f05_pressure", "f05_rel_pressure",
             "f05_rel_pressure_n", "f05_months_sold", "f05_trigger", "f05_exhausted", "f05_score", "f05_threshold",
             "n_cohorts", "pair_short"]


# ---------------------------------------------------------------- daily customer flow from TRACE trades


def daily_flow_from_trades(trades: pd.DataFrame, min_par: float = MIN_PAR,
                           load_lag: pd.Timedelta = pd.Timedelta(0)) -> pd.DataFrame:
    """Panel `trace_daily_flow` from TRACE trades (spec sections 3 and 4, build steps 1 and 2).

    Raw report rows (with `trc_st`) pass through `trace_panel.clean_trades` first. Cleaned rows need `cusip_id`,
    `trd_exctn_dt`, `side`, `contra_party_type` (or `cpt`) and par as `par`, `ascii_rptd_vol_tx` (a cap reads as
    its floor, `trace_bonds.parse_volume`) or `entrd_vol_qt`. Customer sale: side 'B', contra 'C'. Customer
    purchase: side 'S', contra 'C'. Trades under `min_par` and interdealer trades drop out (p. 8).
    available_at = trade day + DISSEMINATION_LAG + load_lag (the WRDS load lag in a live run)."""
    t = clean_trades(trades) if "trc_st" in trades.columns else trades.copy()
    if "par" not in t.columns:
        t["par"] = (t["ascii_rptd_vol_tx"].map(tb.parse_volume) if "ascii_rptd_vol_tx" in t.columns
                    else pd.to_numeric(t["entrd_vol_qt"], errors="coerce"))
    cpt = t["cpt"] if "cpt" in t.columns else t["contra_party_type"]
    sale = cpt.eq("C") & t["side"].eq("B")
    buy = cpt.eq("C") & t["side"].eq("S")
    keep = (sale | buy) & (t["par"] >= min_par)
    par = t["par"].astype(float)
    x = pd.DataFrame({
        "date": pd.to_datetime(t["trd_exctn_dt"]).dt.normalize(), "cusip": t["cusip_id"],
        "cust_sell_par": par.where(sale, 0.0), "cust_buy_par": par.where(buy, 0.0),
        "cust_sell_n": sale.astype(int), "cust_buy_n": buy.astype(int),
    })[keep]
    out = x.groupby(["date", "cusip"], as_index=False).sum()
    out["available_at"] = out["date"] + tb.DISSEMINATION_LAG + pd.Timedelta(load_lag)
    return out[FLOW_COLS].astype({"cust_sell_n": int, "cust_buy_n": int}).reset_index(drop=True)


# ---------------------------------------------------------------- formulas (spec section 3)


def trading_days(month_end: pd.Timestamp, n: int) -> pd.DatetimeIndex:
    """The last `n` weekdays that end on or before `month_end` (W_t and the volume window, spec section 3)."""
    return pd.bdate_range(end=pd.Timestamp(month_end).normalize(), periods=int(n))


def bond_pressure(flow: pd.DataFrame, month_end: pd.Timestamp, window: int = WINDOW, short: int = SHORT,
                  vol_window: int = VOL_WINDOW) -> pd.DataFrame:
    """P, P^(10), the count twin, M and the customer trade count per cusip at month end t (spec section 3).

    P = sum NS over W_t / (|W_t| Vbar). Vbar = customer par (sales plus purchases) over the `vol_window` days
    before W_t, divided by `vol_window`: days with no trade count as zero. P^(10) uses the last `short` days of W_t
    with the same Vbar. M counts the calendar months t-2, t-1, t with NS > 0 inside W_t. Vbar = 0 gives NaN.
    Intuition: P is the share of normal volume that went one way (p. 12)."""
    days = trading_days(month_end, vol_window + window)
    w0, s0 = days[vol_window], days[-short]
    f = flow[(flow["date"] >= days[0]) & (flow["date"] <= days[-1])]
    ns = f["cust_sell_par"] - f["cust_buy_par"]
    ns_n = f["cust_sell_n"] - f["cust_buy_n"]
    in_w, in_s = f["date"] >= w0, f["date"] >= s0
    g = pd.DataFrame({
        "cusip": f["cusip"], "ns_w": ns.where(in_w, 0.0), "ns_s": ns.where(in_s, 0.0),
        "nsn_w": ns_n.where(in_w, 0), "n_trades": (f["cust_sell_n"] + f["cust_buy_n"]).where(in_w, 0),
        "vol": (f["cust_sell_par"] + f["cust_buy_par"]).where(~in_w, 0.0),
        "vol_n": (f["cust_sell_n"] + f["cust_buy_n"]).where(~in_w, 0),
    }).groupby("cusip").sum()
    vbar = (g["vol"] / vol_window).where(g["vol"] > 0)
    vbar_n = (g["vol_n"] / vol_window).where(g["vol_n"] > 0)
    months = pd.Series(0, index=g.index)
    mth = f["date"].dt.to_period("M")
    for k in range(3):
        m = pd.Timestamp(month_end).to_period("M") - k
        sold = ns.where(in_w & (mth == m), 0.0).groupby(f["cusip"]).sum()
        months = months.add((sold.reindex(g.index, fill_value=0.0) > 0).astype(int), fill_value=0)
    return pd.DataFrame({
        "pressure": g["ns_w"] / (window * vbar), "pressure_short": g["ns_s"] / (short * vbar),
        "pressure_n": g["nsn_w"] / (window * vbar_n), "months_sold": months.astype(int),
        "n_trades": g["n_trades"].astype(int),
    }).rename_axis("cusip").reset_index()


def relative_pressure(p: pd.Series, dts: pd.Series, issuer: pd.Series) -> pd.Series:
    """RP_i = P_i - sum_{j != i} DTS_j P_j / sum_{j != i} DTS_j over the bonds of the same issuer (spec section 3).

    Leave-one-out DTS weights. NaN for a bond without a sibling or with zero sibling weight. Intuition: the
    issuer's own flow, which carries its credit news, drops out (pp. 4, 23)."""
    ok = p.notna() & (dts > 0)
    w = dts.where(ok, 0.0)
    wp = (w * p.fillna(0.0))
    sw = w.groupby(issuer).transform("sum") - w
    swp = wp.groupby(issuer).transform("sum") - wp
    return (p - swp / sw.where(sw > 0)).where(ok)


def winsorise(x: pd.Series, limits: tuple[float, float] = WINSOR) -> pd.Series:
    """Clip x at its `limits` quantiles (spec section 3; the source winsorises at 1% and 99%, p. 10)."""
    v = x.dropna()
    if v.empty:
        return x
    return x.clip(v.quantile(limits[0]), v.quantile(limits[1]))


def trigger_threshold(history: list[pd.Series], q: float = Q_TRIGGER, min_months: int = MIN_HIST_MONTHS) -> float:
    """c_t: the q quantile of RP over all bond-months of the history months (spec section 3, RFQ section 20.2).

    NaN when fewer than `min_months` history months carry an RP."""
    full = [h.dropna() for h in history if h.notna().any()]
    if len(full) < min_months:
        return np.nan
    return float(pd.concat(full).quantile(q))


def f05_score(rp: pd.Series, p: pd.Series, months_sold: pd.Series, rp_short: pd.Series, c: float,
              min_months: int = MIN_MONTHS_SOLD) -> pd.DataFrame:
    """Trig, Exh and F05 = Trig Exh RP (spec section 3). F05 is NaN where RP is NaN and 0 where the bond does not
    trigger. Exh: RP^(10) <= 0, so the bond no longer takes more net sales than its siblings."""
    trig = (rp >= c) & (p > 0) & (months_sold >= min_months)
    exh = rp_short <= 0
    score = rp.where(trig & exh, 0.0).where(rp.notna())
    return pd.DataFrame({"trigger": trig & rp.notna(), "exhausted": exh & rp_short.notna(), "f05": score})


def hold_score(cohorts: list[pd.Series], hold: int = HOLD) -> tuple[pd.Series, pd.Series]:
    """Score of the overlapped book: sum of the positive F05 over the last `hold` cohorts divided by `hold` (spec
    section 3, entry and hold). Returns the score (NaN where no cohort holds the bond) and the number of cohorts."""
    if not cohorts:
        return pd.Series(dtype=float), pd.Series(dtype=int)
    wide = pd.concat(cohorts, axis=1)
    pos = wide.where(wide > 0)
    n = pos.notna().sum(axis=1)
    return (pos.sum(axis=1) / hold).where(n > 0), n


# ---------------------------------------------------------------- one month end


def month_frame(flow: pd.DataFrame, panel: pd.DataFrame, month_end: pd.Timestamp, window: int = WINDOW,
                short: int = SHORT, vol_window: int = VOL_WINDOW, min_trades: int = MIN_TRADES) -> pd.DataFrame:
    """RP, RP^(10) and their inputs per bond at month end t (spec build steps 3 to 5). Columns MONTH_COLS.

    A bond needs an eligible panel row at t (`backtest.eligible`), price >= FLAT_PRICE, MIN_YEARS left, an issuer,
    `min_trades` customer trades in W_t, and DTS = mod_dur x g_spread at the prior month end. An issuer needs 2 such
    bonds. RP is winsorised per date. RP^(10) and the count twin are not."""
    t = pd.Timestamp(month_end)
    rows = panel[panel["date"] == t]
    rows = rows[eligible(rows) & (rows["price"] >= FLAT_PRICE) & (rows["years"] >= MIN_YEARS) & rows["gvkey"].notna()]
    prior = panel[panel["date"] == t - pd.offsets.MonthEnd(1)].drop_duplicates("cusip", keep="last")
    dts = (prior["mod_dur"].astype(float) * prior["g_spread"].astype(float)).rename("dts")
    dts.index = prior["cusip"]
    bp = bond_pressure(flow, t, window, short, vol_window)
    x = rows.drop_duplicates("cusip", keep="last")[["cusip", "gvkey"]].merge(bp, on="cusip")
    x["dts"] = x["cusip"].map(dts)
    x = x[(x["n_trades"] >= min_trades) & (x["dts"] > 0) & x["pressure"].notna()]
    x = x[x.groupby("gvkey")["cusip"].transform("count") >= 2].reset_index(drop=True)
    if x.empty:
        return pd.DataFrame(columns=MONTH_COLS)
    x["rel_pressure"] = winsorise(relative_pressure(x["pressure"], x["dts"], x["gvkey"]))
    x["rel_short"] = relative_pressure(x["pressure_short"], x["dts"], x["gvkey"])
    x["rel_pressure_n"] = relative_pressure(x["pressure_n"], x["dts"], x["gvkey"])
    return x[MONTH_COLS]


def _formation(frames: dict[pd.Timestamp, pd.DataFrame], s: pd.Timestamp, hist_months: int, q: float,
               min_hist: int, min_months_sold: int) -> tuple[pd.DataFrame, float]:
    """F05 at formation month s, with c_s from the `hist_months` month ends before s."""
    fr = frames[s]
    hist = [frames[m]["rel_pressure"].astype(float) for m in pd.date_range(end=s - pd.offsets.MonthEnd(1),
                                                                           periods=hist_months, freq="ME")]
    c = trigger_threshold(hist, q, min_hist)
    sc = f05_score(fr["rel_pressure"].astype(float), fr["pressure"].astype(float), fr["months_sold"],
                   fr["rel_short"].astype(float), c, min_months_sold)
    return pd.concat([fr.reset_index(drop=True), sc.reset_index(drop=True)], axis=1), c


def compute(panels: Mapping[str, pd.DataFrame], as_of: pd.Timestamp, window: int = WINDOW, short: int = SHORT,
            vol_window: int = VOL_WINDOW, q_trigger: float = Q_TRIGGER, hist_months: int = HIST_MONTHS,
            min_hist_months: int = MIN_HIST_MONTHS, min_trades: int = MIN_TRADES,
            min_months_sold: int = MIN_MONTHS_SOLD, hold: int = HOLD) -> pd.DataFrame:
    """F05 hold score per eligible bond of bond_panel at as_of (spec build steps 2 to 8). One row per cusip.

    Reads only rows with available_at <= decision_time(as_of). Formation months t-hold+1 .. t each need c_s from
    their own `hist_months` prior month ends. Empty frame (columns BOND_COLS) when bond_panel or trace_daily_flow is
    missing. Higher score = long."""
    as_of = pd.Timestamp(as_of)
    if any(panels.get(k) is None or len(panels[k]) == 0 for k in META["needs"]):
        return pd.DataFrame(columns=BOND_COLS)
    dt = decision_time(as_of)
    flow = panels["trace_daily_flow"]
    flow = flow[flow["available_at"] <= dt].copy()
    flow["date"] = pd.to_datetime(flow["date"]).dt.normalize()
    panel = panels["bond_panel"]
    panel = panel[panel["available_at"] <= dt].copy()
    panel["date"] = pd.to_datetime(panel["date"]) + pd.offsets.MonthEnd(0)
    months = pd.date_range(end=as_of, periods=hist_months + hold, freq="ME")
    frames = {m: month_frame(flow, panel, m, window, short, vol_window, min_trades) for m in months}
    formed = {s: _formation(frames, s, hist_months, q_trigger, min_hist_months, min_months_sold) for s in months[-hold:]}
    score, n = hold_score([f.set_index("cusip")["f05"].rename(s) for s, (f, _) in formed.items() if len(f)], hold)
    cur, c_t = formed[as_of]
    now = panel[(panel["date"] == as_of)]
    now = now[eligible(now) & now["gvkey"].notna()].drop_duplicates("cusip", keep="last")[["cusip", "gvkey"]]
    out = now.merge(cur.drop(columns="gvkey"), on="cusip", how="left")
    rp = cur.dropna(subset=["rel_pressure"]).astype({"rel_pressure": float})
    lowest = rp.loc[rp.groupby("gvkey")["rel_pressure"].idxmin()] if len(rp) else rp
    out["pair_short"] = out["gvkey"].map(dict(zip(lowest["gvkey"], lowest["cusip"])))
    out.loc[out["pair_short"] == out["cusip"], "pair_short"] = None
    out = out.rename(columns={"pressure": "f05_pressure", "rel_pressure": "f05_rel_pressure",
                              "rel_pressure_n": "f05_rel_pressure_n", "months_sold": "f05_months_sold",
                              "trigger": "f05_trigger", "exhausted": "f05_exhausted", "f05": "f05_score"})
    out["score"] = out["cusip"].map(score)
    out["n_cohorts"] = out["cusip"].map(n).fillna(0).astype(int)
    out["f05_threshold"] = c_t
    out["date"] = as_of
    out["available_at"] = dt
    for col in BOND_COLS:
        if col not in out.columns:
            out[col] = np.nan
    return out[BOND_COLS].astype({"score": float, "f05_score": float}).reset_index(drop=True)
