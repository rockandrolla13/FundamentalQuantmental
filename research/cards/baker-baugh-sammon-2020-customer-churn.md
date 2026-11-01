# Baker, Baugh, Sammon (2020), "Measuring Customer Churn and Interconnectedness"

NBER w27707. An open copy. An agent read it. We checked the churn equation against the text. We did not check the table values.

## Claim
Customer churn, read from card data, goes with higher volatility and lower profit (Table 5 and related).

## Method
Churn is half the sum of absolute changes in customer shares (eq. 1). Source: one card aggregator.

## Data
2.7m users, 2010 to 2015, 558 consumer-facing firms. Unreviewed working paper.

## Result
Total volatility on churn 0.0113 (se 0.002). Absolute log revenue change on churn 0.0860 (se 0.038). SG&A over sales is the proxy that the paper tests as poor in retail and restaurants.

## Limits
No bond, spread, or default test. Card data blocks the main measures. Large consumer firms. Tables 6 and 7 apply 2010-2015 churn back to 1970, which breaks our `available_at` rule.

## Section touched
`docs/methodology.md` Section 4.7.1, M1.12. `hy/clocks.py` `rev_abs_growth`, `sga_sales`.

## Use for the two clocks
**Source says:** customer capital differs by firm. **Data says:** nothing yet. **We decide:** do not buy card data on this evidence. Test the two filing proxies as report-only fields.
