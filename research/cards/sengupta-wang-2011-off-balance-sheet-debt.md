# Sengupta and Wang (2011), "Pricing of off-balance sheet debt"

Accounting and Finance 51, 787-808. DOI 10.1111/j.1467-629X.2010.00368.x. The user supplied the PDF. We read the method, variable definitions, and Tables 1, 3, 5, and 6.

## Claim
Rating agencies and new-issue bond buyers price footnoted operating leases, and they treat them like capital leases (abstract).

## Method
Ordered probit on S&P rating, and OLS on yield at issue, with `LEASEDEBT` as a present value of the footnote over assets (eqs. 1 to 3, Appendix II).

## Data
Hand-collected 10-K data, 1999 to 2001, firms with defined benefit plans. 1,712 firm-years, median rating BAA, median assets $3.4bn (Table 1). 173 new issues for yields. Firms rated below BA leave the sample (p. 797).

## Result
- Rating: leases -4.849 (t -9.44), debt -4.640 (t -16.16) (Table 3 col 2).
- Rating with balance sheet leases: off -4.506 (t -8.50), on -7.229 (t -3.22). The Wald test does not reject equality (Table 5).
- Yield: leases 2.209 (t 1.70), and 2.999 (t 2.19) with retirement debt (Table 6).

## Limits
- Three years, pension firms only. The sample leaves out deep HY.
- Levels at issue, 173 observations for yields. No returns.

## Section touched
`docs/methodology.md` Section 4.7.1.

## Use for the two clocks
**Source says:** footnoted leases carry a price. **Data says:** nothing yet. **We decide:** count it as a third level source for the lease sign in Method 2, and for nothing else.
