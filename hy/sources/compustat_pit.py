"""Compustat point-in-time quarterly data from WRDS (methodology Section 3.2).

Source table: `comp_pit.pithistdataus`. Each row is what Compustat showed at
month end `pointdate` for fiscal quarter `datadate`. A value that changes
between snapshots is a restatement. A snapshot is complete only at the end of
its month, so a value first seen at `pointdate` is available from the next day.

Two Compustat conventions matter:
1. Cash flow statement items (capex, operating cash flow, interest paid, taxes
   paid) are fiscal year-to-date. `decumulate` turns them into quarters within
   one snapshot.
2. `oibdpq` (operating income before depreciation) excludes special items.
   Reported EBITDA is therefore `oibdpq + spiq`, and `-spiq` is the add-back.
"""

from __future__ import annotations

import os
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any, Protocol

import numpy as np
import pandas as pd

LIBRARY = "comp_pit"
HIST_TABLE = "pithistdataus"
CURRENT_TABLE = "pitqtrdataus"

# Compustat stem -> (our column, year-to-date flag)
FIELDS: dict[str, tuple[str, bool]] = {
    "saleq": ("revenue", False),
    "oibdpq": ("oibdp", False),
    "spiq": ("special_items", False),
    "dpq": ("depreciation", False),
    "xintq": ("interest_expense", False),
    "txtq": ("tax_expense", False),
    "cogsq": ("cogs", False),
    "xsgaq": ("sga", False),
    "cheq": ("cash", False),
    "invtq": ("inventory", False),
    "rectq": ("receivables", False),
    "apq": ("payables", False),
    "dlcq": ("debt_current", False),
    "dlttq": ("debt_long_term", False),
    "capxq": ("capex", True),
    "oancfq": ("operating_cash_flow", True),
    "intpnq": ("interest_paid", True),
    "txpdq": ("taxes_paid", True),
}
YTD_COLUMNS = [col for col, ytd in FIELDS.values() if ytd]
VALUE_COLUMNS = [col for col, _ in FIELDS.values()]


class SqlConnection(Protocol):
    """The slice of `wrds.Connection` used here."""

    def raw_sql(self, sql: str) -> pd.DataFrame: ...


def pgpass_username(path: Path = Path.home() / ".pgpass") -> str | None:
    """WRDS user name from the `wrds-pgdata` line of ~/.pgpass, if present."""
    try:
        for line in path.read_text().splitlines():
            parts = line.split(":")
            if len(parts) >= 5 and parts[0].startswith("wrds-pgdata"):
                return parts[3]
    except OSError:
        return None
    return None


def connect(username: str | None = None) -> Any:
    """Open a WRDS connection. Auth comes from ~/.pgpass; the user name from the argument, $WRDS_USERNAME, or ~/.pgpass."""
    import wrds  # lazy: the rest of hy does not need the SDK

    user = username or os.environ.get("WRDS_USERNAME") or pgpass_username()
    if not user:
        raise RuntimeError("no WRDS user name: pass username, set WRDS_USERNAME, or add ~/.pgpass")
    return wrds.Connection(wrds_username=user)


def _in_list(values: Iterable[str]) -> str:
    vals = [str(v) for v in values]
    if not all(v.isalnum() for v in vals):
        raise ValueError("gvkeys must be alphanumeric")
    return ", ".join(f"'{v}'" for v in vals)


def lookup_issuers(con: SqlConnection, tickers: Sequence[str]) -> pd.DataFrame:
    """Map tickers to gvkey, CIK, and name: tickers from `comp.security`, CIK and name from `comp.company`."""
    tick = [t.upper() for t in tickers]
    if not all(t.replace(".", "").isalnum() for t in tick):
        raise ValueError("tickers must be alphanumeric")
    q = ", ".join(f"'{t}'" for t in tick)
    return con.raw_sql(
        "select distinct c.gvkey, s.tic, c.conm, c.cik from comp.security s "
        f"join comp.company c on c.gvkey = s.gvkey where upper(s.tic) in ({q})"
    )


def fiscal_quarters(con: SqlConnection, gvkeys: Sequence[str]) -> pd.DataFrame:
    """Fiscal quarter number and earnings report date per (gvkey, datadate), from the current-view table."""
    sql = (
        f"select gvkey, datadate, fqtr, rdqe from {LIBRARY}.{CURRENT_TABLE} "
        f"where gvkey in ({_in_list(gvkeys)})"
    )
    out = con.raw_sql(sql)
    out["datadate"] = pd.to_datetime(out["datadate"])
    out["rdqe"] = pd.to_datetime(out["rdqe"])
    return out.drop_duplicates(["gvkey", "datadate"])


def pull_history(
    con: SqlConnection,
    gvkeys: Sequence[str],
    start: str,
    end: str,
    max_quarters_back: int = 8,
) -> pd.DataFrame:
    """Every monthly snapshot of the selected fields for `gvkeys` between `start` and `end` (pointdate)."""
    cols = ", ".join(f"{stem}h as {name}" for stem, (name, _) in FIELDS.items())
    sql = (
        f"select gvkey, pointdate, datadate, qtrsback, {cols} from {LIBRARY}.{HIST_TABLE} "
        f"where gvkey in ({_in_list(gvkeys)}) and pointdate between '{start}' and '{end}' "
        f"and qtrsback <= {int(max_quarters_back)}"
    )
    out = con.raw_sql(sql)
    out["pointdate"] = pd.to_datetime(out["pointdate"])
    out["datadate"] = pd.to_datetime(out["datadate"])
    return out


def pull_current(con: SqlConnection, gvkeys: Sequence[str], start: str, end: str) -> pd.DataFrame:
    """Latest-known values per (gvkey, datadate) from the current-view table, shaped like one snapshot.

    These values include later restatements, so they are not point in time. Use them only to fill quarters that
    the history table lacks, and keep them flagged (`pit_exact = False`).
    """
    cols = ", ".join(f"{stem} as {name}" for stem, (name, _) in FIELDS.items())
    sql = (
        f"select gvkey, datadate, {cols} from {LIBRARY}.{CURRENT_TABLE} "
        f"where gvkey in ({_in_list(gvkeys)}) and datadate between '{start}' and '{end}'"
    )
    out = con.raw_sql(sql)
    out["datadate"] = pd.to_datetime(out["datadate"])
    out["pointdate"] = pd.NaT
    out["qtrsback"] = 0
    return out


def decumulate(snap: pd.DataFrame, fq: pd.DataFrame) -> pd.DataFrame:
    """Turn year-to-date cash flow items into quarterly flows within each snapshot.

    Q1 = YTD1; Qn = YTDn - YTD(n-1) when quarter n-1 of the same fiscal year is in the same snapshot, else NaN.
    Intuition: Compustat reports the cash flow statement as filed, and filers report it year to date.
    """
    df = snap.merge(fq[["gvkey", "datadate", "fqtr"]], on=["gvkey", "datadate"], how="left")
    df = df.sort_values(["gvkey", "pointdate", "datadate"]).reset_index(drop=True)
    grp = df.groupby(["gvkey", "pointdate"], sort=False, dropna=False)
    prev_fqtr = grp["fqtr"].shift(1)
    prev_date = grp["datadate"].shift(1)
    consecutive = (prev_fqtr == df["fqtr"] - 1) & ((df["datadate"] - prev_date).dt.days.between(80, 100))
    for col in YTD_COLUMNS:
        prev = grp[col].shift(1)
        q = np.where(df["fqtr"] == 1, df[col], np.where(consecutive, df[col] - prev, np.nan))
        df[col] = q
    return df


def build_vintages(snap: pd.DataFrame) -> pd.DataFrame:
    """One row per (gvkey, datadate, version): keep a snapshot only when its values differ from the last kept one.

    `snapshot_available_at` is the day after `pointdate`, because a month-end snapshot is complete only at month end.
    `vintage` is 0 for the first version and counts restatements after it.
    """
    df = snap.sort_values(["gvkey", "datadate", "pointdate"]).reset_index(drop=True)
    vals = df[VALUE_COLUMNS].astype(float).round(6).fillna(-9.99e18)
    key = df["gvkey"].astype(str) + "|" + df["datadate"].astype(str)
    changed = (vals != vals.groupby(key).shift(1)).any(axis=1)
    out = df.loc[changed].copy()
    out["snapshot_available_at"] = out["pointdate"] + pd.Timedelta(1, unit="D")
    out["vintage"] = out.groupby(["gvkey", "datadate"]).cumcount()
    return out.drop(columns=["qtrsback"], errors="ignore").reset_index(drop=True)


def cache_path(root: Path, gvkey: str, start: str, end: str) -> Path:
    return root / "compustat_pit" / f"{gvkey}_{start}_{end}.parquet"


def load_vintages(
    con: SqlConnection,
    gvkeys: Sequence[str],
    start: str,
    end: str,
    cache_root: Path | None = None,
    refresh: bool = False,
    max_quarters_back: int = 8,
) -> pd.DataFrame:
    """Pull, de-cumulate, and version Compustat PIT data; cache one parquet file per gvkey and window under `cache_root`.

    The pull reaches 3 quarters past `max_quarters_back` so that every kept quarter has its fiscal-year
    predecessors for de-cumulation; the extra rows are dropped before versioning.
    """
    frames, todo = [], []
    for g in gvkeys:
        p = cache_path(cache_root, g, start, end) if cache_root else None
        if p is not None and p.exists() and not refresh:
            frames.append(pd.read_parquet(p))
        else:
            todo.append(g)
    if todo:
        snap = pull_history(con, todo, start, end, max_quarters_back=max_quarters_back + 3)
        fq = fiscal_quarters(con, todo)
        flows = decumulate(snap, fq)
        vint = build_vintages(flows[flows["qtrsback"] <= max_quarters_back])
        vint["pit_exact"] = True
        cur = decumulate(pull_current(con, todo, start, end), fq)
        seen = set(zip(vint["gvkey"], vint["datadate"]))
        gap = cur[[(g, d) not in seen for g, d in zip(cur["gvkey"], cur["datadate"])]].copy()
        gap = gap.drop(columns=["qtrsback", "pointdate", "fqtr"], errors="ignore")
        gap["snapshot_available_at"] = pd.NaT
        gap["vintage"] = 0
        gap["pit_exact"] = False
        vint = pd.concat([vint.drop(columns=["fqtr", "pointdate"], errors="ignore"), gap], ignore_index=True)
        vint = vint.merge(fq[["gvkey", "datadate", "rdqe"]], on=["gvkey", "datadate"], how="left")
        if cache_root:
            for g, part in vint.groupby("gvkey"):
                p = cache_path(cache_root, str(g), start, end)
                p.parent.mkdir(parents=True, exist_ok=True)
                part.to_parquet(p, index=False)
        frames.append(vint)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
