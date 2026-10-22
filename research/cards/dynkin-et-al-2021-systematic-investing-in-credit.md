# Ben Dor, Desclée, Dynkin, Hyman and Polbennikov (2021), *Systematic Investing in Credit*

John Wiley & Sons, Hoboken, 2021. Frank J. Fabozzi Series. ISBN 9781119751281 (hardback). Practitioner book by the Barclays Quantitative Portfolio Strategy (QPS) group. The title page (PDF p. 9) lists five authors: Arik Ben Dor, Albert Desclée, Lev Dynkin, Jay Hyman, Simon Polbennikov. The copyright page (PDF p. 10) gives 2021. The repo cites the book as "Dynkin et al. 2021". The PDF metadata names Dynkin only.

Page numbers below are PDF pages of the repo-root file. For chapters 13 to 21, PDF page = book page + 28. The text comes from `pdftotext` of a scanned copy. Rotated tables did not survive, so this card quotes only numbers that the text or a legible table states.

## Claim
Three issuer-level signals predict corporate bond excess returns beyond spread level:
1. ESP, excess spread to peers, is a relative value signal (ch. 13).
2. SPiDER, spread per unit of debt over sustainable EBITDA, is a long-horizon value signal (ch. 14).
3. EMC, the issuer's own stock return, is a momentum signal (ch. 15).

ESP is pro-cyclical and EMC is contra-cyclical in index drawdowns. OneScore averages the two within each sector and gives steadier returns (ch. 19, PDF p. 632). Most of that cyclicality comes from DTS bias between the long and short legs. A DTS-neutral form removes most of it (PDF p. 632).

## Method

**ESP (ch. 13, PDF pp. 443–446).** The peer group is rating x industry x duration. The method controls for financial leverage over the same peers (PDF p. 444). The book draws the idea as a scatter of excess spread against excess leverage (Figure 13.3, PDF p. 444). It does not print a closed formula. One reading of the text:

```latex
ESP_i = (s_i - \bar{s}_{peer}) \;\text{after a control for}\; (L_i - \bar{L}_{peer}), \qquad L_i = \frac{D_i^{book}}{E_i^{mkt} + D_i^{book}}
```

Intuition: a bond is cheap when its spread is above peers by more than its excess leverage explains.
- Leverage is book debt over (market equity plus book debt), with a 3-month lag (note 5, PDF p. 461).
- The text says "peer averages" (PDF p. 445). It gives no log transform and no median.
- Universe: senior noncallable bonds of the Bloomberg Barclays US Corporate (IG) index, mapped to Compustat. The top 0.5% of spreads are out (note 7, PDF p. 462).
- Monthly ESP. Decile sorts, and a long-short of above against below median, market weighted (note 9, PDF p. 462).
- Fama-MacBeth regressions of bond excess return on percentile-rank exposures to spread, duration and ESP, plus sector DTS (notes 13–14, PDF p. 462).

**SPiDER (ch. 14, PDF pp. 468–469).**

```latex
SPiDER_{i,t} = \frac{OAS_{i,t}}{Debt_{i,t} \,/\, \text{Sustainable EBITDA}_{i,t}}
```

Intuition: the market price of default risk per unit of the issuer's debt burden on long-run earnings.
- OAS is the market-value-weighted OAS of all the issuer's bonds.
- Debt is long-term plus short-term debt.
- Sustainable EBITDA is the mean of the last 10 annual EBITDA figures, with at least 6 (PDF p. 468).
- Formation each end of February. Fundamentals come from fiscal periods that end October to December of year t−1, a lag of two months (PDF p. 469).
- Filters: no financials, HY rated B or above, HY price at least $50, at least 6 years of statements (PDF pp. 465–466).
- Quintiles are ranked **within each industry** (PDF p. 473, p. 475). Issuers carry equal weight and the book holds them 12 months (PDF p. 475).
- Universe: US Corporate and High Yield indices, March 1993 to February 2020.

**EMC (ch. 15, PDF pp. 513–514).** The book first sorts on the 3-month stock return "as an illustration" (PDF p. 513). It calls the 3-month choice arbitrary (PDF p. 514). The rest of the chapter uses a combined signal:

```latex
EMC_i = \tfrac{1}{3}\left(\frac{r_{i,1m}}{\sqrt{1}} + \frac{r_{i,3m}}{\sqrt{3}} + \frac{r_{i,6m}}{\sqrt{6}}\right)
```

Intuition: the square-root scale puts the three horizons on one volatility footing, so a steady trend scores higher than a one-month jump (note 9, PDF p. 541). Universe: US IG and HY index bonds, December 1992 to May 2017, issuers with listed equity only (PDF p. 513).

**OneScore (ch. 19, PDF p. 626).**
1. Aggregate bond ESP and EMC to the issuer. Use market weights and bonds with more than 3 years to maturity only.
2. Rank each issuer signal within its industry sector.
3. Average the two ranks with equal weights.
4. Re-rank the average within each sector. Assign deciles 1 to 10.

Chapter 18 instead combines ESP and EMC with equal weights at the bond level (PDF p. 625). The ch. 19 test universe is US IG. Portfolios hold up to 10 top and 10 bottom issuers per sector, equal weight across issuers (PDF p. 628).

**DTS neutral (ch. 19, PDF p. 632).** Divide each leg's excess return by its start-of-month DTS and multiply by 12. The value 12 is the 1993 to 2020 mean DTS of the IG index (note 4, PDF p. 635).

## Data
- ch. 13: US IG index, January 1993 to January 2016. Over 2,000 bonds a month on average, over 4,000 recently (PDF p. 445).
- ch. 14: US IG and HY, March 1993 to February 2020. February 2019 final sample: 463 IG and 491 HY tickers (Table 14.1, PDF p. 466). Compustat maps 68% of HY market value in 1994 and 83% in 2019.
- ch. 15: US IG and HY, January 1993 to May 2017.
- ch. 19: US IG, results to 28 February 2020.
- All returns are excess over duration-matched Treasuries, before transaction costs, unless the text says otherwise.

## Result
**ESP (ch. 13).**
- Top-decile information ratio 0.42 without the leverage control, 0.53 with it. Top-decile excess return 2.63% against 3.29% a year (Table 13.1, PDF p. 446). The book calls the gain "moderate".
- High minus low ESP: 1.78% a year, volatility 1.18%, max drawdown −2.0%, correlation with index 20%, 1993–2016 (Table 13.3, PDF p. 448). High ESP over index: 1.18% a year.
- 2002 and 2015 gave negative 12-month returns. The book links them to spread momentum against mean reversion (PDF p. 451).
- The edge is larger when ESP dispersion is high, and the top dispersion quintile is the 2008 crisis (PDF p. 451).
- By liquidity (TES quintiles, from 2007), information ratios are highest in the less liquid buckets (Table 13.6, PDF p. 452).
- Turnover falls from 11.2% to 5.7% a month with a 10% buffer, and return rises to 1.98% (Table 13.7, PDF pp. 453–454).
- Fama-MacBeth ESP premium 15.2 bp a month, t 8.6, alone. It stays significant (t 8.0) beside spread and duration, and spread loses significance (PDF p. 458).

**SPiDER (ch. 14).**
- Long-short Q5 minus Q1 information ratio 1.17 in IG and 0.73 in HY (PDF p. 477).
- HY long-only: 3.64% a year, IR 0.47, against benchmark 2.21% and 0.27 (PDF p. 477).
- Debt over EBITDA predicts downgrades within a rating bucket (Table 14.3, PDF p. 469). With industry dummies, one standard deviation of D over E adds 28.3 bp to HY OAS (PDF p. 471).
- The edge survives DTS risk matching and an OAS-neutral sort (PDF pp. 481–482).
- By rating: Ba IR 0.30, B IR 0.63 (Table 14.9, PDF p. 484).
- Signal life is about 8 quarters, with a small peak in quarter 5 (Figure 14.8, PDF p. 492).
- Value weights cut the long-short IR to 0.58 IG and 0.57 HY (PDF p. 489).

**EMC (ch. 15).**
- Q5 minus Q1: 6.34% a year, IR 1.56, 1993–2017 (Table 15.1, PDF p. 515).
- By quality: Aaa–A 3.9% (IR 0.83), Baa 8.8% (IR 1.87). For HY the text says 19.9% a year, IR 1.74 (PDF pp. 515–516). The OCR of Table 15.2 reads 15.7. Check the print before you quote the HY figure.
- The signal decays fast (PDF p. 516).
- Sector timing with EMC (ch. 16): +4.04% a year over the US HY index, 2007–2017, before costs (PDF p. 550).

**OneScore (ch. 19).**
- Top minus bottom OneScore outperforms in every IG sector over 2016–2020 (PDF p. 629). Table 19.2 is not legible.
- In drawdowns, raw EMC is contra-cyclical and raw ESP is pro-cyclical (PDF p. 632).
- With the DTS adjustment, both make money in every drawdown episode (PDF p. 632).
- ESP correlation with the index falls from 34% to −6% in drawdowns, and from 44% to −22% in other periods (PDF p. 634).

## What our data says (hy/peers.py, decision pages of 22 October 2026)
The repo build differs from the book at four points. Points 1 to 3 are mismatches to fix or record. Point 4 is a known gap.

1. **ESP leverage is a different ratio.** `esp_lev_*` controls for excess log of debt over LTM EBITDA (the `leverage` column of `leverage_full`). The book uses market leverage, book debt over (market equity plus book debt), lagged 3 months (note 5, PDF p. 461). Our control is a cash-flow leverage, which also enters E13. The result "the leverage control halves the ESP edge" therefore tests our ratio, not the book's. Market leverage needs `prccq × cshoq`, which `hy/sources/compustat_pit.py` can supply.
2. **SPiDER rank scope.** The `hy/peers.py` docstring and decision page `2026-10-22-esp-peer-groups` say "one rank across all sectors". The book calls SPiDER an absolute measure (PDF p. 464), but it ranks quintiles within industry (PDF p. 473, p. 475). Our `spider_sr` (sector x rating) is nearer the book's sort than our `spider`. The book version for a test is a within-GICS-sector rank of `spider`.
3. **EMC horizon.** `EMC_MONTHS = 3` and the onescore decision page say "main case 3 months". The book uses 3 months only as an illustration and builds the chapter on the combined 1, 3 and 6-month signal with square-root scale (PDF p. 514, note 9 p. 541). OneScore inherits that EMC.
4. **OneScore aggregation.** `onescore()` takes the median `esp_sr` over all the issuer's bonds. The book uses a market-weighted mean over bonds with more than 3 years to maturity (PDF p. 626). The panel has no amount outstanding, so the weight gap is a known gap. The 3-year filter is not, because `years` is in the panel. The book re-ranks the average within sector and assigns deciles. Our mean of ranks gives the same order inside a sector, so that step changes nothing for the within-sector rank IC.

Points of agreement:
- Sustainable EBITDA (10 years, minimum 6), the 2-month lag, and the February schedule match ch. 14.
- Financials out of SPiDER matches.
- The equal ESP and EMC weight matches ch. 18 and 19.
- The decision page's note that our HY universe keeps CCC bonds is correct. Ch. 14 keeps B or above and price at least $50 (PDF p. 465).

Comparison of results:
- The book's ESP and OneScore evidence is investment grade only. Our HY panel shows ESP fails in stress (2008 −0.05, 2020 −0.17 beyond spread). The book also reports ESP losses in 2002 and 2015 and pro-cyclicality (PDF pp. 451, 632). So our result agrees with the book, not against it.
- The book's fix for that pro-cyclicality is the DTS-neutral leg (PDF p. 632). Decision page `2026-10-22-onescore` already lists it as the test that settles the rest.

**Falsifiable tests.**
1. Rebuild `esp_lev` with market leverage. Keep the leverage control only if the 12-month beyond-spread IC beats plain ESP (+0.096, t 2.6).
2. Rank `spider` within GICS sector. Replace the absolute rank if the 12-month beyond-spread IC rises above +0.032.
3. Compute the combined 1, 3 and 6-month EMC. Keep 3 months only if the combined signal does not raise the 6-month beyond-spread IC of OneScore above +0.034 or the cycle pass count above 3 of 4.
4. Drop bonds with 3 years or less from the issuer ESP. Rerun `scripts/backtest_onescore.py`.
5. DTS-neutral long-short (scale each leg to DTS 12, or to the HY panel's own mean DTS). The book predicts ESP turns positive in the 2008 and 2020 windows.

## Chapters not yet used that serve the mission
1. **Ch. 2–4, fallen angels (PDF p. 109 onward, Reversal Scorecard p. 191).** Forced selling at the IG-to-HY boundary and a reversal score. This fits signal S6 (rating migration and forced flows).
2. **Ch. 10, coupon effects (PDF p. 361).** Premium bonds trade wider, and discount bonds show spread convexity and outperform in high-risk periods (PDF p. 378). This fits the fair spread model (Section 7.2) as a price control.
3. **Ch. 11, maturity dependence (PDF p. 383).** Long bonds earn less per unit of risk, through roll-down and downgrades (PDF p. 395). This fits the maturity bucket of the peer cell and the horizon of Section 7.5.
4. **Ch. 17, issuer size (PDF p. 555).** After sector, rating and liquidity controls, the HY size premium is 5.3 bp in May 2018, in a range from −171 to 70 bp (PDF p. 580). It is a control, not a signal.
5. **Ch. 18, implementation (PDF p. 591).** Turnover control, liquidity filters, and costs for ESP and EMC together (PDF p. 617). This fits the cost line of the alpha formula in Section 7.5.
6. **Ch. 20, post-earnings drift (PDF p. 641).** Bond returns drift after earnings surprises, apart from EMC (PDF p. 678). This fits signal S3 (estimate revision) and the event model of Section 9.
7. **Ch. 21, equity short interest (PDF p. 681).** High short interest predicts downgrades and low bond returns in HY and IG (PDF p. 714). This fits S6 and Section 9.

The book has no DTS chapter and no liquidity chapter. DTS comes from Ben Dor et al. (2007), which ch. 14 cites (PDF p. 474). Liquidity appears only as TES in ch. 13 (note 10, PDF p. 462) and in ch. 3 (bond-CDS basis and costs). A DTS card needs that 2007 paper.

## Limits
- ESP, EMC by quality, and OneScore results are mostly IG. Only ch. 14, 15 and 16 report HY.
- All results are before transaction costs, except where ch. 18 adds them.
- Barclays index data uses OAS and market weights. Our panel uses TRACE G-spread and equal weights.
- The book does not print an ESP formula, so the ESP rebuild rests on text and a figure.
- Rotated tables (13.5, 13.8, 14.2, 14.7, 14.8, 14.10, 19.2, 19.3, 19.4) are not legible in the text layer. This card quotes their figures only where the text repeats them.
- The text layer gives the page numbers of the chapter 16, 17, 20 and 21 conclusions. Check them against the PDF before you cite them in a memo.

## Section touched
`docs/methodology.md` Section 7.4 (ESP, SPiDER and OneScore paragraphs), Section 8 (S3, S6, and the composite), Section 9 (event signals from ch. 20 and 21), and Section 11 (backtest design: DTS-neutral legs). Code: `hy/peers.py` (`peer_signals`, `equity_momentum`, `onescore`), `hy/groups.py` (E14, E15, E16). Decision pages: `2026-10-22-esp-peer-groups`, `2026-10-22-weights-esp-spider`, `2026-10-22-onescore`. A sprint that runs tests 1 to 5 should amend those pages.
