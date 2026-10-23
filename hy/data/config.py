"""One data root and one WRDS connection for every run (design: data module, `config`; review finding AR-DEP-001).

Before this module, 16 files defined their own `RAW = ROOT / "data" / "raw"` and 9 call sites opened their own
WRDS connection. Now a run builds one `DataConfig` (`from_env`) and everything reads its paths and its connection
from it. `HY_DATA_ROOT` points a run at another root, such as a frozen snapshot.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ROOT = REPO_ROOT / "data" / "raw"

_CONNECTION: Any = None


class NetworkDisabled(RuntimeError):
    """Raised when a run that must use cached data only asks for a live connection."""


def _open_wrds(user: str | None) -> Any:
    from hy.sources import compustat_pit  # noqa: PLC0415 - the adapter owns the wrds import

    return compustat_pit.connect(user)


def reset_connection() -> None:
    """Forget the shared connection (tests; a new process starts with none)."""
    global _CONNECTION
    _CONNECTION = None


@dataclass(frozen=True)
class DataConfig:
    """Where data lives and whether a run may reach the network. Intuition: one place to point a run."""

    root: Path = DEFAULT_ROOT
    wrds_user: str | None = None      # None: the user in ~/.pgpass
    allow_network: bool = True        # False: cached data only (tests, replays)
    refresh: bool = False

    @classmethod
    def from_env(cls) -> "DataConfig":
        """The default config, with `HY_DATA_ROOT` and `HY_OFFLINE=1` read from the environment."""
        root = Path(os.environ["HY_DATA_ROOT"]) if os.environ.get("HY_DATA_ROOT") else DEFAULT_ROOT
        return cls(root=root, allow_network=os.environ.get("HY_OFFLINE") != "1")

    def path(self, *parts: str) -> Path:
        """A folder or file under the data root."""
        return self.root.joinpath(*parts)

    def connect(self) -> Any:
        """The process's one WRDS connection, opened on first use."""
        global _CONNECTION
        if not self.allow_network:
            raise NetworkDisabled("this run is offline (allow_network=False); use cached data")
        if _CONNECTION is None:
            _CONNECTION = _open_wrds(self.wrds_user)
        return _CONNECTION


CONFIG = DataConfig.from_env()
