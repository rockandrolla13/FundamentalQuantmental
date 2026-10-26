"""F20 Tail dependence of spread changes with the market (rank 20). Spec docs/factors/F20-tail-dependence.md;
methodology Section 8 (a control of the S1 residual) and Section 9.3 (position risk measures). Source: Pelster and
Vilsmeier (2018), Rev Deriv Res 21: 63-118, "The determinants of CDS spreads_ evidence from.pdf". Pages are PDF
pages: UTD definition Table 3 (p. 13), Table 1 (p. 8), estimation Appendix A (pp. 40-44).

    x_j,t   = mean over bonds b of j of  log s_b,t - log s_b,t-1          issuer log G-spread change, consecutive periods
    m_-j,t  = mean over issuers k != j of x_k,t                            market change, issuer left out (our choice)
    z       = EWMA-standardised AR(1) residual of x and of m               filter (source: AR-GARCH by AIC, p. 41)
    u       = rank(z) / (n + 1)                                            empirical CDF (p. 41)
    rho     = sin(pi tau_K / 2),  nu = argmax sum log c_t(u1, u2; rho, nu)  static t-copula on the window (our choice)
    UTD     = 2 t_{nu+1}( -sqrt((nu + 1)(1 - rho) / (1 + rho)) )           upper tail dependence of the t-copula
    score   = standardised rank of -(UTD - X b),  X = [1, rating dummies, log s_j]

Intuition: an issuer that widens with the market in the market's worst periods carries crash risk. The source finds
that a high lagged UTD comes before a larger spread widening (Table 1, p. 8: t-copula coefficient 0.848). A wider
spread is a lower bond return, so the score is short high UTD. The control keeps the part of UTD that the rating
class and the spread level do not pay for.

Inputs. `bond_panel` is required. A new optional panel `bond_daily` (the F02 panel: `cusip`, `date` trade day,
`g_spread` par-weighted day mean, `available_at` trade day + 1 day) gives weekly changes (freq "W", 104 weeks, at
least 52) or daily changes (freq "D", 504 trade days, at least 250). Without it the module uses month-end
`bond_panel` G-spreads (freq "M", 60 months, at least 48). The column `freq` flags the source. `ratings` and
`leverage` are optional: with `ratings`, the universe is HY (BB, B, CCC, not D or SD) and the control adds rating
dummies (column `ctrl`). Without `bond_panel` the result is empty (columns COLS). Without `bond_daily` and with
freq "W" or "D", the result is empty.

Level. Issuer (`gvkey`). The source estimates one UTD per CDS name (p. 13).
"""

from __future__ import annotations

from typing import Mapping

import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar
from scipy.special import gammaln, stdtr, stdtrit
from scipy.stats import kendalltau, rankdata
from scipy.stats import t as student_t

from hy.backtest import MIN_BONDS, decision_time, eligible
from hy.factors.f04_bond_momentum import DEFAULT_SYMBOLS, HY_CLASSES, mark_stale, rating_classes
from hy.signals import neutralise, standardise_by_date

WINDOW = {"D": 504, "W": 104, "M": 60}   # periods in the window (our choice; the source fits each full sample, p. 43)
MIN_OBS = {"D": 250, "W": 52, "M": 48}   # fewest joint changes: 1 year for D and W (after p. 5), 4 years for M (ours)
EWMA_LAMBDA = 0.94         # EWMA variance decay (our choice, the RiskMetrics convention; the source uses GARCH, p. 41)
NU_BOUNDS = (2.0, 100.0)   # search range of nu (our choice; source estimates "never larger than 21", p. 39)
RHO_CAP = 0.995            # |rho| cap that keeps 1 - rho^2 away from zero (our choice)
PHI_CAP = 0.99             # |phi| cap of the AR(1) filter (our choice)
MIN_MKT = 10               # fewest other issuers for a market change (our choice)
MIN_XS = MIN_BONDS         # fewest scored issuers for the control regression (hy.backtest, our choice)
HOLD = 3                   # one-quarter horizon: the source regresses quarterly changes on lagged UTD (p. 8)
PERIOD = {"W": "W-FRI", "M": "M"}        # weekly periods end on Friday (our choice)

META = {
    "rank": 20,
    "name": "Tail dependence of spread changes with the market",
    "level": "issuer",
    "horizon_months": HOLD,
    "needs": ["bond_panel", "bond_daily", "ratings", "leverage"],
    "spec": "docs/factors/F20-tail-dependence.md",
    "section": "8",
}
REQUIRED = ("bond_panel",)

COLS = ["date", "gvkey", "score", "available_at", "utd", "utd_emp", "utd_ctrl", "rho", "nu", "n_obs", "freq", "ctrl",
        "rclass", "g_spread"]


# ---------------------------------------------------------------- formula helpers


def period_ordinal(dates: pd.Series, freq: str, calendar: np.ndarray | None = None) -> np.ndarray:
    """Integer period per date: week ("W") or month ("M") ordinals, or the position in `calendar` ("D") (spec
    build step 3). Two periods are consecutive when their ordinals differ by 1."""
    d = pd.DatetimeIndex(pd.to_datetime(dates))
    if freq == "D":
        return np.searchsorted(np.asarray(calendar, dtype="datetime64[ns]"), d.to_numpy())
    return pd.PeriodIndex(d, freq=PERIOD[freq]).asi8


def log_changes(rows: pd.DataFrame, freq: str, calendar: np.ndarray | None = None) -> pd.DataFrame:
    """Log G-spread change per bond over consecutive periods (spec build step 3). The last positive g_spread of each
    period counts. A gap of more than one period gives no change (our choice). Columns cusip, gvkey, per, dls."""
    r = rows[rows["g_spread"].astype(float) > 0].copy()
    if r.empty:
        return pd.DataFrame(columns=["cusip", "gvkey", "per", "dls"])
    r["per"] = period_ordinal(r["date"], freq, calendar)
    r = r.sort_values(["cusip", "date"]).drop_duplicates(["cusip", "per"], keep="last")
    r["ls"] = np.log(r["g_spread"].astype(float))
    g = r.groupby("cusip")
    r["dls"], r["dper"] = g["ls"].diff(), g["per"].diff()
    return r.loc[r["dper"] == 1, ["cusip", "gvkey", "per", "dls"]].reset_index(drop=True)


def issuer_changes(ch: pd.DataFrame) -> pd.DataFrame:
    """x_j,t = mean of the bond changes of issuer j in period t (spec build step 4). Periods x gvkey."""
    return ch.pivot_table(index="per", columns="gvkey", values="dls", aggfunc="mean").sort_index()


def market_changes(X: pd.DataFrame, min_n: int = MIN_MKT) -> pd.DataFrame:
    """m_-j,t = mean of x_k,t over the other issuers k with a change in t (spec build step 4). NaN where fewer than
    `min_n` other issuers change. Intuition: leaving j out stops j's own move from building its dependence."""
    has = X.notna().to_numpy()
    n_other = has.sum(axis=1, keepdims=True) - has
    total = np.nansum(X.to_numpy(float), axis=1, keepdims=True)
    with np.errstate(invalid="ignore", divide="ignore"):
        m = (total - np.nan_to_num(X.to_numpy(float))) / n_other
    m[n_other < min_n] = np.nan
    return pd.DataFrame(m, index=X.index, columns=X.columns)


def ar1_residual(x: np.ndarray) -> np.ndarray:
    """e_t = (x_t - mu) - phi (x_t-1 - mu), phi by OLS on consecutive pairs, |phi| <= PHI_CAP (spec section 3, our
    choice for the AR(m) step of p. 41). The first value after a gap keeps x_t - mu. NaN stays NaN."""
    x = np.asarray(x, float)
    xc = x - np.nanmean(x)
    prev = np.r_[np.nan, xc[:-1]]
    pair = np.isfinite(xc) & np.isfinite(prev)
    den = float(prev[pair] @ prev[pair])
    phi = float(np.clip(prev[pair] @ xc[pair] / den, -PHI_CAP, PHI_CAP)) if pair.sum() >= 3 and den > 0 else 0.0
    return np.where(pair, xc - phi * prev, xc)


def ewma_standardise(e: np.ndarray, lam: float = EWMA_LAMBDA) -> np.ndarray:
    """z_t = e_t / sigma_t, sigma_t^2 = lam sigma_t-1^2 + (1 - lam) e_t-1^2 over the observed values, seeded with the
    mean of e^2 (spec section 3, our choice for the GARCH step of p. 41). Intuition: a 10 bp move counts for more
    in a calm month than in a crisis month. NaN stays NaN."""
    e = np.asarray(e, float)
    z = np.full_like(e, np.nan)
    ok = np.isfinite(e)
    if not ok.any():
        return z
    s2 = float(np.mean(e[ok] ** 2))
    for i in np.flatnonzero(ok):
        z[i] = e[i] / np.sqrt(s2) if s2 > 0 else 0.0
        s2 = lam * s2 + (1.0 - lam) * e[i] ** 2
    return z


def pseudo_obs(z: np.ndarray) -> np.ndarray:
    """u_t = rank(z_t) / (n + 1), the empirical CDF with divisor T + 1 (Pelster and Vilsmeier, p. 41)."""
    z = np.asarray(z, float)
    return rankdata(z) / (len(z) + 1.0)


def t_copula_loglik(u1: np.ndarray, u2: np.ndarray, rho: float, nu: float) -> float:
    """Sum of log c(u1, u2; rho, nu), the bivariate t-copula density: the bivariate t density over the product of the
    two t marginals at x = t_nu^-1(u) (Pelster and Vilsmeier, p. 8)."""
    x1, x2 = stdtrit(nu, np.asarray(u1, float)), stdtrit(nu, np.asarray(u2, float))
    one = 1.0 - rho ** 2
    q = (x1 ** 2 - 2.0 * rho * x1 * x2 + x2 ** 2) / one
    l2 = (gammaln((nu + 2.0) / 2.0) - gammaln(nu / 2.0) - np.log(np.pi * nu) - 0.5 * np.log(one)
          - (nu + 2.0) / 2.0 * np.log1p(q / nu))
    return float(np.sum(l2 - student_t.logpdf(x1, nu) - student_t.logpdf(x2, nu)))


def fit_t_copula(u1: np.ndarray, u2: np.ndarray, bounds: tuple[float, float] = NU_BOUNDS) -> tuple[float, float]:
    """(rho, nu) of a static t-copula (spec section 3, our choice). rho = sin(pi tau / 2) from Kendall's tau, exact
    for every elliptical copula. nu maximises the pseudo log-likelihood on `bounds`. NaN pair when tau is NaN."""
    tau = kendalltau(u1, u2)[0]
    if not np.isfinite(tau):
        return np.nan, np.nan
    rho = float(np.clip(np.sin(np.pi * tau / 2.0), -RHO_CAP, RHO_CAP))
    res = minimize_scalar(lambda nu: -t_copula_loglik(u1, u2, rho, nu), bounds=bounds, method="bounded",
                          options={"xatol": 1e-3})
    return rho, float(res.x)


def t_tail_dependence(rho, nu):
    """lambda_U = lambda_L = 2 t_{nu+1}(-sqrt((nu + 1)(1 - rho) / (1 + rho))), the tail dependence of the t-copula
    (spec section 3; the source states that closed forms exist, p. 44). Intuition: it rises with rho and falls as
    nu grows. At nu = infinity (the Gaussian copula) it is zero for rho < 1."""
    rho, nu = np.asarray(rho, float), np.asarray(nu, float)
    out = 2.0 * stdtr(nu + 1.0, -np.sqrt((nu + 1.0) * (1.0 - rho) / (1.0 + rho)))
    return float(out) if out.ndim == 0 else out


def empirical_upper_tail(u1: np.ndarray, u2: np.ndarray, k: int | None = None) -> float:
    """Share of the top k periods of u2 (the market) that are also in the top k of u1 (the issuer), k = floor(sqrt n)
    by default (spec section 3, our choice). Intuition: a model-free count of joint widenings. NaN when n < 4."""
    u1, u2 = np.asarray(u1, float), np.asarray(u2, float)
    n = len(u1)
    if n < 4:
        return np.nan
    k = int(np.floor(np.sqrt(n))) if k is None else int(k)
    top1, top2 = rankdata(u1) > n - k, rankdata(u2) > n - k
    return float((top1 & top2).sum() / k)


def control_residual(y: pd.Series, rclass: pd.Series, log_s: pd.Series, min_n: int = MIN_XS) -> pd.Series:
    """OLS residual of y on [1, rating class dummies, log spread] across one date (spec section 3; Section 8
    `signals.neutralise`). A missing rating class drops the dummies. Fewer than `min_n` rows gives y minus its
    mean. Intuition: keep the tail dependence that the rating and the spread level do not pay for."""
    use_r = rclass.notna().any()
    ok = y.notna() & log_s.notna() & (rclass.notna() if use_r else True)
    out = pd.Series(np.nan, index=y.index, name="utd_ctrl")
    if not ok.any():
        return out
    if ok.sum() < min_n:
        out[ok] = y[ok] - y[ok].mean()
        return out
    X = pd.get_dummies(rclass[ok].astype(str), drop_first=True, dtype=float) if use_r else pd.DataFrame(index=y[ok].index)
    X["log_s"] = log_s[ok].astype(float)
    X = X.loc[:, X.std(ddof=0) > 0]                       # a constant column adds nothing to the intercept
    out[ok] = neutralise(y[ok].to_numpy(float), X.to_numpy(float)) if X.shape[1] else \
        y[ok].to_numpy(float) - y[ok].mean()
    return out


def issuer_tail(x: np.ndarray, m: np.ndarray, min_obs: int) -> dict:
    """UTD, utd_emp, rho, nu and n for one issuer from its change series x and its market series m (spec build steps
    5 and 6). Fewer than `min_obs` joint filtered changes gives NaN measures."""
    zx, zm = ewma_standardise(ar1_residual(x)), ewma_standardise(ar1_residual(m))
    joint = np.isfinite(zx) & np.isfinite(zm)
    n = int(joint.sum())
    nan = {"utd": np.nan, "utd_emp": np.nan, "rho": np.nan, "nu": np.nan, "n_obs": n}
    if n < min_obs:
        return nan
    u1, u2 = pseudo_obs(zx[joint]), pseudo_obs(zm[joint])
    rho, nu = fit_t_copula(u1, u2)
    if not np.isfinite(rho):
        return nan
    return {"utd": t_tail_dependence(rho, nu), "utd_emp": empirical_upper_tail(u1, u2), "rho": rho, "nu": nu,
            "n_obs": n}


def _known(panels: Mapping[str, pd.DataFrame], name: str, dt: pd.Timestamp) -> pd.DataFrame | None:
    df = panels.get(name)
    if df is None or len(df) == 0:
        return None
    return df[df["available_at"] <= dt]


def _spread_rows(panels: Mapping[str, pd.DataFrame], p: pd.DataFrame, freq: str, as_of: pd.Timestamp,
                 dt: pd.Timestamp) -> pd.DataFrame | None:
    """Rows cusip, gvkey, date, g_spread that feed the change series (spec build step 3). Monthly: `bond_panel`
    without stale and carried rows. Daily and weekly: `bond_daily`, gvkey from the latest known `bond_panel` row."""
    if freq == "M":
        return p[~p["carried"].astype(bool) & ~mark_stale(p)][["cusip", "gvkey", "date", "g_spread"]]
    d = _known(panels, "bond_daily", dt)
    if d is None:
        return None
    d = d.assign(date=pd.to_datetime(d["date"]))
    d = d[d["date"] <= as_of].sort_values("available_at").drop_duplicates(["cusip", "date"], keep="last")
    gv = p.sort_values("date").drop_duplicates("cusip", keep="last").set_index("cusip")["gvkey"]
    d = d.assign(gvkey=d["cusip"].map(gv)).dropna(subset=["gvkey"])
    return d[["cusip", "gvkey", "date", "g_spread"]]


# ---------------------------------------------------------------- compute


def compute(panels: Mapping[str, pd.DataFrame], as_of: pd.Timestamp, freq: str = "auto", window: int | None = None,
            min_obs: int | None = None) -> pd.DataFrame:
    """UTD score per issuer at month end as_of (spec build steps 1 to 7). One row per gvkey.

    freq "auto" uses weekly `bond_daily` changes when the panel is present, else monthly `bond_panel` changes.
    Universe: issuers with an `eligible` bond at as_of; with `ratings`, class BB, B or CCC and not D or SD.
    score = standardised percentile rank of -utd_ctrl, NaN where utd_ctrl is NaN. Empty frame (columns COLS)
    without bond_panel. Higher score = long."""
    as_of = pd.Timestamp(as_of) + pd.offsets.MonthEnd(0)
    dt = decision_time(as_of)
    p = _known(panels, "bond_panel", dt)
    if p is None:
        return pd.DataFrame(columns=COLS)
    p = p.assign(date=pd.to_datetime(p["date"]))
    p = p[p["date"] <= as_of]

    # universe at as_of (step 2)
    now = p[p["date"] == as_of].drop_duplicates("cusip", keep="last")
    now = now[eligible(now) & now["gvkey"].notna()]
    out = now.groupby("gvkey")["g_spread"].median().astype(float).to_frame()
    out["rclass"], ctrl = None, "spread"
    ratings = _known(panels, "ratings", dt)
    if ratings is not None and len(out):
        cls = rating_classes(ratings, _known(panels, "leverage", dt), as_of)
        out["rclass"] = out.index.map(cls["rclass"])
        raw = out.index.map(cls["raw"])
        out = out[out["rclass"].isin(HY_CLASSES) & ~pd.Series(raw, index=out.index).isin(DEFAULT_SYMBOLS)]
        ctrl = "rating+spread"
    if out.empty:
        return pd.DataFrame(columns=COLS)

    # change series (steps 3 and 4)
    f = ("W" if _known(panels, "bond_daily", dt) is not None else "M") if freq == "auto" else freq
    rows = _spread_rows(panels, p, f, as_of, dt)
    if rows is None:
        return pd.DataFrame(columns=COLS)
    cal = np.sort(rows["date"].unique()) if f == "D" else None
    W, n_min = window or WINDOW[f], min_obs or MIN_OBS[f]
    end = len(cal) - 1 if f == "D" else int(period_ordinal(pd.Series([as_of]), f)[0])
    ch = log_changes(rows, f, cal)
    ch = ch[(ch["per"] > end - W) & (ch["per"] <= end)]
    X = issuer_changes(ch) if len(ch) else pd.DataFrame()
    M = market_changes(X) if len(X) else X

    # tail dependence per issuer (steps 5 and 6)
    stats = {g: issuer_tail(X[g].to_numpy(float), M[g].to_numpy(float), n_min) if g in X.columns else
             {"utd": np.nan, "utd_emp": np.nan, "rho": np.nan, "nu": np.nan, "n_obs": 0} for g in out.index}
    out = out.join(pd.DataFrame.from_dict(stats, orient="index"))

    # control, rank, standardise (step 7)
    out["utd_ctrl"] = control_residual(out["utd"], out["rclass"], np.log(out["g_spread"]))
    out = out.rename_axis("gvkey").reset_index()
    out["date"], out["available_at"], out["freq"], out["ctrl"] = as_of, dt, f, ctrl
    out["score"] = (-out["utd_ctrl"]).rank(pct=True)
    out = standardise_by_date(out, ["score"])
    out["score"] = out["score"].where(out["utd_ctrl"].notna())
    num = ["score", "utd", "utd_emp", "utd_ctrl", "rho", "nu", "g_spread"]
    return out[COLS].astype({c: float for c in num} | {"n_obs": int}).reset_index(drop=True)
