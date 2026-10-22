"""Fair spread layer: anchor, empirical model, conformal band (methodology Section 7).

The layer turns a probability of default and a loss given default into an
anchor spread (7.1), explains the rest of the log spread with a monotone
model (7.2), scales the residual by its own noise and wraps it in a Mondrian
conformal band (7.3), checks tranche pairs without a model (7.4), and fits
the decay of each residual (7.5).

Units. Spreads are in basis points (bp). Probabilities, hazards and LGD are
decimals per year. `s_el` is in bp, so `kappa` is a pure number.
Inputs are numpy arrays and pandas objects. This module imports no other
`hy` layer.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Mapping, Sequence

import numpy as np
import pandas as pd
from scipy.optimize import brentq
from scipy.special import expit, logit
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

BP = 1e4  # basis points per unit of decimal spread

# ---------------------------------------------------------------------------
# 7.1 Structural anchor
# ---------------------------------------------------------------------------

# Forward features of the PD logit (Section 7.1 formula; names from Section 5.3 and 4).
PD_FEATURES: tuple[str, ...] = (
    "lev_fwd_4",
    "cov_fwd_4",
    "p_liq_short_8",
    "p_refi_4",
    "margin_trend",
    "eq_flags",
    "q_score",
    "gap_rating",
    "log_size",
    "dd_equity",
)

# Cumulative default rates by rating bucket: (1 year, 5 years), decimals.
# "HY" is the book's number: speculative grade 3.60% at 1y, 14.16% at 5y
# (Gatto p. 274). "BB", "B" and "CCC" are PLACEHOLDERS of the order of the
# agency tables. Replace them with the agency study the desk uses.
DEFAULT_PD_TABLE: dict[str, tuple[float, float]] = {
    "HY": (0.0360, 0.1416),  # book, p. 274
    "BB": (0.0070, 0.0600),  # placeholder
    "B": (0.0300, 0.1600),  # placeholder
    "CCC": (0.2200, 0.4500),  # placeholder
}


def hazard(pd_12m: np.ndarray | float) -> np.ndarray:
    """Section 7.1: lambda = -log(1 - PD_12m).

    Intuition: the hazard is the constant default intensity that gives the
    one-year default probability, so it adds across time where PD does not.
    """
    p = np.clip(np.asarray(pd_12m, dtype=float), 0.0, 1.0 - 1e-12)
    return -np.log1p(-p)


def expected_loss_spread_bp(pd_12m: np.ndarray | float, lgd_adj: np.ndarray | float) -> np.ndarray:
    """Section 7.1: s_EL = lambda * LGD_adj, returned in bp.

    Intuition: a risk-neutral investor needs a spread equal to the default
    intensity times the share of the claim lost (book p. 119).
    """
    return hazard(pd_12m) * np.asarray(lgd_adj, dtype=float) * BP


def kappa_by_bucket(
    index_spread_bp: Mapping[str, float] | pd.Series,
    index_el_bp: Mapping[str, float] | pd.Series,
) -> pd.Series:
    """Section 7.1: kappa_t(bucket) = index spread / index expected loss.

    Intuition: kappa is the market price of one unit of expected loss; it is
    high after a sell-off and low in a frothy market (book pp. 113, 531).
    """
    s = pd.Series(index_spread_bp, dtype=float)
    el = pd.Series(index_el_bp, dtype=float).reindex(s.index)
    if (el <= 0).any():
        raise ValueError("index expected loss must be positive in every bucket")
    return (s / el).rename("kappa_t")


def anchor_spread_bp(s_el_bp: np.ndarray | float, kappa: np.ndarray | float) -> np.ndarray:
    """Section 7.1: s_anchor = kappa_t * s_EL (bp).

    Intuition: the anchor is the expected loss priced at today's market rate
    for credit risk.
    """
    return np.asarray(kappa, dtype=float) * np.asarray(s_el_bp, dtype=float)


def pd_5y(
    pd_12m: np.ndarray | float,
    rating_bucket: Sequence[str] | np.ndarray | None = None,
    term_table: Mapping[str, tuple[float, float]] | None = None,
) -> np.ndarray:
    """Section 7.1 and 7.6 `pd_5y`: cumulative 5-year PD from the 12-month PD.

    Assumption. With no `term_table`, the hazard is constant over five years:
    pd_5y = 1 - (1 - pd_12m)^5. A constant hazard overstates the agency
    5-year rate for speculative grade (1 - 0.964^5 = 16.7% against 14.16%),
    because survivors improve. With a `term_table` {bucket: (pd1, pd5)}, the
    hazard in years 2 to 5 is the issuer's 1-year hazard times the bucket
    multiplier m_b = lambda_fwd(b) / lambda_1(b), where
    lambda_fwd(b) = -log((1 - pd5) / (1 - pd1)) / 4. Then
    pd_5y = 1 - (1 - pd_12m) * exp(-4 * m_b * lambda_i).

    Intuition: the term structure of the bucket bends the issuer's own hazard,
    so a bucket where survivors improve gets a lower 5-year rate.
    """
    lam = hazard(pd_12m)
    mult = np.ones_like(lam)
    if term_table is not None:
        if rating_bucket is None:
            raise ValueError("term_table needs rating_bucket")
        buckets = np.asarray(rating_bucket)
        for b, (p1, p5) in term_table.items():
            lam1 = -math.log1p(-p1)
            lam_fwd = -math.log((1.0 - p5) / (1.0 - p1)) / 4.0
            mult = np.where(buckets == b, lam_fwd / lam1, mult)
    return 1.0 - (1.0 - np.clip(np.asarray(pd_12m, dtype=float), 0.0, 1.0)) * np.exp(-4.0 * mult * lam)


@dataclass
class PDModel:
    """Section 7.1: logit PD_12m = alpha + beta' x_fwd, then per-bucket intercept recalibration.

    Step 1 fits a logistic regression on the forward features (standardised,
    NaN replaced by the training median, so `dd_equity` may be empty for a
    private issuer). Step 2 adds an offset delta_b per rating bucket so that
    the mean fitted PD in bucket b equals the 1-year rate of `pd_table[b]`.
    Buckets absent from `pd_table` keep delta = 0.

    Intuition: the regression ranks issuers by fundamentals; the offset pins
    the level of each bucket to the agency record (book p. 274).
    """

    pd_table: Mapping[str, tuple[float, float]] = field(default_factory=lambda: dict(DEFAULT_PD_TABLE))
    C: float = 1.0
    features_: list[str] = field(default_factory=list, init=False)
    medians_: pd.Series | None = field(default=None, init=False)
    scaler_: StandardScaler | None = field(default=None, init=False)
    clf_: LogisticRegression | None = field(default=None, init=False)
    offsets_: dict[str, float] = field(default_factory=dict, init=False)

    def _design(self, X: pd.DataFrame) -> np.ndarray:
        Z = X[self.features_].astype(float).fillna(self.medians_)
        return self.scaler_.transform(Z.to_numpy())

    def _score(self, X: pd.DataFrame) -> np.ndarray:
        return self.clf_.decision_function(self._design(X))

    def fit(self, X: pd.DataFrame, defaulted: np.ndarray, rating_bucket: Sequence[str]) -> "PDModel":
        """Fit the logit on 12-month default flags, then recalibrate per bucket (Section 7.1)."""
        self.features_ = [c for c in X.columns]
        self.medians_ = X[self.features_].astype(float).median()
        Z = X[self.features_].astype(float).fillna(self.medians_).to_numpy()
        self.scaler_ = StandardScaler().fit(Z)
        self.clf_ = LogisticRegression(C=self.C, max_iter=1000).fit(self.scaler_.transform(Z), np.asarray(defaulted))
        self.recalibrate(X, rating_bucket)
        return self

    def recalibrate(self, X: pd.DataFrame, rating_bucket: Sequence[str]) -> dict[str, float]:
        """Section 7.1: solve mean_i expit(score_i + delta_b) = PD1_table(b) for each bucket b.

        Intuition: a single shift of the log odds moves the bucket mean to the
        target and keeps the rank order inside the bucket.
        """
        score = self._score(X)
        buckets = np.asarray(rating_bucket)
        self.offsets_ = {}
        for b in np.unique(buckets):
            if b not in self.pd_table:
                continue
            target = self.pd_table[b][0]
            s = score[buckets == b]
            g = lambda d, s=s, target=target: expit(s + d).mean() - target  # noqa: E731
            lo, hi = logit(target) - s.max() - 1.0, logit(target) - s.min() + 1.0
            self.offsets_[str(b)] = brentq(g, lo, hi, xtol=1e-12)
        return self.offsets_

    def predict_pd12(self, X: pd.DataFrame, rating_bucket: Sequence[str]) -> np.ndarray:
        """Section 7.6 `pd_12m`: expit(alpha + beta' x + delta_bucket)."""
        off = np.array([self.offsets_.get(str(b), 0.0) for b in rating_bucket])
        return expit(self._score(X) + off)

    def predict_pd5y(self, X: pd.DataFrame, rating_bucket: Sequence[str], use_term_table: bool = True) -> np.ndarray:
        """Section 7.6 `pd_5y`: see `pd_5y`; `use_term_table=False` gives the constant hazard."""
        p1 = self.predict_pd12(X, rating_bucket)
        return pd_5y(p1, rating_bucket, self.pd_table if use_term_table else None)


# ---------------------------------------------------------------------------
# 7.2 Empirical model
# ---------------------------------------------------------------------------

# Sign of d log s / d x from the Section 7.2 table: +1 spread rises, -1 falls, 0 free.
DEFAULT_SIGN_MAP: dict[str, int] = {
    "lev_adj_k": +1,
    "ltv_k_mid": +1,
    "coverage": -1,
    "recovery_k_adj": -1,
    "p_breach_4": +1,
    "lev_fwd_sd_4": +1,
    "margin_peer_gap": -1,
    "margin_trend": -1,
    "coc_put_price": -1,
    "lme_score_k": +1,
    "bid_ask_bp": +1,
    "log_amount_outstanding": -1,
}


def monotonic_constraints(columns: Sequence[str], sign_map: Mapping[str, int] | None = None) -> list[int]:
    """Section 7.2 table, column "Constraint": map each feature to +1, -1 or 0.

    Intuition: the constraint keeps the sign the book argues for, so a
    residual is never a sign error.
    """
    sm = DEFAULT_SIGN_MAP if sign_map is None else sign_map
    out = [int(sm.get(c, 0)) for c in columns]
    if any(v not in (-1, 0, 1) for v in out):
        raise ValueError("sign map values must be -1, 0 or +1")
    return out


def recency_weights(date: Sequence, half_life: float) -> np.ndarray:
    """Section 7.2 "weight recent dates more": w = 0.5 ** (age / half_life).

    Age is in days for datetime input and in the input's own unit otherwise.
    Intuition: the weight of a date halves every `half_life`, so the fit
    follows the current regime but keeps the full cycle in the window.
    """
    d = pd.Series(np.asarray(date))
    if pd.api.types.is_datetime64_any_dtype(d):
        age = (d.max() - d).dt.total_seconds().to_numpy() / 86400.0
    else:
        age = (d.max() - d).to_numpy(dtype=float)
    return np.power(0.5, age / float(half_life))


@dataclass
class FairSpreadModel:
    """Section 7.2: log s = log s_anchor + f(x) + eta_{sector,t} + eps.

    Fit procedure (backfitting, `n_backfit` rounds; round 1 is the spec's
    first step):
      1. y = log s - log s_anchor.
      2. eta_{g,t} = mean over (sector g, date t) of (y - f_hat), minus the
         weighted grand mean, so eta is demeaned. In round 1, f_hat = 0.
      3. f = HistGradientBoostingRegressor on (x, y - eta) with
         `monotonic_cst` from `sign_map` and recency sample weights.
    Repeat 2 and 3 so eta does not absorb the effect of sector composition in x.

    Intuition: the anchor sets the level, the sector-date effect removes the
    systematic spread, and f prices what the anchor omits with the book's signs.
    """

    sign_map: Mapping[str, int] | None = None
    half_life: float = 365.0
    n_backfit: int = 2
    max_iter: int = 200
    learning_rate: float = 0.05
    max_leaf_nodes: int = 15
    random_state: int = 0
    features_: list[str] = field(default_factory=list, init=False)
    cst_: list[int] = field(default_factory=list, init=False)
    eta_: pd.DataFrame | None = field(default=None, init=False)
    f_: HistGradientBoostingRegressor | None = field(default=None, init=False)

    @staticmethod
    def _eta_table(r: np.ndarray, w: np.ndarray, sector: np.ndarray, date: np.ndarray) -> pd.DataFrame:
        df = pd.DataFrame({"sector": sector, "date": date, "r": r * w, "w": w})
        g = df.groupby(["sector", "date"], sort=True)[["r", "w"]].sum()
        eta = g["r"] / g["w"]
        grand = (r * w).sum() / w.sum()
        return (eta - grand).rename("eta").reset_index()

    def fit(
        self,
        X: pd.DataFrame,
        log_s: np.ndarray,
        log_s_anchor: np.ndarray,
        sector: Sequence,
        date: Sequence,
    ) -> "FairSpreadModel":
        """Fit eta and f by the procedure in the class docstring (Section 7.2)."""
        self.features_ = list(X.columns)
        self.cst_ = monotonic_constraints(self.features_, self.sign_map)
        y = np.asarray(log_s, dtype=float) - np.asarray(log_s_anchor, dtype=float)
        sector, date = np.asarray(sector), np.asarray(date)
        w = recency_weights(date, self.half_life)
        Xn = X.to_numpy(dtype=float)
        fhat = np.zeros_like(y)
        for _ in range(max(1, self.n_backfit)):
            self.eta_ = self._eta_table(y - fhat, w, sector, date)
            eta = self._lookup_eta(sector, date)
            self.f_ = HistGradientBoostingRegressor(
                max_iter=self.max_iter,
                learning_rate=self.learning_rate,
                max_leaf_nodes=self.max_leaf_nodes,
                monotonic_cst=self.cst_,
                random_state=self.random_state,
            ).fit(Xn, y - eta, sample_weight=w)
            fhat = self.f_.predict(Xn)
        return self

    def _lookup_eta(self, sector: np.ndarray, date: np.ndarray) -> np.ndarray:
        """eta for (sector, date); an unseen date takes the sector's latest eta at or before it, else 0."""
        q = pd.DataFrame({"sector": sector, "date": date, "_i": np.arange(len(sector))})
        out = np.zeros(len(q))
        tab = self.eta_
        for g, qg in q.groupby("sector", sort=False):
            tg = tab[tab["sector"] == g].sort_values("date")
            if tg.empty:
                continue
            qs = qg.sort_values("date")
            m = pd.merge_asof(qs, tg[["date", "eta"]], on="date", direction="backward")
            out[m["_i"].to_numpy()] = m["eta"].fillna(0.0).to_numpy()
        return out

    def eta(self, sector: Sequence, date: Sequence) -> np.ndarray:
        """Section 7.6 `eta_sector_t` for each row."""
        return self._lookup_eta(np.asarray(sector), np.asarray(date))

    def predict_log_spread(
        self,
        X: pd.DataFrame,
        sector: Sequence,
        date: Sequence,
        log_s_anchor: np.ndarray,
    ) -> np.ndarray:
        """Section 7.2: log s_hat = log s_anchor + f(x) + eta_{sector,t}.

        Intuition: the fair log spread is the anchor plus what the features and
        the sector-date effect add.
        """
        Xn = X[self.features_].to_numpy(dtype=float)
        return np.asarray(log_s_anchor, dtype=float) + self.f_.predict(Xn) + self.eta(sector, date)

    def model_slope(
        self,
        X: pd.DataFrame,
        sector: Sequence,
        date: Sequence,
        log_s_anchor: np.ndarray,
        feature: str,
        step: float = 0.5,
    ) -> np.ndarray:
        """Section 7.4: model slope d s_hat / d feature (bp per unit) by central difference.

        Intuition: this is the model's spread per turn, the yardstick for the
        observed SPT of a tranche pair.
        """
        up, dn = X.copy(), X.copy()
        up[feature] = up[feature] + step
        dn[feature] = dn[feature] - step
        s_up = np.exp(self.predict_log_spread(up, sector, date, log_s_anchor))
        s_dn = np.exp(self.predict_log_spread(dn, sector, date, log_s_anchor))
        return (s_up - s_dn) / (2.0 * step)


# ---------------------------------------------------------------------------
# 7.3 Mispricing score and conformal band
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Residuals:
    """Section 7.3 residual set: resid_log, resid_bp."""

    resid_log: np.ndarray
    resid_bp: np.ndarray


def residuals(log_s: np.ndarray, log_s_hat: np.ndarray) -> Residuals:
    """Section 7.3: eps = log s - log s_hat; m = s - s_hat (bp). Positive means cheap.

    Intuition: the log gap compares a 300 bp bond and a 900 bp bond on one
    scale; the bp gap is what the price moves on.
    """
    ls, lh = np.asarray(log_s, dtype=float), np.asarray(log_s_hat, dtype=float)
    return Residuals(resid_log=ls - lh, resid_bp=np.exp(ls) - np.exp(lh))


@dataclass
class NoiseScaleModel:
    """Section 7.3: sigma_hat(x) fitted on |eps|.

    method="linear": OLS of log|eps| on [1, x], then a constant c so that
    mean(|eps| / sigma_hat) = 1 on the fit set. sigma_hat is then the
    conditional mean absolute residual, not a standard deviation; the
    conformal quantile absorbs the scale. method="hgb": a gradient boosted
    regression of |eps| on x, floored at a small positive value.

    Intuition: illiquid and low-rated bonds have wider noise, so the same
    residual means less there.
    """

    method: str = "linear"
    floor: float = 1e-4
    coef_: np.ndarray | None = field(default=None, init=False)
    c_: float = field(default=0.0, init=False)
    hgb_: HistGradientBoostingRegressor | None = field(default=None, init=False)

    def fit(self, X: np.ndarray | pd.DataFrame, eps: np.ndarray) -> "NoiseScaleModel":
        Xn = np.asarray(X, dtype=float)
        a = np.abs(np.asarray(eps, dtype=float))
        if self.method == "linear":
            A = np.column_stack([np.ones(len(Xn)), Xn])
            self.coef_, *_ = np.linalg.lstsq(A, np.log(np.maximum(a, self.floor)), rcond=None)
            self.c_ = 0.0
            self.c_ = float(np.log(np.mean(a / self.predict(Xn))))
        elif self.method == "hgb":
            self.hgb_ = HistGradientBoostingRegressor(max_iter=100, learning_rate=0.05, random_state=0).fit(Xn, a)
        else:
            raise ValueError(f"unknown method {self.method}")
        return self

    def predict(self, X: np.ndarray | pd.DataFrame) -> np.ndarray:
        """Section 7.6 `sigma_x`."""
        Xn = np.asarray(X, dtype=float)
        if self.method == "linear":
            A = np.column_stack([np.ones(len(Xn)), Xn])
            return np.exp(A @ self.coef_ + self.c_)
        return np.maximum(self.hgb_.predict(Xn), self.floor)


def z_score(eps: np.ndarray, sigma: np.ndarray) -> np.ndarray:
    """Section 7.3: z = eps / sigma_hat(x).

    Intuition: z states the residual in units of the model's own noise at that bond.
    """
    return np.asarray(eps, dtype=float) / np.asarray(sigma, dtype=float)


def conformal_quantile(scores: np.ndarray, alpha: float) -> float:
    """Section 7.3: split conformal quantile at level ceil((n+1)(1-alpha))/n.

    Returns the k-th smallest score with k = ceil((n+1)(1-alpha)); returns
    +inf when k > n (too few calibration points) and -inf when alpha >= 1.
    Intuition: the extra +1 counts the new bond, which gives coverage of at
    least 1 - alpha in finite samples under exchangeability.
    """
    s = np.sort(np.asarray(scores, dtype=float))
    n = len(s)
    if alpha >= 1.0:
        return -np.inf
    if alpha <= 0.0 or n == 0:
        return np.inf
    k = math.ceil((n + 1) * (1.0 - alpha) - 1e-12)
    return float(s[k - 1]) if k <= n else np.inf


@dataclass
class MondrianConformal:
    """Section 7.3: split conformal band, Mondrian by (rating bucket, liquidity bucket), score |z|.

    Each cell gets its own q_{1-alpha} from its own calibration scores. A cell
    with no calibration data uses the pooled quantile.
    Intuition: coverage then holds inside each cell, not only on average, so
    the band is honest for illiquid CCC bonds as well as liquid BB bonds.
    """

    alpha: float = 0.1
    q_: dict[tuple, float] = field(default_factory=dict, init=False)
    q_pooled_: float = field(default=np.inf, init=False)

    def fit(self, z_cal: np.ndarray, rating_bucket: Sequence, liquidity_bucket: Sequence) -> "MondrianConformal":
        s = np.abs(np.asarray(z_cal, dtype=float))
        df = pd.DataFrame({"r": np.asarray(rating_bucket), "l": np.asarray(liquidity_bucket), "s": s})
        self.q_ = {k: conformal_quantile(g["s"].to_numpy(), self.alpha) for k, g in df.groupby(["r", "l"])}
        self.q_pooled_ = conformal_quantile(s, self.alpha)
        return self

    def threshold(self, rating_bucket: Sequence, liquidity_bucket: Sequence) -> np.ndarray:
        """Section 7.6 `q_alpha_t` per row."""
        return np.array([self.q_.get((r, l), self.q_pooled_) for r, l in zip(rating_bucket, liquidity_bucket)])

    def flags(self, z: np.ndarray, rating_bucket: Sequence, liquidity_bucket: Sequence) -> tuple[np.ndarray, np.ndarray]:
        """Section 7.3: cheap = 1{z > q}, rich = 1{z < -q}."""
        return cheap_rich_flags(z, self.threshold(rating_bucket, liquidity_bucket))


def cheap_rich_flags(z: np.ndarray, q: np.ndarray | float) -> tuple[np.ndarray, np.ndarray]:
    """Section 7.3: flag_cheap = 1{z > q_{1-alpha}}, flag_rich = 1{z < -q_{1-alpha}}.

    Intuition: a bond is cheap only when it sits outside the band, not when it
    sits above a point estimate.
    """
    z = np.asarray(z, dtype=float)
    return z > q, z < -np.asarray(q)


def aci_update(alpha_t: float, err_t: float, alpha: float, gamma: float) -> float:
    """Section 7.3, adaptive conformal inference (Gibbs and Candes 2021): alpha_{t+1} = alpha_t + gamma (alpha - err_t).

    err_t = 1 when the realised score falls outside the band at time t.
    Intuition: a miss lowers alpha_t and widens the band; a hit raises it and
    narrows the band, so the long-run miss rate tracks alpha.
    """
    return alpha_t + gamma * (alpha - err_t)


@dataclass(frozen=True)
class ACIPath:
    """Trace of an online conformal run (Section 11, Conformal band row: the trace of alpha_t)."""

    alpha_t: np.ndarray
    q_t: np.ndarray
    err_t: np.ndarray

    @property
    def coverage(self) -> float:
        return float(1.0 - self.err_t.mean())


def adaptive_conformal(
    scores: np.ndarray,
    alpha: float = 0.1,
    gamma: float = 0.01,
    window: int = 250,
    adaptive: bool = True,
) -> ACIPath:
    """Section 7.3: online split conformal on a stream of scores |z_t|, with ACI.

    At time t the threshold is conformal_quantile(scores[t-window:t], alpha_t);
    err_t = 1{score_t > q_t}; then alpha_t moves by `aci_update`. With
    `adaptive=False`, alpha_t stays at alpha (the plain rolling band). The
    first `window` points only fill the buffer and are not scored.
    Gibbs and Candes bound: |mean(err) - alpha| <= (max(alpha_1, 1 - alpha_1) + gamma) / (gamma T).
    Intuition: when spreads drift the calibration set goes stale; ACI corrects
    the level from the realised misses.
    """
    s = np.asarray(scores, dtype=float)
    T = len(s) - window
    if T <= 0:
        raise ValueError("stream shorter than the calibration window")
    a_path, q_path, e_path = np.empty(T), np.empty(T), np.empty(T)
    a_t = alpha
    for i in range(T):
        t = window + i
        q = conformal_quantile(s[t - window : t], a_t)
        e = float(s[t] > q)
        a_path[i], q_path[i], e_path[i] = a_t, q, e
        if adaptive:
            a_t = aci_update(a_t, e, alpha, gamma)
    return ACIPath(alpha_t=a_path, q_t=q_path, err_t=e_path)


# ---------------------------------------------------------------------------
# 7.4 Spread per unit of risk
# ---------------------------------------------------------------------------


def spread_per_turn(s_k: np.ndarray | float, s_j: np.ndarray | float, lev_k: np.ndarray | float, lev_j: np.ndarray | float) -> np.ndarray:
    """Section 7.4: SPT_{k,j} = (s_k - s_j) / (Lev_k - Lev_j), bp per turn.

    Intuition: the junior tranche must pay for each extra turn of leverage it
    sits behind (HCA memo, pp. 412-413).
    """
    return (np.asarray(s_k, dtype=float) - np.asarray(s_j, dtype=float)) / (
        np.asarray(lev_k, dtype=float) - np.asarray(lev_j, dtype=float)
    )


def model_pair_gap_bp(
    kappa: np.ndarray | float,
    lam: np.ndarray | float,
    lgd_k: np.ndarray | float,
    lgd_j: np.ndarray | float,
) -> np.ndarray:
    """Section 7.4: s_hat_k - s_hat_j ~= kappa * lambda * (LGD_k - LGD_j), in bp.

    Intuition: inside one issuer the default probability is common, so the
    fair gap between two tranches pays only for their recovery gap.
    """
    return np.asarray(kappa, dtype=float) * np.asarray(lam, dtype=float) * (
        np.asarray(lgd_k, dtype=float) - np.asarray(lgd_j, dtype=float)
    ) * BP


# ---------------------------------------------------------------------------
# 7.5 Residual dynamics and expected convergence
# ---------------------------------------------------------------------------


def fit_ar1(eps: np.ndarray) -> float:
    """Section 7.5: eps_{t+1} = rho eps_t + u, OLS without intercept.

    rho = sum(eps_t eps_{t-1}) / sum(eps_{t-1}^2). NaN values break the pairs
    they touch. Returns NaN with fewer than 3 valid pairs.
    Intuition: rho is the share of today's mispricing still present tomorrow.
    """
    e = np.asarray(eps, dtype=float)
    x, y = e[:-1], e[1:]
    ok = np.isfinite(x) & np.isfinite(y)
    if ok.sum() < 3 or np.sum(x[ok] ** 2) == 0:
        return float("nan")
    return float(np.sum(x[ok] * y[ok]) / np.sum(x[ok] ** 2))


def half_life(rho: np.ndarray | float) -> np.ndarray:
    """Section 7.5: h_1/2 = log 2 / (-log rho), in the period unit of the residual series.

    rho >= 1 gives +inf (no reversion); rho <= 0 gives 0 (reversion inside one period).
    Intuition: the half-life is the time for half of the mispricing to close.
    """
    r = np.asarray(rho, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        out = np.log(2.0) / -np.log(np.where((r > 0) & (r < 1), r, 0.5))
    out = np.where(r >= 1, np.inf, np.where(r <= 0, 0.0, out))
    return np.where(np.isnan(r), np.nan, out)


def expected_convergence_return(
    carry_h: np.ndarray | float,
    spread_duration: np.ndarray | float,
    rho: np.ndarray | float,
    h: float,
    m_bp: np.ndarray | float,
) -> np.ndarray:
    """Section 7.5: E[r_h] ~= carry_h + D_s (1 - rho^h) m / 1e4, decimal return.

    Units: `carry_h` decimal return over h; `spread_duration` D_s in years;
    `m_bp` the bp residual (positive = cheap); h in the period unit of rho.
    The spread is expected to tighten by (1 - rho^h) m bp, which pays
    D_s * that / 1e4. Assumption: the bp gap decays at the rate rho fitted on
    the log residual, which holds to first order for small residuals.
    Intuition: a cheap bond earns its carry plus the part of the gap that
    closes inside the horizon.
    """
    r = np.asarray(rho, dtype=float)
    return np.asarray(carry_h, dtype=float) + np.asarray(spread_duration, dtype=float) * (
        1.0 - np.power(np.clip(r, 0.0, None), h)
    ) * np.asarray(m_bp, dtype=float) / BP


def event_contaminated(as_of: Sequence, last_event_date: Sequence, window_days: int = 5) -> np.ndarray:
    """Section 7.5 and 7.6 `event_contaminated`: 1 when an event sits in the last `window_days` calendar days.

    The flag is 1 when 0 <= as_of - last_event_date <= window_days. NaT gives 0.
    Intuition: the model has not yet absorbed the new state, so Section 9
    owns the bond in that window.
    """
    a = pd.to_datetime(pd.Series(np.asarray(as_of)))
    e = pd.to_datetime(pd.Series(np.asarray(last_event_date)))
    if len(a) == 1 and len(e) > 1:
        a = pd.Series(np.repeat(a.iloc[0], len(e)))
    gap = (a.to_numpy() - e.to_numpy()) / np.timedelta64(1, "D")
    with np.errstate(invalid="ignore"):
        flag = (gap >= 0) & (gap <= window_days)
    return np.where(np.isnan(gap), 0, flag.astype(int))


def peer_fair_spread(s: float, esp: float | None, peer_sd: float | None, s_index: float) -> dict:
    """Fair spread from sector peers, with the HY index as fallback (methodology 7.2; decision page
    2026-10-23-peer-fair-spread).

        fair = s exp(-ESP) = the median spread of the peers in the GICS sector x rating x maturity cell (hy.peers)
        fallback, no peer cell: fair = S_index, the high yield index spread
        noise_log = the peers' robust sd of log spread (NaN on the fallback)
    Intuition: a bond is fair when it pays what bonds of the same sector, rating and maturity pay.
    """
    if esp is not None and esp == esp:
        return {"fair": float(s * math.exp(-esp)), "basis": "sector peers",
                "noise_log": float(peer_sd) if peer_sd is not None and peer_sd == peer_sd else float("nan")}
    return {"fair": float(s_index), "basis": "HY index", "noise_log": float("nan")}


def dts_beta(s_bond: float, s_index: float) -> float:
    """Hedge ratio on the HY index by duration times spread (methodology 7.5 hedge; hy.walkforward): s_bond / S_index.
    Intuition: a bond with twice the index spread moves about twice as much when the market's spreads move."""
    return float(s_bond / s_index) if s_index and s_index > 0 else float("nan")
