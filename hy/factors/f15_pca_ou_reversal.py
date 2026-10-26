"""F15 PCA residual reversal with an Ornstein-Uhlenbeck s-score (rank 15). Spec docs/factors/F15-pca-ou-reversal.md;
methodology Section 8 (a new short-horizon leg) and Section 7.5 (AR(1) residual and half-life). Source: Tomasi et
al., Deutsche Bank Quantcraft "Reversion: new horizons" (2021), pp. 5 to 7 and Appendix pp. 22 to 23, after
Avellaneda and Lee (2009). Pages are PDF pages.

    R* = (R - mean R) / sd R = U S V',  F = U_n S_n                   PCA on z-scored returns (pp. 5 to 6)
    r_b,u = c_b + F_u beta_b + eps_b,u,  u in the last T' periods      residual regression with intercept (p. 6)
    X_k = sum_{u<=k} eps_u,  X_k+1 = a + b X_k + e_k+1                OU by lag-1 OLS (Eqs. A1, A2, p. 22)
    mu = a / (1 - b),  theta = -ln b * A,  sigma_eq = sqrt(var e / (1 - b^2))      (Eqs. A3, A4, A6, A7)
    s = -(X_T' - (mu - mu*)) / sigma_eq,  winsorised at +-4            (Eq. A8, p. 22; p. 23)

Intuition: once the common factors leave the return, the residual price drifts back to its own mean. s is the gap
in units of the residual's equilibrium volatility. A bond below its equilibrium (cheap) has s > 0: long.

Centring. The regression intercept makes X_T' = 0 (p. 22). The source then puts the cross-sectional mean mu* in
place of mu, which gives every bond the same sign. Our choice: mu - mu* (the Avellaneda-Lee centred form). The
option `mu_mode` "own" uses mu and "pooled" uses mu* (the literal text).

Inputs. `bond_panel` is required. Monthly (default): excess returns over the duration-matched Treasury from
`hy.factors.f04_bond_momentum.monthly_excess_returns`. Daily (`freq="daily"`): a new optional panel `bond_daily`
with the F02 columns `cusip`, `date` (trade day), `g_spread` (the par-weighted mean of the day's trades) and
`available_at` (trade day + 1 day). The daily return is the spread return s_d-1 dt - D (s_d - s_d-1), with D the
bond's `mod_dur` at as_of. Without `bond_panel`, or without `bond_daily` when freq is "daily", the result is empty.

Bid-ask bounce. Both inputs are trade-weighted: the monthly mark is the par-weighted price of the month's last 7
days, and the daily spread is the par-weighted day mean. The window also skips one period: monthly it ends at
t - 1 month, daily 7 calendar days before t. The price that starts the outcome return never enters the signal.
"""

from __future__ import annotations

from typing import Mapping

import numpy as np
import pandas as pd

from hy.backtest import decision_time, eligible, not_distressed
from hy.factors.f04_bond_momentum import MAX_GAP, monthly_excess_returns, spread_months
from hy.signals import half_life

N_PCS = 3                 # statistical factors removed; source tests 1, 2, 3, 4, 6, 12 (p. 6). Our choice: 3
PCA_MONTHS = 36           # PCA window T: the 3-year case (p. 6), in months. Our choice of frequency
OU_MONTHS = 12            # residual and OU window T': the one-year case (p. 6), in months
SKIP_MONTHS = 1           # monthly window ends at t - 1 (spec section 3, bounce). Our choice
PCA_DAYS = 252            # daily PCA window in trading days. Our choice: one year, TRACE histories are short
OU_DAYS = 63              # daily T': the one-quarter case (p. 6), in trading days
SKIP_DAYS = 7             # daily window ends 7 calendar days before t, the span of the month-end mark. Our choice
ANNUAL = {"monthly": 12, "daily": 252}   # A in theta = -ln b * A; the source uses 52 for weeks (Eq. A4)
MIN_PCA_FRAC = 2 / 3      # a column enters the PCA with 24 of 36 months (168 of 252 days). Our choice
MIN_TRADE_FRAC = 0.5      # daily: half the T' days need a trade (spec section 3). Our choice
MAX_FFILL_DAYS = 10       # daily: carry the last spread over at most 10 days without a trade. Our choice
MAX_HL_FRAC = 0.5         # speed filter: half-life <= T' / 2 periods (after Avellaneda and Lee). Our choice
WINSOR = 4.0              # winsorise s at +-4 (p. 23)
VR_K = 3                  # variance-ratio horizon of the diagnostic (Family 3 leaves k open). Our choice
ENTRY_Q, EXIT_Q = 0.10, 0.30   # hysteresis: open in the top 10%, close below 30% (p. 3; best global p. 4 note 9)
HOLD = 1                  # holding period in months (spec section 2). Our choice: one rebalance

META = {
    "rank": 15,
    "name": "PCA residual reversal with an Ornstein-Uhlenbeck s-score",
    "level": "bond",
    "horizon_months": HOLD,
    "needs": ["bond_panel", "bond_daily"],
    "spec": "docs/factors/F15-pca-ou-reversal.md",
    "section": "8",
}

FIT_COLS = ["status", "x_last", "mu", "b", "theta", "half_life", "sigma_eq", "vr", "n_obs"]
COLS = ["date", "cusip", "score", "available_at", "gvkey", "status", "x_last", "mu", "mu_star", "b", "theta",
        "half_life", "sigma_eq", "n_pcs", "var_explained", "vr", "n_obs", "pct", "entry_signal", "freq"]


# ---------------------------------------------------------------- formula helpers


def pca_factors(R: np.ndarray, n_pcs: int = N_PCS, var_frac: float | None = None) -> tuple[np.ndarray, int, float]:
    """Statistical factors F = U_n S_n of the z-scored return matrix R (T x N) (spec section 3; pp. 5 to 6).

    Each column is z-scored on its present values, then a missing value is set to 0 (our choice). n is `n_pcs`,
    or with `var_frac` the smallest n whose squared singular values reach that share of the total (p. 5 note 13).
    Returns F (T x n), n and the variance share of the n factors. Intuition: the first factors are the market and
    sector moves that a bond residual must not carry."""
    R = np.asarray(R, dtype=float)
    Z = (R - np.nanmean(R, axis=0)) / np.nanstd(R, axis=0, ddof=1)
    U, S, _ = np.linalg.svd(np.nan_to_num(Z, nan=0.0), full_matrices=False)
    share = np.cumsum(S ** 2) / np.sum(S ** 2)
    n = int(np.searchsorted(share, var_frac - 1e-12) + 1) if var_frac is not None else int(n_pcs)
    n = max(1, min(n, len(S)))
    return U[:, :n] * S[:n], n, float(share[n - 1])


def pc_residuals(Y: np.ndarray, F: np.ndarray) -> np.ndarray:
    """Residuals of the OLS of each column of Y (T' x N, complete) on [1, F] (T' x n) (step 5, p. 6).

    One design matrix serves every column (p. 6 note 14). The intercept makes each residual column sum to zero."""
    X = np.column_stack([np.ones(len(F)), F])
    coef, *_ = np.linalg.lstsq(X, Y, rcond=None)
    return Y - X @ coef


def ou_fit(eps: np.ndarray, annual: float = ANNUAL["monthly"]) -> dict[str, float]:
    """OU parameters of one residual series by the lag-1 OLS of X (Appendix, Eqs. A1 to A7, p. 22).

    X_k = cumulative sum of eps. X_k+1 = a + b X_k + e. var(e) = RSS / (n - 1 - 2). mu = a / (1 - b),
    theta = -ln(b) * annual, sigma_eq = sqrt(var e / (1 - b^2)), sigma = sigma_eq sqrt(2 theta). Status
    "no_reversion" when b is outside (0, 1) (p. 22): mu, theta and sigma_eq are then NaN."""
    x = np.cumsum(np.asarray(eps, dtype=float))
    x0, x1 = x[:-1], x[1:]
    out = {"status": "no_reversion", "x_last": float(x[-1]), "a": np.nan, "b": np.nan, "mu": np.nan,
           "theta": np.nan, "sigma_eq": np.nan, "sigma": np.nan}
    sxx = float(np.sum((x0 - x0.mean()) ** 2))
    if len(x) < 4 or sxx <= 0:
        return out
    b = float(np.sum((x0 - x0.mean()) * (x1 - x1.mean())) / sxx)
    a = float(x1.mean() - b * x0.mean())
    var_e = float(np.sum((x1 - a - b * x0) ** 2) / (len(x) - 1 - 2))
    out.update(a=a, b=b)
    if not 0.0 < b < 1.0:
        return out
    theta = -np.log(b) * annual
    sigma_eq = np.sqrt(var_e / (1.0 - b * b))
    out.update(status="ok", mu=a / (1.0 - b), theta=float(theta), sigma_eq=float(sigma_eq),
               sigma=float(sigma_eq * np.sqrt(2.0 * theta)))
    return out


def s_score(x_last, mu, mu_star: float, sigma_eq, mu_mode: str = "centred", cap: float = WINSOR):
    """s = -(X_T' - m) / sigma_eq, winsorised at +-cap (Eq. A8, p. 22; p. 23). m = mu - mu* ("centred", our
    choice), mu ("own") or mu* ("pooled", the p. 22 text). Positive s: the residual is below its equilibrium."""
    centre = {"centred": np.asarray(mu, float) - mu_star, "own": np.asarray(mu, float),
              "pooled": np.full_like(np.asarray(mu, float), mu_star)}[mu_mode]
    return np.clip(-(np.asarray(x_last, float) - centre) / np.asarray(sigma_eq, float), -cap, cap)


def variance_ratio(r: np.ndarray, k: int = VR_K) -> float:
    """VR = Var(k-period sums) / (k Var(r)) on overlapping sums (Family 3, section 3.4). VR < 1: mean reverting."""
    r = np.asarray(r, dtype=float)
    if len(r) <= k or np.var(r, ddof=1) <= 0:
        return np.nan
    sums = np.convolve(r, np.ones(k), mode="valid")
    return float(np.var(sums, ddof=1) / (k * np.var(r, ddof=1)))


def hysteresis(prev: pd.Series, pct: pd.Series, entry: float = ENTRY_Q, exit_: float = EXIT_Q) -> pd.Series:
    """Side +1, 0 or -1 per bond: open long in the top `entry` share of pct, keep a long down to the top `exit_`
    share. Short is symmetric (p. 3). `prev` holds the old sides on the index of `pct`. NaN pct gives 0."""
    prev = prev.reindex(pct.index).fillna(0)
    long_ = (pct >= 1.0 - entry) | ((prev == 1) & (pct >= 1.0 - exit_))
    short = (pct <= entry) | ((prev == -1) & (pct <= exit_))
    return pd.Series(np.where(long_, 1, np.where(short, -1, 0)), index=pct.index)


def signal_weights(score: pd.Series) -> pd.Series:
    """Signal-weighted positions s / sum |s| (p. 23). NaN gives 0. Leverage 1."""
    s = score.fillna(0.0)
    tot = s.abs().sum()
    return s / tot if tot > 0 else s


def daily_spread_returns(daily: pd.DataFrame, dur: pd.Series,
                         max_ffill: int = MAX_FFILL_DAYS) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Daily excess returns r_d = s_d-1 dt - D (s_d - s_d-1) on the grid of trade days in `daily` (spec section 3).

    `daily` has cusip, date, g_spread (decimal). `dur` is mod_dur by cusip. A day without a trade carries the last
    spread for at most `max_ffill` days, so its return is the carry only and the next trade takes the move. dt is
    calendar days / 365.25. Returns (returns, traded), both dates x cusip. Intuition: carry minus the price effect
    of the spread change, the excess return over the duration-matched Treasury."""
    wide = daily.pivot(index="date", columns="cusip", values="g_spread").sort_index()
    traded = wide.notna()
    filled = wide.ffill(limit=max_ffill)
    prev = filled.shift(1)
    dt = pd.Series(wide.index, index=wide.index).diff().dt.days / 365.25
    r = prev.mul(dt, axis=0) - (filled - prev).mul(dur.reindex(wide.columns).astype(float), axis=1)
    return r, traded


# ---------------------------------------------------------------- panel steps


def _known(panels: Mapping[str, pd.DataFrame], name: str, dt: pd.Timestamp) -> pd.DataFrame | None:
    df = panels.get(name)
    if df is None or len(df) == 0:
        return None
    return df[df["available_at"] <= dt]


def monthly_returns(p: pd.DataFrame, last: pd.Timestamp, periods: int, dt: pd.Timestamp) -> pd.DataFrame:
    """Monthly excess returns (months x cusip) over the `periods` months to `last` (spec build step 2). Gaps of up
    to MAX_GAP months spread R / k over their months (F04 rule). A longer gap stays NaN."""
    months = pd.date_range(end=last, periods=periods, freq="ME")
    hist = p[(p["date"] >= months[0] - pd.offsets.MonthEnd(2 * MAX_GAP)) & (p["date"] <= last)]
    pairs = monthly_excess_returns(hist, dt, MAX_GAP)
    if pairs.empty:
        return pd.DataFrame(index=months)
    m = spread_months(pairs, "r_ex")
    return m.groupby(["month", "cusip"])["value"].sum().unstack().reindex(months)


def reversion_table(R: pd.DataFrame, traded: pd.DataFrame, ou_window: int, annual: float, n_pcs: int = N_PCS,
                    var_frac: float | None = None, min_trade_frac: float = 0.0,
                    mu_mode: str = "centred") -> tuple[pd.DataFrame, dict]:
    """s-score per column of R (spec build steps 4 to 7). R is periods x key, the last row the latest period.

    A column enters the PCA with MIN_PCA_FRAC of the periods present and a positive sd. It gets a fit when its
    last `ou_window` returns are all present and `min_trade_frac` of those periods traded. Status per column:
    "ok", "no_reversion" (b outside (0, 1)), "slow" (half-life above MAX_HL_FRAC x ou_window) or "no_history".
    Returns the table (FIT_COLS plus score) and {n_pcs, var_explained, mu_star}."""
    tab = pd.DataFrame(index=R.columns, columns=FIT_COLS, dtype=float)
    tab["status"] = "no_history"
    tab["n_obs"] = R.notna().sum(axis=0)
    info = {"n_pcs": np.nan, "var_explained": np.nan, "mu_star": np.nan}
    sd = R.std(axis=0, ddof=1)
    pca_cols = R.columns[(tab["n_obs"] >= np.ceil(MIN_PCA_FRAC * len(R))) & (sd > 0)]
    if len(pca_cols) <= n_pcs or len(R) < ou_window or ou_window <= n_pcs + 4:
        tab["score"] = np.nan
        return tab, info
    F, n, share = pca_factors(R[pca_cols].to_numpy(), n_pcs, var_frac)
    info.update(n_pcs=n, var_explained=share)
    tail, tr = R[pca_cols].iloc[-ou_window:], traded[pca_cols].iloc[-ou_window:]
    fit_cols = pca_cols[tail.notna().all(axis=0) & (tr.sum(axis=0) >= min_trade_frac * ou_window)]
    if len(fit_cols) and ou_window > n + 3:
        resid = pc_residuals(tail[fit_cols].to_numpy(), F[-ou_window:])
        for j, c in enumerate(fit_cols):
            f = ou_fit(resid[:, j], annual)
            tab.loc[c, ["x_last", "mu", "b", "theta", "sigma_eq"]] = [f["x_last"], f["mu"], f["b"], f["theta"],
                                                                     f["sigma_eq"]]
            tab.loc[c, "status"] = f["status"]
            tab.loc[c, "vr"] = variance_ratio(resid[:, j])
    tab["half_life"] = half_life(tab["b"].to_numpy(float))
    tab.loc[tab["status"].isin(["no_reversion", "no_history"]), "half_life"] = np.nan
    tab.loc[(tab["status"] == "ok") & (tab["half_life"] > MAX_HL_FRAC * ou_window), "status"] = "slow"
    ok = tab["status"] == "ok"
    info["mu_star"] = float(tab.loc[ok, "mu"].mean()) if ok.any() else np.nan
    s = s_score(tab["x_last"], tab["mu"], info["mu_star"], tab["sigma_eq"], mu_mode)
    tab["score"] = np.where(ok, s, np.nan)
    return tab, info


def compute(panels: Mapping[str, pd.DataFrame], as_of: pd.Timestamp, freq: str = "monthly", level: str = "bond",
            n_pcs: int = N_PCS, var_frac: float | None = None, pca_window: int | None = None,
            ou_window: int | None = None, skip: int | None = None, mu_mode: str = "centred") -> pd.DataFrame:
    """F15 s-score per eligible bond at month end `as_of` (spec build steps 1 to 8; methodology Sections 8, 7.5).

    freq "monthly" uses bond_panel (windows in months, `skip` in months). freq "daily" uses bond_daily (windows in
    trade days, `skip` in calendar days). level "issuer" averages each gvkey's bond returns and copies the issuer
    score to its bonds. One row per cusip with the COLS columns. NaN score where a step drops the bond. Empty frame
    without bond_panel, or without bond_daily for freq "daily". Higher score = long."""
    as_of = pd.Timestamp(as_of) + pd.offsets.MonthEnd(0)
    dt = decision_time(as_of)
    p = _known(panels, "bond_panel", dt)
    if p is None:
        return pd.DataFrame(columns=COLS)
    p = p.assign(date=pd.to_datetime(p["date"]))
    now = p[p["date"] == as_of].drop_duplicates("cusip", keep="last")
    now = now[eligible(now) & not_distressed(now) & now["gvkey"].notna()]
    if now.empty:
        return pd.DataFrame(columns=COLS)

    if freq == "daily":
        d = _known(panels, "bond_daily", dt)
        if d is None:
            return pd.DataFrame(columns=COLS)
        T, Tp, sk = pca_window or PCA_DAYS, ou_window or OU_DAYS, SKIP_DAYS if skip is None else skip
        d = d.assign(date=pd.to_datetime(d["date"]))
        d = d[d["cusip"].isin(now["cusip"]) & (d["date"] <= as_of - pd.Timedelta(sk, unit="D"))]
        d = d.sort_values("available_at").drop_duplicates(["cusip", "date"], keep="last")
        if d.empty:
            return pd.DataFrame(columns=COLS)
        R, traded = daily_spread_returns(d, now.set_index("cusip")["mod_dur"])
        R, traded, trade_frac = R.iloc[-T:], traded.iloc[-T:], MIN_TRADE_FRAC
    else:
        T, Tp, sk = pca_window or PCA_MONTHS, ou_window or OU_MONTHS, SKIP_MONTHS if skip is None else skip
        last = as_of - pd.offsets.MonthEnd(sk) if sk else as_of
        hist = p[p["cusip"].isin(now["cusip"])]
        R = monthly_returns(hist, last, T, dt).reindex(columns=now["cusip"])
        traded, trade_frac = R.notna(), 0.0

    gmap = now.set_index("cusip")["gvkey"]
    if level == "issuer":
        R = R.T.groupby(gmap.reindex(R.columns)).mean().T
        traded = traded.T.groupby(gmap.reindex(traded.columns)).max().T.astype(bool)
    tab, info = reversion_table(R, traded, Tp, ANNUAL[freq], n_pcs, var_frac, trade_frac, mu_mode)

    out = now[["cusip", "gvkey"]].copy()
    key = out["gvkey"] if level == "issuer" else out["cusip"]
    out = pd.concat([out.reset_index(drop=True), tab.reindex(key.to_numpy()).reset_index(drop=True)], axis=1)
    out["status"] = out["status"].fillna("no_history")
    out["mu_star"], out["n_pcs"], out["var_explained"] = info["mu_star"], info["n_pcs"], info["var_explained"]
    out["pct"] = out["score"].rank(pct=True)
    out["entry_signal"] = hysteresis(pd.Series(0, index=out.index), out["pct"]).to_numpy()
    out["date"], out["available_at"], out["freq"] = as_of, dt, freq
    num = [c for c in COLS if c not in ("date", "cusip", "available_at", "gvkey", "status", "freq", "entry_signal")]
    return out[COLS].astype({c: float for c in num}).reset_index(drop=True)
