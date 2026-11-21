# 4520 Technology Hardware and Equipment

Archetype (framework F2): A4. Volume moves with business and consumer IT budgets, and product cycles are short. Modifiers that often apply: M3 (one customer or one product above 20% of revenue, common in components and contract manufacture), M1 (sponsor-owned component makers).
GICS industries covered: 452010 Communications Equipment, 452020 Technology Hardware, Storage and Peripherals, 452030 Electronic Equipment, Instruments and Components (with electronic manufacture services and technology distributors).

## Sources
| Source | Type | Date | Opened | Pages or sections used |
|---|---|---|---|---|
| S&P Global Ratings, "Sector-Specific Corporate Methodology". Public copy: South Dakota PUC docket EL26-003, Exhibit TDS-2, https://puc.sd.gov/commission/dockets/electric/2026/EL26-003/Vol2Section6/Exh2TStevens.pdf | rating agency criteria | July 7, 2025, republished Sept. 26, 2025 | yes | Section 33 Technology Hardware And Semiconductors (exhibit pp. 181-184). Appendix 3 margin, return and SER tables (pp. 244-252) |
| S&P Global Ratings, "Key Credit Factors For The Technology Hardware And Semiconductors Industry" | rating agency criteria. Status not verified, may be superseded by the 2025 methodology | unknown | not opened | No public copy found |
| S&P Global Ratings, "Standard & Poor's Assigns Industry Risk Assessments To 38 Nonfinancial Corporate Industries", https://maalot.co.il/publications/MT20150505165520.pdf | rating agency table | Nov. 20, 2013 | yes | Industry risk table, p. 1 |
| Moody's, technology methodologies | rating agency methodology | unknown | not opened | ratings.moodys.com returns a login page |
| Habib, Ranasinghe and Bhuiyan (2025), card `habib-ranasinghe-bhuiyan-2025-order-backlog-credit-ratings.md` | repo card | 2025 | yes | Backlog and credit ratings. Read for the `book_to_bill` row only |

## Industry risk
- S&P cyclicality assessment: "moderately high risk" (4) (2013 table, p. 1).
- S&P competitive risk and growth assessment: "moderately high risk" (4). Industry risk "moderately high" (4) (2013 table). These are 2013 values. We did not find a later public list.

## EBITDA, leverage and coverage
- EBITDA definition: analyst EBITDA under F3. Treat inventory write-downs as recurrent when they appear in two downturns (F3 C1). Read restructuring in the light of EQ5.
- Leverage measure: `lev_gc_total` (F5). Add factored receivables and supplier finance beyond normal terms to debt (card `sp-global-2019-ratios-and-adjustments.md`, paras. 9, 11).
- Coverage measure: `coverage` (F5).
- Agency supplementary ratios (Section 33, exhibit p. 184):
  - Core ratios "intermediate" or stronger: FOCF to debt, for working capital and capex.
  - Core ratios "significant" or weaker: EBITDA to interest, or FOCF to debt as an early sign.
  - S&P states that these issuers most often default "during or after a downturn" on a missed cash interest payment or a maturity.
  - S&P assesses most subsectors as "volatile". Some consumer electronics, office electronics and distributors can be "stable". Communications equipment can be "stable" with a large software and services share.
- EBITDA margin bands (Appendix 3), below average then above average:
  - Communications equipment: below 10%, above 20%.
  - Computer hardware, storage, peripherals and components: below 12%, above 18%.
  - Consumer electronics: below 7%, above 12%.
  - Electronic manufacture services: below 4%, above 8%.
  - Technology distributors: below 3%, above 6%.

## Drivers
| Driver | Formula from filings | Sign in spread | Source |
|---|---|---|---|
| `log_lev` | log of `(dlc + dltt) / oibdp`, clipped | + | Our choice |
| `ebitda_cyc` | Minus the worst YoY EBITDA change over 10 years (F21) | + | Our choice. S&P "moderately high" cyclicality (agency weight) |
| `mat_wall` | `(dd1 + dd2) / (dlc + dltt)` | + | agency weight: S&P Section 33, default at a maturity during or after a downturn |
| `book_to_bill` | Orders over shipments, from the filing | − | Our choice (F8 A4). See the Habib et al. card |
| `inv_days_chg` | Change in `invt / cogs × 365` over 4 quarters | + | Our choice. EQ2 |
| `top_customer_share` | Largest customer's share of revenue | + | agency weight: S&P Section 33, supplier and customer concentration. M3 trigger |

### Sub-industry notes
- Communications equipment: carrier capex sets demand. Read the capex guidance of the top three carrier customers. The software and maintenance share lowers volatility (S&P Section 33).
- Computers, storage and peripherals: PC and server refresh cycles set volume. Memory and component prices set gross margin.
- Electronic manufacture services and distributors: margins are thin, and working capital is large. Working capital releases cash in a downturn (F2 A4). Read `cash_cycle` first.

## Downside case
1. Apply the issuer's own peak-to-trough revenue from its worst recent downturn (F2 A4). Use the 2008-2009 recession and the 2022-2023 inventory correction as the two templates.
2. Hold the fixed cost share for two quarters. Measure operating leverage from the issuer's last downturn.
3. Release working capital on the way down for distributors and contract manufacturers. Do not release it for issuers with obsolete inventory.
4. Remove the largest customer for issuers under M3. Size the jump.
5. Add a tariff or export-control case for issuers with plants or sales in the affected country.

## Collateral and recovery
- Receivables from large customers hold value. Use the high end of the F7.5 receivables band for investment-grade customers.
- Inventory loses value fast when the product cycle turns. Use the low end of the F7.5 inventory band for finished technology goods (Our choice).
- Patents and designs carry value only when a buyer needs them. Use the F7.5 intangibles band.
- Supplier finance and factoring programmes stop in distress. Treat their sudden stop as a liquidity event (F4).

## Events and calendar
- Quarterly orders and book-to-bill releases.
- Product launch cycles of the main customers.
- Tariff and export-control decisions on technology goods.
- Carrier and hyperscale data centre capex guidance at their earnings dates.
- Monthly industry sales releases for components.

## Instructions for the analyst
1. Frame the issuer as A4. Apply M3 when one customer exceeds 20% of revenue.
2. Build analyst EBITDA. Treat repeated inventory write-downs as recurrent.
3. Add factoring and extended supplier finance to debt. Compute `lev_gc_total`.
4. Size liquidity through the next downturn. Count the maturities in `mat_wall`.
5. Run the peak-to-trough, customer loss and tariff cases.
6. Value the issuer at mid-cycle EBITDA (F7.2). Use the trough multiple for `V_default`.
7. Gate the memo under F9. Report the S&P margin band for the subsector.

## Open questions
- Does `book_to_bill` lead HY hardware spreads? Test: add it to the GICS 45 sector fit with a one-quarter lag.
- Is the low end of the inventory band right for technology goods? No repo source. Build a recovery sample from hardware defaults.
