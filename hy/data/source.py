"""What the data layer can be asked for: narrow protocols, one per kind of data (design: data module, `source`).

Each protocol has one or two methods. `hy.data.sources.WarehouseSource` implements them over the caches and WRDS;
`FakeSource` implements them in memory for tests. The pipeline sees neither: it reads a `DataView` (step 4).
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, Sequence, runtime_checkable

import pandas as pd

from hy.data.records import (AnalystInput, Bond, Classification, Curve, Filing, IndexLevel, Issuer, IssuerFacts,
                             IssuerFinancials)
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


@runtime_checkable
class BondSource(Protocol):
    """Bonds and their observations; the frame has `records.BOND_OBS_COLUMNS`. The caller picks the bonds, so the
    eligible-bond rule stays in the domain."""

    def bonds(self, issuer: Issuer) -> list[Bond]: ...
    def observations(self, bonds: Sequence[Bond], start: datetime, end: datetime) -> pd.DataFrame: ...


@runtime_checkable
class MarketSource(Protocol):
    """Market-wide levels: the Treasury par curve and the high yield index."""

    def curve(self, on: datetime) -> Curve: ...
    def hy_index(self, on: datetime) -> IndexLevel: ...


@runtime_checkable
class ReferenceSource(Protocol):
    """Classifications: GICS sector and rating class."""

    def classifications(self, issuers: Sequence[Issuer]) -> list[Classification]: ...


@runtime_checkable
class ForecastSource(Protocol):
    """Macro forecast rows with their vintage times."""

    def forecasts(self, decision_time: datetime) -> list[ForecastRow]: ...


@runtime_checkable
class AnalystSource(Protocol):
    """The analyst's YAML inputs."""

    def analyst_inputs(self, ticker: str) -> AnalystInput: ...
