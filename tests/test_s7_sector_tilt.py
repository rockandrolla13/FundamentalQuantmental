"""Tests for scripts/s7_sector_tilt.py, signal S7 on the TRACE HY panel (decision 2026-10-24-s7-sector-tilt)."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import s7_sector_tilt as s7  # noqa: E402


def _panel_and_macro(n=60, seed=0):
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2010-01-31", periods=n, freq="ME")
    macro = pd.DataFrame(rng.normal(size=(n, 2)), index=dates, columns=["a", "b"])
    rows = []
    for j, beta in (("10", 1.0), ("20", -1.0)):
        for d in dates:
            rows.append({"date": d, "sector": j, "eta": beta * macro.at[d, "a"] + 0.05 * rng.normal()})
    return pd.DataFrame(rows), macro


def test_eta_hat_uses_no_later_months():
    panel, macro = _panel_and_macro()
    a = s7.eta_hat(panel, macro, cols=("a", "b"))
    m2 = macro.copy()
    m2.iloc[50:] += 10.0  # change the future only
    p2 = panel.copy()
    p2.loc[p2["date"] >= macro.index[50], "eta"] += 5.0
    b = s7.eta_hat(p2, m2, cols=("a", "b"))
    early = panel["date"] < macro.index[50]
    pd.testing.assert_series_equal(a[early], b[early])
    assert a[: s7.MIN_TRAIN - 1].isna().all()


def test_eta_hat_learns_the_sector_loading():
    panel, macro = _panel_and_macro(n=120)
    h = s7.eta_hat(panel, macro, cols=("a", "b"))
    late = panel["date"] > macro.index[80]
    assert np.corrcoef(h[late], panel.loc[late, "eta"])[0, 1] > 0.95


def test_sector_month_is_relative_and_point_in_time():
    d = pd.Timestamp("2015-06-30")
    bonds = pd.DataFrame({"date": d, "cusip": [f"c{i}" for i in range(20)], "gvkey": ["1"] * 10 + ["2"] * 10,
                          "g_spread": [0.03] * 10 + [0.06] * 10, "total": [0.02] * 10 + [0.04] * 10,
                          "tsy_ret": 0.0, "cost_rt": 0.01})
    gics = pd.DataFrame({"gvkey": ["1", "2", "2"], "gsector": ["10", "20", "45"],
                         "indfrom": pd.to_datetime(["2000-01-01", "2000-01-01", "2016-01-01"]),
                         "indthru": pd.to_datetime([None, "2015-12-31", None]),
                         "available_at": pd.to_datetime(["2000-01-01", "2000-01-01", "2016-01-01"])})
    s = s7.sector_month(bonds, gics).set_index("sector")
    assert set(s.index) == {"10", "20"}  # the 2016 record of gvkey 2 is not known in 2015
    assert s.at["20", "eta"] == pytest.approx(np.log(2) / 2)
    assert s.at["10", "y"] == pytest.approx(-0.01)


def test_tercile_spread_subtracts_both_legs():
    d = pd.Timestamp("2015-06-30")
    df = pd.DataFrame({"date": d, "s7": np.arange(6.0), "y": np.arange(6.0) / 100, "cost": 0.005})
    r = s7.tercile_spread(df, "s7").iloc[0]
    assert r["gross"] == pytest.approx(0.04)
    assert r["net"] == pytest.approx(0.03)
