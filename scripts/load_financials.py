"""Load point-in-time issuer financials from WRDS Compustat PIT and SEC EDGAR (methodology Section 3.2).

Run from the repo root:
    PYTHONPATH=. python3 scripts/load_financials.py --tickers HCA F --start 2015-01-01 --end 2026-09-30

Needs ~/.pgpass for WRDS. Set $SEC_USER_AGENT to "Name email" for EDGAR.
Writes data/raw/ caches and data/raw/financials_<tickers>.parquet (git ignores data/raw/).
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from hy.sources import compustat_pit as cp
from hy.sources import edgar, financials, xbrl

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--tickers", nargs="+", required=True)
    ap.add_argument("--start", default="2015-01-01")
    ap.add_argument("--end", default="2026-09-30")
    ap.add_argument("--refresh", action="store_true", help="ignore cached WRDS pulls")
    args = ap.parse_args()

    con = cp.connect()
    ids = cp.lookup_issuers(con, args.tickers)
    if ids.empty:
        raise SystemExit(f"no Compustat issuer for {args.tickers}")
    missing_cik = ids[ids["cik"].isna()]
    if len(missing_cik):
        print(f"no CIK in Compustat, EDGAR timing skipped: {missing_cik['tic'].tolist()}")
    vint = cp.load_vintages(con, ids["gvkey"].tolist(), args.start, args.end, cache_root=RAW, refresh=args.refresh)
    idx = pd.concat([edgar.filing_index(c, cache_root=RAW) for c in ids["cik"].dropna().unique()], ignore_index=True)
    cik_by_gvkey = dict(zip(ids["gvkey"], ids["cik"]))
    gaps = vint[~vint["pit_exact"]]
    if len(gaps):
        facts = {edgar._cik10(c): xbrl.company_facts(c, cache_root=RAW) for c in ids["cik"].dropna().unique()}
        filled = xbrl.fill_quarters(gaps, facts, idx, cik_by_gvkey,
                                     pit_first=vint[vint["pit_exact"] & (vint["vintage"] == 0)])
        check = ["revenue", "capex", "operating_cash_flow", "cash", "debt_long_term", "oibdp"]
        print("xbrl vs compustat latest (share within 1%):",
              {k: round(v, 2) for k, v in financials.compare_sources(filled, gaps, check).items()})
        vint = financials.replace_inexact(vint, filled)
    matched = financials.match_filings(vint, edgar.periodic_filings(idx), cik_by_gvkey)

    out = RAW / f"financials_{'_'.join(t.upper() for t in args.tickers)}.parquet"
    matched.to_parquet(out, index=False)
    store = financials.build_store(matched)

    print(ids.to_string(index=False))
    print("timing:", {k: round(v, 3) for k, v in financials.timing_report(matched).items()})
    print(matched[matched["vintage"] == 0].groupby(["gvkey", "value_source"]).size().to_string())
    cols = ["gvkey", "datadate", "vintage", "available_at", "value_source", "revenue", "oibdp",
            "special_items", "capex", "operating_cash_flow", "debt_long_term"]
    print(matched.sort_values(["gvkey", "datadate", "vintage"]).groupby("gvkey").tail(5)[cols].to_string(index=False))
    print(f"records: {sum(1 for _ in store.history(pd.Timestamp.max.to_pydatetime()))}  ->  {out}")


if __name__ == "__main__":
    main()
