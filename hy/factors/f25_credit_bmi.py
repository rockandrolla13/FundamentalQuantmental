"""F25 Credit-BMI v2 HY index timing composite (rank 25). Spec docs/factors/F25-credit-bmi.md; methodology Section 8
(candidate replacement for S7, which failed) and Section 3.6 (macro and credit cycle inputs). Source: the user's own
spec `BMI/files/credit_bmi_v2.md`, sections 1.2 to 3.7, = `credit_bmi_v2.pdf` pp. 1 to 7. Pages are PDF pages.

    z_t^k   = clip((x_{t-l_k}^k - mu_t^k) / sd_t^k, -8, 8),  s_t^k = 20 [Phi(sign_k z_t^k) - 1/2]   (eq. 2, p. 3)
    s~_t^k  = (1 - beta_k g_t) 10 tanh(kappa s_t^k / 10),  g_t = 1{21d OAS vol > expanding p80}    (eq. 5, p. 5)
    w       ~ (lam I + (1 - lam) Sigma)^-1 rho,  feature columns scaled by w                        (eq. 4, p. 5)
    C_t     = [q_{a/2}(x_t) - Q, q_{1-a/2}(x_t) + Q],  Q = ceil((n+1)(1-a))/n quantile of E_j      (eq. 6, p. 5)
    a_{t+1} = a_t + gamma (alpha - err_t)                                                           (eq. 7, p. 5)
    score   = pos_t |point_t| / (hi_t - lo_t) x alignment,  pos = +1 if lo > c, -1 if hi < -c      (eq. 8, p. 6)

Intuition: six market-state blocks (VIX change, HY momentum, risk appetite, dealer balance sheet and CDX-cash
basis, aggregate Merton inputs, the rating-bucket common spread factor) feed a quantile model. The index trades only
when the whole conformal 90% interval of the h-day excess return clears the round-trip cost.

Level. Index: one row, `index` = "US_HY" (or "US_IG" with segment="IG"). Daily walk-forward inside, month-end
output. `walk_forward` returns the daily path so the production machine can run it once and sample month ends.

Inputs. One new optional long panel `macro_series` (`series_id`, `date`, `value`, `available_at`), ids in SERIES
and in the spec Inputs table: H0A0_XR (target, required), BAMLH0A0HYM2, the seven FRED rating-bucket OAS ids,
VIXCLS, NYFED_PD_CORP_NET, CDX_IG_5Y, BAMLC0A0CM, EM_BOND_TR, G10_BOND_TR, G10_EQUITY_TR, STRUCT_EQVOL_MED,
STRUCT_NDEV_MED, STRUCT_NET_DOWNGRADES_3M. Without the panel or the target series the result is an empty frame.
A missing block drops out (its signal enters as 0, the CDF midpoint).

Differences from the user's code (spec Section 9). The code calibrates and updates ACI with targets that mature
after t; here only targets matured by t enter day t. P&L uses the daily excess return, not the h-day forward sum.
Boosted trees use scikit-learn GradientBoostingRegressor(loss="quantile") in place of LightGBM.

Evidence is second-hand (Morgan Stanley hit rates 62% HY, 67% IG, p. 1) or synthetic (coverage 0.899, p. 6).
"""

from __future__ import annotations

from itertools import product
from typing import Mapping

import numpy as np
import pandas as pd
from scipy.stats import norm
from sklearn.covariance import LedoitWolf
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import QuantileRegressor

from hy.backtest import decision_time

# ---------------------------------------------------------------- constants

HORIZONS = (5, 21, 63)      # 1W, 1M, 3M trading days (p. 3)
TRADED = 21                 # the traded horizon (p. 7 driver example, h = 21)
TRAIN, CAL, REFIT = 250, 120, 21    # training rows, calibration rows, refit cadence (p. 3)
ALPHA, GAMMA = 0.10, 0.02   # target miscoverage and ACI step (p. 5)
ALPHA_CLIP = (1e-3, 0.499)  # alpha_t bounds (code on p. 6)
MIN_OBS = 60                # expanding z minimum observations (p. 3)
Z_CLIP = 8.0                # winsorisation of raw z (p. 2)
FFILL_LIMIT = 5             # forward fill cap in trading days (p. 2)
DRIFT_SD = 10.0 / 3.0       # terminal sd of drift factors (p. 3)
CHANGE = 21                 # 1-month change window in trading days (p. 2)
MONTHS4 = 84                # 4 months = 4 x 21 trading days (our choice: the source says "4M")
SENT_Z_WINDOW = 126         # 6-month rolling z of the sentiment level, 6 x 21 days (our choice: "6M", p. 2)
SENT_HI, SENT_LO = 3.0, -4.0        # contra-indicator thresholds on the 6M z (p. 2, source note footnote 8)
PC_WINDOW = 250             # trailing days for the PC1 eigenvector (p. 2)
GATE_Q = 0.80               # crisis state: realised OAS vol above its expanding 80th percentile (p. 5)
BETA_MOM, KAPPA = 0.6, 1.0  # momentum cut in crisis, tanh slope (p. 5)
LAGS = (5, 10)              # weekly feature lags (p. 4)
N_FOLDS = 3                 # purged chronological CV folds (p. 4)
CV_MIN_TRAIN, CV_MIN_VAL = 50, 10   # fold guards (code on p. 4)
SHRINK_LAMBDA = 0.5         # lambda of eq. 4 (our choice: the source gives no value; the code uses 0)
DD_MULT, DD_Q = 2.0, 0.95   # D* = 2 x the 95th percentile of h-day adverse moves (p. 6)
COSTS = {"HY": 0.0012, "IG": 0.0005, "CDX_HY": 0.0004, "CDX_IG": 0.0002}  # round trip, decimal (p. 6)
FALLBACK_MODEL = ("linear", {"alpha": 0.01})   # when no CV fold survives (our choice: the code's default penalty)
LINEAR_GRID = [{"alpha": a} for a in (0.0, 0.01, 0.1)]                          # L1 penalty (p. 4)
GBM_GRID = [{"n_estimators": n, "learning_rate": lr, "max_depth": d}
            for n, lr, d in product((100, 200), (0.03, 0.07), (2, 3))]           # 8 points (p. 4)
GBM_FIXED = {"max_leaf_nodes": 7, "min_samples_leaf": 20, "subsample": 0.9, "max_features": 0.8}  # (p. 4)

BLOCKS = ("vol", "mom", "sent", "liq", "struct", "sys")
SIGN = {"vol": -1.0, "mom": 1.0, "sent": 1.0, "liq": -1.0, "struct": -1.0, "sys": -1.0}   # Table 1 (p. 2)
IMPL_LAG = {"vol": 0, "mom": 5, "sent": 0, "liq_cdx": 1, "struct": 1, "sys": 0}             # rows (p. 2)

# series_id -> publication lag in calendar days (p. 2). FRED ids where FRED has the series; the rest are our names.
SERIES = {
    "H0A0_XR": 0, "C0A0_XR": 0, "BAMLH0A0HYM2": 0, "BAMLC0A0CM": 0, "VIXCLS": 0, "CDX_IG_5Y": 0,
    "NYFED_PD_CORP_NET": 9, "EM_BOND_TR": 0, "G10_BOND_TR": 0, "G10_EQUITY_TR": 0,
    "STRUCT_EQVOL_MED": 0, "STRUCT_NDEV_MED": 0, "STRUCT_NET_DOWNGRADES_3M": 0,
    "BAMLC0A1CAAA": 0, "BAMLC0A2CAA": 0, "BAMLC0A3CA": 0, "BAMLC0A4CBBB": 0,
    "BAMLH0A1HYBB": 0, "BAMLH0A2HYB": 0, "BAMLH0A3HYC": 0,
}
BUCKETS = {"BAMLC0A1CAAA": True, "BAMLC0A2CAA": True, "BAMLC0A3CA": True, "BAMLC0A4CBBB": True,
           "BAMLH0A1HYBB": False, "BAMLH0A2HYB": False, "BAMLH0A3HYC": False}   # id -> investment grade
SEGMENTS = {"HY": {"index": "US_HY", "target": "H0A0_XR", "oas": "BAMLH0A0HYM2"},
            "IG": {"index": "US_IG", "target": "C0A0_XR", "oas": "BAMLC0A0CM"}}
STRUCT_IDS = ("STRUCT_EQVOL_MED", "STRUCT_NDEV_MED", "STRUCT_NET_DOWNGRADES_3M")

META = {
    "rank": 25,
    "name": "Credit-BMI v2 HY index timing composite with dealer positions and a rating-bucket common factor",
    "level": "index",
    "horizon_months": 1,
    "needs": ["macro_series"],
    "spec": "docs/factors/F25-credit-bmi.md",
    "section": "8",
}

COLS = (["date", "index", "score", "available_at", "point", "lo", "hi", "pos", "size", "align", "alpha_t",
         "model_kind", "d_star", "stopped", "coverage"] + [f"point_h{h}" for h in HORIZONS]
        + ["gate", "n_blocks"] + [f"s_{k}" for k in BLOCKS])


# ---------------------------------------------------------------- normalisation helpers (Stage 1)


def expanding_z(x: pd.Series, min_obs: int = MIN_OBS, clip: float = Z_CLIP) -> pd.Series:
    """Point-in-time z: mean and sd (ddof 0, as the code) of data up to and including t, clipped at +-8 (eq. 2, p. 3).

    Rows before `min_obs` observations are NaN. A zero sd gives z = 0 (code on p. 2 of the .py)."""
    x = pd.Series(x, dtype=float)
    mu = x.expanding(min_periods=min_obs).mean()
    sd = x.expanding(min_periods=min_obs).std(ddof=0)
    z = (x - mu) / sd.where(sd > 0)
    z = z.where(~((sd == 0) & x.notna()), 0.0)
    return z.clip(-clip, clip)


def cdf_score(z, sign: float = 1.0):
    """s = 20 [Phi(sign z) - 1/2] in [-10, 10] (eq. 2, p. 3). Intuition: a bounded score, sd about 10/3."""
    return 20.0 * (norm.cdf(sign * np.asarray(z, dtype=float)) - 0.5)


def drift_scale(x: pd.Series, min_obs: int = MIN_OBS) -> pd.Series:
    """Drift factor rescaled to sd 10/3 without removing its mean (p. 3). The sd is expanding (ddof 0) to stay
    point in time. Intuition: momentum keeps its sign in a long bull market."""
    x = pd.Series(x, dtype=float)
    sd = x.expanding(min_periods=min_obs).std(ddof=0)
    return x * DRIFT_SD / sd.where(sd > 0)


def gate_and_squash(s: pd.DataFrame, g: pd.Series, beta_mom: float = BETA_MOM, kappa: float = KAPPA) -> pd.DataFrame:
    """s~ = (1 - beta_k g) 10 tanh(kappa s / 10), beta_mom = 0.6, other betas 0 (eq. 5, p. 5).

    Intuition: momentum lags turns, so it loses 60% in a crisis state, and no factor saturates."""
    out = 10.0 * np.tanh(kappa * s / 10.0)
    if "mom" in out:
        out["mom"] = (1.0 - beta_mom * g.reindex(out.index).fillna(0.0)) * out["mom"]
    return out


def regime_flag(oas: pd.Series, window: int = CHANGE, q: float = GATE_Q, min_obs: int = MIN_OBS) -> pd.Series:
    """g_t = 1{21-day std of daily OAS changes > its expanding 80th percentile} (p. 5). The percentile starts after
    60 rows (code on the .py p. 2). NaN vol gives g = 0."""
    rv = pd.Series(oas, dtype=float).diff().rolling(window).std()
    thr = rv.expanding(min_periods=min_obs).quantile(q)
    return (rv > thr).astype(float).where(thr.notna(), 0.0)


# ---------------------------------------------------------------- block helpers (Table 1, p. 2)


def momentum_raw(r: pd.Series, window: int = MONTHS4, month: int = CHANGE) -> pd.Series:
    """4-month EWMA of the 21-day excess return over the 4-month realised monthly vol (Table 1, p. 2).

    Our choices: EWMA span 84 rows, vol = 84-day std of daily returns x sqrt(21)."""
    r = pd.Series(r, dtype=float)
    m = r.rolling(month).sum()
    ma = m.ewm(span=window, min_periods=window).mean()
    vol = r.rolling(window).std() * np.sqrt(month)
    return ma / vol.where(vol > 0)


def sentiment_signal(em: pd.Series, g10b: pd.Series, g10e: pd.Series, change: int = CHANGE,
                     z_window: int = SENT_Z_WINDOW) -> tuple[pd.Series, pd.Series]:
    """Risk-appetite composite: log of the geometric mean of EM/G10 bond and G10 equity/bond TR (Table 1, p. 2).

    Returns (x, flip): x = 21-day change of the log composite, flip = -1 where the 126-row rolling z of the level is
    above +3 or below -4 (contra-indicator), else +1. Our choice: the log level, so the geometric mean is a mean."""
    lvl = 0.5 * (np.log(em / g10b) + np.log(g10e / g10b))
    roll = lvl.rolling(z_window, min_periods=z_window)
    zl = (lvl - roll.mean()) / roll.std(ddof=0)
    flip = pd.Series(np.where((zl > SENT_HI) | (zl < SENT_LO), -1.0, 1.0), index=lvl.index)
    return lvl.diff(change), flip


def pc1_scores(d_oas: pd.DataFrame, ig: list[bool], window: int = PC_WINDOW, min_obs: int = MIN_OBS) -> pd.Series:
    """PC1 score v_t' dOAS_t, v_t the top eigenvector of the trailing `window` rows' covariance (Table 1, p. 2).

    Sign fixed so the summed IG loading is positive (all loadings when no IG bucket is present). Rows with a NaN
    bucket change give NaN. Intuition: one common shock moves every rating bucket."""
    a = d_oas.to_numpy(float)
    ig_mask = np.asarray(ig, dtype=bool) if any(ig) else np.ones(a.shape[1], dtype=bool)
    out = np.full(len(a), np.nan)
    for t in range(len(a)):
        if not np.isfinite(a[t]).all():
            continue
        w = a[max(0, t - window + 1): t + 1]
        w = w[np.isfinite(w).all(axis=1)]
        if len(w) < min_obs:
            continue
        vals, vecs = np.linalg.eigh(np.cov(w, rowvar=False))
        v = vecs[:, -1]
        if v[ig_mask].sum() < 0:
            v = -v
        out[t] = float(a[t] @ v)
    return pd.Series(out, index=d_oas.index)


# ---------------------------------------------------------------- model helpers (Stage 3)


def build_features(s: pd.DataFrame, lags=LAGS) -> pd.DataFrame:
    """20 columns: the 6 gated signals, lags 5 and 10 of each, vol x liq, vol x mom (p. 4). NaN enters as 0, the CDF
    midpoint (our choice). Intuition: the model sees the trajectory, not only the level."""
    s = s.reindex(columns=list(BLOCKS)).fillna(0.0)
    x = s.copy()
    for lag in lags:
        x = x.join(s.shift(lag).fillna(0.0).add_suffix(f"_lag{lag}"))
    x["vol_x_liq"] = s["vol"] * s["liq"]
    x["vol_x_mom"] = s["vol"] * s["mom"]
    return x


def shrinkage_weights(x: np.ndarray, y: np.ndarray, lam: float = SHRINK_LAMBDA, min_rows: int = MIN_OBS) -> np.ndarray:
    """w ~ (lam I + (1 - lam) Sigma)^-1 rho, normalised to sum |w| = 1 (eq. 4, p. 5; normalisation from the code).

    Sigma: Ledoit-Wolf covariance of the standardised columns, so I and Sigma share a scale (our choice). rho: column
    correlations with y. Constant columns get weight 0. Fewer than `min_rows` rows gives equal weights."""
    k = x.shape[1]
    if len(y) < min_rows:
        return np.ones(k) / k
    sd = x.std(axis=0)
    live = sd > 0
    w = np.zeros(k)
    if not live.any():
        return np.ones(k) / k
    xs = (x[:, live] - x[:, live].mean(axis=0)) / sd[live]
    sigma = LedoitWolf().fit(xs).covariance_
    ys = y - y.mean()
    rho = xs.T @ ys / (len(y) * np.sqrt(np.mean(ys ** 2))) if np.std(y) > 0 else np.zeros(int(live.sum()))
    m = lam * np.eye(len(rho)) + (1.0 - lam) * sigma
    w[live] = np.linalg.solve(m + 1e-6 * np.eye(len(rho)), rho)
    tot = np.abs(w).sum()
    return w / tot if tot > 0 else np.ones(k) / k


def pinball_loss(y, yhat, q: float) -> float:
    """Mean of max(q (y - yhat), (q - 1)(y - yhat)), the proper score of a q-quantile (eq. 3, p. 4)."""
    d = np.asarray(y, dtype=float) - np.asarray(yhat, dtype=float)
    return float(np.mean(np.maximum(q * d, (q - 1.0) * d)))


def purged_cv_splits(n: int, n_folds: int = N_FOLDS, embargo: int = TRADED):
    """Chronological folds with an h-row embargo before each validation block (p. 4, code verbatim).

    fold = n // (n_folds + 1). Fold k trains on [0, k fold - embargo) and validates on [k fold, (k+1) fold). A fold
    needs more than 50 training and 10 validation rows."""
    fold = n // (n_folds + 1)
    for k in range(1, n_folds + 1):
        tr_end = k * fold - embargo
        va = slice(k * fold, min((k + 1) * fold, n))
        if tr_end > CV_MIN_TRAIN and va.stop - va.start > CV_MIN_VAL:
            yield slice(0, tr_end), va


def make_quantile_model(kind: str, q: float, params: dict):
    """L1 linear quantile regression or quantile gradient boosting (p. 4). LightGBM is replaced by scikit-learn
    GradientBoostingRegressor: leaves 7, min leaf 20, subsample 0.9, max_features 0.8 per split (the source's
    colsample 0.8 is per tree)."""
    if kind == "linear":
        return QuantileRegressor(quantile=q, alpha=params.get("alpha", 0.01), solver="highs")
    if kind == "gbm":
        return GradientBoostingRegressor(loss="quantile", alpha=q, n_estimators=params["n_estimators"],
                                         learning_rate=params["learning_rate"], max_depth=params["max_depth"],
                                         random_state=0, **GBM_FIXED)
    raise ValueError(kind)


def tune(x: np.ndarray, y: np.ndarray, h: int, kinds=("linear", "gbm")) -> tuple[str, dict, float]:
    """(kind, params) with the lowest mean median pinball loss over the purged folds (p. 4). No surviving fold gives
    FALLBACK_MODEL (our choice: the code then returns no model)."""
    grid = {"linear": LINEAR_GRID, "gbm": GBM_GRID}
    best = (None, None, np.inf)
    splits = list(purged_cv_splits(len(y), N_FOLDS, embargo=h))
    for kind in kinds:
        for params in grid[kind]:
            losses = [pinball_loss(y[va], make_quantile_model(kind, 0.5, params).fit(x[tr], y[tr]).predict(x[va]), 0.5)
                      for tr, va in splits]
            loss = float(np.mean(losses)) if losses else np.inf
            if loss < best[2]:
                best = (kind, params, loss)
    if best[0] is None:
        return FALLBACK_MODEL[0], FALLBACK_MODEL[1], np.nan
    return best


def fit_three(x: np.ndarray, y: np.ndarray, kind: str, params: dict, alpha_t: float):
    """q_{a/2}, q_{0.5}, q_{1-a/2} with shared (kind, params) (p. 5). Returns a predict function giving (md, lo, hi)
    with crossing repaired: lo = min(lo, hi), hi = max(lo, hi)."""
    a = float(np.clip(alpha_t, *ALPHA_CLIP))
    ql, qm, qh = (make_quantile_model(kind, q, params).fit(x, y) for q in (a / 2.0, 0.5, 1.0 - a / 2.0))

    def predict(xn: np.ndarray):
        lo, md, hi = ql.predict(xn), qm.predict(xn), qh.predict(xn)
        return md, np.minimum(lo, hi), np.maximum(lo, hi)
    return predict


def cqr_q(lo_cal: np.ndarray, hi_cal: np.ndarray, y_cal: np.ndarray, alpha_t: float) -> float:
    """Q = the ceil((n+1)(1-a))/n empirical quantile ("higher") of E_j = max(lo_j - y_j, y_j - hi_j) (eq. 6, p. 5).
    Intuition: widen the model band by the calibration error, with the finite-sample n + 1."""
    a = float(np.clip(alpha_t, *ALPHA_CLIP))
    e = np.maximum(lo_cal - y_cal, y_cal - hi_cal)
    n = len(e)
    k = int(np.ceil((n + 1) * (1.0 - a))) / n
    return float(np.quantile(e, min(k, 1.0), method="higher"))


def aci_step(alpha_t: float, err: float, alpha: float = ALPHA, gamma: float = GAMMA) -> float:
    """alpha_{t+1} = alpha_t + gamma (alpha - err_t), clipped to [0.001, 0.499] (eq. 7, p. 5; clip from p. 6).
    Intuition: a miss shrinks alpha_t and widens the next interval."""
    return float(np.clip(alpha_t + gamma * (alpha - err), *ALPHA_CLIP))


def decision(point: float, lo: float, hi: float, cost: float) -> tuple[int, float]:
    """pos = +1 if lo > c, -1 if hi < -c, else 0; size = |point| / (hi - lo) when trading (eq. 8, p. 6).
    Width floor 1e-6 from the code."""
    width = max(hi - lo, 1e-6)
    if lo > cost:
        return 1, abs(point) / width
    if hi < -cost:
        return -1, abs(point) / width
    return 0, 0.0


def alignment_scale(points: Mapping[int, float], traded: int = TRADED) -> float:
    """Cross-horizon rule (p. 3): 1 if all points share the traded sign, 2/3 if one other horizon does, 0 if none.
    NaN points count as disagreement. A zero traded point gives 0."""
    s = np.sign(points.get(traded, np.nan))
    if not np.isfinite(s) or s == 0:
        return 0.0
    others = [np.sign(v) == s for h, v in points.items() if h != traded]
    agree = int(sum(bool(a) for a in others))
    if agree == len(others):
        return 1.0
    return 2.0 / 3.0 if agree >= 1 else 0.0


def drawdown_threshold(y_train: np.ndarray) -> float:
    """D* = 2 x the 95th percentile of h-day adverse moves in the training window (p. 6). Our choice: adverse move =
    |y^(h)|, since the book is long or short."""
    y = np.abs(np.asarray(y_train, dtype=float))
    y = y[np.isfinite(y)]
    return float(DD_MULT * np.quantile(y, DD_Q)) if len(y) else np.nan


def forward_sum(r: pd.Series, h: int) -> pd.Series:
    """y_t^(h) = sum_{j=1..h} r_{t+j} (eq. 1, p. 1). Known only at t + h."""
    return pd.Series(r, dtype=float).rolling(h).sum().shift(-h)


# ---------------------------------------------------------------- walk-forward (Stage 3.6, p. 7)


def walk_forward(features: pd.DataFrame, r: pd.Series, h: int, cost: float = COSTS["HY"], train: int = TRAIN,
                 cal: int = CAL, refit_every: int = REFIT, alpha: float = ALPHA, gamma: float = GAMMA,
                 kinds=("linear", "gbm"), lam: float = SHRINK_LAMBDA) -> pd.DataFrame:
    """Daily walk-forward for one horizon (Algorithm 1, p. 7) with no look-ahead.

    At day t only targets y_j with j + h <= t are known. Calibration = the `cal` latest matured rows, training = the
    `train` rows before them. Every `refit_every` days: weights w (fixed until the next refit), tune, fit three
    quantiles at alpha_t, D* from the training targets. Every day: ACI update with the interval of day t - h, CQR
    interval, decision, daily P&L pos_{t-1} r_t - |dpos| c, drawdown stop (flat for h days, then the peak resets).
    Returns one row per day from the first day with enough history."""
    x_all = features.to_numpy(float)
    rr = pd.Series(r, dtype=float).reindex(features.index).to_numpy()
    y = forward_sum(pd.Series(rr, index=features.index), h).to_numpy()
    first = int(np.argmax(np.isfinite(rr))) if np.isfinite(rr).any() else len(rr)
    t0 = first + train + cal + h - 1
    rows = []
    alpha_t, predict, w, last_fit, d_star = alpha, None, None, -10 ** 9, np.nan
    pred_cache: dict[int, tuple[float, float, float]] = {}
    issued: dict[int, tuple[float, float]] = {}
    n_cov = n_mat = 0
    pos, equity, peak, cool = 0, 0.0, 0.0, 0
    kind = None
    for t in range(t0, len(x_all)):
        if t - h in issued:                                  # y_{t-h} matured at the close of t
            lo_o, hi_o = issued.pop(t - h)
            err = 0.0 if lo_o <= y[t - h] <= hi_o else 1.0
            alpha_t = aci_step(alpha_t, err, alpha, gamma)
            n_mat, n_cov = n_mat + 1, n_cov + int(err == 0.0)
        c_end = t - h + 1                                    # matured rows are j < c_end
        ca = slice(c_end - cal, c_end)
        tr = slice(c_end - cal - train, c_end - cal)
        ok = np.isfinite(y[tr])
        if (predict is None or t - last_fit >= refit_every) and ok.sum() > CV_MIN_TRAIN:
            x_tr, y_tr = x_all[tr][ok], y[tr][ok]
            w = shrinkage_weights(x_tr, y_tr, lam)
            kind, params, _ = tune(x_tr * w, y_tr, h, kinds)
            predict = fit_three(x_tr * w, y_tr, kind, params, alpha_t)
            d_star, last_fit, pred_cache = drawdown_threshold(y_tr), t, {}
        if predict is None:
            continue
        need = [j for j in range(ca.start, t + 1) if j not in pred_cache]
        if need:
            md_n, lo_n, hi_n = predict(x_all[need] * w)
            pred_cache.update({j: (m, l, u) for j, m, l, u in zip(need, md_n, lo_n, hi_n)})
        lo_c = np.array([pred_cache[j][1] for j in range(ca.start, ca.stop)])
        hi_c = np.array([pred_cache[j][2] for j in range(ca.start, ca.stop)])
        okc = np.isfinite(y[ca])
        if not okc.any():
            continue
        q = cqr_q(lo_c[okc], hi_c[okc], y[ca][okc], alpha_t)
        point, lo, hi = pred_cache[t][0], pred_cache[t][1] - q, pred_cache[t][2] + q
        issued[t] = (lo, hi)

        pnl = pos * (rr[t] if np.isfinite(rr[t]) else 0.0)
        equity += pnl
        peak = max(peak, equity)
        if cool == 0 and peak - equity > d_star:
            cool, peak = h, equity
        new_pos, size = decision(point, lo, hi, cost)
        stopped = cool > 0
        if stopped:
            new_pos, size, cool = 0, 0.0, cool - 1
        equity -= abs(new_pos - pos) * cost
        pos = new_pos
        rows.append({"date": features.index[t], "point": point, "lo": lo, "hi": hi, "pos": pos, "size": size,
                     "alpha_t": alpha_t, "model_kind": kind, "d_star": d_star, "stopped": stopped, "q": q,
                     "equity": equity, "coverage": n_cov / n_mat if n_mat else np.nan})
    return pd.DataFrame(rows, columns=["date", "point", "lo", "hi", "pos", "size", "alpha_t", "model_kind", "d_star",
                                       "stopped", "q", "equity", "coverage"])


# ---------------------------------------------------------------- panel steps


def align_series(obs: pd.DataFrame, calendar: pd.DatetimeIndex, lag_days: int = 0,
                 limit: int = FFILL_LIMIT) -> pd.Series:
    """One series on the trading calendar, point in time (hygiene rules, pp. 2 to 3).

    Usable day = max(date + lag_days, available_at - 1 day): a value known at decision time t + 1 day is usable at the
    close of t. A revision of an older date never overwrites a newer reference date. The value sits on the first
    trading day on or after its usable day, then fills forward at most `limit` rows."""
    if obs is None or obs.empty:
        return pd.Series(np.nan, index=calendar)
    o = obs.assign(date=pd.to_datetime(obs["date"]), available_at=pd.to_datetime(obs["available_at"]))
    o = o.assign(eff=np.maximum(o["date"] + pd.Timedelta(lag_days, unit="D"),
                                o["available_at"] - pd.Timedelta(1, unit="D")).dt.normalize())
    o = o.sort_values(["eff", "available_at", "date"])
    o = o[o["date"] >= o["date"].cummax()]
    loc = calendar.searchsorted(o["eff"].to_numpy(), side="left")
    keep = loc < len(calendar)
    placed = pd.Series(o["value"].astype(float).to_numpy()[keep], index=loc[keep])
    placed = placed[~placed.index.duplicated(keep="last")]
    out = pd.Series(np.nan, index=range(len(calendar)))
    out.loc[placed.index] = placed.to_numpy()
    out.index = calendar
    return out.ffill(limit=limit)


def block_signals(series: Mapping[str, pd.Series], segment: str = "HY") -> pd.DataFrame:
    """The six raw block scores s^(k) in [-10, 10] on the calendar (Table 1, p. 2; eq. 2, p. 3). A block with no
    input is all NaN."""
    seg = SEGMENTS[segment]
    cal = series[seg["target"]].index
    nan = pd.Series(np.nan, index=cal)
    get = lambda k: series.get(k, nan)  # noqa: E731

    def zcdf(x, block, lag):
        return pd.Series(cdf_score(expanding_z(x.shift(lag)), SIGN[block]), index=cal)

    s = pd.DataFrame(index=cal)
    s["vol"] = zcdf(get("VIXCLS").diff(CHANGE), "vol", IMPL_LAG["vol"])
    s["mom"] = drift_scale(momentum_raw(get(seg["target"])).shift(IMPL_LAG["mom"])) * SIGN["mom"]
    x_sent, flip = sentiment_signal(get("EM_BOND_TR"), get("G10_BOND_TR"), get("G10_EQUITY_TR"))
    s["sent"] = zcdf(x_sent, "sent", IMPL_LAG["sent"]) * flip
    z_a = expanding_z(get("NYFED_PD_CORP_NET"))
    z_b = expanding_z((get("CDX_IG_5Y") - get("BAMLC0A0CM")).diff(CHANGE).shift(IMPL_LAG["liq_cdx"]))
    s["liq"] = cdf_score(pd.concat([z_a, z_b], axis=1).mean(axis=1, skipna=True), SIGN["liq"])
    z_st = pd.concat([expanding_z(get(k).shift(IMPL_LAG["struct"])) for k in STRUCT_IDS], axis=1)
    s["struct"] = cdf_score(z_st.mean(axis=1, skipna=True), SIGN["struct"])
    ids = [k for k in BUCKETS if k in series and series[k].notna().any()]
    if len(ids) >= 2:
        d = pd.concat([series[k].diff() for k in ids], axis=1)
        pc = pc1_scores(d, [BUCKETS[k] for k in ids]).rolling(CHANGE).sum()
        s["sys"] = zcdf(pc, "sys", IMPL_LAG["sys"])
    else:
        s["sys"] = np.nan
    return s


def compute(panels: Mapping[str, pd.DataFrame], as_of: pd.Timestamp, horizons=HORIZONS, traded: int = TRADED,
            segment: str = "HY", cost: float | None = None, train: int = TRAIN, cal: int = CAL,
            refit_every: int = REFIT, kinds=("linear", "gbm"), lam: float = SHRINK_LAMBDA) -> pd.DataFrame:
    """F25 score for the index at month end `as_of` (spec Sections 3 and 5).

    score = pos x size x alignment of the traded horizon on the last trading day <= as_of. 0 means flat. NaN means
    too little history. Returns one row with the COLS columns, or an empty frame without `macro_series` or its
    target series."""
    as_of = pd.Timestamp(as_of)
    dt = decision_time(as_of)
    seg = SEGMENTS[segment]
    ms = panels.get("macro_series")
    if ms is None or len(ms) == 0:
        return pd.DataFrame(columns=COLS)
    ms = ms[(pd.to_datetime(ms["available_at"]) <= dt) & (pd.to_datetime(ms["date"]) <= as_of)]
    tgt = ms[ms["series_id"] == seg["target"]]
    if tgt.empty:
        return pd.DataFrame(columns=COLS)
    calendar = pd.DatetimeIndex(sorted(pd.to_datetime(tgt["date"]).dt.normalize().unique()))
    series = {k: align_series(g, calendar, SERIES.get(k, 0)) for k, g in ms.groupby("series_id")}
    s = block_signals(series, segment)
    g = regime_flag(series.get(seg["oas"], pd.Series(np.nan, index=calendar)))
    s_g = gate_and_squash(s, g)
    feats = build_features(s_g)
    r = series[seg["target"]]
    c = COSTS[segment] if cost is None else cost

    paths = {h: walk_forward(feats, r, h, c, train, cal, refit_every, kinds=kinds, lam=lam) for h in horizons}
    last = {h: (p.iloc[-1] if len(p) and p["date"].iloc[-1] == calendar[-1] else None) for h, p in paths.items()}
    points = {h: (float(v["point"]) if v is not None else np.nan) for h, v in last.items()}
    row = {"date": as_of, "index": seg["index"], "available_at": pd.Timestamp(pd.to_datetime(ms["available_at"]).max()),
           "gate": float(g.iloc[-1]), "n_blocks": int(s.iloc[-1].notna().sum())}
    row.update({f"s_{k}": float(s_g[k].iloc[-1]) if pd.notna(s[k].iloc[-1]) else np.nan for k in BLOCKS})
    row.update({f"point_h{h}": points.get(h, np.nan) for h in HORIZONS})
    v = last.get(traded)
    if v is None:
        row.update({"score": np.nan, "point": np.nan, "lo": np.nan, "hi": np.nan, "pos": np.nan, "size": np.nan,
                    "align": np.nan, "alpha_t": np.nan, "model_kind": None, "d_star": np.nan, "stopped": None,
                    "coverage": np.nan})
    else:
        align = alignment_scale(points, traded)
        row.update({k: v[k] for k in ("point", "lo", "hi", "pos", "size", "alpha_t", "model_kind", "d_star",
                                      "stopped", "coverage")})
        row["align"] = align
        row["score"] = float(v["pos"]) * float(v["size"]) * align
    return pd.DataFrame([row]).reindex(columns=COLS)
