"""Support contents against the support label (methodology Section 4.7.3)."""

import math

import numpy as np
import pandas as pd
import pytest

from hy import clocks
from hy.data.pit import LookAheadError

BASE = dict(coverage=0.9, contract_years=6.0, debt_years=5.0, non_cancellable=0.8, ig_share=0.7,
            commenced_share=0.6, reach_share=1.0)


def _s(**kw):
    return clocks.support_score(**{**BASE, **kw})


@pytest.mark.parametrize("part,lo,hi", [("coverage", 0.3, 0.9), ("contract_years", 2.0, 5.0),
                                        ("non_cancellable", 0.2, 0.8), ("ig_share", 0.0, 1.0),
                                        ("commenced_share", 0.0, 1.0), ("reach_share", 0.3, 1.0)])
def test_score_rises_with_each_part(part, lo, hi):
    assert _s(**{part: lo}) < _s(**{part: hi})


def test_one_failed_link_removes_the_support():
    assert _s(non_cancellable=0.0) == 0.0
    assert _s(reach_share=0.0) == 0.0


def test_score_is_capped_and_tenor_beyond_debt_adds_nothing():
    assert _s(coverage=3.0) == pytest.approx(_s(coverage=1.0))
    assert _s(contract_years=20.0) == pytest.approx(_s(contract_years=5.0))
    assert 0.0 <= _s() <= 1.0


def test_basel_grades():
    assert clocks.basel_tenor_grade(7.0, 5.0) == "strong"
    assert clocks.basel_tenor_grade(5.5, 5.0) == "good"
    assert clocks.basel_tenor_grade(4.6, 5.0) == "satisfactory"
    assert clocks.basel_tenor_grade(3.0, 5.0) == "weak"


def _cross_section(price_contents: bool, n=60, seed=0):
    rng = np.random.default_rng(seed)
    score = rng.uniform(0.05, 0.95, n)
    label = rng.uniform(size=n) < 0.5
    log_s = 6.0 - 0.6 * label + rng.normal(0, 0.1, n)
    if price_contents:
        log_s = log_s - 1.5 * score
    return pd.DataFrame({"spread": np.exp(log_s), "label": label, "support_score": score})


def test_label_test_tells_label_pricing_from_contents_pricing():
    assert clocks.label_test(_cross_section(False))["prices_label_only"]
    res = clocks.label_test(_cross_section(True))
    assert not res["prices_label_only"] and res["score_slope"] < 0 and res["r2_gain"] > 0.1


def test_label_gap_flags_both_errors():
    df = pd.DataFrame({"gvkey": ["weak_label", "strong_nolabel", "a", "b", "c", "d"],
                       "spread": [250.0, 900.0, 300.0, 350.0, 700.0, 800.0],
                       "label": [True, False, True, True, False, False],
                       "support_score": [0.05, 0.95, 0.7, 0.6, 0.3, 0.2]})
    out = clocks.label_gap(df).set_index("gvkey")
    assert out.loc["weak_label", "label_too_tight"] and out.loc["strong_nolabel", "unlabelled_too_wide"]
    assert out["label_too_tight"].sum() == 1 and out["unlabelled_too_wide"].sum() == 1


def test_fair_sort_has_no_flags():
    df = pd.DataFrame({"spread": [200.0, 400.0, 600.0, 800.0], "label": [True, True, False, False],
                       "support_score": [0.9, 0.7, 0.4, 0.1]})
    out = clocks.label_gap(df)
    assert out["gap"].abs().max() < 1e-12
    assert not out["label_too_tight"].any() and not out["unlabelled_too_wide"].any()


def test_next_catalyst_picks_the_first_event_ahead():
    ev = {"terms_filed": "2026-08-14", "lease_start": "2027-03-01", "maturity": "2030-06-01", "renewal": None}
    name, when, months = clocks.next_catalyst(ev, "2026-11-30")
    assert name == "lease_start" and when == pd.Timestamp("2027-03-01") and 2.9 < months < 3.1
    assert clocks.next_catalyst({"maturity": "2020-01-01"}, "2026-11-30")[0] == "none"
    assert math.isnan(clocks.next_catalyst({}, "2026-11-30")[2])


def test_support_frame_refuses_late_inputs():
    df = pd.DataFrame([{**BASE, "available_at": pd.Timestamp("2026-12-15")}])
    with pytest.raises(LookAheadError):
        clocks.support_frame(df, pd.Timestamp("2026-12-01"))
    ok = clocks.support_frame(df, pd.Timestamp("2026-12-31"))
    assert ok["support_score"].iloc[0] == pytest.approx(clocks.support_score(**BASE))
    assert ok["basel_grade"].iloc[0] == "good"
