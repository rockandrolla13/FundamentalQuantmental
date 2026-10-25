"""Concrete data sources (design: data module, `sources`).

`WarehouseSource` serves every protocol of `hy.data.source` from the caches under `DataConfig.root`, reaching WRDS
and the web only when the config allows it. `FakeSource` serves them from memory, for tests: the pipeline can run
end to end with no cache and no network (review finding AR-TST-001).
"""

from __future__ import annotations

from datetime import datetime
from typing import Sequence

import pandas as pd

from hy.data.adapters import compustat, edgar_filings, guarded_fetch, reference, trace, treasury_curve
from hy.data.config import DataConfig
from hy.data.pit import DataUnavailable
from hy.data.source import FORECAST_STATUS_COLUMNS, PANELS, SOURCE_METHODS
from hy.data.records import (BOND_OBS_COLUMNS, AnalystInput, BalanceSheet, Bond, Classification, Curve, Filing, IndexLevel, Issuer,
                             IssuerFacts, IssuerFinancials, MarketValue, ReportedCashFlow, FilingText,
                             check_observations)
from hy.forecasts import ForecastRow
from hy.sources import forecast_sources as fs


class WarehouseSource:
    """Every data kind from the local warehouse (data/raw) and, when allowed, WRDS, EDGAR and Treasury.gov."""

    def __init__(self, cfg: DataConfig) -> None:
        self.cfg = cfg
        self._forecast_status: dict[datetime, pd.DataFrame] = {}

    def issuers(self, tickers: Sequence[str]) -> list[Issuer]:
        return [compustat.issuer(t, self.cfg) for t in tickers]

    def financials(self, issuer: Issuer) -> list[IssuerFinancials]:
        return compustat.financials(issuer, self.cfg)

    def facts(self, issuer: Issuer, decision_time: datetime) -> IssuerFacts:
        return edgar_filings.facts(issuer, decision_time, self.cfg)

    def filings(self, issuer: Issuer, forms: Sequence[str]) -> list[Filing]:
        return edgar_filings.filings(issuer, forms, self.cfg)

    def balance_sheet(self, issuer: Issuer, accession: str) -> BalanceSheet:
        return edgar_filings.balance_sheet(issuer, accession, self.cfg)

    def filing_text(self, issuer: Issuer, accession: str) -> FilingText:
        return edgar_filings.filing_text(issuer, accession, self.cfg)

    def reported_cash_flow(self, issuer: Issuer, period_end: datetime, decision_time: datetime) -> ReportedCashFlow:
        return edgar_filings.reported_cash_flow(issuer, period_end, decision_time, self.cfg)

    def bonds(self, issuer: Issuer) -> list[Bond]:
        return trace.bonds(issuer, self.cfg)

    def observations(self, bonds: Sequence[Bond], start: datetime, end: datetime) -> pd.DataFrame:
        return trace.observations(bonds, start, end, self.cfg)

    def curve(self, on: datetime) -> Curve:
        return treasury_curve.curve(on, self.cfg)

    def curves(self, start: datetime, end: datetime) -> list[Curve]:
        return treasury_curve.curves(start, end, self.cfg)

    def hy_index(self, on: datetime) -> IndexLevel:
        return trace.hy_index(on, self.cfg)

    def market_value(self, issuer: Issuer, decision_time: datetime) -> MarketValue:
        return compustat.market_value(issuer, decision_time, self.cfg)

    def classifications(self, issuers: Sequence[Issuer]) -> list[Classification]:
        return reference.classifications(issuers, self.cfg)

    def forecasts(self, decision_time: datetime) -> list[ForecastRow]:
        rows, status = reference.forecasts(decision_time, self.cfg)
        self._forecast_status[pd.Timestamp(decision_time).to_pydatetime()] = status
        return rows

    def forecast_status(self, decision_time: datetime) -> pd.DataFrame:
        t = pd.Timestamp(decision_time).to_pydatetime()
        if t not in self._forecast_status:
            self.forecasts(t)
        return self._forecast_status[t]

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
                 panels: dict[str, pd.DataFrame] | None = None, market_values: Sequence[MarketValue] = (),
                 balance_sheets: Sequence[BalanceSheet] = (), texts: Sequence[FilingText] = (),
                 cash_flows: Sequence[ReportedCashFlow] = ()) -> None:
        self._issuers = {i.ticker: i for i in issuers}
        self._financials, self._facts, self._filings = list(financials), list(facts), list(filings)
        self._bonds, self._curves, self._index = list(bonds), list(curves), list(index_levels)
        self._class, self._forecasts = list(classifications), list(forecasts)
        self._analyst = {a.ticker: a for a in analyst}
        self._panels = dict(panels or {})
        self._mv = list(market_values)
        self._sheets = {b.accession: b for b in balance_sheets}
        self._texts = {x.accession: x for x in texts}
        self._cash_flows = list(cash_flows)
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

    def balance_sheet(self, issuer: Issuer, accession: str) -> BalanceSheet:
        if accession not in self._sheets:
            raise DataUnavailable("balance_sheet", accession, "not in the fake source")
        return self._sheets[accession]

    def filing_text(self, issuer: Issuer, accession: str) -> FilingText:
        if accession not in self._texts:
            raise DataUnavailable("filing_text", accession, "not in the fake source")
        return self._texts[accession]

    def reported_cash_flow(self, issuer: Issuer, period_end: datetime, decision_time: datetime) -> ReportedCashFlow:
        hit = [c for c in self._cash_flows if c.issuer_ticker == issuer.ticker and c.as_of == period_end
               and c.available_at <= decision_time]
        if not hit:
            raise DataUnavailable("reported_cash_flow", issuer.ticker, "not in the fake source")
        return min(hit, key=lambda c: c.available_at)

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

    def curves(self, start: datetime, end: datetime) -> list[Curve]:
        return sorted((x for x in self._curves if start <= x.as_of <= end), key=lambda x: x.as_of)

    def hy_index(self, on: datetime) -> IndexLevel:
        c = [x for x in self._index if x.available_at <= on]
        if not c:
            raise DataUnavailable("hy_index", str(on), "none public by the date")
        return max(c, key=lambda x: x.as_of)

    def market_value(self, issuer: Issuer, decision_time: datetime) -> MarketValue:
        known = [m for m in self._mv if m.issuer_ticker == issuer.ticker and m.available_at <= decision_time]
        if not known:
            raise DataUnavailable("market_value", issuer.ticker, "none reported by the decision time")
        return max(known, key=lambda m: m.as_of)

    def classifications(self, issuers: Sequence[Issuer]) -> list[Classification]:
        names = {i.ticker for i in issuers}
        return [c for c in self._class if c.issuer_ticker in names]

    def forecasts(self, decision_time: datetime) -> list[ForecastRow]:
        return list(self._forecasts)

    def forecast_status(self, decision_time: datetime) -> pd.DataFrame:
        rows = []
        for name in dict.fromkeys(r.source for r in self._forecasts):
            mine = [r for r in self._forecasts if r.source == name]
            kept = [r for r in mine if r.available_at <= decision_time]
            rows.append({"source": name, "status": "fake", "last_vintage": max((r.vintage for r in kept), default=None),
                         "last_available_at": max((r.available_at for r in kept), default=None), "rows": len(kept),
                         "rows_after_decision_time": len(mine) - len(kept)})
        return pd.DataFrame(rows, columns=list(FORECAST_STATUS_COLUMNS))

    def analyst_inputs(self, ticker: str) -> AnalystInput:
        return self._analyst.get(ticker.upper(), AnalystInput(ticker.upper()))

    def panel(self, name: str, columns: Sequence[str] | None = None) -> pd.DataFrame:
        if name not in self._panels:
            raise DataUnavailable("panel", name, "not in the fake source")
        p = self._panels[name]
        return p if columns is None else p[list(dict.fromkeys([*columns, "available_at"]))]


class CompositeSource:
    """One source made of parts. Each data method asks the parts that have it, in order, and returns the first answer;
    a part that raises DataUnavailable passes the request to the next. When no part answers, the last
    DataUnavailable stands, as a real gap would. Intuition: supply the data you license, keep the public data for the
    rest.

    Example: `CompositeSource(MyVendorSource(cfg), PublicSource(cfg, fundamentals=my_vendor))`.
    """

    def __init__(self, *parts: object) -> None:
        if not parts:
            raise ValueError("a composite source needs at least one part")
        self.parts = parts

    def __getattr__(self, name: str):
        if name not in SOURCE_METHODS:
            raise AttributeError(name)
        methods = [m for m in (getattr(p, name, None) for p in self.parts) if callable(m)]

        def ask(*args, **kwargs):
            gap = DataUnavailable(name, "-", "no part of the composite source serves this kind")
            for method in methods:
                try:
                    return method(*args, **kwargs)
                except DataUnavailable as exc:
                    gap = exc
            raise gap

        return ask

    def served_by(self) -> dict[str, str]:
        """Which parts can serve each method, in the order they are asked (class names, or "none")."""
        return {name: " then ".join(type(p).__name__ for p in self.parts if callable(getattr(p, name, None))) or "none"
                for name in SOURCE_METHODS}


class PublicSource:
    """The kinds that come from free US public data, with no WRDS: SEC EDGAR filings (facts, filing list, balance
    sheets and schedules, filing text, first-reported cash flows), the US Treasury par curve, the public macro
    forecasts (SPF, FOMC SEP, Treasury forwards, SLOOS) and the analyst YAML.

    `fundamentals` serves `financials` (your source); the facts take their LTM figures from its quarters. `market`
    (optional) serves `hy_index`; the forecast registry then carries the current HY level from it, in place of the
    TRACE benchmark rows. An issuer needs a CIK for the SEC kinds.
    """

    # The forecast loaders that read public files; the Treasury forwards and the HY level come from the run's parts.
    PUBLIC_FORECASTS = tuple(n for n in fs.SOURCES if n not in ("trace_hy_benchmark", "ust_forward"))
    FETCHING_FORECASTS = ("spf", "fomc_sep", "sloos")

    def __init__(self, cfg: DataConfig, fundamentals: object, market: object | None = None) -> None:
        self.cfg, self.fundamentals, self.market = cfg, fundamentals, market
        self._forecast_status: dict[datetime, pd.DataFrame] = {}

    def facts(self, issuer: Issuer, decision_time: datetime) -> IssuerFacts:
        return edgar_filings.facts_from_financials(issuer, decision_time, self.cfg, self.fundamentals.financials(issuer))

    def filings(self, issuer: Issuer, forms: Sequence[str]) -> list[Filing]:
        return edgar_filings.filings(issuer, forms, self.cfg)

    def balance_sheet(self, issuer: Issuer, accession: str) -> BalanceSheet:
        return edgar_filings.balance_sheet(issuer, accession, self.cfg)

    def filing_text(self, issuer: Issuer, accession: str) -> FilingText:
        return edgar_filings.filing_text(issuer, accession, self.cfg)

    def reported_cash_flow(self, issuer: Issuer, period_end: datetime, decision_time: datetime) -> ReportedCashFlow:
        return edgar_filings.reported_cash_flow(issuer, period_end, decision_time, self.cfg)

    def curve(self, on: datetime) -> Curve:
        return treasury_curve.curve(on, self.cfg)

    def curves(self, start: datetime, end: datetime) -> list[Curve]:
        return treasury_curve.curves(start, end, self.cfg)

    def forecasts(self, decision_time: datetime) -> list[ForecastRow]:
        t = pd.Timestamp(decision_time).to_pydatetime()
        guard = {n: {"fetch": guarded_fetch(self.cfg, fs.fetch_bytes)} for n in self.FETCHING_FORECASTS}
        rows = fs.load_all(t, self.cfg.root, sources=self.PUBLIC_FORECASTS, options=guard).rows()
        status = [fs.source_status()]
        for extra, extra_status in (self._ust_rows(t), self._hy_rows(t)):
            rows += extra
            status.append(pd.DataFrame([extra_status]))
        self._forecast_status[t] = pd.concat(status, ignore_index=True)[list(FORECAST_STATUS_COLUMNS)]
        return rows

    def forecast_status(self, decision_time: datetime) -> pd.DataFrame:
        t = pd.Timestamp(decision_time).to_pydatetime()
        if t not in self._forecast_status:
            self.forecasts(t)
        return self._forecast_status[t]

    def _ust_rows(self, t: datetime) -> tuple[list[ForecastRow], dict]:
        """Treasury forward paths (source "ust_forward") from the latest curve public at `t`: the market part's curve
        when it has one (a curve table), else the public US Treasury curve."""
        empty = {"source": "ust_forward", "last_vintage": None, "last_available_at": None, "rows": 0,
                 "rows_after_decision_time": 0}
        try:
            c = self._curve(t)
        except DataUnavailable as exc:
            return [], {**empty, "status": f"stubbed: {exc}"}
        rows = [r for r in fs.ust_forward_rows(c.as_row()) if r.available_at <= t]
        return rows, {**empty, "status": "live", "last_vintage": c.as_of, "last_available_at": c.available_at,
                      "rows": len(rows)}

    def _curve(self, t: datetime) -> Curve:
        if self.market is not None and callable(getattr(self.market, "curve", None)):
            try:
                return self.market.curve(t)
            except DataUnavailable:
                pass
        return self.curve(t)

    def _hy_rows(self, t: datetime) -> tuple[list[ForecastRow], dict]:
        """hy_spread and distress_ratio at horizon 0 from `market.hy_index` (method "market_implied")."""
        empty = {"source": "hy_index", "last_vintage": None, "last_available_at": None, "rows": 0,
                 "rows_after_decision_time": 0}
        if self.market is None:
            return [], {**empty, "status": "stubbed: no market part"}
        try:
            lvl = self.market.hy_index(t)
        except DataUnavailable as exc:
            return [], {**empty, "status": f"stubbed: {exc}"}
        rows = [ForecastRow("hy_index", var, 0, lvl.as_of, lvl.available_at, val, method="market_implied")
                for var, val in (("hy_spread", lvl.spread), ("distress_ratio", lvl.distress)) if val == val]
        return rows, {**empty, "status": "live", "last_vintage": lvl.as_of, "last_available_at": lvl.available_at,
                      "rows": len(rows)}

    def analyst_inputs(self, ticker: str) -> AnalystInput:
        return reference.analyst_inputs(ticker)
