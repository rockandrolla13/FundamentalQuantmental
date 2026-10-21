"""Input layer: typed records and the point-in-time guard (methodology Section 3).

Every record carries `as_of` (the period it describes) and `available_at`
(the first moment the market could read it). `PointInTimeStore.view(t)`
returns only records with `available_at <= t`, and only the latest
version of each key. All downstream layers read through a view.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Generic, Iterable, TypeVar


class LookAheadError(RuntimeError):
    """Raised when code reads a record that was not available at decision time."""


@dataclass(frozen=True)
class Stamped:
    """Base for every input record. Section 3, first paragraph."""

    key: str
    as_of: datetime
    available_at: datetime

    def __post_init__(self) -> None:
        if self.available_at < self.as_of:
            # A filing can never be public before the period it describes ends.
            raise ValueError(f"{self.key}: available_at {self.available_at} precedes as_of {self.as_of}")


@dataclass(frozen=True)
class NonRecurringItem:
    """One nonrecurring item (Section 3.2, Figure 7.3, p. 192)."""

    name: str
    amount: float
    recurs: bool  # True: treat as an operating cost, do not add back
    cash: bool  # True: the item consumed cash


@dataclass(frozen=True)
class IssuerFinancials(Stamped):
    """Per issuer, each filing (Section 3.2). Amounts in USD millions, quarterly flows."""

    revenue: float = 0.0
    ebitda_reported: float = 0.0
    nonrecurring_items: tuple[NonRecurringItem, ...] = ()
    ebitda_adj_company: float = 0.0
    ebitda_covenant: float = 0.0
    cash_interest: float = 0.0
    cash_taxes: float = 0.0
    capex_total: float = 0.0
    capex_maintenance: float = 0.0
    inventory: float = 0.0
    receivables: float = 0.0
    payables: float = 0.0
    cogs: float = 0.0
    cash: float = 0.0
    revolver_commitment: float = 0.0
    revolver_drawn: float = 0.0
    borrowing_base: float = float("inf")
    letters_of_credit: float = 0.0
    maturity_schedule: tuple[float, ...] = (0.0,) * 5
    rent_expense: float = 0.0
    pension_underfunded: float = 0.0
    guarantees_weak: float = 0.0


@dataclass(frozen=True)
class Tranche(Stamped):
    """One row of the capital structure table (Section 3.3)."""

    issuer_id: str = ""
    tranche_type: str = "senior_unsecured"
    rank: int = 1  # 1 is paid first
    face: float = 0.0
    price: float = 100.0  # per 100 face
    coupon: float = 0.0
    floating: bool = False
    floor: float = 0.0
    spread: float = 0.0  # loan margin over SOFR, decimal
    mandatory_amort: float = 0.0  # per quarter


@dataclass(frozen=True)
class Event(Stamped):
    """One dated event (Section 3.7)."""

    issuer_id: str = ""
    event_type: str = ""
    event_date: datetime | None = None
    date_confirmed: bool = False
    params: dict[str, Any] = field(default_factory=dict)


R = TypeVar("R", bound=Stamped)


class PointInTimeStore(Generic[R]):
    """Holds every version of every record. Restatements are new versions of one key."""

    def __init__(self, records: Iterable[R] = ()) -> None:
        self._records: list[R] = list(records)

    def add(self, record: R) -> None:
        self._records.append(record)

    def view(self, decision_time: datetime) -> dict[str, R]:
        """Latest available version per key, as the market saw it at `decision_time`."""
        out: dict[str, R] = {}
        for r in self._records:
            if r.available_at > decision_time:
                continue
            prev = out.get(r.key)
            if prev is None or (r.available_at, r.as_of) > (prev.available_at, prev.as_of):
                out[r.key] = r
        return out

    def history(self, decision_time: datetime) -> list[R]:
        """Every record available at `decision_time`, sorted by `as_of`."""
        return sorted((r for r in self._records if r.available_at <= decision_time), key=lambda r: r.as_of)


def assert_point_in_time(records: Iterable[Stamped], decision_time: datetime) -> None:
    """Fail loudly if any record used for a decision post-dates it (Section 11, Inputs test)."""
    late = [r.key for r in records if r.available_at > decision_time]
    if late:
        raise LookAheadError(f"records not available at {decision_time}: {late}")
