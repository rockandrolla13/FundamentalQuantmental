# 4530 Semiconductors and Semiconductor Equipment

Archetype (framework F2): A4 for chip designers, analog and power chip makers, and equipment makers. A5 for issuers that own fabs, because capex runs above 15% of sales. Modifiers that often apply: M3 (one customer above 20% of revenue), M1 (sponsor-owned component and equipment makers).
GICS industries covered: 453010 Semiconductors and Semiconductor Equipment (45301010 Semiconductor Materials and Equipment, 45301020 Semiconductors).

## Sources
| Source | Type | Date | Opened | Pages or sections used |
|---|---|---|---|---|
| S&P Global Ratings, "Sector-Specific Corporate Methodology". Public copy: South Dakota PUC docket EL26-003, Exhibit TDS-2, https://puc.sd.gov/commission/dockets/electric/2026/EL26-003/Vol2Section6/Exh2TStevens.pdf | rating agency criteria | July 7, 2025, republished Sept. 26, 2025 | yes | Section 33 Technology Hardware And Semiconductors (exhibit pp. 181-184). Appendix 3 margin, return and SER tables (pp. 244-252) |
| S&P Global Ratings, "Key Credit Factors For The Technology Hardware And Semiconductors Industry" | rating agency criteria. Status not verified, may be superseded by the 2025 methodology | unknown | not opened | No public copy found |
| S&P Global Ratings, "Standard & Poor's Assigns Industry Risk Assessments To 38 Nonfinancial Corporate Industries", https://maalot.co.il/publications/MT20150505165520.pdf | rating agency table | Nov. 20, 2013 | yes | Industry risk table, p. 1 |
| Moody's, semiconductor methodology | rating agency methodology | unknown | not opened | ratings.moodys.com returns a login page |
| Repo cards | none | | | No card in `research/cards` covers semiconductor credit |

## Industry risk
- S&P cyclicality assessment: "moderately high risk" (4), for hardware and semiconductors together (2013 table, p. 1).
- S&P competitive risk and growth assessment: "moderately high risk" (4). Industry risk "moderately high" (4) (2013 table). These are 2013 values. We did not find a later public list.

## EBITDA, leverage and coverage
- EBITDA definition: analyst EBITDA under F3. Read government chip grants as capex offsets, not as EBITDA. Treat inventory write-downs as recurrent when they appear in two cycles.
- Leverage measure: `lev_gc_total` (F5). For fab owners, also compute EBITDA less maintenance capex over debt (F2 A5).
- Coverage measure: `coverage` (F5). It already subtracts capex.
- Agency supplementary ratios: as for hardware (Section 33). FOCF to debt when the core ratios read "intermediate" or stronger. EBITDA to interest or FOCF to debt when they read "significant" or weaker.
- Cash flow volatility (Section 33): S&P assesses equipment makers as "highly volatile". It often assesses memory makers as "highly volatile" and analog makers as "stable".
- EBITDA margin bands (Appendix 3): semiconductors below 20% below average, 20% to 30% average, above 30% above average. Equipment makers: below 15%, 15% to 25%, above 25%.

## Drivers
| Driver | Formula from filings | Sign in spread | Source |
|---|---|---|---|
| `log_lev` | log of `(dlc + dltt) / oibdp`, clipped | + | Our choice |
| `ebitda_cyc` | Minus the worst YoY EBITDA change over 10 years (F21) | + | agency weight: S&P Section 33 volatility classes |
| `capex_int` | `capx / sale` | + | Our choice. Fab owners (A5) |
| `inv_days_chg` | Change in `invt / cogs × 365` over 4 quarters | + | Our choice. EQ2. Add channel inventory when the issuer discloses it |
| `memory_share` | Memory share of revenue, from the segment note | + | agency weight: S&P Section 33, memory "highly volatile" |
| `mat_wall` | `(dd1 + dd2) / (dlc + dltt)` | + | agency weight: S&P Section 33, default at a maturity during or after a downturn |

### Sub-industry notes
- Memory: price per bit sets the cycle. Revenue can fall faster than volume. Use the memory price case first.
- Analog, power and microcontrollers: long product lives and many customers. Inventory in the channel leads the cycle by two to four quarters (Our choice).
- Equipment makers: customer capex sets orders. Orders lead revenue. Use `book_to_bill` from F8.
- Fab owners: capex is large and lumpy. Read the maintenance share of capex in the filing (F4 `capex_flex`).

## Downside case
1. Take the worst peak-to-trough revenue of the last two cycles for the issuer's product mix. Use the 2008-2009, 2019 and 2022-2023 downturns as templates.
2. Memory: cut the price per bit by the worst 4-quarter fall in the issuer's history. Hold bit volume.
3. Equipment: cut orders by the worst 4-quarter fall in customer capex. Revenue follows orders with the backlog lag.
4. Fab owners: hold committed capex. Cut only uncommitted capex (F4 `capex_flex`).
5. Add an export-control case. Remove the revenue to the named countries.

## Collateral and recovery
- Fabs are specialised. Use the low end of the F7.5 machinery band.
- Process know-how and design libraries carry value only in a going concern. Use the F7.5 intangibles band.
- Government chip grants can carry clawback terms. A default or a plant sale can trigger them. Size the clawback as a claim (Our choice).
- Long-term supply agreements with customer prepayments become claims when supply stops (F2 A6 rule, applied here).

## Events and calendar
- Monthly global chip sales releases from the industry association.
- Monthly equipment billings releases.
- Memory contract and spot price releases.
- Export-control rules on chips and equipment.
- Capex guidance from the main foundry, memory and data centre customers at their earnings dates.

## Instructions for the analyst
1. Frame the issuer as A4 or A5. Record the memory share and the fab ownership.
2. Build analyst EBITDA. Treat grants as capex offsets.
3. Compute `lev_gc_total` and, for fab owners, EBITDA less maintenance capex over debt.
4. Size liquidity through one full downturn. Read the grant clawback terms.
5. Run the price, orders and export-control cases.
6. Value the issuer at mid-cycle EBITDA. Use the trough multiple for `V_default`.
7. Gate the memo under F9. Report the S&P volatility class beside `ebitda_cyc`.

## Open questions
- Does `memory_share` add to `ebitda_cyc` in HY chip spreads? No repo source. Test: add both to the GICS 45 sector fit and check the sign.
- Does channel inventory lead spreads? No repo source. Test: lag `inv_days_chg` by one and two quarters.
