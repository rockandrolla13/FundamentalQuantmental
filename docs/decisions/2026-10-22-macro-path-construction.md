# Macro path construction from forecast quantiles (methodology Section 5.4)

## Context
Section 9.2 asks for four to six named macro paths with probabilities. The task asks that each probability trace to a named forecast with a vintage. Framework F6.9 sets the fallback order: market-implied, then the F6 table, then a logged assumption.

## Options
1. Hand-set probabilities per path. Fast, but no trace to a forecast. Rejected by F6.9.
2. Scenario generation by simulation of a macro model (for example a VAR). Needs a calibrated model that the project does not have yet.
3. Regions of the joint forecast distribution of GDP growth and CPI. The quantile mass of each region is the path probability. Each path takes the conditional mean of its region.

## Choice
Option 3, with these rules and defaults (all v0; each needs calibration, framework R9):

| Item | Default | Source of the default |
| --- | --- | --- |
| Paths | soft landing, recession, higher for longer, disinflation rally, stagflation | Task statement and Section 9.2 |
| Horizon | 8 quarters | Section 9.2 |
| Normal per variable | sigma = (q90 - q10) / (2 x 1.2816), times the widen factor of the error accounting | Section 5.4 |
| Axis of the regions | Realised history: median and standard deviation of GDP growth and CPI when at least 8 quarters are passed; else GDP 1.8% plus or minus 1.5%, CPI 2.5% plus or minus 1.0% (logged assumption) | A recession is growth far below its usual level, not below the forecasters' own median. On the forecast's own scale every forecast gives the same masses |
| Region cut | c = 0.8416 (20th and 80th percentiles) | Assumption |
| Regions | recession: zG < -c, zC <= c; stagflation: zG < -c, zC > c; higher for longer: zG >= -c, zC > c; disinflation rally: zG >= -c, zC < -c; soft landing: the rest | Assumption |
| Correlation of GDP and CPI | rho = -0.2, or estimated from history (`estimate_rho`) | Assumption |
| Horizons | The 8 quarterly normals are averaged into one before the mass is computed (horizons move together) | Simplification |
| Policy rate per path | FOMC SEP median, else the market forward; shifted by d_policy = 1.5 d_cpi + 0.5 d_gdp; floored at zero | Taylor-type rule, assumption |
| Yields per path | Forward curve plus b_g d_gdp + b_p d_policy; fitted when at least 8 history rows exist, else 2-year (0.5, 0.9) and 10-year (0.6, 0.5) | Section 9.2 two-factor regression |
| Index spread, default rate, PMI | Registry when present; else 450 bp + 150 bp per -1 sd of GDP; 3.5% + 1.5 points per -1 sd; 50 + 4 zG | Logged assumptions |

Every fallback writes one line to `PathSet.assumptions`, which the memo lists.

## Test
`tests/test_macro.py`: masses sum to one; region masses match Monte Carlo within 0.01; a lower GDP median raises the recession mass; growth and policy parts add up to the yield change; no forecast row released after the decision time is read; the axis comes from history when history is passed.

Open test that settles the method: over vintages with matured outcomes, the realised path (the region that the realised GDP and CPI fall into) must have a Brier score below the phase prior alone.
