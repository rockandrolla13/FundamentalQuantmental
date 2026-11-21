# Sector sources shortlist for the archetypes of framework F2

Date: 2026-11-21. Status: candidates only. Nobody has opened these sources yet. No card exists for any of them.

## Question
Which sources test a sector-specific driver against spreads, default, or recovery? `docs/factors/SECTOR-models.md` section 1 records the gap: every driver list in its section 3.1 is "Our choice".

## Method
1. Search OpenAlex with 4 to 5 queries per archetype, plus 4 cross-sector queries. Scripts and raw hits stay in the session scratchpad, not in git.
2. Keep sources with 20 or more citations, or sources that test credit outcomes directly.
3. Drop sources that already have a card. Gilje, Loutskina and Murphy (2020) and Lim, Mann and Mihov (2017) already have cards.
4. Record the OpenAlex metadata below. The metadata is not evidence. A card needs the full text (CLAUDE.md research protocol, step 2).

"OA" marks a source with an open-access link in OpenAlex. "Paywalled" marks a source with no such link. Use the UCL catalogue or a manual download for a paywalled source (memory: literature retrieval routes).

## Cross-sector: does the sector change the default model?
These sources settle whether one driver list per sector is better than one pooled list with sector effects.

| Source | What it can settle | Access |
|---|---|---|
| Chava and Jarrow (2004), "Bankruptcy Prediction with Industry Effects", *Review of Finance* 8(4), doi 10.1093/rof/8.4.537 | Whether industry groups change the intercept only, or the slopes too. This decides between the pooled fallback and the per-sector fits of `hy.sector.fairspread`. | OA, doi 10.2139/ssrn.287474 |
| Platt and Platt (1991), "A note on the use of industry-relative ratios in bankruptcy prediction", *Journal of Banking & Finance*, doi 10.1016/0378-4266(91)90057-s | Whether ratios divided by the industry mean predict failure better than raw ratios. This tests the within-sector z of SECTOR-models section 3.1. | Paywalled |
| Bruche and González-Aguado (2010), "Recovery rates, default probabilities, and the credit cycle", *Journal of Banking & Finance*, doi 10.1016/j.jbankfin.2009.04.009 | How recovery moves with the cycle. Input to framework F7 recovery rules. | OA, openaccess.city.ac.uk eprint 2790 |

## A1 Lease-heavy consumer

| Source | What it can settle | Access |
|---|---|---|
| Eisfeldt and Rampini (2009), "Leasing, Ability to Repossess, and Debt Capacity", *Review of Financial Studies*, doi 10.1093/rfs/hhn026 | Why constrained firms lease, and how much debt capacity a lease uses. Input to the 8 times rent multiple of `log_lev_lease`. | OA, Census CES-WP-07-19 |
| Sharpe and Nguyen (1995), "Capital market imperfections and the incentive to lease", *Journal of Financial Economics*, doi 10.1016/0304-405x(95)00830-8 | Which firm traits predict a high lease share. Input to the A1 trigger "rent above 8% of sales". | Paywalled |
| Gu and Kim (2002), "Determinants of Restaurant Systematic Risk: A Reexamination", *Journal of Hospitality Financial Management*, doi 10.1080/10913211.2002.10653757 | Which restaurant ratios drive risk. Equity beta only, not spreads. | OA, UMass ScholarWorks |

## A2 Health care services

| Source | What it can settle | Access |
|---|---|---|
| Adelino, Lewellen and McCartney (2022), "Hospital Financial Health and Clinical Choices: Evidence from the Financial Crisis", *Management Science*, doi 10.1287/mnsc.2020.3944 | How a shock to hospital finances changes behaviour and revenue. | OA, doi 10.2139/ssrn.3224667 |
| Blavin (2016), "Association Between the 2014 Medicaid Expansion and US Hospital Finances", *JAMA*, doi 10.1001/jama.2016.14765 | The size of a payer-mix shock on uncompensated care and margin. Input to the A2 downside case "the last reimbursement change". | Paywalled |
| Richards and Whaley (2024), "Hospital behavior over the private equity life cycle", *Journal of Health Economics*, doi 10.1016/j.jhealeco.2024.102902 | What changes after a leveraged buyout of a hospital. Most HY hospital issuers have a sponsor. | OA, accepted manuscript |
| Malone, Pink and Holmes (2024), "An updated model of rural hospital financial distress", *Journal of Rural Health*, doi 10.1111/jrh.12882 | A tested distress model with hospital-specific predictors. | OA, UNC repository copy. Downloaded 2026-11-21 |
| Enumah and Chang (2021), "Predictors of Financial Distress Among Private U.S. Hospitals", *Journal of Surgical Research*, doi 10.1016/j.jss.2021.05.025 | A second set of tested hospital distress predictors. | OA, PMC8678151 |

## A3 Commodity producers

| Source | What it can settle | Access |
|---|---|---|
| Jin and Jorion (2006), "Firm Value and Hedging: Evidence from U.S. Oil and Gas Producers", *Journal of Finance*, doi 10.1111/j.1540-6261.2006.00858.x | Whether the hedge book changes value and price sensitivity. Input to the A3 rule "hedge book marked". | Paywalled |
| Aretz, Banerjee and Pryshchepa (2019), "In the Path of the Storm: Does Distress Cause Non-Financial Firms to Risk-Shift?", *Review of Finance*, doi 10.1093/rof/rfy028 | Whether distressed producers take more risk. Uses oil and gas firms as the setting, from the title. | OA, doi 10.2139/ssrn.2558756 |
| Da Fonseca, Ignatieva and Ziveyi (2016), "Explaining credit default swap spreads by means of realized jumps and volatilities in the energy market", *Energy Economics*, doi 10.1016/j.eneco.2016.03.022 | Whether energy price jumps and volatility explain energy CDS spreads. The only direct spread test found for A3. | OA, AUT repository |
| Gevorkyan and Semmler (2016), "Oil price, overleveraging and shakeout in the shale energy sector", *Economic Modelling*, doi 10.1016/j.econmod.2015.12.029 | A model of shale leverage and the 2015 price fall. Theory, not a test. | OA, working paper |

## A4 Cyclical industrials

| Source | What it can settle | Access |
|---|---|---|
| Donangelo, Gourio, Kehrig and Palacios (2019), "The cross-section of labor leverage and equity returns", *Journal of Financial Economics*, doi 10.1016/j.jfineco.2018.10.016 | Whether a high labour share acts as operating leverage. Input to the A4 "operating leverage measured" rule. Equity returns only. | OA, Chicago Fed WP 2017-22 |

## A5 Asset-heavy contracted

| Source | What it can settle | Access |
|---|---|---|
| Grammenos and Arkoulis (2003), "Determinants of spreads on new high yield bonds of shipping companies", *Transportation Research Part E*, doi 10.1016/s1366-5545(03)00054-1 | Which drivers set HY shipping spreads at issue. A direct spread test for one A5 industry. | Paywalled |
| Ciliberto and Schenone (2012), "Bankruptcy and product-market competition: Evidence from the airline industry", *International Journal of Industrial Organization*, doi 10.1016/j.ijindorg.2012.06.004 | What a filing does to capacity and price for the airline and its rivals. Input to A5 event classes. | OA, MPRA 25714. Downloaded 2026-11-21 |
| Kavussanos and Tsouknidis, "The determinants of credit spread changes in global shipping bonds", SSRN 2640579 | Which bond, issuer, freight and macro variables move shipping bond spreads over time. A direct spread test for one A5 industry. The user found it on 2026-11-21. | Downloaded 2026-11-21 |

## A6 Software and technology

| Source | What it can settle | Access |
|---|---|---|
| Mann (2018), "Creditor rights and innovation: Evidence from patent collateral", *Journal of Financial Economics*, doi 10.1016/j.jfineco.2018.07.001 | How often firms pledge patents, and what creditor rights do to that debt. Input to the A6 collateral basis. | OA, doi 10.2139/ssrn.2356015 |
| Hochberg, Serrano and Ziedonis (2018), "Patent Collateral, Investor Commitment, and the Market for Venture Lending", *Journal of Financial Economics*, doi 10.1016/j.jfineco.2018.06.003 | Whether a liquid patent resale market raises lending. Venture debt, not HY. | OA, doi 10.2139/ssrn.2506911 |
| Ewens, Peters and Wang (2025), "Measuring Intangible Capital with Market Prices", *Management Science*, doi 10.1287/mnsc.2021.02058 | A measured value of intangible capital from asset sale prices. Input to the A6 recovery basis. | OA, doi 10.31235/osf.io/kvp2f |

## Gaps the search did not fill
1. A3: no peer-reviewed test of oil price moves on US HY energy bond spreads. Search next on the 2015 to 2016 energy default wave.
2. A5: no source on telecom or cable leverage and spreads.
3. A6: no source on software leverage, recurring revenue, or recovery in software defaults.
4. A2: no source on spreads of for-profit HY hospital bonds. The hits cover hospital distress and municipal bonds.
5. A4: no direct test of peak-to-trough revenue against default.

## Decision
None yet. Open each source, then write one card per source in `research/cards/`. Start with Chava and Jarrow (2004), because its result decides between per-sector fits and the pooled model for every archetype.
