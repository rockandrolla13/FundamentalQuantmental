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


# ---------------------------------------------------------------- records added by the data module (step 3)


@dataclass(frozen=True)
class Issuer:
    """One company and its identifiers. Static reference data, so not stamped."""

    ticker: str
    gvkey: str | None = None
    cik: str | None = None
    name: str = ""


@dataclass(frozen=True)
class Bond:
    """One bond's terms (Section 3.1). Static between issue and redemption."""

    cusip: str
    issuer_ticker: str
    coupon: float
    maturity: datetime
    seniority: str
    fixed: bool
    convertible: bool
    grade: str = ""


@dataclass(frozen=True, eq=False)
class Curve(Stamped):
    """The Treasury par curve on one date (Section 3.6). Tenors in years, yields as decimals."""

    tenors: tuple[float, ...] = ()
    yields: tuple[float, ...] = ()

    def as_row(self) -> "pd.Series":
        """The curve in the row format of `hy.sources.treasury.interpolate` (tenor index, `available_at`)."""
        import pandas as pd  # noqa: PLC0415 - records stay importable without pandas work

        s = pd.Series(list(self.yields) + [pd.Timestamp(self.available_at)], index=list(self.tenors) + ["available_at"],
                      name=pd.Timestamp(self.as_of))
        return s


@dataclass(frozen=True)
class IndexLevel(Stamped):
    """The high yield market's spread level on one date (Section 3.6, `hy_oas`), as a decimal, and the distress ratio
    (share of high yield bonds above 1,000 bp, decimal; F6 phase indicator). The one rule that turns bond quotes into
    these two numbers is `hy.state.hy_index_level` and `hy.state.distress_ratio`."""

    name: str = "HY"
    spread: float = float("nan")
    distress: float = float("nan")


@dataclass(frozen=True)
class Classification(Stamped):
    """An issuer's GICS sector and rating class, valid from `as_of` (Section 3.2, peers)."""

    issuer_ticker: str = ""
    sector: str = ""
    rating_class: str | None = None
    rating_source: str = ""


@dataclass(frozen=True)
class Filing(Stamped):
    """One SEC filing; `available_at` is the EDGAR acceptance time (UTC)."""

    issuer_ticker: str = ""
    form: str = ""
    accession: str = ""


@dataclass(frozen=True, eq=False)
class IssuerFacts(Stamped):
    """The filing-derived inputs of one issuer as (value, source) pairs, as known at a decision time
    (`hy.sources.clock_inputs.derive_inputs`). Kept as pairs so every value keeps its source."""

    issuer_ticker: str = ""
    values: dict[str, tuple[Any, str]] = field(default_factory=dict)


@dataclass(frozen=True, eq=False)
class AnalystInput:
    """The analyst's YAML for one issuer: {key: {"value", "source", "fallback"}}. Not stamped: it is a judgement."""

    ticker: str
    values: dict[str, dict] = field(default_factory=dict)


@dataclass(frozen=True)
class MarketValue(Stamped):
    """Equity market value of one issuer (framework F7.7): price x shares of the latest quarter reported by the decision
    time, in USD millions. `as_of` is the quarter end; `available_at` is the report date."""

    issuer_ticker: str = ""
    value: float = float("nan")
    source: str = ""


@dataclass(eq=False)
class Ladder:
    """One maturity schedule of a filing (methodology 4.7): bucket amounts in USD millions, the first bucket's length in
    years (the rest are one year each, the last is "thereafter"), the stated total, and whether the buckets add up to
    it. The field names match `hy.sources.schedules.Ladder`, so the schedule functions accept either."""

    family: str
    amounts: list[float]
    first_length: float
    total: float
    reconciles: bool
    concepts: list[str] = field(default_factory=list)


LADDER_FAMILIES = ("operating_lease", "finance_lease", "debt", "purchase")


@dataclass(frozen=True, eq=False)
class BalanceSheet(Stamped):
    """The balance-sheet values and maturity schedules of one 10-Q or 10-K (framework F5; methodology 4.3, 4.7).

    `as_of` is the balance-sheet date; `available_at` is the filing's acceptance time. Amounts in USD millions; NaN
    when the filing does not state the value. `revolver_capacity` is None when no credit-line capacity is stated.
    `ladders` maps each of `LADDER_FAMILIES` to a `Ladder`, or None when the filing has no such schedule.
    `lease_not_commenced` is (total USD m, shortest term years, longest term years). `customer_shares` maps a named
    customer to its share of revenue (decimal) in the latest quarter."""

    issuer_ticker: str = ""
    accession: str = ""
    debt: float = float("nan")
    debt_source: str = ""
    operating_lease_liability: float = float("nan")
    finance_lease_liability: float = float("nan")
    cash: float = float("nan")
    revolver_capacity: float | None = None
    ladders: dict[str, Ladder | None] = field(default_factory=dict)
    lease_not_commenced: tuple[float, float, float] = (float("nan"), float("nan"), float("nan"))
    customer_shares: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True, eq=False)
class FilingText(Stamped):
    """The plain text of one filing's primary document (framework F2 business line, F5 covenant levels). `as_of` and
    `available_at` are the acceptance time."""

    issuer_ticker: str = ""
    accession: str = ""
    text: str = ""


@dataclass(frozen=True)
class ReportedCashFlow(Stamped):
    """One quarter's cash flows as the first 10-Q or 10-K that reported it states them (methodology 3.2), USD millions,
    3-month values. Used only to fill a quarter that the financials leave blank. `as_of` is the quarter end;
    `available_at` is the filing's acceptance time. NaN when the filing does not state the flow."""

    issuer_ticker: str = ""
    accession: str = ""
    operating_cash_flow: float = float("nan")
    capex: float = float("nan")
    interest_paid: float = float("nan")
    taxes_paid: float = float("nan")


# Bond observations come as a frame for volume (600k bond-months). Neutral names: no vendor field leaves an adapter.
BOND_OBS_COLUMNS = ("cusip", "date", "price", "yield", "n_trades", "par_volume", "available_at")


def check_observations(df: "pd.DataFrame") -> "pd.DataFrame":
    """Raise ValueError unless `df` has exactly the BOND_OBS_COLUMNS, in order; return it."""
    if tuple(df.columns) != BOND_OBS_COLUMNS:
        raise ValueError(f"bond observation columns {tuple(df.columns)} != {BOND_OBS_COLUMNS}")
    return df
