"""End-to-end forecast linkage on a synthetic issuer (methodology Sections 5.4, 7.5, 9.2, 10.4).

Forecast registry -> macro paths (quantile mass x phase prior) -> F6 cases under every path -> case weights ->
forward features per path and weighted -> expected alpha -> event matrix -> revision on a second vintage.
Synthetic issuer and synthetic forecasts only (task rule: no real issuer figures).

Run from the repo root: PYTHONPATH=. python3 scripts/forecast_demo.py
"""

from __future__ import annotations

from datetime import datetime

import numpy as np
import pandas as pd

from hy import alpha, events, forward, macro
from hy.forecasts import ForecastRegistry, ForecastRow

H = 8
DRIVERS = dict(v=0.60, a=0.20, inventory_days=60.0, receivable_days=45.0, payable_days=40.0, capex=8.0)
A4_TEMPLATE = {"annual": (-0.20, -0.10), "recovery_shape": "u", "trough_margin": 0.12}


def synthetic_registry(gdp_median: float, vintage: datetime) -> list[ForecastRow]:
    """Survey-style GDP and CPI quantiles, a policy path, and a forward curve, all released 14 days after vintage."""
    avail = vintage + pd.Timedelta(14, unit="D")
    rows = []
    for h in range(H):
        rows.append(ForecastRow("spf", "gdp_growth", h, vintage, avail, gdp_median, gdp_median - 0.015,
                                gdp_median, gdp_median + 0.015, "survey_bins"))
        rows.append(ForecastRow("spf", "cpi", h, vintage, avail, 0.028, 0.020, 0.028, 0.036, "survey_bins"))
        rows.append(ForecastRow("fomc_sep", "policy_rate", h, vintage, avail, 0.040 - 0.001 * h,
                                0.030, 0.040 - 0.001 * h, 0.045, "dot_range"))
        rows.append(ForecastRow("ust_forward", "y2", h, vintage, avail, 0.041, method="market_implied"))
        rows.append(ForecastRow("ust_forward", "y10", h, vintage, avail, 0.046, method="market_implied"))
    return rows


def synthetic_issuer() -> forward.IssuerStart:
    lines = (forward.DebtLine("term_loan", face=200.0, floating=True, spread=0.035, floor=0.005, amort=0.5),
             forward.DebtLine("notes", face=200.0, coupon=0.07, maturity_q=4))
    return forward.IssuerStart(
        revenue_q0=100.0, ebitda_hist=(20.0,) * 4, interest_hist=(7.0,) * 4, cash0=15.0, debt_lines=lines,
        revolver_commitment=60.0, revolver_spread=0.03, commitment_fee=0.005, inventory_days0=60.0,
        receivable_days0=45.0, payable_days0=40.0, cogs_ratio0=0.60, da_q=5.0, min_cash=5.0)


# The fair spread and access functions stand in for Section 7 and framework F4 until both are calibrated.
def s_fair_path(path, q):
    return float(path.index_spread[min(q, H) - 1]) + 0.01


def p_access(path, q):
    return 0.8 if path.index_spread[min(q, H) - 1] < 0.06 else 0.3


def fwd_treasury(path, q, tenor):
    return float(path.y10[min(q, H) - 1])


def run(registry: ForecastRegistry, t: datetime, phase_ind: dict) -> dict:
    ps = macro.build_paths(registry, t, phase_indicators=phase_ind)
    start = synthetic_issuer()
    base = forward.base_from_consensus(dict(g=0.011, **DRIVERS), gaps={"g": -0.002})
    cases = forward.f6_cases(base, "A4", (), A4_TEMPLATE, consensus=dict(g=0.011, **DRIVERS))
    grid = forward.run_grid(start, cases, ps.paths, betas={"g": 0.4}, trend=0.018, forecast_rows=ps.sources,
                            covenant_max_leverage=6.0, s_fair_fn=s_fair_path, p_refi_access_fn=p_access,
                            forward_treasury_fn=fwd_treasury)
    w = forward.case_weights_by_path(ps.paths, ps.phase, "A4")
    feats = forward.forward_features_by_path(
        grid, ps.paths, w, start,
        pd_fn=lambda f: float(np.clip(0.005 * f["lev_fwd_4"] ** 1.5, 0.001, 0.5)),
        s_fair_fn=lambda f: 0.02 + 0.006 * f["lev_fwd_4"], oas=0.065)
    return {"paths": ps, "grid": grid, "w": w, "features": feats}


def main() -> None:
    t1, t2 = datetime(2026, 6, 30), datetime(2026, 9, 30)
    reg = ForecastRegistry(synthetic_registry(0.018, datetime(2026, 5, 15)))
    reg.add(synthetic_registry(0.006, datetime(2026, 8, 15)))  # second vintage: growth forecast cut
    phase_ind = {"pmi": 49.0, "sloos_tightening": [0.10, 0.15], "default_rate_fcst": 0.045, "default_rate_ttm": 0.035}

    old, new = run(reg, t1, phase_ind), run(reg, t2, phase_ind)
    ps = new["paths"]
    print("Phase:", ps.phase)
    print(pd.DataFrame({"prior": ps.prior, "mass": ps.mass, "posterior": ps.posterior}).round(3).to_string())
    print("\nPath probability change since the earlier vintage:")
    print(macro.path_prob_changes(old["paths"], ps).round(3).to_string(index=False))

    f = new["features"]
    cols = ["macro_path", "p_path", "lev_fwd_4", "lev_fwd_sd", "p_breach_4", "p_refi_4", "refi_fail_share",
            "pd_12m", "s_fair", "resid_bp"]
    print("\nForward features by path:")
    print(f[[c for c in cols if c in f]].round(3).to_string(index=False))

    rev = forward.forward_revisions(f, old["features"], consensus_lev_4=4.6)
    print("\nRevisions:", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in rev.items()})

    bond = alpha.BondInputs("SYNTH 7% NOTES", oas=0.065, spread_duration=3.6, rho_q=0.8, beta_mkt=0.9,
                            index_spread=0.045, lgd=0.6, bid_ask_bp=40)
    a = alpha.expected_alpha(bond, f[["macro_path", "p_path", "s_fair", "pd_12m"]], h_years=0.5)
    print("\nExpected alpha, 6 months:")
    print(a["by_path"].round(4).to_string(index=False))
    print({k: round(a[k], 4) if isinstance(a[k], float) else a[k]
           for k in ("carry_w", "converge_w", "loss_w", "cost", "alpha_net", "alpha_net_bp_ann", "alpha_sd",
                     "info_ratio", "passes_g3")})

    probs = events.outcome_probs_from_cases("earnings", new["w"], f)
    print("\nEarnings outcome probabilities by path:")
    print(probs.round(3).to_string())


if __name__ == "__main__":
    main()
