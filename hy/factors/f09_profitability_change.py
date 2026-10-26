"""F09 Profitability change over 5 years (rank 9). Spec docs/factors/F09-profitability-change.md; methodology
Section 8 (S2 fundamental momentum) and Section 11 (backtest design). Source: Kelly, Palhares, Pruitt (2021),
SSRN 3720789, Table A.I (p. 55); results Table I (p. 16) and Table IX (p. 31). PDF page = printed page.

    Prof_i,y   = (SALE_i,y - COGS_i,y) / AT_i,y                 gross profit over total assets, non-financials (p. 55)
    dProf_i,t  = Prof_i,y(t) - Prof_i,y(t)-W,   W = 5           "the 5-year change in profitability" (p. 55)
    rank_i,t   = cross-bond rank of dProf mapped to [-0.5, 0.5]  (p. 15)

y(t) is the latest fiscal year known at the decision time. y(t) - W is matched on `fyear` (our choice).
Intuition: an issuer whose gross margin on assets improves becomes safer than its spread says.

Inputs. A new panel `compustat_annual`: one row per gvkey and fiscal year with `gvkey`, `datadate` (fiscal year
end), `fyear`, `sale`, `cogs`, `at` (comp.funda SALE, COGS, AT) and `available_at`. The production panel
`annual_ebitda` has no SALE, COGS or AT, so it cannot serve, and no proxy replaces them. A row is known at
max(available_at, datadate + ANNUAL_LAG_DAYS). `gics` sets the financials (GICS 40 and 60) to NaN. Without
`compustat_annual`, `gics` or `bond_panel` the score is empty.

Minimum history: a valid Prof (fields present, AT > 0) in both y(t) and y(t) - W. The latest record is at most
SUST_STALE_DAYS old. compute() copies the issuer dProf to each eligible bond of the issuer at as_of.
"""

from __future__ import annotations

from typing import Mapping

import numpy as np
import pandas as pd

from hy.backtest import decision_time, eligible
from hy.peers import FIN_SECTORS, SUST_STALE_DAYS, sector_at
from hy.sources.peer_data import ANNUAL_LAG_DAYS

WINDOW = 5           # years between the two fiscal years of the change (Table A.I, p. 55)
SHORT_WINDOW = 3     # robustness window for short HY histories (reader block A2-F7; our choice)
HORIZON = 1          # months: the source predicts the next month's DtS-scaled return (eq. 10, p. 14)

META = {
    "rank": 9,
    "name": "Profitability change over 5 years",
    "level": "bond",
    "horizon_months": HORIZON,
    "needs": ["bond_panel", "compustat_annual", "gics"],
    "spec": "docs/factors/F09-profitability-change.md",
    "section": "8",
}

ISSUER_COLS = ["gvkey", "score", "prof", "prof_lag", "fyear", "fyear_lag"]
BOND_COLS = ["date", "cusip", "score", "available_at", "gvkey", "rank", "prof", "prof_lag", "fyear", "fyear_lag"]


def profitability(sale: pd.Series, cogs: pd.Series, at: pd.Series) -> pd.Series:
    """Prof = (SALE - COGS) / AT for non-financials (Table A.I, p. 55; spec Definition). NaN where a field is
    missing or AT <= 0. Intuition: gross profit per unit of assets."""
    at = at.astype(float)
    return ((sale.astype(float) - cogs.astype(float)) / at.where(at > 0)).rename("prof")


def known_annual(annual: pd.DataFrame, dt: pd.Timestamp) -> pd.DataFrame:
    """Rows of `compustat_annual` known at decision time dt: max(available_at, datadate + ANNUAL_LAG_DAYS) <= dt
    (spec Inputs). One row per (gvkey, fyear): the one known last."""
    a = annual[annual["fyear"].notna()].copy()
    a["datadate"] = pd.to_datetime(a["datadate"])
    known = np.maximum(pd.to_datetime(a["available_at"]), a["datadate"] + pd.Timedelta(ANNUAL_LAG_DAYS, unit="D"))
    a = a.assign(known_at=known)[known <= dt]
    return a.sort_values("known_at").drop_duplicates(["gvkey", "fyear"], keep="last")


def profitability_change(annual: pd.DataFrame, dt: pd.Timestamp, window: int = WINDOW) -> pd.DataFrame:
    """dProf per gvkey at decision time dt (spec build steps 2 to 5; Table A.I, p. 55): Prof of the latest fiscal
    year y known at dt minus Prof of fiscal year y - window. NaN unless both ends are valid. Drops an issuer whose
    latest record is older than SUST_STALE_DAYS. Columns ISSUER_COLS."""
    a = known_annual(annual, dt)
    if a.empty:
        return pd.DataFrame(columns=ISSUER_COLS)
    a = a.assign(prof=profitability(a["sale"], a["cogs"], a["at"]), fyear=a["fyear"].astype(int))
    last = a.sort_values(["gvkey", "fyear"]).drop_duplicates("gvkey", keep="last")
    last = last[(dt - last["datadate"]).dt.days <= SUST_STALE_DAYS]
    lag = a[["gvkey", "fyear", "prof"]].rename(columns={"fyear": "fyear_lag", "prof": "prof_lag"})
    out = last[["gvkey", "fyear", "prof"]].assign(fyear_lag=last["fyear"] - window)
    out = out.merge(lag, on=["gvkey", "fyear_lag"], how="left")
    out["score"] = out["prof"] - out["prof_lag"]
    return out[ISSUER_COLS].astype({"score": float, "prof": float, "prof_lag": float}).reset_index(drop=True)


def rank_unit(x: pd.Series) -> pd.Series:
    """Cross-sectional rank mapped to [-0.5, 0.5]: lowest -0.5, highest +0.5, ties averaged (p. 15). NaN stays NaN.
    A single value maps to 0. Intuition: the paper's scale, which caps outliers."""
    n = x.notna().sum()
    if n <= 1:
        return pd.Series(np.where(x.notna(), 0.0, np.nan), index=x.index)
    return (x.rank(method="average") - 1.0) / (n - 1.0) - 0.5


def compute(panels: Mapping[str, pd.DataFrame], as_of: pd.Timestamp, window: int = WINDOW) -> pd.DataFrame:
    """dProf per eligible bond of bond_panel at as_of (spec build steps 6 and 7). One row per cusip. score = the
    issuer dProf, NaN where the issuer has none or is a financial. Empty frame (columns BOND_COLS) when
    compustat_annual, gics or bond_panel is missing. Higher score = long (Table I, p. 16: Sharpe +0.60)."""
    as_of = pd.Timestamp(as_of)
    if any(panels.get(k) is None or len(panels[k]) == 0 for k in META["needs"]):
        return pd.DataFrame(columns=BOND_COLS)
    dt = decision_time(as_of)
    iss = profitability_change(panels["compustat_annual"], dt, window)
    g = panels["gics"]
    sector = sector_at(g[g["available_at"] <= dt], as_of)
    iss.loc[iss["gvkey"].map(sector).isin(FIN_SECTORS), "score"] = np.nan
    p = panels["bond_panel"]
    p = p[(p["available_at"] <= dt) & (pd.to_datetime(p["date"]) == as_of)]
    p = p[eligible(p) & p["gvkey"].notna()].drop_duplicates("cusip", keep="last")
    if p.empty:
        return pd.DataFrame(columns=BOND_COLS)
    out = p[["cusip", "gvkey"]].merge(iss, on="gvkey", how="left")
    out["rank"] = rank_unit(out["score"])
    out["date"] = as_of
    out["available_at"] = dt
    return out[BOND_COLS].astype({"score": float, "rank": float}).reset_index(drop=True)
