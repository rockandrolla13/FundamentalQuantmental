"""Tests for the data kinds that used to bypass the view (design: data module; review finding AR-DEP-001).

Each former side door now has a source method, a view method that filters or guards it, and a FakeSource
implementation. These tests prove the point-in-time rule on each one with made-up data.
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import pytest

from hy.data import records, sources
from hy.data.pit import DataUnavailable, LookAheadError
from hy.data.source import FORECAST_STATUS_COLUMNS
from hy.data.view import DataView
from hy.forecasts import ForecastRegistry, ForecastRow

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import process  # noqa: E402
import scenarios  # noqa: E402

T = datetime(2026, 9, 18)
ISS = records.Issuer("ABC", gvkey="000001", cik="1")


def _mv(q_end, reported, value):
    return records.MarketValue("ABC", q_end, reported, issuer_ticker="ABC", value=value, source=f"fake {q_end:%Y-%m}")


# ------------------------------------------------------------------ market value (framework F7.7)


def test_market_value_is_the_latest_quarter_reported_by_the_decision_time():
    src = sources.FakeSource(issuers=[ISS], market_values=[_mv(datetime(2026, 3, 31), datetime(2026, 5, 1), 900.0),
                                                           _mv(datetime(2026, 6, 30), datetime(2026, 8, 1), 1000.0),
                                                           _mv(datetime(2026, 9, 30), datetime(2026, 11, 1), 1100.0)])
    assert DataView(src, T).market_value(ISS).value == 1000.0
    assert process.market_value(DataView(src, T), ISS) == (1000.0, "fake 2026-06")


def test_market_value_from_a_leaky_source_is_caught():
    class Leaky(sources.FakeSource):
        def market_value(self, issuer, decision_time):
            return _mv(datetime(2026, 9, 30), datetime(2026, 11, 1), 1.0)
    with pytest.raises(LookAheadError):
        DataView(Leaky(issuers=[ISS]), T).market_value(ISS)


def test_a_missing_market_value_is_nan_with_a_reason_not_a_crash():
    v, why = process.market_value(DataView(sources.FakeSource(issuers=[ISS]), T), ISS)
    assert v != v and "no equity price" in why
    with pytest.raises(DataUnavailable):
        DataView(sources.FakeSource(issuers=[ISS]), T).market_value(ISS)


# ------------------------------------------------------------------ HY index level and forecast status (F6, Section 5.4)


def _lvl(day, spread, distress=0.05):
    d = datetime.fromisoformat(day)
    return records.IndexLevel("HY", d, d + timedelta(days=1), spread=spread, distress=distress)


def test_phase_indicators_read_each_snapshot_as_published_then():
    end = datetime(2026, 9, 17)
    levels = [_lvl("2026-09-17", 0.0300), _lvl("2026-06-17", 0.0350), _lvl("2026-09-18", 0.9)]  # the last is future
    levels += [_lvl(f"{2026 - y}-09-17", 0.04 + 0.001 * y) for y in range(1, 6)]
    view = DataView(sources.FakeSource(issuers=[ISS], index_levels=levels), end + timedelta(days=1))
    ind, snaps = scenarios.phase_indicators(view, pd.Timestamp(end), ForecastRegistry())
    assert snaps["hy_spread"].tolist() == pytest.approx([0.03, 0.035, 0.041, 0.042, 0.043, 0.044, 0.045])
    assert ind["hy_oas"]["change_3m"] == pytest.approx(-0.005)
    assert ind["distress_ratio"]["level"] == pytest.approx(0.05)


def test_a_missing_snapshot_is_nan_not_a_crash():
    view = DataView(sources.FakeSource(issuers=[ISS], index_levels=[_lvl("2026-09-17", 0.03)]), T)
    _, snaps = scenarios.phase_indicators(view, pd.Timestamp("2026-09-17"), ForecastRegistry())
    assert snaps["hy_spread"].iloc[0] == 0.03 and snaps["hy_spread"].iloc[1:].isna().all()


def test_forecast_status_counts_rows_known_at_the_decision_time():
    rows = [ForecastRow("spf", "gdp_growth", 1, datetime(2026, 8, 1), datetime(2026, 8, 15), 0.02),
            ForecastRow("spf", "gdp_growth", 1, datetime(2026, 11, 1), datetime(2026, 11, 15), 0.01)]
    st = DataView(sources.FakeSource(issuers=[ISS], forecasts=rows), T).forecast_status()
    assert list(st.columns) == list(FORECAST_STATUS_COLUMNS)
    assert st.iloc[0]["rows"] == 1 and st.iloc[0]["rows_after_decision_time"] == 1


# ------------------------------------------------------------------ balance sheet and schedules (F5; methodology 4.3, 4.7)


def _sheet(acc, as_of, accepted, debt=1000.0):
    return records.BalanceSheet(
        acc, as_of, accepted, issuer_ticker="ABC", accession=acc, debt=debt, debt_source="fake", cash=50.0,
        operating_lease_liability=200.0, finance_lease_liability=float("nan"), revolver_capacity=300.0,
        ladders={"operating_lease": records.Ladder("operating_lease", [40.0, 40.0, 40.0, 80.0], 1.0, 200.0, True),
                 "finance_lease": None, "purchase": None,
                 "debt": records.Ladder("debt", [100.0, 0.0, 400.0, 500.0], 1.0, 1000.0, True)})


def test_a_balance_sheet_filed_after_the_decision_is_refused():
    late = _sheet("Q3", datetime(2026, 9, 30), datetime(2026, 11, 1))
    with pytest.raises(LookAheadError):
        DataView(sources.FakeSource(issuers=[ISS], balance_sheets=[late]), T).balance_sheet(ISS, "Q3")


def test_the_clock_case_reads_the_balance_sheet_record():
    import clock_case  # noqa: PLC0415

    src = sources.FakeSource(issuers=[ISS], balance_sheets=[_sheet("Q2", datetime(2026, 6, 30), datetime(2026, 8, 1))])
    inputs = {"ticker": ("ABC", "input"), "name": ("ABC Co", "input"), "q": ("Q2", ""), "k": (None, ""),
              "ltm_ebitda": (400.0, ""), "ltm_revenue": (2000.0, ""), "annual_lease_cost": (40.0, ""),
              "interest_rate": (0.06, ""), "debt_tail_years": (5.0, ""), "rpo_total": (None, ""),
              "rpo_windows": ([], ""), "rpo_tail_years": (2.0, ""), "uncommenced_window": (None, ""),
              "uncommenced_term": (None, ""), "purchase": (None, ""), "run_rate_revenue": (2000.0, ""),
              "scenario_extra_lease": (None, ""), "recourse": (None, ""), "rating": (None, ""),
              "available_at": ("2026-08-01", "")}
    case = clock_case.build_case(inputs, DataView(src, T))
    assert case["ladders"]["debt"] == [100.0, 0.0, 400.0, 500.0]
    assert case["as_of"] == "2026-06-30" and case["revenue_clock"].startswith("skipped")
    assert case["metrics"]["obligations_total"] > 1000.0  # leases + debt + interest


# ------------------------------------------------------------------ filing text and reported cash flows (F2, F5; 3.2)


def _q(q_end, filed, cfo):
    return records.IssuerFinancials("000001", q_end, filed, revenue=100.0, operating_cash_flow=cfo, capex_total=10.0,
                                    cash_interest=5.0, cash_taxes=1.0)


def test_a_blank_quarter_is_filled_only_from_a_filing_public_by_the_decision_time():
    nan = float("nan")
    qs = [_q(datetime(2026, 3, 31), datetime(2026, 5, 1), 20.0), _q(datetime(2026, 6, 30), datetime(2026, 8, 1), nan)]
    early = records.ReportedCashFlow("ABC Q2", datetime(2026, 6, 30), datetime(2026, 8, 2), issuer_ticker="ABC",
                                     accession="A1", operating_cash_flow=30.0, capex=12.0)
    late = records.ReportedCashFlow("ABC Q2", datetime(2026, 6, 30), datetime(2026, 10, 2), issuer_ticker="ABC",
                                    accession="A2", operating_cash_flow=99.0)
    src = sources.FakeSource(issuers=[ISS], cash_flows=[late, early])
    got, filled = process.fill_cash_flow_gaps(qs, DataView(src, T), ISS)
    assert got[-1].operating_cash_flow == 30.0 and got[-1].capex_total == 10.0  # capex was not blank: kept
    assert filled == ["2026-06-30 from A1: operating_cash_flow"]
    got, filled = process.fill_cash_flow_gaps(qs, DataView(sources.FakeSource(issuers=[ISS], cash_flows=[late]), T), ISS)
    assert got[-1].operating_cash_flow != got[-1].operating_cash_flow and filled == []


def test_the_business_line_reads_the_filing_text_through_the_view():
    txt = ("Table of contents Item 1. Business 3 Item 1A. Risk Factors 9 ... Item 1. Business. "
           "Overview ABC runs hospitals in ten states. It earns fees from insurers. A third sentence.")
    src = sources.FakeSource(issuers=[ISS], texts=[records.FilingText("K1", datetime(2026, 2, 20), datetime(2026, 2, 20),
                                                                       issuer_ticker="ABC", accession="K1", text=txt)])
    inputs = {"k": ("K1", ""), "q": ("Q2", ""), "cik": ("1", "")}
    sells, where = process.business_text(inputs, DataView(src, T), ISS)
    assert sells == "ABC runs hospitals in ten states. It earns fees from insurers." and where == "10-K K1, Item 1"
    sells, where = process.business_text(inputs, DataView(sources.FakeSource(issuers=[ISS]), T), ISS)
    assert sells == "" and where.startswith("no filing text")


# ------------------------------------------------------------------ Treasury curve history (Section 3.6; pair step 7.5)


def test_the_curve_history_stops_at_the_decision_time():
    cs = [records.Curve("UST", datetime(2026, 9, d), datetime(2026, 9, d + 1), tenors=(2.0, 10.0), yields=(0.04, 0.045))
          for d in (16, 17, 18)]
    h = DataView(sources.FakeSource(issuers=[ISS], curves=cs), T).curve_history(datetime(2026, 1, 1))
    assert list(h.index) == [pd.Timestamp("2026-09-16"), pd.Timestamp("2026-09-17")]  # the 18th is public on the 19th
    assert list(h.columns) == [2.0, 10.0, "available_at"] and h.loc["2026-09-17", 10.0] == 0.045


# ------------------------------------------------------------------ realised outcomes (Section 11): future data on purpose


def _obs(days):
    return pd.DataFrame({"cusip": ["X"] * len(days), "date": [datetime(2026, 9, d) for d in days],
                         "price": [90.0 + d for d in days], "yield": [0.08] * len(days), "n_trades": [3] * len(days),
                         "par_volume": [1e6] * len(days), "available_at": [datetime(2026, 9, d + 1) for d in days]})


def test_realised_outcomes_read_after_the_decision_and_refuse_before_it():
    from hy.data.outcomes import RealisedOutcomes  # noqa: PLC0415

    out = RealisedOutcomes(sources.FakeSource(issuers=[ISS], observations=_obs([16, 17, 18, 25])), T)
    got = out.observations(["X"], datetime(2026, 9, 30))
    assert got["date"].tolist() == [pd.Timestamp("2026-09-18"), pd.Timestamp("2026-09-25")]
    with pytest.raises(ValueError):
        out.curve(datetime(2026, 9, 1))


def test_the_pipeline_cannot_reach_realised_outcomes():
    root = Path(__file__).resolve().parents[1]
    for f in ("scripts/process.py", "scripts/scenarios.py", "scripts/rv_pair.py", "scripts/clock_case.py",
              "hy/data/view.py", "hy/data/sources.py"):
        assert "outcomes" not in (root / f).read_text().replace("open_questions", ""), f
