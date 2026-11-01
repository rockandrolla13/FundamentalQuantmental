# Kraft (2011 draft), "Rating Agency Adjustments to GAAP Financial Statements and Their Effect on Ratings and Bond Yields"

Published as Kraft (2015), "Rating Agency Adjustments to GAAP Financial Statements and Their Effect on Ratings and Credit Spreads", The Accounting Review 90(2), pp. 641-674, DOI 10.2308/accr-50858. Peer-reviewed. **We did not open the journal article.** We read the draft of December 1, 2011, 49 pages, from a Rutgers seminar page (`raw.rutgers.edu/docs/seminars/Fall11/`). Page numbers are PDF pages, and they equal the printed pages. The journal numbers may differ. Evidence class: US corporate bonds at issue, investment grade and high yield.

**Added at the audit close.** The screen graded this paper 3, and the cap dropped it. The search for a Moody's text found the draft.

## Claim
Moody's adjusts reported statements for off-balance-sheet debt, mainly operating leases and securitizations (p. 1). The median leverage ratio rises by 14% after the adjustments (p. 3). The off-balance-sheet estimates go with lower ratings and higher bond yield spreads (pp. 1, 4).

## Method
**Data construction (pp. 11-12).** The author takes the line-by-line difference between reported and adjusted statements in Moody's Financial Metrics. One random bond issue enters for each issuer-year. The bond must come to market in the twelve months that start three months after the fiscal year end, so the statements are public.

**Yield regression (p. 18, eq. 2).**

```latex
\log Spread_{t+1,i} = \alpha + \beta\,ADJ_{t,i} + \sum_n \gamma_n FirmChar_{n,t,i} + \sum_m \delta_m IssueSpec_{m,t+1,i} + \epsilon_{t,i}
```

Intuition: ask whether the debt that the agency adds to the balance sheet moves the offering spread, at equal reported leverage. `ADJ` is the net adjustment over reported total assets (p. 42). Firm controls are size, leverage, coverage, margin, return on assets, and tangibility. Issue controls are maturity, offering amount, and a senior secured dummy (p. 44).

**Model test (pp. 20-21).** A non-nested J-test compares a model on adjusted ratios with a model on reported ratios.

## Data
- Moody's Financial Metrics, US non-financial issuers, 2002 to 2008 (pp. 3, 11).
- 1,210 firm-year bond issues out of 1,963 with data (p. 12, note 17).
- Ratings (Table 1 Panel B, p. 38): Aaa 9, Aa 41, A 275, Baa 429, Ba 269, B 174, Caa 13. So 456 of 1,210 issues are speculative grade (our sum).
- Spread is the offering yield less a comparable Treasury yield (pp. 12, 18). Most spreads sit between 50 bp and 400 bp (p. 12).

## Result
**Table 4 Panel B (p. 44), log offering spread, 1,210 observations, R-squared 0.52.**

| Term | Coefficient | t |
| --- | --- | --- |
| `OffBS_leases` | 0.450 | 5.24 |
| `OffBS_total debt` (another column) | 0.457 | 5.21 |
| Leverage | 0.860 | 7.23 |
| Size | -0.250 | 12.41 in absolute value |
| Senior secured | 0.138 | 2.40 |

**Reading by the author.** "For a one-unit increase in the scaled increase in total debt, the yield spread increases by 58%" (p. 20). "The footnote-based estimates of off-balance-sheet debt are priced in the bond market" (p. 20). In a rating regression with the spread on the right, "the yield spread fully subsumes the estimate of off-balance-sheet finance" (p. 4).

**Size of the adjustment (pp. 3, 15).** The median coverage ratio falls by 18%. Moody's capitalizes leases for 80% to 100% of observations in almost every industry (p. 15).

## Limits
- The spread is an offering spread. The test holds no secondary market price and no time series of a bond.
- The sample ends in 2008, before ASC 842. It pools investment grade and high yield, with no high yield column.
- The variable is lease amount over assets. It says nothing on the date of rent or on rent after a contract ends.
- The author's data is a licensed Moody's product. Our panel has no such field.
- This is a draft. The journal title and numbers may differ.

## Section touched
`docs/methodology.md` Section 4.7 (the reason for the wrong sign), Section 7.2 (forward block). `docs/framework.md` F8 (`lev_lease_adj`).

## Use for the two clocks
**What the source says.** At equal reported leverage, more capitalized lease goes with a wider offering spread. This is a level result, in a sample with 456 speculative grade issues.

**What our data says.** Section 4.7 records -2.07 (t -2.4) on a share that holds rent and purchases after year 2. That share is a ratio inside all obligations, and it has no leverage control. No test on file reads a lease amount against a spread.

**What we decide (our proposal, not the source's claim).** The source raises the odds of hypothesis 1 of the review, composition. It does not settle that hypothesis, because the source tests an amount and Section 4.7 tests a share. M1.2 reads the amount on our panel.

**Test.** M1.2 of `docs/decisions/2026-11-01-clocks-residual-timing.md`. A slope that stays below 0 under the rules of that test rejects composition on our panel.
