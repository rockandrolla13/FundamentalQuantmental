"""Backtest of the expected alpha forecast (methodology Sections 7.5 and 11; writeup `rv_pairs.tex`, last section).

One question: when the model predicts 100 bp of alpha, does the bond earn about 100 bp more than its hedge?

Inputs are plain frames. The panel (`hy.sources.trace_panel`) has one row per bond and month end `date`, with
`available_at`. The fundamentals history has one row per issuer and month end with leverage as known at that
month's decision time. The decision time for month end t is t + 1 day (`decision_time`).

Conventions: spreads, yields, and returns in decimals; durations in years; horizons `h` in months.

Assumptions, each stated where it acts:
1. Realised alpha (Section 7.5 hedge): bond total return minus the duration-matched Treasury total return minus
   beta times the high yield benchmark's spread return. beta = 1 by default.
2. Spread duration = modified duration of a bullet at the bond's yield (`rv.modified_duration`); calls ignored.
3. Round-trip cost = the bid-ask proxy in price points over the price (`trace_panel` rule 4): buy at the ask, sell
   at the bid, one full spread.
4. No PD is available in the panel, so the default-loss term of Section 7.5 is off (flagged `loss_term = False`).

Every function that reads inputs takes `as_of` and refuses any row with `available_at > as_of` (`LookAheadError`).
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy import stats

from hy import rv
from hy.fairspread import fit_ar1
from hy.signals import CYCLES, passes_cycle_test, rank_ic

DEFAULT_BETA = 1.0
TENOR = 5.0                       # reference tenor of the fair line (years)
RHO_PRIOR_M = 0.85 ** (1 / 3)     # monthly form of the Section 7.5 default (quarterly 0.85)
MIN_RHO_PAIRS = 3000              # residual pairs (about six months of issuers) before the fitted rho replaces the prior
FLAT_PRICE = 50.0                 # below this price a bond trades flat: no coupon accrual
MIN_BONDS = 20                    # fewest bonds on a date for an IC or a decile sort
# Stress windows of the CLAUDE.md cycle test, by formation month (inclusive).
CYCLE_WINDOWS: dict[int, tuple[str, str]] = {
    2008: ("2008-01-01", "2009-12-31"),
    2015: ("2015-01-01", "2016-12-31"),
    2020: ("2020-01-01", "2020-12-31"),
    2022: ("2022-01-01", "2022-12-31"),
}


class LookAheadError(AssertionError):
    """An input row became available after the decision time."""


def decision_time(month_end: pd.Timestamp) -> pd.Timestamp:
    """Decision time for month end t: t + 1 day, when the last trade, the curve, and the snapshot are all loaded."""
    return pd.Timestamp(month_end) + pd.Timedelta(1, unit="D")


def assert_no_lookahead(df: pd.DataFrame, as_of: pd.Timestamp, what: str = "input", col: str = "available_at") -> None:
    """Raise `LookAheadError` when any row of `df` has `col` after `as_of`. A frame without the column fails too."""
    if df is None or len(df) == 0:
        return
    if col not in df:
        raise LookAheadError(f"{what} has no {col} column; cannot prove it is point in time")
    late = pd.to_datetime(df[col]) > pd.Timestamp(as_of)
    if late.any():
        first = pd.to_datetime(df.loc[late, col]).min()
        raise LookAheadError(f"{what}: {int(late.sum())} rows available after {pd.Timestamp(as_of)} (first {first})")


# ---------------------------------------------------------------- universe and benchmark


def eligible(panel: pd.DataFrame) -> pd.Series:
    """Rows a predictor may score: a real trade (not carried), 1 to 30 years left, yield in (0, 100%], price in
    [5, 200], positive G-spread, finite duration. The bounds remove print errors, not distressed bonds."""
    return (
        ~panel["carried"].astype(bool)
        & panel["years"].between(1.0, 30.0)
        & (panel["yield"] > 0) & (panel["yield"] <= 1.0)
        & panel["price"].between(5.0, 200.0)
        & (panel["g_spread"] > 0)
        & np.isfinite(panel["mod_dur"].astype(float))
    )


def benchmark_spread(panel: pd.DataFrame, as_of: pd.Timestamp) -> pd.Series:
    """High yield benchmark per month end: median G-spread of eligible bonds with price >= 80, 1 to 15 years, yield
    <= 25% (the `trace_bonds.benchmark_by_bucket` filters, one bucket). Section 3.6 `hy_oas` proxy."""
    assert_no_lookahead(panel, as_of, "panel")
    p = panel[eligible(panel) & (panel["price"] >= 80) & (panel["years"] <= 15) & (panel["yield"] <= 0.25)]
    return p.groupby("date")["g_spread"].median().rename("bench_spread")


def round_trip_cost(panel: pd.DataFrame) -> pd.Series:
    """Assumption 3: bid_ask_pts / price; a missing proxy takes the month's median cost. Decimal of price."""
    c = panel["bid_ask_pts"].astype(float) / panel["price"].astype(float)
    med = c.groupby(panel["date"]).transform("median")
    return c.fillna(med).clip(lower=0.0, upper=0.2).rename("cost_rt")


# ---------------------------------------------------------------- realised excess return


def realised_excess_return(
    panel: pd.DataFrame, h_months: int, as_of: pd.Timestamp, beta: float = DEFAULT_BETA,
    bench: pd.Series | None = None, flat_price: float = FLAT_PRICE,
) -> pd.DataFrame:
    """Realised alpha of each eligible (bond, month t) over the next `h_months` (Section 7.5 hedge; Section 11).

    total   = (P_end - P_t + 100 c tau_acc) / P_t                      clean price change plus coupon accrual
    tsy     = y_T,t tau - D (y_T,end - y_T,t)                         duration-matched Treasury total return
    hedge   = beta (S_t tau - D (S_end - S_t))                        high yield benchmark spread return
    alpha   = total - tsy - hedge  ~=  (s - beta S) tau - D (ds - beta dS)

    The end row is the bond's latest row in (t, t + h]. A bond that stops trading inside h ends at its last price:
    its carried exit row (`trace_panel` rule 5) stops accrual at the last trade and the hedge at the last trade
    month. A bond with no later row (only at the panel end) has NaN. tau is the hedge period in years. No coupon
    accrues when the start or end price is below `flat_price` (the bond trades flat).
    Intuition: what a long bond, short matched Treasury, short beta of the market's spread, actually earned.
    """
    assert_no_lookahead(panel, as_of, "panel")
    if bench is None:
        bench = benchmark_spread(panel, as_of)
    p = panel.copy()
    start = p[eligible(p)][["cusip", "date", "price", "coupon", "tsy_yield", "mod_dur", "g_spread"]].copy()
    cols = ["cusip", "date", "price", "tsy_yield", "accrue_to", "hedge_date", "carried"]
    end = None
    for k in range(int(h_months), 0, -1):
        cand = start[["cusip", "date"]].copy()
        cand["end_date"] = cand["date"] + pd.offsets.MonthEnd(k)
        hit = cand.merge(p[cols].rename(columns={"date": "end_date"}), on=["cusip", "end_date"], how="left",
                         suffixes=("", "_end"))
        hit.index = start.index
        end = hit if end is None else end.where(end["price"].notna(), hit)
    out = start.copy()
    out["end_date"] = end["end_date"].where(end["price"].notna())
    out["price_end"] = end["price"]
    out["tsy_end"] = end["tsy_yield"]
    out["end_carried"] = end["carried"].fillna(False).astype(bool)
    hedge_end = pd.to_datetime(end["hedge_date"])
    tau = (hedge_end - out["date"]).dt.days / 365.25
    tau_acc = ((pd.to_datetime(end["accrue_to"]) - out["date"]).dt.days / 365.25).clip(lower=0.0)
    flat = (out["price"] < flat_price) | (out["price_end"] < flat_price)
    accrual = np.where(flat, 0.0, 100.0 * out["coupon"] * tau_acc)
    out["total"] = (out["price_end"] - out["price"] + accrual) / out["price"]
    out["tsy_ret"] = out["tsy_yield"] * tau - out["mod_dur"] * (out["tsy_end"] - out["tsy_yield"])
    s_t = out["date"].map(bench)
    s_end = hedge_end.map(bench)
    out["bench_ret"] = beta * (s_t * tau - out["mod_dur"] * (s_end - s_t))
    out["realised"] = out["total"] - out["tsy_ret"] - out["bench_ret"]
    out["h_eff_months"] = ((hedge_end.dt.year - out["date"].dt.year) * 12 + hedge_end.dt.month - out["date"].dt.month)
    return out[["cusip", "date", "end_date", "end_carried", "h_eff_months", "total", "tsy_ret", "bench_ret", "realised"]]


# ---------------------------------------------------------------- predictors


Predictor = Callable[[pd.DataFrame, pd.DataFrame, pd.Timestamp, int], pd.Series]


def _rows_at(panel_up_to_t: pd.DataFrame, as_of: pd.Timestamp) -> pd.DataFrame:
    """The eligible rows of the latest month end in the panel; the guard runs first."""
    assert_no_lookahead(panel_up_to_t, as_of, "panel")
    t = panel_up_to_t["date"].max()
    p = panel_up_to_t[panel_up_to_t["date"] == t]
    return p[eligible(p)]


def predict_widest(panel_up_to_t: pd.DataFrame, fundamentals_up_to_t: pd.DataFrame, as_of: pd.Timestamp,
                   h_months: int) -> pd.Series:
    """Benchmark rule `widest`: alpha_hat = G-spread level. Intuition: buy the bonds that pay the most."""
    assert_no_lookahead(fundamentals_up_to_t, as_of, "fundamentals")
    p = _rows_at(panel_up_to_t, as_of)
    return pd.Series(p["g_spread"].to_numpy(), index=p["cusip"].to_numpy(), name="widest")


def issuer_spreads(rows: pd.DataFrame, tenor: float = TENOR) -> pd.Series:
    """Issuer spread at `tenor` from its bonds' G-spread curve (`rv.curve_fit`), read inside the issuer's maturity range.

    Reading at the nearest end of the range, not beyond it, keeps short-only issuers from wild extrapolation.
    """
    out = {}
    for g, b in rows.groupby("gvkey"):
        fit = rv.curve_fit(b["years"].to_numpy(), b["g_spread"].to_numpy())
        tt = float(np.clip(tenor, b["years"].min(), b["years"].max()))
        out[g] = rv.curve_at(fit, tt)
    return pd.Series(out, name="s5", dtype=float)


def fair_line_residuals(rows: pd.DataFrame, fundamentals_t: pd.DataFrame, tenor: float = TENOR) -> tuple[pd.Series, dict]:
    """Section 7.2 cross-section at one month: OLS log s_5y = a + b leverage across issuers; residual per issuer.

    Only issuers with a positive 5-year spread and a leverage at t enter. Returns the residual (log) by gvkey and
    the fit {a, b, n}. A positive residual means the issuer pays more than its leverage says: cheap.
    """
    s5 = issuer_spreads(rows, tenor)
    lev = fundamentals_t.drop_duplicates("gvkey", keep="last").set_index("gvkey")["leverage"]
    d = pd.concat([s5, lev.rename("leverage")], axis=1, join="inner").dropna()
    d = d[d["s5"] > 0]
    if len(d) < 10:
        return pd.Series(dtype=float), {"a": np.nan, "b": np.nan, "n": len(d)}
    b, a = np.polyfit(d["leverage"].to_numpy(), np.log(d["s5"].to_numpy()), 1)
    eps = np.log(d["s5"]) - (a + b * d["leverage"])
    return eps.rename("eps"), {"a": float(a), "b": float(b), "n": int(len(d))}


def pooled_rho(history: Mapping[pd.Timestamp, pd.Series]) -> tuple[float, int]:
    """Section 7.5 persistence from past residuals: one AR(1) slope pooled across issuers (`fairspread.fit_ar1`).

    Each issuer's monthly residual series sits on the full month grid (NaN where absent); series are stacked with a
    NaN between issuers, so `fit_ar1` uses only same-issuer consecutive-month pairs. Returns (rho, pairs).
    Intuition: one speed for the whole market is noisy-free enough to use from the second year; per-issuer speeds
    are not.
    """
    if len(history) < 2:
        return float("nan"), 0
    wide = pd.DataFrame(history).T.sort_index()
    grid = pd.date_range(wide.index.min(), wide.index.max(), freq="ME")
    wide = wide.reindex(grid)
    arr = np.vstack([wide.to_numpy(dtype=float), np.full((1, wide.shape[1]), np.nan)]).T.ravel()
    x, y = arr[:-1], arr[1:]
    pairs = int((np.isfinite(x) & np.isfinite(y)).sum())
    return fit_ar1(arr), pairs


@dataclass
class FairLine:
    """Predictor family `fair_line` (Section 7.5 alpha without the macro paths and the loss term).

    mode 'conv'  : alpha_hat = D (1 - rho^h) (s - s_fair)                      convergence only
    mode 'gross' : alpha_hat = (s - beta S) h/12 + D (1 - rho^h) (s - s_fair)  carry plus convergence
    mode 'net'   : 'gross' - round-trip cost - default loss (loss off: no PD; `loss_term = False`)

    s_fair for a bond = s x exp(-eps_issuer): the issuer's log residual from the fair line moves every bond of the
    issuer by the same proportion. rho is monthly, pooled over past residuals only (expanding window); the prior
    `RHO_PRIOR_M` holds until `MIN_RHO_PAIRS` pairs exist. Residuals of each month are memoised: a month's residual
    depends only on that month's rows, so the memo cannot leak the future.
    """

    mode: str = "gross"
    beta: float = DEFAULT_BETA
    tenor: float = TENOR
    rho_prior: float = RHO_PRIOR_M
    min_pairs: int = MIN_RHO_PAIRS
    loss_term: bool = False
    memo: dict = field(default_factory=dict)
    fits: dict = field(default_factory=dict)
    rho_log: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.mode not in ("conv", "gross", "net"):
            raise ValueError(f"unknown mode {self.mode}")

    def _residuals(self, panel_up_to_t: pd.DataFrame, fund_up_to_t: pd.DataFrame, month: pd.Timestamp) -> pd.Series:
        if month not in self.memo:
            p = panel_up_to_t[panel_up_to_t["date"] == month]
            p = p[eligible(p) & p["gvkey"].notna()]
            f = fund_up_to_t[fund_up_to_t["date"] == month]
            eps, fit = fair_line_residuals(p, f, self.tenor)
            self.memo[month], self.fits[month] = eps, fit
        return self.memo[month]

    def rho(self, upto: pd.Timestamp) -> tuple[float, str]:
        hist = {m: e for m, e in self.memo.items() if m <= upto and len(e)}
        r, pairs = pooled_rho(hist)
        if pairs < self.min_pairs or not np.isfinite(r):
            return self.rho_prior, "prior"
        return float(np.clip(r, 0.0, 0.999)), "fitted"

    def __call__(self, panel_up_to_t: pd.DataFrame, fundamentals_up_to_t: pd.DataFrame, as_of: pd.Timestamp,
                 h_months: int) -> pd.Series:
        assert_no_lookahead(fundamentals_up_to_t, as_of, "fundamentals")
        rows = _rows_at(panel_up_to_t, as_of)
        t = rows["date"].max() if len(rows) else panel_up_to_t["date"].max()
        for m in sorted(set(panel_up_to_t["date"].unique()) - set(self.memo)):
            self._residuals(panel_up_to_t, fundamentals_up_to_t, m)
        eps = self._residuals(panel_up_to_t, fundamentals_up_to_t, t)
        rho, src = self.rho(t)
        self.rho_log[t] = (rho, src)
        b = rows[rows["gvkey"].isin(eps.index)].copy()
        if b.empty:
            return pd.Series(dtype=float, name=f"fair_line_{self.mode}")
        s = b["g_spread"].to_numpy()
        s_fair = s * np.exp(-b["gvkey"].map(eps).to_numpy(dtype=float))
        conv = b["mod_dur"].to_numpy() * (1.0 - rho ** h_months) * (s - s_fair)
        alpha = conv
        if self.mode in ("gross", "net"):
            bench = benchmark_spread(panel_up_to_t[panel_up_to_t["date"] == t], as_of).get(t, np.nan)
            alpha = alpha + (s - self.beta * bench) * h_months / 12.0
        if self.mode == "net":
            alpha = alpha - round_trip_cost(b).to_numpy()  # loss term off: no PD in the panel (assumption 4)
        return pd.Series(alpha, index=b["cusip"].to_numpy(), name=f"fair_line_{self.mode}")


# ---------------------------------------------------------------- the replay


def run_predictions(
    panel: pd.DataFrame, fund_hist: pd.DataFrame, predictors: Mapping[str, Predictor], h_months: int,
    months: Sequence[pd.Timestamp] | None = None, log: Callable[[str], None] | None = None,
) -> pd.DataFrame:
    """Replay month by month: at each month end t, every predictor sees only panel rows with date <= t (no carried
    rows) and fundamentals with date <= t, and must pass the look-ahead guard at `decision_time(t)`.
    Returns long rows (date, cusip, predictor, alpha_hat)."""
    real = panel[~panel["carried"].astype(bool)]
    months = sorted(real["date"].unique()) if months is None else months
    out = []
    for i, t in enumerate(months):
        t = pd.Timestamp(t)
        as_of = decision_time(t)
        p_t = real[real["date"] <= t]
        f_t = fund_hist[fund_hist["date"] <= t]
        for name, fn in predictors.items():
            a = fn(p_t, f_t, as_of, h_months)
            if len(a):
                out.append(pd.DataFrame({"date": t, "cusip": a.index, "predictor": name, "alpha_hat": a.to_numpy()}))
        if log and (i % 12 == 0):
            log(f"  predictions h={h_months}: {t:%Y-%m}")
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame(columns=["date", "cusip", "predictor", "alpha_hat"])


# ---------------------------------------------------------------- inference


def newey_west_se(x: np.ndarray, lags: int) -> float:
    """Newey-West (Bartlett) standard error of the mean of `x`, NaN dropped.

    var = (gamma_0 + 2 sum_{l=1..L} (1 - l/(L+1)) gamma_l) / T. Use L = h - 1 for overlapping h-period outcomes.
    Intuition: overlapping horizons share months, so successive observations are not independent evidence.
    """
    v = np.asarray(x, dtype=float)
    v = v[np.isfinite(v)]
    n = len(v)
    if n < 2:
        return float("nan")
    u = v - v.mean()
    s = u @ u / n
    for lag in range(1, min(int(lags), n - 1) + 1):
        s += 2.0 * (1.0 - lag / (lags + 1.0)) * (u[lag:] @ u[:-lag]) / n
    return float(np.sqrt(max(s, 0.0) / n))


def hac_mean(x: pd.Series | np.ndarray, lags: int) -> dict[str, float]:
    """Mean, Newey-West SE, t-statistic, and count of a time series (IC per month, long-short per month)."""
    v = np.asarray(x, dtype=float)
    v = v[np.isfinite(v)]
    se = newey_west_se(v, lags)
    m = float(v.mean()) if len(v) else float("nan")
    return {"mean": m, "se": se, "t": m / se if se and np.isfinite(se) and se > 0 else float("nan"), "n": int(len(v))}


def driscoll_kraay_ols(y: np.ndarray, X: np.ndarray, time: np.ndarray, lags: int) -> tuple[np.ndarray, np.ndarray]:
    """Pooled OLS with Driscoll-Kraay standard errors: Newey-West on the per-date sums of score vectors.

    Robust to cross-sectional correlation on a date and to serial correlation up to `lags` across dates (overlap).
    Returns (beta, se).
    """
    y, X = np.asarray(y, dtype=float), np.asarray(X, dtype=float)
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    u = y - X @ beta
    scores = pd.DataFrame(X * u[:, None]).groupby(np.asarray(time)).sum().sort_index().to_numpy()
    T = len(scores)
    S = scores.T @ scores
    for lag in range(1, min(int(lags), T - 1) + 1):
        g = scores[lag:].T @ scores[:-lag]
        S += (1.0 - lag / (lags + 1.0)) * (g + g.T)
    XtX_inv = np.linalg.inv(X.T @ X)
    V = XtX_inv @ S @ XtX_inv
    return beta, np.sqrt(np.diag(V))


def mincer_zarnowitz(df: pd.DataFrame, pred: str, real: str, lags: int, date_col: str = "date") -> dict[str, float]:
    """realised = a + b predicted (pooled bond-months), Driscoll-Kraay SEs. Want b near 1 and a near 0.

    b < 1: right direction, too confident (b = 0.3 means three times too confident). b > 1: too timid.
    """
    d = df[[date_col, pred, real]].replace([np.inf, -np.inf], np.nan).dropna()
    if len(d) < 30:
        return {"a": np.nan, "b": np.nan, "se_a": np.nan, "se_b": np.nan, "t_b_eq_1": np.nan, "n": len(d)}
    X = np.column_stack([np.ones(len(d)), d[pred].to_numpy()])
    beta, se = driscoll_kraay_ols(d[real].to_numpy(), X, d[date_col].to_numpy(), lags)
    return {"a": float(beta[0]), "b": float(beta[1]), "se_a": float(se[0]), "se_b": float(se[1]),
            "t_b_eq_1": float((beta[1] - 1.0) / se[1]) if se[1] > 0 else np.nan, "n": int(len(d))}


# ---------------------------------------------------------------- scoring


def ic_series(df: pd.DataFrame, pred: str, real: str, date_col: str = "date", min_n: int = MIN_BONDS) -> pd.Series:
    """Spearman rank IC per date (`signals.rank_ic`); dates with fewer than `min_n` bonds give NaN."""
    out = {}
    for d, g in df.groupby(date_col):
        out[d] = rank_ic(g[pred].to_numpy(), g[real].to_numpy()) if len(g) >= min_n else np.nan
    return pd.Series(out, name=pred).sort_index()


def ic_beyond(df: pd.DataFrame, pred: str, real: str, control: str, date_col: str = "date",
              min_n: int = MIN_BONDS) -> pd.Series:
    """Incremental IC: per date, remove from `real` its least-squares line on the percentile rank of `control`, then
    rank-correlate `pred` with what is left.

    Intuition: a signal that only re-expresses spread level scores near zero; one that knows something spread does
    not know keeps its IC.
    """
    out = {}
    for d, g in df.groupby(date_col):
        g = g[list(dict.fromkeys([pred, real, control]))].replace([np.inf, -np.inf], np.nan).dropna()
        if len(g) < min_n:
            out[d] = np.nan
            continue
        x = g[control].rank(pct=True).to_numpy()
        y = g[real].to_numpy()
        b, a = np.polyfit(x, y, 1)
        out[d] = rank_ic(g[pred].to_numpy(), y - (a + b * x))
    return pd.Series(out, name=pred).sort_index()


def ic_by_window(ic: pd.Series, windows: Mapping[int, tuple[str, str]] = CYCLE_WINDOWS) -> dict[int, float]:
    """Mean IC over formation months inside each window; NaN when the window has no IC."""
    out = {}
    for k, (a, b) in windows.items():
        sel = ic[(ic.index >= pd.Timestamp(a)) & (ic.index <= pd.Timestamp(b))].dropna()
        out[k] = float(sel.mean()) if len(sel) else float("nan")
    return out


def ic_by_year(ic: pd.Series) -> pd.Series:
    return ic.groupby(pd.DatetimeIndex(ic.index).year).mean()


def cycle_test(ic: pd.Series, windows: Mapping[int, tuple[str, str]] = CYCLE_WINDOWS) -> dict:
    """CLAUDE.md bar: IC after costs > 0 in at least 3 of the 4 cycles (`signals.passes_cycle_test`). A cycle with no
    data counts as a fail."""
    by = ic_by_window(ic, windows)
    return {"by_cycle": by, "cycles_positive": int(sum(1 for c in CYCLES if np.isfinite(by.get(c, np.nan)) and by[c] > 0)),
            "cycles_with_data": int(sum(1 for c in CYCLES if np.isfinite(by.get(c, np.nan)))),
            "passes": bool(passes_cycle_test(by))}


def decile_ranks(df: pd.DataFrame, pred: str, date_col: str = "date", n_bins: int = 10,
                 min_n: int = 5 * MIN_BONDS) -> pd.Series:
    """Decile 1 (lowest alpha_hat) to `n_bins` per date; NaN on dates with fewer than `min_n` bonds."""
    def one(g: pd.Series) -> pd.Series:
        if g.notna().sum() < min_n:
            return pd.Series(np.nan, index=g.index)
        return np.floor(g.rank(method="first", pct=True) * n_bins - 1e-9).clip(0, n_bins - 1) + 1
    return df.groupby(date_col)[pred].transform(one)


def decile_calibration(df: pd.DataFrame, pred: str, real: str, date_col: str = "date", n_bins: int = 10) -> pd.DataFrame:
    """Mean predicted and mean realised per decile of predicted, pooled over dates (calibration plot data)."""
    d = df[[date_col, pred, real]].dropna().copy()
    d["decile"] = decile_ranks(d, pred, date_col, n_bins)
    g = d.dropna(subset=["decile"]).groupby("decile")
    out = g.agg(pred_mean=(pred, "mean"), real_mean=(real, "mean"), n=(real, "size"))
    out["real_se"] = g[real].std() / np.sqrt(out["n"])
    return out.reset_index()


def long_short(df: pd.DataFrame, pred: str, real: str, cost: str | None, date_col: str = "date",
               n_bins: int = 10) -> pd.DataFrame:
    """Top-minus-bottom decile, equal weight, per formation date; h-month returns. After cost: each leg pays its
    bonds' mean round-trip cost (full turnover each formation; conservative)."""
    cols = [date_col, pred, real] + ([cost] if cost else [])
    d = df[cols].dropna().copy()
    d["decile"] = decile_ranks(d, pred, date_col, n_bins)
    d = d.dropna(subset=["decile"])
    top, bot = d[d["decile"] == n_bins].groupby(date_col), d[d["decile"] == 1].groupby(date_col)
    out = pd.DataFrame({"long": top[real].mean(), "short": bot[real].mean()})
    out["gross"] = out["long"] - out["short"]
    out["cost"] = (top[cost].mean() + bot[cost].mean()) if cost else 0.0
    out["net"] = out["gross"] - out["cost"]
    return out.sort_index()


def max_drawdown(wealth: pd.Series) -> float:
    """Largest fall from a running peak, as a fraction of the peak (negative number; 0 when it never falls)."""
    w = np.asarray(wealth, dtype=float)
    if len(w) == 0:
        return float("nan")
    peak = np.maximum.accumulate(w)
    return float((w / peak - 1.0).min())


def long_short_summary(ls: pd.Series, h_months: int) -> dict[str, float]:
    """Mean h-month return with HAC t (lags h-1), annualised mean, hit rate, and the compounded path, drawdown, and
    compound annual growth (`cagr`) of the non-overlapping formation dates (every h-th month from the first).
    The arithmetic mean overstates what compounds when drawdowns are deep; report both."""
    s = ls.dropna()
    hm = hac_mean(s, h_months - 1)
    path = s.iloc[:: int(h_months)]
    wealth = (1.0 + path).cumprod()
    return {"mean_h": hm["mean"], "t": hm["t"], "n": hm["n"], "ann_mean": hm["mean"] * 12.0 / h_months,
            "hit_rate": float((s > 0).mean()) if len(s) else np.nan,
            "max_drawdown": max_drawdown(pd.concat([pd.Series([1.0]), wealth])),
            "cum_return": float(wealth.iloc[-1] - 1.0) if len(wealth) else np.nan,
            "cagr": float(wealth.iloc[-1] ** (12.0 / (h_months * len(wealth))) - 1.0) if len(wealth) else np.nan}


def pit_values(df: pd.DataFrame, pred: str, real: str, h_months: int, date_col: str = "date",
               min_errors: int = 500) -> pd.Series:
    """Probability integral transform of realised against N(predicted, sd_t).

    sd_t is the standard deviation of past forecast errors (realised - predicted) of outcomes complete by t (formed
    at or before t - h months). Uniform PIT means the stated spread of outcomes is right; a U shape means too narrow.
    """
    d = df[[date_col, pred, real]].dropna().sort_values(date_col)
    err = d[real] - d[pred]
    by = pd.DataFrame({"s": err.groupby(d[date_col]).sum(), "ss": (err ** 2).groupby(d[date_col]).sum(),
                       "n": err.groupby(d[date_col]).size()}).sort_index()
    out = pd.Series(np.nan, index=d.index)
    dates = by.index
    for t in dates:
        done = by[by.index <= t - pd.offsets.MonthEnd(h_months)]
        n = done["n"].sum()
        if n < min_errors:
            continue
        mu = done["s"].sum() / n
        sd = np.sqrt(max(done["ss"].sum() / n - mu ** 2, 1e-12))
        idx = d.index[d[date_col] == t]
        out[idx] = stats.norm.cdf((d.loc[idx, real] - d.loc[idx, pred]) / sd)
    return out


def pit_summary(pit: pd.Series, n_bins: int = 10) -> dict:
    v = pit.dropna().to_numpy()
    if len(v) < 50:
        return {"n": int(len(v)), "ks": np.nan, "share_by_decile": []}
    hist, _ = np.histogram(v, bins=n_bins, range=(0, 1))
    return {"n": int(len(v)), "ks": float(stats.kstest(v, "uniform").statistic),
            "share_by_decile": (hist / len(v)).round(4).tolist()}


def evaluate(df: pd.DataFrame, pred: str, h_months: int, real: str = "realised", real_net: str = "realised_net",
             cost: str = "cost_rt") -> dict:
    """All scores for one predictor at one horizon (rv_pairs steps 3 and 4, Section 11)."""
    lags = h_months - 1
    ic_g = ic_series(df, pred, real)
    ic_n = ic_series(df, pred, real_net)
    ls = long_short(df, pred, real, cost)
    return {
        "ic_gross": hac_mean(ic_g, lags), "ic_net": hac_mean(ic_n, lags),
        "ic_net_by_year": {int(k): float(v) for k, v in ic_by_year(ic_n).items()},
        "cycle_test_net": cycle_test(ic_n),
        "mz": mincer_zarnowitz(df, pred, real, lags),
        "long_short_gross": long_short_summary(ls["gross"], h_months),
        "long_short_net": long_short_summary(ls["net"], h_months),
        "_ic_net_series": ic_n, "_ls": ls,
    }


# ---------------------------------------------------------------- peer line (decision page 2026-10-23-peer-fair-spread)


def dts_realised(total, tsy_ret, bench_ret_beta1, s, S) -> np.ndarray:
    """Realised return with the DTS hedge (Section 7.5 hedge; hy.fairspread.dts_beta): total - tsy - (s / S) x bench_ret,
    where bench_ret_beta1 = S tau - D (S_end - S) is the index leg at beta 1 (`realised_excess_return`).
    Intuition: short as much of the index as the bond's spread risk, so only the bond-specific move is left."""
    beta = np.where(np.asarray(S) > 0, np.asarray(s) / np.asarray(S), np.nan)
    return np.asarray(total) - np.asarray(tsy_ret) - beta * np.asarray(bench_ret_beta1)


def peer_convergence_alpha(s, esp, dur, rho: float, h_months: int) -> np.ndarray:
    """Section 7.5 alpha against the peer fair spread: D (1 - rho^h) (s - s exp(-ESP)). With the DTS hedge the carry
    term s - beta S is zero, so this is the whole forecast before cost.
    Intuition: the part of the gap to the peer median that closes before the exit, times the price move per unit."""
    s = np.asarray(s, dtype=float)
    return np.asarray(dur, dtype=float) * (1.0 - rho ** h_months) * (s - s * np.exp(-np.asarray(esp, dtype=float)))


def peer_rho(history: Mapping[pd.Timestamp, pd.Series], t: pd.Timestamp, min_pairs: int = MIN_RHO_PAIRS,
             prior: float = RHO_PRIOR_M) -> tuple[float, str]:
    """Monthly persistence of the issuer ESP gap from months up to and including t only (`pooled_rho`). The prior
    holds until `min_pairs` same-issuer pairs exist. Intuition: the speed the gap closed at in the past."""
    r, pairs = pooled_rho({m: e for m, e in history.items() if m <= t and len(e)})
    if pairs < min_pairs or not np.isfinite(r):
        return prior, "prior"
    return float(np.clip(r, 0.0, 0.999)), "fitted"


# ---------------------------------------------------------------- portfolios (decision page 2026-10-23-peer-fair-spread)

DISTRESSED_SPREAD = 0.10  # 1,000 bp: the market's distressed cut; Gatto stops quoting spreads above it (p. 122)


def not_distressed(df: pd.DataFrame, spread_col: str = "g_spread", cap: float = DISTRESSED_SPREAD) -> pd.Series:
    """True for a bond whose spread is below `cap`; a missing spread is out. Intuition: above 1,000 bp a bond trades
    on recovery, not on spread, and the DTS hedge ratio s / S becomes too large to mean anything."""
    s = df[spread_col].astype(float)
    return (s < cap) & s.notna()


def quarter_end_dates(dates) -> list[pd.Timestamp]:
    """The March, June, September and December month ends among `dates`: the quarterly rebalance dates."""
    return sorted(pd.Timestamp(d) for d in pd.unique(pd.Series(pd.to_datetime(dates))) if pd.Timestamp(d).month % 3 == 0)


def spread_neutral_long_short(df: pd.DataFrame, pred: str, real: str, cost: str | None, control: str,
                              date_col: str = "date", n_ctrl: int = 5, n_bins: int = 5) -> pd.DataFrame:
    """Double sort: per date, split bonds into `n_ctrl` groups of `control` (spread level); inside each group, long the
    top and short the bottom of `n_bins` groups of `pred`; equal weight across all bonds of each leg. Cost as in
    `long_short`. Intuition: long and short legs carry about the same spread, so only the part of `pred` that spread
    level does not explain can earn. Limit: spread still varies inside each control group, so a pure spread signal
    keeps a residual (about a fifth of its plain-sort premium in the test)."""
    cols = [date_col, pred, real, control] + ([cost] if cost else [])
    d = df[cols].dropna().copy()
    d["ctrl"] = decile_ranks(d, control, date_col, n_ctrl, min_n=n_ctrl * n_bins)
    d = d.dropna(subset=["ctrl"])
    key = d[date_col].astype(str) + "|" + d["ctrl"].astype(int).astype(str)
    d["bin"] = d.groupby(key)[pred].transform(
        lambda g: np.floor(g.rank(method="first", pct=True) * n_bins - 1e-9).clip(0, n_bins - 1) + 1)
    top, bot = d[d["bin"] == n_bins].groupby(date_col), d[d["bin"] == 1].groupby(date_col)
    out = pd.DataFrame({"long": top[real].mean(), "short": bot[real].mean()})
    out["gross"] = out["long"] - out["short"]
    out["cost"] = (top[cost].mean() + bot[cost].mean()) if cost else 0.0
    out["net"] = out["gross"] - out["cost"]
    return out.sort_index()


def portfolio_stats(r: pd.Series, periods_per_year: int = 4,
                    windows: Mapping[int, tuple[str, str]] = CYCLE_WINDOWS) -> dict:
    """Return per period -> annual mean, annual volatility, Sharpe (no risk-free: the returns are already excess),
    hit rate, compounded path, maximum drawdown, compound annual growth, and the mean in each cycle window.
    Intuition: what a book that held this portfolio would have seen."""
    s = r.dropna().sort_index()
    if s.empty:
        return {"n": 0}
    wealth = (1.0 + s).cumprod()
    mean, vol = float(s.mean()) * periods_per_year, float(s.std(ddof=1)) * np.sqrt(periods_per_year)
    by = {}
    for c, (a, b) in windows.items():
        w = s[(s.index >= pd.Timestamp(a)) & (s.index <= pd.Timestamp(b))]
        by[c] = float(w.mean()) * periods_per_year if len(w) else float("nan")
    return {"n": int(len(s)), "ann_mean": mean, "ann_vol": vol, "sharpe": mean / vol if vol > 0 else float("nan"),
            "hit_rate": float((s > 0).mean()), "cum_return": float(wealth.iloc[-1] - 1.0),
            "max_drawdown": max_drawdown(pd.concat([pd.Series([1.0]), wealth])),
            "cagr": float(wealth.iloc[-1] ** (periods_per_year / len(s)) - 1.0),
            "by_cycle_ann_mean": by, "cycles_positive": int(sum(1 for v in by.values() if v == v and v > 0)),
            "cycles_with_data": int(sum(1 for v in by.values() if v == v))}


def turnover_cost(legs: pd.DataFrame, id_col: str, cost: str, date_col: str = "date") -> pd.DataFrame:
    """Cost of a rebalanced long-short book when only the bonds that enter a leg trade. `legs` has one row per
    (date, bond, leg) with leg in {long, short}. Per date and leg: the sum of the round-trip cost of the entering
    bonds over the leg size; the book's cost is long plus short. A bond's round trip is charged when it enters,
    because it will leave later. Turnover = entering bonds over all bonds. Intuition: a signal that persists keeps
    most bonds in the book, so the book pays for the names that change, not for the whole book each quarter."""
    out = {}
    prev = {"long": set(), "short": set()}
    for t, g in legs.sort_values(date_col).groupby(date_col):
        c, enter, total = 0.0, 0, 0
        for leg in ("long", "short"):
            x = g[g["leg"] == leg]
            new = ~x[id_col].isin(prev[leg])
            c += float(x.loc[new, cost].sum()) / len(x) if len(x) else 0.0
            enter, total = enter + int(new.sum()), total + len(x)
            prev[leg] = set(x[id_col])
        out[t] = {"cost": c, "turnover": enter / total if total else float("nan")}
    return pd.DataFrame(out).T.astype(float)


def book_legs(df: pd.DataFrame, pred: str, id_col: str, control: str | None = None, date_col: str = "date",
              n_bins: int = 10, n_ctrl: int = 5) -> pd.DataFrame:
    """The members of the long and short legs per date, by the same rule as `long_short` (control None: top and
    bottom of n_bins) or `spread_neutral_long_short` (control given: top and bottom of n_bins inside each of n_ctrl
    control groups). Returns rows (date, id, leg)."""
    cols = [date_col, id_col, pred] + ([control] if control else [])
    d = df[cols].dropna().copy()
    if control is None:
        d["bin"] = decile_ranks(d, pred, date_col, n_bins)
    else:
        d["ctrl"] = decile_ranks(d, control, date_col, n_ctrl, min_n=n_ctrl * n_bins)
        d = d.dropna(subset=["ctrl"])
        key = d[date_col].astype(str) + "|" + d["ctrl"].astype(int).astype(str)
        d["bin"] = d.groupby(key)[pred].transform(
            lambda g: np.floor(g.rank(method="first", pct=True) * n_bins - 1e-9).clip(0, n_bins - 1) + 1)
    d = d[d["bin"].isin([1, n_bins])]
    return d.assign(leg=np.where(d["bin"] == n_bins, "long", "short"))[[date_col, id_col, "leg"]]

