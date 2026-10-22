# Combined view: every approach as one estimate of expected alpha (methodology Section 8; framework F10, F12.1)

Superseded by `2026-10-22-four-group-combination.md`: the estimates now follow the combined framework spec (E0 to E13, four groups), and E4 no longer votes (mapping C2). `ENSEMBLE_WEIGHTS` is removed from the code.

## Context
The process runs many approaches per issuer: the cases under the macro paths, the fair line, the pair, the market-implied default probability, the two clocks, the F8 health panel, the F3 earnings tests, the F4 liquidity and refinancing score, and the F7.7 market check. Each says something about whether the bond is worth owning. The user asked for one weighted combination, set against the expected alpha of the probability-weighted cases. Code: `scripts/process.py` (`combined_view`, `ENSEMBLE_WEIGHTS`).

## Options
1. Report the approaches side by side and leave the combination to the reader. Not comparable; no rank.
2. Methodology Section 8 composite: standardise each signal, weight by trailing rank IC per cycle phase. The right end state, but no IC history exists yet.
3. Ensemble in alpha units now: each approach gives an estimate of expected alpha in bp a year; the combination is their weighted average with stated v0 weights; switch to option 2 when the backtest supplies the ICs.

## Choice
Option 3.

| Estimate | How it becomes bp a year | v0 weight |
| --- | --- | --- |
| E1 Weighted cases and stories | Scenario-weighted expected alpha before cost (methodology 5.4, 7.5) | 0.30 |
| E2 Fair-line convergence | D (1 - rho^(4h)) (s - s_fair) / h, rho = 0.85 a quarter | 0.15 |
| E3 Pair convergence | The pair gap's convergence over h at its measured weekly half-life, + for the long leg, - for the short | 0.10 |
| E4 Default the price assumes | (PD implied by the spread at kappa = 2 - PD in our cases) x LGD | 0.10 |
| E5 Two clocks | Fixed charges in years of EBITDAR (lower is better), standardised across issuers, x sd(E1) | 0.10 |
| E6 Health panel | (greens - reds) / bands on the F8 panel, standardised, x sd(E1) | 0.05 |
| E7 Earnings quality | -(count of F3 flags raised), standardised, x sd(E1) | 0.05 |
| E8 Liquidity and refinancing | F4 score on the likely path + wall cover (capped at 3), standardised, x sd(E1) | 0.10 |
| E9 Market value check | -(debt / market enterprise value), standardised, x sd(E1) | 0.05 |

Missing estimates drop out and the weights renormalise. The combined alpha after cost subtracts the same round-trip cost as E1. The rank across issuers is the force rank of F12.1 until the F10 composite exists.

Known limits: E1 and E2 share the fair line, so it carries more weight than its 0.15 suggests. The score estimates are relative to the issuers in the run, so they change when the run changes.

## Test
The alpha backtest: compute each estimate point in time, score each one's rank IC per cycle phase, and replace these weights with weights proportional to max(0, IC) (F10.2). Keep the ensemble only if its IC beats E1 alone after costs in at least three of the four cycles.
