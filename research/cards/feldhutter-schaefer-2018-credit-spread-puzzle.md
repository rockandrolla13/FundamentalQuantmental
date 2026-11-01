# Feldhütter and Schaefer (2018), "The Myth of the Credit Spread Puzzle"

The Review of Financial Studies 31(8), pp. 2897–2942, DOI 10.1093/rfs/hhy032. Peer-reviewed journal article, open access. We read the journal version at https://lbsresearch.london.edu/id/eprint/953/7/Myth_of_the_Credit_Spread_Puzzle_RevFinStud_v31_iss8_VoR.pdf (47 PDF pages). Page numbers below are PDF pages. PDF page = printed page − 2895. An Internet Appendix was not opened.

## Claim
A Black-Cox model calibrated to a wide cross-section of default rates matches the level of investment grade spreads (p. 2). The model spread is too low for speculative grade, and bond illiquidity contributes to that gap (p. 2). The earlier "puzzle" depends on the sample period of one historical default rate (pp. 3, 7).

## Method
1. **Spread from a default probability (p. 7, eq. 1).** `R` is recovery and `pi^Q` is the risk-neutral default probability.

```latex
s = y - r = -\frac{1}{T} \log\big[1 - (1 - R)\, \pi^{Q}(T)\big]
```

Intuition: the spread is the annual yield give-up that exactly pays for the expected loss under risk-neutral odds.

2. **Common default boundary (p. 24, eq. 7).** Firms default when asset value falls to `d` times face value. The authors fit one `d` to Moody's default rates for ratings AAA to C and horizons of 1 to 20 years.

```latex
\min_{d} \sum_{a=AAA}^{C} \sum_{T=1}^{20} \frac{1}{T} \big| \bar\pi^{P}_{aT}(d) - \hat\pi^{P}_{aT} \big|
```

Intuition: high yield defaults locate the boundary, and that information then pins down rare investment grade defaults.

3. **Sampling error test (pp. 9–12).** Simulate correlated firm values with pairwise correlation 20.02%, 22 cohorts and 25,000 runs (pp. 10–12).
4. **Firm inputs (pp. 20–23, 42).** Leverage is book debt over book debt plus equity value. Payout is interest, dividends and net repurchases over firm value. Asset volatility is unlevered equity volatility with step multipliers from 1 to 1.80 by leverage (p. 22). Recovery is 37.8% (p. 22). The Sharpe ratio is 0.22 (p. 23).
5. **Residual test (pp. 34–36).**
   - Regress actual spreads on model spreads for single bonds.
   - Correlate pricing errors with model inputs.
   - Sort pricing errors by bond age, then by investment and speculative grade.
6. **Inference (pp. 28–29).** Confidence bands come from the simulated distribution of `d`, because the model spread is monotone in `d`.

## Data
- 256,698 yield spreads to the swap rate, April 1987 to July 2012 (pp. 4, 20). Lehman Brothers monthly actual quotes to December 1996. Merrill Lynch daily quotes from January 1997 (p. 20).
- Senior unsecured, fixed rate or zero coupon, industrial bonds, maturity under 20 years. The sample drops callable bonds, convertibles, putable bonds and bonds with covenants (p. 20). Bonds under 3 years leave the reported spreads (p. 20).
- Default rates: Moody's, 1920 to 2012 (p. 24).
- Thin high yield sample: in the 3 to 7 year bucket, a mean month has 6.94 BB bonds, 1.71 B bonds and 0.37 C bonds (Table 5, p. 21). The authors warn that B and C results are noisy (p. 20).

## Result
**Precision (Table 2, p. 16).** 10-year BBB default probability, all ratings and maturities against one default rate: standard deviation 0.48 against 3.05, skewness −0.05 against 1.28, 95% band 3.96% to 5.88% against 1.15% to 12.78%.

**Boundary.** `d` = 0.8944 with 1920 to 2012 default rates (p. 24). `d` = 0.9302 with 1970 to 2012 (p. 37).

**Actual against model spreads, 3 to 20 years (Table 9, p. 30).** Difference is model minus actual, with the 95% band.

| Group | Actual (bp) | Model (bp) | Difference (bp) | Band |
| --- | --- | --- | --- | --- |
| Investment grade | 92 | 111 | 19 | −4 to 36 |
| Speculative grade | 544 | 382 | −162 | −239 to −104 |
| BB | 377 | 349 | −27 | −94 to 21 |
| B | 675 | 445 | −229 | −314 to −166 |
| C | 1,442 | 958 | −484 | −615 to −401 |

**Sort by actual spread (Table 10, p. 32).** Spreads of 300 to 1,000 bp: actual 499, model 507, difference 8 (band −85 to 74). Spreads above 1,000 bp: actual 1,744, model 909, difference −835 (band −997 to −718).

**Default rates (Table 8, p. 27).** The model overstates short-horizon high yield default. One-year BB: model 2.23%, actual 1.35%. One-year B: model 8.43%, actual 3.80%. Five-year B: model 30.78%, actual 22.06%.

**Time series (Table 11, p. 34).**
- Levels: investment grade slope 0.88, R² 0.87. Speculative grade slope 0.85, R² 0.16.
- Monthly changes: investment grade slope 0.52, R² 0.35. Speculative grade slope 0.00, R² 0.00.

The authors link the unexplained changes to supply and demand shocks, with reference to Collin-Dufresne, Goldstein and Martin (2001) (p. 35).

**Single bonds (Table 12, p. 36).** R² is 0.44 for investment grade and 0.13 for speculative grade. The pricing error correlates −0.45 with leverage in investment grade and −0.02 in speculative grade.

**Bond age (Table 13, p. 36).** Mean model minus actual spread, age quintiles 1 to 5.
- Speculative grade: 88, 56, −114, −356, −382 bp. The gap between the youngest and oldest quintiles is 470 bp.
- Investment grade: 18, 8, 19, −5, 30 bp, with no clear relation.

**Crisis (p. 37).** For 2007 Q2 to 2009 Q2, actual minus model is 262 bp in speculative grade.

**Boundary drift (pp. 39–40).** The average face value of debt grows before default, with a log growth of 27.76% over six years in 128 cases. The authors call the misspecification from this drift "mild" (p. 40).

## Limits
- Bond age is a proxy. It may also carry credit migration and survivor effects. The paper does not test this.
- The paper uses non-callable bonds. High yield bonds are often callable, so the sample holds few of them (p. 20).
- Quotes are bid quotes (p. 20). A TRACE check for 2002 to 2012 sits in the Internet Appendix (p. 20, note 10), which was not opened.
- Constant Sharpe ratio, constant recovery, one boundary, no jump risk (p. 35).
- The model sets `d` per firm class only through leverage. Endogenous boundaries are possible but not fitted (p. 14).
- Disagreement: Huang, Nozawa, and Shi (2025, p. 107) describe the dispute with Bai, Goldstein, and Yang (2020). They report that the US HY error moves from −5.5 bp to −90.3 bp by boundary method (p. 123). See `huang-nozawa-shi-2025-global-credit-spread-puzzle.md`. The authors' later paper drops rating C from the boundary fit because of that dispute, and it reports a speculative grade mean of 392 bp against an actual 413 bp (`feldhutter-schaefer-2023-debt-dynamics-credit-risk.md`, Table 6). We did not open Bai, Goldstein, and Yang (2020), so we hold their side at second hand.

## Section touched
`docs/methodology.md` Section 7.1 (structural anchor and calibration of PD), Section 7.2 (liquidity block of `x`), Section 7.3 (residual). Framework F5 and F6 are not changed. Cross-reference: `bharath-shumway-2008-merton-dd.md`, `giesecke-longstaff-schaefer-strebulaev-2011-150-year-default.md`.

## Use for the two clocks
**What the source says.** In speculative grade, a calibrated structural model explains 13% of single-bond spreads (p. 36). The mean residual is −162 bp (p. 30), and bond age sorts that residual by 470 bp (p. 36). A one-horizon default rate is a noisy anchor (p. 16).

**What our data says.** No structural residual exists on our data. Section 7.2 uses a peer median until `f_t` is fitted. Section 4.7 reports the clock coefficients on log spread, not on a residual. E4 is suspended until `kappa_t` is fitted (`hy/groups.py`).

**What we decide (our proposal, not the source's claim).**
1. **Clock-adjusted structural residual (changes the Section 4.7 test).** The Black-Cox inputs include only debt in face value `F`. Compute the model spread twice: with `F` as debt, and with `F` as debt plus the present value of rent and purchase commitments from `hy/clocks.py`. Compare the two pricing error distributions.
   - If the residual falls, the market already prices the fixed obligations and the clock adds no mispricing.
   - If the residual stays, the market prices something else, or it ignores those obligations.
2. **Clock sort of the residual, with an age control.** Use Table 13's design. Sort the pricing error by `renewal_recontract_share` quintile within bond age quintile. A clock effect that survives inside one age quintile is not a bond age effect. An effect that vanishes is a liquidity proxy.
3. **Boundary test.** Let `d = d0 + d1 * c`, with `c` a clock feature, and fit equation (7) on the issuers with clock data. The two clocks predict `d1` above 0: a firm with charges and no contracts defaults at a higher asset value. Few defaults exist since 2018, so report the band. Change no weight on this test alone.
4. **Change to Section 7.1 calibration.** Section 7.1 matches one number: 3.60% at one year for speculative grade. Fit the PD intercept to a grid of ratings and horizons, and report a simulated band. Our v0 uses the source's grid: seven ratings and horizons of 1 to 20 years. The authors' later paper drops rating C unless market values of debt are in hand, so report the grid with and without C.
5. **Read S1 with care.** A wide residual in the B bucket is the normal state in this model, by −229 bp on average (p. 30). So S1 needs an age and liquidity control before a wide residual counts as cheap.
