"""Offline tests for hy.sources.forecast_sources (methodology Section 5.4). Fixtures are inline; no network."""

from __future__ import annotations

import io
import logging
import zipfile
from datetime import datetime

import numpy as np
import pandas as pd
import pytest

from hy.sources import forecast_sources as fs

# ---------------------------------------------------------------- SPF bins -> quantiles


def test_bin_quantiles_uniform_inside_bins():
    # four bins [0,1), [1,2), [2,3), [3,4) with 10%, 40%, 40%, 10%
    q10, q50, q90 = fs.bin_quantiles([0, 1, 2, 3], [1, 2, 3, 4], [10, 40, 40, 10])
    assert q10 == pytest.approx(1.0)   # cdf reaches 0.10 at the end of bin 1
    assert q50 == pytest.approx(2.0)   # symmetric histogram
    assert q90 == pytest.approx(3.0)


def test_bin_quantiles_inside_one_bin_and_empty_bins():
    # all mass in [2,3): quantiles are linear inside it; empty bins do not move them
    q10, q50, q90 = fs.bin_quantiles([0, 1, 2, 3], [1, 2, 3, 4], [0, 0, 100, 0])
    assert (q10, q50, q90) == pytest.approx((2.1, 2.5, 2.9))


def test_bin_edges_open_tails_take_neighbour_width():
    lo, hi = fs.bin_edges((4.0, 3.5, 3.0))  # bins: [4,4.5) [3.5,4) [3,3.5) [2.5,3)
    assert lo.tolist() == [2.5, 3.0, 3.5, 4.0]
    assert hi.tolist() == [3.0, 3.5, 4.0, 4.5]


def test_spf_bin_rows_hand_made_sheet():
    # PRCCPI era 2007Q1+: 10 bins, high to low; put 50% in [2.0,2.5) and 50% in [2.5,3.0) for the current year
    cur = [0, 0, 0, 50, 50, 0, 0, 0, 0, 0]
    nxt = [0, 0, 0, 0, 100, 0, 0, 0, 0, 0]
    sheet = pd.DataFrame([[2024, 3, *cur, *nxt]], columns=["YEAR", "QUARTER", *[f"PRCCPI{i}" for i in range(1, 21)]])
    cal = {(2024, 3): (pd.Timestamp("2024-08-13"), pd.Timestamp("2024-08-16"))}
    rows = fs.spf_bin_rows({"PRCCPI": sheet}, cal)
    assert [r.horizon_q for r in rows] == [1, 5]           # Q4 2024 and Q4 2025 from a Q3 survey
    r0 = rows[0]
    assert r0.method == "survey_bins" and r0.source == "spf_prob" and r0.variable == "cpi"
    assert r0.q50 == pytest.approx(0.025) and r0.q10 == pytest.approx(0.021) and r0.q90 == pytest.approx(0.029)
    assert rows[1].q50 == pytest.approx(0.0225)
    assert r0.vintage == datetime(2024, 8, 13) and r0.available_at == datetime(2024, 8, 17)


def test_spf_release_calendar_and_fallback():
    text = "Survey  Deadline  Release\n\n2026 Q1             3/2/26**            3/6/26** \n     Q2   5/12/26  5/15/26\n"
    cal = fs.parse_spf_release_dates(text)
    assert cal[(2026, 2)] == (pd.Timestamp("2026-05-12"), pd.Timestamp("2026-05-15"))
    v, a = fs.spf_timing(2026, 1, cal)
    assert (v, a) == (datetime(2026, 3, 2), datetime(2026, 3, 7))
    v, a = fs.spf_timing(1985, 3, cal)                     # not in calendar: documented pattern
    assert v == datetime(1985, 8, 15) and a == datetime(1985, 9, 1)


def test_spf_median_cpi_year_on_year():
    # constant 2% annualised quarterly CPI -> 2% year on year at every horizon
    cpi = pd.DataFrame([[y, q, *[2.0] * 6] for y, q in [(2025, 4), (2026, 1), (2026, 2)]],
                       columns=["YEAR", "QUARTER", *[f"CPI{i}" for i in range(1, 7)]])
    rows = [r for r in fs.spf_median_rows(None, None, cpi, {}) if r.vintage.year == 2026 and r.vintage.month == 5]
    assert {r.horizon_q for r in rows} == {0, 1, 2, 3, 4}
    assert all(r.point == pytest.approx(0.02) for r in rows)


# ---------------------------------------------------------------- FOMC SEP

SEP_HTML = """<table>
<tr><th rowspan=2>Variable</th><th colspan=3>Median1</th><th colspan=3>Central Tendency2</th><th colspan=3>Range3</th></tr>
<tr><th>2026</th><th>2027</th><th>Longer run</th><th>2026</th><th>2027</th><th>Longer run</th><th>2026</th><th>2027</th><th>Longer run</th></tr>
<tr><td>Change in real GDP</td><td>2.0</td><td>1.8</td><td>1.8</td><td>1.9&#8211;2.1</td><td>1.7&#8211;2.0</td><td>1.8&#8211;1.9</td><td>1.5&#8211;2.4</td><td>1.2&#8211;2.5</td><td>1.6&#8211;2.2</td></tr>
<tr><td>June projection</td><td>9.9</td><td>9.9</td><td>9.9</td><td>9.9&#8211;9.9</td><td>9.9&#8211;9.9</td><td>9.9&#8211;9.9</td><td>9.9&#8211;9.9</td><td>9.9&#8211;9.9</td><td>9.9&#8211;9.9</td></tr>
<tr><td>Core PCE inflation4</td><td>2.8</td><td>2.4</td><td></td><td>2.7&#8211;2.9</td><td>2.3&#8211;2.5</td><td></td><td>2.5&#8211;3.0</td><td>2.1&#8211;2.7</td><td></td></tr>
<tr><td>Federal funds rate</td><td>3.6</td><td>3.1</td><td>3.0</td><td>3.4&#8211;3.9</td><td>2.9&#8211;3.4</td><td>2.9&#8211;3.4</td><td>2.9&#8211;4.1</td><td>2.4&#8211;3.9</td><td>2.6&#8211;3.9</td></tr>
</table>"""


def test_sep_range_mapping():
    t = fs.parse_sep_table(SEP_HTML)
    assert set(t["variable"]) == {"gdp_growth", "policy_rate"}  # core PCE and the previous SEP are dropped
    assert set(t["year"]) == {2026, 2027}                         # "Longer run" dropped
    rows = fs.sep_rows(t, "2026-09-16")
    ff = {r.horizon_q: r for r in rows if r.variable == "policy_rate"}
    assert ff[1].method == "dot_range" and ff[5].method == "dot_range"   # Q4 2026, Q4 2027 from Q3 2026
    assert (ff[1].q10, ff[1].q50, ff[1].q90, ff[1].point) == pytest.approx((0.029, 0.036, 0.041, 0.036))
    assert ff[3].method == "dot_range_interp" and ff[3].point == pytest.approx((0.036 + 0.031) / 2)
    assert set(ff) == {1, 2, 3, 4, 5}
    assert ff[1].vintage == datetime(2026, 9, 16) and ff[1].available_at == datetime(2026, 9, 17)


# ---------------------------------------------------------------- Treasury forwards


def _curve(fn, date="2026-10-20"):
    from hy.sources.treasury import TENOR_COLUMNS

    row = pd.Series({t: fn(t) for t in TENOR_COLUMNS})
    row["available_at"] = pd.Timestamp(date) + pd.Timedelta(1, unit="D")
    row.name = pd.Timestamp(date)
    return row


def test_forwards_flat_curve_equal_par():
    fw = fs.forwards_from_par(_curve(lambda t: 0.04), range(9))
    for var in ("policy_rate", "y2", "y10"):
        assert np.allclose(fw[var], 0.04, atol=1e-10), var


def test_forwards_upward_curve_rise():
    fw = fs.forwards_from_par(_curve(lambda t: 0.03 + 0.002 * min(t, 10.0)), range(9))
    for var in ("policy_rate", "y2", "y10"):
        assert (np.diff(fw[var]) > 0).all(), var
    # horizon 0 reprices the par curve: the spot 2-year and 10-year par yields come back
    assert fw.loc[0, "y2"] == pytest.approx(0.034, abs=1e-9)
    assert fw.loc[0, "y10"] == pytest.approx(0.05, abs=1e-9)


def test_ust_forward_rows_timing_point_only():
    rows = fs.ust_forward_rows(_curve(lambda t: 0.04), range(3))
    assert len(rows) == 9 and {r.source for r in rows} == {"ust_forward"}
    assert all(np.isnan(r.q10) and np.isnan(r.q90) and r.method == "market_implied" for r in rows)
    assert all(r.available_at == datetime(2026, 10, 21) for r in rows)


# ---------------------------------------------------------------- SLOOS

SLOOS_XML = """<x><kf:Series SERIES_NAME="SUBLPDCILS_N.Q" UNIT="Percentage">
<frb:Obs OBS_STATUS="A" OBS_VALUE="8.1" TIME_PERIOD="2026-06-30" />
<frb:Obs OBS_STATUS="A" OBS_VALUE="0.0" TIME_PERIOD="2026-09-30" />
</kf:Series></x>"""


def test_sloos_rows_and_timing():
    s = fs.parse_sloos_xml(SLOOS_XML)
    rows = fs.sloos_rows(s, {pd.Period("2026Q3"): pd.Timestamp("2026-08-03")})
    assert [r.point for r in rows] == pytest.approx([0.081, 0.0])
    assert rows[0].vintage == datetime(2026, 4, 1) and rows[0].available_at == datetime(2026, 6, 1)  # rule
    assert rows[1].available_at == datetime(2026, 8, 4)                                              # known date
    assert all(r.horizon_q == 0 and r.method == "survey_realised" for r in rows)


def test_load_sloos_offline_zip(tmp_path):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("SLOOS_data.xml", SLOOS_XML)
    pages = {fs.SLOOS_ZIP_URL: buf.getvalue(), fs.SLOOS_PAGE_URL: b"<p>Last Update: August 03, 2026</p>"}
    rows = fs.load_sloos(tmp_path, fetch=pages.__getitem__)
    assert rows[-1].available_at == datetime(2026, 8, 4)


# ---------------------------------------------------------------- TRACE benchmark


def _bonds():
    as_of = pd.Timestamp("2026-10-19")
    return pd.DataFrame({
        "yield": [0.07, 0.08, 0.09, 0.16, 0.30],
        "price": [100.0, 98.0, 95.0, 75.0, 40.0],
        "maturity": [as_of + pd.DateOffset(years=y) for y in (3, 5, 7, 4, 2)],
        "as_of": [as_of] * 5,
        "available_at": [as_of + pd.DateOffset(days=1)] * 5,
    })


def test_trace_hy_rows_spread_and_distress():
    rows = {r.variable: r for r in fs.trace_hy_rows(_bonds(), _curve(lambda t: 0.04, "2026-10-19"))}
    assert rows["hy_spread"].point == pytest.approx(0.04)      # median of 3%, 4%, 5% (price >= 80 only)
    assert rows["distress_ratio"].point == pytest.approx(0.4)  # 12% and 26% exceed 10%
    assert rows["hy_spread"].available_at == datetime(2026, 10, 20)
    assert rows["hy_spread"].source == "trace_hy_benchmark" and rows["hy_spread"].method == "market_implied"


# ---------------------------------------------------------------- availability, stubs, load_all


def test_available_at_never_precedes_vintage():
    t = fs.parse_sep_table(SEP_HTML)
    rows = (fs.sep_rows(t, "2026-09-16") + fs.ust_forward_rows(_curve(lambda t: 0.04))
            + fs.sloos_rows(fs.parse_sloos_xml(SLOOS_XML))
            + fs.trace_hy_rows(_bonds(), _curve(lambda t: 0.04, "2026-10-19")))
    assert rows and all(r.available_at > r.vintage for r in rows)


STUBS = [fs.load_fed_funds_futures, fs.load_agency_default_forecasts, fs.load_ice_hy_oas, fs.load_sector_decks,
         fs.load_sellside_consensus, fs.load_management_guidance]


@pytest.mark.parametrize("loader", STUBS)
def test_stubs_return_empty_and_log(loader, caplog):
    with caplog.at_level(logging.WARNING, logger=fs.__name__):
        assert loader() == []
    msgs = [r.getMessage() for r in caplog.records]
    assert len(msgs) == 1 and msgs[0].startswith("stub: ") and "FALLBACK_ORDER" in msgs[0]
    assert loader.__doc__.startswith("Stub.") and "fill" in loader.__doc__.lower()


def test_load_all_honours_decision_time(tmp_path):
    sep_old, sep_new = "20260617", "20260916"
    cal = f'<a href="fomcprojtabl{sep_old}.htm"></a><a href="fomcprojtabl{sep_new}.htm"></a>'.encode()
    pages = {fs.FOMC_CALENDAR_URL: cal,
             fs.SEP_URL.format(date=sep_old): SEP_HTML.encode(), fs.SEP_URL.format(date=sep_new): SEP_HTML.encode()}
    opts = {"fomc_sep": {"fetch": pages.__getitem__},
            "trace_hy_benchmark": {"bonds": _bonds(), "curve_row": _curve(lambda t: 0.04, "2026-10-19")}}
    decision = datetime(2026, 9, 16, 23, 0)   # the September SEP is public only from 2026-09-17 00:00
    reg = fs.load_all(decision, tmp_path, sources=["fomc_sep", "trace_hy_benchmark", "ice_hy_oas"], options=opts)
    df = reg.frame()
    assert (pd.to_datetime(df["available_at"]) <= decision).all()
    assert set(pd.to_datetime(df["vintage"]).dt.strftime("%Y%m%d")) == {sep_old}
    st = fs.source_status().set_index("source")
    assert st.loc["fomc_sep", "status"] == "live" and st.loc["fomc_sep", "rows_after_decision_time"] > 0
    assert st.loc["trace_hy_benchmark", "rows"] == 0                     # released 2026-10-20, after decision
    assert st.loc["ice_hy_oas", "status"] == "stub"
    # the registry read agrees
    assert reg.as_of(decision)["available_at"].max() <= decision


def test_load_all_marks_failed_live_source_stubbed(tmp_path):
    def boom(url):
        raise OSError("network down")

    fs.load_all(datetime(2026, 10, 21), tmp_path, sources=["spf"], options={"spf": {"fetch": boom}})
    st = fs.source_status()
    assert st.loc[0, "status"].startswith("stubbed: OSError") and st.loc[0, "rows"] == 0
