"""Tests for F01 IPCA (docs/factors/F01-ipca.md section 7; methodology Sections 8 and 11). Synthetic data only."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from scipy import stats

from hy.factors import f01_ipca as f

START = pd.Timestamp("2010-01-31")


def _panels(n_bonds: int = 60, n_months: int = 48, seed: int = 0, extras: bool = True) -> dict[str, pd.DataFrame]:
    """A panel where the next DtS-scaled return is rank(spread) x f_t+1 plus noise, E[f] > 0.

    So the true expected return rises with spread, and the IPCA score must rank bonds by spread."""
    rng = np.random.default_rng(seed)
    months = pd.date_range(START, periods=n_months, freq="ME")
    base = rng.uniform(0.02, 0.10, n_bonds)
    dur = rng.uniform(2.0, 6.0, n_bonds)
    cpn = rng.uniform(0.04, 0.08, n_bonds)
    price = np.full(n_bonds, 100.0)
    rows = []
    for t, d in enumerate(months):
        s = base * np.exp(0.05 * rng.standard_normal(n_bonds))
        rows.append(pd.DataFrame({
            "date": d, "cusip": [f"C{i:03d}" for i in range(n_bonds)], "gvkey": [f"G{i:03d}" for i in range(n_bonds)],
            "years": 5.0, "g_spread": s, "price": price.copy(), "yield": s, "coupon": cpn, "maturity": d + pd.DateOffset(years=5),
            "mod_dur": dur, "tsy_yield": 0.0, "bid_ask_pts": 0.5, "n_trades": 10, "par_volume": 1e6, "carried": False,
            "accrue_to": d, "hedge_date": d, "available_at": d + pd.Timedelta(1, unit="D")}))
        if t + 1 < n_months:                      # next month's price from the true model
            z = (stats.rankdata(s) - 1) / (n_bonds - 1) - 0.5
            r = z * rng.normal(0.02, 0.01) + 0.002 * rng.standard_normal(n_bonds)
            tau = (months[t + 1] - d).days / 365.25
            price = price * (1 + r * np.maximum(dur * s, f.DTS_FLOOR)) - 100 * cpn * tau
    out = {"bond_panel": pd.concat(rows, ignore_index=True)}
    if extras:
        g = [f"G{i:03d}" for i in range(n_bonds)]
        out["leverage"] = pd.DataFrame([{"date": d, "gvkey": k, "leverage": 3 + i % 5, "ltm_ebitda": 100.0,
                                         "debt": 300.0 + i, "available_at": d + pd.Timedelta(1, unit="D")}
                                        for d in months for i, k in enumerate(g)])
        out["gics"] = pd.DataFrame({"gvkey": g, "gsector": [str(10 + 5 * (i % 3)) for i in range(n_bonds)],
                                    "indfrom": pd.Timestamp("2000-01-01"), "indthru": pd.NaT,
                                    "available_at": pd.Timestamp("2000-01-02")})
        out["ratings"] = pd.DataFrame([{"gvkey": k, "datadate": d, "splticrm": ["BB+", "B", "CCC+"][i % 3],
                                        "available_at": d + pd.Timedelta(1, unit="D")}
                                       for d in months for i, k in enumerate(g) if i % 4])   # a quarter unrated
        eq = [{"gvkey": k, "datadate": d, "ret": rng.normal(0.01, 0.05), "available_at": d + pd.Timedelta(3, unit="D")}
              for d in months for i, k in enumerate(g) if i % 2]                             # half are private
        out["equity_monthly"] = pd.DataFrame(eq)
    return out


@pytest.fixture(scope="module")
def panels():
    return _panels()


@pytest.fixture(scope="module")
def result(panels):
    return f.compute(panels, START + pd.offsets.MonthEnd(47), K=1)


# ---------------------------------------------------------------- contract


def test_meta_and_columns(result, panels):
    assert {"rank", "name", "level", "horizon_months", "needs", "spec", "section"} <= set(f.META)
    assert f.META["rank"] == 1 and f.META["level"] == "bond"
    assert {"date", "cusip", "score", "available_at", "ipca_er", "ipca_er_ret", "ipca_beta_1"} <= set(result.columns)
    assert result["cusip"].is_unique and len(result) == 60
    as_of = START + pd.offsets.MonthEnd(47)
    assert (result["date"] == as_of).all() and (result["available_at"] == as_of + pd.Timedelta(1, unit="D")).all()
    assert result.attrs["n_train_months"] >= f.MIN_TRAIN_MONTHS and result.attrs["converged"]


# ---------------------------------------------------------------- sign


def test_score_ranks_by_true_expected_return(result, panels):
    p = panels["bond_panel"]
    s = p[p["date"] == result["date"].iloc[0]].set_index("cusip")["g_spread"]
    ic = stats.spearmanr(result["score"], result["cusip"].map(s)).statistic
    assert ic > 0.9
    assert result.attrs["lam"][0] > 0
    assert result.attrs["gamma"].loc["spread", "f1"] == pytest.approx(result.attrs["gamma"]["f1"].abs().max())


def test_prefitted_gamma_reproduces_score(result, panels):
    as_of = START + pd.offsets.MonthEnd(47)
    again = f.compute(panels, as_of, gamma=result.attrs["gamma"], lam=result.attrs["lam"])
    np.testing.assert_allclose(again["score"], result["score"], atol=1e-10)
    lam_free = f.compute(panels, as_of, gamma=result.attrs["gamma"])    # lambda from the factor steps
    np.testing.assert_allclose(lam_free["score"], result["score"], atol=1e-8)


# ---------------------------------------------------------------- no look-ahead


def test_no_lookahead(panels, result):
    as_of = START + pd.offsets.MonthEnd(47)
    dt = as_of + pd.Timedelta(1, unit="D")
    late = {k: v.copy() for k, v in panels.items()}
    bp = late["bond_panel"]
    fut = bp[bp["date"] == as_of].copy()
    for k in (1, 2):                                       # future months with wild prices
        x = fut.assign(date=as_of + pd.offsets.MonthEnd(k), price=fut["price"] * (1 + 0.5 * k),
                       accrue_to=as_of + pd.offsets.MonthEnd(k), hedge_date=as_of + pd.offsets.MonthEnd(k),
                       available_at=as_of + pd.offsets.MonthEnd(k) + pd.Timedelta(1, unit="D"))
        bp = pd.concat([bp, x], ignore_index=True)
    revised = bp[bp["date"] == as_of].assign(g_spread=0.15, available_at=dt + pd.Timedelta(5, unit="D"))
    late["bond_panel"] = pd.concat([bp, revised], ignore_index=True)       # a late revision of month t
    lev = late["leverage"]
    late["leverage"] = pd.concat([lev, lev[lev["date"] == as_of].assign(leverage=99.0, available_at=dt + pd.Timedelta(9, unit="D"))])
    eq = late["equity_monthly"]
    late["equity_monthly"] = pd.concat([eq, eq.assign(datadate=eq["datadate"] + pd.offsets.MonthEnd(3), ret=0.9,
                                                      available_at=dt + pd.Timedelta(30, unit="D"))])
    out = f.compute(late, as_of, K=1)
    pd.testing.assert_frame_equal(out, result)


def test_training_uses_only_realised_returns(panels):
    """The forecast at t must not change when the panel after t changes (spec section 7)."""
    as_of = START + pd.offsets.MonthEnd(40)
    a = f.compute(panels, as_of, K=1)
    cut = {k: v for k, v in panels.items()}
    bp = panels["bond_panel"]
    cut["bond_panel"] = bp[bp["date"] <= as_of]
    b = f.compute(cut, as_of, K=1)
    pd.testing.assert_frame_equal(a, b)


# ---------------------------------------------------------------- edge cases


def test_short_panel_is_empty():
    p = _panels(n_months=30)
    out = f.compute(p, START + pd.offsets.MonthEnd(29))
    assert out.empty and {"date", "cusip", "score", "available_at"} <= set(out.columns)


def test_missing_bond_panel_is_empty(panels):
    out = f.compute({k: v for k, v in panels.items() if k != "bond_panel"}, START + pd.offsets.MonthEnd(47))
    assert out.empty and "score" in out.columns


def test_missing_optional_panels_still_scores():
    p = _panels(extras=False)
    out = f.compute(p, START + pd.offsets.MonthEnd(47), K=1)
    assert len(out) == 60 and out["score"].notna().all()
    assert (out["flag_equity"] == 1).all() and (out["flag_rating"] == 1).all()
    assert "debt_to_ebitda" not in out.attrs["gamma"].index      # an all-missing characteristic drops out


def test_private_issuer_gets_flag_and_forecast(result):
    priv = result[result["cusip"].str[1:].astype(int) % 2 == 0]
    assert (priv["flag_equity"] == 1).all() and priv["score"].notna().all()


def test_screen_drops_distressed_and_carried(panels):
    as_of = START + pd.offsets.MonthEnd(47)
    p = {k: v.copy() for k, v in panels.items()}
    bp = p["bond_panel"]
    bp.loc[(bp["date"] == as_of) & (bp["cusip"] == "C000"), "g_spread"] = 0.25
    bp.loc[(bp["date"] == as_of) & (bp["cusip"] == "C001"), "carried"] = True
    out = f.compute(p, as_of, K=1)
    assert not {"C000", "C001"} & set(out["cusip"])


def test_all_characteristics_missing_gives_nan():
    z = np.array([[0.2, 1.0], [0.0, 1.0]])
    er = f.expected_return(z, np.array([[1.0], [0.5]]), np.array([0.1]), np.array([True, False]))
    assert er[0] == pytest.approx((0.2 + 0.5) * 0.1) and np.isnan(er[1])


# ---------------------------------------------------------------- helpers


def test_rank_scale():
    df = pd.DataFrame({"date": [1, 1, 1, 1, 2, 2, 2], "x": [3.0, 1.0, 2.0, np.nan, 5.0, 5.0, 1.0]})
    out = f.rank_scale(df, ["x"])["x"].to_numpy()
    np.testing.assert_allclose(out, [0.5, -0.5, 0.0, 0.0, 0.25, 0.25, -0.5])
    one = f.rank_scale(pd.DataFrame({"date": [1, 1], "x": [7.0, np.nan]}), ["x"])["x"]
    assert (one == 0).all()
    rnd = f.rank_scale(pd.DataFrame({"date": 1, "x": np.random.default_rng(1).normal(size=101)}), ["x"])["x"]
    assert rnd.between(-0.5, 0.5).all() and rnd.median() == pytest.approx(0.0)


def test_dts_floor():
    r = f.dts_scaled_return([0.01, 0.01], [2.0, 5.0], [0.05, 0.10])     # DtS 0.1 and 0.5
    np.testing.assert_allclose(r, [0.01 / 0.25, 0.01 / 0.5])


def test_rating_number():
    assert f.rating_number("AAA") == 1 and f.rating_number("BB+") == 11 and f.rating_number("B-") == 16
    assert f.rating_number("D") == 22 and f.rating_number("SD") == 22 and np.isnan(f.rating_number("NR"))


def test_second_lowest():
    w = np.array([[3.0, -1.0, np.nan, -2.0, 0.5], [np.nan, np.nan, 1.0, 2.0, np.nan]])
    out = f._second_lowest(w, 3)
    assert out[0] == -1.0 and np.isnan(out[1])


def _sim(K: int, n: int = 300, T: int = 80, L: int = 4, noise: float = 0.05, seed: int = 3):
    rng = np.random.default_rng(seed)
    gamma = np.linalg.qr(rng.standard_normal((L, K)))[0]
    mean = np.array([0.5, 0.2][:K])
    Z, R = {}, {}
    for t in pd.date_range(START, periods=T, freq="ME"):
        z = np.column_stack([rng.uniform(-0.5, 0.5, (n, L - 1)), np.ones(n)])
        fac = mean + rng.standard_normal(K)
        Z[t], R[t] = z, z @ gamma @ fac + noise * rng.standard_normal(n)
    return Z, R, gamma


def test_als_recovers_gamma_k1():
    Z, R, g = _sim(1)
    fit = f.fit_ipca(Z, R, K=1)
    assert fit.converged
    assert float(np.corrcoef(fit.gamma[:, 0], g[:, 0])[0, 1]) > 0.99    # sign fixed by the positive factor mean
    assert fit.lam[0] > 0


def test_als_recovers_gamma_k2_up_to_rotation():
    Z, R, g = _sim(2)
    fit = f.fit_ipca(Z, R, K=2)
    proj = fit.gamma @ fit.gamma.T @ g                                     # project the true Gamma on the fit
    assert np.max(np.abs(proj - g)) < 0.02
    np.testing.assert_allclose(fit.gamma.T @ fit.gamma, np.eye(2), atol=1e-8)
    ff = fit.factors.T @ fit.factors
    assert abs(ff[0, 1]) < 1e-8 * abs(ff[0, 0]) and ff[0, 0] >= ff[1, 1]
    assert (fit.factors.mean(axis=0) >= 0).all()


def test_factor_step_is_cross_section_ols():
    Z, R, g = _sim(2, T=1)
    (t,) = Z
    x = Z[t] @ g
    ols = np.linalg.lstsq(x, R[t], rcond=None)[0]
    np.testing.assert_allclose(f.factor_step(g, Z[t].T @ Z[t], Z[t].T @ R[t]), ols, atol=1e-10)


def test_gamma_step_given_factors_recovers_gamma():
    rng = np.random.default_rng(5)
    g = rng.standard_normal((3, 2))
    zs, rs, fs = [], [], []
    for _ in range(30):
        z = rng.standard_normal((50, 3))
        fac = rng.standard_normal(2)
        zs.append(z), fs.append(fac), rs.append(z @ g @ fac)
    zz = np.stack([z.T @ z for z in zs])
    zr = np.stack([z.T @ r for z, r in zip(zs, rs)])
    np.testing.assert_allclose(f.gamma_step(zz, zr, np.stack(fs)), g, atol=1e-10)
