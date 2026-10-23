"""Concrete data sources (design: data module, `sources`).

`WarehouseSource` serves every protocol of `hy.data.source` from the caches under `DataConfig.root`, reaching WRDS
and the web only when the config allows it. `FakeSource` serves them from memory, for tests: the pipeline can run
end to end with no cache and no network (review finding AR-TST-001).
"""

from __future__ import annotations

from datetime import datetime
from typing import Sequence

import pandas as pd

from hy.data.adapters import compustat, edgar_filings, reference, trace, treasury_curve
from hy.data.config import DataConfig
from hy.data.pit import DataUnavailable
from hy.data.source import PANELS
from hy.data.records import (BOND_OBS_COLUMNS, AnalystInput, Bond, Classification, Curve, Filing, IndexLevel, Issuer,
                             IssuerFacts, IssuerFinancials, check_observations)
from hy.forecasts import ForecastRow


class WarehouseSource:
    """Every data kind from the local warehouse (data/raw) and, when allowed, WRDS, EDGAR and Treasury.gov."""

    def __init__(self, cfg: DataConfig) -> None:
        self.cfg = cfg

    def issuers(self, tickers: Sequence[str]) -> list[Issuer]:
        return [compustat.issuer(t, self.cfg) for t in tickers]

    def financials(self, issuer: Issuer) -> list[IssuerFinancials]:
        return compustat.financials(issuer, self.cfg)

    def facts(self, issuer: Issuer, decision_time: datetime) -> IssuerFacts:
        return edgar_filings.facts(issuer, decision_time, self.cfg)

    def filings(self, issuer: Issuer, forms: Sequence[str]) -> list[Filing]:
        return edgar_filings.filings(issuer, forms, self.cfg)

    def bonds(self, issuer: Issuer) -> list[Bond]:
        return trace.bonds(issuer, self.cfg)

    def observations(self, bonds: Sequence[Bond], start: datetime, end: datetime) -> pd.DataFrame:
        return trace.observations(bonds, start, end, self.cfg)

    def curve(self, on: datetime) -> Curve:
        return treasury_curve.curve(on, self.cfg)

    def hy_index(self, on: datetime) -> IndexLevel:
        raise DataUnavailable("hy_index", str(pd.Timestamp(on).date()),
                              "the live run and the backtest define it differently; one definition arrives in step 5")

    def classifications(self, issuers: Sequence[Issuer]) -> list[Classification]:
        return reference.classifications(issuers, self.cfg)

    def forecasts(self, decision_time: datetime) -> list[ForecastRow]:
        return reference.forecasts(decision_time, self.cfg)

    def analyst_inputs(self, ticker: str) -> AnalystInput:
        return reference.analyst_inputs(ticker)

    # The cached panel files keep their historical names; the neutral names map onto them here only.
    PANEL_FILES = {"bond_panel": "panel_full", "leverage": "leverage_full", "gics": "gics_history",
                   "ratings": "sp_ratings", "annual_ebitda": "annual_ebitda", "equity_monthly": "equity_monthly"}

    def panel(self, name: str, columns: Sequence[str] | None = None) -> pd.DataFrame:
        f = self.cfg.path("backtest", f"{self.PANEL_FILES.get(name, name)}.parquet")
        if name not in PANELS or not f.exists():
            raise DataUnavailable("panel", name, "unknown panel" if name not in PANELS else f"no cached file {f.name}")
        cols = None if columns is None else list(dict.fromkeys([*columns, "available_at"]))
        return pd.read_parquet(f, columns=cols)


class FakeSource:
    """Every data kind from memory. Anything not given raises DataUnavailable, as a real gap would."""

    def __init__(self, issuers: Sequence[Issuer] = (), financials: Sequence[IssuerFinancials] = (),
                 facts: Sequence[IssuerFacts] = (), filings: Sequence[Filing] = (), bonds: Sequence[Bond] = (),
                 observations: pd.DataFrame | None = None, curves: Sequence[Curve] = (),
                 index_levels: Sequence[IndexLevel] = (), classifications: Sequence[Classification] = (),
                 forecasts: Sequence[ForecastRow] = (), analyst: Sequence[AnalystInput] = (),
                 panels: dict[str, pd.DataFrame] | None = None) -> None:
        self._issuers = {i.ticker: i for i in issuers}
        self._financials, self._facts, self._filings = list(financials), list(facts), list(filings)
        self._bonds, self._curves, self._index = list(bonds), list(curves), list(index_levels)
        self._class, self._forecasts = list(classifications), list(forecasts)
        self._analyst = {a.ticker: a for a in analyst}
        self._panels = dict(panels or {})
        self._obs = check_observations(observations) if observations is not None else pd.DataFrame(columns=list(BOND_OBS_COLUMNS))

    def issuers(self, tickers: Sequence[str]) -> list[Issuer]:
        missing = [t for t in tickers if t not in self._issuers]
        if missing:
            raise DataUnavailable("issuer", ",".join(missing), "not in the fake source")
        return [self._issuers[t] for t in tickers]

    def financials(self, issuer: Issuer) -> list[IssuerFinancials]:
        return [r for r in self._financials if r.key == issuer.gvkey]

    def facts(self, issuer: Issuer, decision_time: datetime) -> IssuerFacts:
        known = [f for f in self._facts if f.issuer_ticker == issuer.ticker and f.available_at <= decision_time]
        if not known:
            raise DataUnavailable("facts", issuer.ticker, "none known at the decision time")
        return max(known, key=lambda f: f.available_at)

    def filings(self, issuer: Issuer, forms: Sequence[str]) -> list[Filing]:
        return [f for f in self._filings if f.issuer_ticker == issuer.ticker and f.form in forms]

    def bonds(self, issuer: Issuer) -> list[Bond]:
        return [b for b in self._bonds if b.issuer_ticker == issuer.ticker]

    def observations(self, bonds: Sequence[Bond], start: datetime, end: datetime) -> pd.DataFrame:
        o = self._obs
        keep = o["cusip"].isin([b.cusip for b in bonds]) & (o["date"] >= pd.Timestamp(start)) & (o["date"] <= pd.Timestamp(end))
        return o[keep].reset_index(drop=True)

    def curve(self, on: datetime) -> Curve:
        c = [x for x in self._curves if x.available_at <= on]
        if not c:
            raise DataUnavailable("curve", str(on), "none public by the date")
        return max(c, key=lambda x: x.as_of)

    def hy_index(self, on: datetime) -> IndexLevel:
        c = [x for x in self._index if x.available_at <= on]
        if not c:
            raise DataUnavailable("hy_index", str(on), "none public by the date")
        return max(c, key=lambda x: x.as_of)

    def classifications(self, issuers: Sequence[Issuer]) -> list[Classification]:
        names = {i.ticker for i in issuers}
        return [c for c in self._class if c.issuer_ticker in names]

    def forecasts(self, decision_time: datetime) -> list[ForecastRow]:
        return list(self._forecasts)

    def analyst_inputs(self, ticker: str) -> AnalystInput:
        return self._analyst.get(ticker.upper(), AnalystInput(ticker.upper()))

    def panel(self, name: str, columns: Sequence[str] | None = None) -> pd.DataFrame:
        if name not in self._panels:
            raise DataUnavailable("panel", name, "not in the fake source")
        p = self._panels[name]
        return p if columns is None else p[list(dict.fromkeys([*columns, "available_at"]))]
