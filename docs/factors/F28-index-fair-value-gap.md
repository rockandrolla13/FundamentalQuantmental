# F28. HY index fair value gap net of carry

- **Rank:** 28. **Tier:** 5 (HY index timing, candidate to replace S7). **Status:** NEW at index level. S1 is a bond-level fair value. This factor values the whole index against a macro anchor.
- **Level:** index. Key `index` = `"US_HY"`. One row per month end.
- **Main source:** J.P. Morgan, de Kock, "Trading and Hedging Long-Term FX Fundamentals with J.P. Morgan's Fair-Value Model", Investment Strategies No. 55, 29 April 2009. File `/home/ak/Documents/Quant Credit/Work_Quant (1)/JPM_Investment_Strategie_2009-04-29_287192 (1).pdf`. Summary p. 1. Test design and Table 2 p. 2. Tables 3 and 4 p. 3. Equations (1) to (6) and Table 5 p. 4. Printed page = PDF page.
- **Model source:** J.P. Morgan, de Kock, "A new fair-value model for G10 currencies", 6 September 2008. File `/home/ak/Documents/Quant Credit/Work_Quant (1)/JPM_A_new_fair_value_mod_2008-09-06_470005 (1).pdf`. Driver rule p. 2. Table 1 p. 4. Permanent share p. 5. Forecast rule p. 7. Estimation pp. 8 to 9.
- **Reader block:** G-F5 (`research/notes/quant-credit-review/out_G.md`).

## Claim
When the US HY index spread sits above its macro fair value by more than the carry the long earns over 6 months, the index excess return over the next 6 months is positive on average. The mirror case gives a negative return. The evidence is from G10 FX only (2004 to 2008). No credit test exists in the folder.

## Definition
```latex
\hat s_k = a + b^{\top} x_k \ (\text{OLS}, k \le t),\quad
s^{*}_t = w\,s_t + (1-w)\,\hat s_t,\quad
m_t = s_t - s^{*}_t,\quad
E_t = \kappa\,D_t\,m_t + s_t\,\tfrac{h}{12},\quad
\mathrm{pos}_t=\begin{cases}+1&E_t>\delta\\-1&E_t<-\delta\\0&\text{else}\end{cases}
```
Intuition: a valuation gap closes slowly, so the trade pays only when the expected convergence beats the carry that the position gives up by waiting.

What the source says (2009 pp. 2 and 4, 2008 pp. 2 to 8):
- Rule (3) p. 4: go short FX when `e*_{t-1} − f = (e*_{t-1} − e_t) − (r* − r) > δ ≥ 0`. The gap to fair value minus the cost of carry must beat the threshold δ. Profit (4) is `e_{t+n} − f`.
- Rule (5) p. 4 prints "< δ" for the long. The text on p. 2 says "undervaluation exceeds its forward premium by more than the threshold". So the long condition is `< −δ`. The printed sign is a typo.
- Convergence regression (1) p. 4: `e_{t+n} − e_t = α (e*_t − e_t) + ε`, no intercept. Out of sample, about 25% of the gap closes in 3 quarters and about 50% in 18 months (p. 2, Table 2: α = 0.2586 at 3 quarters, 0.5208 at 6 quarters).
- The model starts on 1Q80 to 4Q03 data. It re-estimates each quarter with one more quarter of data. Each fair value uses only data public at the time (p. 2). The fair value lags one quarter because the macro data publish three months late (p. 2).
- Thresholds 0%, 5% and 10% (Table 3, p. 3). The rule beat carry at 6 months for every threshold (p. 2). At 10% it beat carry by about 3% at 6, 12 and 18 months (p. 3).
- Fair value = long-run regression on drivers, then a permanent part. Table 1 (p. 4) puts weight 0.2637 on the actual rate and scales each driver by about 0.74. Drivers must work for many currencies and periods. Episode variables are excluded to avoid over-fitting (p. 2). Forecasts hold the drivers at the latest value (p. 7).

What we decide:
- `s_t`: monthly mean of the daily `hy_index` spread, decimal. The source uses period averages (2009 p. 2, Table 2 notes). Our choice.
- `x_k`: three FRED series in levels (our choice, after methodology 5.2.1 `m_t` and reader G-F5). `DRTSCILM` (SLOOS net tightening, 5.2.1 and decision `2026-10-24-review-sloos-pmi`). `T10Y3M` (10-year minus 3-month Treasury slope, 5.2.1). `VIXCLS` (reader G-F5). Few series, general drivers, as the 2008 note asks (p. 2). The parameter `regressors` changes the list.
- Each month k takes, per series, the latest observation with `available_at` <= `decision_time(k)`. It must be at most 190 days old (our choice: one quarter of SLOOS plus its lag). The `available_at` filter replaces the source's one-quarter lag of `e*`.
- Expanding OLS with an intercept on all months up to t. At least 60 months (our choice). The source starts with 96 quarters (p. 2). Refit every month (our choice: each refit only adds public data).
- `w = 0` (our choice). The 0.2637 of Table 1 is an FX panel estimate (p. 4). We fit no permanent-transitory split. Parameter `actual_weight`.
- `D_t`: median `mod_dur` of eligible `bond_panel` rows at as_of. Parameter `duration` overrides. Without both: status `no_duration`, NaN score.
- `h = 6` months. The source result holds at 6 months for every threshold (p. 2). `δ = 0` (our choice from the tested 0, 5, 10%, p. 3: FX magnitudes do not transfer to spreads).
- `κ = 1`: the full gap, as rule (3) assumes. With `kappa=None` the code uses the fitted `α̂_h` (clipped to [0, 1]).
- Score = `E_t`, the expected 6-month excess return of a long index position from gap and carry. Higher = long.

## Inputs
| Field | Production table and column | as_of | available_at rule | Have |
|---|---|---|---|---|
| Index spread | `hy_index` `spread` (decimal), `date` | `date` | `date` + 1 day (wiring 4.5) | have |
| Macro series | new panel `macro_series`: `series_id`, `date`, `value`, `available_at` (long format) | `date` | FRED release time, or ALFRED vintage time | need |
| Duration | `bond_panel` `mod_dur`, `date` | `date` | as the panel (wiring 5) | have |

`macro_series` holds FRED ids `DRTSCILM` (quarterly), `T10Y3M` (daily) and `VIXCLS` (daily). Several vintages per `date` are allowed. Without `hy_index` or `macro_series`, the result is an empty frame.

## Build steps
1. Filter every panel to `available_at` <= `decision_time(as_of)`. Keep the last vintage per date.
2. Build the monthly spread mean from the first index month to as_of.
3. Build `x_k` per month at its own decision time. Mark stale values NaN.
4. Fit OLS on complete months. Fewer than 60: status `too_few_obs`.
5. `ŝ_t`, `s*_t`, `m_t`, carry `s_t h/12`, `E_t`, position.
6. Out-of-sample gap history: for each past month τ, fit on months <= τ, store `m_τ`. Fit `α̂_h = −Σ m_τ Δs_τ / Σ m_τ²` on pairs with τ + h <= t (eq. 1). At least 24 pairs (our choice).

## Code placement
- `hy/factors/f28_index_fair_value_gap.py`. `compute(panels, as_of, regressors=REGRESSORS, horizon=6, threshold=0.0, kappa=1.0, actual_weight=0.0, duration=None, min_train=60, max_stale_days=190)`.
- Output columns: `date`, `index`, `score`, `available_at`, `position`, `spread`, `fair_spread`, `misalignment`, `carry`, `duration`, `kappa`, `alpha_h`, `alpha_n`, `n_train`, `r2`, `status`.
- Helpers: `monthly_spread`, `macro_at`, `macro_matrix`, `fit_fair_value`, `fair_spread`, `carry_over`, `carry_adjusted_edge`, `edge_position`, `oos_misalignments`, `convergence_alpha`, `index_duration`.
- Reuses `hy.backtest.decision_time` and `hy.backtest.eligible`. Docstrings cite Section 8 (S7 replacement), Section 7.5 (expected convergence) and Section 5.2.1 (`m_t`).

## Tests
- No look-ahead: rows after as_of, and macro rows published after the decision time, change nothing. A late vintage of an old month changes nothing before its release.
- Sign: a spread above a known linear fair value gives `E > 0` and position +1. A spread far below gives −1. A small gap below fair with large carry stays long or flat, never short.
- Helpers: OLS recovers known coefficients. `α̂` on a hand series. The edge and position on hand numbers. A series built to close half of each gap gives `α̂ = 0.5`, the 18-month share of p. 2.
- Edges: no `hy_index` or no `macro_series` gives an empty frame. Short history gives `too_few_obs`. No duration gives `no_duration`. A stale or absent series gives `stale_macro`. No spread row in the as_of month gives `no_spread`. `kappa=None` with fewer than 24 gap pairs gives `no_alpha`. NaN spreads drop out of the fit.
- Evaluation (production machine): monthly, 1997 to 2024, expanding window. Signal `E_t`. Horizon 6 and 12 months. Metric: out-of-sample slope of the future index excess return on `E_t`, and the hit rate of the position (reader G-F5). Pass: positive slope with HAC t above 2. The position return beats buy-and-hold HY in at least 3 of the 4 `CYCLE_WINDOWS`.

## Risks
- Evidence is FX only. The sample is 2004 to 2008, 21 model versions (p. 2). The gap explains only 15% to 16% of 18-month moves (p. 2). The authors call the profit "not high enough to compensate for the variability of profits" (p. 4).
- The anchor can break. A regime change (2008, 2020) moves the fair value itself.
- VIX is a market price, not a fundamental. If it moves with the HY spread, the fair value follows the market and the gap shrinks. Drop `VIXCLS` if the gap has no power.
- Carry = spread ignores expected default loss. The rule then leans long in wide markets.
- The duration comes from TRACE bonds, not from the index.
- Overlap: F26 (trend) is likely negative in correlation, because value and momentum returns correlate negatively (reader G-F6, not checked here).

## Open questions
- Regressors. Default `DRTSCILM`, `T10Y3M`, `VIXCLS`. A trailing default rate is the strongest anchor in methodology 5.2.1 but is not on FRED.
- Levels against a cointegration fit. Default levels OLS. The 2008 note uses panel cointegration (p. 8). One index gives no panel.
- `κ`: the full gap (source rule) or the fitted `α̂_h`. Default the source rule.
