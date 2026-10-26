"""F19 Owner cash flow to debt, maintenance capex adjusted (rank 19). Spec docs/factors/F19-owner-cash-flow.md;
methodology Section 4.2 (`fcf_to_debt`, `capex_flex`) and Section 8 (S1 inputs). Source: Leng, Ward et al.
(Deutsche Bank 2019), "Value Anatomy", pp. 11-13 and p. 32 (definition), p. 4 (backtest setup). Conflict: Gonzalez
et al. (Deutsche Bank 2019), "Time To Cross the Bridge", p. 11. Pages are PDF pages (= printed pages).

    MCX_t   = min(CAPX_t, (CAPX_t + CAPX_t-1 + CAPX_t-2) / 3)       maintenance capex (p. 12, p. 32)
    MAQ_t   = min(AQC_t, (AQC_t + AQC_t-1 + AQC_t-2) / 3)           maintenance acquisitions (p. 12, p. 13)
    OCF_t   = CFO_t + INT_t - MCX_t - MAQ_t                         owner cash flow to all debt (our choice: + INT)
    x_t     = OCF_t / (DLC_t + DLTT_t)                              scaled by total debt
    score   = pct rank of x within GICS sector - 0.5                sector neutral (p. 4)

t is the latest 12 months, t - k the 12 months k years earlier. Intuition: growth capex is optional in a downturn,
so a creditor counts only the capex that keeps the business standing.

Our choices against the source: start from Compustat CFO (it already deducts the working capital change, cash taxes
and cash interest), add gross cash interest back, add no R&D back (the source does, p. 12), deduct no preferred
dividends (junior to the bonds). `maint="dp"` sets MCX = depreciation, the floor of docs/framework.md F4.7.

Panels. `compustat_quarterly` (F08 names): `gvkey`, `datadate`, `available_at`, `dlcq`, `dlttq`, and the 3-month
flows `oancf`, `capx`. This module adds the columns `intpn` (de-cumulated `intpny`, cash interest), `xintq` (interest
expense, the fallback for `intpn`), `aqc` (de-cumulated `aqcy`, acquisitions; missing counts as 0) and `dpq`
(depreciation, only for `maint="dp"`). Fallback `compustat_annual` (F09 panel) with the added `comp.funda` columns
`oancf`, `capx`, `aqc`, `intpn`, `xint`, `dp`, `dlc`, `dltt`. An issuer without a valid quarterly block uses the
annual one. Without `bond_panel`, `gics`, or both fundamentals panels, the result is an empty frame.
"""

from __future__ import annotations

from typing import Mapping

import numpy as np
import pandas as pd

from hy.backtest import decision_time, eligible
from hy.factors.f08_lever_event_risk import STALE_DAYS, _consecutive
from hy.factors.f09_profitability_change import known_annual
from hy.peers import FIN_SECTORS, SUST_STALE_DAYS, _sector_pct, sector_at

AVG_YEARS = 3            # years in the capex and acquisition mean, current year included (p. 12, p. 32)
N_QUARTERS = 4 * AVG_YEARS   # quarters a quarterly block needs: three 4-quarter sums (spec build step 2)
HORIZON = 1              # months: the source rebalances monthly (p. 4)
MAINT = ("min3y", "dp")  # maintenance capex proxy: the source rule (p. 12), or depreciation (framework F4.7)

META = {
    "rank": 19,
    "name": "Owner cash flow to debt (maintenance capex adjusted)",
    "level": "bond",
    "horizon_months": HORIZON,
    "needs": ["bond_panel", "gics", "compustat_quarterly", "compustat_annual"],
    "spec": "docs/factors/F19-owner-cash-flow.md",
    "section": "4.2; 8 S1",
}

BLOCK_COLS = ["gvkey", "cfo", "int_raw", "capx0", "capx1", "capx2", "aqc0", "aqc1", "aqc2", "dp", "debt",
              "period_end", "fin_source"]
ISSUER_COLS = ["gvkey", "ocf_debt", "fcf_debt", "owner_cf", "cfo", "interest", "maint_capex", "growth_capex",
               "maint_acq", "debt", "period_end", "fin_source"]
BOND_COLS = ["date", "cusip", "score", "available_at", "gvkey", "sector", "ocf_debt", "fcf_debt", "owner_cf", "cfo",
             "interest", "maint_capex", "growth_capex", "maint_acq", "debt", "period_end", "fin_source"]


# ---------------------------------------------------------------- formula helpers


def maintenance(current: pd.Series, lag1: pd.Series, lag2: pd.Series) -> pd.Series:
    """min(current, mean of current and the two prior years) (spec Definition; p. 12, p. 32).

    The cap at the current level stops a past capex spike from inflating maintenance (p. 13). NaN in any year gives
    NaN. Intuition: a jump above the 3-year norm is growth, so only the norm is a fixed drain."""
    cur = current.astype(float)
    return np.minimum(cur, (cur + lag1.astype(float) + lag2.astype(float)) / AVG_YEARS)


def owner_cash_flow(cfo: pd.Series, interest: pd.Series, maint_capex: pd.Series, maint_acq: pd.Series) -> pd.Series:
    """OCF = CFO + INT - MCX - MAQ (spec Definition; table p. 13, credit form our choice).

    CFO already deducts the working capital change and cash interest, so adding INT back gives the cash that serves
    all debt. Intuition: what the business throws off for creditors after it keeps itself standing."""
    return cfo.astype(float) + interest.astype(float) - maint_capex.astype(float) - maint_acq.astype(float)


def to_debt(flow: pd.Series, debt: pd.Series) -> pd.Series:
    """flow / total debt, NaN where debt <= 0 (spec Definition). Intuition: the share of debt one year repays."""
    d = debt.astype(float)
    return flow.astype(float) / d.where(d > 0)


def sector_score(x: pd.Series, sector: pd.Series) -> pd.Series:
    """Percentile rank of x within GICS sector minus 0.5, so the score lies in (-0.5, 0.5] (spec build step 6; p. 4
    sector neutral). NaN where the sector has fewer than MIN_SECTOR values (hy.peers)."""
    return _sector_pct(x, sector) - 0.5


# ---------------------------------------------------------------- panel steps


def _col(df: pd.DataFrame, name: str) -> pd.Series:
    """Float column, or all NaN when the panel has no such column."""
    return df[name].astype(float) if name in df else pd.Series(np.nan, index=df.index)


def quarterly_blocks(cq: pd.DataFrame, dt: pd.Timestamp) -> pd.DataFrame:
    """Per gvkey: LTM CFO, interest, depreciation, three yearly capex and acquisition sums, debt (spec steps 1 to 3).

    Keeps the latest version of each quarter public at dt, then the last N_QUARTERS quarters. A firm with fewer
    quarters, a gap, or a latest quarter older than STALE_DAYS drops out. Interest per quarter is `intpn`, else
    `xintq`. Missing `aqc` counts as 0. Columns BLOCK_COLS."""
    c = cq[pd.to_datetime(cq["available_at"]) <= dt].copy()
    c["datadate"] = pd.to_datetime(c["datadate"])
    c = c.sort_values("available_at").drop_duplicates(["gvkey", "datadate"], keep="last")
    c = c.sort_values(["gvkey", "datadate"]).groupby("gvkey").tail(N_QUARTERS)
    c["int_q"] = _col(c, "intpn").fillna(_col(c, "xintq"))
    c["aqc_q"] = _col(c, "aqc").fillna(0.0)
    c["dp_q"] = _col(c, "dpq")
    rows = []
    for g, q in c.groupby("gvkey"):
        if len(q) < N_QUARTERS or (dt - q["datadate"].iloc[-1]).days > STALE_DAYS or not _consecutive(q["datadate"]):
            continue
        n = len(q)

        def year(col: str, k: int) -> float:
            return float(q[col].iloc[n - 4 * (k + 1): n - 4 * k].astype(float).sum(min_count=4))

        last = q.iloc[-1]
        rows.append({"gvkey": g, "cfo": year("oancf", 0), "int_raw": year("int_q", 0),
                     "capx0": year("capx", 0), "capx1": year("capx", 1), "capx2": year("capx", 2),
                     "aqc0": year("aqc_q", 0), "aqc1": year("aqc_q", 1), "aqc2": year("aqc_q", 2),
                     "dp": year("dp_q", 0), "debt": float(last["dlcq"]) + float(last["dlttq"]),
                     "period_end": last["datadate"], "fin_source": "quarterly"})
    return pd.DataFrame(rows, columns=BLOCK_COLS)


def annual_blocks(ca: pd.DataFrame, dt: pd.Timestamp) -> pd.DataFrame:
    """The same block from `compustat_annual` (spec step 4): fiscal years y, y - 1, y - 2 matched on `fyear`.

    Known rows follow F09 `known_annual` (available_at and the 90-day lag). The latest year must be at most
    SUST_STALE_DAYS old. A missing prior year gives NaN capex sums, so NaN maintenance. Columns BLOCK_COLS."""
    a = known_annual(ca, dt)
    if a.empty:
        return pd.DataFrame(columns=BLOCK_COLS)
    a = a.assign(fyear=a["fyear"].astype(int), aqc_y=_col(a, "aqc").fillna(0.0), capx_y=_col(a, "capx"))
    last = a.sort_values(["gvkey", "fyear"]).drop_duplicates("gvkey", keep="last")
    last = last[(dt - last["datadate"]).dt.days <= SUST_STALE_DAYS].set_index("gvkey")
    by_year = a.set_index(["gvkey", "fyear"])[["capx_y", "aqc_y"]]
    out = pd.DataFrame(index=last.index)
    for k in range(AVG_YEARS):
        lag = by_year.reindex(pd.MultiIndex.from_arrays([last.index, last["fyear"] - k])).to_numpy()
        out[f"capx{k}"], out[f"aqc{k}"] = lag[:, 0], lag[:, 1]
    out["cfo"] = _col(last, "oancf")
    out["int_raw"] = _col(last, "intpn").fillna(_col(last, "xint"))
    out["dp"] = _col(last, "dp")
    out["debt"] = _col(last, "dlc") + _col(last, "dltt")
    out["period_end"], out["fin_source"] = last["datadate"], "annual"
    return out.reset_index()[BLOCK_COLS]


def issuer_values(blocks: pd.DataFrame, maint: str = "min3y", interest: bool = True) -> pd.DataFrame:
    """OCF to debt and its parts per gvkey from BLOCK_COLS (spec step 5). Also `fcf_debt` = (CFO - CAPX) / debt,
    the plain FCF to debt of the DB note (p. 11), as the control. Columns ISSUER_COLS."""
    b = blocks
    mcx = b["dp"].astype(float) if maint == "dp" else maintenance(b["capx0"], b["capx1"], b["capx2"])
    maq = maintenance(b["aqc0"], b["aqc1"], b["aqc2"])
    add = b["int_raw"].astype(float) if interest else pd.Series(0.0, index=b.index)
    ocf = owner_cash_flow(b["cfo"], add, mcx, maq)
    return pd.DataFrame({
        "gvkey": b["gvkey"], "ocf_debt": to_debt(ocf, b["debt"]),
        "fcf_debt": to_debt(b["cfo"].astype(float) - b["capx0"].astype(float), b["debt"]),
        "owner_cf": ocf, "cfo": b["cfo"].astype(float), "interest": add, "maint_capex": mcx,
        "growth_capex": b["capx0"].astype(float) - mcx, "maint_acq": maq, "debt": b["debt"].astype(float),
        "period_end": b["period_end"], "fin_source": b["fin_source"]})[ISSUER_COLS]


def _present(panels: Mapping[str, pd.DataFrame], name: str) -> bool:
    return panels.get(name) is not None and len(panels[name]) > 0


def compute(panels: Mapping[str, pd.DataFrame], as_of: pd.Timestamp, maint: str = "min3y",
            interest: bool = True) -> pd.DataFrame:
    """F19 score per eligible bond of bond_panel at as_of (spec build steps 1 to 6). One row per cusip.

    score = the issuer's within-sector rank of OCF / debt, minus 0.5. NaN for financials, debt <= 0, no valid block,
    or a sector with fewer than MIN_SECTOR scored issuers. Empty frame (columns BOND_COLS) without bond_panel, gics,
    or both compustat_quarterly and compustat_annual. Higher score = long."""
    if maint not in MAINT:
        raise ValueError(f"maint must be one of {MAINT}")
    as_of = pd.Timestamp(as_of)
    has_q, has_a = _present(panels, "compustat_quarterly"), _present(panels, "compustat_annual")
    if not (_present(panels, "bond_panel") and _present(panels, "gics") and (has_q or has_a)):
        return pd.DataFrame(columns=BOND_COLS)
    dt = decision_time(as_of)
    p = panels["bond_panel"]
    p = p[(p["available_at"] <= dt) & (pd.to_datetime(p["date"]) == as_of)]
    p = p[eligible(p) & p["gvkey"].notna()].drop_duplicates("cusip", keep="last")
    if p.empty:
        return pd.DataFrame(columns=BOND_COLS)

    parts = [quarterly_blocks(panels["compustat_quarterly"], dt)] if has_q else []
    if has_a:
        done = parts[0]["gvkey"] if parts else []
        ann = annual_blocks(panels["compustat_annual"], dt)
        parts.append(ann[~ann["gvkey"].isin(done)])
    parts = [b for b in parts if len(b)]
    blocks = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=BLOCK_COLS)
    iss = issuer_values(blocks, maint, interest).set_index("gvkey").reindex(pd.unique(p["gvkey"]))
    g = panels["gics"]
    iss["sector"] = iss.index.map(sector_at(g[g["available_at"] <= dt], as_of))
    x = iss["ocf_debt"].where(iss["sector"].notna() & ~iss["sector"].isin(FIN_SECTORS))
    iss["score"] = sector_score(x, iss["sector"])

    out = p[["cusip", "gvkey"]].merge(iss.rename_axis("gvkey").reset_index(), on="gvkey", how="left")
    out["date"] = as_of
    out["available_at"] = dt
    return out[BOND_COLS].astype({"score": float, "ocf_debt": float, "fcf_debt": float}).reset_index(drop=True)
