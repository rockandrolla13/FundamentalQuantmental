"""Choose the data source of a run in one place (design: data module; docs/production_wiring.md).

Before this module, six scripts built `WarehouseSource(CONFIG)` themselves, so another machine had to edit each of
them. Now every run asks `open_view(decision_time)`. The environment variable `HY_SOURCE` names the source:

- unset or "warehouse": this machine's WRDS warehouse (`hy.data.sources.WarehouseSource`).
- "package.module:factory": `factory(cfg)` from that module returns the source. Example:
  `HY_SOURCE=mydata.hy_source:make_source`. The factory receives the run's `DataConfig`.
"""

from __future__ import annotations

import importlib
import os
from datetime import datetime
from typing import Any

from hy.data import config as data_config
from hy.data.config import DataConfig
from hy.data.view import DataView

SOURCE_ENV = "HY_SOURCE"
WAREHOUSE = "warehouse"


def open_source(cfg: DataConfig | None = None, spec: str | None = None) -> Any:
    """The source that `spec` (default: `HY_SOURCE`) names, built with `cfg` (default: the run's config)."""
    cfg = cfg or data_config.CONFIG  # read at call time, so a test or a run can replace the config
    spec = spec or os.environ.get(SOURCE_ENV) or WAREHOUSE
    if spec == WAREHOUSE:
        from hy.data.sources import WarehouseSource  # noqa: PLC0415 - only this choice needs the warehouse adapters

        return WarehouseSource(cfg)
    module, _, name = spec.partition(":")
    if not module or not name:
        raise ValueError(f"{SOURCE_ENV}={spec!r}: use 'warehouse' or 'package.module:factory'")
    factory = getattr(importlib.import_module(module), name)
    return factory(cfg)


def open_view(decision_time: datetime, cfg: DataConfig | None = None) -> DataView:
    """A view of the run's source at `decision_time`."""
    return DataView(open_source(cfg), decision_time)
