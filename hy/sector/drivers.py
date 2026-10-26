"""Issuer drivers of the sector fair-spread models. Spec docs/factors/SECTOR-models.md, sections 3 and 4; methodology
Sections 4.1 to 4.3 (state features) and 7.2 (blocks of x and their signs).

One row per gvkey at the decision time dt = hy.backtest.decision_time(as_of). Every driver is NaN when its panel or
column is missing. The sign of each driver in the fair spread is the sign the methodology argues for (7.2 table:
spread rises in leverage, falls in coverage and margin trend). The sector lists are our choice. No source in the repo
tests a sector-specific driver list on spreads. The lists follow the archetype frames of docs/framework.md F2 (A1 to
A6) and Kricheff (2012) ch. 11, pp. 58 to 61 (industry-specific operating metrics, capex as a share of revenue,
gross margin for retailers and manufacturers).

    log_lev        log(clip(debt / LTM EBITDA, 0.1, 20)); EBITDA <= 0 reads as 20x       `leverage`        (+)
    log_lev_lease  log of (debt + 8 rent) / (LTM EBITDA + rent), hy.rv, Section 4.3         `compustat_annual` xrent (+)
    coverage       clip(LTM EBITDA / LTM interest, -5, 30)                                 quarterly xintq, else annual xint (-)
    ebitda_cyc     minus the worst YoY EBITDA change, last 10 fiscal years (F21 cyclicality) `annual_ebitda`  (+)
    capex_int      clip(LTM capex / LTM sales, 0, 2)                                       quarterly, else annual (+)
    fcf_debt       clip((LTM CFO - LTM capex) / debt, -1, 1)                               quarterly, else annual (-)
    margin         LTM EBITDA margin (F23 issuer_margins)                                  `compustat_quarterly` (-)
    margin_trend   8-quarter margin trend t-statistic (hy.state.margin_trend), clip +-10     `compustat_quarterly` (-)
    gross_margin   (sale - cogs) / sale, latest fiscal year                                `compustat_annual` (-)
    mat_wall       clip((dd1 + dd2) / (dlc + dltt), 0, 1): debt due in two years            `compustat_annual` (+)
"""

from __future__ import annotations

from typing import Mapping

import numpy as np
import pandas as pd

from hy.backtest import decision_time
from hy.factors.f08_lever_event_risk import STALE_DAYS, _consecutive
from hy.factors.f09_profitability_change import known_annual
from hy.factors.f21_refinancing_headroom import cyclicality
from hy.factors.f23_margin_squeeze import issuer_margins
from hy.peers import LEV_FLOOR, SUST_STALE_DAYS
from hy.sector.common import month_end, present

LEV_CAP = 20.0               # leverage cap; non-positive EBITDA reads as the cap (our choice)
LEASE_MULTIPLE = 8.0         # rent multiple of lease debt (Section 4.3; Gatto pp. 267-268; hy.rv)
LEV_STALE_DAYS = 92          # the latest leverage row must be at most one quarter old (our choice)
COVER_CLIP = (-5.0, 30.0)    # coverage clip (our choice: removes near-zero interest)
TREND_CLIP = 10.0            # margin trend t clip; a perfect line gives +-inf (our choice)

DRIVER_NAMES = ("log_lev", "log_lev_lease", "coverage", "ebitda_cyc", "capex_int", "fcf_debt", "margin",
                "margin_trend", "gross_margin", "mat_wall")
# Sign of each driver in log spread: +1 the spread rises in the driver, -1 it falls (methodology 7.2 table).
SIGNS: dict[str, int] = {"log_lev": 1, "log_lev_lease": 1, "coverage": -1, "ebitda_cyc": 1, "capex_int": 1,
                         "fcf_debt": -1, "margin": -1, "margin_trend": -1, "gross_margin": -1, "mat_wall": 1}
# A driver that has too little data in a group uses its alternate (lease-adjusted leverage -> plain leverage).
ALTERNATES: dict[str, str] = {"log_lev_lease": "log_lev"}

# Driver list per model group. Our choice: no source tests these lists. The reason column names the frame.
SECTOR_DRIVERS: dict[str, tuple[str, ...]] = {
    # F2 A3: EBITDA at a stress deck, maintenance capex to hold volume. Kricheff p. 61 capex share of revenue.
    "energy": ("log_lev", "ebitda_cyc", "capex_int", "coverage"),
    # F2 A3 and A4: commodity price and volume cycles, capital intensity.
    "materials": ("log_lev", "ebitda_cyc", "capex_int", "margin_trend"),
    # F2 A4: peak-to-trough EBITDA, operating leverage (Kricheff p. 60).
    "industrials": ("log_lev", "ebitda_cyc", "margin_trend", "coverage"),
    # F2 A1: lease-adjusted leverage, gross margin and same-store trend (Kricheff p. 59 gross margin).
    "consumer_disc": ("log_lev_lease", "margin_trend", "gross_margin", "mat_wall"),
    # Defensive volume: leverage, margin trend, coverage.
    "consumer_staples": ("log_lev", "margin_trend", "coverage"),
    # F2 A2: margin level and trend (labour and bad debt), FCF.
    "health_care": ("log_lev", "margin", "margin_trend", "fcf_debt"),
    # F2 A6: cash conversion after capitalised development; margin trend.
    "technology": ("log_lev", "fcf_debt", "margin_trend"),
    # F2 A5: EBITDA less capex, capex above 15% of sales, refinancing wall.
    "telecom_media": ("log_lev", "fcf_debt", "capex_int", "mat_wall"),
    # Regulated, asset heavy: leverage, coverage, refinancing wall.
    "utilities": ("log_lev", "coverage", "mat_wall"),
}
# The pooled model of thin sectors: the drivers every archetype shares (methodology 7.2 capital structure block).
POOLED_DRIVERS: tuple[str, ...] = ("log_lev", "coverage", "fcf_debt", "ebitda_cyc")


def _col(df: pd.DataFrame, name: str) -> pd.Series:
    return df[name].astype(float) if name in df else pd.Series(np.nan, index=df.index)


def leverage_now(lev: pd.DataFrame, as_of: pd.Timestamp, dt: pd.Timestamp) -> pd.DataFrame:
    """Latest `leverage` row per gvkey with date <= as_of, available_at <= dt, at most LEV_STALE_DAYS old.
    Columns gvkey (index), leverage, ltm_ebitda, debt."""
    v = lev[(pd.to_datetime(lev["available_at"]) <= dt)].copy()
    v["date"] = pd.to_datetime(v["date"])
    v = v[(v["date"] <= as_of) & ((as_of - v["date"]).dt.days <= LEV_STALE_DAYS)]
    v = v.sort_values(["date", "available_at"]).drop_duplicates("gvkey", keep="last").set_index("gvkey")
    return pd.DataFrame({"leverage": _col(v, "leverage"), "ltm_ebitda": _col(v, "ltm_ebitda"),
                         "debt": _col(v, "debt")})


def capped_log_leverage(leverage: pd.Series, ebitda: pd.Series) -> pd.Series:
    """log(clip(L, LEV_FLOOR, LEV_CAP)); L <= 0 or EBITDA <= 0 reads as LEV_CAP. Intuition: a firm without EBITDA is
    the most levered firm, not a missing one."""
    lv = leverage.astype(float).where((leverage > 0) & (ebitda > 0), LEV_CAP)
    lv = lv.where(leverage.notna() | ebitda.notna())
    return np.log(lv.clip(lower=LEV_FLOOR, upper=LEV_CAP))


def ltm_quarterly(cq: pd.DataFrame, dt: pd.Timestamp, cols: tuple[str, ...]) -> pd.DataFrame:
    """Sum of the last four quarters of each column in `cols` per gvkey, from rows known at dt.

    The latest version of each quarter wins. A firm needs four consecutive quarters, the latest at most STALE_DAYS
    (F08) old. A column absent from the panel gives NaN."""
    c = cq[pd.to_datetime(cq["available_at"]) <= dt].copy()
    if c.empty:
        return pd.DataFrame(columns=list(cols))
    c["datadate"] = pd.to_datetime(c["datadate"])
    c = c.sort_values("available_at").drop_duplicates(["gvkey", "datadate"], keep="last")
    c = c.sort_values(["gvkey", "datadate"]).groupby("gvkey").tail(4)
    rows = {}
    for g, q in c.groupby("gvkey"):
        if len(q) < 4 or (dt - q["datadate"].iloc[-1]).days > STALE_DAYS or not _consecutive(q["datadate"]):
            continue
        rows[g] = {k: float(_col(q, k).sum(min_count=4)) for k in cols}
    return pd.DataFrame.from_dict(rows, orient="index", columns=list(cols))


def annual_latest(ca: pd.DataFrame, dt: pd.Timestamp) -> pd.DataFrame:
    """Latest fiscal year per gvkey known at dt (F09 `known_annual`), at most SUST_STALE_DAYS old. Index gvkey."""
    a = known_annual(ca, dt)
    if a.empty:
        return pd.DataFrame()
    a = a.sort_values(["gvkey", "fyear"]).drop_duplicates("gvkey", keep="last")
    return a[(dt - a["datadate"]).dt.days <= SUST_STALE_DAYS].set_index("gvkey")


def issuer_drivers(panels: Mapping[str, pd.DataFrame], as_of) -> pd.DataFrame:
    """All drivers of DRIVER_NAMES per gvkey at month end as_of (module docstring). Index gvkey.

    Reads only rows with available_at <= decision_time(as_of). A missing panel leaves its drivers NaN."""
    as_of = month_end(as_of)
    dt = decision_time(as_of)
    keys: set = set()
    parts: dict[str, pd.Series] = {}
    lv = leverage_now(panels["leverage"], as_of, dt) if present(panels, "leverage") else pd.DataFrame(
        columns=["leverage", "ltm_ebitda", "debt"])
    keys |= set(lv.index)
    parts["log_lev"] = capped_log_leverage(lv["leverage"], lv["ltm_ebitda"])

    q = pd.DataFrame()
    if present(panels, "compustat_quarterly"):
        q = ltm_quarterly(panels["compustat_quarterly"], dt, ("xintq", "capx", "saleq", "oancf"))
        keys |= set(q.index)
        cq = panels["compustat_quarterly"]
        if {"oibdpq", "saleq"} <= set(cq.columns):
            m = issuer_margins(cq, dt).set_index("gvkey")
            keys |= set(m.index)
            parts["margin"] = m["margin"].astype(float)
            parts["margin_trend"] = m["margin_trend"].astype(float).clip(-TREND_CLIP, TREND_CLIP)
    a = annual_latest(panels["compustat_annual"], dt) if present(panels, "compustat_annual") else pd.DataFrame()
    keys |= set(a.index)

    idx = pd.Index(sorted(keys, key=str), name="gvkey")
    out = pd.DataFrame(index=idx)
    for k, v in parts.items():
        out[k] = v.reindex(idx)
    lvx = lv.reindex(idx)
    qx = q.reindex(idx) if len(q) else pd.DataFrame(index=idx)
    ax = a.reindex(idx) if len(a) else pd.DataFrame(index=idx)

    def pick(qcol: str, acol: str) -> pd.Series:
        return _col(qx, qcol).fillna(_col(ax, acol))

    interest, capx, sale, cfo = pick("xintq", "xint"), pick("capx", "capx"), pick("saleq", "sale"), pick("oancf", "oancf")
    ebitda, debt = lvx["ltm_ebitda"].astype(float), lvx["debt"].astype(float)
    out["coverage"] = (ebitda / interest.where(interest > 0)).clip(*COVER_CLIP)
    out.loc[(interest == 0) & (ebitda > 0), "coverage"] = COVER_CLIP[1]
    out["capex_int"] = (capx / sale.where(sale > 0)).clip(0.0, 2.0)
    out["fcf_debt"] = ((cfo - capx) / debt.where(debt > 0)).clip(-1.0, 1.0)
    s, cogs = _col(ax, "sale"), _col(ax, "cogs")
    out["gross_margin"] = (s - cogs) / s.where(s > 0)
    adebt = _col(ax, "dlc") + _col(ax, "dltt")
    out["mat_wall"] = ((_col(ax, "dd1").fillna(0.0) + _col(ax, "dd2").fillna(0.0)) / adebt.where(adebt > 0))
    out.loc[_col(ax, "dd1").isna() & _col(ax, "dd2").isna(), "mat_wall"] = np.nan
    out["mat_wall"] = out["mat_wall"].clip(0.0, 1.0)
    rent = _col(ax, "xrent")
    den = ebitda + rent
    lease = (debt + LEASE_MULTIPLE * rent) / den.where(den > 0)
    out["log_lev_lease"] = np.log(lease.where(rent.notna()).clip(lower=LEV_FLOOR, upper=LEV_CAP))
    out.loc[rent.notna() & (den <= 0), "log_lev_lease"] = np.log(LEV_CAP)
    out["ebitda_cyc"] = np.nan
    if present(panels, "annual_ebitda"):
        e = known_annual(panels["annual_ebitda"], dt)
        if len(e):
            e = e.assign(fyear=e["fyear"].astype(int))
            last = e.sort_values(["gvkey", "fyear"]).drop_duplicates("gvkey", keep="last")
            last = last[(dt - last["datadate"]).dt.days <= SUST_STALE_DAYS].set_index("gvkey")["fyear"]
            cyc = cyclicality(e[["gvkey", "fyear", "oibdp"]], last).set_index("gvkey")["cyclicality"]
            out = out.reindex(out.index.union(cyc.index).rename("gvkey"))
            out["ebitda_cyc"] = cyc.reindex(out.index).astype(float)
    for k in DRIVER_NAMES:
        if k not in out:
            out[k] = np.nan
    return out[list(DRIVER_NAMES)].astype(float)
