"""Tests for scripts/lev_tests.py, tests L1 and L2 of docs/decisions/2026-10-30-revenue-leverage-and-negative-equity.md."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import lev_tests as lt  # noqa: E402
from hy.state import LEV_CAP  # noqa: E402


def _row(**kw) -> dict:
    base = {"gvkey": "1", "datadate": "2015-12-31", "fyear": 2015, "sale": 1000.0, "oibdp": 50.0, "dltt": 500.0, "dlc": 0.0,
            "ceq": 100.0, "at": 2000.0, "dlrsn": None, "dldte": pd.NaT, "gsector": "20"}
    return {**base, **kw}


def _synthetic(b_rev: float = 0.0, b_book: float = 0.0, seed: int = 1, per_year: int = 500) -> pd.DataFrame:
    """Firm-years with a planted effect of debt / revenue (inside EBITDA <= 0) and of the negative equity flag."""
    rng = np.random.default_rng(seed)
    n = per_year * (lt.LAST_YEAR - lt.FIRST_YEAR + 1)
    fyear = np.repeat(np.arange(lt.FIRST_YEAR, lt.LAST_YEAR + 1), per_year)
    neg_e = rng.random(n) < 0.5
    book_neg = rng.random(n) < 0.3
    debt = np.exp(rng.normal(6.5, 0.5, n)).clip(150.0)
    sale = debt / np.exp(rng.normal(0.0, 1.0, n))
    oibdp = np.where(neg_e, -0.05 * sale, debt / rng.uniform(4.5, 12.0, n))
    logit = -2.5 + b_rev * neg_e * np.log(debt / sale) + b_book * book_neg
    fail = rng.random(n) < 1.0 / (1.0 + np.exp(-logit))
    datadate = pd.to_datetime(fyear.astype(str) + "-12-31")
    return pd.DataFrame({"gvkey": np.arange(n).astype(str), "datadate": datadate, "fyear": fyear, "sale": sale, "oibdp": oibdp,
                         "dltt": debt, "dlc": 0.0, "ceq": np.where(book_neg, -100.0, 100.0), "at": debt * 2.0,
                         "dlrsn": np.where(fail, "02", None),
                         "dldte": pd.Series(datadate + pd.Timedelta(days=500)).where(fail, pd.NaT), "gsector": "20"})


def test_negative_ebitda_reads_as_the_cap():
    rows = lt.build_rows(pd.DataFrame([_row(oibdp=-10.0), _row(gvkey="2", oibdp=50.0)]))
    assert rows.set_index("gvkey").loc["1", "lev"] == LEV_CAP
    assert rows.set_index("gvkey").loc["2", "lev"] == 10.0
    assert rows.set_index("gvkey").loc["1", "neg_ebitda"] and not rows.set_index("gvkey").loc["2", "neg_ebitda"]


def test_universe_filters():
    raw = [_row(gvkey="small", dltt=100.0), _row(gvkey="low_lev", oibdp=500.0), _row(gvkey="bank", gsector="40.0"),
           _row(gvkey="utility", gsector="55"), _row(gvkey="no_sale", sale=0.0), _row(gvkey="kept")]
    assert list(lt.build_rows(pd.DataFrame(raw))["gvkey"]) == ["kept"]


def test_event_window_and_codes():
    raw = [_row(gvkey="in", dlrsn="02", dldte="2017-01-01"), _row(gvkey="float_code", dlrsn=3.0, dldte="2017-01-01"),
           _row(gvkey="merger", dlrsn="01", dldte="2017-01-01"), _row(gvkey="late", dlrsn="02", dldte="2020-01-01"),
           _row(gvkey="gone", dlrsn="02", dldte="2016-01-15")]
    y = lt.build_rows(pd.DataFrame(raw)).set_index("gvkey")["y"]
    assert y.to_dict() == {"in": 1, "float_code": 1, "merger": 0, "late": 0}    # "gone" left before the decision time


def test_no_look_ahead_in_the_split():
    rows = lt.build_rows(_synthetic())
    for a, b in lt.CYCLE_WINDOWS.values():
        train, test = lt.window_split(rows, a, b)
        assert (train["outcome_available_at"] < pd.Timestamp(a)).all()
        assert test["available_at"].between(pd.Timestamp(a), pd.Timestamp(b)).all()
        assert len(train) and len(test)


def test_planted_debt_to_revenue_passes_l1_and_noise_fails():
    spec = lt.TESTS["L1_debt_to_revenue"]
    assert lt.run_test(lt.build_rows(_synthetic(b_rev=1.0)), spec, n_boot=200)["passed"]
    assert not lt.run_test(lt.build_rows(_synthetic(b_rev=0.0)), spec, n_boot=200)["passed"]


def test_planted_negative_equity_passes_l2_and_wrong_sign_fails():
    spec = lt.TESTS["L2_negative_book_equity"]
    assert lt.run_test(lt.build_rows(_synthetic(b_book=1.5)), spec, n_boot=200)["passed"]
    wrong = lt.run_test(lt.build_rows(_synthetic(b_book=-1.5)), spec, n_boot=200)
    assert not wrong["passed"] and wrong["windows_passed"] == 0


def test_a_window_without_events_gives_no_reading():
    rows = lt.build_rows(_synthetic()).assign(y=0)
    res = lt.run_test(rows, lt.TESTS["L2_negative_book_equity"], n_boot=10)
    assert not res["passed"] and res["pooled_gain"] is None
