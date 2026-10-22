"""Full XBRL instance of one SEC filing, with dimensions (methodology Sections 3.2 to 3.4).

The company-facts feed (`xbrl.py`) drops every fact that carries a dimension. Schedules by year, revenue
by customer, and amounts by legal entity all carry one. This module reads the filing's own instance
(`*_htm.xml` in the EDGAR archive) and returns one row per fact with its period and dimension members.

Every fact carries the filing's acceptance time as `available_at`. The archive at www.sec.gov rejects
requests without a contact in the User-Agent; set $SEC_USER_AGENT to "Name email".
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd

from hy.sources.edgar import Fetch, _cik10, fetch_json

ARCHIVE = "https://www.sec.gov/Archives/edgar/data/"
XBRLI = "{http://www.xbrl.org/2003/instance}"
XBRLDI = "{http://xbrl.org/2006/xbrldi}"


def fetch_bytes(url: str) -> bytes:
    """GET raw bytes from sec.gov with the same agent and rate limit as `edgar.fetch_json`."""
    import time
    import urllib.request

    from hy.sources import edgar

    wait = edgar._MIN_INTERVAL - (time.monotonic() - edgar._last_call)
    if wait > 0:
        time.sleep(wait)
    req = urllib.request.Request(url, headers={"User-Agent": edgar.user_agent(), "Accept-Encoding": "identity"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        edgar._last_call = time.monotonic()
        return resp.read()


def instance_url(cik: int | str, accession: str, fetch: Fetch = fetch_json) -> str:
    """URL of the filing's XBRL instance: the `*_htm.xml` file, else the single non-linkbase `.xml`."""
    folder = f"{ARCHIVE}{int(_cik10(cik))}/{accession.replace('-', '')}/"
    names = [i["name"] for i in fetch(folder + "index.json")["directory"]["item"]]
    hits = [n for n in names if n.endswith("_htm.xml")]
    if not hits:
        hits = [n for n in names if n.endswith(".xml") and not n.endswith(("_cal.xml", "_def.xml", "_lab.xml",
                                                                          "_pre.xml")) and n != "FilingSummary.xml"]
    if not hits:
        raise FileNotFoundError(f"no XBRL instance in {folder}")
    return folder + hits[0]


def parse_instance(xml: bytes) -> pd.DataFrame:
    """One row per fact: concept, value, unit, period, and a `dims` dict {axis: member}.

    `concept` keeps the prefix (`us-gaap:...` or the filer's own, e.g. `crwv:...`). Instant facts have
    `start` NaT. Numeric facts fill `value`; short non-numeric facts (durations such as "P2Y") fill `text`.
    Text blocks and nil facts are skipped.
    """
    root = ET.fromstring(xml)
    ns_prefix = {}
    for _, (prefix, uri) in ET.iterparse(__import__("io").BytesIO(xml), events=["start-ns"]):
        ns_prefix[uri] = prefix
    contexts = {}
    for c in root.iter(f"{XBRLI}context"):
        period = c.find(f"{XBRLI}period")
        inst = period.find(f"{XBRLI}instant")
        start = period.find(f"{XBRLI}startDate")
        end = period.find(f"{XBRLI}endDate")
        dims = {}
        for m in c.iter(f"{XBRLDI}explicitMember"):
            dims[m.get("dimension")] = (m.text or "").strip()
        for m in c.iter(f"{XBRLDI}typedMember"):
            dims[m.get("dimension")] = "".join(m.itertext()).strip()
        contexts[c.get("id")] = (
            pd.NaT if inst is not None else pd.Timestamp(start.text),
            pd.Timestamp(inst.text if inst is not None else end.text),
            dims,
        )
    rows = []
    for el in root:
        ctx = el.get("contextRef")
        if ctx is None or ctx not in contexts or el.text is None:
            continue
        txt = el.text.strip()
        try:
            val, text = float(txt), None
        except ValueError:
            if len(txt) > 40:  # text blocks
                continue
            val, text = float("nan"), txt  # short strings, e.g. ISO 8601 durations such as "P2Y"
        uri, local = el.tag[1:].split("}")
        start, end, dims = contexts[ctx]
        rows.append({"concept": f"{ns_prefix.get(uri, uri)}:{local}", "value": val, "text": text,
                     "unit": el.get("unitRef"), "start": start, "end": end, "dims": dims, "n_dims": len(dims)})
    return pd.DataFrame(rows)


def load_instance(
    cik: int | str, accession: str, cache_root: Path | None = None, fetch: Fetch = fetch_json,
    fetch_raw=fetch_bytes,
) -> pd.DataFrame:
    """Parsed instance for one filing; caches the raw XML under `cache_root/edgar/instances/`."""
    path = cache_root / "edgar" / "instances" / f"{accession}.xml" if cache_root else None
    if path is not None and path.exists():
        xml = path.read_bytes()
    else:
        xml = fetch_raw(instance_url(cik, accession, fetch))
        if path is not None:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(xml)
    df = parse_instance(xml)
    df.insert(0, "accession", accession)
    return df


def facts(df: pd.DataFrame, concept: str, **dims: str) -> pd.DataFrame:
    """Rows of `concept` whose dimensions equal `dims` exactly (no extra axes). Axis and member names may omit prefixes."""
    def match(d: dict) -> bool:
        if len(d) != len(dims):
            return False
        short = {k.split(":")[-1]: v.split(":")[-1] for k, v in d.items()}
        return all(short.get(a.split(":")[-1]) == m.split(":")[-1] for a, m in dims.items())

    sel = df[df["concept"].str.split(":").str[-1] == concept.split(":")[-1]]
    return sel[sel["dims"].map(match)]
