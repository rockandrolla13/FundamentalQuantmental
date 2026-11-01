# Chen, Polselli, and Clarke (2026), "Double Machine Learning with High-dimensional Interactive Fixed Effects"

arXiv preprint 2608.01137v1, preliminary draft of August 4, 2026 (47 PDF pages), DOI 10.48550/arxiv.2608.01137, at https://arxiv.org/pdf/2608.01137. **Working paper. Not peer reviewed.** We read Sections 1 to 5. Page numbers below are PDF pages. The application uses US equities, not bonds.

## Claim
The authors extend double machine learning to a panel with interactive fixed effects, which are latent factors with unit-specific loadings (pp. 1–2). Simulations show that it beats the linear IFE estimator outside the correctly specified linear case (p. 1). Bias falls mainly with the time and covariate dimensions (pp. 1, 5).

## Method
1. **Model (p. 6, eqs. 2.1 to 2.3).**

```latex
Y_{it} = \theta_0 V_{it} + l_0(X_{it}) + \lambda_i' f_t + U_{it}, \quad V_{it} = D_{it} - m_0(X_{it}) - \phi_i' f_t, \quad X_{it} = \Gamma_i' f_t + E_{it}
```

Intuition: each unit carries its own exposure to unseen common shocks, and these shocks can drive the outcome, the variable on test and the controls at once.

2. **Remove the factors by projection (pp. 9, 17).** The authors do not estimate factors by PCA. They use cross-section averages of `X`, in the common correlated effects tradition of Pesaran (2006).

```latex
\hat\Pi = I_T - \hat W(\hat W'\hat W)^{-}\hat W', \qquad \hat W = \bar X \hat\Phi, \qquad \hat r = \sum_{i=1}^{p} I(\hat\varphi_i \ge \alpha\hat\varphi_1)
```

Intuition: if controls load on the common shocks, then their average over units traces those shocks, and the projection strips them out.

The user sets `alpha` at 0.01, 0.05, or another small number (p. 9).

3. **Orthogonal score on projected data (p. 15, eqs. 3.17, 3.18).** Learn `l` and `m` on the projected data, form both residuals, and solve the moment.
4. **Cross-fitting (pp. 17–18).** Split units, not rows, into K folds. The projection uses the full sample. The score follows Chernozhukov et al. (2018).
5. **Inference.** Cluster-robust variance at the unit level (pp. 3, 29). A HAC form applies when the score is serially correlated (p. 14).

**Assumptions (pp. 10–14).**
- Strict exogeneity: lags of the outcome and treatment do not predict the confounders (p. 10).
- Additive separability of observed and latent confounding (p. 10).
- Pervasive factors in `X` (p. 11).
- Rate `o((NT)^{-1/4})` for each learner (p. 12).
- Growth: `(T+p)^2 log^2(T+p) = o(NT)`, which for p of order T means `T log^2 T = o(N)` (p. 13).
- Units are cross-sectionally independent (p. 14). Relaxation is left to future work (p. 14).
- The projected treatment must retain variation: `E[V~^2] >= c_V > 0` (p. 14).

## Data
- **Simulation (pp. 19–26).** 100 replications. N = 20, T in {30, 50, 100}, p in {50, 100, 300}, two factors, and two relevant covariates. Three designs: linear, nonlinear smooth, discontinuous. Larger N of 50, 100, 500 in Appendix C (p. 26).
- **Application (pp. 27–28).** 29 Dow Jones firms, 72 months, April 2016 to March 2022, 89 lagged characteristics, threefold block cross-fitting, cluster-robust errors (p. 29).

## Result
**Bias at p = 50, T = 30 (Tables 1 to 3, pp. 22–25).** True theta is 1.

| Design | IFE | DML Lasso | DML Boosting | DML Neural net |
| --- | --- | --- | --- | --- |
| Linear | 0.0280 | 0.0382 | −0.0814 | −0.2094 |
| Nonlinear smooth | 0.0400 | 0.0873 | −0.0497 | −0.1760 |
| Discontinuous | 0.2446 | 0.1261 | 0.0389 | −0.1506 |

**Inference.** In the linear design at p = 50 and T = 30, the IFE standard error is 1.6615 against a standard deviation of 0.0711, so it is severely conservative (p. 22). DML Lasso has 0.0408 against 0.0452 (p. 22).

**Learner ranking (pp. 26–27).**
- DML Lasso is the most consistent across designs, if the dictionary is rich. Its bias falls mainly with T, not N.
- DML Boosting does best with discontinuities.
- DML Neural net is unstable, with standard errors that "underestimate the standard deviation severely" (p. 26).
- IFE has a bias outside the linear case that more units do not remove.

**Application (Table 4, p. 29).** Coefficients on monthly excess stock returns.

| Characteristic | OLS | IFE | DML-IFE Lasso | DML-IFE Boosting | DML-IFE Neural net |
| --- | --- | --- | --- | --- | --- |
| Bid-ask spread | 0.946*** | −0.207 | −0.007 | −0.159 | −0.006 |
| Change in inventory | −0.144 | −0.07 | −0.037*** | −0.387* | −0.195** |
| Scaled earnings forecast | −0.099 | −0.004 | −0.092*** | −0.216*** | 0.003 |

The authors read the bid-ask result as OLS bias from unmodelled interactive effects (p. 28).

## Limits
- Preprint and marked preliminary. No journal review.
- Application estimates differ by up to ten times across learners on one characteristic (Table 4, p. 29). The sample is small: N = 29.
- The authors assume cross-sectional independence after factors (p. 14). Credit residuals may keep dependence within sector. The paper has no test of this.
- Strict exogeneity may fail for any feature that reacts to past spreads. The paper does not cover feedback.
- The method needs `X` to load on all factors (p. 11). A factor that `X` misses stays in the residual.
- The projection is computed on the full sample (p. 18). That is not point-in-time.
- The panel design is for equal-spaced data, but a unit's series may end early (p. 6, note 2). Other unbalanced forms are not covered.

## Section touched
`docs/methodology.md` Section 7.2 (sector-by-date effects against issuer-specific loadings), Section 7.3, Section 4.7 (test), Section 11.

## Use for the two clocks
**What the source says.** A date effect assumes that all units respond to a shock in the same way. Interactive effects let exposures differ. If they matter, a plain date or sector effect leaves bias in the coefficient. The application shows this for the bid-ask spread (p. 28).

**What our data says.** Section 7.2 uses sector-by-date effects, and `renewal_split_test` uses a monthly cross-section, which removes a common date mean only. No IFE test exists on our panel. Section 4.7 holds 187 issuers and 99 months. These sizes are close to the application's T but are much larger in N. The growth condition `T log^2 T = o(N)` does not look close to met there: at T = 99, `T log^2 T` is about 2,090 with the natural log, against N = 187 (our arithmetic).

**What we decide (our proposal, not the source's claim).**
1. **Robustness arm of the clock test.** Report `theta` for a clock feature from three models: monthly cross-section, sector-by-date effects, and panel DML with interactive effects. This arm is report only, with no conclusion, because its rate condition does not look met on our panel, and learners differ widely in the source (p. 29).
2. **Learner choice (our choice, v0).** Use Lasso with a rich dictionary and boosting. Drop neural nets on this panel. Report both, as the application shows large gaps between learners.
3. **Check the residual variation first.** Clock features update at filing dates and move slowly. After `m` and the projection, `V` may be near zero within an issuer. Report `E[V^2]` per feature, as the paper's relevance condition requires (p. 14). A feature below the data's noise floor has no test.
4. **Feedback warning.** Debt maturity may react to past spreads, since issuers can refinance when spreads are low. This is our reasoning, not the paper's. It would break strict exogeneity for the refinance share. So use the recontract share as the main test, and use lags of at least one filing for the refinance share.
5. **Research only.** The projection and cross-fit use the full sample. Keep this out of live scoring.
