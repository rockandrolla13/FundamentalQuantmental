# 4510 Software and Services

Archetype (framework F2): A6 for software. A4 for IT consulting and services, because client IT budgets move with the cycle and labour is the main cost. A5 for capital-intensive IT outsourcing. Modifiers that often apply: M1 (most HY software issuers are sponsor-owned), M3 (one client above 20% of revenue in IT services).
GICS industries covered: 451020 IT Services, 451030 Software. Transaction and payment processors moved to GICS 4020 in 2023. They use the A6 rules of this page (see `40-financials.md`).

## Sources
| Source | Type | Date | Opened | Pages or sections used |
|---|---|---|---|---|
| S&P Global Ratings, "Sector-Specific Corporate Methodology". Public copy: South Dakota PUC docket EL26-003, Exhibit TDS-2, https://puc.sd.gov/commission/dockets/electric/2026/EL26-003/Vol2Section6/Exh2TStevens.pdf | rating agency criteria | July 7, 2025, republished Sept. 26, 2025 | yes | Section 34 Technology Software And Services (exhibit pp. 185-188). Appendix 3 margin, return and SER tables (pp. 244-252) |
| S&P Global Ratings, "Key Credit Factors For The Technology Software And Services Industry" | rating agency criteria. Status not verified, may be superseded by the 2025 methodology | unknown | not opened | No public copy found |
| S&P Global Ratings, "Standard & Poor's Assigns Industry Risk Assessments To 38 Nonfinancial Corporate Industries", https://maalot.co.il/publications/MT20150505165520.pdf | rating agency table | Nov. 20, 2013 | yes | Industry risk table, p. 2 |
| Moody's, software methodology | rating agency methodology | unknown | not opened | ratings.moodys.com returns a login page |
| McCarthy, Fader and Hardie (2017), card `mccarthy-fader-hardie-2017-subscription-valuation-public-data.md` | peer-reviewed journal, repo card | 2017 | yes | Retention fit from public subscriber counts |
| Fader and Hardie (2010), card `fader-hardie-2010-contractual-customer-base-heterogeneity.md` | peer-reviewed journal, repo card | 2010 | yes | One retention rate undervalues a customer base by 25% to 50% (p. 91) |
| Prakash and Sinha (2009 draft), card `prakash-sinha-2009-deferred-revenues-matching.md` | working paper, repo card | 2009 | yes | Change in current deferred revenue predicts next-year margin (p. 18) |
| Mann (2018) and Ewens, Peters and Wang (2025), in `research/notes/sector-sources-shortlist.md` | peer-reviewed journals | 2018, 2025 | not opened | Listed as candidates for patent collateral and intangible value |

## Industry risk
- S&P cyclicality assessment: "intermediate risk" (3) (2013 table, p. 2).
- S&P competitive risk and growth assessment: "intermediate risk" (3). Industry risk "intermediate" (3) (2013 table). These are 2013 values. We did not find a later public list.

## EBITDA, leverage and coverage
- EBITDA definition: cash EBITDA after capitalised development (F2 A6). Subtract capitalised software cost (`capsft` additions) from EBITDA. Do not add back stock compensation (F3 C6). Flag a release of old deferred revenue under EQ11.
- Leverage measure: `lev_gc_total` on cash EBITDA (F5). Show debt to annual recurring revenue (ARR) beside it when the issuer discloses ARR. Some private credit documents test leverage on ARR. Treat that as the covenant number, not the analyst number (F3).
- Coverage measure: `coverage` on cash EBITDA (F5).
- Agency supplementary ratios (Section 34, exhibit p. 188):
  - Core ratios "intermediate" or stronger: FOCF to debt or CFO to debt.
  - Core ratios "significant" or weaker: FOCF to debt or EBITDA to interest.
  - S&P usually assesses cash flow volatility as "stable" for software and transaction processors. A vendor that chiefly sells perpetual licences can be "volatile".
- EBITDA margin bands (Appendix 3): enterprise and consumer software below 25% below average, 25% to 30% average, above 30% above average. Commercial IT services: below 10%, 10% to 15%, above 15%. Transaction processors: below 20%, 20% to 30%, above 30%.

## Drivers

### Software (A6)
| Driver | Formula from filings | Sign in spread | Source |
|---|---|---|---|
| `log_lev` | log of `(dlc + dltt) / (oibdp − capsft)`, clipped | + | Our choice. Cash EBITDA per F2 A6 |
| `fcf_debt` | `(oancf − capx − capsft) / (dlc + dltt)` | − | Our choice |
| `recurring_share` | Subscription plus maintenance revenue over total revenue, from the revenue note | − | agency weight: S&P Section 34. Above 70% supports strong. Below 50% points to weak |
| `net_retention` | Disclosed dollar-based net retention rate | − | Our choice (F2 A6). Fader and Hardie (2010) and McCarthy et al. (2017) value retention. Equity value only, no credit test |
| `delta_drc` | Change in current deferred revenue `drc` over average assets | − | tested on equity returns: Prakash and Sinha (2009 draft), pp. 18, 22. Not tested on spreads |
| `sbc_rev` | Stock compensation `stkco` over `sale` | + | Our choice. Cash cost hidden from company EBITDA |

### IT services and outsourcing (A4, A5)
| Driver | Formula from filings | Sign in spread | Source |
|---|---|---|---|
| `log_lev` | log of `(dlc + dltt) / oibdp`, clipped | + | Our choice |
| `margin_trend` | 8-quarter slope t-statistic of `oibdpq / saleq` | − | Our choice |
| `book_to_bill` | New contract value over revenue, from the filing | − | Our choice (F8 A4) |
| `top_client_share` | Largest client's share of revenue | + | Our choice. M3 trigger |

## Downside case
1. Software: cut net retention to the issuer's worst 4-quarter value. Without history, cut it by 10 points (Our choice).
2. Software: cut new orders by half for four quarters. Hold the cost base for two quarters, then cut it. Cost cuts reverse in year two (F2 A6).
3. Software: shift perpetual licence sales into subscriptions. The cash dip lasts as long as the average contract.
4. IT services: apply the A4 recession template to discretionary project revenue. Hold managed-service revenue at the contract floor.
5. All: add a secular case for products that new technology can replace. Treat that case under M2 if revenue falls for two years.

## Collateral and recovery
- Liquidation value is small (F2 A6, F7.5 intangibles band 0% to 15%). Value the issuer as a going concern on recurring revenue.
- Customer prepayments and deferred revenue become claims when service stops (F2 A6). Customers can also stop payment and move. Model a faster churn after a filing.
- Intellectual property can move to an unrestricted subsidiary. Score the F7 liability management line for IP transfers first.
- Source code escrow can let a customer leave the estate with the code. Read the escrow terms of the top contracts.
- Recurring revenue loans often carry a step-down from ARR leverage to EBITDA leverage. Read the conversion date in the credit agreement.

## Events and calendar
- Quarterly ARR, net retention and remaining performance obligation (RPO) disclosures.
- Annual price increase dates and the renewal season of the main contracts.
- Sponsor actions: dividend recaps, add-on acquisitions, debt-funded buyouts (F2 M1).
- PIK toggle elections and ARR-to-EBITDA covenant conversion dates.
- Large vendor product launches that can replace the issuer's product.

## Instructions for the analyst
1. Frame the issuer as A6, A4 or A5. Apply M1 when a sponsor owns it.
2. Build cash EBITDA after capitalised software. Keep stock compensation as a cost.
3. Compute `lev_gc_total` on cash EBITDA. Show debt to ARR beside it.
4. Read the IP transfer and unrestricted subsidiary baskets before you score liquidity.
5. Size deferred revenue and prepayments as claims in the claims view.
6. Run the retention, orders and secular cases. Reverse the cost cuts in year two.
7. Value the issuer on recurring revenue and on cash EBITDA. Use the going-concern basis.
8. Gate the memo under F9. Report `recurring_share` against the S&P 70% and 50% lines.

## Open questions
- Does `recurring_share` or `net_retention` explain HY software spreads after leverage? No repo source tests it (shortlist gap 3). Test: add both to the GICS 45 sector fit and keep a driver only if its sign holds.
- What do software creditors recover in default? No repo source. Open Ewens, Peters and Wang (2025) for intangible value, then build a recovery sample.
- Does `delta_drc` predict bond returns as it predicts stock returns? Test M1.10 of the clocks plan on bonds.
