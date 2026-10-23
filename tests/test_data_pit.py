"""Tests for hy.data.pit and hy.data.records: one store, one guard, one LookAheadError (design: data module, step 1)."""

from datetime import datetime

import pandas as pd
import pytest

from hy import backtest, forecasts, inputs, outputs, walkforward
from hy.data import pit, records

T = datetime(2024, 6, 30)


def test_one_lookahead_error_everywhere():
    for mod in (inputs, backtest, walkforward, forecasts, outputs):
        assert mod.LookAheadError is pit.LookAheadError
    # Old callers caught RuntimeError (inputs) or AssertionError (backtest, walkforward); both still work.
    assert issubclass(pit.LookAheadError, RuntimeError) and issubclass(pit.LookAheadError, AssertionError)


def test_inputs_reexports_the_records_and_the_store():
    assert inputs.IssuerFinancials is records.IssuerFinancials
    assert inputs.Tranche is records.Tranche and inputs.Stamped is records.Stamped
    assert inputs.PointInTimeStore is pit.PointInTimeStore


def test_guard_times_ignores_missing_and_flags_late():
    pit.guard_times([T, None, pd.NaT], T, "x")
    with pytest.raises(pit.LookAheadError, match="1 value"):
        pit.guard_times([T, datetime(2024, 7, 1)], T, "x")


def test_guard_frame_needs_the_column():
    pit.guard_frame(pd.DataFrame(), T, "empty")  # nothing to prove
    with pytest.raises(pit.LookAheadError, match="no available_at"):
        pit.guard_frame(pd.DataFrame({"x": [1]}), T, "f")
    with pytest.raises(pit.LookAheadError):
        pit.guard_frame(pd.DataFrame({"available_at": [datetime(2024, 7, 2)]}), T, "f")


def test_guard_records_names_the_late_keys():
    ok = records.Stamped("a", T, T)
    late = records.Stamped("b", T, datetime(2024, 7, 1))
    pit.guard_records([ok], T)
    with pytest.raises(pit.LookAheadError, match="b"):
        pit.guard_records([ok, late], T)


def test_data_unavailable_carries_kind_and_key():
    e = pit.DataUnavailable("financials", "OPI", "no four consecutive quarters")
    assert e.kind == "financials" and e.key == "OPI" and "OPI" in str(e)
