# Fuhr and Papies (2024), "Double Machine Learning meets Panel Data - Promises, Pitfalls, and Potential Solutions"

arXiv 2409.01266v1, September 2024, at https://arxiv.org/pdf/2409.01266 (48 pages). **Working paper. Not peer reviewed in the version we read.** Page numbers are PDF pages, and they equal the printed pages. Evidence class: method, simulation only.

**Added at the audit close.** The screen graded this paper 3, and the cap dropped it. The method audit named it as essential.

## Claim
Violations of independence inside cross-fitting matter little for point estimates (pp. 1, 20). Many panel adaptations fail to remove unobserved unit heterogeneity (p. 1). Double machine learning with correlated random effects gives accurate coefficients across settings, if the sample is large relative to the number of confounders (pp. 1, 24).

## Method
**Correlated random effects inside the learners (p. 16, eq. 6).**

```latex
y_{it} = \gamma g_0(x_{it}, \bar x_i, \bar w_i) + \mu_{it}, \qquad w_{it} = \delta m_0(x_{it}, \bar x_i, \bar w_i) + \eta_{it}
```

Intuition: feed each learner the unit's time means, so it can model what stays fixed for that unit, with no unit dummies. `w` is the treatment. The form needs both the covariate means and the treatment mean (p. 16).

**Rivals (pp. 14-15).** Pooled, early demeaning, late demeaning, and unit dummies.

**Simulation (pp. 16-27).** Baseline N = 500 and T = 10, with others up to N = 10 and T = 500 (p. 25). 100 datasets per setting (p. 26).

## Result
- **Cross-fit by unit (p. 20).** "We should not split by unit when cross-fitting, at least if unobserved heterogeneity could be plausibly present." The bias is heavy for unit dummies and "(much) weaker" for correlated random effects and pooled models.
- **Early demeaning (pp. 3-4).** Strongly biased with nonlinear confounding.
- **Late demeaning (p. 24).** Accurate when unit effects do not touch the confounders. Otherwise it removes the variation twice, so it is biased.
- **Correlated random effects (p. 24).** "Across settings, only DML with correlated random effects consistently delivers estimates that are close to the true effect."
- **Scope (p. 3).** The paper studies point estimates. It does not derive variance estimators.

## Limits
- Simulation only, with no finance data.
- Heterogeneity sits on the unit dimension. The baseline has no time dimension effects (p. 25).
- The number of predictors doubles (p. 16).
- A time mean uses all periods. So it holds look-ahead, and the method fits a research test only.
- We read pp. 1-5, 15-16, 20, 24-27.

## Section touched
`docs/decisions/2026-11-01-clocks-residual-timing.md` Method 2. `docs/methodology.md` Section 4.7.1.

## Use for the two clocks
**What the source says.** A panel slope needs a model of the unit, and issuer means inside the learners are the most stable route.

**What our data says.** The earlier form of arm A of Method 2 held no issuer term and no month term. No test has run.

**What we decide (our proposal, not the source's claim).**
1. Arm A adds issuer means of `X` to both learners. This keeps cross-issuer variation in the clock feature.
2. A second column adds the issuer mean of the clock feature too, which is the source form. That column reads only changes inside an issuer. Clock features move slowly, so it may have little power. Report `v_var`.
3. Fold splits stay by issuer, because clock features are issuer-level and rows of one issuer are near copies. This goes against the source on p. 20, and it follows Chen, Polselli, and Clarke (pp. 17-18). Report a random-row split beside it. The review records the disagreement.

**Test.** A synthetic panel with a month shock, a feature drift, and no true effect must give `theta` near 0 under arm A.
