"""F10 Market-neutral credit carry (rank 10). Spec docs/factors/F10-market-neutral-carry.md; methodology Section 8
(composite, neutralisation) and Section 9.3 (carry = coupon accrual plus roll-down). Source: Tzotchev, "Market-neutral
carry" (J.P. Morgan, 4 October 2018), PDF pp. 3 to 5 (model), p. 7 (estimation), pp. 16 to 18 (credit), pp. 49 to 51
(optimisation). Pages are PDF pages. The source tests CDS indices only (Table 11, p. 18).

    c_b      = s_b h - D_b (shat(T_b - h) - shat(T_b))         1-month carry: spread carry plus roll-down (p. 17)
    shat(T)  = a0 + a1 (1 - e^(-0.4 T)) / (0.4 T)               issuer curve, else class curve, else HY, else flat
    X        = [1, DTS, D, 1{B}, 1{CCC}],  DTS = D s            market, duration and rating exposures (our choice)
    e        = c - X khat,  khat = (X'WX)^-1 X'Wc,  W = 1/DTS^2  carry no exposure pays for
    score    = e / DTS,  w_opt proportional to W e              residual carry per unit risk; X'w_opt = 0

Intuition: raw HY carry is mostly pay for beta. The source hedges with w'B = 0 and then the expected return is the
carry (p. 4). Under that hedge the variance is w'Dw, so max w'c with X'w = 0 and a variance cap gives w = W e: the
WLS residual of carry on the exposures. If carry is only beta pay, e = 0 and no hedged carry exists (p. 5).

Source against us. The source fits B per asset by PCA on past returns (p. 7, Kaiser rule p. 8). We use observable
exposures, which the source allows (p. 3). Option `market="beta"` swaps DTS for a 24-month time-series beta to the
equal-weight HY excess return. The long-only hedge with CDX HY or HYG lives in the spec, not here.

Inputs. `bond_panel` and `ratings` are required. `leverage` is optional (implied class for unrated issuers).
Without `bond_panel` or `ratings` the result is an empty frame.
"""

from __future__ import annotations

from typing import Mapping

import numpy as np
import pandas as pd

from hy.backtest import decision_time, eligible, not_distressed
from hy.factors.f04_bond_momentum import monthly_excess_returns, rating_classes
from hy.factors.f06_issuer_curve_residual import SHOCK_LAMBDA, shock_basis, within_slope
from hy.peers import MIN_PEERS

HOLD = 1                    # horizon in months: 1-month carry (spec section 3; reader block G-F3)
MIN_ISSUER_BONDS = 3        # bonds an issuer curve needs (our choice)
MIN_SPAN = 2.0              # maturity span in years an issuer curve needs (our choice)
MIN_XS = 30                 # scored bonds the cross-sectional WLS needs (our choice)
BETA_WINDOW = 24            # months of the time-series beta (our choice; the source uses 3 m to 2 y, p. 7)
BETA_MIN_OBS = 12           # monthly returns the beta needs (our choice)
GROSS = 2.0                 # sum of |w_opt|: one unit long, one unit short (our choice)
HY_CLASSES = ("BB", "B", "CCC")   # scored universe (spec build step 2)
DEFAULT_SYMBOLS = ("D", "SD")     # raw S&P symbols of a defaulted issuer: never scored (spec build step 2)

META = {
    "rank": 10,
    "name": "Market-neutral credit carry",
    "level": "bond",
    "horizon_months": HOLD,
    "needs": ["bond_panel", "ratings", "leverage"],
    "spec": "docs/factors/F10-market-neutral-carry.md",
    "section": "8",
}
REQUIRED = ("bond_panel", "ratings")

COLS = ["date", "cusip", "score", "available_at", "gvkey", "rclass", "g_spread", "mod_dur", "spread_carry", "roll",
        "carry", "slope", "curve_source", "dts", "beta_ts", "carry_resid", "w_opt", "status"]


# ---------------------------------------------------------------- formula helpers


def spread_carry(g_spread: np.ndarray | float, h: float) -> np.ndarray:
    """s h: the spread over Treasuries earned over h years (spec section 3). The CDS analogue is the coupon (p. 17)."""
    return np.asarray(g_spread, dtype=float) * h


def curve_slope(T: np.ndarray, s: np.ndarray, lam: float = SHOCK_LAMBDA) -> float:
    """a1 of the OLS fit s = a0 + a1 x(T), x the F06 forward shock basis (spec section 3; JPM 2012 p. 22).

    x falls in T, so an upward-sloping curve has a1 < 0. NaN with fewer than 2 distinct maturities."""
    x = shock_basis(np.asarray(T, dtype=float), lam)
    if len(x) < 2 or np.ptp(x) <= 0:
        return np.nan
    xc = x - x.mean()
    return float(xc @ (np.asarray(s, dtype=float) - np.mean(s)) / (xc @ xc))


def roll_down(mod_dur: np.ndarray, T: np.ndarray, slope: np.ndarray, h: float,
              lam: float = SHOCK_LAMBDA) -> np.ndarray:
    """-D (shat(T - h) - shat(T)) = -D a1 (x(T - h) - x(T)) (spec section 3; source -CD (S_T-1 - S_T), p. 17).

    Intuition: on an upward curve the bond rolls to a lower spread as it ages, and the price gains D times the
    fall. A NaN slope (no curve) gives roll 0: the flat-curve carry of Israel et al. (OAS alone, p. 7)."""
    T = np.asarray(T, dtype=float)
    a1 = np.nan_to_num(np.asarray(slope, dtype=float), nan=0.0)
    dx = shock_basis(np.maximum(T - h, 1e-6), lam) - shock_basis(T, lam)
    return -np.asarray(mod_dur, dtype=float) * a1 * dx


def exposures(df: pd.DataFrame, market: str = "dts") -> pd.DataFrame:
    """X of spec section 3: const, market (dts, beta_ts or both), dur, and class dummies B and CCC (BB the base).

    Intuition: the intercept is the source's w'a = 0 (p. 4). The rest are the betas a carry book must not hold."""
    X = pd.DataFrame({"const": 1.0}, index=df.index)
    if market in ("dts", "both"):
        X["dts"] = df["dts"].astype(float)
    if market in ("beta", "both"):
        X["beta_ts"] = df["beta_ts"].astype(float)
    X["dur"] = df["mod_dur"].astype(float)
    for c in HY_CLASSES[1:]:
        X[f"cls_{c}"] = (df["rclass"] == c).astype(float)
    return X


def wls_residual(c: np.ndarray, X: np.ndarray, w: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """e = c - X khat, khat = (X'WX)^-1 X'Wc, W = diag(w) (spec section 3). Returns e and khat.

    The normal equations give X'We = 0 exactly: the book w_opt = W e holds no exposure. With equal weights e is the
    `hy.signals.neutralise` residual. A rank-deficient X (an empty class) takes the minimum-norm khat."""
    c, X, w = np.asarray(c, float), np.asarray(X, float), np.asarray(w, float)
    r = np.sqrt(w)
    k, *_ = np.linalg.lstsq(X * r[:, None], c * r, rcond=None)
    return c - X @ k, k


def hedge_weights(e: np.ndarray, w: np.ndarray, gross: float = GROSS) -> np.ndarray:
    """w_opt = W e scaled to sum |w_opt| = gross (spec section 3; source optimum, pp. 4 and 49 to 50).

    Intuition: hold each bond in proportion to its residual carry over its idiosyncratic variance."""
    v = np.asarray(w, float) * np.asarray(e, float)
    tot = np.nansum(np.abs(v))
    return v * gross / tot if tot > 0 else np.full_like(v, np.nan)


def rolling_beta(pairs: pd.DataFrame, months: pd.DatetimeIndex, min_obs: int = BETA_MIN_OBS) -> pd.Series:
    """Time-series beta per cusip to the equal-weight mean excess return (spec section 3, option "beta").

    `pairs` comes from `f04.monthly_excess_returns`. Only 1-month pairs ending in `months` count. beta =
    cov(r_b, m) / var(m) over the months the bond has, at least `min_obs`. Intuition: the per-asset loading of
    the source's time-series factor model (p. 4), with one observable factor instead of PCs."""
    p = pairs[(pairs["gap_k"] == 1) & pairs["date"].isin(months)]
    if p.empty:
        return pd.Series(dtype=float)
    wide = p.pivot_table(index="date", columns="cusip", values="r_ex", aggfunc="last")
    m = wide.mean(axis=1)
    out = {}
    for cusip in wide.columns:
        ok = wide[cusip].notna()
        if ok.sum() < min_obs:
            continue
        x, y = m[ok].to_numpy(), wide.loc[ok, cusip].to_numpy()
        xc = x - x.mean()
        out[cusip] = float(xc @ (y - y.mean()) / (xc @ xc)) if xc @ xc > 0 else np.nan
    return pd.Series(out, dtype=float)


# ---------------------------------------------------------------- panel steps


def slopes(bonds: pd.DataFrame, lam: float = SHOCK_LAMBDA) -> pd.DataFrame:
    """Curve slope and its source per bond (spec section 3): issuer, else class, else hy, else flat.

    Issuer: MIN_ISSUER_BONDS or more bonds over MIN_SPAN years. Class and hy: the within-issuer slope of
    `f06.within_slope`, with MIN_PEERS or more multi-bond issuers. Intuition: the group gives the shape only."""
    out = pd.DataFrame({"slope": np.nan, "curve_source": "flat"}, index=bonds.index)
    x = shock_basis(bonds["years"].to_numpy(float), lam)
    groups = [("hy", pd.Series("all", index=bonds.index)), ("class", bonds["rclass"])]
    for name, key in groups:                       # coarse first, finer levels overwrite
        for _, idx in key.groupby(key).groups.items():
            pos = bonds.index.get_indexer(idx)
            a1, _, n_i = within_slope(x[pos], bonds["g_spread"].to_numpy(float)[pos], bonds["gvkey"].to_numpy()[pos])
            if n_i >= MIN_PEERS and np.isfinite(a1):
                out.loc[idx, ["slope", "curve_source"]] = [a1, name]
    for _, g in bonds.groupby("gvkey"):
        if len(g) >= MIN_ISSUER_BONDS and np.ptp(g["years"].to_numpy(float)) >= MIN_SPAN:
            a1 = curve_slope(g["years"].to_numpy(float), g["g_spread"].to_numpy(float), lam)
            if np.isfinite(a1):
                out.loc[g.index, ["slope", "curve_source"]] = [a1, "issuer"]
    return out


def compute(panels: Mapping[str, pd.DataFrame], as_of: pd.Timestamp, horizon_months: int = HOLD,
            market: str = "dts", weighting: str = "dts", beta_window: int = BETA_WINDOW,
            beta_min_obs: int = BETA_MIN_OBS) -> pd.DataFrame:
    """F10 score per HY bond at month end `as_of` (spec build steps 1 to 5; methodology Section 8). One row per cusip.

    market "dts" (default), "beta" or "both" picks the market exposure. weighting "dts" uses W = 1/DTS^2,
    "equal" uses W = 1. score = carry_resid / DTS, NaN where a bond lacks an input or fewer than MIN_XS bonds
    score. Empty frame (columns COLS) without bond_panel or ratings. Higher score = long."""
    if market not in ("dts", "beta", "both") or weighting not in ("dts", "equal"):
        raise ValueError("market must be dts, beta or both; weighting dts or equal")
    as_of = pd.Timestamp(as_of) + pd.offsets.MonthEnd(0)
    if any(panels.get(k) is None or len(panels[k]) == 0 for k in REQUIRED):
        return pd.DataFrame(columns=COLS)
    dt = decision_time(as_of)
    p = panels["bond_panel"]
    p = p[p["available_at"] <= dt].copy()
    p["date"] = pd.to_datetime(p["date"])

    # universe at as_of (steps 1 and 2)
    now = p[p["date"] == as_of].drop_duplicates("cusip", keep="last")
    now = now[eligible(now) & not_distressed(now) & now["gvkey"].notna()]
    cls = rating_classes(panels["ratings"], panels.get("leverage"), as_of)
    now = now.assign(rclass=now["gvkey"].map(cls["rclass"]), raw=now["gvkey"].map(cls["raw"]))
    now = now[now["rclass"].isin(HY_CLASSES) & ~now["raw"].isin(DEFAULT_SYMBOLS)].reset_index(drop=True)
    if now.empty:
        return pd.DataFrame(columns=COLS)

    # carry (step 3)
    h = horizon_months / 12.0
    now = now.join(slopes(now))
    now["spread_carry"] = spread_carry(now["g_spread"], h)
    now["roll"] = roll_down(now["mod_dur"], now["years"], now["slope"], h)
    now["carry"] = now["spread_carry"] + now["roll"]
    now["dts"] = now["mod_dur"].astype(float) * now["g_spread"].astype(float)

    # exposures (step 4)
    now["beta_ts"] = np.nan
    if market in ("beta", "both"):
        months = pd.date_range(end=as_of, periods=beta_window, freq="ME")
        hist = p[(p["date"] >= months[0] - pd.offsets.MonthEnd(1)) & (p["date"] <= as_of)]
        now["beta_ts"] = now["cusip"].map(rolling_beta(monthly_excess_returns(hist, dt, 1), months, beta_min_obs))
    X = exposures(now, market)
    ok = np.isfinite(X.to_numpy(float)).all(axis=1) & np.isfinite(now["carry"].to_numpy(float)) & (now["dts"] > 0)
    now["status"] = np.where(ok, "ok", "no_input")

    # WLS residual, score and book (step 5)
    now["carry_resid"], now["w_opt"], now["score"] = np.nan, np.nan, np.nan
    if ok.sum() < MIN_XS:
        now.loc[ok, "status"] = "few_bonds"
    else:
        d = now.loc[ok]
        w = 1.0 / d["dts"].to_numpy(float) ** 2 if weighting == "dts" else np.ones(len(d))
        e, _ = wls_residual(d["carry"].to_numpy(float), X.loc[ok].to_numpy(float), w)
        now.loc[ok, "carry_resid"] = e
        now.loc[ok, "w_opt"] = hedge_weights(e, w)
        now.loc[ok, "score"] = e / d["dts"].to_numpy(float)
    now["date"], now["available_at"] = as_of, dt
    return now[COLS].astype({"score": float, "carry_resid": float, "w_opt": float}).reset_index(drop=True)
