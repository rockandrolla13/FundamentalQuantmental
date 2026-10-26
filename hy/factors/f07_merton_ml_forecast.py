"""F07 Merton-restricted machine-learning bond forecast (rank 7). Spec docs/factors/F07-merton-ml-forecast.md.

Methodology Section 8 (new signal "Merton-restricted expected return") and Section 11 (backtest design). Source:
Bali, Goyal, Huang, Jiang and Wen (2022), "Predicting Corporate Bond Returns: Merton Meets Machine Learning", SFI
Research Paper 20-110. Pages are printed pages (PDF page = printed page + 2).

    h_i,t          = OLS slope of RB_i,s on RS_i,s, s = t-35 .. t                     (eq. 19, p. 21)
    RBmRS_i,t+1    = RB_i,t+1 - h_i,t RS_i,t+1                                        (eq. 10, p. 8)
    E_t[RB_i,t+1]  = h_i,t psi1(XS_i,t) + psi2(XB_i,t)                               (eqs. 11 and 21, pp. 8 and 21)

Intuition: a bond is riskless debt minus a put on the firm. The stock prices the put, so predict that part with
stock characteristics and the rest with bond characteristics.

RB is the issuer's 1-month bond return over the duration-matched Treasury (`realised_excess_return`, beta 0), the
equal-weight mean over its eligible bonds. RS is the stock total return minus the T-bill. psi1 learns RS_t+1 from
the stock features. psi2 learns RBmRS_t+1 from the bond features. Each feature is ranked per month to [-1, 1] and a
missing value is 0, the median (fn. 7, p. 13). An issuer without h (private, or under MIN_HEDGE_OBS months) takes
h = 0: its label is RB and its score is psi2 (`has_equity` False).

Walk-forward (our choice): expanding window, refit at each REFIT_MONTH month end. A training row enters only when
its label `available_at` is on or before the decision time of the fit date, so no label is realised after it.

Panels: `bond_panel` and `equity_monthly` (required; either missing gives an empty frame). `ratings` and `leverage`
feed one feature each (missing: rank 0). New optional panel `tbill_monthly`: `date` (month end), `rf` (monthly,
decimal), `available_at`. Missing: rf = 0.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.base import RegressorMixin, clone
from sklearn.ensemble import RandomForestRegressor

from hy.backtest import assert_no_lookahead, decision_time, eligible, realised_excess_return
from hy.data.pit import LookAheadError
from hy.peers import LEV_FLOOR, RATING_STALE_DAYS

HEDGE_WINDOW = 36          # months in the hedge-ratio regression, t-35 .. t (eq. 19, p. 21)
MIN_HEDGE_OBS = 24         # our choice: bond-stock pairs a hedge ratio needs
RISK_WINDOW = 36           # months for VaR, ES, VOL, SKEW, KURT, betas, COSKEW (Appendix B, pp. 29-35)
MIN_RISK_OBS = 24          # our choice: months a 36-month risk feature needs
MIN_TRAIN_MONTHS = 36      # formation months before the first fit: the source's 3-year training span (p. 10)
REFIT_MONTH = 12           # our choice: refit at each December month end, expanding window
RANDOM_STATE = 0           # our choice: fixed seed, so the forecast is reproducible
RF_PARAMS = {"n_estimators": 100, "max_depth": 6, "min_samples_leaf": 20, "max_features": 0.5}  # our choice
# Bond features (Appendix B). log_spread, cost and log_volume are ours: spread is not in the 43, cost proxies
# AvgBidAsk (item 22), and par volume proxies Size (item 3) until amount outstanding arrives.
BOND_FEATURES = ("rating", "years", "mod_dur", "log_spread", "cost", "log_volume",
                 "var5", "var10", "es5", "es10", "beta_bond", "vol", "skew", "kurt", "coskew", "iskew",
                 "rev", "mom6", "mom12", "ltr")
# Stock features: monthly proxies of 7 of the 94 Green-Hand-Zhang characteristics (our choice; GHZ is not in the folder).
STOCK_FEATURES = ("mom1m", "mom6m", "mom12m", "mom36m", "chmom", "retvol", "beta", "log_lev")
# S&P notches: AAA = 1, BBB- = 10 (the source's IG cut, p. 29), CCC = 18, C, SD and D = 21.
RATING_SCALE = {s: i + 1 for i, s in enumerate(
    ["AAA", "AA+", "AA", "AA-", "A+", "A", "A-", "BBB+", "BBB", "BBB-", "BB+", "BB", "BB-",
     "B+", "B", "B-", "CCC+", "CCC", "CCC-", "CC", "C"])} | {"SD": 21, "D": 21}

META = {"rank": 7, "name": "Merton-restricted machine-learning bond forecast", "level": "issuer",
        "horizon_months": 1, "needs": ["bond_panel", "equity_monthly", "ratings", "leverage", "tbill_monthly"],
        "spec": "docs/factors/F07-merton-ml-forecast.md", "section": "8"}
OUT_COLS = ["date", "gvkey", "score", "available_at", "h_hat", "psi1_stock", "psi2_bond", "has_equity", "n_bonds",
            "fit_date"]


@dataclass
class MertonModel:
    """The two fitted legs (and the optional bond-only benchmark) of one walk-forward fit."""
    psi1: RegressorMixin                # stock leg: RS_t+1 on the stock features
    psi2: RegressorMixin                # bond leg: RBmRS_t+1 on the bond features
    f1: RegressorMixin | None           # benchmark f1(XB): RB_t+1 on the bond features (eq. 12, p. 8)
    fit_date: pd.Timestamp              # the month end the fit stands at
    label_through: pd.Timestamp         # latest label available_at in the training set
    n_stock: int
    n_bond: int


# ---------------------------------------------------------------- formula helpers


def rolling_slope(y: pd.DataFrame, x: pd.DataFrame, window: int, min_obs: int) -> pd.DataFrame:
    """OLS slope of y on x (with intercept) per column over the last `window` rows, pairs only.

    Spec Definition, eq. (19) p. 21. NaN where fewer than `min_obs` pairs or x has no variance."""
    m = y.notna() & x.notna()
    xv, yv, n = x.where(m, 0.0), y.where(m, 0.0), m.astype(float)
    r = lambda f: f.rolling(window, min_periods=1).sum()  # noqa: E731
    sn, sx, sy, sxx, sxy = r(n), r(xv), r(yv), r(xv * xv), r(xv * yv)
    var = sxx - sx * sx / sn
    slope = (sxy - sx * sy / sn) / var
    return slope.where((sn >= min_obs) & (var > 1e-12))


def hedge_ratio(rb: pd.DataFrame, rs: pd.DataFrame, window: int = HEDGE_WINDOW,
                min_obs: int = MIN_HEDGE_OBS) -> pd.DataFrame:
    """h_i,t: slope of firm excess bond return on firm excess stock return over months t-35 .. t (eq. 19, p. 21).
    Frames are month x gvkey on a full month-end grid."""
    return rolling_slope(rb, rs.reindex_like(rb), window, min_obs)


def rbmrs(rb_next: np.ndarray, h: np.ndarray, rs_next: np.ndarray) -> np.ndarray:
    """RBmRS_t+1 = RB_t+1 - h_t RS_t+1: the bond return the stock does not hedge (eq. 10, p. 8)."""
    return np.asarray(rb_next, float) - np.asarray(h, float) * np.asarray(rs_next, float)


def merton_forecast(h: np.ndarray, psi1: np.ndarray, psi2: np.ndarray) -> np.ndarray:
    """E_t[RB_t+1] = h_t psi1(XS_t) + psi2(XB_t) (eq. 21, p. 21)."""
    return np.asarray(h, float) * np.asarray(psi1, float) + np.asarray(psi2, float)


def downside_risk(w: np.ndarray, min_obs: int = MIN_RISK_OBS) -> dict[str, np.ndarray]:
    """VaR5 = -(2nd lowest), VaR10 = -(4th lowest), ES5 = -(mean of 2 lowest), ES10 = -(mean of 4 lowest) of the
    monthly returns in the window, per column of `w` (months x bonds). Appendix B items 6-9, p. 29. The source
    flips VaR so that a higher value is more risk; we flip ES the same way. NaN under `min_obs` returns."""
    s = np.sort(w, axis=0)                                          # NaN sorts last
    ok = np.isfinite(w).sum(axis=0) >= max(min_obs, 4)
    out = {"var5": -s[1], "var10": -s[3], "es5": -s[:2].mean(axis=0), "es10": -s[:4].mean(axis=0)}
    return {k: np.where(ok, v, np.nan) for k, v in out.items()}


def _moments(w: np.ndarray, ok: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """VOL (n-1 std), SKEW and KURT - 3 with population central moments over VOL (items 39-41, pp. 34-35)."""
    with np.errstate(invalid="ignore", divide="ignore"):
        mu = np.nanmean(w, axis=0)
        d = w - mu
        vol = np.nanstd(w, axis=0, ddof=1)
        skew = np.nanmean(d ** 3, axis=0) / vol ** 3
        kurt = np.nanmean(d ** 4, axis=0) / vol ** 4 - 3.0
    return tuple(np.where(ok & (vol > 0), v, np.nan) for v in (vol, skew, kurt))


def _coskew(w: np.ndarray, m: np.ndarray, ok: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """COSKEW = gamma and ISKEW = skew of e in R = a + b Rm + gamma Rm^2 + e, per column (items 42-43, p. 35)."""
    v = np.isfinite(w) & np.isfinite(m)[:, None]
    z = np.column_stack([np.ones_like(m), m, m * m])
    z = np.nan_to_num(z)
    vf = v.astype(float)
    a = np.einsum("nk,nj,nl->jkl", z, vf, z)
    b = np.einsum("nk,nj->jk", z, np.where(v, w, 0.0))
    coef = np.einsum("jkl,jl->jk", np.linalg.pinv(a), b)
    e = np.where(v, w - z @ coef.T, np.nan)
    _, iskew, _ = _moments(e, ok)
    return np.where(ok, coef[:, 2], np.nan), iskew


def window_stats(r: pd.DataFrame, market: pd.Series, window: int = RISK_WINDOW,
                 min_obs: int = MIN_RISK_OBS) -> dict[str, pd.DataFrame]:
    """The 36-month bond risk features per month t (rows) and bond (columns), window t-35 .. t: VaR5, VaR10, ES5,
    ES10, VOL, SKEW, KURT, COSKEW, ISKEW (Appendix B, pp. 29-35). `market` is the bond market excess return."""
    names = ("var5", "var10", "es5", "es10", "vol", "skew", "kurt", "coskew", "iskew")
    out = {k: np.full(r.shape, np.nan) for k in names}
    x, mk = r.to_numpy(float), market.reindex(r.index).to_numpy(float)
    for i in range(len(r)):
        w, m = x[max(0, i - window + 1):i + 1], mk[max(0, i - window + 1):i + 1]
        ok = np.isfinite(w).sum(axis=0) >= min_obs
        if not ok.any():
            continue
        for k, v in downside_risk(w, min_obs).items():
            out[k][i] = v
        out["vol"][i], out["skew"][i], out["kurt"][i] = _moments(w, ok)
        pairs = (np.isfinite(w) & np.isfinite(m)[:, None]).sum(axis=0) >= min_obs
        out["coskew"][i], out["iskew"][i] = _coskew(w, m, pairs)
    return {k: pd.DataFrame(v, index=r.index, columns=r.columns) for k, v in out.items()}


def _cum(r: pd.DataFrame, start_lag: int, length: int) -> pd.DataFrame:
    """Compounded return over months t-start_lag-length+1 .. t-start_lag; every month must be present."""
    lg = np.log1p(r.clip(lower=-0.99)).shift(start_lag)
    return np.expm1(lg.rolling(length, min_periods=length).sum())


def return_windows(r: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """REV = month t; MOM6 = t-6 .. t-1; MOM12 = t-11 .. t-1; LTR = t-47 .. t-12 (items 35-38, p. 34).

    The source writes each window one month earlier because its t is the return month: REV is "the bond return in
    the previous month" and MOM6 runs t-7 .. t-2. Here t is the formation month end."""
    return {"rev": r, "mom6": _cum(r, 1, 6), "mom12": _cum(r, 1, 11), "ltr": _cum(r, 12, 36)}


def stock_windows(rs: pd.DataFrame, window: int = RISK_WINDOW, min_obs: int = MIN_RISK_OBS) -> dict[str, pd.DataFrame]:
    """Monthly proxies of GHZ stock features at formation t (our choice): mom1m = month t; mom6m = t-5 .. t-1;
    mom12m = t-11 .. t-1; mom36m = t-35 .. t-12; chmom = (t-5 .. t) minus (t-11 .. t-6); retvol = sd of t-11 .. t;
    beta = 36-month slope on the equal-weight stock market."""
    mkt = pd.DataFrame(np.repeat(rs.mean(axis=1).to_numpy()[:, None], rs.shape[1], axis=1), index=rs.index,
                       columns=rs.columns)
    return {"mom1m": rs, "mom6m": _cum(rs, 1, 5), "mom12m": _cum(rs, 1, 11), "mom36m": _cum(rs, 12, 24),
            "chmom": _cum(rs, 0, 6) - _cum(rs, 6, 6), "retvol": rs.rolling(12, min_periods=12).std(),
            "beta": rolling_slope(rs, mkt.where(rs.notna()), window, min_obs)}


def rank_features(df: pd.DataFrame, cols: Iterable[str], date_col: str = "date") -> pd.DataFrame:
    """Each feature ranked per date to [-1, 1]; missing is 0, the cross-section median (fn. 7, p. 13).
    Intuition: ranks make the learner read order, not units or outliers."""
    out = pd.DataFrame(index=df.index)
    g = df.groupby(date_col)
    for c in cols:
        rk, n = g[c].rank(method="average"), g[c].transform("count")
        out[c] = (2.0 * (rk - 1.0) / (n - 1.0) - 1.0).where(n > 1, 0.0).fillna(0.0)
    return out


def fit_date(as_of: pd.Timestamp, refit_month: int | None = REFIT_MONTH) -> pd.Timestamp:
    """The fit date for month end as_of: the latest `refit_month` month end on or before as_of (as_of if None)."""
    t = pd.Timestamp(as_of) + pd.offsets.MonthEnd(0)
    if refit_month is None:
        return t
    year = t.year if t.month >= refit_month else t.year - 1
    return pd.Timestamp(year=year, month=refit_month, day=1) + pd.offsets.MonthEnd(0)


# ---------------------------------------------------------------- panels to features


def _wide(df: pd.DataFrame, date: str, key: str, val: str, months: pd.DatetimeIndex) -> pd.DataFrame:
    """month x key frame of `val` on the full month-end grid."""
    return df.pivot_table(index=date, columns=key, values=val, aggfunc="mean").reindex(months)


def _long(frames: Mapping[str, pd.DataFrame], key: str) -> pd.DataFrame:
    """Stack month x key frames into one long frame with columns date, key, then one column per frame."""
    parts = [f.rename_axis(index="date", columns=key).stack(future_stack=True).rename(k) for k, f in frames.items()]
    return pd.concat(parts, axis=1).reset_index()


def _rating_numbers(ratings: pd.DataFrame, months: pd.DatetimeIndex) -> pd.DataFrame:
    """Numeric S&P rating per month end and gvkey, known at the decision time and at most RATING_STALE_DAYS old."""
    rows = []
    r = ratings.assign(n=ratings["splticrm"].astype(str).str.strip().str.upper().map(RATING_SCALE)).dropna(subset=["n"])
    for t in months:
        dt = decision_time(t)
        k = r[(r["available_at"] <= dt) & (r["datadate"] >= dt - pd.Timedelta(RATING_STALE_DAYS, unit="D"))]
        k = k.sort_values("datadate").drop_duplicates("gvkey", keep="last")
        rows.append(pd.DataFrame({"date": t, "gvkey": k["gvkey"].to_numpy(), "rating": k["n"].to_numpy(float)}))
    return pd.concat(rows, ignore_index=True)


def _filtered(panels: Mapping[str, pd.DataFrame], as_of: pd.Timestamp) -> dict[str, pd.DataFrame]:
    """Every panel cut to rows with available_at <= decision_time(as_of)."""
    dt = decision_time(as_of)
    out = {}
    for k, v in panels.items():
        if v is None:
            continue
        out[k] = v[pd.to_datetime(v["available_at"]) <= dt].copy()
        assert_no_lookahead(out[k], dt, k)
    return out


def build_features(panels: Mapping[str, pd.DataFrame], as_of: pd.Timestamp) -> dict[str, pd.DataFrame] | None:
    """All features and labels known at decision_time(as_of), from the cut panels (spec Build steps 1-6).

    Returns `bond` (date, gvkey, bond features, n_bonds, rb_next, rb_label_at), `stock` (date, gvkey, stock
    features, rs_next, rs_label_at) and `hedge` (date, gvkey, h_hat). None when a required panel is missing."""
    p = _filtered(panels, as_of)
    bp, eq = p.get("bond_panel"), p.get("equity_monthly")
    if bp is None or eq is None or bp.empty or eq.empty:
        return None
    as_of = pd.Timestamp(as_of) + pd.offsets.MonthEnd(0)
    bp = bp.assign(date=pd.to_datetime(bp["date"]) + pd.offsets.MonthEnd(0))
    eq = eq.assign(datadate=pd.to_datetime(eq["datadate"]) + pd.offsets.MonthEnd(0))
    months = pd.date_range(min(bp["date"].min(), eq["datadate"].min()), as_of, freq="ME")
    # bond 1-month excess return over the matched Treasury, by formation month (beta 0: no index hedge)
    bench = pd.Series(0.0, index=pd.DatetimeIndex(pd.concat([bp["date"], pd.to_datetime(bp["hedge_date"])]).unique()))
    rx = realised_excess_return(bp, 1, decision_time(as_of), beta=0.0, bench=bench)
    rx = rx.dropna(subset=["realised"]).merge(
        bp[["cusip", "date", "available_at"]].rename(columns={"date": "end_date", "available_at": "label_at"}),
        on=["cusip", "end_date"], how="left")
    rx["month"] = rx["date"] + pd.offsets.MonthEnd(1)                      # the month the return is earned in
    r_bond = _wide(rx, "month", "cusip", "realised", months)               # month x cusip
    # bond features per cusip, then the issuer mean over its eligible bonds at t
    feats = window_stats(r_bond, r_bond.mean(axis=1)) | return_windows(r_bond)
    feats["beta_bond"] = rolling_slope(r_bond, pd.DataFrame(np.repeat(r_bond.mean(axis=1).to_numpy()[:, None],
                                       r_bond.shape[1], axis=1), index=months, columns=r_bond.columns),
                                       RISK_WINDOW, MIN_RISK_OBS)
    el = bp[eligible(bp)].copy()
    el["log_spread"] = np.log(el["g_spread"].astype(float))
    el["cost"] = el["bid_ask_pts"].astype(float) / el["price"].astype(float) if "bid_ask_pts" in el else np.nan
    el["log_volume"] = np.log1p(el["par_volume"].astype(float)) if "par_volume" in el else np.nan
    el = el.merge(_long(feats, "cusip"), on=["date", "cusip"], how="left")
    cols = [c for c in BOND_FEATURES if c != "rating"]
    bond = el.groupby(["date", "gvkey"])[cols].mean()
    bond["n_bonds"] = el.groupby(["date", "gvkey"]).size()
    bond = bond.reset_index()
    rt = p.get("ratings")
    if rt is not None and not rt.empty:
        rated = _rating_numbers(rt, pd.DatetimeIndex(bond["date"].unique()).sort_values())
        bond = bond.merge(rated.astype({"gvkey": bond["gvkey"].dtype}), on=["date", "gvkey"], how="left")
    else:
        bond["rating"] = np.nan
    # firm bond return label RB_t+1, earned by the bonds eligible at t
    rx = rx.merge(bp[["cusip", "date", "gvkey"]], on=["cusip", "date"], how="left")
    lab = rx.groupby(["date", "gvkey"]).agg(rb_next=("realised", "mean"), rb_label_at=("label_at", "max"))
    bond = bond.merge(lab.reset_index(), on=["date", "gvkey"], how="left")
    # stock excess return RS and stock features
    tb = p.get("tbill_monthly")
    rf = (pd.Series(0.0, index=months) if tb is None or tb.empty else
          tb.assign(date=pd.to_datetime(tb["date"]) + pd.offsets.MonthEnd(0)).groupby("date")["rf"].last()
          .reindex(months).fillna(0.0))
    eq["rs"] = eq["ret"].astype(float) - eq["datadate"].map(rf).fillna(0.0)
    rs = _wide(eq, "datadate", "gvkey", "rs", months)
    sf = stock_windows(rs)
    lev = p.get("leverage")
    if lev is not None and not lev.empty:
        lev = lev.assign(date=pd.to_datetime(lev["date"]) + pd.offsets.MonthEnd(0),
                         log_lev=np.log(lev["leverage"].astype(float).clip(lower=LEV_FLOOR)))
        sf["log_lev"] = _wide(lev, "date", "gvkey", "log_lev", months).reindex(columns=rs.columns)
    else:
        sf["log_lev"] = pd.DataFrame(np.nan, index=months, columns=rs.columns)
    stock = _long(sf, "gvkey")
    stock = stock[stock["mom1m"].notna()]                                  # the stock traded in month t
    nxt = eq[["gvkey", "datadate", "rs", "available_at"]].rename(columns={"rs": "rs_next", "available_at": "rs_label_at"})
    nxt["date"] = nxt.pop("datadate") - pd.offsets.MonthEnd(1)
    stock = stock.merge(nxt, on=["date", "gvkey"], how="left")
    # hedge ratio from the firm bond return and the stock return, months t-35 .. t
    rb_firm = _wide(rx.assign(month=rx["date"] + pd.offsets.MonthEnd(1)), "month", "gvkey", "realised", months)
    h = hedge_ratio(rb_firm, rs.reindex(columns=rb_firm.columns))
    hedge = _long({"h_hat": h}, "gvkey").dropna(subset=["h_hat"])
    return {"bond": bond, "stock": stock, "hedge": hedge}


def training_set(feats: Mapping[str, pd.DataFrame], fit_at: pd.Timestamp) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Training rows of psi1 (stock) and psi2 (bond) for a fit at month end `fit_at` (spec Build step 7).

    A row enters only when its label is realised: label available_at <= decision_time(fit_at). The psi2 label is
    RBmRS_t+1 (eq. 10); an issuer without h or without a stock row at t takes h = 0, so its label is RB_t+1."""
    dt = decision_time(fit_at)
    st = feats["stock"].dropna(subset=["rs_next"])
    st = st[st["rs_label_at"] <= dt].copy()
    st["label_at"] = st["rs_label_at"]
    b = feats["bond"].dropna(subset=["rb_next"]).merge(feats["hedge"], on=["date", "gvkey"], how="left")
    b = b.merge(feats["stock"][["date", "gvkey", "rs_next", "rs_label_at"]], on=["date", "gvkey"], how="left",
                indicator="in_stock")
    b["has_equity"] = b["h_hat"].notna() & (b.pop("in_stock") == "both")
    b = b[~b["has_equity"] | b["rs_next"].notna()]                         # a hedged label needs RS_t+1
    h = b["h_hat"].where(b["has_equity"], 0.0)
    b["y"] = rbmrs(b["rb_next"], h, b["rs_next"].where(b["has_equity"], 0.0))
    b["label_at"] = b["rb_label_at"].where(~b["has_equity"], b[["rb_label_at", "rs_label_at"]].max(axis=1))
    b = b[b["label_at"] <= dt]
    return st, b


def _learner(params: Mapping) -> RegressorMixin:
    """A fresh copy of the learner: `learner` in params, else the default random forest."""
    base = params.get("learner") or RandomForestRegressor(**RF_PARAMS, random_state=RANDOM_STATE, n_jobs=1)
    return clone(base)


def fit(panels: Mapping[str, pd.DataFrame], as_of: pd.Timestamp, feats: Mapping[str, pd.DataFrame] | None = None,
        **params) -> MertonModel | None:
    """Fit psi1 and psi2 at the fit date of as_of (`refit_month`, default REFIT_MONTH), on labels realised by its
    decision time. `bond_only=True` also fits the f1(XB) benchmark. None when a panel is missing or there are fewer
    than `min_train_months` formation months."""
    f_at = fit_date(as_of, params.get("refit_month", REFIT_MONTH))
    feats = feats if feats is not None else build_features(panels, as_of)
    if feats is None:
        return None
    st, b = training_set(feats, f_at)
    if min(st["date"].nunique(), b["date"].nunique()) < params.get("min_train_months", MIN_TRAIN_MONTHS):
        return None
    xs, xb = rank_features(st, STOCK_FEATURES), rank_features(b, BOND_FEATURES)
    psi1 = _learner(params).fit(xs.to_numpy(), st["rs_next"].to_numpy(float))
    psi2 = _learner(params).fit(xb.to_numpy(), b["y"].to_numpy(float))
    f1 = _learner(params).fit(xb.to_numpy(), b["rb_next"].to_numpy(float)) if params.get("bond_only") else None
    through = max(st["label_at"].max(), b["label_at"].max())
    return MertonModel(psi1, psi2, f1, f_at, pd.Timestamp(through), len(st), len(b))


def _empty() -> pd.DataFrame:
    return pd.DataFrame({c: pd.Series(dtype=float) for c in OUT_COLS})


def compute(panels: Mapping[str, pd.DataFrame], as_of: pd.Timestamp, **params) -> pd.DataFrame:
    """F07 score per issuer at month end as_of: E_t[RB_t+1] = h psi1(XS) + psi2(XB) (eq. 21, p. 21).

    params: `model` (a pre-fitted MertonModel; its label date must be on or before decision_time(as_of)), else the
    call fits on the history inside it; `refit_month`, `min_train_months`, `learner`, `bond_only`.
    One row per gvkey with an eligible bond at as_of. Empty frame when a required panel is missing or no fit exists."""
    as_of = pd.Timestamp(as_of) + pd.offsets.MonthEnd(0)
    dt = decision_time(as_of)
    model = params.get("model")
    if model is not None and model.label_through > dt:
        raise LookAheadError(f"F07 model holds labels to {model.label_through}, after {dt}")
    feats = build_features(panels, as_of)
    if feats is None:
        return _empty()
    model = model or fit(panels, as_of, feats=feats, **params)
    if model is None:
        return _empty()
    b = feats["bond"][feats["bond"]["date"] == as_of]
    if b.empty:
        return _empty()
    # rank against the whole as_of cross-section, as in training
    xb = rank_features(b, BOND_FEATURES)
    s_all = feats["stock"][feats["stock"]["date"] == as_of]
    xs = rank_features(s_all, STOCK_FEATURES)
    psi1 = pd.Series(model.psi1.predict(xs.to_numpy()) if len(xs) else [], index=s_all["gvkey"].to_numpy())
    out = b[["date", "gvkey", "n_bonds"]].merge(feats["hedge"], on=["date", "gvkey"], how="left")
    out["psi2_bond"] = model.psi2.predict(xb.to_numpy())
    out["psi1_stock"] = out["gvkey"].map(psi1)
    out["has_equity"] = out["h_hat"].notna() & out["psi1_stock"].notna()
    out["h_hat"] = out["h_hat"].where(out["has_equity"])
    out["score"] = np.where(out["has_equity"], merton_forecast(out["h_hat"], out["psi1_stock"], out["psi2_bond"]),
                            out["psi2_bond"])
    if model.f1 is not None:
        out["f1_bond_only"] = model.f1.predict(xb.to_numpy())
    out["available_at"] = dt
    out["fit_date"] = model.fit_date
    extra = ["f1_bond_only"] if model.f1 is not None else []
    return out[OUT_COLS + extra].reset_index(drop=True)


def walk_forward(panels: Mapping[str, pd.DataFrame], months: Iterable[pd.Timestamp], **params) -> pd.DataFrame:
    """compute() over `months` with one fit per fit date (expanding window, refit yearly). Each fit sees only the
    panels cut at its own fit date."""
    out, model, at = [], None, None
    for t in months:
        f_at = fit_date(t, params.get("refit_month", REFIT_MONTH))
        if f_at != at:
            model, at = fit(panels, f_at, **(params | {"refit_month": None})), f_at
        if model is not None:
            out.append(compute(panels, t, **(params | {"model": model})))
    return pd.concat(out, ignore_index=True) if out else _empty()
