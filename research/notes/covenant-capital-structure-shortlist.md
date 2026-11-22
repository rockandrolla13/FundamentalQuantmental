# Covenant and capital structure sources shortlist

Date: 2026-11-21. Status: candidates only. Nobody has opened these sources yet. No card exists for any of them.

## Question
Which sources test how covenants, debt priority, and liability management change bond prices, default, or recovery? Framework F4 (refinance access), F5 (claims), F7 (the liability management score) and F8 (covenants and documents) use these rules. Most of them cite only Gatto (2023).

## Method
1. Search OpenAlex with 32 queries: 10 on covenants, 4 and then 3 more on liability management, 10 on capital structure, plus 5 targeted queries. The scripts and raw hits stay in the session scratchpad, not in git.
2. Keep corporate-debt sources with 30 or more citations. Keep a newer source with fewer citations when it tests HY bonds directly.
3. Drop sovereign-debt sources and sources that already have a card. `ivashina-iverson-smith-2016-chapter-11-claims.md`, `benmelech-bergman-2011-collateral-channel.md` and `boyarchenko-elias-2024-debt-structure-cycle.md` already exist.
4. Record the OpenAlex metadata below. The metadata is not evidence. A card needs the full text.

"OA" marks a source with an open-access link in OpenAlex. "Paywalled" marks a source without one.

## Covenants: which ones bondholders get, and what they are worth

| Source | What it can settle | Section | Access |
|---|---|---|---|
| Bräuning, Ivashina and Ozdagli (2022), "High-Yield Debt Covenants and Their Real Effects", NBER WP 29888, doi 10.3386/w29888 | Despite the title, the sample is leveraged loans, not bonds. It tests what an incurrence covenant trigger does to investment and debt. Card written 2026-11-21. | F8 covenants | OA, downloaded |
| Ivashina and Vallée (2020), "Weak Credit Covenants", NBER | How carve-outs and baskets weaken loan covenants. This is the mechanism behind most liability management deals. Card written 2026-11-21. | F7 LM score, F8 | OA, downloaded |
| Bradley and Roberts (2015), "The Structure and Pricing of Corporate Debt Covenants", *Quarterly Journal of Finance* | Whether more covenants lower the loan spread, and by how much. | F8 | OA |
| Reisel (2014), "On the value of restrictive covenants: Empirical investigation of public bond issues", *Journal of Corporate Finance*, doi 10.1016/j.jcorpfin.2014.05.011 | The yield value of each covenant type in public bonds. | F8 | OA |
| Chava, Kumar and Warga (2010), "Managerial Agency and Bond Covenants", *Review of Financial Studies*, doi 10.1093/rfs/hhp072 | Which firm traits predict which bond covenants. | F8 | OA |
| Billett, King and Mauer (2007), "Growth Opportunities and the Choice of Leverage, Debt Maturity, and Covenants", *Journal of Finance* | How covenants trade off against leverage and maturity. | F8 | Paywalled |
| Becker and Ivashina (2016), "Covenant-Light Contracts and Creditor Coordination", SSRN | Why cov-lite loans spread, and what they mean for creditor coordination in a default. | F5, F7 | OA |
| Billett, Elkamhi, Popov and Pungaliya (2016), "Bank Skin in the Game and Loan Contract Design: Evidence from Covenant-Lite Loans", *JFQA* | Who holds cov-lite loans, and how that changes the contract. | F8 | OA |
| Feldhütter, Hotchkiss and Karakaş (2016), "The value of creditor control in corporate bonds", *Journal of Financial Economics* | The price of the right to vote on a restructuring, measured from bond prices. | F7 LM score | OA |
| Denis and Wang (2014), "Debt Covenant Re-Negotiations and Creditor Control Rights", *Journal of Financial Economics* | How often lenders renegotiate covenants outside default, and what they extract. | F4, F8 | OA |

## Event risk: buyouts and change of control

| Source | What it can settle | Section | Access |
|---|---|---|---|
| Asquith and Wizman (1990), "Event risk, covenants, and bondholder returns in leveraged buyouts", *Journal of Financial Economics* | Bondholder losses in an LBO, with and without protective covenants. | F11 events, F08 factor | Paywalled |
| Billett, Jiang and Lie (2010), "The effect of change-in-control covenants on takeovers: Evidence from leveraged buyouts", *Journal of Corporate Finance* | Whether a change-of-control put deters an LBO, or only prices it. | F8, F11 | Paywalled |
| Eisenthal-Berkovitz, Feldhütter and Vig (2016), "Leveraged Buyouts and Credit Spreads", *Journal of Financial Economics* | How far LBO risk explains spread levels before any deal. | F08 factor, F11 | OA |
| Cremers, Nair and Wei (2007), "Governance Mechanisms and Bond Prices", *Review of Financial Studies* | How takeover defences change bond yields, with and without event-risk covenants. | F8 | OA |

## Liability management and distressed exchanges

| Source | What it can settle | Section | Access |
|---|---|---|---|
| Chatterjee, Dhillon and Ramírez (1995), "Coercive tender and exchange offers in distressed high-yield debt restructurings", *Journal of Financial Economics* | How coercive offers work on HY holders, and who gains. This is the closest academic source to an uptier. | F7 LM score | Paywalled |
| James (1996), "Bank Debt Restructurings and the Composition of Exchange Offers in Financial Distress", *Journal of Finance* | How bank concessions change what bondholders accept in an exchange. | F7 | Paywalled |
| Danis (2016), "Do Empty Creditors Matter? Evidence from Distressed Exchange Offers", *Management Science* | Whether CDS-hedged holders block exchanges, and what that does to the success rate. | F7 | OA, SSRN 2012 version |
| Bedendo, Cathcart and El-Jahel (2016), "Distressed Debt Restructuring in the Presence of Credit Default Swaps", *JMCB*, doi 10.1111/jmcb.12294 | Whether CDS changes the choice between an exchange and a filing. | F7 | OA |

## Capital structure: priority, security and recovery

| Source | What it can settle | Section | Access |
|---|---|---|---|
| Rauh and Sufi (2010), "Capital Structure and Debt Structure", *Review of Financial Studies* | How low-rated firms spread debt across secured, unsecured and subordinated classes. Base fact for F5. | F5 | OA |
| Colla, Ippolito and Li (2020), "Debt Structure", *Annual Review of Financial Economics* | A survey of the debt structure literature. Use it to find the tests the other rows miss. | F5 | OA |
| Donaldson, Gromb and Piacentino (2025), "Conflicting Priorities: A Theory of Covenants and Collateral", *Journal of Finance* | A theory of why covenants and collateral fail to protect against new priority debt. The theory behind priming. | F5, F7 | OA |
| Benmelech, Kumar and Rajan (2024), "The Decline of Secured Debt", *Journal of Finance* | When firms issue secured debt, and how that changes over the cycle. | F5 | OA |
| Altman, Brady, Resti and Sironi (2005), "The Link between Default and Recovery Rates", *Journal of Business* | Recovery falls when default rates rise. Input to the F6 and F7 recovery cases. | F6, F7 | OA |
| Varma and Cantor (2005), "Determinants of Recovery Rates on Defaulted Bonds and Loans for North American Corporate Issuers", *Journal of Fixed Income* | Recovery by seniority and by the debt cushion below each claim. | F5, F7 | Paywalled |
| Eberhart, Moore and Roenfeldt (1990), "Security Pricing and Deviations from the Absolute Priority Rule in Bankruptcy Proceedings", *Journal of Finance* | How far payouts in Chapter 11 depart from strict priority, and whether prices anticipate it. | F5 waterfall | Paywalled |
| Betker (1995), "Management's Incentives, Equity's Bargaining Power, and Deviations from Absolute Priority", *Journal of Business* | What predicts a larger departure from priority. | F5 | OA |
| Valta (2016), "Strategic Default, Debt Structure, and Stock Returns", *JFQA* | How a debt structure that is hard to renegotiate changes default risk. | F5, F7 | OA |
| Morellec (2001), "Asset liquidity, capital structure, and secured debt", *Journal of Financial Economics* | A model of how asset liquidity sets debt capacity and the value of security. | F5 | OA |

## Gaps the search did not fill
1. Post-2020 liability management. OpenAlex returned no finance paper on uptier deals, drop-downs or "creditor-on-creditor violence" for the queries used. Law reviews and SSRN hold this literature. Search SSRN by hand, because SSRN blocks scripts.
2. Covenant tests on HY bonds. Bräuning, Ivashina and Ozdagli (2022) study loans, not bonds, so the list holds no direct HY bond covenant test. Vendor indexes such as Moody's covenant quality scores are not academic sources.
3. Holding company and structural subordination. No corporate source matched the queries.

## Decision
None yet. Open each source, then write one card per source in `research/cards/`. Start with Bräuning, Ivashina and Ozdagli (2022) and Ivashina and Vallée (2020). Together they cover HY bond covenants and the baskets that liability management deals exploit.
