# Huang, Nozawa, and Shi (2025), "The Global Credit Spread Puzzle"

The Journal of Finance 80(1), pp. 101–162, DOI 10.1111/jofi.13409. Peer-reviewed journal article, open access under a CC BY-NC-ND license. **Added by citation chasing** because it reports first-hand how three default boundary methods change the structural residual. The review screen dropped it by the cap at grade 2 (`/home/ak/Gitrepos/sr-tracks/clocks-residual-timing/screening/dropped_by_cap.md`). We read a markdown conversion of the published file in the wiki staging folder (`The Journal of Finance - 2024 - HUANG - The Global Credit Spread Puzzle.md`). The conversion omits displayed equations and some subscripts, so we describe the formulas in words. Page numbers below are printed journal pages. The Internet Appendix was not opened, and the paper places its pricing error regressions there (p. 134). The focus is IG bonds. HY rows appear in Table IV.

## Claim
Two pure default-risk structural models underpredict IG spreads in eight developed markets. A model with endogenous liquidity from search frictions mitigates this and improves the fit of individual IG spreads (p. 101).

## Method
1. **Baseline model (pp. 110, 112).** A Black-Cox variant with continuous coupons, a flat default boundary, and fixed maturity. Default occurs when firm value first falls to the boundary.
2. **Three boundary estimates (pp. 119–120).** Each matches model default probability to historical default rates. They differ in the proxy for the market value of assets.
   - FS: book debt plus market equity, the method of Feldhütter and Schaefer.
   - BGY: estimated market value of debt plus market equity, the method of Bai, Goldstein, and Yang.
   - HNS: asset value and asset volatility solved from equity value and equity volatility.
   
   Under all three, `d` is the same for all firms over time in each country (p. 120).
3. **Pricing error (p. 121).** Model spread minus actual spread, by rating and country. Errors cluster by bond issue (p. 122). A negative value means that the model underpredicts.
4. **Search model, HM (pp. 138–140).** A reduced form of He and Milbradt (2014). It holds the same physical default probability as the baseline. Holding cost and dealer contact parameters come from a fit to proportional bid-ask spreads, not to credit spreads (pp. 105, 140).

Formula in words (pp. 147–148): the liquidity component is the HM yield minus the baseline yield. Intuition: both yields share one default probability, so their gap can only come from search and bargaining frictions.

5. **Drivers of error (pp. 134–136).** Panel regressions of errors on inputs, macro proxies, equity factors, and illiquidity proxies.

## Data
- ICE BofA Merrill Lynch month-end bid quotes, Global Corporate and High Yield indices (pp. 108, 139).
- Non-US countries: January 1997 to December 2017, with later starts for Italy and Australia (p. 108). United States: 1987 to 2015 (Table IV note, p. 122).
- Senior, unsecured, noncallable bonds of nonfinancial issuers (p. 109). No transaction data outside the US (p. 136, note 17).
- Moody's default rates, 1970 to 2017 (pp. 102, 118). The US sample uses seven rating categories, and non-US samples use four (p. 121, note 14).

## Result
**US pricing errors, full sample, bp (Table IV Panel A, p. 123).** t in parentheses.

| Model | AA+ | A | BBB | HY |
| --- | --- | --- | --- | --- |
| BC with FS boundary | −18.1 (−6.2) | −16.9 (−14.0) | −32.6 (−14.8) | −5.5 (−1.0) |
| BC with BGY boundary | −21.5 (−10.3) | −32.8 (−28.9) | −67.3 (−34.1) | −90.3 (−15.9) |
| BC with HNS boundary | −15.5 (−7.7) | −18.5 (−19.3) | −40.9 (−23.2) | −63.0 (−13.7) |
| CDG, stationary leverage | −17.6 (−13.0) | 24.8 (4.0) | −56.7 (−13.3) | 99.2 (5.9) |
| HM, search model | 10.1 (2.6) | 16.3 (6.2) | 25.3 (8.5) | 73.1 (12.5) |

So on US HY, the boundary choice alone moves the mean error by 84.8 bp, from no significant error to −90.3 bp. The search model turns the error positive at all US ratings.

**Boundary values for the US (p. 121).** FS report 0.89, and BGY report 0.82. Other estimates include 0.75 with CDS data and 0.66 from defaulted firms.

**Boundary above one (p. 120).** Canada, Italy, and the UK have estimates of `d` above one. The authors say that their leverage is only a proxy for true leverage: "there may be debt-like obligations that are missing in the book value of debt". They add that firms with higher operating leverage are more likely to default at the same financial leverage.

**Drivers of error (p. 136).** Firm leverage, implied volatility, and market liquidity hold significance most consistently. The coefficient on leverage is positive in all ten specifications. Illiquidity proxies tend to have negative signs. Country-level errors load more on illiquidity proxies than on market conditions (p. 136).

**Liquidity component (p. 148).** It has a significantly negative coefficient on baseline errors, and it captures 25% of their variation. It absorbs the role of observed bid-ask spreads.

**IG bond-level fit (p. 155).** R² runs from 0.19 to 0.35 for the baseline model, and from 0.34 to 0.79 for the search model.

**Bins (pp. 103, 105).** 53 of 72 IG, country, and boundary bins have a significantly negative error. Under the search model, 6 of 24 IG and country bins do, down from 17.

## Limits
- The headline tests cover IG. HY appears in the rows of Table IV and in the percentile table. The search model overpredicts US HY by 73.1 bp (p. 123).
- Same method, different number: Feldhütter and Schaefer (2018, Table 9, p. 30) report −162 bp in speculative grade, and this paper reports −5.5 bp in US HY with the FS boundary (p. 123). The two differ in model variant, in sample years, in the issuer set, and in the rating pool. We did not isolate the cause.
- Bid quotes, not trades. Search parameters are set per country, not per rating or sector. The authors name this as a limit (p. 158).
- Noncallable senior bonds only (p. 109), so much of US HY sits outside the sample.
- `d` is one number per country and over time (p. 120). Its use as a test of debt-like obligations is our step, not a test in the paper.
- The dispute with FS: the authors say that BGY find an underestimate of book debt over market assets for CCC to C firms, which overestimates the boundary and the model spread (p. 107). They say that Feldhütter and Schaefer (2023) respond with a sample that leaves out major rating category C (p. 107). We did not open BGY (2020), so we hold their side at second hand. We opened the reply: `feldhutter-schaefer-2023-debt-dynamics-credit-risk.md`.
- The authors use the FS boundary because a higher `d` biases against a puzzle (pp. 104, 120). So their headline is conservative for IG, but it does not settle which boundary is right.
- The regressions of errors on drivers sit in the Internet Appendix (p. 134), which we did not open. We report only the summary in the main text.

## Section touched
`docs/methodology.md` Section 7.1 (PD calibration), Section 7.2 (`f_t`, liquidity block), Section 7.3 (residual), Section 4.7 (cost clock). `hy/clocks.py`. Related card: `feldhutter-schaefer-2018-credit-spread-puzzle.md`.

## Use for the two clocks
**What the source says.** The structural residual on US HY is not one number. It runs from −5.5 bp to −90.3 bp by boundary method alone (p. 123). Leverage and liquidity load on the residual (p. 136). Book debt may miss debt-like obligations, and operating leverage may be one of them (p. 120).

**What our data says.** No structural residual exists on our data. Section 7.1 calibrates to one number: 3.60% one-year speculative grade. `hy/clocks.py` already holds the cost clock: rent, purchase commitments, interest, and principal. Section 4.7 reports no test of the clock inside a structural model.

**What we decide (our proposal, not the source's claim).**
1. **Report a band, not one structural residual.** Compute the residual under FS, BGY, and HNS boundaries, and report all three. Our rule (v0): do not read a bond as mispriced when the three residuals disagree in sign.
2. **The cost clock as debt-like obligations (changes the Section 4.7 test).** This gives the clock-adjusted structural test of the FS card a source-based reason. Two falsifiable predictions, under the reading that the clock holds the missing obligations:
   - The present value of rent and purchase commitments, when added to book debt, lowers the fitted `d` toward or below one. The source reports `d` above one as evidence of missing debt (p. 120).
   - The positive coefficient of pricing error on leverage (p. 136) shrinks.
   
   If neither happens, then the cost clock is not the missing debt.
3. **A liquidity estimate that uses no spread.** The search model fits to bid-ask spreads, so it shares no price with the outcome through the spread. This suits a residual test. But it overpredicts US HY by 73.1 bp (p. 123). So use it as a check on the `lambda` control of the Dick-Nielsen card, not as a fair value.
4. **Keep the sign convention explicit.** This paper reports model minus actual. Our S1 reads actual minus fair. Check the sign whenever a number from this table enters a note.
