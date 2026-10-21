"""Join Compustat PIT vintages and EDGAR acceptance times into `IssuerFinancials` (methodology Section 3.2).

Rule for `available_at`:
- First version of a quarter: the earlier of the EDGAR acceptance of the
  matching 10-Q or 10-K and the day after the first Compustat snapshot that
  shows it. The 10-Q made the numbers public; a snapshot can come earlier when
  Compustat took them from the earnings release.
- Later versions (restatements): the day after the snapshot that first shows them.

Intuition: use the first moment the market could read the number, and never a
moment before any source shows it.
"""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np
import pandas as pd

from hy.inputs import IssuerFinancials, NonRecurringItem, PointInTimeStore

SOURCE = "compustat_pit+edgar"


def match_filings(
    vintages: pd.DataFrame,
    filings: pd.DataFrame,
    cik_by_gvkey: Mapping[str, str],
    tolerance_days: int = 10,
) -> pd.DataFrame:
    """Attach `acceptance` of the original 10-Q or 10-K to each first version and set `available_at`.

    A filing matches when its CIK is the issuer's, its report date is within `tolerance_days` of `datadate`
    (52-53 week fiscal years end off month end), and it was accepted after `datadate`. The earliest match wins.
    Adds `acceptance`, `available_at`, and `available_at_source` in {"edgar", "snapshot"}.
    """
    v = vintages.copy()
    v["cik"] = v["gvkey"].map(lambda g: f"{int(float(cik_by_gvkey[g])):010d}" if g in cik_by_gvkey and pd.notna(cik_by_gvkey[g]) else None)
    f = filings[~filings["form"].str.endswith("/A")][["cik", "report_date", "acceptance"]].dropna()
    first = v[v["vintage"] == 0][["gvkey", "cik", "datadate"]].dropna(subset=["cik"])
    cand = first.merge(f, on="cik", how="inner")
    gap = (cand["report_date"] - cand["datadate"]).dt.days.abs()
    cand = cand[(gap <= tolerance_days) & (cand["acceptance"] > cand["datadate"])]
    acc = cand.groupby(["gvkey", "datadate"], as_index=False)["acceptance"].min()
    v = v.merge(acc, on=["gvkey", "datadate"], how="left")
    v.loc[v["vintage"] > 0, "acceptance"] = pd.NaT
    snap = v["snapshot_available_at"]
    use_edgar = v["acceptance"].notna() & (snap.isna() | (v["acceptance"] < snap))
    v["available_at"] = pd.to_datetime(np.where(use_edgar, v["acceptance"], snap))
    v["available_at_source"] = np.where(use_edgar, "edgar", "snapshot")
    if "pit_exact" not in v:
        v["pit_exact"] = True
    # A row with neither a snapshot nor a filing has no defensible release time.
    return v[v["available_at"].notna()].drop(columns=["cik"]).reset_index(drop=True)


def replace_inexact(vintages: pd.DataFrame, filled: pd.DataFrame) -> pd.DataFrame:
    """Swap flagged quarters (`pit_exact = False`) for their as-first-filed rebuild where one exists.

    Adds `value_source`: "compustat_pit" for history rows, "compustat_current" for flagged rows left in place,
    and the rebuild's own source (e.g. "edgar_xbrl") for swapped rows.
    """
    v = vintages.copy()
    if "value_source" not in v:
        v["value_source"] = np.where(v["pit_exact"].astype(bool), "compustat_pit", "compustat_current")
    if filled is None or filled.empty:
        return v
    keys = set(zip(filled["gvkey"], filled["datadate"]))
    drop = (~v["pit_exact"].astype(bool)) & pd.Series([(g, d) in keys for g, d in zip(v["gvkey"], v["datadate"])], index=v.index)
    add = filled.drop(columns=["acceptance_10k"], errors="ignore")
    add = add[[(g, d) in set(zip(v.loc[drop, "gvkey"], v.loc[drop, "datadate"])) for g, d in zip(add["gvkey"], add["datadate"])]]
    return pd.concat([v[~drop], add], ignore_index=True)


def compare_sources(a: pd.DataFrame, b: pd.DataFrame, fields: list[str], rel_tol: float = 0.01) -> dict[str, float]:
    """Share of common (gvkey, datadate) where two sources agree within `rel_tol`, per field.

    Use it to check the XBRL rebuild against Compustat's latest values for the same quarters.
    """
    j = a.merge(b, on=["gvkey", "datadate"], suffixes=("_a", "_b"))
    out = {"quarters": float(len(j))}
    for f in fields:
        x, y = j[f + "_a"].astype(float), j[f + "_b"].astype(float)
        ok = x.notna() & y.notna()
        rel = (x[ok] - y[ok]).abs() / y[ok].abs().clip(lower=1e-9)
        out[f] = float((rel <= rel_tol).mean()) if ok.any() else float("nan")
    return out


def timing_report(matched: pd.DataFrame) -> dict[str, float]:
    """How the two timestamp sources compare on first versions (the cross-check the user asked for)."""
    first = matched[matched["vintage"] == 0]
    has = first["acceptance"].notna()
    lag = (first.loc[has, "snapshot_available_at"] - first.loc[has, "acceptance"]).dt.days
    return {
        "quarters": int(len(first)),
        "edgar_matched_share": float(has.mean()) if len(first) else float("nan"),
        "median_snapshot_lag_days": float(lag.median()) if len(lag) else float("nan"),
        "snapshot_before_filing_share": float((lag < 0).mean()) if len(lag) else float("nan"),
        "restated_quarter_share": float(matched.groupby(["gvkey", "datadate"])["vintage"].max().gt(0).mean())
        if len(matched) else float("nan"),
        "not_pit_exact_share": float((~first["pit_exact"].astype(bool)).mean()) if "pit_exact" in first and len(first)
        else 0.0,
    }


def _num(x: object) -> float:
    return float(x) if x is not None and pd.notna(x) else float("nan")


def to_records(matched: pd.DataFrame, special_items_cash: bool = False) -> list[IssuerFinancials]:
    """One `IssuerFinancials` per version (Section 3.2). Missing values stay NaN, never zero.

    EBITDA_rep = oibdp + special_items; the add-back is -special_items (a charge is negative in Compustat).
    `special_items_cash` sets the cash flag of that add-back; Compustat does not split it, and impairments
    (non-cash) dominate by size, so the default is False.
    Cash interest and cash taxes use the paid figures, and fall back to the expense when the paid figure is missing.
    """
    out: list[IssuerFinancials] = []
    for r in matched.itertuples(index=False):
        spi = _num(r.special_items)
        spi = 0.0 if np.isnan(spi) else spi
        oibdp = _num(r.oibdp)
        items = (NonRecurringItem("special_items", -spi, recurs=False, cash=special_items_cash),) if spi else ()
        interest = _num(r.interest_paid)
        taxes = _num(r.taxes_paid)
        out.append(
            IssuerFinancials(
                key=str(r.gvkey),
                as_of=pd.Timestamp(r.datadate).to_pydatetime(),
                available_at=pd.Timestamp(r.available_at).to_pydatetime(),
                revenue=_num(r.revenue),
                ebitda_reported=oibdp + spi,
                nonrecurring_items=items,
                ebitda_adj_company=oibdp,
                ebitda_covenant=float("nan"),
                cash_interest=interest if not np.isnan(interest) else _num(r.interest_expense),
                cash_taxes=taxes if not np.isnan(taxes) else _num(r.tax_expense),
                capex_total=_num(r.capex),
                capex_maintenance=float("nan"),
                inventory=_num(r.inventory),
                receivables=_num(r.receivables),
                payables=_num(r.payables),
                cogs=_num(r.cogs),
                cash=_num(r.cash),
                debt_current=_num(r.debt_current),
                debt_long_term=_num(r.debt_long_term),
                depreciation=_num(r.depreciation),
                operating_cash_flow=_num(r.operating_cash_flow),
                source=getattr(r, "value_source", SOURCE) or SOURCE,
            )
        )
    return out


def build_store(
    matched: pd.DataFrame, special_items_cash: bool = False, include_inexact: bool = False
) -> PointInTimeStore[IssuerFinancials]:
    """Point-in-time store keyed by gvkey; `store.view(t)` gives the latest quarter as known at t.

    Rows with `pit_exact = False` (fourth quarters filled from latest-known values) stay out unless
    `include_inexact` is True, because their values may contain restatements made after `available_at`.

    `view(t)` returns the most recent fiscal quarter per issuer; `as_known(t)` returns every quarter in the version
    known at t.
    """
    rows = matched if include_inexact or "pit_exact" not in matched else matched[matched["pit_exact"].astype(bool)]
    return PointInTimeStore(to_records(rows, special_items_cash))
