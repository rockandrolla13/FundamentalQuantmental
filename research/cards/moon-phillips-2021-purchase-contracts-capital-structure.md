# Moon and Phillips (2021), "Outsourcing Through Purchase Contracts and Firm Capital Structure"

Management Science 67(1), pp. 363-387, DOI 10.1287/mnsc.2019.3443. Peer-reviewed journal article. We read an earlier version: NBER Working Paper 20579, October 2014, 59 pages, titled "Outside Purchase Contracts, Human Capital and Firm Capital Structure". We did not open the journal version, so its numbers may differ. Becker, Josephson and Xu cite the journal pages. Page numbers below are PDF pages of the NBER file. PDF page = printed page + 2. Evidence class: firm level, equity and leverage outcomes, no bond spreads.

## Claim
Firms with more purchase contracts have less risky cash flows, and they still carry less financial leverage (p. 2). The authors argue that these firms choose low debt to protect suppliers and employees from distress costs (p. 2). Purchase obligations are "best viewed as forward contracts with escape clauses" and not as leases (p. 9). The authors say they "should not be regarded as liabilities" (p. 9).

## Method
1. Measure. A purchase obligation is a contract to buy goods or services that binds the firm in the future (p. 8). The authors parse the MD&A table of each 10-K with keyword pairs (pp. 11, 36).
2. Intensity. The authors use only the first-year line (p. 10). Later lines are "frequently minimum amounts" and "sharply fall over time" (p. 10).

```latex
PC/COGS_{i,t} = PO_{i,t+1} / COGS_{i,t}
```

Intuition: the next-year commitment over the cost base shows how much of production the firm has contracted out.

3. Risk test. Propensity score match on size, market to book, leverage, sales, competition and high-tech status, with 10 neighbours in the same industry group (p. 21).
4. Cost test. Regress COGS and SG&A over average sales on a negative downstream demand shock, with firm fixed effects (p. 22).
5. Leverage test. Instrumental variables with firm fixed location and industry input costs (pp. 15-17, 25).

```latex
PC/COGS_{i,t} = \pi_1 CloseToPort_i + \pi_2 HighTransp_j + \gamma X_{i,t} + u_{i,t}
Lev_{i,t+1} = \beta \widehat{PC/COGS}_{i,t} + \delta X_{i,t} + \eta_{j} + \eta_{t} + e_{i,t}
```

Intuition: distance to a port shifts how much a firm buys from outside, and the authors argue that it does not move financing except through that channel.

6. Second instrument set. Supplier competition and supplier distance (pp. 17-18, 27).

## Data
- All 10-K filers in manufacturing with sales of at least $50 million, fiscal years 2004 to 2010 (pp. 9, 11).
- 1,806 firms and about 9,000 firm-years (p. 11). Table 4 says 1,807 firms (p. 47).
- A firm with no disclosed amount counts as zero (p. 11).
- More than 65% of manufacturing firms use purchase contracts (p. 12). The mean is about 10% of COGS, and almost 15% among users (p. 12).

## Result
**Firm profile (Table 4, p. 47).** Means for firms with contracts against firms without:

| Variable | With contracts | Without contracts |
| --- | --- | --- |
| Market leverage | 0.124 | 0.138 |
| Log market value of assets | 6.894 | 5.659 |
| Default probability | 0.016 | 0.033 |
| Stock return volatility | 0.420 | 0.464 |
| Cash flow volatility | 0.278 | 0.429 |

**Cash flow risk (Table 5, p. 48).** Standard deviation of operating margin is 0.022 lower across all quarters (z -1.79). The gap peaks at 0.052 in 2009q2 (z -2.90).

**Cost flexibility (Table 6, p. 49).** After a negative demand shock, COGS plus SG&A over average sales falls by 0.0447 (t -6.00) for firms with contracts. It falls by 0.0224 (t -1.82) for firms without.

**Leverage (Table 8, p. 51, and Table 9, p. 52).** Matched firms with high contract intensity have market leverage 0.035 lower (z -4.08). The instrumented coefficient on market leverage is -1.089 (t -6.11) with industry and year effects. Without instruments, a one standard deviation rise in intensity goes with a 0.051 standard deviation fall in leverage (p. 26).

**Instrument checks.** First set: F 10.85, Anderson LM 17.21, Hansen J 3.32 (p. 17). Second set: F 15.68, LM 31.32, J 3.01, and coefficient -0.869 (t -4.11) (pp. 27, 53).

**Debt maturity (Table 11, p. 54).** The fall comes from long-term leverage: -0.915 (t -6.16). The short-term coefficient is 0.133 (t 1.22).

## Limits
- Manufacturing only. The sample ends in 2010 and has one credit cycle.
- No bond spread and no default test. The default probability is a control, not an outcome.
- The mechanism is an interpretation. The authors say that the exclusion restriction is impossible to prove with correlation data (p. 25).
- Zero for non-disclosure may mix "no contract" with "not material" (p. 11).
- The source treats contracts as flexible in downturns, and it also calls them long-term. Later ladder lines are minimums, so a ladder understates long contracts (p. 10).
- This is the 2014 version, under an earlier title.

## Section touched
`docs/methodology.md` Section 4.7 (`renewal_recontract_share`, `obligation_kind`, purchase commitments in `O_t`) and Section 7.2 (forward block sign). `hy/clocks.py`. `hy/sources/clock_facts.py`.

## Use for the two clocks
**What the source says.** In manufacturing firms, users have a lower raw mean default probability, 0.016 against 0.033. Medians are zero, users are larger, and the paper has no default test (p. 47). Market leverage differs at the 10% level, and book leverage does not differ (p. 47). Contracts lower operating leverage in a downturn. Lines past year one are frequently minimums (p. 10).

**What the data says.** Section 4.7 records a recontract coefficient of -2.07 (t -2.4) across 187 issuers with material RPO. `clocks.obligation_kind` files purchases with rent as "recontract". `clock_facts.py` reads the whole purchase ladder at face.

**What we decide (our proposal, not the source's claim).**
1. Take purchases out of `renewal_recontract_share`. Report `renewal_lease_share` and `renewal_purchase_share` separately. Keep the old share as their sum for one release.
2. Add `pc_cogs_1y = PO_1y / COGS` as the purchase measure. Do not read later ladder lines as fixed charges.
3. Treat this paper as a selection candidate for the wrong sign. Purchases may load the share of larger issuers with less debt. The raw default gap in the source is not a test, so we do not rely on it.
4. Test, fixed before any run. Regress log spread on the lease share, the purchase share and `lev_lease_adj`. The source's story passes when the purchase coefficient is below the lease coefficient. Pass needs a difference t below -2 (Our choice, v0).
