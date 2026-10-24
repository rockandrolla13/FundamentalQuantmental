"""Tests for scripts/wt_sector_rules.py (decision page 2026-10-24-wt-sector-rules, specification S2-S7, S9)."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import wt_sector_rules as sr  # noqa: E402


def test_expanding_z_uses_no_later_data():
    rng = np.random.default_rng(0)
    x = pd.Series(rng.normal(size=200).cumsum(), index=pd.period_range("1980-01", periods=200, freq="M"))
    a = sr.expanding_z(x)
    x2 = x.copy()
    x2.iloc[150:] += 100.0
    b = sr.expanding_z(x2)
    pd.testing.assert_series_equal(a.iloc[:150], b.iloc[:150])
    assert a.iloc[: sr.Z_MIN_MONTHS - 1].isna().all()


def test_owners_equity_known_three_months_after_quarter_end(tmp_path):
    f = tmp_path / "oeh.csv"
    f.write_text("observation_date,OEHRENWBSHNO\n2020-01-01,100\n2020-04-01,110\n")
    s = sr.owners_equity_monthly(f)
    assert s.index[0] == pd.Period("2020-06", "M")  # Q1 ends March, known in June
    assert s.index[1] == pd.Period("2020-09", "M")


def test_gics_at_uses_the_record_in_force_and_backfills_the_first():
    gics = pd.DataFrame({"gvkey": ["1", "1"], "indfrom": ["1999-06-30", "2005-01-01"],
                         "indthru": ["2004-12-31", None], "gsector": ["20", "45"], "ggroup": ["2010", "4520"]})
    keys = pd.DataFrame({"gvkey": ["1", "1", "1", "2"],
                         "date": pd.to_datetime(["1995-03-31", "2003-06-30", "2010-06-30", "2010-06-30"])})
    g = sr.gics_at(keys, gics)
    assert list(g["gsector"]) == ["20", "20", "45", "NA"]


def test_in_group_levels():
    sec = pd.Series(["40", "45", "60", "NA", "40"])
    grp = pd.Series(["4010", "4520", "6010", "NA", "4040"])
    assert list(sr.in_group(sec, grp, sr.HYPER)) == [True, True, False, False, True]
    assert list(sr.in_group(sec, grp, sr.REAL_ESTATE)) == [False, False, True, False, True]
    assert list(sr.in_group(sec, grp, sr.NONFIN)) == [False, True, True, False, False]
    assert list(sr.in_group(sec, grp, sr.MARKET)) == [True, True, True, False, True]


def test_ltm_needs_consecutive_quarters_and_outcome_is_forward():
    qs = ["2000Q1", "2000Q2", "2000Q3", "2000Q4", "2001Q1", "2001Q2", "2001Q3", "2001Q4", "2002Q1"]
    fq = pd.DataFrame({"gvkey": "1", "datacqtr": qs, "datadate": pd.date_range("2000-03-31", periods=9, freq="QE"),
                       "saleq": 100.0, "revtq": np.nan, "oibdpq": [10, 10, 10, 10, 20, 20, 20, 20, 20.0],
                       "ibq": 5.0, "ceqq": 200.0, "atq": 1000.0, "dlttq": 100.0, "dlcq": 0.0})
    W, cols = sr.firm_wide(fq)
    assert np.isnan(W["E"].iloc[0, 2])                      # three quarters only
    assert W["E"].iloc[0, 3] == 40.0
    y = sr.firm_outcome(W, "d_ebitda", 4)
    assert y.loc["1", pd.Period("2000Q4", "Q")] == pytest.approx((80 - 40) / 400)


def test_pair_sign_is_long_minus_short():
    m = pd.period_range("2015-01", periods=3, freq="M")
    df = pd.DataFrame({"m": np.repeat(m, 4), "gsector": ["45", "45", "35", "35"] * 3, "ggroup": "x",
                       "x": [0.03, 0.01, 0.0, 0.0] * 3})
    p = sr.pair_returns(df, "x", sr.RULES["R1"], 1, None)
    assert np.allclose(p.to_numpy(), 0.02)


def test_centred_uses_only_known_outcomes():
    y = pd.Series(np.r_[np.zeros(20), np.full(10, 5.0)], index=pd.period_range("2000Q1", periods=30, freq="Q"))
    c = sr.centred(y, 4)
    assert c.iloc[20] == pytest.approx(5.0)  # the jump is not in the known mean yet


def test_score_recovers_a_real_signal_and_rejects_noise():
    rng = np.random.default_rng(3)
    idx = pd.period_range("1994Q1", periods=128, freq="Q")
    z = pd.Series(rng.normal(size=128), index=idx)
    y_real = 0.5 * z + rng.normal(scale=0.5, size=128)
    y_null = pd.Series(rng.normal(size=128), index=idx)
    r = sr.score(y_real, z, None, 1, sr.OOS_START_Q, sr.CYCLE_WINDOWS, 3)
    n = sr.score(y_null, z, None, 1, sr.OOS_START_Q, sr.CYCLE_WINDOWS, 3)
    assert r["P1"] and r["oos"]["t"] > 3
    assert n["oos"]["p"] > 0.01
