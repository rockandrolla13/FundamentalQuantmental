# F30. HY spread against VIX gap

- **Rank:** 30 of 30. **Tier:** 5 (HY index timing, candidate to replace S7). **Status:** NEW at index level. Proposal only, no evidence.
- **Level:** index. Key `index` = `"US_HY"`. One row per month end.
- **Source:** CARV Quantitative Strategies, "HY vs VIX Stnd Perf", Global Macro Fund, Relative Value Trading Strategies, pricing date 2011-10-06. File `/home/ak/Documents/Quant Credit/HY_VIX (2).pdf`, 4 pages. Page = PDF page. Statistic tables for 1M and 3M p. 1 and p. 2, 6M p. 2, 12M p. 3, 24M p. 4. Regression labels sit inside chart images. We read them from a 300 dpi render.
- **Reader block:** A1-F16 (`research/notes/quant-credit-review/out_A1.md`). The block proposes z(HY) − z(VIX). It omits the regression lines that the screen prints. It quotes the 12M z-scores 3.67 and 2.59 correctly (p. 3).
- **The source is a screen. It has no backtest, no trading rule and no return result.** It shows one day. Every rule below beyond the regression is our choice.

## Claim
When the US HY index spread is wide against the spread that a trailing 12-month regression on the VIX level predicts, the HY index earns a positive excess return over the next 3 months. A tight spread against the fit predicts a negative excess return.

## Definition
```latex
s_d = a_t + b_t\,\mathrm{VIX}_d + e_d,\quad d \in (t-12\text{m},\,t],\qquad
\hat\sigma_t=\sqrt{\tfrac{1}{n-2}\sum_d \hat e_d^{\,2}},\qquad
\mathrm{score}_t = \frac{s_t-(\hat a_t+\hat b_t\,\mathrm{VIX}_t)}{\hat\sigma_t}
```
Intuition: equity volatility prices the common risk, so a spread above the VIX line is credit cheap against equity.

What the source says:
- Each window shows CDX HY against the VIX **level** in a scatter with an OLS line, "Y = a + b X; R2". 1M: Y = 190.36 + 14.5347 X, R2 = 0.71 (p. 1). 3M: Y = 249.66 + 11.9844 X, R2 = 0.86 (p. 1). 6M: Y = 249.07 + 12.0074 X, R2 = 0.92 (p. 2). 12M: Y = 221.51 + 12.5889 X, R2 = 0.86 (p. 3). 24M: Y = 266.66 + 11.9535 X, R2 = 0.67 (p. 3). The reader may misread 12.5889 as 12.5989 at screen resolution.
- Each table gives Last, changes, Z, percentile Pct, Dist = Last − Mean, Min, Mean, Max and StdDev per series. 12M (p. 3): CDX HY Last 863.70, Mean 493.91, StdDev 100.72, Z 3.67, Pct 99.60. VIX Last 40.82, Mean 21.64, StdDev 7.40, Z 2.59, Pct 95.95. Z = (Last − Mean) / StdDev: (863.70 − 493.91) / 100.72 = 3.67.
- A second scatter regresses the ratio CDX HY / VIX on VIX. 12M: Y = 31.14 − 0.3443 X, R2 = 0.65 (p. 3).
- The source states no sign, no threshold and no horizon.

Our arithmetic on the 12M numbers (not printed): fitted = 221.51 + 12.5889 × 40.82 = 735.39 bp. Gap = 863.70 − 735.39 = 128.31 bp. The fit is consistent: 493.91 − 12.5889 × 21.64 = 221.49 against the printed 221.51. With residual sd ≈ 100.72 × sqrt(1 − 0.86) = 37.7 bp, the score is about 3.4.

What we decide (all "Our choice"):
- Regress on the VIX level, as the source does. Not the log.
- Window 12 calendar months, daily rows, at least 120 matched dates. 12M is the window the reader block picked. The 6M window has the best fit (R2 0.92) and stays a parameter.
- The fit includes the last date, as the screen plots the last point with its line.
- Sign: positive gap = long HY. The source gives no direction. The reader block proposes this one.
- Horizon 3 months, from the reader block test.
- Extra column `z_gap` = z(spread) − z(VIX) over the same window, the reader-block form. It is not the score.

## Inputs
| Field | Production table and column | as_of | available_at rule | Have |
|---|---|---|---|---|
| HY index spread | `hy_index` `spread` (decimal), `date` (wiring 4.5) | `date` | `date` + 1 day | have |
| VIX close | new optional long panel `macro_series`: `series_id` = `"VIXCLS"`, `date`, `value` (index points), `available_at`. Same schema as F25 section 4. | `date` | `date` + 1 day (FRED) | need |

The source uses CDX HY in bp. We use the index OAS in decimal. `b` then reads in decimal per VIX point. `hy_index` must hold daily rows. Wiring 4.5 asks only for monthly rows. `distress` is not used.

## Build steps
1. Keep rows with `available_at` <= `decision_time(as_of)` and `date` <= as_of. Keep the last vintage per `date`. Drop NaN values.
2. Take `VIXCLS` rows from `macro_series`. Inner join with `hy_index` on `date`.
3. Keep dates in (as_of − 12 months, as_of]. Check: at least 120 dates, last date >= as_of − 7 days. Else NaN score with status `too_few_obs` or `stale`.
4. OLS of spread on VIX. Residual of the last date over the residual sd (n − 2 divisor). That is the score.
5. Fill `z_spread`, `z_vix` (sample sd), `z_gap`, `alpha`, `beta`, `r2`, `fitted`, `gap`.

## Code placement
- `hy/factors/f30_hy_vix_gap.py`. `compute(panels, as_of, window_months=12, min_obs=120)`.
- Output: `date`, `index`, `score`, `available_at`, `signal_date`, `n_obs`, `spread`, `vix`, `alpha`, `beta`, `r2`, `fitted`, `gap`, `resid_sd`, `z_spread`, `z_vix`, `z_gap`, `status`.
- Helpers: `matched_series`, `ols_fit`, `regression_gap`, `window_z`.
- Reuses `hy.backtest.decision_time`. Docstrings cite methodology Section 8 (S7 replacement) and Section 3.6 (macro inputs).

## Tests
- Unit (`tests/test_factor_f30.py`): contract. No look-ahead with rows after as_of and late `available_at`. Sign: a spread pushed above its VIX line gives a positive score, pushed below gives a negative one. Edges: no `macro_series` or no `VIXCLS` gives an empty frame. Short history gives `too_few_obs`. A stale join gives `stale`. NaN rows drop. Helpers: exact line recovery, the p. 3 fitted value and gap, the p. 3 z-scores 3.67 and 2.59.
- Evaluation (production machine): monthly score against the next 3-month HY index excess return. Pass: (a) rank IC above zero in at least three of 2008, 2015, 2020, 2022. (b) In the reader-block test, long HY beta in the top quintile of the score has hit rate above 60%, net of cost. No source number backs either threshold.

## Risks
- No evidence. The source shows one day in October 2011, near a local peak in both series.
- One time series, about 4 independent 3-month targets a year. Overfit risk is high.
- The fit is unstable. The slope moves from 11.95 to 14.53 bp per VIX point across windows (pp. 1 to 3). R2 drops to 0.67 at 24M (p. 3).
- A wide gap may mean a credit-specific default wave that VIX does not see. The gap then widens further.
- Overlap: the gap carries part of the spread level, so it overlaps F28 fair value gap and S7. No correlation is in the source.
- Turnover is low with monthly rebalance. Cash HY trades the index beta through CDX HY or ETFs.

## Open questions
1. Window: 1M to 24M are all on the screen. Default 12M. Test 6M on the production machine.
2. Level or log VIX: the source uses the level. A log fit bends the line at high VIX. Default the level.
3. Include the last date in the fit: default yes, as the screen. Excluding it gives a true out-of-sample residual.
4. Ratio form: the ratio regression (p. 3) is not built. Default the level regression, because its R2 is higher in every window (pp. 1 to 4).
5. Index: CDX HY in the source, cash OAS here. CDX has no cash basis and no rating drift.
