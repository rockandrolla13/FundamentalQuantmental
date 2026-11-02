# Gourio and Rudanko (NBER w17191), "Customer Capital"

An open copy. An agent read it, and we checked one printed number against the text.

## Claim
Customer bases act like an asset, and search for them costs money up front.

## Method
Model and a Compustat sort on SG&A.

## Data
Balanced panel, 648 firms, 1983 to 1999.

## Result
- Churn of 0.15 a year is set from anecdote.
- Absolute profit volatility rises with SG&A, from 0.085 to 0.114.

## Limits
- No credit test.
- Survivors only, and the sort has look-ahead.
- Low SG&A holds cell phones and supermarkets, so SG&A reads acquisition spend and not customer life.

## Section touched
`hy/clocks.py` `soft_revenue`.

## Use for the two clocks
**Source says:** revenue beyond contracts decays. **Data says:** nothing yet. **We decide:** `soft_revenue` is our extension, at stated decay rates. Do not read SG&A as stability.
