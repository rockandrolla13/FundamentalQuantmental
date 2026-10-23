"""US Treasury par curve adapter (wraps hy.sources.treasury)."""

from __future__ import annotations

from datetime import datetime

import pandas as pd

from hy.data.adapters import guarded_fetch
from hy.data.config import DataConfig
from hy.data.pit import DataUnavailable
from hy.data.records import Curve
from hy.sources import treasury as tr


def curve(on: datetime, cfg: DataConfig) -> Curve:
    """The latest curve that was public by `on`. A curve dated d is published at d + 1 day, so the curve dated `on`
    itself is not yet known at `on`; `curve_on` selects by curve date, so step back until the curve is public."""
    try:
        row = tr.curve_on(on, cache_root=cfg.root, fetch=guarded_fetch(cfg, tr.fetch_url))
        while "available_at" in row and pd.Timestamp(row["available_at"]) > pd.Timestamp(on):
            row = tr.curve_on(pd.Timestamp(row.name) - pd.Timedelta(1, unit="D"), cache_root=cfg.root,
                              fetch=guarded_fetch(cfg, tr.fetch_url))
    except Exception as exc:  # noqa: BLE001
        raise DataUnavailable("curve", str(pd.Timestamp(on).date()), f"{type(exc).__name__}: {exc}") from exc
    ten = [t for t in row.index if t != "available_at"]
    avail = pd.Timestamp(row["available_at"]).to_pydatetime() if "available_at" in row else pd.Timestamp(row.name).to_pydatetime()
    return Curve("UST", pd.Timestamp(row.name).to_pydatetime(), avail, tenors=tuple(float(t) for t in ten),
                 yields=tuple(float(row[t]) for t in ten))
