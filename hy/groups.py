"""One analyst, four method groups, one combined estimate of expected alpha (methodology 8; framework F10, F12.1).

G1 core process (Gatto's seven steps, methodology, framework F1 to F13, the RV PDF additions), G2 built methods
(clocks, fair line, pair, stories and cases, alpha, gate, F8 panel), G3 skills (hy-model-standards and the
private-credit skills adapted to public bonds), G4 books (Kricheff; Ganguin and Bilardello).

The estimate set E0 to E13, their groups, types and v0 weights follow research/combined_framework_spec.md (S14).
Every estimate is in bp a year of expected alpha before cost. Types: "alpha" estimates are already in bp a year;
"score" estimates are standardised across the run and scaled by sd(E1); "one_way" estimates are scaled scores
capped at zero (a penalty can only lower the number). The combined alpha is the weighted mean over the estimates
present inside each bucket; across buckets it is sum_b W_b alpha_b with W_b the user-set share (BUCKETS).
Decision page: docs/decisions/2026-10-22-four-group-combination.md.
"""

from __future__ import annotations

from typing import Any, Mapping

import numpy as np

# research/combined_framework_spec.md, S14 `estimates`: id -> (group, name, type, v0 weight).
ESTIMATES = {
    "E0": ("G2", "Spread level (carry)", "alpha", 0.25),
    "E1": ("G2", "Weighted cases and stories", "alpha", 0.15),
    "E2": ("G2", "Fair-line convergence", "alpha", 0.10),
    "E3": ("G2", "Pair convergence", "alpha", 0.05),
    "E4": ("G1", "Default the price assumes", "alpha", 0.00),  # suspended until kappa_t is fitted (mapping C2)
    "E5": ("G2", "Two clocks", "score", 0.05),
    "E6": ("G2", "Health panel", "score", 0.05),
    "E7": ("G1", "Earnings quality", "one_way", 0.05),  # spec: G1 and G3; counted in G1's share
    "E8": ("G1", "Liquidity and refinancing", "score", 0.05),
    "E9": ("G1", "Market value check", "score", 0.05),
    "E10": ("G1", "Excess over cash", "alpha", 0.05),
    "E11": ("G3", "Watchlist and covenant path", "one_way", 0.05),
    "E12": ("G4", "Ratio-implied rating gap", "score", 0.05),
    "E13": ("G4", "Spread per turn", "score", 0.05),
    # Added 2026-10-22 (decision page 2026-10-22-weights-esp-spider): the peer signals of Dynkin et al. 2021.
    "E14": ("G4", "Excess spread to peers (ESP)", "score", 0.18),
    "E15": ("G4", "SPiDER", "score", 0.06),
}
# User decision 2026-10-22 (decision page 2026-10-22-weights-esp-spider): G1 40%, two clocks 20%, books 17%; the
# rest split on the backtest: G2 18% (holds spread level, the strongest tested signal), G3 5% (one-way only).
# Within a bucket the estimates keep their v0 weights relative to each other: in G4, ESP 9%, SPiDER 3%, E12 and
# E13 2.5% each. The first five-bucket shares were G1 0.45, G2C 0.20, and 0.35 / 3 each for G2, G3 and G4.
BUCKETS = {
    "G1": ("Core process", 0.40, ("E4", "E7", "E8", "E9", "E10")),
    "G2C": ("Two clocks", 0.20, ("E5",)),
    "G2": ("Built methods (rest)", 0.18, ("E0", "E1", "E2", "E3", "E6")),
    "G3": ("Credit skills", 0.05, ("E11",)),
    "G4": ("Books and peers", 0.17, ("E12", "E13", "E14", "E15")),
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


def combine(estimates: Mapping[str, float], cost_bp_yr: float, anchor_bp_yr: float) -> dict[str, Any]:
    """Combined alpha across the five buckets, set against the scenario-weighted alpha (methodology 7.5, 8; spec S14).

    alpha_b = the bucket's weighted mean over its estimates present (v0 weights, renormalised inside the bucket);
    alpha_comb = sum_b W_b alpha_b / sum_b W_b over the buckets with an estimate, W_b the bucket share (BUCKETS).
    After cost subtracts the anchor's round-trip cost once. Returns per-bucket results and the totals.
    Intuition: five analysts each give a number; the desk weighs them as the user set and pays the cost once.
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
    a, b = SIZED_V0
    agree = sum(1 for v in groups.values() if v["present"] and np.sign(v["alpha_bp_yr"]) == np.sign(comb))
    return {"groups": groups, "combined_before_cost": comb, "combined_after_cost": net, "cost": cost_bp_yr,
            "alpha_sized": a + b * net, "anchor_before_cost": anchor_bp_yr, "anchor_after_cost": anchor_bp_yr - cost_bp_yr,
            "groups_agree": agree, "groups_n": sum(1 for v in groups.values() if v["present"])}


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
