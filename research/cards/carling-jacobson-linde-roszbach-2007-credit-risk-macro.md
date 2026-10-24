# Carling, Jacobson, Lindé, and Roszbach (2007), "Corporate Credit Risk Modeling and the Macroeconomy"

Journal of Banking and Finance 31(3), pp. 845–868. Peer-reviewed journal article. We read the open working paper: Sveriges Riksbank Working Paper 142, September 2002, "Capital Charges under Basel II: Corporate Credit Risk Modelling and the Macro Economy", https://archive.riksbank.se/Upload/Dokument_riksbank/Kat_foa/wp_142.pdf. RePEc lists the JBF article as the journal version of this paper. Page numbers below are the printed page numbers of WP 142. The journal version may differ in tables and numbers.

## Claim
In a quarterly firm-level default hazard, macro variables matter beside firm accounting and payment-remark data (pp. 18–19). The output gap, the yield curve slope, and household expectations all enter with the expected sign and are significant (Table 2, p. 19). The move of the output gap from −7% to 0 over 1994–2000 lowers predicted default rates by a factor of about 10 (p. 18). A macro-only model tracks only the smooth part of the aggregate default rate. Firm data are needed for the spikes (pp. 19–20).

## Method
**Discrete-time hazard (pp. 14–17).** T is the number of quarters to default. The hazard is h(k) = Pr[T = k | T > k − 1]. Exits other than default (loan repaid, end of sample) censor the spell.

```latex
h(k) = h_0(k)\,\exp\big( m[x, z, x(\tau), z(\tau);\ \beta, \gamma, \beta^{\tau}, \gamma^{\tau}] \big)   \quad (2)
```

Intuition: a baseline risk by loan age, scaled up or down by firm factors x and macro factors z at calendar quarter τ.

```latex
\ln L = \sum_{i=1}^{n} \Big[ c_i \ln h_i(k_i) - \sum_{s=1}^{k_i - 1} h_i(s) \Big]   \quad (3)
```

Intuition: each spell adds its default quarter (if any) and its survival through the quarters before. c_i = 1 if spell i ends in default.

The form of m comes from a regression smoother of log odds on each regressor, added one at a time (p. 16). The authors keep a variable if it is theoretically justified, stable across sub-samples, simple, and has |t| > 2 (p. 17). Pseudo-R² measures the overlap of predicted PDs for defaulters and non-defaulters (p. 17).

**Point-in-time rules (pp. 10, 14).** Accounting data lag 4 quarters. Output gap and household expectations lag 2 quarters, their publication delay. The yield curve slope does not lag, because it is known in real time.

**Covariates.**
- Firm: total sales, EBITDA over total assets, inventories over sales, total liabilities over total assets (TL/TA), and two payment-remark dummies (pp. 11–12).
- Loan: credit type, loan age (p. 18).
- Macro: output gap (Apel and Jansson unobserved components), 10-year minus 3-month government yield, first difference of household expectations of the Swedish economy (pp. 13–14).

## Data
- All 54,603 Swedish aktiebolag (limited companies) with a loan at one major Swedish bank on at least one quarter end from March 1994 to March 2000. 576,768 firm-quarter observations, 69,249 loan spells, 3,598 defaults (pp. 6, 16–17).
- Default: the bank's rating class 15, which needs 60 days overdue and a judgement that payment is unlikely. It leads official bankruptcy by one or more quarters (p. 7).
- 65% of observations are firms with 5 or fewer employees (p. 6).
- Missing ratio values are set to the sample mean (p. 10). About 10% of the sample would be lost otherwise.
- Average annual default rate 2.6%. In 1995, 4% of counterparts defaulted (p. 7).

## Result
- **Macro coefficients (Table 2, p. 19).** Output gap, lagged 2 quarters: −0.341 (0.018) per percentage point. Household expectations, first difference, lagged 2 quarters: −0.163 (0.016). Yield curve slope, 10Y − 3M: −0.232 (0.025) per percentage point. All signs are as expected.
- **Size.** The output gap moved from about −7% to 0 (p. 18). At −0.341 per point, that is a factor of e^{0.341 × 7} ≈ 11 in the hazard. The authors state "roughly 10 times smaller" (p. 18).
- **Firm coefficients (Table 2).** TL/TA 2.829 (0.114). Inventories over sales 0.436 (0.124). Sales −0.079 (0.023) per million SEK. EBITDA/TA 0.038 (0.026), not significant. Payment remarks of categories 8, 11, 16, 25, 31: 2.638 (0.080), a factor of about 14 (p. 18). Short-term credit 0.761 (0.049), about twice the risk of long-term credit.
- **Loan age.** Duration dependence is weak. The second year is about 3% riskier than the first, not significant. The authors say "a logit approach may very well suffice" (footnote 12, p. 18).
- **Discrimination (p. 19).** Pseudo-R² 63% for the full model, 50% for a model with the bank's rating class only.
- **Time series fit (pp. 19–20, Figure 7).** A regression of the actual quarterly portfolio default rate on the model's mean predicted rate gives R² of 85%. On a model with the output gap only, R² is 41%. The output-gap model catches the smooth trend but not the spikes of 1995 and 1997.
- **Accounting data and remarks (p. 18).** Accounting data predict well alone. Remark data take most of their weight when both enter.
- **No conditional correlation in the VaR (pp. 21–22).** The VaR simulation assumes zero default correlation given the covariates. The authors argue that the macro terms remove the common driver. They give no test of that claim.
- **Smoothing of PD (p. 32).** For capital, a 4-quarter moving average of default frequencies balances risk sensitivity and stability.

## What our data says (docs/methodology.md 5.2 and 5.4, hy/macro.py, hy/groups.py, data/raw/backtest, 24 October 2026)
**What the plan holds.** Section 5.2 fits σ(θ_0 + θ'm_t + θ_sector) with m_t = (`hy_oas`, `sloos_tightening`, `default_rate_fcst`, `pmi`, sector drivers). It holds no firm term and no term-spread term. Section 5.4 builds five macro paths from GDP and CPI quantiles, each with a Treasury curve. Estimates E1 and E10 read the case weights.

**What this paper changes.**
1. **Pooled firm-and-macro logit is the right family.** The paper supports one pooled model with firm and macro terms and a calendar-time macro covariate. It finds almost no duration dependence (footnote 12), so a logit in place of a hazard is acceptable for us. This backs the functional form of 5.2.
2. **Add a firm term.** TL/TA (2.829) and payment remarks (2.638) carry most of the cross-section (Table 2). Our analogue of TL/TA is net leverage from `annual_ebitda.parquet` (`debt`, `oibdp`). Our analogue of remarks is a watchlist, a covenant breach flag, or a negative outlook (estimate E11). Without a firm term, 5.2 gives every issuer in a sector the same p (see also `duffie-saita-wang-2007-multi-period-default.md`).
3. **Add the yield curve slope.** The 10Y − 3M slope is significant at −0.232 per point (Table 2). It is the one macro term that each 5.4 path already carries: every path has a Treasury curve and a policy rate. So the slope is the cleanest route from a macro path to a case weight. Store `ust_10y_3m` in m_t. Read its value under each path from the path's curve.
4. **Growth level, not growth change.** The output gap (a level) and the change in household expectations both enter. `pmi` is a level near 50 at trend, which is closer to the gap. Keep `pmi` as a level. Test a change in `pmi` as a second term.
5. **Macro-only explains the trend, not the spikes.** R² 41% for output gap only against 85% for the full model (pp. 19–20). Do not judge 5.2 on its fit to the aggregate event rate alone. Judge the issuer-level model.
6. **Publication lags are part of the specification.** The paper lags macro terms by their release delay and accounting by 4 quarters (pp. 10, 14). Our registry sets `available_at` for each series. The no-look-ahead test already covers this. Use `available_at`, not the reference period, when building m_t.

**Falsifiable tests (not run).**
1. **Slope.** Add `ust_10y_3m` to the 5.2 logistic on `annual_ebitda.parquet` (event: EBITDA_{t+1y} < 0.8 EBITDA_t). Keep it if its coefficient is negative with |z| > 2 and the walk-forward log loss falls in at least 3 of 2008, 2015, 2020, and 2022.
2. **Macro-only against full.** Regress the yearly realised event share on the mean predicted p of (a) macro + sector and (b) macro + sector + net leverage. Expect R² of (b) above (a). Reject the claim "macro carries the time series" if (a) reaches at least 80% of the R² of (b).
3. **Conditional independence.** Under the full model, compute the PIT of the yearly realised event count. If it fails uniformity, the paper's zero-correlation assumption fails for our data. Then the frailty card applies (`duffie-eckner-horel-saita-2009-frailty.md`).

## Limits
- We read the 2002 working paper, not the 2007 JBF article.
- One Swedish bank's loan book, 1994–2000. The authors say the window may not cover a full business cycle (pp. 18–19). The output gap falls nearly steadily over it, so its coefficient may also carry a time trend.
- Mostly very small private firms (65% with 5 or fewer employees). Not bond issuers, not high yield.
- Default is a bank rating event, not a bond default and not an EBITDA decline.
- Mean imputation of missing ratios understates standard errors (footnote 8, p. 10).
- The VaR assumes zero conditional correlation without a test.
- The output gap is an estimate from a model and is revised. The paper does not say whether it uses real-time vintages.

## Section touched
`docs/methodology.md` Section 5.2 (covariates: firm leverage term, yield curve slope, levels against changes, publication lags) and Section 5.4 (route each macro path into 5.2 through the path's Treasury curve). Estimates E1, E10, and E11 in `hy/groups.py`. No decision page yet: the sprint that fits 5.2 should record the covariate set.
