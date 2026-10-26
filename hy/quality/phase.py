"""Phase hook: which quality expression is active in each cycle phase (spec docs/factors/QUALITY-rotation.md,
Definition 4). Methodology Section 3.6 (`cycle_phase`: expansion, late cycle, downturn, repair, recovery).

HYPOTHESIS, not a tested rule. DEFAULT_MAP is our choice:
- late cycle, downturn -> up in quality. Greenwood and Hanson (2013, Table 3, p. 47; Table 7, p. 51): low issuer
  quality late in a boom forecasts low HY returns and higher default rates, and the effect is largest for the
  lowest ratings.
- repair, recovery -> down in quality. No source in the repo tests this side. It is the mirror of the first.
- expansion -> no expression. No source gives a direction.

Conflict. Nicol (DB, short dated HY, p. 3, Fig. 4; F27 `compression_state`) finds that B tightens against BB in rate
sell-offs, a down-in-quality move that can happen in any phase. The hook reports F27's state in `rate_selloff` and
applies it only when `selloff_override=True` (default False).
"""

from __future__ import annotations

from typing import Mapping

import numpy as np
import pandas as pd

from hy.backtest import decision_time
from hy.factors import f27_real_yield_regime as f27

PHASES = ("expansion", "late cycle", "downturn", "repair", "recovery")
DEFAULT_MAP: dict[str, str | None] = {"expansion": None, "late cycle": "up", "downturn": "up",
                                      "repair": "down", "recovery": "down"}
HYPOTHESIS = True
LEGS = {"pair": {"up": "up_pair", "down": "down_pair"},
        "long": {"up": "long_cheap_hq", "down": "long_cheap_lq"},
        "short": {"up": "short_rich_lq", "down": "short_rich_hq"}}
DIRECTION_SCORE = {"up": -1.0, "down": 1.0, None: 0.0}   # +1 = add low-quality risk, -1 = remove it
KEY = "US_HY"

META = {
    "rank": None,
    "name": "Quality rotation phase hook",
    "level": "index",
    "horizon_months": 12,
    "needs": ["cycle_phase", "macro_series", "hy_index"],
    "spec": "docs/factors/QUALITY-rotation.md",
    "section": "3.6; 8",
}
COLS = ["date", "index", "score", "available_at", "cycle_phase", "direction", "expression", "hypothesis",
        "rate_selloff", "phase_date"]


def normalise_phase(phase) -> str | None:
    """Lower case, `_` and `-` read as spaces. "late_cycle" -> "late cycle". Unknown or missing gives None."""
    if not isinstance(phase, str):
        return None
    p = " ".join(phase.strip().lower().replace("_", " ").replace("-", " ").split())
    return p if p in PHASES else None


def phase_direction(phase, mapping: Mapping[str, str | None] | None = None) -> str | None:
    """"up", "down" or None for a phase. `mapping` overrides DEFAULT_MAP entries (keys are normalised)."""
    m = dict(DEFAULT_MAP)
    m.update({normalise_phase(k): v for k, v in (mapping or {}).items() if normalise_phase(k)})
    p = normalise_phase(phase)
    d = m.get(p) if p else None
    if d not in (None, "up", "down"):
        raise ValueError("a mapping value must be 'up', 'down' or None")
    return d


def phase_expression(phase, mapping: Mapping[str, str | None] | None = None, legs: str = "pair") -> str | None:
    """Expression name of hy.quality.trades.EXPRESSIONS for a phase, or None. `legs` is pair, long or short."""
    d = phase_direction(phase, mapping)
    return LEGS[legs][d] if d else None


def phase_at(panel: pd.DataFrame | None, as_of: pd.Timestamp) -> str | None:
    """Latest `cycle_phase` with date <= as_of and available_at <= decision_time(as_of). Panel columns date,
    cycle_phase, available_at. None without a row."""
    if panel is None or not len(panel):
        return None
    as_of = pd.Timestamp(as_of)
    p = panel[(panel["available_at"] <= decision_time(as_of)) & (pd.to_datetime(panel["date"]) <= as_of)]
    if p.empty:
        return None
    return p.sort_values(["date", "available_at"]).iloc[-1]["cycle_phase"]


def compute(panels: Mapping[str, pd.DataFrame], as_of: pd.Timestamp,
            mapping: Mapping[str, str | None] | None = None, legs: str = "pair",
            selloff_override: bool = False) -> pd.DataFrame:
    """One row for index US_HY at as_of. score = DIRECTION_SCORE (+1 down in quality, -1 up, 0 none), NaN without
    a known phase. With `selloff_override` and F27 compression_state True, the direction is "down". Empty frame
    (columns COLS) without the `cycle_phase` panel."""
    as_of = pd.Timestamp(as_of) + pd.offsets.MonthEnd(0)
    cp = panels.get("cycle_phase")
    if cp is None or not len(cp):
        return pd.DataFrame(columns=COLS)
    dt = decision_time(as_of)
    known = cp[(cp["available_at"] <= dt) & (pd.to_datetime(cp["date"]) <= as_of)]
    phase = phase_at(cp, as_of)
    selloff = None
    if panels.get("macro_series") is not None and len(panels["macro_series"]):
        r = f27.compute(panels, as_of)
        if len(r) and "compression_state" in r and pd.notna(r["compression_state"].iloc[0]):
            selloff = bool(r["compression_state"].iloc[0])
    d = phase_direction(phase, mapping)
    if selloff_override and selloff:
        d = "down"
    row = {"date": as_of, "index": KEY, "available_at": dt, "cycle_phase": normalise_phase(phase),
           "direction": d, "expression": LEGS[legs][d] if d else None, "hypothesis": HYPOTHESIS,
           "rate_selloff": selloff, "phase_date": pd.to_datetime(known["date"]).max() if len(known) else pd.NaT,
           "score": DIRECTION_SCORE[d] if normalise_phase(phase) or (selloff_override and selloff) else np.nan}
    return pd.DataFrame([row], columns=COLS).astype({"score": float})
