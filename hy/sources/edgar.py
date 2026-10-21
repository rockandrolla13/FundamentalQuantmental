"""SEC EDGAR filing index with acceptance timestamps (methodology Section 3.2, `filing_date`).

Source: https://data.sec.gov/submissions/CIK##########.json and its older pages.
`acceptanceDateTime` is UTC. The SEC asks every client to send a User-Agent
with a contact; set $SEC_USER_AGENT to "Name email". The SEC also limits
clients to 10 requests a second; `fetch_json` waits between calls.
"""

from __future__ import annotations

import json
import os
import time
import urllib.request
import warnings
from collections.abc import Callable
from pathlib import Path

import pandas as pd

BASE = "https://data.sec.gov/submissions/"
PERIODIC_FORMS = ("10-Q", "10-K", "10-Q/A", "10-K/A", "10-KT", "10-QT")
_MIN_INTERVAL = 0.15
_last_call = 0.0

Fetch = Callable[[str], dict]


def user_agent() -> str:
    ua = os.environ.get("SEC_USER_AGENT")
    if not ua:
        warnings.warn("SEC_USER_AGENT is not set; the SEC asks for 'Name email'. Using a generic agent.", stacklevel=2)
        return "FundamentalQuantmental research-loader"
    return ua


def fetch_json(url: str) -> dict:
    """GET one JSON document from data.sec.gov, at most about 7 calls a second."""
    global _last_call
    wait = _MIN_INTERVAL - (time.monotonic() - _last_call)
    if wait > 0:
        time.sleep(wait)
    req = urllib.request.Request(url, headers={"User-Agent": user_agent(), "Accept-Encoding": "identity"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        _last_call = time.monotonic()
        return json.loads(resp.read())


def _cik10(cik: int | str) -> str:
    return f"{int(float(cik)):010d}"


def _frame(block: dict, cik: str) -> pd.DataFrame:
    keys = ("accessionNumber", "form", "reportDate", "filingDate", "acceptanceDateTime")
    df = pd.DataFrame({k: block.get(k, []) for k in keys})
    df.insert(0, "cik", cik)
    return df


def filing_index(cik: int | str, fetch: Fetch = fetch_json, cache_root: Path | None = None) -> pd.DataFrame:
    """All filings for one CIK: form, report date, filing date, and acceptance time (naive UTC).

    Reads the recent block and every older page. Caches the raw JSON pages under `cache_root/edgar/`.
    """
    cik10 = _cik10(cik)

    def get(name: str) -> dict:
        path = cache_root / "edgar" / name if cache_root else None
        if path is not None and path.exists():
            return json.loads(path.read_text())
        doc = fetch(BASE + name)
        if path is not None:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(doc))
        return doc

    head = get(f"CIK{cik10}.json")
    frames = [_frame(head["filings"]["recent"], cik10)]
    for page in head["filings"].get("files", []):
        frames.append(_frame(get(page["name"]), cik10))
    df = pd.concat(frames, ignore_index=True).rename(
        columns={"accessionNumber": "accession", "reportDate": "report_date", "filingDate": "filing_date",
                 "acceptanceDateTime": "acceptance"}
    )
    df["report_date"] = pd.to_datetime(df["report_date"], errors="coerce")
    df["filing_date"] = pd.to_datetime(df["filing_date"], errors="coerce")
    df["acceptance"] = pd.to_datetime(df["acceptance"], errors="coerce", utc=True).dt.tz_localize(None)
    return df.drop_duplicates("accession").reset_index(drop=True)


def periodic_filings(index: pd.DataFrame, include_amendments: bool = False) -> pd.DataFrame:
    """10-Q and 10-K rows only; amendments (/A) only on request."""
    forms = PERIODIC_FORMS if include_amendments else tuple(f for f in PERIODIC_FORMS if not f.endswith("/A"))
    return index[index["form"].isin(forms)].reset_index(drop=True)
