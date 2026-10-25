"""Build the monthly panels from records, for a source that has no ready-made panels (docs/production_wiring.md).

On this machine the panels come from TRACE and Compustat warehouse files (`hy.sources.trace_panel`). Another source
can build the two large ones from the kinds it already serves, with the same rules:

- `bond_panel` (methodology 3.1, 11): per bond and month end, the par-weighted price and yield over the last
  `WINDOW_DAYS` of the month, the G-spread on the Treasury curve dated on or before the month end, duration,
  bid-ask, and one carried exit row after a bond's last month (`trace_panel` rules 3 to 6).
- `leverage` (methodology 4.3, plain basis): debt / LTM EBITDA before special items as known at each month end + 1
  day (`trace_panel.leverage_as_of`: four consecutive quarters, or 4/3 of three).

The issuer key of both panels is `Issuer.gvkey`: on another machine, put your own issuer identifier there and use it
in every panel. The small panels (`gics`, `ratings`, `annual_ebitda`, `equity_monthly`) are plain tables; the
schemas in `hy.data.source.PANEL_COLUMNS` state their columns.
"""

from __future__ import annotations

from typing import Callable, Sequence

import numpy as np
import pandas as pd

from hy.data.records import BOND_OBS_COLUMNS, Bond, Issuer, IssuerFinancials
from hy.sources import trace_panel as tp

WINDOW_DAYS = tp.WINDOW_DAYS
BID_ASK_COLUMN = "bid_ask_pts"  # optional extra observation column: quoted bid-ask in price points


def month_ends(start, end) -> list[pd.Timestamp]:
    """Every month end from `start` to `end`."""
    return tp.month_ends(start, end)


def _window_rows(obs: pd.DataFrame, month_end: pd.Timestamp) -> pd.DataFrame:
    """One row per bond over the month's last `WINDOW_DAYS` days, in the column names `trace_panel.finish_month` reads.
    Prices and yields are weighted by par volume; days without volume weigh 1."""
    lo = month_end - pd.Timedelta(WINDOW_DAYS - 1, unit="D")
    w = obs[(obs["date"] >= lo) & (obs["date"] <= month_end)]
    rows = []
    for cusip, g in w.groupby("cusip"):
        wt = g["par_volume"].astype(float).where(g["par_volume"] > 0, 1.0).fillna(1.0)
        has_p, has_y = g["price"].notna(), g["yield"].notna()
        if not has_p.any():
            continue
        ba = g[BID_ASK_COLUMN].astype(float).mean() if BID_ASK_COLUMN in g else np.nan
        rows.append({"cusip_id": cusip, "last_trade": g["date"].max(), "n_trades": int(g["n_trades"].sum()),
                     "par_volume": float(g["par_volume"].sum()),
                     "price_vw": float(np.average(g.loc[has_p, "price"], weights=wt[has_p])),
                     "yield_vw_pct": float(np.average(g.loc[has_y, "yield"], weights=wt[has_y])) * 100 if has_y.any()
                     else np.nan,
                     # A quoted bid-ask enters as the dealer-side gap (rule 4's primary measure).
                     "px_dealer_sell": ba, "px_dealer_buy": 0.0 if ba == ba else np.nan, "day_range": np.nan,
                     "available_at": g["available_at"].max()})
    return pd.DataFrame(rows)


def bond_panel(issuers: Sequence[Issuer], bonds: Sequence[Bond], observations: pd.DataFrame,
               months: Sequence[pd.Timestamp], curve_for: Callable[[pd.Timestamp], pd.Series]) -> pd.DataFrame:
    """The `bond_panel` from bond terms, daily observations (`BOND_OBS_COLUMNS`, plus optional `bid_ask_pts`) and
    `curve_for(month_end)`: the Treasury curve row (`Curve.as_row()`) dated on or before the month end.

    Columns: `trace_panel.PANEL_COLUMNS` plus `gvkey` and `link_source`. `available_at` is the latest observation's `available_at` in
    the window, so the source's own publication lag carries through. Bonds whose issuer is not in `issuers` drop out.
    """
    missing = [c for c in BOND_OBS_COLUMNS if c not in observations.columns]
    if missing:
        raise ValueError(f"observations lack columns {missing}")
    key = {i.ticker: i.gvkey for i in issuers}
    terms = pd.DataFrame([{"cusip": b.cusip, "company_symbol": b.issuer_ticker, "cpn_rt": b.coupon * 100,
                           "mtrty_dt": pd.Timestamp(b.maturity)} for b in bonds if key.get(b.issuer_ticker)])
    if terms.empty:
        return pd.DataFrame(columns=tp.PANEL_COLUMNS + ["gvkey", "link_source"])
    obs = observations[observations["cusip"].isin(terms["cusip"])].copy()
    obs["date"] = pd.to_datetime(obs["date"])
    frames = []
    for m in months:
        t = pd.Timestamp(m) + pd.offsets.MonthEnd(0)
        raw = _window_rows(obs, t)
        if raw.empty:
            continue
        raw = raw.merge(terms, left_on="cusip_id", right_on="cusip", how="inner").drop(columns="cusip")
        part = tp.finish_month(raw, t, curve_for(t))
        part["available_at"] = pd.to_datetime(raw["available_at"]).to_numpy()
        part["yield_source"] = part["yield_source"].replace({"trace": "observed"})
        frames.append(part)
    if not frames:
        return pd.DataFrame(columns=tp.PANEL_COLUMNS + ["gvkey", "link_source"])
    panel = tp.add_exit_rows(pd.concat(frames, ignore_index=True))
    panel["gvkey"] = panel["ticker"].map(key).astype(str)
    panel["link_source"] = "issuer_table"  # every bond names its issuer, so no CUSIP or ticker match is needed
    return panel


def vintages(financials: Sequence[IssuerFinancials]) -> pd.DataFrame:
    """Financial records as the version table `trace_panel.leverage_as_of` reads. EBITDA before special items is
    `ebitda_adj_company` (on this machine: Compustat oibdp); a version's release is its `available_at`."""
    rows = [{"gvkey": r.key, "datadate": pd.Timestamp(r.as_of), "snapshot_available_at": pd.Timestamp(r.available_at),
             "oibdp": r.ebitda_adj_company, "debt_current": r.debt_current, "debt_long_term": r.debt_long_term,
             "revenue": r.revenue} for r in financials]
    v = pd.DataFrame(rows, columns=["gvkey", "datadate", "snapshot_available_at", "oibdp", "debt_current",
                                    "debt_long_term", "revenue"])
    v = v.sort_values(["gvkey", "datadate", "snapshot_available_at"])
    v["vintage"] = v.groupby(["gvkey", "datadate"]).cumcount()
    return v.reset_index(drop=True)


def leverage_panel(financials: Sequence[IssuerFinancials], months: Sequence[pd.Timestamp]) -> pd.DataFrame:
    """The `leverage` panel: `trace_panel.leverage_as_of` at each month end + 1 day, with a `date` column."""
    return tp.leverage_history(vintages(financials), [pd.Timestamp(m) + pd.offsets.MonthEnd(0) for m in months])
