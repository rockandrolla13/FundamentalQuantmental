# Oliveira, Kadapakkam, Beyhaghi (2017), "Effects of customer financial distress on supplier capital structure"

Journal of Corporate Finance 42, 131-149. DOI 10.1016/j.jcorpfin.2016.11.009. The user supplied the PDF. An agent read it. We checked the customer data rules against the text. We did not check the table values.

## Claim
Suppliers raise leverage before a major customer files, when the customer later reemerges (Table 4).

## Method
Pair-year panel of suppliers and customers that file Chapter 11. A customer is at least 10% of sales (p. 135). Pairs with 1 or 2 years of match leave the sample (p. 135).

## Data
163 pairs, 1,664 pair-years, 1980 to 2013.

## Result
Before filing, reemerged customers: 0.0547 (t 3.232) on leverage. Liquidated customers: -0.0209 (t -0.573). Dropped names: the name absence means a terminated relationship or sales under 10% (p. 146).

## Limits
No bonds, spreads, returns, or defaults. The main variable needs the future filing date. Names are voluntary since 1998 (p. 135).

## Section touched
`docs/methodology.md` Section 4.7.1, M1.11. `hy/clocks.py` `customer_persistence`.

## Use for the two clocks
**Source says:** how to define a durable link. **Data says:** nothing yet. **We decide:** take the field rules only. Reading a dropped name as non-renewal is our extension.
