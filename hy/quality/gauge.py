"""Market-level quality compression gauge (spec docs/factors/QUALITY-rotation.md, Definition 3, gauge). Methodology
Section 8 (S7 slot) and Section 3.6 (`oas_bb`, `oas_b`, `oas_ccc`).

    R^Q_t   = median s over LQ bonds / median s over HQ bonds at t        quality spread ratio
    G^Q_t   = median s over LQ bonds - median s over HQ bonds              quality spread gap, decimals
    P_t     = share of prior months with R^Q < R^Q_t                       own-history percentile (F24 rule)
    score   = P_t - 0.5                                                    > 0: the quality spread is wide

HQ and LQ follow hy.quality.valuation.groups: quality quintile 5 and 1 (`hq_def="score"`) or rating buckets
(`"rating"`). The rating ratios BB/BBB and B/BB at 1 to 3 years and their percentiles come from F24 `compute`
(Nicol, DB HY Strategy, 2 March 2021, p. 5, Fig. 8). Intuition: a wide quality spread against its own history
pays for going down in quality. A tight one makes up in quality cheap.

History. The optional panel `quality_gauge_history` (columns HIST_COLS, available_at = decision_time(date)) is a
cache. Without it, `gauge_history` rebuilds every prior month from the panels, each month as known at its own
decision time. The score is NaN with fewer than F24 MIN_HISTORY_YEARS x 12 prior values.
"""

from __future__ import annotations

from typing import Mapping

import numpy as np
import pandas as pd

from hy.backtest import decision_time
from hy.factors import f24_cell_percentile as f24
from hy.quality import score as qs
from hy.quality import valuation as qv

KEY = "US_HY"
MIN_ISSUERS = f24.MIN_ISSUERS             # issuers a group needs for a median (F24, our choice there)
MIN_HISTORY_YEARS = f24.MIN_HISTORY_YEARS

META = {
    "rank": None,
    "name": "Quality compression gauge",
    "level": "index",
    "horizon_months": 3,
    "needs": qs.META["needs"] + ["quality_gauge_history", "cell_history"],
    "spec": "docs/factors/QUALITY-rotation.md",
    "section": "8; 3.6",
}
HIST_COLS = ["date", "kind", "hq_def", "ratio_lq_hq", "gap_lq_hq", "med_hq", "med_lq", "n_hq", "n_lq",
             "available_at"]
COLS = ["date", "index", "score", "available_at", "kind", "hq_def", "ratio_lq_hq", "gap_lq_hq", "med_hq", "med_lq",
        "n_hq", "n_lq", "ratio_pct", "n_hist", "ratio_bb_bbb", "ratio_b_bb", "ratio_bb_bbb_pct", "ratio_b_bb_pct"]


def month_ratio(panels: Mapping[str, pd.DataFrame], month: pd.Timestamp, kind: str = "blend",
                hq_def: str = "score", hq_ratings=None, lq_ratings=None, min_issuers: int = MIN_ISSUERS,
                **quality_params) -> dict:
    """R^Q, G^Q and the group medians at one month end, as known at decision_time(month). A group with fewer than
    `min_issuers` issuers gives NaN. Keys HIST_COLS."""
    month = pd.Timestamp(month) + pd.offsets.MonthEnd(0)
    row = {"date": month, "kind": kind, "hq_def": hq_def, "available_at": decision_time(month)}
    q = qs.compute(panels, month, kind, **quality_params)
    if q.empty:
        return {**dict.fromkeys(HIST_COLS, np.nan), **row, "n_hq": 0, "n_lq": 0}
    b = qs.universe(panels, month).set_index("cusip")
    q["g_spread"] = q["cusip"].map(b["g_spread"]).astype(float)
    hq, lq = qv.groups(q, hq_def, hq_ratings, lq_ratings)
    n_hq, n_lq = int(q.loc[hq, "gvkey"].nunique()), int(q.loc[lq, "gvkey"].nunique())
    mh = float(q.loc[hq, "g_spread"].median()) if n_hq >= min_issuers else np.nan
    ml = float(q.loc[lq, "g_spread"].median()) if n_lq >= min_issuers else np.nan
    row.update({"med_hq": mh, "med_lq": ml, "n_hq": n_hq, "n_lq": n_lq, "gap_lq_hq": ml - mh,
                "ratio_lq_hq": ml / mh if mh > 0 else np.nan})
    return row


def gauge_history(panels: Mapping[str, pd.DataFrame], months, **params) -> pd.DataFrame:
    """month_ratio for each month end in `months`. Columns HIST_COLS. The production machine may cache this frame
    as the panel `quality_gauge_history`."""
    rows = [month_ratio(panels, m, **params) for m in sorted({pd.Timestamp(x) + pd.offsets.MonthEnd(0) for x in months})]
    return pd.DataFrame(rows, columns=HIST_COLS)


def compute(panels: Mapping[str, pd.DataFrame], as_of: pd.Timestamp, kind: str = "blend", hq_def: str = "score",
            hq_ratings=None, lq_ratings=None, window_months: int | None = f24.WINDOW_MONTHS,
            min_history_years: float = MIN_HISTORY_YEARS, rating_ratios: bool = True,
            **quality_params) -> pd.DataFrame:
    """One row for index US_HY at as_of. score = ratio_pct - 0.5: higher = the quality spread is wide against its
    own history = favours down in quality (long LQ against HQ). Empty frame (columns COLS) when the quality panels
    of `kind` are missing."""
    as_of = pd.Timestamp(as_of) + pd.offsets.MonthEnd(0)
    if not qs.required_ok(panels, kind):
        return pd.DataFrame(columns=COLS)
    dt = decision_time(as_of)
    params = dict(kind=kind, hq_def=hq_def, hq_ratings=hq_ratings, lq_ratings=lq_ratings, **quality_params)
    now = month_ratio(panels, as_of, **params)
    cache = panels.get("quality_gauge_history")
    if cache is not None and len(cache):
        hist = cache[(cache["available_at"] <= dt) & (pd.to_datetime(cache["date"]) < as_of)
                     & (cache["kind"] == kind) & (cache["hq_def"] == hq_def)].copy()
    else:
        bp = panels["bond_panel"]
        months = pd.to_datetime(bp.loc[bp["available_at"] <= dt, "date"]).unique()
        hist = gauge_history(panels, [m for m in months if pd.Timestamp(m) < as_of], **params)
    hist = pd.concat([hist[HIST_COLS], pd.DataFrame([now], columns=HIST_COLS)], ignore_index=True)
    hist["date"] = pd.to_datetime(hist["date"]) + pd.offsets.MonthEnd(0)
    hist = hist.sort_values("available_at").drop_duplicates("date", keep="last")
    series = hist.set_index("date")["ratio_lq_hq"].astype(float).sort_index()
    pct = f24.own_history_percentile(series, int(round(12 * float(min_history_years))), window_months).loc[as_of]
    row = {**now, "index": KEY, "ratio_pct": float(pct["pct"]), "n_hist": int(pct["n_hist"]),
           "score": float(pct["pct"]) - 0.5, "available_at": dt}
    for c in ("ratio_bb_bbb", "ratio_b_bb", "ratio_bb_bbb_pct", "ratio_b_bb_pct"):
        row[c] = np.nan
    if rating_ratios:
        r = f24.compute(panels, as_of, window_months, min_history_years)
        if len(r):
            for c in ("ratio_bb_bbb", "ratio_b_bb", "ratio_bb_bbb_pct", "ratio_b_bb_pct"):
                row[c] = float(r[c].iloc[0])
    return pd.DataFrame([row], columns=COLS).astype({"score": float, "ratio_lq_hq": float, "ratio_pct": float})
