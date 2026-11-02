# Jankowitsch, Nagler, Subrahmanyam (2014), "The Determinants of Recovery Rates in the US Corporate Bond Market"

JFE, author copy at the project root. An agent read it, and we checked one printed number against the text.

## Claim
Recovery depends on bond terms, firm facts, and market and industry default rates.

## Method
Recovery price is the mean daily TRACE price over days 0 to 30 (eq. 1, p. 12).

## Data
2,235 event-bonds, 259 firms, 2002 to 2010.

## Result
- Speculative grade, Table 5 Model 2 (N 868): financing covenant +9.4359, market default rate -4.4021, industry default rate -0.6808, maturity -1.0109, default barrier -0.2586.
- Means: secured 49.27, unsecured 39.09, subordinated 15.13 (p. 40).
- Retail 33.40 (N 33), electricity 48.03 (p. 40).

## Limits
- No lease or purchase variable.
- No returns.
- Price dispersion is measured after default, so it cannot enter a forecast.

## Section touched
`docs/methodology.md` Sections 4.7.1, 6.2. Test M1.6.

## Use for the two clocks
**Source says:** a method for a recovery outcome. **Data says:** nothing yet. **We decide:** M1.6 reads this outcome and these controls. Long bonds trade lower (-0.5651, se 0.0686), which conflicts with the Section 6.2 reading, so report the median same-rank price beside it.
