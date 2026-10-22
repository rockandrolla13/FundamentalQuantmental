import numpy as np
import pandas as pd
import pytest

from hy import clocks
from hy.sources import schedules as sc
from hy.sources import xbrl_instance as xi


def test_grid_conserves_mass_and_splits_partial_years():
    g = clocks.to_grid([clocks.Bucket(0.5, 1.0, 100.0), clocks.Bucket(3.0, 30.0, 300.0)], horizon=10)
    assert g.sum() == pytest.approx(400.0)
    assert g[0] == pytest.approx(50.0) and g[1] == pytest.approx(50.0)
    assert g[-1] == pytest.approx(10.0 + 300.0 * 23 / 30)  # mass past the horizon lands in the last year


def test_tail_runs_at_last_stated_rate():
    amounts = [1028.0, 2116.0, 2306.0, 2373.0, 2289.0, 19023.0]  # CoreWeave Jun-2026 operating lease ladder
    assert clocks.tail_years_run_rate(amounts) == pytest.approx(19023.0 / 2289.0)
    assert clocks.tail_years_run_rate([100.0, 0.0, 50.0]) == 5.0  # no rate to extend


def test_uncommenced_and_rpo_keep_totals():
    assert clocks.to_grid(clocks.uncommenced(35_500.0, 0.0, 3.5, 11.5), 40).sum() == pytest.approx(35_500.0)
    r = clocks.rpo(103_700.0, [(0.0, 2.0, 0.41), (2.0, 4.0, 0.39)], tail_years=2.0)
    g = clocks.to_grid(r, 20)
    assert g.sum() == pytest.approx(103_700.0)
    assert g[:2].sum() == pytest.approx(0.41 * 103_700.0)
    assert clocks.runoff_year(g) == 8.0


def test_interest_falls_with_the_balance():
    principal = clocks.ladder([100.0, 100.0, 0.0], 1.0, 1.0)
    i = clocks.interest(principal, 200.0, 0.10, 5)
    assert i[0] == pytest.approx(15.0) and i[1] == pytest.approx(5.0) and i[2] == 0.0


def test_mismatch_on_a_known_case():
    # 10 years of rent at 10/yr against 3 years of contracts at 40/yr, full cash margin.
    res = clocks.mismatch({"rent": [clocks.Bucket(0, 10, 100.0)]}, [clocks.Bucket(0, 3, 120.0)], 1.0, horizon=12)
    m = res.metrics
    assert m["dur_obligations"] == pytest.approx(5.0) and m["dur_revenue"] == pytest.approx(1.5)
    assert m["duration_gap"] == pytest.approx(3.5)
    assert m["revenue_runoff"] == 3.0 and m["renewal_dependent_share"] == pytest.approx(0.7)
    assert np.isnan(m["first_shortfall_year"])  # 120 of cash front-loaded against 100 of rent: never short
    assert m["breakeven_margin"] == pytest.approx(100.0 / 120.0)
    rr = clocks.mismatch({"rent": [clocks.Bucket(0, 10, 100.0)]}, [clocks.Bucket(0, 3, 120.0)], 0.5, 12,
                         run_rate_revenue=40.0).metrics
    assert rr["renewal_revenue_years"] == pytest.approx(70.0 / 0.5 / 40.0)  # 70 of rent after year 3
    short = clocks.mismatch({"rent": [clocks.Bucket(0, 10, 100.0)]}, [clocks.Bucket(0, 3, 120.0)], 0.5, 12).metrics
    assert short["first_shortfall_year"] == 7.0 and short["max_cum_shortfall"] == pytest.approx(40.0)


def test_concentration_floor_and_undisclosed():
    c = clocks.concentration({"A": 0.36, "B": 0.26, "C": 0.10})
    assert c["top3"] == pytest.approx(0.72) and c["hhi_floor"] == pytest.approx(0.36**2 + 0.26**2 + 0.01)
    assert np.isnan(clocks.concentration({})["top3"])  # not disclosed is not zero


XML = b"""<?xml version="1.0"?>
<xbrli:xbrl xmlns:xbrli="http://www.xbrl.org/2003/instance" xmlns:us-gaap="http://fasb.org/us-gaap/2025"
 xmlns:dei="http://xbrl.sec.gov/dei/2025" xmlns:xbrldi="http://xbrl.org/2006/xbrldi" xmlns:srt="http://fasb.org/srt/2025"
 xmlns:crwv="http://coreweave.com/2026">
 <xbrli:context id="i"><xbrli:entity><xbrli:identifier scheme="x">1</xbrli:identifier></xbrli:entity>
  <xbrli:period><xbrli:instant>2026-06-30</xbrli:instant></xbrli:period></xbrli:context>
 <xbrli:context id="q"><xbrli:entity><xbrli:identifier scheme="x">1</xbrli:identifier></xbrli:entity>
  <xbrli:period><xbrli:startDate>2026-04-01</xbrli:startDate><xbrli:endDate>2026-06-30</xbrli:endDate></xbrli:period></xbrli:context>
 <xbrli:context id="h"><xbrli:entity><xbrli:identifier scheme="x">1</xbrli:identifier></xbrli:entity>
  <xbrli:period><xbrli:startDate>2026-01-01</xbrli:startDate><xbrli:endDate>2026-06-30</xbrli:endDate></xbrli:period></xbrli:context>
 <xbrli:context id="w1"><xbrli:entity><xbrli:identifier scheme="x">1</xbrli:identifier><xbrli:segment>
  <xbrldi:typedMember dimension="us-gaap:RevenueRemainingPerformanceObligationExpectedTimingOfSatisfactionStartDateAxis"><x>2026-07-01</x></xbrldi:typedMember>
  </xbrli:segment></xbrli:entity><xbrli:period><xbrli:instant>2026-06-30</xbrli:instant></xbrli:period></xbrli:context>
 <xbrli:context id="w2"><xbrli:entity><xbrli:identifier scheme="x">1</xbrli:identifier><xbrli:segment>
  <xbrldi:typedMember dimension="us-gaap:RevenueRemainingPerformanceObligationExpectedTimingOfSatisfactionStartDateAxis"><x>2028-07-01</x></xbrldi:typedMember>
  </xbrli:segment></xbrli:entity><xbrli:period><xbrli:instant>2026-06-30</xbrli:instant></xbrli:period></xbrli:context>
 <xbrli:context id="ca"><xbrli:entity><xbrli:identifier scheme="x">1</xbrli:identifier><xbrli:segment>
  <xbrldi:explicitMember dimension="srt:MajorCustomersAxis">crwv:CustomerAMember</xbrldi:explicitMember>
  <xbrldi:explicitMember dimension="us-gaap:ConcentrationRiskByBenchmarkAxis">us-gaap:RevenueFromContractWithCustomerMember</xbrldi:explicitMember>
  </xbrli:segment></xbrli:entity><xbrli:period><xbrli:startDate>2026-04-01</xbrli:startDate><xbrli:endDate>2026-06-30</xbrli:endDate></xbrli:period></xbrli:context>
 <xbrli:context id="cah"><xbrli:entity><xbrli:identifier scheme="x">1</xbrli:identifier><xbrli:segment>
  <xbrldi:explicitMember dimension="srt:MajorCustomersAxis">crwv:CustomerAMember</xbrldi:explicitMember>
  <xbrldi:explicitMember dimension="us-gaap:ConcentrationRiskByBenchmarkAxis">us-gaap:RevenueFromContractWithCustomerMember</xbrldi:explicitMember>
  </xbrli:segment></xbrli:entity><xbrli:period><xbrli:startDate>2026-01-01</xbrli:startDate><xbrli:endDate>2026-06-30</xbrli:endDate></xbrli:period></xbrli:context>
 <xbrli:context id="dc"><xbrli:entity><xbrli:identifier scheme="x">1</xbrli:identifier><xbrli:segment>
  <xbrldi:explicitMember dimension="us-gaap:PropertyPlantAndEquipmentByTypeAxis">crwv:DataCenterAndOfficeBuildingsMember</xbrldi:explicitMember>
  </xbrli:segment></xbrli:entity><xbrli:period><xbrli:instant>2026-06-30</xbrli:instant></xbrli:period></xbrli:context>
 <dei:CurrentFiscalYearEndDate contextRef="i">--12-31</dei:CurrentFiscalYearEndDate>
 <us-gaap:LongTermDebtMaturitiesRepaymentsOfPrincipalRemainderOfFiscalYear contextRef="i" unitRef="usd">4413000000</us-gaap:LongTermDebtMaturitiesRepaymentsOfPrincipalRemainderOfFiscalYear>
 <us-gaap:LongTermDebtMaturitiesRepaymentsOfPrincipalInNextTwelveMonths contextRef="i" unitRef="usd">6184000000</us-gaap:LongTermDebtMaturitiesRepaymentsOfPrincipalInNextTwelveMonths>
 <us-gaap:LongTermDebtMaturitiesRepaymentsOfPrincipalInYearTwo contextRef="i" unitRef="usd">4416000000</us-gaap:LongTermDebtMaturitiesRepaymentsOfPrincipalInYearTwo>
 <crwv:LongTermDebtMaturityAfterYearFour contextRef="i" unitRef="usd">14896000000</crwv:LongTermDebtMaturityAfterYearFour>
 <us-gaap:UnrecordedUnconditionalPurchaseObligationDueInRemainderOfFiscalYear contextRef="i" unitRef="usd">500000000</us-gaap:UnrecordedUnconditionalPurchaseObligationDueInRemainderOfFiscalYear>
 <us-gaap:UnrecordedUnconditionalPurchaseObligationBalanceSheetAmount contextRef="i" unitRef="usd">800000000</us-gaap:UnrecordedUnconditionalPurchaseObligationBalanceSheetAmount>
 <us-gaap:UnrecordedUnconditionalPurchaseObligationBalanceSheetAmount contextRef="dc" unitRef="usd">35500000000</us-gaap:UnrecordedUnconditionalPurchaseObligationBalanceSheetAmount>
 <us-gaap:RevenueRemainingPerformanceObligation contextRef="i" unitRef="usd">103700000000</us-gaap:RevenueRemainingPerformanceObligation>
 <us-gaap:RevenueRemainingPerformanceObligationPercentage contextRef="w1" unitRef="pure">0.41</us-gaap:RevenueRemainingPerformanceObligationPercentage>
 <us-gaap:RevenueRemainingPerformanceObligationPercentage contextRef="w2" unitRef="pure">0.39</us-gaap:RevenueRemainingPerformanceObligationPercentage>
 <us-gaap:RevenueRemainingPerformanceObligationExpectedTimingOfSatisfactionPeriod1 contextRef="w2">P48M</us-gaap:RevenueRemainingPerformanceObligationExpectedTimingOfSatisfactionPeriod1>
 <us-gaap:ConcentrationRiskPercentage1 contextRef="ca" unitRef="pure">0.36</us-gaap:ConcentrationRiskPercentage1>
 <us-gaap:ConcentrationRiskPercentage1 contextRef="cah" unitRef="pure">0.40</us-gaap:ConcentrationRiskPercentage1>
 <us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax contextRef="q" unitRef="usd">2575000000</us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax>
</xbrli:xbrl>"""


@pytest.fixture
def inst():
    return xi.parse_instance(XML)


def test_parse_instance_keeps_dims_periods_and_durations(inst):
    rpo = xi.facts(inst, "RevenueRemainingPerformanceObligationPercentage",
                   RevenueRemainingPerformanceObligationExpectedTimingOfSatisfactionStartDateAxis="2028-07-01")
    assert rpo["value"].iloc[0] == pytest.approx(0.39)
    assert inst.loc[inst["concept"].str.endswith("Period1"), "text"].iloc[0] == "P48M"
    rev = xi.facts(inst, "RevenueFromContractWithCustomerExcludingAssessedTax")
    assert rev["start"].iloc[0] == pd.Timestamp("2026-04-01")


def test_ten_q_ladder_uses_remainder_and_custom_after_tag(inst):
    lad = sc.ladder(inst, "debt")
    assert lad.amounts == pytest.approx([4413.0, 6184.0, 4416.0, 14896.0])
    assert lad.first_length == pytest.approx(0.5)  # June to December fiscal year end
    assert lad.reconciles  # no stated total: the sum is the total


def test_untagged_thereafter_goes_to_tail(inst):
    lad = sc.ladder(inst, "purchase")
    assert lad.amounts[-1] == pytest.approx(300.0) and "residual_to_tail" in lad.concepts


def test_rpo_windows_customers_and_uncommenced(inst):
    total, w = sc.rpo_windows(inst)
    assert total == pytest.approx(103_700.0)
    assert w[0][1] == pytest.approx(2.0, abs=0.01)  # unstated length runs to the next window
    assert w[1][1] == pytest.approx(4.0) and w[1][2] == pytest.approx(0.39)
    assert sc.customer_shares(inst) == {"CustomerAMember": pytest.approx(0.36)}  # quarter, not year to date
    assert sc.lease_not_commenced(inst)[0] == pytest.approx(35_500.0)


def test_debt_ladder_reconciles_to_balance_sheet():
    short = sc.Ladder("debt", [100.0, 100.0, 0.0], 1.0, 200.0, True, [])
    fixed, note = sc.reconcile_debt(short, 1000.0)
    assert fixed.amounts == [100.0, 100.0, 800.0] and "residual" in note
    none, note = sc.reconcile_debt(None, 1000.0, fallback_years=10)
    assert sum(none.amounts) == pytest.approx(1000.0) and "assumption" in note
    ok, note = sc.reconcile_debt(sc.Ladder("debt", [500.0, 500.0], 1.0, 1000.0, True, []), 1000.0)
    assert note == "ladder as filed"
