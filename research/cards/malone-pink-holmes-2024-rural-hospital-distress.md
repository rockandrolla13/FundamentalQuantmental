# Malone, Pink and Holmes (2024), "An updated model of rural hospital financial distress"

The Journal of Rural Health (2024), pp. 1-11, DOI 10.1111/jrh.12882. Peer-reviewed journal article, open access. We read the full published article, 11 pages. We did not read the online supplement (Tables A1 to A4 and the Appendix). Page numbers below are journal pages. Journal page = PDF page. Evidence class: hospital-level accounting distress and closure in US rural hospitals, no bonds, no spreads, no defaults.

## Claim
A probit on public cost-report data predicts rural hospital financial distress 2 years ahead with a test-set AUC of 0.87 (pp. 1, 4). Higher total margin, more quality benchmarks met, Critical Access Hospital (CAH) status, a higher Medicare outpatient share, and larger size go with lower distress (p. 4). System affiliation and market poverty go with higher distress (p. 4).

## Method
**Accounting link (p. 2).**

```latex
\text{Equity}_{t+1} = \text{Equity}_t + \text{Net Income}_{t+1} \quad (1)
```

Intuition: losses erode equity, so sustained losses lead to negative equity and then to closure.

**Distress index (p. 2).**

```latex
\Pr\left(y_{h,k,t+2} = 1\right) = f\left(X_{h,t}\beta + \phi_k\right) \quad (2)
```

Intuition: one latent index ranks every hospital, and each outcome k only moves the cut point.

Here `f` is the standard normal CDF (probit, p. 3). `X` holds predictors in year t or earlier. The outcome is in year t + 2 (p. 3).

**Stacked data (p. 3).** Each hospital-year enters three times, once per outcome: negative cash flow margin, negative equity, and closure. The term `phi_k` absorbs the outcome type. Every predictor must have the same effect on all three outcomes. The authors accept this constraint for parsimony (p. 3).

**Outcome 1, negative cash flow margin (Table 1, p. 5).**

```latex
\text{CFM} = \frac{NI - \text{CIA} + \text{Dep} + \text{Int}}{NPR + \text{OthInc} - \text{CIA}} \times 100\%
```

Intuition: a negative value means the hospital uses depreciation to cover operating cost (p. 3). CIA is contributions, investments and appropriations. NPR is net patient revenue.

**Outcome 2, negative equity (Table 1, p. 5).** Total assets minus total liabilities below zero. The authors call this accounting insolvency (p. 3).

**Outcome 3, closure (Table 1, p. 5).** Complete closure or conversion to a facility with no inpatient service, from the North Carolina Rural Health Research Program list (p. 3).

**Fit and checks (pp. 3-4).** The authors split hospitals at random into a training set and a test set. They fit the probit with hospital-clustered standard errors on the training set. They handle gaps by complete case analysis. They check multicollinearity with variance inflation factors. They report the AUC and a 20-bin calibration plot on the test set.

```latex
\text{AUC} = \Pr\left(\hat p_{\text{distress}} > \hat p_{\text{no distress}}\right)
```

Intuition: the AUC is the chance that a random distressed row ranks above a random healthy row (p. 4).

**Risk tiers (p. 4).** Lowest risk: predicted chance of negative cash flow margin below 10%. Mid-lowest: predicted chance of negative equity below 10%. Mid-highest: 10% to below 25%. Highest: 25% or more. The authors take these cut points from the 2017 model and move them to favour sensitivity.

## Data
- Healthcare Cost Reporting Information System (HCRIS) annual cost reports, general care nonfederal rural hospitals, 2013 to 2019 (p. 2).
- 15,402 hospital-years with a 360 to 366 day report. 91.7% have complete data (p. 4).
- Final sample: 14,116 hospital-years, 2311 hospitals, 49 states (p. 4).
- Outcome rates 2 years ahead: negative cash flow margin 22.3% (p. 4), negative equity 10.5%, closure 0.7% (p. 4).
- Mix: 56.8% CAH, 11.3% for-profit, 39.7% system-affiliated (p. 4). Mean net patient revenue $49.3 million, SD $58.4 million (p. 4).
- Mean total margin 2.3%, SD 11.4 (Table 1, p. 5).
- Training and test set sizes: not reported. The split ratio: not reported. The Figure 1 bin counts sum to about 20,417 stacked test rows (our arithmetic from the labels, p. 6).

## Result
**Accuracy (pp. 1, 4).** Test-set AUC 0.87. The authors call this "good" on a scale where 0.8 to 0.9 is good (p. 4). AUC by outcome type: not reported. AUC by year: not reported. The source reports no confidence interval for the AUC.

**Calibration (Figure 1, p. 6).** In the 0% to 5% predicted bin, 10,697 test rows show about 1.3% observed distress (p. 6). The authors say the fit weakens in the highest bins, where the counts are small (p. 6).

**Predictors (Table 2, p. 7).** Average marginal effects (AME) in percentage points of distress probability. For a non-logged continuous variable, the AME is for a one-SD rise (p. 7).

| Predictor | AME | SE | Significance |
|---|---|---|---|
| Total margin, year t | −2.01 | 0.29 | p < 0.001 |
| Total margin, year t − 1 | −0.67 | 0.28 | p < 0.05 |
| Total margin, year t − 2 | −1.64 | 0.24 | p < 0.001 |
| Percent CAHMPAS benchmarks met | −3.62 | 0.40 | p < 0.001 |
| CAH status | −3.16 | 1.08 | p < 0.01 |
| Medicare outpatient payer mix | −0.89 | 0.38 | p < 0.05 |
| Net patient revenue (log) | −3.50 | 0.57 | p < 0.001 |
| System affiliation | +2.06 | 0.74 | p < 0.01 |
| Market population in poverty | +1.09 | 0.35 | p < 0.01 |

**Not significant at 5% (Table 2, p. 7).** Outpatient revenue share −0.49. Uncompensated care (charity care plus bad debt over operating expense) +0.33. Medicaid payer mix +0.02. Medicaid-to-Medicare fee index −0.62. Medicare Advantage day ratio −0.06. For-profit +2.09 (SE 1.20). Miles to a large hospital −0.45. Market share −1.59. Market population −0.41. Medicare Advantage penetration −0.66.

**Outcome terms (Table 2, p. 7).** `phi` for negative equity −11.73 and for closure −21.06, both p < 0.001.

**Risk tiers (pp. 1, 7; Figure 2, p. 8).** Shares of all 14,116 rows: lowest 30.55%, mid-lowest 32.52%, mid-highest 26.40%, highest 10.52%. Observed test-set rates:

| Tier | Negative cash flow margin | Negative equity | Closure |
|---|---|---|---|
| Lowest | 5.78% | 1.50% | 0.00% |
| Mid-lowest | 15.78% | 5.63% | 0.27% |
| Mid-highest | 37.94% | 15.66% | 0.85% |
| Highest | 61.57% | 43.02% | 3.33% |

**Stability against the 2017 model (p. 9).** Total margin, benchmarks met, CAH status, net patient revenue and market poverty are significant in both versions.

## Limits
- No leverage, debt service, interest coverage, liquidity or cash-on-hand predictor enters the model (Table 1, pp. 5-6). Equity enters only as an outcome.
- The outcomes are accounting states and closure. Bankruptcy is out of scope (p. 9). Bond default and spreads are absent.
- The sample is rural and mostly nonprofit: 11.3% for-profit (p. 4) and 56.8% CAH with cost-based Medicare payment (p. 4). Sponsor-owned HY hospital issuers are large urban and suburban for-profit systems. The Medicare outpatient and CAH effects come from cost-based payment (p. 9). They do not transfer to HY issuers.
- The data end in 2019. The authors say the model may be less accurate on early 2020s data because of COVID-19 relief funds (p. 9).
- The model omits staff numbers and type, state policy changes, and management changes (p. 9). Labour cost is not a predictor.
- The model is predictive, not causal (pp. 8, 9). The authors explain the system affiliation sign as selection: weak hospitals seek a system (p. 9).
- The pooled AUC mixes three outcomes with prevalences of 22.3%, 10.5% and 0.7% (p. 4). The `phi_k` terms alone separate closure rows from cash flow rows. Part of the 0.87 may come from outcome type, not from hospital risk (our inference, not tested). The source reports no AUC per outcome.
- The AME unit for logged variables is not stated. The Table 2 note covers only non-logged variables (p. 7).
- Tier shares use the full sample. Tier outcome rates use the test set (pp. 1, 7). The two bases differ.
- Source inconsistency: the text gives 22.3% negative cash flow margin (p. 4). Table 1 gives 22.2% on n = 13,515 (p. 5).
- Source inconsistency: Table 2 labels the benchmark variable "(2 years)" (p. 7). The text and Table 1 give no 2-year definition (pp. 3, 5).
- The training and test sizes are not reported. The closure window is "by year 2021" for a 2019 row (p. 3), but Table 1 measures days from the midpoint of year t (p. 5). The exact cut-off is not reported.

## Section touched
`docs/methodology.md` Section 4.1 (profitability: margin level and margin trend), Section 7.2 (signs of the empirical model). `docs/framework.md` F2 archetype A2 (identify-by rule and downside driver). `docs/factors/SECTOR-models.md` Section 3.1, `health_care` (GICS 35) row. `hy/sector/drivers.py` `SECTOR_DRIVERS["health_care"]`.

## Use for the A2 archetype
**What the source says.** Profitability over three years, size, and quality benchmark performance predict hospital distress 2 years ahead (p. 7). All three margin lags carry a negative sign (p. 7). Bad debt plus charity care does not predict distress once margin is in the model (p. 7). Medicaid payer mix does not predict distress (p. 7). The source tests no leverage measure.

**What the data says.** `hy/sector/drivers.py` sets `health_care` to `log_lev`, `margin`, `margin_trend`, `fcf_debt`, all "Our choice". `margin` is LTM EBITDA margin (F23). `margin_trend` is the 8-quarter slope t-statistic (`hy.state.margin_trend`). The repo has no size driver and no multi-year margin level. `docs/framework.md` F2 A2 names "bad debt and labour inflation" as the downside driver. It identifies A2 by a government payer share above a third of revenue. No source in the repo tests these A2 choices. `docs/factors/SECTOR-models.md` Section 1 records that gap.

**What we decide (our proposal, not the source's claim).**
1. Keep `margin` with sign −. This source supports a margin level as a distress predictor (Table 2, p. 7). The source uses total margin on net income, and our driver uses EBITDA margin. Record the definition gap in the driver comment.
2. Add `margin_3y`, the mean of the last three fiscal-year EBITDA margins, as a candidate. All three lag effects have the same sign (p. 7). Same signs point to a multi-year level, not a trend. A trend would show a positive weight on the old lag.

```latex
\text{margin\_3y}_{i,t} = \tfrac13 \sum_{j=0}^{2} \frac{\text{EBITDA}_{i,t-j}}{\text{Sales}_{i,t-j}}
```

Intuition: a hospital with thin margins for three years has less equity buffer than one with one bad year (Equation 1, p. 2).

3. Add `log_size`, the log of LTM sales, as a candidate with sign −. Net patient revenue has the second largest significant AME, −3.50 (p. 7). Rating effects in the fit may absorb it, so the test decides.
4. Keep `log_lev` and `fcf_debt` as "Our choice". This source neither supports nor rejects them, because it has no debt predictor.
5. Do not add payer mix as a signed driver. Keep payer share only as the A2 identify-by rule. The Medicare effect here comes from CAH cost-based payment (p. 9), and the Medicaid effect is 0.02 (p. 7).
6. Mark "bad debt" in the F2 A2 downside driver as untested. The source finds no effect for charity care plus bad debt (p. 7). The source does not test labour.
7. Test. Take GICS 35 HY issuers, 2010 onward, with fields available at the decision time. Fit three nested sector fair spread models: the current list, the list plus `margin_3y`, and the list plus `margin_3y` and `log_size`. Report the out-of-sample rank IC of the residual against 6-month excess return, and the AUC for a 2-year downgrade to CCC or default. Adopt `margin_3y` if its coefficient keeps sign − and the AUC rises by at least 0.02 in at least three of the four cycles (2008, 2015, 2020, 2022). Drop `margin_trend` if it loses its sign once `margin_3y` is in the model. If GICS 35 has fewer than 15 issuers, the pooled model applies, and the test reports that the sample is too thin.
