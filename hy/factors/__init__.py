"""Candidate factors from the Quant Credit folder review. One module per factor; spec pages in docs/factors/.

Ranked list: research/notes/quant-credit-factor-candidates.md. Each module `hy/factors/fNN_<slug>.py` follows one
contract so the production machine can run and test every factor the same way:

    META = {"rank": NN, "name": str, "level": "bond" | "issuer" | "index", "horizon_months": int,
            "needs": [panel names], "spec": "docs/factors/FNN-<slug>.md", "section": methodology section}

    compute(panels: Mapping[str, pd.DataFrame], as_of: pd.Timestamp, **params) -> pd.DataFrame
        panels  the production panels of docs/production_wiring.md section 5 (bond_panel, leverage, gics, ratings,
                annual_ebitda, equity_monthly), plus any extra panel the module names in META["needs"] and its
                spec page defines (column names and `available_at`).
        as_of   a month end. The module reads only rows with `available_at` <= hy.backtest.decision_time(as_of).
        return  one row per key at `date` = as_of: `date`, the key (`cusip`, `gvkey`, or `index`), `score`,
                `available_at`, then any factor-specific columns. A higher score means a higher expected excess
                return (long). NaN means "no score", never zero.

Evaluation uses hy.signals.rank_ic and hy.signals.passes_cycle_test over hy.backtest.CYCLE_WINDOWS.
`REGISTRY` lists the finished modules by rank.
"""

from __future__ import annotations

REGISTRY: dict[int, str] = {}
