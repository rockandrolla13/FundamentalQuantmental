"""Tests for hy.data.history: the backtest replays read raw panels through the view (design: data module)."""

from datetime import datetime

import pandas as pd

from hy.data import sources
from hy.data.history import backtest_panel
from hy.data.view import DataView


def test_the_full_panel_comes_through_the_view_without_future_rows():
    p = pd.DataFrame({"date": [datetime(2026, 8, 31), datetime(2026, 9, 30)], "gvkey": ["1", "1"],
                      "leverage": [4.0, 5.0], "available_at": [datetime(2026, 9, 1), datetime(2026, 10, 30)]})
    view = DataView(sources.FakeSource(panels={"leverage": p}), datetime(2026, 10, 1))
    got = backtest_panel("leverage", "full", ["date", "gvkey", "leverage"], view)
    assert got["leverage"].tolist() == [4.0] and list(got.columns) == ["date", "gvkey", "leverage"]
