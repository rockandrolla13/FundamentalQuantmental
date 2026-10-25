"""Check a data source against the data contract before a run (docs/data_contract.md; docs/production_wiring.md).

`check_source(source, tickers, decision_time)` reads every kind through a `DataView` and returns one row per check:
`kind`, `level` ("required" or "optional"), `ok` (True, False), and a `detail` that says what was found. It catches
the three mistakes a new connector makes most: a missing kind, wrong units (percent for decimals, dollars for USD
millions), and time stamps that let a value be read before it was public (the view raises `LookAheadError`).

Intuition: the analyst runs on any data that passes this table; a failed required row names what to fix first.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Sequence

import numpy as np
import pandas as pd

from hy.data.pit import DataUnavailable, LookAheadError
from hy.data.records import BOND_OBS_COLUMNS
from hy.data.source import FACT_KEYS, PANEL_BACKTEST_COLUMNS, PANEL_COLUMNS, PANELS, PANELS_FOR_PEERS
from hy.data.view import DataView

REPORT_COLUMNS = ("ticker", "kind", "level", "ok", "detail")
OBS_LOOKBACK_DAYS = 180  # the process reads this window of bond observations (data contract 3.10)


class _Report:
    def __init__(self) -> None:
        self.rows: list[dict] = []

    def add(self, ticker: str, kind: str, level: str, ok: bool, detail: str) -> None:
        self.rows.append({"ticker": ticker, "kind": kind, "level": level, "ok": bool(ok), "detail": detail})

    def run(self, ticker: str, kind: str, level: str, read: Callable[[], Any],
            judge: Callable[[Any], tuple[bool, str]]) -> Any:
        """`read()` the kind, then `judge` it; a gap, a look-ahead or an error becomes a failed row."""
        try:
            got = read()
        except LookAheadError as exc:
            self.add(ticker, kind, level, False, f"look-ahead: {exc}")
            return None
        except DataUnavailable as exc:
            self.add(ticker, kind, level, False, f"unavailable: {exc}")
            return None
        except Exception as exc:  # noqa: BLE001 - any error is a connector defect to report, not to hide
            self.add(ticker, kind, level, False, f"error {type(exc).__name__}: {str(exc)[:160]}")
            return None
        ok, detail = judge(got)
        self.add(ticker, kind, level, ok, detail)
        return got


def _between(x: float, lo: float, hi: float) -> bool:
    return bool(np.isfinite(x) and lo <= x <= hi)


def _judge_issuer(i) -> tuple[bool, str]:
    missing = [n for n in ("gvkey", "cik") if not getattr(i, n)]
    return not missing, f"gvkey={i.gvkey!r} cik={i.cik!r}" + (f"; missing {missing}" if missing else "")


def _judge_financials(qs) -> tuple[bool, str]:
    if len(qs) < 4:
        return False, f"{len(qs)} quarters known; the LTM needs 4 consecutive quarters"
    last = max(qs, key=lambda r: r.as_of)
    rev = last.revenue
    # USD millions: a high yield issuer's quarterly revenue lies far below 1e6 (a trillion dollars).
    units = _between(rev, 0.0, 1e6)
    return units, (f"{len(qs)} quarters, latest {last.as_of:%Y-%m-%d} revenue {rev:,.1f}"
                   + ("" if units else " (expect USD millions)"))


def _judge_facts(f) -> tuple[bool, str]:
    missing = [k for k in FACT_KEYS if k not in f.values]
    bad = [k for k, v in f.values.items() if not (isinstance(v, tuple) and len(v) == 2)]
    detail = f"{len(f.values)} keys, available {f.available_at:%Y-%m-%d %H:%M}"
    if missing:
        detail += f"; missing keys {missing}"
    if bad:
        detail += f"; not (value, source) pairs: {bad[:5]}"
    return not missing and not bad, detail


def _judge_bonds(bs) -> tuple[bool, str]:
    if not bs:
        return False, "no bonds: steps 4 to 15 need a spread"
    coupons = [b.coupon for b in bs]
    units = all(_between(c, 0.0, 0.25) for c in coupons)
    kept = [b for b in bs if b.fixed and not b.convertible and b.seniority in ("senior_unsecured", "secured")]
    return units and bool(kept), (f"{len(bs)} bonds, {len(kept)} fixed non-convertible senior; coupons "
                                  f"{min(coupons):.4f} to {max(coupons):.4f}" + ("" if units else " (expect decimals)"))


def _judge_observations(o: pd.DataFrame) -> tuple[bool, str]:
    if tuple(o.columns) != BOND_OBS_COLUMNS:
        return False, f"columns {tuple(o.columns)} != {BOND_OBS_COLUMNS}"
    if o.empty:
        return False, f"no observations in the last {OBS_LOOKBACK_DAYS} days"
    y, p = o["yield"].dropna(), o["price"].dropna()
    units = (y.abs() < 1.0).all() and p.between(1.0, 200.0).all()
    return bool(units), (f"{len(o)} rows, {o['cusip'].nunique()} bonds, last {pd.Timestamp(o['date'].max()):%Y-%m-%d}; "
                         f"yield {y.median():.4f} price {p.median():.2f}" + ("" if units else
                                                                              " (expect yield decimal, price per 100)"))


def _judge_curve(c) -> tuple[bool, str]:
    ys = np.array(c.yields, dtype=float)
    ok = len(c.tenors) >= 3 and np.nanmax(ys) < 0.25 and max(c.tenors) >= 10
    return bool(ok), f"{c.as_of:%Y-%m-%d}, tenors {min(c.tenors):g} to {max(c.tenors):g} years, yields {np.nanmin(ys):.4f} to {np.nanmax(ys):.4f}"


def _judge_index(lvl) -> tuple[bool, str]:
    ok = _between(lvl.spread, 0.005, 0.30)
    return ok, f"{lvl.as_of:%Y-%m-%d} spread {lvl.spread:.4f} distress {lvl.distress:.4f}" + ("" if ok else " (expect decimal)")


def _judge_market_value(m) -> tuple[bool, str]:
    ok = _between(m.value, 0.0, 1e7)
    return ok, f"{m.value:,.1f} as of {m.as_of:%Y-%m-%d}" + ("" if ok else " (expect USD millions)")


def _judge_panel(name: str) -> Callable[[pd.DataFrame], tuple[bool, str]]:
    def judge(df: pd.DataFrame) -> tuple[bool, str]:
        need = PANEL_COLUMNS[name] + PANEL_BACKTEST_COLUMNS.get(name, ())
        missing = [c for c in need if c not in df.columns]
        live_missing = [c for c in PANEL_COLUMNS[name] if c not in df.columns]
        detail = f"{len(df)} rows"
        if missing:
            detail += f"; missing {missing}" + (" (backtest only)" if not live_missing else "")
        return not live_missing and len(df) > 0, detail
    return judge


def check_source(source: Any, tickers: Sequence[str], decision_time: datetime) -> pd.DataFrame:
    """One row per check (columns `REPORT_COLUMNS`) for `tickers` at `decision_time`. Required rows must pass for a
    full run; optional rows blank one estimate or one memo line each (docs/data_contract.md section 3)."""
    view = DataView(source, decision_time)
    rep = _Report()
    t0 = pd.Timestamp(decision_time)

    rep.run("-", "curve", "required", view.curve, _judge_curve)
    rep.run("-", "hy_index", "required", view.hy_index, _judge_index)
    rep.run("-", "forecasts", "optional", view.forecast_status,
            lambda s: (bool((s["rows"] > 0).any()), "; ".join(f"{r.source}: {r.status} ({r.rows})" for r in s.itertuples())))
    for name in PANELS:
        level = "optional" if name not in PANELS_FOR_PEERS else "required for peers"
        rep.run("-", f"panel:{name}", level, lambda n=name: view.panel(n), _judge_panel(name))

    for t in tickers:
        iss = rep.run(t, "issuer", "required", lambda t=t: view.issuer(t), _judge_issuer)
        if iss is None:
            continue
        rep.run(t, "financials", "required", lambda: view.financials(iss), _judge_financials)
        rep.run(t, "facts", "required", lambda: view.facts(iss), _judge_facts)
        filings = rep.run(t, "filings", "optional", lambda: view.filings(iss, ("10-Q", "10-K")),
                          lambda fs: (bool(fs), f"{len(fs)} 10-Q and 10-K filings"))
        if filings:
            acc = max(filings, key=lambda f: f.available_at).accession
            rep.run(t, "balance_sheet", "required", lambda: view.balance_sheet(iss, acc),
                    lambda b: (bool(np.isfinite(b.debt)), f"{b.as_of:%Y-%m-%d} debt {b.debt:,.1f} ({b.debt_source})"))
            rep.run(t, "filing_text", "optional", lambda: view.filing_text(iss, acc),
                    lambda x: (len(x.text) > 1000, f"{len(x.text):,} characters"))
        rep.run(t, "market_value", "optional", lambda: view.market_value(iss), _judge_market_value)
        bonds = rep.run(t, "bonds", "required", lambda: view.bonds(iss), _judge_bonds)
        if bonds:
            start = t0 - pd.Timedelta(OBS_LOOKBACK_DAYS, unit="D")
            rep.run(t, "observations", "required", lambda: view.observations(bonds, start), _judge_observations)
    return pd.DataFrame(rep.rows, columns=list(REPORT_COLUMNS))


def failures(report: pd.DataFrame, level: str = "required") -> pd.DataFrame:
    """The failed rows of one level."""
    return report[(~report["ok"]) & (report["level"] == level)]
