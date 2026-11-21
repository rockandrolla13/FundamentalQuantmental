# 40 Financials: 4010 Banks, 4020 Financial Services, 4030 Insurance

Archetype (framework F2): A8, out of scope, for banks, insurers, lenders and business development companies (BDCs). These issuers have no operating EBITDA, and debt over EBITDA does not measure them (`hy.peers.FIN_SECTORS`). Some HY issuers in these groups earn fees and have operating EBITDA. They use A6 or A4 rules (see the routing table). Modifiers that often apply: M1 (sponsor-owned insurance brokers, servicers and processors).
GICS industries covered: 401010 Banks, 401020 Thrifts and Mortgage Finance (now in 402010), 402010 Financial Services, 402020 Consumer Finance, 402030 Capital Markets, 402040 Mortgage REITs, 403010 Insurance.

## Sources
| Source | Type | Date | Opened | Pages or sections used |
|---|---|---|---|---|
| S&P Global Ratings, "Financial Institutions Rating Methodology", https://www.maalot.co.il/Publications/MT20220425162409.PDF | rating agency criteria | Dec. 9, 2021, republished March 31, 2022 | yes | paras. 2-4 (scope), paras. 89-91 (BDC asset coverage), Table 11 (leverage), para. 374 (debt to adjusted total equity) |
| S&P Global Ratings, "Sector-Specific Corporate Methodology". Public copy: South Dakota PUC docket EL26-003, Exhibit TDS-2, https://puc.sd.gov/commission/dockets/electric/2026/EL26-003/Vol2Section6/Exh2TStevens.pdf | rating agency criteria | July 7, 2025, republished Sept. 26, 2025 | yes | Nonbank Section 1 Asset Managers (exhibit pp. 218-225). Section 2 Financial Market Infrastructure (pp. 226-233). Section 3 Financial Services Finance Companies (pp. 234-241). Section 34 for transaction processors (pp. 185-188) |
| S&P Global Ratings, "Banking Industry Country Risk Assessment Methodology And Assumptions" | rating agency criteria | Dec. 9, 2021 | not opened | Named in the FI methodology, para. 1 |
| S&P Global Ratings, "Insurers Rating Methodology" and "Insurer Risk-Based Capital Adequacy--Methodology And Assumptions" | rating agency criteria | July 1, 2019 and Nov. 15, 2023 | not opened | spglobal.com returns HTTP 403 |
| S&P criteria for insurance brokers | rating agency criteria | unknown | not opened | No public copy found. We do not know which S&P section covers brokers |
| Moody's and Fitch bank, finance company and insurer methodologies | rating agency methodology | unknown | not opened | Login pages |

## Industry risk
- S&P cyclicality assessment: not applicable to banks. S&P rates banks from a Banking Industry Country Risk Assessment (BICRA), not opened. The 2013 industry risk table covers nonfinancial industries only.
- S&P competitive risk and growth assessment: not applicable to banks and insurers. Financial services finance companies, asset managers and financial market infrastructure use the corporate framework (Sector-Specific Corporate Methodology, nonbank Sections 1-3). We did not find their industry risk values.

## Route rule
S&P splits the group by the main risk (FI methodology, paras. 2-4):
- Asset quality, funds and liquidity, and tangible capital are the main risks. The issuer is a financial institution. Route it to A8.
- The ability to generate cash flow is the main risk, more than capital to absorb credit losses. The issuer is a corporate. Use A6 or A4 rules with operating EBITDA.

Apply the rule in this order:
1. The issuer holds a bank charter or an insurance licence at the rated entity. Route it to A8.
2. The issuer is a BDC or a lender that funds loans on its balance sheet. Route it to A8.
3. More than half of revenue is fees, commissions or service income, and credit losses are small. Route it to A6 or A4 by the table below.
4. Otherwise route it to A8 and write the one-line reason in `issuer_state`.

| Issuer type in GICS 40 | Route | Reason |
|---|---|---|
| Insurance brokers | A6, with M1 | Recurring commission revenue, low capex, intangibles dominate. Our choice. S&P criteria not opened |
| Transaction and payment processors (moved to GICS 4020 in 2023) | A6 | S&P keeps them with software margins (Section 34) and lists money transaction processors under finance companies (nonbank Section 3) |
| Asset managers | A6, with a market beta in the downside | S&P core ratio is debt to adjusted EBITDA (nonbank Section 1) |
| Exchanges and clearing houses | A6 | S&P uses a three-year weighted ratio set: previous year 20%, current year 40%, next year 40% (nonbank Section 2) |
| Mortgage servicers, loan originators that sell their loans, debt purchasers, fleet services | A4 | Volume moves with rates and the cycle. S&P rates them as finance companies on cash flow (nonbank Section 3) |
| Consumer finance lenders, BDCs, banks, insurers, mortgage REITs | A8 | Capital and funds risk dominate (FI methodology, para. 2) |

## EBITDA, leverage and coverage
- EBITDA definition, A6 and A4 routes: analyst EBITDA under F3. For brokers, do not add back acquisition earn-outs that recur (F3 C3). For servicers, remove fair value marks on servicing rights from EBITDA.
- Leverage measure, A6 and A4 routes: `lev_gc_total` (F5). For finance companies, net warehouse debt against conforming loans only when a government-sponsored buyer is certain to buy them soon (nonbank Section 3).
- Coverage measure: `coverage` (F5).
- Agency supplementary ratios:
  - Finance companies (nonbank Section 3): EBITDA to interest and debt to tangible equity. Tangible equity is total equity less goodwill and nonservicing intangibles. S&P scale: below 1.0x minimal, 1.0x to 2.0x modest, 2.0x to 3.0x intermediate, 3.0x to 4.0x significant, 4.0x to 5.0x aggressive, above 5.0x highly leveraged.
  - Finance companies: S&P weights ratios over three years: previous year 20%, current year 40%, next year 40%.
  - Asset managers (nonbank Section 1): debt to adjusted EBITDA, with haircuts on realised performance fees and investment income.

## Drivers

### A6 and A4 routes (fee businesses)
| Driver | Formula from filings | Sign in spread | Source |
|---|---|---|---|
| `log_lev` | log of `(dlc + dltt) / oibdp`, clipped | + | Our choice |
| `fcf_debt` | `(oancf − capx) / (dlc + dltt)` | − | Our choice |
| `organic_growth` | Reported growth less M&A and FX (F8) | − | Our choice. Brokers grow by acquisition, so organic growth shows the base |
| `debt_tangible_equity` | `(dlc + dltt) / (seq − intan + servicing rights)`. Compustat `intan` holds goodwill | + | agency weight: S&P nonbank Section 3 scale |
| `warehouse_share` | Short-term asset-specific debt over total debt | + | agency weight: S&P nonbank Section 3, asset-specific funds as a risk subfactor |

### A8 inputs a separate rulebook needs
| Input | Formula from filings | Sign in spread | Source |
|---|---|---|---|
| Leverage on equity | Debt to adjusted total equity | + | agency weight: S&P FI methodology, Table 11, para. 374 |
| BDC asset coverage | Assets over senior securities, regulatory definition | − | agency weight: S&P FI methodology, paras. 89-91. Risk zone 200% to 220%, or 150% to 165% under the modified test |
| Credit losses | Net charge-offs over average loans, and non-accruals at cost over the portfolio | + | Our choice |
| Funds mix | Secured warehouse, repo and ABS debt over total debt | + | agency weight: S&P nonbank Section 3 |
| Capital, banks and insurers | Regulatory capital ratio, or S&P risk-adjusted capital | − | agency weight: S&P FI methodology. Insurer criteria not opened |

## Downside case
- A6 and A4 routes: cut fee revenue by the issuer's worst peak-to-trough fall. For asset managers, cut assets under management by the worst equity market fall of the last two cycles. For servicers and originators, cut origination volume by the worst 4-quarter fall in the issuer's history.
- A8: out of scope. A separate rulebook must stress credit losses by loan vintage, the loss of warehouse and repo lines, and a capital ratio breach.

## Collateral and recovery
- Banks and insurance companies cannot file under Chapter 7 or Chapter 11 (Bankruptcy Code §109(b)). Regulators resolve them, and insurers go through state receivership with policyholders first. The F5 claims table does not apply to them. Holdco bonds rank behind every operating creditor.
- A bank or insurer holdco can file. Its value is the equity of the regulated subsidiary after the regulator acts. Treat holdco bonds as structurally subordinated (F2 A7 rule).
- Brokers and processors: value is the client book as a going concern (F2 A6). Client funds held in trust are not estate assets.
- Servicers: servicing rights hold value but need investor and agency consent to transfer. Read the consent terms.

## Events and calendar
- Regulatory capital and stress test results for banks.
- Insurance catastrophe seasons and reserve reviews.
- Interest rate decisions, for servicers, originators and brokers with variable-rate debt.
- Changes to government-sponsored buyer eligibility rules for mortgages.
- BDC asset coverage at each quarter end.

## Instructions for the analyst
1. Apply the route rule in order. Record the route and the reason in `issuer_state`.
2. Stop at A8. Write "out of scope" in the memo and name the separate rulebook it needs.
3. For A6 and A4 routes, build analyst EBITDA. Treat recurrent earn-outs as cost.
4. Compute `lev_gc_total`. Add debt to tangible equity for finance companies.
5. Size liquidity with warehouse line maturities. A line loss is a liquidity event.
6. Run the fee, assets under management or volume case for the route.
7. Value fee businesses on recurring revenue. Gate the memo under F9.

## Open questions
- Which S&P criteria cover insurance brokers? Not found. Find the criteria and confirm the A6 route.
- Does the route rule split HY spreads into two groups that fit separately? Test: fit the pooled model on the A6 and A4 routes only and compare residuals with GICS 45 software.
- What does a separate A8 rulebook need first? Decide with a decision page. Candidates: debt to tangible equity, credit losses and funds mix.
