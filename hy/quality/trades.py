"""Up-in-quality and down-in-quality expressions (spec docs/factors/QUALITY-rotation.md, Definition 3). Methodology
Section 8 (composite and sizing) and Section 9.3 (position risk: jump to default).

    DTS_i       = D_i s_i                                    duration times spread (Houweling, van Zundert 2017 p. 47)
    w_i         = (1 / n_L) / DTS_i, scaled so sum_long w_i = 1     equal DTS per long bond, long market value 1
    w_j         = -(1 / n_S) / DTS_j x k, k so that sum_short |w_j| DTS_j = sum_long w_i DTS_i      DTS-matched
    carry       = sum_i w_i s_i                              net spread carry per year per unit long market value
    JTD_i       = |w_i| (1 - R / (P_i / 100))                loss (long) or gain (short) per default, R = recovery
    conv        = sum_i w_i D_i gap_i                         return if every spread gap closes

Intuition: matched DTS removes the first-order beta to a proportional spread move, so the pair earns the quality
residuals and the change in the quality spread, not the market.

Expressions (EXPRESSIONS):
- up_pair: long cheap HQ, short rich LQ. For late cycle and downturn (hy.quality.phase).
- down_pair: long cheap LQ, short rich HQ. The reverse direction with the same value tilt, for repair and recovery.
- long_cheap_hq, short_rich_lq, long_cheap_lq, short_rich_hq: single legs.
Pairs can cross rating buckets: `long_buckets=("BB",)`, `short_buckets=("CCC",)` gives long cheap BB against short
rich CCC, DTS-matched.
"""

from __future__ import annotations

from typing import Mapping

import numpy as np
import pandas as pd

from hy.backtest import decision_time
from hy.factors.f02_spread_to_d2d import CG_RECOVERY
from hy.quality import phase as qp
from hy.quality import valuation as qv

RECOVERY = CG_RECOVERY        # R = 0.3, the bond recovery of F02 (Alber PDF p. 24). Our choice to reuse it
N_PER_LEG = 5                 # bonds per leg, one per issuer (our choice)
EXPRESSIONS: dict[str, tuple[str | None, str | None]] = {   # (long flag, short flag)
    "up_pair": ("cheap_hq", "rich_lq"),
    "down_pair": ("cheap_lq", "rich_hq"),
    "long_cheap_hq": ("cheap_hq", None),
    "short_rich_lq": (None, "rich_lq"),
    "long_cheap_lq": ("cheap_lq", None),
    "short_rich_hq": (None, "rich_hq"),
}

META = {
    "rank": None,
    "name": "Up-in-quality and down-in-quality expressions",
    "level": "bond",
    "horizon_months": 12,
    "needs": qv.META["needs"] + ["cycle_phase"],
    "spec": "docs/factors/QUALITY-rotation.md",
    "section": "8; 9.3",
}

LEG_COLS = ["date", "cusip", "score", "available_at", "gvkey", "expression", "leg", "weight_mv", "dts",
            "dts_contrib", "carry", "jtd", "conv_contrib", "resid", "spread_gap", "quality_rank", "quintile",
            "rating_bucket", "rclass", "fund_rating_gap", "gap_flag", "g_spread", "mod_dur", "price"]
SUMMARY_KEYS = ["expression", "n_long", "n_short", "long_mv", "short_mv", "long_dts", "short_dts", "net_dts",
                "net_carry", "jtd_long_loss", "jtd_short_gain", "jtd_worst_long", "jtd_best_short", "jtd_ratio",
                "conv_return"]


def dts_weights(dts: pd.Series, target_dts: float | None = None) -> pd.Series:
    """Equal DTS per bond. Without `target_dts` the leg market value sums to 1. With it, the leg DTS sums to
    `target_dts`. Positive weights. A bond with DTS <= 0 or NaN gets NaN (spec Definition 3)."""
    d = dts.astype(float).where(dts > 0)
    raw = (1.0 / d.notna().sum()) / d
    if target_dts is None:
        return raw / raw.sum()
    return raw * (target_dts / (raw * d).sum())


def jtd(weight_mv: pd.Series, price: pd.Series, recovery: float = RECOVERY) -> pd.Series:
    """|w| (1 - R / (P / 100)): the market value lost (long) or gained (short) when the issuer defaults and the bond
    falls to recovery R per 100 par. Intuition: a low-priced bond has less left to lose."""
    return weight_mv.abs() * (1.0 - recovery / (price.astype(float) / 100.0))


def build_legs(frame: pd.DataFrame, expression: str, n_per_leg: int = N_PER_LEG, long_buckets=None,
               short_buckets=None, recovery: float = RECOVERY) -> pd.DataFrame:
    """Leg rows of one expression from a valuation frame (hy.quality.valuation.compute). One bond per issuer per
    leg, best residual first. A pair needs both legs, else it is empty. Columns LEG_COLS."""
    if expression not in EXPRESSIONS:
        raise ValueError(f"expression must be one of {tuple(EXPRESSIONS)}")
    lf, sf = EXPRESSIONS[expression]
    longs = qv.candidates(frame, lf, long_buckets, n_per_leg) if lf else frame.iloc[0:0]
    shorts = qv.candidates(frame, sf, short_buckets, n_per_leg) if sf else frame.iloc[0:0]
    shorts = shorts[~shorts["gvkey"].isin(longs["gvkey"])]
    if (lf and longs.empty) or (sf and shorts.empty):
        return pd.DataFrame(columns=LEG_COLS)
    parts = []
    if lf:
        parts.append(longs.assign(leg="long", weight_mv=dts_weights(longs["dts"]).to_numpy()))
    if sf:
        target = float((parts[0]["weight_mv"] * parts[0]["dts"]).sum()) if lf else None
        w = dts_weights(shorts["dts"].reset_index(drop=True), target).to_numpy()
        parts.append(shorts.assign(leg="short", weight_mv=-w))
    legs = pd.concat(parts, ignore_index=True)
    legs["expression"] = expression
    legs["dts_contrib"] = legs["weight_mv"] * legs["dts"]
    legs["carry"] = legs["weight_mv"] * legs["g_spread"]
    legs["jtd"] = jtd(legs["weight_mv"], legs["price"], recovery)
    legs["conv_contrib"] = legs["weight_mv"] * legs["mod_dur"] * legs["spread_gap"]
    legs["score"] = legs["resid"]
    return legs[LEG_COLS].reset_index(drop=True)


def summary(legs: pd.DataFrame) -> dict:
    """Net DTS, net carry, jump-to-default asymmetry and convergence of one expression (spec Definition 3).
    jtd_ratio = short gain / long loss: above 1 means a default on the book pays more than it costs."""
    out = dict.fromkeys(SUMMARY_KEYS, np.nan)
    if legs.empty:
        return out
    lo, sh = legs[legs["leg"] == "long"], legs[legs["leg"] == "short"]
    out.update({"expression": legs["expression"].iloc[0], "n_long": len(lo), "n_short": len(sh),
                "long_mv": float(lo["weight_mv"].sum()), "short_mv": float(sh["weight_mv"].sum()),
                "long_dts": float(lo["dts_contrib"].sum()), "short_dts": float(sh["dts_contrib"].sum()),
                "net_dts": float(legs["dts_contrib"].sum()), "net_carry": float(legs["carry"].sum()),
                "jtd_long_loss": float(lo["jtd"].sum()), "jtd_short_gain": float(sh["jtd"].sum()),
                "jtd_worst_long": float(lo["jtd"].max()) if len(lo) else 0.0,
                "jtd_best_short": float(sh["jtd"].max()) if len(sh) else 0.0,
                "conv_return": float(legs["conv_contrib"].sum())})
    out["jtd_ratio"] = out["jtd_short_gain"] / out["jtd_long_loss"] if out["jtd_long_loss"] > 0 else np.nan
    return out


def compute(panels: Mapping[str, pd.DataFrame], as_of: pd.Timestamp, expression: str | None = None,
            mapping: Mapping[str, str | None] | None = None, legs: str = "pair", n_per_leg: int = N_PER_LEG,
            long_buckets=None, short_buckets=None, recovery: float = RECOVERY, **valuation_params) -> pd.DataFrame:
    """Leg rows of the active expression at as_of (spec build step 9). One row per cusip.

    `expression` None takes it from the phase hook (hy.quality.phase) and the `cycle_phase` panel. score = resid:
    positive on long legs, negative on short legs. Empty frame (columns LEG_COLS) when no expression is active, the
    valuation frame is empty, or a pair lacks a leg."""
    as_of = pd.Timestamp(as_of) + pd.offsets.MonthEnd(0)
    if expression is None:
        expression = qp.phase_expression(qp.phase_at(panels.get("cycle_phase"), as_of), mapping, legs)
    if expression is None:
        return pd.DataFrame(columns=LEG_COLS)
    frame = qv.compute(panels, as_of, **valuation_params)
    if frame.empty:
        return pd.DataFrame(columns=LEG_COLS)
    out = build_legs(frame, expression, n_per_leg, long_buckets, short_buckets, recovery)
    out["date"], out["available_at"] = as_of, decision_time(as_of)
    return out
