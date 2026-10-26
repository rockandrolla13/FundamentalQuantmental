"""F12 HY ETF pressure and contraflow (rank 12). Spec docs/factors/F12-etf-pressure.md; methodology Section 8, S6
(forced flows). Sources: Chao et al. (2019), "Why Do ETF Flows Move Prices?", Deutsche Bank, PDF pp. 1-3, 7; Shim
(2020), "Arbitrage Comovement", SSRN 3287912, eq. 5, 10, 11, 18, PDF pp. 12-14, 21, 35, 40, 42; RFQ alpha spec
section 24. Pages are PDF pages. All evidence is from equities.

    f_e,d    = (S_e,d - S_e,d-) / S_e,d-                              ETF net creation as a share of its shares
    A_i,t    = sum_e sum_{d in W_t} f_e,d Q_i,e,s(d)                    par the ETFs bought pro rata (allocation)
    T_i,t    = sum_e (Q_i,e,s(t) - Q_i,e,s(t-6))                        change in ETF par held (total)
    R_i,t    = T_i,t - A_i,t                                            reconstitution part (DB p. 3)
    Press    = A / Pi_i,t-6 (par) or A / sum_{m in W_t} V_i,m (volume),  score = -Press
    Lambda   = c_i wbar_i^g / sum_j wbar_j c_j wbar_j^g                  arbitrage sensitivity (eq. 5, 10), g = 0.5
    Arb_i,t  = -sum_e sigma_i,e (Lambda_i,e - 1) r_e,t                   over-reaction to the ETF move reverts

Intuition: a creation of 1% of the ETF shares buys 1% of each holding, so the bond takes the ETF flow times its
weight. That demand pushes the price, and the push reverts (DB p. 2: long outflows, short inflows, Sharpe 1.29).

Inputs.
- `bond_panel` (production wiring 5): `date`, `cusip`, `price`, `par_volume`, `available_at` and the `eligible`
  columns. Optional `amt_out` (par outstanding, as in F03) for the par scale.
- `etf_flows` (new): one row per ETF and day. `etf`, `date`, `shares_out` (or a dollar `flow` with `aum`), `nav`,
  optional `ret` (daily total return), `available_at` = date + 1 day (our choice).
- `etf_holdings` (new): one row per ETF, holdings date and bond. `etf`, `date`, `cusip`, `par_held`, optional
  `market_value`, `available_at` = date + 1 day, or the download time in a live run.
Without `etf_flows`, `etf_holdings` or `bond_panel`, compute() returns an empty frame.

Output. One row per eligible bond at as_of. `score` is -pressure on the chosen basis. It is NaN for a bond that no
ETF held in a snapshot of W_t (n_etfs = 0) and where the scale is missing. Positive score = long (the ETFs sold it).
"""

from __future__ import annotations

from typing import Mapping

import numpy as np
import pandas as pd

from hy.backtest import decision_time, eligible

WINDOW = 6           # months of the flow window W_t (DB p. 2: six-month ETF flow)
HOLD = 1             # months held: DB sorts every month (p. 2)
BASIS = "alloc"      # "alloc" = flow times weight (task definition), "total" = change in par held. Our choice
SCALE = "auto"       # "par" (amt_out), "volume" (par_volume), "auto" = par where amt_out exists. Our choice
GAMMA = 0.5          # price impact exponent (Shim p. 21: "standard in the empirical market microstructure literature")
LAM_MONTHS = 12      # months of weights and price impact for Lambda (Shim p. 21: "at least one year")
MIN_C_MONTHS = 6     # fewest monthly observations for the price impact c. Our choice

META = {
    "rank": 12,
    "name": "HY ETF pressure and contraflow",
    "level": "bond",
    "horizon_months": HOLD,
    "needs": ["bond_panel", "etf_flows", "etf_holdings"],
    "spec": "docs/factors/F12-etf-pressure.md",
    "section": "8",
}

BOND_COLS = ["date", "cusip", "score", "available_at", "pressure_alloc", "pressure_total", "pressure_recon",
             "scale_basis", "n_etfs", "arb_sensitivity", "etf_return", "arb_score"]


# ---------------------------------------------------------------- flows and holdings (spec section 3)


def share_flow(flows: pd.DataFrame) -> pd.DataFrame:
    """f_e,d per ETF and day (spec section 3): the change in shares outstanding over the shares of the prior row.

    Without `shares_out`, f = flow / aum of the prior row. The first row of each ETF has no f. Columns etf, date,
    frac. Intuition: f is the share of the ETF that APs created (f > 0) or redeemed (f < 0) that day."""
    f = flows.sort_values(["etf", "date", "available_at"]).drop_duplicates(["etf", "date"], keep="last")
    g = f.groupby("etf")
    if "shares_out" in f.columns and f["shares_out"].notna().any():
        s = f["shares_out"].astype(float)
        prev = g["shares_out"].shift(1).astype(float)
        frac = (s - prev) / prev.where(prev > 0)
    else:
        prev = g["aum"].shift(1).astype(float)
        frac = f["flow"].astype(float) / prev.where(prev > 0)
    return pd.DataFrame({"etf": f["etf"], "date": f["date"], "frac": frac}).dropna().reset_index(drop=True)


def snapshot_for(snaps: pd.DatetimeIndex, days: pd.Series, strict: bool = True) -> pd.Series:
    """The latest snapshot date before each day (on or before when strict is False). NaT where none exists.

    A flow on day d trades the basket that the ETF held before d (spec section 3, s(d))."""
    snaps = pd.DatetimeIndex(sorted(snaps))
    pos = snaps.searchsorted(pd.DatetimeIndex(days), side="left" if strict else "right") - 1
    out = pd.Series(pd.NaT, index=days.index, dtype="datetime64[ns]")
    ok = pos >= 0
    out[ok] = snaps[pos[ok]]
    return out


def allocation_par(frac: pd.DataFrame, holdings: pd.DataFrame) -> pd.Series:
    """A_i = sum_e sum_d f_e,d Q_i,e,s(d) per cusip (spec section 3). Flow days with no prior snapshot drop out.

    Intuition: a pro-rata creation buys the same share of every holding (DB p. 6: allocation flows are spread pro
    rata)."""
    parts = []
    for etf, fe in frac.groupby("etf"):
        he = holdings[holdings["etf"] == etf]
        if he.empty:
            continue
        snap = snapshot_for(pd.DatetimeIndex(he["date"].unique()), fe["date"])
        per = fe.assign(snap=snap).dropna(subset=["snap"]).groupby("snap")["frac"].sum()
        x = he.merge(per.rename("f").rename_axis("date").reset_index(), on="date")
        parts.append(pd.Series((x["f"] * x["par_held"].astype(float)).to_numpy(), index=x["cusip"].to_numpy()))
    if not parts:
        return pd.Series(dtype=float)
    return pd.concat(parts).groupby(level=0).sum()


def holdings_change(holdings: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.Series:
    """T_i = sum_e (Q_i,e,s(end) - Q_i,e,s(start)) per cusip, s = the latest snapshot on or before the date (spec
    section 3). An ETF without a snapshot at both ends drops out. A bond absent from a snapshot holds 0."""
    parts = []
    for _, he in holdings.groupby("etf"):
        snaps = pd.DatetimeIndex(he["date"].unique())
        s0, s1 = snapshot_for(snaps, pd.Series([start, end]), strict=False)
        if pd.isna(s0) or pd.isna(s1):
            continue
        q0 = he[he["date"] == s0].groupby("cusip")["par_held"].sum().astype(float)
        q1 = he[he["date"] == s1].groupby("cusip")["par_held"].sum().astype(float)
        parts.append(q1.sub(q0, fill_value=0.0))
    if not parts:
        return pd.Series(dtype=float)
    return pd.concat(parts).groupby(level=0).sum()


# ---------------------------------------------------------------- arbitrage sensitivity (Shim eq. 5, 10, 11)


def price_impact(panel: pd.DataFrame, as_of: pd.Timestamp, months: int = LAM_MONTHS, gamma: float = GAMMA,
                 min_months: int = MIN_C_MONTHS) -> pd.Series:
    """c_i: median of |P_m / P_m-1 - 1| / V_m^gamma over the last `months` month ends (spec section 3).

    A monthly proxy for eq. 11 (Shim p. 21), which fits r = c sign(V)|V|^gamma on 5-minute signed volume. Needs
    consecutive month ends, V > 0 and `min_months` ratios. Our choice. Intuition: c is the price move per unit of
    volume, the bond's illiquidity."""
    if "par_volume" not in panel.columns:
        return pd.Series(dtype=float)
    end = pd.Timestamp(as_of) + pd.offsets.MonthEnd(0)
    p = panel[(panel["date"] <= end) & (panel["date"] > end - pd.offsets.MonthEnd(months + 1))]
    p = p.sort_values(["cusip", "date"])
    prev_px = p.groupby("cusip")["price"].shift(1).astype(float)
    prev_dt = p.groupby("cusip")["date"].shift(1)
    consec = prev_dt == p["date"] - pd.offsets.MonthEnd(1)
    vol = p["par_volume"].astype(float)
    ratio = ((p["price"].astype(float) / prev_px - 1.0).abs() / vol.where(vol > 0) ** gamma).where(consec)
    ok = ratio.notna() & (p["date"] > end - pd.offsets.MonthEnd(months))
    g = ratio[ok].groupby(p.loc[ok, "cusip"])
    n = g.count()
    return g.median()[n >= min_months].rename("c")


def mean_weights(holdings: pd.DataFrame, end: pd.Timestamp, months: int = LAM_MONTHS) -> pd.DataFrame:
    """wbar_i,e: the mean portfolio weight over the snapshots of the last `months` months (eq. 10, p. 21).

    Weight = market_value share where the column exists, else par share. A bond absent from a snapshot has weight 0
    in it. Columns etf, cusip, w."""
    h = holdings[(holdings["date"] <= end) & (holdings["date"] > end - pd.DateOffset(months=months))].copy()
    use_mv = "market_value" in h.columns and h["market_value"].notna().all()
    h["x"] = (h["market_value"] if use_mv else h["par_held"]).astype(float)
    h["w"] = h["x"] / h.groupby(["etf", "date"])["x"].transform("sum")
    n = h.groupby("etf")["date"].nunique()
    w = h.groupby(["etf", "cusip"])["w"].sum().div(n, level="etf")
    return w.rename("w").reset_index()


def arb_sensitivity(w: pd.Series, c: pd.Series, gamma: float = GAMMA) -> pd.Series:
    """Lambda_i = c_i w_i^gamma / sum_j w_j c_j w_j^gamma over the bonds of one ETF (eq. 5 and 10, pp. 12, 21).

    `w` and `c` are indexed by cusip. Bonds without c or with w = 0 drop out and the weights renormalise, so the
    weighted mean of Lambda is 1 (p. 13). Our choice. Intuition: Lambda > 1 is illiquid for its weight."""
    x = pd.concat([w.rename("w"), c.rename("c")], axis=1).dropna()
    x = x[(x["w"] > 0) & (x["c"] > 0)]
    if x.empty:
        return pd.Series(dtype=float)
    wn = x["w"] / x["w"].sum()
    num = x["c"] * wn ** gamma
    return (num / (wn * num).sum()).rename("lam")


def etf_month_return(flows: pd.DataFrame, as_of: pd.Timestamp) -> pd.Series:
    """r_e over the month that ends at as_of (spec section 3). Compounds the daily `ret` where it exists, else uses
    the last nav on or before as_of over the last nav on or before the prior month end. NaN without both."""
    end = pd.Timestamp(as_of)
    start = end - pd.offsets.MonthEnd(1)
    out = {}
    for etf, fe in flows.sort_values("date").groupby("etf"):
        if "ret" in fe.columns and fe["ret"].notna().any():
            r = fe.loc[(fe["date"] > start) & (fe["date"] <= end), "ret"].dropna().astype(float)
            out[etf] = float((1.0 + r).prod() - 1.0) if len(r) else np.nan
            continue
        n0 = fe.loc[fe["date"] <= start, "nav"].dropna()
        n1 = fe.loc[fe["date"] <= end, "nav"].dropna()
        out[etf] = float(n1.iloc[-1] / n0.iloc[-1] - 1.0) if len(n0) and len(n1) and n0.iloc[-1] > 0 else np.nan
    return pd.Series(out, dtype=float, name="etf_return")


def arb_scores(holdings: pd.DataFrame, flows: pd.DataFrame, panel: pd.DataFrame, as_of: pd.Timestamp,
               gamma: float = GAMMA, months: int = LAM_MONTHS, min_c_months: int = MIN_C_MONTHS) -> pd.DataFrame:
    """Lambda_i = sum_e sigma_i,e Lambda_i,e, r = sum_e sigma_i,e r_e and Arb = -sum_e sigma (Lambda - 1) r_e per
    cusip (spec section 3). sigma_i,e is ETF e's share of bond i's ETF par at the latest snapshot on or before
    as_of, over the ETFs with a Lambda. Columns arb_sensitivity, etf_return, arb_score, indexed by cusip."""
    end = pd.Timestamp(as_of)
    c = price_impact(panel, end, months, gamma, min_c_months)
    wbar = mean_weights(holdings, end, months)
    r_e = etf_month_return(flows, end)
    rows = []
    for etf, he in holdings.groupby("etf"):
        lam = arb_sensitivity(wbar[wbar["etf"] == etf].set_index("cusip")["w"], c, gamma)
        s = snapshot_for(pd.DatetimeIndex(he["date"].unique()), pd.Series([end]), strict=False).iloc[0]
        if lam.empty or pd.isna(s):
            continue
        q = he[he["date"] == s].groupby("cusip")["par_held"].sum().astype(float)
        rows.append(pd.DataFrame({"cusip": lam.index, "etf": etf, "lam": lam.to_numpy(),
                                  "q": q.reindex(lam.index).fillna(0.0).to_numpy(), "r": r_e.get(etf, np.nan)}))
    if not rows:
        return pd.DataFrame(columns=["arb_sensitivity", "etf_return", "arb_score"], dtype=float)
    x = pd.concat(rows, ignore_index=True)
    x = x[x["q"] > 0]
    x["sigma"] = x["q"] / x.groupby("cusip")["q"].transform("sum")
    g = x.assign(sl=x["sigma"] * x["lam"], sr=x["sigma"] * x["r"],
                 sa=-x["sigma"] * (x["lam"] - 1.0) * x["r"]).groupby("cusip")
    return pd.DataFrame({"arb_sensitivity": g["sl"].sum(), "etf_return": g["sr"].sum(min_count=1),
                         "arb_score": g["sa"].sum(min_count=1)})


# ---------------------------------------------------------------- compute


def window_holders(holdings: pd.DataFrame, start: pd.Timestamp) -> pd.Series:
    """Number of ETFs that hold each cusip (par > 0) in a snapshot of W_t (spec build step 4). Each ETF's snapshots
    count from its latest snapshot on or before `start`, the basket s(t-6) of T."""
    first = holdings.loc[holdings["date"] <= start].groupby("etf")["date"].max()
    lo = holdings["etf"].map(first).fillna(pd.Timestamp(start))
    h = holdings[(holdings["date"] >= lo) & (holdings["par_held"] > 0)]
    return h.groupby("cusip")["etf"].nunique().rename("n_etfs")


def _known(df: pd.DataFrame, dt: pd.Timestamp, as_of: pd.Timestamp) -> pd.DataFrame:
    """Rows public by the decision time and dated on or before as_of, with `date` as a timestamp."""
    d = df[df["available_at"] <= dt].copy()
    d["date"] = pd.to_datetime(d["date"])
    return d[d["date"] <= as_of + pd.offsets.MonthEnd(0)]


def compute(panels: Mapping[str, pd.DataFrame], as_of: pd.Timestamp, window: int = WINDOW, basis: str = BASIS,
            scale: str = SCALE, gamma: float = GAMMA, lam_months: int = LAM_MONTHS,
            min_c_months: int = MIN_C_MONTHS) -> pd.DataFrame:
    """F12 score per eligible bond at as_of (spec build steps 1 to 7). One row per cusip.

    Reads only rows with available_at <= decision_time(as_of). score = -pressure on `basis` ("alloc" or "total")
    over `scale` ("par", "volume" or "auto"). Empty frame (columns BOND_COLS) when bond_panel, etf_flows or
    etf_holdings is missing. Higher score = long."""
    as_of = pd.Timestamp(as_of)
    if any(panels.get(k) is None or len(panels[k]) == 0 for k in META["needs"]):
        return pd.DataFrame(columns=BOND_COLS)
    dt = decision_time(as_of)
    flows = _known(panels["etf_flows"], dt, as_of)
    flows = flows[flows["date"] <= as_of]
    hold = _known(panels["etf_holdings"], dt, as_of)
    hold = hold[hold["date"] <= as_of]
    panel = _known(panels["bond_panel"], dt, as_of)
    panel["date"] = panel["date"] + pd.offsets.MonthEnd(0)
    start = as_of - pd.offsets.MonthEnd(window)

    now = panel[panel["date"] == as_of]
    now = now[eligible(now)].drop_duplicates("cusip", keep="last").set_index("cusip")
    held = window_holders(hold, start)
    cusips = now.index
    if cusips.empty:
        return pd.DataFrame(columns=BOND_COLS)
    n_etfs = held.reindex(cusips).fillna(0).astype(int)

    fr = share_flow(flows)
    fr = fr[(fr["date"] > start) & (fr["date"] <= as_of)]
    a = allocation_par(fr, hold).reindex(cusips).fillna(0.0)
    t = holdings_change(hold, start, as_of).reindex(cusips)

    use = scale
    if scale == "auto":
        use = "par" if "amt_out" in now.columns and now["amt_out"].notna().any() else "volume"
    if use == "par":
        first = panel[panel["date"] == start].drop_duplicates("cusip", keep="last").set_index("cusip")
        amt = first["amt_out"].reindex(cusips) if "amt_out" in first.columns else pd.Series(np.nan, index=cusips)
        den = amt.fillna(now["amt_out"].reindex(cusips) if "amt_out" in now.columns else np.nan).astype(float)
    else:
        win = panel[(panel["date"] > start) & (panel["date"] <= as_of)]
        den = (win.groupby("cusip")["par_volume"].sum().reindex(cusips).astype(float)
               if "par_volume" in win.columns else pd.Series(np.nan, index=cusips))
    den = den.where((den > 0) & (n_etfs > 0))

    out = pd.DataFrame(index=cusips.rename("cusip"))
    out["pressure_alloc"] = a / den
    out["pressure_total"] = t / den
    out["pressure_recon"] = (t - a) / den
    out["scale_basis"] = use
    out["n_etfs"] = n_etfs
    out["score"] = -out["pressure_total" if basis == "total" else "pressure_alloc"]
    out = out.join(arb_scores(hold, flows, panel, as_of, gamma, lam_months, min_c_months))
    out = out.reset_index()
    out["date"] = as_of
    out["available_at"] = dt
    for col in BOND_COLS:
        if col not in out.columns:
            out[col] = np.nan
    return out[BOND_COLS].astype({"score": float, "arb_sensitivity": float, "arb_score": float}).reset_index(drop=True)
