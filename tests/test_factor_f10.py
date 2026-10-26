"""F10 market-neutral carry: contract, no look-ahead, carry and roll-down hand checks, curve tiers, the WLS hedge
(X'W e = 0, equal weights = neutralise, pure-beta carry has no residual), sign, the beta option, edge cases."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from hy.factors import f10_market_neutral_carry as f10
from hy.factors.f06_issuer_curve_residual import shock_basis
from hy.signals import neutralise

AS_OF = pd.Timestamp("2012-12-31")
MONTHS = pd.date_range(end=AS_OF, periods=30, freq="ME")
DAY = pd.Timedelta(1, unit="D")
H = 1.0 / 12.0


def _bond(cusip, gvkey, years=5.0, spread=0.05, mod_dur=4.0, rets=None, months=MONTHS) -> pd.DataFrame:
    """Rows per month end. Coupon 0 and Treasury yield 0, so the excess return is the price return."""
    rets = np.zeros(len(months)) if rets is None else np.asarray(rets, float)
    price = 100.0 * np.cumprod(1.0 + np.r_[0.0, rets[1:]])
    return pd.DataFrame({"date": months, "cusip": cusip, "gvkey": gvkey, "years": years, "g_spread": spread,
                         "price": price, "yield": 0.08, "coupon": 0.0, "maturity": AS_OF + pd.DateOffset(years=5),
                         "mod_dur": mod_dur, "tsy_yield": 0.0, "bid_ask_pts": 0.5, "n_trades": 5,
                         "par_volume": 1e6, "carried": False, "accrue_to": months, "hedge_date": months,
                         "available_at": months + DAY})


def _ratings(gvkeys, symbol="B", over=None) -> pd.DataFrame:
    return pd.DataFrame([{"gvkey": g, "datadate": m, "splticrm": (over or {}).get(g, symbol), "available_at": m + DAY}
                         for g in gvkeys for m in MONTHS[-3:]])


def _universe(n=40, seed=0, flat_dur=False, curve_issuer=False, over=None) -> dict:
    """n single-bond issuers with random spreads, durations and maturities. Option: issuer Z with three bonds on a
    steep upward curve (spreads 3%, 5%, 7% at 2, 5, 8 years)."""
    rng = np.random.default_rng(seed)
    rows = [_bond(f"C{i}", f"G{i}", years=float(rng.uniform(2, 10)), spread=float(rng.uniform(0.02, 0.09)),
                  mod_dur=4.0 if flat_dur else float(rng.uniform(2, 7))) for i in range(n)]
    g = [f"G{i}" for i in range(n)]
    if curve_issuer:
        rows += [_bond(f"Z{k}", "Z", years=t, spread=s, mod_dur=4.0) for k, (t, s) in
                 enumerate([(2.0, 0.03), (5.0, 0.05), (8.0, 0.07)])]
        g.append("Z")
    return {"bond_panel": pd.concat(rows, ignore_index=True), "ratings": _ratings(g, over=over)}


# ---------------------------------------------------------------- 1. contract


def test_meta_and_columns():
    for k in ("rank", "name", "level", "horizon_months", "needs", "spec", "section"):
        assert k in f10.META
    assert f10.META["rank"] == 10 and f10.META["level"] == "bond"
    out = f10.compute(_universe(), AS_OF)
    assert list(out.columns) == f10.COLS
    assert out["cusip"].is_unique and len(out) == 40
    assert (out["date"] == AS_OF).all() and (out["available_at"] == AS_OF + DAY).all()
    assert out["score"].notna().all()


# ---------------------------------------------------------------- 2. no look-ahead


def test_no_lookahead():
    base = _universe(curve_issuer=True)
    ref = f10.compute(base, AS_OF)
    late = base["bond_panel"].copy()
    future = late[late["date"] == AS_OF].assign(date=AS_OF + pd.offsets.MonthEnd(1), g_spread=0.5,
                                                available_at=AS_OF + pd.offsets.MonthEnd(1) + DAY)
    restated = late[late["date"] == AS_OF].assign(g_spread=0.09, years=3.0, available_at=AS_OF + 5 * DAY)
    r_late = pd.DataFrame([{"gvkey": "G0", "datadate": AS_OF, "splticrm": "CCC", "available_at": AS_OF + 3 * DAY}])
    panels = {"bond_panel": pd.concat([late, future, restated], ignore_index=True),
              "ratings": pd.concat([base["ratings"], r_late], ignore_index=True)}
    pd.testing.assert_frame_equal(f10.compute(panels, AS_OF), ref)


# ---------------------------------------------------------------- 3. formula helpers


def test_spread_carry_hand():
    assert f10.spread_carry(0.06, H) == pytest.approx(0.005)


def test_curve_slope_recovers_a1():
    T = np.array([2.0, 5.0, 8.0, 10.0])
    s = 0.04 - 0.03 * shock_basis(T)
    assert f10.curve_slope(T, s) == pytest.approx(-0.03)
    assert np.isnan(f10.curve_slope(np.array([5.0, 5.0]), np.array([0.04, 0.05])))


def test_roll_down_hand():
    # D 4, T 5, a1 -0.02: roll = -4 (-0.02) (x(5 - 1/12) - x(5)), x(T) = (1 - e^-0.4T) / (0.4T)
    x = lambda t: (1 - np.exp(-0.4 * t)) / (0.4 * t)  # noqa: E731
    want = -4.0 * -0.02 * (x(5 - H) - x(5.0))
    got = f10.roll_down(np.array([4.0]), np.array([5.0]), np.array([-0.02]), H)[0]
    assert got == pytest.approx(want) and got > 0          # upward curve: positive roll
    assert f10.roll_down(np.array([4.0]), np.array([5.0]), np.array([np.nan]), H)[0] == 0.0   # flat


def test_wls_residual_orthogonal_and_pure_beta():
    rng = np.random.default_rng(1)
    X = np.column_stack([np.ones(50), rng.uniform(0.05, 0.5, 50), rng.uniform(2, 7, 50)])
    w = rng.uniform(1, 10, 50)
    c = rng.normal(0.004, 0.002, 50)
    e, _ = f10.wls_residual(c, X, w)
    np.testing.assert_allclose(X.T @ (w * e), 0.0, atol=1e-12)                # X'W e = 0: the book holds no beta
    e0, k = f10.wls_residual(X @ np.array([0.001, 0.01, 0.0005]), X, w)       # carry only pays for exposures
    np.testing.assert_allclose(e0, 0.0, atol=1e-14)                          # no hedged carry (source p. 5)
    np.testing.assert_allclose(k, [0.001, 0.01, 0.0005])


def test_equal_weights_match_neutralise():
    rng = np.random.default_rng(2)
    Z = rng.normal(size=(40, 2))
    c = rng.normal(size=40)
    e, _ = f10.wls_residual(c, np.column_stack([np.ones(40), Z]), np.ones(40))
    np.testing.assert_allclose(e, neutralise(c, Z), atol=1e-12)


def test_hedge_weights_scale():
    w = f10.hedge_weights(np.array([0.2, -0.1, -0.1]), np.array([1.0, 2.0, 2.0]))
    np.testing.assert_allclose(w, [2 / 3, -2 / 3, -2 / 3])            # W e = (0.2, -0.2, -0.2), scaled to 2
    assert np.abs(w).sum() == pytest.approx(f10.GROSS)


def test_rolling_beta_hand():
    rng = np.random.default_rng(3)
    m = rng.normal(0, 0.01, 24)
    months = pd.date_range(end=AS_OF, periods=24, freq="ME")
    pairs = pd.concat([pd.DataFrame({"cusip": c, "date": months, "gap_k": 1, "r_ex": b * m})
                       for c, b in (("A", 1.5), ("B", 0.5))] +
                      [pd.DataFrame({"cusip": "C", "date": months[-5:], "gap_k": 1, "r_ex": m[-5:]})])
    # market = mean of A and B where C is absent; C enters the mean in its five months, so build the check on A, B
    beta = f10.rolling_beta(pairs[pairs["cusip"] != "C"], months)
    assert beta["A"] == pytest.approx(1.5) and beta["B"] == pytest.approx(0.5)
    assert "C" not in f10.rolling_beta(pairs, months).index                     # 5 < BETA_MIN_OBS


# ---------------------------------------------------------------- 4. curve tiers


def test_slope_tiers():
    rows = [_bond("Z0", "Z", 2.0, 0.03), _bond("Z1", "Z", 5.0, 0.05), _bond("Z2", "Z", 8.0, 0.07)]
    rows += [_bond(f"P{i}{k}", f"P{i}", t, 0.04 + 0.002 * t) for i in range(5) for k, t in enumerate((3.0, 9.0))]
    rows += [_bond("S0", "S", 5.0, 0.05)]
    p = pd.concat(rows, ignore_index=True)
    now = p[p["date"] == AS_OF].assign(rclass="B").reset_index(drop=True)
    sl = f10.slopes(now).set_index(now["cusip"])
    assert (sl.loc[["Z0", "Z1", "Z2"], "curve_source"] == "issuer").all()
    assert sl.loc["S0", "curve_source"] == "class" and sl.loc["P00", "curve_source"] == "class"
    assert sl.loc["Z0", "slope"] < 0 and sl.loc["S0", "slope"] < 0        # upward curves: a1 < 0
    flat = f10.slopes(now[now["cusip"] == "S0"].reset_index(drop=True))
    assert flat["curve_source"].iloc[0] == "flat" and np.isnan(flat["slope"].iloc[0])


# ---------------------------------------------------------------- 5. sign


def test_pure_beta_carry_has_zero_score():
    out = f10.compute(_universe(flat_dur=True), AS_OF)    # D = 4, no curves: carry = s h = h DTS / 4, all beta
    assert (out["curve_source"] == "flat").all()
    np.testing.assert_allclose(out["carry_resid"], 0.0, atol=1e-14)


def test_roll_down_carry_ranks_first():
    out = f10.compute(_universe(flat_dur=True, curve_issuer=True), AS_OF).set_index("cusip")
    top = out["score"].sort_values(ascending=False).index[:3]
    assert set(top) == {"Z0", "Z1", "Z2"}
    assert (out.loc[["Z0", "Z1", "Z2"], "roll"] > 0).all()
    assert (out.loc[["Z0", "Z1", "Z2"], "w_opt"] > 0).all()


def test_book_is_neutral():
    out = f10.compute(_universe(seed=4, over={"G1": "BB", "G2": "CCC", "G3": "BB", "G4": "CCC"}), AS_OF)
    d = out[out["status"] == "ok"]
    X = np.column_stack([np.ones(len(d)), d["dts"], d["mod_dur"], d["rclass"] == "B", d["rclass"] == "CCC"])
    np.testing.assert_allclose(X.astype(float).T @ d["w_opt"].to_numpy(float), 0.0, atol=1e-10)
    assert np.abs(d["w_opt"]).sum() == pytest.approx(f10.GROSS)


def test_beta_option():
    rng = np.random.default_rng(5)
    f = rng.normal(0, 0.01, len(MONTHS))
    rows = [_bond(f"C{i}", f"G{i}", years=float(rng.uniform(2, 10)), spread=float(rng.uniform(0.02, 0.09)),
                  mod_dur=float(rng.uniform(2, 7)), rets=(0.5 + i / 20) * f + rng.normal(0, 0.002, len(MONTHS)))
            for i in range(40)]
    panels = {"bond_panel": pd.concat(rows, ignore_index=True), "ratings": _ratings([f"G{i}" for i in range(40)])}
    out = f10.compute(panels, AS_OF, market="beta")
    assert out["beta_ts"].notna().all() and out["score"].notna().all()
    assert out.set_index("cusip")["beta_ts"].corr(pd.Series({f"C{i}": 0.5 + i / 20 for i in range(40)})) > 0.95
    X = np.column_stack([np.ones(40), out["beta_ts"], out["mod_dur"]])
    np.testing.assert_allclose(X.T @ out["w_opt"].to_numpy(float), 0.0, atol=1e-10)
    both = f10.compute(panels, AS_OF, market="both")
    assert both["score"].notna().all()


# ---------------------------------------------------------------- 6. edge cases


def test_missing_panels_give_empty_frame():
    u = _universe()
    for k in ("bond_panel", "ratings"):
        out = f10.compute({kk: v for kk, v in u.items() if kk != k}, AS_OF)
        assert out.empty and list(out.columns) == f10.COLS
    assert f10.compute({**u, "ratings": u["ratings"].iloc[:0]}, AS_OF).empty


def test_few_bonds_no_score():
    out = f10.compute(_universe(n=10), AS_OF)
    assert (out["status"] == "few_bonds").all() and out["score"].isna().all()
    assert out["carry"].notna().all()


def test_universe_filters():
    u = _universe()
    p = u["bond_panel"].copy()
    at = p["date"] == AS_OF
    p.loc[at & (p["cusip"] == "C0"), "g_spread"] = 0.15           # distressed: out
    p.loc[at & (p["cusip"] == "C1"), "carried"] = True            # carried row: out
    p.loc[at & (p["cusip"] == "C2"), "mod_dur"] = np.nan          # no duration: not eligible
    r = _ratings([f"G{i}" for i in range(40)], over={"G3": "D", "G4": "BBB"})
    out = f10.compute({"bond_panel": p, "ratings": r}, AS_OF)
    assert not set(out["cusip"]) & {"C0", "C1", "C2", "C3", "C4"}
    assert len(out) == 35


def test_bad_option_raises():
    with pytest.raises(ValueError):
        f10.compute(_universe(), AS_OF, market="pca")
