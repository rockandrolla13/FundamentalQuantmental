# Culp, Nozawa, Veronesi (working paper), "Option-Based Credit Spreads"

NBER w20776. An open copy. An agent read it. We checked the pooled regression against the text. We did not check the table values.

## Claim
Pseudo bonds, made of a Treasury less a put, carry spreads that respond to idiosyncratic volatility.

## Method
Pseudo spread on default probability, loss given default, and log idiosyncratic volatility. Idiosyncratic volatility is the standard deviation of market-model residuals.

## Data
SPX and its stocks, January 1996 to July 2015.

## Result
Default probability 0.532 (t 10.92), loss given default 0.007 (t 0.13), log idiosyncratic volatility 0.045 (t 3.89).

## Limits
Pseudo spreads, not corporate bonds. Levels, not returns. The main text gives no estimation window.

## Section touched
`docs/decisions/2026-11-01-clocks-residual-timing.md`, Method 3.

## Use for the residual
**Source says:** idiosyncratic volatility enters a spread level. **Data says:** nothing yet. **We decide:** test log idiosyncratic volatility as a control in `X`, with no signal weight. It may remove return signal, so compare with and without it. No code is added yet.
