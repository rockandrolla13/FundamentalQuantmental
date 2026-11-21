# 2510 Automobiles and Components

Archetype (framework F2): A4 Cyclical industrials. Modifiers that often apply: M3 for suppliers with one manufacturer customer above 20% of revenue, M1 for sponsor-owned suppliers, M2 for suppliers tied to internal combustion parts only.
GICS industries covered: 251010 Automobile Components (25101010 Automotive Parts and Equipment, 25101020 Tires and Rubber), 251020 Automobiles (25102010 Automobile Manufacturers, 25102020 Motorcycle Manufacturers).

## Sources
| Source | Type | Date | Opened | Pages or sections used |
|---|---|---|---|---|
| S&P Global Ratings, "Sector-Specific Corporate Methodology", Section 3 Auto And Commercial Vehicle Manufacturing and Section 4 Auto Suppliers. Public copy: South Dakota PUC docket EL26-003, Exhibit TDS-2, https://puc.sd.gov/commission/dockets/electric/2026/EL26-003/Vol2Section6/Exh2TStevens.pdf | rating agency criteria | 7 July 2025, republished 26 Sept 2025 | yes | pp. 17-27. Appendix 3, pp. 244-248 |
| S&P, "Key Credit Factors For The Auto And Commercial Vehicle Manufacturing Industry". Maalot copy, https://maalot.co.il/publications/MT20131127143753c.pdf | rating agency criteria | 19 Nov 2013 | yes | paras. 8, 14, 16, 18, 65. Status not verified, may be superseded by the 2025 methodology |
| S&P, "Key Credit Factors For The Auto Suppliers Industry". Maalot copy, https://www.maalot.co.il/publications/mt20131127143759c.pdf | rating agency criteria | 19 Nov 2013 | yes | paras. 6, 18-21. Status not verified, may be superseded by the 2025 methodology |
| S&P, "Standard & Poor's Assigns Industry Risk Assessments To 38 Nonfinancial Corporate Industries". Maalot copy, https://maalot.co.il/publications/MT20150505165520.pdf | rating agency release | 20 Nov 2013 | yes | table, pp. 1-2. Status not verified, may be superseded by the 2025 methodology |
| S&P, "Methodology: The Impact Of Captive Finance Operations On Nonfinancial Corporate Issuers" | rating agency criteria | not known | no | not opened |
| Moody's, "Automobile Manufacturers" and "Automotive Suppliers" methodologies | rating agency criteria | not known | no | not opened. ratings.moodys.com blocked the request with a bot check. We did not bypass it |
| Fitch sector criteria for autos | rating agency criteria | not known | no | not opened |
| `research/cards/gatto-2023-credit-cycle-and-recession-cases.md` | practitioner book | 2023 | yes (card) | Figure 6.4, p. 163: autos are pro-cyclical. TM Corp case, pp. 290, 306-309 |
| `research/cards/kricheff-2012-macro-drivers-and-scenarios.md` | practitioner book | 2012 | yes (card) | p. 52 leverage tolerance of a cyclical manufacturer. p. 66 tire maker driver model |
| `research/cards/habib-ranasinghe-bhuiyan-2025-order-backlog-credit-ratings.md` | journal article | 2025 | yes (card) | order backlog and ratings, for the A4 `book_to_bill` metric |

## Industry risk
- S&P cyclicality assessment: manufacturers 5 (high), suppliers 4 (moderately high). S&P measures an average peak-to-trough revenue fall of about 17% for manufacturers and 9.5% for suppliers in recessions since 1952 (OEM KCF para. 18, supplier KCF para. 18).
- S&P competitive risk and growth assessment: manufacturers 3 (intermediate), suppliers 4 (moderately high). Both groups get a global industry risk of 4 (moderately high) in the 2013 release. The 2025 article does not restate these values.

## EBITDA, leverage and coverage
- EBITDA definition: analyst EBITDA of F3 for the industrial group only. Deconsolidate a material captive finance subsidiary before any margin or leverage figure (S&P 2025, p. 21). Treat warranty and recall costs as operating costs, not add-backs, when they recur in three of five years (F3 C5 logic, Our choice).
- Leverage measure: `lev_gc_total` on industrial debt only. Exclude captive finance debt and the captive EBITDA together. Add the pension deficit to `debt_adj` (F5).
- Coverage measure: `coverage = (ebitda_adj_analyst - capex) / cash_interest` (F5, F8).
- Agency standard or supplementary ratios for the sector:
  - Suppliers: FOCF to debt, `(cfo - capex) / debt`, read across a full cycle because launch costs swing it (S&P 2025, p. 27).
  - Manufacturers: return on capital beside the EBITDA margin when the five-year average margin sits near a threshold (S&P 2025, p. 21).
  - S&P EBITDA margin bands, below average, average, above average: manufacturers under 6%, 6% to 10%, over 10%. Suppliers under 9%, 9% to 15%, over 15% (Appendix 3, p. 244).

## Drivers
| Driver | Formula from filings | Sign in spread | Source |
|---|---|---|---|
| `log_lev` | log of `(dlc + dltt)` of the industrial group over LTM EBITDA, clipped to [0.1, 20] | + | `hy.sector.drivers`, Section 4.3. Our choice of list (SECTOR-models 3.1, industrials row) |
| `ebitda_cyc` | minus the worst YoY change of `oibdp` over 10 years | + | S&P cyclicality measure, OEM KCF para. 18. Agency weight |
| `fcf_debt` | `(oancf - capx) / (dlc + dltt)` over a full cycle | − | S&P 2025, p. 27, preferred supplier ratio. Agency weight |
| `margin_trend` | slope of `oibdpq / saleq` over 8 quarters over its standard error | − | F8, `hy.state.margin_trend`. Our choice |
| `book_to_bill` | orders over shipments, from the filing or the truck order release | − | F8 A4 row. Habib et al. (2025) card, rating test. Tested on ratings, not on spreads |
| `cust_top_share` | revenue share of the largest manufacturer customer, from the 10-K concentration note | + | F2 M3. Our choice |

## Downside case
Run the F6 A4 rule: the issuer's own peak-to-trough revenue in the last recession, with the same recovery shape. Floor the moderate case at the agency average: a 17% revenue fall and a 38% fall in EBITDA margin for manufacturers (OEM KCF para. 18). For suppliers the floors are a 9.5% revenue fall and a 13.5% margin fall (supplier KCF para. 18). Set the severe case to the larger of the F6 severe rule and the steepest recorded fall: 31% revenue and 79% margin for manufacturers. Commercial vehicle volume fell more than 50% in 2008 to 2009, so use that floor for truck makers (OEM KCF para. 14). Profits fall faster than sales because the cost base is mostly fixed (OEM KCF para. 16).

Working capital moves in opposite directions in the two sub-industries. Manufacturers carry negative working capital, so payables fall in a downturn and consume cash (OEM KCF para. 65). Suppliers release cash from inventory and receivables when sales fall (S&P 2025, p. 27). This overrides the F6.5 default "a sales decline releases cash in A4" for manufacturers only.

## Collateral and recovery
- Value a supplier as a going concern at the trough multiple (F7 A4 row). Plant and tooling liquidate at the F7.5 machinery rate of 10% to 20%.
- Receivables from manufacturer customers liquidate at the F7.5 rate only when the customer is solvent. When a customer files, cut the receivable to its expected recovery.
- A manufacturer's value sits in the brands, the dealer network and the captive book. Model the captive as a separate entity in the F5 waterfall. Its residual equity passes up to the parent only after captive creditors.
- Size pension claims on the insurer termination basis and retiree medical as modifiable (F5).
- Supplier contracts with a manufacturer are executory. Code each material contract with `hy.clocks.purchase_essentiality` (F5 purchase obligations row).

## Events and calendar
- Monthly light vehicle sales releases and the seasonally adjusted annual rate.
- Monthly and quarterly truck order releases. S&P notes that quarterly truck orders can move 20% to 30% (OEM KCF para. 14).
- Labour contract expiry dates and strike votes at the manufacturers.
- Emissions and fuel economy rule releases, and tariff decisions on vehicles and parts.
- Model changeover and platform award dates. A supplier launch wave depresses CFO before production ramps (S&P 2025, p. 27).

## Instructions for the analyst
1. Frame the issuer as a manufacturer or a supplier. Record the captive finance share and `cust_top_share`.
2. Deconsolidate the captive finance subsidiary before you compute margin, leverage, or coverage.
3. Treat recurrent warranty and recall cost as operating cost. Do not add it back.
4. Size liquidity at the trough. For a manufacturer, model the payables release in the downturn.
5. Map each claim to its entity. Put the captive, the pension, and supplier contracts in separate rows.
6. Build the downside from the issuer's last recession. Floor it at the agency averages above.
7. Value at mid-cycle EBITDA for `V_mid` and at the trough multiple for `V_default`.
8. Pass the F9 gate. Name the sales or order release that carries the catalyst.

## Open questions
- Does the working capital sign in a downturn differ by sub-industry in our data? Test: regress the change in net working capital on the change in sales for 2009 and 2020, split by 251010 and 251020.
- Does `cust_top_share` carry a spread premium after leverage? Test: add it to the industrials fit of `hy.sector.fairspread` and check the sign and the out-of-sample rank IC.
- Do the 2013 KCF averages still describe the sector after 2020? Test: recompute peak-to-trough revenue and margin falls for 2020 from Compustat and compare them with the 2013 averages.
