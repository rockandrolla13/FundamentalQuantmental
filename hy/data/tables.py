"""A source that reads plain tables: the easy way to plug in any data (docs/production_wiring.md).

Export your data into the folder `<HY_DATA_ROOT>/tables/` with the file names and columns of `TABLES`, then run with
`HY_SOURCE=hy.data.tables:make_source`. `make_source` joins this source with `PublicSource`, which reads the SEC
filings and the US Treasury curve, so the tables hold only what a vendor sells: identifiers, financials, bonds,
prices, the HY index level, equity values and the peer panels.

Rules for every table (docs/data_contract.md section 1):
- Rates, yields, spreads, coupons and returns are decimals (0.065 is 6.5%). Amounts are USD millions.
- `available_at` is the first moment the value was public, as naive UTC. Never earlier than the real release.
- A value you do not have stays empty (NaN), never zero.
- Files may be `.parquet` or `.csv`; parquet wins when both exist.
"""

from __future__ import annotations

from dataclasses import fields
from datetime import datetime
from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd

from hy.data.config import DataConfig
from hy.data.pit import DataUnavailable
from hy.data.records import (BOND_OBS_COLUMNS, Bond, Classification, Curve, IndexLevel, Issuer, IssuerFinancials,
                             MarketValue, NonRecurringItem, check_observations)
from hy.data.source import PANELS

TABLES_DIR = "tables"

# File name -> (required columns, optional columns). docs/production_wiring.md explains each column.
FINANCIAL_FIELDS = tuple(f.name for f in fields(IssuerFinancials)
                         if f.name not in ("key", "as_of", "available_at", "nonrecurring_items", "maturity_schedule",
                                           "source"))
# The value of a financials column that a table leaves out: what the warehouse adapter (`hy.sources.financials`) gives
# when Compustat has no such field. Zero for the revolver, letters of credit, rent, pension, guarantees and the
# maturity schedule; no cap for the borrowing base; NaN for every field Compustat does supply.
_WAREHOUSE_ZERO = ("revolver_commitment", "revolver_drawn", "letters_of_credit", "rent_expense", "pension_underfunded",
                   "guarantees_weak")
DEFAULT_FINANCIALS = {f: (0.0 if f in _WAREHOUSE_ZERO else float("inf") if f == "borrowing_base" else float("nan"))
                      for f in FINANCIAL_FIELDS}
TABLES: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "issuers": (("ticker", "issuer_id"), ("cik", "name")),
    "financials": (("issuer_id", "period_end", "available_at", "revenue", "ebitda_reported", "ebitda_adj_company"),
                   tuple(f for f in FINANCIAL_FIELDS if f not in ("revenue", "ebitda_reported", "ebitda_adj_company"))
                   + ("special_items", "special_items_cash", "maturity_y1", "maturity_y2", "maturity_y3",
                      "maturity_y4", "maturity_y5", "source")),
    "bonds": (("bond_id", "ticker", "coupon", "maturity", "seniority", "fixed", "convertible"), ("grade",)),
    "bond_obs": (("bond_id", "date", "price", "yield", "n_trades", "par_volume", "available_at"), ("bid_ask_pts",)),
    "hy_index": (("date", "available_at", "spread"), ("distress", "name")),
    "market_value": (("ticker", "period_end", "available_at", "value"), ("source",)),
    "treasury_curve": (("date", "available_at"), ()),  # plus one column per tenor in years, e.g. "0.25", "10"
}


def _read(folder: Path, name: str) -> pd.DataFrame | None:
    for ext, reader in ((".parquet", pd.read_parquet), (".csv", pd.read_csv)):
        p = folder / f"{name}{ext}"
        if p.exists():
            return reader(p)
    return None


def _num(x) -> float:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return float("nan")
    return v


def _bool(x) -> bool:
    return str(x).strip().lower() in ("1", "true", "t", "yes", "y")


class TableSource:
    """Identifiers, financials, bonds, prices, the HY index, equity values, the Treasury curve (optional) and the
    panels from `<root>/tables/`. A table that is not there raises DataUnavailable for its kinds."""

    def __init__(self, cfg: DataConfig, folder: Path | None = None) -> None:
        self.cfg = cfg
        self.folder = Path(folder) if folder is not None else cfg.path(TABLES_DIR)
        self._cache: dict[str, pd.DataFrame | None] = {}

    def table(self, name: str) -> pd.DataFrame:
        """One table, checked for its required columns; dates parsed."""
        if name not in self._cache:
            df = _read(self.folder, name)
            if df is not None:
                need = TABLES[name][0] if name in TABLES else ()
                missing = [c for c in need if c not in df.columns]
                if missing:
                    raise ValueError(f"{self.folder / name}: missing columns {missing}")
                for c in ("period_end", "available_at", "date", "maturity"):
                    if c in df.columns:
                        df[c] = pd.to_datetime(df[c])
            self._cache[name] = df
        df = self._cache[name]
        if df is None:
            raise DataUnavailable("table", name, f"no {name}.parquet or {name}.csv in {self.folder}")
        return df

    # ------------------------------------------------------------ issuers and fundamentals

    def issuers(self, tickers: Sequence[str]) -> list[Issuer]:
        t = self.table("issuers")
        out = []
        for tick in tickers:
            hit = t[t["ticker"].astype(str).str.upper() == tick.upper()]
            if hit.empty:
                raise DataUnavailable("issuer", tick, "not in issuers table")
            r = hit.iloc[0]
            cik = r.get("cik")
            cik = None if cik is None or pd.isna(cik) else (str(cik).split(".")[0].lstrip("0") or None)
            name = r.get("name")
            out.append(Issuer(tick.upper(), gvkey=str(r["issuer_id"]), cik=cik,
                              name="" if pd.isna(name) else str(name)))
        return out

    def financials(self, issuer: Issuer) -> list[IssuerFinancials]:
        """Every version of every quarter: one row per (issuer_id, period_end, available_at). A restatement is a new
        row with a later `available_at`; the view keeps the latest version public at the decision time."""
        f = self.table("financials")
        rows = f[f["issuer_id"].astype(str) == str(issuer.gvkey)]
        out = []
        for r in rows.to_dict("records"):
            # A column you leave out takes the value the warehouse gives for it (DEFAULT_FINANCIALS); an empty cell in
            # a column you give stays NaN, as a missing value must.
            vals = {k: _num(r[k]) if k in r else DEFAULT_FINANCIALS[k] for k in FINANCIAL_FIELDS}
            if pd.isna(vals["borrowing_base"]):
                vals["borrowing_base"] = float("inf")  # no borrowing base: the revolver is not capped
            spi = _num(r.get("special_items"))
            items = ((NonRecurringItem("special_items", -spi, recurs=False, cash=_bool(r.get("special_items_cash"))),)
                     if np.isfinite(spi) and spi else ())
            sched = (tuple(_num(r.get(f"maturity_y{i}")) for i in range(1, 6)) if "maturity_y1" in r
                     else IssuerFinancials.__dataclass_fields__["maturity_schedule"].default)
            src = r.get("source")
            out.append(IssuerFinancials(
                key=str(issuer.gvkey), as_of=pd.Timestamp(r["period_end"]).to_pydatetime(),
                available_at=pd.Timestamp(r["available_at"]).to_pydatetime(), nonrecurring_items=items,
                maturity_schedule=sched, source="tables/financials" if src is None or pd.isna(src) else str(src),
                **vals))
        return out

    def market_value(self, issuer: Issuer, decision_time: datetime) -> MarketValue:
        m = self.table("market_value")
        m = m[(m["ticker"].astype(str).str.upper() == issuer.ticker) & (m["available_at"] <= pd.Timestamp(decision_time))]
        if m.empty:
            raise DataUnavailable("market_value", issuer.ticker, "none public by the decision time")
        r = m.sort_values("period_end").iloc[-1]
        src = r.get("source")
        return MarketValue(issuer.ticker, r["period_end"].to_pydatetime(), r["available_at"].to_pydatetime(),
                           issuer_ticker=issuer.ticker, value=_num(r["value"]),
                           source="tables/market_value" if src is None or pd.isna(src) else str(src))

    # ------------------------------------------------------------ bonds and market

    def bonds(self, issuer: Issuer) -> list[Bond]:
        b = self.table("bonds")
        b = b[b["ticker"].astype(str).str.upper() == issuer.ticker]
        return [Bond(str(r["bond_id"]), issuer.ticker, _num(r["coupon"]), pd.Timestamp(r["maturity"]).to_pydatetime(),
                     str(r["seniority"]), _bool(r["fixed"]), _bool(r["convertible"]),
                     "" if pd.isna(r.get("grade")) else str(r.get("grade"))) for r in b.to_dict("records")]

    def observations(self, bonds: Sequence[Bond], start: datetime, end: datetime) -> pd.DataFrame:
        o = self.raw_observations()
        keep = (o["bond_id"].astype(str).isin([b.cusip for b in bonds]) & (o["date"] >= pd.Timestamp(start))
                & (o["date"] <= pd.Timestamp(end)) & (o["available_at"] <= pd.Timestamp(end)))
        out = o[keep].rename(columns={"bond_id": "cusip"})[list(BOND_OBS_COLUMNS)].reset_index(drop=True)
        out["cusip"] = out["cusip"].astype(str)
        return check_observations(out)

    def raw_observations(self) -> pd.DataFrame:
        """The whole `bond_obs` table, optional columns included (the panel builder reads `bid_ask_pts`)."""
        return self.table("bond_obs")

    def hy_index(self, on: datetime) -> IndexLevel:
        h = self.table("hy_index")
        h = h[h["available_at"] <= pd.Timestamp(on)]
        if h.empty:
            raise DataUnavailable("hy_index", str(on), "none public by the date")
        r = h.sort_values("date").iloc[-1]
        name = r.get("name")
        return IndexLevel("HY", r["date"].to_pydatetime(), r["available_at"].to_pydatetime(),
                          name="tables/hy_index" if name is None or pd.isna(name) else str(name),
                          spread=_num(r["spread"]), distress=_num(r.get("distress")))

    def _curve_rows(self) -> pd.DataFrame:
        c = self.table("treasury_curve")
        tenors = [col for col in c.columns if col not in ("date", "available_at")]
        return c.rename(columns={t: float(t) for t in tenors}).sort_values("date")

    def curve(self, on: datetime) -> Curve:
        c = self._curve_rows()
        c = c[c["available_at"] <= pd.Timestamp(on)]
        if c.empty:
            raise DataUnavailable("curve", str(on), "none public by the date")
        return self._to_curve(c.iloc[-1])

    def curves(self, start: datetime, end: datetime) -> list[Curve]:
        c = self._curve_rows()
        c = c[(c["date"] >= pd.Timestamp(start)) & (c["date"] <= pd.Timestamp(end))]
        return [self._to_curve(r) for _, r in c.iterrows()]

    @staticmethod
    def _to_curve(r: pd.Series) -> Curve:
        ten = [k for k in r.index if isinstance(k, float)]
        return Curve("UST", r["date"].to_pydatetime(), r["available_at"].to_pydatetime(), tenors=tuple(ten),
                     yields=tuple(_num(r[k]) for k in ten))

    # ------------------------------------------------------------ reference and panels

    def classifications(self, issuers: Sequence[Issuer]) -> list[Classification]:
        """GICS sectors from the `gics` panel (each spell public from its `available_at`)."""
        g = self.panel("gics")
        out = []
        for iss in issuers:
            for r in g[g["gvkey"].astype(str) == str(iss.gvkey)].to_dict("records"):
                t0 = pd.Timestamp(r["indfrom"]).to_pydatetime()
                out.append(Classification(iss.ticker, t0, max(t0, pd.Timestamp(r["available_at"]).to_pydatetime()),
                                          issuer_ticker=iss.ticker, sector=str(r["gsector"]), rating_source="tables/gics"))
        return out

    def panel(self, name: str, columns: Sequence[str] | None = None) -> pd.DataFrame:
        """`tables/panels/<name>.parquet` (or .csv). Build `bond_panel` and `leverage` with scripts/build_panels.py."""
        if name not in PANELS:
            raise DataUnavailable("panel", name, "unknown panel")
        df = _read(self.folder / "panels", name)
        if df is None:
            raise DataUnavailable("panel", name, f"no panels/{name}.parquet or .csv in {self.folder}")
        for c in ("date", "datadate", "indfrom", "indthru", "available_at", "maturity", "accrue_to", "hedge_date"):
            if c in df.columns:
                df[c] = pd.to_datetime(df[c])
        if "gvkey" in df.columns:
            df["gvkey"] = df["gvkey"].astype(str)
        if "gsector" in df.columns:
            df["gsector"] = df["gsector"].astype(str).str.replace(r"\.0$", "", regex=True)
        return df if columns is None else df[list(dict.fromkeys([*columns, "available_at"]))]


def make_source(cfg: DataConfig):
    """The production source: the tables first, then the public SEC and Treasury data for the rest. A Treasury
    curve table, when present, wins over the public curve (a machine without internet)."""
    from hy.data.sources import CompositeSource, PublicSource  # noqa: PLC0415 - avoid an import cycle

    tables = TableSource(cfg)
    return CompositeSource(tables, PublicSource(cfg, fundamentals=tables, market=tables))


def write_tables(source, tickers: Sequence[str], start: datetime, end: datetime, folder: Path,
                 panels: Sequence[str] = PANELS) -> dict[str, int]:
    """Export what `source` serves for `tickers` into `folder` in the `TABLES` layout (rows per table). Two uses:
    example tables to copy on another machine, and the test that a run on the tables equals a run on the source."""
    folder = Path(folder)
    (folder / "panels").mkdir(parents=True, exist_ok=True)
    iss = source.issuers(list(tickers))
    out: dict[str, pd.DataFrame] = {
        "issuers": pd.DataFrame([{"ticker": i.ticker, "issuer_id": i.gvkey, "cik": i.cik, "name": i.name} for i in iss])}
    fin = []
    for i in iss:
        for r in source.financials(i):
            row = {"issuer_id": r.key, "period_end": r.as_of, "available_at": r.available_at, "source": r.source,
                   **{f: getattr(r, f) for f in FINANCIAL_FIELDS}}
            spi = [x for x in r.nonrecurring_items if not x.recurs]
            if spi:
                row["special_items"] = -sum(x.amount for x in spi)
                row["special_items_cash"] = any(x.cash for x in spi)
            row.update({f"maturity_y{k + 1}": v for k, v in enumerate(r.maturity_schedule)})
            fin.append(row)
    out["financials"] = pd.DataFrame(fin)
    bonds = [b for i in iss for b in source.bonds(i)]
    out["bonds"] = pd.DataFrame([{"bond_id": b.cusip, "ticker": b.issuer_ticker, "coupon": b.coupon,
                                  "maturity": b.maturity, "seniority": b.seniority, "fixed": b.fixed,
                                  "convertible": b.convertible, "grade": b.grade} for b in bonds])
    out["bond_obs"] = source.observations(bonds, start, end).rename(columns={"cusip": "bond_id"})
    idx = []
    for d in pd.date_range(start, end, freq="D"):
        try:
            lvl = source.hy_index(d.to_pydatetime())
        except DataUnavailable:
            continue
        idx.append({"date": lvl.as_of, "available_at": lvl.available_at, "spread": lvl.spread,
                    "distress": lvl.distress, "name": lvl.name})
    out["hy_index"] = pd.DataFrame(idx).drop_duplicates("date") if idx else pd.DataFrame(columns=TABLES["hy_index"][0])
    mv = []
    for i in iss:
        try:
            m = source.market_value(i, end)
        except DataUnavailable:
            continue
        mv.append({"ticker": i.ticker, "period_end": m.as_of, "available_at": m.available_at, "value": m.value,
                   "source": m.source})
    out["market_value"] = pd.DataFrame(mv, columns=["ticker", "period_end", "available_at", "value", "source"])
    curves = source.curves(start, end)
    out["treasury_curve"] = pd.DataFrame([{"date": c.as_of, "available_at": c.available_at,
                                           **{repr(float(t)): y for t, y in zip(c.tenors, c.yields)}} for c in curves])
    counts = {}
    for name, df in out.items():
        df.to_parquet(folder / f"{name}.parquet", index=False)
        counts[name] = len(df)
    for name in panels:
        try:
            p = source.panel(name)
        except DataUnavailable:
            continue
        p.to_parquet(folder / "panels" / f"{name}.parquet", index=False)
        counts[f"panels/{name}"] = len(p)
    return counts
