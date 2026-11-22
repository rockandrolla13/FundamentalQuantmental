"""Dynamic leverage slope for ESP: class slopes, partial pooling, a causal filter, and a two-part split.
Methodology 7.2 and 7.4; Dynkin et al. 2021, ch. 13; explainer research/notes/dynamic-leverage-slope.md.

Standalone. `hy.peers` and `scripts/backtest_peers.py` do not import this module yet.

Input: a long table with one row per bond and month. It holds the plain ESP and an excess leverage XL (or XM) over
the same peer cell, as `hy.peers.peer_signals` returns them (`esp_<level>` and `xlev_<level>` or `xmlev_<level>`).

    Part 1, class slope   b_raw(k, t), se(k, t) = OLS slope of ESP on XL inside rating class k at month t,
                          with standard errors clustered by issuer
    Part 2, pooling       mu(t), tau2(t)        = random-effects mean and between-class variance (DerSimonian-Laird),
                          tau2 averaged over months <= t, because one month holds only a few classes
                          w(k, t)              = tau2 / (tau2 + se^2)
                          b_pool(k, t)         = w * b_raw + (1 - w) * mu,   v(k, t) = w * se^2 + (1 - w)^2 * var(mu)
    Part 3, filter        b_dyn(k, t)          = b_dyn(k, t-1) + K * (b_pool(k, t) - b_dyn(k, t-1))
                          K                    = (P + q) / (P + q + v)   (local-level Kalman filter, months <= t only)
    Part 3b, state        b_state(t)           = a_t + c_t * m_t, with a_t and c_t fitted on months < t only
    Part 4, split         priced_lev           = b * XL,   resid_esp = ESP - b * XL

Intuition: the data sets each class slope, a noisy class borrows from the others, and a noisy month moves it little.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

MIN_ROWS = 30          # bonds per class and month for a class slope (as hy.peers._slope)
MIN_ISSUERS = 10       # issuers per class and month, so that the clustered se means something
MIN_STATE_MONTHS = 24  # past months before the state fit (part 3b) gives a value


# ---- Part 1: one slope per rating class and month ------------------------------------------------------------------

def ols_slope_se(y: np.ndarray, x: np.ndarray, groups: np.ndarray | None = None) -> tuple[float, float]:
    """OLS slope of y on x with intercept, and its standard error (methodology 7.2, ESP leverage control).

    With `groups` (issuer ids), the se is cluster-robust (CR1): bonds of one issuer share XL and share errors,
    so the plain se understates the noise. Returns (nan, nan) when x has no variance.
    """
    xc = x - x.mean()
    sxx = float(xc @ xc)
    if len(y) < 3 or sxx <= 0:
        return np.nan, np.nan
    b = float(xc @ (y - y.mean())) / sxx
    e = (y - y.mean()) - b * xc
    if groups is None:
        s2 = float(e @ e) / (len(y) - 2)
        return b, float(np.sqrt(s2 / sxx))
    score = pd.Series(xc * e).groupby(groups).sum().to_numpy()
    g, n = len(score), len(y)
    if g < 2:
        return b, np.nan
    adj = g / (g - 1) * (n - 1) / (n - 2)
    return b, float(np.sqrt(adj * float(score @ score)) / sxx)


def class_slopes(rows: pd.DataFrame, esp: str = "esp", x: str = "xlev", by: str = "rclass",
                 month: str = "month", cluster: str | None = "gvkey") -> pd.DataFrame:
    """Part 1. One row per month and class: b_raw, se, n (bonds), g (issuers).

    A class with fewer than MIN_ROWS bonds or MIN_ISSUERS issuers gets b_raw = se = NaN. Each slope uses only
    the bonds of that month, so it is known at that month.
    """
    out = []
    ok = rows[esp].notna() & rows[x].notna()
    for (t, k), cell in rows[ok].groupby([month, by], sort=True):
        g = cell[cluster].nunique() if cluster else len(cell)
        b = se = np.nan
        if len(cell) >= MIN_ROWS and g >= MIN_ISSUERS:
            b, se = ols_slope_se(cell[esp].to_numpy(float), cell[x].to_numpy(float),
                                 cell[cluster].to_numpy() if cluster else None)
        out.append({month: t, by: k, "b_raw": b, "se": se, "n": len(cell), "g": g})
    return pd.DataFrame(out)


# ---- Part 2: pull each class slope toward the mean of all classes -----------------------------------------------------

def random_effects(b: np.ndarray, se: np.ndarray, tau2: float | None = None) -> tuple[float, float, float]:
    """DerSimonian-Laird random-effects mean mu and between-class variance tau2 of the slopes b with errors se.

    tau2_mom = (Q - (k - 1)) / (S1 - S2 / S1), Q = sum w (b - b_w)^2, w = 1 / se^2, S1 = sum w, S2 = sum w^2.
    Intuition: tau2 is the spread of the class slopes beyond what their own noise explains.
    Returns (mu, max(0, tau2_mom), tau2_mom). A given `tau2` replaces the estimate in mu.
    """
    ok = np.isfinite(b) & np.isfinite(se) & (se > 0)
    b, se = b[ok], se[ok]
    if len(b) == 0:
        return np.nan, np.nan, np.nan
    w = 1.0 / se ** 2
    mom = np.nan
    if len(b) >= 2:
        bw = float(w @ b / w.sum())
        denom = w.sum() - (w ** 2).sum() / w.sum()
        mom = (float(w @ (b - bw) ** 2) - (len(b) - 1)) / denom if denom > 0 else np.nan
    t2 = tau2 if tau2 is not None else (max(0.0, mom) if np.isfinite(mom) else 0.0)
    wr = 1.0 / (se ** 2 + t2)
    return float(wr @ b / wr.sum()), t2, mom


def pool_slopes(cs: pd.DataFrame, month: str = "month") -> pd.DataFrame:
    """Part 2. Add tau2_mom, tau2, mu, w, b_pool and v (the variance of b_pool) to the output of `class_slopes`.

    With few classes, one month gives a noisy tau2. So tau2(t) = max(0, mean of tau2_mom over months <= t).
    b_pool = w * b_raw + (1 - w) * mu, w = tau2 / (tau2 + se^2). With tau2 = 0 every class gets mu.
    A class without its own slope that month also gets mu, with v = the variance of mu.
    """
    months = sorted(cs[month].unique())
    moms = []
    parts = []
    for t in months:
        m = cs[cs[month] == t].copy()
        b, se = m["b_raw"].to_numpy(float), m["se"].to_numpy(float)
        mom = random_effects(b, se)[2]
        if np.isfinite(mom):
            moms.append(mom)
        tau2 = max(0.0, float(np.mean(moms))) if moms else 0.0  # expanding: months <= t only
        mu = random_effects(b, se, tau2)[0]
        se2 = se ** 2
        ok = np.isfinite(b) & np.isfinite(se2) & (se2 > 0)
        var_mu = 1.0 / np.sum(1.0 / (se2[ok] + tau2)) if ok.any() else np.nan
        safe = np.where(ok, se2, 1.0)
        w = np.where(ok, tau2 / (tau2 + safe), 0.0)
        m["tau2_mom"], m["tau2"], m["mu"], m["w"] = mom, tau2, mu, w
        m["b_pool"] = np.where(ok, w * np.nan_to_num(b) + (1 - w) * mu, mu)
        # w * se^2 = 1 / (1/se^2 + 1/tau2): the error of the class's own part; (1 - w)^2 var_mu: the error of mu
        m["v"] = np.where(ok, w * safe + (1 - w) ** 2 * var_mu, var_mu)
        parts.append(m)
    return pd.concat(parts, ignore_index=True)


# ---- Part 3: a causal filter through time -----------------------------------------------------------------------------

def local_level_filter(y: pd.Series, r: pd.Series, q: float) -> pd.DataFrame:
    """Part 3. Forward-only local-level Kalman filter (methodology 7.2). The value at t uses y and r at months <= t.

    State: b(t) = b(t-1) + eta, var(eta) = q.   Measure: y(t) = b(t) + eps, var(eps) = r(t).
    A NaN y(t) keeps the prediction and widens P. Returns b (the filtered slope), P (its variance) and K (the gain).
    """
    yv, rv = y.to_numpy(float), r.to_numpy(float)
    b = np.full(len(yv), np.nan)
    p = np.full(len(yv), np.nan)
    k = np.full(len(yv), np.nan)
    bt = pt = np.nan
    for i in range(len(yv)):
        obs = np.isfinite(yv[i]) and np.isfinite(rv[i]) and rv[i] >= 0
        if not np.isfinite(bt):
            if obs:
                bt, pt, k[i] = yv[i], rv[i], 1.0
                b[i], p[i] = bt, pt
            continue
        pp = pt + q
        if obs:
            gain = pp / (pp + rv[i]) if pp + rv[i] > 0 else 1.0
            bt, pt, k[i] = bt + gain * (yv[i] - bt), (1 - gain) * pp, gain
        else:
            pt = pp
        b[i], p[i] = bt, pt
    return pd.DataFrame({"b": b, "P": p, "K": k}, index=y.index)


def estimate_q(y: pd.Series, r: pd.Series) -> float:
    """State noise q from the training months only. For a local level, var(diff y) = q + 2 * mean r.

    q = max(0, var(diff y) - 2 * mean r). Call it on the training fold. Never on the test months.
    """
    d = y.diff().dropna()
    if len(d) < 3:
        return 0.0
    return max(0.0, float(d.var(ddof=1)) - 2.0 * float(r.dropna().mean()))


def filter_slopes(pooled: pd.DataFrame, q: float, by: str = "rclass", month: str = "month") -> pd.DataFrame:
    """Part 3 for every class: filter b_pool with variance v through the months. Adds b_dyn, P and K."""
    parts = []
    for _, c in pooled.sort_values(month).groupby(by, sort=True):
        f = local_level_filter(c["b_pool"], c["v"], q)
        parts.append(c.assign(b_dyn=f["b"].to_numpy(), P=f["P"].to_numpy(), K=f["K"].to_numpy()))
    return pd.concat(parts, ignore_index=True).sort_values([month, by], ignore_index=True)


# ---- Part 3b: does the slope steepen when spreads are wide? ----------------------------------------------------------

def state_slope(b: pd.Series, var: pd.Series, m: pd.Series, min_months: int = MIN_STATE_MONTHS) -> pd.DataFrame:
    """Part 3b. b_state(t) = a_t + c_t * m_t, a_t and c_t from a WLS fit of b on m over months before t.

    b and var: one pooled slope per month and its variance (for example mu and the variance of mu). m: the spread
    state at t, S_t over its expanding mean (F0b in PositioningWork spec/research/regime_features). Weights 1 / var.
    c_t > 0 says the market prices leverage more steeply when spreads are wide. Months < min_months give NaN.
    """
    bv, wv, mv = b.to_numpy(float), 1.0 / var.to_numpy(float), m.to_numpy(float)
    a = np.full(len(bv), np.nan)
    c = np.full(len(bv), np.nan)
    pred = np.full(len(bv), np.nan)
    for t in range(len(bv)):
        ok = np.isfinite(bv[:t]) & np.isfinite(wv[:t]) & np.isfinite(mv[:t]) & (wv[:t] > 0)
        if ok.sum() < min_months or not np.isfinite(mv[t]):
            continue
        x, y, w = mv[:t][ok], bv[:t][ok], wv[:t][ok]
        xm, ym = w @ x / w.sum(), w @ y / w.sum()
        sxx = w @ (x - xm) ** 2
        if sxx <= 0:
            continue
        c[t] = w @ ((x - xm) * (y - ym)) / sxx
        a[t] = ym - c[t] * xm
        pred[t] = a[t] + c[t] * mv[t]
    return pd.DataFrame({"a": a, "c": c, "b_state": pred}, index=b.index)


# ---- Part 4: split ESP into the part leverage explains and the rest --------------------------------------------------

def split_esp(esp: pd.Series, x: pd.Series, b: pd.Series) -> pd.DataFrame:
    """Part 4. priced_lev = b * x (the gap that excess leverage explains), resid_esp = esp - priced_lev.

    The two parts add back to esp exactly. Score both: the decision page 2026-10-22-esp-peer-groups found that
    the leverage part of the gap also predicts return.
    """
    priced = b * x
    return pd.DataFrame({"priced_lev": priced, "resid_esp": esp - priced}, index=esp.index)


# ---- All four parts together -----------------------------------------------------------------------------------------

def dynamic_esp(rows: pd.DataFrame, q: float, esp: str = "esp", x: str = "xlev", by: str = "rclass",
                month: str = "month", cluster: str | None = "gvkey") -> tuple[pd.DataFrame, pd.DataFrame]:
    """Parts 1 to 4. Returns (rows with b_dyn, priced_lev, resid_esp; the slope table per month and class).

    `q` comes from `estimate_q` on the training months. The b_dyn on a row at month t uses months <= t only.
    A row whose class never had a slope gets the pooled mean mu of its month, unfiltered.
    """
    slopes = filter_slopes(pool_slopes(class_slopes(rows, esp, x, by, month, cluster), month), q, by, month)
    out = rows.merge(slopes[[month, by, "b_dyn", "mu"]], on=[month, by], how="left")
    out["b_dyn"] = out["b_dyn"].fillna(out["mu"])
    out = out.drop(columns="mu")
    sp = split_esp(out[esp], out[x], out["b_dyn"])
    out["priced_lev"], out["resid_esp"] = sp["priced_lev"], sp["resid_esp"]
    out.index = rows.index
    return out, slopes
