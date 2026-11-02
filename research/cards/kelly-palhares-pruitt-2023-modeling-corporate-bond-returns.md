# Kelly, Palhares, and Pruitt (2023), "Modeling Corporate Bond Returns"

The Journal of Finance 78(4), pp. 1967–2008, DOI 10.1111/jofi.13233. Peer-reviewed journal article. We read the SSRN version of August 26, 2021, from the local file `/home/ak/Documents/Quant Credit/ssrn-3720789.pdf` (66 PDF pages). The journal text may differ. The volume and pages come from Crossref. Page numbers below are PDF pages, which equal the printed pages. Two authors work at AQR (p. 1).

## Claim
A conditional five-factor model with latent factors and characteristic-driven betas describes the risk and return of US corporate bonds far better than earlier factor models (pp. 1–4). The model tells whether a characteristic predicts returns through betas (risk) or beyond them (alpha) (p. 19). Debt and equity are closely tied in their systematic parts and weakly tied in their idiosyncratic parts (p. 5).

## Method
1. **Zero-alpha model (p. 6, eq. 1).** `z` holds rank-scaled characteristics plus a constant, with L = 30 (pp. 15–16).

```latex
r_{i,t+1} = \beta_{i,t}' f_{t+1} + \varepsilon_{i,t+1}, \qquad \beta_{i,t} = z_{i,t}' \Gamma_\beta
```

Intuition: the characteristics tell how much of each hidden factor a bond carries this month, so exposures move as the bond changes.

2. **Alpha alternative (p. 56, eq. 14).**

```latex
r_{i,t+1} = \alpha_{i,t} + \beta_{i,t} f_{t+1} + \varepsilon_{i,t+1}, \qquad \alpha_{i,t} = z_{i,t}' \Gamma_\alpha, \qquad \beta_{i,t} = z_{i,t}' \Gamma_\beta
```

Intuition: a characteristic can earn return in line with the risk it predicts, or apart from it, and the second is what the authors call alpha.

3. **Estimation (p. 8, eqs. 2, 3).** Alternating least squares on first-order conditions. Factors are period-by-period cross-section regressions of returns on betas. The authors also show the link to PCA on managed portfolios `x = Z'r / N` (eq. 4).
4. **Return scale (p. 14, eq. 10).** Divide the credit excess return by duration times spread, with a floor of 0.25. Forty percent of bonds sit below the floor.
5. **Tests.**
   - `Gamma_alpha = 0`: wild bootstrap, t(7) errors, 1,000 runs (p. 56).
   - One characteristic: a Wald statistic on the row of `Gamma_beta` with a bootstrap (p. 31).
   - Out of sample: expanding window, first test month 36 months after the start (pp. 21–22).
   - Metrics: total, time series and cross-section R², and relative pricing error (pp. 10–12).
6. **Observable approximation (p. 35, eq. 12).** Panel OLS on factors interacted with instruments.

```latex
r_{i,t+1} = z_{i,t}' \Gamma_\beta\, g_{t+1} + \varepsilon_{i,t+1} = \operatorname{vec}(\Gamma_\beta)'(z_{i,t} \otimes g_{t+1}) + \varepsilon_{i,t+1}
```

Intuition: with known factors, an instrumented beta is only a regression of returns on factor times characteristic.

7. **Residual link to equity (pp. 41–43).** Split bond and equity returns into systematic and idiosyncratic parts, then regress bond parts on Merton-hedged equity parts.

## Data
- ICE corporate bond data for the Bank of America HY (H0A0) and IG (C0A0) indices, December 1999 to December 2020 (pp. 13–14).
- 14,600 bonds, 264 months, 555,894 bond-months (p. 15). Filters: spread from 50 to 2,000 bp, duration at least 0.25 years, no missing characteristics (p. 15).
- 29 characteristics (Table A.I, p. 55).
- Returns net a Treasury hedge portfolio, with option-adjusted analytics from ICE (pp. 13–14).

## Result
**Fit, five factors, out of sample (Table IV, p. 21).** Individual bonds: total R² 50.7%, cross-section R² 34.0%, relative pricing error 63.4%. Managed portfolios: total R² 98.5%, relative pricing error 1.8%.

**Model comparison, July 2004 to December 2019 (Table V, p. 23).**

| Individual bonds | MKT | BBW | FF | IPCA |
| --- | --- | --- | --- | --- |
| Total R² | 32.2 | −16.9 | −3.5 | 45.4 |
| Cross-section R² | 23.3 | −11.7 | −20.4 | 35.0 |
| Relative pricing error | 68.1 | 100.1 | 75.8 | 38.9 |

BBW's in-sample total R² is 26.8%, so out-of-sample failure comes from unstable betas (Table VI, p. 24; p. 25).

**Alpha test (Table A.II, p. 56).** Bootstrapped p-value for `Gamma_alpha = 0` is 0.0% for one to four factors and 2.6% for five. The authors fail to reject at the 1% level and adopt zero alpha (p. 21). At the 5% level, the test rejects.

**Characteristics (Table IX, p. 31).** Largest row norms: spread 0.34, constant 0.34, duration 0.32, bond volatility 0.31, equity momentum 0.25. Fifteen of 30 characteristics are significant at 5% (pp. 31–32).

**Strategies (Tables VII, VIII, pp. 28–30).** Gross Sharpe: tangency 6.23, quintile spread 3.53. Net at 19 bp one way: 2.48 and 1.37. With weight smoothing at gamma 0.3: 2.93 and 1.47. Monthly turnover is about 70%.

**HY segments (Table XIII, p. 39).** Out-of-sample total R²: BB 48.6%, B to D 45.8%. By liquidity tercile within HY: 47.5%, 48.5%, 46.0%.

**Observable factors with instruments (Table X, p. 34).** Total R² 42.4%, relative pricing error 62.9% for bonds, spread portfolio Sharpe 2.95.

**Idiosyncratic residual and equity (Table XIV, p. 40; p. 43).** Regress the bond residual on hedged equity parts: slope on systematic equity 0.01 (t 0.11), slope on idiosyncratic equity 0.89 (t 9.44), R² 4.3%. For the systematic bond part: slope 2.29 and R² 18.1%.

## Limits
- ICE analytics are proprietary, and spreads and returns may use evaluated prices. The paper gives the data choice, not a test against TRACE (p. 13).
- Zero alpha is a modelling choice at the 5% level. The p-value of 2.6% rejects at 5% (p. 56).
- High gross Sharpe ratios with about 70% monthly turnover rest on one flat cost of 19 bp (p. 29). Cost depends on bond and size.
- `Gamma` is constant over time, and the betas are linear in `z`. Bond-specific fixed terms are dropped because of overfit (p. 7, note 4).
- Latent factors have no fixed economic label. Labels rest on Figure 2 and a rotation choice (pp. 9, 33).
- The sample filter requires no missing characteristics (p. 15). A sparse feature such as RPO cuts the sample or needs a missing-value rule.
- Evidence covers IG and HY together. Segment results use one common model (p. 39).

## Section touched
`docs/methodology.md` Section 7.2 and 7.3 (what a residual is net of), S1, Section 8 (aggregator S8). Spec: `docs/factors/F01-ipca.md` holds the estimator. This card adds only the feature test. Cross-reference: `israel-palhares-richardson-2018-common-factors.md`.

## Use for the two clocks
**What the source says.** A characteristic's row in `Gamma_beta` measures whether it predicts risk exposure. A row in `Gamma_alpha` measures return that does not align with risk exposure (pp. 19, 56). So one model separates a risk reading from a mispricing reading.

**What our data says.** No IPCA fit has run on our data (`docs/factors/F01-ipca.md`, and the conviction book page). Section 4.7 records only the shares against log spread and against the IC beyond spread level.

**What we decide (our proposal, not the source's claim).**
1. **Two-row test of a clock feature (changes the Section 4.7 test).** Add one clock feature at a time to `z`. Fit the alpha form. Run the row tests.

| `Gamma_beta` row | `Gamma_alpha` row | Reading | Action |
| --- | --- | --- | --- |
| Not zero | Zero | The clock predicts factor risk, and return comes with it | Risk measure. It moves sizing in Section 9, not the signal |
| Zero | Not zero | Return that risk does not explain | Candidate mispricing. Go to the classifier in `bartram-grinblatt-nozawa-2025-bond-book-to-market-mispricing.md` |
| Not zero | Not zero | Both | Report both. Give weight only to the alpha part |
| Zero | Zero | No role beyond the other instruments | Keep as an analyst note only |

2. **Short-panel form.** The RPO panel has 99 months and 187 issuers (Section 4.7). A latent fit on it may be unstable. So first run equation (12) with the five observable factors of Table X. Cluster by month and by issuer. Use the bootstrap only on the larger cost clock panel.
3. **Missing rule.** Keep `docs/factors/F01-ipca.md` practice: rank 0 and a flag column. Report the row test both on the RPO-only sample and on the full sample, so that the flag does not carry the result.
4. **A cleaner idiosyncratic residual.** Define the bond residual as `eps` from IPCA less its projection on hedged idiosyncratic equity (Table XIV). Equity explains only 4.3% of `eps` variance, so most of `eps` stays. Then run the clock feature against that residual, and test whether it explains the level, as an alpha, and the squared residual, as idiosyncratic risk. The second regression is our addition.
5. **Test S1 against the model.** Add the S1 residual as one instrument. If the `Gamma_alpha` row is zero, S1 is a risk loading in this model, and Section 7.3 should not call it mispricing.
