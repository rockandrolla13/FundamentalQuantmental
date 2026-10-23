"""Tests for the data kinds that used to bypass the view (design: data module; review finding AR-DEP-001).

Each former side door now has a source method, a view method that filters or guards it, and a FakeSource
implementation. These tests prove the point-in-time rule on each one with made-up data.
"""

import sys
from datetime import datetime
from pathlib import Path

import pytest

from hy.data import records, sources
from hy.data.pit import DataUnavailable, LookAheadError
from hy.data.view import DataView

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import process  # noqa: E402

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
