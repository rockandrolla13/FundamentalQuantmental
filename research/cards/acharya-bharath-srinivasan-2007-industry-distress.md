# Acharya, Bharath, Srinivasan (2007), "Does Industry-Wide Distress Affect Defaulted Firms?"

JFE 85, 787-821, DOI 10.1016/j.jfineco.2006.05.011. An agent read it, and we checked one printed number against the text.

## Claim
Instruments recover less when the issuer's industry is in distress, and more so where assets are specific.

## Method
`Distress1` is 1 when the median 3-digit SIC stock return is at or below -30%, leaving out the firm, with 5 or more peers (p. 802). `asset_spec` is median machinery and equipment over assets.

## Data
US, 1982 to 1999. 1,511 instruments, 778 in regressions. Emergence price, discounted at a HY index.

## Result
- Distress1 -11.11 cents (se 4.39) (Table 3).
- Asset specificity x Distress1 -1.08 (se 0.36) (Table 4).
- Senior x Distress1 -21.08 (se 7.16) (Table 5).
- Default lasts 2.16 against 1.37 years (Table 8).

## Limits
- Recovery only. No returns, no spreads. The authors leave pricing open (p. 820).
- The sample ends in 1999, so no haircut size transfers.

## Section touched
`docs/methodology.md` Sections 4.7.1, 6.2. `hy/clocks.py` `industry_distress`.

## Use for the two clocks
**Source says:** recovery depends on the state of the industry. **Data says:** nothing yet. **We decide:** add distress and asset type to Step 5 and to M1.6.
