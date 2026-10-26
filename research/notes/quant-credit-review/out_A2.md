# A2 root papers: new credit factors and signals

Folder: `/home/ak/Documents/Quant Credit/`. Files triaged: 28. Relevant: 15.
Page numbers are PDF pages of each file.
"Source says" holds only the content of the file. "We propose" holds our design.

## Triage table

| File | Title, authors, year | Topic | Relevant (yes/no) | Why |
|---|---|---|---|---|
| The determinants of CDS spreads_ evidence from (1).pdf | The determinants of CDS spreads: evidence from the model space. Pelster, Vilsmeier. Rev Deriv Res 2018 | Bayesian model averaging of CDS spread determinants. Copula tail dependence | yes | Tail dependence with the market is the top determinant of CDS spread changes. CDX IG and HY names. New factor |
| The_credit_spread_curve_I_Fundamental_concepts_fit.pdf | The credit spread curve I: fundamental concepts, fitting, par-adjusted spread, and expected return. R. J. Martin. arXiv 2201.01330, 2022 | Survival-curve fit, par-adjusted spread, carry, rolldown, RV | yes | Defines par-adjusted spread. Removes the high-price-high-spread bias. Critical for HY bonds far from par |
| Why Do ETF Flows Move Prices.pdf | Why Do ETF Flows Move Prices? Chao, Shah, Martin et al. Deutsche Bank Quant View, 9 May 2019 | ETF contraflow in US equities. Flow decomposition | yes | ETF flow signal transfers to HY bond ETFs (HYG, JNK). Also has VRP timing note (already known) |
| credit_bmi_v2 (1).pdf | Credit-BMI v2: an operational spread-forecasting engine. Internal note, 9 June 2026 | Credit index timing composite with conformal decision rule | yes | Candidate replacement for failed S7. Same model as credit_bmi_v2.pdf, run-focused version with code |
| credit_bmi_v2.pdf | A staged, regime-aware framework for forecasting credit spreads (Credit-BMI v2). Internal note, 9 June 2026 | Credit index timing composite, horizons, shrinkage weights | yes | Companion of credit_bmi_v2 (1).pdf. Not byte-identical. Read both, report once |
| credit_spread_stat_arb_architecture_bridge_v0_1.pdf | How the later ideas fit the original credit-spread strategy framework. Technical integration note, June 2026 | Architecture: survival-curve residual, convergence forecast, gates, costs | yes | Defines expected convergence q(h), deterioration gate, liquidity split. Extends S1 |
| effect of rates on quant strategies.pdf | Navigating through rising interest rates: impact for quant strategies. Chen, Shah, Zhao, Elledge, Chao. Deutsche Bank Quant View, 14 June 2018 | Scanned. Equity betas to PCA shift, twist, butterfly by ridge regression | yes (low) | Rate-factor beta transfers as a sector risk control. OCR used |
| fair_value.pdf | Bond fair value calculation using Gaussian mixture models. Quantitative Credit Trading Team, 30 Apr 2025 | Multi-source bond mid by GMM of quotes | yes (infra) | Mark-quality input for TRACE. Not a return signal |
| frameworkidea.pdf | Statistical predictions of trading strategies in electronic markets. Cartea, Cohen, Graumans, Labyad, Sanchez-Betancourt, van Veldhuijzen. c. 2024 | Euronext order-message prediction by member and algo | no | Equity microstructure. No transfer to monthly HY selection |
| fvdeck.pdf | Pricing pipeline component 1: fair value. Optiver Credit Trading Team, Jan 2025 | Market-making fair value, Hayashi-Yoshida lead-lag across venues | yes (infra) | Same pipeline as fair_value.pdf. Venue lead-lag for mark quality only |
| hybrid1.pdf | Comparing the geodesic execution cost framework and factor-based hedging optimization. No author, no date | Execution cost and hedge timing | no | Market-making execution. No selection signal |
| hybrid4.pdf | Refined geodesic framework for credit market making. No author, no date | Execution cost functional | no | Same topic as hybrid1. No selection signal |
| hybridmodel2.pdf | Complete geodesic framework for credit market making with execution uncertainty. No author, no date | Execution with fill probability | no | Same topic as hybrid1. No selection signal |
| lead_lag_ratio_matrix.pdf | One-page figure: lead-lag ratio matrix across BMRG, ECN, TruMid, TWEB, MXS | Venue lead-lag | no | Figure that belongs to fvdeck.pdf |
| mainPOE.pdf | Comprehensive mathematical framework for algorithmic pricing: factor flow, fill curves, and risk balancing. Quantitative Strategy Group, May 2025 | RFQ factor flow, fill curves | yes (low) | Factor-flow definition transfers to TRACE customer flow imbalance. No evidence |
| metrics.pdf | Comprehensive trading performance metrics specification. AK, v1.0 | Performance metric definitions | no | No signal |
| moreMathematicalMain.pdf | Advanced mathematical framework: integrated factor flow, fill curve, and risk balancer pricing. No author, no date | Extension of mainPOE (OU residual, decayed flow) | no | Adds no new signal beyond mainPOE |
| quant_snaps_121106 (1).pdf | Quant Snaps: building a better risk-switch. C. Natividade, Deutsche Bank, 6 Nov 2012 | Risk-state conditioned allocation across macro strategies | yes (low) | Regime state for S7 replacement. Weak evidence |
| quantcraft_130513 (1).pdf | Quantcraft: pairing singles. C. Natividade, Deutsche Bank, 13 May 2013 | Intraday pairs momentum and reversion in FX, commodities, equity indices | no | Intraday macro pairs. No plausible HY bond transfer at our data frequency |
| simulated_spreads.pdf | One-page figure: simulated spreads from five venues | Venue simulation | no | Figure that belongs to fvdeck.pdf |
| squared_correl.pdf | One-page figure: squared cross-correlation MXS vs TruMid | Venue lead-lag | no | Figure that belongs to fvdeck.pdf |
| ssrn-2846157.pdf | ETF activity and informational efficiency of underlying securities. Glosten, Nallareddy, Zou. 2019 | ETF ownership change and earnings information in stock prices | yes (low) | ETF activity weakens post-earnings drift. Conditions known PEAD signal |
| ssrn-3287912.pdf | Arbitrage comovement. J. J. Shim. 2020 | ETF arbitrage distorts constituent comovement. Long-short alpha | yes | Arbitrage sensitivity transfers to HY ETF constituents. New factor |
| ssrn-3335536.pdf | Autoencoder asset pricing models. Gu, Kelly, Xiu. 2019 (WP 19-24) | Conditional autoencoder factor model, US equities | no | Equity. The bond analogue (IPCA, ssrn-3720789) is the better source |
| ssrn-3720789.pdf | Modeling corporate bond returns. Kelly, Palhares, Pruitt. 2021 | IPCA conditional factor model on IG and HY bonds | yes | 29 characteristics with Sharpe ratios. OOS net Sharpe. HY included |
| ssrn-5946898.pdf | Multi-task Gaussian processes for tactical execution under regime shifts. Cartea, Drissi, Palmari. Dec 2025 | Execution bandit with change-point test | no | Child-order execution. No selection signal |
| ssrn-6811380.pdf | Intraday lead-lag relationships in idiosyncratic stock returns. Cartea, Cucuringu, Shi. July 2026 | Kendall lead-lag networks on intraday idiosyncratic equity returns | no | Intraday equity. TRACE HY prints are too sparse for intraday networks |
| ssrn-956825.pdf | DTS (duration times spread): a new measure of spread exposure in credit portfolios. Ben Dor, Dynkin, Hyman, Houweling, van Leeuwen, Penninga. Lehman, 2007 | Spread changes proportional to spread level | yes | Known DTS. New HY evidence on the volatility constant. Variant |

Duplicates: `credit_bmi_v2.pdf` and `credit_bmi_v2 (1).pdf` describe the same model. The figure files `lead_lag_ratio_matrix.pdf`, `simulated_spreads.pdf`, `squared_correl.pdf` belong to `fvdeck.pdf`. `moreMathematicalMain.pdf` extends `mainPOE.pdf`.

Unreadable files: none. `effect of rates on quant strategies.pdf` has no text layer. We read it with OCR (tesseract, 150 dpi).

## Factors found

### F1. Par-adjusted spread residual to a leave-one-out issuer survival curve (source: The_credit_spread_curve_I..., p.10, p.14-15, p.19; credit_spread_stat_arb_architecture_bridge_v0_1.pdf, p.3)
- Status: variant of S1 (fair value residual) and of the known coupon and price effect.
- Definition. Source says (Martin eq. 7, p.10): define the par-adjusted spread $s$ of a bond from its price $P$ by
  $$P/100 - 1 = \big(c - \hat r(T) - s\big)\,\Pi(T),\qquad \hat r(T)=\frac{\int_0^T f(t)B(t)Q(t)\,dt}{\int_0^T B(t)Q(t)\,dt}$$
  where $c$ is the coupon, $B$ the risk-free discount factor, $Q$ the survival curve, $\Pi(T)$ the risky PV01 (RPV01), and $f$ the risk-free forward rate. Intuition: $s$ is the running spread that prices the bond if it traded at par, so a 60-cent bond and a par bond are comparable.
  Fit a parametric hazard curve per issuer (or per rating and sector) by minimising $\sum_j w_j\big(\sqrt{1+\Delta P_j^2}-1\big)$ with $\Delta P_j/100=(s_j-\hat s(T_j))\Pi(T_j)$ and $w_j$ = amount outstanding (p.10-11).
  Bridge note (p.3): residual $e^{curve}_{i,t}=s^{PA}_{i,t}-\hat s_{-i,t}(T_{i,t})$, where the curve is fit without bond $i$ (leave one out). Positive means cheap. Price value of full convergence $RV^{price}_{i,t}\approx e^{curve}_{i,t}\,\Pi_{i,t}$.
  Source says (p.4, p.9): Z-spread is unsuitable because high-price bonds show higher Z-spread at the same maturity without better value. The recovery assumption sets the size of this effect.
- Data needed: bond clean price, coupon, maturity, Treasury curve, recovery assumption, issuer ID. We have TRACE prices and G-spreads, so we can compute $s$. Weights need amount outstanding, which we lack. Use equal weights or trade-volume weights.
- Evidence: none quantitative. Martin shows examples only (Colombia sovereign bonds 2016, mining and EM bank curves 2015-2018, Figures 4-8). Bridge note gives a worked example only (p.9-10).
- HY applicability: high. HY bonds trade far from par, often at 40-90. Z-spread and G-spread bias is largest there. Distressed issuers have several bonds at different prices.
- Fit to our signals: replaces the spread measure inside S1 and S4. The leave-one-out curve gives an issuer-level residual that S1 lacks.
- Test: in TRACE HY 2005-2024, compute the issuer-curve residual with par-adjusted spread and with G-spread. Sort each month into quintiles within issuers with 2+ bonds. Pass if the par-adjusted residual has a higher 3-month rank IC of excess return than the G-spread residual, by 0.02 or more, with Newey-West t > 2.

### F2. Net expected convergence return: carry + rolldown + q(h) times RV minus cost (source: The_credit_spread_curve_I..., p.14-15; bridge note, p.3-4, p.6)
- Status: variant of S1 and of the known maturity and roll-down factor. New element: an estimated fraction of convergence $q(h)$.
- Definition. Source says (Martin eq. 11-13): over $\Delta t$, with $c' = c-\hat r$,
  carry $= c'\Delta t + (s-c')\big(\Pi(T)-\Pi(T-\Delta t)\big)$, rolldown $= \big(\hat s(T)-\hat s(T-\Delta t)\big)\Pi(T-\Delta t)$, RV $= \big(s-\hat s(T)\big)\Pi(T-\Delta t)$.
  The forward RPV01 $\Pi(T-\Delta t)$ in the RV term avoids double count with carry.
  Bridge note (p.3): $E[PNL_i(h)] = Carry_i(h)+Rolldown_i(h)+q_i(h)RV^{price}_{i,t}-Cost_i(h)$.
  Bridge note (p.6): estimate $q$ by a direct-horizon regression $z_{t+h}-z_t=\alpha_h+\beta_h z_t+\varepsilon$, so $q(h)\approx-\beta_h$. For AR(1), $q(h)=1-\phi^h$ and half-life $=\log(1/2)/\log|\phi|$.
  Intuition: a cheap bond is worth only the part of its cheapness that closes inside the horizon, plus carry.
- Data needed: F1 inputs plus a cost model. TRACE gives bid-ask proxies (we have).
- Evidence: none quantitative in the source. Martin (p.16) adds a rating transition term from a transition matrix for expected return.
- HY applicability: high. HY carry is large, so the carry term dominates the ranking unless RV is scaled by $q$.
- Fit to our signals: S1 output layer. It converts the conformal residual into an expected return in price points.
- Test: estimate $\beta_h$ walk-forward by rating bucket. Pass if the realised 3-month fraction closed in held-out data lies inside the 90% interval of the predicted $q(h)$ in each rating bucket, and the ranking by net expected return beats the ranking by raw residual in rank IC after costs.

### F3. Deterioration gate on convergence trades (source: bridge note, p.7; The_credit_spread_curve_I..., p.19)
- Status: variant of S1 combined with known EMC (equity momentum) and ESI. New element: a multiplicative gate, not an additive score.
- Definition. Source says (bridge p.7): $q^{eff}_{i,t}(h)=q_{i,t}(h)\,G_{i,t}$ with $0\le G_{i,t}\le 1$. $G$ uses independent confirmation: issuer CDS and equity moves, synchronized widening across the issuer's bonds, rating and news, sector deterioration. Source says (Martin p.19): issuer RV "mean-reverts until it doesn't". A cheap bond that is first to price a real deterioration shows short-term momentum, and the rating moves later than the price.
  We propose: $G_{i,t}=\sigma\big(a + b_1\,\mathrm{EqRet}^{idio}_{i,t-3m:t} + b_2\,\mathrm{Sync}_{i,t} + b_3\,\Delta \mathrm{FairSpread}_{i,t}\big)$, where $\mathrm{Sync}$ is the share of the issuer's bonds that widened more than 1 DTS-scaled standard deviation in the last month. Fit $b$ by logistic regression of "residual closed by 50% within 3 months".
- Data needed: CRSP equity returns (we have), TRACE issuer bonds (we have), fair spread changes from S2 (we have). CDS we lack.
- Evidence: none quantitative in the source.
- HY applicability: high. HY cheapness often precedes default or downgrade, which is the main loss source of S1-type trades.
- Fit to our signals: gates S1 with S2 and equity momentum. Links to S6 because ratings lag prices.
- Test: split S1 cheap-quintile bonds by $G$ above and below median. Pass if the high-$G$ half has a higher 3-month excess return than the low-$G$ half in at least 3 of the 4 cycles (2008, 2015, 2020, 2022), and lower 12-month default rate.

### F4. IPCA conditional factor model for bond expected returns (source: ssrn-3720789.pdf, p.5, p.14-16, p.29-31, p.39)
- Status: new signal (aggregator). Uses known characteristics plus new ones (F5, F6, F7).
- Definition. Source says: $r_{i,t+1}=\beta_{i,t}' f_{t+1}+\varepsilon_{i,t+1}$, $\beta_{i,t}=z_{i,t}'\Gamma_\beta$, with $z_{i,t}$ = 29 characteristics plus a constant. Each month the characteristics are cross-sectionally ranked and mapped to $[-0.5,0.5]$ (p.15). Returns are excess over a Treasury hedge, scaled by $\max(DtS_{i,t},0.25)$ (eq. 10, p.14). $K=5$ factors, zero alpha. The expected return is $\hat E_t[r_{i,t+1}]=z_{i,t}'\Gamma_\beta\hat\lambda$ with $\hat\lambda$ the factor mean. Intuition: characteristics tell which bonds load on priced latent factors, and loadings update monthly.
  The five most important characteristics are spread, duration, bond volatility, and the constant, then spread-to-D2D, equity momentum, equity market cap, rating (Table IX, p.31; p.33).
- Data needed: OAS, spread duration, bond return history, equity returns, Compustat balance sheet, rating. We have TRACE G-spread (not OAS), CRSP, Compustat point-in-time. We lack ratings after Feb 2017 and OAS. G-spread biases callable HY bonds.
- Evidence: universe ICE BofA H0A0 (HY) and C0A0 (IG), Dec 1999 to Dec 2020, 14,600 bonds, 555,894 bond-months, spreads 50-2000 bp (p.14-15). OOS factor tangency portfolio gross Sharpe 6.23, net 2.48 at 19 bp one-way cost, turnover 68% per month (Table VIII, p.29). With smoothing $\gamma=0.3$: net Sharpe 2.93 tangency, 1.47 quintile spread portfolio (p.30). OOS total $R^2$ by segment: BB 48.6%, B-D 45.8%, HY liquidity terciles 46.0-48.5% (Table XIII, p.39). Mixed IG and HY. Model not re-estimated per segment.
- HY applicability: high. The sample includes HY and fits HY as well as IG.
- Fit to our signals: new signal S8 "conditional factor expected return". It can also serve as the benchmark that S1 must beat.
- Test: fit IPCA K=5 walk-forward on our TRACE HY panel with the characteristics we have. Pass if the OOS quintile spread portfolio has a net Sharpe above 0.5 at 19 bp one-way cost, and positive rank IC after costs in 3 of 4 cycles.

### F5. Spread-to-D2D (source: ssrn-3720789.pdf, p.16, p.55)
- Status: variant of Correia, Richardson, Tuna 2012 (default-probability-implied spread gap). New definition and new HY evidence.
- Definition. Source says (Table A.I, p.55): $\mathrm{S2D}_{i,t}=\dfrac{OAS_{i,t}}{1-\Phi(DD_{i,t})}$, with $DD$ the Shumway (2001) distance to default. Intuition: spread per unit of default probability. A high value means the bond pays a lot for little default risk.
  Note: the text says "one minus the CDF". $1-\Phi(DD)$ equals $\Phi(-DD)$, the Merton default probability.
- Data needed: spread (TRACE G-spread, we have), equity value and volatility (CRSP, we have), debt face (Compustat, we have).
- Evidence: characteristic-managed portfolio Sharpe 1.25, significant at 1% (Table I, p.16). Full-sample, IG and HY, 1999-2020. It is the second largest Sharpe after equity momentum (1.76). IPCA impact 0.23, significant at 5% (Table IX, p.31).
- HY applicability: high. HY spreads vary more with DD, so the ratio spreads more.
- Fit to our signals: an input to S1. It is a simple fair-value proxy that needs no fair spread model.
- Test: monthly quintile sort within rating buckets on TRACE HY. Pass if the top-minus-bottom 1-month DTS-scaled excess return has t > 2 and positive rank IC after costs in 3 of 4 cycles.

### F6. Bond return skewness (source: ssrn-3720789.pdf, p.16, p.55)
- Status: NEW.
- Definition. Source says: skewness of the bond's monthly return over the past 60 months (Table A.I, p.55; from Bai, Bali, Wen 2019).
  $$\mathrm{Skew}_{i,t}=\frac{\frac{1}{n}\sum_{k=0}^{n-1}(r_{i,t-k}-\bar r_i)^3}{\big(\frac{1}{n}\sum_{k}(r_{i,t-k}-\bar r_i)^2\big)^{3/2}},\quad n\le 60$$
  Intuition: bonds with left-skewed history (crash risk) pay a premium. Bonds with right skew (lottery) pay less.
- Data needed: monthly bond returns (TRACE, we have). Needs a long history per bond. Use 24-month minimum.
- Evidence: Sharpe -0.67, significant at 1% (Table I, p.16). Negative sign: buy low skew, sell high skew. Full sample, IG and HY, 1999-2020. Not significant in IPCA once other characteristics enter (impact 0.05, Table IX, p.31). Value-at-risk (second lowest return in 36 months) has Sharpe 0.07, not significant.
- HY applicability: medium. The HY return distribution is the most skewed. But the effect does not survive the multivariate model.
- Fit to our signals: an input to S1 or S8. A risk control for event risk.
- Test: quintile sort within rating on TRACE HY, 1-month DTS-scaled returns. Pass if low-minus-high skew has t > 2 and survives a control for bond volatility and spread.

### F7. Profitability change (5-year) (source: ssrn-3720789.pdf, p.16, p.55)
- Status: NEW (not in the known list). Quality trend, not level.
- Definition. Source says: 5-year change in profitability, with profitability $=(\mathrm{Sales}-\mathrm{COGS})/\mathrm{Assets}$ for non-financials (Table A.I, p.55).
  $$\Delta\mathrm{Prof}_{i,t}=\mathrm{Prof}_{i,t}-\mathrm{Prof}_{i,t-5y}$$
  Intuition: an issuer whose gross margin on assets improves becomes safer than its spread says.
- Data needed: Compustat point-in-time sales, COGS, assets (we have).
- Evidence: Sharpe 0.60, significant at 1% (Table I, p.16). Profitability level has Sharpe 0.14, not significant. IPCA impact 0.03, not significant (Table IX, p.31). Full sample, IG and HY, 1999-2020.
- HY applicability: medium. HY issuers often have short histories. A 5-year window loses many names. Try a 3-year window.
- Fit to our signals: S2 (fundamental momentum) and S3 (estimate revisions). It is a slow fundamental trend.
- Test: quintile sort within rating on HY with 5-year Compustat history. Pass if the long-short 3-month excess return has t > 2 and adds to S2 in a joint regression (t > 2 on the new term).

### F8. Bond-own momentum and spread momentum reverse (source: ssrn-3720789.pdf, p.16, p.55)
- Status: variant of momentum (Houweling and van Zundert, Israel et al.). New evidence with a sign opposite to the usual bond momentum claim.
- Definition. Source says (p.55): Mom. 6m = 6-2 momentum of bond returns. Mom. 6m log(Spread) $=\log s_{i,t-6}-\log s_{i,t}$.
- Evidence: Mom. 6m Sharpe -0.84, Mom. 6m log(Spread) Sharpe -0.80, both significant at 1%. Mom. 6m equity Sharpe +1.76 (Table I, p.16). DTS-scaled returns, IG and HY, 1999-2020. So bonds that rallied underperform, while issuers whose equity rallied outperform.
- HY applicability: high. It warns that bond momentum may hurt in HY over this period. Equity momentum (known EMC) carries the signal.
- Fit to our signals: S2 and EMC. Use bond spread change as a reversal term next to equity momentum.
- Test: on TRACE HY, regress 1-month DTS-scaled excess return on bond 6-2 momentum and equity 6-2 momentum jointly. Pass if bond momentum is negative with t < -2 and equity momentum positive with t > 2.

### F9. DTS-scaled return target with a floor (source: ssrn-3720789.pdf, p.14; ssrn-956825.pdf, p.14-15)
- Status: variant of DTS (known through DTS-neutral legs). New: a floor, and HY evidence on the volatility constant.
- Definition. Source says (KPP eq. 10): $r_{i,t+1}=\tilde r_{i,t+1}/\max(DtS_{i,t},\underline{DtS})$ with $DtS = $ duration × spread and $\underline{DtS}=0.25$ (spread in decimal times years). 40% of bonds sit below the floor. Ben Dor et al.: systematic spread volatility $\sigma(\Delta s)\approx\theta s$ with $\theta=9.1\%$ per month using IG plus Ba and B bonds, 9.4% without three outliers (p.15). The linear relation holds to 400 bp (p.14).
  Intuition: excess return volatility is proportional to DTS, so divide by DTS to compare a BB and a CCC bond.
- Data needed: spread and duration (TRACE, we have).
- Evidence: Ben Dor et al. sample 565,602 observations, Sep 1989 to Jan 2005, IG plus Ba and B. Volatility flattens in the highest-spread cells (p.14). KPP: scaling gives a more homogeneous cross-section (p.14, footnote 15).
- HY applicability: high, with a caveat. The source shows less than linear volatility above 400 bp. CCC and distressed bonds may need a cap as well as a floor.
- Fit to our signals: the target transform for every signal test. Methodology section on fair spread residual scaling.
- Test: on TRACE HY 2005-2024, regress monthly absolute spread change on spread level in spread buckets. Pass if the slope is constant within ±20% up to 800 bp. Otherwise add a cap at the break point.

### F10. Tail dependence of issuer spread changes with the market (source: The determinants of CDS spreads..., p.5, p.8, p.13, p.38-39)
- Status: NEW. Related to the known low-risk and betting-against-beta factors, but nonlinear.
- Definition. Source says: upper tail dependence (UTD) and lower tail dependence (LTD) of daily single-name CDS spread log changes with the CDS market return, from dynamic copulas (t, Gumbel, rotated Clayton, SJC) (Table 3, p.13). For the t-copula with correlation $\rho$ and degrees of freedom $\nu$:
  $$\lambda_U=\lambda_L=2\,t_{\nu+1}\!\left(-\sqrt{\frac{(\nu+1)(1-\rho)}{1+\rho}}\right)$$
  (standard formula, our addition). Intuition: names that widen with the market in its worst days carry crash risk and earn a premium.
- Data needed: daily issuer spread changes and a market spread index. Source uses Markit 5y CDS (we lack). We propose daily TRACE issuer G-spread changes against a TRACE-built HY index. HY issuers trade sparsely, so use weekly changes and a 2-year window.
- Evidence: 277 public firms in CDX NA IG and CDX NA HY series 1-24, Jan 2001 to Sep 2014 (p.5-6). Quarterly firm fixed-effect panel of CDS log changes on lagged UTD: t-copula coefficient 0.848, s.e. 0.152 (Table 1, p.8). OOS RMSE: AR(2) 51.7%, t-copula alone 39.0%, Gumbel U+L plus t-copula 35.5%, full BMA 34.6% (Table 13, p.38). Merton-type and macro variables add almost nothing (p.39). The dependent variable is spread change, not a return. No portfolio test.
- HY applicability: medium. The sample includes HY CDS. Transfer to sparse TRACE HY data is untested.
- Fit to our signals: an input to S1 (fair spread must pay for tail risk) and to the event model (tail beta for stress scenarios).
- Test: estimate UTD per HY issuer on 2 years of weekly TRACE spread changes. Pass if adding lagged UTD to the S1 fair spread regression lowers the OOS RMSE of next-quarter issuer spread change by 3% or more (Diebold-Mariano p < 0.05).

### F11. Credit-BMI v2 market timing composite with conformal decision rule (source: credit_bmi_v2.pdf, p.1-4; credit_bmi_v2 (1).pdf, p.1-3)
- Status: new signal. Candidate replacement for S7. Some inputs are known (EBP, sentiment, VRP).
- Definition. Source says:
  1. Segment $i$ (IG, HY, rating bucket). Target: $h$-day excess return over duration-matched Treasury, $h\in\{1W,1M,3M\}$.
  2. Factors: VIX 1-month change (sign −), vol-adjusted excess-return moving average (+), risk appetite (+, flips when $|z_{6M}|$ is extreme), dealer balance-sheet capacity and CDX-cash basis (−), issuer equity vol, leverage, rating drift (−), PC1 of cross-sectional spread changes (−) (Table 1, p.1).
  3. Score: $z^{(k)}_{t}=(x^{(k)}_{t-\ell_k}-\hat\mu_t)/\hat\sigma_t$ on an expanding window, $s=20[\Phi(z)-\tfrac12]\in[-10,10]$. Drift factors are vol-scaled instead.
  4. Weights: $w_h\propto(\lambda I+(1-\lambda)\Sigma_h)^{-1}\rho_h$, Ledoit-Wolf shrinkage. $\lambda\to1$ gives the equal-weight original.
  5. Regime gate: $\tilde s^{(k)}=(1-\beta_k g_t)\,10\tanh(\kappa s^{(k)}/10)$, $g_t=1$ when realised spread volatility exceeds its expanding 80th percentile. $\beta_{mom}=0.6$.
  6. Decision: fit CQR quantile regressions, calibrate with $Q$ = the $\lceil(n+1)(1-\alpha)\rceil/n$ quantile of $E_j=\max(\hat q_{\alpha/2}-y_j,\,y_j-\hat q_{1-\alpha/2})$. Update $\alpha_{t+1}=\alpha_t+\gamma(\alpha-\mathrm{err}_t)$ (adaptive conformal inference). Long if lower bound > cost, short if upper bound < −cost, else flat. Size = |point| / width.
  7. Drawdown stop at $-D^*$ on trailing P&L.
- Data needed: VIX (public), TRACE HY index returns (we have), PC1 of TRACE spread changes (we have), equity data (we have). We lack CDX-cash basis and Barclays OAS. Dealer capacity needs the NY Fed primary dealer statistics (public).
- Evidence: the note cites original Morgan Stanley credit-BMI hit rates 67% IG and 62% HY, and 55% and 51% for the LIBOR-OIS factor (p.2-3). These are second-hand. The demo coverage of 89.9% against 90% uses synthetic data only (credit_bmi_v2 (1).pdf, p.2). No real-data backtest.
- HY applicability: medium to high. Designed with separate IG and HY calibration.
- Fit to our signals: replaces S7 at the index and rating-bucket level. The conformal rule matches our conformal bands in S1.
- Test: walk-forward on monthly HY index excess returns 2000-2024. Pass if the 90% ACI interval covers 88-92% of outcomes, and the flat-or-trade rule has positive excess return after 19 bp costs in 3 of 4 cycles.

### F12. Arbitrage sensitivity to HY bond ETFs (source: ssrn-3287912.pdf, p.2-3, p.12-14, p.42)
- Status: NEW.
- Definition. Source says (eq. 5, p.12): $\Lambda_{i,e}=\dfrac{\lambda_i(w_i)}{\sum_{j\in e}w_j\lambda_j(w_j)}$, with $\lambda_i(w)=c_i w^{\gamma}$, $w_i$ the ETF weight and $c_i$ the price impact parameter. Weighted average $\Lambda$ equals 1. Intuition: ETF arbitrageurs trade every constituent by weight. Bonds that are illiquid for their weight overreact to ETF moves, and liquid-for-weight bonds underreact. Both correct over months.
  We propose: for HYG and JNK holdings, estimate $c_i$ from TRACE price impact (Amihud-style ratio on trades), set $\gamma=0.5$, and compute $\Lambda_{i}$ monthly. Long low-$\Lambda$, short high-$\Lambda$ bonds, matched on DTS.
- Data needed: ETF holdings by date (iShares and SPDR daily files; we do not have them), TRACE trades for price impact (we have).
- Evidence: US equity ETFs only. Value-weighted decile H-L monthly alpha −0.649% (t = −2.66) for high-volume ETFs, 2008-2017, after market, size, value, momentum and BAB factors. Large-cap ETFs −0.619% (t = −2.35). Control period 1994-2007: −0.150% (t = −0.54) (p.42). About 7.5% a year (p.3).
- HY applicability: medium. HYG and JNK are among the most traded credit ETFs. Their creation and redemption baskets are partial samples, which weakens the weight mechanism.
- Fit to our signals: new signal. Close to S6 (forced flows).
- Test: regress monthly HY bond returns on HYG return interacted with $\Lambda_i$. Pass if the interaction coefficient is positive (t > 2) in 2010-2024, and the low-minus-high $\Lambda$ portfolio has a positive 3-month DTS-scaled return with t > 2.

### F13. ETF contraflow for HY bonds (source: Why Do ETF Flows Move Prices.pdf, p.1-2, p.7)
- Status: NEW for bonds. Related to S6 forced flows and known inclusion delay.
- Definition. Source says: ETF flow = change in total dollar amount held by ETFs, scaled by firm market cap, over 6 months (p.1-2). Sort Russell 3000 within sector into deciles. Long bottom decile (largest outflow), short top. Flows split into allocation, weight reconstitution, and index reconstitution (p.1, p.7).
  We propose: $\mathrm{Flow}_{i,t}=\big(\sum_e H_{i,e,t}-\sum_e H_{i,e,t-6m}\big)/\mathrm{AmtOut}_{i,t}$, summed over HY ETFs. Split into fund-flow (allocation) and index rule (bond enters or leaves the ETF index) parts.
- Data needed: ETF holdings (lack), amount outstanding (lack), ETF index rules (public methodology documents).
- Evidence: equities only. Long-short Sharpe 1.29, Jan 2006 to Dec 2018. Index reconstitution alone Sharpe 0.82, weight reconstitution 0.51, allocation 0.30 (p.7). Decile 1 return 11.9% a year, decile 10 3.7% (Figure 1, p.2).
- HY applicability: medium. HY ETF index rules (size and age cuts) create predictable entry and exit. Data gaps block a test today.
- Fit to our signals: S6 (forced flows), and the known inclusion-delay effect.
- Test: when data exist, sort HY bonds on 6-month ETF flow within rating. Pass if bottom-minus-top decile 3-month DTS-scaled return has t > 2 after costs.

### F14. Separate liquidity into mark reliability, slow premium, and cost (source: bridge note, p.6-7; fair_value.pdf, p.2-4; fvdeck.pdf)
- Status: variant of known size and liquidity controls. Method for S1.
- Definition. Source says (bridge p.6): observation variance $R_{i,t}=g(\text{quote age},\text{bid-offer},\text{dealer count},\text{quote dispersion},\text{trade recency},\text{volume})$. A persistent liquidity premium belongs in slow fair value. Bid-offer, impact and borrow belong in the cost hurdle. Bridge (p.8): impact $=\eta_i\sigma_i(|q|/ADV^{eff}_i)^{\delta_i}$. fair_value.pdf: per-source variance $\sigma^2_{i,t}=w_{micro}(\phi_{i,t}/2)^2+w_{macro}\sigma^2_{macro}$ (e.g. 0.7 and 0.3), mid = median of the Gaussian mixture of sources.
  We propose: use $1/R_{i,t}$ from TRACE (days since last trade, trade count, intra-day price dispersion) as the weight of each bond in the curve fit of F1 and in the S1 conformal calibration.
- Data needed: TRACE trade times, sizes, prices (we have).
- Evidence: none quantitative.
- HY applicability: high. Many HY bonds trade a few times a month. Stale marks create false residuals.
- Fit to our signals: S1 data layer.
- Test: pass if weighting by $1/R$ reduces the share of S1 cheap signals that reverse fully within 5 days (a sign of a stale mark) by 20% or more.

### F15. TRACE customer flow imbalance in risk units (source: mainPOE.pdf, p.5)
- Status: NEW as a selection signal. Our proposal. The source gives a market-making definition only.
- Definition. Source says: factor flow $V^{c,s,k}_{t_1,t_2}=\sum_{t\in[t_1,t_2]}\beta_{b_t,k}\,s_t\,Q_t$, in risk units $V^k_t=\beta_{b_t,k}Q_t\,CR01_{b_t}$ (eq. 3-4, p.5).
  We propose: $\mathrm{FI}_{i,t}=\sum_{\text{trades in month}} \mathrm{side}\cdot Q\cdot DTS / \sum |Q|\cdot DTS$, with side +1 for customer buy, −1 for customer sell (Enhanced TRACE reports the side). Aggregate at issuer and at sector.
- Data needed: Enhanced TRACE with buy-sell side (we have TRACE. Side field availability to check).
- Evidence: none in the source.
- HY applicability: medium. Persistent customer selling may mark forced selling (fund outflows), which predicts reversal.
- Fit to our signals: S6 (forced flows).
- Test: sort HY bonds monthly on $\mathrm{FI}$. Pass if most-sold minus most-bought has a positive next 1-3 month DTS-scaled return with t > 2.

### F16. Risk-state regime for strategy weights (source: quant_snaps_121106 (1).pdf, p.1-3)
- Status: variant for S7 replacement (regime conditioning).
- Definition. Source says: a sentiment index from 11 barometers (5 volatility surface, 3 credit spread, 2 rate spread, 1 price performance). Its density is a 3-component Gaussian mixture (risk on, intermediate, risk off). A Markov chain models state transitions. Strategy weights use minimum variance conditioned on state, not on calendar time (p.1-3).
- Data needed: VIX, rate spreads, TRACE HY index (we have or public).
- Evidence: weak. Year-to-date 2012 only: state-based minimum variance Sharpe 1.9, equal weight Sharpe 1.9, time-based minimum variance 0.8 (p.2-3). Macro price strategies, not credit selection.
- HY applicability: low to medium. Useful as the regime gate $g_t$ of F11.
- Fit to our signals: S7 replacement and the F11 gate.
- Test: pass if S1-S6 rank ICs differ by state with a chi-square p < 0.05, and state-weighted signal mixing beats equal weight OOS in 3 of 4 cycles.

### F17. Issuer rate-curve betas by ridge regression (source: effect of rates on quant strategies.pdf, p.3-7)
- Status: variant of S7 (macro-conditional sector tilt). Risk control, not alpha.
- Definition. Source says (OCR): PCA of Treasury yield changes on a rolling 3-year window gives shift, twist, butterfly. Shift explains about 94% of variance in 2018 (p.3-4). $R_{i,t}=\beta_0+\beta^{shift}\mathrm{shift}_t+\beta^{twist}\mathrm{twist}_t+\beta^{bfly}\mathrm{bfly}_t+\varepsilon$, estimated by ridge regression (p.5-6). Rate factors explain up to 30% of sector-free return dispersion in recent years (p.7).
- Data needed: Treasury curve (public), equity returns (we have), bond excess returns (we have).
- Evidence: Russell 1000 stocks, 1994-2018. No credit evidence.
- HY applicability: low. HY excess returns carry an equity-like rate response. It helps neutralise sector bets, not pick bonds.
- Fit to our signals: S7 replacement as a hedge filter.
- Test: pass if neutralising S1 portfolios to issuer equity shift-beta lowers their volatility by 10% or more without lowering mean return.

### F18. ETF activity weakens post-earnings drift (source: ssrn-2846157.pdf, p.2, p.4, p.20)
- Status: variant of post-earnings drift (EAR, CFE).
- Definition. Source says: ETF activity = quarterly change in ETF ownership share (p.4). Higher ETF activity raises short-run price efficiency for firms with weak information environments and attenuates post-earnings drift (abstract, p.2). Mean ETF ownership 3.6% (p.20). Sample starts 2004.
- Data needed: equity ETF ownership (13F or ETF holdings, we lack), earnings surprises (Compustat or I/B/E/S).
- Evidence: equities. We did not extract coefficient values. Treat as direction only.
- HY applicability: low to medium. HY issuers with listed equity and low analyst coverage may show stronger bond drift.
- Fit to our signals: conditions the known PEAD signal and S3.
- Test: pass if bond drift after earnings is larger (t > 2 on the interaction) for issuers in the bottom tercile of equity ETF ownership.

## Top 3

1. F4 IPCA conditional factor model (with F5 spread-to-D2D as its key value input): the only source here with OOS, cost-adjusted bond evidence that includes HY (net Sharpe 2.48 at 19 bp, HY $R^2$ about 46-48%), and we hold most of the inputs.
2. F1 + F2 + F3 par-adjusted leave-one-out issuer-curve residual with estimated closure $q(h)$ and a deterioration gate: it fixes the price bias that hurts S1 most in HY, where bonds trade far from par, and it uses only TRACE, CRSP, and Compustat.
3. F11 Credit-BMI v2 timing composite with the adaptive conformal trade rule: it fits our conformal design and gives a testable S7 replacement. Its evidence is second-hand or synthetic, so it ranks third.
