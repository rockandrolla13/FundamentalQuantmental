"""Offline tests for the Section 4.7 input derivation (hy/sources/clock_inputs.py)."""

from dataclasses import dataclass
from datetime import datetime

import pandas as pd
import pytest

from hy.sources import clock_inputs as ci

CRWV_LEASE = ("As of June 30, 2026, the Company executed additional lease agreements, primarily for data centers, "
              "equipment, and office buildings, that had not yet commenced. The aggregate amount of estimated future "
              "undiscounted lease payments associated with such leases is $35.5 billion. These leases will commence "
              "between 2026 and 2029 with estimated lease terms of seven to sixteen years. Not included in the "
              "preceding amount are the following lease arrangements.")
ORCL_LEASE = ("As of August 31, 2026, we had $288 billion of additional lease commitments, substantially all related "
              "to data center arrangements, that are generally expected to commence between the second quarter of "
              "fiscal 2027 and fiscal 2029 and for terms of fifteen to nineteen years that were not reflected on our "
              "condensed consolidated balance sheets as of August 31, 2026 or in the maturities table above.")
ORCL_RPO = ("Remaining performance obligations were $ 664 billion as of August 31, 2026 , of which we expect to "
            "recognize approximately 13 % as revenues over the next twelve months , 37 % over the subsequent month 13 "
            "to month 36 , 34 % over the subsequent month 37 to month 60 and the remainder thereafter. We have elected "
            "the optional exemption.")
CRWV_RPO = ("As of June 30, 2026, the Company had $103.7 billion of unsatisfied RPO, of which 41% was expected to be "
            "recognized over the initial 24 months ending June 30, 2028, 39% between months 25 and 48, and the "
            "remaining balance recognized between months 49 and 78.")
IREN_RPO = ("Remaining Performance Obligations (“RPO”) As of June 30, 2026, the Group had $5.1 billion of "
            "unsatisfied RPO, of which $0.9 billion is expected to be recognized over the initial 12 months ending "
            "June 30, 2027, $1.3 billion between months 13 and 24, and the remaining balance recognized between "
            "months 25 and 60.")


# --- commencement window and term -----------------------------------------------------------------------------


def test_crwv_commencement_calendar_years():
    out = ci.parse_commencement(CRWV_LEASE, pd.Timestamp("2026-06-30"), "--12-31")
    assert out["window"][0] == 0.0  # start of 2026 is before the as-of date: floored at 0
    assert out["window"][1] == pytest.approx(3.5, abs=0.01)  # end of 2029
    assert out["term"] == (7.0, 16.0)


def test_orcl_commencement_fiscal_quarter_and_fiscal_year():
    out = ci.parse_commencement(ORCL_LEASE, pd.Timestamp("2026-08-31"), "--05-31")
    assert out["window"][0] == pytest.approx(0.0, abs=0.01)  # Q2 FY27 starts 1 Sep 2026
    assert out["window"][1] == pytest.approx(2.75, abs=0.01)  # FY29 ends 31 May 2029
    assert out["term"] == (15.0, 19.0)


def test_commencement_digits_and_single_fiscal_year():
    s = "The leases will commence between 2027 and 2028 with lease terms of 10 to 20 years."
    out = ci.parse_commencement(s, pd.Timestamp("2026-06-30"))
    assert out["window"] == pytest.approx((0.504, 2.507), abs=0.01)
    assert out["term"] == (10.0, 20.0)
    s = "These leases are expected to commence in fiscal 2027 and have a term of twenty-one years."
    out = ci.parse_commencement(s, pd.Timestamp("2026-08-31"), (5, 31))
    assert out["window"] == pytest.approx((0.0, 0.75), abs=0.01)
    assert out["term"] == (21.0, 21.0)


def test_commencement_missing_or_not_a_lease():
    assert ci.parse_commencement("No such disclosure here.", pd.Timestamp("2026-06-30")) is None
    plant = "Initial operations at the site are anticipated to commence during calendar year 2027."
    assert ci.parse_commencement(plant, pd.Timestamp("2026-06-30")) is None


def test_number_words():
    assert ci.number("sixteen") == 16 and ci.number("twenty-one") == 21 and ci.number("thirty") == 30
    assert ci.number("7") == 7 and ci.number("12.5") == 12.5


# --- RPO timetable --------------------------------------------------------------------------------------------


def test_orcl_rpo_percentages_and_open_remainder():
    out = ci.parse_rpo(ORCL_RPO)
    assert out["windows"] == [(0.0, 1.0, 0.13), (1.0, 2.0, 0.37), (3.0, 2.0, 0.34)]
    assert out["tail"] is None  # "the remainder thereafter" states no timing
    assert out["total"] == 664_000


def test_crwv_rpo_with_stated_tail():
    out = ci.parse_rpo(CRWV_RPO)
    assert out["windows"] == [(0.0, 2.0, 0.41), (2.0, 2.0, 0.39)]
    assert out["tail"] == (4.0, 2.5)  # months 49 to 78
    assert out["total"] == pytest.approx(103_700)


def test_iren_rpo_in_dollars():
    out = ci.parse_rpo(IREN_RPO)
    assert out["total"] == pytest.approx(5_100)
    assert [w[:2] for w in out["windows"]] == [(0.0, 1.0), (1.0, 1.0)]
    assert [w[2] for w in out["windows"]] == pytest.approx([0.9 / 5.1, 1.3 / 5.1], abs=1e-3)
    assert out["tail"] == (2.0, 3.0)


def test_rpo_missing():
    assert ci.parse_rpo("Revenue grew 12% in the quarter.") is None


def test_rpo_crosscheck_reads_cumulative_lengths():
    xbrl = [(0.003, 2.0, 0.41), (2.004, 4.0, 0.39)]  # CoreWeave tags months 25-48 as P48M
    assert ci.rpo_crosscheck(xbrl, ci.parse_rpo(CRWV_RPO)["windows"]) == "lengths differ"
    assert ci.rpo_crosscheck([(0.003, 1.0, 0.13), (1.002, 2.0, 0.37), (3.003, 2.0, 0.34)],
                             ci.parse_rpo(ORCL_RPO)["windows"]) == "agree"
    assert ci.rpo_crosscheck(xbrl, []) == "missing"


# --- lease term, text, documents ------------------------------------------------------------------------------


def test_lease_term_table_and_prose():
    table = ("Weighted-average remaining lease term (in years): Operating leases 12 11 Finance leases 5 5 "
             "Weighted-average discount rate:")
    assert ci.parse_lease_term(table) == 12.0
    prose = "The weighted-average remaining lease term was eight years as of May 31, 2026."
    assert ci.parse_lease_term(prose) == 8.0
    assert ci.parse_lease_term("No lease data.") is None
    assert ci.iso_years("P12Y") == 12 and ci.iso_years("P3Y2M12D") == pytest.approx(3.2, abs=0.01)
    assert ci.iso_years(None) is None


def test_strip_html_keeps_split_words_and_separates_cells():
    raw = "<div>commence between the second quarter of fiscal 2027 a<span>nd</span> fiscal 2029</div><td>12</td><td>11</td>"
    text = ci.strip_html(raw)
    assert "2027 and fiscal 2029" in text and "12 11" in text


def test_primary_document_pairs_with_instance():
    items = [{"name": "orcl-20260831.htm", "size": "2708953"}, {"name": "orcl-20260831_htm.xml", "size": "1"},
             {"name": "orcl-ex31_01.htm", "size": "9999999"}]
    assert ci.primary_document(items) == "orcl-20260831.htm"
    items = [{"name": "d123d10q.htm", "size": "500"}, {"name": "d123dex311.htm", "size": "900"}]
    assert ci.primary_document(items) == "d123d10q.htm"


# --- overrides ------------------------------------------------------------------------------------------------


def test_override_precedence_fallback_and_secondary(tmp_path):
    (tmp_path / "XYZ.yaml").write_text(
        "debt_tail_years:\n  value: 2.0\n  source: wall in 2031\n"
        "interest_rate:\n  value: 0.045\n  source: hand entry\n  fallback: true\n"
        "rating:\n  value: BBB-\n  source: press\n  secondary: true\n"
        "scenario_extra_lease:\n  value: {amount: 100, window: [0, 2], term: 16}\n  source: text\n")
    ov = ci.load_overrides("xyz", tmp_path)
    assert ov["scenario_extra_lease"]["value"]["window"] == (0, 2)
    derived = {"debt_tail_years": (4.6, "default assumption: run-rate"), "interest_rate": (0.034, "loader ..."),
               "rating": (None, "analyst only")}
    out = ci.apply_overrides(derived, ov, ci._rate_ok)
    assert out["debt_tail_years"][0] == 2.0 and out["debt_tail_years"][1].startswith("analyst override: wall in 2031")
    assert "derived was 4.6" in out["debt_tail_years"][1]
    assert out["interest_rate"][0] == 0.034  # derived value is valid: the fallback stays unused
    assert out["rating"] == ("BBB-", "analyst override (secondary source): press")
    clipped = ci.apply_overrides({"interest_rate": (0.20, "loader, clipped")}, ov, ci._rate_ok)
    assert clipped["interest_rate"][0] == 0.045  # clipped derived value: the fallback applies
    assert ci.load_overrides("NONE", tmp_path) == {}


# --- loader quantities ----------------------------------------------------------------------------------------


@dataclass
class Q:
    as_of: datetime
    cash_interest: float
    debt_current: float
    debt_long_term: float
    revenue: float = 100.0
    ebitda_adj_company: float = 30.0
    available_at: datetime = datetime(2026, 1, 1)
    source: str = "test"


def _quarters(interest, debt):
    ends = pd.to_datetime(["2025-09-30", "2025-12-31", "2026-03-31", "2026-06-30"])
    return [Q(e.to_pydatetime(), i, 0.0, d) for e, i, d in zip(ends, interest, debt)]


def test_interest_rate_ltm_over_average_debt():
    rate, src = ci.interest_rate(_quarters([20, 20, 30, 30], [1000, 1000, 1000, 1000]))
    assert rate == pytest.approx(0.10)
    assert src.startswith("loader LTM cash interest 100")


def test_interest_rate_clips_and_reports_missing():
    lo, src = ci.interest_rate(_quarters([1, 1, 1, 1], [1000] * 4))
    assert lo == 0.02 and "clipped from 0.004" in src
    hi, _ = ci.interest_rate(_quarters([100] * 4, [1000] * 4))
    assert hi == 0.20
    none, src = ci.interest_rate(_quarters([20, float("nan"), 20, 20], [1000] * 4))
    assert none is None and "missing" in src
    assert ci.interest_rate(_quarters([20] * 4, [1000] * 4)[:3])[0] is None  # fewer than four quarters


def test_ltm_sums_and_flags_missing_quarter():
    q = _quarters([20] * 4, [1000] * 4)
    out = ci.ltm(q)
    assert out["ltm_revenue"][0] == 400 and out["ltm_ebitda"][0] == 120 and out["run_rate_revenue"][0] == 400
    q[-1].ebitda_adj_company = float("nan")
    val, src = ci.ltm(q)["ltm_ebitda"]
    assert val == pytest.approx(90 * 4 / 3) and "3 of 4 quarters" in src  # one gap: annualise, and say so
    q[-2].ebitda_adj_company = float("nan")
    assert ci.ltm(q)["ltm_ebitda"][0] is None  # two gaps: no LTM


# --- filings and tags -----------------------------------------------------------------------------------------


def _index():
    return pd.DataFrame({
        "cik": "0000000001",
        "accession": ["a-10k", "a-10q1", "a-10q1-amend", "a-10q2", "a-8k"],
        "form": ["10-K", "10-Q", "10-Q/A", "10-Q", "8-K"],
        "report_date": pd.to_datetime(["2025-12-31", "2026-03-31", "2026-03-31", "2026-06-30", "2026-09-01"]),
        "filing_date": pd.to_datetime(["2026-02-20", "2026-05-08", "2026-06-01", "2026-08-12", "2026-09-02"]),
        "acceptance": pd.to_datetime(["2026-02-20 21:00", "2026-05-08 20:00", "2026-06-01 20:00",
                                      "2026-08-12 03:24", "2026-09-02 12:00"]),
    })


def test_latest_filings_respects_as_of():
    now = ci.latest_filings(1, "2026-10-01", index=_index())
    assert now["latest"]["accession"] == "a-10q2" and now["annual"]["accession"] == "a-10k"
    before = ci.latest_filings(1, "2026-08-12 03:00", index=_index())  # 24 minutes before the Q2 acceptance
    assert before["latest"]["accession"] == "a-10q1"  # the amendment is not a new period
    with pytest.raises(LookupError):
        ci.latest_filings(1, "2026-01-01", index=_index())


def test_annual_lease_cost_with_filer_prefix():
    as_of = pd.Timestamp("2026-08-31")
    rows = [
        ("us-gaap:OperatingLeaseCost", 1101e6, pd.Timestamp("2026-06-01")),
        ("orcl:FinanceLeaseCost", 275e6, pd.Timestamp("2026-06-01")),
        ("us-gaap:VariableLeaseCost", 999e6, pd.Timestamp("2026-06-01")),
        ("us-gaap:Assets", 1e9, pd.NaT),
    ]
    df = pd.DataFrame([{"concept": c, "value": v, "text": None, "unit": "usd", "start": st, "end": as_of,
                        "dims": {}, "n_dims": 0} for c, v, st in rows])
    value, src = ci.annual_lease_cost(df)
    assert value == pytest.approx((1101 + 275) * 4)
    assert "orcl:FinanceLeaseCost" in src and "Variable" not in src
