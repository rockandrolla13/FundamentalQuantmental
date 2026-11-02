# Hoberg and Phillips (NBER w15991), "Text-Based Network Industries and Endogenous Product Differentiation"

An open copy. An agent read it, and we checked one printed number against the text.

## Claim
Peers built from 10-K text fit better than SIC.

## Method
Cosine similarity of product text, then firm-centred peer sets.

## Data
50,673 firm-years, 1997 to 2006, listed firms.

## Result
- Operating income over sales R-squared 0.458 against 0.312 for SIC-3.

## Limits
- No credit test.
- The averages include the firm itself. Leaving it out reverses the leverage result, by an agent's reading.
- GICS is never tested, and our peer cell is GICS.

## Section touched
`docs/methodology.md` Section 4.7.1, Step 2.

## Use for the two clocks
**Source says:** text peers fit better than SIC. **Data says:** nothing yet. **We decide:** report text peers beside GICS, and first test the fit against GICS with the firm left out.
