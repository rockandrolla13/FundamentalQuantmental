"""TRACE adapter: bond terms and daily observations (wraps hy.sources.trace_bonds). Vendor names stop here:
`trade_date`, `price_vw`, `yield_vw` become `date`, `price`, `yield`."""

from __future__ import annotations

from datetime import datetime
from typing import Sequence

import pandas as pd

from hy.data.adapters import LazyConnection
from hy.data.config import DataConfig
from hy.data.pit import DataUnavailable
from hy.data.records import BOND_OBS_COLUMNS, Bond, Issuer, check_observations
from hy.sources import trace_bonds as tb

TRACE_LAG_DAYS = 1  # a trade is public the next day (the process rule: TRACE through t, read at t + 1)


def bonds(iss: Issuer, cfg: DataConfig) -> list[Bond]:
    try:
        m = tb.bond_master(LazyConnection(cfg), [iss.ticker], cache_root=cfg.root)
    except Exception as exc:  # noqa: BLE001
        raise DataUnavailable("bonds", iss.ticker, f"{type(exc).__name__}: {exc}") from exc
    return [Bond(str(r.cusip), iss.ticker, float(r.coupon), pd.Timestamp(r.maturity).to_pydatetime(), str(r.seniority),
                 bool(r.fixed), bool(r.is_convertible), str(r.grade)) for r in m.itertuples()]


def observations(bs: Sequence[Bond], start: datetime, end: datetime, cfg: DataConfig) -> pd.DataFrame:
    """Daily observations of `bs` that were public by `end`."""
    if not bs:
        return pd.DataFrame(columns=list(BOND_OBS_COLUMNS))
    # Trades public by `end` are those traded up to `end` less the TRACE lag; asking for exactly that range keeps the
    # request, and so the cache key, the same as the process has always used.
    last_trade = pd.Timestamp(end).normalize() - pd.Timedelta(TRACE_LAG_DAYS, unit="D")
    try:
        q = tb.bond_quotes(LazyConnection(cfg), [b.cusip for b in bs], str(pd.Timestamp(start).date()),
                           str(last_trade.date()), cache_root=cfg.root)
    except Exception as exc:  # noqa: BLE001
        raise DataUnavailable("observations", ",".join(b.cusip for b in bs)[:60], f"{type(exc).__name__}: {exc}") from exc
    out = pd.DataFrame({"cusip": q["cusip"], "date": pd.to_datetime(q["trade_date"]), "price": q["price_vw"],
                        "yield": q["yield_vw"], "n_trades": q["n_trades"], "par_volume": q["par_volume"]})
    out["available_at"] = out["date"] + pd.Timedelta(TRACE_LAG_DAYS, unit="D")
    return check_observations(out)
