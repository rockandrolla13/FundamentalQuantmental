"""Sector and rating history for peer groups (methodology Section 7.2; decision page 2026-10-22-esp-peer-groups).

Two WRDS tables, both point in time:

1. `comp.co_hgic`: GICS history per gvkey with `indfrom` and `indthru`. The sector at t is the row with
   indfrom <= t and (indthru is null or indthru >= t). GICS is public on `indfrom`, so `available_at` = indfrom.
2. `comp.adsprate`: S&P long-term issuer credit rating (`splticrm`) per gvkey and month end. It ends in
   February 2017. The rating at month end t is public by t, so `available_at` = datadate + 1 day (the WRDS load
   lag used in `trace_panel`).

Mergent FISD and Capital IQ ratings are not in the licence; `comp_ratings.erating` ends in August 2012. So no rating
source covers March 2017 onward. `hy.peers` fills that gap with a rating class implied by leverage.
Each pull is cached as parquet under data/raw/backtest/.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

import pandas as pd

from hy.sources.compustat_pit import _in_list

CACHE = Path(__file__).resolve().parents[2] / "data/raw/backtest"


def _chunks(xs: Sequence[str], n: int = 500):
    for i in range(0, len(xs), n):
        yield xs[i:i + n]


def gics_history(con: Any, gvkeys: Sequence[str], refresh: bool = False) -> pd.DataFrame:
    """GICS sector, group and industry history per gvkey (columns gvkey, gsector, ggroup, gind, indfrom, indthru,
    available_at). Cached at data/raw/backtest/gics_history.parquet."""
    path = CACHE / "gics_history.parquet"
    if path.exists() and not refresh:
        return pd.read_parquet(path)
    keys = sorted({str(g) for g in gvkeys if g})
    parts = [con.raw_sql("select gvkey, gsector, ggroup, gind, indfrom, indthru from comp.co_hgic "
                         f"where indtype = 'GICS' and gvkey in ({_in_list(c)})") for c in _chunks(keys)]
    out = pd.concat(parts, ignore_index=True)
    out["indfrom"] = pd.to_datetime(out["indfrom"])
    out["indthru"] = pd.to_datetime(out["indthru"])
    out["available_at"] = out["indfrom"]
    out.to_parquet(path)
    return out


def sp_ratings(con: Any, gvkeys: Sequence[str], refresh: bool = False) -> pd.DataFrame:
    """S&P long-term issuer rating per gvkey and month end, 2007 onward (columns gvkey, datadate, splticrm,
    available_at). Cached at data/raw/backtest/sp_ratings.parquet."""
    path = CACHE / "sp_ratings.parquet"
    if path.exists() and not refresh:
        return pd.read_parquet(path)
    keys = sorted({str(g) for g in gvkeys if g})
    parts = [con.raw_sql("select gvkey, datadate, splticrm from comp.adsprate where datadate >= '2007-01-01' "
                         f"and splticrm is not null and gvkey in ({_in_list(c)})") for c in _chunks(keys)]
    out = pd.concat(parts, ignore_index=True)
    out["datadate"] = pd.to_datetime(out["datadate"])
    out["available_at"] = out["datadate"] + pd.Timedelta(days=1)
    out.to_parquet(path)
    return out


ANNUAL_LAG_DAYS = 90            # a 10-K is public at most 90 days after fiscal year end (large filers: 60 to 75)


def annual_ebitda(con: Any, gvkeys: Sequence[str], refresh: bool = False) -> pd.DataFrame:
    """Annual EBITDA (OIBDP) and debt per gvkey and fiscal year, 1996 onward, for sustainable EBITDA (Dynkin et al.
    2021, ch. 14: the average of the last 10 annual EBITDA figures, at least 6). Columns gvkey, datadate, fyear,
    oibdp, debt, available_at. Cached at data/raw/backtest/annual_ebitda.parquet.

    `comp.funda` is the current view, not point in time: a later restatement can replace an old year. The 10-year
    average damps that. `available_at` = datadate + ANNUAL_LAG_DAYS, the latest filing date for a 10-K.
    """
    path = CACHE / "annual_ebitda.parquet"
    keys = sorted({str(g) for g in gvkeys if g})
    cached = pd.read_parquet(path) if path.exists() and not refresh else None
    if cached is not None:
        keys = sorted(set(keys) - set(cached["gvkey"]))   # pull only the gvkeys not yet cached
        if not keys or con is None:
            return cached
    parts = [con.raw_sql("select gvkey, datadate, fyear, oibdp, dlc, dltt from comp.funda "
                         "where indfmt = 'INDL' and datafmt = 'STD' and popsrc = 'D' and consol = 'C' "
                         f"and datadate >= '1996-01-01' and gvkey in ({_in_list(c)})") for c in _chunks(keys)]
    out = pd.concat(parts, ignore_index=True)
    out["datadate"] = pd.to_datetime(out["datadate"])
    for c in ("oibdp", "dlc", "dltt", "fyear"):
        out[c] = out[c].astype("float64")
    out["debt"] = out["dlc"].fillna(0.0) + out["dltt"].fillna(0.0)
    out["debt"] = out["debt"].where(out["dlc"].notna() | out["dltt"].notna())
    out = out.sort_values(["gvkey", "datadate"]).drop_duplicates(["gvkey", "fyear"], keep="last")
    out["available_at"] = out["datadate"] + pd.Timedelta(days=ANNUAL_LAG_DAYS)
    out = out.drop(columns=["dlc", "dltt"])
    if cached is not None:
        out = pd.concat([cached, out], ignore_index=True)
    out.to_parquet(path)
    return out
