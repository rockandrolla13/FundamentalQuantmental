# Internal specification draft (2012), "European Single Names – Framework/Template for Fundamental Analysis"

Version 080212, no author, about 3,000 words, 15 PDF pages. We read the PDF and the Word copy in the user's folder `Quant Credit/Screening Models/`. The two copies hold the same text. Page numbers are PDF pages. Evidence class: an internal practitioner draft. It is not peer-reviewed and reports no test. Many sections are empty placeholders.

## Claim
A fundamental screen for European corporate credit can run in five steps: build the data set, compute ratios, compare 5-year CDS spreads with fundamentals inside a sector ("static" relative value), run stress tests and model inferences ("dynamic" relative value), and write reports (contents, p. 1).

## Method
1. **Spread per turn of leverage (p. 9).** SPL = 5Y CDS spread divided by net debt over EBITDA. A name's predicted spread is its leverage times the sector average SPL with the name left out. Actual minus predicted marks it cheap or expensive. The spec repeats this with forecast leverage.
2. **Spread against interest coverage (pp. 9-10).** The same frame with EBIT over interest as the denominator.
3. **Rating buckets (p. 11).** A table maps S&P, Moody's and Fitch ratings to 19 numbered buckets.
4. **Cyclicality against liquidity (p. 12).** The EBITDA decline over two years that forces a company to refinance, from cash, LTM EBITDA, interest and capex.
5. **Ratings drift screen (p. 13).** Regress the mapped rating on fundamentals by sector. Compare the model rating with the actual rating. Two trade templates follow:
   - The model calls an upgrade or a downgrade, the agency has no watch or outlook, and the market already prices some rating change. The spec measures that with Moody's bond market implied ratings.
   - The model calls a change, and the market prices none.

## Data
None. The spec names sources (Bloomberg, Capital IQ, CS Holt, analyst reports) and history lengths: 3 years of accounts, 7 to 10 years for EBITDA, net debt and free cash flow (p. 2).

## Result
None. The spec reports no output. Its Table 9 is a stylised example with invented numbers (p. 9).

## Limits
1. No test, no sample and no author.
2. Steps 3E, 3F, 4A, 4D and all of Step 5 are empty (pp. 10-14).
3. The rating model was "derived for US issuers". The spec asks, without an answer, what changes for European names (p. 13).
4. The spec prices CDS. This repository prices US high yield bonds.

## Section touched
1. **4.5.1 (new).** The two drift templates and the idea of a market-implied rating come from p. 13. We replace the Moody's series with our own cross-section estimate. The cut-offs are Our choice.
2. **7.2 and the peer model.** SPL with the name left out (p. 9) matches `hy/peers.py`. No change.
3. **F21.** Step 4B (p. 12) is already the source of the refinancing headroom factor. No change.
4. **Section 5.** The spec asks whether to take the median of each analyst's leverage or median debt over median EBITDA (p. 3). It gives no answer, and neither do we. Open item.
