"""Shared steps of the sector package: the scored bond universe at a month end and the GICS sector groups.
Spec docs/factors/SECTOR-models.md, section 3; methodology Sections 7.2 (sector effect) and 8 (S1, S4).

    universe(t)  = bonds at month end t with a real trade (`hy.backtest.eligible`), spread below 1,000 bp
                   (`hy.backtest.not_distressed`), a gvkey, a GICS sector in force at t, and, when `ratings` exists,
                   an HY class (BB, B, CCC) that is not a default symbol
    group(i)     = SECTOR_GROUPS[GICS sector of i]; financials (40) and real estate (60) get no group

Every input is filtered to `available_at` <= hy.backtest.decision_time(t). Without `bond_panel` or `gics` the universe
is empty.
"""

from __future__ import annotations

from typing import Mapping

import numpy as np
import pandas as pd

from hy.backtest import decision_time, eligible, not_distressed
from hy.factors.f04_bond_momentum import rating_classes
from hy.peers import FIN_SECTORS, maturity_bucket, sector_at

# GICS two-digit sector -> model group. Our choice: one group per GICS sector. GICS 40 and 60 have no group,
# because debt over EBITDA does not measure a bank or a REIT (SPiDER rule of hy.peers, FIN_SECTORS).
SECTOR_GROUPS: dict[str, str] = {
    "10": "energy",
    "15": "materials",
    "20": "industrials",
    "25": "consumer_disc",
    "30": "consumer_staples",
    "35": "health_care",
    "45": "technology",
    "50": "telecom_media",
    "55": "utilities",
}
HY_CLASSES = ("BB", "B", "CCC")       # scored classes (as F04, F10)
DEFAULT_SYMBOLS = ("D", "SD")         # raw S&P symbols of a defaulted issuer: never scored (as F04, F10)

UNIVERSE_COLS = ["cusip", "gvkey", "years", "g_spread", "mod_dur", "price", "coupon", "gsector", "group", "rclass",
                 "mat_bucket", "dts"]


def present(panels: Mapping[str, pd.DataFrame], name: str) -> bool:
    """True when the panel exists and has rows."""
    return panels.get(name) is not None and len(panels[name]) > 0


def month_end(as_of) -> pd.Timestamp:
    """The month end of `as_of`."""
    return pd.Timestamp(as_of) + pd.offsets.MonthEnd(0)


def gsector_at(gics: pd.DataFrame | None, as_of: pd.Timestamp) -> pd.Series:
    """Two-digit GICS sector per gvkey in force at as_of, from rows known at the decision time (`hy.peers.sector_at`).

    The code is read as the first two digits, so 10, 10.0 and "10" all give "10"."""
    if gics is None or not len(gics):
        return pd.Series(dtype=object)
    g = gics[pd.to_datetime(gics["available_at"]) <= decision_time(as_of)].copy()
    if g.empty:
        return pd.Series(dtype=object)
    g["indfrom"] = pd.to_datetime(g["indfrom"])
    g["indthru"] = pd.to_datetime(g["indthru"])
    return sector_at(g, as_of).str.extract(r"^(\d{2})")[0].dropna()


def universe(panels: Mapping[str, pd.DataFrame], as_of) -> pd.DataFrame:
    """Scored bonds at month end as_of (module docstring). One row per cusip, columns UNIVERSE_COLS.

    `rclass` is the actual S&P class, else the leverage-implied class (F04 `rating_classes`), NaN without `ratings`.
    `dts` = mod_dur x g_spread (decimal spread), the bond's spread risk."""
    as_of = month_end(as_of)
    if not (present(panels, "bond_panel") and present(panels, "gics")):
        return pd.DataFrame(columns=UNIVERSE_COLS)
    dt = decision_time(as_of)
    p = panels["bond_panel"]
    p = p[pd.to_datetime(p["available_at"]) <= dt].copy()
    p["date"] = pd.to_datetime(p["date"])
    now = p[p["date"] == as_of].sort_values("available_at").drop_duplicates("cusip", keep="last")
    if now.empty:
        return pd.DataFrame(columns=UNIVERSE_COLS)
    now = now[eligible(now) & not_distressed(now) & now["gvkey"].notna()].copy()
    now["gsector"] = now["gvkey"].map(gsector_at(panels["gics"], as_of))
    now["group"] = now["gsector"].map(SECTOR_GROUPS)
    now = now[now["gsector"].notna() & ~now["gsector"].isin(FIN_SECTORS) & now["group"].notna()]
    if present(panels, "ratings"):
        cls = rating_classes(panels["ratings"], panels.get("leverage"), as_of)
        now["rclass"] = now["gvkey"].map(cls["rclass"])
        raw = now["gvkey"].map(cls["raw"])
        now = now[now["rclass"].isin(HY_CLASSES) & ~raw.isin(DEFAULT_SYMBOLS)]
    else:
        now["rclass"] = np.nan
    if "coupon" not in now:
        now["coupon"] = np.nan
    now["mat_bucket"] = now["years"].astype(float).map(maturity_bucket)
    now["dts"] = now["mod_dur"].astype(float) * now["g_spread"].astype(float)
    return now[UNIVERSE_COLS].reset_index(drop=True)
