"""End-to-end run of the HY Analyst on a synthetic universe (methodology Sections 5 to 8).

The script plants a known mispricing in some bonds and checks that the
pipeline finds them. It is a test of the wiring, not of alpha: the data
come from the same structure the models assume.

Run from the repo root: PYTHONPATH=. python3 scripts/demo_pipeline.py
"""

from __future__ import annotations

from datetime import datetime

import numpy as np
import pandas as pd

import hy.forward as fw
import hy.recovery as rc
from hy.fairspread import (
    FairSpreadModel,
    MondrianConformal,
    NoiseScaleModel,
    PDModel,
    anchor_spread_bp,
    expected_loss_spread_bp,
    kappa_by_bucket,
    residuals,
    z_score,
)
from hy.inputs import Tranche
from hy.signals import force_rank, s1_residual

SEED = 7
N_ISSUERS = 300
N_DATES = 12
N_PLANTED = 15
PLANT_LOG = 0.45  # planted cheapness, about 57% wider than fair
SECTORS = ("industrials", "consumer", "energy", "healthcare", "tech")
DECISION = datetime(2026, 9, 30)


def build_issuer(i: int, rng: np.random.Generator) -> dict:
    """Run one issuer through the forward (Section 5) and recovery (Section 6) layers."""
    ebitda_q = rng.uniform(30, 120)
    lev0 = rng.uniform(3.0, 7.5)
    debt = lev0 * 4 * ebitda_q
    senior_share = rng.uniform(0.3, 0.6)
    margin = rng.uniform(0.15, 0.30)
    revenue_q = ebitda_q / margin
    start = fw.IssuerStart(
        revenue_q0=revenue_q,
        ebitda_hist=(ebitda_q,) * 4,
        interest_hist=(0.07 * debt / 4,) * 4,
        cash0=rng.uniform(0.02, 0.10) * debt,
        debt_lines=(
            fw.DebtLine("tlb", senior_share * debt, floating=True, spread=0.035, floor=0.005),
            fw.DebtLine("notes", (1 - senior_share) * debt, coupon=0.075, maturity_q=24),
        ),
        revolver_commitment=0.15 * debt,
        inventory_days0=40, receivable_days0=45, payable_days0=35, cogs_ratio0=0.6, da_q=0.2 * ebitda_q,
    )
    v = 1 - margin - 0.12
    drivers = {"v": v, "a": 0.12, "inventory_days": 40, "receivable_days": 45, "payable_days": 35,
               "capex": 0.25 * ebitda_q}
    cyclical = rng.random() < 0.4
    scen = fw.build_scenario_set(drivers, analyst_g=rng.normal(0.008, 0.01),
                                 recession_annual=(-0.25, -0.12) if cyclical else (-0.12, -0.05))
    paths = fw.run_scenarios(start, list(scen.values()), np.full(8, 0.04), covenant_max_leverage=lev0 + 1.5)
    p_down = 0.15 + (0.15 if cyclical else 0.0)  # Section 5.2 weight; a fitted logit in production
    weights = fw.scenario_weights(p_down, 0.10)
    ff = fw.forward_features(paths, weights, lev_t=lev0, debt_t=debt)

    ebitda_ltm = 4 * ebitda_q
    multiple = rng.uniform(6.0, 9.0)
    v_mid = multiple * ebitda_ltm
    severe_ebitda = 4 * float(np.min(paths["down_severe"].ebitda))
    v_def = rc.default_value(0.8 * multiple, max(severe_ebitda, 0.3 * ebitda_ltm), costs=0.05 * v_mid)
    notes_price = 95.0
    tranches = [
        Tranche(key=f"I{i}-tlb", as_of=DECISION, available_at=DECISION, issuer_id=f"I{i}", rank=1,
                face=senior_share * debt, price=99.0),
        Tranche(key=f"I{i}-notes", as_of=DECISION, available_at=DECISION, issuer_id=f"I{i}", rank=2,
                face=(1 - senior_share) * debt, price=notes_price, coupon=0.075),
    ]
    rec = rc.tranche_outputs(tranches, f"I{i}-notes", ebitda_adj=ebitda_ltm, v_low=0.75 * v_mid, v_mid=v_mid,
                             v_high=1.25 * v_mid, v_default=v_def, p_liq_8=ff["p_liq_short_8"])
    return {
        "issuer_id": f"I{i}", "sector": SECTORS[i % len(SECTORS)],
        "lev_adj_k": lev0, "ltv_k_mid": rec["ltv_k_mid"], "coverage": ff["cov_fwd_4"],
        "recovery_k_adj": rec["recovery_k_adj"], "p_breach_4": ff["p_breach_4"], "lev_fwd_sd_4": ff["lev_fwd_sd_4"],
        "lev_fwd_4": ff["lev_fwd_4"], "p_breach_8": ff["p_breach_8"], "lgd_k_adj": rec["lgd_k_adj"],
        "log_amount_outstanding": np.log((1 - senior_share) * debt),
        "rating": "BB" if lev0 < 4.5 else ("B" if lev0 < 6.5 else "CCC"),
    }


def main() -> None:
    rng = np.random.default_rng(SEED)
    issuers = pd.DataFrame([build_issuer(i, rng) for i in range(N_ISSUERS)])

    # Section 7.1: PD model. True default law is known here, so calibration can be checked.
    pd_cols = ["lev_fwd_4", "coverage", "p_breach_8"]
    true_logit = -7.0 + 0.7 * issuers.lev_fwd_4 - 0.2 * issuers.coverage + 3.0 * issuers.p_breach_8
    panel = pd.concat([issuers] * 6, ignore_index=True)
    defaulted = rng.random(len(panel)) < 1 / (1 + np.exp(-np.tile(true_logit, 6)))
    pdm = PDModel().fit(panel[pd_cols], defaulted.astype(int), panel.rating)
    pd12 = pdm.predict_pd12(issuers[pd_cols], issuers.rating)
    s_el = expected_loss_spread_bp(pd12, issuers.lgd_k_adj.to_numpy())

    # Daily market spreads: true fair spread, sector-by-date shock, liquidity noise, planted cheapness.
    liquidity = rng.choice(["liquid", "illiquid"], N_ISSUERS, p=[0.6, 0.4])
    bid_ask = np.where(liquidity == "liquid", rng.uniform(25, 60, N_ISSUERS), rng.uniform(60, 150, N_ISSUERS))
    issuers["bid_ask_bp"] = bid_ask
    true_kappa = {"BB": 2.2, "B": 1.8, "CCC": 1.4}
    base_log = np.log(np.maximum(s_el, 1.0) * issuers.rating.map(true_kappa)) + 0.002 * bid_ask
    noise_sd = np.where(liquidity == "liquid", 0.08, 0.18)
    planted = rng.choice(N_ISSUERS, N_PLANTED, replace=False)
    rows = []
    for t in range(N_DATES):
        eta = {s: rng.normal(0, 0.05) for s in SECTORS}
        log_s = base_log + issuers.sector.map(eta) + rng.normal(0, noise_sd)
        if t == N_DATES - 1:
            log_s = log_s.copy()
            log_s.iloc[planted] += PLANT_LOG
        rows.append(issuers.assign(date=t, log_s=log_s, liquidity=liquidity))
    data = pd.concat(rows, ignore_index=True)

    # Section 7.1 kappa from the index: mean spread over mean expected loss per rating bucket.
    train = data[data.date < N_DATES - 3]
    s_el_rows = np.tile(s_el, N_DATES)
    data["s_el"] = s_el_rows
    kappa = kappa_by_bucket(train.groupby("rating").log_s.apply(lambda x: np.exp(x).mean()),
                            data[data.date < N_DATES - 3].groupby("rating").s_el.mean())
    data["log_s_anchor"] = np.log(anchor_spread_bp(np.maximum(data.s_el, 1.0), data.rating.map(kappa).to_numpy()))

    # Section 7.2: fit on early dates; 7.3: calibrate the band on two later dates; score the last date.
    feats = ["lev_adj_k", "ltv_k_mid", "coverage", "recovery_k_adj", "p_breach_4", "lev_fwd_sd_4",
             "bid_ask_bp", "log_amount_outstanding"]
    fit_mask = data.date < N_DATES - 3
    cal_mask = data.date.between(N_DATES - 3, N_DATES - 2)
    test_mask = data.date == N_DATES - 1
    model = FairSpreadModel().fit(data.loc[fit_mask, feats], data.loc[fit_mask, "log_s"].to_numpy(),
                                  data.loc[fit_mask, "log_s_anchor"].to_numpy(), data.loc[fit_mask, "sector"],
                                  data.loc[fit_mask, "date"])

    def predict(mask: pd.Series) -> np.ndarray:
        # The sector-by-date effect of an unseen date is estimated from that date's cross-section (Section 7.2).
        d = data[mask]
        no_eta = model.predict_log_spread(d[feats], d.sector, np.full(len(d), -1), d.log_s_anchor.to_numpy())
        gap = pd.Series(d.log_s.to_numpy() - no_eta, index=d.index)
        eta_hat = gap.groupby([d.date, d.sector]).transform("median")
        return no_eta + eta_hat.to_numpy()

    noise = NoiseScaleModel().fit(data.loc[fit_mask, ["bid_ask_bp"]],
                                  residuals(data.loc[fit_mask, "log_s"].to_numpy(), predict(fit_mask)).resid_log)
    z_all = {}
    for name, mask in (("cal", cal_mask), ("test", test_mask)):
        eps = residuals(data.loc[mask, "log_s"].to_numpy(), predict(mask)).resid_log
        z_all[name] = z_score(eps, noise.predict(data.loc[mask, ["bid_ask_bp"]]))
    conf = MondrianConformal(alpha=0.05).fit(z_all["cal"], data.loc[cal_mask, "rating"], data.loc[cal_mask, "liquidity"])
    test = data[test_mask].reset_index(drop=True)
    q = conf.threshold(test.rating, test.liquidity)
    cheap, _ = conf.flags(z_all["test"], test.rating, test.liquidity)

    # Section 8: S1 and the force rank.
    s1 = s1_residual(z_all["test"], q, np.zeros(len(test), dtype=bool))
    ranked = force_rank(test.issuer_id, s1)
    planted_ids = set(issuers.issuer_id.iloc[planted])
    top = ranked.head(N_PLANTED)
    hits = len(planted_ids & set(top.id))
    false_flags = int(cheap.sum()) - len(planted_ids & set(test.issuer_id[cheap]))

    print("HY Analyst demo: synthetic universe")
    print(f"  issuers {N_ISSUERS}, dates {N_DATES}, planted cheap bonds {N_PLANTED} at +{PLANT_LOG:.2f} log spread")
    print(f"  PD by rating (model mean): " + ", ".join(
        f"{r} {pd12[issuers.rating == r].mean():.2%}" for r in ("BB", "B", "CCC")))
    print(f"  kappa by rating: " + ", ".join(f"{k} {v:.2f}" for k, v in kappa.items()))
    print(f"  conformal threshold |z| range: {q.min():.2f} to {q.max():.2f}")
    print(f"  planted bonds found in top {N_PLANTED} of the force rank: {hits} of {N_PLANTED}")
    print(f"  cheap flags: {int(cheap.sum())}, of which false: {false_flags} "
          f"(expected about {0.025 * (N_ISSUERS - N_PLANTED):.0f} at alpha 0.05, one side)")
    print(ranked.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
