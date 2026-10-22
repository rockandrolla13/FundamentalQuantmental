# Combined framework spec (machine-readable)

Status: FINAL v2, 2026-10-22 (user bucket weights; code state after agent one's run). Agent two wrote this file from `docs/writeup/combined_framework.tex` (46 pages).
Agent one aligns `scripts/process.py` and `scripts/memo.py` with it. When this file and the .tex disagree, the .tex wins.

Groups: G1 core process (Gatto, methodology.md, framework.md, RV PDF); G2 built methods (clocks, fair line, pair, stories, cases, alpha, gate, panel, combined view, backtest); G3 skills (hy-model-standards plus six private-credit skills, adapted to public HY); G4 books (Kricheff; Ganguin and Bilardello, S&P).

Conventions: spreads and rates in decimals unless the id ends in `_bp`; money in USD m unless `_bn`. `E` = LTM EBITDA; `I_c` = LTM cash interest; `D` = financial debt at face; `R` = annual lease cost; `K` = capex; `K_m` = maintenance capex. Bands are `[green, amber, red]` thresholds and are v0 (framework R9). Status codes: `built`, `partial`, `not_built` (code on 2026-10-22).

## Steps

```yaml
steps:
  - {id: S1,  name: load,                   code: process.step_inputs,     status: partial,   groups: [G1,G2,G3,G4]}
  - {id: S2,  name: frame,                  code: process.step_frame,      status: partial,   groups: [G1,G2,G3,G4]}
  - {id: S3,  name: normalise_earnings,     code: process.step_normalise,  status: partial,   groups: [G1,G2,G3,G4]}
  - {id: S4,  name: liquidity_wall,         code: process.step_liquidity,  status: partial,   groups: [G1,G2,G3,G4]}
  - {id: S5,  name: claims_capstructure_covenants, code: process.step_capstructure, status: partial, groups: [G1,G2,G3,G4]}
  - {id: S6,  name: two_clocks,             code: process.step_clocks,     status: built,     groups: [G1,G2,G3,G4]}
  - {id: S7,  name: stories_cases,          code: [scenarios.live_paths, scenarios.issuer_scenarios, process.step_cases], status: partial, groups: [G1,G2,G3,G4]}
  - {id: S8,  name: value_recovery,         code: process.step_valuation,  status: partial,   groups: [G1,G2,G3,G4], note: "hy/recovery.py built and tested, not wired"}
  - {id: S9,  name: relative_value_pair,    code: [process.step_rv, process.step_pair], status: partial, groups: [G1,G2,G4]}
  - {id: S10, name: expected_alpha,         code: [hy.alpha.expected_alpha, process.step_alpha], status: partial, groups: [G1,G2,G4]}
  - {id: S11, name: gate,                   code: process.step_gate,       status: partial,   groups: [G1,G2,G3,G4]}
  - {id: S12, name: events_monitoring,      code: process.step_events,     status: partial,   groups: [G1,G2,G3,G4], note: "hy/events.py built and tested, not wired"}
  - {id: S13, name: metrics_panel,          code: process.step_metrics,    status: partial,   groups: [G1,G2,G3,G4]}
  - {id: S14, name: combined_view,          code: process.combined_view,   status: partial,   groups: [G1,G2,G3,G4]}
  - {id: S14b, name: size_calibration,      code: process.step_size_calibration, status: built, groups: [G1,G2], note: "b = 0.079, se 0.054; not > 2 se, so rank only"}
  - {id: S15, name: decision_against_cash,  code: [process.step_decision, hy.alpha.decision_against_cash, hy.alpha.opportunity_cost], status: built, groups: [G1,G2,G3,G4], note: "v0 recovery 0.4, tau 1y, k 15%"}
```

Order in code: S7 runs before S4 (S4 reads case statistics). S9's fair line feeds S7.

## Per-step outputs and the key rule changes (what agent one should implement)

```yaml
S1:  {outputs: [filing, bonds_priced, curve_basis, decision_time, sources], add: [quote_convention, accrued_interest, dirty_price]}
S2:  {outputs: [archetype, modifiers, sells, earns, breaks], add: [market_structure, business_risk (S&P 1-10, capped by industry), material_risks, watch_concentration (top1 >= 0.15)]}
S3:  {outputs: [ebitda_ltm_m, margin_trend_t, fcf_ltm_m, fcf_conversion, fcf_to_debt, eq_flags, eq_score],
      add: [ebitda_rep, ebitda_adj, ebitda_covenant, addback_table, addback_gap, covenant_gap, addback_category_share, fcf (M4.2), fcf_check_gap, ffo, focf, organic_growth],
      rules: ["reject stock comp (F3 C6) and projected synergies (C8)", "reject an add-back present 3 of last 5 years or 3-4 quarters in a row", "fcf_check_gap = (fcf - (cfo - capex)) / ebitda_adj; flag > 0.15"]}
S4:  {outputs: [L_eff_m, runway_static_q, runway_scen_q, wall_18m_m, wall_cover_4_base, refi_score_by_path],
      add: [runway_full_capex_q, funding_gap_min, first_gap_q, delta_I, delta_I_to_ebitda, watch_liquidity],
      rules: ["min_cash = (cogs_q + sga_q) / 3 (F4.4), not 0.02 * revenue_q (K11)",
              "run the severe case twice: maintenance capex only and committed capex; quote the shorter runway (K14)",
              "G_h = C0 + A_h - C_min + sum FCF_u - M_h - U_h (PDF E75)",
              "delta_I = sum D_refi_k (c_new_k - c_old_k), c_new = fwd UST at date + issuer 5y spread (PDF E77)"]}
S5:  {outputs: [debt_m, lease_debt_m, lev_gc_total, lev_lease_adj, net_lev, coverage, fccr, bonds],
      add: [lev_8x, cash_cov, ffo_to_debt, focf_to_debt, priority_ratio, notch, lev_face_k, lev_creation_k, headroom_H, debt_capacity, rp_capacity, lme_score, claims_table],
      rules: ["leases: filed liability (code already); S&P PV at 10% when untagged; 8x only pre-2019 (C6, B1)",
              "pensions: deficit incl. OPEB to debt, expense less service cost to EBITDA; tax-effect only for cash tax payers (C7, B2)",
              "fccr = (E + R - K_m) / (I_c + R + Am); also print E / (I_c + Am) (K4)",
              "check the debt tag excludes finance leases (else double count)"]}
S6:  {outputs: [fixed_charges_bn, duration_gap, breakeven_margin, coverage_contracted, renewal_dependent_share, renewal_dependent_ebitda_years, largest_shortfall_bn, years_of_ebitdar]}
S7:  {outputs: [phase, p_path, case_weights, lev_fwd_4, lev_peak_down, liq_min_down, p_refi_4, refi_fail_share, p_liq_short_8, pd_12m_by_path],
      add: [default_state_prob, first_default_q, reverse_stress, runway_full_capex_q],
      rules: ["add a default state per path with prob PD_H(m) (C10)",
              "default point: E - cash_tax - K_m < I + Am (S&P)",
              "PD: fundamental route (S&P implied rating -> cumulative default table), not spread/kappa (C2, B5); keep spread PD as display only"]}
S8:  {outputs: [market_cap_bn, market_tev_bn, tev_to_ebitda, debt_to_market_tev],
      add: [v_low, v_mid, v_high, v_default, recovery_k, recovery_pv_k, recovery_adj_k, recovery_score, ltv_k],
      rules: ["recovery_pv = R / (1 + 0.15) ** tau; tau by S&P bucket: <0.5y good collateral, 0.5-2.5y partial liquidation, >2.5y unsecured (B9)",
              "prior when no waterfall: senior unsecured recovery 0.37-0.40"]}
S9:  {outputs: [spread_5y_bp, fair_5y_bp, cheap_by_bp, fair_line, pairs],
      add: [z_rv (resid / leave-one-issuer-out sd), curve_resid_bp (leave-one-out issuer curve), spt_bond, spt_total, jtd_ratio]}
S10: {outputs: [weighted_bp_year_before_cost, weighted_bp_year_after_cost, by_path_bp_year, passes_cost_test],
      add: [l_def, jtd_per_mm, info_ratio, alpha_sized],
      rules: ["loss on price: l_def = (P_dirty/100 - R_pv) / (P_dirty/100) replaces LGD on face (C3)",
              "one hedge beta for prediction and test; beta = 1 until estimated; the code's beta = s/S sets carry to zero (K15)"]}
S11: {outputs: [table, G1, G2, G3, G6, call, direction],
      add: [G4, G5, G7, G8, G9, credit_floor],
      rules: ["PD row shown, not counted in G1 until kappa_t is fitted by bucket and date (C2)",
              "credit_floor: >= 3 reds in S4+S5 and recovery_score in {4,5} -> no 'long' on relative value alone without a curing catalyst (S&P soft factors only lower)",
              "a 'long candidate' needs alpha_sized > 0 and G1, G2, G3, G6, G8"]}
S12: {outputs: [events], add: [events_90d, event_matrix, event_var, watch_tier, trajectory, spread_shock_z],
      rules: ["watch_tier from dev = E_act/E_plan - 1: > -0.10 -> 0; -0.10..-0.20 -> 1; < -0.20 or headroom < 0.10 or watch_liquidity -> 2; breach -> 3; plan = analyst base case (public HY has no sponsor plan)"]}
S13: {outputs: [panel], add: [group per row, panel_score, red_by_group, rating_sp_implied]}
S14: {outputs: [rows, combined_before_cost, combined_after_cost, cost, anchor_before_cost, anchor_after_cost, agree, n, rank],
      add: [group per row, group_share, alpha_sized, gate_pass, grid_label]}
S14b: {outputs: [mz_a, mz_b, alpha_sized, pit_deciles],
       rules: ["alpha_sized = a + b * alpha_net, (a, b) from pooled Mincer-Zarnowitz on past closed horizons; v0 a = 0, b = 0.08",
               "raw alpha sets the rank; alpha_sized feeds S15 and size",
               "if b is not > 0 by 2 se: rank only, minimum size"]}
S15: {outputs: [mu_excess, pi_loss, pi_cash, es95, opportunity_cost, best_admissible, replaces_position],
      rules: ["actions: S14 candidates passing S11, each holding (retain, sell), cash",
              "states: path m x {survive, default}; q = p(m)(1-PD_H(m)) or p(m) PD_H(m)",
              "survive value: remaining cash flows at fwd UST + s_fair(m); default: R_pv",
              "admissible if es95 <= 0.25; choose max mu among admissible",
              "convergence at H (current choice, as coded): s_H = s_b * S_H(m)/S0 - (1 - rho^(4h)) * (s5 - s_fair5) * Sbar(m)/S0; alternative: full convergence by 6 months (1 - rho^(4h) -> 1)",
              "hedged version beside it with beta = 1 (K15); E10 uses the unhedged mu"]}
```

## Combined score (S14) - replaces ENSEMBLE_WEIGHTS

```yaml
buckets:  # user choice, 2026-10-22 (conflict W1); within a bucket, estimates keep their relative weights
  G1: {weight: 0.45, estimates: [E4, E7, E8, E9, E10]}
  clocks: {weight: 0.20, estimates: [E5]}
  G2_rest: {weight: 0.11667, estimates: [E0, E1, E2, E3, E6]}
  G3: {weight: 0.11667, estimates: [E11], one_way: true}
  G4: {weight: 0.11667, estimates: [E12, E13]}
estimates:
  - {id: E0,  bucket: G2_rest, type: alpha,   w: 0.0486, formula: "(s5 - S_index) * 1e4, beta = 1"}
  - {id: E1,  bucket: G2_rest, type: alpha,   w: 0.0292, formula: "scenario alpha before cost"}
  - {id: E2,  bucket: G2_rest, type: alpha,   w: 0.0194, formula: "D (1 - rho^(4h)) (s - s_fair) / h"}
  - {id: E3,  bucket: G2_rest, type: alpha,   w: 0.0097, formula: "pair convergence, sign by leg"}
  - {id: E6,  bucket: G2_rest, type: score,   w: 0.0097, formula: "(greens - reds) / banded"}
  - {id: E5,  bucket: clocks,  type: score,   w: 0.2000, formula: "-years_of_ebitdar"}
  - {id: E4,  bucket: G1,      type: alpha,   w: 0.0000, formula: "(PD_kappa_t - PD_fund) * l_def", note: "held at 0 until kappa_t fitted (C2)"}
  - {id: E7,  bucket: G1,      type: one_way, w: 0.1125, formula: "-(eq_score + addback_flags + fcf_check_flag)", note: "G1+G3 rules; counted in G1 as hy/groups.py does"}
  - {id: E8,  bucket: G1,      type: score,   w: 0.1125, formula: "refi_score(modal) + min(wall_cover_4, 3) + 1{funding_gap_min >= 0}"}
  - {id: E9,  bucket: G1,      type: score,   w: 0.1125, formula: "-debt_to_tev"}
  - {id: E10, bucket: G1,      type: alpha,   w: 0.1125, formula: "mu_excess / H (S15, unhedged)"}
  - {id: E11, bucket: G3,      type: one_way, w: 0.1167, formula: "-(watch_tier) - 1{headroom falling}"}
  - {id: E12, bucket: G4,      type: score,   w: 0.0583, formula: "z(log s5) - z(S&P default risk score)"}
  - {id: E13, bucket: G4,      type: score,   w: 0.0583, formula: "z(spt) if fcf_to_debt > 0 and tev/debt > 1 else 0"}
rule:
  score_to_bp: "alpha_j = (x_j - mean_run) / sd_run * sd_run(E1)"
  one_way: "alpha_j = min(0, alpha_j) for E7, E11"
  combine: "alpha_comb = sum_g W_g * mean_g, mean_g = sum_{j in g, present} w_j alpha_j / sum_{j in g, present} w_j; W_g renormalised over buckets with an estimate present"
  net: "alpha_net = alpha_comb - cost"
  sized: "alpha_sized = b * alpha_net, b = 0.079 (se 0.054), a = 0; not > 2 se -> rank only, minimum size (S14b)"
  call: "long candidate only if gate passes and S15 finds the bond beats cash within the ES budget"
  rank: "by alpha_net (raw), across the run"
weights_later:
  rule: "w_ic proportional to max(0, IC_net[j, phase]); w = lam * w_ic + (1 - lam) * w_v0; lam = N / (N + 36), N = months of history"
  guards: ["ablation: drop j if removing it does not lower ensemble net IC (C15)",
           "ensemble must beat the 'widest' rule after cost in >= 3 of 4 cycles",
           "calibration slope must rise toward 1 once the loss term is on"]
evidence_2026_10_22:
  widest_ic_net: {h3: 0.22, h6: 0.29}
  fair_line_net_ic_net: {h3: 0.21, h6: 0.25}
  fair_conv_incremental_ic: {h3: 0.036, t: 2.2}
  mz_slope: {full: [0.07, 0.08], pilot_2019_2026: [0.25, 0.31]}
  cycles_positive: "4 of 4 windows; calendar 2008 and 2015 negative"
  loss_term: off
weights_history: {backtest_led_v0: {E0: 0.25, E1: 0.15, E2: 0.10, E3: 0.05, E5: 0.05, E6: 0.05, E7: 0.05, E8: 0.05, E9: 0.05, E10: 0.05, E11: 0.05, E12: 0.05, E13: 0.05}, replaced_by: user bucket weights (W1)}
revisit_test: ["clocks backtest (now running): IC of E5 after cost, beyond the spread rank, per cycle", "backtest of each G1 estimate (E7-E10)", "then rank-IC weights with ablation; must beat widest in >= 3 of 4 cycles"]
crwv_check: {old_weights: {raw_after_cost: 145, calibrated: 11}, new_weights: "pending agent one rerun; expected to fall (clocks and G1 scores weak)"}
```

## Metrics (id, formula, unit, bands, group, step)

```yaml
metrics:
  - [g_spread, "y - y_ust(T)", bp, rec, G2, S1]
  - [cust_top1, "max_j rev_j/rev", pct, [0.15, 0.20], "G1,G3", S2]
  - [business_risk, "sum w_k b_k, capped by industry", "1-10", [4, 6], G4, S2]
  - [addback_gap, "E_co/E_adj - 1", pct, [0.10, 0.20], "G1,G3", S3]
  - [covenant_gap, "E_cov/E_adj - 1", pct, [0.10, 0.25], G1, S3]
  - [addback_category_share, "largest class / E_rep", pct, [0.05, 0.10], G3, S3]
  - [fcf_check_gap, "(fcf - (cfo - K)) / E_adj", pct, [0.05, 0.15], G3, S3]
  - [fcf_conversion, "sum(cfo - K)/sum E", ratio, [0.30, 0.10], G1, S3, higher_better]
  - [eq_score, "count EQ flags, EQ10 twice", count, [0, 2], G1, S3]
  - [margin_trend_t, "slope/se over 8q", t, [1, -1], G1, S3, higher_better]
  - [runway_static_q, "L_eff / max(0, -fcf_ltm/4)", quarters, [8, 4], G1, S4, higher_better]
  - [runway_scen_q, "first shortfall q, severe, shorter of two capex runs", quarters, [8, 4], "G1,G3", S4, higher_better]
  - [wall_cover_4, "(L_eff + sum4 fcf_base)/sum4 M", ratio, [1.5, 1.0], G1, S4, higher_better]
  - [funding_gap_min, "min_h G_h", usd_m, [0, 0], G1, S4, higher_better]
  - [delta_I_to_ebitda, "delta_I / E", pct, [0.05, 0.15], "G1,G4", S4]
  - [refi_score, "F4 points", "0-6", [4, 1.5], G1, S4, higher_better]
  - [lev_gross, "D/E", x, rank, "G1,G3", S5]
  - [lev_net, "(D - cash)/E", x, rank, G1, S5]
  - [lev_lease, "(D + L_op + L_fin)/(E + R)", x, rank, G1, S5]
  - [cash_cov, "E/I_c", x, [3.0, 1.5], "G1,G4", S5, higher_better]
  - [after_capex_cov, "(E - K)/I_c", x, [2.0, 1.25], "G1,G4", S5, higher_better]
  - [fccr, "(E + R - K_m)/(I_c + R + Am)", x, [1.5, 1.1], "G1,G3", S5, higher_better]
  - [ffo_to_debt, "FFO/D", pct, [0.195, 0.108], G4, S5, higher_better]
  - [focf_to_debt, "FOCF/D", pct, [0.085, 0.025], G4, S5, higher_better]
  - [priority_ratio, "(D_prior + L_prior)/total_assets", pct, [0.15, 0.30], G4, S5]
  - [headroom_H, "1 - lev_cov/lev_max", pct, [0.25, 0.10], "G1,G3", S5, higher_better]
  - [lme_score, "F7 points", "0-10", [2, 5], G1, S5]
  - [duration_gap, "D_O - D_R", years, [1, 3], G2, S6]
  - [breakeven_margin, "sum O / sum R", ratio, [0.6, 1.0], G2, S6]
  - [coverage_contracted, "m sum R / sum O", ratio, [1.0, 0.7], G2, S6, higher_better]
  - [renewal_dependent_share, "share of O after runoff", pct, [0.15, 0.30], G2, S6]
  - [renewal_dependent_ebitda_years, "that amount / E", years, [2, 5], G2, S6]
  - [w_down, "sum downside weights", prob, [0.25, 0.50], G1, S7]
  - [p_liq_short_8, "weight with shortfall in 8q", prob, [0.05, 0.20], G1, S7]
  - [p_refi_4, "weight with wall cover < 1 in 4q", prob, [0.05, 0.20], G1, S7]
  - [debt_to_tev, "D/TEV", ratio, [0.5, 0.7], G1, S8]
  - [ltv_k, "debt through k / V_mid", pct, [0.50, 0.80], "G1,G3", S8]
  - [recovery_score, "S&P 1-5 from recovery", score, [2, 3], G4, S8]
  - [z_rv, "resid_log / u", sd, "abs > threshold (v0 1.0)", "G1,G2", S9]
  - [half_life_weeks, "log2 / -log(rho_w)", weeks, [26, 52], G2, S9]
  - [alpha_net, "S10 sum - cost", bp_yr, [100, 0], "G1,G2", S10, higher_better]
  - [info_ratio, "alpha / sd_paths(alpha)", ratio, [1.0, 0.5], G1, S10, higher_better]
  - [watch_tier, "S12 rule", "0-3", [0, 1], G3, S12]
  - [spread_shock_z, "(ds - beta dS)/sd", sd, [2, 2], G1, S12]
  - [mz_b, "MZ slope", ratio, "0.7-1.3 green; 0.3-0.7 amber; <0.3 red", "G1,G2", S14b]
  - [es95, "expected shortfall of -R_net", pct, "<= 0.25 admissible", G1, S15]
```

## Conflicts (id -> winning rule), full text in the .tex register

C1 S14 ranks, S15 decides. C2 PD row display only until kappa_t fitted; fundamental PD. C3 loss on price, full repricing in S15. C4 constant hazard <= 1y, cumulative table beyond. C5 PDF creation leverage. C6/B1 filed lease liability. C7/B2 PDF pension form + OPEB. C8 cash and face debt apart (code already). C9 Gatto cash-first order (code already). C10 add default state. C11/B8 blend within going concern only. C12/B9 undiscounted for claims, discounted for price. C13 credit retained new money. C14 no own price in fair model. C15/B13 IC weights + ablation. C16/B4 scenario route; S&P grade only as E12; soft factors one-way. C17 Gatto organic growth. C18 per-bond quote convention. C19 F4.7 default labelled. C20 phase as prior. K1 M4.2 FCF + CFO-capex cross-check. K2/B3 no stock-comp add-back. K3 coin-toss base. K4 print both FCCR forms. K5/B6 F8 bands + trajectory + one-year-out. K6 indenture definition (no certificate in public HY). K7 20% modifier, 15% watch. K8 F6 templates. K9 F12 memo. K10 no solver. K11 F4.4 min cash. K12 update docs to match code (C6, C8, C9). K13 both trend lengths. K14 two capex runs, shorter runway. K15 one beta, 1 until estimated; add E0. B5 fundamental PD. B7 one FCF definition per use. B10 S&P stress depth. B11 spread per turn at both levels with trap guard. B12 YTW only as call cap. W1 combination weights: user bucket weights (G1 45, clocks 20, G2 rest / G3 / G4 11.67 each) replace the backtest-led weights by user choice; revisit after the clocks backtest and a G1 backtest.

Code state (2026-10-22, after agent one): loss on price built (C3); spread-to-PD gate row shown, not voting, breakeven-default row votes (C2); severe runway funds committed capex (K14); S14b built; S15 built. Gaps: claims, recovery and covenant wiring partial; credit lines untagged; gate rules G4, G5, G7, G8, G9 not built.
