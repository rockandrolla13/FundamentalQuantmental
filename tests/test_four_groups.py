"""Tests for the four-group analyst: G1 additions (funding gap, price-based loss, refinancing shock, decision against
cash), G3 skill rules, G4 book methods, and the group combination."""

import numpy as np
import pandas as pd
import pytest

from hy import alpha, books, forward, groups, recovery, skills


# --------------------------------------------------------------------------- G1: funding gap (RV PDF E75, E76)


def test_funding_gap_matches_hand_calculation():
    # C0 100 + revolver 50 - min cash 20 = 130; FCF 10 a quarter; 60 due in q2 and 100 in q4.
    r = forward.funding_gap(100, 50, 20, [10, 10, 10, 10], [0, 60, 0, 100], debt0=400)
    np.testing.assert_allclose(r["G"], [140, 90, 100, 10])
    assert r["funding_gap_min"] == 10 and r["first_gap_q"] is None and r["funding_need_max"] == 0
    assert r["maturity_share"] == pytest.approx(160 / 400)


def test_funding_gap_first_failure_quarter_and_need():
    r = forward.funding_gap(50, 0, 10, [-20, -20, -20], [0, 0, 30])
    np.testing.assert_allclose(r["G"], [20, 0, -50])
    assert r["first_gap_q"] == 3 and r["funding_need_max"] == 50


def test_funding_gap_falls_when_burn_rises():
    lo = forward.funding_gap(100, 0, 0, [-5] * 8, [0] * 8)["funding_gap_min"]
    hi = forward.funding_gap(100, 0, 0, [-15] * 8, [0] * 8)["funding_gap_min"]
    assert hi < lo


def test_funding_gap_rejects_mismatched_lengths():
    with pytest.raises(ValueError):
        forward.funding_gap(1, 0, 0, [1, 2], [1])


# --------------------------------------------------------------------------- G1: price-based loss (E149, E109)


def test_recovery_pv_gatto_example():
    assert recovery.recovery_pv(50, 0.20, 2) == pytest.approx(34.72, abs=0.01)


def test_price_based_loss_is_lower_for_a_discount_bond():
    par = recovery.price_based_loss(100, 0.4, 0.15, 1.0)
    disc = recovery.price_based_loss(70, 0.4, 0.15, 1.0)
    assert par == pytest.approx(1 - 0.4 / 1.15)
    assert disc < par
    assert disc == pytest.approx((0.70 - 0.4 / 1.15) / 0.70)


def test_price_based_loss_floors_at_zero_below_recovery():
    assert recovery.price_based_loss(30, 0.4, 0.0, 0.0) == 0.0


# --------------------------------------------------------------------------- G1: refinancing shock (E77)


def test_refinancing_shock_hand_calculation():
    r = forward.refinancing_shock([1000, 500], 0.04, [0.07, 0.08], ebitda=1000, cash_interest=200, capex=300,
                                  fcf=150, debt=5000)
    assert r["delta_I"] == pytest.approx(1000 * 0.03 + 500 * 0.04)
    assert r["delta_I_to_E"] == pytest.approx(0.05)
    assert r["cash_cov_after"] == pytest.approx(1000 / 250)
    assert r["after_capex_cov_after"] == pytest.approx(700 / 250)
    assert r["fcf_after_to_debt"] == pytest.approx(100 / 5000)


def test_refinancing_shock_is_zero_when_coupons_match_and_negative_when_rates_fall():
    assert forward.refinancing_shock([100], 0.05, [0.05], 10, 1, 1, 1, 10)["delta_I"] == 0
    assert forward.refinancing_shock([100], 0.08, [0.05], 10, 1, 1, 1, 10)["delta_I"] < 0


# --------------------------------------------------------------------------- G1: decision against cash (E50 to E60)


def _states(pd_h=0.0, s_H=0.03, y=0.04):
    return pd.DataFrame([{"macro_path": "a", "p_path": 0.6, "pd_h": pd_h, "y_tsy_H": y, "s_H": s_H},
                         {"macro_path": "b", "p_path": 0.4, "pd_h": pd_h, "y_tsy_H": y, "s_H": s_H}])


def test_bond_price_at_par_and_coupons_paid():
    assert alpha.bond_price(0.06, 5.0, 0.06) == pytest.approx(100.0)
    assert alpha.coupons_paid(0.06, 4.75, 0.5) == pytest.approx(3.0)
    assert alpha.accrued_interest(0.06, 4.75) == pytest.approx(1.5)


def test_decision_against_cash_carry_only_case():
    # Par bond at 7%, yield unchanged, no default: wealth return over 0.5y is ~3.5%; cash at 4% earns 2%.
    r = alpha.decision_against_cash(100.0, 0.07, 5.0, 0.5, _states(0.0, 0.03, 0.04), 0.35, 0.04)
    assert r["mu_excess"] == pytest.approx(0.035 - 0.02, abs=1e-3)
    assert r["pi_loss"] == 0.0 and r["pi_cash"] == 0.0


def test_decision_against_cash_default_lowers_mu_and_raises_es():
    safe = alpha.decision_against_cash(100.0, 0.07, 5.0, 0.5, _states(0.0), 0.35, 0.04)
    risky = alpha.decision_against_cash(100.0, 0.07, 5.0, 0.5, _states(0.10), 0.35, 0.04)
    assert risky["mu_excess"] < safe["mu_excess"]
    assert risky["es95"] > safe["es95"]
    assert risky["pi_loss"] == pytest.approx(0.10)


def test_expected_shortfall_partial_tail():
    # 2% at -50%, 98% at +1%: ES95 = (0.02 x 50% + 0.03 x -1%) / 0.05.
    assert alpha.expected_shortfall([-0.5, 0.01], [0.02, 0.98]) == pytest.approx((0.02 * 0.5 - 0.03 * 0.01) / 0.05)


def test_opportunity_cost_names_cash_when_nothing_beats_it():
    oc = alpha.opportunity_cost({"A": -0.01, "B": -0.02}, {"A": 0.1, "B": 0.1}, 0.2)
    assert oc["A"]["best_admissible"] == "cash" and oc["A"]["opportunity_cost"] == pytest.approx(0.01)


def test_opportunity_cost_skips_inadmissible_bonds():
    oc = alpha.opportunity_cost({"A": 0.01, "B": 0.05, "C": 0.03}, {"A": 0.1, "B": 0.5, "C": 0.1}, 0.2)
    assert oc["A"]["best_admissible"] == "C"
    assert not oc["B"]["admissible"]


# --------------------------------------------------------------------------- G3: skills


def test_addback_bridge_load_flags_and_recurrence():
    r = skills.addback_bridge([100] * 8, [0, 0, 0, 0, 3, 4, 5, 8])
    assert r["addback_load"] == pytest.approx(20 / 400)
    assert not r["addback_flags"]["single_above_5pct"]
    assert r["addback_flags"]["recurring"] and r["recurring_quarters"] == 4
    big = skills.addback_bridge([100] * 4, [0, 0, 0, 50])
    assert big["addback_flags"]["total_above_10pct"] and not big["addback_flags"]["recurring"]


def test_fcf_check_gap_flags_a_break():
    ok = skills.fcf_check_gap(ocf=500, capex=200, ebitda_adj=800, cash_nr=0, cash_interest=200, cash_tax=100, delta_wc=0)
    assert not ok["fcf_check_flag"]
    bad = skills.fcf_check_gap(ocf=200, capex=200, ebitda_adj=800, cash_nr=0, cash_interest=200, cash_tax=100, delta_wc=0)
    assert bad["fcf_check_flag"]


def test_covenant_headroom_and_bands():
    assert skills.covenant_headroom("max_leverage", 4.0, 3.0) == pytest.approx(0.25)
    assert skills.covenant_headroom("min_coverage", 2.0, 2.5) == pytest.approx(0.20)
    assert skills.headroom_tier(0.25) == "comfortable"
    assert skills.headroom_tier(0.15) == "elevated attention"
    assert skills.headroom_tier(0.05) == "tight"
    assert skills.headroom_tier(-0.01) == "breach"


def test_parse_covenants_reads_levels():
    text = ("The facility requires us to maintain minimum interest coverage at a ratio of not less than 3.0 to 1.0. "
            "The Consolidated Net Leverage Ratio is not to exceed 4.50 to 1.00. Free liquidity of no less than "
            "$250,000,000 at all times.")
    got = {c["kind"]: c["level"] for c in skills.parse_covenants(text)}
    assert got == {"min_coverage": 3.0, "max_leverage": 4.5, "min_liquidity": 250.0}


def test_watchlist_tiers():
    calm = skills.watchlist_tier(0.05, 100, 500, 100, None, 2.0, 5)
    assert calm["watchlist_tier"] == "none"
    assert skills.watchlist_tier(-0.12, 100, 500, 100, None, 2.0, 5)["watchlist_tier"] == "watch closely"
    assert skills.watchlist_tier(0.0, -10, 500, 100, None, 2.0, 5)["watchlist_tier"] == "watchlist"
    assert skills.watchlist_tier(0.0, 10, 50, 100, None, 0.5, 1)["watchlist_tier"] == "workout"
    assert skills.watchlist_tier(0.0, 10, 500, 100, None, 2.0, 5, headroom=-0.1)["watchlist_tier"] == "workout"


def test_trajectory_counts_consecutive_quarters():
    rising = [100, 100, 100, 100, 110, 111, 112, 113]
    t = skills.trajectory({"revenue": rising, "cost": rising}, {"cost": False})
    assert t["revenue"]["call"] == "improving" and t["revenue"]["weight"] == "trend"
    assert t["cost"]["call"] == "deteriorating"
    one = skills.trajectory({"revenue": [100] * 7 + [90]})["revenue"]
    assert one["call"] == "deteriorating" and one["weight"] == "observation"
    assert skills.trajectory({"revenue": [1, 2]})["revenue"]["call"] == "open"


# --------------------------------------------------------------------------- G4: books


def test_kricheff_bridge_and_ratios():
    b = books.kricheff_bridge(1000, 300, 200, 50, 20, cfo=740)
    assert b["fcf"] == 430 and b["cfo_gap"] == pytest.approx(430 + 300 - 740)
    r = books.kricheff_ratios(1000, 300, 200, 200, 4000, 500, 430, 6000)
    assert r["after_capex_cov"] == pytest.approx(3.5) and r["lev_net"] == pytest.approx(3.5)
    assert r["equity_cushion"] == pytest.approx(1 - 4000 / 9500)


def test_sp_scores_are_monotone_in_each_ratio():
    worse = [books._ratio_score("ffo_to_debt", x) for x in (70, 40, 20, 10, 2)]
    assert worse == sorted(worse)
    worse = [books._ratio_score("debt_to_cap", x) for x in (30, 45, 60, 80, 95)]
    assert worse == sorted(worse)
    assert books._ratio_score("ebitda_cov", 5.5) == pytest.approx(5.5)


def test_sp_default_risk_weights_follow_business_risk():
    # Table 10-7: a high-risk business (7) puts 70% on the financial score.
    r = books.sp_default_risk_score(7.0, 5.0)
    assert r["w_business"] == pytest.approx(0.30)
    assert r["sp_default_risk_score"] == pytest.approx(0.3 * 7 + 0.7 * 5)
    assert r["sp_anchor_class"] == "BBB"


# --------------------------------------------------------------------------- group combination


def test_bucket_shares_are_the_users_choice():
    # User decision 2026-10-22 (weights-esp-spider): G1 40%, two clocks 20%, books 17%, G2 18%, G3 5%.
    assert groups.GROUP_WEIGHTS == pytest.approx({"G1": 0.40, "G2C": 0.20, "G2": 0.18, "G3": 0.05, "G4": 0.17})
    assert sum(groups.GROUP_WEIGHTS.values()) == pytest.approx(1.0)
    assert groups.SPEC_GROUP_WEIGHTS == pytest.approx({"G1": 0.20, "G2": 0.65, "G3": 0.05, "G4": 0.10})


def test_effective_weights_keep_relative_weights_inside_a_bucket():
    w = groups.effective_weights()
    assert sum(w.values()) == pytest.approx(1.0)
    assert w["E5"] == pytest.approx(0.20)
    assert w["E0"] / w["E1"] == pytest.approx(0.25 / 0.15)  # spec ratio kept inside the rest of G2
    assert w["E7"] == pytest.approx(0.40 / 4) and w["E4"] == 0.0
    assert w["E14"] == pytest.approx(0.09) and w["E15"] == pytest.approx(0.03)
    assert w["E12"] == pytest.approx(0.025) and w["E13"] == pytest.approx(0.025)


def test_combine_equals_effective_weighted_mean_and_subtracts_cost_once():
    est = {k: 10.0 * i for i, k in enumerate(groups.ESTIMATES)}
    r = groups.combine(est, cost_bp_yr=30, anchor_bp_yr=-40)
    w = groups.effective_weights()
    flat = sum(w[k] * est[k] for k in est)
    assert r["combined_before_cost"] == pytest.approx(flat)
    assert r["combined_after_cost"] == pytest.approx(flat - 30)
    assert r["anchor_after_cost"] == pytest.approx(-70)
    assert sum(g["contribution"] for g in r["groups"].values()) == pytest.approx(flat)


def test_combine_keeps_bucket_share_when_an_estimate_is_missing():
    full = {k: 0.0 for k in groups.ESTIMATES}
    full.update({"E7": 100.0})
    drop = dict(full)
    del drop["E8"]  # G1 still counts 40%; its mean is now over E4 (weight 0), E7, E9, E10
    r = groups.combine(drop, 0, 0)
    assert r["groups"]["G1"]["group_share"] == pytest.approx(0.40)
    assert r["combined_before_cost"] == pytest.approx(0.40 * 100 / 3)


def test_combine_renormalises_over_present_buckets():
    r = groups.combine({"E1": 100.0}, 0, 0)
    assert r["combined_before_cost"] == pytest.approx(100) and r["groups_n"] == 1
    assert r["groups"]["G2"]["group_share"] == pytest.approx(1.0)


def test_zero_weight_estimate_is_shown_not_counted():
    r = groups.combine({"E4": 500.0, "E9": 10.0}, 0, 0)
    assert r["groups"]["G1"]["alpha_bp_yr"] == pytest.approx(10.0)
    assert any(row["estimate"] == "E4" and row["weight"] == 0 for row in r["groups"]["G1"]["rows"])


def test_one_way_bucket_can_only_lower_the_combination():
    base = {k: 50.0 for k in groups.ESTIMATES}
    clean = groups.combine({**base, "E11": groups.one_way(80.0)}, 0, 0)["combined_before_cost"]
    hit = groups.combine({**base, "E11": groups.one_way(-80.0)}, 0, 0)["combined_before_cost"]
    assert hit < clean and clean < 50.0


def test_one_way_estimates_only_lower():
    assert groups.one_way(5.0) == 0.0 and groups.one_way(-5.0) == -5.0


def test_scale_scores_and_convergence_signs():
    s = groups.scale_scores({"a": 1, "b": 2, "c": 3}, 10)
    assert s["c"] > 0 > s["a"] and s["b"] == pytest.approx(0)
    assert groups.convergence_alpha_bp(0.01, 4.0, 0.85, 0.5) > 0 > groups.convergence_alpha_bp(-0.01, 4.0, 0.85, 0.5)


def test_verdict_bands():
    assert groups.verdict(50, 30) == "supports owning"
    assert groups.verdict(10, 30) == "leans to owning"
    assert groups.verdict(-1, 30) == "against owning"
    assert groups.verdict(float("nan"), 30) == "no view"
    assert groups.verdict(0.0, 30, one_way_only=True) == "no objection"


def test_treasury_return_on_a_flat_curve_is_the_yield_over_the_horizon():
    # Broken first period (4.657 years): dividing by 100 instead of the dirty price would add the accrued (~1.6%).
    r = alpha.treasury_return(0.0478, 0.0478, 4.657, 0.5)
    assert r == pytest.approx(0.0478 / 2, abs=5e-4)


def test_watchlist_thin_liquidity_is_open_when_the_revolver_is_unknown():
    r = skills.watchlist_tier(0.0, 10, 50, 100, None, 2.0, 5, revolver_known=False)
    assert r["watchlist_tier"] == "none" and r["open"]


def test_rank_shares_ties_and_puts_nan_last():
    r = groups.rank({"a": 0.0, "b": 0.0, "c": 5.0, "d": float("nan")})
    assert r == {"c": 1, "a": 2, "b": 2, "d": 4}


def test_cash_flow_from_filing_reads_ytd_and_refuses_look_ahead():
    from hy.sources import xbrl

    tag = "NetCashProvidedByUsedInOperatingActivities"
    start = pd.Timestamp("2025-01-01")
    facts = pd.DataFrame([
        {"tag": tag, "start": start, "end": pd.Timestamp("2025-06-30"), "days": 180, "val": 300e6, "accn": "A2",
         "filed": pd.Timestamp("2025-08-05")},
        {"tag": tag, "start": start, "end": pd.Timestamp("2025-03-31"), "days": 89, "val": 100e6, "accn": "A1",
         "filed": pd.Timestamp("2025-05-05")},
    ])
    filings = pd.DataFrame([{"cik": "0000000001", "form": "10-Q", "report_date": pd.Timestamp("2025-06-30"),
                             "acceptance": pd.Timestamp("2025-08-05 16:00"), "accession": "A2",
                             "filing_date": pd.Timestamp("2025-08-05")}])
    got = xbrl.cash_flow_from_filing(facts, filings, 1, pd.Timestamp("2025-06-30"), pd.Timestamp("2025-09-01"))
    assert got["operating_cash_flow"] == pytest.approx(200.0)  # YTD 300 less Q1 100, in USD m
    assert xbrl.cash_flow_from_filing(facts, filings, 1, pd.Timestamp("2025-06-30"), pd.Timestamp("2025-08-01")) == {}


def test_bridge_debt_survives_a_missing_anchor_value():
    from hy.sources import xbrl

    vals = {"debt_total": 100.0, "debt_current": 10.0, "debt_long_term": 90.0}
    anchor = pd.Series({"debt_current": pd.NA, "debt_long_term": pd.NA}, dtype="object")
    assert xbrl._bridge_debt(vals, anchor, {"debt_total": 100.0}) == []
    assert np.isnan(vals["debt_long_term"])
