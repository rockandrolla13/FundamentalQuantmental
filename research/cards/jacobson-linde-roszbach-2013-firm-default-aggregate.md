# Jacobson, Lindé, and Roszbach (2013), "Firm Default and Aggregate Fluctuations"

Journal of the European Economic Association 11(4), pp. 945–972. Peer-reviewed journal article. We read the open final working paper version dated 5 July 2011: https://www.riksbank.se/globalassets/media/forskning/medarbetare/2011/jacobsonlinderoszbach_2011_final.pdf (also Federal Reserve IFDP 1029, August 2011). Page numbers below are the printed page numbers of that file. Tables 1 to 4 sit at the end of the file without page numbers. The journal version may differ in tables and numbers. We did not read the online Appendices A and B.

## Claim
In a firm-level logit of default, firm variables rank firms and macro variables set the level (pp. 3, 15, 23–24). Adding four macro series barely moves the firm-level fit (pseudo-R² +1 to 2 points) but doubles the fit to the aggregate default rate (Tables 1 and 2). Out of sample, 2000Q1–2009Q2, the firm-and-macro model forecasts the aggregate default rate 3.6 times more accurately than a firm-only model (Table 3). It beats a random walk, a 4-quarter moving average, and a macro-only time-series regression. Macro effects are larger in cyclical sectors (p. 13).

## Method
**Multi-period logit (pp. 9–10).** Shumway (2001) form, quarterly, all firms pooled:

```latex
y^{*}_{i,t} = \beta' x_{i,t} + \gamma' z_t + \varepsilon_{i,t}, \qquad y_{i,t} = \mathbb{1}\{ y^{*}_{i,t} \ge 0 \}
```

Intuition: firm i defaults in quarter t when its firm state x and the macro state z push a latent score past zero. ε is logistic.

The authors assume errors independent across firms and over time, given x and z (p. 10). They cite Das, Duffie, Kapadia, and Saita (2007) rejecting this on US data, and Lando and Nielsen (2010) failing to reject it with a wider covariate set.

**Covariates (pp. 6–8).**
- Firm: EBITDA/TA, TL/TA, liquid assets over TL, inventories over sales, log TL over sales, interest payments over (interest + EBITDA), a dividend dummy (PAYDIV), a dummy for no financial statement in the last 18 months (TTLFS), and two payment-remark dummies (PAYREMARK, TAXARREARS).
- Macro: HP-filtered output gap (λ = 1,600), GDP deflator inflation (4-quarter change), the Riksbank repo rate (nominal), HP-detrended real exchange rate (p. 8).
- An industry intercept and a third-quarter dummy (Table 2 notes).
- Accounting data lag 4 quarters (p. 12).

**Industry models.** One model per one-digit industry (10 industries) and one economy-wide model (p. 9).

**Fit measures (p. 15).** McFadden pseudo-R² for the firm-level fit. "Industry R²": sum the fitted PDs per quarter, then compute R² against the 40 quarterly default rates.

**Out-of-sample test (pp. 18–23).** Fit on 1990Q1–1999Q4. Forecast one step ahead, 2000Q1–2009Q2, with macro lagged one quarter so that all models share one information set (p. 19). Compare RMSE by Diebold-Mariano. Decile capture of defaulters. Calibration plot of predicted against actual default rate by percentile (Figure 3).

## Data
- All Swedish aktiebolag (limited companies), 1990Q1–2009Q2: 16,928,521 firm-quarters, more than 200,000 firms per quarter (pp. 2, 4). Fewer than 500 are listed (p. 22).
- In sample, 1990Q1–1999Q4: 8,106,176 observations, 105,605 defaults. Out of sample, 2000Q1–2009Q2: 8,822,345 observations, 55,945 defaults (p. 9). About 1% a quarter.
- Default: legal bankruptcy, suspended payments, debt composition, reconstruction, or distraint without assets (p. 6).
- The in-sample period includes the Swedish banking crisis of the early 1990s.
- Missing values are imputed from the firm's own past or future, then from a draw within industry and default status (footnote 2, p. 7).

## Result
- **Macro coefficients, economy-wide (Table 2).** Output gap −0.133 (0.003) per percentage point. Repo rate +0.073 (0.002) per point. GDP inflation +0.012 (0.002). Real exchange rate −0.026 (0.001). All significant.
- **Sector spread of the output gap (Table 2).** Construction −0.200, real estate −0.171, hotel and restaurant −0.141, manufacturing −0.131, retail −0.126, not classified −0.070. The repo rate is largest for real estate (0.115) and bank, finance, and insurance (0.096).
- **Firm coefficients barely move with macro (Tables 1 and 2).** Economy-wide EBITDA/TA, TL/TA, and the remark dummies change by less than 0.15 when macro enters (for example, TL/TA 0.395 to 0.383).
- **Level against rank (Tables 1 and 2, p. 15).** Economy-wide pseudo-R² 0.33 to 0.34. Economy-wide industry R² 0.42 to 0.95. Industry R² more than doubles in most industries.
- **Macro alone is mis-specified (eq. 2, pp. 17–18).** OLS of the aggregate default rate on the four macro series: R² 0.81, Durbin-Watson 1.43, so the residuals are autocorrelated. With average firm ratios added (eq. 1), R² 0.88, DW 1.98. The full firm-level model aggregates to R² 0.95.
- **Out-of-sample RMSE, economy-wide, percent (Table 3).** Firm and macro 0.0802. Firm only 0.2902. Random walk 0.1371. 4-quarter moving average 0.1033. Macro-only OLS 0.1308. The firm-only model is 3.6 times worse. Weighted industry models give 0.0716, significantly better than 0.0802 by Diebold-Mariano.
- **Industry models help at the industry level (p. 20).** Firm-and-macro beats firm-only in 8 of 9 classified industries, by factors of 1.2 to 3.6.
- **The 2008–2009 rise.** The model picks up the rise in defaults in the recent recession through the fall in the output gap from +4% to −4% (pp. 18–19). It under-predicts in 2006 and 2007 (p. 18).
- **Ranking out of sample (Table 4).** The riskiest decile holds 0.78 (economy-wide) to 0.81 (industry) of defaulters. Deciles 6 to 10 hold 0.04.
- **Calibration (Figure 3, p. 23).** With macro, predicted and actual default rates by percentile lie close to the 45-degree line. Without macro, the models overestimate default risk out of sample.
- **Rolling cross-sections fail (pp. 16–17, Figure 2).** A separate firm-only logit per quarter gives unstable firm coefficients, some with sign changes. Time-varying firm coefficients do not replace macro terms.
- **Interest rate sign.** Higher nominal rates raise default risk here (+0.073). The authors read it as tighter credit conditions (p. 11).

## What our data says (docs/methodology.md 5.2 and 5.4, hy/macro.py, hy/groups.py, data/raw/backtest, 24 October 2026)
**What the plan holds.** Section 5.2 fits P(large EBITDA decline in 4 quarters | m_t, sector) = σ(θ_0 + θ'm_t + θ_sector). The sector enters as an intercept only. No firm term enters. Section 5.2 also asks for a sector revenue sensitivity β_sector for the driver shift. Section 5.4 uses p for the case weights of every issuer under every path. Estimates E1 and E10 read those weights.

**What this paper changes.**
1. **The two jobs need both terms.** Macro sets the level and firm data set the rank (pp. 15, 23). The 5.2 plan has only the level half. Each issuer's p then differs only by sector and δ_i. A firm term (net leverage, interest cover, or a negative-outlook flag) gives the rank half. This matches the Duffie, Saita, and Wang and Carling et al. cards. Three papers agree on this point.
2. **Macro-only fits look good in sample and fail out of sample.** The macro-only regression has R² 0.81 but autocorrelated residuals (DW 1.43) and a worse RMSE out of sample (0.1308 against 0.0802). A 5.2 model with only m_t and sector may do the same. Judge it out of sample, not on in-sample R².
3. **Sector slopes, not only sector intercepts.** The output-gap slope ranges from −0.070 to −0.200 across sectors (Table 2). Industry models beat the pooled model at the industry level. Allow θ_sector × m_t for one or two macro terms in cyclical sectors. Section 5.2 already names a cyclical archetype through β_sector, so the interaction can use that split (cyclical against defensive) to save parameters.
4. **Interest rate sign differs by country and by conditioning set.** Here the nominal rate raises default risk (+0.073). In Duffie, Saita, and Wang the 3-month rate lowers it (−0.105). Our m_t has no rate term. Section 5.4 paths carry a policy rate and a Treasury curve. If a rate term enters 5.2, do not fix its sign in a monotone test before the fit. Record both priors.
5. **Calibration across the cycle needs the macro terms.** The firm-only model over-predicts out of sample (Figure 3). CLAUDE.md asks for PD calibration by cycle phase. Expect a firm-only fit to fail that test in benign years.
6. **Use the out-of-sample test design.** Fit through one date, forecast one step ahead with lagged macro, and compare RMSE of the aggregate rate against a random walk and a 4-quarter moving average. This is a direct template for the 5.2 validation.

**Falsifiable tests (not run).**
1. **Level and rank split.** On `annual_ebitda.parquet` (event: EBITDA_{t+1y} < 0.8 EBITDA_t), fit (a) firm only (net leverage, EBITDA/TA, interest cover), (b) macro + sector only, and (c) both. Report pseudo-R² and the R² of the yearly mean predicted p against the realised share. The paper's pattern predicts: (c) − (a) is small in pseudo-R² but large in aggregate R². (c) − (b) is large in pseudo-R². Reject the pattern for our data if either gap is below 0.05.
2. **Benchmarks.** Walk forward by year from 2005. Compare the RMSE of the yearly event share for (c) against a random walk and a 3-year moving average. Keep the macro terms only if (c) beats both by Diebold-Mariano at 10%.
3. **Sector slopes.** Add the interaction of `pmi` (or the output-gap analogue) with a cyclical-sector dummy. Keep it if the likelihood ratio test rejects at 5% and the cyclical slope is at least 1.3 times the defensive slope.

## Limits
- We read the 2011 working paper, not the 2013 JEEA article. We did not read the online appendices.
- Swedish limited companies, nearly all private and small. Default is a legal event, not a bond default and not an EBITDA decline.
- The out-of-sample window (2000–2009) holds no default spike as large as the in-sample banking crisis (p. 18).
- The output gap is HP-filtered on the full sample. Two-sided filters use future data. The paper does not say whether it uses a one-sided filter or real-time vintages. Our no-look-ahead rule would forbid a two-sided gap.
- The model assumes conditional independence of defaults. The paper tests it only indirectly, through out-of-sample fit.
- Payment-remark data have no US analogue. The authors say the macro results do not depend on them (p. 5, online Appendix B, not read).

## Section touched
`docs/methodology.md` Section 5.2 (add a firm term, sector-by-macro slopes for cyclical sectors, out-of-sample validation design) and Section 5.4 (case weights depend on both level and rank). Section 11 (calibration by cycle phase). Estimates E1 and E10 in `hy/groups.py`. No decision page yet: the sprint that fits 5.2 should record the specification and the validation design.
