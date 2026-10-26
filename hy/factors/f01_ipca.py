"""F01 IPCA conditional factor model (rank 1, signal S8). Spec docs/factors/F01-ipca.md; methodology Section 8
(new subsection "S8. Conditional factor expected return") and Section 11 (backtest design). Source: Kelly,
Palhares, Pruitt (2021), "Modeling Corporate Bond Returns" (KPP), SSRN 3720789. Pages are PDF pages.

    r_i,t+1   = beta_i,t' f_t+1 + eps_i,t+1,   beta_i,t = z_i,t' Gamma               restricted IPCA, Gamma_alpha = 0 (p. 8)
    r_i,t+1   = r~_i,t+1 / max(DtS_i,t, 0.25),  DtS = mod_dur x g_spread                 DtS-scaled excess return (eq. 10, p. 14)
    f_t+1     = (Gamma' Z_t'Z_t Gamma)^-1 Gamma' Z_t' r_t+1                              factor step (eq. 2, p. 8)
    vec(Gamma') = (sum_t Z_t'Z_t (x) f f')^-1 sum_t (Z_t (x) f')' r_t+1                  Gamma step (eq. 3, p. 8)
    E_t[r_i,t+1] = z_i,t' Gamma_t lambda_t,  lambda_t = mean of the fitted factors to t  forecast (footnote 12, p. 13)

Intuition: the characteristics tell which bonds load on the priced latent factors, and the loadings update each
month with the characteristics.

Estimation. Alternating least squares (ALS) from the SVD of the managed portfolios x_t = Z_t' r_t+1 / N_t (eq. 4,
p. 8). After each step: Gamma'Gamma = I, the factor second moment diagonal and descending, the factor means
non-negative (p. 9). The fit uses an expanding window: every pair (z_s, r_s+1) with s + 1 <= t whose return the
panel holds by decision_time(t). No forecast exists before MIN_TRAIN_MONTHS months of pairs (pp. 21-22).

lambda. We implement the spec's choice (F01 section 3, "Our choice"): lambda_t is the mean of the in-sample
factors of the fit at t. Factors of earlier fits sit in other rotations, so a mean across fits has no meaning.

Characteristics. Only the "have" rows of spec section 4 that the production panels of docs/production_wiring.md
section 5 can build. Each month the code ranks each characteristic over the screened bonds and scales the rank to
[-0.5, 0.5] (p. 15). A missing value takes 0, the cross-section median, so it drops out of beta. A constant 1
closes z. A bond with every characteristic missing gets NaN. Panels: `bond_panel` is required (without it the
result is empty). `leverage`, `gics`, `ratings` and `equity_monthly` are optional: without one, its
characteristics are 0 for every bond and the fit drops them. Spec rows that need `market_value`, `financials` or
`treasury_curve` (items 9, 19, 23, 26) and the "need" rows are not built.

Spreads, yields and returns are decimals. DtS is mod_dur x g_spread in decimal spread (spec section 5 step 2).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view

from hy.backtest import MIN_BONDS, decision_time, eligible, realised_excess_return
from hy.peers import RATING_STALE_DAYS, equity_momentum, sector_at
from hy.signals import standardise

K_FACTORS = 5               # latent factors (p. 21; zero alpha not rejected at 1% for K = 5, Table A.II p. 56)
DTS_FLOOR = 0.25            # DtS floor of the scaled return (eq. 10, p. 14)
SPREAD_MIN, SPREAD_MAX = 0.005, 0.20   # 50 to 2000 bp at the start of the month (p. 15)
DUR_MIN = 0.25              # duration at least 0.25 years (p. 15)
MIN_TRAIN_MONTHS = 36       # months of pairs before the first forecast (pp. 21-22)
ALS_TOL = 1e-6              # largest change in Gamma that stops ALS (spec section 3, our choice)
ALS_MAX_ITER = 500          # ALS iteration cap (spec section 3, our choice)
MOM_MONTHS = 5              # 6-2 momentum: compound months t-5 .. t-1, skip t (spec open question 4, our choice)
MOM_MIN = 3                 # bond returns the 6-2 window needs (our choice: HY trades are sparse)
VOL_MONTHS, VOL_MIN = 24, 12        # bond and equity volatility window and minimum (spec section 7, our choice)
SKEW_MONTHS, SKEW_MIN = 60, 24      # bond skewness window (Table A.I, p. 55) and minimum (our choice)
VAR_MONTHS, VAR_MIN = 36, 24        # value-at-risk: 2nd lowest return over 36 months, at least 24 (Table A.I, p. 55)
SPREAD_MOM_MONTHS = 6       # momentum of log spread over 6 months (Table A.I, p. 55)
PAR = 100.0                 # price of par for the call distortion instrument (spec section 4, fix 2)

# Instruments z (spec section 4 item numbers). price_premium is instrument 31 (spec section 4, fix 2).
CHARS = (
    "coupon",          # 2   bond_panel.coupon
    "debt_to_ebitda",  # 5   leverage.leverage
    "duration",        # 6   bond_panel.mod_dur
    "mom_equity",      # 7   equity_monthly.ret, 6-2
    "equity_vol",      # 10  equity_monthly.ret, 24 months
    "firm_debt",       # 11  leverage.debt
    "mom_bond",        # 12  T1, 6-2
    "mom_industry",    # 13  item 12 minus its gics.gsector mean
    "mom_rating",      # 14  item 12 x item 22
    "spread",          # 18  bond_panel.g_spread
    "rating",          # 22  ratings.splticrm, 1 (AAA) to 22 (D)
    "bond_skew",       # 24  T1, 60 months
    "mom_log_spread",  # 25  log g_spread(t-6) - log g_spread(t)
    "bond_vol",        # 27  T1, 24 months
    "var",             # 28  2nd lowest T1, 36 months
    "price_premium",   # 31  max(price - 100, 0) / 100
)
CONST = "const"
INSTRUMENTS = CHARS + (CONST,)
EQUITY_CHARS = ("mom_equity", "equity_vol")
RATING_SCALE = ("AAA", "AA+", "AA", "AA-", "A+", "A", "A-", "BBB+", "BBB", "BBB-", "BB+", "BB", "BB-",
                "B+", "B", "B-", "CCC+", "CCC", "CCC-", "CC", "C", "D")   # 1 to 22 (Table A.I, p. 55)

META = {
    "rank": 1,
    "name": "IPCA conditional factor model",
    "level": "bond",
    "horizon_months": 1,
    "needs": ["bond_panel", "leverage", "gics", "ratings", "equity_monthly"],
    "spec": "docs/factors/F01-ipca.md",
    "section": "8",
}

BASE_COLS = ["date", "cusip", "score", "available_at", "gvkey", "ipca_er", "ipca_er_ret", "s8_ipca",
             "n_chars", "flag_equity", "flag_rating"]


@dataclass
class IPCAFit:
    """Result of `fit_ipca`. gamma is L x K, factors T x K (one row per training month), lam the factor means,
    impact the row norms of gamma (Table IX, p. 31)."""
    gamma: np.ndarray
    factors: np.ndarray
    lam: np.ndarray
    n_iter: int
    converged: bool
    impact: np.ndarray


# ---------------------------------------------------------------- formula helpers


def rating_number(symbol: str | None) -> float:
    """S&P letter to 1 (AAA) to 22 (D); SD maps to 22; anything else NaN (spec section 6; Table A.I, p. 55)."""
    if not isinstance(symbol, str) or not symbol.strip():
        return np.nan
    s = symbol.strip().upper()
    s = "D" if s == "SD" else s
    return float(RATING_SCALE.index(s) + 1) if s in RATING_SCALE else np.nan


def dts_scaled_return(r_tilde, mod_dur, g_spread, floor: float = DTS_FLOOR) -> np.ndarray:
    """r = r~ / max(DtS, floor), DtS = mod_dur x g_spread at the start month (eq. 10, p. 14).

    Intuition: divide by ex ante volatility so the most volatile bonds do not drive least squares."""
    dts = np.asarray(mod_dur, float) * np.asarray(g_spread, float)
    return np.asarray(r_tilde, float) / np.maximum(dts, floor)


def rank_scale(chars: pd.DataFrame, cols, date_col: str = "date") -> pd.DataFrame:
    """Per date, rank each column over its non-missing values and map rank 1 .. n to -0.5 .. 0.5 (p. 15).

    Ties take the average rank. One value maps to 0. A missing value maps to 0, the cross-section median.
    Intuition: ranks remove the units and the outliers, so Gamma compares like with like."""
    out = chars.copy()
    for c in cols:
        g = chars.groupby(date_col)[c]
        n = g.transform("count").astype(float)
        rk = g.rank(method="average")
        out[c] = ((rk - 1.0) / (n - 1.0).where(n > 1) - 0.5).where(n > 1, 0.0).fillna(0.0)
    return out


def factor_step(gamma: np.ndarray, zz: np.ndarray, zr: np.ndarray) -> np.ndarray:
    """f_t+1 = (Gamma' Z'Z Gamma)^-1 Gamma' Z' r_t+1 (eq. 2, p. 8): cross-section regression of returns on betas."""
    return np.linalg.lstsq(gamma.T @ zz @ gamma, gamma.T @ zr, rcond=None)[0]


def gamma_step(zz: np.ndarray, zr: np.ndarray, f: np.ndarray) -> np.ndarray:
    """vec(Gamma') = (sum_t Z'Z (x) f f')^-1 sum_t Z'r (x) f (eq. 3, p. 8). zz is T x L x L, zr T x L, f T x K.

    Intuition: a pooled regression of returns on characteristics times factors. vec(Gamma') stacks Gamma's rows."""
    L, K = zz.shape[1], f.shape[1]
    a = np.einsum("tij,tk,tl->ikjl", zz, f, f).reshape(L * K, L * K)
    b = np.einsum("ti,tk->ik", zr, f).reshape(L * K)
    return np.linalg.lstsq(a, b, rcond=None)[0].reshape(L, K)


def normalise(gamma: np.ndarray, factors: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Rotate (Gamma, F) so Gamma'Gamma = I, F'F diagonal and descending, factor means >= 0 (p. 9).

    F is T x K. Gamma F' is unchanged. Intuition: IPCA identifies Gamma only up to rotation, so fix one."""
    r = np.linalg.cholesky(gamma.T @ gamma).T                  # Gamma'Gamma = R'R, R upper
    g1, f1 = gamma @ np.linalg.inv(r), factors @ r.T
    _, p = np.linalg.eigh(f1.T @ f1)
    p = p[:, ::-1]                                             # descending second moment
    g2, f2 = g1 @ p, f1 @ p
    sign = np.where(f2.mean(axis=0) < 0, -1.0, 1.0)
    return g2 * sign, f2 * sign


def fit_ipca(Z: Mapping[pd.Timestamp, np.ndarray], R: Mapping[pd.Timestamp, np.ndarray], K: int = K_FACTORS,
             tol: float = ALS_TOL, max_iter: int = ALS_MAX_ITER) -> IPCAFit:
    """Restricted IPCA (Gamma_alpha = 0) by ALS on eqs. (2) and (3), p. 8. Z[t] is N_t x L, R[t] the N_t returns
    of month t + 1 (keys: the start months). Start: the first K left singular vectors of the L x T managed
    portfolios x_t = Z_t' r_t+1 / N_t (eq. 4, p. 8). Stop when the largest change in Gamma < tol."""
    keys = sorted(Z)
    zz = np.stack([Z[t].T @ Z[t] for t in keys])
    zr = np.stack([Z[t].T @ R[t] for t in keys])
    x = (zr / np.array([len(R[t]) for t in keys])[:, None]).T
    gamma = np.linalg.svd(x, full_matrices=False)[0][:, :K]
    n_iter, converged = 0, False
    for n_iter in range(1, max_iter + 1):
        f = np.stack([factor_step(gamma, zz[i], zr[i]) for i in range(len(keys))])
        new, _ = normalise(gamma_step(zz, zr, f), f)
        change = float(np.max(np.abs(new - gamma)))
        gamma = new
        if change < tol:
            converged = True
            break
    f = np.stack([factor_step(gamma, zz[i], zr[i]) for i in range(len(keys))])
    gamma, f = normalise(gamma, f)
    return IPCAFit(gamma, f, f.mean(axis=0), n_iter, converged, np.linalg.norm(gamma, axis=1))


def expected_return(z: np.ndarray, gamma: np.ndarray, lam: np.ndarray, has_char: np.ndarray) -> np.ndarray:
    """E_t[r_i,t+1] = z_i,t' Gamma lambda (KPP eq. 1 with Gamma_alpha = 0; footnote 12, p. 13). NaN where the bond
    has no characteristic. Intuition: a bond's expected return is its beta times the factor risk premia."""
    er = np.asarray(z, float) @ gamma @ lam
    return np.where(has_char, er, np.nan)


# ---------------------------------------------------------------- characteristics


def _second_lowest(window: np.ndarray, min_obs: int) -> np.ndarray:
    """2nd lowest non-missing value along the last axis; NaN with fewer than `min_obs` values (Table A.I item 28)."""
    s = np.sort(window, axis=-1)                               # NaN sorts last
    n = np.isfinite(window).sum(axis=-1)
    return np.where(n >= min_obs, s[..., 1], np.nan)


def bond_return_history(panel: pd.DataFrame, dt: pd.Timestamp) -> pd.DataFrame:
    """T1 per bond and start month: r~ = total - tsy_ret over one month (`realised_excess_return`; KPP p. 14)."""
    rr = realised_excess_return(panel, 1, dt)
    rr["r_tilde"] = rr["total"] - rr["tsy_ret"]
    return rr.loc[rr["r_tilde"].notna(), ["cusip", "date", "r_tilde"]]


def bond_return_features(rr: pd.DataFrame, months: pd.DatetimeIndex) -> pd.DataFrame:
    """Items 12, 24, 27 and 28 per (date, cusip) from the T1 returns that end at or before each month end.

    mom_bond at s compounds the returns that end in s-5 .. s-1. Intuition: the bond's own return history."""
    w = rr.assign(m=rr["date"] + pd.offsets.MonthEnd(1)).pivot(index="m", columns="cusip", values="r_tilde")
    w = w.reindex(months)
    mom = np.expm1(np.log1p(w).shift(1).rolling(MOM_MONTHS, min_periods=MOM_MIN).sum())
    vol = w.rolling(VOL_MONTHS, min_periods=VOL_MIN).std()
    skew = w.rolling(SKEW_MONTHS, min_periods=SKEW_MIN).skew()
    arr = np.vstack([np.full((VAR_MONTHS - 1, w.shape[1]), np.nan), w.to_numpy(float)])
    var = pd.DataFrame(_second_lowest(sliding_window_view(arr, VAR_MONTHS, axis=0), VAR_MIN), index=w.index,
                       columns=w.columns)
    out = pd.concat({"mom_bond": mom, "bond_vol": vol, "bond_skew": skew, "var": var}, axis=1)
    out = out.stack(level="cusip", future_stack=True).dropna(how="all")
    out.index.names = ["date", "cusip"]
    return out.reset_index()


def _issuer_month_features(panels: Mapping[str, pd.DataFrame], months: pd.DatetimeIndex) -> pd.DataFrame:
    """Items 7, 10 and 22 per (date, gvkey), each from rows with available_at <= decision_time(date)."""
    eq, rt = panels.get("equity_monthly"), panels.get("ratings")
    rows = []
    for s in months:
        dt = decision_time(s)
        parts = []
        if eq is not None and len(eq):
            parts.append(equity_momentum(eq, s - pd.offsets.MonthEnd(1), dt, months=MOM_MONTHS).rename("mom_equity"))
            ends = pd.date_range(end=s, periods=VOL_MONTHS, freq="ME")
            g = eq[eq["datadate"].isin(ends) & (eq["available_at"] <= dt)].groupby("gvkey")["ret"]
            parts.append(g.std().where(g.count() >= VOL_MIN).rename("equity_vol"))
        if rt is not None and len(rt):
            r = rt[(rt["available_at"] <= dt) & (rt["datadate"] >= dt - pd.Timedelta(RATING_STALE_DAYS, unit="D"))]
            r = r.sort_values("datadate").drop_duplicates("gvkey", keep="last").set_index("gvkey")
            parts.append(r["splticrm"].map(rating_number).rename("rating"))
        if parts:
            rows.append(pd.concat(parts, axis=1).assign(date=s))
    cols = ["date", "gvkey", "mom_equity", "equity_vol", "rating"]
    if not rows:
        return pd.DataFrame(columns=cols)
    out = pd.concat(rows).rename_axis("gvkey").reset_index()
    return out.reindex(columns=cols)


def screen(panel: pd.DataFrame) -> pd.Series:
    """Rows the model fits and scores: `eligible`, spread 50 to 2000 bp, duration >= 0.25 years (p. 15)."""
    return (eligible(panel) & panel["g_spread"].between(SPREAD_MIN, SPREAD_MAX)
            & (panel["mod_dur"].astype(float) >= DUR_MIN))


def characteristics(panels: Mapping[str, pd.DataFrame], as_of: pd.Timestamp) -> pd.DataFrame:
    """Raw characteristics (CHARS) of every screened bond at every month end to as_of (spec section 4, build step 3).

    Panels must be filtered to available_at <= decision_time(as_of). Each month reads only what its own decision
    time allows. Adds flag_equity and flag_rating (1 when the group is missing) and n_chars."""
    as_of = pd.Timestamp(as_of)
    panel = panels["bond_panel"]
    months = pd.date_range(panel["date"].min(), as_of, freq="ME")
    base = panel[screen(panel)]
    out = base[["date", "cusip", "gvkey", "coupon", "mod_dur", "g_spread", "price"]].copy()
    out["duration"], out["spread"] = out["mod_dur"], out["g_spread"]     # raw copies stay for DtS
    out["price_premium"] = np.maximum(out["price"] - PAR, 0.0) / PAR
    spread_w = panel[~panel["carried"].astype(bool)].pivot(index="date", columns="cusip", values="g_spread")
    smom = (np.log(spread_w.reindex(months).shift(SPREAD_MOM_MONTHS)) - np.log(spread_w.reindex(months)))
    smom = smom.stack(future_stack=True).dropna().rename("mom_log_spread")
    smom.index.names = ["date", "cusip"]
    out = out.merge(smom.reset_index(), on=["date", "cusip"], how="left")
    feats = bond_return_features(bond_return_history(panel, decision_time(as_of)), months)
    out = out.merge(feats, on=["date", "cusip"], how="left")
    lev = panels.get("leverage")
    if lev is not None and len(lev):
        lev = lev[lev["available_at"] <= lev["date"] + pd.Timedelta(1, unit="D")]
        lev = lev.sort_values("available_at").drop_duplicates(["date", "gvkey"], keep="last")
        lev = lev[["date", "gvkey", "leverage", "debt"]].rename(columns={"leverage": "debt_to_ebitda",
                                                                       "debt": "firm_debt"})
        out = out.merge(lev, on=["date", "gvkey"], how="left")
    out = out.merge(_issuer_month_features(panels, months), on=["date", "gvkey"], how="left")
    gics = panels.get("gics")
    if gics is not None and len(gics):
        sec = {s: sector_at(gics[gics["available_at"] <= decision_time(s)], s) for s in months}
        out["sector"] = [sec[d].get(g, np.nan) for d, g in zip(out["date"], out["gvkey"])]
        out["mom_industry"] = out["mom_bond"] - out.groupby(["date", "sector"])["mom_bond"].transform("mean")
    out = out.reindex(columns=[*out.columns, *[c for c in CHARS if c not in out.columns]])
    out["mom_rating"] = out["mom_bond"] * out["rating"]
    out[list(CHARS)] = out[list(CHARS)].astype(float)
    out["n_chars"] = out[list(CHARS)].notna().sum(axis=1)
    out["flag_equity"] = out[list(EQUITY_CHARS)].isna().all(axis=1).astype(int)
    out["flag_rating"] = out["rating"].isna().astype(int)
    return out.reset_index(drop=True)


# ---------------------------------------------------------------- compute


def _empty(k: int = 0) -> pd.DataFrame:
    return pd.DataFrame(columns=BASE_COLS + [f"ipca_beta_{j + 1}" for j in range(k)])


def _filter(panels: Mapping[str, pd.DataFrame], as_of: pd.Timestamp, dt: pd.Timestamp) -> dict[str, pd.DataFrame]:
    """Every panel cut to available_at <= dt; bond_panel and leverage also to date <= as_of."""
    out = {}
    for name in META["needs"]:
        df = panels.get(name)
        if df is None:
            continue
        df = df[pd.to_datetime(df["available_at"]) <= dt]
        if "date" in df and name in ("bond_panel", "leverage"):
            df = df[df["date"] <= as_of]
        out[name] = df
    return out


def compute(panels: Mapping[str, pd.DataFrame], as_of: pd.Timestamp, **params) -> pd.DataFrame:
    """s8_ipca per screened bond at as_of (spec section 5, build steps 1 to 8).

    params: K (default K_FACTORS), tol, max_iter, gamma (a pre-fitted L x K frame indexed by instrument name: the
    fit is skipped and lambda is the mean of the factor steps on the training months), lam (with gamma: skip
    those too). The result attrs hold gamma (frame), lam, n_iter, converged and n_train_months for reuse."""
    as_of = pd.Timestamp(as_of) + pd.offsets.MonthEnd(0)
    dt = decision_time(as_of)
    K = int(params.get("K", K_FACTORS))
    p = _filter(panels, as_of, dt)
    if "bond_panel" not in p or p["bond_panel"].empty or (p["bond_panel"]["date"] == as_of).sum() == 0:
        return _empty(K)
    chars = characteristics(p, as_of)
    z = rank_scale(chars, CHARS)
    z[CONST] = 1.0
    rr = bond_return_history(p["bond_panel"], dt)
    pairs = z.merge(rr, on=["date", "cusip"], how="inner")
    pairs["r"] = dts_scaled_return(pairs["r_tilde"], pairs["mod_dur"], pairs["g_spread"])
    pairs = pairs[(pairs["n_chars"] > 0) & (pairs["date"] < as_of) & np.isfinite(pairs["r"])]
    sizes = pairs.groupby("date").size()
    train = sorted(sizes.index[sizes >= MIN_BONDS])
    if len(train) < MIN_TRAIN_MONTHS:
        return _empty(K)
    pairs = pairs[pairs["date"].isin(train)]
    gamma_in = params.get("gamma")
    if gamma_in is not None:
        g = pd.DataFrame(gamma_in).reindex(list(INSTRUMENTS)).fillna(0.0)
        active, K = list(INSTRUMENTS), g.shape[1]
        gamma = g.to_numpy(float)
    else:
        active = [c for c in INSTRUMENTS if c == CONST or (pairs[c] != 0).any()]
        K = min(K, len(active))
    Zd = {d: grp[active].to_numpy(float) for d, grp in pairs.groupby("date")}
    Rd = {d: grp["r"].to_numpy(float) for d, grp in pairs.groupby("date")}
    if gamma_in is None:
        fit = fit_ipca(Zd, Rd, K, float(params.get("tol", ALS_TOL)), int(params.get("max_iter", ALS_MAX_ITER)))
        gamma, lam, n_iter, conv = fit.gamma, fit.lam, fit.n_iter, fit.converged
    else:
        lam = params.get("lam")
        if lam is None:
            lam = np.mean([factor_step(gamma, Zd[d].T @ Zd[d], Zd[d].T @ Rd[d]) for d in train], axis=0)
        lam, n_iter, conv = np.asarray(lam, float), 0, True
    now = z[z["date"] == as_of]
    zt = now[active].to_numpy(float)
    has = now["n_chars"].to_numpy() > 0
    er = expected_return(zt, gamma, lam, has)
    betas = np.where(has[:, None], zt @ gamma, np.nan)
    dts = np.maximum(now["mod_dur"].to_numpy(float) * now["g_spread"].to_numpy(float), DTS_FLOOR)
    out = pd.DataFrame({"date": as_of, "cusip": now["cusip"].to_numpy(), "available_at": dt,
                        "gvkey": now["gvkey"].to_numpy(), "ipca_er": er, "ipca_er_ret": er * dts})
    ok = np.isfinite(er)
    s8 = np.full(len(er), np.nan)
    s8[ok] = standardise(er[ok])
    out["s8_ipca"] = s8
    out["score"] = s8
    for c in ("n_chars", "flag_equity", "flag_rating"):
        out[c] = now[c].to_numpy()
    for j in range(K):
        out[f"ipca_beta_{j + 1}"] = betas[:, j]
    out = out[BASE_COLS + [f"ipca_beta_{j + 1}" for j in range(K)]].reset_index(drop=True)
    out.attrs.update({"gamma": pd.DataFrame(gamma, index=active, columns=[f"f{j + 1}" for j in range(K)]),
                      "lam": lam, "n_iter": n_iter, "converged": conv, "n_train_months": len(train)})
    return out
