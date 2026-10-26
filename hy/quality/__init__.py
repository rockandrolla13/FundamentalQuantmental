"""Quality rotation for directional HY trades: up in quality when the cycle turns down, down in quality when it
turns up. Spec docs/factors/QUALITY-rotation.md. Methodology Sections 4 (issuer state), 7.4 (spread per unit of
risk), 8 (signals) and 3.6 (`cycle_phase`).

Modules, each with the factor contract of hy.factors (META, compute(panels, as_of), available_at <=
hy.backtest.decision_time(as_of), NaN = no score):

    score      issuer quality: fundamental (spread-free), rating (F04 classes), and their blend; the
               fundamental-against-rating gap (methodology 4.5, signal S6)
    valuation  residual of log spread on quality and log duration each month; cheap HQ, rich LQ, and the mirror
    trades     DTS-matched pairs and single-leg lists, with net carry and jump-to-default asymmetry
    gauge      market quality spread ratio (LQ over HQ) against its own history, plus the F24 BB/BBB and B/BB ratios
    phase      cycle_phase -> active expression (a documented hypothesis the user can override)

The repo holds implementation and unit tests only. Evaluation runs on the production machine.
"""

from __future__ import annotations

MODULES: dict[str, str] = {
    "score": "hy.quality.score",
    "valuation": "hy.quality.valuation",
    "trades": "hy.quality.trades",
    "gauge": "hy.quality.gauge",
    "phase": "hy.quality.phase",
}
