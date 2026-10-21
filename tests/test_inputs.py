from datetime import datetime

import pytest

from hy.inputs import IssuerFinancials, LookAheadError, PointInTimeStore, assert_point_in_time


def _fin(ebitda, as_of, available_at):
    return IssuerFinancials(key="ACME", as_of=as_of, available_at=available_at, ebitda_reported=ebitda)


def test_view_hides_filing_before_release():
    q3 = _fin(100.0, datetime(2026, 9, 30), datetime(2026, 11, 5))
    store = PointInTimeStore([q3])
    assert store.view(datetime(2026, 11, 4)) == {}
    assert store.view(datetime(2026, 11, 5))["ACME"].ebitda_reported == 100.0


def test_restatement_replaces_original_only_after_release():
    original = _fin(100.0, datetime(2026, 9, 30), datetime(2026, 11, 5))
    restated = _fin(80.0, datetime(2026, 9, 30), datetime(2027, 2, 1))
    store = PointInTimeStore([original, restated])
    assert store.view(datetime(2026, 12, 31))["ACME"].ebitda_reported == 100.0
    assert store.view(datetime(2027, 2, 1))["ACME"].ebitda_reported == 80.0


def test_assert_point_in_time_raises_on_late_record():
    late = _fin(100.0, datetime(2026, 9, 30), datetime(2026, 11, 5))
    with pytest.raises(LookAheadError):
        assert_point_in_time([late], datetime(2026, 10, 31))


def test_record_cannot_be_available_before_its_period():
    with pytest.raises(ValueError):
        _fin(100.0, datetime(2026, 9, 30), datetime(2026, 9, 1))
