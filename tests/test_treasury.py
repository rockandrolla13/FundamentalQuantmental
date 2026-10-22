import numpy as np
import pandas as pd
import pytest

from hy.sources import treasury as tr

HEADER = 'Date,"1 Mo","1.5 Month","2 Mo","3 Mo","4 Mo","6 Mo","1 Yr","2 Yr","3 Yr","5 Yr","7 Yr","10 Yr","20 Yr","30 Yr"'
CSV = "\n".join(
    [
        HEADER,
        "09/17/2026,4.00,4.00,4.00,4.00,4.00,4.00,3.80,3.60,3.60,3.70,3.90,4.10,4.60,4.70",
        "09/15/2026,4.10,4.10,4.10,4.10,4.10,4.10,3.90,3.70,3.70,3.80,4.00,4.20,4.70,4.80",
    ]
)


def test_parse_csv_tenors_decimals_order_and_available_at():
    c = tr.parse_csv(CSV)
    assert list(c.index) == [pd.Timestamp("2026-09-15"), pd.Timestamp("2026-09-17")]
    assert set(tr.TENOR_COLUMNS) <= set(c.columns)
    assert c.loc["2026-09-17", 5.0] == pytest.approx(0.037)
    assert c.loc["2026-09-17", 1 / 12] == pytest.approx(0.04)
    assert c.loc["2026-09-17", "available_at"] == pd.Timestamp("2026-09-18")


def test_parse_csv_tolerates_missing_tenor_column():
    text = CSV.replace(',"1.5 Month"', "").replace("4.00,4.00,4.00,4.00,4.00,4.00", "4.00,4.00,4.00,4.00,4.00", 1)
    text = text.replace("4.10,4.10,4.10,4.10,4.10,4.10", "4.10,4.10,4.10,4.10,4.10", 1)
    c = tr.parse_csv(text)
    assert c[1.5 / 12].isna().all()
    assert c.loc["2026-09-17", 30.0] == pytest.approx(0.047)


def test_interpolate_inside_and_flat_beyond_ends():
    row = tr.parse_csv(CSV).loc[pd.Timestamp("2026-09-17")]
    assert tr.interpolate(row, 4.0) == pytest.approx((0.036 + 0.037) / 2)
    assert tr.interpolate(row, 6.0) == pytest.approx(0.038)
    assert tr.interpolate(row, 0.01) == pytest.approx(0.04)  # flat below 1 month
    assert tr.interpolate(row, 40.0) == pytest.approx(0.047)  # flat beyond 30 years
    assert tr.interpolate(row, np.array([2.0, 10.0])) == pytest.approx([0.036, 0.041])


def test_curve_on_picks_latest_date_not_after_target_and_caches(tmp_path):
    calls = []

    def fetch(url):
        calls.append(url)
        return CSV

    c = tr.curve_on("2026-09-16", cache_root=tmp_path, fetch=fetch)
    assert c.name == pd.Timestamp("2026-09-15")  # 09-17 is after the target
    assert c["available_at"] == pd.Timestamp("2026-09-16")
    assert tr.curve_on("2026-09-17", cache_root=tmp_path, fetch=fetch).name == pd.Timestamp("2026-09-17")
    assert len(calls) == 1 and "2026" in calls[0]
    assert tr.cache_path(tmp_path, 2026).exists()


def test_curve_on_refetches_stale_current_year_cache(tmp_path):
    texts = iter([CSV, CSV + "\n09/21/2026,4,4,4,4,4,4,4,4,4,4,4,4,4,4"])
    c = tr.curve_on("2026-09-15", cache_root=tmp_path, fetch=lambda u: next(texts))
    assert c.name == pd.Timestamp("2026-09-15")
    assert tr.curve_on("2026-09-22", cache_root=tmp_path, fetch=lambda u: next(texts)).name == pd.Timestamp("2026-09-21")
