"""TRACE bond reference data, daily volume-weighted quotes, and a high yield benchmark from WRDS (methodology Sections 1, 3.1, 3.6).

Tables:
- `trace.camasterfile`: one row per CUSIP and version. The current version is the row with the latest `enddt`.
- `trace.trace` (public bonds) and `trace.trace_btds144a` (144A bonds): one row per trade report.

Trade report status `trc_st`, as observed on this account: 'M' is a trade, 'N' cancels the report whose
`msg_seq_nb` equals its `orig_msg_seq_nb`, 'O' corrects that report and replaces it. We keep 'M' and 'O' rows that no
later 'N' or 'O' row references, matched on CUSIP, execution date, and message sequence number.

Volume: `ascii_rptd_vol_tx` is text. Public dissemination caps large sizes as '1MM+' and '5MM+'. We read a cap as
its floor (1,000,000 and 5,000,000), so volume weights of large trades are understated. We keep trades of at least
100,000 par: institutional size, which removes retail prints that trade away from the dealer market.

Timing: FINRA disseminates TRACE trades on the trade day, but WRDS loads them later. We set `available_at` to the
last trade date + 1 day, 00:00. This assumes a daily load; check the WRDS load lag before a live use.

Yields: `yld_pt` is the FINRA yield in percent. It is NULL for many Reg S CUSIPs (prefix 'U'). We store decimals.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Iterable, Sequence
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from hy.sources import treasury
from hy.sources.compustat_pit import SqlConnection, connect  # noqa: F401  (re-export the WRDS pattern)

MASTER_TABLE = "trace.camasterfile"
TRADE_TABLES = ("trace.trace", "trace.trace_btds144a")
MIN_PAR = 100_000
CAPPED_VOLUME = {"1MM+": 1_000_000.0, "5MM+": 5_000_000.0}
LIVE_STATUS = ("M", "O")
REPLACING_STATUS = ("N", "O")
DEFAULT_BUCKETS: tuple[tuple[float, float], ...] = ((1, 3), (3, 5), (5, 7), (7, 10), (10, 15))
DAYS_PER_YEAR = 365.25
DISSEMINATION_LAG = pd.Timedelta(days=1)


# ---------------------------------------------------------------- input validation


def _quoted(values: Iterable[str], what: str, check: Callable[[str], bool]) -> str:
    vals = sorted({str(v).upper() for v in values})
    if not vals:
        raise ValueError(f"no {what} given")
    if not all(check(v) for v in vals):
        raise ValueError(f"{what} must be alphanumeric")
    return ", ".join(f"'{v}'" for v in vals)


def _tickers_sql(tickers: Iterable[str]) -> str:
    return _quoted(tickers, "tickers", lambda v: v.replace(".", "").isalnum())


def _cusips_sql(cusips: Iterable[str]) -> str:
    return _quoted(cusips, "cusips", lambda v: v.isalnum() and len(v) == 9)


def _day(d: str | pd.Timestamp) -> str:
    """Validated 'YYYY-MM-DD' text for SQL."""
    return pd.Timestamp(d).strftime("%Y-%m-%d")


# ---------------------------------------------------------------- caching


def cache_path(root: Path, name: str, *key: Any) -> Path:
    digest = hashlib.sha1("|".join(map(str, key)).encode()).hexdigest()[:12]
    return Path(root) / "trace" / f"{name}_{digest}.parquet"


def _cached(cache_root: Path | None, refresh: bool, name: str, key: tuple, pull: Callable[[], pd.DataFrame]) -> pd.DataFrame:
    p = cache_path(cache_root, name, *key) if cache_root else None
    if p is not None and p.exists() and not refresh:
        return pd.read_parquet(p)
    out = pull()
    if p is not None:
        p.parent.mkdir(parents=True, exist_ok=True)
        out.to_parquet(p, index=False)
    return out


# ---------------------------------------------------------------- bond master


def seniority(debt_type: str | None, description: str | None, convertible: bool) -> str:
    """Seniority class from TRACE codes (Section 3.3 ranks): 'secured', 'senior_unsecured', or 'other'.

    Secured: the description says 'Secured' but not 'Unsecured', or names a lien or mortgage.
    Senior unsecured: the debt type starts with 'S-' and the bond is not convertible.
    """
    dt = debt_type.upper() if isinstance(debt_type, str) else ""
    low = description.lower() if isinstance(description, str) else ""
    if ("secured" in low and "unsecured" not in low) or "lien" in low or "mortgage" in low:
        return "secured"
    if dt.startswith("S-") and not convertible:
        return "senior_unsecured"
    return "other"


def current_version(master: pd.DataFrame) -> pd.DataFrame:
    """One row per CUSIP: the version with the latest `enddt`, ties broken by the latest `stdt`."""
    df = master.copy()
    df["enddt"] = pd.to_datetime(df["enddt"])
    df["stdt"] = pd.to_datetime(df["stdt"])
    df = df.sort_values(["cusip_id", "enddt", "stdt"])
    return df.drop_duplicates("cusip_id", keep="last").reset_index(drop=True)


def bond_master(con: SqlConnection, tickers: Sequence[str], cache_root: Path | None = None, refresh: bool = False) -> pd.DataFrame:
    """Reference data per CUSIP for the issuers `tickers` (TRACE `company_symbol`); Section 3.1 `coupon`, `maturity`."""
    tick = sorted({t.upper() for t in tickers})

    def pull() -> pd.DataFrame:
        raw = con.raw_sql(
            "select cusip_id, company_symbol, issuer_nm, scrty_ds, debt_type_cd, cpn_rt, cpn_type_cd, mtrty_dt, "
            f"ind_144a, cnvrb_fl, grade, stdt, enddt from {MASTER_TABLE} where company_symbol in ({_tickers_sql(tick)})"
        )
        cur = current_version(raw)
        conv = cur["cnvrb_fl"].astype(str).str.upper().eq("Y")
        out = pd.DataFrame(
            {
                "cusip": cur["cusip_id"].astype(str),
                "ticker": cur["company_symbol"].astype(str),
                "issuer": cur["issuer_nm"].astype("string"),
                "description": cur["scrty_ds"].astype("string"),
                "coupon": pd.to_numeric(cur["cpn_rt"], errors="coerce").astype(float) / 100.0,
                "maturity": pd.to_datetime(cur["mtrty_dt"]),
                "is_144a": cur["ind_144a"].astype(str).str.upper().eq("Y"),
                "is_convertible": conv,
                "grade": cur["grade"].astype("string"),
                "debt_type": cur["debt_type_cd"].astype("string"),
                "fixed": cur["cpn_type_cd"].astype(str).str.upper().eq("FXPV"),
                "master_stdt": cur["stdt"],
                "master_enddt": cur["enddt"],
            }
        )
        out["seniority"] = [seniority(d, s, c) for d, s, c in zip(out["debt_type"], out["description"], out["is_convertible"])]
        return out.sort_values(["ticker", "maturity", "cusip"]).reset_index(drop=True)

    return _cached(cache_root, refresh, "master", ("master", *tick), pull)


# ---------------------------------------------------------------- trades and daily quotes


def parse_volume(text: Any) -> float:
    """Par volume from `ascii_rptd_vol_tx`: '1MM+' -> 1e6, '5MM+' -> 5e6 (cap read as floor), '250000.00' -> 250000."""
    if text is None or (isinstance(text, float) and np.isnan(text)):
        return np.nan
    s = str(text).strip().upper()
    if s in CAPPED_VOLUME:
        return CAPPED_VOLUME[s]
    if s.endswith("MM+"):
        try:
            return float(s[:-3]) * 1_000_000.0
        except ValueError:
            return np.nan
    try:
        return float(s.replace(",", ""))
    except ValueError:
        return np.nan


# The same rule as `parse_volume`, in SQL. No literal percent sign: WRDS raw_sql reads it as a parameter marker.
VOLUME_SQL = (
    "case when t.ascii_rptd_vol_tx = '5MM+' then 5000000.0 "
    "when t.ascii_rptd_vol_tx = '1MM+' then 1000000.0 "
    "when right(t.ascii_rptd_vol_tx, 3) = 'MM+' and replace(t.ascii_rptd_vol_tx, 'MM+', '') ~ '^[0-9.]+$' "
    "then cast(replace(t.ascii_rptd_vol_tx, 'MM+', '') as numeric) * 1000000.0 "
    "when t.ascii_rptd_vol_tx ~ '^[0-9.]+$' then cast(t.ascii_rptd_vol_tx as numeric) end"
)
YIELD_SQL = "case when t.yld_sign_cd = '-' then -t.yld_pt else t.yld_pt end"


def _trades_ctes(where: str) -> str:
    """One CTE per trade table (`r0`, `r1`) with the reports that match `where` (alias `t`), parsed par and yield.

    Each CTE is scanned once. `_live_trades_sql` removes referenced reports with NOT IN, which Postgres runs as a hashed
    subplan: about 2 s for the 10-day high yield window, against about 350 s for a correlated NOT EXISTS.
    """
    cols = (
        f"t.cusip_id, t.trd_exctn_dt, t.msg_seq_nb, t.orig_msg_seq_nb, t.trc_st, {VOLUME_SQL} as par, "
        f"{YIELD_SQL} as yld, t.rptd_pr as pr"
    )
    return ", ".join(f"r{i} as (select {cols} from {tbl} t where {where})" for i, tbl in enumerate(TRADE_TABLES))


def _live_trades_sql() -> str:
    """Live reports from the CTEs of `_trades_ctes`: status 'M' or 'O', not cancelled or replaced, yield and price present."""
    live = ", ".join(f"'{s}'" for s in LIVE_STATUS)
    repl = ", ".join(f"'{s}'" for s in REPLACING_STATUS)
    parts = [
        f"select a.cusip_id, a.trd_exctn_dt, a.par, a.yld, a.pr from r{i} a "
        f"where a.trc_st in ({live}) and a.yld is not null and a.pr is not null "
        f"and (a.cusip_id, a.trd_exctn_dt, a.msg_seq_nb) not in (select cusip_id, trd_exctn_dt, orig_msg_seq_nb from r{i} "
        f"where trc_st in ({repl}) and orig_msg_seq_nb is not null)"
        for i in range(len(TRADE_TABLES))
    ]
    return " union all ".join(parts)


def clean_trades(trades: pd.DataFrame) -> pd.DataFrame:
    """Python form of the SQL cleaning, for raw trade rows: drop referenced reports, keep live rows, parse par."""
    t = trades.copy()
    t["trd_exctn_dt"] = pd.to_datetime(t["trd_exctn_dt"])
    rep = t[t["trc_st"].isin(REPLACING_STATUS)]
    gone = set(zip(rep["cusip_id"], rep["trd_exctn_dt"], rep["orig_msg_seq_nb"]))
    keep = t["trc_st"].isin(LIVE_STATUS) & ~pd.Series(
        [k in gone for k in zip(t["cusip_id"], t["trd_exctn_dt"], t["msg_seq_nb"])], index=t.index
    )
    t = t[keep & t["yld_pt"].notna() & t["rptd_pr"].notna()].copy()
    sign = np.where(t.get("yld_sign_cd", pd.Series(index=t.index, dtype=object)).eq("-"), -1.0, 1.0)
    t["par"] = t["ascii_rptd_vol_tx"].map(parse_volume)
    t["yld"] = sign * t["yld_pt"].astype(float)
    t["pr"] = t["rptd_pr"].astype(float)
    return t[["cusip_id", "trd_exctn_dt", "par", "yld", "pr"]]


def aggregate_daily(trades: pd.DataFrame, min_par: float = MIN_PAR) -> pd.DataFrame:
    """Python form of the SQL daily aggregation over cleaned trades (columns cusip_id, trd_exctn_dt, par, yld, pr)."""
    t = trades[trades["par"] >= min_par].copy()
    t["py"], t["pp"] = t["par"] * t["yld"], t["par"] * t["pr"]
    g = t.groupby(["cusip_id", "trd_exctn_dt"], as_index=False).agg(
        n_trades=("par", "size"), par_volume=("par", "sum"), py=("py", "sum"), pp=("pp", "sum")
    )
    g["yield_vw_pct"], g["price_vw"] = g["py"] / g["par_volume"], g["pp"] / g["par_volume"]
    return _finish_daily(g.drop(columns=["py", "pp"]))


def _finish_daily(raw: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(
        {
            "cusip": raw["cusip_id"].astype(str),
            "trade_date": pd.to_datetime(raw["trd_exctn_dt"]),
            "yield_vw": pd.to_numeric(raw["yield_vw_pct"]).astype(float) / 100.0,
            "price_vw": pd.to_numeric(raw["price_vw"]).astype(float),
            "n_trades": pd.to_numeric(raw["n_trades"]).astype(int),
            "par_volume": pd.to_numeric(raw["par_volume"]).astype(float),
        }
    )
    return out.sort_values(["cusip", "trade_date"]).reset_index(drop=True)


def bond_quotes(
    con: SqlConnection,
    cusips: Sequence[str],
    start: str,
    end: str,
    min_par: float = MIN_PAR,
    cache_root: Path | None = None,
    refresh: bool = False,
) -> pd.DataFrame:
    """Daily volume-weighted yield and price per CUSIP from institutional-size TRACE trades (Section 3.1, `trace_*`).

    yield_vw = sum(par_i * y_i) / sum(par_i) over trades with par_i >= `min_par`.
    Intuition: large trades price at the dealer market; par weights let the trades that move risk set the level.
    """
    cus, s, e = _cusips_sql(cusips), _day(start), _day(end)
    where = f"t.cusip_id in ({cus}) and t.trd_exctn_dt between '{s}' and '{e}'"

    def pull() -> pd.DataFrame:
        sql = (
            f"with {_trades_ctes(where)} "
            "select cusip_id, trd_exctn_dt, count(*) as n_trades, sum(par) as par_volume, "
            "sum(par * yld) / sum(par) as yield_vw_pct, sum(par * pr) / sum(par) as price_vw "
            f"from ({_live_trades_sql()}) x where par >= {float(min_par)} group by cusip_id, trd_exctn_dt"
        )
        return _finish_daily(con.raw_sql(sql))

    return _cached(cache_root, refresh, "quotes", (cus, s, e, float(min_par)), pull)


def latest_snapshot(quotes: pd.DataFrame, window_days: int = 10) -> pd.DataFrame:
    """Per CUSIP: volume-weighted yield and price over the `window_days` calendar days that end at its last trade.

    `as_of` is the last trade date; `available_at` is as_of + 1 day (WRDS load lag, see the module note).
    """
    q = quotes.copy()
    last = q.groupby("cusip")["trade_date"].transform("max")
    q = q[q["trade_date"] > last - pd.Timedelta(days=int(window_days))]
    q["py"], q["pp"] = q["yield_vw"] * q["par_volume"], q["price_vw"] * q["par_volume"]
    g = q.groupby("cusip", as_index=False).agg(
        py=("py", "sum"), pp=("pp", "sum"), par_volume=("par_volume", "sum"),
        n_trades=("n_trades", "sum"), n_days=("trade_date", "nunique"), as_of=("trade_date", "max"),
    )
    g["yield"], g["price"] = g["py"] / g["par_volume"], g["pp"] / g["par_volume"]
    g["available_at"] = g["as_of"] + DISSEMINATION_LAG
    return g[["cusip", "yield", "price", "n_trades", "n_days", "par_volume", "as_of", "available_at"]]


# ---------------------------------------------------------------- spreads and benchmark


def remaining_years(maturity: Any, as_of: Any) -> np.ndarray | float:
    m, a = pd.to_datetime(maturity), pd.to_datetime(as_of)
    days = (m - a) / pd.Timedelta(days=1)
    return np.asarray(days, dtype=float) / DAYS_PER_YEAR if np.ndim(days) else float(days) / DAYS_PER_YEAR


def g_spread(yld: Any, maturity: Any, as_of: Any, curve_row: pd.Series) -> np.ndarray | float:
    """G-spread = bond yield - Treasury par yield interpolated at the remaining maturity (Section 3.1, `g_spread`, p. 117).

    Intuition: the spread pays for credit risk only after the matched-tenor risk-free rate is removed.
    The curve date must not be after the latest bond date; this blocks look-ahead.
    """
    curve_date = curve_row.name
    latest = pd.to_datetime(pd.Series(np.atleast_1d(as_of))).max()
    if isinstance(curve_date, pd.Timestamp) and curve_date > latest:
        raise ValueError(f"curve date {curve_date.date()} is after the bond date {latest.date()}")
    t = remaining_years(maturity, as_of)
    out = np.asarray(yld, dtype=float) - treasury.interpolate(curve_row, t)
    return float(out) if np.ndim(out) == 0 else out


def hy_benchmark(
    con: SqlConnection,
    end: str,
    window_days: int = 10,
    min_years: float = 1.0,
    max_years: float = 15.0,
    min_par: float = MIN_PAR,
    cache_root: Path | None = None,
    refresh: bool = False,
) -> pd.DataFrame:
    """Market-wide high yield level per bond (Section 3.6, `hy_oas` proxy): VW yield over the window that ends at `end`.

    Universe: the master version in force at `end` (latest `enddt` among versions with `stdt` <= end), grade 'H',
    fixed coupon, not convertible, maturity between `min_years` and `max_years` after `end`. Aggregation runs on the
    server, so the transfer is one row per bond.
    """
    e = pd.Timestamp(_day(end))
    s = e - pd.Timedelta(days=int(window_days) - 1)
    lo = e + pd.DateOffset(days=int(round(min_years * DAYS_PER_YEAR)))
    hi = e + pd.DateOffset(days=int(round(max_years * DAYS_PER_YEAR)))
    es, ss, los, his = _day(e), _day(s), _day(lo), _day(hi)

    def pull() -> pd.DataFrame:
        universe = (
            f"select cusip_id, mtrty_dt, debt_type_cd, company_symbol from (select distinct on (cusip_id) cusip_id, mtrty_dt, "
            f"grade, cpn_type_cd, cnvrb_fl, debt_type_cd, company_symbol from {MASTER_TABLE} "
            f"where stdt <= '{es}' and enddt >= '{ss}' order by cusip_id, enddt desc, stdt desc) v "
            f"where grade = 'H' and cpn_type_cd = 'FXPV' and cnvrb_fl = 'N' and mtrty_dt between '{los}' and '{his}'"
        )
        where = f"t.trd_exctn_dt between '{ss}' and '{es}' and t.cusip_id in (select cusip_id from u)"
        sql = (
            f"with u as ({universe}), {_trades_ctes(where)} "
            "select g.*, u.mtrty_dt, u.debt_type_cd, u.company_symbol from ("
            "select x.cusip_id, max(x.trd_exctn_dt) as last_trade, count(*) as n_trades, sum(x.par) as par_volume, "
            "sum(x.par * x.yld) / sum(x.par) as yield_vw_pct, sum(x.par * x.pr) / sum(x.par) as price_vw "
            f"from ({_live_trades_sql()}) x where x.par >= {float(min_par)} group by x.cusip_id"
            ") g join u on u.cusip_id = g.cusip_id"
        )
        raw = con.raw_sql(sql)
        out = pd.DataFrame(
            {
                "cusip": raw["cusip_id"].astype(str),
                "ticker": raw["company_symbol"].astype(str),
                "debt_type": raw["debt_type_cd"].astype(str),
                "maturity": pd.to_datetime(raw["mtrty_dt"]),
                "yield": pd.to_numeric(raw["yield_vw_pct"]).astype(float) / 100.0,
                "price": pd.to_numeric(raw["price_vw"]).astype(float),
                "n_trades": pd.to_numeric(raw["n_trades"]).astype(int),
                "par_volume": pd.to_numeric(raw["par_volume"]).astype(float),
                "as_of": pd.to_datetime(raw["last_trade"]),
            }
        )
        out["available_at"] = out["as_of"] + DISSEMINATION_LAG
        return out.sort_values("cusip").reset_index(drop=True)

    return _cached(cache_root, refresh, "hy_benchmark", (es, int(window_days), min_years, max_years, float(min_par)), pull)


def benchmark_by_bucket(
    df: pd.DataFrame,
    curve_row: pd.Series,
    buckets: Sequence[tuple[float, float]] = DEFAULT_BUCKETS,
    min_price: float = 80.0,
    max_yield: float = 0.25,
    min_yield: float = 0.0,
) -> pd.DataFrame:
    """Median and interquartile range of G-spread per remaining-maturity bucket (Sections 1 and 3.6).

    Excludes distressed bonds (price < `min_price`, Section 1 universe: they trade on price, not spread, p. 122)
    and yields above `max_yield`. Yields at or below `min_yield` are print errors and drop out.
    Bucket k holds lo <= years < hi; the last bucket includes its upper end.
    """
    d = df[(df["price"] >= min_price) & (df["yield"] <= max_yield) & (df["yield"] > min_yield)].copy()
    d["years"] = remaining_years(d["maturity"], d["as_of"])
    d["g_spread"] = g_spread(d["yield"].to_numpy(), d["maturity"], d["as_of"], curve_row) if len(d) else []
    rows = []
    for i, (lo, hi) in enumerate(buckets):
        last = i == len(buckets) - 1
        sel = d[(d["years"] >= lo) & ((d["years"] <= hi) if last else (d["years"] < hi))]["g_spread"]
        q25, q50, q75 = (sel.quantile([0.25, 0.5, 0.75]).tolist() if len(sel) else [np.nan] * 3)
        rows.append({"bucket": f"{lo:g}-{hi:g}y", "lo": lo, "hi": hi, "count": int(len(sel)),
                     "median": q50, "q25": q25, "q75": q75, "iqr": q75 - q25})
    out = pd.DataFrame(rows)
    stamps = [d["available_at"].max() if len(d) else pd.NaT, pd.to_datetime(curve_row.get("available_at", pd.NaT))]
    out["as_of"] = d["as_of"].max() if len(d) else pd.NaT
    out["available_at"] = max((x for x in stamps if pd.notna(x)), default=pd.NaT)
    return out
