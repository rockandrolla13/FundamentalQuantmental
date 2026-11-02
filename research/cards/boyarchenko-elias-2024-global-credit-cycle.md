# Boyarchenko and Elias (2024, revised 2026), "The Global Credit Cycle"

Federal Reserve Bank of New York Staff Report 1094, March 2024, revised May 2026, DOI 10.59576/sr.1094. Working paper. Corporate bonds, global, with US columns. We read the staff report (84 pages). Page numbers are PDF pages. PDF page = printed page + 2.

## Claim
One factor, a nonlinear function of the excess bond premium (EBP) and the VIX, predicts bond returns three months ahead in the time series and in the cross-section (pp. 2–3). Exposure rises with bond risk (p. 4). The authors read it as a common price of credit risk (p. 2).

## Method
**Return (pp. 10–11).** Credit part of the excess return: bond return less the return on a duration-matched sovereign, in USD.

**Factor (pp. 14–15, 60–62).** Sieve reduced-rank regression on three-month returns of four advanced-economy rating portfolios.

```latex
rx_{i,t+h} = b_{i,h}\big(\gamma_h' X_{m,t}\big) + u_{i,t+h}, \qquad \varphi(cs_t, VIX_t) \approx \gamma_h' X_{m,t} \quad (\text{A.1, p. 60})
```

Intuition: let the data pick one curved function of spreads and volatility that best forecasts all rating portfolios. X is a spline basis. The out-of-sample MSE picks rank and knots, and a new factor must cut MSE by at least 5% (p. 62). The credit input is the log US EBP: "We use the (log) U. S. EBP as our measure of credit spreads" (p. 61). The authors prefer EBP because it has no level shift (p. 61, note 25). The winner is one factor, linear in log EBP and quadratic in VIX, with interactions (p. 15, p. 62). The search covers 2,058 specifications by out-of-sample MSE, with the first forecast in January 2009 (pp. 61-62). The high yield loading is normalised to 1 (p. 60).

**Bond-level test (p. 19).**

```latex
rx_{i,t+h} = \beta\,\lambda_t + \beta_r\,\lambda_t \times 1_{r,i,t} + \epsilon_{i,t+h}, \qquad \lambda_t = \lambda_0 + \lambda_1\,\varphi(cs_t, VIX_t)
```

Intuition: bonds of each rating load on one common price of risk, each with its own size. R² splits into time-series, cross-sectional and market-timing parts (pp. 19–20).

**Out of sample (pp. 22–23, 43).** Factor vintages by expanding window, first vintage through December 2008, one month added at a time. Each vintage uses "the same bivariate basis" (p. 22). So the form comes from a choice on the same window, and the test is pseudo out of sample (p. 61). The out-of-sample R-squared is "the covariance between the predicted returns" and realized returns, read as "the fraction of return variance explained by the predicted returns" (pp. 23, 43). It is a bond-level measure with rating terms.

**Episodes (pp. 26, 30).** Tight: the factor is in its top tercile and reaches the top quintile at least once. Local projections of spreads and EDF over h from −6 to +6.

## Data
ICE Global Bond Indices 1998 to 2024 and Lehman-Warga from 1973, with returns from January 1986 (pp. 8–10). 2.3 million bond-months, 40,000 bonds, 50 countries (p. 10). Senior unsecured fixed-coupon bonds of non-financial parents, spread between 50 bp and 2,000 bp (p. 9).

## Result
**Table 1, p. 43.** High yield loading 0.68 (se 0.01). Differences: BBB −0.32, A −0.48, AAA and AA −0.58. One sd of the factor adds 11.7 points to the annualised three-month-ahead expected return on high yield, 6 on BBB, 3.4 on A, 1.5 on AAA and AA (p. 20). US column: R² 9.2%, time-series 7.1, cross-section 0.7, market-timing 1.4, out-of-sample 5.8. N 1,449,575.

**What the factor adds (Table 3, p. 45).** Total R²: factor 9.4, EBP 4.7, VIX 4.2, nonlinear EBP 6.9, nonlinear VIX 8.6, additive 9.0. The additive form comes close in the full sample. Out-of-sample RMSE: 117.38 with interactions, 117.80 additive, 119.82 EBP alone (Table A.2, p. 69).

**Interactions matter in calm (Table 4, p. 46).** Loose periods: R² 1.9 for the factor, 0.8 for nonlinear VIX, 0.7 for additive. Correlation of the factor with the VIX factor: 0.86 in tight periods and −0.42 in loose periods (p. 27). So the factor ignores VIX spikes that credit does not confirm.

**Subperiods (Table 6, p. 48, in-sample, global).** R²: 5.6 (1998–2006), 15.7 (2007–2009), 3.8 (2010–2019), 15.8 (2020), 3.5 (2021–2024). So most of the in-sample fit sits in two stress windows.

**Event time (Table 7b, p. 49).** High yield spread change around the start of a tight episode: −6.2 bp and −20.3 bp in the two windows before, +96.6 bp at month 0, +75.3 bp at month 3, +48.0 bp at month 6. BBB is about 41 bp at month 0 (96.56 less 55.34). One-year EDF of high yield firms rises about 40% at onset (p. 31).

**Flows (pp. 34–35).** High yield funds see outflows when the factor rises.

## Limits
- No cost, no turnover, no tradable rule. R² is the only measure.
- Long sample with look-ahead risk in EBP. The vintage test holds the basis fixed (p. 22), and that basis was chosen on the same out-of-sample window (pp. 61-62). So the 5.8% is not comparable with a Campbell-Thompson R-squared on a HY return.
- The tight-episode rule asks whether the factor "reaches the top quintile at least once during the episode" (pp. 26, 49). A vintage cannot know that at the first month.
- Full-sample factor results dominate the paper (p. 23).
- A high factor means a high expected return, so the signal is contrarian. The spread jump of month 0 comes before a signal formed at the end of month 0. Spreads then narrow from +96.6 bp to +48.0 bp by month 6 (p. 49). A book that buys then still needs liquidity in the stress.
- Intro text gives 13.3% overall with 1.5% cross-section (p. 4). Table 1 shows 13.3 with 0.6 cross-section for emerging markets, and 1.5 is the full-sample market-timing number (p. 43).
- Authors are Federal Reserve staff. The paper is preliminary (p. 2).

## Section touched
`docs/methodology.md` Section 3.6 (`cycle_phase`), Section 5.2 (macro conditioning), Section 8 (composite, candidate S7 replacement), Section 9.2 (spread channel), and `docs/decisions/2026-10-26-conviction-book.md` layer 1.

## Use for the two clocks
This section is our proposal, not the source's claim.

**What the source says.** Spreads and volatility together forecast credit returns, and more so in high yield. Refinancing conditions tighten at the same time (see `boyarchenko-elias-2024-debt-structure-cycle.md`).

**What our data says.** S7, the macro sector tilt, failed. Macro adds nothing to the sector spread (EWC t 1.44) (`docs/decisions/2026-10-26-conviction-book.md`). `F30` compares the HY spread with a VIX line and has no backtest. No phase result exists.

**What we decide.**
1. Build `gcc_us`: fit the source's form on US rating portfolios, with vintages, and with only data available at the decision date. Do not use the published series. EBP needs its own vintage.
2. Use it as the target inside the conviction-book band in place of a raw phase rule. It is not a name selector.
3. Report it as an arm of the market state in Method 4, with the label "our extension". The opened price sources use a liquidity state, not this factor. The HY spread version is also our extension, with no source test. The log EBP version is the source form.
4. Treat the target as contrarian, and step toward it over several rebalances, as the band rule already says. Kargar et al. estimates, as converted in `dickerson-nozawa-robotti-2025-factor-delays.md` (p. 28, n. 24), show lower trade intensity in the COVID episode. Kargar et al. stays unopened. So a one-step move may not be realistic.

Duplication check: F30 uses one linear line in VIX. This factor uses EBP, curvature and an interaction, and it targets returns.

**Test.** Arm of the conviction-book test: band target from `gcc_us` against the static band (T2). Pass: higher net excess return in at least three of four windows, one-way turnover not above the static arm by more than 10 points a year, and out-of-sample R² above zero by the Campbell-Thompson form. Our choice, v0.
