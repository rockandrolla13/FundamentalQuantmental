# 60 Real Estate: 6010 Equity REITs, 6020 Real Estate Management and Development

Archetype (framework F2): A5 for REITs and real estate operators with a portfolio of leased property. A7 for a single property or a single-tenant holdco. A4 for homebuilders, developers and real estate services. Modifiers that often apply: M2 (office), M3 (one tenant or one operator above 20% of rent, common in health care and net lease REITs), M1 (sponsor-owned developers and services firms).
GICS industries covered: 601010 Diversified REITs, 601025 Industrial REITs, 601030 Hotel and Resort REITs, 601040 Office REITs, 601050 Health Care REITs, 601060 Residential REITs, 601070 Retail REITs, 601080 Specialized REITs, 602010 Real Estate Management and Development. Tower and data centre REITs also follow `5010-telecommunication-services.md`, sub-section "Towers and fibre infrastructure".

The sector fit gives real estate no score (SECTOR-models 3.1). This page sets the REIT rules a separate fit needs.

## Sources
| Source | Type | Date | Opened | Pages or sections used |
|---|---|---|---|---|
| S&P Global Ratings, "Key Credit Factors For The Real Estate Industry", https://www.maalot.co.il/Publications/MT20191210114512.PDF | rating agency criteria. Status not verified, may be superseded by the 2025 methodology. The 2025 article still refers to it (p. 253) | Feb. 26, 2018, republished Dec. 4, 2019 | yes | paras. 3-4 (scope), 10-14 (industry risk), 61-67 and Table 1 (ratios), 84-86 (secured debt notch) |
| S&P Global Ratings, "Sector-Specific Corporate Methodology". Public copy: South Dakota PUC docket EL26-003, Exhibit TDS-2, https://puc.sd.gov/commission/dockets/electric/2026/EL26-003/Vol2Section6/Exh2TStevens.pdf | rating agency criteria | July 7, 2025, republished Sept. 26, 2025 | yes | Section 19 Homebuilders And Real Estate Developers (exhibit pp. 103-109). Section 13 Digital Infrastructure (pp. 61-78). Appendix 3 SER tables (pp. 248-252) |
| S&P Global Ratings, "Standard & Poor's Assigns Industry Risk Assessments To 38 Nonfinancial Corporate Industries", https://maalot.co.il/publications/MT20150505165520.pdf | rating agency table | Nov. 20, 2013 | yes | Industry risk table, pp. 1-2 |
| Moody's, "REITs and Other Commercial Real Estate Firms" | rating agency methodology | Sept. 2022 version, no longer in effect | not opened | ratings.moodys.com returns a login page |
| Repo cards on leases: `lim-mann-mihov-2017-operating-leases-credit-capacity.md` and others | repo cards | | yes | Tenant side of leases only. No card covers REIT credit |

## Industry risk
- S&P cyclicality assessment: REITs "intermediate risk" (3) (2018, paras. 10-12. 2013 table, p. 2). Homebuilders and developers "high risk" (5) (2013 table, p. 1).
- S&P competitive risk and growth assessment: REITs "low risk" (2), industry risk "low" (2) (2018, para. 14). Homebuilders and developers "intermediate risk" (3), industry risk "moderately high" (4) (2013 table).

## EBITDA, leverage and coverage
- EBITDA definition: EBITDA from rents. Remove gains on property sales and fair value changes (F3 C4). Report Nareit funds from operations (FFO) beside it: net income without property sale gains and impairments, plus real estate depreciation. Report adjusted FFO (AFFO): FFO less recurring capex, tenant improvements, leasing commissions and straight-line rent.
- Leverage measure: `lev_gc_total` on rent EBITDA. Add `secured_share`, secured debt over undepreciated assets.
- Coverage measure: S&P fixed-charge coverage. `fcc = EBITDA / (interest incurred, with capitalised interest + scheduled principal amortisation + preferred dividends)` (2018, para. 66).
- Agency core ratios (2018, Table 1): debt to EBITDA, EBITDA to interest, fixed-charge coverage. Debt to EBITDA: 7.5x to 9.5x significant, 9.5x to 13x aggressive, above 13x highly leveraged. Fixed-charge coverage below 1.3x is highly leveraged.
- Agency supplementary ratios (2018, Table 1): FFO to debt, below 5% highly leveraged. Debt to debt plus equity on undepreciated book value, above 70% highly leveraged. Fair value basis, above 65% highly leveraged.
- Homebuilders and developers (Section 19): debt to debt plus equity as an extra supplementary ratio. Historical cost basis above 60% is highly leveraged. Fair value basis above 55% is highly leveraged. S&P treats percentage-of-completion revenue as less conservative.

## Drivers

### Equity REITs (A5)
| Driver | Formula from filings | Sign in spread | Source |
|---|---|---|---|
| `log_lev` | log of `(dlc + dltt) / oibdp`, clipped | + | agency weight: S&P 2018 Table 1, debt to EBITDA |
| `fcc` | Formula above | − | agency weight: S&P 2018 para. 66, emphasised for REITs with mortgages that amortise |
| `secured_share` | `dm / (at + dpact)`, secured debt over undepreciated assets | + | agency weight: S&P 2018 para. 85. Above 35% of undepreciated assets, or 40% of fair value, S&P rates unsecured debt one notch lower |
| `unenc_cover` | Unencumbered asset value over unsecured debt, from the bond covenant table | − | Our choice. Unsecured bonds recover only from this pool |
| `wale` | Weighted average lease term left, in years | − | Our choice. S&P Section 13 uses lease tenor for towers and data centres |
| `top_tenant_share` | Largest tenant or operator share of rent | + | agency weight: S&P 2018 para. 40, tenant concentration. M3 trigger |

### Homebuilders, developers and services (A4)
| Driver | Formula from filings | Sign in spread | Source |
|---|---|---|---|
| `log_lev` | log of `(dlc + dltt) / oibdp`, clipped | + | Our choice |
| `debt_cap` | `(dlc + dltt) / (dlc + dltt + seq)` | + | agency weight: S&P Section 19 table |
| `ebitda_cyc` | Minus the worst YoY EBITDA change over 10 years (F21) | + | agency weight: S&P "high" cyclicality, 2013 table |
| `land_months` | Owned and optioned lots over annual closings, in months | + | Our choice. Land is the largest cash call |

### Sub-industry notes
- Office: apply M2. Read the lease expiries for the next three years and the sublease space in each market.
- Hotels: rent is daily. Revenue per available room drives EBITDA (S&P 2018, para. 32). Use the A4 recession template on hotel revenue.
- Health care REITs: rent comes from operators. Read operator EBITDAR coverage of rent. A weak operator is the main risk (M3).
- Retail: read tenant sales per square foot and rent as a share of tenant sales (S&P 2018, para. 32).

## Downside case
1. Raise cap rates by the peak-to-trough rise of the 2008-2010 or 2022-2024 commercial property fall. Use a public property price index.
2. Cut net operating income (NOI) by the worst occupancy fall in the issuer's history for its property type.
3. Run the maturity wall with secured lenders who extend only at a lower loan-to-value. The gap is a refinance need (F4).
4. Under M3: remove the largest tenant at its next lease expiry. For an operator tenant, remove it now and cut the rent on a new lease by one third (Our choice).
5. Homebuilders: cut closings and price by the issuer's worst year in 2007-2011. Hold land payments that are already committed.

## Collateral and recovery
- Value the property at the stress cap rate on stress NOI, less sale cost (F7 A5).
- Secured mortgage debt sits at property entities, often without recourse. Unsecured REIT bonds recover only from unencumbered property and from equity in mortgaged property. Run the waterfall per property pool.
- Many REIT bonds sit at the operating partnership with a parent guarantee. Map the guarantor chain (F7.12).
- US REITs must pay out at least 90% of taxable income. Retained cash is small. Do not count dividend cuts as a large lever unless the REIT has a tax loss.
- Ground leases under the issuer's property are real property leases. The F5 rejection cap applies to them.
- When a tenant files, the landlord's claim for a rejected lease is capped (F5). Size the time to a new lease and rent from the market.

## Events and calendar
- Lease expiry schedule and tenant renewals.
- Property-level mortgage and CMBS maturities.
- Tenant and operator bankruptcy filings and lease decision deadlines.
- Monthly commercial property price index releases. Interest rate decisions.
- Homebuilders: monthly new home sales and housing starts. Mortgage rates.

## Instructions for the analyst
1. Frame the issuer as A5, A7 or A4. Apply M2 to office and M3 to concentrated tenant books.
2. Build rent EBITDA, FFO and AFFO. Remove sale gains and fair value changes.
3. Compute `lev_gc_total`, `fcc` and `secured_share`. Compare `secured_share` with the S&P 35% line.
4. Size liquidity to each mortgage maturity. Count unencumbered property that the issuer can pledge.
5. Map secured debt per property pool and the unsecured guarantor chain in the claims view.
6. Run the cap rate, NOI and tenant-loss cases.
7. Value property at the stress cap rate. Run the waterfall per pool.
8. Gate the memo under F9. Report FFO to debt beside `lev_gc_total`.

## Open questions
- Does `secured_share` widen HY REIT unsecured spreads at the S&P 35% line? Test: an event study of unsecured spreads when issuers cross the line.
- Should GICS 60 get a sector fit with `fcc` and `secured_share`? Test: fit a REIT-only model and compare its out-of-sample rank IC with the pooled model.
- Which source gives REIT recovery rates by property type? Not found. Add a card before the recovery rules change.
