# Campello, Lin, Ma, Zou (NBER w16622), "The Real and Financial Implications of Corporate Hedging"

An open copy. Published in JF. An agent read it, and we checked one printed number against the text.

## Claim
Hedged firms pay less on loans, and more so when closer to distress.

## Method
Loan spread on IR and FX hedging, with an instrument.

## Data
2,718 loans, 1,185 firms, 1996 to 2002.

## Result
- IV -2.021 (se 0.315) (Table II).
- Firm effects -1.177, deal level -1.171.
- Hedging x Z-score 0.496.

## Limits
- Loans only, ratings pooled.
- Gross notional counts swaps to floating as hedges.
- Commodity hedges are out of scope.

## Section touched
`hy/clocks.py` `float_unhedged`.

## Use for the two clocks
**Source says:** hedging lowers loan cost. **Data says:** nothing yet. **We decide:** add `float_unhedged` as our own field, split by swap direction, and run M1.19.
