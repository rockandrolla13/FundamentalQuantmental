"""How much alpha: the risk premium test of methodology 7.7 (decision 2026-10-25-risk-premium-alpha)."""

import numpy as np
import pandas as pd
import pytest

from hy import alpha


def _paths(spreads, d, p=(0.7, 0.2, 0.1), y=0.04):
    return pd.DataFrame({"macro_path": ["good", "slow", "bad"], "p_path": list(p), "d_h": list(d), "y_H": y,
                         "s_H": list(spreads)})


def test_spec_es_example_returns_0_56():
    # Specification p. 27: losses 0.10, 0.20, 0.80 with probabilities 0.90, 0.07, 0.03 give ES95 = 0.56.
    assert alpha.expected_shortfall([-0.10, -0.20, -0.80], [0.90, 0.07, 0.03], 0.95) == pytest.approx(0.56)


def test_unchanged_spreads_and_no_default_earn_the_spread_over_treasuries():
    par = alpha.bond_price(0.09, 5.0, 0.09)
    r = alpha.credit_excess_states(par, 0.09, 5.0, 0.5, _paths([0.05] * 3, [0.0] * 3), 0.4,
                                   r_tsy=alpha.treasury_return(0.04, 0.04, 5.0, 0.5))
    assert r["mu"] * 2 == pytest.approx(0.05, abs=0.004)  # about the spread a year
    assert r["es"] < 0  # no path loses against Treasuries


def test_costs_lower_the_return_by_the_round_trip():
    par = alpha.bond_price(0.09, 5.0, 0.09)
    kw = dict(paths=_paths([0.05, 0.06, 0.09], [0.0, 0.01, 0.05]), recovery_pv_per_1=0.35, r_tsy=0.02)
    free = alpha.credit_excess_states(par, 0.09, 5.0, 0.5, **kw)["mu"]
    paid = alpha.credit_excess_states(par, 0.09, 5.0, 0.5, cost_in=0.00075, cost_out=0.00075, **kw)["mu"]
    assert free - paid == pytest.approx(0.0015, abs=1e-4)


def test_more_default_or_wider_bad_path_raises_the_tail_and_lowers_the_return():
    par = alpha.bond_price(0.09, 5.0, 0.09)
    base = alpha.credit_excess_states(par, 0.09, 5.0, 0.5, _paths([0.05, 0.06, 0.09], [0.0, 0.01, 0.05]), 0.35, 0.02)
    worse = alpha.credit_excess_states(par, 0.09, 5.0, 0.5, _paths([0.05, 0.06, 0.12], [0.0, 0.01, 0.10]), 0.35, 0.02)
    assert worse["es"] > base["es"] and worse["mu"] < base["mu"]


def test_alpha_is_return_less_risk_at_the_index_price():
    a = alpha.risk_premium_alpha(mu_bond=0.030, es_bond=0.08, mu_index=0.020, es_index=0.05)
    assert a["lambda"] == pytest.approx(0.4) and a["required"] == pytest.approx(0.032)
    assert a["alpha"] == pytest.approx(-0.002)  # wide enough to beat cash, too thin for its risk


def test_same_risk_as_the_index_needs_the_index_return():
    a = alpha.risk_premium_alpha(0.020, 0.05, 0.020, 0.05)
    assert a["alpha"] == pytest.approx(0.0)


def test_no_index_tail_loss_leaves_the_price_of_risk_undefined():
    a = alpha.risk_premium_alpha(0.03, 0.05, 0.02, -0.01)
    assert np.isnan(a["alpha"]) and "undefined" in a["flag"]


def test_negative_index_excess_charges_nothing_and_says_so():
    a = alpha.risk_premium_alpha(0.01, 0.05, -0.01, 0.04)
    assert a["lambda"] == 0.0 and a["alpha"] == pytest.approx(0.01) and a["flag"]


def test_probabilities_must_sum_to_one():
    with pytest.raises(ValueError):
        alpha.credit_excess_states(100.0, 0.09, 5.0, 0.5, _paths([0.05] * 3, [0.0] * 3, p=(0.5, 0.2, 0.1)), 0.4, 0.02)
