"""scripts/download_sec.py writes the SEC files that the analyst's loaders then read with the network refused."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import download_sec as ds  # noqa: E402

from hy.sources import clock_inputs as ci  # noqa: E402
from hy.sources import edgar, xbrl  # noqa: E402
from hy.sources import xbrl_instance as xi  # noqa: E402

CIK = "9000001"
FILINGS = [("0009000001-26-000010", "10-Q", "2026-06-30", "2026-08-05T16:01:02.000Z"),
           ("0009000001-26-000002", "10-K", "2025-12-31", "2026-02-20T16:00:00.000Z"),
           ("0009000001-26-000005", "8-K", "", "2026-04-01T12:00:00.000Z"),
           ("0009000001-14-000003", "10-Q", "2014-03-31", "2014-05-05T16:00:00.000Z")]  # before --start
XML = (b'<xbrl xmlns="http://www.xbrl.org/2003/instance" xmlns:us-gaap="http://fasb.org/us-gaap/2024">'
       b'<context id="c1"><entity><identifier scheme="x">1</identifier></entity>'
       b'<period><instant>2026-06-30</instant></period></context>'
       b'<us-gaap:CashAndCashEquivalentsAtCarryingValue contextRef="c1" unitRef="usd">1000000</us-gaap:'
       b'CashAndCashEquivalentsAtCarryingValue></xbrl>')
HTML = b"<html><body><p>Item 1. Business. AAA Health runs hospitals.</p></body></html>"


class FakeSEC:
    """Serves the four SEC endpoints; counts every request."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    def json(self, url: str) -> dict:
        self.calls.append(url)
        if url == ci.TICKERS_URL:
            return {"0": {"ticker": "AAA", "cik_str": int(CIK), "title": "AAA Health"}}
        if url.startswith(edgar.BASE):
            cols = list(zip(*FILINGS))
            return {"name": "AAA Health", "filings": {"files": [], "recent": {
                "accessionNumber": list(cols[0]), "form": list(cols[1]), "reportDate": list(cols[2]),
                "filingDate": [a[:10] for a in cols[3]], "acceptanceDateTime": list(cols[3])}}}
        if url.startswith(xbrl.BASE):
            return {"facts": {"us-gaap": {"NetCashProvidedByUsedInOperatingActivities": {"units": {"USD": [
                {"start": "2026-04-01", "end": "2026-06-30", "val": 5e8, "accn": FILINGS[0][0], "form": "10-Q",
                 "filed": "2026-08-05"}]}}}}}
        if url.endswith("index.json"):
            stem = url.rstrip("/").split("/")[-2]
            return {"directory": {"item": [{"name": f"a{stem}.htm", "size": "900"}, {"name": f"a{stem}_htm.xml"},
                                           {"name": "a_cal.xml"}, {"name": "ex21.htm", "size": "5000"}]}}
        raise AssertionError(f"unexpected url {url}")

    def raw(self, url: str) -> bytes:
        self.calls.append(url)
        return XML if url.endswith("_htm.xml") else HTML


def refuse(url):
    raise OSError(f"network refused: {url}")


def test_download_writes_what_the_loaders_read_offline(tmp_path):
    sec = FakeSEC()
    issuers = ds.ciks_for(["aaa"], fetch=sec.json)
    assert issuers == [("AAA", CIK)]
    log = ds.download(issuers, tmp_path, pd.Timestamp("2018-01-01"), fetch=sec.json, fetch_raw=sec.raw,
                      echo=lambda _m: None)
    # Two periodic filings after --start, each with an instance and a text; the 8-K and the 2014 10-Q stay out.
    assert sorted(log.loc[log["kind"] == "instance", "accession"]) == sorted([FILINGS[0][0], FILINGS[1][0]])
    assert (log["status"].str.startswith("ok")).all(), log.to_string()
    assert (tmp_path / "edgar" / "download_log.csv").exists()

    # The loaders read every file back with the network refused.
    idx = edgar.filing_index(CIK, fetch=refuse, cache_root=tmp_path)
    assert set(idx["accession"]) == {f[0] for f in FILINGS}
    assert len(xbrl.company_facts(CIK, fetch=refuse, cache_root=tmp_path)) == 1
    inst = xi.load_instance(CIK, FILINGS[0][0], cache_root=tmp_path, fetch=refuse, fetch_raw=refuse)
    assert inst["value"].iloc[0] == 1e6
    assert "AAA Health runs hospitals" in ci.filing_text(CIK, FILINGS[0][0], tmp_path, fetch=refuse, fetch_raw=refuse)
    assert ci.latest_filings(CIK, "2026-09-18", tmp_path, fetch=refuse)["latest"]["accession"] == FILINGS[0][0]


def test_a_rerun_refreshes_the_index_and_skips_cached_filings(tmp_path):
    sec = FakeSEC()
    ds.download([("AAA", CIK)], tmp_path, pd.Timestamp("2018-01-01"), fetch=sec.json, fetch_raw=sec.raw,
                echo=lambda _m: None)
    sec.calls.clear()
    log = ds.download([("AAA", CIK)], tmp_path, pd.Timestamp("2018-01-01"), fetch=sec.json, fetch_raw=sec.raw,
                      echo=lambda _m: None)
    assert set(log.loc[log["kind"].isin(["instance", "text"]), "status"]) == {"cached"}
    assert all(u.startswith((edgar.BASE, xbrl.BASE)) for u in sec.calls)  # only the two index files again
    assert len(pd.read_csv(tmp_path / "edgar" / "download_log.csv")) == 2 * len(log)


def test_one_bad_filing_does_not_stop_the_issuer(tmp_path):
    sec = FakeSEC()

    def raw(url):
        if FILINGS[1][0].replace("-", "") in url and url.endswith(".xml"):
            raise OSError("HTTP Error 404")
        return sec.raw(url)
    log = ds.download([("AAA", CIK)], tmp_path, pd.Timestamp("2018-01-01"), fetch=sec.json, fetch_raw=raw,
                      echo=lambda _m: None)
    bad = log[log["status"].str.startswith("failed")]
    assert list(zip(bad["kind"], bad["accession"])) == [("instance", FILINGS[1][0])]
    assert (tmp_path / "edgar" / "text" / f"{FILINGS[1][0]}.txt").exists()


def test_issuers_from_tables_and_an_unknown_ticker(tmp_path):
    (tmp_path / "issuers.csv").write_text("ticker,issuer_id,cik\nAAA,1,9000001\nBBB,2,\n")
    assert ds.ciks_from_tables(tmp_path) == [("AAA", "9000001")]
    with pytest.raises(LookupError, match="ZZZ"):
        ds.ciks_for(["ZZZ"], fetch=FakeSEC().json)
    assert json.loads(json.dumps(ds.LOG_COLUMNS))  # the log columns are plain names
