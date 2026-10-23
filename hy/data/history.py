"""Raw panels for the backtest replays (design: data module; review finding AR-DEP-001).

A replay reads the whole history once and applies the point-in-time rule month by month itself (`hy.backtest`
guards each month). So it reads through a view at the present time. The pilot tag is a warehouse subset kept for
old runs; it is not part of the data contract, so it alone reads the warehouse file of that tag.
"""

from __future__ import annotations

from typing import Sequence

import pandas as pd

from hy.data.config import CONFIG, DataConfig
from hy.data.sources import WarehouseSource
from hy.data.view import DataView

# Panels that the warehouse also keeps as a tagged subset (file prefix per neutral name).
TAGGED = {"bond_panel": "panel", "leverage": "leverage"}


def history_view(cfg: DataConfig | None = None) -> DataView:
    """A view of the whole history: the decision time is now."""
    return DataView(WarehouseSource(cfg or CONFIG), pd.Timestamp.now())


def backtest_panel(name: str, tag: str = "full", columns: Sequence[str] | None = None,
                   view: DataView | None = None) -> pd.DataFrame:
    """The raw panel `name` (one of `hy.data.source.PANELS`) for a replay. Tag "full" reads through the view; another
    tag reads the warehouse's subset file `<prefix>_<tag>.parquet`."""
    if tag == "full" or name not in TAGGED:
        return (view or history_view()).panel(name, columns)
    return pd.read_parquet(CONFIG.path("backtest", f"{TAGGED[name]}_{tag}.parquet"),
                           columns=None if columns is None else list(columns))
