# 5020 Media and Entertainment

Archetype (framework F2): one primary per sub-industry, because the drivers differ.
- A5 for cable and satellite operators.
- A4 for ad-funded businesses: local TV, radio, outdoor, ad agencies.
- A6 for subscription content, interactive media and data publishers.
- A1 for cinema chains.

Modifiers that often apply: M2 (print, radio, linear TV networks, satellite TV), M1 (sponsor-owned local TV, radio, outdoor and data publishers), M3 (one network affiliation or one sports right above 20% of revenue).
GICS industries covered: 502010 Media (Advertising, Broadcasting, Cable and Satellite, Publishing), 502020 Entertainment (Movies and Entertainment, Interactive Home Entertainment), 502030 Interactive Media and Services.

## Sources
| Source | Type | Date | Opened | Pages or sections used |
|---|---|---|---|---|
| S&P Global Ratings, "Sector-Specific Corporate Methodology". Public copy: South Dakota PUC docket EL26-003, Exhibit TDS-2, https://puc.sd.gov/commission/dockets/electric/2026/EL26-003/Vol2Section6/Exh2TStevens.pdf | rating agency criteria | July 7, 2025, republished Sept. 26, 2025 | yes | Section 21 Media And Entertainment (exhibit pp. 117-124). Section 35 Telecommunications for cable (pp. 189-193). Appendix 3 margin and SER tables (pp. 244-252) |
| S&P Global Ratings, "Key Credit Factors For The Media And Entertainment Industry" | rating agency criteria. Status not verified, may be superseded by the 2025 methodology | unknown | not opened | No public copy found |
| S&P Global Ratings, "Standard & Poor's Assigns Industry Risk Assessments To 38 Nonfinancial Corporate Industries", https://maalot.co.il/publications/MT20150505165520.pdf | rating agency table | Nov. 20, 2013 | yes | Industry risk table, p. 2 |
| Moody's, media methodology | rating agency methodology | unknown | not opened | ratings.moodys.com returns a login page |
| McCarthy, Fader and Hardie (2017), card `mccarthy-fader-hardie-2017-subscription-valuation-public-data.md` | peer-reviewed journal, repo card | 2017 | yes | Retention fit from public subscriber counts. Satellite TV and satellite radio cases |

## Industry risk
- S&P cyclicality assessment: media and entertainment "intermediate risk" (3). Telecommunications and cable "low risk" (2) (2013 table, p. 2).
- S&P competitive risk and growth assessment: media and entertainment "intermediate risk" (3), industry risk "intermediate" (3). Telecommunications and cable "intermediate risk" (3), industry risk "intermediate" (3) (2013 table). These are 2013 values.

## EBITDA, leverage and coverage
- EBITDA definition by sub-industry:
  - Content owners: subtract cash content spend less content amortisation from EBITDA (Our choice). S&P notes that expense recognition varies widely in this sector (Section 21, exhibit p. 124).
  - Local TV: use average EBITDA over the last eight quarters. This removes the even-year political ad peak. S&P uses debt to eight-quarter average EBITDA as a supplementary ratio for US local TV, with the core thresholds (Section 21).
  - Cable: EBITDA less capex (F2 A5).
  - Outdoor and cinemas: EBITDAR, because site and screen leases are large (F2 A1).
- Leverage measure: `lev_gc_total` for most sub-industries. `lev_lease_adj` for outdoor and cinemas (F5).
- Coverage measure: `coverage` (F5). `fccr` for outdoor and cinemas.
- Agency supplementary ratios: FOCF to debt across the sector, for comparability (Section 21). FOCF to debt first for cable (Section 35).
- Cash flow volatility (Section 21): video game developers, newspapers, magazines and printers are usually "volatile". Pure film producers are "highly volatile". E-commerce and ad-funded online platforms are "volatile" or "highly volatile".
- EBITDA margin bands (Appendix 3), below average then above average:
  - Local and cable TV and streaming: below 20%, above 35%.
  - Broadcast networks, radio and music: below 15%, above 30%.
  - Outdoor: below 20%, above 40%. Cinema chains: below 30%, above 40%.
  - Printing, newspapers and magazines: below 15% is below average. No above-average band.
  - Film and TV production: below 12% is below average. No above-average band.

## Drivers
| Driver | Formula from filings | Sign in spread | Source |
|---|---|---|---|
| `log_lev` | log of `(dlc + dltt) / oibdp`, clipped. Local TV uses 8-quarter average EBITDA | + | Our choice. S&P Section 21 for the local TV average (agency weight) |
| `fcf_debt` | `(oancf − capx) / (dlc + dltt)` | − | agency weight: S&P Section 21, FOCF to debt for comparability |
| `mat_wall` | `(dd1 + dd2) / (dlc + dltt)` | + | Our choice |
| `ad_share` | Ad revenue over total revenue, from the revenue note | + | Our choice. Ad revenue moves with the cycle |
| `sub_trend` | 8-quarter slope t-statistic of subscribers (video, broadband or paid users) | − | Our choice. McCarthy et al. (2017) fit retention from such counts. Equity value only |
| `content_gap` | (Cash content spend − content amortisation) over EBITDA, from the cash flow statement | + | Our choice |

### Cable and satellite (A5)
- Broadband carries the value. Video subscribers fall each year. Apply M2 to video revenue, not to broadband.
- Fixed wireless and fibre overbuilders compete for broadband. Track broadband net adds and the share of homes with a fibre rival.
- Programme cost per video subscriber rises faster than video price. Read the margin of the video product alone.

### Local TV and radio (A4, often M2)
- Retransmission fees from pay-TV distributors are the stable part. S&P views retransmission above 30% of broadcast revenue as strong and below 15% as weak (Section 21).
- Network affiliation fees paid to the networks reduce the net retransmission margin. Read the net figure.
- Political ad revenue peaks in even years in the US. Never annualise an even-year quarter.

### Content, streaming and interactive media (A6)
- Subscriber retention and content spend set cash flow. A hit-driven slate makes cash flow lumpy.
- Sports rights are long contracts with fixed cost. Treat a lost right as an M3 event.

### Outdoor, cinemas and ad agencies
- Outdoor and cinemas follow A1 lease rules. Site leases under billboards are real property leases.
- Ad agencies are asset-light. Client wins and losses drive revenue. Apply M3 to the largest client.

## Downside case
1. Ad-funded: cut ad revenue by the issuer's worst peak-to-trough fall, from 2008-2009 or 2020. Hold retransmission revenue.
2. Local TV: run the case in an odd year. Remove political ad revenue.
3. Cable: double the 3-year rate of broadband net loss (Our choice). Extend the video decline at its 3-year rate.
4. Content: delay the slate by one quarter. Hold the cash content spend.
5. Under M2: shorten the terminal value (F7.4) and treat restructuring as recurrent.

## Collateral and recovery
- US broadcast licences cannot carry a direct lien. Lenders take liens on the stock of the licence subsidiary and on sale proceeds. Read where the licences sit.
- Content and music libraries hold value. Value them as a DCF of library cash flows, not at book value.
- Talent and sports rights contracts are executory. The estate can assume or reject them. Model a rejection claim at contract damages less mitigation.
- Guild and union plans can create multiemployer withdrawal liability (F5 pensions).
- Cable plant: appraised value per home passed (F7 A5).

## Events and calendar
- Retransmission and carriage renewals. Many contracts end at a year end. Read the renewal schedule in the 10-K.
- US election years and the even-year political ad cycle.
- The spring upfront ad market and quarterly ad sales releases.
- Sports rights renewals and league media deals.
- Broadcast ownership rule changes and licence renewals.
- Quarterly subscriber disclosures for cable and subscription content.

## Instructions for the analyst
1. Frame each segment by its sub-industry archetype. Apply M2 where volume falls for five years without a cause in the cycle.
2. Build analyst EBITDA. Use the 8-quarter average for local TV and subtract the content cash gap for content owners.
3. Compute `lev_gc_total`, or `lev_lease_adj` for outdoor and cinemas.
4. Size liquidity through the next odd year for local TV, and through the slate gap for content.
5. Locate the licences and libraries. Map the liens in the claims view.
6. Run the ad, subscriber and content-delay cases.
7. Value library assets by DCF. Value operators at the trough multiple.
8. Gate the memo under F9. Report the S&P margin band for the subsector.

## Open questions
- Does `ad_share` widen spreads in recessions only, or in all phases? Test: fit the GICS 50 sector model by F6 cycle phase.
- Does `content_gap` predict downgrades before leverage rises? No repo source. Test: AUC for a 2-year downgrade with and without it.
- What do library assets recover in default? No repo source. Build a sample of library sales by distressed sellers.
