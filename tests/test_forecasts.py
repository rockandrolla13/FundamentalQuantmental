from datetime import datetime

import numpy as np
import pytest

from hy.forecasts import ForecastRegistry, ForecastRow, assert_no_lookahead, revisions, widen_factor
from hy.inputs import LookAheadError


def _row(v, avail, point, h=1, src="spf", var="gdp_growth", q=(np.nan, np.nan, np.nan)):
    return ForecastRow(src, var, h, v, avail, point, *q, method="survey_bins")


def test_as_of_never_reads_rows_released_later():
    reg = ForecastRegistry([
        _row(datetime(2026, 5, 1), datetime(2026, 5, 15), 0.018),
        _row(datetime(2026, 8, 1), datetime(2026, 8, 14), 0.010),
    ])
    early = reg.as_of(datetime(2026, 8, 13))
    assert early["point"].tolist() == [0.018]
    assert reg.as_of(datetime(2026, 8, 14))["point"].tolist() == [0.010]


def test_lookahead_fixture_fails_on_a_late_row():
    reg = ForecastRegistry([_row(datetime(2026, 8, 1), datetime(2026, 8, 14), 0.010)])
    leaked = reg.frame()  # every vintage, the wrong door for a decision
    with pytest.raises(LookAheadError):
        assert_no_lookahead(leaked, datetime(2026, 8, 1))


def test_quantiles_must_be_ordered_and_release_after_vintage():
    with pytest.raises(ValueError):
        _row(datetime(2026, 8, 1), datetime(2026, 8, 14), 0.01, q=(0.03, 0.01, 0.02))
    with pytest.raises(ValueError):
        _row(datetime(2026, 8, 14), datetime(2026, 8, 1), 0.01)


def test_errors_bias_coverage_and_widen_factor():
    reg = ForecastRegistry()
    for i in range(12):
        v = datetime(2023 + i // 4, 1 + 3 * (i % 4), 15)
        reg.add(_row(v, v, 0.02, h=1, q=(0.015, 0.02, 0.025)))
        tgt = (np.datetime64(v, "M") + np.timedelta64(3, "M")).astype("datetime64[D]").astype(datetime)
        reg.record_realised("gdp_growth", tgt, 0.02 + (0.01 if i % 2 else -0.01))  # misses the band every time
    rep = reg.error_report().iloc[0]
    assert rep["n"] == 12 and rep["bias"] == pytest.approx(0.0) and rep["coverage_80"] == 0.0
    assert widen_factor(rep["coverage_80"], int(rep["n"])) > 1.0
    assert widen_factor(0.8, 50) == pytest.approx(1.0)
    assert widen_factor(0.0, 3) == 1.0  # too few matured rows: no change


def test_revisions_between_vintages():
    reg = ForecastRegistry([
        _row(datetime(2026, 5, 1), datetime(2026, 5, 15), 0.018),
        _row(datetime(2026, 8, 1), datetime(2026, 8, 14), 0.010),
    ])
    r = revisions(reg, datetime(2026, 9, 1), datetime(2026, 6, 1))
    assert r["revision"].iloc[0] == pytest.approx(-0.008)


def test_old_vintage_never_fills_a_horizon_the_new_one_drops():
    reg = ForecastRegistry([
        _row(datetime(2026, 5, 1), datetime(2026, 5, 15), 0.018, h=0),
        _row(datetime(2026, 5, 1), datetime(2026, 5, 15), 0.019, h=1),
        _row(datetime(2026, 8, 1), datetime(2026, 8, 14), 0.010, h=1),  # new vintage has no horizon 0
    ])
    got = reg.as_of(datetime(2026, 9, 1))
    assert got["horizon_q"].tolist() == [1] and got["point"].tolist() == [0.010]
