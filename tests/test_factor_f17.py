"""F17 bond return skewness: contract, no look-ahead, skew sign, minimum count, screen, missing panel, reuse of the
F01 definition and the formula helpers."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from scipy.stats import skew as sp_skew

from hy.backtest import decision_time
from hy.factors import f01_ipca as f01
from hy.factors import f17_return_skewness as f17

AS_OF = pd.Timestamp("2012-12-31")
MONTHS = pd.date_range(end=AS_OF, periods=64, freq="ME")       # 2007-09 .. 2012-12
DAY = pd.Timedelta(1, unit="D")
N = 6


def _bond(cusip: str, rets, g_spread: float = 0.05, months: pd.DatetimeIndex = MONTHS) -> pd.DataFrame:
    """Rows per month end. Coupon 0 and Treasury yield 0, so r~ is the price return: P_m = P_m-1 (1 + r_m)."""
    rets = np.asarray(rets, float)
    price = 100.0 * np.cumprod(1.0 + np.r_[0.0, rets[1:]])
    return pd.DataFrame({"date": months, "cusip": cusip, "gvkey": "G" + cusip, "years": 5.0, "g_spread": g_spread,
                         "price": price, "yield": 0.08, "coupon": 0.0, "maturity": AS_OF + pd.DateOffset(years=5),
                         "mod_dur": 4.0, "tsy_yield": 0.0, "bid_ask_pts": 0.5, "n_trades": 5, "par_volume": 1e6,
                         "carried": False, "accrue_to": months, "hedge_date": months,
                         "available_at": months + DAY})


def _rets(seed: int, sd: float = 0.01, n: int = len(MONTHS)) -> np.ndarray:
    return np.random.default_rng(seed).normal(0.003, sd, n)


def _universe(n: int = N, shocks: dict | None = None) -> dict:
    """n bonds. `shocks` maps a bond index to (month index, return) overrides."""
    bonds = []
    for i in range(n):
        r = _rets(i)
        for m, v in (shocks or {}).get(i, []):
            r[m] = v
        bonds.append(_bond(f"C{i}", r))
    return {"bond_panel": pd.concat(bonds, ignore_index=True)}


def _run(panels, as_of=AS_OF) -> pd.DataFrame:
    return f17.compute(panels, as_of).set_index("cusip")


# ---------------------------------------------------------------- 1. contract


def test_meta_keys():
    for k in ("rank", "name", "level", "horizon_months", "needs", "spec", "section"):
        assert k in f17.META
    assert f17.META["rank"] == 17 and f17.META["level"] == "bond" and f17.META["needs"] == ["bond_panel"]


def test_columns_and_one_row_per_cusip():
    out = f17.compute(_universe(), AS_OF)
    assert list(out.columns) == f17.COLS
    assert out["cusip"].is_unique and len(out) == N
    assert (out["date"] == AS_OF).all() and (out["available_at"] == decision_time(AS_OF)).all()
    assert out["score"].notna().all()
    assert (out["n_ret"] == f01.SKEW_MONTHS).all()


# ---------------------------------------------------------------- 2. no look-ahead


def test_no_lookahead():
    base = _universe()
    ref = _run(base)
    later = pd.date_range(AS_OF + pd.offsets.MonthEnd(1), periods=3, freq="ME")
    fut = pd.concat([_bond(f"C{i}", np.full(3, -0.3), months=later) for i in range(N)])
    revised = base["bond_panel"][base["bond_panel"]["date"] == AS_OF - pd.offsets.MonthEnd(1)].copy()
    revised["price"] *= 0.5
    revised["available_at"] = decision_time(AS_OF) + DAY
    p = {"bond_panel": pd.concat([base["bond_panel"], fut, revised], ignore_index=True)}
    pd.testing.assert_frame_equal(_run(p), ref)


# ---------------------------------------------------------------- 3. sign


def test_left_skew_scores_above_right_skew():
    out = _run(_universe(shocks={0: [(40, -0.15)], 1: [(40, 0.15)]}))
    assert out.loc["C0", "bond_skew"] < 0 < out.loc["C1", "bond_skew"]
    assert out.loc["C0", "score"] > out.loc["C1", "score"]
    assert out["score"].idxmax() == "C0" and out["score"].idxmin() == "C1"
    assert out.loc["C0", "rank"] == pytest.approx(-0.5) and out.loc["C1", "rank"] == pytest.approx(0.5)


# ---------------------------------------------------------------- 4. edge cases


def test_missing_panel_gives_empty_frame():
    for panels in ({}, {"bond_panel": pd.DataFrame()}):
        out = f17.compute(panels, AS_OF)
        assert out.empty and list(out.columns) == f17.COLS


def test_short_history_gives_nan():
    short = pd.date_range(end=AS_OF, periods=f01.SKEW_MIN, freq="ME")      # 23 returns, one below the minimum
    p = _universe()
    p["bond_panel"] = pd.concat([p["bond_panel"], _bond("NEW", _rets(99, n=len(short)), months=short)])
    out = _run(p)
    assert out.loc["NEW", "n_ret"] == f01.SKEW_MIN - 1
    assert np.isnan(out.loc["NEW", "score"]) and np.isnan(out.loc["NEW", "rank"])
    assert out.drop("NEW")["score"].notna().all()


def test_screen_drops_wide_spread():
    p = _universe()
    p["bond_panel"] = pd.concat([p["bond_panel"], _bond("WIDE", _rets(7), g_spread=0.25)])
    assert "WIDE" not in _run(p).index


def test_constant_returns_give_nan():
    p = _universe()
    p["bond_panel"] = pd.concat([p["bond_panel"], _bond("FLAT", np.zeros(len(MONTHS)))])
    out = _run(p)
    assert np.isnan(out.loc["FLAT", "score"])


def test_window_is_sixty_months():
    """A shock 61 end months back leaves the window and so changes no score."""
    ref = _run(_universe())
    out = _run(_universe(shocks={0: [(2, -0.4)]}))           # end month index 2 = AS_OF - 61 months
    pd.testing.assert_frame_equal(out, ref)


# ---------------------------------------------------------------- 5. helpers


def test_skew_matches_hand_g1_and_f01():
    r = _rets(3)
    r[30] = -0.12
    p = {"bond_panel": _bond("C0", r)}
    got = _run(p).loc["C0", "bond_skew"]
    x = r[-f01.SKEW_MONTHS:]                                  # returns that end in the last 60 month ends
    n = len(x)
    d = x - x.mean()
    g1 = (d ** 3).mean() / (d ** 2).mean() ** 1.5
    hand = np.sqrt(n * (n - 1)) / (n - 2) * g1
    assert got == pytest.approx(hand, rel=1e-8)
    assert got == pytest.approx(sp_skew(x, bias=False), rel=1e-8)
    chars = f01.characteristics({"bond_panel": p["bond_panel"]}, AS_OF)
    assert got == pytest.approx(chars.loc[chars["date"] == AS_OF, "bond_skew"].iloc[0], rel=1e-12)


def test_skew_score_flips_sign_and_keeps_nan():
    s = f17.skew_score(pd.Series([0.5, -1.2, np.nan]))
    assert s.iloc[0] == -0.5 and s.iloc[1] == 1.2 and np.isnan(s.iloc[2])
