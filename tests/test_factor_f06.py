"""Tests for F06 within-issuer curve residual on par-adjusted spread (docs/factors/F06-issuer-curve-residual.md)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from scipy.optimize import brentq

from hy.factors import f06_issuer_curve_residual as f6

AS_OF = pd.Timestamp("2015-06-30")
TSY = 0.04
TENORS = [0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 7.0, 10.0, 20.0, 30.0]


# ---------------------------------------------------------------- synthetic fixture


def tsy_panel(date=AS_OF, level=TSY) -> pd.DataFrame:
    row = {"date": date, "available_at": date + pd.Timedelta(1, unit="D")}
    row.update({str(t): level for t in TENORS})
    return pd.DataFrame([row])


def flat_disc():
    grid, b = f6.discount_factors(pd.Series({t: TSY for t in TENORS}))
    return lambda t: f6._disc(np.asarray(t, dtype=float), grid, b)


def price_for_spread(c: float, T: float, s: float, R: float, disc) -> float:
    """Price of a bond whose flat-hazard par-adjusted spread is s (inverse of eq. 7)."""
    g = lambda lam: (1 - R) * f6.flat_hazard_legs(T, lam, disc)["xi"] / f6.flat_hazard_legs(T, lam, disc)["pi"] - s
    lam = brentq(g, 1e-9, 3.0)
    return f6.model_price(c, T, lam, R, disc)


def ytm(price: float, c: float, T: float) -> float:
    """Semiannual yield to maturity, for the G-spread column."""
    n = int(round(T * 2))
    pv = lambda y: sum(c / 2 / (1 + y / 2) ** k for k in range(1, n + 1)) * 100 + 100 / (1 + y / 2) ** n - price
    return brentq(pv, -0.5, 5.0)


def bond_row(cusip, gvkey, T, price, c, date=AS_OF):
    y = ytm(price, c, T)
    return {"date": date, "cusip": cusip, "gvkey": gvkey, "years": T, "price": price, "coupon": c, "yield": y,
            "g_spread": y - TSY, "tsy_yield": TSY, "mod_dur": T * 0.8, "carried": False,
            "available_at": date + pd.Timedelta(1, unit="D")}


def issuer_rows(gvkey, years, spreads, coupons, R=0.25, prefix=None):
    disc = flat_disc()
    prefix = prefix or gvkey
    return [bond_row(f"{prefix}{k}", gvkey, T, price_for_spread(c, T, s, R, disc), c)
            for k, (T, s, c) in enumerate(zip(years, spreads, coupons))]


def curve(T, a0=0.03, a1=0.02):
    return a0 + a1 * f6.shock_basis(np.asarray(T, float))


YEARS6 = [2.0, 3.0, 5.0, 7.0, 10.0, 15.0]
NOISE6 = np.array([0.0002, -0.0002, 0.0001, 0.0, -0.0001, 0.0002])


def base_panels(bump=0.0050, bumped=3):
    s = curve(YEARS6) + NOISE6
    s[bumped] += bump
    rows = issuer_rows("A", YEARS6, s, [0.06] * 6)
    return {"bond_panel": pd.DataFrame(rows), "treasury_curve": tsy_panel()}


# ---------------------------------------------------------------- contract


def test_meta_and_columns():
    for k in ("rank", "name", "level", "horizon_months", "needs", "spec", "section"):
        assert k in f6.META
    assert f6.META["rank"] == 6 and f6.META["level"] == "bond"
    out = f6.compute(base_panels(), AS_OF)
    assert list(out.columns) == f6.COLS
    assert out["cusip"].is_unique and len(out) == 6
    assert (out["date"] == AS_OF).all()


def test_missing_bond_panel_gives_empty_frame():
    out = f6.compute({"treasury_curve": tsy_panel()}, AS_OF)
    assert out.empty and list(out.columns) == f6.COLS


def test_no_lookahead():
    p = base_panels()
    ref = f6.compute(p, AS_OF)
    late = pd.DataFrame(issuer_rows("A", YEARS6, curve(YEARS6) + 0.02, [0.06] * 6))
    late_date = late.assign(date=AS_OF + pd.offsets.MonthEnd(1), available_at=AS_OF + pd.Timedelta(32, unit="D"))
    late_avail = late.assign(available_at=AS_OF + pd.Timedelta(5, unit="D"), cusip=late["cusip"] + "x")
    p2 = {"bond_panel": pd.concat([p["bond_panel"], late_date, late_avail], ignore_index=True),
          "treasury_curve": pd.concat([p["treasury_curve"], tsy_panel(AS_OF + pd.Timedelta(10, unit="D"), 0.09)])}
    out = f6.compute(p2, AS_OF)
    pd.testing.assert_frame_equal(ref, out)
    assert (out["available_at"] <= f6.decision_time(AS_OF)).all()


# ---------------------------------------------------------------- sign


def test_cheap_bond_scores_top_and_rich_bond_bottom():
    out = f6.compute(base_panels(bump=0.0050, bumped=3), AS_OF).set_index("cusip")
    assert (out["tier"] == "issuer").all()
    assert out["score"].idxmax() == "A3"
    assert out.at["A3", "resid"] == pytest.approx(0.0050, abs=0.0004)
    assert out.at["A3", "signal_base"] == 1.0 and out.at["A3", "signal_strict"] == 1.0
    rich = f6.compute(base_panels(bump=-0.0050, bumped=2), AS_OF).set_index("cusip")
    assert rich["score"].idxmin() == "A2" and rich.at["A2", "score"] < 0
    assert rich.at["A2", "signal_base"] == -1.0


def test_par_adjustment_removes_coupon_bias():
    """Bonds on one flat hazard with 3% and 12% coupons: equal par-adjusted spreads, but unequal G-spreads."""
    disc, lam, R = flat_disc(), 0.05, 0.25
    coupons = [0.03, 0.12, 0.03, 0.12, 0.03, 0.12]
    years = [4.0, 4.5, 5.0, 5.5, 6.0, 6.5]
    rows = [bond_row(f"C{k}", "C", T, f6.model_price(c, T, lam, R, disc), c) for k, (T, c) in
            enumerate(zip(years, coupons))]
    bullets = pd.DataFrame({"cusip": [r["cusip"] for r in rows], "callable": False, "available_at": AS_OF})
    p = {"bond_panel": pd.DataFrame(rows), "treasury_curve": tsy_panel(), "bond_terms": bullets}
    pas = f6.compute(p, AS_OF)
    assert (pas["tier"] == "issuer").all()
    g = f6.compute(p, AS_OF, measure="g_spread")
    assert pas["pas"].max() - pas["pas"].min() < 0.0002
    assert pas["resid"].abs().max() < 0.0002
    assert g["resid"].abs().max() > 5 * pas["resid"].abs().max()
    hi = g.set_index("cusip")["resid"][["C1", "C3", "C5"]]
    assert (hi > 0).all()          # yield-based spread makes the high-coupon bonds look cheap (Martin p. 9)


# ---------------------------------------------------------------- tiers and edge cases


def group_panels():
    rows = []
    for k in range(5):                                  # five peer issuers, two bonds each, same slope
        rows += issuer_rows(f"P{k}", [3.0, 9.0], curve([3.0, 9.0], a0=0.03 + 0.004 * k, a1=0.02), [0.06, 0.06])
    s = curve([2.0, 5.0, 8.0], a0=0.045, a1=0.02)
    s[1] += 0.0060
    rows += issuer_rows("G", [2.0, 5.0, 8.0], s, [0.06] * 3)
    rows += issuer_rows("S", [6.0], curve([6.0]), [0.06])
    return {"bond_panel": pd.DataFrame(rows), "treasury_curve": tsy_panel()}


def test_group_shape_tier_and_single_tier():
    out = f6.compute(group_panels(), AS_OF).set_index("cusip")
    assert (out.loc[["G0", "G1", "G2"], "tier"] == "group_shape").all()
    assert out.at["G1", "resid"] == pytest.approx(0.0060, abs=0.0006)
    assert out.at["G1", "score"] > 0 and out.at["G0", "score"] < 0
    assert out.at["S0", "tier"] == "single" and np.isnan(out.at["S0", "score"])


def test_group_shape_without_enough_peers_has_no_score():
    p = group_panels()
    p["bond_panel"] = p["bond_panel"][~p["bond_panel"]["gvkey"].isin(["P0", "P1"])]
    out = f6.compute(p, AS_OF).set_index("cusip")
    assert out.loc[["G0", "G1", "G2"], "score"].isna().all()


def test_missing_treasury_curve_uses_panel_yields():
    p = base_panels()
    out = f6.compute({"bond_panel": p["bond_panel"]}, AS_OF)
    ref = f6.compute(p, AS_OF)
    assert (out["curve_source"] == "bond_panel").all() and (ref["curve_source"] == "treasury_curve").all()
    np.testing.assert_allclose(out["score"], ref["score"], atol=1e-6)


def test_call_proxy_drops_premium_bond_without_terms():
    p = base_panels()
    bp = p["bond_panel"]
    extra = bond_row("A9", "A", 6.0, 110.0, 0.06)        # 110 >= 100 x (1 + 0.03): trades to the call
    p["bond_panel"] = pd.concat([bp, pd.DataFrame([extra])], ignore_index=True)
    out = f6.compute(p, AS_OF).set_index("cusip")
    assert out.at["A9", "call_status"] == "proxy_itm" and out.at["A9", "status"] == "call"
    assert np.isnan(out.at["A9", "score"])
    assert out.at["A0", "call_status"] == "unknown"


def test_bond_terms_itm_drop_seniority_split_and_bullets_only():
    p = base_panels()
    cus = p["bond_panel"]["cusip"].tolist()
    terms = pd.DataFrame({"cusip": cus, "seniority": ["senior_unsecured"] * 6,
                          "callable": [True, False, False, False, False, False],
                          "call_price": [50.0, np.nan, np.nan, np.nan, np.nan, np.nan],
                          "available_at": AS_OF})
    out = f6.compute({**p, "bond_terms": terms}, AS_OF).set_index("cusip")
    assert out.at["A0", "call_status"] == "itm" and np.isnan(out.at["A0", "score"])
    assert (out.loc[cus[1:], "call_status"] == "bullet").all()
    assert (out.loc[cus[1:], "tier"] == "issuer").all() and out.at["A1", "n_curve"] == 5
    split = terms.assign(seniority=["secured"] * 3 + ["senior_unsecured"] * 3, callable=False)
    out2 = f6.compute({**p, "bond_terms": split}, AS_OF).set_index("cusip")
    assert (out2["tier"] == "group_shape").all() and (out2["n_curve"] == 3).all()
    assert out2["score"].isna().all()                    # no peer issuers in the cell: no slope, no score
    otm = terms.assign(call_price=[200.0] + [np.nan] * 5)
    out3 = f6.compute({**p, "bond_terms": otm}, AS_OF, bullets_only=True).set_index("cusip")
    assert out3.at["A0", "call_status"] == "otm" and out3.at["A0", "status"] == "call"


def test_nan_price_and_late_terms_are_ignored():
    p = base_panels()
    bp = p["bond_panel"].copy()
    bp.loc[0, "price"] = np.nan
    late_terms = pd.DataFrame({"cusip": bp["cusip"], "seniority": "secured", "callable": True,
                               "call_price": 1.0, "available_at": AS_OF + pd.Timedelta(10, unit="D")})
    out = f6.compute({**p, "bond_panel": bp, "bond_terms": late_terms}, AS_OF)
    assert "A0" not in set(out["cusip"]) and len(out) == 5
    assert (out["seniority"] == "unknown").all()


def test_rating_sets_recovery():
    p = base_panels()
    ratings = pd.DataFrame({"gvkey": ["A"], "datadate": [AS_OF - pd.Timedelta(10, unit="D")],
                            "splticrm": ["BB"], "available_at": [AS_OF - pd.Timedelta(9, unit="D")]})
    out = f6.compute({**p, "ratings": ratings}, AS_OF)
    assert out["recovery"].iloc[0] == pytest.approx(0.34)
    assert f6.compute(p, AS_OF)["recovery"].iloc[0] == pytest.approx(0.25)    # no class: B, 25%


def test_score_is_residual_times_forward_rpv01():
    out = f6.compute(base_panels(), AS_OF, horizon_months=2).set_index("cusip")
    r = out.loc["A3"]
    fwd = f6.flat_hazard_legs(7.0 - 2 / 12, r["hazard"], flat_disc())["pi"]
    assert r["score"] == pytest.approx(r["resid"] * fwd, rel=1e-9)


# ---------------------------------------------------------------- formula helpers


def test_recovery_and_notch_match_martin_p19():
    assert f6.rating_notch("BBB-") == 10 and f6.rating_notch("AA") == 3 and f6.rating_notch("D") == 22
    assert f6.rating_notch("NR") is None
    for sym, rec in (("BBB-", 0.40), ("AA", 0.61), ("BB", 0.34), ("B", 0.25)):
        assert f6.recovery_rate(f6.rating_notch(sym)) == pytest.approx(rec)


def test_shock_basis_hand_value():
    assert f6.shock_basis(2.5) == pytest.approx(1 - np.exp(-1.0))       # lam T = 1
    assert f6.shock_basis(1e-8) == pytest.approx(1.0)


def test_discount_factors_flat_par_curve():
    grid, b = f6.discount_factors(pd.Series({t: 0.04 for t in TENORS}))
    assert b[0] == 1.0
    assert b[grid == 1.0][0] == pytest.approx(1.02 ** -2)
    assert b[grid == 10.0][0] == pytest.approx(1.02 ** -20)


def martin_disc():
    """Martin p. 8 footnote 9: USD zero rates 0 to 10y (semiannual, %), linear in between, flat beyond."""
    zr = np.array([0.65, 0.74, 0.85, 0.94, 1.05, 1.15, 1.26, 1.37, 1.46, 1.55, 1.55]) / 100
    return lambda t: (1 + np.interp(t, np.arange(11.0), zr) / 2) ** (-2 * np.asarray(t, float))


def test_par_adjusted_spread_reproduces_martin_colom_example():
    disc = martin_disc()
    a = f6.par_adjusted_spread(100.10, 0.04, 7.88, 0.0, disc)
    b = f6.par_adjusted_spread(125.50, 0.08125, 8.11, 0.0, disc)
    assert a["pas"] == pytest.approx(0.0258, abs=0.0001)       # p. 15: 258 bp
    assert b["pas"] == pytest.approx(0.0298, abs=0.0003)       # p. 15: 298 bp
    assert b["pas"] - a["pas"] == pytest.approx(0.0040, abs=0.0003)
    a, b = (f6.par_adjusted_spread(100.10, 0.04, 7.88, 0.555, disc),
            f6.par_adjusted_spread(125.50, 0.08125, 8.11, 0.555, disc))
    assert a["hazard"] == pytest.approx(b["hazard"], abs=0.0005)   # p. 10 table: one hazard near R = 55.5%
    assert a["pas"] == pytest.approx(0.0260, abs=0.0002)          # p. 15: both 260 bp


def test_par_adjusted_spread_identity_and_bounds():
    disc = flat_disc()
    r = f6.par_adjusted_spread(85.0, 0.07, 6.0, 0.25, disc)
    g = f6.flat_hazard_legs(6.0, r["hazard"], disc)
    assert r["pas"] == pytest.approx((1 - 0.25) * g["xi"] / g["pi"], abs=1e-9)    # eq. 7 with Phat = P
    assert g["bq"] + g["xi"] + g["r_pi"] == pytest.approx(1.0, abs=1e-12)          # parity eq. 8
    assert f6.par_adjusted_spread(10.0, 0.07, 6.0, 0.25, disc)["status"] == "below_recovery"
    rich = f6.par_adjusted_spread(150.0, 0.07, 6.0, 0.25, disc)
    assert rich["hazard"] == 0.0 and rich["pas"] < 0
    assert f6.par_adjusted_spread(np.nan, 0.07, 6.0, 0.25, disc)["status"] == "no_price"


def test_loo_curve_exact_and_hand():
    T = np.array([1.0, 3.0, 5.0, 8.0, 12.0])
    fit, se = f6.loo_curve(T, curve(T))
    np.testing.assert_allclose(fit, curve(T), atol=1e-12)
    np.testing.assert_allclose(se, 0.0, atol=1e-12)
    s = curve(T) + np.array([0, 0, 0.01, 0, 0])
    fit, _ = f6.loo_curve(T, s)
    assert fit[2] == pytest.approx(curve(T)[2], abs=1e-12)        # bond 2 does not shape its own curve
    x = f6.shock_basis(T)
    keep = np.arange(5) != 0
    a1, a0 = np.polyfit(x[keep], s[keep], 1)
    assert fit[0] == pytest.approx(a0 + a1 * x[0])


def test_within_slope_hand():
    x = np.array([0.9, 0.5, 0.8, 0.4, 0.7])
    s = np.array([0.050, 0.042, 0.030, 0.022, 0.100])
    a1, se, n = f6.within_slope(x, s, np.array(["a", "a", "b", "b", "c"]))
    assert n == 2 and a1 == pytest.approx(0.02) and se == pytest.approx(0.0, abs=1e-12)


def test_call_status_cases():
    assert f6.call_status(104.0, 0.08, None, np.nan) == "proxy_itm"
    assert f6.call_status(103.9, 0.08, None, np.nan) == "unknown"
    assert f6.call_status(104.0, 0.08, True, 104.0) == "itm"
    assert f6.call_status(103.0, 0.08, True, 104.0) == "otm"
    assert f6.call_status(130.0, 0.08, False, np.nan) == "bullet"
