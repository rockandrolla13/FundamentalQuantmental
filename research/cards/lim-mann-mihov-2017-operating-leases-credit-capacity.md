# Lim, Mann, Mihov (2017), "Do operating leases expand credit capacity? Evidence from borrowing costs and credit ratings"

Journal of Corporate Finance 42, 100-114. DOI 10.1016/j.jcorpfin.2016.10.015. The user supplied the PDF. An agent read it, and we checked Table 3 and the lease definitions against the text.

## Claim
Leases carry a lower price than debt per dollar under some lease measures, so leases can expand credit capacity (Tables 2, 3).

## Method
Three lease values: S&P present value, Moody's higher of that value and 8 x rent, and a perpetuity form (p. 102). New bond spread, loan spread, and rating on debt and leases over assets.

## Data
Compustat, SIC 2000 to 5999, 1995 to 2011, 31,339 firm-years. 3,399 bonds in Table 3.

## Result
- Bonds: debt 2.051 (t 14.19), S&P leases 1.804 (t 9.02), equality F 0.95 (p 0.329).
- Bonds: debt 2.050 (t 14.26), Moody's leases 1.228 (t 10.65), F 19.11 (p 0.000).
- Loans: debt 146.936 (t 31.30), S&P leases 38.029 (t 5.03), F 165.55 (p 0.000).

## Limits
- Spreads at issue. No seasoned bonds, no returns, no HY-only regression.
- Moody's lease values run larger, so its lower slope may be partly scale (our reading).
- The text differs on whether assets include the lease value.

## Section touched
`docs/methodology.md` Section 4.7.1. `hy/clocks.py` `sp_present_value`, `moodys_lease`.

## Use for the two clocks
**Source says:** the verdict depends on the lease measure, and in bonds the contractual measure prices near debt. **Data says:** nothing yet. **We decide:** use the contractual measure as `amt_lease_after` input before ASC 842, and report the Moody's floor beside it.
