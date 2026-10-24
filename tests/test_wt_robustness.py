"""Tests for scripts/wt_robustness.py, the stress tests of the Wolfe Trahan firm-level results (decision 2026-10-24)."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import statsmodels.api as sm

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import wt_robustness as r  # noqa: E402
import wt_tests as w  # noqa: E402


def _ar1(n, rho, rng):
    e = rng.standard_normal(n)
    x = np.empty(n)
    x[0] = e[0]
    for i in range(1, n):
        x[i] = rho * x[i - 1] + e[i]
    return x


def _synthetic(beta=0.5, n=136, seed=0):
    rng = np.random.default_rng(seed)
    idx = pd.period_range("1992Q1", periods=n, freq="Q")
    z = pd.Series(_ar1(n, 0.7, rng), index=idx)
    ctr = pd.DataFrame({"c1": _ar1(n, 0.5, rng), "c2": rng.standard_normal(n)}, index=idx)
    y = pd.Series(beta * z.to_numpy() + 0.3 * ctr["c1"].to_numpy() + rng.standard_normal(n), index=idx)
    return z, ctr, y


@pytest.mark.parametrize("beta", [0.0, 0.5])
def test_fast_clark_west_reproduces_the_study(beta):
    z, ctr, y = _synthetic(beta)
    k = 2
    d = r.design(z, ctr, y, k)
    X = d.drop(columns="y")
    slow = w.clark_west(d["y"], X.drop(columns="z"), X, k)
    fast = r.CWRace(d, k).run(d["z"].to_numpy())
    assert fast["n"] == slow["n"]
    assert fast["cw_t"] == pytest.approx(slow["cw_t"], rel=1e-8)
    assert fast["oos_r2"] == pytest.approx(slow["oos_r2"], rel=1e-8)


@pytest.mark.parametrize("beta,outcome", [(0.0, "dv_k2"), (0.6, "dv_k2"), (0.6, "debitda_k4")])
def test_evaluate_reproduces_run_outcome(beta, outcome):
    z, ctr, y = _synthetic(beta)
    ref = w.run_outcome(z, ctr, y, outcome, +1)
    got = r.evaluate(z, ctr, y, outcome, +1)
    assert got["hold_t"] == pytest.approx(ref["regression"]["holdout"]["t"], rel=1e-8)
    assert got["cw_p"] == pytest.approx(ref["clark_west"]["p"], rel=1e-8, abs=1e-12)
    assert got["cycles"] == pytest.approx(ref["cycles"])
    assert got["pass"] == ref["pass"]


def test_leave_one_window_out_removes_its_quarters_only():
    z, ctr, y = _synthetic(0.6)
    full = r.evaluate(z, ctr, y, "dv_k2", +1)
    for c, (a, b) in w.CYCLE_WINDOWS.items():
        e = r.evaluate(z, ctr, y, "dv_k2", +1, drop_window=c)
        n_in = sum(pd.Period(a, "Q") <= q <= pd.Period(b, "Q") for q in r.design(z, ctr, y, 2).index)
        assert e["n"] == full["n"] - n_in
        assert np.isnan(e["cycles"][c])


def test_circular_shifts_keep_a_minimum_distance():
    s = r.circular_shifts(40, 8)
    assert min(s) == 8 and max(s) == 32 and len(s) == 25


def test_stationary_bootstrap_blocks_have_the_mean_length():
    rng = np.random.default_rng(r.SEED)
    idx = np.concatenate([r.stationary_bootstrap_index(500, 8, rng) for _ in range(40)])
    assert idx.min() >= 0 and idx.max() < 500
    one = r.stationary_bootstrap_index(5000, 8, np.random.default_rng(1))
    breaks = np.mean(np.diff(one) % 5000 != 1)
    assert 1 / breaks == pytest.approx(8, rel=0.15)


def test_empirical_p_counts_the_real_draw():
    assert r.empirical_p(3.0, np.array([1.0, 2.0, 4.0, np.nan])) == pytest.approx(2 / 4)
    assert r.empirical_p(9.0, np.zeros(99)) == pytest.approx(0.01)


def test_placebo_puts_a_strong_signal_in_the_tail():
    z, ctr, y = _synthetic(1.0, seed=3)
    p = r.placebo(z, ctr, y, "dv_k2", +1, draws=60)
    assert p["circular"]["p_cw"] < 0.05 and p["bootstrap"]["p_cw"] < 0.05
    assert p["bootstrap"]["p_hold_t"] < 0.05


def _lrv_bartlett(v, S):
    T = len(v)
    om = v.T @ v / T
    for j in range(1, S):
        g = v[j:].T @ v[:-j] / T
        om += (1 - j / S) * (g + g.T)
    return om


def test_har_sandwich_and_nw_cov_match_statsmodels():
    z, ctr, y = _synthetic(0.4)
    d = r.design(z, ctr, y, 2)
    yy, X, names = r.holdout_ols(d)
    res = sm.OLS(yy, X).fit(cov_type="HAC", cov_kwds={"maxlags": 2})
    j = names.index("z")
    assert r.har_t(yy, X, j, lambda v: _lrv_bartlett(v, 3)) == pytest.approx(res.tvalues[j], rel=1e-8)
    b = np.linalg.lstsq(X, yy, rcond=None)[0]
    assert np.sqrt(np.diag(r.nw_cov(X, yy - X @ b, 2))) == pytest.approx(res.bse, rel=1e-8)


def test_ewc_nu_rounds_down_as_llsw():
    assert r.ewc_nu(54) == 5  # 0.4 * 54^(2/3) = 5.71; LLSW footnote 3 rounds nu down
    assert r.ewc_nu(200) == 13
    assert r.holm_cv_one_sided(6) == pytest.approx(3.52, abs=0.005)  # the memo's bar uses nu = 6
    assert r.holm_cv_one_sided(5) == pytest.approx(3.81, abs=0.005)


@pytest.mark.parametrize("beta,outcome", [(0.0, "dv_k2"), (0.6, "dv_k2"), (0.6, "debitda_k4")])
def test_fast_test_reproduces_run_outcome(beta, outcome):
    z, ctr, y = _synthetic(beta)
    ref = w.run_outcome(z, ctr, y, outcome, +1)
    ft = r.FastTest(y, y.index, w.horizon(outcome), +1)
    got = ft.run(z.reindex(y.index).to_numpy(), ctr.reindex(y.index).to_numpy())
    assert got["hold_t"] == pytest.approx(ref["regression"]["holdout"]["t"], rel=1e-6)
    assert got["cw_t"] == pytest.approx(ref["clark_west"]["cw_t"], rel=1e-6)
    assert got["cycles"] == pytest.approx(ref["cycles"])
    assert got["pass"] == ref["pass"]


def test_romano_wolf_is_monotone_and_controls_the_max():
    rng = np.random.default_rng(r.SEED)
    null = rng.standard_normal((999, 5))
    t_obs = np.array([5.0, 0.1, 2.9, -1.0, np.nan])
    p = r.romano_wolf(t_obs, null)
    assert p[0] == pytest.approx(1 / 1000)
    order = np.argsort(-np.nan_to_num(t_obs, nan=-np.inf))
    assert np.all(np.diff(p[order]) >= 0)
    single = r.empirical_p(2.9, null[:, 2])
    assert p[2] >= single  # stepdown is never below the single-test p


def test_fdr_q_values_order_bh_below_by():
    p = np.array([0.001, 0.01, 0.03, 0.2, np.nan])
    bh, by = r.fdr_q(p, "fdr_bh"), r.fdr_q(p, "fdr_by")
    assert np.isnan(bh[-1]) and np.all(bh[:4] <= by[:4])
    assert bh[0] == pytest.approx(0.004)


def test_macro_frame_moves_whole_rows():
    idx = pd.period_range("1980Q1", periods=80, freq="Q")
    rng = np.random.default_rng(0)
    macro = pd.DataFrame(rng.standard_normal((80, 1)) + 0, index=idx, columns=["PPC"])
    for c in set(w.CONTROL_COLS) | {n for n, _ in (s["signal"] for s in w.CLAIMS.values())}:
        macro[c] = rng.standard_normal(80).cumsum()
    M = r.macro_frame(macro, idx[20:])
    assert {"PPC|change2", "PPC|level", "gac", "dbaa", "sloos"} <= set(M.columns)
    A = M.to_numpy()
    ix = np.roll(np.arange(len(A)), 9)
    assert np.allclose(A[ix][0], A[ix[0]], equal_nan=True)  # one draw index moves every column together


def test_ewc_size_is_near_nominal_under_persistent_errors():
    """Few quarters, persistent regressor and errors: EWC with t_nu holds size; NW with lag 2 over-rejects."""
    rng = np.random.default_rng(r.SEED)
    T, rej_ewc, rej_nw = 56, 0, 0
    nu = r.ewc_nu(T)
    cv = r.t_dist.ppf(0.975, nu)
    for _ in range(400):
        x, u = _ar1(T, 0.7, rng), _ar1(T, 0.7, rng)
        X = np.column_stack([np.ones(T), x])
        rej_ewc += abs(r.har_t(u, X, 1, lambda v: r.lrv_ewc(v, nu))) > cv
        rej_nw += abs(r.har_t(u, X, 1, lambda v: _lrv_bartlett(v, 3))) > 1.96
    assert rej_ewc / 400 < 0.10
    assert rej_nw / 400 > rej_ewc / 400


def test_historical_members_respect_dates_and_fall_back_to_current():
    q = pd.period_range("2000Q1", "2001Q4", freq="Q")
    firms = pd.Index(["A", "B", "C"])
    info = pd.DataFrame({"gsector": ["20", "20", "45"]}, index=firms)
    gh = pd.DataFrame({"gvkey": ["A", "A", "B"], "gsector": ["45", "20", "20"],
                       "indfrom": pd.to_datetime(["1999-06-30", "2000-09-15", "2001-01-01"]),
                       "indthru": pd.to_datetime(["2000-09-14", None, None]),
                       "available_at": pd.to_datetime(["1999-06-30", "2000-09-15", "2001-01-01"])})
    mem, cov = r.historical_members(gh, q, firms, info, ["20"])
    assert not mem.at["A", pd.Period("2000Q2", "Q")]  # history says 45 at that date
    assert mem.at["A", pd.Period("2000Q3", "Q")]  # the move dated 2000-09-15 is known by 2000-09-30
    assert mem.at["B", pd.Period("2000Q1", "Q")] and not cov.at["B", pd.Period("2000Q1", "Q")]  # current fills
    assert not mem.loc["C"].any()


def test_sales_weighted_mean():
    Y = pd.DataFrame(np.arange(1.0, 25.0).reshape(24, 1).repeat(2, 1), columns=pd.period_range("2000Q1", periods=2, freq="Q"))
    S = Y * 0 + np.arange(1.0, 25.0)[:, None]
    rows = pd.Series(True, index=Y.index)
    got = r.group_series(Y, rows, weights=S)
    v = np.arange(1.0, 25.0)
    assert got.iloc[0] == pytest.approx((v * v).sum() / v.sum())
    assert r.group_series(Y, rows).iloc[0] == pytest.approx(v.mean())


def test_patched_restores_the_study_constants():
    w0, d0 = w._winsor, w.DECLINE
    with r.patched(w, DECLINE=0.3, _winsor=lambda x: x):
        assert w.DECLINE == 0.3
    assert w._winsor is w0 and w.DECLINE == d0


def test_claimed_signs_come_from_the_study():
    for _, claim, _, group, outcome in r.RESULTS:
        assert r.claimed_sign(claim, group, outcome) in (-1, +1)
    assert r.claimed_sign("H2", "Consumer Discretionary", "debitda_k4") == -1
