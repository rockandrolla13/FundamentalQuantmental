"""Compustat point-in-time adapter: issuer identity, quarterly financials and the equity market value (wraps
hy.sources.clock_inputs, hy.sources.financials; the market value query moved here from scripts/process.py)."""

from __future__ import annotations

from datetime import datetime

import pandas as pd

from hy.data.adapters import LazyConnection, guarded_fetch
from hy.data.config import DataConfig
from hy.data.pit import DataUnavailable
from hy.data.records import Issuer, IssuerFinancials, MarketValue
from hy.sources import clock_inputs as ci
from hy.sources import edgar
from hy.sources import financials as fin


def issuer(ticker: str, cfg: DataConfig) -> Issuer:
    """Identifiers for `ticker`: the cached Compustat lookup, then WRDS, then the SEC ticker file."""
    try:
        d = ci.lookup_issuer(ticker, cfg.root, fetch=guarded_fetch(cfg, edgar.fetch_json))
    except Exception as exc:  # noqa: BLE001 - every failure means the same thing to the caller
        raise DataUnavailable("issuer", ticker, f"{type(exc).__name__}: {exc}") from exc
    return Issuer(ticker.upper(), gvkey=d.get("gvkey"), cik=d.get("cik"), name=d.get("conm", ""))


def financials(iss: Issuer, cfg: DataConfig) -> list[IssuerFinancials]:
    """Every version of every quarter in the cached point-in-time parquet (the view filters by decision time)."""
    if not iss.gvkey:
        raise DataUnavailable("financials", iss.ticker, "no gvkey")
    hit = ci._parquet_for(iss.gvkey, cfg.root)  # noqa: SLF001 - wrapped until step 7 moves the body here
    if hit is None:
        raise DataUnavailable("financials", iss.ticker, "no cached point-in-time parquet")
    return [r for r in fin.build_store(hit[0]).records() if r.key == iss.gvkey]


def market_value(iss: Issuer, on: datetime, cfg: DataConfig) -> MarketValue:
    """Price x shares (`comp.fundq` prccq x cshoq) of the latest quarter with a report date on or before `on`."""
    if not iss.gvkey:
        raise DataUnavailable("market_value", iss.ticker, "no gvkey")
    day = pd.Timestamp(on).date()
    try:
        df = LazyConnection(cfg).raw_sql(f"select datadate, rdq, prccq, cshoq from comp.fundq where gvkey = '{iss.gvkey}' "
                                         f"and rdq <= '{day}' and prccq is not null order by datadate desc limit 1")
    except Exception as exc:  # noqa: BLE001 - offline or no WRDS: the value is unavailable
        raise DataUnavailable("market_value", iss.ticker, f"{type(exc).__name__}: {exc}") from exc
    if df.empty:
        raise DataUnavailable("market_value", iss.ticker, "no Compustat price")
    r = df.iloc[0]
    as_of = pd.Timestamp(r["datadate"]).to_pydatetime()
    avail = max(as_of, pd.Timestamp(r["rdq"]).to_pydatetime())
    return MarketValue(iss.ticker, as_of, avail, issuer_ticker=iss.ticker, value=float(r["prccq"] * r["cshoq"]),
                       source=f"Compustat fundq {r['datadate']} (reported {r['rdq']})")
