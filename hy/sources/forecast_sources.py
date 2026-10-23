"""External forecast sources for the forecast registry (methodology Section 5.4, framework F6).

Each loader returns `list[ForecastRow]` (hy.forecasts). Each row carries two times:
- `vintage`: the date the forecast was made (survey deadline, meeting date, curve date, survey quarter start).
- `available_at`: the first moment the market could read it. The rule is always "release date of the
  publication, end of day", stored as release date + 1 day, 00:00. It is never the reference period.

Live sources (free, public):
1. `spf`, `spf_prob`, `spf_prob_pce`: Philadelphia Fed Survey of Professional Forecasters.
2. `fomc_sep`: FOMC Summary of Economic Projections (Fed website tables).
3. `ust_forward`: forward paths bootstrapped from the Treasury par curve (hy.sources.treasury).
4. `sloos`: Senior Loan Officer Opinion Survey, Fed Data Download Program.
5. `trace_hy_benchmark`: median G-spread and distress ratio of the TRACE high yield benchmark
   (hy.sources.trace_bonds, WRDS).

Stub sources return [] and log one line. Their docstrings name the real source and the fields it would fill.

Units: decimals for rates, growth, and spreads (0.025 = 2.5%), the same as hy.forecasts.
Raw downloads go under `<cache_root>/forecasts/<source>/`; `cache_root` defaults to `data/raw` (git ignores it).
FRED is not used: fred.stlouisfed.org returned a bot check, then timed out, on 2026-10-22.
"""

from __future__ import annotations

import io
import logging
import math
import os
import re
import urllib.request
import zipfile
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from hy.forecasts import FALLBACK_ORDER, ForecastRegistry, ForecastRow
from hy.data.config import CONFIG

log = logging.getLogger(__name__)

DEFAULT_CACHE_ROOT = CONFIG.root
END_OF_DAY = pd.Timedelta(1, unit="D")  # release date d is readable from d + 1 day, 00:00
NAN = float("nan")

Fetch = Callable[[str], bytes]


def fetch_bytes(url: str) -> bytes:
    """GET `url`. Government sites ask for a contact User-Agent: send $SEC_USER_AGENT."""
    agent = os.environ.get("SEC_USER_AGENT") or "FundamentalQuantmental research"
    req = urllib.request.Request(url, headers={"User-Agent": agent})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def _cached_bytes(path: Path, url: str, fetch: Fetch, refresh: bool) -> bytes:
    if path.exists() and not refresh:
        return path.read_bytes()
    data = fetch(url)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return data


def _root(cache_root: Path | str | None) -> Path:
    return Path(cache_root) if cache_root is not None else DEFAULT_CACHE_ROOT


def _ts(x) -> datetime:
    return pd.Timestamp(x).to_pydatetime()


def _quarter(d) -> tuple[int, int]:
    t = pd.Timestamp(d)
    return t.year, (t.month - 1) // 3 + 1


def horizon_to_q4(vintage_year: int, vintage_quarter: int, target_year: int) -> int:
    """Quarters from the vintage quarter to Q4 of `target_year` (annual targets sit at Q4 of their year)."""
    return 4 * (int(target_year) - int(vintage_year)) + (4 - int(vintage_quarter))


# ================================================================ 1. Survey of Professional Forecasters

SPF_BASE = "https://www.philadelphiafed.org/-/media/frbp/assets/surveys-and-data/survey-of-professional-forecasters"
SPF_FILES = {
    "level": f"{SPF_BASE}/historical-data/medianLevel.xlsx",
    "growth": f"{SPF_BASE}/historical-data/medianGrowth.xlsx",
    "prob": f"{SPF_BASE}/historical-data/prob.xlsx",
    "dates": f"{SPF_BASE}/spf-release-dates.txt",
}

# Bin lower bounds, highest bin first, as the workbook orders them (SPF documentation, Tables 7, 8, 9).
# A label "a to b" covers [a, b + 0.1): each bin ends where the next higher bin starts. The last bin is open below.
# Each era: (first survey (year, quarter), lower bounds of bins 1..n-1).
SPF_BIN_ERAS: dict[str, list[tuple[tuple[int, int], tuple[float, ...]]]] = {
    "PRGDP": [
        ((1992, 1), (6.0, 5.0, 4.0, 3.0, 2.0, 1.0, 0.0, -1.0, -2.0)),
        ((2009, 2), (6.0, 5.0, 4.0, 3.0, 2.0, 1.0, 0.0, -1.0, -2.0, -3.0)),
        ((2020, 2), (16.0, 10.0, 7.0, 4.0, 2.5, 1.5, 0.0, -3.0, -6.0, -12.0)),
        ((2024, 2), (9.0, 7.0, 5.5, 4.0, 2.5, 1.5, 0.0, -1.5, -3.0, -5.1)),
    ],
    "PRUNEMP": [
        ((2009, 2), (11.0, 10.0, 9.5, 9.0, 8.5, 8.0, 7.5, 7.0, 6.0)),
        ((2014, 1), (9.0, 8.0, 7.5, 7.0, 6.5, 6.0, 5.5, 5.0, 4.0)),
        ((2020, 2), (15.0, 12.0, 10.0, 8.0, 7.0, 6.0, 5.0, 4.0, 3.0)),
        ((2024, 2), (9.9, 8.3, 7.2, 6.1, 5.5, 4.9, 4.3, 3.7, 3.1)),
    ],
    "PRCCPI": [((2007, 1), (4.0, 3.5, 3.0, 2.5, 2.0, 1.5, 1.0, 0.5, 0.0))],
    "PRCPCE": [((2007, 1), (4.0, 3.5, 3.0, 2.5, 2.0, 1.5, 1.0, 0.5, 0.0))],
}
# Sheet -> (registry source, variable). Core PCE goes to its own source so that no reader mixes it with CPI.
SPF_BIN_TARGETS = {
    "PRGDP": ("spf_prob", "gdp_growth"),    # annual-average over annual-average real GDP growth
    "PRUNEMP": ("spf_prob", "unemployment"),  # annual-average unemployment rate
    "PRCCPI": ("spf_prob", "cpi"),          # core CPI, Q4 over Q4
    "PRCPCE": ("spf_prob_pce", "cpi"),      # core PCE, Q4 over Q4
}


def bin_edges(lowers_desc: Sequence[float]) -> tuple[np.ndarray, np.ndarray]:
    """Ascending (lo, hi) arrays for the bins given by their lower bounds, highest bin first.

    The top bin is [lowers[0], inf) and the bottom bin is (-inf, lowers[-1]). Each open tail gets the width of
    its neighbour bin, so the tails hold their mass in a finite interval.
    Intuition: an open bin is as wide as the bin beside it; this is the usual SPF convention in the literature.
    """
    low = list(lowers_desc)
    if len(low) < 2 or any(a <= b for a, b in zip(low, low[1:])):
        raise ValueError("bin lower bounds must be strictly decreasing, at least two")
    top = low[0] + (low[0] - low[1])
    bottom = low[-1] - (low[-2] - low[-1])
    hi_desc = [top, *low]          # bin k spans [low[k], hi_desc[k]) ; last bin [bottom, low[-1])
    lo_desc = [*low, bottom]
    return np.array(lo_desc[::-1], dtype=float), np.array(hi_desc[::-1], dtype=float)


def bin_quantiles(lo: Sequence[float], hi: Sequence[float], probs: Sequence[float],
                  qs: Sequence[float] = (0.1, 0.5, 0.9)) -> list[float]:
    """Quantiles of a histogram forecast: mass uniform inside each bin, bins ascending (method "survey_bins").

    F(x) is the cumulative bin probability, linear inside each bin. Quantile q is x with F(x) = q:
    x = lo_k + (q - F(lo_k)) / p_k * (hi_k - lo_k) for the first bin k with F(hi_k) >= q.
    Probabilities may be in percent; they are normalised to sum 1.
    Intuition: the q-th forecaster dollar of probability sits at a point spread evenly across its bin.
    """
    lo, hi, p = (np.asarray(x, dtype=float) for x in (lo, hi, probs))
    p = np.nan_to_num(p, nan=0.0).clip(min=0.0)
    if p.sum() <= 0:
        raise ValueError("bin probabilities sum to zero")
    p = p / p.sum()
    cdf = np.cumsum(p)
    out = []
    for q in qs:
        k = int(np.searchsorted(cdf, q - 1e-12))
        k = min(k, len(p) - 1)
        while p[k] == 0 and k > 0:  # q fell exactly on an edge after an empty bin
            k -= 1
        below = cdf[k] - p[k]
        frac = 0.0 if p[k] == 0 else float(np.clip((q - below) / p[k], 0.0, 1.0))
        out.append(float(lo[k] + frac * (hi[k] - lo[k])))
    return out


def _era(sheet: str, year: int, quarter: int) -> tuple[float, ...] | None:
    eras = [e for e in SPF_BIN_ERAS[sheet] if (year, quarter) >= e[0]]
    return eras[-1][1] if eras else None


def parse_spf_release_dates(text: str) -> dict[tuple[int, int], tuple[pd.Timestamp, pd.Timestamp]]:
    """(year, quarter) -> (true deadline, news release date) from `spf-release-dates.txt`. Footnote stars dropped."""
    out: dict[tuple[int, int], tuple[pd.Timestamp, pd.Timestamp]] = {}
    year = None
    pat = re.compile(r"^\s*(\d{4})?\s*Q([1-4])\s+(\d{1,2}/\d{1,2}/\d{2})\**\s+(\d{1,2}/\d{1,2}/\d{2})")
    for line in text.splitlines():
        m = pat.match(line)
        if not m:
            continue
        if m.group(1):
            year = int(m.group(1))
        if year is None:
            continue
        dl, rel = (pd.to_datetime(m.group(i), format="%m/%d/%y") for i in (3, 4))
        out[(year, int(m.group(2)))] = (dl, rel)
    return out


def spf_timing(year: int, quarter: int, calendar: dict) -> tuple[datetime, datetime]:
    """(vintage, available_at) of one survey.

    Rule: vintage = the true deadline date; available_at = news release date + 1 day, 00:00 (end of release day).
    Dates come from the Philadelphia Fed release calendar (`spf-release-dates.txt`, surveys since 1990 Q2).
    Fallback for a survey not in the calendar: the documented pattern is a deadline in the middle of the second
    month of the quarter and a release a few days later. We use vintage = day 15 of the second month and
    available_at = the first day of the third month (conservative by about two weeks).
    """
    if (year, quarter) in calendar:
        dl, rel = calendar[(year, quarter)]
        return _ts(dl), _ts(rel + END_OF_DAY)
    m2 = 3 * (quarter - 1) + 2
    return _ts(pd.Timestamp(year, m2, 15)), _ts(pd.Timestamp(year, m2 + 1, 1))


def _sheet(xlsx: bytes, name: str) -> pd.DataFrame:
    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        df = pd.read_excel(io.BytesIO(xlsx), sheet_name=name)
    df.columns = [str(c).upper() for c in df.columns]
    for c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df.dropna(subset=["YEAR", "QUARTER"]).astype({"YEAR": int, "QUARTER": int})


def spf_median_rows(level: pd.DataFrame | None, growth: pd.DataFrame | None, cpi: pd.DataFrame | None,
                    calendar: dict, since: tuple[int, int] = (1990, 2)) -> list[ForecastRow]:
    """Median SPF forecasts, horizons 0..4 (method "survey_median", source "spf").

    - gdp_growth: `medianGrowth.xlsx` sheet RGDP, DRGDP2..DRGDP6 = annualised q/q real GDP growth, h = 0..4.
    - unemployment: `medianLevel.xlsx` sheet UNEMP, UNEMP2..UNEMP6 = quarterly average rate, h = 0..4.
    - cpi: `medianLevel.xlsx` sheet CPI holds annualised q/q headline CPI inflation for quarters -1..4
      (CPI1..CPI6). Year on year at horizon h = prod over the four quarters h-3..h of (1 + r/100)^(1/4) - 1.
      Quarters -3 and -2 come from CPI1 of the two earlier surveys, which were public before this one.
    Columns are percent; rows are decimals. q10, q50, q90 stay NaN: a median carries no spread.
    """
    rows: list[ForecastRow] = []

    def emit(df, variable, transform):
        if df is None:
            return
        for _, r in df.iterrows():
            y, q = int(r["YEAR"]), int(r["QUARTER"])
            if (y, q) < since:
                continue
            vint, avail = spf_timing(y, q, calendar)
            for h in range(5):
                v = transform(r, h, y, q)
                if v is not None and v == v:
                    rows.append(ForecastRow("spf", variable, h, vint, avail, float(v), method="survey_median"))

    emit(growth, "gdp_growth", lambda r, h, y, q: r.get(f"DRGDP{h + 2}", NAN) / 100.0)
    emit(level, "unemployment", lambda r, h, y, q: r.get(f"UNEMP{h + 2}", NAN) / 100.0)

    if cpi is not None:
        # realised (as first reported) quarterly CPI rate for quarter (y, q) - 1, from survey (y, q)
        hist = {}
        for _, r in cpi.iterrows():
            p = pd.Period(year=int(r["YEAR"]), quarter=int(r["QUARTER"]), freq="Q")
            hist[p - 1] = r.get("CPI1", NAN)

        def yoy(r, h, y, q):
            p0 = pd.Period(year=y, quarter=q, freq="Q")
            rates = []
            for k in range(h - 3, h + 1):
                if k >= -1:
                    rates.append(r.get(f"CPI{k + 2}", NAN))
                else:
                    rates.append(hist.get(p0 + k, NAN))
            rates = np.asarray(rates, dtype=float)
            if np.isnan(rates).any():
                return None
            return float(np.prod((1 + rates / 100.0) ** 0.25) - 1)

        emit(cpi, "cpi", yoy)
    return rows


def spf_bin_rows(prob_sheets: dict[str, pd.DataFrame], calendar: dict,
                 since: tuple[int, int] = (1990, 2)) -> list[ForecastRow]:
    """SPF density forecasts as q10, q50, q90 per target year (method "survey_bins").

    Each sheet holds mean probabilities (percent) over bins, n bins per target year, the current year first
    (SPF documentation, Section 6). Target year Y maps to horizon = quarters from the survey quarter to Q4 of Y.
    point = q50. Approximations, stated:
    - PRGDP is annual-average over annual-average growth; the registry variable is q/q annualised growth.
    - PRCCPI and PRCPCE are core, Q4 over Q4; the registry variable cpi is headline year on year.
    - The histogram is the mean across forecasters; it mixes disagreement with individual uncertainty.
    """
    rows: list[ForecastRow] = []
    for sheet, df in prob_sheets.items():
        source, variable = SPF_BIN_TARGETS[sheet]
        cols = [c for c in df.columns if c.startswith(sheet) and c[len(sheet):].isdigit()]
        cols.sort(key=lambda c: int(c[len(sheet):]))
        for _, r in df.iterrows():
            y, q = int(r["YEAR"]), int(r["QUARTER"])
            if (y, q) < since:
                continue
            lowers = _era(sheet, y, q)
            if lowers is None:
                continue
            nb = len(lowers) + 1
            lo, hi = bin_edges(lowers)
            vals = r[cols].to_numpy(dtype=float)
            vint, avail = spf_timing(y, q, calendar)
            for k in range(len(vals) // nb):
                block = vals[k * nb:(k + 1) * nb]
                if np.isnan(block).all() or np.nansum(block) < 50:  # not asked, or not reported
                    continue
                q10, q50, q90 = bin_quantiles(lo, hi, block[::-1])  # workbook order is high to low
                rows.append(ForecastRow(source, variable, horizon_to_q4(y, q, y + k), vint, avail,
                                        q50 / 100, q10 / 100, q50 / 100, q90 / 100, method="survey_bins"))
    return rows


def load_spf(cache_root: Path | str | None = None, fetch: Fetch = fetch_bytes, refresh: bool = False,
             since: tuple[int, int] = (1990, 2)) -> list[ForecastRow]:
    """SPF medians (source "spf") and densities (sources "spf_prob", "spf_prob_pce"), every vintage since `since`."""
    d = _root(cache_root) / "forecasts" / "spf"
    raw = {k: _cached_bytes(d / Path(u).name, u, fetch, refresh) for k, u in SPF_FILES.items()}
    calendar = parse_spf_release_dates(raw["dates"].decode("utf-8", "replace"))
    rows = spf_median_rows(_sheet(raw["level"], "UNEMP"), _sheet(raw["growth"], "RGDP"),
                           _sheet(raw["level"], "CPI"), calendar, since)
    rows += spf_bin_rows({s: _sheet(raw["prob"], s) for s in SPF_BIN_TARGETS}, calendar, since)
    return rows


# ================================================================ 2. FOMC Summary of Economic Projections

FOMC_CALENDAR_URL = "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"
SEP_URL = "https://www.federalreserve.gov/monetarypolicy/fomcprojtabl{date}.htm"
SEP_ROWS = {  # table row label (footnote digits removed) -> registry variable
    "Change in real GDP": "gdp_growth",   # Q4 over Q4
    "Unemployment rate": "unemployment",  # Q4 average
    "PCE inflation": "cpi",               # headline PCE, Q4 over Q4 (not CPI: stated approximation)
    "Federal funds rate": "policy_rate",  # midpoint of the target range at year end
}


def _range(text) -> tuple[float, float]:
    s = str(text).replace("–", "-").replace("−", "-").strip()
    m = re.fullmatch(r"(-?\d+(?:\.\d+)?)\s*-\s*(-?\d+(?:\.\d+)?)", s)
    if m:
        return float(m.group(1)), float(m.group(2))
    v = pd.to_numeric(s, errors="coerce")
    return float(v), float(v)


def parse_sep_table(html: str) -> pd.DataFrame:
    """Table 1 of one SEP release -> rows (variable, year, median, ct_lo, ct_hi, rng_lo, rng_hi), percent.

    Rows labelled "... projection" repeat the previous SEP and are dropped. "Longer run" is dropped: it has no date.
    """
    t = pd.read_html(io.StringIO(html))[0]
    groups = {"Median": "median", "Central": "ct", "Range": "rng"}
    out = []
    for _, r in t.iterrows():
        label = re.sub(r"\d+$", "", str(r.iloc[0])).strip()
        if label not in SEP_ROWS:
            continue
        rec: dict[int, dict] = {}
        for (grp, year), v in r.iloc[1:].items():
            g = next((val for key, val in groups.items() if str(grp).startswith(key)), None)
            if g is None or not str(year).strip().isdigit():
                continue
            lo, hi = _range(v)
            d = rec.setdefault(int(year), {})
            if g == "median":
                d["median"] = lo
            else:
                d[f"{g}_lo"], d[f"{g}_hi"] = lo, hi
        out += [{"variable": SEP_ROWS[label], "year": y, **d} for y, d in rec.items()]
    return pd.DataFrame(out)


def sep_rows(table: pd.DataFrame, meeting_date, fill_quarters: bool = True) -> list[ForecastRow]:
    """SEP projections as registry rows (source "fomc_sep", method "dot_range").

    Rule: vintage = the second day of the meeting; available_at = that day + 1 day, 00:00. The tables are
    published with the statement at 2:00 p.m. on the second day.
    Mapping: year Y -> horizon to Q4 of Y. q50 = median; q10 = low end and q90 = high end of the range of all
    participants. This is a stated approximation: the range is disagreement across participants, not one
    forecaster's 80% band, and it can be narrower or wider than that band.
    With `fill_quarters`, quarters between two Q4 anchors take linear interpolation of point and quantiles
    (method "dot_range_interp").
    """
    vint = _ts(pd.Timestamp(meeting_date).normalize())
    avail = _ts(pd.Timestamp(meeting_date).normalize() + END_OF_DAY)
    vy, vq = _quarter(meeting_date)
    rows: list[ForecastRow] = []
    for var, g in table.groupby("variable"):
        g = g.dropna(subset=["median"]).sort_values("year")
        h = np.array([horizon_to_q4(vy, vq, y) for y in g["year"]])
        keep = h >= 0
        g, h = g[keep], h[keep]
        if g.empty:
            continue
        cols = {k: g[k].to_numpy(float) / 100 if k in g else np.full(len(g), np.nan)
                for k in ("median", "rng_lo", "rng_hi")}
        for i, hh in enumerate(h):
            m, lo, hi = cols["median"][i], cols["rng_lo"][i], cols["rng_hi"][i]
            rows.append(ForecastRow("fomc_sep", var, int(hh), vint, avail, m, lo, m, hi, method="dot_range"))
        if fill_quarters and len(h) > 1:
            grid = np.arange(h[0] + 1, h[-1])
            grid = grid[~np.isin(grid, h)]
            vals = {k: np.interp(grid, h, v) for k, v in cols.items()}
            for j, hh in enumerate(grid):
                m, lo, hi = vals["median"][j], vals["rng_lo"][j], vals["rng_hi"][j]
                rows.append(ForecastRow("fomc_sep", var, int(hh), vint, avail, m, lo, m, hi,
                                        method="dot_range_interp"))
    return rows


def sep_meeting_dates(calendar_html: str) -> list[pd.Timestamp]:
    """Meeting dates with SEP tables, from the links on the FOMC calendar page (about the last five years)."""
    return sorted({pd.Timestamp(d) for d in re.findall(r"fomcprojtabl(\d{8})\.htm", calendar_html)})


def load_fomc_sep(cache_root: Path | str | None = None, fetch: Fetch = fetch_bytes, refresh: bool = False,
                  meeting_dates: Iterable | None = None) -> list[ForecastRow]:
    """All SEP vintages linked from the FOMC calendar page (or `meeting_dates`)."""
    d = _root(cache_root) / "forecasts" / "fomc_sep"
    if meeting_dates is None:
        cal = _cached_bytes(d / "fomccalendars.htm", FOMC_CALENDAR_URL, fetch, refresh).decode("utf-8", "replace")
        meeting_dates = sep_meeting_dates(cal)
    rows: list[ForecastRow] = []
    for md in meeting_dates:
        key = pd.Timestamp(md).strftime("%Y%m%d")
        html = _cached_bytes(d / f"fomcprojtabl{key}.htm", SEP_URL.format(date=key), fetch, False)
        rows += sep_rows(parse_sep_table(html.decode("utf-8", "replace")), md)
    return rows


# ================================================================ 3. Treasury forward curve

FORWARD_TENORS = {"policy_rate": 0.25, "y2": 2.0, "y10": 10.0}


def _discount_curve(curve_row: pd.Series):
    """Discount function D(t) bootstrapped from the par curve (bond-equivalent, semiannual coupons).

    Nodes: quoted tenors of 6 months or less are zero-coupon: D(t) = (1 + y/2)^(-2t). From 1 year on, par yields
    are interpolated (hy.sources.treasury.interpolate) on the semiannual grid and bootstrapped:
    D(t_n) = (1 - c/2 * sum_{i<n} D(t_i)) / (1 + c/2), c = par yield at t_n.
    Between nodes the continuous zero rate z(t) = -ln D(t) / t is linear; it is flat beyond the ends.
    Intuition: a par bond prices at 100, so each new coupon date pins one more discount factor.
    """
    from hy.sources import treasury  # lazy: the other agent owns this module

    pts = pd.to_numeric(curve_row[[k for k in curve_row.index if isinstance(k, float)]], errors="coerce").dropna()
    if pts.empty:
        raise ValueError("curve row has no tenor points")
    t_short = [t for t in sorted(pts.index) if t <= 0.5 + 1e-9]
    nodes_t, nodes_d = [], []
    for t in t_short:
        nodes_t.append(float(t))
        nodes_d.append((1 + pts[t] / 2) ** (-2 * t))
    grid = np.arange(0.5, float(max(pts.index)) + 1e-9, 0.5)
    par = np.atleast_1d(treasury.interpolate(curve_row, grid))
    ds: list[float] = []
    for i, (t, c) in enumerate(zip(grid, par)):
        d = (1 - c / 2 * sum(ds)) / (1 + c / 2)
        ds.append(d)
        if t > 0.5 + 1e-9 or 0.5 not in nodes_t:
            nodes_t.append(float(t))
            nodes_d.append(d)
    nt, nd = np.asarray(nodes_t), np.asarray(nodes_d)
    if (nd <= 0).any():  # a curve too steep to bootstrap at the long end: keep the nodes before the break
        cut = nt[np.argmax(nd <= 0)]
        log.warning("ust_forward: discount factor not positive from %.1fy; zero rate held flat beyond", cut)
        nt, nd = nt[nt < cut], nd[nt < cut]
    order = np.argsort(nt)
    nt = nt[order]
    z = -np.log(nd[order]) / nt

    def D(t):
        t = np.asarray(t, dtype=float)
        return np.exp(-np.interp(t, nt, z) * t)

    return D


def forwards_from_par(curve_row: pd.Series, horizons_q: Sequence[int] = range(9)) -> pd.DataFrame:
    """Forward rates implied by the par curve, one row per horizon (methodology Section 5.4, method "market_implied").

    With start tau = h / 4 years, all rates bond-equivalent (semiannual), like the par curve:
    - policy_rate (3-month forward): f = 2 * ((D(tau) / D(tau + 0.25))^2 - 1).
    - y2, y10 (forward par yield of an n-year bond that starts at tau):
      c = 2 * (D(tau) - D(tau + n)) / sum_{i=1}^{2n} D(tau + i/2).
    Intuition: the forward is the rate you can lock today for a loan that starts at tau. It equals the expected
    future rate plus a term premium, so it is a biased forecast when term premia are not zero.
    A flat par curve gives forwards equal to the par yield; an upward curve gives forwards that rise with h.
    """
    D = _discount_curve(curve_row)
    out = []
    for h in horizons_q:
        tau = h / 4.0
        rec = {"horizon_q": int(h)}
        d0 = float(D(tau))
        rec["policy_rate"] = 2 * ((d0 / float(D(tau + 0.25))) ** 2 - 1)
        for var in ("y2", "y10"):
            n = FORWARD_TENORS[var]
            ann = float(np.sum(D(tau + np.arange(1, int(2 * n) + 1) / 2)))
            rec[var] = 2 * (d0 - float(D(tau + n))) / ann
        out.append(rec)
    return pd.DataFrame(out)


def ust_forward_rows(curve_row: pd.Series, horizons_q: Sequence[int] = range(9)) -> list[ForecastRow]:
    """Forward paths as registry rows (source "ust_forward", method "market_implied", point only).

    Rule: vintage = the curve date (row name); available_at = the curve's `available_at` (curve date + 1 day,
    00:00, the end-of-day rule of hy.sources.treasury).
    """
    vint = pd.Timestamp(curve_row.name)
    avail = pd.Timestamp(curve_row.get("available_at", vint + END_OF_DAY))
    fw = forwards_from_par(curve_row, horizons_q)
    return [ForecastRow("ust_forward", var, int(r["horizon_q"]), _ts(vint), _ts(avail), float(r[var]),
                        method="market_implied")
            for _, r in fw.iterrows() for var in FORWARD_TENORS]


def load_ust_forwards(decision_time, cache_root: Path | str | None = None, dates: Iterable | None = None,
                      horizons_q: Sequence[int] = range(9), refresh: bool = False) -> list[ForecastRow]:
    """Forward rows from the latest curve readable at `decision_time` (and from any extra `dates`).

    The curve for date d is readable at d + 1 day, so the search date is `decision_time` - 1 day.
    """
    from hy.sources import treasury

    targets = [pd.Timestamp(decision_time) - END_OF_DAY, *(pd.Timestamp(x) for x in (dates or []))]
    rows, seen = [], set()
    for t in targets:
        row = treasury.curve_on(t, _root(cache_root), refresh=refresh)
        if row.name in seen:
            continue
        seen.add(row.name)
        rows += ust_forward_rows(row, horizons_q)
    return rows


# ================================================================ 4. Senior Loan Officer Opinion Survey

SLOOS_ZIP_URL = "https://www.federalreserve.gov/datadownload/Output.aspx?rel=SLOOS&filetype=zip"
SLOOS_PAGE_URL = "https://www.federalreserve.gov/data/sloos.htm"
SLOOS_SERIES = "SUBLPDCILS_N.Q"  # net % of domestic banks tightening C&I standards, large and middle-market firms


def parse_sloos_xml(xml: str, series: str = SLOOS_SERIES) -> pd.Series:
    """One SLOOS series from the DDP SDMX file: index = quarter-end label date, values in percent."""
    i = xml.find(f'SERIES_NAME="{series}"')
    if i < 0:
        raise ValueError(f"series {series} not in SLOOS file")
    j = xml.find("</kf:Series>", i)
    obs = re.findall(r'OBS_VALUE="([^"]+)"\s+TIME_PERIOD="([^"]+)"', xml[i:j])
    s = pd.Series({pd.Timestamp(t): pd.to_numeric(v, errors="coerce") for v, t in obs}, dtype=float)
    return s.dropna().sort_index()


def sloos_timing(label: pd.Timestamp, known_release: dict | None = None) -> tuple[datetime, datetime]:
    """(vintage, available_at) of the survey with quarter-end label `label`.

    The DDP labels a survey by the quarter of its survey month: the January, April, July, October surveys carry
    the labels Q1, Q2, Q3, Q4 (the July 2026 survey has label 2026-09-30, released August 3, 2026).
    Rule: vintage = the first day of the label quarter (responses close near then). available_at = the release
    date + 1 day when known; else the first day of the third month of the quarter. The Fed releases the survey
    in the second month of the quarter, so the fallback is late by up to four weeks and never early.
    """
    p = pd.Timestamp(label).to_period("Q")
    vint = p.start_time
    rel = (known_release or {}).get(p)
    avail = (pd.Timestamp(rel) + END_OF_DAY) if rel is not None else (vint + pd.DateOffset(months=2))
    return _ts(vint), _ts(avail)


def sloos_rows(series: pd.Series, known_release: dict | None = None) -> list[ForecastRow]:
    """Net tightening as registry rows (variable sloos_tightening, horizon 0, method "survey_realised"), decimals."""
    out = []
    for label, v in series.items():
        vint, avail = sloos_timing(label, known_release)
        out.append(ForecastRow("sloos", "sloos_tightening", 0, vint, avail, float(v) / 100.0,
                               method="survey_realised"))
    return out


def _latest_sloos_release(page_html: str) -> dict:
    """Release date of the latest survey: the "Last Update" stamp of the SLOOS landing page, keyed by quarter.

    The page changes when a survey is released. A stamp outside the second month of a quarter is ignored. A later
    edit of the page can only move the stamp later, so the rule never makes a survey readable too early.
    """
    txt = re.sub(r"<[^>]+>", " ", page_html)
    m = re.search(r"Last Update:\s*(January|February|March|April|May|June|July|August|September|October|November|December)"
                  r" (\d{1,2}), (\d{4})", txt)
    if not m:
        return {}
    d = pd.Timestamp(f"{m.group(1)} {m.group(2)} {m.group(3)}")
    return {d.to_period("Q"): d} if d.month % 3 == 2 else {}


def load_sloos(cache_root: Path | str | None = None, fetch: Fetch = fetch_bytes, refresh: bool = False,
               series: str = SLOOS_SERIES) -> list[ForecastRow]:
    """SLOOS C&I net tightening, every survey since 1990. The DDP zip holds one SDMX XML file."""
    d = _root(cache_root) / "forecasts" / "sloos"
    z = _cached_bytes(d / "SLOOS.zip", SLOOS_ZIP_URL, fetch, refresh)
    with zipfile.ZipFile(io.BytesIO(z)) as zf:
        xml = zf.read("SLOOS_data.xml").decode("utf-8", "replace")
    try:
        known = _latest_sloos_release(_cached_bytes(d / "sloos.htm", SLOOS_PAGE_URL, fetch, refresh)
                                      .decode("utf-8", "replace"))
    except Exception as exc:  # the landing page only refines one date; the rule covers the rest
        log.info("sloos: landing page unreadable (%s); rule-based release dates only", exc)
        known = {}
    return sloos_rows(parse_sloos_xml(xml, series), known)


# ================================================================ 5. TRACE high yield benchmark

DISTRESS_SPREAD = 0.10  # 1,000 bp


def trace_hy_rows(bonds: pd.DataFrame, curve_row: pd.Series, min_price: float = 80.0,
                  max_yield: float = 0.25) -> list[ForecastRow]:
    """hy_spread and distress_ratio at horizon 0 from one TRACE benchmark window (method "market_implied").

    Input: the per-bond frame of hy.sources.trace_bonds.hy_benchmark (columns yield, price, maturity, as_of,
    available_at) and the Treasury curve row for the window end.
    - hy_spread = median G-spread of bonds that pass the benchmark_by_bucket filters (price >= `min_price`,
      0 < yield <= `max_yield`): the same universe as the bucket medians, all buckets pooled.
    - distress_ratio = share of all bonds with a positive yield whose G-spread exceeds 1,000 bp. No price filter
      here: distressed bonds are the numerator.
    Rule: vintage = the last trade date in the window; available_at = max(bond available_at, curve available_at),
    which is the last trade date + 1 day (TRACE end-of-day rule of hy.sources.trace_bonds).
    Caveat: a G-spread is not an OAS; callable bonds show a wider G-spread than OAS.
    """
    from hy.sources import trace_bonds  # lazy: the other agent owns this module

    d = bonds[bonds["yield"] > 0].copy()
    if d.empty:
        return []
    d["g_spread"] = trace_bonds.g_spread(d["yield"].to_numpy(), d["maturity"], d["as_of"], curve_row)
    buckets = trace_bonds.benchmark_by_bucket(bonds, curve_row, min_price=min_price, max_yield=max_yield)
    core = d[(d["price"] >= min_price) & (d["yield"] <= max_yield)]
    vint = pd.Timestamp(d["as_of"].max())
    stamps = [pd.Timestamp(d["available_at"].max()) if "available_at" in d else vint + END_OF_DAY,
              pd.to_datetime(curve_row.get("available_at", pd.NaT)),
              pd.to_datetime(buckets["available_at"].max()) if len(buckets) else pd.NaT]
    avail = max(x for x in stamps if pd.notna(x))
    rows = []
    if len(core):
        from hy import state  # the one index rule (data module step 5)
        rows.append(ForecastRow("trace_hy_benchmark", "hy_spread", 0, _ts(vint), _ts(avail),
                                state.hy_index_level(core["g_spread"], core["price"], core["yield"]),
                                method="market_implied"))
    from hy import state  # the one distress rule (data module step 5)
    rows.append(ForecastRow("trace_hy_benchmark", "distress_ratio", 0, _ts(vint), _ts(avail),
                            state.distress_ratio(d["g_spread"], d["yield"]), method="market_implied"))
    return rows


def load_trace_hy(decision_time, cache_root: Path | str | None = None, bonds: pd.DataFrame | None = None,
                  curve_row: pd.Series | None = None, con=None, window_days: int = 10) -> list[ForecastRow]:
    """TRACE benchmark rows for the window that ends at the last TRACE trade date before `decision_time`.

    Pass `bonds` (and `curve_row`) to stay offline. Otherwise call trace_bonds.hy_benchmark with `con`; with no
    connection it reads its parquet cache, and raises if the cache misses.
    WRDS loads TRACE with a lag of weeks (on 2026-10-22 the last trade date was 2026-09-17). With `con`, the
    window ends at the latest trade date on WRDS that is before `decision_time` - 1 day, so the pull is never
    empty because of the load lag. The rows then carry that older vintage.
    """
    from hy.sources import trace_bonds, treasury

    end = (pd.Timestamp(decision_time) - END_OF_DAY).normalize()
    root = _root(cache_root)
    if bonds is None:
        if con is not None:
            last = con.raw_sql(f"select max(trd_exctn_dt) as m from {trace_bonds.TRADE_TABLES[0]} "
                               f"where trd_exctn_dt <= '{end:%Y-%m-%d}' and trd_exctn_dt >= '{end - pd.Timedelta(180, unit="D"):%Y-%m-%d}'")
            if pd.isna(last["m"].iloc[0]):
                raise ValueError(f"no TRACE trades on WRDS in the 180 days before {end.date()}")
            end = min(end, pd.Timestamp(last["m"].iloc[0]))
        bonds = trace_bonds.hy_benchmark(con, end.strftime("%Y-%m-%d"), window_days=window_days, cache_root=root)
    if bonds.empty:
        raise ValueError(f"TRACE benchmark empty for the window that ends {end.date()}")
    if curve_row is None:
        curve_row = treasury.curve_on(pd.Timestamp(bonds["as_of"].max()), root)
    return trace_hy_rows(bonds, curve_row)


# ================================================================ Stubs


def _stub(name: str) -> list[ForecastRow]:
    log.warning("stub: %s not licensed/available; fallback per FALLBACK_ORDER %s", name, FALLBACK_ORDER)
    return []


def load_fed_funds_futures(*_, **__) -> list[ForecastRow]:
    """Stub. Real source: CME 30-Day Federal Funds futures (ZQ) settlement prices, CME DataMine (licensed).

    Would fill: policy_rate, horizons 0..8, point = 100 - price averaged over the quarter's months, source
    "ff_futures", method "market_implied"; q10, q90 from CME options on ZQ or SOFR futures. available_at = the
    settlement date + 1 day. Fallback now: source "ust_forward" policy_rate (3-month bill forward).
    """
    return _stub("fed_funds_futures (CME)")


def load_agency_default_forecasts(*_, **__) -> list[ForecastRow]:
    """Stub. Real source: Moody's Default Report (monthly, baseline, optimistic, pessimistic forecast of the US
    speculative-grade default rate) and S&P Global Ratings default outlook (quarterly). Both are licensed.

    Would fill: default_rate, horizons 0..4, point = baseline, q10 = optimistic, q90 = pessimistic, source
    "agency_default", method "scenario_range"; available_at = the report release date + 1 day.
    """
    return _stub("agency_default_forecasts (Moody's, S&P)")


def load_ice_hy_oas(*_, **__) -> list[ForecastRow]:
    """Stub. Real source: ICE BofA US High Yield Index (H0A0) option-adjusted spread and the share of index par
    above 1,000 bp (ICE Data Indices, licensed; the public FRED copy BAMLH0A0HYM2 covers 3 years only and FRED
    blocked this machine).

    Would fill: hy_spread and distress_ratio, horizon 0, source "ice_hy_oas", method "market_implied".
    Fallback now: source "trace_hy_benchmark" (G-spread, not OAS).
    """
    return _stub("ice_hy_oas (ICE BofA H0A0)")


def load_sector_decks(*_, **__) -> list[ForecastRow]:
    """Stub. Sector forecasts by archetype (framework F2), each "<sector>:<driver>":

    - A3 energy: price decks (WTI, Henry Hub strip; EIA STEO is public, bank decks licensed) -> "energy:wti".
    - A2 healthcare: CMS reimbursement schedules (IPPS, OPPS, physician fee final rules) -> "health:rate_update".
    - A4 consumer cyclical: housing starts and auto SAAR forecasts (NAHB, Cox, S&P Mobility) -> "housing:starts".
    - Compute infrastructure: hyperscaler capex guidance and GPU utilisation -> "compute:capex", "compute:util".
    Would fill those variables, horizons 0..8, method "sector_deck"; available_at = the publication date + 1 day.
    """
    return _stub("sector_decks (energy A3, reimbursement A2, housing and auto A4, AI capex)")


def load_sellside_consensus(*_, **__) -> list[ForecastRow]:
    """Stub. Real source: LSEG I/B/E/S or FactSet Estimates detail history (licensed).

    Would fill: "<issuer>:revenue", "<issuer>:ebitda", "<issuer>:capex" per fiscal quarter, point = mean, q10 and
    q90 from the estimate distribution, and the estimate count and standard deviation (dispersion) in a side
    table; method "consensus"; available_at = the estimate's activation date + 1 day.
    """
    return _stub("sellside_consensus (I/B/E/S, FactSet)")


def load_management_guidance(*_, **__) -> list[ForecastRow]:
    """Stub. Real source: guidance in 8-K Item 2.02 exhibits and earnings call transcripts (EDGAR is public; a
    structured guidance feed such as FactSet Guidance is licensed).

    Would fill: "<issuer>:revenue", "<issuer>:ebitda", "<issuer>:capex" for the guided period, q10 = low end,
    q90 = high end, point = midpoint, method "guidance_range"; available_at = the 8-K acceptance time.
    """
    return _stub("management_guidance (8-K, transcripts)")


# ================================================================ Registry assembly


@dataclass(frozen=True)
class SourceSpec:
    name: str
    live: bool
    loader: Callable[..., list[ForecastRow]]


def _spf(dt, root, **kw):
    return load_spf(root, **kw)


def _sep(dt, root, **kw):
    return load_fomc_sep(root, **kw)


def _ust(dt, root, **kw):
    return load_ust_forwards(dt, root, **kw)


def _sloos(dt, root, **kw):
    return load_sloos(root, **kw)


def _trace(dt, root, **kw):
    return load_trace_hy(dt, root, **kw)


SOURCES: dict[str, SourceSpec] = {s.name: s for s in (
    SourceSpec("spf", True, _spf),
    SourceSpec("fomc_sep", True, _sep),
    SourceSpec("ust_forward", True, _ust),
    SourceSpec("sloos", True, _sloos),
    SourceSpec("trace_hy_benchmark", True, _trace),
    SourceSpec("fed_funds_futures", False, lambda *a, **k: load_fed_funds_futures()),
    SourceSpec("agency_default_forecasts", False, lambda *a, **k: load_agency_default_forecasts()),
    SourceSpec("ice_hy_oas", False, lambda *a, **k: load_ice_hy_oas()),
    SourceSpec("sector_decks", False, lambda *a, **k: load_sector_decks()),
    SourceSpec("sellside_consensus", False, lambda *a, **k: load_sellside_consensus()),
    SourceSpec("management_guidance", False, lambda *a, **k: load_management_guidance()),
)}

_STATUS: list[dict] = []


def load_all(decision_time, cache_root: Path | str | None = None, sources: Sequence[str] | None = None,
             options: dict[str, dict] | None = None) -> ForecastRegistry:
    """Load every source, keep rows with `available_at <= decision_time`, and return one registry.

    `options[name]` passes keyword arguments to one loader (for example {"trace_hy_benchmark": {"bonds": df}}
    or {"spf": {"fetch": fake}}). A live source that fails is logged, marked "stubbed: <reason>" in
    `source_status()`, and contributes no rows; readers then apply FALLBACK_ORDER.
    """
    t = pd.Timestamp(decision_time).to_pydatetime()
    names = list(sources) if sources is not None else list(SOURCES)
    options = options or {}
    reg = ForecastRegistry()
    _STATUS.clear()
    for name in names:
        spec = SOURCES[name]
        status = "live" if spec.live else "stub"
        try:
            rows = spec.loader(t, cache_root, **options.get(name, {}))
        except Exception as exc:
            reason = f"{type(exc).__name__}: {str(exc).splitlines()[0][:120] if str(exc) else ''}"
            log.warning("stub: %s unavailable (%s); fallback per FALLBACK_ORDER %s", name, reason, FALLBACK_ORDER)
            rows, status = [], f"stubbed: {reason}"
        kept = [r for r in rows if r.available_at <= t]
        reg.add(kept)
        last = max((r.vintage for r in kept), default=None)
        _STATUS.append({"source": name, "status": status, "last_vintage": last,
                        "last_available_at": max((r.available_at for r in kept), default=None),
                        "rows": len(kept), "rows_after_decision_time": len(rows) - len(kept)})
    return reg


def source_status() -> pd.DataFrame:
    """Table of the last `load_all` call: source, live or stub, last vintage, rows kept."""
    return pd.DataFrame(_STATUS, columns=["source", "status", "last_vintage", "last_available_at", "rows",
                                          "rows_after_decision_time"])
