# Chen, Kacperczyk, Ortiz-Molina (2010 author copy), "Do Non-Financial Stakeholders Affect the Pricing of Risky Debt? Evidence from Unionized Workers"

Published in Review of Finance, DOI 10.1093/rof/rfq028. An agent read it, and we checked one printed number against the text.

## Claim
Stronger unions go with narrower bond spreads, more so in distress.

## Method
Yield spread on workers covered in the industry at t-1, with rating dummies, leverage, and controls.

## Data
996 firms, 5,557 firm-years, 1984 to 1998.

## Result
- Union -186.862 (t 3.33) (Table III col 6), about -32 bp per sd.
- 2SLS -223.635 (t 2.29).
- x HighPD -395.366 (t 4.93) (Table IV).

## Limits
- Levels, no returns, no speculative grade table.
- 93% of the variation is across industries (p. 11), so read it under sector effects.
- The sample ends in 1998.

## Section touched
`docs/methodology.md` Section 4.7.1, M1.14.

## Use for the two clocks
**Source says:** union voice protects creditors against owner risk. **Data says:** nothing yet. **We decide:** keep `union_cic` apart from `labor_share`. Do not pool one labor sign.

**Status, 2026-11-02:** the user closed labor for the clocks. This card is a record only, and its decisions no longer apply.
