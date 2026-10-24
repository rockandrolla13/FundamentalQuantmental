# Duffie, Saita, and Wang (2007), "Multi-Period Corporate Default Prediction with Stochastic Covariates"

Journal of Financial Economics 83(3), pp. 635–665. Peer-reviewed journal article. We read the open working paper: NBER Working Paper 11962, January 2006 (author order Duffie, Wang, Saita), https://www.nber.org/papers/w11962. Page numbers below are the printed page numbers of w11962. The journal version may differ in coefficients. Quote the journal only after a check against it.

## Claim
A firm's term structure of default probabilities depends on firm-level and macro covariates and on how those covariates move over time (p. 1). Distance to default (DD) dominates every other covariate in economic size (pp. 1, 20). Given DD and the firm's own stock return, the default intensity falls with the 3-month Treasury rate and rises with the trailing S&P 500 return (p. 21). GDP growth, the 10-year yield, personal income growth, the Aaa-Baa spread, firm size, and the industry-average DD add nothing once the four covariates are in (p. 16).

## Method
**Doubly-stochastic intensity (pp. 7–8).** A Markov state X_t = (U_t, Y_t) holds firm covariates U and macro covariates Y. Default arrives with intensity λ_t = Λ(X_t). Other exits (merger, delisting) arrive with intensity α_t = A(X_t). Given the path of X, exits are independent Poisson arrivals.

```latex
q(X_t, s) = E\left[ \int_t^{t+s} e^{-\int_t^{z} (\lambda(u) + \alpha(u))\,du}\,\lambda(z)\,dz \;\middle|\; X_t \right]   \quad (1)
```

Intuition: the chance of default by t + s is the chance to survive both default and other exits to each date, times the default rate at that date, summed over dates.

**Intensity form (p. 20).**

```latex
\Lambda(x;\mu) = e^{\mu_0 + \mu_1 x_1 + \cdots + \mu_n x_n}   \quad (17)
```

Intuition: each covariate scales the default rate by a constant factor per unit, the same for all firms.

**Decoupled likelihood (pp. 11–12).** Under the doubly-stochastic assumption the log likelihood splits into a covariate time-series part (γ) and an intensity part (β = (μ, ν)). The intensity part is a standard competing-risks duration model with time-varying covariates. Other exits censor the default spell.

**Covariate dynamics (pp. 18–19).** A Gaussian VAR(1), monthly step. Two Treasury rates follow a 2-factor mean-reverting model. DD and log assets mean-revert to a firm-specific target θ_iD, with a drift term in the short rate gap:

```latex
D_{i,t+1} = D_{it} + k_D(\theta_{iD} - D_{it}) + b_1(\theta_r - r_t) + \sigma_D\,\eta_{i,t+1}   \quad (14)
S_{t+1} = S_t + k_S(\theta_S - S_t) + \xi_{t+1}   \quad (15)
```

Intuition: firms steer leverage back to a target, and the macro state mean-reverts, so the hazard term structure slopes toward the long-run mean.

**DD construction (App. A, pp. 35–36).** Default point L = max(Compustat 45, 49) + 0.5 × item 51. Iterate the Black-Scholes call equation for V and σ_A = sdev of quarterly ln V changes. T = 4 quarters.

**Out-of-sample test (pp. 29–31).** Fit on 1979–1992. Score 1993–2004. Report the accuracy ratio (AR = 2 × area between the power curve and the diagonal) at 1 and 5 years.

## Data
- US-listed firms of the Moody's "Industrial" category with a Moody's and Compustat common identifier, at least 6 months of data. 2,770 firms, 392,404 firm-months, 1979–2004 (p. 14).
- Exits (Table 1, p. 16): 175 bankruptcies, 495 defaults, 497 failures, 872 mergers or acquisitions, 877 other exits. Exits that are not defaults outnumber defaults by more than 3 to 1.
- Default = bankruptcy, distressed exchange, missed payment, and other Moody's default types (p. 15).
- Macro: 3-month and 10-year Treasury (Federal Reserve), trailing 1-year S&P 500 return (CRSP), GDP and industrial production growth (BEA) (p. 13).

## Result
- **Intensity coefficients, default (Table 2, p. 21).** Constant −2.156 (0.113). DD −1.129 (0.036). Trailing 1-year own stock return −0.694 (0.075). 3-month Treasury rate −0.105 (0.021) per percentage point. Trailing 1-year S&P 500 return +1.203 (0.289).
- **DD dominates.** A 10% fall in DD raises the default intensity by 11.3% (p. 20). A one-standard-deviation shock to DD moves the Xerox hazard curve far more than a one-standard-deviation shock to the short rate, because DD has a larger scaled coefficient and more persistence (pp. 25–26, Figures 4 and 5).
- **Macro signs are not the textbook signs.** The short rate enters with a negative sign. The authors read it as the Fed raising rates in expansions (p. 21). The S&P 500 return enters with a positive sign, given the firm's own return (p. 21). The authors offer only a tentative reason.
- **Rejected covariates (p. 16).** 10-year yield, personal income growth, GDP growth, Aaa-Baa spread, log model-implied assets, industry-average DD. Industrial production is marginally significant, coefficient about 2 standard errors (footnote 13, p. 16).
- **Fit.** The model implies about 471 defaults against 495 observed, 1979–2004 (p. 21).
- **Out of sample (Table 3, p. 31).** AR for default: 0.87 at 1 year (1993–2004), 0.70 at 5 years (1993–2000). Refitting each year does not change the AR (p. 30). Moody's ratings give 65% and bond yield spreads give 74% for 1999–2003, from Hamilton and Cantor (2004) (p. 30). The worst 20% of firms hold about 92% of the next-year defaults (p. 29). Top-decile capture of next-quarter defaults is 94% for 1993–2004 (p. 31).
- **Merger is not predictable.** AR for merger is −0.03 at 1 year (Table 3).
- **Correlation gap.** The model implies default correlations that are "unrealistically low" against de Servigny and Renault (2002) (p. 34). This gap motivates the frailty paper (`duffie-eckner-horel-saita-2009-frailty.md`).
- **Mean reversion.** k_D = 0.0355 a month, σ_D = 0.346 (App. B, p. 37). Median target DD θ_iD ≈ 3.1, inter-quartile range 1.4 to 4.8 (p. 19). A common target produced implausible hazard curves for low-leverage firms, so the authors fit θ_iD firm by firm (p. 19).

## What our data says (docs/methodology.md 5.2 and 5.4, hy/macro.py, hy/groups.py, data/raw/backtest, 24 October 2026)
**What the plan holds.** Section 5.2 fits P(EBITDA_{t+4} < (1 − δ_i) EBITDA_t | m_t, sector) = σ(θ_0 + θ'm_t + θ_sector). The vector m_t is `hy_oas`, `sloos_tightening`, `default_rate_fcst`, `pmi`, and the sector drivers. Section 5.4 uses the fitted p as the downside weight of every case under every macro path. Estimate E1 "Weighted cases and stories" (0.15 inside G2) reads those weights. Estimate E10 "Excess over cash" (0.05 inside G1) reads μ = Σ q X from `hy/alpha.py`, so the same weights move it.

**What this paper changes.**
1. **The plan has no firm-level covariate.** In DSW, firm DD dominates the hazard (Table 2, pp. 20, 25). Macro covariates only shift the level for all firms. In the 5.2 logistic, two issuers in one sector at one date get the same p unless δ_i differs. That makes p a sector-date base rate, not an issuer probability. Decision needed: add one firm-state term (net leverage or interest cover from `annual_ebitda`, or naive DD where equity exists), or rename p as a base rate and let the case set carry the issuer difference.
2. **Macro signs can flip once firm state is in.** The short rate enters with a negative sign and the equity index with a positive sign, conditional on DD (p. 21). The Aaa-Baa spread drops out given DD (p. 16). Our `hy_oas` may do the same once a firm term enters. So a monotone-sign test on θ must state whether it conditions on firm state. Do not hard-code the expected sign of `hy_oas` or `pmi` until the conditional fit exists.
3. **One horizon only.** The 5.2 logistic is a single 4-quarter model. DSW say one-period logits cannot extrapolate to longer horizons without covariate dynamics (p. 2). Section 5.3 asks for 8-quarter features. Either fit a second logistic at 8 quarters, or chain the 4-quarter model through the macro paths of 5.4. The paths already give m_{t+4} per path, so the chain is cheap.
4. **Exits censor the event.** Non-default exits are 3.5 times defaults (Table 1). In our panel an issuer acquired or delisted before t + 4 has no EBITDA_{t+4}. Dropping those rows is a survivorship filter. Treat them as censored, and report the share.
5. **Correlation is too low without a latent factor (p. 34).** Observed macro covariates alone understate how bad years cluster. See the frailty card before 5.4 uses p for tail features (`lev_peak_down`, `p_liq_short_h`).

**Inputs on disk.** `data/raw/backtest/annual_ebitda.parquet` has `oibdp` and `debt` with `available_at`, 50,336 rows, fiscal years 1995–2026. That gives the 5.2 target at an annual step. `equity_monthly.parquet` gives the own trailing return. The macro registry holds `hy_oas`, `sloos_tightening`, and `pmi` (`hy/macro.py` INDICATORS). No quarterly EBITDA panel exists in the backtest files yet.

**Falsifiable tests (not run).**
1. **Firm term.** On `annual_ebitda`, define the event EBITDA_{t+1y} < 0.8 EBITDA_t. Fit (a) macro + sector and (b) macro + sector + net leverage + own trailing return. Walk forward by year from 2005. Reject the macro-only form if (b) beats (a) in out-of-sample AUC in at least 3 of 2008, 2015, 2020, and 2022.
2. **Sign stability.** Report the sign and z-statistic of `hy_oas` and `pmi` in (a) and (b). If a sign flips between (a) and (b), the 5.2 sign test must use (b).
3. **Censoring.** Count issuers with EBITDA at t and none at t + 1y. If the share exceeds 10%, fit a censored (discrete-time competing-risks) logit and compare θ with the dropped-row fit.

## Limits
- We read the 2006 working paper, not the 2007 journal version. Coefficients may differ in the published Table.
- US listed industrial firms, 1979–2004. Defaults, not EBITDA declines. The paper says nothing directly about an operating-earnings event.
- The doubly-stochastic assumption fails the Das, Duffie, Kapadia, and Saita (2005) tests, as the authors say (p. 3).
- The positive S&P 500 coefficient has no firm explanation in the paper.
- Firm-specific targets θ_iD have wide standard errors and drive much of the error in the hazard curves (p. 19).
- The AR comparisons with ratings and spreads use a different sample and period (Hamilton and Cantor 2004).

## Section touched
`docs/methodology.md` Section 5.2 (macro conditioning of the scenario weights) and Section 5.4 (case weights under paths, 8-quarter features). Estimates E1 and E10 in `hy/groups.py`. No decision page yet: the sprint that fits 5.2 should add one that records the firm-term choice and the censoring rule.
