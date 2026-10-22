"""Offline tests of the two-clocks measures from companyfacts (Sections 4.7, 11): tag mapping, ladder gaps, the
per-filing clocks against `hy.clocks` by hand, point-in-time carry and ageing, the monthly signals, and the
incremental IC."""

import numpy as np
import pandas as pd
import pytest

from hy import backtest as bt
from hy import clocks
from hy.sources import clock_facts as cf


def test_canonical_tag_maps_rolling_and_new_purchase_names():
    assert cf.canonical_tag("LesseeOperatingLeaseLiabilityPaymentsDueNextRollingTwelveMonths") == \
        "LesseeOperatingLeaseLiabilityPaymentsDueNextTwelveMonths"
    assert cf.canonical_tag("FinanceLeaseLiabilityPaymentsDueInRollingYearThree") == "FinanceLeaseLiabilityPaymentsDueYearThree"
    assert cf.canonical_tag("LesseeOperatingLeaseLiabilityPaymentsDueAfterRollingYearFive") == \
        "LesseeOperatingLeaseLiabilityPaymentsDueAfterYearFive"
    assert cf.canonical_tag("UnrecordedUnconditionalPurchaseObligationDueInSecondYear") == \
        "UnrecordedUnconditionalPurchaseObligationDueYearTwo"
    assert cf.canonical_tag("UnrecordedUnconditionalPurchaseObligationDueInNextTwelveMonths") == \
        "UnrecordedUnconditionalPurchaseObligationDueNextTwelveMonths"
    assert cf.canonical_tag("LongTermDebtMaturitiesRepaymentsOfPrincipalInYearTwo") == \
        "LongTermDebtMaturitiesRepaymentsOfPrincipalInYearTwo"


def test_fill_ladder_gaps_keeps_positions():
    stem = "LongTermDebtMaturitiesRepaymentsOfPrincipal"
    tags = {stem + "InYearTwo": 5.0, stem + "InYearFour": 7.0, stem + "AfterYearFive": 9.0}
    out, filled = cf.fill_ladder_gaps(tags)
    assert filled
    assert out[stem + "InNextTwelveMonths"] == 0.0 and out[stem + "InYearThree"] == 0.0
    assert stem + "InYearFive" not in out          # after the last stated year: nothing to fill
    _, none = cf.fill_ladder_gaps({stem + "InNextTwelveMonths": 1.0, stem + "InYearTwo": 2.0})
    assert not none


def _facts(accn, end, filed, form, tags):
    return [dict(tag=t, start=pd.NaT, end=pd.Timestamp(end), val=v * 1e6, accn=accn, form=form,
                 filed=pd.Timestamp(filed), fp="FY" if form == "10-K" else "Q1") for t, v in tags.items()]


OP = "LesseeOperatingLeaseLiabilityPayments"
DEBT = "LongTermDebtMaturitiesRepaymentsOfPrincipal"


def _k_tags():
    return {OP + "DueNextTwelveMonths": 10, OP + "DueYearTwo": 10, OP + "DueYearThree": 10, OP + "DueYearFour": 10,
            OP + "DueYearFive": 10, OP + "DueAfterYearFive": 20, OP + "Due": 70,
            DEBT + "InNextTwelveMonths": 0, DEBT + "InYearTwo": 0, DEBT + "InYearThree": 100, DEBT + "InYearFour": 0,
            DEBT + "InYearFive": 0, DEBT + "AfterYearFive": 200, "LongTermDebt": 300,
            "RevenueRemainingPerformanceObligation": 50}


def test_filing_state_matches_hy_clocks_by_hand():
    facts = pd.DataFrame(_facts("k1", "2023-12-31", "2024-02-20", "10-K", _k_tags()))
    st = cf.filing_states(facts, "1").iloc[0]
    leases = clocks.ladder([10, 10, 10, 10, 10, 20], 1.0, clocks.tail_years_run_rate([10, 10, 10, 10, 10, 20]))
    debt = clocks.ladder([0, 0, 100, 0, 0, 200], 1.0, cf.ci.DEFAULT_DEBT_TAIL)  # last-but-one bucket is 0: default tail
    expect = clocks.mismatch({"Leases in force": leases, "Debt principal": debt}, clocks.rpo(50, [], 2.0), 0.0, 25).metrics
    assert st["obligations_total"] == pytest.approx(370.0)
    assert st["dur_obligations"] == pytest.approx(expect["dur_obligations"])
    assert st["duration_gap"] == pytest.approx(expect["dur_obligations"] - 1.0)   # RPO over 2 years: centre at 1
    assert st["renewal_dependent_share"] == pytest.approx(expect["renewal_dependent_share"])
    assert st["rent_1y"] == pytest.approx(10.0) and st["available_at"] == pd.Timestamp("2024-02-21")


def test_later_filing_carries_and_ages_missing_ladders():
    k = _facts("k1", "2023-12-31", "2024-02-20", "10-K", _k_tags())
    q = _facts("q1", "2024-06-30", "2024-08-01", "10-Q", {"LongTermDebt": 300})
    st = cf.filing_states(pd.DataFrame(k + q), "1").set_index("accn")
    assert set(st.loc["q1", "carried"].split(",")) == {"op", "debt", "rpo"}
    assert st.loc["q1", "dur_obligations"] < st.loc["k1", "dur_obligations"]      # half a year older
    assert st.loc["q1", "obligations_total"] == pytest.approx(370.0)
    late = _facts("q9", "2025-06-30", "2025-08-01", "10-Q", {"LongTermDebt": 300})   # 18 months after the 10-K
    st2 = cf.filing_states(pd.DataFrame(k + late), "1").set_index("accn")
    assert st2.loc["q9", "carried"] == "" and st2.loc["q9", "lease_total"] == 0.0


def test_monthly_signals_are_point_in_time_and_signed():
    states = cf.filing_states(pd.DataFrame(_facts("k1", "2023-12-31", "2024-02-20", "10-K", _k_tags())), "1")
    fund = pd.DataFrame({"gvkey": ["G1"], "ltm_ebitda": [27.0], "ltm_revenue": [100.0], "debt": [300.0],
                         "available_at": [pd.Timestamp("2024-02-01")]})
    before = cf.clock_signals_as_of(states, fund, {"G1": "1"}, pd.Timestamp("2024-02-20"))
    assert before.empty                                      # the 10-K is not known yet
    s = cf.clock_signals_as_of(states, fund, {"G1": "1"}, pd.Timestamp("2024-03-01")).iloc[0]
    assert s["fixed_charge_years"] == pytest.approx(370.0 / (27.0 + 10.0))
    assert s["e5"] == -s["fixed_charge_years"] and s["dgap"] < 0
    assert s["rpo_material"] and s["renew"] == pytest.approx(-states.iloc[0]["renewal_dependent_share"])
    small = fund.assign(ltm_revenue=1000.0)
    assert np.isnan(cf.clock_signals_as_of(states, small, {"G1": "1"}, pd.Timestamp("2024-03-01")).iloc[0]["renew"])
    loss = fund.assign(ltm_ebitda=-50.0)
    assert cf.clock_signals_as_of(states, loss, {"G1": "1"}, pd.Timestamp("2024-03-01")).iloc[0]["e5"] == -cf.YEARS_CAP
    leak = fund.assign(available_at=pd.Timestamp("2024-04-01"))
    with pytest.raises(bt.LookAheadError):
        cf.clock_signals_as_of(states, leak, {"G1": "1"}, pd.Timestamp("2024-03-01"))


def test_compustat_debt_fills_a_filing_without_debt():
    tags = {k: v for k, v in _k_tags().items() if not k.startswith(DEBT) and k != "LongTermDebt"}
    states = cf.filing_states(pd.DataFrame(_facts("k1", "2023-12-31", "2024-02-20", "10-K", tags)), "1")
    fund = pd.DataFrame({"gvkey": ["G1"], "ltm_ebitda": [27.0], "ltm_revenue": [100.0], "debt": [300.0],
                         "available_at": [pd.Timestamp("2024-02-01")]})
    s = cf.clock_signals_as_of(states, fund, {"G1": "1"}, pd.Timestamp("2024-03-01")).iloc[0]
    assert s["debt_source"] == "compustat" and s["fixed_charge_years"] == pytest.approx((70.0 + 300.0) / 37.0)


def test_extract_keeps_only_clock_tags():
    doc = {"facts": {"us-gaap": {
        OP + "DueYearTwo": {"units": {"USD": [{"end": "2023-12-31", "val": 5, "accn": "a", "form": "10-K",
                                               "filed": "2024-02-01", "fp": "FY"}]}},
        "Revenues": {"units": {"USD": [{"start": "2023-01-01", "end": "2023-12-31", "val": 9, "accn": "a",
                                        "form": "10-K", "filed": "2024-02-01"}]}},
    }}}
    f = cf.extract(doc)
    assert f["tag"].tolist() == [OP + "DueYearTwo"] and cf.extract(None).empty


def test_fetch_refuses_other_hosts():
    with pytest.raises(ValueError):
        cf.fetch_sec_json("https://example.com/x.json")


def test_ic_beyond_removes_spread_and_keeps_new_information(rng):
    rows = []
    for d in pd.date_range("2020-01-31", periods=24, freq="ME"):
        s = rng.uniform(0.02, 0.10, 200)
        news = rng.standard_normal(200)
        real = 0.5 * pd.Series(s).rank(pct=True).to_numpy() + 0.3 * news + 0.3 * rng.standard_normal(200)
        rows.append(pd.DataFrame({"date": d, "spread": s, "news": news, "real": real}))
    df = pd.concat(rows, ignore_index=True)
    assert bt.ic_series(df, "spread", "real").mean() > 0.25
    assert abs(bt.ic_beyond(df, "spread", "real", "spread").mean()) < 0.05
    assert bt.ic_beyond(df, "news", "real", "spread").mean() > 0.4
