"""The point-in-time rule: one store, one guard, one `LookAheadError` (methodology Section 3; CLAUDE.md "a model
reads only fields available before the decision time"; design: data module, `pit`).

Before this module the repo had three `LookAheadError` classes and five guards (review finding AR-DRY-002). They now
all resolve here.
"""

from __future__ import annotations

from datetime import datetime
from typing import Generic, Iterable, TypeVar

import pandas as pd

from hy.data.records import Stamped


class LookAheadError(RuntimeError, AssertionError):
    """Raised when code reads a record that was not available at decision time. It subclasses both RuntimeError
    (the old `hy.inputs` class) and AssertionError (the old `hy.backtest` and `hy.walkforward` classes), so every
    existing `except` clause still catches it."""


class DataUnavailable(LookupError):
    """Raised by the data layer when an item does not exist at the decision time. The pipeline turns it into an open
    question instead of a crash (review finding AR-ABS-001)."""

    def __init__(self, kind: str, key: str, reason: str = "") -> None:
        self.kind, self.key, self.reason = kind, key, reason
        super().__init__(f"{kind} for {key} unavailable" + (f": {reason}" if reason else ""))


R = TypeVar("R", bound=Stamped)


class PointInTimeStore(Generic[R]):
    """Holds every version of every record. Restatements are new versions of one key."""

    def __init__(self, records: Iterable[R] = ()) -> None:
        self._records: list[R] = list(records)

    def add(self, record: R) -> None:
        self._records.append(record)

    def view(self, decision_time: datetime) -> dict[str, R]:
        """Latest period per key, in its latest available version, as the market saw it at `decision_time`.

        The period wins first, so a late restatement of an old quarter never hides a newer quarter.
        """
        out: dict[str, R] = {}
        for r in self._records:
            if r.available_at > decision_time:
                continue
            prev = out.get(r.key)
            if prev is None or (r.as_of, r.available_at) > (prev.as_of, prev.available_at):
                out[r.key] = r
        return out

    def as_known(self, decision_time: datetime) -> list[R]:
        """Every period per key, each in its latest version available at `decision_time`, sorted by key and `as_of`."""
        best: dict[tuple[str, datetime], R] = {}
        for r in self._records:
            if r.available_at > decision_time:
                continue
            k = (r.key, r.as_of)
            if k not in best or r.available_at > best[k].available_at:
                best[k] = r
        return [best[k] for k in sorted(best)]

    def history(self, decision_time: datetime) -> list[R]:
        """Every record available at `decision_time`, sorted by `as_of`."""
        return sorted((r for r in self._records if r.available_at <= decision_time), key=lambda r: r.as_of)


def guard_times(times: Iterable, decision_time, what: str) -> None:
    """Raise `LookAheadError` when any time in `times` is after `decision_time`; NaT and None are ignored.
    Intuition: every input of a prediction must have been public at the decision time."""
    ts = pd.to_datetime(pd.Series(list(times), dtype="object"), errors="coerce").dropna()
    late = ts[ts > pd.Timestamp(decision_time)]
    if len(late):
        raise LookAheadError(f"{what}: {len(late)} value(s) after {pd.Timestamp(decision_time)} (first {late.min()})")


def guard_frame(df: pd.DataFrame | None, decision_time, what: str = "input", col: str = "available_at") -> None:
    """Raise `LookAheadError` when any row of `df` has `col` after `decision_time`. A non-empty frame without the
    column fails too: it cannot prove it is point in time."""
    if df is None or len(df) == 0:
        return
    if col not in df:
        raise LookAheadError(f"{what} has no {col} column; cannot prove it is point in time")
    late = pd.to_datetime(df[col]) > pd.Timestamp(decision_time)
    if late.any():
        first = pd.to_datetime(df.loc[late, col]).min()
        raise LookAheadError(f"{what}: {int(late.sum())} rows available after {pd.Timestamp(decision_time)} (first {first})")


def guard_records(records: Iterable[Stamped], decision_time: datetime) -> None:
    """Fail loudly if any record used for a decision post-dates it (Section 11, Inputs test)."""
    late = [r.key for r in records if r.available_at > decision_time]
    if late:
        raise LookAheadError(f"records not available at {decision_time}: {late}")
