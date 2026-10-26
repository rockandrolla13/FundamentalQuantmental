"""Sector models for concentrated within-sector long-short HY positions. Spec docs/factors/SECTOR-models.md;
methodology Sections 7.2 (fair spread with sector effects), 7.5 (convergence) and 8 (S1, S4, composite).

Three pieces, each with the hy.factors contract: META and compute(panels, as_of, **params) -> one row per key at
`date` = as_of, with `score` (higher = long, NaN = no score) and `available_at` = hy.backtest.decision_time(as_of).
A module reads only rows with `available_at` <= that time.

    hy.sector.fairspread   per-sector fair spread on sector drivers, pooled fallback for thin sectors; z residual
    hy.sector.relative     any REGISTRY factor ranked within GICS sector, and the sector composite
    hy.sector.pairs        cheapest against richest inside a sector, DTS-hedged, with convergence, carry and JTD

Helpers: hy.sector.common (universe, sector groups), hy.sector.drivers (issuer drivers and the sector driver lists),
hy.sector.synthetic (synthetic panels for tests and a smoke run).
"""

from __future__ import annotations

SECTOR_REGISTRY: dict[str, str] = {
    "sector_fs": "hy.sector.fairspread",
    "sector_composite": "hy.sector.relative",
    "sector_pairs": "hy.sector.pairs",
}
