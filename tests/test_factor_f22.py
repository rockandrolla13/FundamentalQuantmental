"""Tests for F22 credit curve shape against level (docs/factors/F22-curve-shape.md)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from scipy.optimize import brentq

from hy.factors import f06_issuer_curve_residual as f6
from hy.factors import f22_curve_shape as f22

AS_OF = pd.Timestamp("2015-06-30")
TSY = 0.04
TENOR_COLS = [0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 7.0, 10.0, 20.0, 30.0]
YEARS = [2.0, 4.0, 6.0, 8.0, 10.0]
R = 0.25
X2, X5, X10 = f6.shock_basis(np.array([2.0, 5.0, 10.0]))


# ---------------------------------------------------------------- synthetic fixture


def flat_disc():
    grid, b = f6.discount_factors(pd.Series({t: TSY for t in TENOR_COLS}))
    return lambda t: f6._disc(np.asarray(t, dtype=float), grid, b)


DISC = flat_disc()


def price_for_spread(c: float, T: float, s: float) -> float:
    """Price of a bond whose flat-hazard par-adjusted spread is s (inverse of Martin eq. 7)."""
    g = lambda lam: (1 - R) * f6.flat_hazard_legs(T, lam, DISC)["xi"] / f6.flat_hazard_legs(T, lam, DISC)["pi"] - s
    return f6.model_price(c, T, brentq(g, 1e-9, 3.0), R, DISC)


def ytm(price: float, c: float, T: float) -> float:
    n = int(round(T * 2))
    pv = lambda y: sum(c / 2 / (1 + y / 2) ** k for k in range(1, n + 1)) * 100 + 100 / (1 + y / 2) ** n - price
    return brentq(pv, -0.5, 5.0)


def issuer_rows(gvkey, level, slope, date=AS_OF, years=YEARS):
    """Bonds of one issuer on the exact F06 curve with 2y spread `level` and 5s10s slope `slope`."""
    a1 = slope / (X10 - X5)
    a0 = level - a1 * X2
    rows = []
    for k, T in enumerate(years):
        s = a0 + a1 * f6.shock_basis(np.array([T]))[0]
        c = TSY + s                                   # near par, so the proxy call test keeps the bond
        p = price_for_spread(c, T, s)
        y = ytm(p, c, T)
        rows.append({"date": date, "cusip": f"{gvkey}{k}", "gvkey": gvkey, "years": T, "price": p, "coupon": c,
                     "yield": y, "g_spread": y - TSY, "tsy_yield": TSY, "mod_dur": T * 0.8, "carried": False,
                     "available_at": date + pd.Timedelta(1, unit="D")})
    return rows


def tsy_panel(date=AS_OF):
    row = {"date": date, "available_at": date + pd.Timedelta(1, unit="D")}
    row.update({str(t): TSY for t in TENOR_COLS})
    return pd.DataFrame([row])


ALPHA, BETA = 0.002, 0.10
LEVELS = np.linspace(0.02, 0.06, 12)


def panels(bump=0.0, bumped=0, n=12, date=AS_OF, extra_rows=()):
    rows = []
    for i, L in enumerate(LEVELS[:n]):
        sl = ALPHA + BETA * L + (bump if i == bumped else 0.0)
        rows += issuer_rows(f"G{i:02d}", L, sl, date)
    rows += list(extra_rows)
    return {"bond_panel": pd.DataFrame(rows), "treasury_curve": tsy_panel(date)}


@pytest.fixture(scope="module")
def base():
    return panels()


@pytest.fixture(scope="module")
def bumped():
    return panels(bump=0.003, bumped=4)


# ---------------------------------------------------------------- contract


def test_meta_and_columns(base):
    for k in ("rank", "name", "level", "horizon_months", "needs", "spec", "section"):
        assert k in f22.META
    assert f22.META["rank"] == 22 and f22.META["level"] == "issuer"
    out = f22.compute(base, AS_OF)
    assert list(out.columns) == f22.COLS
    assert out["gvkey"].is_unique and len(out) == 12
    assert (out["date"] == AS_OF).all() and (out["status"] == "ok").all()


def test_empty_without_bond_panel():
    out = f22.compute({"treasury_curve": tsy_panel()}, AS_OF)
    assert out.empty and list(out.columns) == f22.COLS


# ---------------------------------------------------------------- no look-ahead


def test_no_lookahead(bumped):
    ref = f22.compute(bumped, AS_OF)
    late_date = AS_OF + pd.offsets.MonthEnd(1)
    late = pd.DataFrame(sum((issuer_rows(f"G{i:02d}", 0.09, -0.02, late_date) for i in range(3)), []))
    hidden = pd.DataFrame(issuer_rows("G04", 0.03, 0.05, AS_OF)).assign(
        cusip=lambda d: "X" + d["cusip"], available_at=AS_OF + pd.Timedelta(5, unit="D"))
    p = {**bumped, "bond_panel": pd.concat([bumped["bond_panel"], late, hidden], ignore_index=True)}
    out = f22.compute(p, AS_OF)
    pd.testing.assert_frame_equal(ref, out)


# ---------------------------------------------------------------- sign and fit


def test_exact_line_gives_zero_residual(base):
    out = f22.compute(base, AS_OF)
    assert np.allclose(out["slope"], ALPHA + BETA * LEVELS, atol=1e-7)
    assert np.allclose(out["level"], LEVELS, atol=1e-7)
    assert np.allclose(out["beta"], BETA, atol=1e-5)
    assert np.allclose(out["score"], 0.0, atol=1e-7)
    assert (out["reg_cell"] == "pooled").all()


def test_steep_for_level_scores_top(bumped):
    out = f22.compute(bumped, AS_OF).set_index("gvkey")
    assert out["score"].idxmax() == "G04"
    assert out.loc["G04", "score"] > 0.002 and out.loc["G04", "z"] > 2
    assert out.loc["G04", "long_cusip"] == "G044" and out.loc["G04", "short_cusip"] == "G040"


def test_inverted_flag():
    p = panels(bump=-0.02, bumped=11)               # 2s10s of G11 goes below zero
    out = f22.compute(p, AS_OF).set_index("gvkey")
    assert bool(out.loc["G11", "inverted"]) and out.loc["G11", "slope_2s10s"] < 0
    assert not bool(out.loc["G00", "inverted"])
    assert out["score"].idxmin() == "G11"


# ---------------------------------------------------------------- edge cases


def test_few_bonds_and_short_span():
    extra = issuer_rows("TWO", 0.04, 0.006, years=[3.0, 9.0]) + issuer_rows("SHORT", 0.04, 0.006,
                                                                             years=[1.5, 3.0, 5.0, 6.0])
    out = f22.compute(panels(extra_rows=extra), AS_OF).set_index("gvkey")
    assert out.loc["TWO", "status"] == "few_bonds" and np.isnan(out.loc["TWO", "score"])
    assert out.loc["SHORT", "status"] == "short_span" and np.isnan(out.loc["SHORT", "score"])
    assert out.loc["G00", "status"] == "ok"


def test_too_few_issuers():
    out = f22.compute(panels(n=5), AS_OF)
    assert (out["status"] == "few_issuers").all() and out["score"].isna().all()


def test_class_cell_and_pooled_fallback(base):
    dates = AS_OF - pd.Timedelta(10, unit="D")
    sym = ["B"] * 10 + ["BB", "BB"]
    ratings = pd.DataFrame({"gvkey": [f"G{i:02d}" for i in range(12)], "datadate": dates, "splticrm": sym,
                            "available_at": dates})
    out = f22.compute({**base, "ratings": ratings}, AS_OF).set_index("gvkey")
    assert (out.loc[[f"G{i:02d}" for i in range(10)], "reg_cell"] == "B").all()
    assert (out.loc[["G10", "G11"], "reg_cell"] == "pooled").all()


def test_control_curvature_runs(base):
    out = f22.compute(base, AS_OF, control_curvature=True)
    assert out["score"].notna().all()


# ---------------------------------------------------------------- formula helpers


def test_tenor_spreads_hand():
    s = f22.tenor_spreads(0.03, 0.02)
    hand = [0.03 + 0.02 * (1 - np.exp(-0.4 * T)) / (0.4 * T) for T in (2.0, 5.0, 10.0)]
    assert np.allclose(s, hand)


def test_curvature_forms():
    assert f22.curvature(0.02, 0.03, 0.05) == pytest.approx(0.03 - 0.035)
    assert f22.curvature(0.02, 0.03, 0.05, form="as_written") == pytest.approx(0.03 - 0.025 + 0.01)


def test_ns_curvature_recovers_hump():
    T = np.array([1.5, 3.0, 5.0, 7.0, 10.0, 15.0])
    lam = f6.SHOCK_LAMBDA
    ns = lambda t: 0.04 - 0.01 * f6.shock_basis(t) + 0.02 * (f6.shock_basis(t) - np.exp(-lam * t))
    s2, s5, s10 = ns(np.array([2.0, 5.0, 10.0]))
    assert f22.ns_curvature(T, ns(T)) == pytest.approx(s5 - 0.5 * (s2 + s10), abs=1e-12)
    assert np.isnan(f22.ns_curvature(T[:3], ns(T[:3])))


def test_slope_residual_hand():
    L = np.array([0.02, 0.03, 0.04, 0.05])
    sl = 0.001 + 0.2 * L + np.array([0.0, 0.001, -0.001, 0.0])
    out = f22.slope_residual(sl, L, min_n=4)
    X = np.column_stack([np.ones(4), L])
    coef = np.linalg.lstsq(X, sl, rcond=None)[0]
    e = sl - X @ coef
    assert np.allclose(out["resid"], e) and np.allclose(out["beta"], coef[1])
    assert np.allclose(out["z"], e / np.sqrt(np.sum(e ** 2) / 2))
    assert f22.slope_residual(sl, L, min_n=5)["resid"].isna().all()


def test_bucket_z_hand():
    lv = np.arange(6, dtype=float)
    sl = np.array([1.0, 2.0, 3.0, 10.0, 20.0, 30.0])
    z = f22.bucket_z(sl, lv, n_buckets=2, min_n=3)
    assert np.allclose(z, [-1, 0, 1, -1, 0, 1])


def test_own_history_z_hand():
    past = np.arange(12, dtype=float)
    assert f22.own_history_z(20.0, past) == pytest.approx((20 - 5.5) / np.std(past, ddof=1))
    assert np.isnan(f22.own_history_z(20.0, past[:11]))


def test_history_z_own_in_compute():
    months = [AS_OF - pd.offsets.MonthEnd(k) for k in (3, 2, 1, 0)]
    shifts = [0.0, 0.001, -0.001, 0.004]
    parts, tsy = [], []
    for d, sh in zip(months, shifts):
        p = panels(bump=sh, bumped=4, date=d)
        parts.append(p["bond_panel"])
        tsy.append(p["treasury_curve"])
    p = {"bond_panel": pd.concat(parts, ignore_index=True), "treasury_curve": pd.concat(tsy, ignore_index=True)}
    out = f22.compute(p, AS_OF, history_months=3).set_index("gvkey")
    assert out.loc["G04", "z_own"] > 2
    assert f22.compute(p, AS_OF)["z_own"].isna().all()


def test_spread_vol_hand():
    d = [AS_OF - pd.offsets.MonthEnd(k) for k in range(7, -1, -1)]
    g = [0.03, 0.031, 0.029, 0.032, 0.03, 0.033, 0.031, 0.034]
    panel = pd.DataFrame({"date": d, "gvkey": "A", "cusip": "A1", "g_spread": g, "years": 5.0, "yield": 0.07,
                          "price": 100.0, "carried": False, "mod_dur": 4.0, "available_at": d})
    v = f22.spread_vol(panel, AS_OF)
    assert v["A"] == pytest.approx(np.std(np.diff(g), ddof=1))
    assert np.isnan(f22.spread_vol(panel, AS_OF, min_obs=8)["A"])


def test_dts_hedge_hand():
    assert f22.dts_hedge(0.05, 7.0, 0.03, 2.0) == pytest.approx(0.35 / 0.06)
    assert np.isnan(f22.dts_hedge(0.05, 7.0, 0.0, 2.0))
