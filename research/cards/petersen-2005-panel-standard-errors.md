# Petersen (2005, revised 2006), "Estimating Standard Errors in Finance Panel Data Sets: Comparing Approaches"

Published in The Review of Financial Studies 22(1), pp. 435-480, DOI 10.1093/rfs/hhn053. Peer-reviewed. **We did not open the journal article.** We read NBER Working Paper 11280, revised June 2006, 70 pages, at https://www.nber.org/system/files/working_papers/w11280/w11280.pdf. Page numbers are PDF pages. PDF page = printed page + 2. Evidence class: method, with simulated panels and two equity and capital structure applications.

**Added at the audit close.** The corpus holds this paper with the status `NOT_SCREENED`. The method audit named it as essential.

## Claim
When a firm effect sits in the residual and in the regressor, both OLS and Fama-MacBeth standard errors are too small (p. 4). The Fama-MacBeth bias is larger than the OLS bias (p. 16). Adjusted Fama-MacBeth errors stay biased (p. 5). Standard errors clustered by firm are unbiased under a firm effect (pp. 4-5).

## Method
**True variance of the Fama-MacBeth mean under a firm effect (p. 15, eq. 12).**

```latex
Var(\hat\beta_{FM}) = \frac{\sigma_\varepsilon^2}{N T \sigma_X^2}\big(1 + (T-1)\rho_X\rho_\varepsilon\big)
```

Intuition: if the same firms keep the same regressor and the same error, then each month repeats the last month. T monthly slopes then hold far less than T slopes of information.

**Two-way clusters (p. 26, eq. 16).**

```latex
V_{Firm \& Time} = V_{Firm} + V_{Time} - V_{White}
```

Intuition: add the correlation within a firm to the correlation within a date, and subtract the diagonal that both count.

**Simulation (pp. 14-30).** 5,000 panels for most tables, with fixed and temporary firm effects and time effects.

## Data
Simulated panels, with two applications in Section VI of the paper.

## Result
- **Fixed firm effect (p. 16).** At `rho_X = rho_e = 0.75`, the OLS standard error has a bias of 60%, and the Fama-MacBeth standard error has a bias of 74%.
- **Rejections (p. 16, note 10).** At `rho = 0.50`, 25% of Fama-MacBeth t values and 15% of OLS t values are significant at the 1% level.
- **Newey-West on a panel (p. 21).** It underestimates under a fixed firm effect, because the weights fall with lag length and the firm effect does not fade.
- **Time effect (p. 5).** Fama-MacBeth is unbiased under a time effect alone.
- **Two-way clusters (p. 27).** They fit best when both dimensions have enough clusters. With 100 firms and 100 years, 1% of t values exceed 2.58.
- **Temporary firm effect (pp. 28-30).** Firm dummies do not repair OLS errors when the firm effect decays.

## Limits
- The paper assumes a correct model. It studies errors only (p. 8, note 4).
- A working paper copy. The journal numbers may differ.
- We read pp. 2-8, 15-22, 26-30.

## Section touched
`docs/methodology.md` Section 11. `hy/backtest.py` (`hac_mean`, `driscoll_kraay_ols`). `scripts/backtest_clocks.py` (`renewal_split_test`).

## Use for the two clocks
**What the source says.** A level regression with a persistent regressor and a persistent error needs clusters by firm. Fama-MacBeth with a lag adjustment does not repair it.

**What our data says.** `renewal_split_test` regresses log spread on two shares each month. It passes the slopes to `hac_mean` with `h - 1` lags, so 2 or 5. No AR(1) of the monthly slopes is on file.

**Our own check (not the source's result).** We simulated 187 issuers and 99 months with no true effect. The feature has AR(1) 0.97 and the residual has AR(1) 0.95. These two values are assumed. Script: `/home/ak/Gitrepos/sr-tracks/clocks-residual-timing/analysis/sensitivity/close/inference_check.py`.

| Rule | P(absolute t above 2), or P(p below 0.05) |
| --- | --- |
| Fama-MacBeth, Newey-West with 5 lags | 0.417 |
| Pooled OLS, clusters by issuer | 0.050 |
| Pooled OLS, clusters by issuer and month | 0.048 |
| Driscoll-Kraay with 12 lags | 0.318 |
| Permutation of issuer paths, 199 draws | 0.033 |

**What we decide (our proposal, not the source's claim).**
1. Read on-file t values from the split test as unverified, until the AR(1) of the slopes is printed.
2. Use pooled OLS with clusters by issuer and month, and a permutation null, for every level test in the proposal. Driscoll-Kraay is a report only.

**Test.** Print the AR(1) of the monthly slopes of the split test before Method 1 runs. See the rules of `docs/decisions/2026-11-01-clocks-residual-timing.md`.
