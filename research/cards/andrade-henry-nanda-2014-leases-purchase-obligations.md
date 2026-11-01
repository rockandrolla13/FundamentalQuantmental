# Andrade, Henry, Nanda (March 2014 draft), "The Impact of Operating Leases and Purchase Obligations on Credit Market Prices"

SSRN 1941896. The copy is a draft dated March 2014, and our records list the SSRN entry as 2011. The user supplied the PDF. We read pp. 1-27, Tables 3 to 5, and Appendix B.

## Claim
CDS spreads rise with leases and with purchase obligations, and leases cost more per unit of leverage (pp. 2-3). The authors conjecture that essential contracts are assumed in bankruptcy, and so rank ahead of unsecured debt in effect (pp. 3-4).

## Method
Log 5-year CDS on three leverage parts over one denominator, plus asset volatility, log assets, and strategic controls, with quarter effects and firm clusters (pp. 10, 16-17, 19). Obligations past year 5 run at a constant amount for the closest integer of thereafter over year 5 (p. 16). The discount rate is the 5-year swap rate less 10 bp (p. 16). The authors code each firm's purchase text as high, moderate, or low essentiality by judgement (p. 18, footnote 11).

## Data
Markit, Compustat, Moody's KMV, Thomson, and hand-collected 10-K text. 372 firms, 2,846 firm-quarters, 2004Q1 to 2006Q1 (pp. 14-16). Median assets are $8.6bn (p. 17). Speculative grade has 541 observations (p. 22, footnote 13).

## Result
- Table 3 col 3: debt 3.25 (t 9.35), leases 2.68 (t 5.15), purchases 0.90 (t 3.00). Leases less debt -0.57 (t -1.03). Leases less purchases 1.78 (t 3.11).
- At a 60 bp spread, 10 points of leverage adds 18 bp for leases, 23 bp for debt, and 6 bp for purchases (p. 20).
- Table 4 col 3, speculative grade: debt 3.02 (t 4.47), leases 2.76 (t 2.85), purchases 1.67 (t 2.10). The source fails to reject equal lease and purchase effects here (p. 22).
- Table 5 col 2: purchases 0.61 (t 1.86), non-essential term -0.56 (t -1.25), essential term 1.89 (t 2.91). Essential sum 2.50 against leases 2.58. Non-essential sum 0.05 (p. 25).
- Cases, Appendix A and p. 5: Bally assumed 330 leases and rejected 70, and it assumed 10 purchase contracts and rejected 540.

## Limits
- CDS, not bonds. Levels, not returns. Two years of data, before 2008.
- Large firms. Essentiality has no speculative grade split.
- Hand coding by the authors. The coded data is not in our file.
- Assumption is a conjecture. No recovery test exists in the draft.
- Text errors: p. 19 says 2003-2005, and p. 23 labels both essentiality distributions speculative grade.

## Section touched
`docs/methodology.md` Section 4.7.1. `docs/framework.md` F5. `hy/clocks.py` `purchase_essentiality`, `executory_leverage`, `sp_present_value`.

## Use for the two clocks
**Source says:** purchases are not one claim. **Data says:** nothing yet. **We decide:** report purchases by class, keep them at face in E5, and test the split in HY with M1.3b.
