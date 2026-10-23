"""Typed point-in-time records (methodology Section 3; design: data module, `records`).

Every record carries `as_of` (the period it describes) and `available_at` (the first moment the market could read
it). Adapters build records from vendor rows; the domain reads records, never vendor fields.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


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
    debt_current: float = 0.0
    debt_long_term: float = 0.0
    depreciation: float = 0.0
    operating_cash_flow: float = 0.0  # cross-check for the FCF waterfall
    source: str = ""  # provenance, e.g. "compustat_pit+edgar"


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
