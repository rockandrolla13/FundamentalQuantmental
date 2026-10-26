"""Tests for F25 Credit-BMI v2 HY index timing composite (docs/factors/F25-credit-bmi.md)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from scipy.stats import norm

from hy.factors import f25_credit_bmi as f25

AS_OF = pd.Timestamp("2016-06-30")
FAST = {"horizons": (5, 10, 21), "traded": 10, "train": 120, "cal": 60, "refit_every": 21, "kinds": ("linear",)}


# ---------------------------------------------------------------- synthetic fixture


def long_rows(series_id: str, dates: pd.DatetimeIndex, values, lag_days: int = 1) -> pd.DataFrame:
    return pd.DataFrame({"series_id": series_id, "date": dates, "value": np.asarray(values, dtype=float),
                         "available_at": dates + pd.Timedelta(lag_days, unit="D")})


def macro_panel(days: int = 600, seed: int = 0, drop: float = 0.0, blocks: bool = True) -> pd.DataFrame:
    """Daily series to AS_OF. The next-day HY excess return loads on minus the 21-day VIX change, so a VIX fall
    predicts a positive return. `drop` lowers VIX over the last 21 days."""
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range(end=AS_OF, periods=days)
    vix = 20.0 + np.cumsum(rng.standard_normal(days))
    vix[-21:] -= np.linspace(0.0, drop, 21)
    dv = pd.Series(vix).diff(21).fillna(0.0).to_numpy()
    r = np.empty(days)
    r[0] = 0.0
    sig = 10.0 * np.tanh(f25.cdf_score(-dv / 4.6) / 10.0) / 10.0       # about the gated vol signal, in [-1, 1]
    r[1:] = 0.001 * sig[:-1] + 0.0001 * rng.standard_normal(days - 1)
    oas = 4.0 + np.cumsum(0.02 * rng.standard_normal(days))
    parts = [long_rows("H0A0_XR", dates, r), long_rows("VIXCLS", dates, vix), long_rows("BAMLH0A0HYM2", dates, oas)]
    if blocks:
        common = np.cumsum(0.02 * rng.standard_normal(days))
        for j, k in enumerate(f25.BUCKETS):
            parts.append(long_rows(k, dates, 1.0 + j + (1 + j) * common + np.cumsum(0.005 * rng.standard_normal(days))))
        weds = dates[dates.weekday == 2]
        parts.append(long_rows("NYFED_PD_CORP_NET", weds, 1e4 + rng.standard_normal(len(weds)), 9))
        for k in ("EM_BOND_TR", "G10_BOND_TR", "G10_EQUITY_TR"):
            parts.append(long_rows(k, dates, 100.0 * np.exp(np.cumsum(0.005 * rng.standard_normal(days)))))
        for k in f25.STRUCT_IDS:
            parts.append(long_rows(k, dates, rng.standard_normal(days)))
    return pd.concat(parts, ignore_index=True)


@pytest.fixture(scope="module")
def base():
    panel = macro_panel(drop=12.0)
    return panel, f25.compute({"macro_series": panel}, AS_OF, **FAST)


# ---------------------------------------------------------------- contract and edge cases


def test_meta_and_columns(base):
    for k in ("rank", "name", "level", "horizon_months", "needs", "spec", "section"):
        assert k in f25.META
    assert f25.META["rank"] == 25 and f25.META["level"] == "index" and "macro_series" in f25.META["needs"]
    _, out = base
    assert list(out.columns) == f25.COLS
    assert len(out) == 1 and out["index"].iloc[0] == "US_HY" and out["date"].iloc[0] == AS_OF
    assert out["available_at"].iloc[0] <= f25.decision_time(AS_OF)
    assert out["n_blocks"].iloc[0] == 6


def test_missing_panel_or_target_is_empty():
    assert f25.compute({}, AS_OF).empty
    assert list(f25.compute({}, AS_OF).columns) == f25.COLS
    panel = macro_panel(days=100)
    assert f25.compute({"macro_series": panel[panel["series_id"] != "H0A0_XR"]}, AS_OF).empty


def test_short_history_gives_nan_score():
    out = f25.compute({"macro_series": macro_panel(days=150)}, AS_OF, **FAST)
    assert len(out) == 1 and np.isnan(out["score"].iloc[0])


def test_missing_optional_blocks_still_score():
    out = f25.compute({"macro_series": macro_panel(drop=12.0, blocks=False)}, AS_OF, **FAST)
    assert out["n_blocks"].iloc[0] == 2                     # vol and mom only
    assert np.isnan(out["s_sys"].iloc[0]) and np.isnan(out["s_liq"].iloc[0])
    assert np.isfinite(out["score"].iloc[0])


# ---------------------------------------------------------------- no look-ahead


def test_no_lookahead(base):
    panel, out = base
    dt = f25.decision_time(AS_OF)
    later = pd.bdate_range(AS_OF + pd.Timedelta(1, unit="D"), periods=30)
    extra = [long_rows("H0A0_XR", later, np.full(30, 0.05)), long_rows("VIXCLS", later, np.full(30, 80.0))]
    # a late revision of the last VIX close and of the last return: public only after the decision time
    last = panel[panel["series_id"].isin(["VIXCLS", "H0A0_XR"])].groupby("series_id").tail(5).copy()
    last["value"] = last["value"] * 3.0 + 1.0
    last["available_at"] = dt + pd.Timedelta(3, unit="D")
    noisy = pd.concat([panel, *extra, last], ignore_index=True)
    out2 = f25.compute({"macro_series": noisy}, AS_OF, **FAST)
    pd.testing.assert_frame_equal(out, out2)


def test_dealer_publication_lag_and_ffill_cap():
    cal = pd.bdate_range("2015-01-01", "2015-02-27")
    obs = pd.DataFrame({"date": [pd.Timestamp("2015-01-07")], "value": [5.0],
                        "available_at": [pd.Timestamp("2015-01-16")]})
    s = f25.align_series(obs, cal, lag_days=9)
    assert s[:"2015-01-15"].isna().all()                    # date + 9 days = Friday 16 January
    assert s["2015-01-16"] == 5.0
    assert s["2015-01-23"] == 5.0 and np.isnan(s["2015-01-26"])   # 5 rows of forward fill, then NaN


def test_old_revision_does_not_overwrite_newer_date():
    cal = pd.bdate_range("2015-01-01", periods=10)
    obs = pd.DataFrame({"date": [cal[2], cal[4], cal[2]], "value": [1.0, 2.0, 9.0],
                        "available_at": [cal[2] + pd.Timedelta(1, "D"), cal[4] + pd.Timedelta(1, "D"),
                                         cal[6] + pd.Timedelta(1, "D")]})
    s = f25.align_series(obs, cal)
    assert s[cal[3]] == 1.0 and s[cal[5]] == 2.0 and s[cal[7]] == 2.0


# ---------------------------------------------------------------- sign


def test_sign_vix_fall_is_bullish_block(base):
    _, up = base
    down = f25.compute({"macro_series": macro_panel(drop=-12.0)}, AS_OF, **FAST)
    assert up["s_vol"].iloc[0] > 5 and down["s_vol"].iloc[0] < -3        # VIX sign is minus (Table 1, p. 2)
    for out in (up, down):                                                # score = pos x size x alignment
        assert out["score"].iloc[0] == pytest.approx(out["pos"].iloc[0] * out["size"].iloc[0] * out["align"].iloc[0])


@pytest.mark.parametrize("x_last, expected", [(3.0, 1), (-3.0, -1)])
def test_sign_walk_forward_known_answer(x_last, expected):
    """y^(1)_t = 0.002 x_t + small noise: a large x at the last day gives a long (short) call above the cost."""
    rng = np.random.default_rng(6)
    idx = pd.bdate_range("2014-01-01", periods=300)
    feats = pd.DataFrame(rng.standard_normal((300, 3)), index=idx)
    feats.iloc[-1, 0] = x_last
    r = np.r_[0.0, 0.002 * feats[0].to_numpy()[:-1]] + 0.0002 * rng.standard_normal(300)
    path = f25.walk_forward(feats, pd.Series(r, index=idx), 1, cost=0.0012, train=120, cal=60, kinds=("linear",))
    last = path.iloc[-1]
    assert np.sign(last["point"]) == expected and last["pos"] == expected and last["size"] > 0
    assert last["coverage"] == pytest.approx(0.9, abs=0.08)


# ---------------------------------------------------------------- formula helpers


def test_cdf_score_and_expanding_z():
    assert f25.cdf_score(1.0) == pytest.approx(20.0 * (norm.cdf(1.0) - 0.5))
    assert f25.cdf_score(1.0) == pytest.approx(6.826894921)
    assert f25.cdf_score(1.0, -1.0) == pytest.approx(-6.826894921)
    z = f25.expanding_z(pd.Series(np.arange(1.0, 61.0)))
    assert z.iloc[:59].isna().all()
    assert z.iloc[59] == pytest.approx((60 - 30.5) / np.sqrt((60 ** 2 - 1) / 12.0))
    spike = f25.expanding_z(pd.Series(np.r_[np.tile([0.0, 1.0], 40), 1e6]))
    assert spike.iloc[-1] == 8.0


def test_gate_and_squash():
    s = pd.DataFrame({"vol": [5.0, 5.0], "mom": [5.0, 5.0]})
    out = f25.gate_and_squash(s, pd.Series([0.0, 1.0]))
    assert out["vol"].tolist() == pytest.approx([10 * np.tanh(0.5)] * 2)
    assert out["mom"].iloc[0] == pytest.approx(4.621171573)
    assert out["mom"].iloc[1] == pytest.approx(0.4 * 4.621171573)


def test_regime_flag():
    oas = pd.Series(np.r_[np.tile([0.0, 0.01], 50), np.tile([0.0, 1.0], 20)])
    g = f25.regime_flag(oas)
    assert g.iloc[:80].sum() == 0 and g.iloc[-1] == 1.0


def test_pc1_sign_and_score():
    rng = np.random.default_rng(3)
    f = rng.standard_normal(300)
    load = np.array([0.5, 1.0, 2.0, 3.0])
    d = pd.DataFrame(np.outer(f, load) + 0.01 * rng.standard_normal((300, 4)))
    sc = f25.pc1_scores(d, [True, True, False, False])
    assert sc.iloc[:59].isna().all()
    assert np.corrcoef(sc.iloc[100:], f[100:])[0, 1] > 0.99
    assert sc.iloc[-1] == pytest.approx(f[-1] * np.linalg.norm(load), rel=0.05)


def test_sentiment_flip_at_extreme():
    idx = pd.RangeIndex(200)
    rng = np.random.default_rng(1)
    em = pd.Series(100.0 * np.exp(np.r_[0.001 * rng.standard_normal(199), 0.5]), index=idx)
    one = pd.Series(100.0, index=idx)
    x, flip = f25.sentiment_signal(em, one, one)
    assert flip.iloc[-1] == -1.0 and flip.iloc[150] == 1.0
    assert x.iloc[-1] == pytest.approx(0.5 * (np.log(em.iloc[-1] / 100.0) - np.log(em.iloc[-22] / 100.0)))


def test_momentum_and_drift_scale():
    r = pd.Series(0.001 + 0.002 * np.tile([1.0, -1.0], 150))
    m = f25.momentum_raw(r)
    assert m.iloc[:100].isna().sum() > 0 and (m.dropna() > 0).all()
    d = f25.drift_scale(pd.Series(np.tile([1.0, 3.0], 50)))
    assert d.iloc[-1] == pytest.approx(3.0 * (10 / 3) / 1.0)     # sd of {1, 3} is 1, mean not removed


def test_forward_sum():
    y = f25.forward_sum(pd.Series([1.0, 2.0, 3.0, 4.0]), 2)
    assert y.iloc[0] == 5.0 and y.iloc[1] == 7.0 and y.iloc[2:].isna().all()


def test_purged_splits_source_case():
    splits = list(f25.purged_cv_splits(250, 3, 21))
    assert splits == [(slice(0, 103), slice(124, 186)), (slice(0, 165), slice(186, 248))]
    assert len(list(f25.purged_cv_splits(250, 3, 5))) == 3


def test_pinball_loss():
    assert f25.pinball_loss([1.0, 2.0], [0.0, 3.0], 0.9) == pytest.approx(0.5)


def test_cqr_q():
    zeros = np.zeros(9)
    assert f25.cqr_q(zeros, zeros, np.arange(1.0, 10.0), 0.10) == 9.0          # ceil(10 x 0.9)/9 = 1
    z19 = np.zeros(19)
    assert f25.cqr_q(z19, z19, np.arange(1.0, 20.0), 0.20) == 17.0           # 16/19 quantile, "higher"


def test_aci_step():
    assert f25.aci_step(0.10, 1.0) == pytest.approx(0.082)
    assert f25.aci_step(0.10, 0.0) == pytest.approx(0.102)
    assert f25.aci_step(0.001, 1.0) == pytest.approx(0.001)


def test_decision_and_alignment():
    assert f25.decision(0.02, 0.005, 0.03, 0.0012) == (1, pytest.approx(0.02 / 0.025))
    assert f25.decision(-0.02, -0.03, -0.005, 0.0012) == (-1, pytest.approx(0.02 / 0.025))
    assert f25.decision(0.01, -0.001, 0.03, 0.0012) == (0, 0.0)
    assert f25.alignment_scale({5: 1.0, 21: 2.0, 63: 0.5}) == 1.0
    assert f25.alignment_scale({5: 1.0, 21: 2.0, 63: -0.5}) == pytest.approx(2 / 3)
    assert f25.alignment_scale({5: -1.0, 21: 2.0, 63: -0.5}) == 0.0


def test_drawdown_threshold():
    y = np.r_[np.full(19, 0.01), 0.1]
    assert f25.drawdown_threshold(y) == pytest.approx(2.0 * (0.01 + 0.05 * 0.09))


def test_shrinkage_weights():
    rng = np.random.default_rng(2)
    x = rng.standard_normal((200, 2))
    y = x[:, 0] + 0.5 * rng.standard_normal(200)
    w = f25.shrinkage_weights(x, y, lam=1.0)
    rho = np.array([np.corrcoef(x[:, k], y)[0, 1] for k in range(2)])
    assert w == pytest.approx(rho / np.abs(rho).sum(), abs=1e-4)
    assert f25.shrinkage_weights(x[:10], y[:10]).tolist() == [0.5, 0.5]       # too few rows: equal weights
    w0 = f25.shrinkage_weights(np.c_[x, np.ones(200)], y)
    assert w0[2] == 0.0 and np.abs(w0).sum() == pytest.approx(1.0)


def test_models_fit_and_tune_fallback():
    rng = np.random.default_rng(4)
    x = rng.standard_normal((80, 3))
    y = x[:, 0] + 0.1 * rng.standard_normal(80)
    m = f25.make_quantile_model("gbm", 0.5, f25.GBM_GRID[0]).fit(x, y)
    assert np.corrcoef(m.predict(x), y)[0, 1] > 0.9
    assert f25.tune(x[:40], y[:40], 21, ("linear",))[:2] == f25.FALLBACK_MODEL     # no fold survives
    md, lo, hi = f25.fit_three(x, y, "linear", {"alpha": 0.0}, 0.10)(x)
    assert (lo <= hi).all() and np.mean((lo <= md) & (md <= hi)) > 0.9


def test_walk_forward_uses_matured_targets_only():
    rng = np.random.default_rng(5)
    idx = pd.bdate_range("2014-01-01", periods=260)
    feats = pd.DataFrame(rng.standard_normal((260, 3)), index=idx)
    r = pd.Series(0.001 * rng.standard_normal(260), index=idx)
    a = f25.walk_forward(feats, r, 5, train=120, cal=60, kinds=("linear",))
    r2 = r.copy()
    r2.iloc[-3:] = 1.0                                     # the last returns change targets that are not matured
    b = f25.walk_forward(feats, r2, 5, train=120, cal=60, kinds=("linear",))
    cols = ["point", "lo", "hi", "alpha_t"]
    pd.testing.assert_frame_equal(a[cols].iloc[:-3], b[cols].iloc[:-3])
    assert a["date"].iloc[0] == idx[120 + 60 + 5 - 1]
