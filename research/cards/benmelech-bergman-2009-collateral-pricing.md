# Benmelech and Bergman (NBER w13874, March 2008), "Collateral Pricing"

Published in JFE 91 (2009), as the 2011 paper cites it. We hold the working paper. An agent read it, and we checked one printed number against the text.

## Claim
More redeployable collateral goes with lower spreads, better ratings, and higher loan-to-value.

## Method
Seat-weighted counts of other solvent users of each aircraft type in the pool, leaving out the issuer (p. 13). OLS and ordered probit, clusters by airline.

## Data
246 tranches of 12 US airlines, 1,086 aircraft, 1990 to 2005. Spread at issue.

## Result
- Operators with 5 or more: -0.523 (t -2.39), and -1.277 (t -3.18) with airline effects (Table 6).
- Holding loan-to-value: -2.34 (t -4.03) (Table 12).
- No link to maturity (Table 10).

## Limits
- Primary market levels. No returns, and no speculative grade split.
- Twelve clusters.
- The pool is nearly all new aircraft (mean age 1.3 years).

## Section touched
`docs/methodology.md` Section 4.7.1. `hy/clocks.py` `collateral_weighted`.

## Use for the two clocks
**Source says:** buyers for the asset lower the price of secured debt. **Data says:** nothing yet. **We decide:** use `redeploy_operators_5` for aircraft. The sign on unsecured lease bite stays open, because lessees can renegotiate in distress (p. 6, citing work we did not open).
