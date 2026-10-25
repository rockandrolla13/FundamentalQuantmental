# Decision: a medium-term model from macro paths to sector EBITDA and earnings

Date: 2026-10-24. Status: **proposed, not fitted.** Sections touched: methodology 5.2 (driver shifts), 5.4 (macro
paths). Companion page: `2026-10-24-wt-sector-rules.md` (the 15 single-horizon rules).

## Question

Given a macro path over the next 1 to 3 years, how do EBITDA and earnings of each sector move, quarter by quarter?
The 15 rules ask a yes-or-no question at one horizon. The scenario engine needs a full response path.

## Options

| Option | What it is | For | Against |
| --- | --- | --- | --- |
| A. Panel local projections (Jorda 2005) | One regression per horizon h = 1 to 12 quarters: the EBITDA change from q to q+h on the macro block at q | Gives the response at each horizon directly. Stays valid when the model is wrong in detail (Montiel Olea, Plagborg-Moller, Qian and Wolf, Econometrica 2026) | Wide bands at long horizons in a short sample |
| B. VAR or Bayesian VAR with sector blocks | One system of macro and sector equations, iterated forward | Narrow bands. One model for all horizons | Bias at long horizons when the lag length is short (same paper). Many parameters for 11 sectors |
| C. Global VAR with a satellite equation (Castren, Dees and Zaher, ECB WP 875, 2008) | A macro model makes the path. A separate credit equation maps the path to sector outcomes | The design used in stress tests. Keeps credit apart from macro | We have no macro model of our own. Section 5.4 already gives the paths |
| D. Panel error correction, pooled mean group (Pesaran, Shin and Smith, JASA 1999) | A long-run link of sector EBITDA to activity, common across sectors. Short-run speed and dynamics differ by sector | Captures the medium-term pull back to the long-run level | Needs a long-run relation that holds. Margins shift with structure |
| E. Quantile panel model (Covas, Rump and Zakrajsek, IJF 2014) | The same regressions for the 10th percentile, not the mean | Credit cares about the bad tail. In their backtest, realised 2007-09 losses fell inside the quantile model's bands and outside the linear model's | More noise. Needs firm-level data |

## Choice

A satellite design (C) with local projections (A) as the satellite, plus a tail version (E):

1. **The macro path comes from Section 5.4.** No new macro model.
2. **The satellite is a panel of local projections.** For each sector s and horizon h = 1 to 12 quarters:

   `Y[s, q -> q+h] = a[s,h] + B[s,h]' M[q] + sum_{j=1..4} c[s,h,j] * Y[s, q-j -> q-j+1] + e`

   - `Y` is the sector median of the firm outcome of the sector-rules page (EBITDA change over sales, or the change
     in ROE for financials).
   - `M[q]` is a small macro block known at q: activity (the Philadelphia Fed GAC), inflation (CPI, 12-month change),
     oil (12-month change), the 10-year yield (12-month change), and the Baa spread. Five series, not 30, because
     11 sectors and about 120 quarters cannot carry more.
   - Four lags of the outcome. Lags keep the inference valid and remove the trend that the sector already carries.
3. **Partial pooling across sectors.** Each `B[s,h]` shrinks toward the all-sector mean `B[h]`. The shrinkage weight
   comes from the data (empirical Bayes). A sector with a strong, stable response keeps its own slope. A noisy sector
   moves toward the average.
4. **Smooth over horizons.** The response at h should not jump between h and h+1. Use a penalty on the second
   difference of `B[s,h]` over h (smooth local projections). The penalty is chosen by holdout error before 2012.
5. **Tail version.** The same regressions for the 10th percentile of firms in each sector, instead of the median.
   This gives the downside case its own response.
6. **Long-run check.** Fit option D once as a check. If EBITDA levels and activity share a long-run relation, the
   local projections at h = 8 to 12 should agree with it. If they disagree, the page records both.

## How the scenario engine uses it

For a macro path `m[1..12]` from Section 5.4, the sector EBITDA path is `sum over h` of the response to each step of
the path. This replaces the single `beta_sector` of Section 5.2 with a profile by horizon. The downside cases use the
tail version. The five named paths then give five sector EBITDA paths, which feed `g`, `v` and `a` in the cases.

## The test that settles it

1. **Sample.** Fit on 1994-2011. Score out of sample from 2012, with the model refitted each quarter on data known
   then.
2. **Baselines.** (a) Each sector's own past changes only (the lag terms). (b) The sector mean.
3. **Measure.** Mean squared error at h = 4, 8 and 12, pooled over sectors. Clark-West against each baseline. For the
   tail version, the pinball loss at the 10th percentile.
4. **Pass.** The model beats baseline (a) at h = 4 and h = 8 with Clark-West p below 0.05, pooled over sectors, and
   the sign of the response to activity is the same in at least 3 of the 4 cycle windows.
5. **Power.** From 2012 there are about 13 non-overlapping 4-quarter windows per sector. Pooling 11 sectors makes the
   test usable at h = 4 and h = 8. At h = 12 the result is reported, not used to pass.

## Order of work

1. Run the 15 sector rules first. They use the same data pull and the same outcomes.
2. Then fit this model. If no rule passes on fundamentals, the model still runs: it asks a wider question (the
   whole macro block, all horizons) than any single rule.

## Sources

- Jorda (2005), "Estimation and inference of impulse responses by local projections", American Economic Review.
- Montiel Olea, Plagborg-Moller, Qian and Wolf, "Double robustness of local projections and some unpleasant
  VARithmetic", Econometrica 94(4), 2026.
- Castren, Dees and Zaher, "Global macro-financial shocks and expected default frequencies in the euro area", ECB
  Working Paper 875, 2008.
- Pesaran, Shin and Smith (1999), "Pooled mean group estimation of dynamic heterogeneous panels", JASA 94(446),
  621-634.
- Covas, Rump and Zakrajsek (2014), "Stress-testing US bank holding companies: a dynamic panel quantile regression
  approach", International Journal of Forecasting 30, 691-713.

Source cards for these five go in `research/cards/` before the fit.
