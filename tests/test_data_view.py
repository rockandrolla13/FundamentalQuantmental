"""Tests for hy.data.view.DataView: one decision time, filtered and guarded reads, memoised (design: data module,
step 4)."""

from datetime import datetime

import pandas as pd
import pytest

from hy.data import records, sources
from hy.data.pit import DataUnavailable, LookAheadError
from hy.data.view import DataView

T = datetime(2026, 9, 18)
ISS = records.Issuer("ABC", gvkey="000001", cik="1")


def _fin(q_end, avail, revenue):
    return records.IssuerFinancials("000001", q_end, avail, revenue=revenue)


def _source(**kw):
    base = dict(issuers=[ISS])
    base.update(kw)
    return sources.FakeSource(**base)


def test_financials_are_as_known_at_the_decision_time():
    # Q2 first filed in August at 100, restated in October at 90: in September the view sees 100.
    src = _source(financials=[_fin(datetime(2026, 6, 30), datetime(2026, 8, 1), 100.0),
                              _fin(datetime(2026, 6, 30), datetime(2026, 10, 1), 90.0),
                              _fin(datetime(2026, 9, 30), datetime(2026, 11, 1), 120.0)])
    got = DataView(src, T).financials(ISS)
    assert [r.revenue for r in got] == [100.0]
    assert [r.revenue for r in DataView(src, datetime(2026, 12, 1)).financials(ISS)] == [90.0, 120.0]


def test_observations_stop_at_the_decision_time():
    obs = pd.DataFrame({"cusip": ["X", "X"], "date": [datetime(2026, 9, 17), datetime(2026, 9, 18)],
                        "price": [99.0, 98.0], "yield": [0.07, 0.071], "n_trades": [2, 2], "par_volume": [1e6, 1e6],
                        "available_at": [datetime(2026, 9, 18), datetime(2026, 9, 19)]})
    bond = records.Bond("X", "ABC", 0.06, datetime(2031, 1, 1), "senior_unsecured", True, False)
    got = DataView(_source(bonds=[bond], observations=obs), T).observations([bond], datetime(2026, 9, 1))
    assert got["price"].tolist() == [99.0]


def test_a_source_that_leaks_is_caught():
    class Leaky(sources.FakeSource):
        def curve(self, on):
            return records.Curve("UST", on, datetime(2026, 9, 30), tenors=(5.0,), yields=(0.04,))
    with pytest.raises(LookAheadError):
        DataView(Leaky(issuers=[ISS]), T).curve()


def test_reads_are_memoised_and_at_gives_a_fresh_view():
    calls = []

    class Counting(sources.FakeSource):
        def issuers(self, tickers):
            calls.append(tuple(tickers))
            return super().issuers(tickers)
    v = DataView(Counting(issuers=[ISS]), T)
    assert v.issuer("ABC") is v.issuer("ABC") and calls == [("ABC",)]
    v2 = v.at(datetime(2026, 12, 31))
    assert v2.decision_time == datetime(2026, 12, 31) and v2.source is v.source
    v2.issuer("ABC")
    assert len(calls) == 2


def test_missing_data_raises_data_unavailable():
    with pytest.raises(DataUnavailable):
        DataView(_source(), T).issuer("ZZZ")


def test_panels_are_filtered_by_available_at():
    p = pd.DataFrame({"gvkey": ["1", "1"], "x": [1, 2],
                      "available_at": [datetime(2026, 9, 1), datetime(2026, 10, 1)]})
    v = DataView(_source(panels={"leverage": p}), T)
    assert v.panel("leverage")["x"].tolist() == [1]
