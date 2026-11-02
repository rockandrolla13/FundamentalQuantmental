# Becker, Josephson and Xu (2023), contract rejection and debt capacity

Working paper. IFN Working Paper 1477 and ECGI Finance 937/2023, DOI 10.2139/ssrn.4608083. We read two versions, both opened in full:
- IFN file, dated 4 October 2026, 58 pages, titled "Should Insolvency Law Cover Non-Financial Obligations? Contract Rejection and Debt Capacity". This is the main source below. PDF page = printed page + 2.
- HKU file, dated 2 December 2024, 42 pages, titled "Non-Financial Liabilities and Effective Corporate Restructuring". We use it only to note changes. Its coefficients differ.

Page numbers are PDF pages of the IFN file. Evidence class: firm leverage and syndicated loan flows, not bond spreads.

## Claim
The option to reject executory contracts prevents excess liquidation and raises debt capacity (p. 2). Non-financial obligations are often large, and they exceed financial debt in a quarter of US firms (p. 2). An executory contract is one where both parties have remaining obligations, such as office leases and long-term vendor contracts (p. 4).

## Method
**Model.** Three periods (pp. 9-14). A firm has revenue `q θ + x ψ`, a contract for `x` units at price `p`, and debt of face `D`. Regime F allows only debt writedowns. Regime O also lets the court cut the contract price to `k`, the supplier's outside value. So `P(F) = p` and `P(O) = k`.

```latex
\theta_I = \frac{D + xp - x\psi}{q} \quad (2) \qquad \theta^i_L = \frac{L + xP(i) - x\psi}{q} \quad (4)
```

Intuition: the insolvency point depends on the contract at full price, and the liquidation point depends on the price a court can enforce.

```latex
D^i = q + x\psi - xp - C/t + x\big(p - P(i)\big)/t \quad (9)
```

Intuition: a contract concession offsets part of the bankruptcy cost, so the firm carries more debt.

Proposition 1 orders the thresholds: `θ_L^O < θ_L^F < θ_I^F < θ_I^O` (p. 15). So, in the model, rejection lowers the liquidation threshold and raises the insolvency threshold. Proposition 2: leverage is higher under O and rises faster with `x` (p. 15).

**Measure.** Executory intensity is lease plus purchase obligations over assets (pp. 17, 19).

```latex
E_j = \text{median}_{i \in j} \frac{3 \times xrent_i + PO_i}{assets_i}
```

Intuition: three years of rent stands in for lease commitments, and it avoids the 2018 change in lease accounting. The result does not change with a multiple of 2, 4 or 5 (p. 19). The December 2024 file states the median of the sum (its p. 16). The IFN file names the same two parts (p. 19).

**Tests.** Difference in differences, with `E_j` interacted with a US indicator, and with industry-year and country-year effects (p. 27, equation 14). Second, the 2019 Israeli reform, with firm effects (p. 31, equation 15). Third, loan flows from Dealscan (p. 33, equation 16).

## Data
- US executory measure, Compustat and 10-K text. Global firm panel from Compustat and Capital IQ (p. 18).
- Large US firms in 2018: mean obligations 13.0% of book assets, mean leverage 29.6% (p. 3).
- All firms: median 7.7% of book assets (p. 6). Firm 25th and 75th percentiles are 0.040 and 0.206 (p. 22).
- Industry measures (Table 1, p. 22): Apparel 0.324, Retail 0.317, Restaurants and hotels 0.230, Aircraft and ships 0.170, Precious metals and mining 0.045. Purchase obligation share: Retail 20%, Aircraft and ships 76%.
- Cross-industry standard deviation is 0.072 (p. 22).

## Result
**US against other countries (Table 3, p. 27).** The coefficient is 0.094 (se 0.026) on leverage, 1.641 (se 0.431) on debt to EBITDA, and 0.228 (se 0.055) on a high leverage indicator.

**Components (Table 4, p. 29).** On leverage: leases only 0.233 (se 0.072), purchase agreements only 0.074 (se 0.152). On debt to EBITDA: leases only 4.292 (se 0.941), purchase agreements only 3.738 (se 1.716). The mean-based industry measure gives 0.038 (se 0.021) on leverage.

**Israel (Table 5, p. 31).** The coefficient is 0.667 (se 0.138) on leverage. Without 2019 data it is 0.790 (p. 32).

**Loan flows (Table 6, p. 34).** The coefficient is 3.757 (se 0.881) on log loan value. One standard deviation of intensity goes with 31% higher volume.

**Priced claims.** The authors dropped loan price tests from the paper, because theory is ambiguous on them (p. 35).

## Limits
- Tests use leverage and loan quantity. They do not test bond spreads, ratings or defaults.
- The measure is by industry, not by issuer. The authors assume the US order holds abroad (p. 18). The R-squared of firm leases on the industry measure is 0.14 for US firms and 0.13 for foreign firms (p. 20). So most firm variation is outside the measure.
- The purchase-only row is not significant on leverage (Table 4).
- The cross-country result is a relative one. It says that executory contracts reduce debt capacity less in the US, "possibly not at all" (p. 35). It does not say that US firms with more leases carry more debt than US firms with fewer.
- The model assumes that executory claims rank ahead of financial claims and that a rejected claim recovers zero (p. 10).
- Aircraft leases sit outside this logic. Section 1110 gives the debtor 60 days to cure (p. 5, footnote 4).
- Source inconsistency: the text calls a rise of 0.007 on a mean of 0.228 "around 3 percentage points" (p. 27). It is about 3 percent of the mean.
- Coefficients changed between versions. The December 2024 file reports 0.199 for Table 3 and 0.632 for Israel. Quote the IFN file.

## Section touched
`docs/methodology.md` Section 4.7 (recontract split, downside rule 4), Section 6.2 (waterfall), Section 7.1 (expected loss anchor). `docs/framework.md` F5 (rejected lease rule) and F8 (`claim_haircut_leases`). `hy/clocks.py`.

## Use for the two clocks
**What the source says.** In the model (Proposition 1), a lease or supply contract is an option for the debtor in Chapter 11. Rejection lowers the liquidation threshold and raises the insolvency threshold. The paper tests leverage and loan flows, not default or recovery (pp. 27, 35). The authors dropped loan price tests, because theory is ambiguous on them (p. 35).

**What the data says.** Section 4.7 reads rent and purchases at face and finds a negative coefficient (-2.07, t -2.4). `docs/framework.md` F5 already caps rejected real property claims and records `claim_haircut_leases`. No clock feature reads that cap. We checked the statute: 11 U.S.C. 502(b)(6) says "the greater of one year, or 15 percent, not to exceed three years, of the remaining term". F5 applies the 15 percent to remaining rent, and the statute text applies it to the remaining term. The two differ when rent escalates, so F5 should state which reading it uses.

**What we decide (our proposal, not the source's claim).**
1. Compute the cost clock twice, as framework rule R3 asks. The going-concern view keeps rent at face. The claims view uses assumed leases at rent and rejected leases at the allowed claim.

```latex
O^{claim}_{i} = \sum_t D_{i,t} + \sum_{j \in A} \sum_t o_{j,t} + \sum_{j \in \text{Rej}} C_j, \qquad \text{rent\_option\_gap}_i = \frac{\sum_{j \in \text{Rej}} \left(\sum_t o_{j,t} - C_j\right)}{\sum_t O_{i,t}}
```

Intuition: the gap is the part of the fixed charges that a court can remove and that never dilutes the bonds.

2. Split the spread effect into default and recovery. Prediction from Proposition 1: lease intensity raises the default hazard and raises recovery for unsecured bonds, compared with the same amount of debt.
3. Exclude aircraft and other Section 1110 assets from the rejection set. F5 already states this.
4. Test. Regress default within 24 months on the lease tail in years of EBITDAR, and regress realised recovery on `rent_option_gap`. The rejection reading passes when both coefficients are above 0. A rise in hazard with no rise in recovery rejects it.
