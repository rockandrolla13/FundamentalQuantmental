"""Quarters missing from Compustat PIT, rebuilt as first filed from SEC XBRL company facts (Section 3.2).

Compustat PIT history lacks about half of fiscal Q4 quarters and, for some issuers, the latest quarter (see
`compustat_pit`). This module rebuilds each missing quarter from the 10-K or 10-Q that first reported it:
- Balances (cash, debt, working capital) are the filing's instant values at the quarter end.
- Flows are the filing's three-month value when tagged; else its year-to-date value minus the shorter
  year-to-date value as first filed before it (FY minus 9M for a 10-K, 6M minus 3M for a Q2 10-Q).
- `available_at` is the filing's acceptance time.

Definition bridge. XBRL tags and Compustat items define cash, debt, and EBITDA differently (Compustat adds
short-term investments to cash and finance leases to debt, and strips special items from EBITDA). For the
fields in `BRIDGED`, the rebuilt value is scaled by Compustat / XBRL in the prior quarter, both as first
reported, so the series keeps one definition. Both prior values were public before the gap's filing, so the
bridge adds no look-ahead. A ratio outside [0.5, 2] means the definitions differ too much; the field stays NaN.

Source: https://data.sec.gov/api/xbrl/companyfacts/CIK##########.json. Values arrive in USD and leave in
USD millions to match Compustat. Tags differ by filer, so each field tries an ordered list of tags.

EBITDA here is GAAP operating income plus D&A, or pre-tax income plus interest plus D&A when the filer tags
no operating income. Either way it includes special items, which XBRL does not split out; the record has
no add-back, so adjusted EBITDA equals reported EBITDA for these quarters.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path

import numpy as np
import pandas as pd

from hy.sources.edgar import Fetch, _cik10, fetch_json

BASE = "https://data.sec.gov/api/xbrl/companyfacts/"
TOLERANCE_DAYS = 10

FLOW_TAGS: dict[str, tuple[str, ...]] = {
    "revenue": ("Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "SalesRevenueNet",
                "RevenueFromContractWithCustomerIncludingAssessedTax",
                "HealthCareOrganizationPatientServiceRevenueLessProvisionForBadDebts", "HealthCareOrganizationRevenue"),
    "operating_income": ("OperatingIncomeLoss",),
    "pretax_income": ("IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
                      "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments"),
    "depreciation": ("DepreciationDepletionAndAmortization", "DepreciationAndAmortization",
                     "DepreciationAmortizationAndAccretionNet", "Depreciation"),
    "interest_expense": ("InterestExpense", "InterestExpenseNonoperating", "InterestExpenseDebt"),
    "tax_expense": ("IncomeTaxExpenseBenefit",),
    "cogs": ("CostOfRevenue", "CostOfGoodsAndServicesSold", "CostOfGoodsSold"),
    "sga": ("SellingGeneralAndAdministrativeExpense",),
    "capex": ("PaymentsToAcquirePropertyPlantAndEquipment", "PaymentsToAcquireProductiveAssets"),
    "operating_cash_flow": ("NetCashProvidedByUsedInOperatingActivities",
                            "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations"),
    "interest_paid": ("InterestPaidNet", "InterestPaid"),
    "taxes_paid": ("IncomeTaxesPaidNet", "IncomeTaxesPaid"),
}
INSTANT_TAGS: dict[str, tuple[str, ...]] = {
    "cash": ("CashAndCashEquivalentsAtCarryingValue",
             "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"),
    "inventory": ("InventoryNet",),
    "receivables": ("AccountsReceivableNetCurrent",),
    "payables": ("AccountsPayableCurrent",),
    "debt_current": ("LongTermDebtCurrent", "DebtCurrent"),
    "debt_long_term": ("LongTermDebtNoncurrent", "LongTermDebtAndCapitalLeaseObligations"),
}


def company_facts(cik: int | str, fetch: Fetch = fetch_json, cache_root: Path | None = None) -> pd.DataFrame:
    """Long table of USD us-gaap facts: tag, start, end, val, accn, form, filed. Caches the JSON."""
    cik10 = _cik10(cik)
    path = cache_root / "edgar" / f"companyfacts_CIK{cik10}.json" if cache_root else None
    if path is not None and path.exists():
        doc = json.loads(path.read_text())
    else:
        doc = fetch(f"{BASE}CIK{cik10}.json")
        if path is not None:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(doc))
    rows = []
    for tag, body in doc.get("facts", {}).get("us-gaap", {}).items():
        for f in body.get("units", {}).get("USD", []):
            rows.append((tag, f.get("start"), f["end"], f["val"], f["accn"], f.get("form"), f.get("filed")))
    df = pd.DataFrame(rows, columns=["tag", "start", "end", "val", "accn", "form", "filed"])
    for c in ("start", "end", "filed"):
        df[c] = pd.to_datetime(df[c], errors="coerce")
    df["days"] = (df["end"] - df["start"]).dt.days
    return df


def _near(s: pd.Series, d: pd.Timestamp) -> pd.Series:
    return (s - d).dt.days.abs() <= TOLERANCE_DAYS


def _flow(facts: pd.DataFrame, tags: Sequence[str], qend: pd.Timestamp, accn: str, filed: pd.Timestamp) -> float:
    """Quarter flow for the first tag that yields one: 3-month value from filing `accn`, else its YTD value minus
    the YTD value one quarter shorter (same start) as first filed on or before `filed`."""
    for tag in tags:
        t = facts[(facts["tag"] == tag) & _near(facts["end"], qend)]
        k = t[t["accn"] == accn]
        q = k[k["days"].between(80, 100)]
        if len(q):
            return float(q["val"].iloc[0])
        ytd = k[k["days"] > 100].sort_values("days")
        if not len(ytd):
            continue
        top = ytd.iloc[-1]
        # Filers switch tags between filings, so the shorter YTD may sit under another tag of the same family.
        prior = facts[facts["tag"].isin(tags) & (facts["start"] == top["start"])
                      & (facts["days"] - top["days"] + 91).abs().le(15) & (facts["filed"] <= filed)]
        if len(prior):
            prior = prior.assign(other_tag=prior["tag"] != tag).sort_values(["other_tag", "filed"])
            return float(top["val"] - prior.iloc[0]["val"])
    return float("nan")


def _instant(facts: pd.DataFrame, tags: Sequence[str], qend: pd.Timestamp, accn: str) -> float:
    for tag in tags:
        t = facts[(facts["tag"] == tag) & facts["start"].isna() & _near(facts["end"], qend) & (facts["accn"] == accn)]
        if len(t):
            return float(t["val"].iloc[0])
    return float("nan")


BRIDGED = ("cash", "debt_current", "debt_long_term")
BRIDGE_RANGE = (0.5, 2.0)
# EBITDA is not bridged: the prior-quarter ratio carries that quarter's special items. It is kept unscaled only
# when the prior quarter shows the two definitions agree within this range; otherwise it is NaN.
CHECKED = ("oibdp",)
CHECK_RANGE = (0.8, 1.25)


def quarter_from_filing(facts: pd.DataFrame, qend: pd.Timestamp, accn: str, filed: pd.Timestamp) -> dict[str, float]:
    """All loader fields for one quarter, in USD millions, as first filed in the 10-Q or 10-K `accn`."""
    v = {name: _flow(facts, tags, qend, accn, filed) / 1e6 for name, tags in FLOW_TAGS.items()}
    v.update({name: _instant(facts, tags, qend, accn) / 1e6 for name, tags in INSTANT_TAGS.items()})
    if not np.isnan(v["operating_income"]):
        v["oibdp"] = v["operating_income"] + v["depreciation"]
    else:
        v["oibdp"] = v["pretax_income"] + v["interest_expense"] + v["depreciation"]
    v["special_items"] = 0.0  # included in oibdp; XBRL does not split it out
    return v


def _first_filing(filings: pd.DataFrame, cik10: str, qend: pd.Timestamp) -> pd.Series | None:
    f = filings[(filings["cik"] == cik10) & filings["form"].isin(["10-Q", "10-K", "10-KT", "10-QT"])
                & _near(filings["report_date"], qend) & (filings["acceptance"] > qend)]
    return f.sort_values("acceptance").iloc[0] if len(f) else None


def bridge_ratio(compustat_prior: float, xbrl_prior: float, bounds: tuple[float, float] = BRIDGE_RANGE) -> float:
    """Compustat / XBRL for one field in the prior quarter; NaN when undefined or outside `bounds`."""
    if any(np.isnan(x) for x in (compustat_prior, xbrl_prior)) or xbrl_prior == 0:
        return float("nan")
    r = compustat_prior / xbrl_prior
    return r if bounds[0] <= r <= bounds[1] else float("nan")


def fill_quarters(
    gaps: pd.DataFrame,
    facts_by_cik: dict[str, pd.DataFrame],
    filings: pd.DataFrame,
    cik_by_gvkey: dict[str, str],
    pit_first: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Rebuild each (gvkey, datadate) in `gaps` from the filing that first reported it; skip rows with no filing.

    `pit_first` holds first-version Compustat PIT rows; when given, `BRIDGED` fields are scaled by the
    prior-quarter Compustat / XBRL ratio and `bridged` lists the fields that were scaled, and `CHECKED` fields
    are kept only when the prior-quarter ratio lies in `CHECK_RANGE`. Without a usable prior quarter, those
    fields stay NaN. A quarter with neither revenue nor EBITDA is skipped.
    Output columns match the Compustat vintages, with `pit_exact = True`, `value_source = "edgar_xbrl"`,
    and no snapshot date.
    """
    rows = []
    for g, d in zip(gaps["gvkey"], gaps["datadate"]):
        cik = cik_by_gvkey.get(g)
        if cik is None or pd.isna(cik):
            continue
        cik10 = _cik10(cik)
        facts = facts_by_cik.get(cik10)
        first = _first_filing(filings, cik10, d)
        if facts is None or first is None:
            continue
        vals = quarter_from_filing(facts, d, first["accession"], first["filing_date"])
        bridged = []
        prior_row = None
        if pit_first is not None:
            cand = pit_first[(pit_first["gvkey"] == g) & (d - pit_first["datadate"]).dt.days.between(80, 100)]
            prior_row = cand.iloc[0] if len(cand) else None
        prior_filing = _first_filing(filings, cik10, prior_row["datadate"]) if prior_row is not None else None
        prior_vals = (quarter_from_filing(facts, prior_row["datadate"], prior_filing["accession"], prior_filing["filing_date"])
                      if prior_filing is not None else None)
        for f in BRIDGED:
            r = bridge_ratio(float(prior_row[f]), prior_vals[f]) if prior_vals is not None else float("nan")
            vals[f] = vals[f] * r
            if not np.isnan(vals[f]):
                bridged.append(f)
        for f in CHECKED:
            r = bridge_ratio(float(prior_row[f]), prior_vals[f], CHECK_RANGE) if prior_vals is not None else float("nan")
            if np.isnan(r):
                vals[f] = float("nan")
        if np.isnan(vals["revenue"]) and np.isnan(vals["oibdp"]):
            continue  # nothing usable was filed under known tags; keep the flagged Compustat row
        rows.append({"gvkey": g, "datadate": d, **vals, "bridged": ",".join(bridged)})
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["vintage"] = 0
    out["snapshot_available_at"] = pd.NaT
    out["pit_exact"] = True
    out["value_source"] = "edgar_xbrl"
    return out
