"""Rate and inflation stress screen on synthetic panels (methodology Section 9.2).

The screen asks which issuers lose the most interest coverage when the Fed hikes and inflation stays sticky.
Four steps:
    1. Shock SOFR and Treasury yields by the scenario.
    2. Run `hy.events.cash_interest_change` per issuer: floating debt reprices now, debt due in two years refinances
       at the new yield plus the issuer's spread.
    3. Cut EBITDA by the cost inflation the issuer cannot pass on (`hy.events.cost_squeeze`).
    4. Rank two ways. `rank` orders by stressed coverage (who breaks first). `rank_exposure` orders by the share of
       coverage the scenario removes (who the scenario hurts most). Flag `double_hit` = maturity wall and sticky prices.

This is a test of the wiring, not of the drivers. The synthetic panels hold no real issuer. The script plants one
double-hit issuer (high floating share, low pass-through, 60% of debt due in two years) and one safe issuer, and
checks that `rank_exposure` puts them first and last. The planted issuer starts with high coverage, so it need not
rank first on the stressed level. `phi_float` and `passthrough` are synthetic: no production panel
holds them yet (docs/factors/PRODUCTION_DATA.md lists the panels).

Run from the repo root: PYTHONPATH=. python3 scripts/rate_inflation_stress.py
"""

from __future__ import annotations

import argparse

import numpy as np
import pandas as pd

from hy import events as ev
from hy.sector.synthetic import make_panels

AS_OF = "2015-06-30"
SCENARIOS = {
    "hike_only": ev.RateInflationScenario(d_sofr=0.02, d_tsy=0.015, cost_inflation=0.0),
    "hike_sticky": ev.RateInflationScenario(d_sofr=0.02, d_tsy=0.015, cost_inflation=0.04),
    "severe": ev.RateInflationScenario(d_sofr=0.03, d_tsy=0.02, cost_inflation=0.06),
}
PLANT_BAD, PLANT_SAFE = "G25_3", "G35_1"


def synthetic_panels(seed: int = 0) -> dict[str, pd.DataFrame]:
    """`make_panels` plus a synthetic `debt_terms` panel and the two planted issuers.

    phi_float ~ U(0, 0.6) and passthrough ~ U(0.2, 1.0) for the rest (Our choice, no source).
    """
    p = make_panels(as_of=AS_OF, sectors={"10": 20, "20": 20, "25": 20, "35": 10, "45": 15}, seed=seed)
    rng = np.random.default_rng(seed + 100)
    ca = p["compustat_annual"].copy()
    for g, (d1, d2) in {PLANT_BAD: (0.3, 0.3), PLANT_SAFE: (0.0, 0.0)}.items():
        i = ca.index[ca["gvkey"] == g]
        debt = float((ca.loc[i, "dlc"] + ca.loc[i, "dltt"]).iloc[0])
        ca.loc[i, "dd1"], ca.loc[i, "dd2"] = d1 * debt, d2 * debt
        if g == PLANT_SAFE:
            ca.loc[i, "xint"] = 0.02 * debt
    p["compustat_annual"] = ca
    gv = sorted(ca["gvkey"].unique())
    phi = rng.uniform(0.0, 0.6, len(gv))
    pt = rng.uniform(0.2, 1.0, len(gv))
    terms = pd.DataFrame({"gvkey": gv, "phi_float": phi, "passthrough": pt, "available_at": pd.Timestamp("2015-01-01")})
    terms.loc[terms["gvkey"] == PLANT_BAD, ["phi_float", "passthrough"]] = [0.9, 0.1]
    terms.loc[terms["gvkey"] == PLANT_SAFE, ["phi_float", "passthrough"]] = [0.0, 1.0]
    p["debt_terms"] = terms
    return p


def sector_summary(out: pd.DataFrame) -> pd.DataFrame:
    """Per GICS sector: issuers, median coverage drop, share below 1.5x stressed coverage, double hits."""
    return out.groupby("gsector").agg(
        issuers=("gvkey", "size"),
        median_cov_drop=("cov_drop", "median"),
        share_below_1_5x=("cov_stress", lambda s: float((s < 1.5).mean())),
        double_hits=("double_hit", "sum"),
    ).sort_values("median_cov_drop", ascending=False)


def main(seed: int = 0, top: int = 8) -> dict[str, pd.DataFrame]:
    panels = synthetic_panels(seed)
    issuers = ev.stress_inputs(panels, AS_OF)
    cols = ["rank", "rank_exposure", "gvkey", "gsector", "cov_base", "cov_stress", "pct_loss", "phi_float",
            "passthrough", "wall_share", "double_hit"]
    results = {}
    pd.set_option("display.width", 160)
    for name, scen in SCENARIOS.items():
        out = ev.rate_inflation_screen(issuers, scen)
        results[name] = out
        print(f"\n=== {name}: dSOFR {scen.d_sofr:+.2%}, dTsy {scen.d_tsy:+.2%}, cost inflation {scen.cost_inflation:.0%}, "
              f"h {scen.h} quarters ===")
        print("Lowest stressed coverage:")
        print(out[cols].head(top).round(3).to_string(index=False))
        print("Largest coverage loss:")
        print(out.sort_values("rank_exposure")[cols].head(top).round(3).to_string(index=False))
        print("\nBy sector:")
        print(sector_summary(out).round(3).to_string())
    sticky = results["hike_sticky"].set_index("gvkey")
    first, last = int(sticky.loc[PLANT_BAD, "rank_exposure"]), int(sticky.loc[PLANT_SAFE, "rank_exposure"])
    n = len(sticky)
    ok = first == 1 and last == n and bool(sticky.loc[PLANT_BAD, "double_hit"])
    print(f"\nCheck (hike_sticky): planted double hit {PLANT_BAD} rank_exposure {first} of {n}, "
          f"planted safe {PLANT_SAFE} rank_exposure {last} of {n}: {'PASS' if ok else 'FAIL'}")
    if not ok:
        raise SystemExit(1)
    return results


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--top", type=int, default=8)
    a = ap.parse_args()
    main(a.seed, a.top)
