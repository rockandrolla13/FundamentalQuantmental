"""Inputs for the cost clock against the revenue clock, derived for any ticker (methodology Section 4.7).

Every input is a pair (value, source). The source string starts with one of:
- "tag ...": an XBRL fact in the filing instance;
- "text ...": a sentence in the filing's primary document;
- "loader ...": the point-in-time financials store (Compustat PIT and SEC XBRL, Section 3.2);
- "default assumption ...": our convention where the filing is silent;
- "analyst override ...": a value from `data/analyst_inputs/<TICKER>.yaml`.

The analyst supplies judgement fields (recourse structure, rating, scenario leases); the system computes the rest.
No input reads a filing accepted after the decision time `as_of`.
"""

from __future__ import annotations

import html
import json
import math
import re
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from hy import clocks
from hy.sources import edgar
from hy.sources import schedules as sc
from hy.sources import xbrl_instance as xi

Pair = tuple[Any, str]
TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
RATE_BOUNDS = (0.02, 0.20)
DEFAULT_UNCOMMENCED_WINDOW = (0.0, 3.0)
DEFAULT_UNCOMMENCED_TERM = 15.0
DEFAULT_RPO_TAIL = 2.0
DEFAULT_DEBT_TAIL = 5.0
MAX_DEBT_TAIL = 10.0
DEFAULT_PURCHASE_YEARS = 2.0

# ---------------------------------------------------------------------------------------------------------------
# Filings
# ---------------------------------------------------------------------------------------------------------------


def _decision_time(as_of: object | None) -> pd.Timestamp:
    """Decision time as naive UTC; `None` means now."""
    if as_of is None:
        return pd.Timestamp.now(tz="UTC").tz_localize(None)
    t = pd.Timestamp(as_of)
    return t.tz_convert("UTC").tz_localize(None) if t.tzinfo else t


def latest_filings(
    cik: int | str, as_of: object | None = None, cache_root: Path | None = None, index: pd.DataFrame | None = None,
    refresh: bool = False,
) -> dict[str, dict | None]:
    """Latest original 10-Q or 10-K, and the latest 10-K, accepted on or before `as_of` (no look-ahead).

    Returns {"latest": row, "annual": row}; each row holds accession, form, report_date, acceptance (naive UTC).
    `index` lets a caller pass a filing index (tests); otherwise the EDGAR index is read (cached).
    """
    t = _decision_time(as_of)
    idx = index if index is not None else edgar.filing_index(cik, cache_root=cache_root, refresh=refresh)
    per = edgar.periodic_filings(idx)
    per = per[per["acceptance"].notna() & (per["acceptance"] <= t)].sort_values("acceptance")
    if per.empty:
        raise LookupError(f"no 10-Q or 10-K for CIK {cik} accepted on or before {t}")

    def row(r: pd.Series) -> dict:
        return {"accession": r["accession"], "form": r["form"], "report_date": r["report_date"],
                "acceptance": r["acceptance"]}

    annual = per[per["form"].isin(("10-K", "10-KT"))]
    return {"latest": row(per.iloc[-1]), "annual": row(annual.iloc[-1]) if len(annual) else None}


_BLOCK = re.compile(r"(?i)<br\s*/?>|</?(?:p|div|tr|li|h\d|table|section)\b[^>]*>")
_CELL = re.compile(r"(?i)</?(?:td|th)\b[^>]*>")


def strip_html(raw: str) -> str:
    """Plain text of an HTML or inline XBRL document.

    Block tags become line breaks and table cells become spaces. Inline tags (span, ix:nonFraction) vanish without
    a space, so a word split across two spans stays one word.
    """
    s = re.sub(r"(?is)<(script|style|ix:header|head)\b[^>]*>.*?</\1>", " ", raw)
    s = _BLOCK.sub("\n", s)
    s = _CELL.sub(" ", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s).replace("\xa0", " ").replace(" ", " ")
    s = re.sub(r"[ \t\r\f\v]+", " ", s)
    return re.sub(r"\s*\n\s*", "\n", s).strip()


def primary_document(items: Sequence[dict]) -> str:
    """Name of the filing's main document from the archive `index.json` items.

    Prefer the inline XBRL document that pairs with the instance (`x_htm.xml` -> `x.htm`); else the largest `.htm`
    that is not an exhibit, an index page, or a rendered `R` page.
    """
    names = [i["name"] for i in items]
    for n in names:
        if n.endswith("_htm.xml") and n[: -len("_htm.xml")] + ".htm" in names:
            return n[: -len("_htm.xml")] + ".htm"
    cand = [i for i in items if i["name"].lower().endswith((".htm", ".html"))
            and not re.search(r"(?i)index|^r\d+\.htm|ex-?\d|exhibit|dex\d", i["name"])]
    if not cand:
        raise FileNotFoundError("no primary document in the filing index")
    return max(cand, key=lambda i: int(i.get("size") or 0))["name"]


def filing_text(
    cik: int | str, accession: str, cache_root: Path | None = None, fetch: edgar.Fetch = edgar.fetch_json,
    fetch_raw: Callable[[str], bytes] = xi.fetch_bytes,
) -> str:
    """Plain text of the filing's primary document; caches it under `cache_root/edgar/text/<accession>.txt`."""
    path = cache_root / "edgar" / "text" / f"{accession}.txt" if cache_root else None
    if path is not None and path.exists():
        return path.read_text()
    folder = f"{xi.ARCHIVE}{int(edgar._cik10(cik))}/{accession.replace('-', '')}/"
    name = primary_document(fetch(folder + "index.json")["directory"]["item"])
    text = strip_html(fetch_raw(folder + name).decode("utf-8", errors="replace"))
    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    return text


# ---------------------------------------------------------------------------------------------------------------
# Text parsers
# ---------------------------------------------------------------------------------------------------------------

_UNITS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve",
          "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
NUMBER_WORDS: dict[str, int] = {w: i for i, w in enumerate(_UNITS)}
NUMBER_WORDS.update({"twenty": 20, "thirty": 30})
NUMBER_WORDS.update({f"twenty{sep}{_UNITS[i]}": 20 + i for i in range(1, 10) for sep in ("-", " ")})
_NUM = r"(?:\d+(?:\.\d+)?|" + "|".join(sorted((re.escape(w) for w in NUMBER_WORDS), key=len, reverse=True)) + r")"
_ORD = {"first": 1, "second": 2, "third": 3, "fourth": 4}


def number(token: str) -> float:
    """'sixteen' -> 16, 'twenty-one' -> 21, '7' -> 7. Raises KeyError on an unknown word."""
    t = token.strip().lower()
    return float(t) if re.fullmatch(r"\d+(?:\.\d+)?", t) else float(NUMBER_WORDS[t])


def sentences(text: str) -> list[str]:
    """Split on a full stop followed by a space and a capital, or on a line break. Decimals stay intact."""
    return [s.strip() for s in re.split(r"(?<=[.;])\s+(?=[A-Z(])|\n", text) if s.strip()]


def fiscal_year_end(month_day: str | None) -> tuple[int, int]:
    """(month, day) from dei:CurrentFiscalYearEndDate ('--05-31'); December 31 when missing."""
    m = re.fullmatch(r"-*(\d{2})-(\d{2})", month_day or "")
    return (int(m.group(1)), int(m.group(2))) if m else (12, 31)


def _period(ordinal: str | None, fiscal: bool, year: int, fy_end: tuple[int, int]) -> tuple[pd.Timestamp, pd.Timestamp]:
    """[start, end) of a calendar or fiscal year, or of one quarter of it. Fiscal year Y ends in calendar year Y."""
    if fiscal:
        mm, dd = fy_end
        # The day after the fiscal year end; a day of 28 or later means the month end (52-53 week years drift).
        first = pd.Timestamp(year=year, month=mm, day=1)
        end = first + pd.DateOffset(months=1) if dd >= 28 else pd.Timestamp(year=year, month=mm, day=dd) + pd.DateOffset(days=1)
        start = end - pd.DateOffset(years=1)
    else:
        start, end = pd.Timestamp(year, 1, 1), pd.Timestamp(year + 1, 1, 1)
    if ordinal:
        q = _ORD[ordinal.lower()]
        start, end = start + pd.DateOffset(months=3 * (q - 1)), start + pd.DateOffset(months=3 * q)
    return start, end


def _years(a: pd.Timestamp, b: pd.Timestamp) -> float:
    return max(0.0, (b - a).days / 365.25)


_BOUND = (r"(?:(?:the\s+)?(first|second|third|fourth)\s+(?:fiscal\s+)?quarter\s+of\s+)?"
          r"(?:(?:calendar\s+)?(fiscal)\s+(?:year\s+)?|calendar\s+(?:year\s+)?)?((?:19|20)\d{2})")
_WINDOW = re.compile(r"(?i)commence\w*[^.]{0,80}?between\s+" + _BOUND + r"\s+and\s+" + _BOUND)
_SINGLE = re.compile(r"(?i)commence\w*[^.]{0,40}?\b(?:in|during)\s+" + _BOUND)
_TERM = re.compile(r"(?i)terms?\s+(?:of\s+)?(?:up\s+to\s+)?(?:approximately\s+)?(" + _NUM + r")"
                   r"(?:\s*(?:to|-|–|and|through)\s*(" + _NUM + r"))?\s+years?")


def parse_commencement(
    text: str, as_of: pd.Timestamp, fy_end: str | tuple[int, int] | None = None,
) -> dict | None:
    """Commencement window and term of signed leases not yet commenced, from filing prose.

    Returns {"window": (start, end) years from `as_of`, "term": (min, max) years or None, "sentence": str},
    or None when no sentence matches. A year maps to its start for the start bound and to its end for the end
    bound; fiscal years use `fy_end`; offsets are floored at 0. Intuition: the rent clock starts when the
    landlord delivers, and the filing states the delivery years in words, not tags.
    """
    fye = fy_end if isinstance(fy_end, tuple) else fiscal_year_end(fy_end)
    as_of = pd.Timestamp(as_of)
    for s in sentences(text):
        low = s.lower()
        if "commenc" not in low or "lease" not in low:  # a plant that "will commence operations" is not a lease
            continue
        m = _WINDOW.search(s)
        if m:
            o1, f1, y1, o2, f2, y2 = m.groups()
            fiscal = bool(f1 or f2)  # "between fiscal 2027 and 2029": one qualifier covers both bounds
            start, _ = _period(o1, fiscal, int(y1), fye)
            _, end = _period(o2, fiscal, int(y2), fye)
        else:
            m = _SINGLE.search(s)
            if not m:
                continue
            o1, f1, y1 = m.groups()
            start, end = _period(o1, bool(f1), int(y1), fye)
        t = _TERM.search(s[m.start():]) or _TERM.search(s)
        term = None
        if t:
            lo = number(t.group(1))
            term = (lo, number(t.group(2)) if t.group(2) else lo)
        return {"window": (round(_years(as_of, start), 3), round(_years(as_of, end), 3)), "term": term, "sentence": s}
    return None


_PCT = re.compile(r"(\d+(?:\.\d+)?)\s*%")
_SPAN = re.compile(r"(?i)months?\s+(\d+)\s*(?:to|and|-|–|through)\s*(?:months?\s+)?(\d+)")
_NEXT = re.compile(r"(?i)(next|initial|first|following|subsequent)\s+(" + _NUM + r")\s+(months|years)")


def _chunk_window(chunk: str, prev_end: float) -> tuple[float, float] | None:
    """(start, length) in years of the period named in one clause of an RPO sentence."""
    m = _SPAN.search(chunk)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        return (a - 1) / 12, (b - a + 1) / 12
    m = _NEXT.search(chunk)
    if m:
        n = number(m.group(2)) / (12 if m.group(3).lower() == "months" else 1)
        start = prev_end if m.group(1).lower() in ("following", "subsequent") else 0.0
        return start, n
    if re.search(r"(?i)twelve months|12 months|one year", chunk):
        return prev_end, 1.0
    return None


_USD = r"\$\s*([\d,]+(?:\.\d+)?)\s*(billion|million)"
_REST = re.compile(r"(?i)\bremain(?:der|ing)\b(?!\s+performance)")


def _usd(num: str, unit: str) -> float:
    return float(num.replace(",", "")) * (1e3 if unit.lower() == "billion" else 1.0)


def parse_rpo(text: str) -> dict | None:
    """RPO timing from filing prose: {"windows": [(start, length, share)], "tail": (start, length) or None,
    "total": USD m or NaN, "sentence": str}; None when no sentence states a timetable.

    Windows come as percentages (Oracle: '13% ... over the next twelve months') or as dollar amounts over the
    stated total (IREN: '$0.9 billion ... over the initial 12 months'). The tail is the stated window of 'the
    remaining balance' (CoreWeave: months 49 to 78); 'the remainder thereafter' gives None.
    Intuition: when XBRL lacks the timing tags, the same timetable is in one sentence.
    """
    for s in sentences(text):
        low = s.lower()
        if not (("remaining performance obligation" in low or re.search(r"\brpo\b", low))
                and re.search(r"recogni[sz]", low) and ("%" in s or "$" in s)):
            continue
        tot = (re.search(r"(?i)" + _USD + r"\s+of\s+(?:unsatisfied\s+)?(?:remaining performance\s+obligations?|RPO)", s)
               or re.search(r"(?i)(?:remaining performance obligations?|RPO)\)?\s+(?:were|was|totall?ed|of)\s+"
                            r"(?:approximately\s+)?" + _USD, s))
        total = _usd(tot.group(1), tot.group(2)) if tot else float("nan")
        rest = list(_REST.finditer(s))
        cut = rest[-1].start() if rest else len(s)
        tokens = [(m.start(), m.end(), float(m.group(1)) / 100) for m in _PCT.finditer(s[:cut])]
        if not tokens and total == total and total > 0:
            tokens = [(m.start(), m.end(), _usd(m.group(1), m.group(2)) / total)
                      for m in re.finditer(_USD, s[:cut])
                      if not (tot and m.start() < tot.end() and m.end() > tot.start())]  # skip the total itself
        windows, prev_end = [], 0.0
        for i, (_, end, share) in enumerate(tokens):
            stop = tokens[i + 1][0] if i + 1 < len(tokens) else cut
            w = _chunk_window(s[end:stop], prev_end)
            if w is None:
                continue
            windows.append((round(w[0], 3), round(w[1], 3), round(share, 4)))
            prev_end = w[0] + w[1]
        if not windows or sum(w[2] for w in windows) > 1.01:
            continue
        tail = None
        if rest:
            m = _SPAN.search(s[cut:])
            if m:
                a, b = int(m.group(1)), int(m.group(2))
                tail = ((a - 1) / 12, (b - a + 1) / 12)
        return {"windows": windows, "tail": tail, "total": total, "sentence": s}
    return None


_WAVG = re.compile(r"(?i)weighted[- ]average remaining (?:operating )?lease terms?")


def parse_lease_term(text: str) -> float | None:
    """Weighted-average remaining operating lease term (years) from prose or a flattened table; None if absent."""
    for m in _WAVG.finditer(text):
        after = text[m.end(): m.end() + 160]
        t = re.search(r"(?i)operating leases?\D{0,12}?(\d+(?:\.\d+)?)", after)
        if t:
            return float(t.group(1))
        t = re.search(r"(?i)^[^.]{0,80}?\b(?:was|of|is)\s+(?:approximately\s+)?(" + _NUM + r")\s+years", after)
        if t:
            return number(t.group(1))
    return None


# ---------------------------------------------------------------------------------------------------------------
# Instance helpers
# ---------------------------------------------------------------------------------------------------------------


def _local(df: pd.DataFrame) -> pd.Series:
    return df["concept"].str.split(":").str[-1]


def annual_lease_cost(df: pd.DataFrame) -> Pair:
    """Operating plus finance lease cost of the latest period ending at the as-of date, annualised.

    Accepts filer-prefixed names (orcl:FinanceLeaseCost). Without a finance lease cost tag, uses amortisation plus
    interest on finance leases. Intuition: EBITDA is after rent, so the EBITDAR margin adds this back.
    """
    as_of = sc.as_of_date(df)
    d = df[(df["n_dims"] == 0) & (df["end"] == as_of) & df["start"].notna() & df["value"].notna()].copy()
    d["local"] = _local(d)
    d["months"] = ((d["end"] - d["start"]).dt.days / 30.44).round()
    used, total = [], 0.0
    months_used = None

    def pick(names: Callable[[str], bool]) -> tuple[float, float, str] | None:
        hit = d[d["local"].map(names)]
        if hit.empty:
            return None
        hit = hit.sort_values(["months", "concept"])
        r = hit.iloc[0]
        return float(r["value"]) / 1e6, float(r["months"]), str(r["concept"])

    bad = re.compile(r"Variable|ShortTerm|Sublease|Income|Payment")
    op = pick(lambda n: n == "OperatingLeaseCost") or pick(lambda n: n.endswith("OperatingLeaseCost") and not bad.search(n))
    fin = pick(lambda n: n.endswith("FinanceLeaseCost") and not bad.search(n))
    parts = [op, fin]
    if fin is None:
        parts += [pick(lambda n: n == "FinanceLeaseRightOfUseAssetAmortization"),
                  pick(lambda n: n == "FinanceLeaseInterestExpense")]
    for p in parts:
        if p is None:
            continue
        v, months, concept = p
        total += v * 12 / months
        used.append(f"{concept} ({months:.0f}m)")
        months_used = months
    if not used:
        return None, "not tagged: no OperatingLeaseCost or FinanceLeaseCost at the as-of date"
    return total, f"tag {' + '.join(used)}, annualised x {12 / months_used:.0f}"


def lease_term_tag(df: pd.DataFrame) -> float | None:
    s = df[_local(df) == "OperatingLeaseWeightedAverageRemainingLeaseTerm1"]
    s = s[s["n_dims"] == 0]
    if s.empty:
        return None
    s = s.sort_values("end")
    return iso_years(s["text"].iloc[-1])


def iso_years(s: object) -> float | None:
    """ISO 8601 duration to years: 'P12Y' -> 12, 'P3Y2M12D' -> 3.2. None when not a duration."""
    m = re.fullmatch(r"P(?:(\d+)Y)?(?:(\d+)M)?(?:(\d+)D)?", str(s or ""))
    if not m or not any(m.groups()):
        return None
    y, mo, d = (int(g or 0) for g in m.groups())
    return round(y + mo / 12 + d / 365.25, 3)


def purchase_total(df: pd.DataFrame) -> float | None:
    """Undimensioned unrecorded purchase obligation at the as-of date (USD m), for filers without a ladder."""
    as_of = sc.as_of_date(df)
    s = df[(_local(df) == "UnrecordedUnconditionalPurchaseObligationBalanceSheetAmount") & (df["n_dims"] == 0)
           & (df["end"] == as_of)]
    return float(s["value"].iloc[0]) / 1e6 if len(s) else None


def fy_end_text(df: pd.DataFrame) -> str | None:
    s = df.loc[df["concept"] == "dei:CurrentFiscalYearEndDate", "text"]
    return s.iloc[0] if len(s) else None


def rpo_crosscheck(xbrl_windows: Sequence[tuple[float, float, float]], text_windows: Sequence[tuple[float, float, float]],
                   tol_share: float = 0.01, tol_years: float = 0.1) -> str:
    """'agree', 'lengths differ', 'shares differ', or 'missing'. Compares shares first, then starts and lengths."""
    if not xbrl_windows or not text_windows:
        return "missing"
    if len(xbrl_windows) != len(text_windows) or any(abs(a[2] - b[2]) > tol_share
                                                       for a, b in zip(xbrl_windows, text_windows)):
        return "shares differ"
    if any(abs(a[0] - b[0]) > tol_years or abs(a[1] - b[1]) > tol_years for a, b in zip(xbrl_windows, text_windows)):
        return "lengths differ"
    return "agree"


# ---------------------------------------------------------------------------------------------------------------
# Loader quantities
# ---------------------------------------------------------------------------------------------------------------


def _finite(x: float) -> bool:
    return x is not None and not (isinstance(x, float) and math.isnan(x))


def last_four(quarters: Sequence[Any]) -> list[Any]:
    """The last four quarters if they are consecutive (first to last within 290 days); else []."""
    q = sorted(quarters, key=lambda r: r.as_of)[-4:]
    if len(q) < 4 or (q[-1].as_of - q[0].as_of).days > 290:
        return []
    return q


def interest_rate(quarters: Sequence[Any], bounds: tuple[float, float] = RATE_BOUNDS) -> Pair:
    """LTM cash interest over average total debt across the last four quarters, clipped to `bounds`.

    Intuition: the rate the issuer pays on its average balance. Quarters without a debt figure drop out of the
    average; the source says how many entered. Returns (None, reason) when the inputs are missing.
    """
    q = last_four(quarters)
    if not q:
        return None, "loader: fewer than four consecutive quarters"
    interest = [r.cash_interest for r in q]
    if not all(_finite(x) for x in interest):
        return None, "loader: cash interest missing in the last four quarters"
    debts = [(0.0 if not _finite(r.debt_current) else r.debt_current) + r.debt_long_term
             for r in q if _finite(r.debt_long_term)]
    if not debts or np.mean(debts) <= 0:
        return None, "loader: total debt missing in the last four quarters"
    raw = float(sum(interest) / np.mean(debts))
    rate = float(np.clip(raw, *bounds))
    note = f", clipped from {raw:.3f}" if rate != raw else ""
    return rate, (f"loader LTM cash interest {sum(interest):,.0f} / average total debt {np.mean(debts):,.0f} "
                  f"({len(debts)} of 4 quarters), {q[0].as_of:%b-%Y}..{q[-1].as_of:%b-%Y}{note}")


def ltm(quarters: Sequence[Any]) -> dict[str, Pair]:
    """LTM EBITDA (company-adjusted, Compustat OIBDP basis), LTM revenue, and latest-quarter revenue x 4."""
    q = last_four(quarters)
    if not q:
        miss = (None, "loader: fewer than four consecutive quarters")
        return {"ltm_ebitda": miss, "ltm_revenue": miss, "run_rate_revenue": miss}
    span = f"{q[0].as_of:%b-%Y}..{q[-1].as_of:%b-%Y}"
    srcs = "+".join(sorted({r.source for r in q}))

    def total(field: str, label: str) -> Pair:
        vals = [getattr(r, field) for r in q]
        if not all(_finite(v) for v in vals):
            gaps = [f"{r.as_of:%b-%Y}" for r, v in zip(q, vals) if not _finite(v)]
            ok = [v for v in vals if _finite(v)]
            if len(ok) == 3:  # one quarter lost to the XBRL definition check: annualise the other three, and say so
                return float(sum(ok) * 4 / 3), (f"loader LTM {span} {label}, {srcs}; fallback: 3 of 4 quarters x 4/3 "
                                                f"({', '.join(gaps)} missing)")
            return None, f"loader LTM {span} {label} missing for {', '.join(gaps)}"
        return float(sum(vals)), f"loader LTM {span} {label}, {srcs}"

    rr = q[-1].revenue
    return {
        "ltm_ebitda": total("ebitda_adj_company", "EBITDA (OIBDP)"),
        "ltm_revenue": total("revenue", "revenue"),
        "run_rate_revenue": (float(rr * 4), f"loader {q[-1].as_of:%b-%Y} quarter revenue x 4") if _finite(rr)
        else (None, "loader latest quarter revenue missing"),
    }


def _issuer_cache(cache_root: Path) -> Path:
    return cache_root / "compustat_pit" / "issuers.json"


def lookup_issuer(ticker: str, cache_root: Path, fetch: edgar.Fetch = edgar.fetch_json) -> dict:
    """{gvkey, cik, conm, source} for a ticker: cached Compustat lookup, then WRDS, then the SEC ticker file."""
    t = ticker.upper()
    path = _issuer_cache(cache_root)
    cache = json.loads(path.read_text()) if path.exists() else {}
    if t in cache:
        return cache[t]
    try:
        from hy.sources import compustat_pit as cp

        ids = cp.lookup_issuers(cp.connect(), [t])
        ids = ids[ids["cik"].notna()]
        if len(ids):
            r = ids.iloc[0]
            out = {"gvkey": str(r["gvkey"]), "cik": str(int(float(r["cik"]))), "conm": str(r["conm"]),
                   "source": "loader Compustat comp.security/comp.company"}
            cache[t] = out
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(cache, indent=1))
            return out
    except Exception as exc:  # WRDS down or no credentials: fall back to the SEC file
        print(f"Compustat lookup failed for {t} ({type(exc).__name__}); using the SEC ticker file")
    doc = fetch(TICKERS_URL)
    for v in doc.values():
        if str(v["ticker"]).upper() == t:
            return {"gvkey": None, "cik": str(v["cik_str"]), "conm": v["title"], "source": "text SEC company_tickers.json"}
    raise LookupError(f"ticker {t} not in Compustat or the SEC ticker file")


def _parquet_for(gvkey: str, raw: Path) -> tuple[pd.DataFrame, Path] | None:
    """The `financials_*.parquet` with the latest quarter for `gvkey` (newest file on ties)."""
    best = None
    for p in sorted(raw.glob("financials_*.parquet"), key=lambda p: p.stat().st_mtime):
        d = pd.read_parquet(p)
        d = d[d["gvkey"].astype(str) == gvkey]
        if d.empty:
            continue
        key = d["datadate"].max()
        if best is None or key >= best[0]:
            best = (key, d, p)
    return (best[1], best[2]) if best else None


def run_loader(tickers: Sequence[str], raw: Path, start: str = "2015-01-01", end: str | None = None) -> Path:
    """The steps of `scripts/load_financials.py`: Compustat PIT vintages, XBRL gap fill, EDGAR timing. Needs WRDS."""
    from hy.sources import compustat_pit as cp
    from hy.sources import financials, xbrl

    end = end or str(pd.Timestamp.today().date())
    con = cp.connect()
    ids = cp.lookup_issuers(con, list(tickers))
    if ids.empty:
        raise LookupError(f"no Compustat issuer for {tickers}")
    vint = cp.load_vintages(con, ids["gvkey"].tolist(), start, end, cache_root=raw)
    idx = pd.concat([edgar.filing_index(c, cache_root=raw, refresh=True) for c in ids["cik"].dropna().unique()],
                    ignore_index=True)
    cik_by_gvkey = dict(zip(ids["gvkey"], ids["cik"]))
    gaps = vint[~vint["pit_exact"]]
    if len(gaps):
        facts = {edgar._cik10(c): xbrl.company_facts(c, cache_root=raw) for c in ids["cik"].dropna().unique()}
        filled = xbrl.fill_quarters(gaps, facts, idx, cik_by_gvkey,
                                    pit_first=vint[vint["pit_exact"] & (vint["vintage"] == 0)])
        vint = financials.replace_inexact(vint, filled)
    matched = financials.match_filings(vint, edgar.periodic_filings(idx), cik_by_gvkey)
    out = raw / f"financials_{'_'.join(t.upper() for t in tickers)}.parquet"
    matched.to_parquet(out, index=False)
    return out


def loader_quarters(ticker: str, gvkey: str | None, raw: Path, decision_time: pd.Timestamp,
                    need_through: pd.Timestamp | None = None, allow_wrds: bool = True) -> tuple[list, str]:
    """Quarters known at `decision_time` from the PIT store. Runs the loader when the cached parquet is stale."""
    from hy.sources import financials

    if gvkey is None:
        return [], "no gvkey"
    hit = _parquet_for(gvkey, raw)
    stale = hit is None or (need_through is not None and hit[0]["datadate"].max() < need_through - pd.Timedelta(10, unit="D"))
    if stale and allow_wrds:
        try:
            run_loader([ticker], raw, end=str(decision_time.date()))
            hit = _parquet_for(gvkey, raw)
        except Exception as exc:
            print(f"loader run failed for {ticker} ({type(exc).__name__}: {exc}); using the cached parquet if any")
    if hit is None:
        return [], "no loader data"
    store = financials.build_store(hit[0])
    q = [r for r in store.as_known(decision_time.to_pydatetime()) if r.key == gvkey]
    return q, hit[1].name


# ---------------------------------------------------------------------------------------------------------------
# Overrides
# ---------------------------------------------------------------------------------------------------------------


def _tuplify(x: Any) -> Any:
    if isinstance(x, list):
        return tuple(_tuplify(v) for v in x)
    if isinstance(x, dict):
        return {k: _tuplify(v) for k, v in x.items()}
    return x


def load_overrides(ticker: str, overrides_dir: Path | str | None) -> dict[str, dict]:
    """Analyst YAML for a ticker: {key: {"value": v, "source": s, "fallback": bool}}. Missing file -> {}.

    A bare value is accepted and gets the source 'analyst override (no source given)'. Lists become tuples.
    """
    if overrides_dir is None:
        return {}
    path = Path(overrides_dir) / f"{ticker.upper()}.yaml"
    if not path.exists():
        return {}
    import yaml

    doc = yaml.safe_load(path.read_text()) or {}
    out = {}
    for k, v in doc.items():
        if isinstance(v, dict) and "value" in v:
            out[k] = {"value": _tuplify(v["value"]), "source": str(v.get("source", "no source given")),
                      "fallback": bool(v.get("fallback", False)), "secondary": bool(v.get("secondary", False))}
        else:
            out[k] = {"value": _tuplify(v), "source": "no source given", "fallback": False, "secondary": False}
    return out


def apply_overrides(inputs: dict[str, Pair], overrides: dict[str, dict],
                    valid: Callable[[str, Any], bool] | None = None) -> dict[str, Pair]:
    """Overrides win over derived values. An override marked `fallback` applies only when the derived value is
    None or fails `valid(key, value)`. The source records the override and keeps the derived one for audit."""
    out = dict(inputs)
    for k, o in overrides.items():
        derived = out.get(k, (None, "not derived"))
        if o["fallback"] and derived[0] is not None and (valid is None or valid(k, derived[0])):
            out[k] = (derived[0], derived[1] + f"; analyst fallback {o['value']!r} not used")
            continue
        tag = "analyst override (secondary source)" if o["secondary"] else "analyst override"
        prior = f"; derived was {derived[0]!r} [{derived[1]}]" if derived[0] is not None else ""
        out[k] = (o["value"], f"{tag}: {o['source']}{prior}")
    return out


def _rate_ok(key: str, value: Any) -> bool:
    if key != "interest_rate":
        return True
    return RATE_BOUNDS[0] < float(value) < RATE_BOUNDS[1]  # a clipped rate is not a measured rate


# ---------------------------------------------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------------------------------------------


def _short_name(name: str) -> str:
    """'CoreWeave, Inc.' -> 'CoreWeave'; 'ORACLE CORP' -> 'Oracle'."""
    n = re.sub(r"(?i)[,.]?\s+(inc|corp|corporation|ltd|limited|n\.?v|plc|co)\.?$", "", name.strip())
    return n.title() if n.isupper() else n


def derive_inputs(
    ticker: str, cache_root: Path, overrides_dir: Path | str | None = "data/analyst_inputs", as_of: object | None = None,
    allow_wrds: bool = True,
) -> dict[str, Pair]:
    """Every input of the Section 4.7 case for `ticker` as (value, source), as known at `as_of` (default now).

    Order: identifiers and filings, loader quantities, instance tags, prose, defaults, then analyst overrides.
    """
    t = ticker.upper()
    cache_root = Path(cache_root)
    decision = _decision_time(as_of)
    ov = load_overrides(t, overrides_dir)
    iss = lookup_issuer(t, cache_root)
    cik = iss["cik"]
    filings = latest_filings(cik, decision, cache_root, refresh=as_of is None)
    q_row, k_row = filings["latest"], filings["annual"]
    q = xi.load_instance(cik, q_row["accession"], cache_root=cache_root)
    k = None
    if k_row is not None and k_row["accession"] != q_row["accession"]:
        k = xi.load_instance(cik, k_row["accession"], cache_root=cache_root)
    bs = sc.as_of_date(q)
    head = cache_root / "edgar" / f"CIK{edgar._cik10(cik)}.json"
    sec_name = json.loads(head.read_text()).get("name") if head.exists() else None
    label = f"{q_row['form']} {bs:%b-%Y}"

    inp: dict[str, Pair] = {
        "ticker": (t, "input"),
        "name": (_short_name(sec_name or iss["conm"]), "text EDGAR submissions name" if sec_name else iss["source"]),
        "cik": (cik, iss["source"]),
        "gvkey": (iss["gvkey"], iss["source"]),
        "decision_time": (str(decision), "input as_of" if as_of is not None else "run time (now, UTC)"),
        "q": (q_row["accession"], f"EDGAR index: latest {q_row['form']} accepted {q_row['acceptance']} <= decision time"),
        "k": (k_row["accession"] if k is not None else None,
              f"EDGAR index: latest 10-K accepted {k_row['acceptance']}" if k is not None else "latest filing is the 10-K"),
        "q_acceptance": (str(q_row["acceptance"]), "EDGAR acceptanceDateTime (UTC)"),
        "k_acceptance": (str(k_row["acceptance"]) if k is not None else None, "EDGAR acceptanceDateTime (UTC)"),
        "balance_sheet_date": (str(bs.date()), f"tag instant context mode, {label}"),
    }

    # Loader quantities (Section 3.2 point-in-time store).
    quarters, loader_file = loader_quarters(t, iss["gvkey"], cache_root, decision, need_through=bs, allow_wrds=allow_wrds)
    inp.update(ltm(quarters))
    inp["interest_rate"] = interest_rate(quarters)
    if quarters:
        last = last_four(quarters)
        inp["loader_available_at"] = (str(max(r.available_at for r in last)) if last else None, f"loader {loader_file}")
        if last and last[-1].as_of.date() != bs.date():
            inp["loader_lag"] = (str(last[-1].as_of.date()), f"loader's latest quarter differs from the filing date {bs.date()}")

    # Instance tags.
    inp["annual_lease_cost"] = annual_lease_cost(q)
    wavg = lease_term_tag(q)
    text = filing_text(cik, q_row["accession"], cache_root)
    if wavg is not None:
        inp["lease_wavg_term"] = (wavg, f"tag OperatingLeaseWeightedAverageRemainingLeaseTerm1, {label}; check only")
    else:
        w = parse_lease_term(text)
        inp["lease_wavg_term"] = (w, f"text {label} weighted-average remaining lease term; check only" if w is not None
                                  else "not tagged and not found in text")

    # Signed leases not yet commenced: amount from tags, window and term from prose.
    fye = fy_end_text(q)
    nc_total, nc_lo, nc_hi = sc.lease_not_commenced(q)
    com = parse_commencement(text, bs, fye)
    src_doc = label
    if com is None and k is not None:
        com = parse_commencement(filing_text(cik, k_row["accession"], cache_root), bs, fye)
        src_doc = f"10-K {sc.as_of_date(k):%b-%Y}"
    if com is not None:
        inp["uncommenced_window"] = (com["window"], f"text {src_doc}: '{_clip(com['sentence'])}'")
    else:
        inp["uncommenced_window"] = (DEFAULT_UNCOMMENCED_WINDOW, "default assumption: no commencement sentence found")
    if com is not None and com["term"] is not None:
        lo, hi = com["term"]
        inp["uncommenced_term"] = ((lo + hi) / 2, f"text {src_doc}: midpoint of {lo:g} to {hi:g} years")
    elif not (np.isnan(nc_lo) or np.isnan(nc_hi)):
        inp["uncommenced_term"] = ((nc_lo + nc_hi) / 2, f"tag LeaseNotYetCommencedTermOfContract min and max, {label}")
    else:
        inp["uncommenced_term"] = (DEFAULT_UNCOMMENCED_TERM, "default assumption: 15-year term, filing gives none")
    if np.isnan(nc_total):
        unused = "not used: no lease not yet commenced is tagged"
        inp["uncommenced_window"] = (None, unused + (f"; text gives {com['window']}" if com else ""))
        inp["uncommenced_term"] = (None, unused)

    # Debt tail: run-rate convention on the ladder when the last two buckets are positive.
    debt = sc.ladder(q, "debt")
    dsrc = label
    if debt is None and k is not None:
        debt, dsrc = sc.ladder(k, "debt"), f"10-K {sc.as_of_date(k):%b-%Y}"
    if debt is not None and len(debt.amounts) >= 2 and debt.amounts[-2] > 0 and debt.amounts[-1] > 0:
        run = clocks.tail_years_run_rate(debt.amounts)
        cap = f", capped from {run:.1f} (a bullet wall is not level amortisation)" if run > MAX_DEBT_TAIL else ""
        inp["debt_tail_years"] = (min(run, MAX_DEBT_TAIL), f"default assumption: run-rate tail on the {dsrc} debt ladder "
                                  f"(thereafter {debt.amounts[-1]:,.0f} / last year {debt.amounts[-2]:,.0f}){cap}")
    else:
        inp["debt_tail_years"] = (DEFAULT_DEBT_TAIL, "default assumption: 5 years, ladder tail not usable")

    # RPO: XBRL first, prose as the cross-check and the fallback.
    rpo_total, xw = sc.rpo_windows(q)
    rt = parse_rpo(text)
    if xw:
        check = rpo_crosscheck(xw, rt["windows"]) if rt else "missing"
        if check == "lengths differ":
            # Shares agree but lengths differ: some filers tag each window's period cumulatively from the
            # balance sheet date (CoreWeave tags months 25-48 as P48M). The sentence states the window itself.
            inp["rpo_windows"] = (rt["windows"], f"text {label}: '{_clip(rt['sentence'])}' "
                                  f"(XBRL lengths {[w[1] for w in xw]} read as cumulative; shares agree)")
        else:
            inp["rpo_windows"] = (xw, f"tag RevenueRemainingPerformanceObligationPercentage windows, {label}; "
                                  f"text cross-check: {check}")
    elif rt:
        inp["rpo_windows"] = (rt["windows"], f"text {label}: '{_clip(rt['sentence'])}'")
    else:
        inp["rpo_windows"] = ([], "not disclosed: no XBRL timing tags and no timetable sentence")
    if not np.isnan(rpo_total):
        inp["rpo_total"] = (rpo_total, f"tag RevenueRemainingPerformanceObligation, {label}")
    elif rt and not np.isnan(rt["total"]):
        inp["rpo_total"] = (rt["total"], f"text {label}: RPO amount in the timetable sentence")
    else:
        inp["rpo_total"] = (None, "not disclosed: no RevenueRemainingPerformanceObligation tag or sentence")
    if rt and rt["tail"] is not None:
        inp["rpo_tail_years"] = (round(rt["tail"][1], 3), f"text {label}: remaining balance over months "
                                 f"{rt['tail'][0] * 12 + 1:.0f} to {(rt['tail'][0] + rt['tail'][1]) * 12:.0f}")
    else:
        inp["rpo_tail_years"] = (DEFAULT_RPO_TAIL, "default assumption: 2 years, filing gives no timing for the rest")

    # Purchase commitments: the ladder is read by the case; a bare total needs a spread assumption.
    if sc.ladder(q, "purchase") is None:
        pt = purchase_total(q)
        inp["purchase"] = ((pt, DEFAULT_PURCHASE_YEARS), "tag UnrecordedUnconditionalPurchaseObligationBalanceSheetAmount; "
                           "default assumption: spread over 2 years") if pt else (None, "no purchase ladder or total")
    else:
        inp["purchase"] = (None, f"tag ladder UnrecordedUnconditionalPurchaseObligation, {label}")

    # Judgement fields: analyst only.
    inp["scenario_extra_lease"] = (None, "analyst only: none given")
    inp["recourse"] = (None, "analyst only: none given")
    inp["rating"] = (None, "analyst only: no source in the system has current ratings")

    inp = apply_overrides(inp, ov, _rate_ok)
    stamps = [inp["q_acceptance"][0], inp.get("loader_available_at", (None,))[0]]
    if k is not None:
        stamps.append(inp["k_acceptance"][0])
    inp["available_at"] = (max(str(pd.Timestamp(s)) for s in stamps if s), "latest acceptance or loader release among inputs")
    if pd.Timestamp(inp["available_at"][0]) > decision:
        raise AssertionError(f"look-ahead: input available at {inp['available_at'][0]} after {decision}")
    return inp


def _clip(s: str, n: int = 220) -> str:
    s = " ".join(s.split())
    return s if len(s) <= n else s[: n - 3] + "..."


def values(inputs: dict[str, Pair]) -> dict[str, Any]:
    return {k: v[0] for k, v in inputs.items()}


def sources(inputs: dict[str, Pair]) -> dict[str, str]:
    return {k: v[1] for k, v in inputs.items()}


def defaults_used(inputs: dict[str, Pair]) -> list[str]:
    return [k for k, (_, s) in inputs.items() if s.startswith("default assumption")]
