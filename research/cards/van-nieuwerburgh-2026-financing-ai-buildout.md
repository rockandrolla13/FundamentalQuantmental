# Van Nieuwerburgh (2026), "Financing the AI Buildout"

NBER Working Paper 35865, October 2026. The paper is forthcoming in the Fall 2026 Brookings Papers on Economic Activity (p. 1). We read the NBER PDF, 32 pages, with the inner draft date 2 October 2026 (p. 3). Page numbers below are PDF pages. Printed page = PDF page - 2. Evidence class: working paper, not peer-reviewed (p. 1). The paper is descriptive. It holds one transaction case, Hyperion, and aggregate cost arithmetic. It holds no bond spread regression and no default outcome.

## Claim
Hyperscaler capital expenditure now outgrows operating cash flow. So the financing moves to leases, joint ventures, project debt, private credit, securitization and special-purpose vehicles (SPVs) (pp. 2, 8). These structures do not remove risk. They move ownership and leverage away from the tenant, and they do not fully transfer the economic risk (pp. 4, 9). Long-duration debt then rests on lease renewals, utilization and residual values. Each of these is uncertain (p. 14). Investment-grade (IG) tenants make the structures financeable through long contracted cash flows (pp. 4, 8).

## Method
**Case study (pp. 10-13).** The author reads the Hyperion financing from the S&P pre-sale report and the Entergy 2025 Form 10-K (p. 12). He describes the owners, the leverage, the lease terms, the guarantee and the yield. He does not model the cash flows of the SPV.

**Residual value guarantee (p. 11).** At each renewal date Meta may end the lease for some or all of the campus. The assets then go to sale. Meta pays any shortfall of the sale price below a minimum value set in the contract. In our notation, not the source's:

```latex
RVG_k = \max\left(0,\; V^{\min}_k - P^{sale}_k\right) \quad \text{if Meta ends lease } k
```

Intuition: Meta either keeps the rent or pays the gap to a floor value, so lenders keep much of the support of a long lease.

**Lease-adjusted leverage (pp. 11-12, note 6).** The author compares four ratios. He adds commenced lease obligations and uncommenced lease obligations to debt. He multiplies the uncommenced amount by 0.75 to approximate a present value.

```latex
L_1 = \frac{D}{D + E^{book}}, \quad L_2 = \frac{D + \Lambda}{D + \Lambda + E^{book}}, \quad L_3 = \frac{D}{EBITDA}, \quad L_4 = \frac{D + \Lambda}{EBITDA}, \quad \Lambda = \Lambda^{comm} + 0.75\,\Lambda^{uncomm}
```

Intuition: leases are debt in all but name, and signed leases that have not started are debt too.

**Required revenue (pp. 28-29, equations 3, 5, 6).** The appendix computes the mature revenue that the 2025 to 2032 buildout needs to earn a set unlevered return. IT equipment is 68% of cost with a six-year life. Buildings, power and cooling are 32% with a 20-year life (p. 29).

```latex
a(r, N) = \frac{r(1+r)^N}{(1+r)^N - 1}, \qquad CF_t(r) = B_t\left[0.68\, a(r,6) + 0.32\, a(r,20)\right]
```

Intuition: the short-lived IT share sets most of the annual capital charge, so the asset life drives the revenue each cohort must earn.

**Market beta (p. 16, Figure 3).** The author runs 36-month rolling regressions of data centre REIT excess returns on the S&P 500 excess return, the 10-year Treasury excess return and the Fama-French five factors.

## Data
- Hyperion terms: S&P pre-sale report and Entergy 2025 Form 10-K (p. 12). Sopaipilla appears in one footnote only (p. 13, note 7).
- Hyperscaler capex and operating cash flow: 10-K and 10-Q filings of Oracle, Microsoft, Amazon, Meta and Alphabet, 2020 to 2025, plus guidance and analyst estimates for 2026 (p. 9).
- Lease-adjusted leverage: June 2026 filings of four hyperscalers, Amazon excluded (p. 12, note 6).
- Lease commitment totals: Moody's (2026a) and a Wall Street Journal tally (p. 11, note 5). The author does not rebuild these figures.
- CDS levels: five-year CDS on the five hyperscalers on two dates, 21 November 2025 and 22 July 2026 (p. 13, note 8). The source of the CDS data is not stated.
- Capacity: Cleanview project records, 3,423 projects, accessed 12 September 2026 (p. 22).
- REIT returns: FTSE Nareit data centre REITs, monthly, January 2018 to March 2026 (p. 16).
- No bond-level data. No TRACE prices, no loan prices, no contract exhibits.

## Result
**Hyperion structure (pp. 10-12).** The project has about 2.0 GW and about $30bn of investment (p. 10). The figure excludes IT equipment, which Meta finances separately as the tenant (p. 10, note 3). Meta sold an 80% equity stake to Blue Owl for about $2.5bn (p. 10). The joint venture raised $27bn of debt in October 2025 (p. 10). Laidley LLC owns the campus. Meta holds 20% of the joint venture through Iris Crossing LLC, and Blue Owl holds its stake through Beignet Investor LLC (p. 12, Figure 2). Laidley has a power purchase agreement with Entergy Louisiana (p. 12).

**Leverage at the asset (p. 11).** Debt is about 90% of asset value. The debt service coverage ratio is 1.12x. Meta's own year-end 2025 leverage is about 25% on book equity and 4% on market equity (p. 11, note 4).

**Lease term against debt term (p. 11).** Meta signs five four-year leases. The first starts in 2029, and the last runs to the bond's 2049 maturity. Meta may end the lease at each renewal date. The residual value guarantee then applies. So the firm lease term is four years, and the debt runs to 2049.

**Loss allocation (pp. 11, 13, 14).** The SPVs are bankruptcy-remote and issue debt backed by claims on future lease payments (p. 11). Bondholders have no direct claim on Meta's balance sheet (p. 13). Repayment depends on cash through the project and on Meta's lease and residual value guarantee (p. 13). Debt service is fixed, while revenue depends on utilization, renewals and residual values (p. 14). A modest fall in demand or asset values gives larger losses to equity and may impair creditors (p. 14). A tenant may shift work away from leased capacity to protect its owned sites. That puts the adjustment on third-party assets (p. 14).

**Accounting (p. 11).** Under current GAAP, Meta records neither the future leases nor the guarantee before each one takes effect. The author notes that one of the two will occur for sure. Moody's puts hyperscaler lease commitments at about $970bn, of which about $660bn are future leases not on the balance sheet (p. 11). For four hyperscalers, `L_1` rises from 20% to `L_2` of 48%, and `L_3` from 0.7x to `L_4` of 2.6x (p. 12, note 6).

**Pricing (pp. 10, 12, 13).** S&P rated the debt A+, one notch below Meta (p. 10). The yield was 6.58%. The author states this is at least 100bp above the rate that Meta "likely would have paid" on unsecured debt (p. 12). He attributes the premium to the absence of a direct claim on Meta, to structural, contractual, liquidity and enforcement risk, to longer duration and to the private-placement form (p. 13). He does not split the premium among these causes. Five-year CDS widened for all five hyperscalers between the two dates, Meta from 56.1bp to 80.2bp and Oracle from 118.8bp to 205.5bp (p. 13, note 8). The author reads this as a price on off-balance-sheet commitments. He runs no test of that reading.

**Asset life (pp. 9, 14, 28, 32).** GPU collateral has a shorter life and less certain resale value than real estate (p. 9). Long debt maturities meet much shorter economic lives (p. 14). GPUs may become obsolete within three to six years, while buildings and power connections last longer (p. 28). A three-year IT life raises the weighted capital charge from 19.37% to 31.10% of the capital base (p. 32).

**Vendor support (p. 15, note 9).** NVIDIA provides a 25% residual value guarantee on a $500bn chip credit facility. That exposes NVIDIA to as much as $125bn.

**Disclosure gap (pp. 13, 16-17).** Publicly rated debt is a small share of data centre finance. Bank loans and private credit hold larger volumes with little public data (p. 13). The author asks for disclosure of project debt, joint venture stakes, future leases, residual value guarantees, construction guarantees, tenant concentration, renewal options and recovery values (pp. 16-17).

## Limits
- One transaction. The Hyperion facts come from one S&P pre-sale report. Sopaipilla gets one sentence. No cross-section of structures exists in the paper.
- No spread test. The 100bp premium compares an observed yield with an unobserved Meta rate that the author estimates. The CDS evidence is two dates per name, with no control for market-wide spread moves.
- The paper does not state the minimum values of the residual value guarantee, the renewal notice terms or the lease rent. So the size of lender support after a termination is unknown.
- The paper names "Beignet" as the joint venture that raised the debt (p. 10). Figure 2 names Beignet Investor LLC as Blue Owl's vehicle and Laidley LLC as the owner (p. 12). The exact issuer entity is not clear from the text.
- All issuers in the case are IG. The paper does not discuss high-yield developers, neoclouds or holding company debt above an SPV.
- The 0.75 present value factor for uncommenced leases is the author's approximation, with no stated rate or term (p. 11, note 6).
- The six-year and 20-year lives are assumptions "based on current industry assessment and accounting practices" (p. 29). No test supports them.

## Section touched
`docs/methodology.md` Section 4.7.3 (support label against support contents), Section 4.7 (duration mismatch), Section 4.7.2 (delivery delay). Decision page `2026-11-23-support-label-gap`.

**Section 4.7.3, term by term.**
1. `min(1, T^c / T^d)`. The source informs this term. Hyperion has a firm term of four years against a debt to 2049 (p. 11). Our arithmetic: the tenor ratio is near 0.17 on the firm term, and near 0.85 on all five leases from 2029. Both grade "weak" under our Basel cut-offs. Yet S&P rated the debt A+ (p. 10). The residual value guarantee carries the support past each renewal date. The formula has no term for it. So the score understates a lease with a guarantee. A candidate fix: count a guaranteed renewal period toward `T^c` up to the guaranteed share. The source gives no number for that share.
2. `q^nc`. The source informs this term. Each renewal date is a tenant option to end the lease (p. 11). So the non-cancellable share covers only the current four-year lease, unless the guarantee counts as non-cancellable.
3. `q^ig` and `c_ig`. The source informs the input but not the number. IG tenant credit is what makes the structure financeable (pp. 4, 8). The source also shows that an IG tenant can move work off leased capacity (p. 14). So IG credit protects the rent in force, not the renewal. The source gives no value for `NONIG_CREDIT = 0.5`.
4. `q^on` and `c_on`. The source informs the input. At issue in October 2025, the first lease starts in 2029 (pp. 10, 11). So the commenced share was zero at issue. Under GAAP, the tenant does not record the lease before it starts (p. 11). The 0.75 factor (p. 11, note 6) is a present value discount, not a credit haircut. It does not inform `UNSTARTED_CREDIT = 0.5`.
5. `q^reach`. The source informs this term most directly. The bankruptcy-remote SPV receives the lease cash and the guarantee for its own bonds (pp. 11, 13). For the SPV's own debt, reach is close to 1. For any debt outside the SPV, the source says only that exposures become hard to trace (p. 11). It gives no number.
6. Step 2, `prices_label_only`. The source gives one data point against a pure label market. The debt of a Meta-backed SPV priced at least 100bp over Meta's estimated unsecured rate (p. 12). The source does not test a cross-section, so it does not settle the step.
7. Step 4, `next_catalyst`. The source informs the event list. Lease start (2029) and each renewal date are dated events (p. 11). Our arithmetic: the renewal dates fall in 2033, 2037, 2041 and 2045.
8. The Basel cut-offs of 1.25x and 0.9x and the mis-sort cut of 0.25 rank. The source does not inform them.

**Section 4.7.**
1. `duration_gap` and `renewal_recontract_share`. The source supports the premise that debt outlasts the firm lease (pp. 11, 14). It gives no issuer data to fit them.
2. Obligations grid. The source supports the rule that signed leases not yet commenced count as obligations (p. 11). It does not inform the "thereafter" default.
3. `recourse_share` and `ring_fenced_assets_share`. The source supports both as features (pp. 11, 13). It gives Hyperion's debt at about 90% of assets with a DSCR of 1.12x (p. 11) as one reference point.
4. The source does not inform the renewal split test result or any Section 7 sign.

**Section 4.7.2.** The source names execution delay as a risk: revenue may start later or never (p. 14). It gives no delay length, reserve or rent credit. It does not inform `delay_tolerance_months`.
