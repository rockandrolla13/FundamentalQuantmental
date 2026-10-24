"""Stress tests for the Wolfe Trahan firm-level results that passed or came close.

Decision page: docs/decisions/2026-10-24-wt-relationship-tests.md, section "Robustness". Methodology 5.2.
Run:
    PYTHONPATH=. python3 scripts/wt_robustness.py               # 1,000 bootstrap draws
    PYTHONPATH=. python3 scripts/wt_robustness.py --draws 200   # quicker

H0 per result: the signal carries no information about the group outcome beyond the controls. Under H0 a placebo
signal with the same autocorrelation gives a Clark-West t and a holdout t as large as the real one in a large share
of draws. H1: the real statistics sit in the upper tail of the placebo distribution (empirical p < 0.05), the result
survives the removal of any one cycle window, holds in most reasonable specifications, and keeps |t| > 2 under
EWC errors with t_nu critical values (Lazarus, Lewis, Stock, Watson 2018).

Checks:
a. Placebo. Replace z by circular shifts of itself (all shifts of at least 8 quarters) and by stationary-bootstrap
   resamples (Politis and Romano 1994, mean block 8 quarters). Controls and outcome stay fixed.
   Full rule: resample the whole macro frame (every signal and control, rows together) by joint circular shifts and
   by arch.bootstrap.StationaryBootstrap, run all 92 study tests (A, A high leverage, B) on each draw, and apply the
   full pass rule. Report the false-pass rate, the placebo p per test, Romano-Wolf stepdown p on the Clark-West t,
   and Benjamini-Hochberg and Benjamini-Yekutieli q-values.
b. Leave one cycle window out. Drop the signal quarters of one window and refit the pass rule.
c. Specification curve over the high-leverage cut-off, minimum LTM sales, winsorising, signal transform, weighting,
   and the decline threshold.
d. Holdout t and Clark-West t with equal-weighted cosine (EWC) errors and t_nu critical values next to Newey-West
   (Lazarus, Lewis, Stock, Watson 2018, eq. 10; nu = floor(0.4 T^(2/3)) per their footnote 3).
e. Historical GICS (data/raw/backtest/gics_history.parquet) in place of current GICS, where history exists.

Reuses scripts/wt_tests.py for every input, outcome, and statistic. The fast Clark-West path reproduces
wt_tests.clark_west (tests/test_wt_robustness.py checks it).
"""

from __future__ import annotations

import argparse
import contextlib
import functools
import itertools
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import norm, t as t_dist

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import wt_tests as w  # noqa: E402
from hy.backtest import CYCLE_WINDOWS  # noqa: E402

SEED = 42
MIN_SHIFT = 8  # quarters; a circular shift closer than this keeps too much of the real timing
MEAN_BLOCK = 8  # quarters, stationary bootstrap
POST_WINDOWS = (2015, 2020, 2022)
_WINSOR = w._winsor  # the study's winsor function, captured before any patch

# The results under stress: (id, claim, panel, group, outcome). panel "all" = test A, "hl" = test A high leverage.
RESULTS = [
    ("R1", "H1c", "hl", "Industrials", "dv_k2"),
    ("R2a", "H5k", "all", "Materials", "dsg_k2"),
    ("R2b", "H5k", "hl", "Materials", "dsg_k2"),
    ("R3", "H5k", "all", "Industrials", "dsg_k2"),
    ("R4a", "H3", "hl", "Energy", "debitda_k4"),
    ("R4b", "H3", "all", "Consumer Discretionary", "dv_k2"),
    ("R5a", "H2", "all", "Consumer Discretionary", "debitda_k4"),
    ("R5b", "H2", "all", "Consumer Discretionary", "dmargin_k4"),
    ("R5c", "H2", "hl", "Consumer Discretionary", "debitda_k4"),
    ("R5d", "H2", "hl", "Consumer Discretionary", "dmargin_k4"),
    ("R6a", "H8a", "all", "All", "decline_k4"),
    ("R6b", "H8a", "hl", "All", "decline_k4"),
]

# Specification grid. The first value of each list is the study's choice.
SPEC_HL = (4.0, 3.0, 5.0, 6.0)
SPEC_SALES = (40.0, 100.0, 250.0)
SPEC_WINSOR = (0.01, 0.025)
SPEC_WEIGHT = ("equal", "sales")
SPEC_DECLINE = (0.20, 0.10, 0.30)


def claimed_sign(claim: str, group: str, outcome: str) -> int:
    """The sign fixed in wt_tests.CLAIMS. The stress test never changes it."""
    for g, o, s in w.CLAIMS[claim]["tests"]:
        if g == group and o == outcome:
            return s
    raise KeyError((claim, group, outcome))


@contextlib.contextmanager
def patched(module, **values):
    """Set module globals for the duration of the block (wt_tests reads its constants at call time)."""
    old = {k: getattr(module, k) for k in values}
    try:
        for k, v in values.items():
            setattr(module, k, v)
        yield
    finally:
        for k, v in old.items():
            setattr(module, k, v)


# ---------------------------------------------------------------------------
# Group series
# ---------------------------------------------------------------------------


def group_series(Y: pd.DataFrame, rows: pd.Series | pd.DataFrame, cell: pd.DataFrame | None = None,
                 weights: pd.DataFrame | None = None) -> pd.Series:
    """Mean outcome per quarter over the group firms. rows: firm flags (current GICS) or a firm x quarter matrix
    (historical GICS). weights: firm x quarter weights (LTM sales at q) for a weighted mean; None = equal weight."""
    if isinstance(rows, pd.DataFrame):
        cell = rows if cell is None else (rows.reindex_like(Y).fillna(False) & cell.reindex_like(Y).fillna(False))
        rows = pd.Series(True, index=Y.index)
    if weights is None:
        return w.group_mean(Y, rows, cell)
    X = Y.loc[rows.reindex(Y.index, fill_value=False)]
    if cell is not None:
        X = X.where(cell.reindex_like(X).fillna(False))
    Wt = weights.reindex_like(X).where(X.notna())
    n = X.notna().sum()
    return ((X * Wt).sum() / Wt.sum()).where(n >= w.MIN_FIRMS)


# ---------------------------------------------------------------------------
# Statistics on one design
# ---------------------------------------------------------------------------


def design(z: pd.Series, controls: pd.DataFrame, y: pd.Series, k: int) -> pd.DataFrame:
    """Complete-case frame [y, z, controls, y_lag], exactly the sample of wt_tests.run_outcome."""
    X = pd.concat([z.rename("z"), controls, y.shift(k).rename("y_lag")], axis=1)
    return pd.concat([y.reindex(X.index).rename("y"), X], axis=1).dropna()


def _const(a: np.ndarray) -> np.ndarray:
    return np.column_stack([np.ones(len(a)), a])


class CWRace:
    """Expanding-window Clark-West race of wt_tests.clark_west, split so that a placebo z refits only the full model.

    At holdout quarter q both models fit on rows t <= q - k. The base model holds no z, so its forecasts stay fixed
    across placebo draws.
    """

    def __init__(self, d: pd.DataFrame, k: int, start: pd.Period = w.HOLDOUT_START, min_train: int = 24):
        self.k, self.y = k, d["y"].to_numpy()
        self.others = d.drop(columns=["y", "z"]).to_numpy()
        self.zcol = list(d.columns[1:]).index("z")
        ords = d.index.asi8
        self.tests, self.trains = [], []
        for i in np.flatnonzero(ords >= start.ordinal):
            tr = ords <= ords[i] - k
            if tr.sum() >= min_train:
                self.tests.append(i)
                self.trains.append(tr)
        Xb = _const(self.others)
        self.yb = np.array([Xb[i] @ np.linalg.lstsq(Xb[tr], self.y[tr], rcond=None)[0]
                            for i, tr in zip(self.tests, self.trains)])
        self.cols_full = list(d.columns[1:])

    def full_x(self, z: np.ndarray) -> np.ndarray:
        """Columns in the order of wt_tests: const, z, controls, y_lag."""
        X = np.insert(self.others, self.zcol, z, axis=1)
        return _const(X)

    def run(self, z: np.ndarray, return_f: bool = False) -> dict:
        if len(self.tests) < 12:
            return {"n": len(self.tests), "cw_t": np.nan, "p": np.nan, "oos_r2": np.nan}
        Xf = self.full_x(z)
        yf = np.array([Xf[i] @ np.linalg.lstsq(Xf[tr], self.y[tr], rcond=None)[0]
                       for i, tr in zip(self.tests, self.trains)])
        yo = self.y[self.tests]
        eb, ef = yo - self.yb, yo - yf
        f = eb**2 - (ef**2 - (self.yb - yf) ** 2)
        res = sm.OLS(f, np.ones(len(f))).fit(cov_type="HAC", cov_kwds={"maxlags": self.k})
        t = float(res.tvalues[0])
        out = {"n": len(f), "cw_t": t, "p": float(1 - norm.cdf(t)), "oos_r2": float(1 - (ef**2).sum() / (eb**2).sum())}
        if return_f:
            out["f"] = f
        return out


def holdout_ols(d: pd.DataFrame, z: np.ndarray | None = None):
    """OLS of y on const, z, controls, y_lag over the holdout rows. Returns (y, X, column names) or None if n < 20."""
    hold = d.index >= w.HOLDOUT_START
    X = d.drop(columns="y").copy()
    if z is not None:
        X["z"] = z
    if hold.sum() < 20:
        return None
    return d["y"].to_numpy()[hold], _const(X.to_numpy()[hold]), ["const"] + list(X.columns)


def holdout_t_nw(d: pd.DataFrame, k: int, z: np.ndarray | None = None) -> tuple[float, float]:
    """Holdout b and Newey-West t of z, as wt_tests.hac_regression (maxlags = horizon)."""
    o = holdout_ols(d, z)
    if o is None:
        return np.nan, np.nan
    y, X, names = o
    res = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": k})
    j = names.index("z")
    return float(res.params[j]), float(res.tvalues[j])


# ---------------------------------------------------------------------------
# Check d: inference with few quarters (Lazarus, Lewis, Stock, Watson 2018)
# ---------------------------------------------------------------------------


def ewc_nu(T: int) -> int:
    """LLSW (2018) rule (4): nu = 0.4 T^(2/3) cosine terms, rounded down (their footnote 3), at least 2."""
    return max(2, int(np.floor(0.4 * T ** (2 / 3))))


def lrv_ewc(v: np.ndarray, nu: int) -> np.ndarray:
    """Equal-weighted cosine long-run variance of the T x p scores v: (1/nu) sum_j L_j L_j',
    L_j = sqrt(2/T) sum_t v_t cos(pi j (t - 1/2) / T). Intuition: nu low-frequency averages, each an
    independent draw of the long-run variance, so t has a Student t law with nu degrees of freedom."""
    T = len(v)
    tt = np.arange(1, T + 1) - 0.5
    C = np.sqrt(2.0 / T) * np.cos(np.pi * np.outer(np.arange(1, nu + 1), tt) / T)  # nu x T
    L = C @ v
    return L.T @ L / nu


def har_t(y: np.ndarray, X: np.ndarray, j: int, lrv) -> float:
    """t of coefficient j with Var(b) = (X'X)^-1 T Omega (X'X)^-1, Omega the long-run variance of x_t u_t."""
    b = np.linalg.lstsq(X, y, rcond=None)[0]
    v = X * (y - X @ b)[:, None]
    A = np.linalg.inv(X.T @ X)
    V = A @ (len(y) * lrv(v)) @ A
    return float(b[j] / np.sqrt(V[j, j]))


def holm_cv_one_sided(nu: int) -> float:
    """t_nu critical value for the study's one-sided Holm level 0.05 / 8."""
    return float(t_dist.ppf(1 - w.holm_threshold(), nu))


def har_holdout(d: pd.DataFrame, k: int, sign: int) -> dict:
    """Holdout t of z with Newey-West (the study) and with EWC and t_nu critical values (LLSW 2018).
    Also the Clark-West t with EWC errors, against the one-sided Holm bar 0.05 / 8 under t_nu."""
    o = holdout_ols(d)
    if o is None:
        return {"n": 0}
    y, X, names = o
    j, T = names.index("z"), len(y)
    nu = ewc_nu(T)
    b, t_nw = holdout_t_nw(d, k)
    t_ewc = har_t(y, X, j, functools.partial(lrv_ewc, nu=nu))
    cw = CWRace(d, k).run(d["z"].to_numpy(), return_f=True)
    out = {"n": T, "b": b, "t_nw_study": t_nw, "p_nw_study": float(2 * (1 - norm.cdf(abs(t_nw)))),
           "t_ewc": t_ewc, "ewc_nu": nu, "p_ewc": float(2 * (1 - t_dist.cdf(abs(t_ewc), nu))),
           "cv_ewc_5pct": float(t_dist.ppf(0.975, nu)), "ewc_significant": bool(sign * t_ewc > t_dist.ppf(0.975, nu))}
    f = cw.get("f")
    if f is not None:
        nf = ewc_nu(len(f))
        t_cw = har_t(f, np.ones((len(f), 1)), 0, functools.partial(lrv_ewc, nu=nf))
        out.update({"cw_t_nw_study": cw["cw_t"], "cw_t_ewc": t_cw, "cw_ewc_nu": nf,
                    "cw_p_ewc": float(1 - t_dist.cdf(t_cw, nf)), "cw_holm_cv_ewc": holm_cv_one_sided(nf),
                    "cw_holm_cv_ewc_nu_rounded": holm_cv_one_sided(int(round(0.4 * len(f) ** (2 / 3)))),
                    "cw_clears_holm_ewc": bool(t_cw > holm_cv_one_sided(nf))})
    return out


# ---------------------------------------------------------------------------
# One evaluation with the pass rule
# ---------------------------------------------------------------------------


def evaluate(z: pd.Series, controls: pd.DataFrame, y: pd.Series, outcome: str, sign: int,
             drop_window: int | None = None, with_har: bool = False) -> dict:
    """Holdout b and t, Clark-West, cycle signs, and the pass rule of wt_tests.run_outcome.

    drop_window: a cycle window whose signal quarters leave the sample after the lags are built. The cycle rule then
    asks for the claimed sign in all but one of the remaining windows (2 of 3), and in all but one of the remaining
    post-note windows. Without drop_window the rule is the study's: 3 of 4 and 2 of 3.
    """
    k = w.horizon(outcome)
    d = design(z, controls, y, k)
    yy = y.copy()
    if drop_window is not None:
        a, b_ = (pd.Period(x, "Q") for x in CYCLE_WINDOWS[drop_window])
        d = d[(d.index < a) | (d.index > b_)]
        yy[(yy.index >= a) & (yy.index <= b_)] = np.nan
    hb, ht = holdout_t_nw(d, k)
    cw = CWRace(d, k).run(d["z"].to_numpy())
    cyc = w.cycle_means(z, yy, sign, k)
    windows = [c for c in CYCLE_WINDOWS if c != drop_window]
    post = [c for c in POST_WINDOWS if c != drop_window]
    need_all, need_post = (3, 2) if drop_window is None else (len(windows) - 1, len(post) - 1)
    n_cyc = sum(cyc[c] > 0 for c in windows if np.isfinite(cyc[c]))
    n_post = sum(cyc[c] > 0 for c in post if np.isfinite(cyc[c]))
    sign_ok = bool(np.isfinite(hb) and np.sign(hb) == sign)
    passed = sign_ok and np.isfinite(cw["p"]) and cw["p"] < w.holm_threshold() and n_cyc >= need_all and n_post >= need_post
    out = {"n": int(len(d)), "hold_b": hb, "hold_t": ht, "hold_t_claimed": sign * ht if np.isfinite(ht) else np.nan,
           "sign_ok": sign_ok, "cw_t": cw["cw_t"], "cw_p": cw["p"], "oos_r2": cw["oos_r2"],
           "cycles": cyc, "cycles_as_claimed": int(n_cyc), "post_as_claimed": int(n_post), "pass": bool(passed)}
    if with_har:
        out["har"] = har_holdout(d, k, sign)
    return out


# ---------------------------------------------------------------------------
# Check a: placebo signals that keep the autocorrelation
# ---------------------------------------------------------------------------


def circular_shifts(n: int, min_shift: int = MIN_SHIFT) -> list[int]:
    """All shifts s with min(s, n - s) >= min_shift."""
    return [s for s in range(1, n) if min(s, n - s) >= min_shift]


def stationary_bootstrap_index(n: int, mean_block: float, rng: np.random.Generator) -> np.ndarray:
    """Politis-Romano (1994) stationary bootstrap: blocks of geometric length (mean `mean_block`), wrapped circularly."""
    p = 1.0 / mean_block
    new = rng.random(n) < p
    new[0] = True
    starts = rng.integers(0, n, size=n)
    idx = np.empty(n, dtype=int)
    for t in range(n):
        idx[t] = starts[t] if new[t] else (idx[t - 1] + 1) % n
    return idx


def empirical_p(real: float, placebo: np.ndarray) -> float:
    """(1 + #{placebo >= real}) / (1 + N): the share of placebos at least as large, with the real draw counted."""
    placebo = placebo[np.isfinite(placebo)]
    return float((1 + np.sum(placebo >= real)) / (1 + len(placebo)))


def placebo(z: pd.Series, controls: pd.DataFrame, y: pd.Series, outcome: str, sign: int, draws: int) -> dict:
    """Empirical p of the real Clark-West t and the claim-signed holdout t against placebo z series."""
    k = w.horizon(outcome)
    d = design(z, controls, y, k)
    race, zr = CWRace(d, k), d["z"].to_numpy()
    real_cw = race.run(zr)["cw_t"]
    real_ht = sign * holdout_t_nw(d, k, zr)[1]

    def stats(zp):
        return race.run(zp)["cw_t"], sign * holdout_t_nw(d, k, zp)[1]

    shifts = circular_shifts(len(zr))
    sh = np.array([stats(np.roll(zr, s)) for s in shifts])
    rng = np.random.default_rng(SEED)
    bs = np.array([stats(zr[stationary_bootstrap_index(len(zr), MEAN_BLOCK, rng)]) for _ in range(draws)])
    out = {"n_quarters": int(len(zr)), "real_cw_t": real_cw, "real_hold_t_claimed": real_ht}
    for name, arr in (("circular", sh), ("bootstrap", bs)):
        out[name] = {"n": int(len(arr)), "p_cw": empirical_p(real_cw, arr[:, 0]),
                     "p_hold_t": empirical_p(real_ht, arr[:, 1]),
                     "q95_cw_t": float(np.nanquantile(arr[:, 0], 0.95)),
                     "q95_hold_t": float(np.nanquantile(arr[:, 1], 0.95))}
    return out


# ---------------------------------------------------------------------------
# Check a, full rule: the 92-test family under a joint resample of the macro frame
# ---------------------------------------------------------------------------


def nw_cov(X: np.ndarray, u: np.ndarray, L: int) -> np.ndarray:
    """Newey-West covariance of OLS b as statsmodels HAC (maxlags L, Bartlett 1 - j/(L+1), no small-sample factor)."""
    v = X * u[:, None]
    S = v.T @ v
    for j in range(1, L + 1):
        g = v[j:].T @ v[:-j]
        S += (1 - j / (L + 1)) * (g + g.T)
    A = np.linalg.inv(X.T @ X)
    return A @ S @ A


class FastTest:
    """One study test (wt_tests.run_outcome) on a fixed quarter grid, in numpy, for placebo draws of the macro frame.

    The outcome y stays fixed. Each call takes the signal z and the controls C on the grid. It returns the holdout b
    and Newey-West t, the Clark-West t and p, the cycle means, and the pass rule. Training sets of the forecast race
    are prefixes of the complete rows, so cumulative X'X gives every fit.
    """

    def __init__(self, y: pd.Series, grid: pd.PeriodIndex, k: int, sign: int):
        yg = y.reindex(grid)
        self.y, self.ylag = yg.to_numpy(float), yg.shift(k).to_numpy(float)
        yd = y.dropna()
        self.yc = (yg - w.cycle_centre(yd, k).reindex(grid)).to_numpy(float) if len(yd) else np.full(len(grid), np.nan)
        self.ords, self.k, self.sign = grid.asi8, k, sign
        self.h0 = w.HOLDOUT_START.ordinal
        self.win = {c: (self.ords >= pd.Period(a, "Q").ordinal) & (self.ords <= pd.Period(b, "Q").ordinal)
                    for c, (a, b) in CYCLE_WINDOWS.items()}

    @staticmethod
    def _prefix_fits(X: np.ndarray, Y: np.ndarray, n_tr: np.ndarray, rows: np.ndarray) -> np.ndarray:
        """Forecast at rows[i] from OLS on the first n_tr[i] rows."""
        XtX = np.cumsum(X[:, :, None] * X[:, None, :], axis=0)
        Xty = np.cumsum(X * Y[:, None], axis=0)
        b = np.linalg.solve(XtX[n_tr - 1], Xty[n_tr - 1][..., None])[..., 0]
        return np.einsum("ij,ij->i", X[rows], b)

    def run(self, z: np.ndarray, C: np.ndarray) -> dict:
        m = np.isfinite(self.y) & np.isfinite(z) & np.isfinite(C).all(1) & np.isfinite(self.ylag)
        Y, o = self.y[m], self.ords[m]
        X = np.column_stack([np.ones(m.sum()), z[m], C[m], self.ylag[m]])
        hb = ht = np.nan
        h = o >= self.h0
        if h.sum() >= 20:
            Xh, Yh = X[h], Y[h]
            b = np.linalg.solve(Xh.T @ Xh, Xh.T @ Yh)
            V = nw_cov(Xh, Yh - Xh @ b, self.k)
            hb, ht = b[1], b[1] / np.sqrt(V[1, 1])
        cw_t = cw_p = np.nan
        rows = np.flatnonzero(h)
        n_tr = np.searchsorted(o, o[rows] - self.k, side="right")
        keep = n_tr >= 24
        rows, n_tr = rows[keep], n_tr[keep]
        if len(rows) >= 12:
            Xb = np.delete(X, 1, axis=1)
            yb, yf = self._prefix_fits(Xb, Y, n_tr, rows), self._prefix_fits(X, Y, n_tr, rows)
            yo = Y[rows]
            f = (yo - yb) ** 2 - ((yo - yf) ** 2 - (yb - yf) ** 2)
            one = np.ones((len(f), 1))
            V = nw_cov(one, f - f.mean(), self.k)
            cw_t = f.mean() / np.sqrt(V[0, 0])
            cw_p = 1 - norm.cdf(cw_t)
        zc = z * self.yc
        ok = np.isfinite(zc)
        cyc = {c: (float(np.mean(self.sign * zc[s & ok])) if (s & ok).any() else np.nan) for c, s in self.win.items()}
        sign_ok = bool(np.isfinite(hb) and np.sign(hb) == self.sign)
        n_cyc = sum(v > 0 for v in cyc.values() if np.isfinite(v))
        n_post = sum(cyc[c] > 0 for c in POST_WINDOWS if np.isfinite(cyc[c]))
        passed = sign_ok and np.isfinite(cw_p) and cw_p < w.holm_threshold() and n_cyc >= 3 and n_post >= 2
        return {"hold_b": float(hb), "hold_t": float(ht), "hold_t_claimed": float(self.sign * ht),
                "cw_t": float(cw_t), "cw_p": float(cw_p), "cycles": cyc, "pass": bool(passed)}


def family(outcomes: dict, info: pd.DataFrame, hl: pd.DataFrame) -> list[dict]:
    """Every A, A high-leverage, and B test of wt_tests.run_claim: claim, label, group series, horizon, sign, signal."""
    out = []
    for cid, spec in w.CLAIMS.items():
        sig = spec["signal"]
        for group, oname, sign in spec["tests"]:
            rows = w.group_members(info, group)
            for pnl, cell in (("A", None), ("A_high_leverage", hl)):
                out.append({"claim": cid, "panel": pnl, "label": group, "outcome": oname, "sign": sign, "signal": sig,
                            "y": w.group_mean(outcomes[oname], rows, cell)})
        for target, comp, oname, sign in spec["relative"]:
            t_rows = w.group_members(info, target)
            c_rows = ~t_rows if comp == "rest" else w.group_members(info, comp)
            out.append({"claim": cid, "panel": "B", "label": f"{target} minus {comp}", "outcome": oname, "sign": sign,
                        "signal": sig, "y": w.group_mean(outcomes[oname], t_rows) - w.group_mean(outcomes[oname], c_rows)})
    return out


def macro_frame(macro: pd.DataFrame, grid: pd.PeriodIndex) -> pd.DataFrame:
    """One row per quarter: every claim signal z (column 'name|transform') and the raw controls. A placebo draw
    moves whole rows, so the signals and controls keep their joint law and their relation to each other."""
    cols = {f"{n}|{t}": w.make_signal(macro, n, t) for n, t in {s["signal"] for s in w.CLAIMS.values()}}
    cols.update({c: macro[c] for c in w.CONTROL_COLS})
    return pd.DataFrame(cols).reindex(grid)


def family_draws(tests: list[dict], M: pd.DataFrame, draws: int) -> dict:
    """Run every test on the real frame, on all joint circular shifts, and on `draws` joint stationary-bootstrap
    resamples (arch StationaryBootstrap, mean block MEAN_BLOCK). Returns statistic arrays of shape (draws, tests)."""
    from arch.bootstrap import StationaryBootstrap

    grid, A = M.index, M.to_numpy(float)
    col = {c: i for i, c in enumerate(M.columns)}
    fts, zi, ci = [], [], []
    for t in tests:
        n, tf = t["signal"]
        fts.append(FastTest(t["y"], grid, w.horizon(t["outcome"]), t["sign"]))
        zi.append(col[f"{n}|{tf}"])
        ci.append([col[c] for c in w.CONTROL_COLS if c != n])

    def run_all(Ab):
        return [ft.run(Ab[:, z], Ab[:, c]) for ft, z, c in zip(fts, zi, ci)]

    real = run_all(A)
    keys = ("cw_t", "hold_t_claimed", "pass")
    out = {"real": real}
    shifts = circular_shifts(len(A))
    bs = StationaryBootstrap(MEAN_BLOCK, np.arange(len(A)), seed=SEED)
    idx_bs = []
    for _ in bs.bootstrap(draws):
        idx_bs.append(bs.index.copy())
    for name, idxs in (("circular", [np.roll(np.arange(len(A)), s) for s in shifts]), ("bootstrap", idx_bs)):
        res = [run_all(A[ix]) for ix in idxs]
        out[name] = {k: np.array([[r[k] for r in rr] for rr in res], dtype=float) for k in keys}
    return out


def romano_wolf(t_obs: np.ndarray, t_null: np.ndarray) -> np.ndarray:
    """Romano-Wolf (2005) stepdown p-values for one-sided statistics. t_null holds draws under the null (draws x
    tests). Step j compares t_obs of the j-th largest test with the max of the null draws over the tests not yet
    rejected. Monotone by construction. NaN statistics count as minus infinity."""
    t_obs = np.where(np.isfinite(t_obs), t_obs, -np.inf)
    t_null = np.where(np.isfinite(t_null), t_null, -np.inf)
    order = np.argsort(-t_obs)
    p = np.empty(len(t_obs))
    prev = 0.0
    for i, j in enumerate(order):
        mx = t_null[:, order[i:]].max(axis=1)
        pj = (1 + np.sum(mx >= t_obs[j])) / (1 + len(mx))
        prev = max(prev, pj)
        p[j] = prev
    return p


def fdr_q(p: np.ndarray, method: str) -> np.ndarray:
    """Benjamini-Hochberg ('fdr_bh') or Benjamini-Yekutieli ('fdr_by') q-values; NaN p stays NaN."""
    from statsmodels.stats.multitest import multipletests

    q = np.full(len(p), np.nan)
    ok = np.isfinite(p)
    if ok.any():
        q[ok] = multipletests(p[ok], method=method)[1]
    return q


def family_report(tests: list[dict], fd: dict, old: dict) -> dict:
    """False-pass rate of the pass rule under the null, placebo p per test, Romano-Wolf, BH and BY."""
    real = fd["real"]
    t_obs = np.array([r["cw_t"] for r in real])
    h_obs = np.array([r["hold_t_claimed"] for r in real])
    p_cw = np.array([r["cw_p"] for r in real])
    rep = {"n_tests": len(tests)}
    for name in ("circular", "bootstrap"):
        P, T, H = fd[name]["pass"], fd[name]["cw_t"], fd[name]["hold_t_claimed"]
        rep[name] = {"n_draws": int(P.shape[0]), "false_pass_rate_per_test": float(P.mean()),
                     "share_draws_with_any_pass": float((P.sum(1) > 0).mean()),
                     "mean_passes_per_draw": float(P.sum(1).mean()),
                     "real_passes": int(sum(r["pass"] for r in real)),
                     "share_draws_with_at_least_real_passes": float(
                         (P.sum(1) >= sum(r["pass"] for r in real)).mean())}
    Tb = fd["bootstrap"]["cw_t"]
    rw_b, rw_c = romano_wolf(t_obs, Tb), romano_wolf(t_obs, fd["circular"]["cw_t"])
    p_pl = np.array([empirical_p(t_obs[i], Tb[:, i]) if np.isfinite(t_obs[i]) else np.nan for i in range(len(tests))])
    q = {"bh_cw_p": fdr_q(p_cw, "fdr_bh"), "by_cw_p": fdr_q(p_cw, "fdr_by"),
         "bh_placebo_p": fdr_q(p_pl, "fdr_bh"), "by_placebo_p": fdr_q(p_pl, "fdr_by")}
    rows = []
    for i, (t, r) in enumerate(zip(tests, real)):
        key = (t["claim"], t["panel"], t["label"], t["outcome"])
        rows.append({"claim": t["claim"], "panel": t["panel"], "label": t["label"], "outcome": t["outcome"],
                     "sign": t["sign"], "cw_t": r["cw_t"], "cw_p": r["cw_p"], "hold_t": r["hold_t"],
                     "pass": r["pass"], "pass_old_cycle_rule": old.get(key, {}).get("pass"),
                     "hold_t_old_json": old.get(key, {}).get("hold_t"), "cw_p_old_json": old.get(key, {}).get("cw_p"),
                     "cycles": r["cycles"],
                     **{f"placebo_{name}": {"p_cw": empirical_p(t_obs[i], fd[name]["cw_t"][:, i]),
                                            "p_hold_t": empirical_p(h_obs[i], fd[name]["hold_t_claimed"][:, i]),
                                            "p_pass_under_null": float(fd[name]["pass"][:, i].mean())}
                        for name in ("circular", "bootstrap")},
                     "romano_wolf_p_bootstrap": float(rw_b[i]), "romano_wolf_p_circular": float(rw_c[i]),
                     **{k: float(v[i]) for k, v in q.items()}})
    rep["tests"] = rows
    return rep


def old_family(path: Path) -> dict:
    """Pass flag, holdout t and Clark-West p of each test in the study JSON (old cycle rule)."""
    out = {}
    for f in sorted(path.glob("wt_firm_*.json")):
        r = json.loads(f.read_text())
        for pnl in ("A", "A_high_leverage", "B"):
            for o in r[pnl]:
                lab = o["group"] if pnl != "B" else f"{o['target']} minus {o['comparison']}"
                out[(r["claim"], pnl, lab, o["outcome"])] = {"pass": o["pass"], "cw_p": o["clark_west"]["p"],
                                                            "hold_t": o["regression"]["holdout"]["t"]}
    return out


# ---------------------------------------------------------------------------
# Data and drivers
# ---------------------------------------------------------------------------


def signal_for(macro: pd.DataFrame, claim: str, transform: str | None = None) -> tuple[pd.Series, pd.DataFrame]:
    """The claim's z and the controls, as wt_tests.run_claim builds them. transform overrides the claimed one."""
    name, t0 = w.CLAIMS[claim]["signal"]
    z = w.make_signal(macro, name, transform or t0)
    return z, macro[[c for c in w.CONTROL_COLS if c != name]]


def panel(W40: dict, min_sales: float, winsor: float, decline: float) -> tuple[dict, dict]:
    """Firm matrices above `min_sales` and their outcomes with the given winsor level and decline threshold."""
    W = {k: v.where(W40["S"] > min_sales) for k, v in W40.items()}
    with patched(w, DECLINE=decline, _winsor=functools.partial(_WINSOR, p=winsor)):
        out = w.firm_outcomes(W)
    return W, out


def high_leverage(W: dict, cut: float) -> pd.DataFrame:
    with patched(w, HL_LEVERAGE=cut):
        return w.high_leverage(W)


def historical_members(gh: pd.DataFrame, quarters: pd.PeriodIndex, firms: pd.Index, info: pd.DataFrame,
                       codes: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Firm x quarter membership of a GICS sector group from the history table at each quarter end.

    A row counts at quarter end e when indfrom <= e <= indthru (open end = still valid) and available_at <= e.
    Where no row covers (firm or date outside the table), the current code fills in. Returns (members, covered).
    """
    qend = np.array([q.end_time.normalize() for q in quarters], dtype="datetime64[ns]")
    g = gh[gh["gvkey"].isin(firms)].sort_values("indfrom")
    pos = {f: i for i, f in enumerate(firms)}
    H = np.full((len(firms), len(quarters)), None, dtype=object)
    for r in g.itertuples(index=False):
        thru = np.datetime64(r.indthru) if pd.notna(r.indthru) else np.datetime64("2262-01-01")
        m = (qend >= np.datetime64(r.indfrom)) & (qend <= thru) & (qend >= np.datetime64(r.available_at))
        H[pos[r.gvkey], m] = r.gsector
    hist = pd.DataFrame(H, index=firms, columns=quarters)
    covered = hist.notna()
    cur = info["gsector"].reindex(firms)
    filled = hist.where(covered, pd.DataFrame(np.repeat(cur.to_numpy()[:, None], len(quarters), 1),
                                              index=firms, columns=quarters))
    return filled.isin(codes), covered


def run(draws: int = 1000, results: list | None = None) -> dict:
    t0 = time.time()
    macro = w.build_macro(ROOT / "data/raw/macro")
    W40, info = w.firm_matrices(pd.read_parquet(ROOT / "data/raw/compustat/fundq_nonfin.parquet"))
    gh = pd.read_parquet(ROOT / "data/raw/backtest/gics_history.parquet")
    results = results or RESULTS
    print(f"loaded in {time.time() - t0:.0f}s")

    W, out = panel(W40, 40.0, 0.01, 0.20)
    hl = high_leverage(W, 4.0)
    rep = {"meta": {"seed": SEED, "draws": draws, "min_shift": MIN_SHIFT, "mean_block": MEAN_BLOCK,
                    "holm_threshold": w.holm_threshold(), "holdout_start": str(w.HOLDOUT_START),
                    "spec_grid": {"hl_cut": SPEC_HL, "min_sales": SPEC_SALES, "winsor": SPEC_WINSOR,
                                  "transform": "claimed and the other of level/change2", "weight": SPEC_WEIGHT,
                                  "decline": SPEC_DECLINE}},
           "results": {}}

    # Historical GICS membership for the sector groups.
    quarters, firms = W["S"].columns, W["S"].index
    hist = {}
    for g in {r[3] for r in results if w.GROUPS[r[3]][0] == "gsector"}:
        hist[g] = historical_members(gh, quarters, firms, info, w.GROUPS[g][1])

    for rid, claim, pnl, group, oname in results:
        ts = time.time()
        sign = claimed_sign(claim, group, oname)
        z, ctr = signal_for(macro, claim)
        rows = w.group_members(info, group)
        cell = hl if pnl == "hl" else None
        y = group_series(out[oname], rows, cell)
        base = evaluate(z, ctr, y, oname, sign, with_har=True)
        r = {"claim": claim, "panel": pnl, "group": group, "outcome": oname, "sign": sign, "baseline": base}
        r["placebo"] = placebo(z, ctr, y, oname, sign, draws)
        r["leave_one_out"] = {str(c): evaluate(z, ctr, y, oname, sign, drop_window=c) for c in CYCLE_WINDOWS}
        if group in hist:
            mem, cov = hist[group]
            cur = pd.DataFrame(np.repeat(rows.reindex(firms, fill_value=False).to_numpy()[:, None], len(quarters), 1),
                               index=firms, columns=quarters)
            live = out[oname].notna() & (hl if cell is not None else True)
            either = live & (mem | cur)
            r["historical_gics"] = {
                **evaluate(z, ctr, group_series(out[oname], mem, cell), oname, sign),
                "firm_quarters_current": int((live & cur).sum().sum()),
                "firm_quarters_historical": int((live & mem).sum().sum()),
                "firm_quarters_moved": int((live & (mem != cur)).sum().sum()),
                "share_with_history": float((either & cov).sum().sum() / either.sum().sum()),
            }
        rep["results"][rid] = r
        print(f"{rid} {claim} {pnl} {group} {oname}: base CW p {base['cw_p']:.4f} hold t {base['hold_t']:+.2f} | "
              f"placebo p circ {r['placebo']['circular']['p_cw']:.3f} boot {r['placebo']['bootstrap']['p_cw']:.3f} "
              f"| {time.time() - ts:.0f}s")

    # Check a, full rule: the whole family under joint resamples of the macro frame; multiple testing.
    ts = time.time()
    tests = family(out, info, hl)
    fd = family_draws(tests, macro_frame(macro, W["S"].columns), draws)
    fam = family_report(tests, fd, old_family(ROOT / "data/raw/backtest"))
    dt = [abs(r["hold_t"] - r["hold_t_old_json"]) for r in fam["tests"] if r["hold_t_old_json"] is not None]
    dp = [abs(r["cw_p"] - r["cw_p_old_json"]) for r in fam["tests"] if r["cw_p_old_json"] is not None]
    fam["check_against_study_json"] = {"n_matched": len(dt), "max_abs_diff_hold_t": float(max(dt)),
                                       "max_abs_diff_cw_p": float(max(dp))}
    fam["pass_flag_changes_from_cycle_fix"] = [
        {k: r[k] for k in ("claim", "panel", "label", "outcome", "pass_old_cycle_rule", "pass")}
        for r in fam["tests"] if r["pass_old_cycle_rule"] is not None and r["pass_old_cycle_rule"] != r["pass"]]
    rep["family"] = fam
    by_key = {(r["claim"], r["panel"], r["label"], r["outcome"]): r for r in fam["tests"]}
    for rid, claim, pnl, group, oname in results:
        rep["results"][rid]["family_row"] = by_key[(claim, "A_high_leverage" if pnl == "hl" else "A", group, oname)]
    print(f"family: {len(tests)} tests, {time.time() - ts:.0f}s; max diff vs study JSON: hold t "
          f"{fam['check_against_study_json']['max_abs_diff_hold_t']:.2e}, CW p {fam['check_against_study_json']['max_abs_diff_cw_p']:.2e}")

    # Check c: specification curve. Outer loop over panels so that only one outcome set sits in memory.
    specs = {rid: [] for rid, *_ in results}
    is_dec = lambda o: o.startswith("decline")  # noqa: E731
    for ms, wz, dc in itertools.product(SPEC_SALES, SPEC_WINSOR, SPEC_DECLINE):
        need = [r for r in results if (is_dec(r[4]) and wz == SPEC_WINSOR[0]) or (not is_dec(r[4]) and dc == SPEC_DECLINE[0])]
        if not need:
            continue
        Wp, op = panel(W40, ms, wz, dc)
        hls = {c: high_leverage(Wp, c) for c in SPEC_HL}
        for rid, claim, pnl, group, oname in need:
            sign = claimed_sign(claim, group, oname)
            rows = w.group_members(info, group)
            t_claim = w.CLAIMS[claim]["signal"][1]
            transforms = [t_claim, "change2" if t_claim in ("level", "raw") else "level"]
            for cut, tf, wt in itertools.product(SPEC_HL if pnl == "hl" else (None,), transforms, SPEC_WEIGHT):
                z, ctr = signal_for(macro, claim, tf)
                y = group_series(op[oname], rows, hls[cut] if cut else None, Wp["S"] if wt == "sales" else None)
                e = evaluate(z, ctr, y, oname, sign)
                specs[rid].append({"hl_cut": cut, "min_sales": ms, "winsor": None if is_dec(oname) else wz,
                                   "decline": dc if is_dec(oname) else None, "transform": tf, "weight": wt,
                                   **{k: e[k] for k in ("n", "hold_b", "hold_t", "sign_ok", "cw_t", "cw_p",
                                                        "cycles_as_claimed", "post_as_claimed", "pass")}})
        del op, Wp, hls
    for rid, rows_ in specs.items():
        df = pd.DataFrame(rows_)
        strong = df["sign_ok"] & (df["hold_t"].abs() > 2) & (df["cw_p"] < 0.05)
        rep["results"][rid]["spec_curve"] = {
            "n_specs": int(len(df)), "share_sign": float(df["sign_ok"].mean()),
            "share_t_gt_2": float((df["sign_ok"] & (df["hold_t"].abs() > 2)).mean()),
            "share_cw_p_lt_05": float((df["cw_p"] < 0.05).mean()),
            "share_t2_and_cw05": float(strong.mean()), "share_pass": float(df["pass"].mean()),
            "share_t2_and_cw05_claimed_transform": float(strong[df["transform"] == df["transform"].iloc[0]].mean()),
            "specs": rows_}
    rep["meta"]["runtime_s"] = round(time.time() - t0, 1)
    return rep


def verdict(r: dict) -> str:
    """robust: placebo p < 0.05 both ways, passes or keeps CW p < 0.05 without any one window, spec share >= 0.5,
    EWC |t| above its 5% cv. fails: placebo p >= 0.10 on CW and on the holdout t, or spec share < 0.2.
    fragile: anything else."""
    pl, sc, har = r["placebo"], r["spec_curve"], r["baseline"]["har"]
    p_pl = max(pl["circular"]["p_cw"], pl["bootstrap"]["p_cw"])
    p_ht = max(pl["circular"]["p_hold_t"], pl["bootstrap"]["p_hold_t"])
    loo_ok = all(v["sign_ok"] and v["cw_p"] < 0.05 for v in r["leave_one_out"].values())
    ewc_ok = r["sign"] * har["t_ewc"] > har["cv_ewc_5pct"]
    if p_pl < 0.05 and p_ht < 0.05 and loo_ok and sc["share_t2_and_cw05"] >= 0.5 and ewc_ok:
        return "robust"
    if (p_pl >= 0.10 and p_ht >= 0.10) or sc["share_t2_and_cw05"] < 0.2:
        return "fails"
    return "fragile"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--draws", type=int, default=1000)
    ap.add_argument("--out", default=str(ROOT / "data/raw/backtest/wt_robustness.json"))
    a = ap.parse_args()
    rep = run(a.draws)
    for rid, r in rep["results"].items():
        r["verdict"] = verdict(r)
        loo = r["leave_one_out"]
        carry = max(loo, key=lambda c: (loo[c]["cw_p"] if np.isfinite(loo[c]["cw_p"]) else 1.0))
        r["most_influential_window"] = carry
        breaks = not (loo[carry]["sign_ok"] and loo[carry]["cw_p"] < 0.05)
        r["window_that_carries"] = carry if breaks else None  # None: no single window removal breaks the result
        h, sc, pl, fr = r["baseline"]["har"], r["spec_curve"], r["placebo"], r["family_row"]
        jb = fr["placebo_bootstrap"]
        print(f"{rid} {r['claim']} {r['panel']:3s} {r['group'][:22]:22s} {r['outcome']:10s} {r['verdict']:7s} | "
              f"z-only placebo CW p {pl['circular']['p_cw']:.3f}/{pl['bootstrap']['p_cw']:.3f} | joint CW p "
              f"{jb['p_cw']:.3f} P(pass|null) {jb['p_pass_under_null']:.3f} RW {fr['romano_wolf_p_bootstrap']:.3f} "
              f"BH {fr['bh_cw_p']:.3f} BY {fr['by_cw_p']:.3f} | spec {sc['share_t2_and_cw05']:.2f} | t NW "
              f"{h['t_nw_study']:+.2f} EWC {h['t_ewc']:+.2f} (nu {h['ewc_nu']}) | CW t EWC {h.get('cw_t_ewc', np.nan):+.2f} "
              f"bar {h.get('cw_holm_cv_ewc', np.nan):.2f} | without {carry}: CW p {loo[carry]['cw_p']:.3f} "
              f"{'BREAKS' if r['window_that_carries'] else 'holds'} | pass {fr['pass_old_cycle_rule']}->{fr['pass']}")
    f = rep["family"]
    for name in ("circular", "bootstrap"):
        print(f"family {name}: {f[name]}")
    print(f"pass flags changed by the cycle fix: {f['pass_flag_changes_from_cycle_fix']}")
    Path(a.out).write_text(json.dumps(rep, indent=1, default=w._json_default))
    print(f"wrote {a.out} ({rep['meta']['runtime_s']}s)")


if __name__ == "__main__":
    main()
