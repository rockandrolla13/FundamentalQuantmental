"""Pull the `market_equity` panel for ESP with market leverage (methodology 7.2; Dynkin et al. 2021 ch. 13, note 5).

Run on the machine with WRDS access, after the leverage panel exists:
    PYTHONPATH=. python3 scripts/pull_market_equity.py [--refresh]

It reads every gvkey of the `leverage` panel, pulls `comp.fundq` price x shares and book debt per quarter, and caches
data/raw/backtest/market_equity.parquet. Then run `scripts/backtest_peers.py --tag full` to score esp_mlev.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from hy.data.history import history_view  # noqa: E402
from hy.sources import compustat_pit, peer_data  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true", help="pull every gvkey again, ignoring the cache")
    a = ap.parse_args()
    lev = history_view().panel("leverage", ["gvkey"])
    gvkeys = sorted(lev["gvkey"].astype(str).unique())
    print(f"gvkeys in leverage panel: {len(gvkeys)}")
    out = peer_data.market_equity_quarterly(compustat_pit.connect(), gvkeys, refresh=a.refresh)
    ok = (out["mkt_equity"] > 0) & out["debt"].notna()
    print(f"market_equity rows {len(out)}, gvkeys {out['gvkey'].nunique()}, usable {ok.mean():.1%}, "
          f"{out['datadate'].min():%Y-%m} to {out['datadate'].max():%Y-%m}")


if __name__ == "__main__":
    main()
