"""F24 Rating x tenor cell valuation percentile, with the BB/BBB and B/BB spread ratios (rank 24). Spec
docs/factors/F24-cell-percentile.md; methodology Section 8 (S7 slot, S1 value). Sources: Nicol, Deutsche Bank HY
Strategy, 2 March 2021, p. 5 (Figs. 7 and 8); Nicol, Global Leveraged Finance Weekly, 5 March 2021, pp. 7 to 8;
Jezek, Macro Credit Brief, 22 February 2021, pp. 11 to 13. Pages are PDF pages.

    m_c,t     = median of s_i,t over the eligible bonds of cell c = rating x tenor at t      cell spread
    P_c,t     = share of prior months tau in W_t with m_c,tau < m_c,t                         own-history percentile
    score_i,t = P_c(i),t                                                                      high = wide = cheap
    R^BB/BBB  = m_BB,1-3y / m_BBB,1-3y,  R^B/BB = m_B,1-3y / m_BB,1-3y                         cross-rating ratios

Intuition: every cell moves with the cycle, so the cell's own history is the peer group that controls for its
structural spread level.

Convention. The HY note puts 100% at the tights (p. 5). The IG brief says x% means the series "has been lower x%
of the time" (p. 11). We use the IG brief form: a high P means wide, so cheap, so long.

Cells. Rating BBB, BB, B, CCC x tenor 1-3, 3-5, 5-7, 7-10 years (p. 5) and 10+ years (p. 12). CCC is one pooled
cell, because the note drops CCC curve points for lack of market size (p. 5). The rating class is the one of
`hy.factors.f04_bond_momentum.rating_classes`: S&P to February 2017, then the leverage-implied class. Class IG maps
to BBB when the raw symbol is BBB+, BBB or BBB-, or when the class is implied (no symbol). A to AAA have no cell.

Inputs. `bond_panel` and `ratings` are required, `leverage` is optional (without it, an issuer with no S&P rating
on file has no class). Optional panel `cell_history`: the output of `cell_history`, columns HIST_COLS, with
`available_at` = decision_time(date). It is a cache. Without it, compute() rebuilds the history from bond_panel.
Without `bond_panel` or `ratings` the result is empty (columns COLS).

Evidence. The sources give snapshots only (February and March 2021). No backtest, hit rate or horizon exists.
"""

from __future__ import annotations

from typing import Mapping

import numpy as np
import pandas as pd

from hy.backtest import decision_time, eligible
from hy.factors.f04_bond_momentum import DEFAULT_SYMBOLS, rating_classes
from hy.peers import MIN_PEERS, rating_class

TENOR_EDGES = (3.0, 5.0, 7.0, 10.0)                     # 1-3, 3-5, 5-7, 7-10y (p. 5 Fig. 7) and 10+y (p. 12)
TENOR_LABELS = ("1-3", "3-5", "5-7", "7-10", "10+")
CELL_RATINGS = ("BBB", "BB", "B", "CCC")                # rating rows of p. 5 Fig. 7
POOLED_RATINGS = ("CCC",)                               # one cell across tenors (p. 5: "lack of market size")
POOLED_TENOR = "all"
HY_RATINGS = ("BB", "B", "CCC")                         # scored classes (spec build step 7, our choice)
MIN_ISSUERS = MIN_PEERS                                 # issuers a cell-month needs for a median (our choice)
MIN_HISTORY_YEARS = 3                                   # prior years of medians a percentile needs (our choice)
WINDOW_MONTHS = None                                    # None = expanding window (spec section 3, our choice)
RATIO_TENOR = "1-3"                                     # tenor of the BB/BBB and B/BB ratios (p. 5 Fig. 8)
HOLD = 3                                                # horizon in months: the sources give none (our choice)

META = {
    "rank": 24,
    "name": "Rating x tenor cell valuation percentile",
    "level": "bond",
    "horizon_months": HOLD,
    "needs": ["bond_panel", "ratings", "leverage", "cell_history"],
    "spec": "docs/factors/F24-cell-percentile.md",
    "section": "8",
}
REQUIRED = ("bond_panel", "ratings")

HIST_COLS = ["date", "cell", "rating", "tenor", "median_spread", "n_bonds", "n_issuers", "available_at"]
COLS = ["date", "cusip", "score", "available_at", "gvkey", "rating", "rclass_src", "tenor", "cell", "g_spread",
        "cell_spread", "cell_pct", "cell_n_hist", "cell_n_issuers", "ratio_bb_bbb", "ratio_b_bb",
        "ratio_bb_bbb_pct", "ratio_b_bb_pct"]


# ---------------------------------------------------------------- cells


def tenor_bucket(years: pd.Series) -> pd.Series:
    """Tenor label per bond from years to maturity (p. 5 Fig. 7, p. 12): 1-3, 3-5, 5-7, 7-10, 10+. A bucket holds
    its upper edge, so 3.0 years is 1-3. NaN years give NaN."""
    y = years.astype(float)
    idx = np.searchsorted(TENOR_EDGES, y.to_numpy(), side="left")
    lab = pd.Series(np.asarray(TENOR_LABELS, dtype=object)[np.minimum(idx, len(TENOR_LABELS) - 1)], index=y.index)
    return lab.where(y.notna())


def cell_rating(rclass: pd.Series, raw: pd.Series) -> pd.Series:
    """Cell rating per issuer (spec section 3). BB, B, CCC as the class. IG is BBB when the raw S&P symbol is in the
    BBB family or missing (implied class), else NaN (A and better). Intuition: the sources rank BBB, not all IG."""
    r = rclass.astype(object)
    sym = raw.astype(object).where(raw.notna())
    base = sym.dropna().astype(str).str.strip().str.upper().str.rstrip("+-").reindex(r.index)
    ig_bbb = (r == "IG") & (base.isna() | (base == "BBB"))
    out = r.where(r.isin(HY_RATINGS))
    return out.mask(ig_bbb, "BBB")


def cell_key(rating: pd.Series, tenor: pd.Series) -> pd.Series:
    """Cell label rating|tenor. A pooled rating (CCC) takes rating|all (p. 5). NaN where an input is missing."""
    t = tenor.astype(object).mask(rating.isin(POOLED_RATINGS), POOLED_TENOR)
    key = rating.astype(str) + "|" + t.astype(str)
    return key.where(rating.notna() & t.notna())


def month_cells(panels: Mapping[str, pd.DataFrame], month: pd.Timestamp) -> pd.DataFrame:
    """Bonds in a cell at month end `month`, as known at decision_time(month) (spec build steps 1 to 3).

    Rows: `eligible` bond_panel rows dated `month` with a gvkey, a cell rating and no D or SD symbol. Columns cusip,
    gvkey, g_spread, rating, rclass_src (actual or implied), tenor, cell."""
    cols = ["cusip", "gvkey", "g_spread", "rating", "rclass_src", "tenor", "cell"]
    month = pd.Timestamp(month) + pd.offsets.MonthEnd(0)
    dt = decision_time(month)
    p = panels["bond_panel"]
    p = p[(p["available_at"] <= dt) & (pd.to_datetime(p["date"]) == month)]
    p = p.sort_values("available_at").drop_duplicates("cusip", keep="last")
    p = p[eligible(p) & p["gvkey"].notna()]
    if p.empty:
        return pd.DataFrame(columns=cols)
    cls = rating_classes(panels["ratings"], panels.get("leverage"), month)
    rclass, raw = p["gvkey"].map(cls["rclass"]), p["gvkey"].map(cls["raw"])
    out = p[["cusip", "gvkey", "g_spread"]].copy()
    out["rating"] = cell_rating(rclass, raw)
    out["rclass_src"] = np.where(raw.map(rating_class).notna(), "actual", "implied")
    out["tenor"] = tenor_bucket(p["years"])
    out["cell"] = cell_key(out["rating"], out["tenor"])
    out = out[out["cell"].notna() & ~raw.astype(str).str.strip().str.upper().isin(DEFAULT_SYMBOLS)]
    return out[cols].reset_index(drop=True)


def cell_medians(bonds: pd.DataFrame, min_issuers: int = MIN_ISSUERS) -> pd.DataFrame:
    """Median G-spread per cell (spec definition, m_c,t). A cell with fewer than `min_issuers` distinct gvkeys has
    a NaN median. Intuition: the median is the typical bond, robust to one distressed name. Index cell, columns
    rating, tenor, median_spread, n_bonds, n_issuers."""
    if bonds.empty:
        return pd.DataFrame(columns=["rating", "tenor", "median_spread", "n_bonds", "n_issuers"],
                            index=pd.Index([], name="cell"))
    g = bonds.groupby("cell")
    out = pd.DataFrame({"rating": g["rating"].first(), "tenor": g["tenor"].first(),
                        "median_spread": g["g_spread"].median().astype(float), "n_bonds": g["cusip"].count(),
                        "n_issuers": g["gvkey"].nunique()})
    out.loc[out["rating"].isin(POOLED_RATINGS), "tenor"] = POOLED_TENOR
    out["median_spread"] = out["median_spread"].where(out["n_issuers"] >= min_issuers)
    return out


def _ns(df: pd.DataFrame) -> pd.DataFrame:
    """date and available_at as datetime64[ns], so frames built from scalars and from panels concatenate."""
    return df.assign(date=pd.to_datetime(df["date"]).astype("datetime64[ns]"),
                     available_at=pd.to_datetime(df["available_at"]).astype("datetime64[ns]"))


def cell_history(panels: Mapping[str, pd.DataFrame], months, min_issuers: int = MIN_ISSUERS) -> pd.DataFrame:
    """Cell medians for each month end in `months`, each as known at its own decision time (spec build step 5).
    Columns HIST_COLS, available_at = decision_time(date). The production machine may cache this frame as the
    panel `cell_history`."""
    parts = []
    for m in sorted({pd.Timestamp(x) + pd.offsets.MonthEnd(0) for x in months}):
        med = cell_medians(month_cells(panels, m), min_issuers)
        if len(med):
            parts.append(_ns(med.reset_index().assign(date=m, available_at=decision_time(m))))
    if not parts:
        return pd.DataFrame(columns=HIST_COLS)
    return pd.concat(parts, ignore_index=True)[HIST_COLS]


# ---------------------------------------------------------------- percentiles and ratios


def own_history_percentile(x: pd.Series, min_obs: int, window: int | None = WINDOW_MONTHS) -> pd.DataFrame:
    """P_t = share of the prior non-NaN values in the window that are strictly below x_t (spec definition; p. 11:
    "has been lower x% of the time"). `x` is indexed by month end. `window` None is expanding, else the last
    `window` months before t. NaN when x_t is NaN or fewer than `min_obs` prior values exist. Columns pct, n_hist.
    Intuition: 1 means the widest the cell has been, 0 the tightest."""
    s = x.sort_index().astype(float)
    vals, dates = s.to_numpy(), s.index
    pct, n_hist = np.full(len(s), np.nan), np.zeros(len(s), dtype=int)
    for i in range(len(s)):
        prior = dates < dates[i]
        if window is not None:
            prior &= dates >= dates[i] - pd.offsets.MonthEnd(int(window))
        h = vals[prior]
        h = h[~np.isnan(h)]
        n_hist[i] = len(h)
        if not np.isnan(vals[i]) and len(h) >= min_obs:
            pct[i] = float(np.mean(h < vals[i]))
    return pd.DataFrame({"pct": pct, "n_hist": n_hist}, index=dates)


def spread_ratios(wide: pd.DataFrame, tenor: str = RATIO_TENOR) -> pd.DataFrame:
    """R^BB/BBB and R^B/BB per month at one tenor (p. 5 Fig. 8). `wide` has months as index and cell labels as
    columns (median spreads). NaN where a cell is missing. Columns ratio_bb_bbb, ratio_b_bb. Intuition: a high
    BB/BBB ratio means BB pays a lot over BBB for one notch of quality."""
    def col(r: str) -> pd.Series:
        c = f"{r}|{tenor}"
        return wide[c].astype(float) if c in wide.columns else pd.Series(np.nan, index=wide.index)
    bbb, bb, b = col("BBB"), col("BB"), col("B")
    return pd.DataFrame({"ratio_bb_bbb": bb / bbb.where(bbb > 0), "ratio_b_bb": b / bb.where(bb > 0)},
                        index=wide.index)


# ---------------------------------------------------------------- compute


def compute(panels: Mapping[str, pd.DataFrame], as_of: pd.Timestamp, window_months: int | None = WINDOW_MONTHS,
            min_history_years: float = MIN_HISTORY_YEARS, min_issuers: int = MIN_ISSUERS) -> pd.DataFrame:
    """Cell percentile score per BB, B and CCC bond at as_of (spec build steps 1 to 7). One row per cusip.

    History: the optional `cell_history` panel (rows with available_at <= decision_time(as_of)) for the months
    before as_of, else `cell_history` rebuilt from bond_panel. The as_of month always comes from bond_panel.
    score = cell_pct, NaN with fewer than min_history_years x 12 prior medians or a thin cell. The ratio columns
    are index level: the same value on every row. Empty frame (columns COLS) without bond_panel or ratings."""
    as_of = pd.Timestamp(as_of) + pd.offsets.MonthEnd(0)
    if any(panels.get(k) is None or len(panels[k]) == 0 for k in REQUIRED):
        return pd.DataFrame(columns=COLS)
    dt = decision_time(as_of)
    now = month_cells(panels, as_of)
    if now.empty:
        return pd.DataFrame(columns=COLS)
    med_now = _ns(cell_medians(now, min_issuers).reset_index().assign(date=as_of, available_at=dt))

    cache = panels.get("cell_history")
    if cache is not None and len(cache):
        hist = cache[(cache["available_at"] <= dt) & (pd.to_datetime(cache["date"]) < as_of)].copy()
        hist = _ns(hist.assign(date=pd.to_datetime(hist["date"]) + pd.offsets.MonthEnd(0)))
    else:
        bp = panels["bond_panel"]
        months = pd.to_datetime(bp.loc[bp["available_at"] <= dt, "date"]).unique()
        hist = cell_history(panels, [m for m in months if pd.Timestamp(m) < as_of], min_issuers)
    hist = pd.concat([hist[HIST_COLS], med_now[HIST_COLS]], ignore_index=True)
    hist = hist.sort_values("available_at").drop_duplicates(["date", "cell"], keep="last")
    wide = hist.pivot(index="date", columns="cell", values="median_spread").sort_index()

    # own-history percentile of each cell and of each ratio at as_of (step 6)
    min_obs = int(round(12 * float(min_history_years)))
    pct = {c: own_history_percentile(wide[c], min_obs, window_months).loc[as_of] for c in wide.columns}
    ratios = spread_ratios(wide)
    r_now = ratios.loc[as_of]
    r_pct = {c: own_history_percentile(ratios[c], min_obs, window_months).loc[as_of, "pct"] for c in ratios.columns}

    # score each HY bond with its cell (step 7)
    out = now[now["rating"].isin(HY_RATINGS)].copy()
    if out.empty:
        return pd.DataFrame(columns=COLS)
    m = med_now.set_index("cell")
    out["cell_spread"] = out["cell"].map(m["median_spread"]).astype(float)
    out["cell_n_issuers"] = out["cell"].map(m["n_issuers"]).astype(int)
    out["cell_pct"] = out["cell"].map({c: v["pct"] for c, v in pct.items()}).astype(float)
    out["cell_n_hist"] = out["cell"].map({c: int(v["n_hist"]) for c, v in pct.items()}).astype(int)
    out["score"] = out["cell_pct"]
    for c in ratios.columns:
        out[c] = float(r_now[c])
        out[f"{c}_pct"] = float(r_pct[c])
    out["date"] = as_of
    out["available_at"] = dt
    return out[COLS].astype({"score": float, "g_spread": float}).reset_index(drop=True)
