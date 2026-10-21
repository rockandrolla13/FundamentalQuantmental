"""Tests for hy/forward.py (methodology Section 5)."""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

from hy.forward import (
    DebtLine,
    IssuerStart,
    annual_to_quarterly,
    base_scenario,
    breach_probability,
    build_scenario_set,
    decline_labels,
    downside_scenario,
    fit_decline_model,
    fit_sector_beta,
    forward_features,
    growth_shift,
    run_scenario,
    run_scenarios,
    scenario_weights,
    severe_scenario,
    upside_scenario,
)

H = 8
DRIVERS = dict(v=0.60, a=0.20, inventory_days=60.0, receivable_days=45.0, payable_days=40.0, capex=8.0)


def make_start(float_share: float = 0.5, revolver: float = 50.0, cash0: float = 20.0) -> IssuerStart:
    total = 400.0
    lines = (
        DebtLine("term_loan", face=total * float_share, floating=True, spread=0.035, floor=0.005, amort=1.0),
        DebtLine("notes", face=total * (1 - float_share), coupon=0.07, maturity_q=6, refi_coupon=0.09),
    )
    return IssuerStart(
        revenue_q0=100.0,
        ebitda_hist=(20.0, 20.0, 20.0, 20.0),
        interest_hist=(6.5, 6.5, 6.5, 6.5),
        cash0=cash0,
        debt_lines=lines,
        revolver_commitment=revolver,
        revolver_spread=0.03,
        commitment_fee=0.005,
        inventory_days0=60.0,
        receivable_days0=45.0,
        payable_days0=40.0,
        cogs_ratio0=0.60,
        da_q=5.0,
        tax_rate=0.25,
    )


def make_base(g: float = 0.01):
    return base_scenario(H, g=g, **DRIVERS)


SOFR = np.full(H, 0.04)


@pytest.mark.parametrize("sweep", [0.0, 1.0])
def test_accounting_identity_each_quarter(sweep):
    start = replace(make_start(), sweep_share=sweep)
    for scen in build_scenario_set(DRIVERS, horizon=H, analyst_g=0.01).values():
        p = run_scenario(start, scen, SOFR, covenant_max_leverage=6.0)
        net_debt = p.debt - p.cash
        prev = np.concatenate(([start.debt0 - start.cash0], net_debt[:-1]))
        np.testing.assert_allclose(net_debt - prev, -p.fcf, atol=1e-9)


def test_higher_rate_path_lowers_fcf_raises_leverage():
    scen = make_base()
    # Cash kept on balance sheet: net leverage carries the rate shock.
    start = make_start(float_share=0.6)
    lo = run_scenario(start, scen, np.full(H, 0.02))
    hi = run_scenario(start, scen, np.full(H, 0.06))
    assert np.all(hi.fcf < lo.fcf)
    assert np.all(hi.net_leverage > lo.net_leverage)
    assert np.all(hi.coverage < lo.coverage)
    # Cash sweep into the term loan: gross leverage carries it too.
    swept = replace(start, sweep_share=1.0)
    lo_s = run_scenario(swept, scen, np.full(H, 0.02))
    hi_s = run_scenario(swept, scen, np.full(H, 0.06))
    assert np.all(hi_s.leverage > lo_s.leverage)


def test_downside_leverage_at_or_above_base():
    start = make_start()
    paths = run_scenarios(start, list(build_scenario_set(DRIVERS, horizon=H, analyst_g=0.01).values()), SOFR)
    assert np.all(paths["down_moderate"].leverage >= paths["base"].leverage - 1e-12)
    assert np.all(paths["down_severe"].leverage >= paths["down_moderate"].leverage - 1e-12)
    assert np.all(paths["upside"].leverage <= paths["base"].leverage + 1e-12)


def test_tm_corp_recession_conversion():
    g = annual_to_quarterly([-0.20, -0.10])
    assert g.size == 8
    assert np.prod(1 + g[:4]) == pytest.approx(0.80)
    assert np.prod(1 + g) == pytest.approx(0.72)


def test_downside_shapes_and_main_risk():
    base = make_base(0.0)
    for shape in ("v", "u", "structural", "customer_replace"):
        assert downside_scenario(base, recession_annual=(-0.2,), recovery_shape=shape).recovery_shape == shape
    v = downside_scenario(base, recession_annual=(-0.2,), recovery_shape="v")
    s = downside_scenario(base, recession_annual=(-0.2,), recovery_shape="structural")
    lvl = lambda sc: np.cumprod(1 + sc.g)[-1]
    assert lvl(v) == pytest.approx(1.0)  # back to the base level
    assert lvl(s) == pytest.approx(0.8)  # new lower level
    cc = downside_scenario(base, main_risk="customer_concentration", customer_share=0.25)
    assert cc.recovery_shape == "customer_replace" and cc.g[0] == pytest.approx(-0.25)
    sup = downside_scenario(base, main_risk="single_source_supplier", margin_squeeze=0.03)
    np.testing.assert_allclose(sup.g, base.g)
    np.testing.assert_allclose(sup.v, base.v + 0.03)
    sev = severe_scenario(base)
    assert np.all(sev.payable_days < base.payable_days)
    with pytest.raises(ValueError):
        downside_scenario(base, main_risk="bad_flag")


def test_upside_mirrors_moderate():
    base = make_base(0.0)
    mod = downside_scenario(base, recession_annual=(-0.2,))
    up = upside_scenario(base, mod)
    r_down = np.cumprod(1 + mod.g)
    r_up = np.cumprod(1 + up.g)
    np.testing.assert_allclose(r_up - 1.0, 1.0 - r_down, atol=1e-12)


def test_fallback_order_sets_forecast_source():
    assert build_scenario_set(DRIVERS, analyst_g=0.01, consensus_g=0.02)["base"].forecast_source == "analyst"
    assert build_scenario_set(DRIVERS, consensus_g=0.02, trend_g=0.0)["base"].forecast_source == "consensus_template"
    s = build_scenario_set(DRIVERS, trend_g=0.005)
    assert all(sc.forecast_source == "trend_template" for sc in s.values())
    with pytest.raises(ValueError):
        build_scenario_set(DRIVERS)


def test_weights_sum_to_one_and_rise_with_stress(rng):
    n = 4000
    m = rng.normal(size=(n, 2))  # columns: hy_oas z-score, pmi z-score
    sectors = rng.choice(["energy", "health", "retail"], size=n)
    z = -1.5 + 1.2 * m[:, 0] - 0.8 * m[:, 1] + np.where(sectors == "retail", 0.5, 0.0)
    y = (rng.random(n) < 1 / (1 + np.exp(-z))).astype(int)
    down = fit_decline_model(m, sectors, y)
    up = fit_decline_model(m, sectors, (rng.random(n) < 1 / (1 + np.exp(1.5 + 1.0 * m[:, 0]))).astype(int), "up")
    calm, stress = np.array([-1.0, 1.0]), np.array([2.0, -2.0])
    w_calm = scenario_weights(down.predict(calm, "retail"), up.predict(calm, "retail"))
    w_stress = scenario_weights(down.predict(stress, "retail"), up.predict(stress, "retail"))
    for w in (w_calm, w_stress):
        assert sum(w.values()) == pytest.approx(1.0)
        assert all(v >= 0 for v in w.values())
    assert w_stress["down_moderate"] + w_stress["down_severe"] > w_calm["down_moderate"] + w_calm["down_severe"]
    # Overflow case: both probabilities high still gives valid weights.
    w = scenario_weights(0.9, 0.8)
    assert sum(w.values()) == pytest.approx(1.0) and w["base"] == pytest.approx(0.0)


def test_logistic_recovers_coefficient_signs(rng):
    n = 5000
    m = rng.normal(size=(n, 3))
    sectors = rng.choice(["a", "b"], size=n)
    z = -1.0 + 1.5 * m[:, 0] - 1.0 * m[:, 1] + 0.0 * m[:, 2] + np.where(sectors == "b", 1.0, 0.0)
    y = (rng.random(n) < 1 / (1 + np.exp(-z))).astype(int)
    model = fit_decline_model(m, sectors, y)
    assert model.theta[0] > 0 and model.theta[1] < 0
    assert abs(model.theta[2]) < 0.2
    assert model.theta_sector["b"] > 0 and model.theta_sector["a"] == 0.0
    assert model.theta0 == pytest.approx(-1.0, abs=0.2)


def test_decline_labels():
    e0 = np.array([100.0, 100.0, 100.0])
    e4 = np.array([70.0, 90.0, 130.0])
    np.testing.assert_array_equal(decline_labels(e0, e4, 0.2), [1, 0, 0])
    np.testing.assert_array_equal(decline_labels(e0, e4, 0.2, "up"), [0, 0, 1])


def test_sector_beta_and_growth_shift(rng):
    G = rng.normal(0.005, 0.01, size=200)
    gr = 0.002 + 1.8 * G + rng.normal(0, 0.002, size=200)
    beta, se = fit_sector_beta(gr, G)
    assert beta == pytest.approx(1.8, abs=4 * se)
    shift = growth_shift(beta, np.full(H, -0.01), 0.005)
    assert np.all(shift < 0)
    s_shift = build_scenario_set(DRIVERS, analyst_g=0.01, growth_shift=shift)["base"]
    np.testing.assert_allclose(s_shift.g, 0.01 + shift)


def test_p_breach_monotone_in_covenant_tightness():
    start = make_start()
    scen = list(build_scenario_set(DRIVERS, horizon=H, analyst_g=0.01).values())
    w = scenario_weights(0.3, 0.1)
    prev = -1.0
    for max_lev in (8.0, 7.0, 6.0, 5.5, 5.0, 4.5):
        paths = run_scenarios(start, scen, SOFR, covenant_max_leverage=max_lev)
        p = breach_probability(paths, w, 8)
        assert p >= prev - 1e-12
        prev = p
    assert prev > 0.5


def test_liquidity_nonnegative_while_revolver_available():
    start = make_start(revolver=500.0, cash0=5.0)
    sev = severe_scenario(make_base(0.0), recession_annual=(-0.3, -0.2))
    p = run_scenario(start, sev, SOFR)
    avail = start.revolver_commitment - p.revolver_drawn
    assert np.all(avail > 0)
    assert np.all(p.liquidity >= 0)
    assert np.all(p.cash >= -1e-9)
    # With a small revolver the same case runs out of liquidity.
    tight = run_scenario(make_start(revolver=5.0, cash0=5.0), sev, SOFR)
    assert tight.liquidity.min() < 0


def test_forward_features_contents():
    start = make_start()
    scen = build_scenario_set(DRIVERS, horizon=H, analyst_g=0.01)
    paths = run_scenarios(start, list(scen.values()), SOFR, covenant_max_leverage=6.0)
    w = scenario_weights(0.3, 0.1)
    f = forward_features(paths, w, lev_t=start.lev0, debt_t=start.debt0, consensus_lev_4=5.0,
                         mgmt_lev_4=4.5, prior_lev_fwd_4=5.2)
    for h in (4, 8):
        for k in ("lev_fwd", "delev", "lev_fwd_sd", "p_breach", "p_liq_short", "p_refi", "cov_fwd"):
            assert f"{k}_{h}" in f
        assert 0.0 <= f[f"p_breach_{h}"] <= 1.0
    lev4 = [paths[s].leverage[3] for s in w]
    assert min(lev4) <= f["lev_fwd_4"] <= max(lev4)
    assert f["delev_4"] == pytest.approx(f["lev_fwd_4"] - start.lev0)
    assert f["lev_peak_down"] == pytest.approx(paths["down_severe"].leverage.max())
    assert f["liq_min_down"] == pytest.approx(paths["down_severe"].liquidity.min())
    assert f["gap_consensus"] == pytest.approx(paths["base"].leverage[3] - 5.0)
    assert f["rev_lev"] == pytest.approx(f["lev_fwd_4"] - 5.2)
    assert f["downside_is_base"] is False and f["forecast_source"] == "analyst"
    assert forward_features(paths, scenario_weights(0.7, 0.05), start.lev0, start.debt0)["downside_is_base"] is True
    with pytest.raises(ValueError):
        forward_features(paths, {"base": 0.5, "upside": 0.2}, start.lev0, start.debt0)


def test_refi_wall_flags_maturity():
    start = make_start()
    p = run_scenario(start, make_base(), SOFR)
    assert np.all(np.isfinite(p.wall_cover))  # term loan amortises from h = 1
    assert p.wall_cover[5] < 1.0  # the notes mature at h = 6 and exceed liquidity plus FCF
    # Refinance at 9% raises interest after maturity.
    assert p.interest[6] > p.interest[5]


def test_downside_weights_split_p_between_moderate_and_severe():
    # Section 5.2 and decision 2026-10-21-downside-weight-split: moderate (1 - f)p, severe fp, f = 0.25.
    from hy.forward import scenario_weights

    w = scenario_weights(0.2, 0.1)
    assert w["down_moderate"] == pytest.approx(0.15)
    assert w["down_severe"] == pytest.approx(0.05)
    assert w["down_moderate"] + w["down_severe"] == pytest.approx(0.2)
    assert sum(w.values()) == pytest.approx(1.0)
