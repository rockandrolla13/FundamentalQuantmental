# McCarthy, Fader and Hardie (2017), "Valuing Subscription-Based Businesses Using Publicly Disclosed Customer Data"

Journal of Marketing 81(1), pp. 17-35, DOI 10.1509/jm.15.0519. Peer-reviewed journal article. We read the author manuscript dated 15 October 2016, on LBS Research Online, 59 pages. Page numbers below are PDF pages of that file. PDF page = printed page + 3. Evidence class: two listed firms, equity value, no credit outcome.

## Claim
A customer model fitted only on public disclosures can project revenue and value a subscription firm (p. 5). Prior models assume a constant retention rate, and they do not fit the data (pp. 4, 12). The method gives a stock price within 3% of market for Dish Network (p. 27) and a price of $4.24 against $3.90 for Sirius XM (p. 30).

## Method
**Inputs.** Quarterly customer additions, losses, the ending count and revenue: `ADD`, `LOSS`, `END`, `REV` (pp. 9-10).

**Decomposition.** A cohort matrix `C(m, m')` counts customers from month `m` still active in month `m'` (p. 8). Revenue is the average customer count times revenue per user (p. 22, equation 25).

**Retention.** A proportional hazard with a Weibull baseline and gamma heterogeneity (pp. 15-16).

```latex
B_R(m,m') = \sum_{i=m+1}^{m'} \big[(i-m)^{c_R} - (i-m-1)^{c_R}\big] e^{\beta_R x_R(i)} \quad (13)
S_R(m'-m \mid m) = \left(\frac{\alpha_R}{\alpha_R + B_R(m,m')}\right)^{r_R} \quad (14)
```

Intuition: each customer has a churn rate, churn rates differ across customers, and macro covariates scale the hazard over time.

**Acquisition.** A split hazard on a prospect pool. The pool grows with population and with past churn, and a share `π_NA` never buys (pp. 17-19, equations 15-19).

**Estimation.** Nonlinear least squares on quarterly disclosures, with terms for missing early data (pp. 19-20).

```latex
SSE_{MISS} = \sum_{q=q_A+1}^{q_B} \big[(END_q - END_{q-1}) - (\widehat{END}_q - \widehat{END}_{q-1})\big]^2 + \sum_{q=q_B+1}^{Q} \big\{(ADD_q - \widehat{ADD}_q)^2 + (LOSS_q - \widehat{LOSS}_q)^2\big\} + (END_Q - \widehat{END}_Q)^2 \quad (21)
```

Intuition: the fit uses whatever a firm disclosed, and it treats a gap in the record as missing and not as zero.

**Revenue per user.** A time trend, or a random walk with drift if the trend residuals fail a unit root test (pp. 20-21).

**Residual lifetime (p. 31).** Expected remaining life is the sum of survival conditional on the present tenure (equation 26).

**Validation.** Rolling two-year forecasts over 60 calibration periods against two prior models, GLS and SSW (pp. 25-27).

## Data
- Dish Network, Q1 1996 to Q1 2015, 77 quarters. `ADD` starts in Q1 1998 (p. 23).
- Sirius XM. Data on paid customers starts in Q3 2008, so almost half of the history is absent (p. 29).
- Covariates: three quarter dummies and a Great Recession dummy for Dish (p. 24). Vehicle sales for Sirius XM (p. 29).

## Result
**Dish parameters (Table 2, p. 53).** Retention: `r` 1.648 (se 0.232), `α` 81.196 (se 4.897), `c` 1.423 (se 0.056). The recession coefficient on the retention hazard is 0.129 (se 0.010). So the recession raised the churn hazard by about 14% (our arithmetic: exp 0.129 = 1.138).

**Sirius XM parameters (Table 6, p. 57).** Retention: `r` 153.206 (se 35.129), `α` 2671.833 (se 602.632), `c` 1.066 (se 0.085). The authors report that the gamma term adds no significant fit for Sirius XM (p. 30, footnote 17).

**Forecast error (Table 3, p. 54).** Mean absolute percent error at two horizons:

| Horizon | GLS | SSW | This paper |
| --- | --- | --- | --- |
| Q+1 | 26.0 | 14.7 | 8.2 |
| Q+8 | 55.8 | 22.9 | 16.0 |

**Value.** Dish: $64.62 against $66.38 at market. GLS gives $48.84 and SSW gives $63.72 (pp. 27-28). Sirius XM: $4.24 against $3.90. GLS gives $0.41 and SSW gives $6.55 (p. 30).

**Sensitivity (p. 28).** The 95% price interval is +/- 0.2% from acquisition, +/- 3.4% from retention, and +/- 3.0% from revenue per user.

**Tenure (pp. 31-32).** A customer who joined at the valuation date has an expected remaining life of 5.5 years. A customer with 10 years of tenure has 9.4 years.

## Limits
- Two firms. No cross-section and no credit outcome.
- The framework fits only subscription firms that report customer counts, where attrition is observed (p. 36).
- The authors warn that the data supports few parameters (p. 36). For Sirius XM the gamma term adds no significant fit (p. 30, footnote 17). So one firm's data does not always identify heterogeneity.
- Spend and churn are assumed uncorrelated (p. 21, footnote 13).
- Source inconsistency: in the file we read, Table 3 prints the same numbers in the `ADD`, `LOSS` and `END` panels (p. 54). The text says the method's errors are about one third below SSW (p. 27). We quote one panel, and only for the ratio across models. Check the journal version before any use of the levels.
- Source inconsistency: subscriber acquisition cost is $854 in the text (p. 32) and $716.46 per customer in Table 5 (p. 56).

## Section touched
`docs/methodology.md` Section 4.7 (`revenue_runoff`, `renewal_dependent_share`, `coverage_contracted`, `renewal_revenue_years`) and Section 5.1 (case revenue paths). `hy/clocks.py`.

## Use for the two clocks
**What the source says.** A renewal curve can be fitted from public quarterly counts. A recession dummy in the hazard moves it. A single retention rate gives worse forecasts.

**What the data says.** `clock_facts.py` rule 3 spreads all RPO over 2 years, then assumes no revenue after that. So the backtest revenue clock has no renewal curve. Section 4.7 reports no test of a hazard.

**What we decide (our proposal, not the source's claim).**
1. For issuers that disclose subscriber additions, losses and counts, replace the post-RPO zero with the fitted curve.

```latex
\hat{R}_{i,t} = \widehat{ARPU}_{i,t} \cdot \hat{C}_{i,t}, \qquad \hat{K}_{i,t} = m_i \hat{R}_{i,t}, \qquad \text{hazard\_cover}_{i,t} = \frac{\sum_{s \le t} \hat{K}_{i,s}}{\sum_{s \le t} O_{i,s}}
```

Intuition: the cost clock meets an expected revenue curve, and not a cliff at the end of the signed contracts.

2. Report the curve for the current customer base with no new customers. Report a second one with new customers. The gap shows how far the clocks rest on sales not yet made.
3. Fit a recession coefficient on the hazard. Use it in the Section 5.2 macro paths, so the renewal risk moves with the cycle.
4. Mark the scope. This covers cable, satellite, telecom and software issuers that disclose counts. All others use `fader-hardie-2010-contractual-customer-base-heterogeneity.md` or stay on the grid.
5. Test. Refit the mismatch features with `hazard_cover` on the covered issuers. The curve earns its place if `hazard_cover` adds to `coverage_contracted` in the spread regression, with t above 2 (Our choice, v0).
