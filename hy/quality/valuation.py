"""Quality-adjusted valuation: the spread the market pays per unit of quality (spec docs/factors/QUALITY-rotation.md,
Definition 2). Methodology Section 7.4 (spread per unit of risk) and Section 8 (S1 fair value residual).

    y_i      = log s_i                       (y_kind "log", default)    or  s_i  ("level")
    y_i      = a_t + b_t Q_i + c_t log D_i + e_i   ("log")   or   a_t + b_t Q_i + c_t D_i + e_i   ("level")
    gap_i    = s_i - s_hat_i                 spread gap in decimals
    conv_i   = D_i gap_i                     price return per unit market value if the gap closes

Fit by OLS each month over the non-distressed eligible bonds (spread <= hy.backtest.DISTRESSED_SPREAD) that have a
quality score. Intuition: e > 0 means the bond pays more than its quality and duration justify, so it is cheap.
The form follows the empirical value measure of Israel, Palhares, Richardson (2018, p. 27: log OAS on log duration,
rating, volatility) with the quality score in place of rating. Our choice: quality in place of rating, so the fit
asks what the market pays per unit of fundamentals.

Groups. High quality (HQ) and low quality (LQ) come from the quality quintile (`hq_def="score"`: quintile 5 and 1),
from the rating bucket (`"rating"`: bucket in hq_ratings or lq_ratings), or from both (`"both"`). Cheap HQ = HQ with
e > 0, ranked by e descending. Rich LQ = LQ with e < 0, ranked by e ascending. The mirror pair (cheap LQ, rich HQ)
serves the down-in-quality expression.
"""

from __future__ import annotations

from typing import Mapping

import numpy as np
import pandas as pd

from hy.backtest import DISTRESSED_SPREAD, MIN_BONDS, decision_time
from hy.factors import f08_lever_event_risk as f08
from hy.factors import f16_downside_risk as f16
from hy.quality import score as qs

Y_KINDS = ("log", "level")
HQ_DEFS = ("score", "rating", "both")
HQ_QUINTILE, LQ_QUINTILE = 5, 1                  # top and bottom quality quintile (task definition)
# Rating bucket presets (task examples): BB against B and CCC; the BBB/BB crossover against CCC; BB against CCC.
BUCKET_PRESETS: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "bb_vs_bccc": (("BB",), ("B", "CCC")),
    "crossover_vs_ccc": (("BBB", "BB"), ("CCC",)),
    "bb_vs_ccc": (("BB",), ("CCC",)),
}
DEFAULT_PRESET = "bb_vs_bccc"                    # our choice: the first example of the task
MIN_FIT = MIN_BONDS                              # bonds the monthly fit needs (hy.backtest, our choice)

META = {
    "rank": None,
    "name": "Quality-adjusted valuation residual",
    "level": "bond",
    "horizon_months": 12,
    "needs": qs.META["needs"],
    "spec": "docs/factors/QUALITY-rotation.md",
    "section": "7.4; 8 S1",
}

COLS = ["date", "cusip", "score", "available_at", "gvkey", "kind", "quality_rank", "quintile", "rclass",
        "rclass_src", "rating_bucket", "fund_rank", "rating_rank", "blend_rank", "fund_rating_gap", "gap_flag",
        "sector", "g_spread", "mod_dur", "years", "price", "dts", "fitted_spread", "resid", "spread_gap",
        "conv_return", "fit_n", "fit_b_quality", "is_hq", "is_lq", "cheap_hq", "rich_lq", "cheap_lq", "rich_hq",
        "cheap_hq_rank", "rich_lq_rank", "cheap_lq_rank", "rich_hq_rank", "lever", "var5"]


def fit_residuals(df: pd.DataFrame, quality: str = "quality_rank", y_kind: str = "log",
                  min_fit: int = MIN_FIT) -> tuple[pd.DataFrame, dict]:
    """One cross-sectional OLS (spec Definition 2). Fit rows: finite spread > 0 and <= DISTRESSED_SPREAD, mod_dur >
    0, quality present. Residuals for every row with inputs. Returns (frame with fitted_spread, resid, spread_gap,
    conv_return; dict with n, coef). Fewer than `min_fit` fit rows gives NaN everywhere."""
    if y_kind not in Y_KINDS:
        raise ValueError(f"y_kind must be one of {Y_KINDS}")
    s, d, q = (df[c].astype(float) for c in ("g_spread", "mod_dur", quality))
    ok = (s > 0) & (d > 0) & q.notna() & np.isfinite(s) & np.isfinite(d)
    fit = ok & (s <= DISTRESSED_SPREAD)
    out = pd.DataFrame(np.nan, index=df.index, columns=["fitted_spread", "resid", "spread_gap", "conv_return"])
    info = {"n": int(fit.sum()), "coef": None}
    if fit.sum() < min_fit:
        return out, info
    dx = np.log(d) if y_kind == "log" else d
    y = np.log(s) if y_kind == "log" else s
    X = np.column_stack([np.ones(len(df)), q.fillna(0.0), dx.where(ok, 0.0)])
    coef, *_ = np.linalg.lstsq(X[fit.to_numpy()], y[fit].to_numpy(), rcond=None)
    yhat = pd.Series(X @ coef, index=df.index).where(ok)
    out["resid"] = (y - yhat).where(ok)
    out["fitted_spread"] = np.exp(yhat) if y_kind == "log" else yhat
    out["spread_gap"] = s - out["fitted_spread"]
    out["conv_return"] = d * out["spread_gap"]
    info["coef"] = coef
    return out, info


def groups(df: pd.DataFrame, hq_def: str = "score", hq_ratings=None, lq_ratings=None) -> tuple[pd.Series, pd.Series]:
    """is_hq and is_lq masks (spec Definition 2, Groups). Rating buckets default to BUCKET_PRESETS[DEFAULT_PRESET]."""
    if hq_def not in HQ_DEFS:
        raise ValueError(f"hq_def must be one of {HQ_DEFS}")
    hr, lr = BUCKET_PRESETS[DEFAULT_PRESET]
    hr, lr = tuple(hq_ratings or hr), tuple(lq_ratings or lr)
    qh, ql = df["quintile"] == HQ_QUINTILE, df["quintile"] == LQ_QUINTILE
    rh, rl = df["rating_bucket"].isin(hr), df["rating_bucket"].isin(lr)
    qh, ql = qh.fillna(False).astype(bool), ql.fillna(False).astype(bool)
    if hq_def == "score":
        return qh, ql
    if hq_def == "rating":
        return rh, rl
    return qh & rh, ql & rl


def _rank(mask: pd.Series, key: pd.Series, ascending: bool) -> pd.Series:
    """1 = best candidate inside `mask`, by `key`. NaN outside."""
    return key.where(mask).rank(method="first", ascending=ascending)


def label(df: pd.DataFrame, is_hq: pd.Series, is_lq: pd.Series) -> pd.DataFrame:
    """Add is_hq, is_lq, the four flags and their ranks (spec Definition 2). Intuition: the up-in-quality trade
    wants the HQ bonds the market prices too wide, and the LQ bonds it prices too tight."""
    e = df["resid"].astype(float)
    out = df.assign(is_hq=is_hq.to_numpy(), is_lq=is_lq.to_numpy())
    out["cheap_hq"] = out["is_hq"] & (e > 0)
    out["rich_hq"] = out["is_hq"] & (e < 0)
    out["cheap_lq"] = out["is_lq"] & (e > 0)
    out["rich_lq"] = out["is_lq"] & (e < 0)
    for c, asc in (("cheap_hq", False), ("rich_lq", True), ("cheap_lq", False), ("rich_hq", True)):
        out[f"{c}_rank"] = _rank(out[c], e, asc)
    return out


def candidates(frame: pd.DataFrame, flag: str, buckets=None, n: int | None = None,
               one_per_issuer: bool = True) -> pd.DataFrame:
    """Single-leg list (spec Expressions c): rows with `flag` (cheap_hq, rich_lq, cheap_lq, rich_hq), cut to rating
    `buckets` when given, best first, at most one bond per issuer (the best residual) unless one_per_issuer=False."""
    r = frame[frame[flag].fillna(False).astype(bool)]
    if buckets is not None:
        r = r[r["rating_bucket"].isin(tuple(buckets))]
    r = r.sort_values(f"{flag}_rank")
    if one_per_issuer:
        r = r.drop_duplicates("gvkey", keep="first")
    return (r.head(n) if n else r).reset_index(drop=True)


def compute(panels: Mapping[str, pd.DataFrame], as_of: pd.Timestamp, kind: str = "blend", within: str = "universe",
            y_kind: str = "log", hq_def: str = "score", hq_ratings=None, lq_ratings=None,
            diagnostics: bool = False, **quality_params) -> pd.DataFrame:
    """Quality-adjusted residual per eligible bond at as_of (spec build steps 6 to 8). One row per cusip.

    score = resid: higher = cheaper for its quality = long. NaN where the bond has no quality score or the fit has
    fewer than MIN_FIT bonds. With `diagnostics`, adds F08 `lever` (event risk) and F16 `var5` (downside risk) by
    cusip, as checks only. Empty frame (columns COLS) when the quality panels are missing."""
    as_of = pd.Timestamp(as_of) + pd.offsets.MonthEnd(0)
    q = qs.compute(panels, as_of, kind, within, **quality_params)
    if q.empty:
        return pd.DataFrame(columns=COLS)
    b = qs.universe(panels, as_of).set_index("cusip")
    for c in ("g_spread", "mod_dur", "years", "price"):
        q[c] = q["cusip"].map(b[c]).astype(float)
    q["dts"] = q["mod_dur"] * q["g_spread"]
    res, info = fit_residuals(q, "quality_rank", y_kind)
    q = pd.concat([q, res], axis=1)
    q["fit_n"] = info["n"]
    q["fit_b_quality"] = float(info["coef"][1]) if info["coef"] is not None else np.nan
    is_hq, is_lq = groups(q, hq_def, hq_ratings, lq_ratings)
    q = label(q, is_hq, is_lq)
    q["score"] = q["resid"]
    q["lever"], q["var5"] = np.nan, np.nan
    if diagnostics:
        lv = f08.compute(panels, as_of)
        if len(lv):
            q["lever"] = q["cusip"].map(lv.set_index("cusip")["lever"]).astype(float)
        dr = f16.compute(panels, as_of)
        if len(dr):
            q["var5"] = q["cusip"].map(dr.set_index("cusip")["var5"]).astype(float)
    q["available_at"] = decision_time(as_of)
    return q[COLS].reset_index(drop=True)
