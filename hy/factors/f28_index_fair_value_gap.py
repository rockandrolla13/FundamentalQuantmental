"""F28 HY index fair value gap net of carry (rank 28). Spec docs/factors/F28-index-fair-value-gap.md; methodology
Section 8 (S7 replacement, index timing), Section 7.5 (expected convergence) and Section 5.2.1 (the macro vector
m_t). Sources: de Kock (J.P. Morgan, 29 April 2009), "Trading and Hedging Long-Term FX Fundamentals", pp. 1 to 4;
de Kock (J.P. Morgan, 6 September 2008), "A new fair-value model for G10 currencies", pp. 2, 4, 5, 7, 8. Printed
page = PDF page. The evidence is G10 FX only, 2004 to 2008. No credit test exists in the folder.

    shat_k   = a + b' x_k,  OLS on months k <= t                       macro fair spread, expanding window (2009 p. 2)
    s*_t     = w s_t + (1 - w) shat_t                                  permanent part, w = 0 (2008 Table 1 p. 4: 0.2637)
    m_t      = s_t - s*_t                                              misalignment, positive = cheap
    E_t      = kappa D_t m_t + s_t h / 12                              convergence plus carry over h months
    pos_t    = +1 if E_t > delta, -1 if E_t < -delta, else 0           rule (3) and (5), 2009 p. 4
    alpha_h  = -sum m_tau ds_tau / sum m_tau^2,  ds = s_tau+h - s_tau  convergence share, eq. (1), out of sample

Intuition: a valuation gap closes slowly, so the trade pays only when the expected convergence beats the carry that
the position gives up by waiting. The FX rule (3) reads e*_{t-1} - f = (e*_{t-1} - e_t) - (r* - r) > delta: the gap
minus the cost of carry. In credit the long earns the spread, so carry adds to the long side and costs the short.

Inputs. `hy_index` (wiring 4.5: `date`, `spread` decimal, `available_at`), a new panel `macro_series` in long format
(`series_id` FRED id, `date`, `value`, `available_at`; several vintages per date allowed) and, for the duration,
`bond_panel` (`mod_dur`). Default regressors DRTSCILM (SLOOS net tightening), T10Y3M (10-year minus 3-month slope),
VIXCLS. Without `hy_index` or `macro_series` the result is an empty frame. Without a duration the score is NaN with
status `no_duration`.
"""

from __future__ import annotations

from typing import Mapping, Sequence

import numpy as np
import pandas as pd

from hy.backtest import decision_time, eligible

INDEX_KEY = "US_HY"
REGRESSORS = ("DRTSCILM", "T10Y3M", "VIXCLS")  # SLOOS, slope (methodology 5.2.1 m_t), VIX (reader G-F5); our choice
HORIZON = 6             # months: the rule beat carry at 6 months for every threshold (2009 p. 2, Table 3 p. 3)
THRESHOLD = 0.0         # delta, decimal return over the horizon: tested 0, 5, 10% in FX (p. 3); our choice 0
KAPPA = 1.0             # share of the gap the rule expects to close: the full gap, as rule (3) assumes (p. 4)
ACTUAL_WEIGHT = 0.0     # w: weight of the actual spread in s*. FX panel 0.2637 (2008 Table 1 p. 4); our choice 0
MIN_TRAIN = 60          # months the OLS needs (our choice; the source starts with 96 quarters, 1Q80-4Q03, p. 2)
MIN_ALPHA_OBS = 24      # out-of-sample pairs the convergence share needs (our choice)
MAX_STALE_DAYS = 190    # oldest macro value allowed: one SLOOS quarter plus its release lag (our choice)

META = {
    "rank": 28,
    "name": "HY index fair value gap net of carry",
    "level": "index",
    "horizon_months": HORIZON,
    "needs": ["hy_index", "macro_series", "bond_panel"],
    "spec": "docs/factors/F28-index-fair-value-gap.md",
    "section": "8",
}

COLS = ["date", "index", "score", "available_at", "position", "spread", "fair_spread", "misalignment", "carry",
        "duration", "kappa", "alpha_h", "alpha_n", "n_train", "r2", "status"]


# ---------------------------------------------------------------- formula helpers


def _public(df: pd.DataFrame, dt: pd.Timestamp, keys: Sequence[str]) -> pd.DataFrame:
    """Rows with available_at <= dt, the last vintage per `keys` (spec build step 1)."""
    d = df[pd.to_datetime(df["available_at"]) <= dt].copy()
    d["date"] = pd.to_datetime(d["date"])
    d["available_at"] = pd.to_datetime(d["available_at"])
    return d.sort_values("available_at").drop_duplicates(list(keys), keep="last")


def monthly_spread(hy_index: pd.DataFrame) -> pd.Series:
    """Monthly mean of the index spread, indexed by month end (spec Definition; the source uses period averages,
    2009 p. 2, Table 2 notes). NaN spreads drop out."""
    h = hy_index[np.isfinite(hy_index["spread"].astype(float))]
    month = h["date"] + pd.offsets.MonthEnd(0)
    return h["spread"].astype(float).groupby(month).mean().sort_index().rename("spread")


def macro_at(rows: pd.DataFrame, month_end: pd.Timestamp, max_stale_days: int = MAX_STALE_DAYS) -> float:
    """Value of one series as known at decision_time(month_end) (spec build step 3).

    Take rows dated <= month_end with available_at <= decision_time(month_end). Pick the latest date, then its
    latest vintage. NaN when no row qualifies or the date is more than `max_stale_days` before month_end. The
    available_at filter plays the role of the source's one-quarter lag of the fair value (2009 p. 2)."""
    dt = decision_time(month_end)
    r = rows[(rows["date"] <= month_end) & (rows["available_at"] <= dt)]
    r = r[np.isfinite(r["value"].astype(float))]
    if r.empty:
        return np.nan
    last = r["date"].max()
    if (month_end - last).days > max_stale_days:
        return np.nan
    return float(r[r["date"] == last].sort_values("available_at")["value"].iloc[-1])


def macro_matrix(macro: pd.DataFrame, months: pd.DatetimeIndex, regressors: Sequence[str] = REGRESSORS,
                 max_stale_days: int = MAX_STALE_DAYS) -> pd.DataFrame:
    """x_k for each month k, each value point in time at its own decision time (spec build step 3). Columns =
    `regressors`. A series missing from the panel is all NaN."""
    out = pd.DataFrame(index=months, columns=list(regressors), dtype=float)
    for sid in regressors:
        rows = macro[macro["series_id"] == sid]
        if rows.empty:
            continue
        out[sid] = [macro_at(rows, k, max_stale_days) for k in months]
    return out


def fit_fair_value(y: pd.Series, X: pd.DataFrame, min_train: int = MIN_TRAIN) -> dict:
    """OLS y_k = a + b' x_k + u_k on the complete rows (spec Definition; long-run regression of the 2008 note,
    pp. 4 and 8, in levels, one index so no panel). Returns coef (intercept first), r2 and n. coef is None when
    fewer than max(min_train, p + 2) rows exist."""
    d = pd.concat([y.rename("y"), X], axis=1).dropna()
    n, p = len(d), X.shape[1]
    if n < max(min_train, p + 2):
        return {"coef": None, "r2": np.nan, "n": n}
    A = np.column_stack([np.ones(n), d[X.columns].to_numpy(float)])
    yy = d["y"].to_numpy(float)
    coef, *_ = np.linalg.lstsq(A, yy, rcond=None)
    sst = float(((yy - yy.mean()) ** 2).sum())
    r2 = 1.0 - float(((yy - A @ coef) ** 2).sum()) / sst if sst > 0 else np.nan
    return {"coef": coef, "r2": r2, "n": n}


def fair_spread(coef: np.ndarray, x: np.ndarray, spread: float, actual_weight: float = ACTUAL_WEIGHT) -> float:
    """s* = w s + (1 - w)(a + b'x) (spec Definition). w is the weight of the actual level in the permanent part
    (2008 Table 1 p. 4 puts 0.2637 on the actual rate and scales each driver by 1 - w). Intuition: w > 0 trusts
    that the market level carries news the drivers miss."""
    fitted = float(coef[0] + np.dot(coef[1:], np.asarray(x, dtype=float)))
    return actual_weight * spread + (1.0 - actual_weight) * fitted


def carry_over(spread: float, horizon: int = HORIZON) -> float:
    """Spread carry over `horizon` months, decimal of price: s h / 12 (spec Definition; our choice for the FX cost
    of carry r* - r over n periods, 2009 p. 4). Expected default loss is not deducted."""
    return spread * horizon / 12.0


def carry_adjusted_edge(misalignment: float, spread: float, duration: float, horizon: int = HORIZON,
                        kappa: float = KAPPA) -> float:
    """E = kappa D m + s h / 12: expected excess return of a long index position over the horizon (spec Definition).

    The FX rule (3) of 2009 p. 4 compares the gap e* - e with the carry r* - r. Here the gap in price terms is
    D m (a spread above fair tightens by kappa m), and the long earns the carry. The short has edge -E. Intuition:
    act only when convergence pays more than the carry lost by waiting."""
    return kappa * duration * misalignment + carry_over(spread, horizon)


def edge_position(edge: float, threshold: float = THRESHOLD) -> float:
    """+1 if E > delta, -1 if E < -delta, else 0; NaN stays NaN (rules (3) and (5), 2009 p. 4). Rule (5) prints
    "< delta" for the long; the text of p. 2 ("exceeds ... by more than the threshold") gives -delta."""
    if not np.isfinite(edge):
        return np.nan
    return 1.0 if edge > threshold else (-1.0 if edge < -threshold else 0.0)


def oos_misalignments(spread_m: pd.Series, X: pd.DataFrame, min_train: int = MIN_TRAIN,
                      actual_weight: float = ACTUAL_WEIGHT) -> pd.Series:
    """m_tau for each month tau from a fit on months <= tau only (spec build step 6; the source re-estimates each
    quarter with only the data then available, 2009 p. 2). NaN where the fit or x_tau is missing."""
    out = pd.Series(np.nan, index=spread_m.index, name="m_oos")
    for tau in spread_m.index:
        x = X.loc[tau].to_numpy(float)
        if not np.all(np.isfinite(x)):
            continue
        f = fit_fair_value(spread_m.loc[:tau], X.loc[:tau], min_train)
        if f["coef"] is not None:
            out[tau] = spread_m[tau] - fair_spread(f["coef"], x, spread_m[tau], actual_weight)
    return out


def convergence_alpha(m: pd.Series, spread_m: pd.Series, horizon: int = HORIZON,
                      min_obs: int = MIN_ALPHA_OBS) -> tuple[float, int]:
    """Share of the gap that closes over `horizon` months: s_tau+h - s_tau = alpha (s*_tau - s_tau) + e, no
    intercept (eq. (1), 2009 p. 4). So alpha = -sum m ds / sum m^2. Pairs need m_tau and s_tau+h. Source values
    (FX): 0.2586 at 3 quarters, 0.5208 at 6 quarters (Table 2, p. 2). NaN with fewer than `min_obs` pairs."""
    fwd = spread_m.reindex(spread_m.index + pd.offsets.MonthEnd(horizon)).to_numpy(float)
    d = pd.DataFrame({"m": m.reindex(spread_m.index).to_numpy(float), "ds": fwd - spread_m.to_numpy(float)}).dropna()
    den = float((d["m"] ** 2).sum())
    if len(d) < min_obs or den <= 0:
        return np.nan, len(d)
    return -float((d["m"] * d["ds"]).sum()) / den, len(d)


def index_duration(bond_panel: pd.DataFrame | None, as_of: pd.Timestamp, dt: pd.Timestamp) -> float:
    """D_t: median `mod_dur` of the eligible bond_panel rows at as_of (spec Definition, our choice). NaN when the
    panel or its rows are missing."""
    if bond_panel is None or len(bond_panel) == 0 or "mod_dur" not in bond_panel:
        return np.nan
    p = bond_panel[(pd.to_datetime(bond_panel["available_at"]) <= dt) & (pd.to_datetime(bond_panel["date"]) == as_of)]
    need = {"carried", "years", "yield", "price", "g_spread"}
    if need <= set(p.columns):
        p = p[eligible(p)]
    d = p["mod_dur"].astype(float)
    d = d[np.isfinite(d) & (d > 0)]
    return float(d.median()) if len(d) else np.nan


# ---------------------------------------------------------------- compute


def compute(panels: Mapping[str, pd.DataFrame], as_of: pd.Timestamp, regressors: Sequence[str] = REGRESSORS,
            horizon: int = HORIZON, threshold: float = THRESHOLD, kappa: float | None = KAPPA,
            actual_weight: float = ACTUAL_WEIGHT, duration: float | None = None, min_train: int = MIN_TRAIN,
            max_stale_days: int = MAX_STALE_DAYS) -> pd.DataFrame:
    """One row for `index` = "US_HY" at as_of (spec build steps 1 to 6). score = E_t, higher = long. `kappa=None`
    uses the fitted alpha_h clipped to [0, 1]. Empty frame (columns COLS) without hy_index or macro_series."""
    as_of = pd.Timestamp(as_of) + pd.offsets.MonthEnd(0)
    hy, mac = panels.get("hy_index"), panels.get("macro_series")
    if hy is None or mac is None or len(hy) == 0 or len(mac) == 0:
        return pd.DataFrame(columns=COLS)
    dt = decision_time(as_of)
    hy = _public(hy, dt, ["date"])
    mac = _public(mac, dt, ["series_id", "date"])
    spread_m = monthly_spread(hy[hy["date"] <= as_of])
    row = {"date": as_of, "index": INDEX_KEY, "score": np.nan, "available_at": dt, "position": np.nan,
           "spread": np.nan, "fair_spread": np.nan, "misalignment": np.nan, "carry": np.nan, "duration": np.nan,
           "kappa": np.nan, "alpha_h": np.nan, "alpha_n": 0, "n_train": 0, "r2": np.nan, "status": "ok"}

    def done(status: str) -> pd.DataFrame:
        row["status"] = status
        return pd.DataFrame([row])[COLS].astype({"score": float})

    if as_of not in spread_m.index:
        return done("no_spread")
    row["spread"] = s = float(spread_m[as_of])
    X = macro_matrix(mac, spread_m.index, regressors, max_stale_days)
    x = X.loc[as_of].to_numpy(float)
    if not np.all(np.isfinite(x)):
        return done("stale_macro")
    fit = fit_fair_value(spread_m, X, min_train)
    row["n_train"], row["r2"] = fit["n"], fit["r2"]
    if fit["coef"] is None:
        return done("too_few_obs")
    row["fair_spread"] = fs = fair_spread(fit["coef"], x, s, actual_weight)
    row["misalignment"] = m = s - fs
    row["carry"] = carry_over(s, horizon)
    alpha, n_a = convergence_alpha(oos_misalignments(spread_m, X, min_train, actual_weight), spread_m, horizon)
    row["alpha_h"], row["alpha_n"] = alpha, n_a
    k = kappa if kappa is not None else (float(np.clip(alpha, 0.0, 1.0)) if np.isfinite(alpha) else np.nan)
    row["kappa"] = k
    D = float(duration) if duration is not None else index_duration(panels.get("bond_panel"), as_of, dt)
    row["duration"] = D
    if not np.isfinite(D):
        return done("no_duration")
    if not np.isfinite(k):
        return done("no_alpha")
    row["score"] = e = carry_adjusted_edge(m, s, D, horizon, k)
    row["position"] = edge_position(e, threshold)
    return done("ok")
