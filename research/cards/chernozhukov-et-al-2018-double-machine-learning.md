# Chernozhukov, Chetverikov, Demirer, Duflo, Hansen, Newey, and Robins (2018), "Double/Debiased Machine Learning for Treatment and Structural Parameters"

The Econometrics Journal 21(1), pp. C1–C68, DOI 10.1111/ectj.12097. Peer-reviewed journal article. We read arXiv 1608.00060v7, dated November 3, 2024 (71 PDF pages), at https://arxiv.org/pdf/1608.00060. The arXiv text states a correction to the published Assumptions 4.1 and 4.2 (p. 32, note 8). The volume and pages come from Crossref. Page numbers below are PDF pages. **This is an econometric method. It holds no credit evidence.**

## Claim
A low-dimensional parameter can be estimated at the root-N rate, with valid confidence intervals, while machine learning estimates the high-dimensional nuisance functions (p. 1). This needs two parts: a Neyman-orthogonal score and cross-fitting (p. 1). A plain plug-in of an ML fit gives an estimator that is not root-N consistent (pp. 1, 3).

## Method
1. **Partially linear model (p. 2, eqs. 1.1, 1.2; p. 31).** `D` is the variable of interest, and `X` holds the controls.

```latex
Y = D\theta_0 + g_0(X) + U, \quad E[U \mid X, D] = 0, \qquad D = m_0(X) + V, \quad E[V \mid X] = 0
```

Intuition: the second equation records how the controls drive `D`, and that link is what causes the bias if it is ignored.

2. **Why the plug-in fails (p. 3).** With `g` learned on another sample, the scaled error holds a term `b`.

```latex
b = (E D_i^2)^{-1} \frac{1}{\sqrt{n}} \sum_{i \in I} m_0(X_i)\big(g_0(X_i) - \hat g_0(X_i)\big) + o_P(1)
```

Intuition: regularisation leaves a bias in `g`, and this bias does not average out when `D` correlates with `X`.

3. **Orthogonal score (p. 31, eq. 4.4).** The partialling-out form, with `l(X) = E[Y | X]`.

```latex
\psi(W;\theta,\eta) = \big\{Y - \ell(X) - \theta\,(D - m(X))\big\}\big(D - m(X)\big), \qquad \eta = (\ell, m)
```

Intuition: regress the part of `Y` that the controls miss on the part of `D` that the controls miss, so small errors in either fit have no first-order effect.

4. **Cross-fitting, DML2 (p. 24, Definition 3.2).** Split the sample into K folds. Fit `eta` on the complement of each fold. Solve the pooled moment over all folds. The authors recommend DML2 and K of 4 or 5 (p. 24).
5. **Split repeat (pp. 30–31, Definition 3.3).** Repeat S times. Report the median estimate. The variance adds the spread across splits.
6. **Rate condition (p. 32, Assumption 4.1).** The product of the two nuisance errors must be below `delta_N N^{-1/2}`. So the two fits can each converge slowly (p. 33).
7. **Result (p. 32, Theorem 4.1).** Asymptotic normality, with variance as below.

```latex
\sqrt{N}(\tilde\theta_0 - \theta_0)/\sigma \rightsquigarrow N(0,1), \qquad \sigma^2 = [E V^2]^{-1} E[V^2 U^2] [E V^2]^{-1}
```

Intuition: the variance has the sandwich form of a regression of `U` on `V`, as if both fits were known.

## Data
- Theory assumes `(W_i)` are i.i.d. copies (pp. 12, 23).
- Three illustrations (pp. 39–46): the Pennsylvania reemployment bonus experiment, 401(k) eligibility, and institutions and growth. None is about finance or credit spreads.
- The illustrations use lasso, regression trees, random forests, boosting, neural nets, and an ensemble, with 2-fold and 5-fold cross-fitting and 100 splits (pp. 39–40).

## Result
- **Theorem 4.1 (p. 32).** Uniform validity of the confidence interval over the model class.
- **Simulation figures (pp. 4, 7).** The orthogonal estimator centres on the truth, where the non-orthogonal one is shifted. Sample splitting removes the overfitting bias.
- **Bonus experiment (Table 1, p. 41).** Effect on log unemployment duration, interactive model, 2-fold: from −0.073 to −0.084 across learners, with standard error 0.036.
- **Across examples (p. 46).** The choice of ML method does not change the conclusion in any example. The split adjustment raises standard errors, but it does not alter the main results.

## Limits
- `theta_0` has a causal reading only if `D` is conditionally exogenous (p. 31). The method does not supply exogeneity. For a clock feature, it delivers only a partial effect.
- The i.i.d. setup does not hold for a bond panel. Bonds on one date share shocks, and issuers repeat. So a panel form is needed. See `chen-polselli-clarke-2026-panel-dml-interactive-fixed-effects.md`.
- The partially linear form assumes a constant `theta` and additive `g`. Heterogeneous effects need another score.
- Cross-fitting uses data from all periods for the nuisance fits. That is fine for a research test of `theta`. It breaks the no-look-ahead rule if used in a live signal.
- Finite-sample results depend on K and learner choice (p. 24).

## Section touched
`docs/methodology.md` Section 7.2 (fair spread `f_t` as nuisance), Section 7.3 (residual), Section 4.7 (test of the clock features), Section 11 (validation).

## Use for the two clocks
**What the source says.** Controls fitted by ML cannot be plugged in directly. One must residualise both `Y` and `D` on the controls, with cross-fitting.

**What our data says.** `renewal_split_test` regresses log spread on two shares with no controls. So the −2.07 on the recontract share may reflect any correlated trait. Section 4.7 names one, firm strength, as untested. No DML run exists.

**What we decide (our proposal, not the source's claim).**
1. **The core test of a clock feature as an explanation of the residual.** Set `Y` = log spread, `D` = one clock feature, `X` = the Section 7.2 blocks. Fit `l` with the monotone model that Section 7.2 specifies. Fit `m` with a separate learner. Then estimate the slope below.

```latex
\hat\theta = \frac{\sum_{i,t} \hat V_{i,t}\,\big(\log s_{i,t} - \hat\ell(X_{i,t})\big)}{\sum_{i,t} \hat V_{i,t}^2}, \qquad \hat V_{i,t} = c_{i,t} - \hat m(X_{i,t})
```

Intuition: ask whether the part of the clock that the fundamentals do not predict lines up with the part of the spread that the fundamentals do not predict.

2. **Do not regress the S1 residual on the raw clock feature.** That is the plug-in form with the `b` term above, because clock features correlate with leverage and size. Use `V_hat`, the clock net of `X`.
3. **Falsifiable claim.** If the firm strength story of Section 4.7 holds, then `theta` on the recontract share moves from −2.07 toward zero once `X` enters. If `theta` stays negative with a tight interval, the sign is a fact about the market, and the story fails.
4. **Fold rule (our choice, v0).** Split by issuer, not by row, so that one issuer does not sit on both sides. K = 5 and S = 100, median aggregate, as in the paper's examples (pp. 24, 40).
5. **Output.** `theta`, its interval, the fit quality of `l` and `m`, and `theta` by learner. Report the spread across learners as a warning. This is a research test only. It feeds no live score, because of the look-ahead limit above.
