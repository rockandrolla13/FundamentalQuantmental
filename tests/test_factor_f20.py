"""F20 tail dependence: contract, no look-ahead, tail sign, weekly and monthly paths, rating filter, short history,
gaps, missing panels and the formula helpers."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from scipy.stats import multivariate_t
from scipy.stats import t as student_t

from hy.backtest import decision_time
from hy.factors import f20_tail_dependence as f20

AS_OF = pd.Timestamp("2012-12-31")
DAY = pd.Timedelta(1, unit="D")
WEEKS = pd.date_range(end=AS_OF, periods=110, freq="W-FRI")   # last Friday 2012-12-28
MONTHS = pd.date_range(end=AS_OF, periods=64, freq="ME")
N = 24                     # issuers: 0 .. 11 tail-dependent, 12 .. 23 independent


def _paths(n_periods: int, seed: int = 0, n: int = N) -> np.ndarray:
    """Log spread changes, periods x issuers. Half load on a common t(3) shock, half are independent."""
    rng = np.random.default_rng(seed)
    common = student_t.rvs(3, size=n_periods, random_state=rng)
    own = student_t.rvs(3, size=(n_periods, n), random_state=rng)
    load = np.r_[np.full(n // 2, 1.0), np.zeros(n - n // 2)]
    return 0.02 * (common[:, None] * load + own * np.where(load > 0, 0.5, 1.0))


def _levels(dx: np.ndarray, s0: float = 0.05) -> np.ndarray:
    return s0 * np.exp(np.cumsum(np.vstack([np.zeros(dx.shape[1]), dx[1:]]), axis=0))


def _bond_panel(months=MONTHS, spreads: np.ndarray | None = None, n: int = N) -> pd.DataFrame:
    """Month-end rows. `spreads` (months x issuers) sets g_spread, else 5%. The price moves so no row is stale."""
    rows = []
    for i in range(n):
        s = spreads[:, i] if spreads is not None else np.full(len(months), 0.05)
        rows.append(pd.DataFrame({"date": months, "cusip": f"C{i}", "gvkey": f"G{i}", "years": 5.0, "g_spread": s,
                                  "price": 90.0 + np.arange(len(months)) * 0.01, "yield": 0.08, "mod_dur": 4.0,
                                  "n_trades": 5, "carried": False, "available_at": months + DAY}))
    return pd.concat(rows, ignore_index=True)


def _bond_daily(weeks=WEEKS, seed: int = 0, n: int = N) -> pd.DataFrame:
    """One trade per bond per Friday."""
    s = _levels(_paths(len(weeks), seed, n))
    rows = [pd.DataFrame({"cusip": f"C{i}", "date": weeks, "g_spread": s[:, i], "available_at": weeks + DAY})
            for i in range(n)]
    return pd.concat(rows, ignore_index=True)


def _ratings(n: int = N, over: dict | None = None) -> pd.DataFrame:
    return pd.DataFrame([{"gvkey": f"G{i}", "datadate": AS_OF - pd.Timedelta(30, unit="D"),
                          "splticrm": (over or {}).get(f"G{i}", "B"), "available_at": AS_OF - DAY} for i in range(n)])


def _weekly(**kw) -> dict:
    return {"bond_panel": _bond_panel(), "bond_daily": _bond_daily(**kw)}


def _run(panels, **kw) -> pd.DataFrame:
    return f20.compute(panels, AS_OF, **kw).set_index("gvkey")


# ---------------------------------------------------------------- 1. contract


def test_meta_and_columns():
    for k in ("rank", "name", "level", "horizon_months", "needs", "spec", "section"):
        assert k in f20.META
    assert f20.META["rank"] == 20 and f20.META["level"] == "issuer" and f20.META["horizon_months"] == 3
    out = f20.compute(_weekly(), AS_OF)
    assert list(out.columns) == f20.COLS
    assert out["gvkey"].is_unique and len(out) == N
    assert (out["date"] == AS_OF).all() and (out["available_at"] == decision_time(AS_OF)).all()
    assert (out["freq"] == "W").all() and (out["ctrl"] == "spread").all()
    assert (out["n_obs"] == f20.WINDOW["W"] - 1).all()       # the week of as_of (ends 2013-01-04) has no trade yet
    assert out["score"].notna().all() and abs(out["score"].mean()) < 1e-9
    assert out["utd"].between(0, 1).all() and out["nu"].between(*f20.NU_BOUNDS).all()


# ---------------------------------------------------------------- 2. no look-ahead


def test_later_rows_and_late_revisions_do_not_change_score():
    base = _weekly()
    ref = _run(base)
    d, p = base["bond_daily"], base["bond_panel"]
    later = pd.date_range(AS_OF + DAY, periods=8, freq="W-FRI")
    fut_d = pd.concat([d, pd.DataFrame({"cusip": "C0", "date": later, "g_spread": 5.0, "available_at": later + DAY})])
    late = d[d["date"] == WEEKS[-3]].assign(g_spread=9.0, available_at=AS_OF + 3 * DAY)   # revision known too late
    fut_p = pd.concat([p, p[p["date"] == AS_OF].assign(date=AS_OF + pd.offsets.MonthEnd(1), g_spread=0.5,
                                                       available_at=AS_OF + 40 * DAY)])
    out = _run({"bond_panel": fut_p, "bond_daily": pd.concat([fut_d, late], ignore_index=True)})
    pd.testing.assert_frame_equal(out, ref)


# ---------------------------------------------------------------- 3. sign


def test_tail_dependent_issuers_get_higher_utd_and_lower_score():
    out = _run(_weekly())
    dep, ind = out.loc[[f"G{i}" for i in range(12)]], out.loc[[f"G{i}" for i in range(12, N)]]
    assert dep["utd"].median() > ind["utd"].max()            # nu is weak at n = 103: one dependent fit may go Gaussian
    assert dep["rho"].min() > ind["rho"].max()
    assert dep["utd_emp"].mean() > ind["utd_emp"].mean()
    assert dep["score"].mean() < ind["score"].mean()


def test_monthly_fallback_without_bond_daily():
    s = _levels(_paths(len(MONTHS), seed=3))
    out = _run({"bond_panel": _bond_panel(spreads=s)})
    assert (out["freq"] == "M").all() and (out["n_obs"] == f20.WINDOW["M"]).all()
    assert out["utd"].notna().all()
    dep, ind = out.loc[[f"G{i}" for i in range(12)]], out.loc[[f"G{i}" for i in range(12, N)]]
    assert dep["rho"].mean() > ind["rho"].mean() + 0.2


# ---------------------------------------------------------------- 4. edge cases


def test_missing_panels():
    assert list(f20.compute({}, AS_OF).columns) == f20.COLS and f20.compute({}, AS_OF).empty
    out = f20.compute({"bond_panel": _bond_panel()}, AS_OF, freq="W")
    assert out.empty and list(out.columns) == f20.COLS


def test_short_history_gives_nan():
    panels = {"bond_panel": _bond_panel(), "bond_daily": _bond_daily(weeks=WEEKS[-40:])}
    out = _run(panels)
    assert out["utd"].isna().all() and out["score"].isna().all() and (out["n_obs"] == 39).all()
    assert _run(panels, min_obs=30)["utd"].notna().all()


def test_ratings_filter_and_control():
    panels = _weekly()
    panels["ratings"] = _ratings(over={"G0": "D", "G1": "BBB", "G2": "BB"})
    out = _run(panels)
    assert {"G0", "G1"}.isdisjoint(out.index) and len(out) == N - 2
    assert (out["ctrl"] == "rating+spread").all() and out.loc["G2", "rclass"] == "BB"


def test_carried_rows_and_gaps_give_no_change():
    s = _levels(_paths(len(MONTHS), seed=3))
    p = _bond_panel(spreads=s)
    p.loc[(p["cusip"] == "C0") & p["date"].isin(MONTHS[-10:-7]), "carried"] = True
    out = _run({"bond_panel": p})
    assert out.loc["G0", "n_obs"] == f20.WINDOW["M"] - 4      # 3 carried months break 4 changes
    rows = pd.DataFrame({"cusip": "A", "gvkey": "G", "date": MONTHS[[0, 1, 3, 4]], "g_spread": [1.0, 2.0, 4.0, 2.0]})
    ch = f20.log_changes(rows, "M")
    assert len(ch) == 2 and np.allclose(ch["dls"], [np.log(2.0), np.log(0.5)])


# ---------------------------------------------------------------- 5. formula helpers


def test_t_tail_dependence_hand_values():
    # 2 t_5(-sqrt(5 * 0.5 / 1.5)) and 2 t_11(-sqrt(11 * 0.5 / 1.5))
    assert f20.t_tail_dependence(0.5, 4.0) == pytest.approx(2 * student_t.cdf(-np.sqrt(5 / 3), 5), abs=1e-12)
    assert f20.t_tail_dependence(0.5, 4.0) == pytest.approx(0.2532, abs=1e-4)
    assert f20.t_tail_dependence(0.5, 10.0) == pytest.approx(0.0819, abs=1e-4)
    assert f20.t_tail_dependence(0.0, 1e6) < 1e-6
    assert np.all(np.diff(f20.t_tail_dependence(np.array([0.1, 0.5, 0.9]), 4.0)) > 0)


def test_t_copula_loglik_against_scipy_density():
    u1, u2, rho, nu = np.array([0.2, 0.9]), np.array([0.3, 0.7]), 0.4, 5.0
    x1, x2 = student_t.ppf(u1, nu), student_t.ppf(u2, nu)
    f2 = multivariate_t(loc=[0, 0], shape=[[1, rho], [rho, 1]], df=nu).logpdf(np.c_[x1, x2])
    hand = np.sum(f2 - student_t.logpdf(x1, nu) - student_t.logpdf(x2, nu))
    assert f20.t_copula_loglik(u1, u2, rho, nu) == pytest.approx(hand, rel=1e-10)
    assert f20.t_copula_loglik(u1, u2, 0.0, 1e7) == pytest.approx(0.0, abs=1e-5)


def test_fit_t_copula_recovers_parameters():
    rng = np.random.default_rng(7)
    rho, nu = 0.6, 4.0
    x = multivariate_t(loc=[0, 0], shape=[[1, rho], [rho, 1]], df=nu).rvs(3000, random_state=rng)
    r_hat, nu_hat = f20.fit_t_copula(f20.pseudo_obs(x[:, 0]), f20.pseudo_obs(x[:, 1]))
    assert r_hat == pytest.approx(rho, abs=0.05) and 2.5 < nu_hat < 7.0


def test_pseudo_obs_and_empirical_tail():
    assert np.allclose(f20.pseudo_obs([3.0, 1.0, 2.0]), [0.75, 0.25, 0.5])
    u = np.arange(1, 17) / 17.0
    assert f20.empirical_upper_tail(u, u) == 1.0 and f20.empirical_upper_tail(u, u[::-1]) == 0.0
    assert np.isnan(f20.empirical_upper_tail(u[:3], u[:3]))


def test_market_changes_leave_one_out():
    X = pd.DataFrame({"a": [1.0, 1.0], "b": [2.0, np.nan], "c": [3.0, 5.0]})
    m = f20.market_changes(X, min_n=1)
    assert np.allclose(m.iloc[0], [2.5, 2.0, 1.5])
    assert np.allclose(m.iloc[1], [5.0, 3.0, 1.0])
    m2 = f20.market_changes(X, min_n=2).iloc[1]                # a and c see one other issuer, b sees two
    assert m2[["a", "c"]].isna().all() and m2["b"] == 3.0


def test_ar1_residual_and_ewma_hand_values():
    # x = 1..4: mu 2.5, xc = [-1.5, -0.5, 0.5, 1.5], phi = 1.25 / 2.75
    phi = 1.25 / 2.75
    e = f20.ar1_residual(np.array([1.0, 2.0, 3.0, 4.0]))
    assert np.allclose(e, [-1.5, -0.5 + 1.5 * phi, 0.5 + 0.5 * phi, 1.5 - 0.5 * phi])
    # e = [2, 0, 2]: s2 = 8/3, then 0.94 * 8/3 + 0.06 * 4, then 0.94 * that
    s0 = 8 / 3
    s1 = 0.94 * s0 + 0.06 * 4
    z = f20.ewma_standardise(np.array([2.0, 0.0, 2.0]))
    assert np.allclose(z, [2 / np.sqrt(s0), 0.0, 2 / np.sqrt(0.94 * s1)])
    assert np.isnan(f20.ewma_standardise(np.array([np.nan, 1.0]))[0])


def test_control_residual_removes_spread_level():
    idx = [f"G{i}" for i in range(30)]
    log_s = pd.Series(np.linspace(-4, -2, 30), index=idx)
    y = 0.1 + 0.05 * log_s
    r = f20.control_residual(y, pd.Series(None, index=idx, dtype=object), log_s)
    assert np.allclose(r, 0.0, atol=1e-12)
    few = f20.control_residual(y.iloc[:5], pd.Series(None, index=idx[:5], dtype=object), log_s.iloc[:5])
    assert np.allclose(few, y.iloc[:5] - y.iloc[:5].mean())
