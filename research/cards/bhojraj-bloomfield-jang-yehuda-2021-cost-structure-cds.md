# Bhojraj, Bloomfield, Jang, Yehuda (2021), "Cost Structure, Operating Leverage, and CDS Spreads"

The Accounting Review 96 (5), 79-105. DOI 10.2308/TAR-2018-0497. Published online in October 2020, so our review lists it as 2020. The user supplied the PDF. We read pp. 79-90 and Tables 6 and 7, and the sections on grade, asset intensity, and alternative measures. We did not read Tables 8 to 11 in full.

The text extraction drops minus signs. Signs below come from the authors' text.

## Claim
CDS investors price cost structure with macro forecasts, but not fully, so the interaction predicts next-quarter CDS changes (abstract, p. 80).

## Method
`ELASTIC` is the firm's slope of log change in quarterly cash operating costs on log change in sales, year on year, over the prior 40 quarters (eq. 1, p. 83). Cash operating costs are cash sales less operating cash flow before extraordinary items, interest, and taxes (p. 83). `DAI` is the change in the anxious index, the Survey of Professional Forecasters probability of a fall in real GDP next quarter (p. 83). The regression reads CDS change on `ELASTIC x DAI` and controls, with December year ends only, and clusters by industry and quarter (eq. 3, p. 87).

## Data
Markit 5-year CDS, Compustat quarterly, 2001 to 2017. 462 firms, 15,398 firm-quarters, 44,981 firm-months (pp. 82-83). Median market value $8.1bn. No financials or utilities.

## Result
- Same quarter: interaction -1.715 (t 1.80) with all controls (Table 3 col IV).
- Next quarter: interaction -1.470 (t 2.13) with all controls (Table 4 Panel A col IV). The change in leverage and its interaction are not significant.
- One standard deviation of elasticity moves next-quarter spread by 1.13 to 1.32 bp, against a mean quarterly change of 1.90 bp (p. 89). The size is small.
- It sits in the high-elasticity subsample: 1.118 (t 2.42) against 0.301 (t 0.31) (Table 4 Panel B).
- Hedge portfolio: magnitude 0.336 (t 2.26), which is 3.00 bp a month and 36 bp annualized per standard deviation of `DAI` (Table 6, p. 81).
- **By grade (Table 7), magnitudes: investment grade hedge 0.364 (t 2.68). Speculative grade hedge 0.067 (t 0.21).** The grade series ends in 2015 (p. 93).
- Level: mean EDF falls from 0.910 in the lowest elasticity quintile to 0.420 in the highest (Table 1 Panel C).
- Alternative measures with no regression, modified Weiss and Novy-Marx, give similar results (p. 100). Windows of 20 and 32 quarters give similar results (p. 101).

## Limits
- CDS, not bonds. Large firms with CDS quotes.
- The timing result is absent in speculative grade, which is our market.
- The authors say that they cannot fully rule out risk as an explanation (p. 81).
- Forty quarters of history removes young issuers.
- The EDF sort has no controls, and leverage differs across quintiles.

## Section touched
`docs/methodology.md` Section 4.7.1, M1.13. `hy/clocks.py` `cost_elasticity`. Method 4 may read the anxious index as a state.

## Use for the two clocks
**Source says:** fixed cost is a macro exposure, and CDS prices it incompletely in investment grade. **Data says:** nothing yet. **We decide:** add `cost_elasticity` as a level feature and a control. Do not build the timing trade for HY. Test the level with M1.13.
