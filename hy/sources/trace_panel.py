"""Monthly high yield bond panel from TRACE, issuer link to Compustat, and point-in-time leverage (methodology Sections 3.1, 3.2, 11).

The backtest of Section 11 needs, for every month end t from 2008: each high yield bond's price, yield, G-spread, a
bid-ask proxy, and the issuer's leverage as known at t. This module builds that panel. Aggregation runs on the WRDS
server, one query per month, so the transfer is one row per bond and month. Each month is cached as parquet.

Rules (each one is a decision, stated so a reader can change it):

1. Universe per month. The `trace.camasterfile` version in force at the month end (the version with the latest
   `enddt` among versions with `stdt <= t` and `enddt >=` the window start). We do not use today's master, so a bond
   that is upgraded or downgraded later is classed as it was then. Keep grade 'H', coupon type 'FXPV' (fixed, plain
   vanilla), not convertible, maturity after t.
2. Trades. Status codes changed twice. Before February 2012: 'T' trade, 'C' cancel, 'W' correction. 2012 to
   mid-2012 transition files: 'G' trade, 'H' cancel, 'I' correction. After: 'M' trade, 'N' cancel, 'O' correction.
   A cancel or a correction removes the report whose `msg_seq_nb` equals its `orig_msg_seq_nb` (same CUSIP and
   execution date). A correction row is itself a live trade. Reversals (`asof_cd = 'R'`) are dropped; the report they
   reverse is not matched (a small error, stated). Institutional size only: par >= 100,000 (see `trace_bonds`).
3. Window. The last `WINDOW_DAYS` = 7 calendar days of the month. Price and yield are par-weighted means over the
   window. Price uses every live trade with a price; yield uses the trades with a yield. A bond in default trades
   flat and often has no yield; it stays in the panel on its price.
4. Bid-ask proxy, in price points. Primary: par-weighted price of dealer sales to customers minus dealer purchases
   from customers in the window (the `side` field, populated from about 2012). Fallback: the mean intraday high-low
   price range on days with two or more institutional trades. The fallback overstates the spread when the price
   moves during the day, so it is conservative for costs.
5. Survivorship. A bond that stops trading before the panel end stays in: one extra row in the month after its last
   observation carries its last price forward (`carried = True`), then it leaves. A bond that matures before that
   month redeems at 100. The extra row exists only to end the bond's return; no predictor sees it.
6. Timing. `available_at` = last trade date in the window + 1 day (WRDS load lag, as in `trace_bonds`). The Treasury
   curve is the latest one with curve date <= t (`treasury.curve_on`), available the next day. The decision time for
   month t is t + 1 day, so every field of the row is known by then.

Issuer link: bond CUSIP first six characters (the issuer number) to `comp.security.cusip` first six characters, then
TRACE `company_symbol` to `comp.security.tic` where the first rule fails. Leverage: Compustat point-in-time history
(`compustat_pit.load_vintages`). The history table has no lease liability field, so leverage is plain
(debt current + debt long term) / LTM EBITDA before special items, flagged `lev_basis = 'plain'`.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.optimize import brentq

from hy import rv
from hy.sources import compustat_pit as cp
from hy.sources import trace_bonds as tb
from hy.sources import treasury as tr

WINDOW_DAYS = 7
MIN_PAR = tb.MIN_PAR
TRADE_STATUS = ("T", "G", "M")
CANCEL_STATUS = ("C", "H", "N")
CORRECT_STATUS = ("W", "I", "O")
LIVE_STATUS = TRADE_STATUS + CORRECT_STATUS
REPLACING_STATUS = CANCEL_STATUS + CORRECT_STATUS
FLAT_PRICE = 50.0       # below this price a bond is treated as trading flat (no coupon accrual)
LEV_CAP = 20.0          # leverage ceiling; EBITDA <= 0 with debt > 0 maps here
MAX_STALE_DAYS = 270    # a fiscal quarter older than this at t is too old to use
PANEL_COLUMNS = [
    "date", "cusip", "cusip6", "ticker", "coupon", "maturity", "years", "price", "yield", "yield_source",
    "g_spread", "tsy_yield", "mod_dur", "n_trades", "par_volume", "bid_ask_pts", "bid_ask_source", "last_trade",
    "available_at", "carried", "accrue_to", "hedge_date",
]


def _sql_list(values: Sequence[str]) -> str:
    vals = [str(v) for v in values]
    if not all(v.isalnum() for v in vals):
        raise ValueError("status codes must be alphanumeric")
    return ", ".join(f"'{v}'" for v in vals)


# ---------------------------------------------------------------- server-side monthly aggregate


def window(month_end: Any, window_days: int = WINDOW_DAYS) -> tuple[str, str]:
    """('YYYY-MM-DD' start, end) of the last `window_days` calendar days of the month that contains `month_end`."""
    e = pd.Timestamp(month_end) + pd.offsets.MonthEnd(0)
    s = e - pd.Timedelta(days=int(window_days) - 1)
    return s.strftime("%Y-%m-%d"), e.strftime("%Y-%m-%d")


def month_sql(month_end: Any, window_days: int = WINDOW_DAYS, min_par: float = MIN_PAR) -> str:
    """SQL for one month: one row per bond in the month's grade-H universe that has an institutional trade in the window.

    No literal percent sign appears (WRDS `raw_sql` reads it as a parameter marker).
    """
    ss, es = window(month_end, window_days)
    universe = (
        "select cusip_id, mtrty_dt, cpn_rt, company_symbol from (select distinct on (cusip_id) cusip_id, mtrty_dt, "
        f"cpn_rt, grade, cpn_type_cd, cnvrb_fl, company_symbol from {tb.MASTER_TABLE} "
        f"where stdt <= '{es}' and enddt >= '{ss}' order by cusip_id, enddt desc, stdt desc) v "
        f"where grade = 'H' and cpn_type_cd = 'FXPV' and cnvrb_fl = 'N' and mtrty_dt > '{es}'"
    )
    cols = (
        f"t.cusip_id, t.trd_exctn_dt, t.msg_seq_nb, t.orig_msg_seq_nb, t.trc_st, t.asof_cd, {tb.VOLUME_SQL} as par, "
        f"{tb.YIELD_SQL} as yld, t.rptd_pr as pr, t.side, t.contra_party_type as cpt"
    )
    where = f"t.trd_exctn_dt between '{ss}' and '{es}' and t.cusip_id in (select cusip_id from u)"
    ctes = ", ".join(f"r{i} as (select {cols} from {tbl} t where {where})" for i, tbl in enumerate(tb.TRADE_TABLES))
    live = " union all ".join(
        f"select a.cusip_id, a.trd_exctn_dt, a.par, a.yld, a.pr, a.side, a.cpt from r{i} a "
        f"where a.trc_st in ({_sql_list(LIVE_STATUS)}) and a.pr is not null and coalesce(a.asof_cd, '') <> 'R' "
        f"and (a.cusip_id, a.trd_exctn_dt, a.msg_seq_nb) not in (select cusip_id, trd_exctn_dt, orig_msg_seq_nb from r{i} "
        f"where trc_st in ({_sql_list(REPLACING_STATUS)}) and orig_msg_seq_nb is not null)"
        for i in range(len(tb.TRADE_TABLES))
    )
    sell = "x.cpt = 'C' and x.side = 'S'"
    buy = "x.cpt = 'C' and x.side = 'B'"
    return (
        f"with u as ({universe}), {ctes}, x as (select * from ({live}) z where par >= {float(min_par)}), "
        "d as (select cusip_id, trd_exctn_dt, max(pr) - min(pr) as rng, count(*) as n from x group by 1, 2), "
        "dr as (select cusip_id, avg(rng) as day_range from d where n >= 2 group by 1), "
        "g as (select x.cusip_id, max(x.trd_exctn_dt) as last_trade, count(*) as n_trades, sum(x.par) as par_volume, "
        "sum(x.par * x.pr) / sum(x.par) as price_vw, "
        "sum(case when x.yld is not null then x.par * x.yld end) / nullif(sum(case when x.yld is not null then x.par end), 0) "
        "as yield_vw_pct, "
        f"sum(case when {sell} then x.par * x.pr end) / nullif(sum(case when {sell} then x.par end), 0) as px_dealer_sell, "
        f"sum(case when {buy} then x.par * x.pr end) / nullif(sum(case when {buy} then x.par end), 0) as px_dealer_buy "
        "from x group by x.cusip_id) "
        "select g.*, dr.day_range, u.mtrty_dt, u.cpn_rt, u.company_symbol from g join u on u.cusip_id = g.cusip_id "
        "left join dr on dr.cusip_id = g.cusip_id"
    )


# ---------------------------------------------------------------- the same rules in Python (tests, small samples)


def clean_trades(trades: pd.DataFrame) -> pd.DataFrame:
    """Python form of the SQL cleaning over raw report rows of any TRACE era.

    Drop reports that a cancel or correction references, drop cancels and reversals, parse par from text, keep rows
    with a price. Input columns: cusip_id, trd_exctn_dt, msg_seq_nb, orig_msg_seq_nb, trc_st, ascii_rptd_vol_tx,
    rptd_pr, optional yld_pt, yld_sign_cd, asof_cd, side, contra_party_type.
    """
    t = trades.copy()
    t["trd_exctn_dt"] = pd.to_datetime(t["trd_exctn_dt"])
    rep = t[t["trc_st"].isin(REPLACING_STATUS) & t["orig_msg_seq_nb"].notna()]
    gone = set(zip(rep["cusip_id"], rep["trd_exctn_dt"], rep["orig_msg_seq_nb"]))
    hit = pd.Series([k in gone for k in zip(t["cusip_id"], t["trd_exctn_dt"], t["msg_seq_nb"])], index=t.index)
    reversal = t["asof_cd"].eq("R") if "asof_cd" in t else pd.Series(False, index=t.index)
    keep = t["trc_st"].isin(LIVE_STATUS) & ~hit & ~reversal & t["rptd_pr"].notna()
    t = t[keep].copy()
    sign = np.where(t["yld_sign_cd"].eq("-"), -1.0, 1.0) if "yld_sign_cd" in t else 1.0
    t["par"] = t["ascii_rptd_vol_tx"].map(tb.parse_volume)
    t["yld"] = sign * pd.to_numeric(t["yld_pt"], errors="coerce") if "yld_pt" in t else np.nan
    t["pr"] = t["rptd_pr"].astype(float)
    t["side"] = t["side"] if "side" in t else None
    t["cpt"] = t["contra_party_type"] if "contra_party_type" in t else None
    return t[["cusip_id", "trd_exctn_dt", "par", "yld", "pr", "side", "cpt"]].reset_index(drop=True)


def aggregate_window(trades: pd.DataFrame, min_par: float = MIN_PAR) -> pd.DataFrame:
    """Python form of the SQL monthly aggregate over cleaned trades of one window (output columns as `month_sql`)."""
    x = trades[trades["par"] >= min_par].copy()
    rows = []
    for cusip, g in x.groupby("cusip_id"):
        y = g[g["yld"].notna()]
        sell = g[(g["cpt"] == "C") & (g["side"] == "S")]
        buy = g[(g["cpt"] == "C") & (g["side"] == "B")]
        d = g.groupby("trd_exctn_dt")["pr"].agg(["max", "min", "size"])
        d = d[d["size"] >= 2]
        rows.append({
            "cusip_id": cusip, "last_trade": g["trd_exctn_dt"].max(), "n_trades": len(g), "par_volume": g["par"].sum(),
            "price_vw": np.average(g["pr"], weights=g["par"]),
            "yield_vw_pct": np.average(y["yld"], weights=y["par"]) if len(y) else np.nan,
            "px_dealer_sell": np.average(sell["pr"], weights=sell["par"]) if len(sell) else np.nan,
            "px_dealer_buy": np.average(buy["pr"], weights=buy["par"]) if len(buy) else np.nan,
            "day_range": (d["max"] - d["min"]).mean() if len(d) else np.nan,
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- bond math


def price_from_yield(ytm: float, coupon: float, maturity: float, freq: int = 2) -> float:
    """Clean price per 100 of a fixed-coupon bullet at `ytm`, cash flows on the `rv.modified_duration` grid."""
    if maturity <= 0:
        return 100.0
    n = max(1, int(np.ceil(maturity * freq)))
    t = maturity - (n - np.arange(1, n + 1)) / freq
    cf = np.full(n, coupon / freq * 100.0)
    cf[-1] += 100.0
    return float((cf * (1 + ytm / freq) ** (-t * freq)).sum())


def yield_from_price(price: float, coupon: float, maturity: float) -> float:
    """Yield that reprices the bullet to `price`; NaN when no root lies in (-50%, 300%).

    Used only where TRACE gives no yield (flat-trading bonds). Intuition: the yield a buyer at that price earns if
    every coupon is paid.
    """
    if not (np.isfinite(price) and price > 0 and np.isfinite(coupon) and maturity > 0):
        return float("nan")
    f = lambda y: price_from_yield(y, coupon, maturity) - price  # noqa: E731
    try:
        return float(brentq(f, -0.5, 3.0, xtol=1e-8))
    except ValueError:
        return float("nan")


# ---------------------------------------------------------------- panel assembly


def bid_ask_points(raw: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Rule 4: dealer-sell minus dealer-buy price where both exist and the gap is positive, else the day range."""
    side = raw["px_dealer_sell"].astype(float) - raw["px_dealer_buy"].astype(float)
    rng = raw["day_range"].astype(float)
    use_side = side.notna() & (side > 0)
    out = side.where(use_side, rng)
    src = pd.Series(np.where(use_side, "side", np.where(rng.notna(), "day_range", "none")), index=raw.index)
    return out.clip(lower=0.0, upper=10.0), src


def finish_month(raw: pd.DataFrame, month_end: Any, curve_row: pd.Series) -> pd.DataFrame:
    """Turn one month's server rows into panel rows: units, yields (filled from price), G-spread, duration, bid-ask.

    The curve must be dated on or before the month end (checked).
    """
    t = pd.Timestamp(month_end) + pd.offsets.MonthEnd(0)
    if isinstance(curve_row.name, pd.Timestamp) and curve_row.name > t:
        raise ValueError(f"curve date {curve_row.name.date()} is after month end {t.date()}")
    if raw is None or raw.empty:
        return pd.DataFrame(columns=PANEL_COLUMNS)
    out = pd.DataFrame({
        "date": t,
        "cusip": raw["cusip_id"].astype(str).to_numpy(),
        "ticker": raw["company_symbol"].astype(str).to_numpy(),
        "coupon": pd.to_numeric(raw["cpn_rt"], errors="coerce").astype(float).to_numpy() / 100.0,
        "maturity": pd.to_datetime(raw["mtrty_dt"], errors="coerce").to_numpy(),  # perpetuals (3999) -> NaT
        "price": pd.to_numeric(raw["price_vw"]).astype(float).to_numpy(),
        "yield": pd.to_numeric(raw["yield_vw_pct"]).astype(float).to_numpy() / 100.0,
        "n_trades": pd.to_numeric(raw["n_trades"]).astype(int).to_numpy(),
        "par_volume": pd.to_numeric(raw["par_volume"]).astype(float).to_numpy(),
        "last_trade": pd.to_datetime(raw["last_trade"]).to_numpy(),
    })
    out["cusip6"] = out["cusip"].str[:6]
    out["years"] = (out["maturity"] - t).dt.days / tb.DAYS_PER_YEAR
    out["coupon"] = out["coupon"].fillna(0.0)
    has_y = out["yield"].notna()
    out["yield_source"] = np.where(has_y, "trace", "from_price")
    fill = [yield_from_price(p, c, m) for p, c, m in zip(out.loc[~has_y, "price"], out.loc[~has_y, "coupon"],
                                                          out.loc[~has_y, "years"])]
    out.loc[~has_y, "yield"] = fill
    out["tsy_yield"] = tr.interpolate(curve_row, out["years"].clip(lower=0.0).to_numpy())
    out["g_spread"] = out["yield"] - out["tsy_yield"]
    out["mod_dur"] = [rv.modified_duration(y, c, m) if np.isfinite(y) and np.isfinite(m) and y > -0.5 else np.nan
                      for y, c, m in zip(out["yield"], out["coupon"], out["years"])]
    ba, src = bid_ask_points(raw.reset_index(drop=True))
    out["bid_ask_pts"], out["bid_ask_source"] = ba.to_numpy(), src.to_numpy()
    out["available_at"] = out["last_trade"] + tb.DISSEMINATION_LAG
    out["carried"] = False
    out["accrue_to"] = t
    out["hedge_date"] = t
    return out[PANEL_COLUMNS]


def add_exit_rows(panel: pd.DataFrame) -> pd.DataFrame:
    """Rule 5 (survivorship): one carried row in the month after each bond's last observation, then it leaves.

    The carried row repeats the last price (or 100 when the bond matured in between), keeps the last row's Treasury
    yield and benchmark date (`hedge_date`), and stops coupon accrual at the last trade (`accrue_to`). So the bond's
    return ends where its prices end, and the hedge ends with it. No row is added after the panel's last month.
    """
    p = panel[~panel["carried"]].sort_values(["cusip", "date"])
    last_month = p["date"].max()
    last = p.groupby("cusip").tail(1)
    last = last[last["date"] < last_month].copy()
    if last.empty:
        return panel.reset_index(drop=True)
    nxt = last["date"] + pd.offsets.MonthEnd(1)
    matured = last["maturity"] <= nxt
    ex = last.copy()
    ex["date"] = nxt
    ex["carried"] = True
    ex["price"] = np.where(matured, 100.0, last["price"])
    ex["accrue_to"] = np.where(matured, last["maturity"], last["last_trade"])
    ex["hedge_date"] = last["date"]
    ex["years"] = (ex["maturity"] - ex["date"]).dt.days / tb.DAYS_PER_YEAR
    ex["available_at"] = ex["date"] + pd.Timedelta(days=1)
    out = pd.concat([panel, ex[panel.columns]], ignore_index=True)
    return out.sort_values(["date", "cusip"]).reset_index(drop=True)


def month_cache_path(root: Path, month_end: Any) -> Path:
    t = pd.Timestamp(month_end) + pd.offsets.MonthEnd(0)
    return Path(root) / "trace_panel" / f"month_{t:%Y-%m}.parquet"


def pull_month(con: cp.SqlConnection, month_end: Any, cache_root: Path | None = None, refresh: bool = False) -> pd.DataFrame:
    """Server rows for one month (cached raw, before `finish_month`)."""
    p = month_cache_path(cache_root, month_end) if cache_root else None
    if p is not None and p.exists() and not refresh:
        return pd.read_parquet(p)
    raw = con.raw_sql(month_sql(month_end))
    if p is not None:
        p.parent.mkdir(parents=True, exist_ok=True)
        raw.to_parquet(p, index=False)
    return raw


def month_ends(start: Any, end: Any) -> list[pd.Timestamp]:
    return list(pd.date_range(pd.Timestamp(start) + pd.offsets.MonthEnd(0), pd.Timestamp(end) + pd.offsets.MonthEnd(0),
                              freq="ME"))


def pull_months(
    months: Sequence[pd.Timestamp],
    cache_root: Path,
    connect: Callable[[], Any] = cp.connect,
    workers: int = 3,
    log: Callable[[str], None] = print,
) -> dict[str, float]:
    """Pull every uncached month, `workers` WRDS connections in parallel. Returns timing per month (seconds)."""
    todo = [m for m in months if not month_cache_path(cache_root, m).exists()]
    times: dict[str, float] = {}
    if not todo:
        return times
    chunks = [todo[i::workers] for i in range(workers)]

    def run(chunk: list[pd.Timestamp]) -> None:
        if not chunk:
            return
        con = connect()
        try:
            for m in chunk:
                t0 = time.time()
                pull_month(con, m, cache_root)
                times[f"{m:%Y-%m}"] = time.time() - t0
                log(f"  month {m:%Y-%m}: {times[f'{m:%Y-%m}']:.0f} s")
        finally:
            try:
                con.close()
            except Exception:  # noqa: BLE001  (closing is best effort)
                pass

    with ThreadPoolExecutor(max_workers=workers) as ex:
        list(ex.map(run, chunks))
    return times


def build_panel(months: Sequence[pd.Timestamp], cache_root: Path, curve_for: Callable[[pd.Timestamp], pd.Series]) -> pd.DataFrame:
    """Panel over cached months (`pull_months` first), with exit rows. `curve_for(t)` gives the Treasury row at t."""
    frames = []
    for m in months:
        p = month_cache_path(cache_root, m)
        if not p.exists():
            raise FileNotFoundError(f"month {m:%Y-%m} not pulled: {p}")
        frames.append(finish_month(pd.read_parquet(p), m, curve_for(m)))
    panel = pd.concat([f for f in frames if len(f)], ignore_index=True)
    return add_exit_rows(panel)


# ---------------------------------------------------------------- issuer link and fundamentals


def security_table(con: cp.SqlConnection, cache_root: Path | None = None, refresh: bool = False) -> pd.DataFrame:
    """Every Compustat security: gvkey, iid, cusip, ticker (one cached pull, about 50k rows)."""
    p = Path(cache_root) / "trace_panel" / "comp_security.parquet" if cache_root else None
    if p is not None and p.exists() and not refresh:
        return pd.read_parquet(p)
    out = con.raw_sql("select s.gvkey, s.iid, s.cusip, s.tic, s.secstat, c.conm from comp.security s "
                      "join comp.company c on c.gvkey = s.gvkey where s.cusip is not null")
    if p is not None:
        p.parent.mkdir(parents=True, exist_ok=True)
        out.to_parquet(p, index=False)
    return out


def link_issuers(bonds: pd.DataFrame, security: pd.DataFrame) -> pd.DataFrame:
    """Map each bond's (cusip6, ticker) to one gvkey: cusip6 first, ticker second.

    Where a key maps to several gvkeys, keep the gvkey with an active security (`secstat = 'A'`) first, then the most
    securities under that key (ties: smallest gvkey), and flag `link_ambiguous`. Active first matters for tickers:
    TRACE carries the current symbol, and an old company can keep a ticker that a new one now uses.
    Returns one row per distinct (cusip6, ticker) with gvkey, link_source.
    """
    sec = security.copy()
    sec["cusip6"] = sec["cusip"].astype(str).str[:6]
    sec["tic"] = sec["tic"].astype(str).str.upper()
    sec["active"] = sec["secstat"].astype(str).str.upper().eq("A") if "secstat" in sec else False

    def pick(key: str) -> pd.DataFrame:
        c = sec.groupby([key, "gvkey"]).agg(n=("active", "size"), active=("active", "max")).reset_index()
        c = c.sort_values([key, "active", "n", "gvkey"], ascending=[True, False, False, True])
        amb = c.groupby(key)["gvkey"].transform("size") > 1
        c["ambiguous"] = amb
        return c.drop_duplicates(key)[[key, "gvkey", "ambiguous"]]

    by6, bytic = pick("cusip6"), pick("tic")
    keys = bonds[["cusip6", "ticker"]].drop_duplicates().copy()
    keys["tic"] = keys["ticker"].astype(str).str.upper()
    a = keys.merge(by6, on="cusip6", how="left")
    b = keys.merge(bytic, on="tic", how="left")
    a["gvkey"] = a["gvkey"].astype(object)
    use_b = a["gvkey"].isna() & b["gvkey"].notna().to_numpy()
    out = a.copy()
    out.loc[use_b, "gvkey"] = b.loc[use_b.to_numpy(), "gvkey"].to_numpy()
    out.loc[use_b, "ambiguous"] = b.loc[use_b.to_numpy(), "ambiguous"].to_numpy()
    out["link_source"] = np.where(a["gvkey"].notna() & ~use_b, "cusip6", np.where(use_b, "ticker", "none"))
    out = out.rename(columns={"ambiguous": "link_ambiguous"})
    out["link_ambiguous"] = out["link_ambiguous"].astype("boolean").fillna(False).astype(bool)
    return out[["cusip6", "ticker", "gvkey", "link_source", "link_ambiguous"]]


class NumpyDtypes:
    """Connection proxy: nullable integer and float columns come back as numpy float (NA -> NaN).

    `compustat_pit.decumulate` compares `fqtr` with `==`; on a nullable column with a missing quarter that raises.
    """

    def __init__(self, con: Any) -> None:
        self.con = con

    def raw_sql(self, sql: str) -> pd.DataFrame:
        out = self.con.raw_sql(sql)
        for c in out.columns:
            if isinstance(out[c].dtype, (pd.Int64Dtype, pd.Int32Dtype, pd.Float64Dtype)) or str(out[c].dtype) in (
                    "Int64", "Int32", "Int16", "Float64"):
                out[c] = out[c].astype("float64")
        return out


def load_fundamentals(
    con: cp.SqlConnection, gvkeys: Sequence[str], start: str, end: str, cache_root: Path, chunk: int = 250,
    log: Callable[[str], None] = print,
) -> pd.DataFrame:
    """Compustat PIT vintages for `gvkeys` (via `compustat_pit.load_vintages`, per-gvkey cache), in chunks."""
    p = Path(cache_root) / "trace_panel" / f"fundamentals_{start}_{end}_{len(gvkeys)}.parquet"
    if p.exists():
        return pd.read_parquet(p)
    frames = []
    keys = sorted({str(g) for g in gvkeys})
    for i in range(0, len(keys), chunk):
        t0 = time.time()
        v = cp.load_vintages(NumpyDtypes(con), keys[i:i + chunk], start, end, cache_root=cache_root)
        frames.append(v)
        log(f"  fundamentals {i + len(keys[i:i + chunk])}/{len(keys)}: {time.time() - t0:.0f} s")
    out = pd.concat([f for f in frames if len(f)], ignore_index=True)
    keep = ["gvkey", "datadate", "vintage", "snapshot_available_at", "pit_exact", "oibdp", "special_items",
            "debt_current", "debt_long_term", "cash", "interest_expense", "revenue"]
    out = out[[c for c in keep if c in out]]
    p.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(p, index=False)
    return out


def leverage_as_of(vintages: pd.DataFrame, as_of: Any, max_stale_days: int = MAX_STALE_DAYS) -> pd.DataFrame:
    """Issuer leverage as known at `as_of` (Section 4.3, plain basis): debt / LTM EBITDA before special items.

    Steps: keep versions with `available_at <= as_of` (the snapshot day after month end; rows without a snapshot
    stay out); per fiscal quarter, the latest such version; per issuer, the four latest quarters, which must span
    no more than 13 months; the latest quarter must be at most `max_stale_days` old. Debt is that quarter's
    debt_current + debt_long_term. EBITDA <= 0 with positive debt maps to `LEV_CAP`; leverage is clipped to
    [0, LEV_CAP]. Intuition: the leverage a reader of the latest filed quarter would compute that day.
    """
    t = pd.Timestamp(as_of)
    v = vintages.copy()
    v["available_at"] = pd.to_datetime(v["snapshot_available_at"])
    v = v[v["available_at"].notna() & (v["available_at"] <= t)]
    if v.empty:
        return pd.DataFrame(columns=["gvkey", "ltm_ebitda", "ltm_revenue", "debt", "leverage", "datadate", "available_at",
                                     "lev_basis"])
    v = v.sort_values(["gvkey", "datadate", "vintage"]).drop_duplicates(["gvkey", "datadate"], keep="last")
    v = v.sort_values(["gvkey", "datadate"]).groupby("gvkey").tail(4)
    g = v.groupby("gvkey")
    span = (g["datadate"].max() - g["datadate"].min()).dt.days
    n = g["oibdp"].count()
    ltm = g["oibdp"].sum(min_count=4)
    latest = v.drop_duplicates("gvkey", keep="last").set_index("gvkey")
    debt = latest["debt_current"].fillna(0.0) + latest["debt_long_term"].fillna(0.0)
    debt = debt.where(latest["debt_current"].notna() | latest["debt_long_term"].notna())
    rev = g["revenue"].sum(min_count=4) if "revenue" in v else pd.Series(np.nan, index=ltm.index)
    out = pd.DataFrame({"ltm_ebitda": ltm, "ltm_revenue": rev, "debt": debt, "datadate": latest["datadate"],
                        "available_at": g["available_at"].max()})
    ok = (n == 4) & (span <= 400) & ((t - out["datadate"]).dt.days <= max_stale_days) & out["debt"].notna()
    out = out[ok].copy()
    lev = np.where(out["ltm_ebitda"] > 0, out["debt"] / out["ltm_ebitda"].where(out["ltm_ebitda"] > 0), LEV_CAP)
    out["leverage"] = np.clip(np.where(out["debt"] <= 0, 0.0, lev), 0.0, LEV_CAP)
    out["lev_basis"] = "plain"
    return out.reset_index()


def leverage_history(vintages: pd.DataFrame, months: Sequence[pd.Timestamp]) -> pd.DataFrame:
    """`leverage_as_of` at each month's decision time (month end + 1 day), stacked with a `date` column (month end)."""
    frames = []
    for m in months:
        f = leverage_as_of(vintages, m + pd.Timedelta(days=1))
        f.insert(0, "date", m)
        frames.append(f)
    return pd.concat(frames, ignore_index=True)
