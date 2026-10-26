"""F04 Volatility-adjusted and residual bond momentum (rank 4). Spec docs/factors/F04-bond-momentum.md; methodology
Section 8, subsection "BM. Bond momentum" (formulas BM-1 and BM-2, after S7). Sources: van Zundert (2017), PhD
thesis, ch. 4, eq. 4.6 (p. 104), method (p. 112), Table 4.7 (p. 124); Jostova et al., FDIC WP 2010-04 (p. 12).
Pages are printed pages.

    r_i,m    = total_i,m - tsy_i,m                                         excess over the duration-matched Treasury
    VAMOM_iT = sum_{m=T-6..T-1} r_i,m / sd{r_i,m}_{m=T-12..T-1}             BM-1, skip month T
    lam_k,m  = median_{j in k} r_j,m / DTS_j,m-1,  DTS = mod_dur x g_spread  cell = rating class x GICS sector
    eps_i,m  = r_i,m - lam_k(i),m DTS_i,m-1
    RMOM_iT  = sum_{m=T-6..T-1} eps_i,m / sd{eps_i,m}_{m=T-12..T-1}         BM-2

Intuition: rank on return per unit of own risk, so long-duration and CCC bonds do not fill both tails. The residual
removes the part of the return that the market spread move explains and keeps the slow issuer news.

Inputs. `bond_panel` and `ratings` are required. `gics` and `leverage` are optional: without `gics` every cell
falls back to the rating class. Without `leverage` a bond with no S&P rating on file has no class and no score.
Without `bond_panel` or `ratings` the result is empty (columns COLS). `equity_monthly` is not read.

Returns. r_i,m reuses `hy.backtest.realised_excess_return` with beta 0 (no benchmark hedge). A stale row (at most
STALE_MAX_TRADES trades and the same price as the bond's prior row) and a carried row are missing. A gap of k <= 3
months between two rows spreads the k-month return R as R / k to each month of the formation sum and gives sigma
one observation R / sqrt(k). A gap of 4 or more months leaves the months missing.

Score. Percentile rank of VAMOM across the month's scored bonds, then `signals.standardise_by_date`. The columns
`vamom`, `rmom` and `raw_mom` hold the unranked values for the evaluation grid (`evaluation_grid`, `choose_branch`).
"""

from __future__ import annotations

from typing import Mapping

import numpy as np
import pandas as pd

from hy.backtest import (CYCLE_WINDOWS, assert_no_lookahead, decision_time, eligible, hac_mean, ic_by_window, not_distressed,
                         realised_excess_return)
from hy.peers import MIN_PEERS, fit_cutoffs, implied_class, rating_class, rating_at, sector_at, RATING_STALE_DAYS
from hy.signals import CYCLES, standardise_by_date

FORM = 6                   # formation months T-6 .. T-1 (Jostova p. 12; van Zundert p. 112; spec section 3)
SKIP = 1                   # skip month T (Jostova p. 12; spec open question 2 default)
VOL_WINDOW = 12            # sigma window T-12 .. T-1 (van Zundert p. 112)
MIN_FORM = 5               # formation months a score needs, of 6 (spec section 3, our choice)
MIN_VOL = 8                # sigma observations a score needs, of 12 (spec section 3, our choice)
MAX_GAP = 3                # longest gap in months that spreads its return (spec build step 3, our choice)
SIGMA_FLOOR_Q = 0.10       # sigma floor: 10th percentile of the month's scored sigmas (spec section 3, our choice)
STALE_MAX_TRADES = 1       # a row with at most this many trades and an unchanged price is stale (spec build step 2)
SIGMA_TOL = 1e-12          # a sigma at or below this is a numerical zero: no score (our choice)
SD_DDOF = 1                # sample sd of the sigma observations (our choice: the sources do not give the divisor)
HOLD = 6                   # main holding period in months (van Zundert Table 4.6 p. 123; Jostova p. 12)
HY_CLASSES = ("BB", "B", "CCC")   # scored universe (spec build step 6)
DEFAULT_SYMBOLS = ("D", "SD")     # raw S&P symbols of a defaulted issuer: never scored (spec build step 6)
CELL_LEVELS = ("sr", "r", "all")  # residual cell: rating x sector, then rating (spec section 3), then all (our choice)

# Evaluation grid and decision rule (spec section 7)
HORIZONS = (1, 6)          # h = 1 (Kelly horizon) and h = 6 (main)
HAC_LAGS = 5               # Newey-West lags of the IC t-statistic (spec section 7)
T_PASS = 2.0               # HAC t a pass needs; branch 3 needs t <= -T_PASS (spec section 7)
MIN_CYCLES = 3             # cycle windows of 4 with positive IC a pass needs (CLAUDE.md; spec section 7)
GRID_SIGNALS = {"raw": "raw_mom", "va": "vamom", "resid": "rmom"}
GRID_SUBSETS = {           # subset -> (spread cap in decimals or None, rating classes kept)
    "all": (None, HY_CLASSES),
    "lt1000": (0.10, HY_CLASSES),    # spread < 1,000 bp
    "lt2000": (0.20, HY_CLASSES),    # spread < 2,000 bp (Kelly's cut, p. 15)
    "ex_ccc": (None, ("BB", "B")),
}
RATING_SUBSETS = {"bb": (None, ("BB",)), "b": (None, ("B",)), "ccc": (None, ("CCC",))}  # report cells (spec section 7)

META = {
    "rank": 4,
    "name": "Volatility-adjusted and residual bond momentum",
    "level": "bond",
    "horizon_months": HOLD,
    "needs": ["bond_panel", "ratings", "gics", "leverage"],
    "spec": "docs/factors/F04-bond-momentum.md",
    "section": "8",
}
REQUIRED = ("bond_panel", "ratings")

COLS = ["date", "cusip", "score", "available_at", "gvkey", "vamom", "rmom", "raw_mom", "mom_sigma", "rmom_sigma",
        "mom_n_form", "mom_n_vol", "rclass", "sector", "g_spread", "n_trades"]


# ---------------------------------------------------------------- monthly excess returns


def mark_stale(panel: pd.DataFrame, max_trades: int = STALE_MAX_TRADES) -> pd.Series:
    """True for a row with at most `max_trades` trades and the same price as the bond's prior row (spec build step
    2). A missing trade count counts as zero (our choice). Intuition: a repeated print of an idle bond is no news."""
    p = panel.sort_values(["cusip", "date"])
    prev = p.groupby("cusip")["price"].shift(1)
    stale = (p["n_trades"].fillna(0) <= max_trades) & (p["price"] == prev)
    return stale.reindex(panel.index)


def monthly_excess_returns(panel: pd.DataFrame, as_of: pd.Timestamp, max_gap: int = MAX_GAP) -> pd.DataFrame:
    """r_ex per pair of consecutive usable month-end rows of each bond (spec build steps 2 and 3).

    Stale and carried rows drop out first. The start row must be `eligible`. The pair ends at the bond's next row
    within `max_gap` months. r_ex = total - tsy_ret of `realised_excess_return` with beta 0. Columns: cusip, gvkey,
    start, date (the end month m), gap_k (months spanned), r_ex, dts (mod_dur x g_spread at the start row).
    Raises LookAheadError when a row has available_at after `as_of`."""
    cols = ["cusip", "gvkey", "start", "date", "gap_k", "r_ex", "dts"]
    assert_no_lookahead(panel, as_of, "bond_panel")
    p = panel[~mark_stale(panel) & ~panel["carried"].astype(bool)].copy()
    if p.empty:
        return pd.DataFrame(columns=cols)
    dates = pd.concat([p["date"], pd.to_datetime(p["hedge_date"])]).dropna().unique()
    zero = pd.Series(0.0, index=pd.DatetimeIndex(dates))          # beta 0: no benchmark leg
    parts = []
    for k in range(1, int(max_gap) + 1):
        x = realised_excess_return(p, k, as_of, beta=0.0, bench=zero)
        x = x[x["end_date"] == x["date"] + pd.offsets.MonthEnd(k)].copy()  # the next row is exactly k months on
        x["gap_k"] = k
        parts.append(x)
    x = pd.concat(parts).sort_values("gap_k").drop_duplicates(["cusip", "date"], keep="first")
    x["r_ex"] = x["total"] - x["tsy_ret"]
    start = p[["cusip", "date", "gvkey", "mod_dur", "g_spread"]].drop_duplicates(["cusip", "date"], keep="last")
    x = x.merge(start, on=["cusip", "date"], how="left")
    x["dts"] = x["mod_dur"].astype(float) * x["g_spread"].astype(float)
    x = x.rename(columns={"date": "start"}).rename(columns={"end_date": "date"})
    return x[cols].sort_values(["cusip", "date"]).reset_index(drop=True)


def spread_months(pairs: pd.DataFrame, col: str) -> pd.DataFrame:
    """One row per month a pair spans, value col / gap_k (spec build step 3). Columns cusip, month, value, pair.
    Intuition: a 3-month return with no prints between counts as three equal monthly returns in the sum."""
    k = pairs["gap_k"].astype(int).to_numpy()
    idx = np.repeat(np.arange(len(pairs)), k)
    back = np.concatenate([np.arange(n)[::-1] for n in k]) if len(k) else np.array([], dtype=int)
    end = pd.DatetimeIndex(pairs["date"].to_numpy()[idx])
    month = pd.DatetimeIndex([m - pd.offsets.MonthEnd(int(b)) if b else m for m, b in zip(end, back)])
    return pd.DataFrame({"cusip": pairs["cusip"].to_numpy()[idx], "month": month,
                         "value": pairs[col].to_numpy(float)[idx] / k[idx], "pair": pairs.index.to_numpy()[idx]})


def vol_observations(pairs: pd.DataFrame, col: str) -> pd.Series:
    """One sigma observation per pair, col / sqrt(gap_k), dated at the end month (spec build step 3). Intuition: a
    k-month return has k times the monthly variance, so dividing by sqrt(k) puts it on the monthly scale."""
    return pairs[col].astype(float) / np.sqrt(pairs["gap_k"].astype(float))


# ---------------------------------------------------------------- classes, cells, DTS residuals


def _raw_symbol(ratings: pd.DataFrame, dt: pd.Timestamp) -> pd.Series:
    """Latest raw S&P symbol per gvkey known at dt and at most RATING_STALE_DAYS old (as `peers.rating_at`)."""
    r = ratings[(ratings["available_at"] <= dt) & (ratings["datadate"] >= dt - pd.Timedelta(RATING_STALE_DAYS, unit="D"))]
    r = r.sort_values("datadate").drop_duplicates("gvkey", keep="last")
    return r.set_index("gvkey")["splticrm"].astype(str).str.strip().str.upper()


def rating_classes(ratings: pd.DataFrame, leverage: pd.DataFrame | None, month_end: pd.Timestamp) -> pd.DataFrame:
    """Rating class per gvkey at month_end (spec Inputs: splticrm to Feb 2017, then the implied class of hy.peers).

    Actual class from `peers.rating_at`. Otherwise the leverage-implied class, with cut-offs fitted on the actual
    ratings and leverage known at decision_time(month_end). Columns rclass and raw (the raw S&P symbol or NaN)."""
    dt = decision_time(month_end)
    r = ratings[ratings["available_at"] <= dt]
    out = pd.DataFrame({"rclass": rating_at(r, dt)})
    raw = _raw_symbol(r, dt)
    if leverage is not None and len(leverage):
        lv = leverage[leverage["available_at"] <= dt]
        act = r.assign(rclass=r["splticrm"].map(rating_class)).dropna(subset=["rclass"])
        hist = act.merge(lv[["date", "gvkey", "leverage", "ltm_ebitda"]], left_on=["gvkey", "datadate"],
                         right_on=["gvkey", "date"], how="inner")
        hist = hist[(hist["leverage"] > 0) & (hist["ltm_ebitda"].astype(float) > 0)]
        cut = fit_cutoffs(np.log(hist["leverage"].astype(float)), hist["rclass"])
        now = lv[lv["date"] == month_end].sort_values("available_at").drop_duplicates("gvkey", keep="last")
        imp = pd.Series([implied_class(l, bool(e > 0), cut) for l, e in zip(now["leverage"], now["ltm_ebitda"])],
                        index=now["gvkey"].to_numpy(), dtype=object)
        out = out.reindex(out.index.union(imp.index))
        out["rclass"] = out["rclass"].fillna(imp.reindex(out.index))
    out = out.reindex(out.index.union(raw.index))
    out["raw"] = raw.reindex(out.index)
    return out


def _sectors(gics: pd.DataFrame | None, month_end: pd.Timestamp) -> pd.Series:
    if gics is None or not len(gics):
        return pd.Series(dtype=str)
    return sector_at(gics[gics["available_at"] <= decision_time(month_end)], month_end)


def cell_keys(rclass: pd.Series, sector: pd.Series) -> pd.DataFrame:
    """Cell key per level of CELL_LEVELS (spec section 3): sr = class|sector, r = class, all. NaN where an input is
    missing, so the fallback moves to the next level."""
    c = rclass.astype(object)
    s = sector.astype(object)
    sr = c.astype(str) + "|" + s.astype(str)
    return pd.DataFrame({"sr": sr.where(c.notna() & s.notna()), "r": c.where(c.notna()), "all": "all"},
                        index=rclass.index)


def cell_lambdas(month: pd.Series, key: pd.Series, r_ex: pd.Series, dts: pd.Series, issuer: pd.Series,
                 min_issuers: int = MIN_PEERS) -> pd.Series:
    """lam_k,m = median over the cell's bonds of r / DTS, indexed by (month, key) (BM-2). A cell with fewer than
    `min_issuers` issuers has no lam. A bond with DTS <= 0 or no key drops out. Intuition: the cell's typical
    return per unit of spread risk that month."""
    ok = key.notna() & (dts > 0) & r_ex.notna()
    d = pd.DataFrame({"m": month[ok], "k": key[ok], "x": (r_ex / dts)[ok], "g": issuer[ok]})
    if d.empty:
        return pd.Series(dtype=float, index=pd.MultiIndex.from_arrays([[], []]))
    g = d.groupby(["m", "k"])
    return g["x"].median()[g["g"].nunique() >= min_issuers].rename("lam")


def dts_residuals(pairs: pd.DataFrame, keys: pd.DataFrame, min_issuers: int = MIN_PEERS) -> pd.Series:
    """eps per pair = r_ex - DTS_start x sum of lam over the months the pair spans (BM-2; spec build step 4).

    `keys` holds the pair's cell key per level (same index as `pairs`). lam comes from the one-month pairs only
    (our choice: a gap return blurs the month). Each month takes the first level of CELL_LEVELS whose cell has a
    lam. A pair with a month without lam has NaN. Intuition: what is left after the market spread move."""
    one = pairs[pairs["gap_k"] == 1]
    sm = spread_months(pairs, "r_ex")
    lam = np.full(len(sm), np.nan)
    for lvl in CELL_LEVELS:
        tab = cell_lambdas(one["date"], keys.loc[one.index, lvl], one["r_ex"], one["dts"], one["gvkey"], min_issuers)
        k = keys.loc[sm["pair"], lvl].fillna("~none").to_numpy()
        v = tab.reindex(pd.MultiIndex.from_arrays([sm["month"], k])).to_numpy(float) if len(tab) else lam * np.nan
        lam = np.where(np.isnan(lam), v, lam)
    sm["lam"] = lam
    n = sm.groupby("pair")["lam"].count()
    lam_sum = sm.groupby("pair")["lam"].sum().where(n == pairs["gap_k"].reindex(n.index))
    return (pairs["r_ex"] - pairs["dts"] * lam_sum.reindex(pairs.index)).rename("eps")


# ---------------------------------------------------------------- momentum statistics


def formation_sum(pairs: pd.DataFrame, col: str, months: pd.DatetimeIndex) -> pd.DataFrame:
    """Sum and count of the spread monthly values of `col` inside the formation `months` per cusip (BM-1, BM-2
    numerator; spec section 3: a sum, not a product). Columns total, n."""
    sm = spread_months(pairs[pairs[col].notna()], col)
    sm = sm[sm["month"].isin(months)]
    g = sm.groupby("cusip")["value"]
    return pd.DataFrame({"total": g.sum(), "n": g.count()})


def vol_estimate(pairs: pd.DataFrame, col: str, months: pd.DatetimeIndex, ddof: int = SD_DDOF) -> pd.DataFrame:
    """sd and count of the sigma observations of `col` dated inside the vol `months` per cusip (BM-1, BM-2
    denominator; van Zundert p. 112). Columns sigma, n."""
    p = pairs[pairs[col].notna() & pairs["date"].isin(months)]
    g = vol_observations(p, col).groupby(p["cusip"])
    return pd.DataFrame({"sigma": g.std(ddof=ddof), "n": g.count()})


def floor_sigma(sigma: pd.Series, q: float = SIGMA_FLOOR_Q) -> pd.Series:
    """max(sigma, q-quantile of sigma across the scored bonds) (spec section 3). A sigma <= SIGMA_TOL is NaN. Intuition: a bond with stale, flat
    prints must not get a near-zero denominator."""
    s = sigma.where(sigma > SIGMA_TOL)
    if s.notna().sum() == 0:
        return s
    return s.clip(lower=float(s.quantile(q)))


def momentum_ratio(total: pd.Series, sigma: pd.Series, n_form: pd.Series, n_vol: pd.Series,
                   min_form: int = MIN_FORM, min_vol: int = MIN_VOL) -> pd.Series:
    """total / sigma where the counts pass (BM-1, BM-2); NaN otherwise (spec section 3 count rules)."""
    ok = (n_form >= min_form) & (n_vol >= min_vol) & sigma.notna()
    return (total / sigma).where(ok)


def leg_weights(sigma: pd.Series) -> pd.Series:
    """Inverse-sigma weights inside one leg, summing to one (van Zundert eq. 4.4, p. 103; spec section 3). The
    scaling of each leg to equal ex-ante volatility needs a covariance model and is not here."""
    w = 1.0 / sigma.where(sigma > 0)
    return w / w.sum()


# ---------------------------------------------------------------- compute


def compute(panels: Mapping[str, pd.DataFrame], as_of: pd.Timestamp, form: int = FORM, skip: int = SKIP,
            vol_window: int = VOL_WINDOW, min_form: int = MIN_FORM, min_vol: int = MIN_VOL,
            max_gap: int = MAX_GAP) -> pd.DataFrame:
    """VAMOM score per bond of the HY universe at as_of (spec build steps 1 to 7). One row per cusip.

    Universe: an `eligible` row at as_of with a yield, rating class BB, B or CCC, and a raw S&P symbol other than
    D or SD. score = standardised percentile rank of vamom, NaN where vamom is NaN. Empty frame (columns COLS)
    without bond_panel or ratings. Higher score = long."""
    as_of = pd.Timestamp(as_of) + pd.offsets.MonthEnd(0)
    if any(panels.get(k) is None or len(panels[k]) == 0 for k in REQUIRED):
        return pd.DataFrame(columns=COLS)
    dt = decision_time(as_of)
    ratings, gics, lev = panels["ratings"], panels.get("gics"), panels.get("leverage")
    p = panels["bond_panel"]
    p = p[p["available_at"] <= dt].copy()
    p["date"] = pd.to_datetime(p["date"])

    # universe at as_of (step 6)
    now = p[p["date"] == as_of].drop_duplicates("cusip", keep="last")
    now = now[eligible(now) & now["yield"].notna() & now["gvkey"].notna()]
    cls = rating_classes(ratings, lev, as_of)
    now = now.assign(rclass=now["gvkey"].map(cls["rclass"]), raw=now["gvkey"].map(cls["raw"]),
                     sector=now["gvkey"].map(_sectors(gics, as_of)))
    now = now[now["rclass"].isin(HY_CLASSES) & ~now["raw"].isin(DEFAULT_SYMBOLS)]
    if now.empty:
        return pd.DataFrame(columns=COLS)

    # returns over the windows, ending at T - skip (steps 2 and 3)
    last = as_of - pd.offsets.MonthEnd(skip)
    first = last - pd.offsets.MonthEnd(max(form, vol_window) + 2 * max_gap)  # gap pairs and their lam months
    hist = p[(p["date"] >= first) & (p["date"] <= last)]
    pairs = monthly_excess_returns(hist, dt, max_gap)
    form_m = pd.date_range(end=last, periods=form, freq="ME")
    vol_m = pd.date_range(end=last, periods=vol_window, freq="ME")
    pairs = pairs[pairs["date"] >= vol_m[0] - pd.offsets.MonthEnd(max_gap - 1)].reset_index(drop=True)

    # DTS residuals with the cell of each pair's start month (step 4)
    keys = pd.DataFrame(index=pairs.index, columns=list(CELL_LEVELS), dtype=object)
    for s, idx in pairs.groupby("start").groups.items():
        g = pairs.loc[idx, "gvkey"]
        keys.loc[idx] = cell_keys(g.map(rating_classes(ratings, lev, s)["rclass"]),
                                  g.map(_sectors(gics, s))).to_numpy()
    pairs["eps"] = dts_residuals(pairs, keys) if len(pairs) else pd.Series(dtype=float)

    # momentum statistics (step 5)
    fr, vr = formation_sum(pairs, "r_ex", form_m), vol_estimate(pairs, "r_ex", vol_m)
    fe, ve = formation_sum(pairs, "eps", form_m), vol_estimate(pairs, "eps", vol_m)
    out = now[["cusip", "gvkey", "rclass", "sector", "g_spread", "n_trades"]].set_index("cusip")
    out = out.join(fr.add_prefix("f_")).join(vr.add_prefix("v_")).join(fe.add_prefix("fe_")).join(ve.add_prefix("ve_"))
    for c in ("f_n", "v_n", "fe_n", "ve_n"):
        out[c] = out[c].fillna(0).astype(int)
    ok_r = (out["f_n"] >= min_form) & (out["v_n"] >= min_vol)
    ok_e = (out["fe_n"] >= min_form) & (out["ve_n"] >= min_vol)
    out["mom_sigma"] = floor_sigma(out["v_sigma"].where(ok_r))
    out["rmom_sigma"] = floor_sigma(out["ve_sigma"].where(ok_e))
    out["raw_mom"] = out["f_total"].where(ok_r)
    out["vamom"] = momentum_ratio(out["f_total"], out["mom_sigma"], out["f_n"], out["v_n"], min_form, min_vol)
    out["rmom"] = momentum_ratio(out["fe_total"], out["rmom_sigma"], out["fe_n"], out["ve_n"], min_form, min_vol)
    out["mom_n_form"], out["mom_n_vol"] = out["f_n"], out["v_n"]

    # rank, standardise (step 7)
    out = out.reset_index()
    out["date"] = as_of
    out["available_at"] = dt
    out["score"] = out["vamom"].rank(pct=True)
    out = standardise_by_date(out, ["score"])
    out["score"] = out["score"].where(out["vamom"].notna())
    return out[COLS].astype({"score": float, "vamom": float, "rmom": float, "raw_mom": float}).reset_index(drop=True)


# ---------------------------------------------------------------- evaluation grid and decision rule


def evaluation_grid(include_rating_cells: bool = True) -> list[dict]:
    """The spec section 7 conflict grid: {raw, va, resid} x HORIZONS x {all, lt1000, lt2000, ex_ccc}.

    Each cell: signal, column (of the compute output), h, subset, max_spread (decimal, strict upper bound, or None),
    classes (rating classes kept). With `include_rating_cells`, the grid adds BB, B and CCC alone, which the VAMOM
    pass needs (spec section 7: VAMOM must stay positive in BB alone). Filter rows with `grid_mask`."""
    subsets = {**GRID_SUBSETS, **(RATING_SUBSETS if include_rating_cells else {})}
    return [{"signal": sig, "column": col, "h": h, "subset": name, "max_spread": cap, "classes": classes}
            for sig, col in GRID_SIGNALS.items() for h in HORIZONS for name, (cap, classes) in subsets.items()]


def grid_mask(df: pd.DataFrame, cell: Mapping) -> pd.Series:
    """Rows of `df` (columns rclass, g_spread at the formation date) inside the grid cell's subset."""
    m = df["rclass"].isin(cell["classes"])
    if cell["max_spread"] is not None:
        m &= not_distressed(df, "g_spread", cell["max_spread"])
    return m


def ic_row(ic: pd.Series, lags: int = HAC_LAGS) -> dict:
    """One row of the IC table from a monthly IC series (beyond spread, after cost): mean_ic, t_hac and the mean IC
    per cycle window, ic_<year> (`hac_mean`, `ic_by_window`)."""
    h = hac_mean(ic, lags)
    return {"mean_ic": h["mean"], "t_hac": h["t"],
            **{f"ic_{y}": v for y, v in ic_by_window(ic, CYCLE_WINDOWS).items()}}


def _row(t: pd.DataFrame, signal: str, h: int, subset: str) -> pd.Series | None:
    r = t[(t["signal"] == signal) & (t["h"] == h) & (t["subset"] == subset)]
    return r.iloc[0] if len(r) else None


def _passes(r: pd.Series | None) -> bool:
    """Spec section 7 pass: mean IC > 0, HAC t >= T_PASS, positive in at least MIN_CYCLES of the 4 windows."""
    if r is None:
        return False
    wins = sum(1 for y in CYCLES if np.isfinite(r.get(f"ic_{y}", np.nan)) and r[f"ic_{y}"] > 0)
    return bool(r["mean_ic"] > 0 and r["t_hac"] >= T_PASS and wins >= MIN_CYCLES)


def _beats(a: pd.Series | None, b: pd.Series | None) -> bool:
    """a beats b: higher mean IC and a higher window IC in at least MIN_CYCLES of the 4 windows (branch 2)."""
    if a is None or b is None:
        return False
    wins = sum(1 for y in CYCLES if np.isfinite(a.get(f"ic_{y}", np.nan)) and
               (not np.isfinite(b.get(f"ic_{y}", np.nan)) or a[f"ic_{y}"] > b[f"ic_{y}"]))
    return bool(a["mean_ic"] > b["mean_ic"] and wins >= MIN_CYCLES)


def choose_branch(ic_table: pd.DataFrame) -> dict:
    """The spec section 7 four-branch decision rule (our choice) on an IC table.

    `ic_table` columns: signal (raw, va, resid), h, subset, mean_ic, t_hac, ic_2008, ic_2015, ic_2020, ic_2022, one
    row per grid cell (`ic_row`). Main tests at h = 6, subset all. Order:
      leg: resid if it passes and beats va (branch 2); else va if it passes and its BB-alone mean IC > 0 (branch 1).
      branch 4: the leg passes in all but fails below 1,000 bp. It overrides 1 and 2 (the edge lives in distress).
      branch 3: no leg, and raw at h = 1 has HAC t <= -T_PASS (the Kelly reversal reading).
      branch 0: no rule applies. No momentum leg.
    The pass for resid in branch 2 is our choice (the spec says only "beats"). Returns branch, leg (column name or
    None) and reason."""
    va, rs = _row(ic_table, "va", 6, "all"), _row(ic_table, "resid", 6, "all")
    bb = _row(ic_table, "va", 6, "bb")
    va_ok = _passes(va) and bb is not None and bb["mean_ic"] > 0
    leg, branch, reason = None, 0, "no branch applies: no momentum leg"
    if _passes(rs) and _beats(rs, va):
        leg, branch, reason = "resid", 2, "RMOM passes and beats VAMOM in mean IC and in 3 of 4 windows"
    elif va_ok:
        leg, branch, reason = "va", 1, "VAMOM passes and RMOM does not beat it"
    low = _row(ic_table, leg, 6, "lt1000") if leg is not None else None
    if low is not None and not _passes(low):
        return {"branch": 4, "leg": None,
                "reason": f"{GRID_SIGNALS[leg]} passes in all but fails below 1,000 bp: route to Section 9"}
    if leg is None:
        raw1 = _row(ic_table, "raw", 1, "all")
        if raw1 is not None and np.isfinite(raw1["t_hac"]) and raw1["t_hac"] <= -T_PASS:
            return {"branch": 3, "leg": None, "reason": "both fail and raw h=1 IC has t <= -2: reversal control only"}
    return {"branch": branch, "leg": GRID_SIGNALS[leg] if leg else None, "reason": reason}
