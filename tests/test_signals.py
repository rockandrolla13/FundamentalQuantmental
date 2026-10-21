"""Tests for hy.signals (methodology Section 8 and Section 11, Signals row)."""

import numpy as np
import pandas as pd
import pytest

from hy import signals as sg


def test_s1_zero_inside_band():
    z = np.array([0.5, -1.0, 2.5, -3.0])
    out = sg.s1_residual(z, 2.0, np.zeros(4, dtype=bool))
    np.testing.assert_array_equal(out, [0.0, 0.0, 2.5, -3.0])


def test_s1_zero_when_event_contaminated():
    z = np.array([2.5, -3.0])
    out = sg.s1_residual(z, 2.0, np.array([True, False]))
    np.testing.assert_array_equal(out, [0.0, -3.0])


def test_s1_entry_needs_return_above_cost_and_exit_at_half_band():
    z = np.array([3.0, 3.0])
    entry = sg.s1_entry(z, 2.0, [False, False], exp_conv_ret_h=[0.02, 0.001], bid_ask_bp=[25, 25], spread_duration=[4, 4])
    np.testing.assert_array_equal(entry, [True, False])  # round-trip cost = 25 * 4 / 1e4 = 1%
    ex = sg.s1_exit([0.9, 1.5, 1.5], 2.0, periods_held=[1, 10, 1], horizon=[5, 5, 5], event_reset=[False, False, False])
    np.testing.assert_array_equal(ex, [True, True, False])


def test_s1_horizon_is_two_half_lives():
    assert sg.s1_horizon(0.5) == pytest.approx(2.0)
    assert np.isinf(sg.s1_horizon(1.0))


def test_hca_spread_tightening_loose_bound():
    """Book trade (pp. 517-518): B bond 540 bp to peers at 440 bp in six months, about 22.9% annualised.

    The book's coupon, price, and duration are not in the methodology. Assumptions:
    yield = 540 bp + 5.0% Treasury = 10.4%; carry = yield * h; compound annualising.
    With spread duration 4 the trade gives about 19.2%; test a 17%-25% bound.
    Spread duration 5.66 (a seven-to-eight-year B bond) reproduces 22.9%.
    """
    r4 = sg.spread_tightening_return(0.054, 0.044, 4.0, 0.104, 0.5)
    assert r4.price_return == pytest.approx(0.04)
    assert 0.17 < r4.annualised < 0.25
    r = sg.spread_tightening_return(0.054, 0.044, 5.66, 0.104, 0.5)
    assert r.annualised == pytest.approx(0.229, abs=0.003)


def test_s2_positive_when_fundamentals_lead_spread():
    # Fair spread fell 20% on fundamentals; market spread fell only 5%: long.
    s = sg.s2_momentum(s_fair_t=[0.040], s_fair_prev=[0.050], s_t=[0.0475], s_prev=[0.050])
    assert s[0] > 0


def test_s3_signs_and_bias():
    rev = np.array([-0.5, 0.5, 0.0])
    gap = np.array([-0.3, 0.3, 0.0])
    s = sg.s3_revision_gap(rev, gap)
    assert s[0] > 0 > s[1]
    # A conservative analyst (bias +0.3) has no real gap on bond 0.
    s_b = sg.s3_revision_gap(np.zeros(3), gap, bias=np.array([-0.3, 0.3, 0.0]))
    np.testing.assert_allclose(s_b, 0.0)
    b = sg.analyst_bias(["a", "a", "b"], [5.0, 4.0, 3.0], [4.5, 3.5, 3.0])
    assert b == {"a": pytest.approx(0.5), "b": pytest.approx(0.0)}


def test_s4_hca_unsecured_rich():
    # Unsecured 60 bp over second lien; fair gap with lambda 4%, kappa 1.5, LGD gap 0.25 is 150 bp: short unsecured.
    s = sg.s4_pair_score(0.0660, 0.0600, 1.5, 0.04, 0.70, 0.45, 0.005)
    assert s < 0
    assert sg.spread_per_turn(0.0060, 0.0, 1.7, 0.0) == pytest.approx(0.0060 / 1.7)


def test_s5_put_and_lme():
    assert sg.s5_put_value(0.5, 101.0, 95.0) == pytest.approx(0.5 * 6 / 95)
    assert sg.s5_put_value(0.5, 101.0, 103.0) == 0.0
    assert sg.s5_lme_value(0.3, 0.6, 0.3, 80.0) < 0 < sg.s5_lme_value(0.3, 0.4, 0.6, 80.0)


def test_s6_migration_monotone_in_gap():
    up, down = sg.migration_probabilities(np.array([-3, 0, 3]))
    assert np.all(np.diff(up) > 0) and np.all(np.diff(down) < 0)
    assert up[1] == pytest.approx(sg.P_UP_BASE) and down[1] == pytest.approx(sg.P_DOWN_BASE)
    assert np.all(up + down <= 0.95 + 1e-12)
    w = sg.flow_weight([1.0, 3.0], [0.5, 0.5])
    s6 = sg.s6_migration(up[[0, 2]], down[[0, 2]], w)
    assert s6[0] < 0 < s6[1]


def test_s7_tilt_broadcast():
    t = sg.s7_sector_tilt({"energy": 0.2, "health": -0.1}, {"energy": 0.0, "health": 0.0}, {"energy": 0.1}, theta=1.0)
    assert t == {"energy": pytest.approx(0.1), "health": pytest.approx(-0.1)}
    np.testing.assert_allclose(sg.apply_sector_tilt(["health", "energy", "tech"], t), [-0.1, 0.1, 0.0])


def test_composite_orthogonal_to_beta_and_duration(rng):
    n = 200
    beta = rng.normal(1.0, 0.3, n)
    dur = rng.uniform(2, 7, n)
    raw = np.column_stack([2 * beta + rng.normal(size=n), dur + rng.normal(size=n), rng.normal(size=n)])
    c = sg.composite(raw, np.array([0.5, 0.3, 0.2]), beta, dur)
    X = np.column_stack([np.ones(n), beta, dur])
    np.testing.assert_allclose(X.T @ c, 0.0, atol=1e-8)


def test_standardise_by_date_unit_variance(rng):
    df = pd.DataFrame({"date": np.repeat([1, 2], 50), "s1": rng.normal(5, 3, 100)})
    out = sg.standardise_by_date(df, ["s1"])
    g = out.groupby("date")["s1"]
    np.testing.assert_allclose(g.mean(), 0.0, atol=1e-12)
    np.testing.assert_allclose(g.std(ddof=1), 1.0)


def test_ic_weights_zero_for_negative_ic():
    ic = pd.DataFrame({"expansion": [0.05, -0.02, 0.15], "recession": [-0.1, -0.2, -0.05]}, index=["s1", "s2", "s3"])
    w = sg.ic_weights(ic, "expansion")
    assert w["s2"] == 0.0
    assert w.sum() == pytest.approx(1.0)
    assert w["s3"] == pytest.approx(0.75)
    assert (sg.ic_weights(ic, "recession") == 0.0).all()


def test_adv_cap_keeps_sign():
    np.testing.assert_allclose(sg.adv_cap([-10.0, 3.0], [2.0, 2.0], 2.0), [-4.0, 3.0])


def test_force_rank_whole_universe():
    fr = sg.force_rank(["a", "b", "c"], [0.1, 0.9, -0.5])
    assert fr["id"].tolist() == ["b", "a", "c"]
    assert fr["force_rank"].tolist() == [1, 2, 3]


def test_admit_refuses_missing_replaces_position():
    with pytest.raises(sg.MissingReplacementError):
        sg.admit_position("new", None, {"a", "b"})
    with pytest.raises(sg.MissingReplacementError):
        sg.admit_position("new", "  ", {"a", "b"})
    with pytest.raises(sg.MissingReplacementError):
        sg.admit_position("new", "zzz", {"a", "b"})
    assert sg.admit_position("new", "a", {"a", "b"}) == {"new", "b"}
    assert sg.admit_position("new", sg.CASH, {"a"}) == {"new", "a"}


def test_rank_ic_net_of_costs_by_phase(rng):
    n, dates = 100, 6
    rows = []
    for d in range(dates):
        s = rng.normal(size=n)
        ret = 0.01 * s + rng.normal(scale=0.002, size=n)
        phase = "expansion" if d < 3 else "recession"
        net = sg.net_return(ret, turnover=np.ones(n), bid_ask_bp=np.full(n, 50.0), spread_duration=np.full(n, 4.0))
        rows.append(pd.DataFrame({"date": d, "cycle_phase": phase, "good": s, "bad": -s, "ret_net": net}))
    ic = sg.rank_ic_by_phase(pd.concat(rows), ["good", "bad"])
    assert (ic.loc["good"] > 0.8).all() and (ic.loc["bad"] < -0.8).all()
    assert sg.net_return(0.01, 1.0, 50.0, 4.0) == pytest.approx(0.01 - 0.01)


def test_cycle_pass_three_of_four():
    assert sg.passes_cycle_test({2008: 0.02, 2015: 0.01, 2020: -0.01, 2022: 0.03})
    assert not sg.passes_cycle_test({2008: 0.02, 2015: -0.01, 2020: -0.01, 2022: 0.03})
    assert sg.passes_cycle_test({2008: 0.02, 2015: 0.01, 2022: 0.03, 2020: np.nan})
    assert not sg.passes_cycle_test({2008: 0.02, 2015: np.nan, 2022: 0.03, 2020: -0.1})
    assert not sg.passes_cycle_test({2008: 0.02, 2015: 0.01})
