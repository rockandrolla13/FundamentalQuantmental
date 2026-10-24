"""Tests for scripts/wt_tests.py, the firm-level historical test of the Wolfe Trahan claims (decision 2026-10-24)."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import wt_tests as w  # noqa: E402


def _quarters(n, start="1990Q1"):
    return pd.period_range(start, periods=n, freq="Q")


def test_signals_use_no_later_data():
    rng = np.random.default_rng(0)
    x = pd.Series(rng.normal(size=80).cumsum(), index=_quarters(80))
    x2 = x.copy()
    x2.iloc[60:] += 50.0  # change the future only
    for f in (w.signal_z, w.level_z):
        pd.testing.assert_series_equal(f(x).iloc[:60], f(x2).iloc[:60])


def test_release_lag_moves_a_month_to_its_publication_month(tmp_path):
    p = tmp_path / "X.csv"
    pd.DataFrame({"DATE": ["2020-01-01", "2020-02-01", "2020-03-01"], "X": [1.0, 2.0, 3.0]}).to_csv(p, index=False)
    s = w.load_fred_monthly(p, lag_months=1)
    assert str(s.index[0]) == "2020-02"  # January's value is published in February
    q = w.to_quarter(s)
    assert len(q) == 0  # 2020Q1 now has only two published months, so no complete quarter


def _fq(n_firms=30, n_q=24, cogs=None, sector="20"):
    rows = []
    for f in range(n_firms):
        for i, q in enumerate(_quarters(n_q, "2000Q1")):
            rows.append({"gvkey": f"{f:03d}", "datacqtr": str(q), "datadate": q.end_time.normalize(),
                         "saleq": 100.0, "cogsq": 70.0 if cogs is None else cogs[i], "oibdpq": 15.0,
                         "dlttq": 50.0, "dlcq": 0.0, "gsector": sector, "gind": "201010", "gsubind": "20101010"})
    return pd.DataFrame(rows)


def test_ltm_needs_four_consecutive_quarters():
    fq = _fq(n_firms=1, n_q=8)
    fq = fq[fq["datacqtr"] != "2000Q4"]  # a gap
    W, _ = w.firm_matrices(fq)
    s = W["S"].iloc[0]
    assert s[pd.Period("2001Q2", "Q")] != s[pd.Period("2001Q2", "Q")]  # NaN: the window still holds the gap
    assert s[pd.Period("2001Q4", "Q")] == pytest.approx(400.0)


def test_firm_outcomes_read_the_change_after_q():
    cogs = [70.0] * 12 + [80.0] * 12  # cost ratio steps from 0.70 to 0.80 in 2003Q1
    W, info = w.firm_matrices(_fq(cogs=cogs))
    out = w.firm_outcomes(W)
    q = pd.Period("2002Q2", "Q")  # LTM at q+2 = 2002Q4 holds no new quarter yet; at q+4 = 2003Q2 it holds two
    dv = out["dv_k2"][q]
    assert dv.mean() == pytest.approx(0.0)
    dv_later = out["dv_k2"][pd.Period("2002Q4", "Q")]  # LTM 2003Q2 has two quarters at 0.80
    assert dv_later.mean() == pytest.approx(0.05)
    assert out["decline_k4"][q].mean() == pytest.approx(0.0)


def test_group_mean_needs_enough_firms():
    Y = pd.DataFrame(np.ones((10, 3)), index=[f"{i}" for i in range(10)], columns=_quarters(3))
    rows = pd.Series(True, index=Y.index)
    assert w.group_mean(Y, rows).isna().all()  # 10 firms < MIN_FIRMS


def test_regression_recovers_a_lead():
    rng = np.random.default_rng(1)
    n = 120
    z = pd.Series(rng.normal(size=n), index=_quarters(n))
    y = pd.Series(0.5 * z.to_numpy() + rng.normal(scale=0.5, size=n), index=z.index)
    r = w.hac_regression(y, pd.DataFrame({"z": z}), lags=2)
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
    assert w.clark_west(y_real, ctl, X, k=1, start=idx[60])["cw_t"] > 3
    assert w.clark_west(y_null, ctl, X, k=1, start=idx[60])["cw_t"] < 2


def test_clark_west_trains_only_on_known_outcomes():
    idx = _quarters(80)
    y = pd.Series(np.zeros(80), index=idx)
    y.iloc[-10:] = 100.0  # a jump no past row could predict
    X = pd.DataFrame({"z": np.arange(80.0), "c": np.ones(80)}, index=idx)
    r = w.clark_west(y, X[["c"]], X, k=4, start=idx[40])
    assert r["oos_r2"] < 0.5  # a leaking fit would track the jump and score near 1


def test_event_count_and_episodes():
    idx = _quarters(10)
    z = pd.Series([0, 2, 2, 0, 0, 3, 0, 0, 0, 0], index=idx, dtype=float)
    y = pd.Series([1, -1, -1, 1, 1, -1, 1, 1, 1, 1], index=idx, dtype=float)
    e = w.event_count(z, y, sign=-1)
    assert (e["n_signal_quarters"], e["n_episodes"], e["hit_rate_signal"], e["hit_rate_other"]) == (3, 2, 1.0, 0.0)


def _exposure_panel(persistent: bool, n_firms=400, n_q=100, seed=3):
    rng = np.random.default_rng(seed)
    idx = _quarters(n_q)
    z = pd.Series(rng.normal(size=n_q), index=idx)
    beta = rng.normal(size=n_firms)
    Y = np.empty((n_firms, n_q))
    for t in range(n_q):
        b_t = beta if persistent else rng.normal(size=n_firms)  # non-persistent: a fresh exposure each quarter
        Y[:, t] = b_t * z.iloc[t] + rng.normal(scale=1.0, size=n_firms)
    return pd.DataFrame(Y, index=[f"{i}" for i in range(n_firms)], columns=idx), z


def test_past_betas_use_no_later_data():
    Y, z = _exposure_panel(True, n_firms=50, n_q=60)
    B1 = w.past_betas(Y, z, k=2)
    Y2 = Y.copy()
    Y2.iloc[:, 40:] += 99.0
    B2 = w.past_betas(Y2, z, k=2)
    pd.testing.assert_frame_equal(B1.iloc[:, :42], B2.iloc[:, :42])  # b at q uses data through q - 2


def test_fama_macbeth_finds_persistent_exposure_and_not_noise():
    Y, z = _exposure_panel(True)
    assert w.fama_macbeth(Y, z, k=1)["full"]["t"] > 5
    Y0, z0 = _exposure_panel(False)
    assert abs(w.fama_macbeth(Y0, z0, k=1)["full"]["t"]) < 3


def test_claim_leads_are_fixed_in_the_table():
    h1 = w.CLAIMS["H1"]
    assert {(o, s) for _, o, s in h1["tests"]} == {("dv_k2", +1), ("dsg_k4", -1)}
    assert {w.horizon(o) for _, o, _ in h1["tests"]} == {2, 4}
    assert w.holm_threshold() == pytest.approx(0.05 / 8)
