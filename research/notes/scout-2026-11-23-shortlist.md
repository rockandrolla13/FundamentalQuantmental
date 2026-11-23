# Scout shortlist, 2026-11-23: five gaps

Date: 2026-11-23. Status: candidates only. Nobody has opened these sources. No card exists for any of them. Five scout agents searched OpenAlex and Semantic Scholar, with about 110 queries in all. Every DOI below comes from an API response. Two DOIs had a year that did not match. I checked both titles against OpenAlex, and both are correct. OpenAlex stores the year of the first working-paper version, so this note gives the journal year that the DOI implies.

Each agent excluded the sources on file: `research/cards/`, `research/reading-list.md`, `sector-sources-shortlist.md` and `covenant-capital-structure-shortlist.md`. Varma and Cantor (2005) came up twice. It is already on the covenant shortlist, so this note leaves it out.

The metadata is not evidence. A card needs the full text.

## 1. Support label against support contents (methodology 4.7.3)

Finding: no source tests contract terms in bond spreads. The terms are tenor against debt tenor, cancellability, and commenced against uncommenced. So the 4.7.3 claim has no test in the literature.

| Source | What it can settle | Access |
|---|---|---|
| Van Nieuwerburgh (2026), "Financing the AI Buildout", NBER WP 35865 | Data centre financing, off-balance-sheet structures (leases, SPVs, residual value guarantees), and asset life against debt term. It is the first working paper on file for this sector. The user's skill library holds it as `van-nieuwerburgh-financing-ai-buildout`. | Skill on file; open the PDF |
| Cen, Dasgupta, Elkamhi et al. (2015), *Review of Finance*, doi 10.1093/rof/rfv014 | Whether a link to a reputable principal customer lowers the loan spread. This is a test of the label, not of the terms. | OA |
| Campello and Gao (2017), *JFE*, doi 10.1016/j.jfineco.2016.03.010 | Customer concentration against loan spread and covenants. | OA |
| Ağca, Babich, Birge et al. (2021), *Management Science*, doi 10.1287/mnsc.2021.4174 | How fast a customer's credit shock reaches the supplier's CDS. | OA |
| Pinto, Marques and Megginson (2020), *JCF*, doi 10.1016/j.jcorpfin.2020.101580 | Ring-fenced SPV pricing against straight corporate debt. It bears on `q^reach`. | OA |
| Lee, Naranjo and Sirmans (2021), *RAPS*, doi 10.1093/rapstu/raaa025 | Slow information diffusion in credit prices. It bears on the 6-month catch-up window. | OA |

## 2. Covenants and liability management (F7, F8)

Finding: gaps 1 and 2 of the covenant shortlist are now partly filled. Gap 3, structural subordination, stays almost empty.

| Source | What it can settle | Access |
|---|---|---|
| Buccola and Nini (2024), *Journal of Legal Studies*, doi 10.1086/729676 | Loan terms that block uptiers after Serta (2020). The F7 document lines by vintage. | OA |
| Roe and Rotaru (2026), ECGI Law WP 968, doi 10.67929/ecgi-law-968-2026 | The abstract says that most firms with a coercive non-pro-rata deal file anyway. A prior for `pi_lme` and `R_LME`. | OA |
| Handler, Jankowitsch and Weiss (2026), *RAPS*, doi 10.1093/rapstu/raag004 | Covenant prices from secondary bond trades, varying over time. All US bonds, not HY only. | OA |
| Gietzmann, Isidro and Raonic (2021), *JAAF*, doi 10.1177/0148558x20987384 | The sign of a covenant-lite flag on HY bond spreads. | OA |
| Fridson, Xu and Liu (2014), *JACF*, doi 10.1111/jacf.12069 | Moody's covenant quality scores against new-issue HY yields. | Paywalled |
| Antill, Wang and Jiang (2024), NBER WP 32823, doi 10.3386/w32823 | A model: the threat of creditor-on-creditor violence raises the secured spread before any deal. A falsifiable claim, not a test. | OA |

## 3. Rate and inflation stress (methodology 9.2)

Finding: nothing calibrates the 50% sticky pass-through cut-off or the 2-year maturity window. Both stay Our choice.

| Source | What it can settle | Access |
|---|---|---|
| Ippolito, Ozdagli and Pérez-Orive (2018), *JME*, doi 10.1016/j.jmoneco.2018.02.001 | The floating-rate channel, `phi_float`. Equity and real outcomes, not spreads. | OA |
| Jungherr, Meier, Reinelt and Schott (2024), Fed IFDP 1402, doi 10.17016/ifdp.2024.1402 | Firms with more maturing debt react more to policy. Check its maturity window against our 2 years. | OA |
| Guo, Kontonikas and Maio (2020), *RAPS*, doi 10.1093/rapstu/raaa005 | Bond returns after policy shocks, by rating. A prior for the policy beta. | OA |
| Gürkaynak, Karasoy-Can and Lee (2022), *JF*, doi 10.1111/jofi.13163 | Debt type and maturity shape the stock response to the Fed. | OA |
| Kang and Pflueger (2015), *JF*, doi 10.1111/jofi.12195 | Counter-source: the inflation fear that bonds price is deflation. Record both views and the conditions for each. | OA |
| Roulet (2020), OECD, doi 10.1787/788a0c77-en | A coverage stress test on HY issuers. It may give coverage cut-offs for `cov_stress`. | OA |

## 4. Sector driver tests (docs/sectors, F2)

Finding: no source tests a sector driver list against US HY spreads. Six sectors have no test at all: telecom, software, retail, hospitals, autos and airlines.

| Source | What it can settle | Sectors | Access |
|---|---|---|---|
| Altman and Kishore (1996), *FAJ*, doi 10.2469/faj.v52.n6.2040 | Recovery by sector at fixed seniority: utilities 70%, chemicals and petroleum 63%. | 5510, 1510, 1010 | Paywalled |
| Apergis (2019), *QREF*, doi 10.1016/j.qref.2019.01.012 | Oil price against HY spreads, energy against non-energy. European sample. | 1010 | Paywalled |
| Ellis (2020), *IJFS*, doi 10.3390/ijfs8010001 | No consistent default contagion across sectors. It tests the F2.7 collateral-only rule. | All | OA |
| Chuang and Chen (2023), *Econometrics*, doi 10.3390/econometrics11010006 | Industry distress cuts loan recovery, by quantile. | All | OA |
| Jostova, Nikolova, Philipov and Stahel (2013), *RFS*, doi 10.1093/rfs/hht022 | Bond momentum is strongest in HY. Bond level, not industry level. | None | OA |

## 5. Books to compare with Gatto

Finding: `research/comparisons/` is empty. CLAUDE.md asks for one comparison per book, so this gap comes before any new title.

| Book | What it would add or challenge | Identifier |
|---|---|---|
| Duffie (2011), *Measuring Corporate Default Risk*, OUP | A PD model with macro covariates and frailty, for the PD calibration by cycle phase | doi 10.1093/acprof:oso/9780199279234.001.0001 |
| Harmon (2024), *The Financial Restructuring Tool Set*, Columbia | Liability management and out-of-court tools beyond Chapter 11 | ISBN 9780231216982 |
| Barclays QPS (2012), *Quantitative Credit Portfolio Management*, Wiley | DTS and liquidity cost scores. The earlier book of the Dynkin team. | doi 10.1002/9781119202851 |
| Ilmanen (2011), *Expected Returns*, Wiley | The credit premium, carry and timing across cycles | doi 10.1002/9781118467190 |
| Gilson (2010, 2nd ed.), *Creating Value Through Corporate Restructuring*, Wiley | Case evidence on fulcrum securities and value transfer | ISBN 978-0-470-50352-2 |

## Decision

None yet. Card in this order. The first two each settle a stated open item.
1. Van Nieuwerburgh (2026), for 4.7.3. It is the only sector source beyond a practitioner essay.
2. Buccola and Nini (2024) and Roe and Rotaru (2026), for F7.
3. Jungherr et al. (2024), to check the 2-year window of 9.2.
4. Write the first comparison in `research/comparisons/`, Dynkin et al. (2021) against Gatto, because the book and its cards are already on file.
