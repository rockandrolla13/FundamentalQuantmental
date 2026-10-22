# Issuer scenarios under macro paths: v0 defaults (methodology Sections 5.4, 7.5; framework F4, F6)

## Context
The clock write-up and the pair report now show each issuer under each live macro path: leverage, refinancing risk, and expected alpha. The data gives the paths, the issuer's starting point, its debt ladder, and its bond spreads. It does not give a calibrated fair-spread model, ratings, sector sensitivities, or a refinance-access calibration. The task rule is: no hand-set number without a decision page. This page lists every one. Code: `scripts/scenarios.py` (`V0`).

## Choice (all v0; framework R9)

| Item | Default | Reason |
| --- | --- | --- |
| Archetype | From framework F2 per issuer, in `data/analyst_inputs/<ticker>.yaml` | F2 table names hospitals A2, data centres and shipping A5, software A6, casinos A7 |
| Revenue sensitivity to GDP, `beta_sector` | A2 0.3, A4 1.5, A5 1.0, A6 0.5, A7 1.2 | Ordering by cyclicality; calibrate per sector on history (Section 5.2) |
| Trend GDP `G_bar` | 1.8% | Reference point of the path construction page |
| Moderate downside, annual revenue | A2 -5%, -2%; A4 -20%, -10% (book, TM Corp); A5 -15%, -5%; A6 -10%, -3%; A7 -20%, -5% | F6 table names the driver; size is v0. Replace with each issuer's own last-cycle path |
| Trough margin | 0.8 x current EBITDA margin | F6 severe case needs a trough |
| Starting growth | Trailing four quarters over the four before, quarterly rate, bounded to -5% and +8% | Base equals consensus plus a gap; no consensus source yet |
| Capex in the cases | Maintenance only: the lower of capex and depreciation | F4.7: depreciation is the floor for A4 and A5; growth capex is cuttable and funded by its own facilities |
| Working-capital days | Bounded to 0 to 120 | Payables can include capex payables |
| Debt lines | Each ladder bucket due inside 8 quarters is one line; the rest one line; coupon = derived cash rate; all fixed | No standard fixed or floating tag |
| Fair spread under a path | s_fair_now x S(m) / S_now; s_fair_now from the pair report's fair line | Spread-proportional systematic repricing |
| Expected loss | PD x LGD = s_fair(m) / kappa, kappa = 2, LGD = 0.6; index loss S(m) / kappa | Keeps loss consistent with spread; kappa from the credit-spread literature, to calibrate |
| Hedge | Spread-proportional: beta = s_now / S_now | Removes carry and systematic moves, so alpha measures mispricing |
| Hedged convergence | D x (1 - rho^(4h)) x (s - s_fair_now) x S(m) / S_now, rho = 0.85 a quarter | Derived from the hedge; rho to replace with the measured half-life |
| Default risk from the cases | PD >= 0.5 x need x (1 - p_refi_access) + 0.5 x p_liq_short_8; need = debt due inside 8 quarters over total debt | Links the F6 cases to alpha without the F6.3 cliff |
| F4 points with data | 1: spread inside 700 bp stands in for B- or better; 2: an issuer bond first trades inside the 6-month TRACE window; 4: longest bond inside 700 bp (spread only; low-coupon long bonds trade below 90 because of rates); 5: path HY spread below 1.5 x today. Points 3 and 6: 0 | F4 table; the 6-month window understates point 2 |
| F4 score to p_refi_access | 0.20, 0.50, 0.80, 0.92, 0.97, 0.99, 0.995 for scores 0 to 6 | An open market plus one more point refinances; calibrate from realised refinancings by score (F4) |
| Cost | 20 bp of spread round trip, times spread duration | Typical institutional high yield bid-ask |
| Horizon | 6 months | Matches the pair report |

## Test
Offline: `tests/test_scenarios.py` (F4 score arithmetic and path dependence). Live: every issuer's per-path PD and alpha is printed by `scripts/rv_pair.py`; the first run with a cliff-type rule gave every issuer a 50% PD in a recession, which this design removes.
Open test that settles the defaults: the alpha backtest (`docs/writeup/backtest_alpha.pdf` when complete). If realised hedged returns do not rank with the predicted alpha, revisit kappa, rho, and the access map first.

Known limit: under spread-proportional pricing a mispricing scales with the market, so the stress paths enlarge it. In practice a stress often widens a gap before it closes.
