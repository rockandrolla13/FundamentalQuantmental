# 1010 Energy

Archetype (framework F2): A3 primary. Oilfield services take A4, offshore contract drilling takes A5, midstream takes A5 (A7 for a single asset), and refining takes A3 with A4 second. Modifiers that often apply: M1 for sponsor-owned services and midstream issuers, M2 for thermal coal, M3 for a gathering system tied to one producer.
GICS industries covered: 101010 Energy Equipment & Services (10101010 Oil & Gas Drilling, 10101020 Oil & Gas Equipment & Services). 101020 Oil, Gas & Consumable Fuels (10102010 Integrated Oil & Gas, 10102020 Oil & Gas Exploration & Production, 10102030 Oil & Gas Refining & Marketing, 10102040 Oil & Gas Storage & Transportation, 10102050 Coal & Consumable Fuels).

Integrated oil and gas issuers use the E&P block and add the refining block for the downstream segment. S&P rates coal under its mining section, not under an energy section. This page keeps coal in Energy because GICS puts it there.

## Sources
| Source | Type | Date | Opened | Pages or sections used |
|---|---|---|---|---|
| S&P Global Ratings, "Sector-Specific Corporate Methodology". Public copy filed as Exhibit TDS-2, South Dakota PUC docket EL26-003: https://puc.sd.gov/commission/dockets/electric/2026/EL26-003/Vol2Section6/Exh2TStevens.pdf | rating agency criteria | 7 July 2025, republished 26 Sept. 2025 | yes | Section 12 Contract Drilling, Section 23 Midstream Energy, Section 24 Mining (coal subsector), Section 25 Oil And Gas E&P, Section 26 Oilfield Services And Equipment, Section 29 Refining And Marketing |
| S&P Global Ratings, "Key Credit Factors For The Oil And Gas Exploration And Production Industry". Copy hosted by S&P Global Ratings Maalot: https://www.maalot.co.il/Publications/MT20170423100329.pdf | rating agency criteria | 12 Dec. 2013 | yes | paras. 9, 15 to 16 (industry risk and cyclicality), 19 (hedges), 74 to 77 (economic hedges, volumetric production payments) |
| S&P, "Key Credit Factors: Criteria For Rating The Global Oil Refining Industry". Maalot copy: https://www.maalot.co.il/Publications/MT20120529105512a.pdf | rating agency criteria, superseded | 28 Nov. 2011 | yes | crack spread definition, liquidity standard for refiners (EBITDA decline of more than 30% for "adequate") |
| S&P, "Key Credit Factors For The Oil Refining And Marketing Industry" | rating agency criteria | 27 Mar. 2014 | no, not opened | name and date only |
| S&P, "Key Credit Factors For The Metals And Mining Upstream Industry". Maalot copy: https://www.maalot.co.il/publications/MT20140107164018.pdf | rating agency criteria | 20 Dec. 2013 | yes | para. 5 and the cyclicality paragraph (used for coal) |
| S&P, "The Change To The Industry Risk Assessment For Exploration & Production Companies And What It Means For Issuer Ratings": https://spglobal.com/ratings/en/research/articles/210125-the-change-to-the-industry-risk-assessment-for-exploration-production-companies-and-what-it-means-for-issuer-11808862 | rating agency commentary | Jan. 2021 | no, not opened (HTTP 403) | none |
| S&P, "The Change To The Industry Risk Assessment For Midstream Energy Companies And What It Means For Credit Quality": https://www.spglobal.com/ratings/en/research/articles/210127-the-change-to-the-industry-risk-assessment-for-midstream-energy-companies-and-what-it-means-for-credit-qualit-11814520 | rating agency commentary | Jan. 2021 | no, not opened (HTTP 403) | none |
| S&P Key Credit Factors articles for oilfield services, contract drilling, and midstream | rating agency criteria | unknown | no, not found | none |
| Moody's, "Independent Exploration and Production" methodology: https://ratings.moodys.com/api/rmc-documents/396736 | rating agency criteria | not verified | no, not opened (HTTP 403) | none |
| Morningstar DBRS, "Global Methodology for Rating Companies in the Oil & Gas, Oilfield Services, and Pipeline and Midstream Energy Industries": https://dbrs.morningstar.com/research/453397 | rating agency criteria | 6 May 2025 | press release only. Methodology text not opened | none |
| Fitch energy criteria | rating agency criteria | none | no, not found | none |
| Card `gilje-loutskina-murphy-2020-drilling-debt.md` | peer-reviewed journal | 2020 | yes | lendable share of PV-10 by reserve class (Fig. 3, p. 1319) |
| Card `forecast-sector-decks.md` | forecast source | 2026 | yes | EIA STEO cadence, futures strip as the point forecast |
| Card `kricheff-2012-macro-drivers-and-scenarios.md` | practitioner book | 2012 | yes | industry driver over GDP (p. 63), breakeven EBITDA decline (p. 69) |
| Card `kim-kung-2013-asset-redeployability.md` | working paper | 2013 | yes | oil and gas has the lowest redeployability score, R = 0.12 (p. 32) |
| Card `campello-et-al-2011-corporate-hedging.md` | working paper | 2011 | yes | hedges lower loan spreads. Commodity hedges are out of its scope |

The 2025 methodology says a separate note lists the criteria it supersedes. That note was not opened. So this page does not state whether the 2013 and 2014 Key Credit Factors articles are still in force.

## Industry risk
- S&P cyclicality assessment, E&P: "moderately high" (4). Recessions since 1952 cut E&P revenue by 7.9% and EBITDA margin by 15.5% on average, peak to trough. The largest margin drop was 27.5% (2013 KCF, paras. 15 to 16).
- S&P competitive risk and growth assessment, E&P: "intermediate" (3). Industry risk is "intermediate" (category 3) in the 2013 KCF. S&P changed the E&P assessment in January 2021. That article was not opened, so the new value is not recorded here.
- Oilfield services and contract drilling: not opened.
- Midstream: not opened. S&P changed the assessment in January 2021 (not opened).
- Refining and marketing: not opened. The 2011 article predates the S&P industry risk scale.
- Coal (S&P mining industry as a whole): "high" cyclicality and "intermediate" competitive risk and growth, so "moderately high" industry risk (category 4) (2013 mining KCF, para. 5). Recessions since 1952 cut mining revenue by 13% and EBITDA margin by 30% on average. In 2007 to 2009 the cuts were 21% and 56%.

## EBITDA, leverage and coverage
- EBITDA definition: EBITDAX for E&P (EBITDA before exploration expense). Remove unrealised derivative gains and losses on future production. Keep realised hedge effects (2013 KCF, para. 74). Midstream: proportionate EBITDA of joint ventures only when cash distributions support it (Our choice). Refining: EBITDA before inventory gains and losses (LIFO or replacement cost basis) (Our choice).
- Leverage measure: `total_debt / ebitda_adj_analyst` (F8 `lev_gc_total`). Add a volumetric production payment with strong investor protection to debt (2013 KCF, para. 76). Add holdco debt to midstream leverage when the holdco depends on distributions (F2 A7).
- Coverage measure: `(ebitda_adj_analyst - capex) / cash_interest` (F8 `coverage`). Use maintenance capex for midstream and refining (S&P Sections 23 and 29).
- Agency standard or supplementary ratios for the sector:
  - E&P: FOCF to debt, with at least maintenance capex. DCF to debt when the issuer pays out excess cash (S&P Section 25).
  - Oilfield services and contract drilling: FOCF to debt (S&P Sections 12 and 26). S&P moves the cash flow assessment toward FOCF to debt for drillers.
  - Midstream: FOCF to debt with maintenance capex only (S&P Section 23).
  - Refining: FOCF to debt with integrity, environmental, and regulatory capex only (S&P Section 29).
  - Coal: FOCF to debt. Add EBITDA to interest when the core assessment is "significant" or weaker (S&P Section 24).

## Sub-industry: Oil and gas exploration and production (10102020, upstream of 10102010)

### Drivers
| Driver | Formula from filings | Sign in spread | Source |
|---|---|---|---|
| `log_lev` | log of clip(debt / LTM EBITDAX, 0.1, 20) (`hy.sector.drivers`) | + | methodology 7.2. agency weight |
| `fcf_debt` | (oancf − capx) / (dlc + dltt) | − | S&P Section 25, preferred supplementary ratio. agency weight |
| `reserve_life` | proved reserves / annual production, boe (10-K reserve note, ASC 932. No Compustat field assumed) | − | S&P Section 25: below 5 years weak, 10 years or more strong. agency weight |
| `recycle_ratio` | unit netback / three-year unit FD&A cost | − | S&P Section 25: below 1x means weak efficiency. agency weight |
| `hedge_cover_4` | hedged volumes in the next 4 quarters / forecast production in the same quarters | − | 2013 KCF, para. 19 (qualitative). Our choice |
| `bb_cushion` | (low lendable value from `borrowing_base_collateral` − drawn RBL) / low lendable value | − | card `gilje-loutskina-murphy-2020-drilling-debt.md` (behaviour, not spreads). Our choice |

### Downside case
Run three price decks: the futures strip as base, a moderate deck, and a severe deck (card `forecast-sector-decks.md`: futures first, EIA STEO second). Set the severe deck to the lowest four-quarter average front-month price of the last two price cycles (2015 to 2016 and 2020), in real terms (Our choice). Set the moderate deck halfway between the strip and the severe deck (Our choice). Cut capex to maintenance and let production follow the base decline rate. Recompute `bb_cushion` at the severe deck, because the bank resets the base on the new price. A recession alone understates the case: the S&P recession average margin cut is 15.5%, but price cycles outside recessions cut deeper.

### Collateral and recovery
- Value reserves at PV-10 on the severe deck (F7 A3). Lendable value follows reserve class: producing 90% to 95%, nonproducing 65% to 75%, undeveloped 25% to 50%, unproved 0 (card `gilje-loutskina-murphy-2020-drilling-debt.md`).
- Oil and gas assets have the lowest redeployability score in the Kim and Kung sample (R = 0.12). Expect a forced-sale discount above the F7.5 machinery default (card `kim-kung-2013-asset-redeployability.md`, no recovery test).
- Claims that differ from F5 defaults: hedge counterparties net and close out under the safe harbour (F5 §560). Plugging and abandonment obligations can survive the case and rank ahead of unsecured claims (F5 environmental row). A volumetric production payment conveys a real interest that the parties expect to survive bankruptcy (2013 KCF, para. 75). Remove those volumes from the estate.

### Events and calendar
- Borrowing base redeterminations: twice a year, on the dates in the credit agreement (F2 A3).
- EIA Short-Term Energy Outlook: monthly (card `forecast-sector-decks.md`).
- Year-end reserve report in the 10-K. Watch negative technical revisions, which S&P reads as a sign of aggressive bookings (S&P Section 25).
- OPEC+ production decisions: dated meetings. Treat a surprise as a price shock event (F2 A3).

### Instructions for the analyst
1. Frame the issuer as A3. Record basin count, oil and gas mix, and operator share.
2. Normalise EBITDAX. Strip unrealised hedge gains and losses on future production.
3. Compute `bb_cushion` at the strip and at the severe deck. Set liquidity from the lower one.
4. Size claims. Add plugging obligations, net hedge termination values, and debt-like production payments.
5. Run the three decks with maintenance capex and the base decline rate.
6. Value at net asset value on the severe deck. Cross-check against precedent value per barrel a day of production.
7. Gate: reject a long call when `recycle_ratio` is below 1 at the strip.

## Sub-industry: Oilfield services and equipment, and contract drilling (10101010, 10101020)

### Drivers
| Driver | Formula from filings | Sign in spread | Source |
|---|---|---|---|
| `log_lev` | log of clip(debt / LTM EBITDA, 0.1, 20) | + | methodology 7.2. agency weight |
| `fcf_debt` | (oancf − capx) / (dlc + dltt) | − | S&P Sections 12 and 26, preferred supplementary ratio. agency weight |
| `ebitda_cyc` | minus the worst YoY EBITDA change, last 10 fiscal years (F21) | + | `hy.sector.drivers`. Our choice |
| `capex_int` | capx / sale | + | `hy.sector.drivers`, Kricheff p. 61. Our choice |
| `backlog_cover` | contracted backlog due in the next 4 quarters / LTM revenue (drillers and equipment makers) | − | S&P Section 12, revenue predictability. agency weight |
| `util_gap` | issuer fleet utilisation − industry utilisation, same rig class | − | S&P Section 12, efficiency of operations. agency weight |

### Downside case
Demand follows E&P capex. Cut revenue by the issuer's own peak-to-trough decline in the last two activity downturns (2015 to 2016 and 2020) (F6 A4 rule). Release working capital in the first two quarters and absorb it again in the recovery (S&P Section 26). For drillers, roll each contract at its expiry to the day rate at the last trough. Add the cost to keep idle rigs (Our choice). Treat a speculative newbuild without a contract as a funded liability in every case (S&P Section 12, financial policy modifier).

### Collateral and recovery
- Land equipment and pressure pumping fleets: machinery at 10% to 20% (F7.5 default).
- Rigs and vessels: appraised value in a forced sale (F7 A5). Rig appraisals fall with day rates, so use the trough appraisal.
- Customer receivables: S&P notes slow collection for small providers in a downturn (Section 26). Use the low end of the F7.5 receivables band.

### Events and calendar
- Weekly rig and frac spread counts (Our choice of activity series).
- E&P capex guidance in fourth-quarter results (F2 A4 order and backlog releases).
- Contract awards and expiries in the driller fleet status report.

### Instructions for the analyst
1. Frame land services as A4 and offshore drillers as A5.
2. Normalise EBITDA through a full activity cycle (F3.1).
3. Map contract expiries by quarter. Compute `backlog_cover`.
4. Size claims. Add newbuild commitments without a contract as debt-like.
5. Run the activity downturn with the working capital release and the trough day rate.
6. Value land services at the trough multiple. Value rigs at the trough appraisal.
7. Gate: flag a top-10 customer share above the F2 M3 limit.

## Sub-industry: Midstream, storage and transportation (10102040)

### Drivers
| Driver | Formula from filings | Sign in spread | Source |
|---|---|---|---|
| `log_lev` | log of clip(debt / LTM EBITDA, 0.1, 20). Add holdco debt | + | methodology 7.2. agency weight |
| `fee_share` | fee-based and take-or-pay EBITDA / EBITDA | − | S&P Section 23: at least 90% for the low volatility table, two thirds for the medial table. agency weight |
| `contract_tenor` | volume-weighted years left on firm contracts | − | S&P Section 23: eight or more years on average is strong. agency weight |
| `cpty_ig_share` | EBITDA from investment-grade counterparties / EBITDA | − | S&P Section 23, counterparty cap. agency weight |
| `coverage` | clip(LTM EBITDA / LTM interest, −5, 30) | − | `hy.sector.drivers`. Our choice |

### Downside case
Split EBITDA into fee, volume, and commodity parts. Gathering and processing systems in a mature basin can lose more than 10% of volume in a year (S&P Section 23). Cut volume by 10% a year for two years on unhedged gathering systems (Our choice). Move commodity-linked margin with the severe E&P deck. Then default the largest counterparty below investment grade. Reprice its contracts to the market rate on the asset (Our choice). If one counterparty uses the only asset, cap the issuer at the counterparty view (S&P Section 23).

### Collateral and recovery
- Value long-haul pipelines and storage by contract DCF (F7 A5 and A7). Value gathering systems on basin volume, not on replacement cost.
- A producer in bankruptcy may try to reject gathering contracts. No opened source states when the dedication survives. See Open questions.
- Holdco claims are structurally subordinated to debt of the operating partnership (F2 A7). Holdco recovery comes from distributions only.

### Events and calendar
- Contract roll-off dates in the 10-K firm commitment table.
- Regulated tariff index changes and rate cases. Check the order date in each docket (Our choice).
- Counterparty rating actions on the largest shippers.

### Instructions for the analyst
1. Frame the issuer as A5. Use A7 for a single asset or a distribution-only holdco.
2. Normalise EBITDA. Split fee, volume, and commodity parts.
3. Compute `fee_share`, `contract_tenor`, and `cpty_ig_share` from the contract table.
4. Size claims. Put holdco debt behind all debt of the operating entities.
5. Run the volume decline and the counterparty default.
6. Value by contract DCF. Haircut gathering value with basin volume.
7. Gate: block a long call when one counterparty below investment grade supplies most EBITDA.

## Sub-industry: Refining and marketing (10102030)

### Drivers
| Driver | Formula from filings | Sign in spread | Source |
|---|---|---|---|
| `log_lev` | log of clip(debt / LTM EBITDA, 0.1, 20) | + | methodology 7.2. agency weight |
| `fcf_debt` | (oancf − maintenance capex) / (dlc + dltt). Use capx when maintenance capex is not disclosed | − | S&P Section 29. agency weight |
| `ebitda_cyc` | minus the worst YoY EBITDA change, last 10 fiscal years (F21) | + | `hy.sector.drivers`. Our choice |
| `refinery_count` | number of refineries that supply at least 10% of throughput | − | S&P Section 29: fewer than three is weak. agency weight |
| `complexity` | throughput-weighted complexity index of the refineries | − | S&P Section 29, Nelson Complexity Index. agency weight |
| `crack_capture` | realised gross margin per barrel / benchmark crack spread for the region | − | S&P 2011 article (crack spread). Our choice |

### Downside case
Set the crack spread to the trough of the last 10 years for four quarters (S&P Section 29 uses a 10-year midcycle). Hold utilisation at the issuer's lowest year in that window. Add one unplanned outage at the largest refinery for one quarter (Our choice). Test liquidity against an EBITDA decline of more than 30%. S&P required that for "adequate" liquidity in 2011. Add the working capital outflow when crude prices rise.

### Collateral and recovery
- Crude and product inventory: high end of the F7.5 inventory band, because both trade on open markets (Our choice).
- Refineries: appraisal in a forced sale. A single-site refiner has little going-concern diversity (F2 A7).
- Environmental and site obligations can survive the case (F5 environmental row).

### Events and calendar
- Weekly refinery utilisation and product stock data (Our choice of series).
- Planned turnaround schedules in company guidance.
- Hurricane season for coastal refineries, June to November. Review insurance cover before it (S&P Section 29).
- Renewable fuel compliance deadlines. See Open questions.

### Instructions for the analyst
1. Frame the issuer as A3 with A4 second. Report both views (F2.1).
2. Normalise EBITDA to a midcycle crack spread over 10 years.
3. Strip inventory gains and losses from EBITDA.
4. Size claims. Add environmental obligations that survive.
5. Run the trough crack spread with the outage and the working capital outflow.
6. Value at the trough multiple on midcycle EBITDA.
7. Gate: do not take a long call at a peak crack spread without the two-step S&P volatility cut.

## Sub-industry: Coal and consumable fuels (10102050)

### Drivers
| Driver | Formula from filings | Sign in spread | Source |
|---|---|---|---|
| `log_lev` | log of clip(debt / LTM EBITDA, 0.1, 20) | + | methodology 7.2. agency weight |
| `fcf_debt` | (oancf − capx) / (dlc + dltt) | − | S&P Section 24. agency weight |
| `cost_quartile` | tonnage-weighted quartile of the issuer's mines on the global cash cost curve | + | S&P Section 24: fourth-quartile assets can be idled. agency weight |
| `reserve_life` | proven and probable reserves / annual production | − | S&P Section 24: 10 years or more strong, one to three years weak. agency weight |
| `legacy_debt` | (reclamation obligations + retiree benefit obligations) / (dlc + dltt) | + | F5 environmental and pension rows. Our choice |
| `contract_cover_4` | tons sold forward at a fixed price for the next 4 quarters / forecast tons | − | S&P Section 24, contracts. Our choice |

### Downside case
Set the price to the cash cost of the 75th percentile of the global curve (Our choice). S&P says fourth-quartile assets can turn cash negative and idle in a downturn (Section 24). Apply the mining recession history: average cuts of 13% in revenue and 30% in EBITDA margin. The 2007 to 2009 cuts were 21% and 56%. For thermal coal add M2: volume falls at the rate of the last five years, and the terminal value declines (F7.4).

### Collateral and recovery
- Value mines at net asset value on the stress deck (F7 A3).
- Reclamation bonds and statutory employee benefit claims can survive the case. Deduct them from value before the waterfall (F5).
- Pension claims use the termination liability, not the accounting deficit (F8 `claim_haircut_pension`).

### Events and calendar
- Annual contract price settlements with utilities and steel makers.
- Mine safety and permit decisions.
- Rule releases on power plant emissions (M2 driver).

### Instructions for the analyst
1. Frame the issuer as A3. Add M2 for thermal coal.
2. Normalise EBITDA over a full price cycle.
3. Place each mine on the cost curve. Compute `cost_quartile`.
4. Size claims. Add reclamation, retiree benefit, and pension termination claims.
5. Run the cost-curve price case and the M2 volume decline.
6. Value at net asset value after legacy claims.
7. Gate: block a long call when most tons sit in the fourth quartile.

## Open questions
- Do `reserve_life`, `recycle_ratio`, and `bb_cushion` carry their sign on spreads? Test: add each to the energy group of `hy.sector.fairspread`. Keep a driver only with the stated sign and a positive rank IC after costs in three of the four cycles (2008, 2015, 2020, 2022).
- What is the S&P E&P and midstream industry risk after January 2021? Test: open the two commentary articles with a login and update the Industry risk block.
- When does a gathering dedication survive a producer bankruptcy? No opened source settles it. Test: write a card on the case law, then set the F5 rule for midstream contracts.
- How do renewable fuel compliance obligations rank in a refiner default? Test: write a card from a refiner bankruptcy docket, then set the claim rule.
- Is the severe deck too deep for gas-weighted issuers? Test: compare the 2015 to 2016 and 2020 troughs for oil and gas separately, and set one deck per commodity.
- The reserve, hedge, and contract drivers have no field in `data/schemas/`. Add each field with `as_of` and `available_at` before a fit.
