# Kim and Kung (January 2013 draft), "The Asset Redeployability Channel"

Published in RFS (2017), DOI 10.1093/rfs/hhv076. The copy at the project root is the draft, and the published version is unread. An agent read it, and we checked one printed number against the text.

## Claim
Firms with less redeployable assets cut investment more when uncertainty rises.

## Method
`A_a` is the share of 123 industries that use asset `a`. `R_j = sum_a w_ja A_a`, with `w_ja` the industry's capex share on `a` (p. 5). Input: BEA 1997 capital flow table, 180 assets.

## Data
91,526 firm-quarters, 1989 to 2010, four VIX shocks. No financials or utilities. Outcome: capex over assets.

## Result
- After x R 1.508 (t 2.92), and 1.309 (t 2.60) with controls (Table 4).
- Placebos -0.243 (t -0.61), 0.155 (t 0.84) (Table 6).
- R runs from 0.12 for oil and gas to 0.68 for legal, sd 0.10 (p. 32).

## Limits
- No bond, spread, loan, default, or recovery test.
- Across industries only (p. 25). One 1997 snapshot. New capex and not installed stock.

## Section touched
`docs/methodology.md` Section 4.7.1. `hy/clocks.py` `collateral_weighted`.

## Use for the two clocks
**Source says:** resale can be scored for any industry. **Data says:** nothing yet. **We decide:** report `redeploy_r`, with no sign on spread until M1.15 reads.
