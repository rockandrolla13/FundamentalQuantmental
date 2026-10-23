"""Realised outcomes: data that became public AFTER a decision (design: data module; methodology Section 11).

A backtest or a walk-forward scores a prediction against what happened next. That needs future data on purpose.
`RealisedOutcomes` is the only read path for it, and it is separate from `DataView` so that no step that forms a
prediction can reach it by accident: the pipeline (scripts/process.py) never imports this module, and a test checks it.

Every read takes `public_by`, the time at which the outcome is read, and refuses a time before the decision.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Sequence

import pandas as pd

from hy.data.records import Bond, Curve, IndexLevel


class RealisedOutcomes:
    """What became public after `decision_time`, read from the same source as the prediction's view.
    Intuition: the newspaper of the following months, kept in another room from the analyst."""

    def __init__(self, source: Any, decision_time: datetime) -> None:
        self.source = source
        self.decision_time = pd.Timestamp(decision_time).to_pydatetime()

    def _check(self, public_by: datetime) -> datetime:
        t = pd.Timestamp(public_by).to_pydatetime()
        if t < self.decision_time:
            raise ValueError(f"realised outcome at {t} precedes the decision {self.decision_time}: use a DataView")
        return t

    def observations(self, cusips: Sequence[str], public_by: datetime) -> pd.DataFrame:
        """Bond observations dated after the decision time and public by `public_by` (`records.BOND_OBS_COLUMNS`).
        Bonds are named by CUSIP only: an outcome needs no bond terms."""
        t = self._check(public_by)
        bonds = [Bond(c, "", float("nan"), self.decision_time, "", True, False) for c in cusips]
        o = self.source.observations(bonds, self.decision_time, t)
        keep = (pd.to_datetime(o["date"]) >= pd.Timestamp(self.decision_time)) & (pd.to_datetime(o["available_at"]) <= t)
        return o[keep].reset_index(drop=True)

    def curve(self, public_by: datetime) -> Curve:
        """The latest Treasury curve public by `public_by`."""
        return self.source.curve(self._check(public_by))

    def hy_index(self, public_by: datetime) -> IndexLevel:
        """The HY index level public by `public_by`."""
        return self.source.hy_index(self._check(public_by))
