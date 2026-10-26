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

REGISTRY: dict[int, str] = {
    1: "hy.factors.f01_ipca",
    2: "hy.factors.f02_spread_to_d2d",
    3: "hy.factors.f03_residual_equity_momentum",
    4: "hy.factors.f04_bond_momentum",
    5: "hy.factors.f05_flow_pressure_reversal",
    6: "hy.factors.f06_issuer_curve_residual",
    7: "hy.factors.f07_merton_ml_forecast",
    8: "hy.factors.f08_lever_event_risk",
    9: "hy.factors.f09_profitability_change",
    10: "hy.factors.f10_market_neutral_carry",
    11: "hy.factors.f11_delta_implied_vol",
    12: "hy.factors.f12_etf_pressure",
    13: "hy.factors.f13_realized_illiquidity",
    14: "hy.factors.f14_abnormal_volume",
    15: "hy.factors.f15_pca_ou_reversal",
    16: "hy.factors.f16_downside_risk",
    17: "hy.factors.f17_return_skewness",
    18: "hy.factors.f18_equity_credit_discordance",
    19: "hy.factors.f19_owner_cash_flow",
    20: "hy.factors.f20_tail_dependence",
    21: "hy.factors.f21_refinancing_headroom",
    22: "hy.factors.f22_curve_shape",
    23: "hy.factors.f23_margin_squeeze",
    24: "hy.factors.f24_cell_percentile",
    25: "hy.factors.f25_credit_bmi",
    26: "hy.factors.f26_index_trend",
    27: "hy.factors.f27_real_yield_regime",
    28: "hy.factors.f28_index_fair_value_gap",
    29: "hy.factors.f29_macro_momentum",
    30: "hy.factors.f30_hy_vix_gap",
}
