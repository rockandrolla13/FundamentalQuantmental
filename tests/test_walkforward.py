"""Tests for the quarterly walk-forward plumbing (hy.walkforward): decision dates, no look-ahead, realised return,
scoring, and the 8-K event labels."""

import numpy as np
import pandas as pd
import pytest

from hy import walkforward as wf


def test_decision_dates_need_three_months_of_outcome():
    d = wf.decision_dates("2024-03-31", "2026-09-17", min_months=3)
    # 2026-06-30 + 3 months = 2026-09-30 is after the last TRACE date, so the last decision is 2026-03-31.
    assert d[0] == pd.Timestamp("2024-03-31") and d[-1] == pd.Timestamp("2026-03-31") and len(d) == 9
    assert all(x.is_quarter_end for x in d)
    assert wf.decision_dates("2024-03-31", "2026-06-29", 3)[-1] == pd.Timestamp("2025-12-31")


def test_decision_time_is_the_next_day():
    assert wf.decision_time(pd.Timestamp("2024-03-31")) == pd.Timestamp("2024-04-01")


def test_assert_pit_refuses_a_late_input_and_accepts_on_time():
    dec = pd.Timestamp("2024-04-01")
    wf.assert_pit([pd.Timestamp("2024-03-31"), None, pd.NaT, "2024-04-01"], dec, "ok")
    with pytest.raises(wf.LookAheadError):
        wf.assert_pit(["2024-03-31", "2024-04-02"], dec, "filing acceptance")


def test_end_quote_reads_only_the_outcome_window():
    q = pd.DataFrame({"cusip": ["A"] * 4,
                      "trade_date": pd.to_datetime(["2024-03-28", "2024-05-10", "2024-06-25", "2024-07-15"]),
                      "price_vw": [90.0, 95.0, 97.0, 120.0], "yield_vw": [0.1, 0.09, 0.085, 0.05]})
    r = wf.end_quote(q, "A", pd.Timestamp("2024-03-31"), pd.Timestamp("2024-06-30"))
    assert r["price"] == 97.0 and not r["early"]  # not the pre-t trade, not the post-end trade
    early = wf.end_quote(q, "A", pd.Timestamp("2024-03-31"), pd.Timestamp("2024-06-20"))
    assert early["price"] == 95.0 and early["early"]
    assert wf.end_quote(q, "A", pd.Timestamp("2024-07-20"), pd.Timestamp("2024-09-30")) is None


def test_bond_realised_hand_calculation():
    # Price 100 -> 101, 6% coupon over 0.25y; Treasury 4% flat; spread 3% vs market 4%, both flat; DTS beta 0.75.
    r = wf.bond_realised(100, 101, 0.06, 0.25, 0.04, 0.04, 4.0, 0.03, 0.04, 0.04, beta=0.75, cost=0.002)
    assert r["total"] == pytest.approx((1 + 1.5) / 100)
    assert r["tsy"] == pytest.approx(0.01)
    assert r["bench"] == pytest.approx(0.75 * 0.04 * 0.25)
    assert r["net"] == pytest.approx(r["realised"] - 0.002)


def test_bond_realised_no_accrual_when_trading_flat():
    r = wf.bond_realised(40, 42, 0.06, 0.5, 0.04, 0.04, 3.0, 0.2, 0.04, 0.04, beta=1.0, cost=0.0)
    assert r["total"] == pytest.approx(2 / 40)


def test_score_perfect_and_reversed_predictors():
    rng = np.random.default_rng(1)
    rows = []
    for d in pd.date_range("2024-03-31", periods=6, freq="QE"):
        x = rng.normal(size=8)
        rows += [{"date": d, "p": v, "r": 2 * v, "q": -v} for v in x]
    df = pd.DataFrame(rows)
    s = wf.score(df, "p", "r")
    assert s["ic_mean"] == pytest.approx(1.0) and s["hit_rate"] == 1.0 and s["slope"] == pytest.approx(2.0)
    assert wf.score(df, "q", "r")["ic_mean"] == pytest.approx(-1.0)


def test_rank_ic_skips_thin_dates():
    df = pd.DataFrame({"date": ["a"] * 3, "p": [1, 2, 3], "r": [1, 2, 3]})
    assert wf.rank_ic_by_date(df, "p", "r").empty


def test_gate_outcomes_counts_right_calls():
    df = pd.DataFrame({"call": ["Watch", "Watch", "Pass"], "dir": ["cheap", "cheap", "rich"], "r": [50.0, -10.0, -5.0]})
    g = wf.gate_outcomes(df, "call", "dir", "r").set_index(["call", "dir"])
    assert g.loc[("Watch", "cheap"), "right_share"] == pytest.approx(0.5)
    assert g.loc[("Pass", "rich"), "right_share"] == 1.0


def test_events_from_8k_labels_credit_items_only():
    rows = [("2025-10-31", "1.01,1.03,2.04,7.01"), ("2025-07-30", "2.02,9.01"), ("2024-12-11", "1.01,2.03,3.02")]
    ev = wf.events_from_8k(rows, "2024-01-01", "2026-09-17")
    labels = dict((d.strftime("%Y-%m-%d"), x) for d, x in ev)
    assert "bankruptcy filing" in labels["2025-10-31"] and "debt acceleration" in labels["2025-10-31"]
    assert labels["2024-12-11"] == "new debt agreement" and "2025-07-30" not in labels


def test_numeric_or_nan_keeps_numbers_and_drops_text():
    # Step 4 quotes the runway as a number or as "no shortfall in 8 quarters"; a mixed column cannot be saved.
    assert wf.numeric_or_nan(6.5) == 6.5
    assert wf.numeric_or_nan(3) == 3.0
    for x in ("no shortfall in 8 quarters", None, float("nan")):
        assert wf.numeric_or_nan(x) != wf.numeric_or_nan(x)  # NaN
