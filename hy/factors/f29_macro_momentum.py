"""F29 Macro momentum: PMI momentum and earnings revision ratio momentum (rank 29). Spec
docs/factors/F29-macro-momentum.md; methodology Section 8 (S7 replacement candidate), Section 3.6 (macro inputs) and
Section 9.2 (macro overlay, index beta). Source: J.P. Morgan, Inkinen and Bassi (2015), "Systematic fixed income
trading strategies", rules 1 and 2 and footnote 2 p. 2, weights and results p. 7. Extra columns: Deutsche Bank
Quantcraft (2015), "Delving into new territories", index recipe pp. 3 to 4, signal p. 7. Pages are printed pages
(= PDF pages).

    agree(a, b) = +1 if a > 0 and b > 0, -1 if a < 0 and b < 0, else 0         both readings must agree (p. 2)
    p_t   = agree(PMI_loc,t - PMI_loc,t-2, PMI_glob,t - PMI_glob,t-2)           PMI momentum, 2 months (rule 1)
    RR_t  = (N_up - N_down) / (N_up + N_down)                                  revision ratio (our choice: undefined)
    r_t   = agree(RR_loc,t - RR_loc,t-3, RR_glob,t - RR_glob,t-3)               revision momentum, 3 months (rule 2)
    score = mean of the available p_t, r_t                                     equal weights, 15% each (p. 7)

Intuition: macro data are serially correlated and investors absorb them slowly (p. 2), so a rise tends to go on.

Sign. The source trades government bond duration: rising PMI means short duration. For HY the sign flips: rising
PMI and revisions mean long the index excess return. The basis is p. 3 ("positive growth revisions are typically
beneficial for corporate earnings"). No source tests a credit asset, so the sign is a hypothesis.

Inputs. A new optional panel `macro_series`: `series_id`, `date` (reference date, month end for monthly series),
`value`, `available_at` (release time). Series: `ism_pmi` (fallback `philly_gac`, the proxy of decision page
2026-10-24-review-sloos-pmi), `global_pmi`, and beat and shock components `beat:<category>:<name>` and
`shock:<category>:<name>` with category `growth` or `inflation`. A new optional panel `revision_counts`: `date`
(month end of the I/B/E/S period), `region` (`US` or `GLOBAL`), `n_up`, `n_down`, `available_at`. Without a global
reading the rule uses the local sign alone. Without revision counts the score is the PMI signal alone. Without
either panel the result is an empty frame.

Extra columns (not the score): DB beat and shock indices. Components on business days, Spearman matrix with
correlation averaging (negatives to 0), PC1 weights summing to 1, I_t = I_t-1 + sum_j w_j z_j,t on release days,
B_t = 5-year z-score of I_t (p. 4), then the 1-year z-score of B_t (p. 7).
"""

from __future__ import annotations

import warnings
from typing import Mapping

import numpy as np
import pandas as pd

from hy.backtest import decision_time

KEY = "US_HY"            # value of the `index` key column (spec header)
PMI_MONTHS = 2           # PMI change window in months (JPM p. 2, rule 1)
RR_MONTHS = 3            # revision ratio change window in months (JPM p. 2, rule 2)
MAX_LAG_MONTHS = 2       # latest reading at least as_of - 2 months, else stale (our choice: ISM lags 1 month)
HY_SIGN = 1.0            # improving macro = long HY; the source's duration sign is -1 (spec "Sign"; our choice)
LOCAL_PMI = ("ism_pmi", "philly_gac")   # US PMI, then the proxy of the SLOOS and PMI decision page
GLOBAL_PMI = "global_pmi"               # J.P. Morgan Global Manufacturing PMI (JPM p. 2)
BEAT_CHANGE_MONTHS = 3   # beat components enter as 3-month changes (DB p. 4, footnote 9)
CHANGE_TOL_DAYS = 7      # tolerance to find the reading 3 months back (our choice: weekly series)
CORR_STEP = 65           # correlation averaging step in business days (DB p. 4, footnote 11 example "1-65-130")
MIN_CORR_DAYS = 520      # business days before the first correlation fit (our choice: about 2 years)
Z_WINDOW = "1826D"       # 5-year standardisation window (DB p. 4, steps 3 and 5, footnote 13)
SIGNAL_WINDOW = "365D"   # 1-year z-score of the index level (DB p. 7, step 1)
MIN_Z_OBS = 12           # unique points a z-score needs (our choice)
CATEGORIES = ("growth", "inflation")    # DB p. 3: growth and inflation
KINDS = ("beat", "shock")               # DB p. 3: beat (pulse) and shock (actual minus survey median)
HOLD = 1                 # evaluation horizon in months (JPM rebalances monthly, p. 2 footnote 2)

META = {
    "rank": 29,
    "name": "Macro momentum: PMI momentum and earnings revision ratio momentum",
    "level": "index",
    "horizon_months": HOLD,
    "needs": ["macro_series", "revision_counts"],
    "spec": "docs/factors/F29-macro-momentum.md",
    "section": "8",
}

INDEX_COLS = [f"{c}_{k}{s}" for c in CATEGORIES for k in KINDS for s in ("", "_z")]
COLS = ["date", "index", "score", "available_at", "status", "score_basis", "pmi_source", "pmi_basis", "pmi_date",
        "pmi_local", "pmi_local_chg", "pmi_global_chg", "pmi_signal", "rr_basis", "rr_date", "rr_local",
        "rr_local_chg", "rr_global_chg", "rr_signal"] + INDEX_COLS
NUM = ["score", "pmi_local", "pmi_local_chg", "pmi_global_chg", "pmi_signal", "rr_local", "rr_local_chg",
       "rr_global_chg", "rr_signal"] + INDEX_COLS


# ---------------------------------------------------------------- momentum helpers


def _known(df: pd.DataFrame | None, dt: pd.Timestamp) -> pd.DataFrame:
    """Rows with available_at <= dt and `date` as a timestamp. Empty frame when df is None."""
    if df is None or len(df) == 0:
        return pd.DataFrame(columns=["date", "available_at"])
    d = df[df["available_at"] <= dt].copy()
    d["date"] = pd.to_datetime(d["date"])
    return d


def monthly_series(ms: pd.DataFrame, series_id: str) -> pd.Series:
    """One monthly series from known `macro_series` rows (spec build step 2): reference date as month end, the
    latest vintage per month (our choice: the source is silent). Empty series when the id is absent."""
    d = ms[ms["series_id"] == series_id].copy()
    if d.empty:
        return pd.Series(dtype=float)
    d["date"] = d["date"] + pd.offsets.MonthEnd(0)
    d = d.sort_values("available_at").drop_duplicates("date", keep="last")
    return d.set_index("date")["value"].astype(float).sort_index()


def change_over(s: pd.Series, months: int, at: pd.Timestamp | None = None) -> float:
    """x_at - x_at-months on month-end dates (JPM p. 2: "over past two months", "past three months"). `at`
    defaults to the last date. NaN when either reading is missing."""
    if s.empty:
        return float("nan")
    at = s.index[-1] if at is None else pd.Timestamp(at)
    back = at - pd.offsets.MonthEnd(months)
    if at not in s.index or back not in s.index:
        return float("nan")
    return float(s[at] - s[back])


def agree_signal(local: float, glob: float) -> tuple[float, str | None]:
    """Agree rule of JPM p. 2: +1 if both changes are > 0, -1 if both < 0, else 0. Duration sign flipped for HY
    (HY_SIGN). Without a global change, the local sign alone (our choice). Returns (signal, basis)."""
    if not np.isfinite(local):
        return float("nan"), None
    if not np.isfinite(glob):
        return HY_SIGN * float(np.sign(local)), "local"
    if local > 0 and glob > 0:
        return HY_SIGN * 1.0, "local_global"
    if local < 0 and glob < 0:
        return HY_SIGN * -1.0, "local_global"
    return 0.0, "local_global"


def revision_ratio(n_up, n_down):
    """RR = (N_up - N_down) / (N_up + N_down), the I/B/E/S breadth ratio (our choice: JPM p. 2 names the ratio but
    does not define it). NaN where no estimate moved."""
    up, down = np.asarray(n_up, dtype=float), np.asarray(n_down, dtype=float)
    tot = up + down
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(tot > 0, (up - down) / tot, np.nan)


def revision_series(rc: pd.DataFrame, region: str) -> pd.Series:
    """Monthly RR of one region from known `revision_counts` rows, latest vintage per month (spec build step 3)."""
    d = rc[rc["region"] == region].copy() if len(rc) else rc
    if d.empty:
        return pd.Series(dtype=float)
    d["date"] = d["date"] + pd.offsets.MonthEnd(0)
    d = d.sort_values("available_at").drop_duplicates("date", keep="last")
    return pd.Series(revision_ratio(d["n_up"], d["n_down"]), index=d["date"]).sort_index().dropna()


def _momentum(local: pd.Series, glob: pd.Series, months: int, as_of: pd.Timestamp, max_lag: int) -> dict:
    """Last date, level, local and global change, signal, basis and a stale flag for one rule (build steps 2 to 4).
    The global change is taken at the local reference month (our choice)."""
    out = {"date": pd.NaT, "local": np.nan, "local_chg": np.nan, "global_chg": np.nan, "signal": np.nan,
           "basis": None, "stale": False}
    if local.empty:
        return out
    last = local.index[-1]
    out.update(date=last, local=float(local.iloc[-1]))
    if last < pd.Timestamp(as_of) + pd.offsets.MonthEnd(0) - pd.offsets.MonthEnd(max_lag):
        out["stale"] = True
        return out
    out["local_chg"] = change_over(local, months, last)
    out["global_chg"] = change_over(glob, months, last)
    out["signal"], out["basis"] = agree_signal(out["local_chg"], out["global_chg"])
    return out


# ---------------------------------------------------------------- beat and shock index helpers (DB pp. 3 to 4)


def beat_components(ms: pd.DataFrame, kind: str, category: str) -> dict[str, pd.Series]:
    """Release series of one kind and category, indexed by release time (DB p. 3: announcement dates), first
    release per reference date (p. 3, footnote 8: unrevised data). Beat components become 3-month changes against
    the first release of the reading 3 months back, within CHANGE_TOL_DAYS (p. 4, footnote 9). Shock components
    enter as they are. Each component must already rise when its category rises (step 1)."""
    prefix = f"{kind}:{category}:"
    d = ms[ms["series_id"].astype(str).str.startswith(prefix)] if len(ms) else ms
    out: dict[str, pd.Series] = {}
    for sid, g in d.groupby("series_id"):
        g = g.sort_values("available_at").drop_duplicates("date", keep="first").sort_values("date")
        g = g[["date", "value", "available_at"]].astype({"value": float})
        if kind == "beat":
            back = g[["date", "value"]].rename(columns={"date": "back_date", "value": "back"})
            g["back_date"] = g["date"] - pd.DateOffset(months=BEAT_CHANGE_MONTHS)
            g = pd.merge_asof(g.sort_values("back_date"), back.sort_values("back_date"), on="back_date",
                              direction="nearest", tolerance=pd.Timedelta(CHANGE_TOL_DAYS, unit="D"))
            g["value"] = g["value"] - g["back"]
        g = g.dropna(subset=["value"]).sort_values("available_at")
        if len(g):
            out[str(sid)[len(prefix):]] = pd.Series(g["value"].to_numpy(), index=pd.DatetimeIndex(g["available_at"]))
    return out


def rolling_z(x: pd.Series, window: str = Z_WINDOW, min_obs: int = MIN_Z_OBS) -> pd.Series:
    """z of each point against the unique points of the trailing time window, itself included (DB p. 4, steps 3
    and 5, footnote 13: unique data points only). NaN below min_obs points or with zero spread."""
    if x.empty:
        return x.astype(float)
    x = x.sort_index().astype(float)
    r = x.rolling(window, min_periods=min_obs)
    sd = r.std()
    return (x - r.mean()) / sd.where(sd > 0)


def averaged_spearman(wide: pd.DataFrame, step: int = CORR_STEP) -> pd.DataFrame:
    """Spearman matrix with correlation averaging (DB p. 4, footnote 11): subsample every `step` rows from each
    start offset, take the pairwise Spearman correlation per subsample, average. Negative values go to 0
    (footnote 12). Missing pairs go to 0, the diagonal to 1."""
    mats = [wide.iloc[off::step].corr(method="spearman", min_periods=3).to_numpy()
            for off in range(min(step, len(wide)))]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)     # all-NaN pairs give NaN, then 0 below
        c = np.nanmean(np.stack(mats), axis=0) if mats else np.full((wide.shape[1],) * 2, np.nan)
    c = np.nan_to_num(np.clip(c, 0.0, None), nan=0.0)
    np.fill_diagonal(c, 1.0)
    return pd.DataFrame(c, index=wide.columns, columns=wide.columns)


def pc1_weights(corr: pd.DataFrame) -> pd.Series:
    """PC1 loadings of the correlation matrix, scaled to sum to 1 (DB p. 4, step 4). The matrix has no negative
    entry, so PC1 has one sign and the sum is positive."""
    vals, vecs = np.linalg.eigh(corr.to_numpy(dtype=float))
    v = vecs[:, int(np.argmax(vals))]
    v = -v if v.sum() < 0 else v
    return pd.Series(v / v.sum(), index=corr.index)


def beat_index(comps: Mapping[str, pd.Series], end: pd.Timestamp, step: int = CORR_STEP,
               min_corr_days: int = MIN_CORR_DAYS, window: str = Z_WINDOW, min_obs: int = MIN_Z_OBS) -> pd.Series:
    """B_t on release days up to `end` (DB p. 4, steps 1 to 5). Business-day grid, forward-filled components
    (step 1); the averaged Spearman matrix on an anchored window, refitted at each month end and applied from the
    next business day (step 2; our choice: monthly, not daily); 5-year z per component (step 3); PC1 weights,
    renormalised over the components with a current z (our choice), I_t = I_t-1 + sum_j w_j z_j,t on release days
    (step 4); B_t = 5-year z-score of I_t (step 5). Empty series when no weights can be fitted."""
    if not comps:
        return pd.Series(dtype=float)
    end = pd.Timestamp(end).normalize()
    start = min(s.index.min() for s in comps.values()).normalize()
    grid = pd.bdate_range(start, end)
    if len(grid) == 0:
        return pd.Series(dtype=float)

    def on_grid(s: pd.Series) -> pd.Series:
        day = pd.DatetimeIndex([min(pd.offsets.BDay().rollforward(t.normalize()), grid[-1]) for t in s.index])
        return pd.Series(s.to_numpy(), index=day).groupby(level=0).last()

    x = pd.DataFrame({k: on_grid(s) for k, s in comps.items()}).reindex(grid)
    z = pd.DataFrame({k: on_grid(rolling_z(s, window, min_obs)) for k, s in comps.items()}).reindex(grid)
    released = x.notna().any(axis=1)
    x, z = x.ffill(), z.ffill()
    month_ends = grid.to_series().groupby(grid.to_period("M")).max()
    fits = {}
    for me in month_ends:
        hist = x.loc[:me]
        cols = hist.columns[hist.notna().sum() >= min_corr_days]
        if len(cols):
            fits[me] = pc1_weights(averaged_spearman(hist[cols], step)).reindex(x.columns, fill_value=0.0)
    if not fits:
        return pd.Series(dtype=float)
    w = pd.DataFrame(fits).T.reindex(grid).shift(1).ffill()     # a fit at month end applies from the next day
    live = w.where(z.notna())
    d_i = (live * z).sum(axis=1, min_count=1) / live.sum(axis=1).where(live.sum(axis=1) > 0)
    d_i = d_i[released & d_i.notna()]
    if d_i.empty:
        return pd.Series(dtype=float)
    return rolling_z(d_i.cumsum(), window, min_obs).dropna()


def trailing_z(b: pd.Series, end: pd.Timestamp, window: str = SIGNAL_WINDOW, min_obs: int = MIN_Z_OBS) -> float:
    """1-year z-score of the index level at `end`: (B_last - mean) / sd over the unique points of the last year
    (DB p. 7, step 1). NaN below min_obs points."""
    b = b[b.index <= pd.Timestamp(end)]
    if b.empty:
        return float("nan")
    last = rolling_z(b, window, min_obs).iloc[-1]
    return float(last)


# ---------------------------------------------------------------- compute


def compute(panels: Mapping[str, pd.DataFrame], as_of: pd.Timestamp, pmi_months: int = PMI_MONTHS,
            rr_months: int = RR_MONTHS, max_lag_months: int = MAX_LAG_MONTHS) -> pd.DataFrame:
    """One row for index US_HY at as_of (spec build steps 1 to 5). score = mean of the PMI and revision signals,
    in {-1, -0.5, 0, 0.5, 1}, NaN when neither is available or fresh. Empty frame (columns COLS) when both
    macro_series and revision_counts are missing. Higher score = long the index."""
    as_of = pd.Timestamp(as_of)
    if all(panels.get(k) is None or len(panels[k]) == 0 for k in META["needs"]):
        return pd.DataFrame(columns=COLS)
    dt = decision_time(as_of)
    ms, rc = _known(panels.get("macro_series"), dt), _known(panels.get("revision_counts"), dt)
    row = dict.fromkeys(COLS, np.nan)
    row.update({"date": as_of, "index": KEY, "available_at": dt, "score_basis": None, "pmi_source": None,
                "pmi_basis": None, "rr_basis": None, "pmi_date": pd.NaT, "rr_date": pd.NaT})

    local = pd.Series(dtype=float)
    for sid in LOCAL_PMI if len(ms) else ():
        local = monthly_series(ms, sid)
        if not local.empty:
            row["pmi_source"] = sid
            break
    glob = monthly_series(ms, GLOBAL_PMI) if len(ms) else pd.Series(dtype=float)
    pmi = _momentum(local, glob, pmi_months, as_of, max_lag_months)
    rr_loc = revision_series(rc, "US") if len(rc) else pd.Series(dtype=float)
    rr_glob = revision_series(rc, "GLOBAL") if len(rc) else pd.Series(dtype=float)
    rr = _momentum(rr_loc, rr_glob, rr_months, as_of, max_lag_months)
    for name, m in (("pmi", pmi), ("rr", rr)):
        row.update({f"{name}_date": m["date"], f"{name}_local": m["local"], f"{name}_local_chg": m["local_chg"],
                    f"{name}_global_chg": m["global_chg"], f"{name}_signal": m["signal"], f"{name}_basis": m["basis"]})

    used = [n for n, m in (("pmi", pmi), ("rr", rr)) if np.isfinite(m["signal"])]
    if used:
        row["score"] = float(np.mean([row[f"{n}_signal"] for n in used]))
        row["score_basis"] = "+".join(used)
        row["status"] = "ok"
    else:
        row["status"] = "stale" if pmi["stale"] or rr["stale"] else "no_signal"

    for cat in CATEGORIES:
        for kind in KINDS:
            b = beat_index(beat_components(ms, kind, cat), dt) if len(ms) else pd.Series(dtype=float)
            if not b.empty:
                row[f"{cat}_{kind}"] = float(b.iloc[-1])
                row[f"{cat}_{kind}_z"] = trailing_z(b, dt)
    out = pd.DataFrame([row], columns=COLS)
    return out.astype({k: float for k in NUM})
