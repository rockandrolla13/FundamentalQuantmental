# Prakash and Sinha (August 2009 draft), "Deferred Revenues and the Matching of Revenues and Expenses"

Working draft. The user supplied the PDF. We read pp. 1-32. We did not read the tables at the end, so numbers come from the text. We did not check for a journal version.

## Claim
A rise in current deferred revenue depresses margin now and lifts it next year, because period costs do not wait with the revenue. Markets and analysts underweight this (abstract, pp. 9-11).

## Method
`delta_drc` is the annual change in current deferred revenue over average assets (p. 13). Next-year margin on `delta_drc` and controls (eq. 1). The interaction with margin tests persistence (eq. 2). Decile rank on next-year size-adjusted stock return (eqs. 3, 4), with portfolios formed 3 months after year end (p. 21).

## Data
Compustat XPF and CRSP, 2002 to 2007. 6,684 firm-years, 1,999 firms (p. 13). No financials or utilities, sales of at least $5m, no negative equity. Over 75% NASDAQ (p. 15). Software is about 20% (p. 17). Period costs are about 47% of operating costs (p. 15).

## Result
- Margin: 2.709 (t 5.89) with all controls (p. 18). On margin change 2.139 (t 6.79) (p. 19).
- Persistence: interaction -3.846 (t 5.24 as printed) (p. 20).
- Stock return: 0.080 (t 3.59) alone, 0.090 (t 3.91) with controls (p. 22). Decile hedge 8.4% (t 2.26) (p. 30).
- The change is mispriced, and the level is not (p. 29).
- Analysts: `delta_drc` on sales forecast error 0.043 (t 3.04), on EPS forecast error 0.020 (t 2.80) (p. 24).

## Limits
- Stock returns, not bonds. Six years, one regime, before ASC 606.
- No negative equity firms, which leaves out some HY issuers.
- Mostly small technology firms. The field is sparse outside software and health.
- Compustat shows few non-zero balances before 2001 (p. 1, footnote 1).
- Pooled OLS with firm clusters, and year and industry effects.

## Section touched
`docs/methodology.md` Section 4.7.1, M1.10. `docs/framework.md` EQ11. `hy/clocks.py` `delta_drc`.

## Use for the two clocks
**Source says:** contracted cash already collected moves next-year margin. **Data says:** nothing yet. **We decide:** add `delta_drc` as a revenue clock field that can reach four windows, run M1.10, and flag falls in the memo as EQ11.
