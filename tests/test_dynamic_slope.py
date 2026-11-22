"""Tests for hy.dynamic_slope: recovery of known slopes, pooling, the causal filter, and no look-ahead."""

import numpy as np
import pandas as pd
import pytest

from hy.dynamic_slope import (class_slopes, dynamic_esp, estimate_q, local_level_filter, ols_slope_se,
                              pool_slopes, random_effects, split_esp, state_slope)

TRUE = {"BB": 0.05, "B": 0.12, "CCC": 0.30}


def synthetic(months: int = 48, issuers: int = 40, bonds: int = 2, noise: float = 0.15, seed: int = 3,
              true: dict | None = None) -> pd.DataFrame:
    """Bonds with ESP = b_k * XL + issuer effect + bond noise. XL is shared by the bonds of one issuer."""
    rng = np.random.default_rng(seed)
    true = true or TRUE
    rows = []
    for t in range(months):
        for k, b in true.items():
            xl = rng.normal(0, 0.6, issuers)
            u = rng.normal(0, noise, issuers)
            for i in range(issuers):
                for j in range(bonds):
                    rows.append({"month": t, "rclass": k, "gvkey": f"{k}{i}",
                                 "xlev": xl[i], "esp": b * xl[i] + u[i] + rng.normal(0, noise)})
    return pd.DataFrame(rows)


ROWS = synthetic()


def test_ols_slope_matches_numpy_and_cluster_se_is_wider():
    rng = np.random.default_rng(0)
    xi, ui = rng.normal(size=50), rng.normal(size=50)
    x, y = np.repeat(xi, 4), np.repeat(0.2 * xi + ui, 4) + 0.05 * rng.normal(size=200)
    b, se = ols_slope_se(y, x)
    assert b == pytest.approx(np.polyfit(x, y, 1)[0], rel=1e-10)
    _, se_cl = ols_slope_se(y, x, np.repeat(np.arange(50), 4))
    assert se_cl > 1.5 * se  # four copies of each issuer: the plain se is about half the true one


def test_class_slopes_recover_the_true_slope_per_class():
    cs = class_slopes(ROWS)
    mean = cs.groupby("rclass")["b_raw"].mean()
    for k, b in TRUE.items():
        assert mean[k] == pytest.approx(b, abs=0.02)
    assert cs["se"].gt(0).all()


def test_small_class_gets_no_slope():
    small = ROWS[~((ROWS.rclass == "CCC") & (ROWS.gvkey.str.extract(r"(\d+)$")[0].astype(int) >= 8))]
    cs = class_slopes(small)
    assert cs.loc[cs.rclass == "CCC", "b_raw"].isna().all()


def test_random_effects_tau2_is_zero_for_equal_slopes_and_positive_for_different():
    se = np.full(3, 0.02)
    mu, tau2, _ = random_effects(np.array([0.1, 0.1, 0.1]), se)
    assert (mu, tau2) == (pytest.approx(0.1), 0.0)
    mu, tau2, _ = random_effects(np.array([0.05, 0.12, 0.30]), se)
    assert tau2 > 0.005 and 0.05 < mu < 0.30


def test_pooling_pulls_a_noisy_class_more_than_a_precise_one():
    cs = pd.DataFrame({"month": 0, "rclass": ["BB", "B", "CCC"],
                       "b_raw": [0.05, 0.12, 0.60], "se": [0.01, 0.01, 0.30]})
    p = pool_slopes(cs).set_index("rclass")
    assert p.loc["CCC", "w"] < 0.2 < 0.9 < p.loc["BB", "w"]
    assert abs(p.loc["CCC", "b_pool"] - p.loc["CCC", "mu"]) < abs(0.60 - p.loc["CCC", "mu"])
    assert p.loc["BB", "b_pool"] == pytest.approx(0.05, abs=0.01)


def test_pooling_gives_mu_to_a_class_without_its_own_slope():
    cs = pd.DataFrame({"month": 0, "rclass": ["BB", "B", "CCC"], "b_raw": [0.05, 0.12, np.nan],
                       "se": [0.01, 0.02, np.nan]})
    p = pool_slopes(cs).set_index("rclass")
    assert p.loc["CCC", "b_pool"] == pytest.approx(p.loc["CCC", "mu"])
    assert np.isfinite(p.loc["CCC", "v"])


def test_filter_is_flat_on_a_constant_input_and_ignores_a_noisy_jump():
    y = pd.Series([0.1] * 10 + [0.9] + [0.1] * 5)
    precise = pd.Series([1e-4] * 10 + [1.0] + [1e-4] * 5)  # the jump month is very noisy
    f = local_level_filter(y, precise, q=1e-4)
    assert f["b"].iloc[:10].tolist() == pytest.approx([0.1] * 10)
    assert f["b"].iloc[10] < 0.11
    assert f["K"].iloc[10] < 0.01


def test_filter_follows_a_precise_change():
    y = pd.Series([0.1] * 10 + [0.3] * 10)
    f = local_level_filter(y, pd.Series([1e-4] * 20), q=1e-3)
    assert f["b"].iloc[-1] == pytest.approx(0.3, abs=0.01)


def test_filter_keeps_the_prediction_on_a_missing_month():
    f = local_level_filter(pd.Series([0.1, np.nan, 0.1]), pd.Series([0.01, np.nan, 0.01]), q=0.001)
    assert f["b"].iloc[1] == pytest.approx(0.1)
    assert f["P"].iloc[1] > f["P"].iloc[0]


def test_estimate_q_is_zero_for_pure_noise_and_positive_for_a_random_walk():
    rng = np.random.default_rng(5)
    r = pd.Series(np.full(400, 0.01))
    noise = pd.Series(0.1 + rng.normal(0, 0.1, 400))
    walk = pd.Series(np.cumsum(rng.normal(0, 0.1, 400)) + rng.normal(0, 0.1, 400))
    assert estimate_q(noise, r) < 0.003
    assert estimate_q(walk, r) == pytest.approx(0.01, rel=0.3)


def test_state_slope_recovers_the_steepening():
    rng = np.random.default_rng(9)
    m = pd.Series(rng.uniform(0.6, 2.0, 120))
    b = 0.02 + 0.08 * m + rng.normal(0, 0.005, 120)
    s = state_slope(b, pd.Series(np.full(120, 0.005 ** 2)), m)
    assert s["b_state"].iloc[:24].isna().all()
    assert s["c"].iloc[-1] == pytest.approx(0.08, abs=0.005)


def test_state_slope_has_no_lookahead():
    rng = np.random.default_rng(9)
    m = pd.Series(rng.uniform(0.6, 2.0, 80))
    b = 0.02 + 0.08 * m
    v = pd.Series(np.full(80, 1e-4))
    base = state_slope(b, v, m)
    bad = b.copy()
    bad.iloc[50:] = 5.0
    assert np.allclose(base.iloc[:51].dropna(), state_slope(bad, v, m).iloc[:51].dropna())


def test_split_adds_back_to_esp():
    sp = split_esp(ROWS["esp"], ROWS["xlev"], pd.Series(0.12, index=ROWS.index))
    assert np.allclose(sp["priced_lev"] + sp["resid_esp"], ROWS["esp"])


def test_dynamic_esp_runs_end_to_end_and_keeps_the_rows():
    out, slopes = dynamic_esp(ROWS, q=1e-4)
    assert out.index.equals(ROWS.index) and len(out) == len(ROWS)
    assert out["b_dyn"].notna().all()
    last = slopes[slopes.month == slopes.month.max()].set_index("rclass")
    for k, b in TRUE.items():
        assert abs(last.loc[k, "b_dyn"] - b) < 3 * np.sqrt(last.loc[k, "P"])  # inside the filter's own band
    for _, c in slopes.groupby("rclass"):  # the filter cuts the month-to-month noise of the raw slope
        assert c["b_dyn"].diff().std() < c["b_raw"].diff().std() / 3
    # the residual no longer loads on leverage inside a class
    assert abs(np.corrcoef(out["resid_esp"], out["xlev"])[0, 1]) < 0.05


def test_dynamic_esp_has_no_lookahead():
    cut = 30
    base, _ = dynamic_esp(ROWS, q=1e-4)
    bad = ROWS.copy()
    late = bad.month >= cut
    bad.loc[late, "esp"] = bad.loc[late, "xlev"] * 2.0 + 1.0  # a very different later world
    moved, _ = dynamic_esp(bad, q=1e-4)
    early = ROWS.month < cut
    assert np.allclose(base.loc[early, "b_dyn"], moved.loc[early, "b_dyn"])
    assert np.allclose(base.loc[early, "resid_esp"], moved.loc[early, "resid_esp"])
