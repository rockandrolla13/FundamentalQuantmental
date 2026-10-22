from datetime import datetime

import numpy as np
import pandas as pd
import pytest

from hy.sources import compustat_pit as cp
from hy.sources import edgar, financials
from hy.state import cash_nonrecurring, ebitda_adj_analyst

G = "022260"
QDATES = pd.to_datetime(["2022-03-31", "2022-06-30", "2022-09-30", "2022-12-31"])


def _row(pointdate, datadate, qback, **vals):
    base = {c: np.nan for c in cp.VALUE_COLUMNS}
    base.update(vals)
    return {"gvkey": G, "pointdate": pd.Timestamp(pointdate), "datadate": pd.Timestamp(datadate), "qtrsback": qback, **base}


def _fq():
    return pd.DataFrame({"gvkey": G, "datadate": QDATES, "fqtr": [1, 2, 3, 4], "rdqe": QDATES + pd.Timedelta(25, unit="D")})


def test_decumulate_turns_ytd_into_quarters():
    snap = pd.DataFrame([_row("2023-01-31", d, 3 - i, capex=c) for i, (d, c) in enumerate(zip(QDATES, [861, 1941, 3072, 4395]))])
    out = cp.decumulate(snap, _fq()).set_index("datadate")["capex"]
    assert out.tolist() == pytest.approx([861, 1080, 1131, 1323])


def test_decumulate_gives_nan_when_prior_quarter_is_missing():
    snap = pd.DataFrame([_row("2023-01-31", QDATES[2], 1, capex=3072.0)])
    assert np.isnan(cp.decumulate(snap, _fq())["capex"].iloc[0])


def test_build_vintages_keeps_only_changes():
    snaps = [_row(p, QDATES[0], 0, revenue=v) for p, v in [("2022-04-30", 100.0), ("2022-05-31", 100.0), ("2022-06-30", 95.0)]]
    v = cp.build_vintages(pd.DataFrame(snaps))
    assert v["vintage"].tolist() == [0, 1]
    assert v["revenue"].tolist() == [100.0, 95.0]
    assert v["snapshot_available_at"].tolist() == [pd.Timestamp("2022-05-01"), pd.Timestamp("2022-07-01")]


class StubWrds:
    def __init__(self, hist, fq, current=None):
        self.hist, self.fq, self.sql = hist, fq, []
        self.current = current if current is not None else pd.DataFrame(columns=["gvkey", "datadate", *cp.VALUE_COLUMNS])

    def raw_sql(self, sql):
        self.sql.append(sql)
        if cp.HIST_TABLE in sql:
            return self.hist.copy()
        return (self.fq if "fqtr" in sql else self.current).copy()


def test_load_vintages_drops_extra_lookback_and_caches(tmp_path):
    rows = []
    for p in ["2023-01-31", "2023-02-28"]:
        for i, (d, c) in enumerate(zip(QDATES, [10, 25, 45, 70])):
            rows.append(_row(p, d, 3 - i, capex=float(c), revenue=100.0))
    con = StubWrds(pd.DataFrame(rows), _fq())
    v = cp.load_vintages(con, [G], "2023-01-01", "2023-03-31", cache_root=tmp_path, max_quarters_back=2)
    assert "qtrsback <= 5" in con.sql[0]  # 2 kept + 3 extra for de-cumulation
    assert sorted(v["datadate"]) == list(QDATES[1:])  # qtrsback 3 dropped
    assert v.set_index("datadate")["capex"].tolist() == pytest.approx([15, 20, 25])
    assert (v["vintage"] == 0).all()  # unchanged second snapshot adds no version
    assert v["pit_exact"].all()
    n = len(con.sql)
    cp.load_vintages(con, [G], "2023-01-01", "2023-03-31", cache_root=tmp_path, max_quarters_back=2)
    assert len(con.sql) == n  # served from cache


def test_missing_fourth_quarter_is_filled_flagged_and_kept_out_of_store():
    # History has Q1-Q3 only; the current view has all four quarters as YTD capex.
    hist = pd.DataFrame([_row("2023-01-31", d, 2 - i, capex=float(c), revenue=100.0)
                         for i, (d, c) in enumerate(zip(QDATES[:3], [10, 25, 45]))])
    cur = pd.DataFrame([{"gvkey": G, "datadate": d, **{c: np.nan for c in cp.VALUE_COLUMNS}, "capex": float(c), "revenue": 100.0}
                        for d, c in zip(QDATES, [10, 25, 45, 70])])
    v = cp.load_vintages(StubWrds(hist, _fq(), cur), [G], "2022-01-01", "2023-03-31")
    q4 = v[v["datadate"] == QDATES[3]].iloc[0]
    assert not q4["pit_exact"] and pd.isna(q4["snapshot_available_at"]) and q4["capex"] == pytest.approx(25.0)
    filings = pd.DataFrame({"cik": "0000860730", "form": ["10-K"], "report_date": [QDATES[3]],
                            "acceptance": pd.to_datetime(["2023-02-17 21:00"])})
    m = financials.match_filings(v, filings, {G: "860730"})
    assert m.set_index("datadate").loc[QDATES[3], "available_at"] == pd.Timestamp("2023-02-17 21:00")
    assert financials.timing_report(m)["not_pit_exact_share"] == pytest.approx(0.25)
    assert QDATES[3].to_pydatetime() not in {r.as_of for r in financials.build_store(m).as_known(datetime(2024, 1, 1))}
    assert QDATES[3].to_pydatetime() in {r.as_of for r in financials.build_store(m, include_inexact=True).as_known(datetime(2024, 1, 1))}


def test_gvkeys_are_validated_before_sql():
    with pytest.raises(ValueError):
        cp.pull_history(StubWrds(None, None), ["1; drop table x"], "2020-01-01", "2020-12-31")


def _fake_fetch(url):
    if url.endswith("CIK0000860730.json"):
        return {"filings": {"recent": {"accessionNumber": ["a1", "a2"], "form": ["10-Q", "10-Q/A"],
                                       "reportDate": ["2022-03-31", "2022-03-31"], "filingDate": ["2022-04-22", "2022-06-01"],
                                       "acceptanceDateTime": ["2022-04-22T20:31:00.000Z", "2022-06-01T15:00:00.000Z"]},
                            "files": [{"name": "CIK0000860730-submissions-001.json"}]}}
    return {"accessionNumber": ["a0"], "form": ["10-K"], "reportDate": ["2021-12-31"], "filingDate": ["2022-02-18"],
            "acceptanceDateTime": ["2022-02-18T21:00:00.000Z"]}


def test_filing_index_reads_all_pages_and_parses_utc(tmp_path):
    idx = edgar.filing_index(860730, fetch=_fake_fetch, cache_root=tmp_path)
    assert set(idx["accession"]) == {"a0", "a1", "a2"}
    assert idx.set_index("accession").loc["a1", "acceptance"] == pd.Timestamp("2022-04-22 20:31:00")
    assert len(edgar.periodic_filings(idx)) == 2  # amendment excluded
    again = edgar.filing_index(860730, fetch=lambda u: pytest.fail("cache miss"), cache_root=tmp_path)
    assert len(again) == 3


def _vintages():
    return pd.DataFrame({
        "gvkey": G, "datadate": [QDATES[0], QDATES[0], QDATES[1]], "vintage": [0, 1, 0],
        "snapshot_available_at": pd.to_datetime(["2022-05-01", "2023-03-01", "2022-08-01"]),
        **{c: [100.0, 90.0, 110.0] for c in cp.VALUE_COLUMNS},
    })


def test_match_filings_uses_earlier_edgar_and_snapshot_for_restatements():
    filings = pd.DataFrame({"cik": "0000860730", "form": ["10-Q", "10-Q/A", "10-Q"],
                            "report_date": pd.to_datetime(["2022-04-02", "2022-03-31", "2022-07-01"]),
                            "acceptance": pd.to_datetime(["2022-04-22 20:31", "2022-04-01 10:00", "2022-08-05 20:00"])})
    m = financials.match_filings(_vintages(), filings, {G: "860730"}).set_index(["datadate", "vintage"])
    first_q1 = m.loc[(QDATES[0], 0)]
    assert first_q1["available_at"] == pd.Timestamp("2022-04-22 20:31")  # 52-week report date matched; /A ignored
    assert first_q1["available_at_source"] == "edgar"
    assert m.loc[(QDATES[0], 1), "available_at"] == pd.Timestamp("2023-03-01")  # restatement: snapshot
    q2 = m.loc[(QDATES[1], 0)]
    assert q2["available_at"] == pd.Timestamp("2022-08-01") and q2["available_at_source"] == "snapshot"  # snapshot earlier
    rep = financials.timing_report(m.reset_index())
    assert rep["edgar_matched_share"] == 1.0 and rep["restated_quarter_share"] == 0.5


def test_records_rebuild_reported_ebitda_and_keep_nan():
    m = financials.match_filings(_vintages(), pd.DataFrame(columns=["cik", "form", "report_date", "acceptance"]).astype(
        {"form": str, "report_date": "datetime64[ns]", "acceptance": "datetime64[ns]"}), {G: "860730"})
    m["special_items"] = -20.0
    m["interest_paid"] = np.nan
    m["interest_expense"] = 12.0
    m["capex"] = np.nan
    rec = financials.to_records(m)[0]
    assert rec.ebitda_reported == pytest.approx(80.0)  # oibdp 100 + special items -20
    assert ebitda_adj_analyst(rec.ebitda_reported, rec.nonrecurring_items) == pytest.approx(100.0)
    assert cash_nonrecurring(rec.nonrecurring_items) == 0.0  # default: special items treated as non-cash
    assert rec.cash_interest == 12.0 and np.isnan(rec.capex_total)


def test_store_view_returns_newest_quarter_despite_late_restatement():
    m = financials.match_filings(_vintages(), pd.DataFrame(columns=["cik", "form", "report_date", "acceptance"]).astype(
        {"form": str, "report_date": "datetime64[ns]", "acceptance": "datetime64[ns]"}), {G: "860730"})
    store = financials.build_store(m)
    latest = store.view(datetime(2023, 6, 30))[G]
    assert latest.as_of == QDATES[1].to_pydatetime()
    known = store.as_known(datetime(2023, 6, 30))
    assert [r.revenue for r in known] == [90.0, 110.0]  # Q1 in its restated version
    assert [r.revenue for r in store.as_known(datetime(2022, 12, 31))] == [100.0, 110.0]
