# 5010 Telecommunication Services

Archetype (framework F2): A5. Capex runs above 15% of sales, and the network is the asset. Modifiers that often apply: M2 (copper wireline and geostationary satellite video), M1 (sponsor-owned fibre and alternative carriers), M3 (tower and fibre lessors with a few carrier tenants).
GICS industries covered: 501010 Diversified Telecommunication Services (50101010 Alternative Carriers, 50101020 Integrated Telecommunication Services), 501020 Wireless Telecommunication Services. Cable and satellite TV sit in 5020 (see `5020-media-entertainment.md`). Tower REITs sit in 6010. Their rules are in this page, sub-section "Towers and fibre infrastructure".

## Sources
| Source | Type | Date | Opened | Pages or sections used |
|---|---|---|---|---|
| S&P Global Ratings, "Sector-Specific Corporate Methodology". Public copy: South Dakota PUC docket EL26-003, Exhibit TDS-2, https://puc.sd.gov/commission/dockets/electric/2026/EL26-003/Vol2Section6/Exh2TStevens.pdf | rating agency criteria | July 7, 2025, republished Sept. 26, 2025 | yes | Section 35 Telecommunications (exhibit pp. 189-193). Section 13 Digital Infrastructure (pp. 61-78). Appendix 3 margin and SER tables (pp. 244-252). Revisions note, p. 253 |
| S&P Global Ratings, "Key Credit Factors For The Telecommunications And Cable Industry", archive page https://disclosure.spglobal.com/ratings/jp/regulatory/article/-/view/sourceId/8365003 | rating agency criteria. Status not verified, may be superseded by the 2025 methodology | June 22, 2014 | not opened | Search result only |
| S&P Global Ratings, "Standard & Poor's Assigns Industry Risk Assessments To 38 Nonfinancial Corporate Industries", https://maalot.co.il/publications/MT20150505165520.pdf | rating agency table | Nov. 20, 2013 | yes | Industry risk table, p. 2 |
| Moody's, "Telecommunications Service Providers" | rating agency methodology | Dec. 2025 | not opened | ratings.moodys.com returns a login page |
| Repo cards | none | | | No card in `research/cards` covers telecom churn or spectrum |

## Industry risk
- S&P cyclicality assessment: telecommunications and cable "low risk" (2) (2013 table, p. 2). Digital infrastructure "low risk" (Section 13, exhibit p. 61).
- S&P competitive risk and growth assessment: telecommunications and cable "intermediate risk" (3). Industry risk "intermediate" (3) (2013 table). Digital infrastructure industry risk "low" (2) (Section 13). The telecom values are from 2013.

## EBITDA, leverage and coverage
- EBITDA definition: EBITDA less capex beside EBITDA (F2 A5). Keep lease cost for towers, sites and dark fibre in the lease adjustment. Remove gains on tower, fibre and spectrum sales (F3 C4).
- Leverage measure: `lev_lease_adj` for issuers with large site and tower leases. Otherwise `lev_gc_total` (F5). Add securitised handset receivables to debt (card `sp-global-2019-ratios-and-adjustments.md`, para. 9).
- Coverage measure: `coverage` (F5). It subtracts capex.
- Agency supplementary ratios (Section 35, exhibit p. 193): FOCF to debt first, because of capital intensity. DCF to debt for issuers with large dividends.
- EBITDA margin bands (Appendix 3), below average then above average:
  - Integrated, wireless and fixed-line carriers: below 25%, above 40%.
  - Direct-to-home: below 20%, above 30%.
  - Broadcast towers and fixed satellite service: below 40%, above 60%.
  - Digital infrastructure: towers below 60%, above 80%. Fibre below 40%, above 55%. Data centres below 35%, above 45%.

## Drivers
| Driver | Formula from filings | Sign in spread | Source |
|---|---|---|---|
| `log_lev` | log of `(dlc + dltt) / oibdp`, clipped | + | Our choice |
| `fcf_debt` | `(oancf − capx) / (dlc + dltt)` | − | agency weight: S&P Section 35, FOCF to debt first |
| `capex_int` | `capx / sale` | + | Our choice (F2 A5) |
| `churn` | Monthly customer churn, from the filing | + | agency weight: S&P Section 35, high churn raises sales and promotion cost |
| `arpu_trend` | 8-quarter slope t-statistic of revenue per user | − | Our choice |
| `legacy_share` | Copper voice and legacy data share of revenue | + | Our choice. M2 trigger |

### Wireline and fibre
- Fibre to the premises lowers churn and supports price (S&P Section 35). Track homes passed by fibre, penetration and cost per home passed.
- Copper revenue declines without a cyclical cause. Apply M2 and treat restructuring as recurrent.
- Fibre build capex is growth capex. Split it from maintenance capex for `capex_flex` (F4).

### Wireless
- Spectrum depth sets capacity (S&P Section 35). Count spectrum purchases as capex in the cash view.
- Handset instalment plans build receivables. Their securitisation adds debt.
- Regional carriers pay roam fees to national carriers (S&P Section 35). Read the roam cost line.

### Towers and fibre infrastructure (S&P Section 13)
- Contract tenor sets revenue visibility. S&P sets renewal risk aside when the average lease tenor left is 10 years or more. Below 5 years, renewal terms dominate.
- Revenue comes from a few national carriers. Apply M3. Model a carrier merger that removes duplicate sites.
- Tenancy ratio and escalators drive margin. Read the escalator type: fixed or index.

### Satellite
- Contract backlog and transponder fill set revenue. Low-orbit networks compete with geostationary video and data. Apply M2 to geostationary video.
- Launch failure and in-orbit failure are event risks. Read the in-orbit insurance.

## Downside case
1. Hold the subscriber count. Cut ARPU by the worst 8-quarter fall in the issuer's history or in its nearest peer's (Our choice).
2. Raise churn by one third and hold the acquisition cost per gross add (Our choice).
3. Hold committed capex for network builds and grant milestones. Cut only uncommitted capex.
4. Towers and fibre: remove the sites or routes of one carrier at its next renewal date.
5. Wireline under M2: extend the copper decline at its 3-year rate with no floor.

## Collateral and recovery
- US spectrum licences cannot carry a direct lien. Lenders take liens on the stock of the licence subsidiary and on sale proceeds. Read where the licences sit before you count them as collateral.
- Value spectrum at recent auction prices per MHz-pop in the stress case, less a forced-sale discount (Our choice).
- Tower and fibre assets: appraised value per site or per route mile (F7 A5). Ground leases under towers are real property leases. The F5 rejection cap applies.
- Indefeasible rights of use (IRUs) sold for cash in advance are deferred revenue. Holders can claim when service stops.
- Liability management is common in this sector. Score the F7 line for unrestricted subsidiaries that can hold fibre assets.

## Events and calendar
- Quarterly subscriber net adds, churn and ARPU.
- Spectrum auctions and licence renewals.
- Broadband grant awards and build milestones.
- Universal Service Fund rulings and contribution changes.
- Copper retirement approvals and handset launch seasons.
- Carrier mergers that change tower and fibre tenancy.

## Instructions for the analyst
1. Frame the issuer as A5. Apply M2 to copper and geostationary video revenue.
2. Build EBITDA less capex. Remove gains on asset sales.
3. Add handset receivable securitisations to debt. Compute `lev_gc_total` or `lev_lease_adj`.
4. Split capex into maintenance, network build and spectrum. Size liquidity with build commitments.
5. Locate the spectrum licences. Map the liens on the licence subsidiaries in the claims view.
6. Run the ARPU, churn and carrier-loss cases.
7. Value the issuer at the EBITDA multiple and at asset appraisal. Use the lower for `V_default`.
8. Gate the memo under F9. Report FOCF to debt beside `lev_gc_total`.

## Open questions
- Does `churn` add to `fcf_debt` in HY telecom spreads? No repo source. Test: add `churn` to the GICS 50 sector fit and check the sign.
- What discount applies to spectrum in a forced sale? No repo source. Build a sample of spectrum sales by distressed sellers.
- Does M3 tenant concentration widen tower spreads after a carrier merger? Test it on tower bond spreads around merger approval dates.
