# Fader and Hardie (2010), "Customer-Base Valuation in a Contractual Setting: The Perils of Ignoring Heterogeneity"

Marketing Science 29(1), pp. 85-93, DOI 10.1287/mksc.1080.0482. Peer-reviewed journal article. We read the published pages on the Wharton site, 9 pages. Page numbers below are journal pages. Journal page = PDF page + 84. Evidence class: analytical, numerical, stylised firm data. No credit outcome.

## Claim
Cohort retention rates rise with tenure, mainly because high-churn customers leave first (pp. 86-87). A value based on one aggregate retention rate is biased downward (p. 85). The bias is on the order of 25% to 50% in standard settings (p. 91).

## Method
**Shifted-beta-geometric (sBG) model (p. 87).** A customer renews each period with constant probability `1 - θ`. The value of `θ` differs across customers and follows a beta distribution.

```latex
S(t \mid \alpha, \beta) = \frac{B(\alpha, \beta + t)}{B(\alpha, \beta)}, \quad t = 1, 2, \dots \quad (1)
r_t = \frac{\beta + t - 1}{\alpha + \beta + t - 1} \quad (2)
```

Intuition: no customer changes, but the survivors are the sticky ones, so the cohort rate rises.

**Residual value (p. 88).** The discounted expected residual lifetime of a customer who has been active for `n` periods is below.

```latex
DERL(d \mid \alpha, \beta, n) = \frac{\beta + n - 1}{\alpha + \beta + n - 1}\ {}_2F_1\!\left(1, \beta + n;\ \alpha + \beta + n;\ \frac{1}{1+d}\right) \quad (6)
```

Intuition: the longer a customer has stayed, the more likely it is to be a low-churn type, so its expected remaining value rises.

**Equivalent sum (pp. 92-93).** The paper gives a spreadsheet form that needs no hypergeometric routine. Evaluate `S(t)` by the product of the rates in (2), divide by `S(n-1)`, and discount.

**Comparison.** For each pair of mean `μ = α / (α + β)` and polarisation `φ = 1 / (α + β + 1)`, the authors compare the sBG value with the value from one aggregate rate (p. 89).

## Data
- A hypothetical firm with 10,000 new customers each year from 2003 to 2007 (pp. 85-86).
- Two segments: one third with retention 0.9 and two thirds with retention 0.5 (p. 86).
- Parameters taken from two real data sets in Fader and Hardie (2007a): `μ = 0.15, φ = 0.18` and `μ = 0.37, φ = 0.35` (p. 90).

## Result
**First example (pp. 85, 87).** The naive value is $4,945,049 and the correct value is $7,940,992. The naive value is 38% too low.

**Cases (Table 4, p. 89).** With the same mean churn of 0.20: Case 1 (`α = 3.80, β = 15.20`) has an error of 12%. Case 2 (`α = 0.067, β = 0.267`) has an error of 41%.

**Real parameters (p. 90).** The naive method understates value by 28% and 48%.

**Tenure (p. 89).** In Case 1 a customer with four renewals has an expected residual value 16% above a customer with none. In Case 2 the gap is 33%.

**Elasticity (p. 91).** The retention elasticity is 6.5 by the model and 5.0 by the naive method on the first data set. It is 4.9 and 3.0 on the second.

**Robustness (p. 90).** The result holds for varied cohort sizes and churn rates in the electronic companion, which we did not open.

## Limits
- No formal proof that the bias always holds (p. 92).
- The whole rise in retention is assigned to sorting. If individual renewal changes with tenure, a Weibull form is the alternative (p. 92).
- Contract terms are one period, with no price change and constant cash flow per period (p. 88).
- The setting has observed attrition (p. 85, footnote 1). B2B issuers rarely publish cohort tables.
- The example firm is stylised. The paper does not test on credit data or on issuers.

## Section touched
`docs/methodology.md` Section 4.7 (`revenue_runoff`, `renewal_dependent_share`, rule 3 on RPO tail, downside rule 4). `hy/clocks.py` (`runoff_year`, `share_after`).

## Use for the two clocks
**What the source says.** One retention rate misses the shape of renewal, and it understates what an old book of contracts is worth.

**What the data says.** `runoff_year` and `share_after` treat every obligation after the run-off as unbacked. That is a retention rate of zero. In the backtest the run-off is year 2 for every issuer (`clock_facts.py` rule 3). Section 4.7 records no test of renewal curves.

**What we decide (our proposal, not the source's claim).**
1. Treat a fixed run-off as the lower bound of revenue, not as the estimate. Report `renewal_dependent_share` at retention zero, as now, and at the fitted curve.
2. Calibrate from two disclosed retention rates when no cohort table exists. Equation (2) inverts in closed form. Our derivation:

```latex
\beta = \frac{r_1 (1 - r_2)}{r_2 - r_1}, \qquad \alpha = \frac{\beta (1 - r_1)}{r_1}, \qquad r_2 > r_1
```

Intuition: the rise from the first rate to the second shows how much sorting exists. Check: `r_1 = 0.80` and `r_2 = 0.81` return `α = 3.8` and `β = 15.2`, which is Case 1 (p. 89).

3. Add `book_age` to the renewal downside. A book with long customer tenure gets the conditional curve at `n`, and a young book gets the curve at `n = 1`.
4. Use this as one candidate for the wrong sign. If long leases go with old and sticky customer books, then a zero-retention grid overstates the renewal bet exactly where the leases are long.
5. Test. On issuers with two retention disclosures, recompute the recontract amount net of expected renewal cash. This candidate passes when the coefficient moves toward 0 or above 0 by more than one standard error (Our choice, v0).
