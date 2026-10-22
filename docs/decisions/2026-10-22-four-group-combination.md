# Four-group combination: one analyst, one combined estimate (methodology Section 8; framework F10, F12.1)

## Context
The user asked for one analyst that runs every issuer through four groups of methods and gives one combined result:
G1 core process (Gatto's seven steps, methodology, framework F1 to F13, the RV PDF), G2 built methods (clocks, fair line, pair, stories, cases, alpha, gate, F8 panel), G3 credit skills (hy-model-standards and six private-credit skills), G4 books (Kricheff; Ganguin and Bilardello).
The earlier ensemble (decision page 2026-10-22-combined-view) had nine estimates and no group structure. Its estimate E4 converted the spread to a PD at a fixed kappa and used that in G1 of the gate. Mapping conflict C2 rejects this. Its alpha charged default loss on face. Mapping conflict C3 rejects this.
Code: `hy/groups.py` (`ESTIMATES`, `GROUP_WEIGHTS`, `combine`, `verdict`), `scripts/process.py` (`group_estimates`, `combined_view`, steps 4, 5, 11, 12, 15).

## Options
1. Group-first weights chosen by hand. Each group gives a mean of its own estimates; the groups get fixed shares (first draft: G1 0.35, G2 0.35, G3 0.10, G4 0.20). This weighs each source of method equally, whatever its record.
2. The estimate set of the combined framework (research/combined_framework_spec.md S14, E0 to E13). Each estimate has one group and one v0 weight. The group shares follow from the weights: G2 0.65, G1 0.20, G4 0.10, G3 0.05. The spec rests G2's share on the backtest. Spread level has a net rank IC of 0.22 at 3 months and 0.29 at 6 months. The fair line has 0.21 and 0.25. No estimate of G1, G3 or G4 has an IC yet.
3. IC weights now. No group except G2 has an IC history, so this is option 2 with zeros.
4. User-set buckets (2026-10-22): G1 core process 45%; the two clocks (E5) 20%, taken out of G2 as their own bucket; the rest of G2 (E0, E1, E2, E3, E6) 35/3 = 11.67%; G3 skills 11.67%; G4 books 11.67%. Inside each bucket the estimates keep their option-2 weights relative to each other.

## Choice
Option 4. **This is the user's choice. It overrides the backtest-led weights of option 2.** The user wants the core process and the clocks to drive the combined number, not the spread level.

What the backtest-led weights were (option 2, kept in code as `hy.groups.SPEC_GROUP_WEIGHTS`): G2 0.65 (E0 0.25, E1 0.15, E2 0.10, E3 0.05, E5 0.05, E6 0.05), G1 0.20, G4 0.10, G3 0.05. The evidence behind them: spread level net IC 0.22 (3 months) and 0.29 (6 months); fair line 0.21 and 0.25; leverage residual beyond spread level +0.036 (t 2.2). No other estimate has an IC.

Effective weights now (`hy.groups.effective_weights`): E7, E8, E9, E10 0.1125 each (E4 0); E5 0.200; E0 0.0486, E1 0.0292, E2 0.0194, E3 0.0097, E6 0.0097; E11 0.1167; E12 and E13 0.0583 each. The estimates with a backtest record (E0, E2) now carry about 7% together, against 35% before. The two clocks (no backtest) carry 20%. G3 can only lower the number (one-way), so its 11.67% is a pure penalty bucket. If an estimate is missing, its bucket keeps its share and the bucket mean renormalises. If a whole bucket is missing, the bucket shares renormalise.

Earlier choices stay in the record: option 1 (no evidence behind its shares) and option 2 (the backtest-led weights above).

The estimate set and its v0 weights inside each bucket (spec S14):

| Id | Group | Estimate | Type | v0 weight |
| --- | --- | --- | --- | --- |
| E0 | G2 | Spread level (s5 - S_index), beta = 1 (spec K15) | alpha | 0.25 |
| E1 | G2 | Weighted cases and stories (the anchor) | alpha | 0.15 |
| E2 | G2 | Fair-line convergence D (1 - rho^(4h)) (s - s_fair) / h | alpha | 0.10 |
| E3 | G2 | Pair convergence, signed by the leg | alpha | 0.05 |
| E4 | G1 | Spread-implied PD gap x l_def: shown only (C2) | alpha | 0.00 |
| E5 | G2 | -years of EBITDAR in fixed bills | score | 0.05 |
| E6 | G2 | (greens - reds) / bands on the F8 panel | score | 0.05 |
| E7 | G1 (and G3) | -(earnings-quality flags + add-back flags + FCF check flag) | one way | 0.05 |
| E8 | G1 | refinance score + min(wall cover, 3) + 1{funding gap >= 0} | score | 0.05 |
| E9 | G1 | -debt / market TEV | score | 0.05 |
| E10 | G1 | Excess over cash, mu_excess / H, full repricing (RV PDF E50 to E58) | alpha | 0.05 |
| E11 | G3 | -(watch tier) - 1{headroom falling} | one way | 0.05 |
| E12 | G4 | z(log s5) - z(S&P default risk score) | score | 0.05 |
| E13 | G4 | z(spread per turn) when FCF / debt > 0 and TEV / debt > 1, else 0 | score | 0.05 |

Size calibration (step S14b, `process.step_size_calibration`). The alpha backtest (decision page 2026-10-22-alpha-backtest-design; `data/raw/backtest/summary_full.json`, read only) gives a Mincer-Zarnowitz slope for `fair_line_net` at 6 months of 0.079 (se 0.054) for 2008 to 2026, and 0.252 for 2019 to 2026. The memo shows the raw combined number and the calibrated number = slope x raw, and states that alpha sizes are uncalibrated. The slope is not above zero by two standard errors, so by the spec rule the number ranks issuers and sizes nothing beyond the minimum. The backtest panel has no default-loss term.

Runway (spec K14). The cases fund maintenance capex only. The severe case now runs a second time on the likely story with all committed capex. The memo shows the static runway and both severe runs, and quotes the shortest (CRWV: 2 quarters, not "no shortfall").

LTM inputs. Compustat leaves a quarter's cash flows blank when it cannot de-cumulate year-to-date figures (CCL Aug-2025, WYNN Jun-2026). `process.fill_cash_flow_gaps` reads that quarter from its first 10-Q or 10-K, only if accepted before the decision date (`hy.sources.xbrl.cash_flow_from_filing`). LTM cash flows are now strict: a missing quarter blanks the LTM, never a silent three-quarter sum. LTM earnings with one quarter missing use the input layer's 3 x 4/3 fallback (THC, MGM), flagged in `ltm_scaled_x4_3`.

Rules. A score is standardised across the run and scaled by sd(E1). A one-way estimate is min(0, scaled score), so a checklist can only lower the number. Missing estimates drop out and the weights renormalise inside their bucket. Trading cost is subtracted once, the same round-trip cost as E1. `alpha_sized` = 0 + 0.08 x the after-cost number is the v0 Mincer-Zarnowitz size (spec S14b). The rank uses the raw after-cost number.
Group verdict: "supports owning" when the group's alpha beats the trading cost; "leans to owning" between zero and the cost; "against owning" below zero; "no objection" when a one-way group sits at zero.

v0 inputs of the G1 additions (mapping Top 10 items 1 to 4):

| Input | v0 | Why |
| --- | --- | --- |
| Recovery R per 1 of face | 0.40 (1 - V0 lgd) | Senior unsecured prior; the claims view replaces it |
| Delay tau, required return k | 1 year, 15% | Mapping item 2; Gatto's example uses 20% over 2 years |
| ES budget for an admissible position | 25% of capital over 6 months | Spec S15 |
| Minimum cash C_min | (revenue - EBITDA) / 3 of the last quarter = (cogs + SG&A) / 3 | Framework F4.4; spec K11 |
| c_old | Mean TRACE coupon of bonds due inside 27 months, else LTM interest / debt | Mapping item 4 |
| c_new | Path Treasury par yield for 5 years at the maturity quarter + today's 5-year spread | Mapping item 4 |

Where this page departs from the spec, and why:
- S15 survive value. The spec reprices at the forward Treasury + s_fair(m), which closes the whole gap in six months. The code closes (1 - rho^(4h)) of the gap at the measured speed of methodology 7.5. That is the speed E1 and E2 use. Full closure in six months would contradict the AR(1) half-life.
- The gate (C2). The spread-to-PD row stays in the table, renamed, and does not vote in G1 or G6. A breakeven row replaces it in the vote: be = s / l_def, the yearly default rate at which the spread only pays for default losses on the price paid. It is a hurdle the price sets, not a physical PD.
- The watchlist "plan". borrower-monitoring compares with a sponsor plan. The spec uses the analyst base case. No past base case is stored yet, so the code uses the same quarters a year earlier. It switches when the run history exists.
- Funding gap with no tagged revolver. The gap then rests on missing data, so the indicator in E8 counts 0 and the memo raises an open question.

Known limits: E0, E1, E2 and E12 all read the spread level, so the level carries more weight than any single row shows. The score estimates are relative to the issuers in the run. Covenant levels parse from the filing text for some issuers only (three of eight on 2026-10-22). Headroom uses our EBITDA, not covenant EBITDA.

## Test
0. The test that would revisit the user's weights: in the alpha backtest, compute each bucket's estimates point in time and its net rank IC per cycle (2008, 2015, 2020, 2022), at 3 and 6 months. Compare three ensembles after cost: the user's buckets, the backtest-led weights, and E1 alone. Revisit the user's weights if the backtest-led ensemble beats them on net IC in at least three of the four cycles, or if the two-clocks bucket shows no positive net IC in at least three cycles. The clocks need the RPO and lease history built point in time first; until then the 20% rests on judgement.
1. Unit tests (`tests/test_four_groups.py`): the funding gap, the loss on price, the refinancing shock, the decision against cash, the Treasury hedge return, and the combination. The combination tests check equality with the flat weighted mean, renormalisation, zero weight, one-way capping, and the spec group shares. They also check the user's bucket shares, the within-bucket ratios, and that a bucket keeps its share when one estimate is missing. All pass.
2. The alpha backtest settles the weights. Compute each estimate point in time and score its rank IC per cycle phase. Then set w = lam w_ic + (1 - lam) w_v0, with lam = N / (N + 36). Ablate each estimate and drop any whose removal does not lower the ensemble's net IC (C15). Keep the four-group ensemble only if its IC beats E1 alone after costs in at least three of the four cycles (2008, 2015, 2020, 2022).
3. Repricing check (C3): on TRACE history, compare predicted and realised 6-month returns of E10 against the M7.5 sum, by price bucket (below 90, 90 to 103, above 103).
