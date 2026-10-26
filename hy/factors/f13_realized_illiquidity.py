"""F13 Realized bond illiquidity (Amihud), level and shock (rank 13). Spec docs/factors/F13-realized-illiquidity.md;
methodology Section 8 (new signal), Section 7.2 (liquidity block) and Section 9.3 (exit cost). Sources: Lacava,
Ranaldo and Santucci de Magistris, "Realized Illiquidity" (2023), PDF pp. 7, 11 to 12, 21 to 24, 41; Deutsche Bank,
"Designing a Liquidity based Toolkit" (22 November 2016), PDF pp. 6, 12 to 14, 20 to 21. Pages are PDF pages.

    A_b,W     = sum_{k in W} |log p_k - log p_k-1| / sum_{k in W} nu_k        realized Amihud (eq. 5, p. 7)
    A^M_b,t   = |log(P_t / P_t-1)| / (V_t P_t / 100)                         monthly Amihud, I = 1 (pp. 7, 11): fallback
    L_b,t     = log(10^6 A_b,t)                                              log price move per $1mm traded
    L_b,t     = w + a_1 L_b,t-1 + a_3 Lbar^(3)_b,t-1 + a_12 Lbar^(12)_b,t-1 + e   pooled log-linear HAR (eq. 37, p. 41)
    shock     = L_b,t - Lhat_b,t                                             unexpected illiquidity (pp. 23 to 24)
    score     = z_cell(L_b,t) + SHOCK_WEIGHT z(shock)                         long illiquid bonds

Intuition: a bond whose price moves far per dollar traded is costly to exit, and holders ask a premium for it. A
shock raises expected illiquidity, so the price falls now and the expected return rises after (Lacava p. 23).

Prices. p_k are previous-tick prices sampled on a SAMPLE grid: the last trade price in each interval (p. 12: 5 to
10 minute sampling cuts the microstructure bias). Returns run between consecutive sampled prices inside the window,
across days too, so a bond that trades once a day still has returns. nu_k is the dollar volume (price / 100 x par).

Sparse bonds. A bond needs MIN_RETURNS sampled returns in month t (`measure` "trace"). With fewer, the window grows to
the EXTEND_MONTHS months t-2 .. t ("trace_3m"). With fewer still, or without TRACE trades, the bond takes the
monthly Amihud from `bond_panel` ("panel"). The two families never mix: each has its own HAR fit and its own z.

Inputs.
- `bond_panel` (production wiring 5, required): `date`, `cusip`, `gvkey`, `years`, `price`, `yield`, `g_spread`,
  `mod_dur`, `carried`, `n_trades`, `par_volume`, `bid_ask_pts`, `available_at`.
- `trace_trades` (new, optional): one row per cleaned TRACE trade. Columns `cusip`, `trade_time` (execution date and
  time), `price` (per 100), `par` (face value), `available_at` = trade day + `trace_bonds.DISSEMINATION_LAG` plus
  the WRDS load lag in a live run. `trades_from_trace` builds it. `trace_daily_flow` (F05) has no prices, so it
  cannot carry this measure.
- `ratings`, `leverage` (optional): rating class of the peer cell (`hy.factors.f04_bond_momentum.rating_classes`).

Output. compute() returns one row per eligible bond of `bond_panel` at as_of. Without `bond_panel` the frame is
empty. Without `trace_trades` every bond takes the panel measure, and `measure` says so. The cost gate columns
`illiq`, `impact_bp`, `illiq_pct`, `cost_rt` and `cost_gate_pass` serve other factors as a trade filter.
"""

from __future__ import annotations

from typing import Mapping

import numpy as np
import pandas as pd

from hy.backtest import decision_time, eligible, round_trip_cost
from hy.factors.f04_bond_momentum import DEFAULT_SYMBOLS, rating_classes
from hy.factors.f05_flow_pressure_reversal import winsorise
from hy.peers import maturity_bucket
from hy.sources import trace_bonds as tb

MIN_PAR = tb.MIN_PAR            # institutional trades only: par >= 100,000 (reader F-F7 proposal). Our choice
SAMPLE = "5min"                 # previous-tick sampling grid (Lacava p. 12: 5 to 10 minutes)
SCALE = 1e6                     # A per $1mm traded, so log A is near zero for a typical bond. Our choice
MIN_RETURNS = 5                 # fewest sampled returns a TRACE window needs. Our choice: the source is silent
EXTEND_MONTHS = 3               # sparse bonds: window t-2 .. t. Our choice
HAR_LAGS = (1, 3, 12)           # monthly HAR terms: month, quarter, year. Our choice: monthly form of 1, 5, 22 days (p. 21)
MIN_LAG_OBS = {3: 2, 12: 6}     # months a HAR mean needs, of 3 and of 12. Our choice
HIST_MONTHS = 36                # target months of the pooled HAR fit before t. Our choice
MIN_FIT = 200                   # bond-months the pooled fit needs, else the own-mean fallback. Our choice
MIN_OWN = 3                     # months of own history the fallback expectation needs. Our choice
CHANGE_MONTHS = 3               # liquidity change horizon: 63 trading days (reader F-F8 proposal; DB p. 6 uses 1 month)
MIN_CELL = 10                   # bonds a peer cell needs, else the next level. Our choice
CELL_LEVELS = ("rm", "r", "all")  # rating class x maturity bucket, then class, then all. Our choice
WINSOR = (0.01, 0.99)           # log A winsorised per family before z (F05 rule). Our choice
SHOCK_WEIGHT = 0.0              # weight of the shock z in score: 0 until the evaluation settles its sign (spec 9.1)
TRADE_SIZE = 1e6                # dollar size of the impact estimate. Our choice
GATE_PCT = 0.80                 # cost gate: the bond passes at or below this illiquidity percentile. Our choice
HOLD = 1                        # months held: monthly rebalance (DB p. 14 for the level, Lacava Table 7 monthly, p. 24)

META = {
    "rank": 13,
    "name": "Realized bond illiquidity (Amihud), level and shock",
    "level": "bond",
    "horizon_months": HOLD,
    "needs": ["bond_panel", "trace_trades", "ratings", "leverage"],
    "spec": "docs/factors/F13-realized-illiquidity.md",
    "section": "8",
}
REQUIRED = ("bond_panel",)

TRADE_COLS = ["cusip", "trade_time", "price", "par", "available_at"]
MEASURE_COLS = ["cusip", "illiq", "n_returns", "dollar_volume", "measure"]
COLS = ["date", "cusip", "score", "available_at", "gvkey", "measure", "illiq", "log_illiq", "n_returns",
        "dollar_volume", "expected", "shock", "shock_source", "illiq_change", "level_z", "shock_z", "rclass", "cell",
        "illiq_pct", "impact_bp", "cost_rt", "cost_gate_pass"]
FAMILY = {"trace": "trace", "trace_3m": "trace", "panel": "panel"}


# ---------------------------------------------------------------- panel trace_trades from TRACE trades


def trades_from_trace(trades: pd.DataFrame, min_par: float = MIN_PAR,
                      load_lag: pd.Timedelta = pd.Timedelta(0)) -> pd.DataFrame:
    """Panel `trace_trades` from cleaned TRACE trades (spec section 4, build step 1).

    Rows must be clean already: cancels, corrections and reversals gone, as `trace_panel.clean_trades` does. That
    function drops the execution time, so the export keeps `trd_exctn_tm`. Columns: `cusip_id`, `trd_exctn_dt`,
    `trd_exctn_tm` (optional, midnight when missing), price as `rptd_pr` or `pr`, par as `par` or
    `ascii_rptd_vol_tx` (a cap reads as its floor, `trace_bonds.parse_volume`). Trades under `min_par` drop out.
    available_at = trade day + DISSEMINATION_LAG + load_lag."""
    t = trades.copy()
    if "par" not in t.columns:
        t["par"] = t["ascii_rptd_vol_tx"].map(tb.parse_volume)
    day = pd.to_datetime(t["trd_exctn_dt"]).dt.normalize()
    tm = pd.to_timedelta(t["trd_exctn_tm"].astype(str)) if "trd_exctn_tm" in t.columns else pd.Timedelta(0)
    out = pd.DataFrame({"cusip": t["cusip_id"], "trade_time": day + tm,
                        "price": pd.to_numeric(t["rptd_pr"] if "rptd_pr" in t.columns else t["pr"], errors="coerce"),
                        "par": pd.to_numeric(t["par"], errors="coerce"),
                        "available_at": day + tb.DISSEMINATION_LAG + pd.Timedelta(load_lag)})
    out = out[(out["par"] >= min_par) & (out["price"] > 0)]
    return out[TRADE_COLS].sort_values(["cusip", "trade_time"]).reset_index(drop=True)


# ---------------------------------------------------------------- formulas (spec section 3)


def sample_prices(trades: pd.DataFrame, freq: str = SAMPLE) -> pd.DataFrame:
    """Previous-tick sampling (spec section 3; Lacava p. 12). One row per cusip and `freq` interval with a trade:
    `price` = the last trade price of the interval, `dollar_volume` = sum of price / 100 x par over all its trades.
    Intuition: trades inside one interval are one price observation, so bid-ask bounce inside it drops out."""
    t = trades.sort_values(["cusip", "trade_time"], kind="stable")
    g = t.assign(bucket=t["trade_time"].dt.floor(freq), dv=t["price"] / 100.0 * t["par"]).groupby(
        ["cusip", "bucket"], sort=True)
    return pd.DataFrame({"price": g["price"].last(), "dollar_volume": g["dv"].sum(),
                         "n_trades": g["price"].size()}).reset_index()


def realized_amihud(sampled: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp, scale: float = SCALE) -> pd.DataFrame:
    """A = RPV / nu per cusip over the window [start, end] (eq. 5, p. 7), times `scale`.

    RPV = sum of |log p_k - log p_k-1| over consecutive sampled prices inside the window (realized absolute
    variation, p. 7). nu = dollar volume of the window. No return links to a price before `start`. A = NaN when
    nu = 0 or RPV = 0. Columns cusip, illiq, n_returns, dollar_volume."""
    s = sampled[(sampled["bucket"] >= start) & (sampled["bucket"] <= end)]
    lp = np.log(s["price"].astype(float))
    r = lp.groupby(s["cusip"]).diff().abs()
    g = pd.DataFrame({"cusip": s["cusip"], "r": r, "dv": s["dollar_volume"]}).groupby("cusip")
    out = pd.DataFrame({"rpv": g["r"].sum(), "n_returns": g["r"].count(), "dollar_volume": g["dv"].sum()})
    out["illiq"] = (scale * out["rpv"] / out["dollar_volume"]).where((out["dollar_volume"] > 0) & (out["rpv"] > 0))
    return out.reset_index()[["cusip", "illiq", "n_returns", "dollar_volume"]]


def trace_measure(sampled: pd.DataFrame, month_end: pd.Timestamp, min_returns: int = MIN_RETURNS,
                  extend_months: int = EXTEND_MONTHS, scale: float = SCALE) -> pd.DataFrame:
    """TRACE measure per cusip at month end t (spec build step 3). Month t first ("trace"). A bond with fewer than
    `min_returns` returns takes the window of the last `extend_months` months ("trace_3m"). A bond with fewer still
    has no TRACE measure. Columns MEASURE_COLS."""
    t = pd.Timestamp(month_end) + pd.offsets.MonthEnd(0)
    end = t + pd.Timedelta(1, unit="D") - pd.Timedelta(1, unit="ns")
    one = realized_amihud(sampled, t - pd.offsets.MonthBegin(1), end, scale).assign(measure="trace")
    wide = realized_amihud(sampled, t - pd.offsets.MonthEnd(extend_months) + pd.Timedelta(1, unit="D"), end,
                           scale).assign(measure="trace_3m")
    ok1 = one[(one["n_returns"] >= min_returns) & one["illiq"].notna()]
    ok3 = wide[(wide["n_returns"] >= min_returns) & wide["illiq"].notna() & ~wide["cusip"].isin(ok1["cusip"])]
    return pd.concat([ok1, ok3], ignore_index=True)[MEASURE_COLS]


def panel_measure(panel: pd.DataFrame, month_end: pd.Timestamp, scale: float = SCALE) -> pd.DataFrame:
    """Monthly Amihud with one return, A^M = |log(P_t / P_t-1)| / (par_volume_t x P_t / 100) (eq. 5 with I = 1,
    pp. 7, 11), times `scale` (spec build step 4). Both rows real trades (not carried), exactly one month apart,
    par_volume > 0. NaN when the price did not move. Intuition: the coarse fallback the source calls the daily
    Amihud, three times noisier than its high-low twin (p. 11). Columns MEASURE_COLS."""
    t = pd.Timestamp(month_end)
    if "par_volume" not in panel.columns:
        return pd.DataFrame(columns=MEASURE_COLS)
    p = panel[~panel["carried"].astype(bool)]
    now = p[p["date"] == t].drop_duplicates("cusip", keep="last").set_index("cusip")
    prev = p[p["date"] == t - pd.offsets.MonthEnd(1)].drop_duplicates("cusip", keep="last").set_index("cusip")
    x = now.join(prev[["price"]].rename(columns={"price": "prev"}), how="inner")
    dv = x["par_volume"].astype(float) * x["price"].astype(float) / 100.0
    r = np.log(x["price"].astype(float) / x["prev"].astype(float)).abs()
    out = pd.DataFrame({"illiq": (scale * r / dv).where((dv > 0) & (r > 0)), "n_returns": 1, "dollar_volume": dv,
                        "measure": "panel"}).dropna(subset=["illiq"])
    return out.rename_axis("cusip").reset_index()[MEASURE_COLS]


def har_terms(wide: pd.DataFrame, lags: tuple[int, ...] = HAR_LAGS,
              min_obs: Mapping[int, int] = MIN_LAG_OBS) -> dict[int, pd.DataFrame]:
    """HAR regressors per month and cusip from `wide` (months x cusip of L, consecutive month ends): lag 1 is
    L_t-1, lag k > 1 is the mean of L_t-k .. L_t-1 with at least min_obs[k] values (eq. 37, p. 41, monthly form).
    Intuition: last month, last quarter and last year each predict this month."""
    past = wide.shift(1)
    return {k: past if k == 1 else past.rolling(k, min_periods=min_obs.get(k, k)).mean() for k in lags}


def fit_har(y: np.ndarray, x: np.ndarray) -> np.ndarray:
    """OLS of y on [1, x] (eq. 37, p. 41, without the leverage term). Returns [w, a_1, a_3, a_12]."""
    design = np.column_stack([np.ones(len(y)), x])
    return np.linalg.lstsq(design, y, rcond=None)[0]


def illiquidity_shock(wide: pd.DataFrame, as_of: pd.Timestamp, hist_months: int = HIST_MONTHS,
                      min_fit: int = MIN_FIT, min_own: int = MIN_OWN) -> pd.DataFrame:
    """Expected L, shock = L_t - Lhat_t, and its source per cusip at month end t (spec section 3, build step 5).

    Lhat from the pooled HAR fitted on target months t-hist_months .. t-1 only ("har"). A bond without all HAR terms
    at t, or a fit with fewer than `min_fit` bond-months, takes the mean of its own last 12 months with at least
    `min_own` values ("own"). Intuition: the residual is the unexpected illiquidity of Lacava pp. 23 to 24."""
    t = pd.Timestamp(as_of)
    terms = har_terms(wide)
    stack = pd.concat({k: v.stack() for k, v in terms.items()}, axis=1)
    stack["y"] = wide.stack()
    fit_months = wide.index[(wide.index < t) & (wide.index >= t - pd.offsets.MonthEnd(hist_months))]
    train = stack[stack.index.get_level_values(0).isin(fit_months)].dropna()
    cur = wide.loc[t] if t in wide.index else pd.Series(dtype=float)
    out = pd.DataFrame(index=cur.dropna().index)
    out["expected"], out["shock_source"] = np.nan, None
    if len(train) >= min_fit:
        coef = fit_har(train["y"].to_numpy(), train[list(HAR_LAGS)].to_numpy())
        xt = pd.concat({k: terms[k].loc[t] for k in HAR_LAGS}, axis=1).reindex(out.index).dropna()
        out.loc[xt.index, "expected"] = coef[0] + xt.to_numpy() @ coef[1:]
        out.loc[xt.index, "shock_source"] = "har"
    own = wide.shift(1).rolling(12, min_periods=min_own).mean()
    own_t = own.loc[t].reindex(out.index) if t in own.index else pd.Series(np.nan, index=out.index)
    fill = out["expected"].isna() & own_t.notna()
    out.loc[fill, "expected"] = own_t[fill]
    out.loc[fill, "shock_source"] = "own"
    out["shock"] = cur.reindex(out.index) - out["expected"]
    return out.rename_axis("cusip")


def peer_z(x: pd.Series, keys: pd.DataFrame, min_cell: int = MIN_CELL) -> tuple[pd.Series, pd.Series]:
    """z of x inside the first cell level of CELL_LEVELS with `min_cell` scored bonds (spec section 3). NaN where no
    level qualifies or the cell sd is zero. Returns z and the cell used. Intuition: a CCC bond is compared with CCC
    bonds of its maturity, so the score is not a rating or a maturity bet."""
    z = pd.Series(np.nan, index=x.index)
    used = pd.Series(None, index=x.index, dtype=object)
    for level in CELL_LEVELS:
        k = keys[level].where(x.notna())          # the cell holds all its scored bonds, not only the unplaced ones
        n = k.groupby(k).transform("count")
        ok = k.notna() & (n >= min_cell)
        g = x.where(ok).groupby(k.where(ok))
        sd = g.transform("std")
        zz = ((x - g.transform("mean")) / sd.where(sd > 0)).where(ok)
        hit = zz.notna() & z.isna()
        z[hit], used[hit] = zz[hit], level + ":" + k[hit].astype(str)
    return z, used


def cost_gate(illiq: pd.Series, family: pd.Series, trade_size: float = TRADE_SIZE, scale: float = SCALE,
              gate_pct: float = GATE_PCT) -> pd.DataFrame:
    """Cost gate columns (spec section 3, cost gate). impact_bp = A x trade_size x 10^4: the price move in bp that
    a `trade_size` trade carries at the measured impact. illiq_pct = percentile rank of A inside its family.
    cost_gate_pass = illiq_pct <= gate_pct. A bond without a measure fails the gate."""
    a = illiq / scale
    pct = illiq.groupby(family).rank(pct=True)
    return pd.DataFrame({"impact_bp": a * trade_size * 1e4, "illiq_pct": pct,
                         "cost_gate_pass": (pct <= gate_pct).fillna(False).astype(bool)}, index=illiq.index)


# ---------------------------------------------------------------- one month end


def _wide(frames: dict[pd.Timestamp, pd.DataFrame], months: pd.DatetimeIndex) -> pd.DataFrame:
    """Months x cusip of L = log A from the per-month measure frames."""
    parts = {m: f.set_index("cusip")["illiq"] for m, f in frames.items() if len(f)}
    if not parts:
        return pd.DataFrame(index=months, dtype=float)
    return np.log(pd.DataFrame(parts).T.reindex(months).astype(float))


def compute(panels: Mapping[str, pd.DataFrame], as_of: pd.Timestamp, sample: str = SAMPLE,
            min_returns: int = MIN_RETURNS, extend_months: int = EXTEND_MONTHS, hist_months: int = HIST_MONTHS,
            min_fit: int = MIN_FIT, min_cell: int = MIN_CELL, shock_weight: float = SHOCK_WEIGHT,
            gate_pct: float = GATE_PCT) -> pd.DataFrame:
    """F13 score per eligible bond of bond_panel at as_of (spec build steps 2 to 8). One row per cusip.

    Reads only rows with available_at <= decision_time(as_of). Each bond takes its TRACE measure where one exists,
    else the panel measure. score = level z inside the cell + shock_weight x shock z, NaN without a level. A raw
    D or SD rating has no score. Empty frame (columns COLS) without bond_panel. Higher score = long."""
    as_of = pd.Timestamp(as_of)
    if any(panels.get(k) is None or len(panels[k]) == 0 for k in REQUIRED):
        return pd.DataFrame(columns=COLS)
    dt = decision_time(as_of)
    panel = panels["bond_panel"]
    panel = panel[panel["available_at"] <= dt].copy()
    panel["date"] = pd.to_datetime(panel["date"]) + pd.offsets.MonthEnd(0)
    trades = panels.get("trace_trades")
    sampled = None
    if trades is not None and len(trades):
        tr = trades[(trades["available_at"] <= dt) & (pd.to_datetime(trades["trade_time"]) < dt)].copy()
        tr["trade_time"] = pd.to_datetime(tr["trade_time"])
        sampled = sample_prices(tr, sample) if len(tr) else None
    months = pd.date_range(end=as_of, periods=hist_months + max(HAR_LAGS) + 1, freq="ME")
    fam = {"panel": {m: panel_measure(panel, m) for m in months}}
    if sampled is not None:
        fam["trace"] = {m: trace_measure(sampled, m, min_returns, extend_months) for m in months}

    now = panel[panel["date"] == as_of]
    now = now[eligible(now)].drop_duplicates("cusip", keep="last")
    out = now[["cusip", "gvkey", "years"]].set_index("cusip")
    cur = pd.concat([fam[f][as_of].assign(order=i) for i, f in enumerate(("trace", "panel")) if f in fam])
    cur = cur.sort_values("order").drop_duplicates("cusip", keep="first").set_index("cusip")
    out = out.join(cur[["measure", "illiq", "n_returns", "dollar_volume"]])
    out["family"] = out["measure"].map(FAMILY)
    out["log_illiq"] = np.log(out["illiq"].astype(float))
    out["expected"], out["shock"], out["shock_source"], out["illiq_change"] = np.nan, np.nan, None, np.nan
    for f, frames in fam.items():
        wide = _wide(frames, months)
        mine = out.index[out["family"] == f]
        sh = illiquidity_shock(wide, as_of, hist_months, min_fit).reindex(mine)
        out.loc[mine, ["expected", "shock", "shock_source"]] = sh[["expected", "shock", "shock_source"]].to_numpy()
        lag = wide.loc[as_of - pd.offsets.MonthEnd(CHANGE_MONTHS)] if len(wide.columns) else pd.Series(dtype=float)
        out.loc[mine, "illiq_change"] = out.loc[mine, "log_illiq"] - lag.reindex(mine)

    ratings = panels.get("ratings")
    if ratings is not None and len(ratings):
        cls = rating_classes(ratings, panels.get("leverage"), as_of)
        out["rclass"] = out["gvkey"].map(cls["rclass"])
        out.loc[out["gvkey"].map(cls["raw"]).isin(DEFAULT_SYMBOLS), "log_illiq"] = np.nan
    else:
        out["rclass"] = None
    bucket = out["years"].astype(float).map(maturity_bucket).astype(str)
    fkey = out["family"].astype(str)
    keys = pd.DataFrame({"rm": (fkey + "|" + out["rclass"].astype(str) + "|" + bucket).where(out["rclass"].notna()),
                         "r": (fkey + "|" + out["rclass"].astype(str)).where(out["rclass"].notna()),
                         "all": fkey}, index=out.index)
    lev = pd.Series(np.nan, index=out.index)
    shk = pd.Series(np.nan, index=out.index)
    for f in fam:
        m = out["family"] == f
        lev[m] = winsorise(out.loc[m, "log_illiq"].astype(float))
        s = out.loc[m, "shock"].astype(float)
        shk[m] = (s - s.mean()) / s.std() if s.notna().sum() > 1 and s.std() > 0 else np.nan
    out["level_z"], out["cell"] = peer_z(lev, keys, min_cell)
    out["shock_z"] = shk.where(out["level_z"].notna())
    out["score"] = out["level_z"] + shock_weight * out["shock_z"].fillna(0.0)
    out = out.join(cost_gate(out["illiq"].astype(float), out["family"], gate_pct=gate_pct))
    out["cost_rt"] = (round_trip_cost(now.set_index("cusip").assign(date=as_of)).reindex(out.index)
                      if "bid_ask_pts" in now.columns else np.nan)
    out["measure"] = out["measure"].fillna("no_measure")
    out["date"] = as_of
    out["available_at"] = dt
    out = out.reset_index()
    return out[COLS].astype({"score": float, "level_z": float, "shock_z": float, "illiq": float}).reset_index(drop=True)
