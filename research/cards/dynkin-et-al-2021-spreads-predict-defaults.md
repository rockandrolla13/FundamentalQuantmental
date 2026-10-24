# Ben Dor, Desclée, Dynkin, Hyman, Polbennikov (2021), *Systematic Investing in Credit*: spreads, defaults, and the credit cycle

Wiley, 2021. Practitioner research book (Barclays Research), not peer reviewed. Page numbers are PDF pages of the copy in the repo root. The printed folio is the PDF page minus 28. The card `dynkin-et-al-2021-systematic-investing-in-credit.md` covers the signal chapters. This card covers only the passages on the credit cycle: chapter 8 (spreads and defaults) and chapter 5 (issuance).

## Claim
1. The high yield index spread at the start of a year predicts the default rate of that year's cohort. The link holds for one or two years and is gone by year three (ch. 8, pp. 311–313).
2. "Two years is a long time in the context of the credit cycle". Beyond two years, today's spread says almost nothing about default or about future spreads (p. 316).
3. Spreads also predict downgrade rates, but with wide scatter (pp. 313–314).
4. Downgrades into high yield move with the business cycle, proxied by index OAS. Upgrades do not (ch. 2, p. 114).
5. High net issuance predicts low excess returns over the next six months. The effect is larger in sectors that the credit cycle hits hardest: cyclical, communication and technology, and financials (ch. 5, pp. 220–224).

## Method
**Spread against cohort default (pp. 311–312).** For each annual cohort 1991–2012, plot the beginning-of-year spread of the Bloomberg Barclays High Yield index against the Moody's issuer-weighted cumulative default rate at horizons of one to five years. Report the correlation per horizon.

```latex
\rho_h = \mathrm{corr}\big(OAS_{HY}(t_0),\ CDR_{HY}(t_0, t_0 + h)\big), \qquad h = 1, \dots, 5 \text{ years}
```

Intuition: if the market prices the coming default wave, a wide start spread should precede a high default count.

**Spread against downgrade rate (pp. 313–314).** Annual cohorts of issuers in the US Corporate index, 1991–2013, without 2009. Regress the one-year frequency of a full-letter downgrade on the beginning-of-year OAS (in %).

```latex
\text{A-rated: } DG = 0.014 + 0.049\,OAS,\ R^2 = 0.312 \qquad \text{Baa-rated: } DG = 0.018 + 0.022\,OAS,\ R^2 = 0.128
```

**Spread persistence (p. 316).** Follow the same bonds from January of each year 1991–2013 for one to five years. Correlate the start spread with the end spread per rating.

**Issuance (pp. 221–224).** Six-month net issuance as a share of amount outstanding in the US Corporate All Ratings index, August 1994 to July 2014. Sort periods into issuance quartiles. Compare the next six-month excess return of the bottom and top quartiles, overall and by sector (Table 5.2, p. 223).

## Data
- Moody's cumulative issuer-weighted default rates by annual cohort, 1991–2012 (Ou et al. 2013, note 16, p. 330). Bloomberg Barclays High Yield and Corporate indices.
- Downgrades: issuer-level data from market-value weighted bonds, 1991–2013.
- Issuance: US Corporate All Ratings index, August 1994 to July 2014.

## Result
- **Default.** Correlation of start spread with realised default is 0.84 for HY and 0.63 for IG in year 1. It is 0.12 (HY) and 0.18 (IG) in year 2. From year 3 the correlation turns negative (p. 312). Low spreads at the start of 1998 and 2006 gave no warning of the later crises (p. 313).
- **Downgrade.** Same-spread cohorts can differ a lot. At 140 to 160 bp, the A-rated downgrade rate ranged from 2.48% (2010) to 20.90% (2003) (p. 313). The 2009 cohort is an outlier: wide spreads, modest downgrades, much of the spread from illiquidity (p. 313).
- **Spread persistence.** Start spreads correlate with spreads one or two years later. The correlation turns negative by the end of year 3 (p. 316).
- **Issuance.** The bottom issuance quartile beats the top quartile in the next six months. Total: 4.72% over August 1994 to July 2014 (Table 5.2, p. 223). The book says the gap is larger for cyclical, communication and technology, and financials (p. 224). The OCR of Table 5.2 is partly garbled, so only the total row and the noncyclical row (0.40, 1.00, 0.61) are quoted here.

## What our data says
No fit on our data yet. Effect on the three macro links:

1. **Link 1, path probabilities (5.4).** The horizon result matters here. Our paths run 8 quarters. The book shows that the spread information fades after about 2 years. Proposal: do not hold the forecast mass of a path flat across all 8 to 12 quarters. Shrink the path probabilities toward the phase prior as the horizon passes 8 quarters. Test: over matured vintages, the Brier score of the path mass at horizons 9 to 12 should not beat the phase prior alone. If it does not, apply the shrink.
2. **Link 2, downside weights (5.2).**
   - Supports `hy_oas` as an input to the logistic at the 4-quarter horizon. A correlation of 0.84 between start spread and one-year HY default rate is the strongest number in these sources for a macro input to a default-type event.
   - The event in Section 5.2 is an EBITDA decline, not a default. The book measures default. The link from spread to EBITDA decline is not tested here. Test: on our panel, fit the logistic with `hy_oas` alone, then add `sloos_tightening`, `default_rate_fcst`, and `pmi`. Keep each added input only if the out-of-sample log loss falls in at least three of the four cycle windows.
   - The 2009 outlier warns that part of a wide spread is illiquidity, not expected loss (p. 313). Proposal: when the median `bid_ask_bp` of the HY universe (Section 3.1) sits in its top decile, cap the `hy_oas` input at its 90th percentile before the logistic reads it.
   - The issuance result supports the "issuance quality" indicator of the F6 phase vote. It also says the effect is sector-specific. That supports `θ_sector` in the logistic.
3. **Link 3, revenue shift (5.2).** Nothing direct on revenue. The sector split of the issuance result (cyclical and communication and technology larger, noncyclical small) agrees in sign with the cyclical against defensive split of `β_sector`.

## Limits
- Index-level and cohort-level results. Each correlation rests on about 22 annual points.
- The default series is Moody's issuer-weighted, all HY. No split by sector or rating inside HY.
- The study is in-sample. No out-of-sample test of the spread-to-default map.
- Pages 311–312 figures are OCR-garbled. Only the numbers stated in the text are quoted.
- The issuance study is on the US Corporate All Ratings index. The book does not split HY from IG in that study.

## Section touched
`docs/methodology.md` Section 5.2 (logistic inputs, `θ_sector`) and Section 5.4 (path probability by horizon). `docs/framework.md` F6 (issuance quality indicator). `hy/forward.py` (pooled logistic).
