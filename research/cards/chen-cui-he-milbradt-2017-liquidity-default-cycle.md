# Chen, Cui, He and Milbradt (2017), "Quantifying Liquidity and Default Risks of Corporate Bonds over the Business Cycle"

Review of Financial Studies, DOI 10.1093/rfs/hhx107 (per the track's screening record). Peer-reviewed. Corporate bonds and CDS. **Added by citation chasing** from Nagler (2015 version, p. 7) and He and Xiong. **We did not open the journal article.** We read NBER Working Paper 20638, October 2014, 61 pages. Page numbers are PDF pages. The journal numbers may differ.

## Claim
Liquidity and default interact through debt rollover. The interaction terms account for 25% to 40% of credit spreads and up to 55% of the spread rise over the cycle (p. 2). Additive splits of the spread into default and liquidity mislead (pp. 6, 40).

## Method
A structural model with two aggregate states, finite-maturity debt, and over-the-counter search frictions (pp. 3–5, 8). Holding costs rise as bond prices fall, through collateralised finance (pp. 4–5). The model is calibrated on four free parameters across Aaa and Aa, A, Baa and Ba, at 5-year and 10-year maturities (p. 5).

**Decomposition (p. 40).**

```latex
\widehat{cs} = \widehat{cs}^{\,pureDEF} + \widehat{cs}^{\,LIQ \to DEF} + \widehat{cs}^{\,pureLIQ} + \widehat{cs}^{\,DEF \to LIQ} \quad (18)
```

Intuition: two terms stand alone, and two terms record how bad liquidity brings default forward and how default risk worsens liquidity.

Definitions (pp. 41–42):
- Pure default: the spread in a Leland model with no liquidity friction.
- Default component: the bond priced with no friction, at the default boundary of the full model. Liquidity-driven default is the difference from pure default.
- Pure liquidity: the spread of a default-free bond with the search friction.
- Default-driven liquidity: the rest.

Bonds map to the model through observed quasi-market leverage by firm-quarter (p. 42, p. 60). Targets: default rates, credit spreads, bond-CDS spreads and bid-ask spreads (pp. 5–6).

## Data
Moments from TRACE, FISD, Markit CDS and Compustat, for firm-quarters by rating (pp. 28–29, 42). NBER states are expansion and recession. The sample excludes 2008 Q4 and 2009 Q1 from recession moments (p. 6, n. 3).

## Result
**Levels, 5-year bonds (Table 4, Panel A, p. 60).**

| Rating, state | Spread (bp) | Pure default | Liq to default | Pure liquidity | Default to liq |
| --- | --- | --- | --- | --- | --- |
| Baa, expansion | 170 | 65.5 (39%) | 20.5 (12%) | 45.9 (27%) | 37.9 (22%) |
| Baa, recession | 243 | 86.9 (36%) | 26.7 (11%) | 61.1 (25%) | 68.5 (28%) |
| Ba, expansion | 341 | 178 (52%) | 45.3 (13%) | 45.9 (13%) | 71.9 (21%) |
| Ba, recession | 459 | 215 (47%) | 57.5 (13%) | 61 (13%) | 124.7 (27%) |

**Changes, expansion to recession (Panel B, p. 60).** Ba: +118 bp, of which pure default 32%, liquidity-driven default 10%, pure liquidity 13%, default-driven liquidity 45%. Baa: +73.5 bp, with 29%, 8%, 21%, 42%.

**Against Longstaff et al. (2005) (p. 44).** Default share here: about 17% for Aaa and Aa, 33% for A, 50% for Baa, 64% for Ba. Longstaff et al.: 51%, 56%, 71%, 83%. The authors trace this mostly to a lower CDS-to-bond spread ratio in their longer sample.

**Policy (pp. 7–8).** Restoring normal-state liquidity in recession lowers the Ba spread by about 112 bp, 32% of the spread. Of this, liquidity-driven default is 67%, pure liquidity 23% and default-driven liquidity about 11%.

**Fit (p. 6).** The model explains about 55% of observed bond-CDS spread variation across ratings. Its term structure is too steep at 10 years.

## Limits
- A calibration of a structural model, not a return test. It offers no trade rule.
- Stops at Ba in the tables. B and CCC are outside Table 4.
- "Recession" moments drop the two worst quarters of the 2008 crisis (p. 6, n. 3). The model has no crisis state.
- Pure liquidity is the same across ratings by construction (p. 42).
- Weak fit at 10 years (p. 6).

## Section touched
`docs/methodology.md` Section 7.1 (structural anchor and `kappa_t`), Section 7.3 (reading of the residual), Section 7.6 (outputs), Section 9.2 (spread channel).

## Use for the two clocks
This section is our proposal, not the source's claim.

**What the source says.** Rollover creates a default component that depends on market liquidity. For Ba bonds, this part is about 13% of spread in both states. The largest part of the cycle rise is default-driven liquidity (45%).

**What our data says.** Section 7.1 scales expected loss by one market factor `kappa_t`. Section 7.2 adds a liquidity block. No part of the model separates liquidity-driven default. The S1 residual therefore holds any such part.

**What we decide.**
1. Add `s_liq_to_def` as a labelled term in the anchor, for issuers with a debt ladder. Solve the anchor again at two liquidity states with the same assets, as in `he-xiong-2012-rollover-risk-credit-risk.md`. Intuition: the part of the fair spread that exists only because debt must roll in this market.
2. Report the residual with and without this term. A residual that shrinks when it enters reads as rollover, not mispricing.
3. Read a wide S1 residual in a liquidity shock as partly default-driven liquidity (45% of the Ba rise), and do not treat all of it as a convergence trade.

**Test.** On the panel: correlate the S1 residual with `rollover_rate_12m` × market illiquidity, month by month. Pass: the correlation is positive in stress windows. The residual without this term has a lower sd in at least three of four windows, and its rank IC does not fall. Our choice, v0.
