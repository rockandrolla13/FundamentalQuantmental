# Combining forecast mass with the phase prior (methodology Section 5.4, framework F6.10)

## Context
Two sources speak to the same question, which macro path comes next. The phase vote of framework F6 reads the cycle from six indicators. The forecast quantile mass reads it from the forecasters. The task asks for a Bayesian update that records both.

## Options
1. Use the forecast mass alone. Ignores the base rate of what follows each phase.
2. Use the phase prior alone. Ignores current forecasts.
3. Linear pool: a fixed weighted average of the two. Simple, but the weight is a free parameter and the result is not a posterior.
4. Bayes' rule: posterior proportional to prior times mass, with the mass read as the likelihood of the forecast evidence under each path.

## Choice
Option 4.

```latex
p(m) = \frac{\pi_{phase}(m)\,\mathit{mass}(m)}{\sum_{m'} \pi_{phase}(m')\,\mathit{mass}(m')}
```

Record the prior, the mass, the posterior, and the log-likelihood ratio `log(mass(m) / mean mass)` per path. With no GDP and no CPI forecast, the mass is flat and the posterior equals the prior (logged as `f6_table`).

Phase prior, v0 (each row sums to one; calibrate from the realised path after each phase once history exists):

| Phase | Soft landing | Recession | Higher for longer | Disinflation rally | Stagflation |
| --- | --- | --- | --- | --- | --- |
| Expansion | 0.45 | 0.10 | 0.20 | 0.20 | 0.05 |
| Late cycle | 0.30 | 0.25 | 0.25 | 0.10 | 0.10 |
| Downturn | 0.15 | 0.45 | 0.10 | 0.20 | 0.10 |
| Repair | 0.35 | 0.20 | 0.15 | 0.25 | 0.05 |
| Recovery | 0.45 | 0.10 | 0.15 | 0.25 | 0.05 |

Phase rule: count the late-cycle votes of the six F6 indicators, scaled to six when some are missing. 0 to 1 is expansion, 2 to 3 late cycle, 4 or more downturn. Repair and recovery apply only when the count falls after a downturn or a repair.

Known limit: the product treats the forecast mass as independent evidence. Forecasters also read the cycle, so the update double-counts part of the information. The open test below measures the cost of that.

## Test
`tests/test_macro.py`: prior rows, mass, and posterior each sum to one; a flat mass returns the prior.

Open test that settles the choice: over matured vintages, compare the log score of the realised path under options 1, 2, 3 (weights 0.25, 0.5, 0.75), and 4. Keep option 4 unless another option wins by more than its standard error.
