"""F16 bond downside risk: contract, no look-ahead, tail sign, rating and S1 control, minimum count, gaps, defaulted
issuers, missing panels and the formula helpers."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from hy.backtest import decision_time
from hy.factors import f16_downside_risk as f16

AS_OF = pd.Timestamp("2012-12-31")
MONTHS = pd.date_range(end=AS_OF, periods=40, freq="ME")       # 2009-09 .. 2012-12
WIN = pd.date_range(end=AS_OF, periods=36, freq="ME")          # 2010-01 .. 2012-12
DAY = pd.Timedelta(1, unit="D")
N = 24


def _bond(cusip: str, gvkey: str, rets, mod_dur: float = 4.0, drop=()) -> pd.DataFrame:
    """Rows per month end. Coupon 0 and Treasury yield 0, so r_ex is the price return: P_m = P_m-1 (1 + r_m)."""
    rets = np.asarray(rets, float)
    price = 100.0 * np.cumprod(1.0 + np.r_[0.0, rets[1:]])
    df = pd.DataFrame({"date": MONTHS, "cusip": cusip, "gvkey": gvkey, "years": 5.0, "g_spread": 0.05,
                       "price": price, "yield": 0.08, "coupon": 0.0, "maturity": AS_OF + pd.DateOffset(years=5),
                       "mod_dur": mod_dur, "tsy_yield": 0.0, "bid_ask_pts": 0.5, "n_trades": 5,
                       "par_volume": 1e6, "carried": False, "accrue_to": MONTHS, "hedge_date": MONTHS,
                       "available_at": MONTHS + DAY})
    return df[~df["date"].isin(pd.DatetimeIndex(drop))].reset_index(drop=True)


def _ratings(over: dict | None = None, n: int = N, symbol: str = "B") -> pd.DataFrame:
    rows = [{"gvkey": f"G{i}", "datadate": m, "splticrm": (over or {}).get(f"G{i}", symbol), "available_at": m + DAY}
            for i in range(n) for m in MONTHS]
    return pd.DataFrame(rows)


def _rets(rng, sd: float = 0.01) -> np.ndarray:
    return rng.normal(0.003, sd, len(MONTHS))


def _universe(n: int = N, seed: int = 0, shocks: dict | None = None, rating_over: dict | None = None) -> dict:
    """n bonds. `shocks` maps a bond index to a list of (month index, return) overrides."""
    rng = np.random.default_rng(seed)
    bonds = []
    for i in range(n):
        r = _rets(rng)
        for m, v in (shocks or {}).get(i, []):
            r[m] = v
        bonds.append(_bond(f"C{i}", f"G{i}", r, mod_dur=3.0 + 0.1 * i))
    return {"bond_panel": pd.concat(bonds, ignore_index=True), "ratings": _ratings(rating_over, n)}


def _run(panels, **kw) -> pd.DataFrame:
    return f16.compute(panels, AS_OF, **kw).set_index("cusip")


# ---------------------------------------------------------------- 1. contract


def test_meta_and_columns():
    for k in ("rank", "name", "level", "horizon_months", "needs", "spec", "section"):
        assert k in f16.META
    assert f16.META["rank"] == 16 and f16.META["level"] == "bond" and f16.META["horizon_months"] == 1
    out = f16.compute(_universe(), AS_OF)
    assert list(out.columns) == f16.COLS
    assert out["cusip"].is_unique and len(out) == N
    assert (out["date"] == AS_OF).all() and (out["available_at"] == decision_time(AS_OF)).all()
    assert (out["n_ret"] == 36).all() and (out["ctrl"] == "rating+dur").all()
    assert out["score"].notna().all() and abs(out["score"].mean()) < 1e-9
    assert out["score"].rank().tolist() == out["var5_ctrl"].rank().tolist()


# ---------------------------------------------------------------- 2. no look-ahead


def test_later_rows_and_late_revisions_do_not_change_score():
    base = _universe()
    ref = _run(base)
    p = base["bond_panel"]
    later = p[p["date"] == AS_OF].copy()
    later["date"] = AS_OF + pd.offsets.MonthEnd(1)
    later["available_at"] = later["date"] + DAY
    late_rev = p[p["date"] == WIN[-3]].copy()
    late_rev["price"] *= 0.5                                     # a crash print known only after the decision time
    late_rev["available_at"] = AS_OF + pd.Timedelta(10, unit="D")
    late_rating = _ratings({"G0": "D"}).query("gvkey == 'G0'").assign(available_at=AS_OF + pd.Timedelta(5, unit="D"))
    late_s1 = pd.DataFrame({"date": AS_OF, "cusip": ["C0"], "z": [3.0], "available_at": AS_OF + pd.Timedelta(3, unit="D")})
    panels = {**base, "bond_panel": pd.concat([p, later, late_rev], ignore_index=True),
              "ratings": pd.concat([base["ratings"], late_rating], ignore_index=True), "s1_residual": late_s1}
    got = _run(panels)
    assert (got["ctrl"] == "rating+dur").all()                   # the late S1 row is not known: no z in the control
    pd.testing.assert_frame_equal(got, ref)


# ---------------------------------------------------------------- 3. sign


def test_bond_with_two_bad_months_has_highest_var5_and_score():
    out = _run(_universe(shocks={5: [(10, -0.08), (20, -0.09)]}))
    assert out["var5"].idxmax() == "C5"
    assert out.loc["C5", "var5"] == pytest.approx(0.08, abs=1e-9)  # second lowest of 36, sign flipped
    assert out.loc["C5", "es5"] == pytest.approx(0.085, abs=1e-9)
    assert out["score"].idxmax() == "C5"


def test_rating_control_removes_a_pure_class_effect():
    # CCC bonds have a large tail, BB and B bonds a small one: VaR5 is a rating proxy only
    over = {f"G{i}": ("CCC" if i < 8 else "BB" if i < 16 else "B") for i in range(N)}
    shocks = {i: [(10, -0.10), (20, -0.10)] for i in range(8)}
    out = _run(_universe(shocks=shocks, rating_over=over))
    ccc = out[out["rclass"] == "CCC"]
    assert ccc["var5"].min() > out[out["rclass"] != "CCC"]["var5"].max()
    assert abs(ccc["var5_ctrl"].mean()) < 1e-12                 # the class dummy takes the CCC tail
    assert ccc["var5"].mean() - out["var5"].mean() > 0.05
    assert out["var5_ctrl"].abs().max() < 0.01                  # what is left is noise, not class


def test_s1_residual_enters_the_control():
    # VaR5 = 0.05 + 0.004 (i mod 5): not a duration effect, but z = i mod 5 explains it in full
    base = _universe(shocks={i: [(10, -0.05 - 0.004 * (i % 5)), (20, -0.05 - 0.004 * (i % 5))] for i in range(N)})
    z = pd.DataFrame({"date": AS_OF, "cusip": [f"C{i}" for i in range(N)], "z": np.arange(N, dtype=float) % 5,
                      "available_at": decision_time(AS_OF)})
    no_s1 = _run(base)
    with_s1 = _run({**base, "s1_residual": z})
    assert (with_s1["ctrl"] == "rating+dur+s1").all()
    assert with_s1.loc["C3", "s1_z"] == 3.0 and np.isnan(no_s1.loc["C3", "s1_z"])
    assert no_s1["var5_ctrl"].abs().max() > 1e-3
    assert with_s1["var5_ctrl"].abs().max() < 1e-9
    pd.testing.assert_series_equal(with_s1["var5"], no_s1["var5"])


# ---------------------------------------------------------------- 4. edge cases


def test_missing_required_panels_give_empty_frame():
    u = _universe()
    for k in ("bond_panel", "ratings"):
        out = f16.compute({**{j: v for j, v in u.items() if j != k}}, AS_OF)
        assert out.empty and list(out.columns) == f16.COLS


def test_short_history_gives_nan_and_gaps_do_not_enter():
    u = _universe()
    p = u["bond_panel"]
    drop0 = WIN[:14]                                              # C0 keeps 22 months of the window: below 24
    drop1 = WIN[[5, 15]]                                          # C1 loses 4 monthly pairs to two one-month gaps
    p = p[~((p["cusip"] == "C0") & p["date"].isin(drop0)) & ~((p["cusip"] == "C1") & p["date"].isin(drop1))]
    out = _run({**u, "bond_panel": p})
    assert out.loc["C0", "n_ret"] < f16.MIN_OBS and np.isnan(out.loc["C0", "var5"]) and np.isnan(out.loc["C0", "score"])
    assert out.loc["C1", "n_ret"] == 32 and np.isfinite(out.loc["C1", "score"])


def test_defaulted_issuer_is_not_scored_and_small_cross_section_gives_nan():
    out = _run(_universe(rating_over={"G2": "D"}))
    assert "C2" not in out.index
    small = _run(_universe(n=10))
    assert small["var5"].notna().all() and small["score"].isna().all()


def test_stale_rows_drop_out():
    u = _universe()
    p = u["bond_panel"].copy()
    m = (p["cusip"] == "C4") & p["date"].isin(WIN[-14:])
    p.loc[m, "price"] = 95.0                                      # a flat print each month: stale after the first
    p.loc[m, "n_trades"] = 1
    out = _run({**u, "bond_panel": p})
    assert out.loc["C4", "n_ret"] < f16.MIN_OBS and np.isnan(out.loc["C4", "score"])


# ---------------------------------------------------------------- 5. helpers


def test_tail_count_gives_source_ranks_at_36():
    assert f16.tail_count(36, f16.Q5) == 2 and f16.tail_count(36, f16.Q10) == 4
    assert f16.tail_count(24, f16.Q5) == 1 and f16.tail_count(24, f16.Q10) == 2 and f16.tail_count(5, 0.05) == 1


def test_var_and_es_by_hand():
    r = np.r_[np.full(30, 0.01), -0.05, -0.04, -0.03, -0.02, -0.01, 0.0]   # 36 returns
    assert f16.value_at_risk(r, 0.05) == pytest.approx(0.04)                 # second lowest
    assert f16.value_at_risk(r, 0.10) == pytest.approx(0.02)                 # fourth lowest
    assert f16.expected_shortfall(r, 0.05) == pytest.approx(0.045)           # mean of -0.05, -0.04
    assert f16.expected_shortfall(r, 0.10) == pytest.approx(0.035)           # mean of the four lowest
    assert np.isnan(f16.value_at_risk(np.array([np.nan]))) and np.isnan(f16.expected_shortfall(np.array([])))


def test_control_residual_matches_ols():
    rng = np.random.default_rng(1)
    n = 30
    rc = pd.Series(np.where(np.arange(n) < 10, "BB", np.where(np.arange(n) < 20, "B", "CCC")))
    dur = pd.Series(rng.uniform(2, 8, n))
    z = pd.Series(rng.normal(size=n))
    y = pd.Series(0.01 + 0.02 * (rc == "CCC") + 0.003 * dur + 0.004 * z + rng.normal(0, 0.001, n))
    got = f16.control_residual(y, rc, dur, z)
    X = np.column_stack([np.ones(n), rc == "BB", rc == "CCC", dur, z]).astype(float)
    b, *_ = np.linalg.lstsq(X, y.to_numpy(), rcond=None)
    np.testing.assert_allclose(got.to_numpy(), y.to_numpy() - X @ b, atol=1e-12)
    assert f16.control_residual(y.iloc[:5], rc.iloc[:5], dur.iloc[:5]).isna().all()
