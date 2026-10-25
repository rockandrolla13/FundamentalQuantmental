"""What the data layer can be asked for: narrow protocols, one per kind of data (design: data module, `source`).

Each protocol has one or two methods. `hy.data.sources.WarehouseSource` implements them over the caches and WRDS;
`FakeSource` implements them in memory for tests. The pipeline sees neither: it reads a `DataView` (step 4).
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, Sequence, runtime_checkable

import pandas as pd

from hy.data.records import (AnalystInput, BalanceSheet, Bond, Classification, Curve, Filing, IndexLevel, Issuer, IssuerFacts,
                             IssuerFinancials, MarketValue, ReportedCashFlow, FilingText)
from hy.forecasts import ForecastRow


@runtime_checkable
class IssuerSource(Protocol):
    """Identity and fundamentals: Compustat point-in-time vintages joined to EDGAR acceptance times."""

    def issuers(self, tickers: Sequence[str]) -> list[Issuer]: ...
    def financials(self, issuer: Issuer) -> list[IssuerFinancials]: ...


@runtime_checkable
class FilingSource(Protocol):
    """SEC filings and the inputs derived from them, as known at a decision time."""

    def facts(self, issuer: Issuer, decision_time: datetime) -> IssuerFacts: ...
    def filings(self, issuer: Issuer, forms: Sequence[str]) -> list[Filing]: ...
    def balance_sheet(self, issuer: Issuer, accession: str) -> BalanceSheet: ...
    def filing_text(self, issuer: Issuer, accession: str) -> FilingText: ...
    def reported_cash_flow(self, issuer: Issuer, period_end: datetime, decision_time: datetime) -> ReportedCashFlow: ...


@runtime_checkable
class BondSource(Protocol):
    """Bonds and their observations; the frame has `records.BOND_OBS_COLUMNS`. The caller picks the bonds, so the
    eligible-bond rule stays in the domain."""

    def bonds(self, issuer: Issuer) -> list[Bond]: ...
    def observations(self, bonds: Sequence[Bond], start: datetime, end: datetime) -> pd.DataFrame: ...


@runtime_checkable
class MarketSource(Protocol):
    """Market-wide levels: the Treasury par curve (one date, or every date from `start` to `end`) and the high yield
    index."""

    def curve(self, on: datetime) -> Curve: ...
    def curves(self, start: datetime, end: datetime) -> list[Curve]: ...
    def hy_index(self, on: datetime) -> IndexLevel: ...


@runtime_checkable
class EquitySource(Protocol):
    """The issuer's equity market value, as reported by a decision time (framework F7.7)."""

    def market_value(self, issuer: Issuer, decision_time: datetime) -> MarketValue: ...


@runtime_checkable
class ReferenceSource(Protocol):
    """Classifications: GICS sector and rating class."""

    def classifications(self, issuers: Sequence[Issuer]) -> list[Classification]: ...


@runtime_checkable
class ForecastSource(Protocol):
    """Macro forecast rows with their vintage times, and a status table per forecast source (the run's audit trail:
    columns `FORECAST_STATUS_COLUMNS`)."""

    def forecasts(self, decision_time: datetime) -> list[ForecastRow]: ...
    def forecast_status(self, decision_time: datetime) -> pd.DataFrame: ...


@runtime_checkable
class AnalystSource(Protocol):
    """The analyst's YAML inputs."""

    def analyst_inputs(self, ticker: str) -> AnalystInput: ...


FORECAST_STATUS_COLUMNS = ("source", "status", "last_vintage", "last_available_at", "rows", "rows_after_decision_time")

# Panel names: neutral names for the cross-sectional files the backtests and the peer step read.
PANELS = ("bond_panel", "leverage", "gics", "ratings", "annual_ebitda", "equity_monthly")


@runtime_checkable
class PanelSource(Protocol):
    """Cross-sectional history (every bond-month, every issuer's leverage, sector, rating, EBITDA, stock return).
    Each frame carries `available_at`; the view filters it."""

    def panel(self, name: str, columns: Sequence[str] | None = None) -> pd.DataFrame: ...


PROTOCOLS = (IssuerSource, FilingSource, BondSource, MarketSource, EquitySource, ReferenceSource, ForecastSource,
             AnalystSource, PanelSource)

# Every method a complete source serves, in protocol order (`CompositeSource` routes these).
SOURCE_METHODS = ("issuers", "financials", "facts", "filings", "balance_sheet", "filing_text", "reported_cash_flow",
                  "bonds", "observations", "curve", "curves", "hy_index", "market_value", "classifications",
                  "forecasts", "forecast_status", "analyst_inputs", "panel")

# The columns each panel must carry (docs/data_contract.md 3.14). `gvkey` is the issuer key of every panel: any
# string that is the same key as `Issuer.gvkey` and `IssuerFinancials.key`. `splticrm` is a rating on the S&P letter
# scale (AAA to D, with + and -); `gsector` is the two-digit GICS sector. The live run reads `PANEL_COLUMNS`; the
# backtests also read `PANEL_BACKTEST_COLUMNS`.
PANEL_COLUMNS: dict[str, tuple[str, ...]] = {
    "bond_panel": ("date", "cusip", "gvkey", "years", "g_spread", "available_at"),
    "leverage": ("date", "gvkey", "leverage", "ltm_ebitda", "debt", "available_at"),
    "gics": ("gvkey", "gsector", "indfrom", "indthru", "available_at"),
    "ratings": ("gvkey", "datadate", "splticrm", "available_at"),
    "annual_ebitda": ("gvkey", "datadate", "fyear", "oibdp", "debt", "available_at"),
    "equity_monthly": ("gvkey", "datadate", "ret", "available_at"),
}
PANEL_BACKTEST_COLUMNS: dict[str, tuple[str, ...]] = {
    "bond_panel": ("price", "yield", "coupon", "maturity", "mod_dur", "tsy_yield", "bid_ask_pts", "n_trades",
                   "par_volume", "carried", "accrue_to", "hedge_date"),
}
# Panels without which the peer step (step 9) has no cell; the others only blank one estimate each.
PANELS_FOR_PEERS = ("bond_panel", "leverage", "gics", "ratings")

# The keys of `IssuerFacts.values` that the process reads (docs/data_contract.md 3.3). Each value is a pair
# (value, source text); a value may be None when the filing does not give it, but the key must be there.
FACT_KEYS = ("ticker", "name", "cik", "gvkey", "q", "k", "q_acceptance", "k_acceptance", "balance_sheet_date",
             "ltm_ebitda", "ltm_revenue", "run_rate_revenue", "interest_rate", "annual_lease_cost", "lease_wavg_term",
             "uncommenced_window", "uncommenced_term", "debt_tail_years", "rpo_total", "rpo_windows", "rpo_tail_years",
             "purchase", "rating", "recourse", "scenario_extra_lease", "available_at")
