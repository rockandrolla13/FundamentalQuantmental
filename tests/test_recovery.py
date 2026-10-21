"""Tests for hy/recovery.py (methodology Section 6)."""

from __future__ import annotations

import math
from datetime import datetime

import numpy as np
import pytest

from hy import recovery as rc
from hy.inputs import Tranche

T0 = datetime(2025, 3, 31)
T1 = datetime(2025, 5, 1)


def _tr(key: str, rank: int, face: float, price: float = 100.0) -> Tranche:
    return Tranche(key=key, as_of=T0, available_at=T1, issuer_id="X", rank=rank, face=face, price=price)


# 6.1 ---------------------------------------------------------------------------


def test_lognormal_params_match_percentiles():
    mu, sigma = rc.lognormal_params(600.0, 800.0, 1000.0)
    assert mu == pytest.approx(math.log(800.0))
    assert sigma == pytest.approx((math.log(1000) - math.log(600)) / 2.56)
    with pytest.raises(ValueError):
        rc.lognormal_params(900.0, 800.0, 1000.0)


def test_value_methods():
    assert rc.comparables_value(100.0, 7.6) == pytest.approx(760.0)
    assert rc.precedent_value(100.0, 9.4) == pytest.approx(940.0)
    # Four quarters of 25, then a perpetuity of 100 a year at 10% and g = 0.
    disc = [1.1 ** -(q / 4) for q in range(1, 5)]
    expected = 25.0 * sum(disc) + 1000.0 * disc[-1]
    assert rc.dcf_value([25.0] * 4, 0.10, 0.0) == pytest.approx(expected)
    with pytest.raises(ValueError):
        rc.dcf_value([25.0], 0.05, 0.05)
    lo, mid, hi = rc.football_field({"comps": (700.0, 900.0), "dcf": (500.0, 1100.0)})
    assert (lo, hi) == (600.0, 1000.0) and mid == pytest.approx(math.sqrt(600_000.0))


def test_liquidation_value_vcc_rates():
    assets = {"cash": 10.0, "receivables": 100.0, "inventory": 100.0, "machinery": 100.0}
    gross = 10 + 0.90 * 100 + 0.675 * 100 + 0.15 * 100
    assert rc.liquidation_value(assets) == pytest.approx(0.95 * gross)
    assert rc.liquidation_value({"cash": 100.0}, wind_down=5.0) == pytest.approx(90.0)
    with pytest.raises(KeyError):
        rc.liquidation_value({"goodwill": 1.0})


def test_default_value_pu_corp_style():
    # A priming DIP takes value off the top (p. 503).
    assert rc.default_value(5.0, 80.0, dip=100.0, costs=20.0) == pytest.approx(280.0)
    assert rc.default_value(1.0, 10.0, dip=100.0) == 0.0


# 6.2 ---------------------------------------------------------------------------


@pytest.mark.parametrize("senior,face,sigma", [(0.0, 300.0, 0.3), (400.0, 300.0, 0.4), (900.0, 200.0, 0.5),
                                               (200.0, 500.0, 0.8)])
def test_closed_form_matches_monte_carlo(rng, senior, face, sigma):
    mu = math.log(800.0)
    cf = rc.recovery_closed_form(senior, face, mu, sigma)
    mc = rc.recovery_monte_carlo(senior, face, mu, sigma, rng, n=400_000)
    assert mc == pytest.approx(cf, rel=0.01, abs=0.002)


def test_closed_form_limits():
    mu = math.log(800.0)
    assert rc.recovery_closed_form(0.0, 100.0, mu, 0.01) == pytest.approx(1.0)
    assert rc.recovery_closed_form(5000.0, 100.0, mu, 0.01) == pytest.approx(0.0, abs=1e-9)
    assert rc.recovery_closed_form(750.0, 100.0, mu, 0.0) == pytest.approx(0.5)


def test_recovery_falls_as_senior_claims_rise():
    mu = math.log(800.0)
    r = [rc.recovery_closed_form(s, 200.0, mu, 0.4) for s in np.linspace(0, 1500, 16)]
    assert np.all(np.diff(r) < 0)


def test_recovery_rises_with_value():
    r = [rc.recovery_closed_form(500.0, 200.0, math.log(v), 0.4) for v in np.linspace(300, 2000, 16)]
    assert np.all(np.diff(r) > 0)


def test_senior_recovers_at_least_junior():
    s = [_tr("abl", 1, 100.0), _tr("tl", 2, 400.0), _tr("ssn", 3, 300.0), _tr("sub", 4, 200.0)]
    w = rc.waterfall(s, math.log(700.0), 0.4)
    vals = [w[k] for k in ("abl", "tl", "ssn", "sub")]
    assert all(a >= b for a, b in zip(vals, vals[1:]))


def test_pari_passu_split_pro_rata():
    s = [_tr("tl", 1, 400.0), _tr("ssn_a", 2, 300.0), _tr("ssn_b", 2, 100.0)]
    mu, sigma = math.log(600.0), 0.4
    w = rc.waterfall(s, mu, sigma)
    assert w["ssn_a"] == pytest.approx(w["ssn_b"])
    pool = rc.recovery_closed_form(400.0, 400.0, mu, sigma)
    assert w["ssn_a"] == pytest.approx(pool)
    # Dollar recoveries split by face: 3 to 1.
    assert (w["ssn_a"] * 300) / (w["ssn_b"] * 100) == pytest.approx(3.0)
    assert rc.senior_claims(s, "ssn_b") == (400.0, 400.0)


def test_waterfall_conserves_value():
    s = [_tr("a", 1, 200.0), _tr("b", 2, 300.0), _tr("c", 3, 500.0)]
    mu, sigma = math.log(600.0), 0.5
    w = rc.waterfall(s, mu, sigma)
    paid = sum(w[t.key] * t.face for t in s)
    expected = rc.recovery_closed_form(0.0, 1000.0, mu, sigma) * 1000.0  # E[min(V, total)]
    assert paid == pytest.approx(expected)


def test_market_checks():
    c = rc.check_creation_vs_distressed(4.0, 500.0, 100.0)
    assert c["price_below_recovery"] and c["distressed_multiple"] == 5.0
    assert rc.market_implied_recovery([45.0, 40.0, 42.0], [3.0, 10.0, 6.0]) == pytest.approx(0.40)


def test_ltv_scenarios_vcc_shape():
    # VCC: 67% at mid, 87% at low (p. 332). Given debt and those LTVs, the values round-trip.
    debt = 670.0
    v_mid, v_low = debt / 0.67, debt / 0.87
    out = rc.ltv_scenarios(debt, v_low, v_mid, 1.2 * v_mid)
    assert out["ltv_k_mid"] == pytest.approx(0.67)
    assert out["ltv_k_low"] == pytest.approx(0.87)
    assert out["ltv_k_low"] < 1.0  # still covered


# 6.3 ---------------------------------------------------------------------------


def test_lme_blend_bounds():
    for pi in (0.0, 0.3, 1.0):
        r = rc.recovery_adj(0.8, 0.3, pi)
        assert 0.3 <= r <= 0.8
    assert rc.recovery_adj(0.8, 0.3, 0.0) == 0.8
    assert rc.recovery_adj(0.8, 0.3, 1.0) == 0.3
    with pytest.raises(ValueError):
        rc.recovery_adj(0.8, 0.3, 1.2)


def test_pi_lme_monotone_and_bounded():
    assert 0 < rc.pi_lme(0.0, 0.0) < rc.pi_lme(2.0, 0.0) < rc.pi_lme(2.0, 0.5) < 1


def test_lme_score_directions():
    base = dict(v_mid=1000.0, face_k=300.0)
    s0 = rc.lme_score(**base)
    assert s0 == 0.0
    assert rc.lme_score(**base, unrestricted_sub_capacity=200.0) > s0
    assert rc.lme_score(**base, bare_majority=True) > s0
    assert rc.lme_score(**base, lien_basket=150.0) > s0
    assert rc.lme_score(**base, sponsor_behavior=2) > s0


def test_lme_stress_lowers_recovery():
    mu, sigma = math.log(800.0), 0.4
    clean = rc.recovery_closed_form(300.0, 300.0, mu, sigma)
    assert rc.recovery_lme(300.0, 300.0, mu, sigma, priming_debt=200.0) < clean
    assert rc.recovery_lme(300.0, 300.0, mu, sigma, value_stripped=200.0) < clean
    assert rc.recovery_lme(300.0, 300.0, mu, sigma, value_stripped=900.0) == 0.0


# 6.4 ---------------------------------------------------------------------------


def test_tranche_outputs_fields():
    s = [_tr("tl", 1, 400.0), _tr("ssn", 2, 300.0, price=70.0)]
    out = rc.tranche_outputs(s, "ssn", ebitda_adj=100.0, v_low=500.0, v_mid=700.0, v_high=900.0,
                             v_default=550.0, p_liq_8=0.2, lme_inputs={"bare_majority": True},
                             priming_debt=100.0)
    for f in ("tev_low", "tev_mid", "tev_high", "tev_default", "v_sigma", "ltv_k_low", "ltv_k_mid",
              "ltv_k_high", "recovery_k", "lgd_k", "recovery_k_adj", "lme_score_k", "pi_lme",
              "recovery_price_k", "creation_multiple_k"):
        assert f in out
    assert out["creation_multiple_k"] == pytest.approx((400 + 0.7 * 300) / 100)
    assert out["ltv_k_mid"] == pytest.approx(1.0)
    assert out["recovery_k_adj"] <= out["recovery_k"]
    assert out["recovery_price_k"] == pytest.approx(100 * out["recovery_k_adj"])
    assert out["lgd_k"] == pytest.approx(1 - out["recovery_k"])
