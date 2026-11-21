# 1510 Materials

Archetype (framework F2): A4 primary. Metals and mining upstream takes A3. Fertilizers, forest products, and pulp take A3 with A4 second. Steel and aluminum take A4 with A3 second. Modifiers that often apply: M1 for sponsor-owned specialty chemicals and packaging issuers, M2 for graphic paper, M3 for a packaging issuer with one large customer.
GICS industries covered: 151010 Chemicals (15101010 Commodity Chemicals, 15101020 Diversified Chemicals, 15101030 Fertilizers & Agricultural Chemicals, 15101040 Industrial Gases, 15101050 Specialty Chemicals). 151020 Construction Materials (15102010). 151030 Containers & Packaging (15103010 Metal, Glass & Plastic Containers, 15103020 Paper & Plastic Packaging Products & Materials). 151040 Metals & Mining (15104010 Aluminum, 15104020 Diversified Metals & Mining, 15104025 Copper, 15104030 Gold, 15104040 Precious Metals & Minerals, 15104045 Silver, 15104050 Steel). 151050 Paper & Forest Products (15105010 Forest Products, 15105020 Paper Products).

Coal is in `1010-energy.md`, because GICS puts it in Energy. Diversified chemicals use the commodity chemicals block, as S&P does (Section 8 subsector table).

## Sources
| Source | Type | Date | Opened | Pages or sections used |
|---|---|---|---|---|
| S&P Global Ratings, "Sector-Specific Corporate Methodology". Public copy filed as Exhibit TDS-2, South Dakota PUC docket EL26-003: https://puc.sd.gov/commission/dockets/electric/2026/EL26-003/Vol2Section6/Exh2TStevens.pdf | rating agency criteria | 7 July 2025, republished 26 Sept. 2025 | yes | Section 5 Building Materials, Section 8 Commodity Chemicals, Section 11 Containers And Packaging, Section 16 Forest And Paper Products, Section 22 Metals Production And Processing, Section 24 Mining, Section 32 Specialty Chemicals |
| S&P, "Key Credit Factors For The Commodity Chemicals Industry". Maalot copy: https://www.maalot.co.il/Publications/MT20190326153259.PDF | rating agency criteria | 31 Dec. 2013, republished 10 Jan. 2019 | yes | para. 4 and the cyclicality paragraphs |
| S&P, "Key Credit Factors For The Specialty Chemicals Industry". Maalot copies: https://www.maalot.co.il/Publications/MT20190623170556.PDF and https://maalot.co.il/Publications/MT20180313123145.PDF | rating agency criteria | 31 Dec. 2013, republished 30 Jan. 2019 | yes | para. 4 and the cyclicality paragraphs |
| S&P, "Key Credit Factors For The Building Materials Industry". Maalot copy: https://www.maalot.co.il/Publications/MT20170524164632.pdf | rating agency criteria | 19 Dec. 2013 | yes | paras. 5, 9, 18 to 19 |
| S&P, "Key Credit Factors For The Metals And Mining Upstream Industry". Maalot copy: https://www.maalot.co.il/publications/MT20140107164018.pdf | rating agency criteria | 20 Dec. 2013 | yes | para. 5 and the cyclicality paragraph |
| S&P, "Key Credit Factors For The Forest And Paper Products Industry". Maalot copy: https://www.maalot.co.il/Publications/MT20180228114249.PDF | rating agency criteria | 12 Feb. 2014 | yes | para. 5 and paras. 12 to 13 |
| S&P, "Key Credit Factors For The Metals And Mining Downstream Industry" | rating agency criteria | unknown | no, not found | none |
| S&P, "Key Credit Factors For The Containers And Packaging Industry" | rating agency criteria | unknown | no, not found | none |
| Moody's, "Steel" methodology: https://ratings.moodys.com/api/rmc-documents/356428. Moody's "Chemicals" methodology: https://ratings.moodys.com/api/rmc-documents/389870 | rating agency criteria | not verified | no, not opened (the Moody's document server returned HTTP 403) | none |
| Fitch materials criteria | rating agency criteria | none | no, not found | none |
| Card `almeida-hankins-williams-2017-supply-contracts-risk-management.md` | peer-reviewed journal | 2017 | yes | purchase obligations act as hedges for steel users. Users commit 12% of COGS one year ahead (p. 11) |
| Card `becker-josephson-xu-2023-executory-contract-rejection.md` | working paper | 2023 | yes | industry measure for precious metals and mining, 0.045 (Table 1, p. 22) |
| Card `kricheff-2012-macro-drivers-and-scenarios.md` | practitioner book | 2012 | yes | industry driver over GDP (p. 63). Cyclical manufacturers carry 3x to 4x leverage (p. 52) |
| Card `forecast-sector-decks.md` | forecast source | 2026 | yes | housing starts forecast for A4 |

The 2025 methodology says a separate note lists the criteria it supersedes. That note was not opened. So this page does not state whether the 2013 and 2014 Key Credit Factors articles are still in force.

## Industry risk
- Commodity chemicals: "moderately high" cyclicality (4), "moderately high" competitive risk and growth (4), so "moderately high" industry risk (category 4). Recessions since 1950 cut revenue by 7% and EBITDA margin by 15% on average. The worst revenue cut was 23%, in the last recession before 2013. The worst margin cut was 28%, in 1989 to 1992.
- Specialty chemicals: "intermediate" cyclicality (3), "low" competitive risk and growth (2), so "low" industry risk (category 2). Recessions since 1950 cut revenue by 4% and EBITDA margin by 12% on average. Revenue fell 18% in 2007 to 2009.
- Building materials (covers construction materials): "moderately high" cyclicality (4), "intermediate" competitive risk and growth (3), so "intermediate" industry risk (category 3). Average cuts were 8% in revenue and 16% in EBITDA margin since 1952. The worst revenue cuts were 23% (1979 to 1982) and 16% (2007 to 2009). The worst margin cut was 32% (1979 to 1982).
- Containers and packaging: not opened.
- Metals and mining upstream: "high" cyclicality, "intermediate" competitive risk and growth, so "moderately high" industry risk (category 4). Average cuts were 13% in revenue and 30% in EBITDA margin since 1952. The 2007 to 2009 cuts were 21% and 56%.
- Metals production and processing (steel, aluminum): not opened.
- Forest and paper products: "moderately high" cyclicality (4), "moderately high" competitive risk and growth (4), so "moderately high" industry risk (category 4). Revenue fell 6% on average in recessions since 1968, and 16% in 1979 to 1982. EBITDA margin fell 20% on average since 1952, and 42% in 1979 to 1982.

## EBITDA, leverage and coverage
- EBITDA definition: EBITDA through a full cycle with at least one recession (F3.1). Treat plant closure and restructure charges as recurrent under M2 (F2). For A3 metals and mining, compute EBITDA at the strip and at the stress deck.
- Leverage measure: `total_debt / ebitda_adj_analyst` (F8 `lev_gc_total`). Add after-tax retiree benefit deficits and asset retirement obligations to debt (card `sp-global-2019-ratios-and-adjustments.md`).
- Coverage measure: `(ebitda_adj_analyst - capex) / cash_interest` (F8 `coverage`).
- Agency standard or supplementary ratios for the sector:
  - Commodity and specialty chemicals: FOCF to debt when the core assessment is "intermediate" or better. Commodity chemicals use EBITDA to interest when it is "significant" or weaker. Specialty chemicals use CFO to debt when working capital exceeds 25% of sales (S&P Sections 8 and 32).
  - Construction materials: CFO to debt when the core assessment is "intermediate" or better, else FOCF to debt (S&P Section 5).
  - Containers and packaging: FOCF to debt. DCF to debt when payouts exceed half of FOCF (S&P Section 11).
  - Mining: FOCF to debt. Add FFO plus cash interest to cash interest and EBITDA to interest when the core assessment is "significant" or weaker (S&P Section 24).
  - Steel and aluminum: FOCF to debt and CFO to debt (S&P Section 22). Paper and forest products: S&P adjusts the cash flow assessment by up to two categories for volatility (Section 16).

## Sub-industry: Commodity, diversified, and fertilizer chemicals (15101010, 15101020, 15101030)

### Drivers
| Driver | Formula from filings | Sign in spread | Source |
|---|---|---|---|
| `log_lev` | log of clip(debt / LTM EBITDA, 0.1, 20) | + | methodology 7.2. agency weight |
| `ebitda_cyc` | minus the worst YoY EBITDA change, last 10 fiscal years (F21) | + | `hy.sector.drivers`. Our choice |
| `gross_margin` | (sale − cogs) / sale, as a proxy for margin over raw material cost | − | S&P Section 8 names margin over raw material cost. agency weight |
| `fcf_debt` | (oancf − capx) / (dlc + dltt) | − | S&P Section 8. agency weight |
| `capex_int` | capx / sale | + | S&P Section 8 names capex to sales. `hy.sector.drivers` |

### Downside case
Run two cases. The recession case cuts revenue by 7% and EBITDA margin by 15%, the S&P averages. Use the issuer's own worst cycle when it is deeper (F6 A4 rule). The supply case holds the margin at the issuer's lowest four quarters of the last 10 years for eight quarters (Our choice). New capacity can cut margins without a recession, so the supply case can bind. For fertilizers, move price with the crop price deck and the input gas price (A3 second view).

### Collateral and recovery
- Plants are specialised. Use the low end of the F7.5 machinery band.
- Environmental and site obligations can survive the case (F5 environmental row). Deduct them before the waterfall.
- Inventory: commodity grades trade on open markets. Use the middle of the F7.5 inventory band (Our choice).

### Events and calendar
- PMI and industrial production releases (F2 A4).
- Capacity start-ups announced by the industry. Treat each as a supply event (Our choice).
- Monthly crop and plant area reports for fertilizer demand (Our choice of series).

### Instructions for the analyst
1. Frame the issuer as A4. Add the A3 view for fertilizers and single-product petrochemicals.
2. Normalise EBITDA through a full cycle with one recession.
3. Read the feedstock and energy cost position against peers in the same region.
4. Size claims. Add environmental and pension termination claims.
5. Run the recession case and the supply case. Use the worse one as the severe downside.
6. Value at the trough multiple on mid-cycle EBITDA.
7. Gate: flag a top customer above 10% of sales (S&P Section 8).

## Sub-industry: Specialty chemicals and industrial gases (15101040, 15101050)

### Drivers
| Driver | Formula from filings | Sign in spread | Source |
|---|---|---|---|
| `log_lev` | log of clip(debt / LTM EBITDA, 0.1, 20) | + | methodology 7.2. agency weight |
| `margin_trend` | 8-quarter margin trend t-statistic (`hy.state.margin_trend`) | − | `hy.sector.drivers`. Our choice |
| `gross_margin` | (sale − cogs) / sale | − | S&P Section 32 names gross margin. agency weight |
| `passthrough_share` | share of sales under contracts with raw material pass-through clauses | − | S&P Section 32. agency weight |
| `fcf_debt` | (oancf − capx) / (dlc + dltt) | − | S&P Section 32. agency weight |

### Downside case
Cut revenue by 4% and EBITDA margin by 12%, the S&P recession averages. Use 18%, the 2007 to 2009 revenue cut, in the severe case. Add a raw material shock: raise input cost by its largest four-quarter rise in the last 10 years. Pass it through with the contract lag in the filings (Our choice). S&P says raw materials and energy often exceed half of COGS in this sector (Section 32).

### Collateral and recovery
- Value as a going concern. Product formulations and customer approvals hold value that a liquidation does not recover (F7 A4).
- Plants: low end of the F7.5 machinery band.
- For M1 issuers, check intellectual property transfers before the claims view (F7 liability management score).

### Events and calendar
- Raw material price releases for the main feedstocks (Our choice of series).
- Price increase announcements by the issuer and its peers.
- Sponsor actions for M1 issuers: dividends, add-on debt, asset transfers.

### Instructions for the analyst
1. Frame the issuer as A4. Check M1.
2. Normalise EBITDA. Apply the F3 add-back rules strictly to sponsor adjustments.
3. Read `passthrough_share` and the lag from the contract notes.
4. Size claims. Score the documents for the liability management score.
5. Run the recession case with the raw material shock.
6. Value as a going concern at the trough multiple.
7. Gate: flag a gross margin below the peer median for four quarters.

## Sub-industry: Construction materials (15102010)

### Drivers
| Driver | Formula from filings | Sign in spread | Source |
|---|---|---|---|
| `log_lev` | log of clip(debt / LTM EBITDA, 0.1, 20) | + | methodology 7.2. agency weight |
| `ebitda_cyc` | minus the worst YoY EBITDA change, last 10 fiscal years (F21) | + | `hy.sector.drivers`. Our choice |
| `gm_peer_gap` | issuer gross margin trend − peer median gross margin trend | − | S&P Section 5: the gross margin trend against peers measures the power to pass through cost. agency weight |
| `cfo_debt` | oancf / (dlc + dltt) | − | S&P Section 5, preferred supplementary ratio. agency weight |
| `capex_int` | capx / sale | + | `hy.sector.drivers`. Our choice |

### Downside case
Cut revenue by 16% and EBITDA margin by 32%, the 2007 to 2009 and 1979 to 1982 worst cases (S&P building materials KCF). Use the average cuts of 8% and 16% in the moderate case. Split revenue by end market: residential falls hardest, and repair and public works fall less (S&P Section 5). Tie residential volume to the housing starts forecast (card `forecast-sector-decks.md`).

### Collateral and recovery
- Owned quarries and permitted reserves keep value in a sale. Use an appraisal, not the F7.5 real estate default (Our choice).
- Cement plants: low end of the F7.5 machinery band.
- Transport cost limits the buyer pool to nearby producers. Apply the F7.1 size discount.

### Events and calendar
- Housing starts and permits: monthly.
- Public works budgets and highway bill dates.
- Energy cost changes for kilns (Our choice).

### Instructions for the analyst
1. Frame the issuer as A4.
2. Normalise EBITDA through one housing cycle.
3. Split revenue into residential, commercial, and public works.
4. Size claims. Add asset retirement obligations for quarries.
5. Run the end-market case with the worst S&P cuts.
6. Value at mid-cycle EBITDA. Cross-check with reserve value per ton.
7. Gate: flag `gm_peer_gap` below zero for four quarters.

## Sub-industry: Containers and packaging (15103010, 15103020)

### Drivers
| Driver | Formula from filings | Sign in spread | Source |
|---|---|---|---|
| `log_lev` | log of clip(debt / LTM EBITDA, 0.1, 20) | + | methodology 7.2. agency weight |
| `fcf_debt` | (oancf − capx) / (dlc + dltt) | − | S&P Section 11. agency weight |
| `passthrough_share` | share of sales under contracts with raw material pass-through clauses | − | S&P Section 11 calls pass-through a critical factor. agency weight |
| `stable_end_share` | sales to food, beverage, household, personal care, and medical markets / sales | − | S&P Section 11. agency weight |
| `top1_customer` | largest customer sales / sales | + | S&P Section 11: above 10% is a risk. agency weight |
| `margin_trend` | 8-quarter margin trend t-statistic | − | `hy.sector.drivers`. Our choice |

### Downside case
Volume risk is low in stable end markets. Cost risk is high. Raise resin, metal, or energy cost by the largest four-quarter rise in the last 10 years. Pass it through with the contract lag (Our choice). S&P says raw materials are about 50% to 60% of COGS for plastic and metal packaging (Section 11). Film and flexible producers absorb the rise for a period. Use a full lag of one year for them (Our choice). Add a loss-of-contract branch for the largest customer (F2 M3).

### Collateral and recovery
- Value as a going concern. Heavy containers do not ship far at an economic cost (S&P Section 11). So a plant near its customers keeps its value inside the business as a going concern (our inference).
- Glass furnaces and can lines: low end of the F7.5 machinery band.
- Run the F7 liability management score for M1 issuers.

### Events and calendar
- Raw material indices: resin, aluminum, steel, and soda ash (Our choice of series).
- Beverage season: spring and summer volume (S&P Section 11).
- Packaging rule releases on recycled content and bans on single-use plastics.

### Instructions for the analyst
1. Frame the issuer as A4 with low cyclicality. Check M1 and M3.
2. Normalise EBITDA. Separate gains from the pass-through lag from the run rate.
3. Read `passthrough_share` and the lag by product line.
4. Size claims. Score the documents for the liability management score.
5. Run the cost shock with the lag and the customer loss.
6. Value as a going concern on EV to EBITDA peers.
7. Gate: flag `top1_customer` above 20% (F2 M3).

## Sub-industry: Metals and mining upstream (15104020, 15104025, 15104030, 15104040, 15104045)

### Drivers
| Driver | Formula from filings | Sign in spread | Source |
|---|---|---|---|
| `log_lev` | log of clip(debt / LTM EBITDA, 0.1, 20) | + | methodology 7.2. agency weight |
| `fcf_debt` | (oancf − capx) / (dlc + dltt) | − | S&P Section 24. agency weight |
| `cost_quartile` | production-weighted quartile of the issuer's mines on the global cash cost curve | + | S&P Section 24. agency weight |
| `reserve_life` | proven and probable reserves / annual production | − | S&P Section 24: 10 years or more strong, one to three years weak. agency weight |
| `ebitda_cyc` | minus the worst YoY EBITDA change, last 10 fiscal years (F21) | + | `hy.sector.drivers`. Our choice |
| `capex_int` | capx / sale | + | `hy.sector.drivers`. Our choice |

### Downside case
Set the metal price to the cash cost of the 75th percentile of the global curve for eight quarters (Our choice). S&P says fourth-quartile assets can turn cash negative and idle in a downturn (Section 24). Check the case against the S&P history: average cuts of 13% in revenue and 30% in EBITDA margin, and 21% and 56% in 2007 to 2009. Hold growth capex only when the issuer cannot stop the project. S&P adds FOCF to debt as a test for a capex program that is hard to curtail (Section 24).

### Collateral and recovery
- Value mines at net asset value on the stress deck (F7 A3).
- Reclamation obligations can survive the case (F5 environmental row). Deduct them first.
- Streams and royalties sold on a mine reduce the value left for creditors. Treat a stream as debt-like until a source card settles it (Our choice).

### Events and calendar
- Exchange metal prices and the futures strip: daily.
- Mine plan and reserve updates in the annual report.
- Jurisdiction events: royalty and tax changes, export rules, permits (S&P Section 24).

### Instructions for the analyst
1. Frame the issuer as A3. Record mine count, commodity mix, and jurisdictions.
2. Normalise EBITDA at the strip and at the stress deck.
3. Place each mine on the cost curve. Compute `cost_quartile`.
4. Size claims. Add reclamation, streams, and royalties.
5. Run the cost-curve price case for eight quarters.
6. Value at net asset value on the stress deck.
7. Gate: block a long call on a single mine with a reserve life under three years.

## Sub-industry: Metals production and processing, steel and aluminum (15104010, 15104050)

### Drivers
| Driver | Formula from filings | Sign in spread | Source |
|---|---|---|---|
| `log_lev` | log of clip(debt / LTM EBITDA, 0.1, 20) | + | methodology 7.2. agency weight |
| `fcf_debt` | (oancf − capx) / (dlc + dltt) | − | S&P Section 22. agency weight |
| `cfo_debt` | oancf / (dlc + dltt) | − | S&P Section 22. agency weight |
| `ebitda_per_ton` | LTM EBITDA / tons shipped | − | S&P Section 22. agency weight |
| `ebitda_cyc` | minus the worst YoY EBITDA change, last 10 fiscal years (F21) | + | `hy.sector.drivers`. Our choice |
| `capex_flex` | (capex_total − capex_maintenance) / capex_total (F8) | − | S&P Section 22: the record of capex cuts in a downturn. agency weight |

### Downside case
Set the metal spread to the trough of the last two cycles. The spread is the product price less the main input cost, such as scrap, ore and coal, or alumina and power (Our choice). Use the issuer's own peak-to-trough revenue in the last recession for volume (F6 A4 rule). Cut capex to maintenance at the rate the issuer showed in its last downturn (S&P Section 22). Add the working capital release on the way down (F2 A4). Purchase obligations for inputs act as forward contracts. Mark them at the trough price (card `almeida-hankins-williams-2017-supply-contracts-risk-management.md`).

### Collateral and recovery
- Inventory and receivables carry most of the ABL value (F4.2). Metal inventory trades on open markets. Use the high end of the F7.5 inventory band (Our choice).
- Mills: low end of the F7.5 machinery band.
- Pension and retiree claims: use the termination liability (F5 pension row).

### Events and calendar
- Trade decisions: tariffs, antidumping orders, and import quotas.
- Monthly contract price settlements with auto and appliance customers.
- Capacity utilisation releases for the industry (Our choice of series).

### Instructions for the analyst
1. Frame the issuer as A4. Add the A3 view for primary aluminum and commodity steel.
2. Normalise EBITDA through a full cycle. Report `ebitda_per_ton`.
3. Recompute the ABL borrowing base at the trough metal price (F4.2).
4. Size claims. Add pension termination and purchase obligation claims.
5. Run the trough metal spread with the issuer's past capex cut.
6. Value at the trough multiple on mid-cycle EBITDA.
7. Gate: flag a single-mill issuer with a high import share in its market.

## Sub-industry: Paper and forest products (15105010, 15105020)

### Drivers
| Driver | Formula from filings | Sign in spread | Source |
|---|---|---|---|
| `log_lev` | log of clip(debt / LTM EBITDA, 0.1, 20) | + | methodology 7.2. agency weight |
| `ebitda_cyc` | minus the worst YoY EBITDA change, last 10 fiscal years (F21) | + | `hy.sector.drivers`. Our choice |
| `reinvest` | capx / dp | − | S&P Section 16: an issuer that cannot sustain reinvestment is weak. Our choice |
| `decline_share` | sales in segments with structural decline, such as graphic paper / sales | + | S&P Section 16. agency weight |
| `integration_share` | own boxes and converted products / own containerboard and paper output | − | S&P Section 16: box prices are higher and more stable. agency weight |
| `fcf_debt` | (oancf − capx) / (dlc + dltt) | − | methodology 7.2. Our choice |

### Downside case
Cut revenue by 16% and EBITDA margin by 42%, the 1979 to 1982 worst case (S&P forest KCF). Use the average cuts of 6% and 20% in the moderate case. Run pulp and lumber on their own price decks (A3 second view). For graphic paper add M2: volume falls at the rate of the last five years, and the terminal value declines (F7.4). Add a mill shutdown for one quarter at the largest mill (Our choice).

### Collateral and recovery
- Owned timberland: appraisal value. It holds value apart from the mills (Our choice).
- Mills: low end of the F7.5 machinery band. A graphic paper mill may only have scrap value under M2.
- Pension claims: use the termination liability (F5 pension row).

### Events and calendar
- Monthly containerboard, pulp, and paper price publications (Our choice of series).
- Housing starts for lumber demand.
- Mill closure announcements by peers. Treat each as a supply event.

### Instructions for the analyst
1. Frame the issuer as A4. Use A3 for timber, pulp, and lumber. Add M2 for graphic paper.
2. Normalise EBITDA. Treat closure charges as recurrent under M2.
3. Compute `decline_share` and `integration_share` from the segment note.
4. Size claims. Add pension termination and mill closure liabilities.
5. Run the 1979 to 1982 case and the M2 volume decline.
6. Value timberland apart from the mills.
7. Gate: block a long call when `reinvest` stays below 1 for three years.

## Open questions
- Does capex carry a plus or a minus sign in paper and forest spreads? `hy.sector.drivers` gives `capex_int` a plus sign. S&P Section 16 reads low reinvestment as weak. Both hold in different states: high capex strains cash in a downturn, and low capex erodes the asset base. This page chooses `reinvest` with a minus sign. Test: fit both in the materials group of `hy.sector.fairspread` and keep the one with the stated sign and a positive rank IC after costs in three of the four cycles (2008, 2015, 2020, 2022).
- Does `passthrough_share` carry its sign on spreads? Test: parse the share from contract notes, then run the same fit and rank IC test.
- Should packaging stay in A4? Its demand is stable, but its cost shock is A4-like. Test: compare the peak-to-trough EBITDA of packaging issuers in 2008 to 2009 and 2020 with the A4 median.
- What are the S&P cyclicality and competitive risk values for packaging and for steel and aluminum? Test: open the downstream and packaging criteria articles and update the Industry risk block.
- How do metal streams rank in a miner default? No opened source settles it. Test: write a card from a bankruptcy docket, then set the F5 rule.
- The cost curve, reserve, pass-through, and end-market drivers have no field in `data/schemas/`. Add each field with `as_of` and `available_at` before a fit.
