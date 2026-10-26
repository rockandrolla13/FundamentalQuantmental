"""F21 Refinancing headroom against cyclicality (rank 21). Spec docs/factors/F21-refinancing-headroom.md; methodology
Section 4.2 (cash flow and liquidity, `wall_cover_h`) and Section 9 (event-driven positional risk). Sources: Morgan
Stanley, "Stressing Growth and High Yield" (Aug 2011), pp. 5 to 7; "High Yield: Looking for the Best in Stress"
(Sep 2011), p. 4; European single-name spec v. 080212, Step 4B, PDF p. 12. Breadth column: MS Apr 2011, p. 3.

    L         = CHE + RCF                                          cash plus undrawn revolver (Sep p. 4; RCF our choice)
    A_k       = L + k (E - XINT - CAPX) - sum_{j<=k} DDj,  k = 1, 2  liquidity left after year k at no EBITDA cut
    H         = clip_[0,1]( min_k A_k / (w_k E) )                  largest two-year cut before refinancing (Aug p. 5)
    C         = - min_y max((E_y - E_y-1) / E_y-1, -1)              worst YoY EBITDA fall, last 10 years (Sep p. 4)
    S         = H - C                                              positive = above the line = add risk (Aug p. 6)

Path "linear" (default): year-k EBITDA is E (1 - d k / 2), so w = (1/2, 3/2) and the cut reaches d at month 24
("Cumulative Linear EBITDA Decline", Aug p. 7). Path "flat": both years cut by d, w = (1, 2). Both our choice.
Intuition: S > 0 means the issuer survives a repeat of its own worst year for two years without the market.

Inputs. A panel `compustat_annual` (the F09 panel): `gvkey`, `datadate`, `fyear`, `che`, `xint`, `capx`, `dd1`,
`dd2`, `available_at`; optional `dd3`, `dd4`, `dd5` and `revolver_undrawn` (10-K text). A missing or NaN revolver
counts as 0 and sets `revolver_missing`; a NaN `dd1` or `dd2` counts as 0 and sets `mat_missing`. `annual_ebitda`
gives `oibdp` (E, history for C) and `debt` (breadth). `gics` sets the financials (GICS 40 and 60) to NaN. A row is
known at max(available_at, datadate + ANNUAL_LAG_DAYS). Without `compustat_annual`, `annual_ebitda`, `gics` or
`bond_panel` the score is empty.

No source tests S on returns or on defaults. The first test is a 24-month default test (AUC, default rate by S
quintile) on the production machine; `issuer_scores` gives its issuer-level input.
"""

from __future__ import annotations

from typing import Mapping

import numpy as np
import pandas as pd

from hy.backtest import decision_time, eligible
from hy.factors.f09_profitability_change import known_annual
from hy.peers import FIN_SECTORS, SUST_STALE_DAYS, sector_at

WINDOW_YEARS = 2         # refinancing window: "debt due over the next two years" (Aug p. 5)
CYCLE_YEARS = 10         # cyclicality look-back: "over the last decade" (Sep p. 4)
MIN_CHANGES = 3          # fewest YoY changes for a cyclicality value (our choice)
CHANGE_FLOOR = -1.0      # a YoY change is floored at -100%, the axis floor (Sep p. 4, Exhibit 7)
H_MIN, H_MAX = 0.0, 1.0  # headroom range: the source axes run from 0% to -100% (Sep p. 4)
PATH_WEIGHTS = {"linear": (0.5, 1.5), "flat": (1.0, 2.0)}  # cumulative cut weights by year end (our choice)
BREADTH_PEAK = 0.70      # share delevering YoY that "has recently marked the peak of market breadth" (Apr 2011 p. 3)
HORIZON = 24             # months: the refinancing window and the PD test horizon (Aug p. 5; reader block H-F4)

META = {
    "rank": 21,
    "name": "Refinancing headroom against cyclicality",
    "level": "bond",
    "horizon_months": HORIZON,
    "needs": ["bond_panel", "compustat_annual", "annual_ebitda", "gics"],
    "spec": "docs/factors/F21-refinancing-headroom.md",
    "section": "4.2",
}

ISSUER_COLS = ["gvkey", "score", "headroom", "headroom_raw", "cyclicality", "cover_ratio", "n_changes", "fyear",
               "liquidity", "mat_2y", "mat_3_5y", "fails_at_zero", "revolver_missing", "mat_missing"]
BOND_COLS = ["date", "cusip", "score", "available_at"] + ISSUER_COLS[:1] + ISSUER_COLS[2:] + \
    ["delever_breadth", "breadth_peak"]


def headroom(cash: pd.Series, revolver: pd.Series, ebitda: pd.Series, xint: pd.Series, capx: pd.Series,
             dd1: pd.Series, dd2: pd.Series, path: str = "linear") -> pd.DataFrame:
    """Two-year refinancing headroom H (spec Definition; Aug p. 5, Sep p. 4, European spec p. 12). The issuer must
    refinance once cash plus revolver plus cumulative cash flow falls short of the maturities due, tested at the end
    of years 1 and 2. A_k is linear in the cut d, so H = min_k A_k / (w_k E), clipped to [0, 1]. E <= 0 gives H = 0
    when the test already fails at d = 0, else NaN. Inputs are NaN-free except `ebitda`, `cash`, `xint`, `capx`.
    Columns: headroom, headroom_raw, fails_at_zero, liquidity. Intuition: the cut the balance sheet can absorb."""
    w1, w2 = PATH_WEIGHTS[path]
    e = ebitda.astype(float)
    liq = cash.astype(float) + revolver.astype(float)
    fcf = e - xint.astype(float) - capx.astype(float)
    a1 = liq + fcf - dd1.astype(float)
    a2 = liq + 2.0 * fcf - dd1.astype(float) - dd2.astype(float)
    ok = e > 0
    raw = np.minimum(a1 / (w1 * e.where(ok)), a2 / (w2 * e.where(ok)))
    fails = (np.minimum(a1, a2) < 0) & a1.notna() & a2.notna()
    h = raw.clip(H_MIN, H_MAX).where(ok, np.where(fails, H_MIN, np.nan))
    return pd.DataFrame({"headroom": h.astype(float), "headroom_raw": raw.astype(float), "fails_at_zero": fails,
                         "liquidity": liq})


def yoy_changes(ebitda: pd.DataFrame) -> pd.DataFrame:
    """Year-on-year EBITDA change per (gvkey, fyear) (Sep p. 4). NaN unless the prior fiscal year exists with a
    positive EBITDA. Floored at CHANGE_FLOOR. Input: one row per (gvkey, fyear) with `oibdp`. Adds `change`."""
    e = ebitda.sort_values(["gvkey", "fyear"]).copy()
    prev = e.groupby("gvkey")["oibdp"].shift(1).astype(float)
    consecutive = e.groupby("gvkey")["fyear"].diff() == 1
    chg = (e["oibdp"].astype(float) - prev) / prev.where(consecutive & (prev > 0))
    return e.assign(change=chg.clip(lower=CHANGE_FLOOR))


def cyclicality(ebitda: pd.DataFrame, last_fyear: pd.Series, years: int = CYCLE_YEARS) -> pd.DataFrame:
    """C = minus the worst YoY EBITDA change over fiscal years y - years + 1 to y, y = `last_fyear` per gvkey (Sep
    p. 4: "worst year-on-year LTM EBITDA performance over the last decade"). NaN below MIN_CHANGES changes. C < 0
    when EBITDA never fell. Columns: gvkey, cyclicality, n_changes. Intuition: how hard the issuer's worst year hit."""
    e = yoy_changes(ebitda)
    y = e["gvkey"].map(last_fyear)
    e = e[(e["fyear"] <= y) & (e["fyear"] > y - years) & e["change"].notna()]
    g = e.groupby("gvkey")["change"]
    out = pd.DataFrame({"cyclicality": -g.min(), "n_changes": g.size()}).reindex(last_fyear.index)
    out["n_changes"] = out["n_changes"].fillna(0).astype(int)
    out.loc[out["n_changes"] < MIN_CHANGES, "cyclicality"] = np.nan
    return out.rename_axis("gvkey").reset_index()


def delever_breadth(ebitda: pd.DataFrame, last_fyear: pd.Series) -> float:
    """Share of the issuers in `last_fyear` whose debt / EBITDA fell from y - 1 to y (Apr 2011 p. 3: "% of issuers
    deleveraging YoY"). Both years need a positive EBITDA. NaN with no valid issuer. Intuition: how broad the
    repair of balance sheets is. A market reading, not a bond score."""
    e = ebitda[ebitda["gvkey"].isin(last_fyear.index) & (ebitda["oibdp"] > 0)]
    lev = e.set_index(["gvkey", "fyear"])["debt"].astype(float) / e.set_index(["gvkey", "fyear"])["oibdp"]
    y = last_fyear.astype(int)
    now = lev.reindex(list(zip(y.index, y))).to_numpy()
    before = lev.reindex(list(zip(y.index, y - 1))).to_numpy()
    valid = ~(np.isnan(now) | np.isnan(before))
    return float((now[valid] < before[valid]).mean()) if valid.any() else np.nan


def issuer_scores(panels: Mapping[str, pd.DataFrame], dt: pd.Timestamp, path: str = "linear",
                  use_revolver: bool = True) -> pd.DataFrame:
    """S = H - C per gvkey at decision time dt (spec build steps 1 to 5). y(t) is the latest fiscal year of
    `compustat_annual` known at dt, at most SUST_STALE_DAYS old. E is `annual_ebitda.oibdp` of y(t). Financials get
    NaN. Columns ISSUER_COLS. The issuer-level input of the PD test."""
    a = known_annual(panels["compustat_annual"], dt)
    e = known_annual(panels["annual_ebitda"], dt)[["gvkey", "fyear", "oibdp", "debt"]]
    if a.empty:
        return pd.DataFrame(columns=ISSUER_COLS)
    a = a.assign(fyear=a["fyear"].astype(int)).sort_values(["gvkey", "fyear"]).drop_duplicates("gvkey", keep="last")
    a = a[(dt - a["datadate"]).dt.days <= SUST_STALE_DAYS]
    e = e.assign(fyear=e["fyear"].astype(int))
    a = a.merge(e[["gvkey", "fyear", "oibdp"]], on=["gvkey", "fyear"], how="left")
    rcf = a["revolver_undrawn"] if use_revolver and "revolver_undrawn" in a else pd.Series(np.nan, index=a.index)
    dd = {k: a[k] if k in a else pd.Series(np.nan, index=a.index) for k in ("dd1", "dd2", "dd3", "dd4", "dd5")}
    h = headroom(a["che"], rcf.fillna(0.0), a["oibdp"], a["xint"], a["capx"], dd["dd1"].fillna(0.0),
                 dd["dd2"].fillna(0.0), path)
    out = pd.concat([a[["gvkey", "fyear"]], h], axis=1)
    out["mat_2y"] = dd["dd1"].fillna(0.0) + dd["dd2"].fillna(0.0)
    out["mat_3_5y"] = dd["dd3"] + dd["dd4"] + dd["dd5"]
    out["revolver_missing"] = rcf.isna().to_numpy()
    out["mat_missing"] = (dd["dd1"].isna() | dd["dd2"].isna()).to_numpy()
    cyc = cyclicality(e, a.set_index("gvkey")["fyear"])
    out = out.merge(cyc, on="gvkey", how="left")
    out["score"] = out["headroom"] - out["cyclicality"]
    out["cover_ratio"] = out["headroom"] / out["cyclicality"].where(out["cyclicality"] > 0)
    g = panels["gics"]
    sector = sector_at(g[g["available_at"] <= dt], dt)
    out.loc[out["gvkey"].map(sector).isin(FIN_SECTORS), "score"] = np.nan
    floats = ["score", "headroom", "headroom_raw", "cyclicality", "cover_ratio", "liquidity", "mat_2y", "mat_3_5y"]
    return out[ISSUER_COLS].astype({c: float for c in floats}).reset_index(drop=True)


def compute(panels: Mapping[str, pd.DataFrame], as_of: pd.Timestamp, path: str = "linear",
            use_revolver: bool = True) -> pd.DataFrame:
    """S per eligible bond of bond_panel at as_of (spec build step 6). One row per cusip. score = the issuer S, NaN
    where the issuer has none or is a financial. `delever_breadth` is one value over the scored issuers. Empty
    frame (columns BOND_COLS) when a panel of META["needs"] is missing. Higher score = long (Aug p. 6)."""
    as_of = pd.Timestamp(as_of)
    if any(panels.get(k) is None or len(panels[k]) == 0 for k in META["needs"]):
        return pd.DataFrame(columns=BOND_COLS)
    dt = decision_time(as_of)
    iss = issuer_scores(panels, dt, path, use_revolver)
    p = panels["bond_panel"]
    p = p[(p["available_at"] <= dt) & (pd.to_datetime(p["date"]) == as_of)]
    p = p[eligible(p) & p["gvkey"].notna()].drop_duplicates("cusip", keep="last")
    if p.empty:
        return pd.DataFrame(columns=BOND_COLS)
    out = p[["cusip", "gvkey"]].merge(iss, on="gvkey", how="left")
    scored = iss[iss["gvkey"].isin(out["gvkey"]) & iss["score"].notna()].set_index("gvkey")["fyear"]
    ebitda = known_annual(panels["annual_ebitda"], dt)
    breadth = delever_breadth(ebitda.assign(fyear=ebitda["fyear"].astype(int)), scored)
    out["delever_breadth"] = breadth
    out["breadth_peak"] = bool(breadth > BREADTH_PEAK) if np.isfinite(breadth) else False
    out["date"] = as_of
    out["available_at"] = dt
    return out[BOND_COLS].astype({"score": float}).reset_index(drop=True)
