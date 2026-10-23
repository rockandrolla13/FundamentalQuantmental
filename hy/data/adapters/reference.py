"""Reference adapters: GICS sectors (cached WRDS comp.co_hgic), public forecasts, analyst YAML (wraps
hy.sources.peer_data caches, hy.sources.forecast_sources, hy.sources.clock_inputs.load_overrides)."""

from __future__ import annotations

from datetime import datetime
from typing import Sequence

import pandas as pd

from hy.data.config import DataConfig
from hy.data.pit import DataUnavailable
from hy.data.records import AnalystInput, Classification, Issuer
from hy.forecasts import ForecastRow
from hy.sources import clock_inputs as ci
from hy.sources import forecast_sources as fs

ANALYST_DIR = "data/analyst_inputs"


def classifications(issuers: Sequence[Issuer], cfg: DataConfig) -> list[Classification]:
    """GICS sector spells per issuer from the cached history; each spell is public from its start date."""
    f = cfg.path("backtest", "gics_history.parquet")
    if not f.exists():
        raise DataUnavailable("classifications", "gics_history", "no cached GICS history")
    g = pd.read_parquet(f)
    g["gvkey"] = g["gvkey"].astype(str)
    out = []
    for iss in issuers:
        for r in g[g["gvkey"] == str(iss.gvkey)].itertuples():
            t0 = pd.Timestamp(r.indfrom).to_pydatetime()
            out.append(Classification(iss.ticker, t0, t0, issuer_ticker=iss.ticker, sector=str(r.gsector),
                                      rating_class=None, rating_source="none: ratings join the view in step 5"))
    return out


def forecasts(decision_time: datetime, cfg: DataConfig) -> list[ForecastRow]:
    return fs.load_all(decision_time, cfg.root).rows()


def analyst_inputs(ticker: str) -> AnalystInput:
    return AnalystInput(ticker.upper(), ci.load_overrides(ticker, ANALYST_DIR))
