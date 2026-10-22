"""US Treasury par yield curve from the public Treasury CSV (methodology Sections 1, 3.1 and 3.6, field `ust_curve`).

The risk-free rate is the first price driver (Section 1, p. 113). The G-spread is the bond yield minus the Treasury
par yield at the same remaining maturity (Section 3.1, `g_spread`).

Assumptions:
1. Treasury publishes the daily par curve in the late afternoon of the curve date. We do not record the exact hour,
   so a curve for date d is available at d + 1 day, 00:00. This is end-of-day publication: it removes look-ahead
   at the cost of at most one day of lag.
2. Yields in the CSV are percent, bond-equivalent (semiannual). We store decimals.
3. Interpolation is linear in tenor and flat beyond the shortest and longest tenor.
"""

from __future__ import annotations

import io
import os
import urllib.request
from collections.abc import Callable
from pathlib import Path

import numpy as np
import pandas as pd

URL = (
    "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/{year}/all"
    "?type=daily_treasury_yield_curve&field_tdr_date_value={year}&page&_format=csv"
)

# CSV column -> tenor in years
TENORS: dict[str, float] = {
    "1 Mo": 1 / 12,
    "1.5 Month": 1.5 / 12,
    "2 Mo": 2 / 12,
    "3 Mo": 0.25,
    "4 Mo": 4 / 12,
    "6 Mo": 0.5,
    "1 Yr": 1.0,
    "2 Yr": 2.0,
    "3 Yr": 3.0,
    "5 Yr": 5.0,
    "7 Yr": 7.0,
    "10 Yr": 10.0,
    "20 Yr": 20.0,
    "30 Yr": 30.0,
}
TENOR_COLUMNS = list(TENORS.values())
PUBLICATION_LAG = pd.Timedelta(1, unit="D")


def fetch_url(url: str) -> str:
    """GET `url` as text. Treasury rejects requests without a User-Agent, so send $SEC_USER_AGENT or a generic one."""
    agent = os.environ.get("SEC_USER_AGENT") or "Mozilla/5.0 (FundamentalQuantmental research)"
    req = urllib.request.Request(url, headers={"User-Agent": agent})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8")


def parse_csv(text: str) -> pd.DataFrame:
    """Parse one Treasury CSV: index `as_of` (ascending), float tenor columns in years, decimal yields, `available_at`."""
    raw = pd.read_csv(io.StringIO(text))
    out = pd.DataFrame(index=pd.to_datetime(raw["Date"], format="%m/%d/%Y"))
    for col, tenor in TENORS.items():
        out[tenor] = pd.to_numeric(raw[col], errors="coerce").to_numpy() / 100.0 if col in raw else np.nan
    out.index.name = "as_of"
    out = out.sort_index()
    out["available_at"] = out.index + PUBLICATION_LAG
    return out


def cache_path(root: Path, year: int) -> Path:
    return Path(root) / "treasury" / f"par_curve_{int(year)}.csv"


def par_curve(
    year: int,
    cache_root: Path | None = None,
    fetch: Callable[[str], str] = fetch_url,
    refresh: bool = False,
) -> pd.DataFrame:
    """Daily par yield curve for one calendar year (Section 3.6, `ust_curve`); cache the raw CSV under cache_root/treasury/."""
    year = int(year)
    p = cache_path(cache_root, year) if cache_root else None
    if p is not None and p.exists() and not refresh:
        text = p.read_text()
    else:
        text = fetch(URL.format(year=year))
        if p is not None:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text)
    return parse_csv(text)


def curve_on(
    date: str | pd.Timestamp,
    cache_root: Path | None = None,
    fetch: Callable[[str], str] = fetch_url,
    refresh: bool = False,
) -> pd.Series:
    """Latest curve with curve date <= `date` (no look-ahead). The row name is its curve date; it carries `available_at`.

    A cached file for the current year can end before `date`; then the year is fetched again once.
    The previous year covers the first business days of January.
    """
    target = pd.Timestamp(date).normalize()
    curves = par_curve(target.year, cache_root, fetch, refresh)
    if (curves.empty or curves.index.max() < target) and not refresh and cache_root is not None:
        curves = par_curve(target.year, cache_root, fetch, refresh=True)
    eligible = curves[curves.index <= target]
    if eligible.empty:
        eligible = par_curve(target.year - 1, cache_root, fetch, refresh)
        eligible = eligible[eligible.index <= target]
    if eligible.empty:
        raise ValueError(f"no Treasury curve on or before {target.date()}")
    return eligible.iloc[-1]


def interpolate(curve_row: pd.Series, tenor_years: float | np.ndarray) -> float | np.ndarray:
    """Par yield at `tenor_years`: linear in tenor between curve points, flat beyond the ends (Section 3.1, `g_spread`).

    Intuition: the matched-tenor Treasury (p. 117) is the straight line between the two nearest quoted tenors.
    """
    pts = pd.to_numeric(curve_row[[k for k in curve_row.index if isinstance(k, float)]], errors="coerce").dropna()
    if pts.empty:
        raise ValueError("curve row has no tenor points")
    pts = pts.sort_index()
    out = np.interp(np.asarray(tenor_years, dtype=float), pts.index.to_numpy(dtype=float), pts.to_numpy(dtype=float))
    return float(out) if np.ndim(out) == 0 else out
