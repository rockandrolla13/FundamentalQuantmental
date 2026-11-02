"""Filing features added to the two clocks (methodology Section 4.7.1). Examples come from the source tables."""

import math

import pytest

from hy import clocks, state


def test_sp_tail_rounds_to_closest_year():
    assert clocks.sp_tail_years([100, 100, 100, 100, 100, 340]) == 3.0  # 3.4 years
    assert clocks.sp_tail_years([100, 100, 100, 100, 100, 360]) == 4.0  # 3.6 years
    assert clocks.sp_tail_years([100, 100, 100, 100, 100, 10]) == 1.0  # a stated tail is never zero years
    assert clocks.sp_tail_years([100, 100, 100, 100, 100, 0]) == 0.0
    assert math.isnan(clocks.sp_tail_years([100, 100, 100, 100, 0, 50]))  # no rate to extend


def test_sp_present_value_matches_hand_sum():
    amounts = [100.0, 100.0, 300.0]  # two stated years, then 3 years at 100
    r = 0.10
    expected = sum(100.0 / (1 + r) ** y for y in range(1, 6))
    assert clocks.sp_present_value(amounts, r) == pytest.approx(expected)
    assert clocks.sp_present_value(amounts, 0.0) == pytest.approx(sum(amounts))  # no discount keeps the total
    assert math.isnan(clocks.sp_present_value([100.0, 0.0, 50.0], r))


def test_moodys_floor_never_below_contract():
    assert clocks.moodys_lease(500.0, 50.0) == 500.0
    assert clocks.moodys_lease(300.0, 50.0) == 400.0
    assert math.isnan(clocks.moodys_lease(300.0, float("nan")))
    assert clocks.MOODYS_RENT_MULTIPLE == state.LEASE_MULTIPLE


def test_lease_renewal_gap_needs_positive_cash():
    assert clocks.lease_renewal_gap(300.0, 50.0, 200.0) == pytest.approx(0.5)
    assert math.isnan(clocks.lease_renewal_gap(300.0, 50.0, -1.0))


def test_executory_parts_add_to_total_leverage():
    p = clocks.executory_leverage(190.0, 38.0, 60.0, 712.0)  # source means: 0.190, 0.038, 0.060 (Table 2)
    assert p["bs_debt"] == pytest.approx(0.190)
    assert p["op_leases"] == pytest.approx(0.038)
    assert p["purchase_obligations"] == pytest.approx(0.060)
    assert sum(p.values()) == pytest.approx(0.288)
    assert math.isnan(clocks.executory_leverage(0.0, 0.0, 0.0, 0.0)["bs_debt"])


def test_lease_gap_splits_by_sign():
    u = clocks.lease_gap(120.0, 100.0, 1000.0)
    assert (u["gap"], u["undervalued"], u["overvalued"]) == pytest.approx((0.02, 0.02, 0.0))
    o = clocks.lease_gap(80.0, 100.0, 1000.0)
    assert (o["gap"], o["undervalued"], o["overvalued"]) == pytest.approx((-0.02, 0.0, 0.02))
    assert math.isnan(clocks.lease_gap(1.0, 1.0, 0.0)["gap"])


APPENDIX_B = [  # text cut to the part that carries the code. Andrade, Henry, Nanda (2014 draft), Appendix B
    ("ALLTEL", "wireless handset purchases, network facilities and transport services, agreements for software", "essential"),
    ("Alcoa", "Raw material and other purchase obligations", "non_essential"),
    ("Baker Hughes", "fixed or minimum quantities; exclude agreements that are cancelable at anytime", "moderate"),
    ("Bard", "These inventory purchase commitments do not exceed the projected requirements", "moderate"),
    ("Chevron", "take-or-pay agreements. goods and services, such as pipeline and storage capacity, utilities", "essential"),
    ("Chiron", "information technology services. We can now terminate this agreement, subject to charges", "non_essential"),
    ("EDS", "principally software and telecommunications services, enforceable and legally binding", "essential"),
    ("GA Pac", "take-or-pay contracts related to raw material purchases and utilities. commitments for capital projects", "non_essential"),
    ("Gillette", "take-or-pay arrangements or firm commitments. we generally negotiate new contracts", "moderate"),
]


@pytest.mark.parametrize("firm,text,code", APPENDIX_B)
def test_essentiality_coder_matches_source_examples(firm, text, code):
    assert clocks.purchase_essentiality(text) == code, firm


def test_essentiality_coder_known_miss_and_retail_rule():
    brinker = "purchase of telecommunication services, certain non-alcoholic beverages and baked goods"
    assert clocks.purchase_essentiality(brinker) == "essential"  # the source codes Moderate: the known miss, 9 of 10
    assert clocks.purchase_essentiality("inventory for stores", retail=True) == "essential"
    assert clocks.purchase_essentiality("inventory for stores") == "moderate"


def test_obligation_classes_cover_each_line():
    assert clocks.obligation_class("Debt principal") == "debt"
    assert clocks.obligation_class("Interest") == "debt"
    assert clocks.obligation_class("Finance leases") == "debt"
    assert clocks.obligation_class("Leases in force") == "lease"
    assert clocks.obligation_class("Signed leases not yet started") == "lease"
    assert clocks.obligation_class("Purchase commitments") == "purchase_moderate"
    assert clocks.obligation_class("Purchase commitments essential") == "purchase_essential"
    assert clocks.obligation_class("Purchase commitments non-essential") == "purchase_non_essential"


def test_class_amounts_add_to_renewal_total_and_old_split_holds():
    obligations = {
        "Debt principal": [clocks.Bucket(0.0, 10.0, 100.0)],
        "Leases in force": [clocks.Bucket(0.0, 10.0, 100.0)],
        "Purchase commitments essential": [clocks.Bucket(0.0, 10.0, 50.0)],
        "Purchase commitments": [clocks.Bucket(0.0, 10.0, 30.0)],
        "Purchase commitments non-essential": [clocks.Bucket(0.0, 10.0, 20.0)],
    }
    m = clocks.mismatch(obligations, [clocks.Bucket(0.0, 2.0, 200.0)], 0.5).metrics
    parts = [m[f"renewal_{c}_amount"] for c in clocks.OBLIGATION_CLASSES]
    assert sum(parts) == pytest.approx(m["renewal_dependent_amount"])
    assert m["renewal_refinance_amount"] == pytest.approx(m["renewal_debt_amount"])
    assert m["renewal_recontract_amount"] == pytest.approx(sum(parts[1:]))
    assert m["renewal_lease_amount"] == pytest.approx(80.0)


def test_customer_persistence():
    history = [{"A": 0.30, "B": 0.12}, {"A": 0.25, "B": 0.11}, {"A": 0.20, "C": 0.15}]
    p = clocks.customer_persistence(history)
    assert p["durable_share"] == pytest.approx(0.20)  # A only: three filings
    assert p["n_durable"] == 1.0
    assert p["new_share"] == pytest.approx(0.15)
    assert p["dropped_share"] == pytest.approx(0.11)


def test_undisclosed_customers_are_nan_not_zero():
    assert math.isnan(clocks.customer_persistence([{"A": 0.3}, {}])["durable_share"])
    assert math.isnan(clocks.customer_persistence([])["dropped_share"])
    one = clocks.customer_persistence([{"A": 0.3}])
    assert math.isnan(one["dropped_share"]) and one["durable_share"] == 0.0


def test_revenue_proxies():
    assert clocks.rev_abs_growth(110.0, 100.0) == pytest.approx(clocks.rev_abs_growth(100.0, 110.0))
    assert math.isnan(clocks.rev_abs_growth(0.0, 100.0))
    assert clocks.sga_sales(20.0, 100.0, sic=3711) == pytest.approx(0.20)
    assert math.isnan(clocks.sga_sales(20.0, 100.0, sic=5812))  # restaurants: the source calls the proxy poor here
    assert math.isnan(clocks.sga_sales(20.0, 0.0))


def test_delta_drc_scales_by_average_assets():
    assert clocks.delta_drc(30.0, 10.0, 1100.0, 900.0) == pytest.approx(0.02)
    assert clocks.delta_drc(10.0, 30.0, 1100.0, 900.0) == pytest.approx(-0.02)
    assert math.isnan(clocks.delta_drc(float("nan"), 10.0, 1100.0, 900.0))
    assert math.isnan(clocks.delta_drc(30.0, 10.0, 0.0, 0.0))


def _sales_path(n=44):
    return [100.0 * (1.03 ** i) * (1.0 + 0.1 * ((i // 5) % 2)) for i in range(n)]


def test_cost_elasticity_reads_the_cost_structure():
    sales = _sales_path()
    assert clocks.cost_elasticity([0.8 * v for v in sales], sales) == pytest.approx(1.0)  # all variable
    assert clocks.cost_elasticity([50.0] * len(sales), sales) == pytest.approx(0.0)  # all fixed
    mixed = clocks.cost_elasticity([30.0 + 0.5 * v for v in sales], sales)
    assert 0.0 < mixed < 1.0


def test_cost_elasticity_needs_enough_clean_history():
    sales = _sales_path()
    assert math.isnan(clocks.cost_elasticity([50.0] * 10, sales[:10]))  # 6 changes, under the floor
    assert math.isnan(clocks.cost_elasticity([50.0] * 44, [100.0] * 44))  # no sales variation
    assert math.isnan(clocks.cost_elasticity([-1.0] * 44, sales))  # negative costs cannot enter a log


def test_float_unhedged():
    assert clocks.float_unhedged(600.0, 200.0, 1000.0) == pytest.approx(0.4)
    assert clocks.float_unhedged(100.0, 300.0, 1000.0) == 0.0  # over-hedged does not go negative
    assert math.isnan(clocks.float_unhedged(1.0, 0.0, 0.0))


def test_collateral_weighted_and_peer_shock():
    pool = {"737": 300.0, "A320": 100.0}
    assert clocks.collateral_weighted(pool, {"737": 10.0, "A320": 2.0}) == pytest.approx(8.0)
    assert math.isnan(clocks.collateral_weighted(pool, {"737": 10.0}))  # a missing type is not zero
    assert clocks.peer_shock(pool, {"737": 1.0, "A320": 1.0}) == pytest.approx(math.log(2.0))
    assert clocks.peer_shock(pool, {"737": 0.0, "A320": 0.0}) == 0.0


def test_soft_revenue_gives_a_clock_with_no_rpo():
    g = clocks.soft_revenue(100.0, 0.20, horizon=40)
    assert g[0] < 100.0 and g[1] == pytest.approx(g[0] * 0.8)
    assert g.sum() == pytest.approx(100.0 * (1.0 - 0.8 ** 40) / -math.log(0.8))
    assert clocks.soft_revenue(100.0, 0.0, horizon=3).tolist() == [100.0, 100.0, 100.0]
    assert math.isnan(clocks.soft_revenue(100.0, 1.0, horizon=3)[0])
    fast = clocks.mismatch({"Debt principal": [clocks.Bucket(0.0, 10.0, 100.0)]}, clocks.soft_revenue(100.0, 0.40), 0.3).metrics
    slow = clocks.mismatch({"Debt principal": [clocks.Bucket(0.0, 10.0, 100.0)]}, clocks.soft_revenue(100.0, 0.10), 0.3).metrics
    assert fast["coverage_contracted"] < slow["coverage_contracted"]  # higher churn leaves less cash behind the same debt


def test_industry_distress():
    assert clocks.industry_distress([-0.5, -0.4, -0.35, -0.2, -0.1]) == 1.0
    assert clocks.industry_distress([-0.5, -0.4, -0.25, -0.2, -0.1]) == 0.0
    assert math.isnan(clocks.industry_distress([-0.5, -0.4]))  # under the five peer floor


def test_competition_flag():
    universe = [0.05, 0.10, 0.20, 0.30, 0.40]
    assert clocks.competition_flag(0.05, universe) == 1.0
    assert clocks.competition_flag(0.30, universe) == 0.0
    assert math.isnan(clocks.competition_flag(float("nan"), universe))


def test_borrowing_base_collateral():
    lo, hi = clocks.borrowing_base_collateral({"producing": 100.0, "undeveloped": 100.0, "unproved": 100.0})
    assert (lo, hi) == pytest.approx((115.0, 145.0))
    with pytest.raises(KeyError):
        clocks.borrowing_base_collateral({"probable": 100.0})


def test_soft_revenue_decay_stays_on_the_grid_and_coverage_is_readable():
    m = clocks.mismatch({"Debt principal": [clocks.Bucket(0.0, 5.0, 100.0)]}, clocks.soft_revenue(100.0, 0.15), 0.3).metrics
    long = clocks.mismatch({"Debt principal": [clocks.Bucket(0.0, 5.0, 100.0)]}, clocks.soft_revenue(100.0, 0.15, 40), 0.3, horizon=40)
    assert long.metrics["revenue_runoff"] > m["revenue_runoff"]  # run-off moves with the grid, which the docstring warns about
    assert m["coverage_contracted"] > 1.0
