# Valta (2012), "Competition and the Cost of Debt"

JFE 105, at the project root. An agent read it, and we checked one printed number against the text.

## Claim
Firms in more competitive industries pay more on bank loans.

## Method
`Competition` is 1 when the fitted Hoberg-Phillips SIC-3 HHI is in the lowest yearly quartile. Log all-in-drawn spread. Tariff cuts serve as a shock.

## Data
12,256 loans, 1992 to 2007, mean spread 178 bp.

## Result
- Competition 0.096 (t 3.00), about 17 bp (Table 3).
- Tariff cut 0.221 (t 7.05) (Table 6). Firm and year effects 0.080 (t 2.72) (Table 7).
- Illiquid assets 0.243 (t 2.91), liquid 0.096 (t 2.28), p 0.11 (Table 11).

## Limits
- Loans only. No bonds, no returns, no speculative grade split.
- Tariff events cover manufacturing only.

## Section touched
`docs/methodology.md` Sections 4.4, 4.7.1. `hy/clocks.py` `competition_flag`.

## Use for the two clocks
**Source says:** competition carries a credit price. **Data says:** nothing yet. **We decide:** fill `adverse_competition`, and test bonds with M1.17.
