"""Check the run's data source against the data contract (docs/production_wiring.md, step 3).

Reads every kind for the tickers at the decision time through a `DataView`, prints which part serves each kind and
one row per check, writes the table to `<HY_DATA_ROOT>/check_source.csv`, and exits 1 when a required check fails.

    HY_SOURCE=hy.data.tables:make_source HY_DATA_ROOT=/path/to/data PYTHONPATH=. python3 scripts/check_source.py \
        AAA BBB --decision 2026-09-18
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hy.data import config as data_config  # noqa: E402
from hy.data.contract import check_source, failures  # noqa: E402
from hy.data.factory import open_source  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("tickers", nargs="+")
    ap.add_argument("--decision", default=str(pd.Timestamp.now().normalize().date()),
                    help="decision time (default: today 00:00); a run at END decides at END + 1 day")
    a = ap.parse_args()
    source = open_source()
    print(f"source: {type(source).__name__}; data root: {data_config.CONFIG.root}")
    if hasattr(source, "served_by"):
        for kind, part in source.served_by().items():
            print(f"  {kind:<20} {part}")
    rep = check_source(source, [t.upper() for t in a.tickers], pd.Timestamp(a.decision).to_pydatetime())
    with pd.option_context("display.max_colwidth", 110, "display.width", 200):
        print(rep.to_string(index=False))
    out = data_config.CONFIG.path("check_source.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    rep.to_csv(out, index=False)
    bad = failures(rep)
    print(f"\n{len(rep)} checks, {int((~rep['ok']).sum())} failed, {len(bad)} of them required. Table: {out}")
    return 1 if len(bad) else 0


if __name__ == "__main__":
    sys.exit(main())
