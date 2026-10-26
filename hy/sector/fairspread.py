"""Sector fair-spread models: a cross-sectional fair spread per GICS sector group on the drivers of that sector.
Spec docs/factors/SECTOR-models.md, section 3.1; methodology Section 7.2 (empirical model, signs), 7.3 (residual and
z), 8 S1 (fair value residual).

For one month end t and one group g with at least MIN_ISSUERS issuers:

    log s_i   = b0 + sum_k b_k z_k(x_ik) + c * z(T_i) + sum_r d_r 1{class_i = r} + e_i       i in group g
    fit       = Huber IRLS (k = 1.345, MAD scale); a driver whose b_k has the wrong sign leaves and the fit reruns
    z_k(x)    = (winsorised x - mean) / sd within the group; a missing x takes the group median
    e_i       = log s_i - log s_fair_i                                         residual: positive = cheap
    score_i   = e_i / (1.4826 MAD of e in the estimation sample)              the 7.3 z with a robust sigma

A thin group (fewer than MIN_ISSUERS issuers, too few degrees of freedom, or no driver with data) takes the pooled
model: the same form on POOLED_DRIVERS over all scored bonds, plus GICS sector effects eta_sector (Section 7.2).

Intuition: a bond is cheap when it pays more than bonds of its own sector with the same leverage, cash conversion,
cycle exposure, maturity and rating. The driver list changes by sector because what drives default risk changes by
sector (docs/framework.md F2). The sign rule keeps every coefficient on the side the methodology argues for, so a
residual is never a sign error (Section 7.2).

Panels. Required: `bond_panel`, `gics`, `leverage`. Optional: `ratings` (class controls and the HY filter),
`compustat_quarterly`, `compustat_annual`, `annual_ebitda` (the drivers of hy.sector.drivers). Without a required
panel the result is an empty frame with columns COLS.
"""

from __future__ import annotations

from typing import Mapping

import numpy as np
import pandas as pd

from hy.backtest import decision_time
from hy.sector.common import month_end, present, universe
from hy.sector.drivers import ALTERNATES, POOLED_DRIVERS, SECTOR_DRIVERS, SIGNS, issuer_drivers

MIN_ISSUERS = 15          # issuers a sector model needs, else the pooled model (our choice)
MIN_DOF = 10              # bonds beyond the number of parameters a fit needs (our choice)
MIN_COVER = 0.6           # share of the group's bonds with a driver value, to keep the driver (our choice)
WINSOR = (0.01, 0.99)     # driver winsorisation quantiles within the group (our choice)
HUBER_K = 1.345           # Huber tuning constant: 95% efficiency under normal errors (Huber 1964; our choice)
HUBER_ITERS = 25
MAD_SCALE = 1.4826        # robust sd = 1.4826 x MAD (hy.peers, decision page 2026-10-23-peer-fair-spread)
HORIZON = 6               # months: two half-lives of a residual (Section 7.5); our default, set on production
SD_TOL = 1e-9             # a driver with a smaller relative sd is a constant (floating noise only)
CLASS_BASE = "B"          # base level of the rating class dummies (our choice: the HY middle)

META = {
    "rank": None,
    "name": "Sector fair-spread residual",
    "level": "bond",
    "horizon_months": HORIZON,
    "needs": ["bond_panel", "gics", "leverage", "ratings", "compustat_quarterly", "compustat_annual",
              "annual_ebitda"],
    "spec": "docs/factors/SECTOR-models.md",
    "section": "7.2; 7.3; 8 S1",
}
REQUIRED = ("bond_panel", "gics", "leverage")

COLS = ["date", "cusip", "score", "available_at", "gvkey", "gsector", "group", "model", "rclass", "g_spread",
        "mod_dur", "dts", "log_s", "log_fair", "s_fair", "resid_log", "resid_sd", "n_issuers", "drivers",
        "n_imputed"]


# ---------------------------------------------------------------- formula helpers


def robust_sd(x: np.ndarray) -> float:
    """1.4826 x median absolute deviation. NaN with no finite value."""
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    if not len(x):
        return np.nan
    return float(MAD_SCALE * np.median(np.abs(x - np.median(x))))


def huber_fit(y: np.ndarray, X: np.ndarray, k: float = HUBER_K, iters: int = HUBER_ITERS) -> np.ndarray:
    """Huber M-estimate of y = X b by iteratively reweighted least squares, scale = robust_sd of the residuals.

    Intuition: a bond far from the line (the mispriced one we look for) gets less weight, so it cannot pull the
    line toward itself. With a zero scale (an exact fit) the OLS answer stands."""
    y, X = np.asarray(y, float), np.asarray(X, float)
    w = np.ones(len(y))
    b = np.zeros(X.shape[1])
    for _ in range(iters):
        r = np.sqrt(w)
        b_new, *_ = np.linalg.lstsq(X * r[:, None], y * r, rcond=None)
        e = y - X @ b_new
        s = robust_sd(e)
        done = np.allclose(b_new, b, atol=1e-10)
        b = b_new
        if not np.isfinite(s) or s <= 0 or done:
            break
        u = np.abs(e) / s
        w = np.where(u <= k, 1.0, k / np.maximum(u, 1e-12))
    return b


def signed_fit(y: np.ndarray, X: pd.DataFrame, signs: Mapping[str, int]) -> tuple[pd.Series, list[str]]:
    """Huber fit with the sign rule of Section 7.2: while a driver column has a coefficient of the wrong sign,
    drop the one most wrong (sign x b lowest) and refit. Columns not in `signs` (intercept, controls) are free.

    Returns the coefficients over the kept columns and the kept driver names."""
    cols = list(X.columns)
    while True:
        b = pd.Series(huber_fit(y, X[cols].to_numpy(float)), index=cols)
        bad = {c: signs[c] * b[c] for c in cols if c in signs and signs[c] * b[c] < 0}
        if not bad:
            return b, [c for c in cols if c in signs]
        cols.remove(min(bad, key=bad.get))


def _zscore(x: pd.Series) -> pd.Series | None:
    """Winsorised z-score within the sample; None when x has no spread."""
    lo, hi = x.quantile(WINSOR[0]), x.quantile(WINSOR[1])
    x = x.clip(lo, hi)
    sd = x.std(ddof=0)
    ok = np.isfinite(sd) and sd > SD_TOL * max(1.0, abs(float(x.mean())))
    return (x - x.mean()) / sd if ok else None


def resolve_drivers(df: pd.DataFrame, names, min_cover: float = MIN_COVER) -> list[str]:
    """Drivers of `names` with data in at least `min_cover` of the rows and some spread; a driver short of data
    takes its ALTERNATES entry (lease-adjusted leverage -> plain leverage)."""
    out: list[str] = []
    for n in names:
        for cand in (n, ALTERNATES.get(n)):
            if cand is None or cand in out or cand not in df:
                continue
            v = df[cand]
            if v.notna().mean() >= min_cover and _zscore(v.dropna()) is not None:
                out.append(cand)
                break
    return out


def design(df: pd.DataFrame, drivers: list[str], sector_fe: bool) -> tuple[pd.DataFrame, pd.Series]:
    """X of the module docstring: const, z-scored drivers (missing -> group median), z(years), class dummies
    (base CLASS_BASE), and with `sector_fe` GICS sector dummies. Also the count of imputed drivers per row."""
    X = pd.DataFrame({"const": 1.0}, index=df.index)
    n_imp = pd.Series(0, index=df.index)
    for d in drivers:
        v = df[d].astype(float)
        n_imp += v.isna().astype(int)
        z = _zscore(v.fillna(v.median()))
        if z is not None:
            X[d] = z
    zt = _zscore(df["years"].astype(float))
    if zt is not None:
        X["years"] = zt
    cls = df["rclass"].dropna()
    if cls.nunique() > 1:
        for c in sorted(cls.unique()):
            if c != CLASS_BASE:
                X[f"cls_{c}"] = (df["rclass"] == c).astype(float)
    if sector_fe:
        secs = sorted(df["gsector"].dropna().unique())
        for s in secs[1:]:
            X[f"sec_{s}"] = (df["gsector"] == s).astype(float)
    return X, n_imp


def fit_model(df: pd.DataFrame, drivers: list[str], sector_fe: bool = False) -> dict | None:
    """One cross-sectional fit (module docstring). None when the sample has too few bonds for its parameters.

    Returns fitted log fair spread, residual, robust sigma, coefficients, kept drivers and imputed counts."""
    X, n_imp = design(df, drivers, sector_fe)
    if len(df) < X.shape[1] + MIN_DOF:
        return None
    y = df["log_s"].to_numpy(float)
    b, kept = signed_fit(y, X, SIGNS)
    fitted = pd.Series(X[b.index].to_numpy(float) @ b.to_numpy(), index=df.index)
    resid = df["log_s"] - fitted
    return {"fitted": fitted, "resid": resid, "sigma": robust_sd(resid.to_numpy()), "coef": b.to_dict(),
            "kept": kept, "n_imputed": n_imp}


# ---------------------------------------------------------------- panel step


def _empty() -> pd.DataFrame:
    return pd.DataFrame(columns=COLS)


def compute(panels: Mapping[str, pd.DataFrame], as_of, min_issuers: int = MIN_ISSUERS,
            drivers: Mapping[str, tuple[str, ...]] | None = None,
            pooled_drivers: tuple[str, ...] = POOLED_DRIVERS) -> pd.DataFrame:
    """Sector fair-spread residual per bond at month end as_of (spec section 3.1). One row per cusip, columns COLS.

    `drivers` overrides SECTOR_DRIVERS per group. `model` is "sector" or "pooled" (thin group), "none" when even the
    pooled fit lacks bonds (score NaN). score = resid_log / resid_sd: higher = cheaper = long. NaN = no score.
    attrs["models"] holds the coefficients per group."""
    as_of = month_end(as_of)
    if any(not present(panels, k) for k in REQUIRED):
        return _empty()
    u = universe(panels, as_of)
    if u.empty:
        return _empty()
    u = u.join(issuer_drivers(panels, as_of), on="gvkey")
    u["log_s"] = np.log(u["g_spread"].astype(float))
    table = drivers or SECTOR_DRIVERS
    pooled = fit_model(u, resolve_drivers(u, pooled_drivers), sector_fe=True)
    for c in ("log_fair", "resid_log", "resid_sd"):
        u[c] = np.nan
    u["model"], u["drivers"], u["n_imputed"], u["n_issuers"] = "none", "", 0, 0
    models: dict[str, dict] = {}
    for grp, sub in u.groupby("group"):
        n_iss = int(sub["gvkey"].nunique())
        res, kind = None, "pooled"
        if n_iss >= min_issuers:
            kept = resolve_drivers(sub, table.get(grp, pooled_drivers))
            res = fit_model(sub, kept) if kept else None
            kind = "sector" if res is not None else "pooled"
        if res is None and pooled is not None:
            res = {k: (v.loc[sub.index] if isinstance(v, pd.Series) else v) for k, v in pooled.items()}
        if res is None:
            u.loc[sub.index, "n_issuers"] = n_iss
            models[grp] = {"model": "none", "n_issuers": n_iss}
            continue
        idx = sub.index
        u.loc[idx, "log_fair"] = res["fitted"].loc[idx]
        u.loc[idx, "resid_log"] = res["resid"].loc[idx]
        u.loc[idx, "resid_sd"] = res["sigma"]
        u.loc[idx, "model"] = kind
        u.loc[idx, "drivers"] = ",".join(res["kept"])
        u.loc[idx, "n_imputed"] = res["n_imputed"].loc[idx].to_numpy()
        u.loc[idx, "n_issuers"] = n_iss
        models[grp] = {"model": kind, "n_issuers": n_iss, "coef": res["coef"], "drivers": res["kept"]}
    u["s_fair"] = np.exp(u["log_fair"].astype(float))
    sd = u["resid_sd"].astype(float)
    u["score"] = u["resid_log"].astype(float) / sd.where(sd > 0)
    u["date"], u["available_at"] = as_of, decision_time(as_of)
    out = u[COLS].astype({"score": float, "log_fair": float, "s_fair": float, "resid_log": float,
                          "resid_sd": float, "n_issuers": int, "n_imputed": int}).reset_index(drop=True)
    out.attrs["models"] = models
    return out
