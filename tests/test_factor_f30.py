"""F30 HY spread against VIX gap: contract, no look-ahead, sign of the gap, edge cases (missing panels, missing
VIXCLS, short history, stale join, NaN rows) and the formula helpers against the source screen (p. 3)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from hy.backtest import decision_time
from hy.factors import f30_hy_vix_gap as f30

AS_OF = pd.Timestamp("2011-09-30")
DAYS = pd.bdate_range(end=AS_OF, periods=400)
DAY = pd.Timedelta(1, unit="D")
A, B = 0.0222, 0.00126   # true line in decimal per VIX point, near the 12M fit of p. 3


def _vix(seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return 20.0 + 5.0 * np.sin(np.arange(len(DAYS)) / 30.0) + rng.normal(0.0, 1.0, len(DAYS))


def _panels(last_shock: float = 0.0, seed: int = 0, days: pd.DatetimeIndex = DAYS) -> dict[str, pd.DataFrame]:
    """Spread = A + B VIX + noise, with `last_shock` added on the last date."""
    rng = np.random.default_rng(seed + 1)
    v = _vix(seed)[: len(days)]
    s = A + B * v + rng.normal(0.0, 0.002, len(days))
    s[-1] += last_shock
    hy = pd.DataFrame({"date": days, "available_at": days + DAY, "spread": s, "distress": 0.1})
    macro = pd.DataFrame({"series_id": "VIXCLS", "date": days, "value": v, "available_at": days + DAY})
    other = pd.DataFrame({"series_id": "BAMLH0A0HYM2", "date": days, "value": 5.0, "available_at": days + DAY})
    return {"hy_index": hy, "macro_series": pd.concat([macro, other], ignore_index=True)}


def _run(panels, as_of=AS_OF) -> pd.Series:
    out = f30.compute(panels, as_of)
    assert len(out) == 1
    return out.iloc[0]


# ---------------------------------------------------------------- 1. contract


def test_meta_keys():
    for k in ("rank", "name", "level", "horizon_months", "needs", "spec", "section"):
        assert k in f30.META
    assert f30.META["rank"] == 30 and f30.META["level"] == "index"
    assert f30.META["needs"] == ["hy_index", "macro_series"]


def test_columns_and_one_row():
    out = f30.compute(_panels(), AS_OF)
    assert list(out.columns) == f30.COLS and len(out) == 1
    r = out.iloc[0]
    assert r["index"] == "US_HY" and r["date"] == AS_OF and r["available_at"] == decision_time(AS_OF)
    assert r["status"] == "ok" and np.isfinite(r["score"])
    assert r["signal_date"] == DAYS[-1]
    n_window = int((DAYS > AS_OF - pd.DateOffset(months=12)).sum())
    assert r["n_obs"] == n_window
    assert r["beta"] == pytest.approx(B, rel=0.1) and r["r2"] > 0.5


# ---------------------------------------------------------------- 2. no look-ahead


def test_no_look_ahead():
    base = _run(_panels())
    p = _panels()
    late = pd.bdate_range(AS_OF + DAY, periods=20)
    p["hy_index"] = pd.concat([p["hy_index"], pd.DataFrame({"date": late, "available_at": late + DAY,
                                                            "spread": 0.5, "distress": 0.9})])
    p["macro_series"] = pd.concat([p["macro_series"], pd.DataFrame({"series_id": "VIXCLS", "date": late,
                                                                    "value": 80.0, "available_at": late + DAY})])
    # a revision of the last day published after the decision time
    p["hy_index"] = pd.concat([p["hy_index"], pd.DataFrame({"date": [DAYS[-1]], "spread": [0.9], "distress": [0.9],
                                                            "available_at": [decision_time(AS_OF) + DAY]})])
    p["macro_series"] = pd.concat([p["macro_series"], pd.DataFrame(
        {"series_id": ["VIXCLS"], "date": [DAYS[-1]], "value": [5.0], "available_at": [decision_time(AS_OF) + DAY]})])
    after = _run(p)
    for k in ("score", "alpha", "beta", "gap", "z_gap"):
        assert after[k] == pytest.approx(base[k])
    assert after["n_obs"] == base["n_obs"]


# ---------------------------------------------------------------- 3. sign


def test_sign_wide_and_tight():
    wide, tight = _run(_panels(last_shock=0.02)), _run(_panels(last_shock=-0.02))
    assert wide["score"] > 2.0 and wide["gap"] > 0
    assert tight["score"] < -2.0 and tight["gap"] < 0


def test_score_is_gap_over_resid_sd():
    r = _run(_panels(last_shock=0.01))
    assert r["score"] == pytest.approx(r["gap"] / r["resid_sd"])
    assert r["fitted"] == pytest.approx(r["alpha"] + r["beta"] * r["vix"])
    assert r["z_gap"] == pytest.approx(r["z_spread"] - r["z_vix"])


# ---------------------------------------------------------------- 4. edge cases


def test_missing_panels_give_empty_frame():
    p = _panels()
    for panels in ({"hy_index": p["hy_index"]}, {"macro_series": p["macro_series"]}, {},
                   {"hy_index": p["hy_index"], "macro_series": p["macro_series"].iloc[0:0]}):
        out = f30.compute(panels, AS_OF)
        assert out.empty and list(out.columns) == f30.COLS


def test_no_vix_series_gives_empty_frame():
    p = _panels()
    p["macro_series"] = p["macro_series"][p["macro_series"]["series_id"] != "VIXCLS"]
    assert f30.compute(p, AS_OF).empty


def test_short_history():
    r = _run(_panels(days=DAYS[-60:]))
    assert r["status"] == "too_few_obs" and np.isnan(r["score"]) and r["n_obs"] == 60


def test_stale_join():
    p = _panels()
    cut = AS_OF - pd.Timedelta(20, unit="D")
    p["macro_series"] = p["macro_series"][p["macro_series"]["date"] <= cut]
    r = _run(p)
    assert r["status"] == "stale" and np.isnan(r["score"])


def test_nan_rows_drop():
    p = _panels()
    p["hy_index"].loc[p["hy_index"].index[-30:-20], "spread"] = np.nan
    r = _run(p)
    assert r["status"] == "ok" and np.isfinite(r["score"])
    assert r["n_obs"] == _run(_panels())["n_obs"] - 10


def test_flat_vix_gives_nan_score():
    p = _panels()
    p["macro_series"].loc[p["macro_series"]["series_id"] == "VIXCLS", "value"] = 20.0
    assert np.isnan(_run(p)["score"])


# ---------------------------------------------------------------- 5. helpers


def test_ols_exact_line():
    x = np.array([10.0, 15.0, 20.0, 30.0, 45.0])
    a, b, r2, sd = f30.ols_fit(x, 221.51 + 12.5889 * x)
    assert a == pytest.approx(221.51) and b == pytest.approx(12.5889)
    assert r2 == pytest.approx(1.0) and sd == pytest.approx(0.0, abs=1e-9)


def test_ols_hand_case():
    # x = 1, 2, 3; y = 1, 3, 2: b = 0.5, a = 1, residuals -0.5, 1, -0.5, SSR 1.5, SST 2, sd = sqrt(1.5 / 1)
    a, b, r2, sd = f30.ols_fit(np.array([1.0, 2.0, 3.0]), np.array([1.0, 3.0, 2.0]))
    assert (a, b) == pytest.approx((1.0, 0.5))
    assert r2 == pytest.approx(0.25) and sd == pytest.approx(np.sqrt(1.5))


def test_regression_gap_source_example():
    # 12M line Y = 221.51 + 12.5889 X; CDX HY Last 863.70, VIX Last 40.82 (p. 3)
    fitted, gap = f30.regression_gap(863.70, 40.82, 221.51, 12.5889)
    assert fitted == pytest.approx(735.39, abs=0.01) and gap == pytest.approx(128.31, abs=0.01)
    # the printed intercept is consistent with the printed means: 493.91 - 12.5889 x 21.64 = 221.49 (p. 3)
    assert 493.91 - 12.5889 * 21.64 == pytest.approx(221.51, abs=0.05)


def test_window_z_source_example():
    # z = (Last - Mean) / StdDev: CDX HY (863.70 - 493.91) / 100.72 = 3.67, VIX (40.82 - 21.64) / 7.40 = 2.59 (p. 3)
    s = pd.Series([1.0, 2.0, 3.0, 4.0, 10.0])
    assert f30.window_z(s) == pytest.approx((10.0 - s.mean()) / s.std(ddof=1))
    assert round((863.70 - 493.91) / 100.72, 2) == 3.67 and round((40.82 - 21.64) / 7.40, 2) == 2.59
    assert np.isnan(f30.window_z(pd.Series([5.0, 5.0, 5.0])))
