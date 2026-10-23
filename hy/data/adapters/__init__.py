"""Vendor adapters: the only code that knows vendor schemas, SQL, URLs and cleaning rules (design: data module).

Step 3 wraps the existing `hy.sources` functions without changing them; step 7 moves their bodies here. Every adapter
takes a `DataConfig`, honours `allow_network`, and returns `hy.data.records` types.
"""

from __future__ import annotations

from typing import Any, Callable

from hy.data.config import DataConfig, NetworkDisabled


def guarded_fetch(cfg: DataConfig, fetch: Callable[[str], Any]) -> Callable[[str], Any]:
    """`fetch`, or a fetch that raises NetworkDisabled when the run is offline."""
    if cfg.allow_network:
        return fetch

    def refuse(url: str) -> Any:
        raise NetworkDisabled(f"offline run: {url} is not in the cache")

    return refuse


class LazyConnection:
    """A WRDS connection that opens only when a query reaches it (a cache hit never does)."""

    def __init__(self, cfg: DataConfig) -> None:
        self._cfg = cfg

    def raw_sql(self, sql: str, *args: Any, **kwargs: Any) -> Any:
        return self._cfg.connect().raw_sql(sql, *args, **kwargs)
