"""Quarters missing from Compustat PIT, rebuilt as first filed from SEC XBRL company facts (Section 3.2).

Compustat PIT history lacks about half of fiscal Q4 quarters and, for some issuers, the latest quarter (see
`compustat_pit`). This module rebuilds each missing quarter from the 10-K or 10-Q that first reported it:
- Balances (cash, debt, working capital) are the filing's instant values at the quarter end.
- Flows are the filing's three-month value when tagged; else its year-to-date value minus the shorter
  year-to-date value as first filed before it (FY minus 9M for a 10-K, 6M minus 3M for a Q2 10-Q).
- `available_at` is the filing's acceptance time.

Definition bridge. XBRL tags and Compustat items define cash, debt, and EBITDA differently (Compustat adds
short-term investments to cash and leases to debt, and strips special items from EBITDA). Cash and total
debt are scaled by Compustat / XBRL in the latest earlier Compustat quarter (both as first reported), so the
series keeps one definition. Both anchor values were public before the gap's filing, so the bridge adds no
look-ahead. A ratio outside [1/3, 3] means the definitions differ too much; the field stays NaN.

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
    "debt_current": ("LongTermDebtCurrent", "DebtCurrent", "NotesPayableCurrent"),
    "debt_long_term": ("LongTermDebtNoncurrent", "LongTermDebtAndCapitalLeaseObligations", "LongTermNotesAndLoans",
                       "LongTermNotesPayable"),
    "debt_total": ("LongTermDebt", "DebtInstrumentCarryingAmount", "DebtAndCapitalLeaseObligations"),
}


def company_facts(cik: int | str, fetch: Fetch = fetch_json, cache_root: Path | None = None,
                  refresh: bool = False) -> pd.DataFrame:
    """Long table of USD us-gaap facts: tag, start, end, val, accn, form, filed. Caches the JSON."""
    cik10 = _cik10(cik)
    path = cache_root / "edgar" / f"companyfacts_CIK{cik10}.json" if cache_root else None
    if path is not None and path.exists() and not refresh:
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
        # Filers occasionally key in impossible years; they would overflow date arithmetic.
        df.loc[(df[c].dt.year < 1990) | (df[c].dt.year > 2100), c] = pd.NaT
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


def _instant(facts: pd.DataFrame, tags: Sequence[str], qend: pd.Timestamp, accn: str) -> tuple[float, str | None]:
    """First tag in `tags` with an instant value at `qend` in filing `accn`: (value, tag), else (NaN, None)."""
    for tag in tags:
        t = facts[(facts["tag"] == tag) & facts["start"].isna() & _near(facts["end"], qend) & (facts["accn"] == accn)]
        if len(t):
            return float(t["val"].iloc[0]), tag
    return float("nan"), None


# Cash is bridged on its own; debt is bridged as a total, because filers tag the current / non-current split
# inconsistently and Compustat adds leases and financing obligations (Caesars: about 2x the XBRL debt).
BRIDGE_RANGE = (1 / 3, 3.0)
# EBITDA is not bridged: the prior-quarter ratio carries that quarter's special items. It is kept unscaled only
# when the prior quarter shows the two definitions agree within this range; otherwise it is NaN.
CHECKED = ("oibdp",)
CHECK_RANGE = (0.8, 1.25)


def quarter_from_filing(
    facts: pd.DataFrame, qend: pd.Timestamp, accn: str, filed: pd.Timestamp, force_tags: dict[str, str] | None = None
) -> dict:
    """All loader fields for one quarter, in USD millions, as first filed in the 10-Q or 10-K `accn`.

    `v["_tags"]` records which tag supplied each instant field ("parts" for a debt total summed from its parts).
    `force_tags` restricts an instant field to one tag, so a bridge compares like with like across quarters.
    """
    force_tags = force_tags or {}
    v: dict = {name: _flow(facts, tags, qend, accn, filed) / 1e6 for name, tags in FLOW_TAGS.items()}
    v["_tags"] = {}
    for name, tags in INSTANT_TAGS.items():
        forced = force_tags.get(name)
        use = (forced,) if forced and forced != "parts" else (() if forced == "parts" else tags)
        val, tag = _instant(facts, use, qend, accn)
        v[name], v["_tags"][name] = val / 1e6, tag
    if not np.isnan(v["operating_income"]):
        v["oibdp"] = v["operating_income"] + v["depreciation"]
    else:
        v["oibdp"] = v["pretax_income"] + v["interest_expense"] + v["depreciation"]
    v["special_items"] = 0.0  # included in oibdp; XBRL does not split it out
    if np.isnan(v["debt_total"]) and not np.isnan(v["debt_long_term"]):
        v["debt_total"] = v["debt_long_term"] + (0.0 if np.isnan(v["debt_current"]) else v["debt_current"])
        v["_tags"]["debt_total"] = "parts"
    return v


def _num(x) -> float:
    """float(x), with pandas NA and None as NaN (Compustat rows carry pandas NA for missing values)."""
    return float(x) if x is not None and pd.notna(x) else float("nan")


def _bridge_debt(vals: dict[str, float], anchor_compustat: pd.Series, anchor_xbrl: dict[str, float]) -> list[str]:
    """Scale total debt by the anchor's Compustat / XBRL total-debt ratio, then split it (in place).

    Compustat total = dlcq + dlttq (a missing current part counts as 0). The current part keeps the filed
    current debt times the same ratio; the long-term part is the remainder. When the filing has no current debt,
    the whole total goes to `debt_long_term`, `debt_current` is 0, and the label `debt_split_unknown` is returned.
    """
    cur_c = float(anchor_compustat["debt_current"]) if pd.notna(anchor_compustat["debt_current"]) else 0.0
    lt_c = _num(anchor_compustat["debt_long_term"])  # pandas NA: the anchor has no long-term debt figure
    r = bridge_ratio(cur_c + lt_c, anchor_xbrl["debt_total"])
    total = vals["debt_total"] * r
    if np.isnan(total):
        vals["debt_current"] = vals["debt_long_term"] = float("nan")
        return []
    if np.isnan(vals["debt_current"]):
        vals["debt_current"], vals["debt_long_term"] = 0.0, total
        return ["debt", "debt_split_unknown"]
    vals["debt_current"] = vals["debt_current"] * r
    vals["debt_long_term"] = total - vals["debt_current"]
    return ["debt"]


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


BRIDGE_LOOKBACK_DAYS = 400


def _bridge_anchor(g, d, pit_first, facts, filings, cik10, force_tags=None):
    """Most recent first-version Compustat PIT quarter before `d` (within `BRIDGE_LOOKBACK_DAYS`) that also has a
    filing, with its XBRL values. The latest Compustat quarters are often missing too, so the anchor may sit two
    or three quarters back; balance-sheet definition gaps are stable over that span."""
    if pit_first is None:
        return None, None
    cand = pit_first[(pit_first["gvkey"] == g) & (pit_first["datadate"] < d)
                     & ((d - pit_first["datadate"]).dt.days <= BRIDGE_LOOKBACK_DAYS)]
    for _, row in cand.sort_values("datadate", ascending=False).iterrows():
        filing = _first_filing(filings, cik10, row["datadate"])
        if filing is not None:
            return row, quarter_from_filing(facts, row["datadate"], filing["accession"], filing["filing_date"], force_tags)
    return None, None


def fill_quarters(
    gaps: pd.DataFrame,
    facts_by_cik: dict[str, pd.DataFrame],
    filings: pd.DataFrame,
    cik_by_gvkey: dict[str, str],
    pit_first: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Rebuild each (gvkey, datadate) in `gaps` from the filing that first reported it; skip rows with no filing.

    `pit_first` holds first-version Compustat PIT rows. Cash and total debt are scaled by the Compustat / XBRL
    ratio of the most recent PIT quarter with a filing (see `_bridge_anchor` and `_bridge_debt`); `bridged` lists
    what was scaled. `CHECKED` fields are kept only when that quarter's ratio lies in `CHECK_RANGE`. Without an
    anchor quarter, cash, debt, and the checked fields stay NaN. A quarter with neither revenue nor EBITDA is skipped.
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
        # The anchor must use the same XBRL tags as the gap quarter, or the ratio mixes definitions.
        same = {k: t for k, t in vals["_tags"].items() if k in ("cash", "debt_total", "debt_current") and t}
        prior_row, prior_vals = _bridge_anchor(g, d, pit_first, facts, filings, cik10, same)
        if prior_row is None:
            for f in ("cash", "debt_current", "debt_long_term", *CHECKED):
                vals[f] = float("nan")
        else:
            vals["cash"] = vals["cash"] * bridge_ratio(_num(prior_row["cash"]), prior_vals["cash"])
            if not np.isnan(vals["cash"]):
                bridged.append("cash")
            bridged += _bridge_debt(vals, prior_row, prior_vals)
            for f in CHECKED:
                if np.isnan(bridge_ratio(_num(prior_row[f]), prior_vals[f], CHECK_RANGE)):
                    vals[f] = float("nan")
        if np.isnan(vals["revenue"]) and np.isnan(vals["oibdp"]):
            continue  # nothing usable was filed under known tags; keep the flagged Compustat row
        vals.pop("_tags", None)
        rows.append({"gvkey": g, "datadate": d, **vals, "bridged": ",".join(bridged)})
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["vintage"] = 0
    out["snapshot_available_at"] = pd.NaT
    out["pit_exact"] = True
    out["value_source"] = "edgar_xbrl"
    return out


CASH_FLOW_FIELDS = ("operating_cash_flow", "capex", "interest_paid", "taxes_paid")


def cash_flow_from_filing(facts: pd.DataFrame, filings: pd.DataFrame, cik: int | str, qend: pd.Timestamp,
                          decision: pd.Timestamp) -> dict:
    """Quarter cash flows (USD millions) from the first 10-Q or 10-K that reported quarter `qend` (methodology 3.2).

    For a quarter whose Compustat year-to-date figures could not be de-cumulated (the predecessor quarter was missing
    from the same snapshot). Point in time: the filing must be accepted on or before `decision`, else {} (no
    look-ahead). Each flow is the 3-month value of that filing, else its YTD value less the shorter YTD (`_flow`).
    Intuition: the filing itself states the quarter; read it when the vendor's subtraction fails.
    """
    first = _first_filing(filings, _cik10(cik), pd.Timestamp(qend))
    if first is None or pd.Timestamp(first["acceptance"]) > pd.Timestamp(decision):
        return {}
    out = {f: _flow(facts, FLOW_TAGS[f], pd.Timestamp(qend), first["accession"], first["filing_date"]) / 1e6
           for f in CASH_FLOW_FIELDS}
    out["accession"] = first["accession"]
    out["available_at"] = pd.Timestamp(first["acceptance"])
    return out
