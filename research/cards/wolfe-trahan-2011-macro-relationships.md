# Source: Wolfe Trahan macro relationships, 2011 notes

Data: `research/wolfe-trahan-2011-relationships.csv`, 156 source rows, 159 rows after tags. Origin: Google Sheet "Macro Indicators & Relationships_Master List", tab "WT Relationships". The owner of this repo wrote the sheet from 25 Wolfe Trahan strategy notes, May to November 2011. The notes themselves are not in Drive or Gmail (search on 2026-10-23).

## Claim
Each row pairs two series and states how one leads or tracks the other. Two claims recur. Inflation (prices paid, CPI, oil) leads the ISM index by six to nine months. The ISM index leads earnings revisions, valuation, credit spreads, and sector relative returns.

## Method
The source shows each pair on a chart. "Advanced nM" means that the analyst shifted series 1 forward by n months, so series 1 leads. "Inverted" means that the analyst flipped the sign. The notes give no coefficients, no sample periods, and no out-of-sample tests.

## Data
Columns: `sheet_row` (the row in the sheet tab), `sector`, `wt_note`, `note_date`, `series_1`, `series_2`, `relationship`. The comments are verbatim, typos included. The sheet has no sector column. I assigned the `sector` tag from the series in each row. Three rows carry two tags: two rows are Financials and Housing, one row is Energy and Consumer Discretionary.

| Sector | Rows |
|---|---|
| Industrials and Transports | 14 (12 are freight data sources) |
| Financials | 13 |
| Cross-sector rotation (cyclicals vs defensives) | 11 |
| Housing and Real Estate | 8 |
| Consumer Discretionary | 4 |
| Utilities, Materials | 3 each |
| Energy, Information Technology | 2 each |
| Consumer Staples, Health Care, Telecoms | 1 each |
| Macro and market-wide (no sector) | 96 |

## Result
For this project the useful rows are the candidate leads into the macro vector `m_t` and the sector drivers:
- ISM prices paid, advanced 6 to 9 months and inverted, leads the ISM index and regional Fed indices.
- The ISM index tracks Baa credit spreads, inverted.
- Bank lending standards, advanced 2 years, lead core CPI.
- The real yield curve (10Y minus CPI) replaces the 10Y minus Fed funds curve at the zero bound.
- NAHB and new home sales lead bank relative returns.

## Limits
- Sell-side strategy notes, not peer reviewed. They show charts only.
- One regime: the 2011 zero-bound period. Several rows say that a pre-2008 relationship broke.
- Sector coverage is thin outside Financials and Housing. Most of those rows come from one note, "Bullish case for financials" (17 Nov 2011).
- The rows forecast equity returns and macro series, not HY spreads or defaults.

## Decision
Use the rows as a list of candidate leads only. The test plan is `docs/decisions/2026-10-24-wt-relationship-tests.md`. Test each candidate lead on the HY panel before it enters `m_t` or a `β_sector` regression. A candidate passes when it adds out-of-sample information over `hy_oas`, `sloos_tightening`, `default_rate_fcst`, and `pmi`.

Section touched: methodology 3.6, 5.2

## Test results
- H1 (prices paid → lower margins and sales): failed on 1994–2026 Compustat data, all three sectors. After a prices-paid jump, EBITDA and sales usually rose. Details: `docs/decisions/2026-10-24-wt-relationship-tests.md`, Phase 1 results.
- All claims, firm level (17,767 firms, equal weight): 3 of 87 tests pass the pre-set rule; 1 survives Holm across all tests (H1c: input-price jumps raise high-leverage industrials' cost ratio 0.2 points of sales). H2 and H3 hold in direction only. Write-up: `docs/writeup/wt_relationships.pdf`.
