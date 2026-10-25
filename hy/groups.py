"""One analyst, five method groups (six weight buckets), one combined estimate of expected alpha (methodology 8; framework F10, F12.1).

G1 core process (Gatto's seven steps, methodology, framework F1 to F13, the RV PDF additions), G2 built methods
(clocks, fair line, pair, stories and cases, alpha, gate, F8 panel), G3 skills (hy-model-standards and the
private-credit skills adapted to public bonds), G4 books (Kricheff; Ganguin and Bilardello), G5 macro link (the
issuer-macro downside model of methodology 5.2.1, estimate E17).

The estimate set E0 to E13, their groups, types and v0 weights follow research/combined_framework_spec.md (S14).
Every estimate is in bp a year of expected alpha before cost. Types: "alpha" estimates are already in bp a year;
"score" estimates are standardised across the run and scaled by sd(E1); "one_way" estimates are scaled scores
capped at zero (a penalty can only lower the number). The combined alpha is the weighted mean over the estimates
present inside each bucket; across buckets it is sum_b W_b alpha_b with W_b the user-set share (BUCKETS).
Decision page: docs/decisions/2026-10-22-four-group-combination.md.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd

from hy import calibration

# research/combined_framework_spec.md, S14 `estimates`: id -> (group, name, type, v0 weight).
ESTIMATES = {
    "E0": ("G2", "Spread level (carry)", "alpha", 0.25),
    "E1": ("G2", "Weighted cases and stories", "alpha", 0.15),
    # User decision 2026-10-22 (decision page 2026-10-22-e2-lowest-weight): the lowest active weight, 0.10 -> 0.02.
    "E2": ("G2", "Fair-line convergence", "alpha", 0.02),
    "E3": ("G2", "Pair convergence", "alpha", 0.05),
    "E4": ("G1", "Default the price assumes", "alpha", 0.00),  # suspended until kappa_t is fitted (mapping C2)
    "E5": ("G2", "Two clocks", "score", 0.05),
    "E6": ("G2", "Health panel", "score", 0.05),
    "E7": ("G1", "Earnings quality", "one_way", 0.05),  # spec: G1 and G3; counted in G1's share
    "E8": ("G1", "Liquidity and refinancing", "score", 0.05),
    "E9": ("G1", "Market value check", "score", 0.05),
    # User decision 2026-10-25 (decision page 2026-10-25-risk-premium-alpha): E10 is the risk premium test of
    # methodology 7.7, one weighted input of the alpha. It replaces the excess over cash (same step 15 cash flows).
    "E10": ("G1", "Risk premium alpha", "alpha", 0.05),
    "E11": ("G3", "Watchlist and covenant path", "one_way", 0.05),
    "E12": ("G4", "Ratio-implied rating gap", "score", 0.05),
    "E13": ("G4", "Spread per turn", "score", 0.05),
    # Added 2026-10-22 (decision page 2026-10-22-weights-esp-spider): the peer signals of Dynkin et al. 2021.
    "E14": ("G4", "Excess spread to peers (ESP)", "score", 0.09),
    "E15": ("G4", "SPiDER", "score", 0.06),
    # User decision 2026-10-22 (decision page 2026-10-22-onescore): E14's share split with OneScore. A private issuer
    # has no OneScore, so scripts/process.py sets its E16 to its E14: ESP then carries the whole 9%.
    "E16": ("G4", "OneScore (ESP and equity momentum)", "score", 0.09),
    # User decision 2026-10-24 (decision page 2026-10-24-macro-link-method): the issuer-macro downside model of
    # methodology 5.2.1 is its own method, not an input of E1. NaN until the model is fitted and passes T1 to T7.
    "E17": ("G5", "Spread against the issuer-macro downside risk", "score", 1.00),
}
# User decision 2026-10-22 (decision page 2026-10-22-weights-esp-spider): G1 40%, two clocks 20%, books 17%; the
# rest split on the backtest: G2 18% (holds spread level, the strongest tested signal), G3 5% (one-way only).
# Within a bucket the estimates keep their v0 weights relative to each other: in G4, ESP 9%, SPiDER 3%, E12 and
# E13 2.5% each; ESP's 9% is split 4.5% ESP and 4.5% OneScore (E16). The first five-bucket shares were G1 0.45, G2C 0.20, and 0.35 / 3 each for G2, G3 and G4.
BUCKETS = {
    "G1": ("Core process", 0.40, ("E4", "E7", "E8", "E9", "E10")),
    "G2C": ("Two clocks", 0.20, ("E5",)),
    "G2": ("Built methods (rest)", 0.18, ("E0", "E1", "E2", "E3", "E6")),
    "G3": ("Credit skills", 0.05, ("E11",)),
    "G4": ("Books and peers", 0.17, ("E12", "E13", "E14", "E15", "E16")),
    # Share 0 until tests T1 to T7 of methodology 5.2.1 pass; the user sets the live share then. A zero share shows
    # the method in the memo and leaves the combined number unchanged.
    "G5": ("Macro link", 0.00, ("E17",)),
}
GROUP_NAMES = {k: v[0] for k, v in BUCKETS.items()}
GROUP_WEIGHTS = {k: v[1] for k, v in BUCKETS.items()}
# The spec's backtest-led shares (E0 to E13 v0 weights by group), kept for the record.
SPEC_GROUP_WEIGHTS = {"G1": 0.20, "G2": 0.65, "G3": 0.05, "G4": 0.10}


def effective_weights() -> dict[str, float]:
    """Weight of each estimate in the combination: bucket share x its v0 weight / the bucket's v0 total.
    Intuition: the user sets how much each bucket counts; the spec sets the mix inside the bucket."""
    out = {}
    for _, share, ids in BUCKETS.values():
        tot = sum(ESTIMATES[k][3] for k in ids)
        out.update({k: share * ESTIMATES[k][3] / tot if tot else 0.0 for k in ids})
    return out


SIZED_V0 = (0.0, 0.08)  # spec S14b: alpha_sized = a + b alpha_net, pooled Mincer-Zarnowitz; v0 a = 0, b = 0.08
# The fitted map the memo reads (decision page 2026-10-23-size-calibration): the carry-kept peer forecast, whose hedge
# (beta = 1, carry kept) matches E0 and the combined alpha, at the process horizon h = 6 months (scenarios V0 0.5 y).
SIZE_PREDICTOR = "peer_carry_net"
SIZE_HORIZON = 6


def size_map(decision_time: pd.Timestamp | None, path: Path | None = None,
             predictor: str = SIZE_PREDICTOR, horizon_months: int = SIZE_HORIZON) -> dict[str, Any]:
    """The S14b size map in force at `decision_time` (methodology 7.5 size calibration; hy.calibration).

    Reads the calibration file (`hy.calibration.default_path()`, written by scripts/calibrate_sizes.py) and takes the
    latest record of the chosen method with available_at <= decision_time. Falls back to `SIZED_V0` (a = 0, b = 0.08)
    when the decision time is None, the file does not exist, or no record is available yet at that time.
    Intuition: size with the map the desk had on the day, else with the v0 slope.
    """
    rec = None
    if decision_time is not None:
        rec = calibration.latest_before(calibration.load(path or calibration.default_path()), decision_time,
                                        predictor, horizon_months)
    if rec is None:
        a, b = SIZED_V0
        return {"record": None, "a": a, "b": b, "use": "rank only, minimum size",
                "source": "spec S14b v0 (a = 0, b = 0.08); no calibration available at the decision time"}
    return {"record": rec, "a": rec.a * 1e4 * 12.0 / rec.horizon_months, "b": rec.b, "use": rec.use,
            "source": f"{rec.method} size map fitted {rec.fit_date} on {rec.n_months} months, {rec.predictor}, "
                      f"h = {rec.horizon_months} months (decision page 2026-10-23-size-calibration)"}


def sized_alpha(alpha_net_bp_yr: float, smap: Mapping[str, Any]) -> float:
    """Spec S14b: alpha_sized = m(alpha_net), m the size map (`size_map`); with no record, a + b alpha_net (v0).
    Intuition: the raw number ranks; this number is the part of it that past outcomes support."""
    rec = smap.get("record")
    if rec is None:
        return smap["a"] + smap["b"] * alpha_net_bp_yr
    return calibration.size_bp_yr(rec, alpha_net_bp_yr)


def convergence_alpha_bp(gap: float, spread_duration: float, rho_q: float, h_years: float) -> float:
    """Spread gap to bp a year of alpha through convergence (methodology 7.5): D (1 - rho^(4h)) gap / h x 1e4.

    `gap` = spread - fair spread, decimal; positive means the bond pays more than fair (cheap).
    Intuition: the part of the gap that closes by the horizon, times the price move per unit of spread.
    """
    if gap != gap:
        return float("nan")
    return spread_duration * (1.0 - rho_q ** (4 * h_years)) * gap / h_years * 1e4


def scale_scores(scores: Mapping[str, float], scale: float) -> dict[str, float]:
    """Standardise one score across issuers and scale it to alpha units: (x - mean) / sd x scale (spec S14 score_to_bp).

    NaN stays NaN; with fewer than three values or zero spread the estimate is NaN (no cross-section to compare).
    Intuition: a score says better or worse than the others; the scale says by how much in bp.
    """
    v = np.array([x for x in scores.values() if x == x], dtype=float)
    if v.size < 3 or np.std(v, ddof=1) == 0:
        return {k: float("nan") for k in scores}
    mu, sd = v.mean(), v.std(ddof=1)
    return {k: (x - mu) / sd * scale if x == x else float("nan") for k, x in scores.items()}


def one_way(x: float) -> float:
    """Spec S14 one_way rule: alpha_j = min(0, alpha_j). Intuition: a clean checklist earns no credit; a failed one costs."""
    return min(0.0, x) if x == x else float("nan")


def weighted(estimates: Mapping[str, float], weights: Mapping[str, float]) -> dict[str, Any]:
    """Weighted mean over the estimates present (NaN drops out; weights renormalise; zero weights are shown, not counted).

    Returns rows (estimate, value, weight, contribution), the total, and the agreement count (estimates with the same
    sign as the total). Intuition: each estimate is one witness; missing witnesses do not count as zero.
    """
    ok = {k: v for k, v in estimates.items() if k in weights and v is not None and v == v}
    w = sum(weights[k] for k in ok)
    if w <= 0:
        return {"rows": [{"estimate": k, "alpha_bp_yr": ok[k], "weight": 0.0, "contribution": 0.0} for k in weights if k in ok],
                "alpha_bp_yr": float("nan"), "agree": 0, "n": 0, "weight_present": 0.0}
    rows = [{"estimate": k, "alpha_bp_yr": ok[k], "weight": weights[k] / w, "contribution": ok[k] * weights[k] / w}
            for k in weights if k in ok]
    tot = sum(r["contribution"] for r in rows)
    counted = [r for r in rows if r["weight"] > 0]
    agree = sum(1 for r in counted if np.sign(r["alpha_bp_yr"]) == np.sign(tot))
    return {"rows": rows, "alpha_bp_yr": tot, "agree": agree, "n": len(counted), "weight_present": w}


def combine(estimates: Mapping[str, float], cost_bp_yr: float, anchor_bp_yr: float,
            decision_time: pd.Timestamp | None = None, calibration_path: Path | None = None) -> dict[str, Any]:
    """Combined alpha across the weight buckets (BUCKETS), set against the scenario-weighted alpha (methodology 7.5, 8; spec S14).

    alpha_b = the bucket's weighted mean over its estimates present (v0 weights, renormalised inside the bucket);
    alpha_comb = sum_b W_b alpha_b / sum_b W_b over the buckets with an estimate, W_b the bucket share (BUCKETS).
    After cost subtracts the anchor's round-trip cost once. Returns per-bucket results and the totals.
    alpha_sized (spec S14b) uses the latest calibration available before `decision_time` when the calibration file
    exists (`size_map`), else `SIZED_V0`; `size_use` says "size" or "rank only, minimum size".
    Intuition: each bucket is one analyst who gives a number; the desk weighs them as the user set and pays the cost once.
    """
    groups = {}
    for g, (name, share, ids) in BUCKETS.items():
        wts = {k: ESTIMATES[k][3] for k in ids}
        r = weighted({k: estimates.get(k, float("nan")) for k in ids}, wts)
        present = r["weight_present"] > 0
        groups[g] = {"name": name, "alpha_bp_yr": r["alpha_bp_yr"], "rows": r["rows"], "agree": r["agree"], "n": r["n"],
                     "share_set": share, "present": present,
                     "one_way_only": all(ESTIMATES[k][2] == "one_way" for k in ids if ESTIMATES[k][3] > 0)}
    wp = sum(v["share_set"] for v in groups.values() if v["present"])
    comb = sum(v["share_set"] * v["alpha_bp_yr"] for v in groups.values() if v["present"]) / wp if wp else float("nan")
    for v in groups.values():
        v["group_share"] = v["share_set"] / wp if wp and v["present"] else 0.0
        v["contribution"] = v["group_share"] * v["alpha_bp_yr"] if v["present"] else 0.0
    net = comb - cost_bp_yr
    smap = size_map(decision_time, calibration_path)
    sized = sized_alpha(net, smap)
    # A fitted map that says "rank only" gives every bond about the same number (its intercept): the sample's average
    # excess return, not a view on this bond. Show no size then, and name that level on its own.
    rank_only = smap["record"] is not None and smap["use"] != "size"
    voting = [v for v in groups.values() if v["present"] and v["share_set"] > 0]  # a zero-share bucket is shown, not counted
    agree = sum(1 for v in voting if np.sign(v["alpha_bp_yr"]) == np.sign(comb))
    return {"groups": groups, "combined_before_cost": comb, "combined_after_cost": net, "cost": cost_bp_yr,
            "alpha_sized": float("nan") if rank_only else sized, "size_level_bp_yr": sized if rank_only else None,
            "size_use": smap["use"], "size_source": smap["source"],
            "anchor_before_cost": anchor_bp_yr, "anchor_after_cost": anchor_bp_yr - cost_bp_yr,
            "groups_agree": agree, "groups_n": len(voting)}


def verdict(alpha_bp_yr: float, cost_bp_yr: float, one_way_only: bool = False) -> str:
    """Group call from its alpha: "supports owning" above the trading cost; "leans to owning" between zero and cost;
    "against owning" below zero; "no objection" for a one-way group at zero; "no view" when it has no estimate.
    Intuition: a group only supports a trade if its edge pays for getting in and out.
    """
    if alpha_bp_yr != alpha_bp_yr:
        return "no view"
    if one_way_only and alpha_bp_yr >= 0:
        return "no objection"
    if alpha_bp_yr > cost_bp_yr:
        return "supports owning"
    return "leans to owning" if alpha_bp_yr > 0 else "against owning"


def rank(values: Mapping[str, float], reverse: bool = True) -> dict[str, int]:
    """Rank issuers by a value, 1 = best (highest when `reverse`); ties share a rank (1 + the number strictly better).
    NaN ranks last. Intuition: five issuers with a clean checklist are equal, not first to fifth."""
    ok = {k: v for k, v in values.items() if v == v}
    out = {k: 1 + sum(1 for w in ok.values() if (w > v if reverse else w < v)) for k, v in ok.items()}
    out.update({k: len(ok) + 1 for k in values if k not in ok})
    return out


def zscore(values: Mapping[str, float]) -> dict[str, float]:
    """Cross-sectional z-score; NaN stays NaN; fewer than three values gives NaN. Intuition: place in the run."""
    return scale_scores(values, 1.0)
