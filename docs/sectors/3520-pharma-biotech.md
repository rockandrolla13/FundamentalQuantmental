# 3520 Pharmaceuticals, Biotechnology and Life Sciences

Archetype (framework F2): A6 for branded pharmaceuticals and commercial biotechnology, because intangibles dominate and the value is the going concern. A4 for generics, contract development and manufacture (CDMO), and life sciences tools. Modifiers that often apply: M3 (one drug above 20% of sales), M1 (sponsor-owned CDMOs, specialty pharma and tools makers).
GICS industries covered: 352010 Biotechnology, 352020 Pharmaceuticals, 352030 Life Sciences Tools and Services.

F2.1 applies. A branded issuer with one large drug fits A6 and M3 together. Compute both views and report the difference.

## Sources
| Source | Type | Date | Opened | Pages or sections used |
|---|---|---|---|---|
| S&P Global Ratings, "Sector-Specific Corporate Methodology". Public copy: South Dakota PUC docket EL26-003, Exhibit TDS-2, https://puc.sd.gov/commission/dockets/electric/2026/EL26-003/Vol2Section6/Exh2TStevens.pdf | rating agency criteria | July 7, 2025, republished Sept. 26, 2025 | yes | Section 27 Pharmaceuticals (exhibit pp. 149-154). Appendix 3 margin and SER tables (pp. 244-252) |
| S&P Global Ratings, "Key Credit Factors For The Pharmaceutical Industry", https://www.maalot.co.il/publications/MT20141001143230.pdf | rating agency criteria. Status not verified, may be superseded by the 2025 methodology | April 8, 2014 | yes | paras. 9-13 (industry risk, cyclicality, competitive risk) |
| S&P Global Ratings, "Standard & Poor's Assigns Industry Risk Assessments To 38 Nonfinancial Corporate Industries", https://maalot.co.il/publications/MT20150505165520.pdf | rating agency table | Nov. 20, 2013 | yes | Industry risk table, p. 2 |
| Moody's, pharmaceutical industry methodology | rating agency methodology | unknown | not opened | ratings.moodys.com returns a login page |
| Repo cards | none | | | No card in `research/cards` covers drug patents, pipelines or pharma credit |

## Industry risk
- S&P cyclicality assessment: "low risk" (2). Revenue cyclicality is very low and profit cyclicality is low (2014, para. 10).
- S&P competitive risk and growth assessment: "low risk" (2). Industry risk "low" (2) (2014, paras. 9, 13. 2013 table, p. 2). The 2025 article does not restate these values.

## EBITDA, leverage and coverage
- EBITDA definition: analyst EBITDA under F3. Treat upfront and milestone payments for in-licensed drugs as investment, not as operating cost. Treat recurrent litigation settlements as operating cost (F3 C5). Remove royalty income sold to a third party from EBITDA.
- Leverage measure: `lev_gc_total` (F5). Add royalty and revenue-interest sales to debt when the issuer keeps the product risk (Our choice. S&P adds asset monetisation in place of debt, card `sp-global-2019-ratios-and-adjustments.md`, para. 9).
- Coverage measure: `coverage` (F5).
- Agency supplementary ratios: EBITDA to interest when the core ratios read "significant" or weaker. FFO plus cash interest to cash interest when PIK or low-coupon convertible debt exists (Section 27, exhibit p. 154).
- EBITDA margin bands (Appendix 3): branded below 30% below average, 30% to 40% average, above 40% above average. Generics and CDMOs: below 20%, 20% to 30%, above 30%.

## Drivers

### Branded pharmaceuticals and biotechnology (A6)
| Driver | Formula from filings | Sign in spread | Source |
|---|---|---|---|
| `log_lev` | log of `(dlc + dltt) / oibdp`, clipped | + | Our choice |
| `loe_3y` | Share of sales from drugs that face generic or biosimilar entry within 3 years, from the patent and exclusivity tables of the 10-K | + | agency weight: S&P Section 27. Below 10% supports strong. Above 30% points to weak |
| `top_drug_share` | Largest drug's share of sales, from the product revenue note | + | agency weight: S&P Section 27 (diversity). M3 trigger |
| `pipeline_replace` | Peak sales of late-stage (phase III) and newly launched drugs over sales at risk in `loe_3y` | − | agency weight: S&P Section 27. Below 30% replacement is weak |
| `fcf_debt` | `(oancf − capx) / (dlc + dltt)` | − | Our choice |

### Generics, CDMOs and life sciences tools (A4)
| Driver | Formula from filings | Sign in spread | Source |
|---|---|---|---|
| `log_lev` | log of `(dlc + dltt) / oibdp`, clipped | + | Our choice |
| `margin_trend` | 8-quarter slope t-statistic of `oibdpq / saleq` | − | Our choice. Generic price erosion shows here first |
| `capex_int` | `capx / sale` | + | Our choice. CDMO plant builds |
| `fda_flag` | Count of open FDA warning letters and import alerts at the issuer's plants | + | agency weight: S&P Section 27 cites regulatory sanctions and manufacture problems |

## Downside case
1. Branded: remove the sales in `loe_3y` on the disclosed entry dates. Apply the issuer's own erosion assumption. Without one, apply the erosion of the issuer's last product at generic entry (Our choice).
2. Branded: delay each late-stage launch by one year and cut its peak sales by half (Our choice).
3. Branded: apply the next government price negotiation or rebate rule to the drugs that the rule names.
4. Generics: cut the price of the top ten products by the worst annual erosion in the issuer's last five years. Hold volume.
5. CDMO and tools: cut volume by the largest customer's share (M3). Keep fixed plant cost.

## Collateral and recovery
- Value sits in patents, regulatory exclusivity and product rights. Liquidation value of plant is low (F7.5 machinery band).
- Value the patent estate as product DCF to the loss-of-exclusivity date. A patent near expiry has little value in a sale.
- A royalty sale can be a true sale. Then the royalty stream leaves the estate. Read the sale agreement before you count the stream as collateral.
- Product liability and settlement claims can be large. A mass tort can go to a trust (F5). Size the claim from the reserve and the claim count.
- Government settlements and integrity agreements can rank as unsecured claims with conduct terms. Read them before you run the waterfall.

## Events and calendar
- FDA decision dates (PDUFA dates) for pipeline drugs.
- Patent expiry and regulatory exclusivity dates. Paragraph IV patent challenges and court decisions.
- US Medicare drug price negotiation: CMS names the drugs by Feb. 1 and publishes the negotiated prices by Nov. 30 each year.
- Phase III data releases. Major medical congress dates.
- Plant inspection results: FDA Form 483 observations, warning letters and import alerts.

## Instructions for the analyst
1. Frame the issuer as A6 or A4. Apply M3 when one drug exceeds 20% of sales.
2. Build analyst EBITDA. Treat in-licence payments as investment and recurrent settlements as cost.
3. Add retained-risk royalty sales to debt. Compute `lev_gc_total` and `coverage`.
4. Build `loe_3y` and `top_drug_share` from the 10-K patent and product tables.
5. Size liquidity to the first major loss-of-exclusivity date. Compare it with the maturity wall.
6. Run the exclusivity, launch delay and price cases. Weight them by the F6 table.
7. Value the issuer by product DCF to exclusivity loss. Check it against the peer multiple.
8. Gate the memo under F9. Report the S&P margin band and the `loe_3y` band.

## Open questions
- Does `loe_3y` explain HY pharma spreads after leverage? No source in the repo tests it. Test: add `loe_3y` to the GICS 35 sector fit. Keep it if the sign stays + in three of four cycles.
- How fast do sales fall at generic entry for small-molecule drugs against biologics? No repo source. Add a card on generic and biosimilar entry before the downside rule changes.
- Should branded pharma have its own archetype? A6 fits the collateral rule but not the revenue rule. Decide with a decision page after the `loe_3y` test.
