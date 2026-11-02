# Asvanunt and Richardson (2017), "The Credit Risk Premium"

The Journal of Fixed Income 26(3), pp. 6–24, Winter 2017, DOI 10.3905/jfi.2017.26.3.006. Peer-reviewed. Corporate bonds and CDS. We read the journal article on the AQR site (`aqr.com/-/media/AQR/Documents/Journal-Articles/JFI_Winter_2017_AQR_The-Credit-Risk-Premium.pdf`, 20 pages). The review's first check found no open copy. Page numbers are PDF pages. Printed page = PDF page + 4. Exhibits with no text layer were read from page images. Both authors work at AQR, which invests in these securities (p. 19).

## Claim
A credit risk premium exists once excess returns match duration (pp. 2–3). A simple difference of long corporate and long government returns over-hedges and understates it (p. 2). The premium adds to the equity and term premia (pp. 3, 11). It is larger in periods of growth and when default rates fall (pp. 3, 14–15).

## Method
**Empirical durations (p. 6).** Rolling 120-month regressions.

```latex
R^{GOVT}_t = \alpha + \beta^{GOVT\_IR}_t \Delta Y^{GOVT}_t + \epsilon_t \quad (1), \qquad R^{CORP}_t = \alpha + \beta^{CORP\_IR}_t \Delta Y^{GOVT}_t + \beta^{CORP\_SPR}_t \Delta Y^{Baa-Aaa}_t + \epsilon_t \quad (2)
```

Intuition: each regression reads the rate sensitivity of an index from its own returns, because the old data give no duration.

**Credit excess return (p. 6).**

```latex
R^{CORP\_XS}_t = R^{CORP}_t - \frac{\beta^{CORP\_IR}_t}{\beta^{GOVT\_IR}_t} R^{GOVT}_t \quad (3)
```

Intuition: hedge only the rate exposure that the corporate bond actually has, and keep the term premium out of the credit return.

From 1988, use Barclays credit excess returns, built with key-rate-duration matched Treasuries (p. 5). A validity check on Barclays data gives correlation above 0.99 and averages within 1 bp (p. 7).

**State split (pp. 12–15).** Growth: mean of the standardised CFNAI and the surprise in industrial production. Inflation: mean of the standardised inflation rate and CPI surprise. Default: mean of the standardised change and surprise in the Moody's investment-grade default rate. Split at the median. The authors call this descriptive, since states and returns are contemporaneous (pp. 14–15).

## Data
Ibbotson long-term corporate bonds from 1926, Barclays US IG and HY from August 1988, Barclays pan-European from 1999, CDX and iTraxx from April 2004 (pp. 4–5, 16–17).

## Result
- US IG, 1936–2014: 137 bp a year, Sharpe 0.37 (p. 2). The naive difference gives 7 bp (p. 3).
- 1988–2014 (p. 2, p. 8): high yield 248 bp, Sharpe 0.26. Barclays IG 50 bp, Sharpe 0.13. Ibbotson long corporate 161 bp, Sharpe 0.33.
- Durations 1936–1988 (p. 6): government −11.76, corporate −6.09.
- Regression intercepts of credit on equity and term: 7 to 11 bp a month (p. 11).
- Optimal weights, 1936–2014: 48% credit, 35% government, 17% equity, not different from equal weight (pp. 11–12). 1988–2014 with high yield: 18%, 74%, 7% (p. 16).
- CDX Sharpe, 2004–2014: IG 0.45, HY 0.68 (p. 17). Removing spread tightening lowers HY to 0.66 (p. 17).

**Growth and inflation (Exhibit 10, p. 14), Sharpe, 1972–2014.**

| State | Sharpe |
| --- | --- |
| Growth up | 0.60 |
| Growth down | 0.08 |
| Inflation up | 0.11 |
| Inflation down | 0.31 |
| Growth up, inflation up | 0.62 |
| Growth up, inflation down | 0.57 |
| Growth down, inflation up | −0.14 |
| Growth down, inflation down | 0.25 |

**Default (Exhibit 11, p. 15), 1936–2014.** Default rates up: 0.5% a year, Sharpe 0.12. Default rates down: 2.2%, Sharpe 0.48.

## Limits
- States are contemporaneous, so this is not a timing rule (pp. 14–15). The authors state that a tactical investor needs forecasts of growth and inflation (p. 19).
- Older data hold AA-like long bonds (p. 10). So the long sample says little about high yield.
- Sharpe ratios on index returns before cost. The authors say the optimal weights ignore cost and capacity (p. 11).
- Source inconsistency: the conclusion says the premium is higher in periods of growth and inflation (p. 19). Exhibit 10 shows a higher Sharpe when inflation is down (0.31 against 0.11, p. 14).
- High yield result rests on one sample, 1988–2014, with a low Sharpe.
- Authors' firm invests in the area (p. 19).

## Section touched
`docs/methodology.md` Section 7.7 (risk premium test), Section 8 (composite phase weights), Section 11 (return definition), and `docs/decisions/2026-10-26-conviction-book.md` layer 1.

## Use for the two clocks
This section is our proposal, not the source's claim.

**What the source says.** Realised credit excess returns are high when growth is above median and when default rates fall. Those states are only known afterward.

**What our data says.** `hy/backtest.py` already hedges duration with a matched Treasury return in `realised_excess_return`. So the measurement bias of this paper does not apply to our panel. S7 failed. No phase test exists.

**What we decide.**
1. Keep the duration-matched return as the single credit return in every clock test.
2. Do not use the state table as a timing rule. Use it as a target. A timing rule must forecast these states or returns ahead of time.
3. Record the difference from `boyarchenko-elias-2024-global-credit-cycle.md`. Realised return is high when growth is high. Expected return is high after spreads and VIX jump. Both can hold, because one is contemporaneous and the other predictive. Use the predictive form for the band target.
4. Report the clock features in the four state cells of Exhibit 10 as a description, with no weight.

**Test.** Any new band target must forecast the sign of the growth and default states out of sample. Pass: Brier score below the base rate, scored as in test T7 of the conviction-book page. Our choice, v0.
