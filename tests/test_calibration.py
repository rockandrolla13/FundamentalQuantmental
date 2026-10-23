"""Size calibration (hy.calibration; methodology 7.5 size calibration; spec S14b; decision page 2026-10-23-size-calibration)."""

import json

import numpy as np
import pandas as pd
import pytest

from hy import calibration as cb
from hy import groups
from hy.data.pit import LookAheadError


def synth(rng, slope=0.4, a=0.002, months=60, per=200, h=3, noise=0.03, spread=True):
    """Bond-month rows with realised y = a + slope x + noise; a common shock per date makes the errors correlated."""
    dates = pd.date_range("2010-01-31", periods=months, freq="ME")
    d = np.repeat(dates, per)
    x = rng.normal(0.0, 0.03, len(d))
    shock = np.repeat(rng.normal(0.0, 0.005, months), per)
    y = a + slope * x + shock + rng.normal(0.0, noise, len(d))
    df = pd.DataFrame({"date": d, "pred": x, "real": y})
    if spread:
        df["g_spread"] = rng.uniform(0.01, 0.099, len(d))
    return cb.calibration_rows(df, "pred", "real", h, spread="g_spread" if spread else None)


def test_known_slope_is_recovered(rng):
    rows = synth(rng, slope=0.4)
    as_of = rows["available_at"].max()
    cal = cb.fit_calibration(rows, as_of, 3, "pred")
    assert abs(cal.b_raw - 0.4) < 3 * cal.se_b
    assert abs(cal.b_raw - 0.4) < 0.05
    assert cal.use == "size"
    assert 0.35 < cal.b <= cal.b_raw            # a sure slope is kept nearly whole
    assert np.isclose(cal.a, rows["y"].mean() - cal.b * rows["x"].mean())


def test_slope_of_one_recovered_by_mz_of_calibrated_forecast(rng):
    """Out of sample, the calibrated forecast of a known-slope process has an MZ slope near 1."""
    from hy.backtest import mincer_zarnowitz

    rows = synth(rng, slope=0.3, months=72, per=150)
    oos, _ = cb.expanding_forecasts(rows, 3, "pred", methods=("linear",), min_months=24)
    mz = mincer_zarnowitz(oos.dropna(subset=["linear"]), "linear", "y", lags=2)
    assert abs(mz["b"] - 1.0) < 0.2
    raw = mincer_zarnowitz(oos.dropna(subset=["linear"]), "x", "y", lags=2)
    assert abs(raw["b"] - 0.3) < 0.1


def test_noise_slope_shrinks_to_zero(rng):
    rows = synth(rng, slope=0.0, noise=0.08)
    cal = cb.fit_calibration(rows, rows["available_at"].max(), 3, "pred")
    assert cal.b == 0.0
    assert cal.use == "rank only, minimum size"
    assert np.isclose(cal.a, rows["y"].mean())   # a flat map at the mean realised return


def test_shrink_slope_rule():
    assert cb.shrink_slope(0.2, 0.1, 100) == 0.0                     # t = 2: rank only
    assert np.isclose(cb.shrink_slope(0.4, 0.1, 100), 0.4 * 0.75)    # t = 4: keeps 75%
    assert cb.shrink_slope(-0.5, 0.01, 100) == 0.0                   # wrong sign: zero
    assert cb.shrink_slope(0.8, 0.01, 10) == 0.0                     # too few months: zero


def test_too_few_months_gives_zero_slope(rng):
    rows = synth(rng, slope=0.5, months=12, noise=0.01)
    cal = cb.fit_calibration(rows, rows["available_at"].max(), 3, "pred")
    assert cal.b_raw > 0.4 and cal.b == 0.0 and cal.a == 0.0
    assert cal.use == "rank only, minimum size"


def test_unfinished_outcome_raises(rng):
    rows = synth(rng)
    as_of = pd.Timestamp("2012-06-30")
    with pytest.raises(LookAheadError):
        cb.fit_calibration(rows, as_of, 3, "pred")
    ok = cb.known_by(rows, as_of)
    assert ok["date"].max() <= as_of - pd.offsets.MonthEnd(3)
    cb.fit_calibration(ok, as_of, 3, "pred")


def test_available_at_waits_the_full_horizon():
    av = cb.outcome_available_at(pd.Series([pd.Timestamp("2020-01-31")]), 6)
    assert av.iloc[0] == pd.Timestamp("2020-08-01")


def test_expanding_window_never_reads_an_unfinished_outcome(rng):
    """Look-ahead fixture: outcomes formed in the last 12 months carry slope 5, the rest slope 0.3. A fit at T that
    read any row formed after T - h would see the slope jump. The test fails if the expanding window peeks."""
    h = 3
    rows = synth(rng, slope=0.3, months=60, per=150, h=h, noise=0.01)
    cut = rows["date"].max() - pd.offsets.MonthEnd(12)
    late = rows["date"] > cut
    rows.loc[late, "y"] = 5.0 * rows.loc[late, "x"]
    _, fits = cb.expanding_forecasts(rows, h, "pred", methods=("linear",), min_months=24)
    for cal in fits["linear"]:
        fit_at = pd.Timestamp(cal.fit_date)
        if fit_at <= cut + pd.offsets.MonthEnd(h) + pd.Timedelta(1, unit="D"):   # it may read rows formed up to cut
            assert cal.b_raw < 0.4, f"fit at {fit_at.date()} read an unfinished outcome"
    first_late = [c for c in fits["linear"] if pd.Timestamp(c.fit_date) > cut + pd.offsets.MonthEnd(h) + pd.offsets.MonthEnd(2)]
    assert first_late and first_late[-1].b_raw > 0.4      # once finished, the late rows do count


def test_partial_pool_shrinks_noisy_buckets():
    b, tau2 = cb.partial_pool(np.array([0.1, 0.12, 0.11]), np.array([0.05, 0.05, 0.05]), 0.11)
    assert tau2 == 0.0 and np.allclose(b, 0.11)                      # buckets agree within noise: pooled
    b, tau2 = cb.partial_pool(np.array([0.0, 1.0]), np.array([0.01, 0.01]), 0.5)
    assert tau2 > 0 and abs(b[0] - 0.0) < 0.01 and abs(b[1] - 1.0) < 0.01   # precise and different: own slope


def test_bucket_fit_recovers_band_slopes(rng):
    rows = synth(rng, slope=0.0, noise=0.01, months=48, per=300)
    wide = rows["bucket"] == 2
    rows.loc[wide, "y"] = 0.8 * rows.loc[wide, "x"] + rng.normal(0, 0.01, wide.sum())
    rows.loc[~wide, "y"] = 0.2 * rows.loc[~wide, "x"] + rng.normal(0, 0.01, (~wide).sum())
    cal = cb.fit_calibration(rows, rows["available_at"].max(), 3, "pred", method="bucket")
    assert abs(cal.buckets["by"]["2"]["b"] - 0.8) < 0.1
    assert abs(cal.buckets["by"]["0"]["b"] - 0.2) < 0.1
    out = cb.apply(cal, np.array([0.1, 0.1]), np.array([0, 2]))
    assert out[1] > out[0]


def test_pava_and_isotonic_are_monotone(rng):
    assert np.allclose(cb.pava(np.array([1.0, 3.0, 2.0, 4.0]), np.ones(4)), [1.0, 2.5, 2.5, 4.0])
    x = rng.normal(0, 1, 5000)
    y = np.tanh(x) + rng.normal(0, 0.5, 5000)
    iso = cb.fit_isotonic(x, y, 10)
    assert np.all(np.diff(iso["value"]) >= 0)
    assert cb.apply_isotonic(iso, np.array([100.0]))[0] == iso["value"][-1]   # capped at the top bin


def test_json_round_trip(tmp_path, rng):
    rows = synth(rng)
    cal = cb.fit_calibration(rows, rows["available_at"].max(), 3, "pred", method="isotonic")
    cal.evaluation = {"chosen": True}
    p = cb.save([cal], tmp_path / "c.json", {"note": "x"})
    json.loads(p.read_text())
    back = cb.load(p)[0]
    assert back.b == cal.b and back.isotonic == cal.isotonic and back.available_at == cal.available_at


def test_latest_before_is_point_in_time():
    def rec(day, b):
        return cb.Calibration("p", 6, "linear", day, str(pd.Timestamp(day) + pd.Timedelta(1, unit="D")), 100, 30,
                              0.0, b, 0.0, b, 0.1, 0.1, "size", evaluation={"chosen": True})
    recs = [rec("2015-01-31", 0.1), rec("2016-01-31", 0.2), rec("2017-01-31", 0.3)]
    assert cb.latest_before(recs, pd.Timestamp("2016-06-30"), "p", 6).b == 0.2
    assert cb.latest_before(recs, pd.Timestamp("2016-01-31"), "p", 6).b == 0.1   # 2016 fit readable from 1 Feb
    assert cb.latest_before(recs, pd.Timestamp("2014-01-01"), "p", 6) is None


def test_unshrunk_comparator_and_demean(rng):
    rows = synth(rng, slope=0.0, noise=0.08)
    cal = cb.fit_calibration(rows, rows["available_at"].max(), 3, "pred", method="unshrunk")
    assert cal.b == 0.0 and cal.b_raw != 0.0
    assert np.isclose(cb.apply(cal, np.array([0.1]))[0], cal.a_raw + cal.b_raw * 0.1)
    d = cb.demean_by_date(pd.DataFrame({"date": [1, 1, 2, 2], "f": [1.0, 3.0, 10.0, 14.0]}), ["f"])
    assert np.allclose(d["f"], [-1.0, 1.0, -2.0, 2.0])


def test_size_bp_yr_units():
    cal = cb.Calibration("p", 6, "linear", "2020-01-31", "2020-02-01", 100, 30, 0.001, 0.5, 0.0, 0.5, 0.1, 0.1, "size")
    # 200 bp a year = 1% over 6 months -> 0.001 + 0.5 x 0.01 = 0.6% over 6 months = 120 bp a year
    assert np.isclose(cb.size_bp_yr(cal, 200.0), 120.0)


# ---------------------------------------------------------------- hook in hy.groups


EST = {"E0": 300.0, "E1": 200.0, "E7": -10.0, "E14": 1.0}


def test_groups_falls_back_to_sized_v0_without_file(tmp_path):
    missing = tmp_path / "none.json"
    r = groups.combine(EST, 30.0, 200.0, decision_time=pd.Timestamp("2026-10-23"), calibration_path=missing)
    a, b = groups.SIZED_V0
    assert np.isclose(r["alpha_sized"], a + b * r["combined_after_cost"])
    assert r["size_source"].startswith("spec S14b v0")
    r0 = groups.combine(EST, 30.0, 200.0)                       # no decision time: v0, as before
    assert np.isclose(r0["alpha_sized"], a + b * r0["combined_after_cost"])


def test_groups_reads_latest_calibration_before_decision(tmp_path):
    def rec(day, b, chosen=True):
        return cb.Calibration(groups.SIZE_PREDICTOR, groups.SIZE_HORIZON, "linear", day,
                              str(pd.Timestamp(day) + pd.Timedelta(1, unit="D")), 1000, 60, 0.0, b, 0.0, b, 0.01, 0.01,
                              "size", evaluation={"chosen": chosen})
    p = cb.save([rec("2020-06-30", 0.3), rec("2026-09-30", 0.5), rec("2026-12-31", 0.9)], tmp_path / "c.json")
    r = groups.combine(EST, 30.0, 200.0, decision_time=pd.Timestamp("2026-10-23"), calibration_path=p)
    assert np.isclose(r["alpha_sized"], 0.5 * r["combined_after_cost"])
    assert r["size_use"] == "size" and "2026-09-30" in r["size_source"]
    r = groups.combine(EST, 30.0, 200.0, decision_time=pd.Timestamp("2019-01-01"), calibration_path=p)
    assert r["size_source"].startswith("spec S14b v0")          # nothing fitted yet at that date


def test_rank_only_calibration_leaves_no_per_bond_size(tmp_path):
    # A fitted slope of 0 maps every bond to the same number (the intercept). That is the sample's average excess
    # return, not a view on the bond, so the combined output shows no size and names the level separately.
    rec = cb.Calibration(groups.SIZE_PREDICTOR, groups.SIZE_HORIZON, "linear", "2026-08-01", "2026-08-02", 1000, 217,
                         -0.0054, 0.0, 0.002, 0.0, 0.0, 0.0, "rank only, minimum size", evaluation={"chosen": True})
    p = cb.save([rec], tmp_path / "c.json")
    r = groups.combine(EST, 30.0, 200.0, decision_time=pd.Timestamp("2026-09-18"), calibration_path=p)
    assert r["size_use"] == "rank only, minimum size"
    assert np.isnan(r["alpha_sized"])
    assert np.isclose(r["size_level_bp_yr"], -0.0054 * 1e4 * 12 / groups.SIZE_HORIZON)
