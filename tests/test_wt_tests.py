"""Tests for scripts/wt_tests.py, the historical test of the Wolfe Trahan claims (decision 2026-10-24)."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import wt_tests as w  # noqa: E402


def _quarters(n, start="1990Q1"):
    return pd.period_range(start, periods=n, freq="Q")


def test_signal_z_uses_no_later_data():
    rng = np.random.default_rng(0)
    x = pd.Series(rng.normal(size=80).cumsum(), index=_quarters(80))
    z1 = w.signal_z(x)
    x2 = x.copy()
    x2.iloc[60:] += 50.0  # change the future only
    z2 = w.signal_z(x2)
    pd.testing.assert_series_equal(z1.iloc[:60], z2.iloc[:60])


def test_ltm_needs_four_consecutive_quarters():
    qs = ["2000Q1", "2000Q2", "2000Q3", "2001Q1", "2001Q2", "2001Q3", "2001Q4"]  # 2000Q4 missing
    fq = pd.DataFrame({
        "gvkey": "001", "datacqtr": qs, "datadate": pd.date_range("2000-03-31", periods=7, freq="QE"),
        "saleq": 100.0, "cogsq": 70.0, "oibdpq": 15.0, "dlttq": 50.0, "dlcq": 0.0, "gsector": "20",
    })
    p = w.firm_panel(fq)
    assert list(p["q"].astype(str)) == ["2001Q4"]  # first quarter with four consecutive quarters behind it
    assert p["saleq_ltm"].iloc[0] == pytest.approx(400.0)


def _synthetic_panel(n_firms=30, n_q=40, v_path=None):
    rows = []
    qs = _quarters(n_q)
    for f in range(n_firms):
        for i, q in enumerate(qs):
            v = 0.7 if v_path is None else v_path[i]
            rows.append({"gvkey": f"{f:03d}", "q": q, "gsector": "20", "saleq_ltm": 400.0 + f,
                         "cogsq_ltm": v * (400.0 + f), "oibdpq_ltm": 60.0, "debt": 200.0})
    return pd.DataFrame(rows)


def test_sector_outcomes_reads_the_matched_change():
    v = np.r_[np.full(20, 0.70), np.full(20, 0.75)]
    out = w.sector_outcomes(_synthetic_panel(v_path=v), "20")
    qs = out.index
    assert out.at[qs[18], "dv_k2"] == pytest.approx(0.05)  # q18 -> q20 crosses the step
    assert out.at[qs[10], "dv_k2"] == pytest.approx(0.0)
    assert out.at[qs[10], "dlev_k4"] == pytest.approx(0.0)


def test_regression_recovers_a_two_quarter_lead():
    rng = np.random.default_rng(1)
    n = 120
    z = pd.Series(rng.normal(size=n), index=_quarters(n))
    y = 0.5 * z + rng.normal(scale=0.5, size=n)  # y indexed at q is the outcome over q..q+k
    r = w.hac_regression(pd.Series(y, index=z.index), pd.DataFrame({"z": z}), lags=2)
    assert r["b"] == pytest.approx(0.5, abs=0.15)
    assert r["t"] > 4


def test_clark_west_rewards_a_real_predictor_and_not_noise():
    rng = np.random.default_rng(2)
    n = 120
    idx = _quarters(n)
    ctl = pd.DataFrame({"c": rng.normal(size=n)}, index=idx)
    z = pd.Series(rng.normal(size=n), index=idx, name="z")
    y_real = pd.Series(0.8 * z.to_numpy() + 0.3 * ctl["c"].to_numpy() + rng.normal(scale=0.5, size=n), index=idx)
    y_null = pd.Series(0.3 * ctl["c"].to_numpy() + rng.normal(scale=0.5, size=n), index=idx)
    X = pd.concat([z, ctl], axis=1)
    start = idx[60]
    real = w.clark_west(y_real, ctl, X, k=1, start=start)
    null = w.clark_west(y_null, ctl, X, k=1, start=start)
    assert real["cw_t"] > 3
    assert null["cw_t"] < 2


def test_clark_west_trains_only_on_known_outcomes():
    # The outcome at q is known only at q + k. If the race trained on rows up to q, it would see y_q itself.
    idx = _quarters(80)
    y = pd.Series(np.zeros(80), index=idx)
    y.iloc[-10:] = 100.0  # a jump no past row could predict
    X = pd.DataFrame({"z": np.arange(80.0), "c": np.ones(80)}, index=idx)
    r = w.clark_west(y, X[["c"]], X, k=4, start=idx[40])
    assert r["n"] > 0
    assert r["oos_r2"] < 0.5  # a leaking fit would track the jump and score near 1


def test_event_count_and_episodes():
    idx = _quarters(10)
    z = pd.Series([0, 2, 2, 0, 0, 3, 0, 0, 0, 0], index=idx, dtype=float)
    y = pd.Series([1, -1, -1, 1, 1, -1, 1, 1, 1, 1], index=idx, dtype=float)
    e = w.event_count(z, y, sign=-1)
    assert e["n_signal_quarters"] == 3
    assert e["n_episodes"] == 2
    assert e["hit_rate_signal"] == 1.0
    assert e["hit_rate_other"] == 0.0


def test_claim_leads_are_fixed_in_the_table():
    h1 = w.CLAIMS["H1"]
    assert h1["primary"] == {"dv_k2": +1, "dsg_k4": -1}
    assert {w.horizon(k) for k in h1["primary"]} == {2, 4}
    assert w.holm_threshold() == pytest.approx(0.05 / 8)
