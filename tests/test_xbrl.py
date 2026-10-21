import numpy as np
import pandas as pd
import pytest

from hy.sources import financials, xbrl

CIK = "0000860730"
G = "022260"
Q3, Q4 = pd.Timestamp("2024-09-30"), pd.Timestamp("2024-12-31")
FY0 = pd.Timestamp("2024-01-01")


def _fact(tag, val, end, accn, filed, start=None):
    start = pd.Timestamp(start) if start else pd.NaT
    end = pd.Timestamp(end)
    return {"tag": tag, "start": start, "end": end, "val": val, "accn": accn, "form": None,
            "filed": pd.Timestamp(filed), "days": (end - start).days if start is not pd.NaT else np.nan}


def _facts(**over):
    rows = [
        # 9M as first filed in the Q3 10-Q, under a different revenue tag than the 10-K uses
        _fact("RevenueFromContractWithCustomerIncludingAssessedTax", 51e9, Q3, "q3", "2024-10-31", FY0),
        _fact("Revenues", 70e9, Q4, "k", "2025-02-14", FY0),
        # later comparative restates 9M; must be ignored because it was filed after the 10-K
        _fact("Revenues", 50e9, Q3, "q3next", "2025-10-30", FY0),
        _fact("PaymentsToAcquirePropertyPlantAndEquipment", 3.6e9, Q3, "q3", "2024-10-31", FY0),
        _fact("PaymentsToAcquirePropertyPlantAndEquipment", 4.9e9, Q4, "k", "2025-02-14", FY0),
        # three-month operating income tagged directly in the 10-K
        _fact("OperatingIncomeLoss", 2.6e9, Q4, "k", "2025-02-14", "2024-10-01"),
        _fact("DepreciationDepletionAndAmortization", 0.9e9, Q4, "k", "2025-02-14", "2024-10-01"),
        _fact("OperatingIncomeLoss", 2.4e9, Q3, "q3", "2024-10-31", "2024-07-01"),
        _fact("DepreciationDepletionAndAmortization", 0.85e9, Q3, "q3", "2024-10-31", "2024-07-01"),
        _fact("CashAndCashEquivalentsAtCarryingValue", 1.9e9, Q4, "k", "2025-02-14"),
        _fact("CashAndCashEquivalentsAtCarryingValue", 1.0e9, Q3, "q3", "2024-10-31"),
        _fact("LongTermDebtNoncurrent", 38e9, Q4, "k", "2025-02-14"),
        _fact("LongTermDebtNoncurrent", 37e9, Q3, "q3", "2024-10-31"),
    ]
    return pd.DataFrame(rows)


FILINGS = pd.DataFrame({"cik": CIK, "form": ["10-Q", "10-K"], "report_date": [Q3, Q4],
                        "accession": ["q3", "k"], "filing_date": pd.to_datetime(["2024-10-31", "2025-02-14"]),
                        "acceptance": pd.to_datetime(["2024-10-31 20:30", "2025-02-14 21:00"])})


def test_flows_use_fy_minus_nine_months_as_first_filed_across_tag_switch():
    v = xbrl.quarter_from_filing(_facts(), Q4, "k", pd.Timestamp("2025-02-14"))
    assert v["revenue"] == pytest.approx(19_000.0)  # 70bn - 51bn (first-filed 9M), not 70 - 50
    assert v["capex"] == pytest.approx(1_300.0)
    assert v["oibdp"] == pytest.approx(3_500.0)  # direct 3-month operating income + D&A


def test_bridge_scales_balances_by_prior_quarter_ratio():
    pit_prior = pd.DataFrame({"gvkey": [G], "datadate": [Q3], "cash": [1_100.0], "debt_current": [np.nan],
                              "debt_long_term": [38_850.0], "oibdp": [3_250.0]})
    out = xbrl.fill_quarters(pd.DataFrame({"gvkey": [G], "datadate": [Q4]}), {CIK: _facts()}, FILINGS,
                             {G: "860730"}, pit_first=pit_prior).iloc[0]
    assert out["cash"] == pytest.approx(1_900.0 * 1.1)
    assert out["debt_long_term"] == pytest.approx(38_000.0 * 1.05)
    assert out["oibdp"] == pytest.approx(3_500.0)  # checked, not scaled: prior ratio 3250/3250 = 1
    assert out["bridged"] == "cash,debt,debt_split_unknown" and out["pit_exact"]


def test_ebitda_dropped_when_definitions_disagree():
    pit_prior = pd.DataFrame({"gvkey": [G], "datadate": [Q3], "cash": [1_000.0], "debt_current": [np.nan],
                              "debt_long_term": [37_000.0], "oibdp": [6_000.0]})  # ratio 1.85: out of range
    out = xbrl.fill_quarters(pd.DataFrame({"gvkey": [G], "datadate": [Q4]}), {CIK: _facts()}, FILINGS,
                             {G: "860730"}, pit_first=pit_prior).iloc[0]
    assert np.isnan(out["oibdp"]) and out["revenue"] == pytest.approx(19_000.0)


def test_bridge_ratio_bounds():
    assert xbrl.bridge_ratio(110.0, 100.0) == pytest.approx(1.1)
    assert np.isnan(xbrl.bridge_ratio(400.0, 100.0))
    assert np.isnan(xbrl.bridge_ratio(np.nan, 100.0))
    assert np.isnan(xbrl.bridge_ratio(1.0, 0.0))


def test_quarter_without_usable_facts_is_skipped_and_flag_row_kept():
    empty = _facts().iloc[0:0]
    gaps = pd.DataFrame({"gvkey": [G], "datadate": [Q4], "pit_exact": [False], "vintage": [0],
                         "snapshot_available_at": [pd.NaT], "revenue": [18_285.0]})
    filled = xbrl.fill_quarters(gaps, {CIK: empty}, FILINGS, {G: "860730"})
    assert filled.empty
    kept = financials.replace_inexact(gaps, filled)
    assert kept["value_source"].tolist() == ["compustat_current"]


def test_replace_inexact_swaps_only_flagged_rows():
    v = pd.DataFrame({"gvkey": [G, G], "datadate": [Q3, Q4], "pit_exact": [True, False], "vintage": [0, 0],
                      "revenue": [17_000.0, 18_000.0]})
    filled = pd.DataFrame({"gvkey": [G, G], "datadate": [Q3, Q4], "revenue": [1.0, 19_000.0], "vintage": [0, 0],
                           "pit_exact": [True, True], "value_source": ["edgar_xbrl"] * 2})
    out = financials.replace_inexact(v, filled).set_index("datadate")
    assert out.loc[Q3, "revenue"] == 17_000.0 and out.loc[Q3, "value_source"] == "compustat_pit"
    assert out.loc[Q4, "revenue"] == 19_000.0 and out.loc[Q4, "value_source"] == "edgar_xbrl"


def test_bridge_anchors_on_latest_pit_quarter_when_prior_is_also_missing():
    q2 = pd.Timestamp("2024-06-30")
    facts = pd.concat([_facts(), pd.DataFrame([
        _fact("CashAndCashEquivalentsAtCarryingValue", 0.8e9, q2, "q2", "2024-08-01"),
        _fact("LongTermDebtNoncurrent", 36e9, q2, "q2", "2024-08-01")])], ignore_index=True)
    filings = pd.concat([FILINGS, pd.DataFrame({"cik": [CIK], "form": ["10-Q"], "report_date": [q2], "accession": ["q2"],
                                                "filing_date": [pd.Timestamp("2024-08-01")],
                                                "acceptance": [pd.Timestamp("2024-08-01 20:30")]})], ignore_index=True)
    pit = pd.DataFrame({"gvkey": [G], "datadate": [q2], "cash": [880.0], "debt_current": [np.nan],
                        "debt_long_term": [37_800.0], "oibdp": [np.nan]})  # Q3 absent from PIT too
    out = xbrl.fill_quarters(pd.DataFrame({"gvkey": [G], "datadate": [Q4]}), {CIK: facts}, filings,
                             {G: "860730"}, pit_first=pit).iloc[0]
    assert out["cash"] == pytest.approx(1_900.0 * 1.1)
    assert out["debt_long_term"] == pytest.approx(38_000.0 * 1.05)
    too_old = pit.assign(datadate=pd.Timestamp("2023-06-30"))
    out_old = xbrl.fill_quarters(pd.DataFrame({"gvkey": [G], "datadate": [Q4]}), {CIK: facts}, filings,
                                 {G: "860730"}, pit_first=too_old).iloc[0]
    assert np.isnan(out_old["cash"])  # anchor beyond the 400-day lookback


def test_total_debt_bridge_keeps_lease_heavy_definition_and_split():
    # Caesars-like: Compustat debt is twice the XBRL debt (leases); the filing tags both parts.
    facts = pd.concat([_facts(), pd.DataFrame([
        _fact("LongTermDebtCurrent", 1e9, Q4, "k", "2025-02-14"),
        _fact("LongTermDebtCurrent", 1e9, Q3, "q3", "2024-10-31")])], ignore_index=True)
    pit = pd.DataFrame({"gvkey": [G], "datadate": [Q3], "cash": [1_000.0], "debt_current": [2_000.0],
                        "debt_long_term": [74_000.0], "oibdp": [3_250.0]})  # total 76bn vs XBRL 38bn -> ratio 2
    out = xbrl.fill_quarters(pd.DataFrame({"gvkey": [G], "datadate": [Q4]}), {CIK: facts}, FILINGS,
                             {G: "860730"}, pit_first=pit).iloc[0]
    assert out["debt_current"] + out["debt_long_term"] == pytest.approx(2 * 39_000.0)
    assert out["debt_current"] == pytest.approx(2_000.0)
    assert "debt_split_unknown" not in out["bridged"]
