"""Compustat point-in-time adapter: issuer identity and quarterly financials (wraps hy.sources.clock_inputs,
hy.sources.financials)."""

from __future__ import annotations

from hy.data.adapters import guarded_fetch
from hy.data.config import DataConfig
from hy.data.pit import DataUnavailable
from hy.data.records import Issuer, IssuerFinancials
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
