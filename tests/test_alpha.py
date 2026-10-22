import numpy as np
import pandas as pd
import pytest

from hy.alpha import BondInputs, alpha_table, expected_alpha, path_alpha, pd_over_horizon


def _paths(s_fair, pd12, p=(0.5, 0.3, 0.2)):
    return pd.DataFrame({"macro_path": ["soft_landing", "recession", "higher_for_longer"], "p_path": p,
                         "s_fair": s_fair, "pd_12m": pd12})


def test_parts_of_one_path():
    b = BondInputs("X", oas=0.05, spread_duration=4.0, rho_q=0.5, beta_mkt=0.8, index_spread=0.04, lgd=0.6)
    r = path_alpha(b, s_fair=0.04, pd_12m=0.02, h_years=1.0)
    assert r["carry"] == pytest.approx(0.05 - 0.032)
    assert r["converge"] == pytest.approx(4.0 * (1 - 0.5 ** 4) * 0.01)
    assert r["loss"] == pytest.approx(0.02 * 0.6)
    assert r["alpha"] == pytest.approx(r["carry"] + r["converge"] - r["loss"])


def test_fair_bond_unhedged_earns_carry_less_loss_only():
    b = BondInputs("X", oas=0.05, spread_duration=4.0, beta_mkt=0.0)
    r = expected_alpha(b, _paths([0.05] * 3, [0.02] * 3), h_years=1.0)
    assert r["converge_w"] == pytest.approx(0.0)
    assert r["alpha_net"] == pytest.approx(0.05 - 0.02 * 0.6)
    assert r["alpha_sd"] == pytest.approx(0.0)


def test_weighting_dispersion_cost_and_gate():
    b = BondInputs("X", oas=0.05, spread_duration=4.0, rho_q=0.0, beta_mkt=1.0, index_spread=0.05, bid_ask_bp=50)
    # Hedge carry cancels carry; convergence is the whole gap (rho 0); recession path makes the bond rich.
    r = expected_alpha(b, _paths([0.04, 0.07, 0.05], [0.0, 0.0, 0.0]), h_years=1.0)
    per = 4.0 * np.array([0.01, -0.02, 0.0])
    w = np.array([0.5, 0.3, 0.2])
    assert r["alpha_w"] == pytest.approx((per * w).sum())
    assert r["cost"] == pytest.approx(0.005 * 4.0)
    assert r["alpha_net"] == pytest.approx((per * w).sum() - 0.02)
    assert r["alpha_sd"] == pytest.approx(np.sqrt((w * (per - (per * w).sum()) ** 2).sum()))
    assert r["passes_g3"] is False  # cost exceeds the expected convergence


def test_probabilities_must_sum_to_one_and_weighted_row_is_ignored():
    b = BondInputs("X", oas=0.05, spread_duration=4.0)
    bad = _paths([0.05] * 3, [0.02] * 3, p=(0.5, 0.3, 0.3))
    with pytest.raises(ValueError):
        expected_alpha(b, bad)
    ok = pd.concat([_paths([0.05] * 3, [0.02] * 3), pd.DataFrame(
        {"macro_path": ["weighted"], "p_path": [1.0], "s_fair": [0.0], "pd_12m": [0.9]})])
    assert expected_alpha(b, ok)["loss_w"] == pytest.approx(pd_over_horizon(0.02, 0.5) * 0.6)


def test_table_ranks_cheap_bond_first():
    cheap = BondInputs("CHEAP", oas=0.07, spread_duration=4.0, rho_q=0.7)
    rich = BondInputs("RICH", oas=0.04, spread_duration=4.0, rho_q=0.7)
    t = alpha_table({"CHEAP": cheap, "RICH": rich},
                    {"CHEAP": _paths([0.05] * 3, [0.02] * 3), "RICH": _paths([0.05] * 3, [0.02] * 3)})
    assert t["cusip"].tolist() == ["CHEAP", "RICH"]
