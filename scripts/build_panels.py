"""Build the `bond_panel` and `leverage` panels from the tables (docs/production_wiring.md, step 4; hy.data.panels).

Reads every issuer, bond and observation in `<HY_DATA_ROOT>/tables/`, the Treasury curve from the run's source (the
curve table, else the public US Treasury files), and writes `tables/panels/bond_panel.parquet` and
`tables/panels/leverage.parquet`. The small panels (gics, ratings, annual_ebitda, equity_monthly) are exported
directly; this script does not build them.

    HY_SOURCE=hy.data.tables:make_source HY_DATA_ROOT=/path/to/data PYTHONPATH=. python3 scripts/build_panels.py \
        --start 2010-01-31 --end 2026-08-31
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hy.data import config as data_config  # noqa: E402
from hy.data import panels  # noqa: E402
from hy.data.factory import open_source  # noqa: E402
from hy.data.pit import DataUnavailable  # noqa: E402
from hy.data.tables import TableSource  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--start", required=True, help="first month end")
    ap.add_argument("--end", required=True, help="last month end")
    a = ap.parse_args()
    cfg = data_config.CONFIG
    tables, source = TableSource(cfg), open_source(cfg)
    months = panels.month_ends(a.start, a.end)
    tickers = tables.table("issuers")["ticker"].astype(str).str.upper().tolist()
    issuers = tables.issuers(tickers)
    bonds = [b for i in issuers for b in tables.bonds(i)]
    curves: dict[pd.Timestamp, pd.Series] = {}

    def curve_for(t: pd.Timestamp) -> pd.Series:
        # The curve public the day after the month end is the one dated on or before it (trace_panel rule 6).
        if t not in curves:
            curves[t] = source.curve((t + pd.Timedelta(1, unit="D")).to_pydatetime()).as_row()
        return curves[t]

    out = tables.folder / "panels"
    out.mkdir(parents=True, exist_ok=True)
    obs = tables.raw_observations().rename(columns={"bond_id": "cusip"})
    obs["cusip"] = obs["cusip"].astype(str)
    bp = panels.bond_panel(issuers, bonds, obs, months, curve_for)
    bp.to_parquet(out / "bond_panel.parquet", index=False)
    fin = []
    for i in issuers:
        try:
            fin += tables.financials(i)
        except DataUnavailable:
            continue
    lev = panels.leverage_panel(fin, months)
    lev.to_parquet(out / "leverage.parquet", index=False)
    print(f"{len(months)} months, {len(issuers)} issuers, {len(bonds)} bonds")
    print(f"bond_panel: {len(bp)} rows -> {out / 'bond_panel.parquet'}")
    print(f"leverage: {len(lev)} rows -> {out / 'leverage.parquet'}")


if __name__ == "__main__":
    main()
