"""Within-sector long-short pairs for concentrated positions. Spec docs/factors/SECTOR-models.md, section 3.3;
methodology Sections 7.5 (convergence), 8 S1 and S4 (pair trades; "size by jump-to-default, not by DV01"), 9.3.

Per GICS sector at month end t, from a bond score (default: the hy.sector.fairspread residual z):

    longs     = bonds with score >= the sector's (1 - CAND_Q) quantile and score > 0      cheap
    shorts    = bonds with score <= the sector's CAND_Q quantile and score < 0             rich
    match     "dts":    |log DTS_L - log DTS_S| <= log(1 + DTS_TOL)
              "bucket": same rating class and maturity bucket (hy.peers.maturity_bucket)
    pick      the richest admissible short for each long, cheapest long first; one issuer per pair leg, no reuse
    h         = DTS_L / DTS_S = s_L D_L / (s_S D_S)      short market value per unit long (hy.factors.f22.dts_hedge)
    conv      = D_L q (s_L - f_L) - h D_S q (s_S - f_S),  q = 1 - rho^H       expected convergence (Section 7.5)
    carry     = (H / 12) (s_L - h s_S)                                       spread carry of the pair over H months
    JTD_L     = 1 - 100 R_L / P_L,   JTD_S = h (1 - 100 R_S / P_S)           default loss of the long, gain of the short
    jtd_ratio = JTD_L / JTD_S;  jtd_ok = jtd_ratio <= JTD_MAX

All returns are per unit of long market value, decimals, before cost. f is the fair spread of hy.sector.fairspread.
R is the recovery of the rating class middle notch, (70 - 3 r)% (F06 `recovery_rate`, Martin p. 19).

Intuition: inside one sector the two legs share the sector's spread moves. With DTS equal on both legs, a parallel
sector move in log spread cancels, and the pair earns the closing of the two residuals. The JTD check guards the
trap of methodology S4: a pair can be DTS neutral and still lose far more on a default of the long than it gains on
a default of the short, because the long is the wider, riskier credit.

Panels. Required: `bond_panel`, `gics`, `leverage` (for the default score). Optional: `ratings` (classes, bucket
match, recovery), `residual_history` (`date`, `cusip`, `resid_log`, `available_at`: past fair-spread residuals; the
pooled AR(1) per sector gives rho). Without `residual_history` rho comes from HALF_LIFE. A missing required panel
gives an empty frame.
"""

from __future__ import annotations

from typing import Mapping

import numpy as np
import pandas as pd

from hy.backtest import decision_time
from hy.factors.f06_issuer_curve_residual import CLASS_NOTCH, DEFAULT_NOTCH, recovery_rate
from hy.factors.f22_curve_shape import dts_hedge
from hy.fairspread import expected_convergence_return, fit_ar1
from hy.rv import SENIOR_UNSECURED_LGD
from hy.sector import fairspread
from hy.sector.common import month_end, present, universe

N_PAIRS = 3            # pairs per sector: a concentrated book (our choice)
CAND_Q = 0.25          # long candidates: the top quarter of the sector's scores; shorts: the bottom quarter (our choice)
DTS_TOL = 0.5          # DTS match: the larger DTS at most 1.5 times the smaller (our choice)
HORIZON = 6            # months of the expected return (our choice; equals two half-lives, Section 7.5)
HALF_LIFE = 3.0        # months: default residual half-life without history (our choice: H = two half-lives, 7.5)
MIN_HIST_PAIRS = 24    # residual pairs the pooled AR(1) needs (our choice)
JTD_MAX = 1.5          # the long's default loss at most 1.5 times the short's default gain (our choice)
MODES = ("dts", "bucket")

META = {
    "rank": None,
    "name": "Within-sector long-short pairs",
    "level": "bond",
    "horizon_months": HORIZON,
    "needs": ["bond_panel", "gics", "leverage", "ratings", "residual_history"],
    "spec": "docs/factors/SECTOR-models.md",
    "section": "7.5; 8 S1, S4; 9.3",
}
REQUIRED = ("bond_panel", "gics", "leverage")

PAIR_COLS = ["date", "gsector", "group", "pair_id", "mode", "long_cusip", "long_gvkey", "short_cusip", "short_gvkey",
             "score", "available_at", "long_score", "short_score", "s_long", "s_short", "fair_long", "fair_short",
             "dur_long", "dur_short", "dts_long", "dts_short", "hedge_ratio", "net_dts", "net_dur", "rho",
             "close_share", "exp_conv", "carry", "exp_return", "rec_long", "rec_short", "jtd_loss_long",
             "jtd_gain_short", "jtd_net", "jtd_ratio", "jtd_ok", "hedge_jtd"]
LEG_COLS = ["date", "cusip", "score", "available_at", "gvkey", "gsector", "group", "pair_id", "leg", "weight",
            "mode", "hedge_ratio", "exp_conv", "carry", "exp_return", "jtd_ratio", "jtd_ok"]


# ---------------------------------------------------------------- formula helpers


def class_recovery(rclass) -> float:
    """Recovery per unit of par for a rating class: F06 (70 - 3 r)% at the class middle notch (BB 34%, B 25%, CCC
    16%); without a class, 1 - hy.rv.SENIOR_UNSECURED_LGD (40%)."""
    if isinstance(rclass, str) and rclass in CLASS_NOTCH:
        return recovery_rate(CLASS_NOTCH[rclass])
    return 1.0 - SENIOR_UNSECURED_LGD


def jtd_unit(price: float, recovery: float) -> float:
    """Loss per unit of market value when the bond defaults to `recovery` x par: 1 - 100 R / P (P per 100 par)."""
    return float(1.0 - 100.0 * recovery / price) if price and price > 0 else np.nan


def rho_from_half_life(half_life: float) -> float:
    """Monthly persistence from a half-life in months: rho = 0.5^(1 / h_1/2) (Section 7.5 inverted)."""
    return float(0.5 ** (1.0 / half_life)) if half_life and half_life > 0 else 0.0


def pooled_rho(history: pd.DataFrame | None, cusips, dt: pd.Timestamp, min_pairs: int = MIN_HIST_PAIRS) -> float:
    """Pooled AR(1) of the monthly fair-spread residuals of `cusips` (hy.fairspread.fit_ar1 on the stacked series,
    each bond's series demeaned and separated by a NaN). Rows with available_at > dt drop out. NaN with fewer than
    `min_pairs` consecutive-month pairs."""
    if history is None or not len(history):
        return np.nan
    h = history[(pd.to_datetime(history["available_at"]) <= dt) & history["cusip"].isin(set(cusips))].copy()
    if h.empty:
        return np.nan
    h["date"] = pd.to_datetime(h["date"]) + pd.offsets.MonthEnd(0)
    series, n_pairs = [], 0
    for _, g in h.sort_values("available_at").drop_duplicates(["cusip", "date"], keep="last").groupby("cusip"):
        s = g.set_index("date")["resid_log"].astype(float).sort_index()
        s = s.reindex(pd.date_range(s.index.min(), s.index.max(), freq="ME"))
        s = s - s.mean()
        n_pairs += int((s.notna() & s.shift(1).notna()).sum())
        series.append(np.r_[s.to_numpy(), np.nan])
    if n_pairs < min_pairs:
        return np.nan
    return fit_ar1(np.concatenate(series))


def pair_metrics(L: pd.Series, S: pd.Series, rho: float, horizon: int = HORIZON) -> dict:
    """Hedge, convergence, carry and JTD of one pair (module docstring), per unit of long market value."""
    h = dts_hedge(L["g_spread"], L["mod_dur"], S["g_spread"], S["mod_dur"])
    m_l, m_s = (L["g_spread"] - L["s_fair"]) * 1e4, (S["g_spread"] - S["s_fair"]) * 1e4
    conv = float(expected_convergence_return(0.0, L["mod_dur"], rho, horizon, m_l)
                 - h * expected_convergence_return(0.0, S["mod_dur"], rho, horizon, m_s))
    carry = horizon / 12.0 * (L["g_spread"] - h * S["g_spread"])
    r_l, r_s = class_recovery(L["rclass"]), class_recovery(S["rclass"])
    j_l, j_s_unit = jtd_unit(L["price"], r_l), jtd_unit(S["price"], r_s)
    j_s = h * j_s_unit
    return {"hedge_ratio": h, "net_dts": L["dts"] - h * S["dts"], "net_dur": L["mod_dur"] - h * S["mod_dur"],
            "rho": rho, "close_share": 1.0 - max(rho, 0.0) ** horizon, "exp_conv": conv, "carry": carry,
            "exp_return": conv + carry, "rec_long": r_l, "rec_short": r_s, "jtd_loss_long": j_l,
            "jtd_gain_short": j_s, "jtd_net": j_s - j_l, "jtd_ratio": j_l / j_s if j_s > 0 else np.nan,
            "jtd_ok": bool(j_s > 0 and j_l / j_s <= JTD_MAX), "hedge_jtd": j_l / j_s_unit if j_s_unit > 0 else np.nan}


def select_pairs(sub: pd.DataFrame, mode: str = "dts", n_pairs: int = N_PAIRS, cand_q: float = CAND_Q,
                 dts_tol: float = DTS_TOL) -> list[tuple]:
    """(long index, short index) pairs inside one sector (module docstring: candidates, match, pick)."""
    c = sub[sub["score"].notna() & (sub["dts"] > 0)]
    if len(c) < 2:
        return []
    hi, lo = c["score"].quantile(1.0 - cand_q), c["score"].quantile(cand_q)
    longs = c[(c["score"] >= hi) & (c["score"] > 0)].sort_values("score", ascending=False)
    shorts = c[(c["score"] <= lo) & (c["score"] < 0)]
    used: set = set()
    out = []
    for i, L in longs.iterrows():
        if len(out) >= n_pairs:
            break
        if L["gvkey"] in used:
            continue
        pool = shorts[~shorts["gvkey"].isin(used | {L["gvkey"]})]
        if mode == "bucket":
            pool = pool[pool["rclass"].notna() & (pool["rclass"] == L["rclass"]) & (pool["mat_bucket"] == L["mat_bucket"])]
        else:
            pool = pool[np.abs(np.log(pool["dts"] / L["dts"])) <= np.log1p(dts_tol)]
        if pool.empty:
            continue
        j = pool.assign(dd=np.abs(np.log(pool["dts"] / L["dts"]))).sort_values(["score", "dd"]).index[0]
        out.append((i, j))
        used |= {L["gvkey"], pool.loc[j, "gvkey"]}
    return out


# ---------------------------------------------------------------- panel steps


def _scored(panels: Mapping[str, pd.DataFrame], as_of: pd.Timestamp, scores: pd.DataFrame | None) -> pd.DataFrame:
    """Universe bonds with `score` (from `scores` by cusip, else the sector fair-spread z) and `s_fair`."""
    u = universe(panels, as_of)
    if u.empty:
        return u
    fs = fairspread.compute(panels, as_of)
    fair = fs.set_index("cusip")["s_fair"] if len(fs) else pd.Series(dtype=float)
    src = fs if scores is None else scores
    sc = src.dropna(subset=["score"]).drop_duplicates("cusip", keep="last").set_index("cusip") if len(src) else None
    u["score"] = u["cusip"].map(sc["score"]).astype(float) if sc is not None else np.nan
    if sc is not None and "s_fair" in sc:
        u["s_fair"] = u["cusip"].map(sc["s_fair"]).astype(float)
    else:
        u["s_fair"] = u["cusip"].map(fair).astype(float)
    return u


def pairs(panels: Mapping[str, pd.DataFrame], as_of, scores: pd.DataFrame | None = None, mode: str = "dts",
          n_pairs: int = N_PAIRS, horizon: int = HORIZON, half_life: float = HALF_LIFE,
          drop_jtd_fail: bool = False) -> pd.DataFrame:
    """Pair table at month end as_of (spec section 3.3). One row per pair, columns PAIR_COLS.

    `scores` is any bond score frame (cusip, score; optional s_fair), for example the hy.sector.relative composite.
    score = long score - short score. With `drop_jtd_fail` a pair that fails the JTD check is left out."""
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    as_of = month_end(as_of)
    if any(not present(panels, k) for k in REQUIRED):
        return pd.DataFrame(columns=PAIR_COLS)
    dt = decision_time(as_of)
    u = _scored(panels, as_of, scores)
    if u.empty:
        return pd.DataFrame(columns=PAIR_COLS)
    rows = []
    for sec, sub in u.groupby("gsector"):
        rho = pooled_rho(panels.get("residual_history"), sub["cusip"], dt)
        if not np.isfinite(rho):
            rho = rho_from_half_life(half_life)
        for k, (i, j) in enumerate(select_pairs(sub, mode, n_pairs)):
            L, S = sub.loc[i], sub.loc[j]
            m = pair_metrics(L, S, rho, horizon)
            if drop_jtd_fail and not m["jtd_ok"]:
                continue
            rows.append({"date": as_of, "gsector": sec, "group": L["group"], "pair_id": f"{sec}-{k + 1}",
                         "mode": mode, "long_cusip": L["cusip"], "long_gvkey": L["gvkey"], "short_cusip": S["cusip"],
                         "short_gvkey": S["gvkey"], "score": L["score"] - S["score"], "available_at": dt,
                         "long_score": L["score"], "short_score": S["score"], "s_long": L["g_spread"],
                         "s_short": S["g_spread"], "fair_long": L["s_fair"], "fair_short": S["s_fair"],
                         "dur_long": L["mod_dur"], "dur_short": S["mod_dur"], "dts_long": L["dts"],
                         "dts_short": S["dts"], **m})
    return pd.DataFrame(rows, columns=PAIR_COLS)


def legs(pair_table: pd.DataFrame) -> pd.DataFrame:
    """One row per leg (columns LEG_COLS): weight +1 on the long, -hedge_ratio on the short (market value per unit
    long). score = +pair score on the long leg and -pair score on the short leg, so higher = long."""
    if pair_table.empty:
        return pd.DataFrame(columns=LEG_COLS)
    shared = ["date", "available_at", "gsector", "group", "pair_id", "mode", "hedge_ratio", "exp_conv", "carry",
              "exp_return", "jtd_ratio", "jtd_ok"]
    lo = pair_table[shared].assign(cusip=pair_table["long_cusip"], gvkey=pair_table["long_gvkey"], leg="long",
                                   weight=1.0, score=pair_table["score"])
    sh = pair_table[shared].assign(cusip=pair_table["short_cusip"], gvkey=pair_table["short_gvkey"], leg="short",
                                   weight=-pair_table["hedge_ratio"], score=-pair_table["score"])
    return pd.concat([lo, sh], ignore_index=True)[LEG_COLS].sort_values(["pair_id", "leg"]).reset_index(drop=True)


def compute(panels: Mapping[str, pd.DataFrame], as_of, **params) -> pd.DataFrame:
    """Factor-contract entry: the pair legs at month end as_of (`legs(pairs(panels, as_of, **params))`)."""
    return legs(pairs(panels, as_of, **params))
