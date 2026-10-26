"""F03 Residual equity momentum spillover (rank 3). Spec docs/factors/F03-residual-equity-momentum.md; methodology
7.4 (OneScore paragraph), Section 8 (E16 equity momentum) and Section 11 (backtest design). Source: van Zundert
(2018), PhD thesis, ch. 5, eq. 5.3 (p. 137); hedge on p. 139. Pages are printed pages.

    E_i,m   = ret_i,m - RF_m                                              stock return over the 1-month T-bill
    E_i,m   = alpha_i + beta_i RMRF_m + eps_i,m,   m in [t-36, t-1]       one-factor market model, OLS (eq. 5.3)
    RM_i,t  = (prod_{k=1..6} (1 + eps_i,t-k) - 1) / sd(eps_i,t-36 .. t-1)  compounded last 6 residuals over their sd
    h_t     = ls_t - beta_DEF,t DEF_t,  beta_DEF,t from months t-36 .. t-1 (our choice: the source uses the full sample)

Intuition: rank on firm-specific equity news only. The market part of the stock return carries the default-risk
tilt that crashes after equity bear markets (pp. 137-139).

Inputs. `equity_monthly` (gvkey, datadate, ret, available_at) and a new optional panel `ff_factors`: one row per
month end with `date`, `mktrf` (Fama-French Mkt-RF, decimal), `rf` (1-month T-bill, decimal) and `available_at`
(the download time). Without `ff_factors` or `equity_monthly` the score is empty. No proxy replaces RMRF or RF.

Bonds. compute() copies the issuer RM to each eligible bond of the issuer in `bond_panel` at as_of. The column
`weight` is the bond's weight inside its company for the portfolio return. The source weights by market value
(p. 131). Where the optional `bond_panel` column `amt_out` (par amount outstanding) exists for every bond of the
company, weight = price x amt_out over the company total (`weight_basis` "mv"). Otherwise the bonds of the
company take equal weights (`weight_basis` "equal"). The production panel has no amt_out today.
"""

from __future__ import annotations

from typing import Mapping

import numpy as np
import pandas as pd

from hy.backtest import decision_time, eligible, realised_excess_return

WINDOW = 36          # months of the market-model estimation window, moving (p. 137)
FORM = 6             # J: residuals compounded in the formation period (p. 137; base case p. 132)
SKIP = 1             # implementation lag in months: skip month t (p. 137, p. 132)
MIN_OBS = 36         # returns the window needs: all 36 (spec build step 3; our choice, the source is silent)
HOLD = 6             # K: holding period, six overlapping books (p. 132)
HEDGE_WINDOW = 36    # months of past long-short and DEF returns for beta_DEF (our choice: the source is in-sample)
SD_DDOF = 1          # sample sd of the 36 residuals (our choice: the source does not give the divisor)

META = {
    "rank": 3,
    "name": "Residual equity momentum spillover",
    "level": "bond",
    "horizon_months": HOLD,
    "needs": ["bond_panel", "equity_monthly", "ff_factors"],
    "spec": "docs/factors/F03-residual-equity-momentum.md",
    "section": "8",
}

ISSUER_COLS = ["date", "gvkey", "score", "available_at", "rm_beta", "rm_sd", "n_obs"]
BOND_COLS = ["date", "cusip", "score", "available_at", "gvkey", "rm_beta", "rm_sd", "weight", "weight_basis"]


def window_months(as_of: pd.Timestamp, window: int = WINDOW, skip: int = SKIP) -> pd.DatetimeIndex:
    """Month ends t-window-skip+1 .. t-skip of the estimation window (spec build step 3; p. 137, lag 1 month)."""
    last = pd.Timestamp(as_of) + pd.offsets.MonthEnd(0) - pd.offsets.MonthEnd(skip)
    return pd.date_range(end=last, periods=window, freq="ME")


def market_residuals(excess: pd.DataFrame, mktrf: pd.Series) -> tuple[pd.DataFrame, pd.Series]:
    """OLS of each column of `excess` (months x gvkey) on `mktrf` with an intercept (eq. 5.3, p. 137).

    Returns the residuals (same shape) and the betas. Each column must be complete. Intuition: eps is the stock
    return that the equity market does not explain."""
    x = mktrf.to_numpy(float)
    xc = x - x.mean()
    y = excess.to_numpy(float)
    yc = y - y.mean(axis=0)
    beta = xc @ yc / (xc @ xc)
    resid = yc - np.outer(xc, beta)
    return pd.DataFrame(resid, index=excess.index, columns=excess.columns), pd.Series(beta, index=excess.columns)


def residual_momentum(resid: pd.DataFrame, form: int = FORM, ddof: int = SD_DDOF) -> tuple[pd.Series, pd.Series]:
    """RM per column: compounded last `form` residuals over the sd of all window residuals (p. 137).

    Compounds, never sums: prod(1 + eps) - 1. Intuition: a firm-specific rally scaled by the firm's own noise."""
    comp = (1.0 + resid.iloc[-form:]).prod(axis=0) - 1.0
    sd = resid.std(axis=0, ddof=ddof)
    return (comp / sd.where(sd > 0)).rename("rm"), sd.rename("rm_sd")


def _fit(excess: pd.DataFrame, mktrf: pd.Series, form: int) -> pd.DataFrame:
    """Market model then RM for complete columns of `excess`. Rows gvkey, score, rm_beta, rm_sd."""
    resid, beta = market_residuals(excess, mktrf.loc[excess.index])
    rm, sd = residual_momentum(resid, form)
    return pd.DataFrame({"gvkey": excess.columns, "score": rm.to_numpy(), "rm_beta": beta.to_numpy(),
                         "rm_sd": sd.to_numpy()})


def issuer_scores(equity: pd.DataFrame, ff: pd.DataFrame, as_of: pd.Timestamp, window: int = WINDOW,
                  form: int = FORM, skip: int = SKIP, min_obs: int = MIN_OBS) -> pd.DataFrame:
    """RM per gvkey at month end as_of (spec build steps 2 to 4). Reads only rows with available_at <=
    decision_time(as_of). An issuer needs `min_obs` returns in the window and all `form` formation returns. The fit
    uses the present months only. A month without RMRF and RF drops out of every window. Without RMRF and RF for
    the `form` formation months, no issuer scores. Columns ISSUER_COLS."""
    dt = decision_time(as_of)
    months = window_months(as_of, window, skip)
    f = ff[ff["available_at"] <= dt].copy()
    f["date"] = pd.to_datetime(f["date"]) + pd.offsets.MonthEnd(0)
    f = f.sort_values("available_at").drop_duplicates("date", keep="last").set_index("date")
    f = f.reindex(months)[["mktrf", "rf"]].dropna()
    e = equity[equity["available_at"] <= dt].copy()
    e["datadate"] = pd.to_datetime(e["datadate"]) + pd.offsets.MonthEnd(0)
    e = e[e["datadate"].isin(f.index)].sort_values("available_at").drop_duplicates(["gvkey", "datadate"], keep="last")
    wide = e.pivot(index="datadate", columns="gvkey", values="ret").reindex(f.index)
    wide = wide.sub(f["rf"], axis=0)
    n_obs = wide.notna().sum(axis=0)
    recent = wide.index[-form:].equals(months[-form:]) if len(wide) >= form else False
    keep = n_obs[(n_obs >= min_obs) & wide.iloc[-form:].notna().all(axis=0)].index if recent else []
    complete = [g for g in keep if n_obs[g] == len(wide)]
    parts = [_fit(wide[complete], f["mktrf"], form)] if complete else []
    # an issuer with gaps (only when min_obs < window) gets its own fit on its present months
    parts += [_fit(wide[[g]].dropna(), f["mktrf"], form) for g in keep if n_obs[g] < len(wide)]
    out = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=["gvkey", "score", "rm_beta", "rm_sd"])
    out["n_obs"] = out["gvkey"].map(n_obs).astype("Int64") if len(out) else pd.Series(dtype="Int64")
    out["date"] = pd.Timestamp(as_of)
    out["available_at"] = dt
    return out[ISSUER_COLS].astype({"score": float, "rm_beta": float, "rm_sd": float}).reset_index(drop=True)


def company_weights(bonds: pd.DataFrame) -> pd.DataFrame:
    """Weight of each bond inside its gvkey (p. 131): price x amt_out where `amt_out` exists for every bond of the
    company, else equal weights. Returns columns weight and weight_basis on the index of `bonds`."""
    n = bonds.groupby("gvkey")["cusip"].transform("count")
    w = pd.DataFrame({"weight": 1.0 / n, "weight_basis": "equal"}, index=bonds.index)
    if "amt_out" in bonds.columns:
        mv = bonds["price"].astype(float) * bonds["amt_out"].astype(float)
        full = mv.notna().groupby(bonds["gvkey"]).transform("all") & (mv.groupby(bonds["gvkey"]).transform("sum") > 0)
        w.loc[full, "weight"] = (mv / mv.groupby(bonds["gvkey"]).transform("sum"))[full]
        w.loc[full, "weight_basis"] = "mv"
    return w


def compute(panels: Mapping[str, pd.DataFrame], as_of: pd.Timestamp, window: int = WINDOW, form: int = FORM,
            skip: int = SKIP, min_obs: int = MIN_OBS) -> pd.DataFrame:
    """RM per eligible bond of bond_panel at as_of (spec build step 5). One row per cusip. score = the issuer RM,
    NaN where the issuer has none. Empty frame (columns BOND_COLS) when ff_factors, equity_monthly or bond_panel is
    missing. Higher score = long."""
    as_of = pd.Timestamp(as_of)
    if any(panels.get(k) is None or len(panels[k]) == 0 for k in META["needs"]):
        return pd.DataFrame(columns=BOND_COLS)
    dt = decision_time(as_of)
    iss = issuer_scores(panels["equity_monthly"], panels["ff_factors"], as_of, window, form, skip, min_obs)
    p = panels["bond_panel"]
    p = p[(p["available_at"] <= dt) & (pd.to_datetime(p["date"]) == as_of)]
    p = p[eligible(p) & p["gvkey"].notna()].drop_duplicates("cusip", keep="last")
    if p.empty:
        return pd.DataFrame(columns=BOND_COLS)
    out = p[["cusip", "gvkey"]].join(company_weights(p))
    out = out.merge(iss[["gvkey", "score", "rm_beta", "rm_sd"]], on="gvkey", how="left")
    out["date"] = as_of
    out["available_at"] = dt
    return out[BOND_COLS].astype({"score": float}).reset_index(drop=True)


def default_factor(panel: pd.DataFrame, as_of: pd.Timestamp) -> pd.Series:
    """DEF per month t: equal-weight mean 1-month excess return over duration-matched Treasuries of the eligible
    bonds (p. 132; spec build step 8), from `realised_excess_return(h=1, beta=0)`. Indexed by the start month t,
    so DEF at t is the return over (t, t+1]. Reads only rows with available_at <= as_of."""
    xr = realised_excess_return(panel[panel["available_at"] <= as_of], 1, as_of, beta=0.0)
    return xr.groupby("date")["realised"].mean().rename("def_xr")


def def_hedge(ls: pd.Series, def_xr: pd.Series, window: int = HEDGE_WINDOW) -> pd.DataFrame:
    """beta_DEF hedge of a monthly long-short return (p. 139): h_t = ls_t - beta_t DEF_t.

    beta_t = cov(ls, DEF) / var(DEF) over the `window` months before t only (our choice; the source's full-sample
    beta of -0.52, Table 5.5 p. 151, looks ahead). beta_t needs all `window` past pairs, else NaN. Columns
    def_beta and ls_hedged. Intuition: the long-short is short credit beta, so add back beta x the market."""
    df = pd.concat([ls.rename("ls"), def_xr.rename("def")], axis=1).sort_index().dropna()
    past = df.shift(1)
    cov = past["ls"].rolling(window, min_periods=window).cov(past["def"])
    var = past["def"].rolling(window, min_periods=window).var()
    beta = (cov / var.where(var > 0)).rename("def_beta")
    return pd.DataFrame({"def_beta": beta, "ls_hedged": df["ls"] - beta * df["def"]})
