"""G5 macro link: the issuer-macro downside model of methodology 5.2.1 as estimate E17 (decision 2026-10-24-macro-link-method)."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from hy import forward, groups

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import process  # noqa: E402

MODEL = forward.IssuerMacroModel(
    theta0=-2.0, theta_x={"net_leverage": 0.4, "interest_cover": -0.3}, theta_m={"ebp": 0.8, "default_rate_ttm": 10.0},
    theta_sector={"Energy": 0.5}, gamma={"CCC": {"ebp": -0.8}}, tau2=0.2, available_at=pd.Timestamp("2026-01-31"))
M = {"ebp": 1.0, "default_rate_ttm": 0.03}


def test_probability_rises_with_leverage_and_the_macro_stress():
    lo = MODEL.predict({"net_leverage": 3.0, "interest_cover": 2.0}, M)
    hi = MODEL.predict({"net_leverage": 6.0, "interest_cover": 2.0}, M)
    worse = MODEL.predict({"net_leverage": 3.0, "interest_cover": 2.0}, {**M, "ebp": 2.0})
    assert 0 < lo < hi < 1 and worse > lo


def test_year_term_is_zero_at_prediction():
    z = -2.0 + 0.4 * 3.0 - 0.3 * 2.0 + 0.8 * 1.0 + 10.0 * 0.03
    assert MODEL.predict({"net_leverage": 3.0, "interest_cover": 2.0}, M) == pytest.approx(1 / (1 + np.exp(-z)))


def test_rating_bucket_slope_adds_to_the_pooled_slope():
    x = {"net_leverage": 3.0, "interest_cover": 2.0}
    # gamma_CCC cancels the pooled EBP slope: macro does not move a CCC issuer (Figlewski et al., test T7).
    assert MODEL.predict(x, {**M, "ebp": 3.0}, bucket="CCC") == pytest.approx(MODEL.predict(x, M, bucket="CCC"))


def test_missing_input_gives_nan_not_zero():
    assert np.isnan(MODEL.predict({"net_leverage": 3.0}, M))
    assert np.isnan(MODEL.predict({"net_leverage": 3.0, "interest_cover": np.nan}, M))
    assert np.isnan(MODEL.predict({"net_leverage": 3.0, "interest_cover": 2.0}, {"ebp": 1.0}))


def test_no_model_or_a_later_fit_gives_no_view():
    cs = {"net_lev": 4.0, "cash_cov": 2.0}
    assert np.isnan(process._macro_logit(None, M, cs, {}, pd.Timestamp("2026-06-30")))
    assert np.isnan(process._macro_logit(MODEL, M, cs, {}, pd.Timestamp("2025-12-31")))  # fit not yet known: look-ahead
    assert np.isnan(process._macro_logit(MODEL, M, cs, {}, None))


def test_rating_history_is_not_stored_so_a_model_that_needs_it_gives_nan():
    m = forward.IssuerMacroModel(theta0=-2.0, theta_x={"net_leverage": 0.4, "downgrade_2y": 0.446}, theta_m={"ebp": 0.8})
    assert np.isnan(process._macro_logit(m, M, {"net_lev": 4.0}, {}, pd.Timestamp("2026-06-30")))


def test_macro_link_bucket_has_zero_share_until_its_tests_pass():
    assert groups.ESTIMATES["E17"][0] == "G5" and groups.ESTIMATES["E17"][2] == "score"
    assert groups.GROUP_WEIGHTS["G5"] == 0.0 and groups.effective_weights()["E17"] == 0.0


def test_e17_does_not_move_the_combination_or_the_agreement_count():
    base = {"E1": 100.0, "E9": -20.0, "E14": 40.0}
    a = groups.combine(base, 10, 100)
    b = groups.combine({**base, "E17": -500.0}, 10, 100)
    assert b["combined_after_cost"] == pytest.approx(a["combined_after_cost"])
    assert b["groups_n"] == a["groups_n"] and b["groups_agree"] == a["groups_agree"]
    assert b["groups"]["G5"]["present"] and b["groups"]["G5"]["contribution"] == 0.0
