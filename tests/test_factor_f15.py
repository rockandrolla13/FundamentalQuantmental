"""Tests for F15 PCA residual reversal with an OU s-score (docs/factors/F15-pca-ou-reversal.md)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from hy.factors import f15_pca_ou_reversal as f15

AS_OF = pd.Timestamp("2015-12-31")
N_MONTHS = 48


# ---------------------------------------------------------------- synthetic fixture


def residual_paths(n: int, months: int, rng, b: float = 0.3, scale: float = 0.01) -> np.ndarray:
    """Residual returns eps = diff(X) of a mean-reverting level X (AR(1) with slope b)."""
    x = np.zeros((months + 1, n))
    for k in range(1, months + 1):
        x[k] = b * x[k - 1] + scale * rng.standard_normal(n)
    return np.diff(x, axis=0)


def returns_matrix(n_bonds: int = 60, seed: int = 0, shock: dict[int, float] | None = None,
                   months: int = N_MONTHS, shock_month: int = -2) -> np.ndarray:
    """months x bonds: two common factors plus a mean-reverting residual. `shock` adds a return to bond j in the
    month `shock_month` (-2 is t - 1, the last month the skip-1 window reads)."""
    rng = np.random.default_rng(seed)
    f = 0.02 * rng.standard_normal((months, 2))
    beta = np.column_stack([rng.uniform(0.5, 1.5, n_bonds), rng.uniform(-1.0, 1.0, n_bonds)])
    r = f @ beta.T + residual_paths(n_bonds, months, rng)
    for j, v in (shock or {}).items():
        r[shock_month, j] += v
    return r


def bond_panel(r: np.ndarray, as_of: pd.Timestamp = AS_OF, issuers: list[str] | None = None) -> pd.DataFrame:
    """bond_panel rows whose month excess return (zero coupon, zero Treasury yield) equals r exactly."""
    months, n = r.shape
    dates = pd.date_range(end=as_of, periods=months + 1, freq="ME")
    price = 100.0 * np.vstack([np.ones(n), np.cumprod(1.0 + r, axis=0)])
    rows = []
    for j in range(n):
        g = issuers[j] if issuers else f"G{j:03d}"
        for k, d in enumerate(dates):
            rows.append({"date": d, "cusip": f"C{j:03d}", "gvkey": g, "years": 5.0, "price": price[k, j],
                         "coupon": 0.0, "yield": 0.08, "g_spread": 0.05, "tsy_yield": 0.0, "mod_dur": 4.0,
                         "carried": False, "n_trades": 10, "accrue_to": d, "hedge_date": d, "bid_ask_pts": 0.5,
                         "available_at": d + pd.Timedelta(1, unit="D")})
    return pd.DataFrame(rows)


def daily_panel(n_bonds: int = 40, days: int = 320, seed: int = 1, as_of: pd.Timestamp = AS_OF) -> pd.DataFrame:
    """bond_daily rows: g_spread = 5% + a common level + a mean-reverting residual level, every business day."""
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range(end=as_of, periods=days)
    common = np.cumsum(0.0005 * rng.standard_normal(days))
    level = np.cumsum(np.vstack([np.zeros(n_bonds), residual_paths(n_bonds, days - 1, rng, 0.5, 0.0005)]), axis=0)
    s = 0.05 + np.outer(common, rng.uniform(0.5, 1.5, n_bonds)) + level
    rows = [{"cusip": f"C{j:03d}", "date": d, "g_spread": s[k, j], "available_at": d + pd.Timedelta(1, unit="D")}
            for j in range(n_bonds) for k, d in enumerate(dates)]
    return pd.DataFrame(rows)


def shocked(seed: int, n_bonds: int = 120, c: float = 0.04) -> np.ndarray:
    """Bonds 0-2: residual jumps up early in the T' window and falls back at t - 1 (now below equilibrium, cheap).
    Bonds 3-5: the mirror (rich). Start months differ so the shocks stay idiosyncratic, not a PC."""
    r = returns_matrix(n_bonds, seed)
    for j, m in zip(range(3), (-13, -12, -11)):
        r[m, j] += c
        r[-2, j] -= c
    for j, m in zip(range(3, 6), (-13, -12, -11)):
        r[m, j] -= c
        r[-2, j] += c
    return r


@pytest.fixture(scope="module")
def base():
    r = returns_matrix(60, 0)
    return r, bond_panel(r)


# ---------------------------------------------------------------- contract


def test_meta_keys():
    for k in ("rank", "name", "level", "horizon_months", "needs", "spec", "section"):
        assert k in f15.META
    assert f15.META["rank"] == 15 and f15.META["level"] == "bond"
    assert f15.META["spec"] == "docs/factors/F15-pca-ou-reversal.md"


def test_columns_and_one_row_per_bond(base):
    _, panel = base
    out = f15.compute({"bond_panel": panel}, AS_OF)
    assert list(out.columns) == f15.COLS
    assert out["cusip"].is_unique and len(out) == 60
    assert (out["date"] == AS_OF).all()
    assert (out["available_at"] == AS_OF + pd.Timedelta(1, unit="D")).all()
    assert out["score"].notna().sum() > 30
    assert set(out["status"]) <= {"ok", "no_reversion", "slow", "no_history"}
    assert out.loc[out["status"] != "ok", "score"].isna().all()
    assert out["score"].abs().max() <= f15.WINSOR
    assert (out["n_pcs"] == f15.N_PCS).all()


# ---------------------------------------------------------------- no look-ahead


def test_no_lookahead_monthly(base):
    _, panel = base
    ref = f15.compute({"bond_panel": panel}, AS_OF)
    late = panel[panel["date"] == AS_OF].copy()
    future = late.assign(date=AS_OF + pd.offsets.MonthEnd(1), price=late["price"] * 1.3,
                         available_at=AS_OF + pd.offsets.MonthEnd(1) + pd.Timedelta(1, unit="D"))
    revised = panel[panel["date"] == AS_OF - pd.offsets.MonthEnd(3)].copy()
    revised = revised.assign(price=revised["price"] * 0.7, available_at=AS_OF + pd.Timedelta(5, unit="D"))
    out = f15.compute({"bond_panel": pd.concat([panel, future, revised], ignore_index=True)}, AS_OF)
    pd.testing.assert_frame_equal(ref, out)


def test_skip_one_month_ignores_month_t_return(base):
    r, _ = base
    r2 = r.copy()
    r2[-1, :10] += 0.05                        # the return into month t moves only the as_of price
    a = f15.compute({"bond_panel": bond_panel(r)}, AS_OF)
    b = f15.compute({"bond_panel": bond_panel(r2)}, AS_OF)
    pd.testing.assert_series_equal(a["score"], b["score"])
    a0 = f15.compute({"bond_panel": bond_panel(r)}, AS_OF, skip=0)
    b0 = f15.compute({"bond_panel": bond_panel(r2)}, AS_OF, skip=0)
    assert not np.allclose(a0["score"].fillna(0), b0["score"].fillna(0))


def test_no_lookahead_daily(base):
    _, panel = base
    d = daily_panel()
    ref = f15.compute({"bond_panel": panel, "bond_daily": d}, AS_OF, freq="daily")
    assert ref["score"].notna().sum() > 20
    future = d[d["date"] == d["date"].max()].assign(date=AS_OF + pd.Timedelta(3, unit="D"), g_spread=0.2)
    future["available_at"] = future["date"] + pd.Timedelta(1, unit="D")
    in_skip = d[d["date"] > AS_OF - pd.Timedelta(f15.SKIP_DAYS, unit="D")].assign(g_spread=0.3)
    late = d[d["date"] == AS_OF - pd.Timedelta(30, unit="D")].assign(g_spread=0.4,
                                                                     available_at=AS_OF + pd.Timedelta(9, unit="D"))
    out = f15.compute({"bond_panel": panel, "bond_daily": pd.concat([d, future, in_skip, late])}, AS_OF, freq="daily")
    pd.testing.assert_frame_equal(ref, out)


# ---------------------------------------------------------------- sign


@pytest.mark.parametrize("seed", range(5))
def test_sign_cheap_residual_scores_high(seed):
    out = f15.compute({"bond_panel": bond_panel(shocked(seed))}, AS_OF)
    cheap, rich = out["score"].iloc[:3], out["score"].iloc[3:6]
    assert cheap.notna().any() and rich.notna().any()
    assert cheap.mean() > 0 > rich.mean()
    assert cheap.mean() > out["score"].iloc[6:].mean() > rich.mean()


def test_sign_pooled_over_seeds():
    s = pd.concat([f15.compute({"bond_panel": bond_panel(shocked(k))}, AS_OF)["score"].iloc[:6].rename(k)
                   for k in range(8)], axis=1)
    assert s.iloc[:3].stack().mean() > 0.5
    assert s.iloc[3:6].stack().mean() < -0.5


# ---------------------------------------------------------------- edge cases


def test_missing_panels_give_empty_frames(base):
    _, panel = base
    for panels, kw in (({}, {}), ({"bond_panel": panel}, {"freq": "daily"}),
                       ({"bond_panel": panel, "bond_daily": pd.DataFrame()}, {"freq": "daily"})):
        out = f15.compute(panels, AS_OF, **kw)
        assert out.empty and list(out.columns) == f15.COLS


def test_short_history_and_gaps_give_nan(base):
    r, panel = base
    young = panel[(panel["cusip"] == "C000") & (panel["date"] < AS_OF - pd.offsets.MonthEnd(10))].index
    gap = panel[(panel["cusip"] == "C001") & panel["date"].between(AS_OF - pd.offsets.MonthEnd(8),
                                                                    AS_OF - pd.offsets.MonthEnd(3))].index
    out = f15.compute({"bond_panel": panel.drop(young.union(gap))}, AS_OF).set_index("cusip")
    assert out.loc["C000", "status"] == "no_history" and np.isnan(out.loc["C000", "score"])
    assert out.loc["C001", "status"] == "no_history" and np.isnan(out.loc["C001", "score"])
    assert out["score"].notna().sum() > 30


def test_distressed_and_carried_bonds_dropped(base):
    _, panel = base
    p = panel.copy()
    now = p["date"] == AS_OF
    p.loc[now & (p["cusip"] == "C002"), "g_spread"] = 0.15
    p.loc[now & (p["cusip"] == "C003"), "carried"] = True
    out = f15.compute({"bond_panel": p}, AS_OF)
    assert not out["cusip"].isin(["C002", "C003"]).any()


def test_issuer_level_copies_score_to_bonds():
    r = returns_matrix(60, 2)
    r[:, 1] = r[:, 0] + 0.001 * np.random.default_rng(9).standard_normal(len(r))   # C000, C001: same issuer
    issuers = ["G000", "G000"] + [f"G{j:03d}" for j in range(2, 60)]
    out = f15.compute({"bond_panel": bond_panel(r, issuers=issuers)}, AS_OF, level="issuer").set_index("cusip")
    assert np.isfinite(out.loc["C000", "score"]) and out.loc["C000", "score"] == out.loc["C001", "score"]
    assert out["gvkey"].nunique() == 59


def test_var_frac_and_mu_modes(base):
    _, panel = base
    v = f15.compute({"bond_panel": panel}, AS_OF, var_frac=0.3)
    assert (v["var_explained"] >= 0.3).all() and v["n_pcs"].iloc[0] >= 1
    own = f15.compute({"bond_panel": panel}, AS_OF, mu_mode="own")
    cen = f15.compute({"bond_panel": panel}, AS_OF)
    ok = cen["status"] == "ok"
    shift = (own["score"] - cen["score"])[ok & (own["score"].abs() < 4) & (cen["score"].abs() < 4)]
    np.testing.assert_allclose(shift, (cen["mu_star"] / cen["sigma_eq"])[shift.index])


# ---------------------------------------------------------------- formula helpers


def test_pc_residuals_hand():
    e = f15.pc_residuals(np.array([[1.0], [2.0], [4.0]]), np.array([[0.0], [1.0], [2.0]]))
    np.testing.assert_allclose(e[:, 0], [1 / 6, -1 / 3, 1 / 6])


def test_pca_factors_rank_one_and_var_frac():
    rng = np.random.default_rng(3)
    f = rng.standard_normal(30)
    R = np.outer(f, rng.uniform(0.5, 2.0, 8)) + rng.uniform(-0.1, 0.1, 8)   # one factor plus constant offsets
    F, n, share = f15.pca_factors(R, 1)
    assert n == 1 and share == pytest.approx(1.0)
    assert np.abs(f15.pc_residuals(R, F)).max() < 1e-10
    R2 = rng.standard_normal((30, 6))
    Z = (R2 - R2.mean(0)) / R2.std(0, ddof=1)
    s = np.linalg.svd(Z, compute_uv=False)
    cum = np.cumsum(s ** 2) / np.sum(s ** 2)
    _, n2, share2 = f15.pca_factors(R2, var_frac=0.5)
    assert n2 == int(np.argmax(cum >= 0.5)) + 1 and share2 == pytest.approx(cum[n2 - 1])


def test_ou_fit_hand():
    x = np.array([0.0, 0.31, 0.44, 0.59, 0.6, 0.55, 0.61, 0.74, 0.76])
    eps = np.diff(np.concatenate([[0.0], x]))
    f = f15.ou_fit(eps, annual=12)
    b, a = np.polyfit(x[:-1], x[1:], 1)
    var_e = np.sum((x[1:] - a - b * x[:-1]) ** 2) / (len(x) - 3)
    assert 0 < b < 1 and f["status"] == "ok"
    assert f["b"] == pytest.approx(b) and f["a"] == pytest.approx(a)
    assert f["mu"] == pytest.approx(a / (1 - b))
    assert f["theta"] == pytest.approx(-np.log(b) * 12)
    assert f["sigma_eq"] == pytest.approx(np.sqrt(var_e / (1 - b * b)))
    assert f["sigma"] == pytest.approx(np.sqrt(var_e * 2 * f["theta"] / (1 - b * b)))     # Eq. A5
    assert f["x_last"] == pytest.approx(0.76)


def test_ou_fit_trend_and_alternation_rejected():
    trend = f15.ou_fit(0.01 * 1.2 ** np.arange(12))                            # X explodes: b = 1.2
    assert trend["status"] == "no_reversion" and trend["b"] == pytest.approx(1.2)
    alt = f15.ou_fit(np.array([1.0, -2, 2, -2, 2, -2, 2, -2]))                 # X alternates: b < 0
    assert alt["status"] == "no_reversion" and alt["b"] < 0 and np.isnan(alt["mu"])


def test_s_score_hand():
    mu, x, sd = np.array([0.02, -0.01, 0.1]), np.zeros(3), np.full(3, 0.01)
    np.testing.assert_allclose(f15.s_score(x, mu, 0.005, sd), [1.5, -1.5, 4.0])
    np.testing.assert_allclose(f15.s_score(x, mu, 0.005, sd, "own"), [2.0, -1.0, 4.0])
    np.testing.assert_allclose(f15.s_score(x, mu, 0.005, sd, "pooled"), [0.5, 0.5, 0.5])
    np.testing.assert_allclose(f15.s_score(np.array([0.03]), np.array([0.01]), 0.0, np.array([0.01]), "own"), [-2.0])


def test_variance_ratio_hand():
    assert f15.variance_ratio(np.array([1.0, -1] * 10), k=2) == pytest.approx(0.0)
    rw = np.random.default_rng(4).standard_normal(20000)
    assert f15.variance_ratio(rw, k=3) == pytest.approx(1.0, abs=0.05)
    assert np.isnan(f15.variance_ratio(np.array([1.0, 2.0]), k=3))


def test_speed_filter_marks_slow():
    rng = np.random.default_rng(5)
    R = pd.DataFrame(rng.standard_normal((36, 30)) * 0.01)
    hump = 0.05 * np.sin(np.pi * np.arange(1, 13) / 13) + 0.001 * rng.standard_normal(12)   # one slow swing
    R.iloc[-12:, 0] = np.diff(np.concatenate([[0.0], hump]))
    tab, info = f15.reversion_table(R, R.notna(), ou_window=12, annual=12)
    assert tab.loc[0, "status"] == "slow" and tab.loc[0, "half_life"] > 6 and np.isnan(tab.loc[0, "score"])
    hl = tab.loc[tab["status"].isin(["ok", "slow"]), "half_life"]
    assert ((hl > 6) == (tab.loc[hl.index, "status"] == "slow")).all()
    assert tab.loc[tab["status"] == "ok", "score"].notna().all()
    assert info["mu_star"] == pytest.approx(tab.loc[tab["status"] == "ok", "mu"].mean())


def test_hysteresis_hand():
    pct = pd.Series([0.95, 0.75, 0.75, 0.5, 0.05, 0.25, np.nan])
    prev = pd.Series([0, 1, 0, 1, 0, -1, 1])
    assert f15.hysteresis(prev, pct).tolist() == [1, 1, 0, 0, -1, -1, 0]


def test_signal_weights_hand():
    w = f15.signal_weights(pd.Series([2.0, -1.0, np.nan]))
    np.testing.assert_allclose(w, [2 / 3, -1 / 3, 0.0])


def test_daily_spread_returns_hand():
    d = pd.DataFrame({"cusip": ["A", "A", "A", "B", "B"],
                      "date": pd.to_datetime(["2015-06-01", "2015-06-02", "2015-06-04", "2015-06-01", "2015-06-03"]),
                      "g_spread": [0.05, 0.06, 0.055, 0.04, 0.05]})
    r, traded = f15.daily_spread_returns(d, pd.Series({"A": 4.0, "B": 2.0}))
    assert r.loc["2015-06-02", "A"] == pytest.approx(0.05 / 365.25 - 4 * 0.01)
    assert r.loc["2015-06-03", "A"] == pytest.approx(0.06 / 365.25)                 # no trade: carry only
    assert r.loc["2015-06-04", "A"] == pytest.approx(0.06 / 365.25 - 4 * (-0.005))
    assert r.loc["2015-06-02", "B"] == pytest.approx(0.04 / 365.25)
    assert r.loc["2015-06-03", "B"] == pytest.approx(0.04 / 365.25 - 2 * 0.01)
    assert traded.sum().to_dict() == {"A": 3, "B": 2}
