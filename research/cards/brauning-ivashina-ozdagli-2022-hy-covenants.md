# Bräuning, Ivashina and Ozdagli (2022), "High-Yield Debt Covenants and Their Real Effects"

NBER Working Paper 29888, March 2022, DOI 10.3386/w29888. The paper also circulates as Federal Reserve Bank of Boston Working Paper 22-05. We read the NBER version, 50 pages, and not the Boston Fed version. Page numbers below are PDF pages. Printed page = PDF page - 2 for the main text. Evidence class: working paper, not peer-reviewed (p. 1). The sample is US leveraged loans, not bonds. The outcomes are investment, debt and equity returns. The paper reports no bond spread and no default outcome.

## Claim
High-yield debt carries incurrence covenants. A trigger of an incurrence covenant does not move control rights to creditors. It switches on a set of restrictions on the borrower's actions (p. 2). The trigger cuts investment, debt and equity value. The cut is large and sudden, before any default or bankruptcy (pp. 2, 5, 28). The investment cut after an incurrence trigger is larger than the cut after a maintenance covenant breach (p. 21).

## Method
**Covenant classes (pp. 4, 16).** A maintenance covenant requires compliance every quarter. A breach moves control rights to lenders. An incurrence covenant ties the ratio test to a restricted action, such as a distribution, new debt or an investment. The terms of the loan do not change on a trigger (p. 16). The firm lifts the restriction when it brings the ratio back inside the threshold (p. 16).

**Restricted actions (p. 36, Table III).** The authors group the incurrence restrictions into four classes: restricted payments, indebtedness (new debt and changes to junior debt), investments (capital expenditure and acquisitions), and other. The paper does not study liens, asset sales or change of control. For those covenants, every figure is not reported.

**Trigger state (pp. 16-17).** The treatment is a dummy for a crossed threshold.

```latex
Bind_{it} = \begin{cases} 1 & \text{if } z_{it} - z^{0}_{it} > 0 \\ 0 & \text{otherwise} \end{cases}
```

Intuition: the dummy switches on in the first quarter that the reported ratio passes the contract threshold. Here `z_it` is the observed leverage ratio, net debt over EBITDA, and `z0_it` is the threshold. For an interest coverage covenant the sign reverses (p. 17). The authors call an incurrence trigger a "latent violation", because no action needs to occur for the dummy to switch on (p. 4, note 3).

**Distance and tightness (pp. 17, 20, 38).** The regressions hold a polynomial of order two in the distance to the threshold. The paper defines tightness at origination as the threshold minus the actual ratio (p. 38, Table V note).

```latex
Tightness_{i,0} = z^{0}_{i,0} - z_{i,0}
```

Intuition: a small positive value means that a small rise in leverage trips the covenant.

**Main regression (pp. 19-20).**

```latex
Investment_{i,t} = \alpha + \beta_0 \, IncurrenceBind_{i,t-1} + \beta_1 \, MaintenanceBind_{i,t-1} + \gamma X_{i,t-1} + \epsilon_{i,t}
```

Intuition: within one firm, investment jumps down in the quarter after the ratio crosses the line, net of a smooth function of the distance. Investment is capital expenditure as a percent of start-of-quarter net PP&E (p. 39). `X` holds log assets, cash flow, macro q, the distance polynomial, firm fixed effects and quarter fixed effects (p. 20). The tightest specification interacts all controls and quarter effects with the covenant type (p. 20). Standard errors are two-way clustered by firm and quarter (p. 20). The authors trim the top and bottom 1% of ratios. They drop any observation that moves `beta_0` or `beta_1` by more than three standard deviations (pp. 20-21).

**Identification (pp. 16-17, 18, 22).** The design follows Chava and Roberts (2008): the effect is the discontinuity at the threshold. Firm fixed effects remove fixed differences between firms. For selection into covenant type, the authors use the subsample of loans with both covenant types (p. 22). In that subsample the incurrence threshold is always tighter. So the incurrence coefficient comes from quarters past the incurrence line but inside the maintenance line (p. 22). For the COVID-19 demand shock, they add quarter by industry fixed effects (pp. 22-23, 50).

**Threshold path (p. 43).** Many contracts step the threshold down over time. The authors take the threshold at origination and at maturity and interpolate the quarters between.

## Data
- Leveraged loans from S&P LCD, originated 2017 to 2019, matched to Compustat (p. 11).
- 278 loans: 222 with covenants hand-collected from credit agreements filed with the SEC, and 56 with covenant data from DealScan only (p. 35, Table II). 83 loans carry incurrence covenants only, 84 maintenance only, and 111 both (p. 35).
- Covenant counts: 169 maintenance covenants and 500 incurrence covenants (p. 36, Table III).
- Firm-quarters from 2017:Q1 to 2020:Q4 (p. 39). The main regression holds 1,759 firm-quarters (p. 39, Table VI).
- DealScan gap: DealScan holds covenant data for 41.7% of loans in 1994 to 2005 and for 26.0% in 2017 to 2019 (p. 34, Table I). For 2017 to 2019, it holds covenant data for 11% (52 of 483) of cov-lite loans and 41% (124 of 301) of cov-strong loans (p. 11).
- The hand-collected thresholds match DealScan where both exist. Leverage: mean 4.1 against 4.2, RMSE 0.45. Interest coverage: mean 3.1 against 3.1, RMSE 0.11 (p. 47, Table A.I).
- Cov-lite share of US leveraged loans: just over 10% in 2007 to more than 80% in 2020 (p. 4, Figure 1).

## Result
**Thresholds (p. 36, Table III).** Maintenance leverage covenants: 144 covenants, mean 4.39x, median 4.25x. Maintenance interest coverage: 119 covenants, mean 2.63x. Incurrence leverage thresholds: 463 covenants, mean 3.61x, median 3.5x. By restricted action, the mean incurrence leverage threshold is 3.35x for restricted payments, 3.91x for indebtedness and 3.59x for investments. About 93% of incurrence covenants use a leverage test (p. 13).

**Tightness at origination (p. 38, Table V).** Initial leverage tightness is -0.086 (median 0.414) for incurrence-only loans. It is 1.908 (median 1.697) for maintenance-only loans and 2.049 (median 1.793) for loans with both. The difference from incurrence-only loans has a p-value of 0.000 (p. 38). So incurrence-only loans start at or near their threshold.

**Restricted action mix (pp. 14, 49, Table A.III).** Among loans with incurrence covenants, 142 restrict payments, 122 restrict indebtedness and 95 restrict investments. About 71% (101 of 142) of loans with a payment restriction also restrict indebtedness. About 62% (88 of 142) also restrict investment (p. 14).

**Trigger frequency (pp. 14-15, 37, Table IV).** About 64% of loans (152 of 237) cross a threshold at some point. About 75% (51 of 68) of incurrence-only loans trigger, against 46% (33 of 71) of maintenance-only loans (p. 14). About 39% of firm-quarters show a trigger or a breach, against 15% in Chava and Roberts (2008) (p. 15).

**Time between states (p. 48, Table A.II).** For loans with both types, a loan moves from no trigger to an incurrence trigger after a mean of 4.39 quarters (median 3). It moves from an incurrence trigger to a maintenance breach after a mean of 3.88 quarters (median 3). It moves from an incurrence trigger back to no trigger after a mean of 2.79 quarters (median 2).

**Investment (p. 39, Table VI).**

| Column | Incurrence Bind | Maintenance Bind | Obs |
| --- | --- | --- | --- |
| (1) pooled Bind | -1.59 (0.34) | | 1,759 |
| (2) | -1.92 (0.43) | | 1,759 |
| (3) incurrence-only firms | -1.84 (0.66) | | 481 |
| (6) both dummies | -1.84 (0.41) | -0.74 (0.34) | 1,759 |
| (7) with type interactions | -1.83 (0.36) | -0.94 (0.30) | 1,759 |
| (8) loans with both types | -1.87 (0.44) | -0.95 (0.44) | 774 |

The test of equal coefficients has p = 0.0292 in column 6, 0.0278 in column 7 and 0.0764 in column 8 (p. 39). The average investment rate before a breach is close to 6% (p. 18). So the incurrence effect is near a third of the pre-breach rate (our arithmetic: 1.83 over 6).

**Checks (pp. 40, 50).** Without loans that restrict investment directly, the incurrence coefficient is -2.16 (0.47) (p. 40, Table VII, column 1). Without loans whose maintenance covenant covers only the revolver, it is -2.14 (0.58) (column 3). About 18% of loans with a maintenance covenant apply it only to the revolver or some facilities (p. 23). Without amended loans, it is -1.88 (0.46) (column 5). About a quarter of loans and firm-quarters have an amendment (p. 24, note 19). With quarter by COVID-industry effects, it is -1.71 (0.37). With quarter by two-digit NAICS effects, it is -1.84 (0.34) (p. 50, Table A.IV).

**Equity (p. 41, Table VIII).** The three-month stock return falls 7.86% (1.94) after any trigger (column 1). It falls 5.67% (2.19) after an incurrence trigger and 5.74% (1.91) after a maintenance breach (column 2). The test of equal effects has p = 0.986 (column 2).

**Debt (p. 42, Table IX).** Debt over assets changes by -2.70 points after any trigger (column 1). It changes by -2.66 (0.55) after an incurrence trigger and -1.58 (0.38) after a maintenance breach, p = 0.0519 (column 2). Net debt over EBITDA changes by -2.07x after any trigger (column 4). It changes by -1.81x (0.59) after an incurrence trigger and -2.27x (0.66) after a maintenance breach, p = 0.547 (column 5).

**Spreads and default.** Not reported. The paper has no bond price, loan price, spread or default regression.

## Limits
- The sample is leveraged loans. The paper asserts that cov-lite loans resemble high-yield bonds (pp. 4, 27). It holds no bond indenture data. A bond ratio debt test and a loan incurrence test may differ in definition and in threshold.
- The ratio `z_it` comes from reported financials. The paper does not report how it maps the contract EBITDA definition, its add-backs, or the pro forma test onto Compustat. A gap between the two definitions puts error into `Bind`.
- An incurrence test applies only when the firm takes the restricted action. The dummy assumes that the restriction bites from the reported ratio each quarter. The paper does not test whether firms planned a restricted action.
- The design is a panel regression with a quadratic in distance, not a local discontinuity with a bandwidth. The paper reports no density test for ratio management near the threshold.
- The linear threshold path (p. 43) misplaces step-downs that occur between origination and maturity.
- The window holds about 16 quarters, and COVID-19 dominates it (pp. 9, 22). The two-way clusters by quarter are few.
- The equity outcome is a quarterly return, not an event study around a filed report date.
- Source inconsistency: footnote 18 says that a latent incurrence violation always precedes a maintenance breach (p. 21). The Table A.II note says that a maintenance breach implies an incurrence trigger (p. 48). The same table shows 22 moves from no trigger to a maintenance breach and 23 moves from a maintenance breach to an incurrence trigger (p. 48).
- Source inconsistency: in Table III the leverage and coverage counts sum to 263 against 169 maintenance covenants, and to 516 against 500 incurrence covenants (p. 36). The paper does not explain the overlap.
- Source inconsistency: the count of loans with an incurrence covenant is 193 in Table A.III (p. 49), 194 in Table II (p. 35: 83 plus 111) and 166 in Table IV (p. 37: 68 plus 98).
- Source inconsistency: Table V defines tightness as the threshold minus the actual ratio (p. 38). For a minimum coverage test, a firm in compliance then has a negative value. The table reports positive coverage tightness, 3.668 to 6.452. So the coverage sign convention differs from the stated definition.
- Source inconsistency: the Table IX note says that the table covers the "quantity and cost of debt" (p. 42). The table reports no cost of debt.
- Source inconsistency: the Table A.IV note refers to "the analysis in Table V" (p. 50). Table V holds summary statistics. The regression it repeats is Table VI.
- Magnitude doubt: a fall in net debt over EBITDA of 1.81x (p. 42) is half the mean incurrence threshold of 3.61x (p. 36). The paper does not state the horizon of the change. Treat the ratio result with care.

## Section touched
`docs/methodology.md` Section 4.6 (covenant headroom), Section 5.3 (`p_breach_h`), Section 6.3 (liability management adjustment), Section 9.1 (event taxonomy). `docs/framework.md` F4 (refinance access score, point 3), F7 (liability management score), F8 (covenants and documents), F11 (covenant test row).

## Use for the framework
**What the source says.** An incurrence trigger is a covenant event with real effects, without a default and without a transfer of control. It cuts investment by about 1.8 points of capital per quarter (p. 39). It cuts debt over assets by about 2.7 points (p. 42) and equity by about 6% (p. 41). Incurrence thresholds sit tighter than maintenance thresholds (p. 36). A trigger comes a mean of 3.88 quarters before a maintenance breach (p. 48).

**What the data says.** The repo models only maintenance covenants. `hy/state.py:510` and `hy/forward.py:223` compute `H_t = 1 - Lev^cov / Lev^max` against a maintenance level. `hy/events.py:53` gives the covenant test the outcomes pass, waiver and acceleration only. F8 holds `H_t`, `p_breach_4`, `rp_capacity_turns` and `debt_capacity_turns`. Methodology Section 4.6 defines incurrence headroom as basket capacity in dollars. No field holds the distance to a ratio-based incurrence test. Outside `hy/skills.py:254`, no code in `hy/` names incurrence. All four F8, F4, F7 and F11 rules rest on Gatto (2023) alone.

**What we decide (our proposal, not the source's claim).**
1. Add an incurrence headroom to F8, separate from `H_t`. Take the tightest ratio test across the restricted payment, debt and investment covenants. Read each threshold at its step-down date, not by interpolation.

```latex
H^{inc}_t = 1 - \frac{Lev^{cov}_t}{\min_{k \in \{RP, Debt, Inv\}} Lev^{inc}_{k,t}}, \qquad inc\_bind_t = \mathbb{1}\{H^{inc}_t < 0\}
```

Intuition: `H_inc` is the share of covenant EBITDA the issuer can lose before the ratio-based permissions close. For a coverage test, use `1 - Cov^{inc}_{k,t} / Cov^{cov}_t`. Undisclosed thresholds are NaN, not 0. Initial bands, for calibration: red below 0, amber 0 to 10%, green above 10%.

2. Split basket capacity in F4 point 3 and in the F7 score by state. Store `rp_capacity` and `debt_capacity` twice: with the ratio test open, and with only the fixed-dollar baskets. When `inc_bind` is 1, use the fixed-dollar figure. The source shows that firms past the trigger cut debt (p. 42), so ratio capacity is not usable then.
3. Score F7 in both the base case and the F6 severe downside path. The liability management points for restricted payment and debt capacity use the state that the path reaches. The source does not test liability management. This step follows from the contract mechanics only.
4. Add `incurrence_bind` to the F11 covenant test row and to `EventType.COVENANT_TEST` as an outcome beside pass, waiver and acceleration. Compute `H_inc` before each earnings release. The source gives no bond spread effect, so record the realised spread change and let F13 score it.
5. Test. Use Mergent FISD covenant flags to select high-yield bonds with a ratio debt test and a restricted payment covenant. FISD does not hold the threshold values to our knowledge, so code them from indentures on SEC EDGAR. Take quarterly leverage, capital expenditure, PP&E and debt from Compustat, and spreads from TRACE. On firm-quarters from 2005 onward, regress capital expenditure over PP&E and the change in debt over assets on `inc_bind_{t-1}`. Include a quadratic in `H_inc`, firm effects and quarter effects. The bond case of this paper holds if both coefficients are below 0 at the 5% level. Then regress the quarterly spread change on `inc_bind_{t-1}` with the same controls. `inc_bind` earns a place in the fair spread model only if its coefficient differs from 0 with `H_inc` in the model. The source predicts no sign for spreads: creditor protection pushes the spread down, and the signal of a weak issuer pushes it up.
