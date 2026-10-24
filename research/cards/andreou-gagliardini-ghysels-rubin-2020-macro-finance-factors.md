# Andreou, Gagliardini, Ghysels, and Rubin (2020), "Mixed-Frequency Macro–Finance Factor Models: Theory and Applications"

*Journal of Financial Econometrics* 18(3), pp. 585–628. Peer-reviewed. Copy: `/home/ak/Documents/JFEC-combined-existing-2026-08-30/033-nbaa015-...pdf`. Page numbers are PDF pages (44 pages). The journal page is the PDF page plus 584.

## Claim
1. A monthly finance panel and a quarterly macro panel share one common "macro–finance" factor, but only inside each regime. Over 1963–2017 as a whole, no common factor with constant loadings exists (pp. 1, 3).
2. The break is the Great Moderation, about 1984Q1. The loadings change across it (p. 3, pp. 17–20).
3. Interest rate spreads and credit spreads drive the common factor in both regimes. Their R² falls from 0.42–0.85 before the break to 0.30–0.46 after it (p. 26).
4. The common factor Granger-causes GDP growth, consumption growth, and the Baa–Aaa default spread. Its predictive effect is much weaker after the break, and for the default spread it loses its role in almost all models (p. 36).
5. Mixed-frequency (MIDAS) models with these factors beat a random walk out of sample for GDP growth and the Baa–Aaa spread (Table 10, p. 38).

## Method
**Group factor model (Eq. 1.1, p. 3).** Two panels, each with a common block and a group-specific block:

```latex
\begin{bmatrix} y_{1,t} \\ y_{2,t} \end{bmatrix} = \begin{bmatrix} \Lambda^c_1 & \Lambda^s_1 & 0 \\ \Lambda^c_2 & 0 & \Lambda^s_2 \end{bmatrix} \begin{bmatrix} f^c_t \\ f^s_{1,t} \\ f^s_{2,t} \end{bmatrix} + \begin{bmatrix} \varepsilon_{1,t} \\ \varepsilon_{2,t} \end{bmatrix}   \quad (1.1)
```

Intuition: part of what moves markets also moves the real economy, and the model separates that shared part from the parts that belong to one panel only.

Estimate principal components per panel, then test for a common factor with canonical correlations. Aggregate monthly data to quarters first, or extract components first and aggregate after. The paper shows both give almost the same factors (p. 3). Test for breaks in loadings with LM and supLM tests (pp. 18–20). Forecast with linear and Almon-MIDAS regressions. Select by BIC. Evaluate out of sample against a random walk with the MSE-F test (pp. 37–40).

## Data
- Macro: quarterly FRED panel (McCracken and Ng type), groups such as output, employment, housing, prices, money and credit (p. 14).
- Finance: monthly panel with interest rates, credit spreads (the Gilchrist and Zakrajšek 2012 spread), commodity spreads, stock market indices, Fama-French portfolios (p. 2, p. 14).
- 1963–2017. Out of sample for GDP, consumption, and Baa–Aaa: in sample 1986Q1–2001Q4, out of sample 2002Q1–2017Q4 (p. 39).

## Result
- One common factor in each regime, none over the full sample (p. 3).
- Pre-break drivers of the common factor: interest rate and default spreads (R² 0.42–0.85), commodity spreads (0.28–0.49), the VXO (0.59). Post-break, the VXO R² falls to 0.01 (p. 26).
- Baa–Aaa spread, one quarter ahead, recursive scheme: RMSE ratios against the random walk fall to 0.41–0.62 with mixed-frequency factors. The best is MIDAS with the GZ spread and the factors at 0.41 (Table 10, Panel A2, p. 38).
- GDP growth, recursive: best RMSE ratio 0.63 (MIDAS with the ADS index and the factors) (p. 38).

## What our data says
No fit on our data yet. Effect on the three macro links:

1. **Link 1, path probabilities (5.4).** Indirect. The paper shows that credit spreads carry the macro state and lead GDP. Our paths take GDP and CPI from forecasters, and treat `hy_oas` as an output of the path (decision page `2026-10-22-macro-path-construction`: "450 bp + 150 bp per -1 sd of GDP"). The paper supports the reverse direction too: spreads predict growth. Proposal: add `hy_oas` (or the GZ spread) as a check on the path masses. If the current spread sits above the level that the recession path implies, flag the gap in the memo. Do not change the mass by hand.
2. **Link 2, downside weights (5.2).** The break result is a warning for the pooled logistic. Loadings of macro variables on the common factor change across regimes. A logistic fitted on 2007–2026 may not hold in the next regime. Test: fit the logistic on 2007–2016 and on 2017–2026 separately. Compare the coefficients with a Wald test. If they differ, add a regime dummy or use a rolling window, and record the choice on a decision page.
3. **Link 3, revenue shift (5.2).** Nothing direct. The same break warning applies to `β_sector`.

## Limits
- Aggregate data only. No firm, sector, or EBITDA results.
- The default variable is the Baa–Aaa spread, an investment grade spread, not a high yield default rate.
- One-quarter-ahead forecasts only. Our horizon is 4 to 12 quarters.
- The paper is mostly econometric theory. The empirical part is one application.

## Section touched
`docs/methodology.md` Section 5.4 (paths, `hy_oas` as a check on masses) and Section 5.2 (stability of the logistic across regimes). Decision page `docs/decisions/2026-10-22-macro-path-construction.md`.
