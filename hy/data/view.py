"""DataView: what was knowable at one decision time (design: data module, `view`; the core abstraction).

The pipeline reads every input through a view and never sees a connection, a path or a vendor field. The view asks
its source, keeps only what was public by the decision time, and guards what the source promised was already
filtered. Reads are memoised for the life of the view; `at(t)` gives a fresh view of the same source at another time
(the walk-forward). A view is read-only, so issuers and dates can run in parallel.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Sequence

import pandas as pd

from hy.data.pit import DataUnavailable, PointInTimeStore, guard_frame, guard_records
from hy.data.records import (AnalystInput, BalanceSheet, Bond, Classification, Curve, Filing, IndexLevel, Issuer, IssuerFacts,
                             IssuerFinancials, MarketValue)
from hy.forecasts import ForecastRow


class DataView:
    """Every input as known at `decision_time`. Intuition: a frozen copy of the world on the morning of the call."""

    def __init__(self, source: Any, decision_time: datetime) -> None:
        self.source = source
        self.decision_time = pd.Timestamp(decision_time).to_pydatetime()
        self._memo: dict[tuple, Any] = {}

    def at(self, decision_time: datetime) -> "DataView":
        """The same source at another decision time, with an empty memo."""
        return DataView(self.source, decision_time)

    def _get(self, key: tuple, load: Callable[[], Any]) -> Any:
        if key not in self._memo:
            self._memo[key] = load()
        return self._memo[key]

    # ------------------------------------------------------------ issuers and fundamentals

    def issuer(self, ticker: str) -> Issuer:
        return self._get(("issuer", ticker.upper()), lambda: self.source.issuers([ticker.upper()])[0])

    def financials(self, issuer: Issuer) -> list[IssuerFinancials]:
        """Every quarter, each in its latest version public by the decision time (restatements included)."""
        def load() -> list[IssuerFinancials]:
            return PointInTimeStore(self.source.financials(issuer)).as_known(self.decision_time)
        return self._get(("financials", issuer.ticker), load)

    def facts(self, issuer: Issuer) -> IssuerFacts:
        def load() -> IssuerFacts:
            f = self.source.facts(issuer, self.decision_time)
            guard_records([f], self.decision_time)
            return f
        return self._get(("facts", issuer.ticker), load)

    def market_value(self, issuer: Issuer) -> MarketValue:
        """Equity market value from the latest quarter reported by the decision time (framework F7.7)."""
        def load() -> MarketValue:
            m = self.source.market_value(issuer, self.decision_time)
            guard_records([m], self.decision_time)
            return m
        return self._get(("market_value", issuer.ticker), load)

    def filings(self, issuer: Issuer, forms: Sequence[str]) -> list[Filing]:
        def load() -> list[Filing]:
            return sorted((f for f in self.source.filings(issuer, forms) if f.available_at <= self.decision_time),
                          key=lambda f: f.available_at)
        return self._get(("filings", issuer.ticker, tuple(forms)), load)

    def balance_sheet(self, issuer: Issuer, accession: str) -> BalanceSheet:
        """Balance-sheet values and schedules of one filing; the filing must be public by the decision time."""
        def load() -> BalanceSheet:
            b = self.source.balance_sheet(issuer, accession)
            guard_records([b], self.decision_time)
            return b
        return self._get(("balance_sheet", issuer.ticker, accession), load)

    # ------------------------------------------------------------ bonds and market

    def bonds(self, issuer: Issuer) -> list[Bond]:
        return self._get(("bonds", issuer.ticker), lambda: self.source.bonds(issuer))

    def observations(self, bonds: Sequence[Bond], start: datetime) -> pd.DataFrame:
        """Daily observations from `start` that were public by the decision time."""
        def load() -> pd.DataFrame:
            o = self.source.observations(bonds, start, self.decision_time)
            return o[pd.to_datetime(o["available_at"]) <= pd.Timestamp(self.decision_time)].reset_index(drop=True)
        return self._get(("observations", tuple(b.cusip for b in bonds), pd.Timestamp(start)), load)

    def curve(self) -> Curve:
        def load() -> Curve:
            c = self.source.curve(self.decision_time)
            guard_records([c], self.decision_time)
            return c
        return self._get(("curve",), load)

    def hy_index(self) -> IndexLevel:
        def load() -> IndexLevel:
            x = self.source.hy_index(self.decision_time)
            guard_records([x], self.decision_time)
            return x
        return self._get(("hy_index",), load)

    # ------------------------------------------------------------ reference, forecasts, analyst, panels

    def classifications(self, issuers: Sequence[Issuer]) -> list[Classification]:
        def load() -> list[Classification]:
            return [c for c in self.source.classifications(issuers) if c.available_at <= self.decision_time]
        return self._get(("classifications", tuple(i.ticker for i in issuers)), load)

    def forecasts(self) -> list[ForecastRow]:
        def load() -> list[ForecastRow]:
            return [r for r in self.source.forecasts(self.decision_time)
                    if pd.Timestamp(r.available_at) <= pd.Timestamp(self.decision_time)]
        return self._get(("forecasts",), load)

    def forecast_status(self) -> pd.DataFrame:
        """Per forecast source: live or stubbed, last vintage and release, rows kept (the run's audit trail)."""
        return self._get(("forecast_status",), lambda: self.source.forecast_status(self.decision_time))

    def analyst_inputs(self, ticker: str) -> AnalystInput:
        return self._get(("analyst", ticker.upper()), lambda: self.source.analyst_inputs(ticker))

    def panel(self, name: str, columns: Sequence[str] | None = None) -> pd.DataFrame:
        """A cross-sectional panel with only the rows public by the decision time. `available_at` is kept only when
        asked for."""
        def load() -> pd.DataFrame:
            p = self.source.panel(name, columns)
            if "available_at" not in p:
                raise DataUnavailable("panel", name, "no available_at column: cannot prove it is point in time")
            p = p[pd.to_datetime(p["available_at"]) <= pd.Timestamp(self.decision_time)]
            guard_frame(p, self.decision_time, name)
            keep = list(columns) if columns is not None else list(p.columns)
            return p[keep].reset_index(drop=True)
        return self._get(("panel", name, tuple(columns) if columns is not None else None), load)
