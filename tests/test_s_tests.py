"""Tests for scripts/s_tests.py, tests S1-S4 of docs/decisions/2026-10-24-review-sloos-pmi.md (methodology 5.2, F6)."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import s_tests as s  # noqa: E402

# ---------------------------------------------------------------------------- no look-ahead


def _vintages(quarters: pd.DatetimeIndex, value: float = 10.0) -> pd.DataFrame:
    """One first version per quarter, published on the first day of the second month after the quarter end."""
    snap = quarters + pd.offsets.MonthBegin(2)
    return pd.DataFrame({"gvkey": "000001", "datadate": quarters, "vintage": 0, "snapshot_available_at": snap,
                         "pit_exact": True, "oibdp": value, "debt_current": 5.0, "debt_long_term": 95.0})


def test_ltm_uses_only_versions_known_on_first_release():
    q = pd.date_range("2010-03-31", periods=10, freq="QE")
    v = _vintages(q)
    late = v.iloc[[3]].copy()  # 2010-12-31 restated two years later to a huge value
    late["vintage"], late["snapshot_available_at"], late["oibdp"] = 1, pd.Timestamp("2013-01-01"), 1e6
    ltm, _ = s.first_release_ltm(pd.concat([v, late], ignore_index=True))
    row = ltm[ltm["datadate"] == pd.Timestamp("2011-03-31")].iloc[0]
    assert row["ltm_ebitda"] == pytest.approx(40.0)
    assert row["ltm_available_at"] == pd.Timestamp("2011-05-01")
    assert (ltm["ltm_available_at"] > ltm["datadate"]).all()


def test_missing_quarter_breaks_ltm_and_is_counted():
    q = pd.date_range("2010-03-31", periods=10, freq="QE")
    v = _vintages(q)
    v = v[v["datadate"] != pd.Timestamp("2010-12-31")]  # a missing fiscal Q4
    ltm, traps = s.first_release_ltm(v)
    broken = ltm[ltm["datadate"].between("2011-03-31", "2011-09-30")]
    assert broken["ltm_ebitda"].isna().all()
    assert traps["removed_missing_quarter_in_ltm_window"] >= 3
    assert traps["loose_400d_rule_would_accept_false_ltm"] >= 1  # the 400-day rule would have summed a false LTM


def test_outcome_label_and_timing():
    q = pd.date_range("2009-03-31", periods=14, freq="QE")
    v = _vintages(q)
    v.loc[v["datadate"] >= "2011-06-30", "oibdp"] = 7.0  # quarterly EBITDA falls from 10 to 7
    ltm, _ = s.first_release_ltm(v)
    o = s.attach_outcome(ltm, 0.20).set_index("datadate")
    assert o.loc["2011-03-31", "D"] == 1.0  # LTM 40 -> 28, a fall of 30%
    assert o.loc["2010-12-31", "D"] == 1.0  # LTM 40 -> 31, a fall of 22.5%
    assert o.loc["2010-09-30", "D"] == 0.0  # LTM 40 -> 34, a fall of 15%
    assert o.loc["2011-03-31", "outcome_available_at"] > o.loc["2011-03-31", "ltm_available_at"]
    assert np.isnan(o.loc[q[-1], "D"])


def test_rows_guard_rejects_late_macro_or_ltm():
    rows = pd.DataFrame({"tau": [pd.Timestamp("2015-02-01")], "ltm_available_at": [pd.Timestamp("2015-02-01")],
                         "macro_available_at": [pd.Timestamp("2015-02-01")],
                         "outcome_available_at": [pd.Timestamp("2016-02-01")]})
    s.assert_rows_pit(rows)
    bad = rows.assign(macro_available_at=pd.Timestamp("2015-03-01"))
    with pytest.raises(AssertionError):
        s.assert_rows_pit(bad)
    with pytest.raises(AssertionError):
        s.assert_rows_pit(rows.assign(outcome_available_at=pd.Timestamp("2015-01-01")))


def test_sloos_enters_only_after_release(tmp_path):
    months = pd.date_range("1995-01-01", "2012-12-01", freq="MS")
    pd.DataFrame({"DATE": months.strftime("%b-%y"), "GAC": 1.0}).to_csv(tmp_path / "bos_dif.csv", index=False)
    pd.DataFrame({"observation_date": months.strftime("%Y-%m-%d"), "BAA10Y": 2.0}).to_csv(tmp_path / "BAA10Y.csv",
                                                                                         index=False)
    qs = pd.date_range("1995-01-01", "2012-10-01", freq="QS")
    sl = pd.DataFrame({"observation_date": qs.strftime("%Y-%m-%d"), "DRTSCILM": np.arange(len(qs), dtype=float)})
    sl.to_csv(tmp_path / "DRTSCILM.csv", index=False)
    m = s.load_macro_monthly(tmp_path)
    jan = sl.set_index("observation_date")["DRTSCILM"]
    # The January 2010 survey is published in February: at end January the latest known is October 2009.
    assert m.loc["2010-01-31", "sloos"] == jan["2009-10-01"]
    assert m.loc["2010-02-28", "sloos"] == jan["2010-01-01"]
    assert m.loc["2010-02-28", "sloos_prev"] == jan["2009-10-01"]
    assert (m["macro_available_at"] == m.index + pd.Timedelta(1, unit="D")).all()


# ---------------------------------------------------------------------------- window split


def test_window_split_trains_only_on_known_outcomes():
    rng = np.random.default_rng(42)
    tau = pd.Timestamp("2008-01-01") + pd.to_timedelta(rng.integers(0, 6000, 3000), unit="D")
    rows = pd.DataFrame({"tau": tau, "outcome_available_at": tau + pd.to_timedelta(rng.integers(300, 500, 3000), unit="D")})
    for w, (a, b) in s.CYCLE_WINDOWS.items():
        tr, te = s.window_split(rows, a, b)
        assert (tr["outcome_available_at"] < pd.Timestamp(a)).all()
        assert ((te["tau"] >= pd.Timestamp(a)) & (te["tau"] <= pd.Timestamp(b) + pd.Timedelta(1, unit="D"))).all()
        assert not set(tr.index) & set(te.index)
    edge = pd.DataFrame({"tau": [pd.Timestamp("2014-01-01")], "outcome_available_at": [pd.Timestamp("2015-01-01")]})
    tr, _ = s.window_split(edge, "2015-01-01", "2016-12-31")
    assert tr.empty  # an outcome known only on the first day of the window is not known before it


# ---------------------------------------------------------------------------- planted and null effects


def _synthetic_panel(seed: int = 42, n_per_q: int = 400, b_x: float = 0.8) -> pd.DataFrame:
    """Quarterly macro x (planted, enters the true model) and z (null); D ~ Bernoulli(sigma(-1.6 + b_x x_q))."""
    rng = np.random.default_rng(seed)
    qs = pd.date_range("1999-03-31", "2023-12-31", freq="QE")
    x = np.zeros(len(qs))
    z = np.zeros(len(qs))
    for i in range(1, len(qs)):
        x[i] = 0.7 * x[i - 1] + rng.normal()
        z[i] = 0.7 * z[i - 1] + rng.normal()
    frames = []
    for i, q in enumerate(qs):
        sec = rng.choice(["10", "20", "45", "55"], n_per_q)
        p = 1 / (1 + np.exp(-(-1.6 + b_x * x[i] + np.where(sec == "10", 0.3, 0.0))))
        tau = q + pd.Timedelta(45, unit="D")
        frames.append(pd.DataFrame({"x": x[i], "z": z[i], "pmi": z[i], "sector": sec,
                                    "D": (rng.random(n_per_q) < p).astype(float), "tau": tau,
                                    "outcome_available_at": tau + pd.Timedelta(366, unit="D")}))
    return pd.concat(frames, ignore_index=True)


def test_planted_macro_effect_is_found_and_null_is_not():
    rows = _synthetic_panel()
    planted, null = [], []
    for w, (a, b) in s.CYCLE_WINDOWS.items():
        tr, te = s.window_split(rows, a, b)
        planted.append(s.compare_models(tr, te, ("z",), ("x", "z"), proxy=False)["logloss_gain"])
        null.append(s.compare_models(tr, te, ("x",), ("x", "z"), proxy=False)["logloss_gain"])
    assert sum(g["mean"] > 0 for g in planted) >= 3
    assert sum(g["ci95"][0] > 0 for g in planted) >= 3
    assert sum(g["ci95"][0] > 0 for g in null) == 0
    assert max(abs(g["mean"]) for g in null) < 0.2 * min(abs(g["mean"]) for g in planted)


def test_planted_vote_raises_share_and_null_vote_does_not():
    rows = _synthetic_panel(seed=7)
    rng = np.random.default_rng(1)
    rows["flag_x"] = rows["x"] > 0
    qflag = pd.Series(rng.random(rows["tau"].nunique()) > 0.5, index=sorted(rows["tau"].unique()))
    rows["flag_null"] = rows["tau"].map(qflag)
    blocks = s.quarter_blocks(rows)
    real = s.block_bootstrap_share_diff(rows["D"].to_numpy(), rows["flag_x"].to_numpy(), blocks)
    fake = s.block_bootstrap_share_diff(rows["D"].to_numpy(), rows["flag_null"].to_numpy(), blocks)
    assert real["diff"] > 0.1 and real["ci95"][0] > 0
    assert fake["ci95"][0] < 0 < fake["ci95"][1]


# ---------------------------------------------------------------------------- vote and design rules


def test_f6_votes_use_pmi_proxy_threshold_zero_and_two_sloos_readings():
    idx = pd.date_range("2010-01-31", periods=3, freq="ME")
    m = pd.DataFrame({"hy_oas": [0.05, 0.06, 0.04], "hy_med5y": 0.05, "hy_chg3": [0.01, 0.01, -0.01],
                      "distress": [0.1, 0.2, 0.05], "distress_med5y": 0.1, "sloos": [5.0, 5.0, -1.0],
                      "sloos_prev": [-2.0, 3.0, 5.0], "pmi": [-0.5, 10.0, np.nan]}, index=idx)
    v = s.f6_votes(m)
    assert v["vote_pmi"].tolist()[:2] == [True, False] and v["vote_pmi"].iloc[2] is None
    assert v["vote_sloos_tightening"].tolist() == [False, True, False]
    assert v["vote_hy_oas"].tolist() == [False, True, False]
    assert v["vote_distress_ratio"].tolist() == [False, True, False]
    assert v["vote_majority"].tolist() == [False, True, False]


def test_pmi_cyclical_term_is_zero_for_defensive_sectors():
    rows = pd.DataFrame({"pmi": [2.0, 2.0, 2.0, 2.0, 2.0], "sector": ["10", "15", "20", "25", "45"]})
    X = s.design(rows, ("pmi", "pmi_cyc"), proxy=False)
    assert X[:, 1].tolist() == [2.0, 2.0, 2.0, 2.0, 0.0]


def test_drop_2020_modes():
    d = pd.to_datetime(["2018-12-31", "2019-03-31", "2019-12-31", "2020-06-30", "2021-03-31"])
    rows = pd.DataFrame({"datadate": d})
    assert s.drop_2020(rows, "quarter")["datadate"].dt.year.tolist() == [2018, 2019, 2019, 2021]
    assert s.drop_2020(rows, "span")["datadate"].tolist() == [d[0], d[4]]


# ---------------------------------------------------------------------------- attrition, EWC, Ibragimov-Mueller


def test_exit_rule_counts_bankruptcy_and_liquidation_only_inside_horizon():
    q = pd.DataFrame({"gvkey": ["A", "B", "C", "D", "E"], "datadate": pd.Timestamp("2015-03-31"),
                      "ltm_available_at": pd.Timestamp("2015-05-01"), "ltm_ebitda": [10.0, 10.0, 10.0, -1.0, 10.0],
                      "D": np.nan, "outcome_available_at": pd.NaT})
    dele = pd.DataFrame({"gvkey": ["A", "B", "C", "D", "E"], "dlrsn": ["02", "01", "03", "02", "02"],
                         "dldte": pd.to_datetime(["2015-12-01", "2015-12-01", "2018-01-01", "2015-12-01",
                                                  "2015-04-15"])})
    out = s.apply_exits(q, dele).set_index("gvkey")
    assert out.loc["A", "D"] == 1.0 and out.loc["A", "outcome_available_at"] == pd.Timestamp("2015-12-02")
    assert np.isnan(out.loc["B", "D"])  # acquisition is not a downside exit
    assert np.isnan(out.loc["C", "D"])  # liquidation outside the 21-month horizon
    assert np.isnan(out.loc["D", "D"])  # LTM EBITDA_t not positive
    assert np.isnan(out.loc["E", "D"])  # deleted before the decision time
    assert out["exit_event"].sum() == 1
    assert s.apply_exits(q, None)["D"].isna().all()


def test_ewc_matches_the_formula_and_ignores_a_level_shift():
    x = np.array([0.5, -0.2, 0.9, 0.1, 0.4, -0.3, 0.7, 0.2, 0.0, 0.6])
    r = s.ewc_test(x)
    T, nu = 10, int(np.floor(0.4 * 10 ** (2 / 3)))
    tt = np.arange(1, T + 1)
    lam = [np.sqrt(2 / T) * np.sum(np.cos(np.pi * j * (tt - 0.5) / T) * x) for j in range(1, nu + 1)]
    assert r["nu"] == nu == 1
    assert r["t"] == pytest.approx(x.mean() / np.sqrt(np.mean(np.square(lam)) / T))
    lam_shift = [np.sqrt(2 / T) * np.sum(np.cos(np.pi * j * (tt - 0.5) / T) * (x + 3.0)) for j in range(1, nu + 1)]
    assert np.allclose(lam, lam_shift)  # cosines j >= 1 are orthogonal to a constant


def test_ewc_size_on_white_noise_is_near_nominal():
    rng = np.random.default_rng(42)
    rej = np.mean([s.ewc_test(rng.normal(size=60))["p_one_sided"] < 0.05 for _ in range(2000)])
    assert 0.03 < rej < 0.07


def test_im_test_and_fair_coin_rate():
    r = s.im_test([0.01, 0.02, 0.015, None])
    assert r["q"] == 3 and r["df"] == 2 and r["t"] > 0 and r["p_one_sided"] < 0.05
    assert s.im_test([0.01])["t"] is None
    v = s.verdicts({}, {}, (2008, 2015, 2020, 2022), 3)
    assert v["fair_coin_pass_probability"] == pytest.approx(5 / 16)
