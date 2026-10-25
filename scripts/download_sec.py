"""Download the SEC EDGAR files that the analyst reads into the cache under HY_DATA_ROOT (docs/production_wiring.md 3).

Run it on a machine that reaches sec.gov. Then run the analyst there, or copy the folder `<HY_DATA_ROOT>/edgar/` to
a machine without internet and run it with HY_OFFLINE=1. The files are the ones the code itself caches, written by
the code's own loaders, so the run reads them back unchanged.

Per issuer (CIK) it writes:
1. `edgar/CIK##########.json` and its older pages: the filing index with acceptance times (filings, facts, events).
2. `edgar/companyfacts_CIK##########.json`: the XBRL company facts (first-reported cash flows).
3. `edgar/instances/<accession>.xml`: the XBRL instance of every original 10-Q and 10-K accepted on or after `--start`
   (balance sheets, schedules, lease and debt ladders).
4. `edgar/text/<accession>.txt`: the plain text of each such filing's primary document (business line, covenants,
   lease and RPO sentences).

A rerun fetches the two index files again, so new filings appear, and skips every filing already in the cache. Each
file's outcome goes to `edgar/download_log.csv`. The SEC limits clients to 10 requests a second; the loaders wait
between calls. Set SEC_USER_AGENT to "Your Name your@email", as the SEC asks.

    SEC_USER_AGENT="Name email" HY_DATA_ROOT=/path/to/data PYTHONPATH=. python3 scripts/download_sec.py \
        --from-tables --start 2018-01-01
    ... scripts/download_sec.py --tickers AAPL F --start 2018-01-01
    ... scripts/download_sec.py --ciks 320193 37996 --start 2018-01-01
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Callable, Sequence

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hy.data import config as data_config  # noqa: E402
from hy.sources import clock_inputs as ci  # noqa: E402
from hy.sources import edgar, xbrl  # noqa: E402
from hy.sources import xbrl_instance as xi  # noqa: E402

LOG_COLUMNS = ("time", "issuer", "cik", "kind", "accession", "status")


def ciks_for(tickers: Sequence[str], fetch: Callable = edgar.fetch_json) -> list[tuple[str, str]]:
    """(ticker, CIK) from the SEC ticker file; a ticker that the file does not hold raises LookupError."""
    doc = fetch(ci.TICKERS_URL)
    by_ticker = {str(v["ticker"]).upper(): str(v["cik_str"]) for v in doc.values()}
    missing = [t for t in tickers if t.upper() not in by_ticker]
    if missing:
        raise LookupError(f"not in the SEC ticker file: {missing}; pass their CIKs with --ciks")
    return [(t.upper(), by_ticker[t.upper()]) for t in tickers]


def ciks_from_tables(folder: Path) -> list[tuple[str, str]]:
    """(ticker, CIK) of every issuer with a CIK in `tables/issuers` (docs/production_wiring.md 4.1)."""
    for ext, read in ((".parquet", pd.read_parquet), (".csv", pd.read_csv)):
        p = folder / f"issuers{ext}"
        if p.exists():
            t = read(p)
            t = t[t["cik"].notna()] if "cik" in t else t.iloc[0:0]
            return [(str(r["ticker"]).upper(), str(r["cik"]).split(".")[0]) for r in t.to_dict("records")]
    raise FileNotFoundError(f"no issuers.parquet or issuers.csv in {folder}")


def download_issuer(name: str, cik: str, root: Path, start: pd.Timestamp, fetch: Callable = edgar.fetch_json,
                    fetch_raw: Callable = xi.fetch_bytes) -> list[dict]:
    """Every file of one issuer into `root/edgar/`; one log row per file. A failed filing does not stop the rest."""
    rows: list[dict] = []

    def log(kind: str, accession: str, status: str) -> None:
        rows.append({"time": pd.Timestamp.now().floor("s"), "issuer": name, "cik": cik, "kind": kind,
                     "accession": accession, "status": status})

    try:
        idx = edgar.filing_index(cik, fetch=fetch, cache_root=root, refresh=True)
        log("filing_index", "", f"ok: {len(idx)} filings")
    except Exception as exc:  # noqa: BLE001 - without the index nothing else of this issuer can load
        log("filing_index", "", f"failed: {type(exc).__name__}: {exc}"[:200])
        return rows
    try:
        xbrl.company_facts(cik, fetch=fetch, cache_root=root, refresh=True)
        log("company_facts", "", "ok")
    except Exception as exc:  # noqa: BLE001 - small filers have no company facts; the rest still loads
        log("company_facts", "", f"failed: {type(exc).__name__}: {exc}"[:200])
    per = edgar.periodic_filings(idx)
    per = per[per["acceptance"].notna() & (per["acceptance"] >= start)].sort_values("acceptance")
    for acc in per["accession"]:
        for kind, path, load in (
            ("instance", root / "edgar" / "instances" / f"{acc}.xml",
             lambda a=acc: xi.load_instance(cik, a, cache_root=root, fetch=fetch, fetch_raw=fetch_raw)),
            ("text", root / "edgar" / "text" / f"{acc}.txt",
             lambda a=acc: ci.filing_text(cik, a, root, fetch=fetch, fetch_raw=fetch_raw)),
        ):
            if path.exists():
                log(kind, acc, "cached")
                continue
            try:
                load()
                log(kind, acc, "ok")
            except Exception as exc:  # noqa: BLE001 - an old filing without XBRL is a gap, not a stop
                log(kind, acc, f"failed: {type(exc).__name__}: {exc}"[:200])
    return rows


def download(issuers: Sequence[tuple[str, str]], root: Path, start: pd.Timestamp, fetch: Callable = edgar.fetch_json,
             fetch_raw: Callable = xi.fetch_bytes, echo: Callable[[str], None] = print) -> pd.DataFrame:
    """`download_issuer` for each (name, CIK); appends the rows to `root/edgar/download_log.csv` and returns them."""
    out = []
    for k, (name, cik) in enumerate(issuers, start=1):
        t0 = time.time()
        rows = download_issuer(name, cik, root, start, fetch, fetch_raw)
        bad = sum(r["status"].startswith("failed") for r in rows)
        echo(f"[{k}/{len(issuers)}] {name} CIK {cik}: {len(rows)} files, {bad} failed, {time.time() - t0:.0f} s")
        out += rows
    log = pd.DataFrame(out, columns=list(LOG_COLUMNS))
    path = root / "edgar" / "download_log.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    log.to_csv(path, mode="a", header=not path.exists(), index=False)
    return log


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    who = ap.add_mutually_exclusive_group(required=True)
    who.add_argument("--tickers", nargs="+", help="tickers; the SEC ticker file gives their CIKs")
    who.add_argument("--ciks", nargs="+", help="CIKs, for issuers the ticker file does not hold")
    who.add_argument("--from-tables", action="store_true", help="every issuer with a CIK in <HY_DATA_ROOT>/tables/issuers")
    ap.add_argument("--start", default="2015-01-01", help="first acceptance date of the 10-Q and 10-K files")
    a = ap.parse_args()
    cfg = data_config.CONFIG
    if not cfg.allow_network:
        print("HY_OFFLINE=1 forbids the network; unset it to download")
        return 2
    if not os.environ.get("SEC_USER_AGENT"):
        # The SEC answers 403 Forbidden to a request without a contact (checked 2026-10-25).
        print('set SEC_USER_AGENT="Your Name your@email" first; the SEC refuses requests without a contact')
        return 2
    if a.from_tables:
        issuers = ciks_from_tables(cfg.path("tables"))
    elif a.tickers:
        try:
            issuers = ciks_for(a.tickers)
        except LookupError as exc:
            print(exc)
            return 2
        except OSError as exc:  # urllib errors: no route to sec.gov, or 403 for a bad contact
            print(f"cannot read the SEC ticker file {ci.TICKERS_URL}: {exc}")
            return 2
    else:
        issuers = [(c, c) for c in a.ciks]
    print(f"{len(issuers)} issuers -> {cfg.path('edgar')}, filings accepted from {a.start}")
    log = download(issuers, cfg.root, pd.Timestamp(a.start))
    failed = log[log["status"].str.startswith("failed")]
    no_index = failed[failed["kind"] == "filing_index"]
    print(f"{len(log)} files: {int((log['status'] == 'cached').sum())} cached, {len(failed)} failed "
          f"({len(no_index)} issuers without an index). Log: {cfg.path('edgar', 'download_log.csv')}")
    return 1 if len(no_index) else 0


if __name__ == "__main__":
    sys.exit(main())
