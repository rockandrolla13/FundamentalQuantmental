# Dickerson, Mueller, and Robotti (2023), "Priced Risk in Corporate Bonds"

Journal of Financial Economics 150(2), article 103707, November 2023, DOI 10.1016/j.jfineco.2023.103707. Peer-reviewed journal article. We read arXiv 2604.05699v1, posted April 7, 2026, with the paper dated August 2023 (41 PDF pages). The volume comes from Crossref. Page numbers below are PDF pages. PDF page = printed page + 1. The Internet Appendix was not opened.

## Claim
Earlier bond factors, with traded liquidity as the only marginal exception, have no incremental explanatory power over the corporate bond market factor (p. 1). So the bond CAPM is not dominated by traded-factor or nontraded-factor models in pairwise and multiple model comparison tests (p. 1).

## Method
1. **Replication of the BBW factors (pp. 7–9).** Rebuild DRF, CRF and LRF. Do not winsorize excess returns in factor construction (p. 8). Compare with the factors the original authors posted.
2. **Spanning (p. 13).** One-factor alpha on MKTB for each factor, with a GRS-type test.
3. **Sharpe ratio comparison (pp. 13–14).** Bias-adjusted squared Sharpe ratios, with tests for nested and non-nested models.

```latex
\widehat{Sh}^2_{adj} = \frac{T - K - 2}{T}\,\widehat{Sh}^2 - \frac{K}{T}
```

Intuition: with `K` factors in `T` months, the sample maximum Sharpe ratio is too high, so shrink it before any comparison.

4. **Two-pass cross-section (pp. 14–16).** OLS and GLS cross-section R². Misspecification-robust t-statistics. The authors use GLS, because the OLS R² can be large even when the pricing relation fails (pp. 3, 16).
5. **Price of covariance risk (p. 17, note 14).** When factors correlate, the incremental question needs the price of covariance risk, not the price of multivariate beta risk.
6. **Nontraded factors (pp. 18–22).** Mimicking portfolios, rank tests for identification, and GLS inference that is robust to weak factors.
7. **Bond-level test (pp. 23–24).** Fama-MacBeth with post-ranking betas and covariances from five portfolios per factor, with rolling 36-month pre-ranking estimates.
8. **Test assets (p. 12).** 32 portfolios: rating, maturity, credit spread and 12 industries.

## Data
- Enhanced TRACE with FISD, July 2002 to December 2016 (pp. 6–7). 31,348 bonds, 3,792 firms, 861,524 bond-months, mean 4,951 bonds a month (p. 7). Factor sample August 2004 to December 2016, 149 months (p. 32).
- Excludes Rule 144A bonds, floating rates and bonds with under one year to maturity (p. 6).
- Robustness with WRDS and ICE in the Internet Appendix (p. 24), and a sample extended back to January 1986 (p. 24).

## Result
**Errors in the posted BBW factors (p. 9).** A one-month lead error in DRF and CRF from August 2004 to December 2014. A one-month lag error in LRF from January 2015 to December 2016. Correlation of original with replicated: DRF 0.264 and CRF 0.445, rising to 0.931 and 0.948 once the lead and lag errors are fixed (Table 1, p. 32).

**Spanning by MKTB (Table 2, p. 33).** Alpha and p-value: DRF 0.020 [0.932], CRF 0.123 [0.681], LRF 0.135 [0.130].

**Squared Sharpe ratios (Table 2, p. 33).** MKTB 0.054 [0.002]. BBW four factors 0.053 [0.015]. CAPMB minus BBW: 0.001 [0.216]. With the original factors, BBW minus CAPMB was 0.077 [0.000] (p. 14, note 11).

**Cross-section (Table 3, p. 34).** OLS R²: CAPMB 0.888, BBW 0.927. GLS R²: CAPMB 0.097, BBW 0.185, and all models are rejected. The GLS difference is −0.088 [0.265]. LRF covariance price under GLS: 32.68, robust t 2.85.

**Bond level (pp. 23–24).** MKTB beta premium 0.36% a month (t 1.97). LRF 0.15% (t 2.03). The other traded factors have no incremental pricing.

**Nontraded (pp. 19–22).** Mimicking portfolios are spanned by MKTB. Five of six nontraded models fail the rank test for identification (p. 22).

**Repeat with ICE and WRDS (p. 24).** Evidence for added factors is even weaker, with liquidity marginally better.

## Limits
- Short sample: T = 149 months. The authors limit test assets for that reason (p. 12, note 6).
- A failure to reject does not prove the bond CAPM right. All models are rejected by GLS (p. 16).
- The factors tested are mainly observable and unconditional. Latent conditional models such as IPCA are not in the test set. We searched the text and found no mention of Kelly, Palhares and Pruitt.
- The paper reports no cost test, and it names this as future work (p. 25).
- The paper does not say why the original factors had errors. The repo flag on the Crossref retraction of BBW (2019) rests on Crossref and on the reference list of Dickerson, Robotti, and Rossetti (2026, p. 43), which prints "RETRACTED" beside it. No retraction notice was opened here.

## Section touched
`docs/methodology.md` Section 8 (benchmark for each signal), Section 11 (factor tests). Specs: `docs/factors/F16-downside-risk.md`, `docs/factors/F17-return-skewness.md`, `docs/factors/F13-realized-illiquidity.md`. The review track flag: `/home/ak/Gitrepos/sr-tracks/clocks-residual-timing/screening/flags.md`.

## Use for the two clocks
**What the source says.** The bond market factor is the first hurdle. Published factor files may have date errors. GLS and misspecification-robust tests give a different answer from OLS.

**What our data says.** `hy/backtest.py` hedges with a beta to the HY benchmark, and IC tests use the spread rank. No factor alpha against a value-weighted bond market factor exists on our data. F16 and F17 cite BBW definitions at second hand.

**What we decide (our proposal, not the source's claim).**
1. **First hurdle for a traded clock factor.** Regress the clock long-short on MKTB and report the alpha with GRS. Then compare squared Sharpe ratios with the bias adjustment above. A factor spanned by MKTB is not an idiosyncratic explanation. It is market exposure.
2. **Build the market factor ourselves, and check its dates.** Do not use a posted factor file as a control until a lead and lag test passes: correlate it with our own series at leads and lags of one month.
3. **Report GLS with OLS.** For any clock test on portfolios, report GLS cross-section R² and the robust t. Rely on the price of covariance risk when the clock factor correlates with other factors.
4. **Keep LRF-style liquidity as the one control factor to test.** It has the only marginal survival here (p. 24). The bond-level measure is the gamma in `bao-pan-wang-2011-bond-illiquidity-gamma.md`.
5. **Use for the F16 and F17 citation decision.** This paper gives evidence of data errors in the published factors, so the user can decide whether to keep the BBW citation. This card changes neither spec.
