# Feng, Giglio, and Xiu (2020), "Taming the Factor Zoo: A Test of New Factors"

The Journal of Finance 75(3), pp. 1327–1370, DOI 10.1111/jofi.12883. Peer-reviewed journal article. We read NBER Working Paper 25481, January 2019 (45 PDF pages), at https://www.nber.org/system/files/working_papers/w25481/w25481.pdf. The journal text may differ. The volume and pages come from Crossref. Page numbers below are PDF pages. PDF page = printed page + 1. **Evidence is from US equities, not bonds.**

## Claim
A two-step selection method gives valid inference on the marginal pricing role of a new factor beyond a very large set of existing factors. This holds even when the selection makes mistakes (pp. 2, 6). Most factors introduced in 2012 to 2016 are redundant against earlier factors. A few, such as profitability, are not (p. 2). Results from a small benchmark such as the three Fama-French factors differ from results with selected controls (pp. 22–23).

## Method
**Model (pp. 9–10).** `g` is the factor on test and `h` is the set of controls. `C` is the covariance of test asset returns with a factor.

```latex
m_t = \gamma_0^{-1}\big(1 - \lambda_g' g_t - \lambda_h' h_t\big), \qquad E(r_t) = \iota_n \gamma_0 + C_g \lambda_g + C_h \lambda_h \quad (1,2)
```

Intuition: a factor matters for pricing when its covariance with assets explains average returns after the covariances with all other factors.

**Step 1a, first selection (p. 14, eq. 7).** Cross-section LASSO of mean returns on covariances with `h`.

```latex
\min_{\gamma,\lambda} \; n^{-1}\big\|\bar r - \iota_n\gamma - \hat C_h\lambda\big\|^2 + \tau_0 n^{-1}\|\lambda\|_1
```

Intuition: keep the controls that price the cross-section.

**Step 1b, second selection (p. 14, eq. 8).** LASSO of the covariance with `g` on covariances with `h`.

```latex
\min_{\xi_j,\chi_{j,\cdot}} \; n^{-1}\big\|\hat C_{g,\cdot,j} - \iota_n\xi_j - \hat C_h\chi_{j,\cdot}'\big\|^2 + \tau_j n^{-1}\|\chi_{j,\cdot}\|_1
```

Intuition: also keep the controls that resemble the new factor, because their omission would bias the test even if their own price looks small.

**Step 2, post-selection (p. 14, eq. 9).** Cross-section OLS on `g` and the union of both selected sets.

**Inference (pp. 15–16, Theorems 1, 2).** `sqrt(T)(lambda_g_hat - lambda_g)` is asymptotically normal for jointly large `n` and `T`. The variance uses a Newey-West form with residuals from a third LASSO of `g` on `h` (eq. 10).

**Tuning (pp. 20, 26).** 10-fold cross-validation with 200 seeds. The authors report heat maps of t-statistics across the seeds.

**Why SDF loadings, not risk premia (pp. 10, 23).** A factor can have a risk premium only because it correlates with true factors. A premium does not show that the factor helps to price other assets.

## Data
- 150 factors, monthly, July 1976 to December 2017 (p. 17). Fifteen published factors and 135 long-short portfolios built on surveyed characteristics (p. 17).
- 750 test portfolios: 3 by 2 size-characteristic sorts (p. 18). Robustness with 1,825 5 by 5 portfolios and 202 portfolios (pp. 18–19).
- NYSE, AMEX and NASDAQ stocks, no financials, value weighted (p. 17).

## Result
**Selection instability (pp. 19–21).** The first LASSO picks 4 factors. Across 200 seeds, only SMB is selected more than 70% of the time. Most factors are selected in 1% to 20% of seeds. The second LASSO picks 20 to 80 controls per test factor.

**Factors of 2012 to 2016 (Table 1, p. 36).** Loading in bp a month per unit beta, with t.

| Factor | Double selection | Single selection | FF3 controls | All controls |
| --- | --- | --- | --- | --- |
| RMW | 160 (4.45) | 15 (0.41) | 20 (1.80) | 74 (1.48) |
| HXZ ROE | 77 (3.37) | 23 (0.83) | 33 (2.92) | 104 (2.87) |
| QMJ | 73 (2.03) | 4 (0.11) | 39 (3.10) | 50 (1.04) |
| HXZ IA | 51 (2.11) | 5 (0.21) | 21 (1.94) | 40 (1.08) |
| Intermediary | 112 (2.21) | 60 (1.19) | 4 (0.08) | 22 (0.32) |
| Betting against beta | 35 (1.45) | 38 (1.50) | 36 (2.25) | 49 (1.49) |
| Gross profitability | 20 (0.48) | 3 (0.06) | 23 (2.00) | 13 (0.26) |

Nine of 15 factors are significant against FF3 (p. 23). In the double-selection column of Table 1, five of 15 are significant at 5% (p. 36).

**Recursive test (p. 24).** From 1994 onward, only 17 factors would have counted as useful.

**Robustness (Table 3, p. 38).** RMW stays significant in all five columns: t 4.45, 3.13, 1.98, 3.43, 2.11. The intermediary factor does not: t 2.21, 0.73, −0.33, −0.33, 1.92. The authors report that its significance is not robust to tuning (p. 26).

## Limits
- Equity evidence. No bond test is in the paper.
- Constant exposures and constant risk prices. The authors therefore advise portfolios rather than single assets (p. 10). Clock exposure at bond level would need portfolios or a conditional form.
- Sparsity is an assumption: few factors matter (p. 12).
- Asymptotics need large `n` and large `T`. A 99-month panel is short against the sample of more than 40 years used here.
- A non-zero SDF loading says that a factor helps to price assets. It does not say whether the premium is a risk premium or a persistent mispricing. The paper does not test this.
- The test does not address multiple testing of many candidate factors, and it leaves this open (p. 8, note 3).
- Standard errors are derived for LASSO. Other selectors have no derived theory here (p. 27, note 13).

## Section touched
`docs/methodology.md` Section 8 (admit a new signal), Section 11 (validation), Section 4.7 (test of the clock features). Related: `docs/factors/README.md`, `research/notes/quant-credit-factor-candidates.md`.

## Use for the two clocks
**What the source says.** The verdict on a new factor depends on the control set. Double selection removes the arbitrary choice, and single selection misses controls that resemble the new factor.

**What our data says.** `renewal_split_test` in `scripts/backtest_clocks.py` has no controls. The decision page `2026-10-22-duration-mismatch.md` asks for a partial correlation "after the Section 7.2 features", and that test has not run. None of F01 to F30 has a result on our data (`2026-10-26-conviction-book.md`).

**What we decide (our proposal, not the source's claim).**
1. **Double selection for the clock regressions.** Keep the source's selection logic but apply it to characteristics, in the Belloni form that the paper cites (p. 4).
   - Select controls from the Section 7.2 blocks that predict log spread.
   - Select controls that predict the clock feature.
   - Run post-selection OLS on the union, per month, then Fama-MacBeth with Newey-West errors.

   This replaces the two-regressor test of Section 4.7. Equity evidence supports the logic. The bond result is open.
2. **Traded clock factor test.** Form a long-short portfolio from the cost clock feature. Use `g` = that factor and `h` = the factors that exist in `hy/factors`, with bond portfolios as test assets. Report the seed heat map, not only the point estimate.
3. **Admission rule (our choice, v0).** A clock factor enters only if its loading is significant at 5% with double selection and stays significant in at least two of the three rival test-asset sets. Otherwise it stays a risk measure.
4. **Do not read the loading as mispricing.** Use `kelly-palhares-pruitt-2023-modeling-corporate-bond-returns.md` and `bartram-grinblatt-nozawa-2025-bond-book-to-market-mispricing.md` for that split.
5. **Power note.** Report how many months the test has. Our v0 keeps the test as a screen when the sample is under one full cycle, and it changes no weight.
