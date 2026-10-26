# F29. Macro momentum: PMI momentum and earnings revision ratio momentum

- **Rank:** 29. **Tier:** 5 (HY index timing, candidate to replace S7). **Status:** NEW at index level. S3 uses issuer estimate revisions. This factor aggregates macro data and revisions to time the whole index.
- **Level:** index. Key `index` = `"US_HY"`. One row per month end.
- **Main source:** J.P. Morgan, Inkinen and Bassi, "Systematic fixed income trading strategies", 13 April 2015. File `/home/ak/Documents/Quant Credit/Work_Quant (1)/JPM_Systematic_fixed_inc_2015-04-13_1679171 (1).pdf`, 11 pages. Printed page = PDF page. Rules and footnote 2 on p. 2. Correlations p. 2 (Exhibit 1). Earnings remark p. 3. Results p. 7 (Exhibit 9).
- **Extra columns source:** Deutsche Bank Quantcraft, "Delving into new territories", 10 November 2015. File `/home/ak/Documents/Quant Credit/Work_Quant (1)/Delving Into New Territories (1).pdf`. Printed page = PDF page. Index recipe pp. 3 to 4. Signal p. 7. Fixed income pp. 11 to 12.
- **Reader blocks:** G-F6 (`research/notes/quant-credit-review/out_G.md`), F-F5 (`out_F.md`). Every number below was checked on the source page. Reader G-F6 gives the revision ratio formula as if from the source. The source does not define it (see Definition).
- **Related decision:** `docs/decisions/2026-10-24-review-sloos-pmi.md`. See Risks.

## Claim
When the US manufacturing PMI and the I/B/E/S earnings revision ratio both rise (local and global readings agree), the US HY index excess return over duration-matched Treasuries over the next month is positive on average. When both fall, it is negative. The score x_t in {−1, −0.5, 0, 0.5, 1} then earns a positive mean return. The source evidence is on government bond duration, where the sign is the opposite. No credit test exists in the folder.

## Definition
```latex
p_t=\mathrm{agree}\big(\mathrm{PMI}^{loc}_t-\mathrm{PMI}^{loc}_{t-2},\ \mathrm{PMI}^{glob}_t-\mathrm{PMI}^{glob}_{t-2}\big),\quad
r_t=\mathrm{agree}\big(RR^{loc}_t-RR^{loc}_{t-3},\ RR^{glob}_t-RR^{glob}_{t-3}\big)
\\
\mathrm{agree}(a,b)=\begin{cases}+1&a>0,\ b>0\\-1&a<0,\ b<0\\0&\text{else}\end{cases},\qquad
RR_t=\frac{N^{up}_t-N^{down}_t}{N^{up}_t+N^{down}_t},\qquad
\mathrm{score}_t=\tfrac12\,(p_t+r_t)
```
Intuition: macro data are serially correlated and investors absorb them slowly, so a rise tends to continue (p. 2).

What the source says (JPM):
- PMI rule: short duration if both local and global manufacturing PMI increased over the past two months. Long if both fell. Neutral otherwise (p. 2, rule 1).
- Revision rule: short duration if the local and global I/B/E/S equity earnings revision ratio increased over the past three months. Long if both fell. Neutral otherwise (p. 2, rule 2).
- Timing: the PMI signal rebalances on the second working day of the month, a day after the global PMI release. The revision signal rebalances a day after its release (p. 2, footnote 2).
- Weights in the five-signal duration model: 15% PMI, 15% revision ratio (p. 7). Equal, so the score uses the plain mean of the two.
- The source does not define the revision ratio. RR above is the usual I/B/E/S breadth ratio. Our choice.

What we decide:
- **Sign.** The source trades 10Y government bond duration in 10 markets (p. 2). Rising PMI means short duration, because yields rise. For HY we flip the sign: rising PMI and revisions mean long HY. The basis is the source's remark that "positive growth revisions are typically beneficial for corporate earnings" (p. 3). This sign is a hypothesis. The source tests no credit asset. The target is the excess return over duration-matched Treasuries, so the duration leg that the source trades is not in the target.
- Local = US: ISM manufacturing PMI (`ism_pmi`). Fallback `philly_gac`, the Philadelphia Fed current activity index. The decision page above uses the same proxy because ISM data is licensed. Global = J.P. Morgan Global Manufacturing PMI (`global_pmi`).
- Missing global reading: the rule uses the local sign alone. Column `pmi_basis` (or `rr_basis`) = `local`. This gives a nonzero signal more often than the source rule. Our choice.
- Missing revision counts: score = p_t (PMI only). Column `score_basis` = `pmi`.
- PMI uses the latest vintage per month known at the decision time (our choice: the source is silent).

Extra columns (not in the score): macro beat and shock indices (DB pp. 3 to 4, 7).
1. Components per category (growth, inflation). Beat components: releases of level or year-on-year series, as 3-month changes. Shock components: actual minus survey median, as is (p. 4, footnote 9). Each component must rise when its category rises (step 1, p. 4). Index each release on its announcement date, not its reference period (p. 3). Use the first release, not revised data (p. 3, footnote 8). Forward-fill on business days (p. 4, step 1).
2. Spearman correlation on an anchored (expanding) window with correlation averaging: subsample in equal steps with every start offset, then average (p. 4, footnote 11). Negative values are set to 0 (footnote 12). Step 65 business days, from the footnote example "1-65-130". Our choice: refit the matrix at each month end, not each day.
3. Standardise each component on a 5-year window of its unique releases (p. 4, step 3, footnote 13). At least 12 releases (our choice).
4. PC1 loadings of the matrix, scaled to sum to 1. ΔI_t = Σ_j w_j z_j,t on a day with a new release, I_t = I_{t−1} + ΔI_t, else I_t = I_{t−1} (step 4).
5. B_t = 5-year z-score of I_t (step 5).
6. Signal input: the 1-year z-score of B_t, because the market prices the level but not its recent change (p. 7, step 1). Columns `growth_beat_z`, `growth_shock_z`, `inflation_beat_z`, `inflation_shock_z`.

## Inputs
| Field | Production table and column | as_of | available_at rule | Have |
|---|---|---|---|---|
| Macro releases | new optional panel `macro_series`: `series_id`, `date` (reference date, month end for monthly series), `value`, `available_at` (release time) | `date` | the release time. ISM: first business day of the next month | need |
| US PMI | `series_id` `ism_pmi`, fallback `philly_gac` | month | release day | need (licensed), proxy have |
| Global PMI | `series_id` `global_pmi` | month | release day | need (licensed) |
| Beat and shock components | `series_id` `beat:<category>:<name>` and `shock:<category>:<name>`, category `growth` or `inflation` | release | release day | need (surveys need Bloomberg) |
| Revision counts | new optional panel `revision_counts`: `date` (month end of the I/B/E/S period), `region` (`US` or `GLOBAL`), `n_up`, `n_down`, `available_at` | month | release + 1 day (JPM fn. 2) | need |

No other module defines `macro_series` yet. This page defines it. A later module (F25, F27) should reuse the schema.

## Build steps
1. Keep rows with `available_at` <= `decision_time(as_of)`. No `macro_series` and no `revision_counts`: empty frame. Panels with no PMI and no revision reading: one row, NaN score, status `no_signal`.
2. PMI: last vintage per month. Change over 2 months, local and global. Latest month must be at least as_of − 2 months, else status `stale`.
3. RR per region and month from `revision_counts`. Change over 3 months. Same staleness rule.
4. p_t, r_t by the agree rule. Score = mean of the available ones. NaN if none.
5. Beat and shock indices per category from the components. Report B_t and its 1-year z-score at the last business day <= decision time.

## Code placement
- `hy/factors/f29_macro_momentum.py`. `compute(panels, as_of, pmi_months=2, rr_months=3, max_lag_months=2)`.
- Output columns: `date`, `index`, `score`, `available_at`, `status`, `score_basis`, `pmi_source`, `pmi_basis`, `pmi_date`, `pmi_local`, `pmi_local_chg`, `pmi_global_chg`, `pmi_signal`, `rr_basis`, `rr_date`, `rr_local`, `rr_local_chg`, `rr_global_chg`, `rr_signal`, then `<category>_<kind>` and `<category>_<kind>_z` for growth and inflation, beat and shock.
- Helpers: `monthly_series`, `change_over`, `agree_signal`, `revision_ratio`, `beat_components`, `rolling_z`, `averaged_spearman`, `pc1_weights`, `beat_index`, `trailing_z`.
- Reuses `hy.backtest.decision_time`. Docstrings cite methodology Section 8 (S7 replacement), Section 3.6 (macro inputs) and Section 9.2 (macro overlay).

## Tests
- No look-ahead: rows after as_of and rows with `available_at` after the decision time change nothing.
- Sign: PMI up in both series gives +1. Down in both gives −1. Mixed gives 0. Same for RR.
- Fallback: no `revision_counts` gives score = PMI signal. No global series gives the local sign.
- Edges: no panel gives an empty frame. A stale PMI gives NaN and `stale`.
- Helpers: RR on hand counts. PC1 weights sum to 1 and match a hand matrix. Averaged Spearman matches the hand mean.
- Evaluation (production machine): monthly, 1998 (source start, p. 7) to 2024. x_t times the next 1-month and 3-month HY index excess return. Pass: mean positive in at least three of the four `CYCLE_WINDOWS`. Reader G-F6 also proposes IR > 0.3 for the combined rule. That threshold is the reader's, not the source's.

## Risks
- Evidence is government bonds, not credit. Since 1998: PMI momentum 2.4% a year, IR 0.59. Revision ratio momentum 3.7%, IR 0.84. Five-signal model IR 1.31 (p. 7, Exhibit 9). The DB bond futures strategy uses inflation only, Sharpe 0.61 before cost over 11 years (p. 12). DB rejects growth for bonds, because its effect on bonds depends on the level of growth (p. 11, footnote 26). HY has the same problem.
- Overlap. Signal return correlations (p. 2, Exhibit 1): revision ratio with PMI 0.62, with equity momentum 0.61. PMI with equity momentum 0.55, with bond momentum 0.41. Expect overlap with F26 (index trend) and the equity momentum factors. Without the equity momentum and revision signals, the combined IR "would be slightly negative" (p. 4).
- The decision page `2026-10-24-review-sloos-pmi` found that the PMI proxy level did not predict issuer EBITDA declines, and the "PMI below 50" vote failed S3 (2 of 4 windows). This factor does not contradict it. It uses the PMI change, not the level, and it predicts index returns, not EBITDA declines. It does not enter `m_t` or the F6 vote. But the result is a warning: a PMI signal in HY has failed the cycle rule before.
- S7 failed (`2026-10-24-s7-sector-tilt`). This factor is index beta, not a sector tilt.
- Monthly signal with three states: low turnover, but a short record. Four cycle windows give few independent signals.

## Open questions
- Revision universe: S&P 500 (breadth, as the source) or HY issuers only (closer to the target). Default: the region `US` that production supplies. Production should try both.
- Global readings may be missing. Default: local sign alone. A production test compares it with the source rule.
- Beat and shock z-scores enter the score only after the production test. The source maps them to returns with a regression per asset (p. 7, step 2). Default: report them, do not combine.
