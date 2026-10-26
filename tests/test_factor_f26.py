"""F26 HY index trend: contract, no look-ahead, sign on tightening and widening, the step path with its cap, edge
cases (missing panel, monthly rows, short history, stale rows) and the formula helpers."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from hy.backtest import decision_time
from hy.factors import f26_index_trend as f26

AS_OF = pd.Timestamp("2015-06-30")
DAYS = pd.bdate_range(end=AS_OF, periods=300)
DAY = pd.Timedelta(1, unit="D")


def _index(spread, days: pd.DatetimeIndex = DAYS) -> pd.DataFrame:
    """hy_index rows per business day, public the next day (wiring 4.5)."""
    return pd.DataFrame({"date": days, "available_at": days + DAY, "spread": np.asarray(spread, float),
                         "distress": 0.1, "name": "test"})


def _returns(r, days: pd.DatetimeIndex = DAYS) -> pd.DataFrame:
    return pd.DataFrame({"date": days, "available_at": days + DAY, "excess_return": np.asarray(r, float)})


def _noise(seed: int = 0, n: int = len(DAYS)) -> np.ndarray:
    return np.random.default_rng(seed).normal(0.0, 0.0005, n)


def _trend(slope: float, seed: int = 0) -> np.ndarray:
    """Spread path 0.04 + slope per day + small noise."""
    return 0.04 + slope * np.arange(len(DAYS)) + _noise(seed)


def _run(panels, as_of=AS_OF) -> pd.Series:
    out = f26.compute(panels, as_of)
    assert len(out) == 1
    return out.iloc[0]


# ---------------------------------------------------------------- 1. contract


def test_meta_keys():
    for k in ("rank", "name", "level", "horizon_months", "needs", "spec", "section"):
        assert k in f26.META
    assert f26.META["rank"] == 26 and f26.META["level"] == "index"
    assert f26.META["needs"] == ["hy_index", "hy_index_return"]


def test_columns_and_one_row():
    out = f26.compute({"hy_index": _index(_trend(-1e-5))}, AS_OF)
    assert list(out.columns) == f26.COLS
    assert len(out) == 1 and out["index"].iloc[0] == "US_HY"
    r = out.iloc[0]
    assert r["date"] == AS_OF and r["available_at"] == decision_time(AS_OF)
    assert r["status"] == "ok" and r["level_source"] == "spread" and r["n_obs"] == len(DAYS)
    assert r["score"] in np.arange(-1.0, 1.01, 0.25)


# ---------------------------------------------------------------- 2. no look-ahead


def test_no_lookahead():
    base = _index(_trend(-1e-5))
    ref = f26.compute({"hy_index": base}, AS_OF)
    later_days = pd.bdate_range(AS_OF + DAY, periods=40)
    later = _index(0.20 + np.zeros(40), later_days)                       # a huge widening after as_of
    revised = base.copy()
    revised["spread"] = 0.30
    revised["available_at"] = decision_time(AS_OF) + DAY                  # a revision public too late
    out = f26.compute({"hy_index": pd.concat([base, later, revised], ignore_index=True)}, AS_OF)
    pd.testing.assert_frame_equal(ref, out)


# ---------------------------------------------------------------- 3. sign


def test_tightening_is_long_widening_is_short():
    assert _run({"hy_index": _index(_trend(-2e-5))})["score"] == 1.0
    w = _run({"hy_index": _index(_trend(2e-5))})
    assert w["score"] == -1.0 and w["jpm_signal"] == -1.0
    assert w["sg_position"] == -1.0 or w["sg_position"] == 0.0
    assert w["ema2_signal"] < 0 and w["ema2_position"] == -1.0


def test_return_series_wins_and_agrees():
    r = 0.0003 + _noise(1)                                                 # a steady gain
    out = _run({"hy_index": _index(_trend(2e-5)), "hy_index_return": _returns(r)})
    assert out["level_source"] == "excess_return"
    assert out["score"] == 1.0 and out["ema2_signal"] > 0


def test_recent_turn_steps_down():
    """60 days of tightening, then 4 days with STA below LTA: x falls from +1 by 0.25 a day to 0."""
    s = np.r_[np.linspace(0.06, 0.04, len(DAYS) - 4), np.full(4, 0.08)]
    out = _run({"hy_index": _index(s)})
    assert out["score"] == pytest.approx(0.0) and out["jpm_signal"] == -1.0


# ---------------------------------------------------------------- 4. edge cases


def test_missing_panels_give_empty_frame():
    for panels in ({}, {"hy_index": None}, {"hy_index": _index(_trend(0.0)).iloc[:0]}):
        out = f26.compute(panels, AS_OF)
        assert out.empty and list(out.columns) == f26.COLS


def test_monthly_rows_not_daily():
    months = pd.date_range(end=AS_OF, periods=72, freq="ME")
    out = _run({"hy_index": _index(np.linspace(0.06, 0.04, 72), months)})
    assert out["status"] == "not_daily" and np.isnan(out["score"])


def test_short_history_and_stale():
    short = _run({"hy_index": _index(_trend(0.0)[:30], DAYS[-30:])})
    assert short["status"] == "too_few_obs" and np.isnan(short["score"])
    old = DAYS[:200]
    stale = _run({"hy_index": _index(_trend(0.0)[:200], old)})
    assert stale["status"] == "stale" and np.isnan(stale["score"])


def test_nan_levels_dropped_and_ema2_needs_history():
    s = _trend(-2e-5)
    s[100:110] = np.nan
    out = _run({"hy_index": _index(s)})
    assert out["n_obs"] == len(DAYS) - 10 and out["score"] == 1.0
    few = _run({"hy_index": _index(_trend(-2e-5)[-100:], DAYS[-100:])})  # 99 changes < EMA_MIN_OBS
    assert few["status"] == "ok" and np.isnan(few["ema2_signal"])


# ---------------------------------------------------------------- 5. helpers


def test_moving_average_and_crossover():
    lv = pd.Series([1.0, 2, 3, 4, 5])
    assert f26.moving_average(lv, 3).tolist()[2:] == [2.0, 3.0, 4.0]
    d = f26.crossover_signal(pd.Series([np.nan, 1.0, 2.0, 2.0]), pd.Series([1.0, 1.0, 3.0, 2.0]))
    assert np.isnan(d[0]) and d[1:].tolist() == [1.0, -1.0, 1.0]          # a tie goes long (p. 120)


def test_step_exposure_hand_path():
    d = pd.Series([np.nan, 1, 1, 1, 1, 1, 1, -1, -1, 1, np.nan, -1])
    x = f26.step_exposure(d)
    want = [np.nan, 0.25, 0.5, 0.75, 1.0, 1.0, 1.0, 0.75, 0.5, 0.75, 0.75, 0.5]
    np.testing.assert_allclose(x.to_numpy(), want)


def test_sg_slope_identity_and_curvature():
    f = pd.Series(np.random.default_rng(3).normal(size=80).cumsum())
    m, n = 5, 2
    s, c = f26.sg_slope_curvature(f, m, n)
    np.testing.assert_allclose(s.dropna(), ((f - f.shift(m + 1)) / (m + 1)).dropna())          # eq. 2
    closed = (f - f.shift(m + 1) - f.shift(n + 1) + f.shift(m + n + 2)) / ((n + 1) * (m + 1))   # eq. 4, no stray sum
    np.testing.assert_allclose(c.dropna(), closed.dropna())
    pos = f26.sg_position(pd.Series([1.0, -1, 1, np.nan]), pd.Series([2.0, -2, -2, 1]))
    assert pos[:3].tolist() == [1.0, -1.0, 0.0] and np.isnan(pos[3])


def test_risk_adjusted_changes_hand():
    dx = pd.Series([np.nan, 2.0, 4.0, -2.0])
    u = f26.risk_adjusted_changes(dx, vol_n=2)
    # var: 4, 0.5*4 + 0.5*16 = 10; U_3 = 4 / 2 = 2, U_4 = -2 / sqrt(10)
    assert np.isnan(u.iloc[0])
    np.testing.assert_allclose(u.iloc[1:].to_numpy(), [2.0, -2.0 / np.sqrt(10.0)])


def test_ema2_weights_and_unit_sd():
    a, b = 1 - 1 / 20, 1 - 1 / 40
    impulse = pd.Series(np.r_[1.0, np.zeros(3999)])
    w = f26.ema2_filter(impulse, 20, 40).to_numpy()
    j = np.arange(len(w))
    np.testing.assert_allclose(w, (a ** (j + 1) - b ** (j + 1)) / (a - b), atol=1e-12)        # p. 7
    assert f26.ema2_unit_sd(20, 40) == pytest.approx(np.sqrt(np.sum(w ** 2)), rel=1e-6)        # eq. 18, M = 1
    u = pd.Series(np.random.default_rng(5).normal(size=200_000))
    z = f26.ema2_filter(u).iloc[2000:] / f26.ema2_unit_sd()
    assert z.std() == pytest.approx(1.0, abs=0.05)
