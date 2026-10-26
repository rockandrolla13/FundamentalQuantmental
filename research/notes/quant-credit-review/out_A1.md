# A1: root papers. New credit factors and signals

Scope: 29 files from `A1_root_papers.txt`, in "/home/ak/Documents/Quant Credit/". Page numbers are PDF pages of each file.
Convention in each block: "Source says" is the document. "We propose" is our design. No number below comes from anywhere except the cited page.

Duplicates found:
- `Design and analysis of momentum trading strategies.pdf` (arXiv v2, 2023) and `Design_and_analysis_of_momentum_trading_strategies.pdf` (arXiv v1, 2021) hold the same paper. I read v2.
- `Factor Architecture.pdf` and `Factor Architecture (1).pdf` hold two drafts of the same one-page software diagram.
- `FillCurveV2.pdf` and `MainCLVersionMay28th.pdf` hold two drafts of the same dealer pricing framework. I read both in part.

## Triage table

| File | Title, authors, year | Topic | Relevant (yes/no) | Why |
|---|---|---|---|---|
| 10-1108_jes-03-2016-0053.pdf | The lead-lag relationship between US industry-level credit and stock markets. Shahzad, Nor, Sanusi, Kumar. J. Economic Studies 2017 | Wavelet coherence and Granger tests, 11 US industry CDS and equity indices, 2007-2014 | yes (weak) | Equity leads CDS at industry level. Variant of EMC. No return test. |
| 2406.12983v1.pdf | Reinforcement Learning for Corporate Bond Trading: A Sell Side Perspective. Atkins, Fathi, Assefa (U.S. Bank). 2024 | RL for dealer bid-ask quoting on RFQs | no | Dealer quoting. No selection or timing signal. |
| 2506.18147v1.pdf | Causal Interventions in Bond Multi-Dealer-to-Client Platforms. Marin, Ardanza-Trevijano, Sabio (BBVA). 2025 | Causal graph model of RFQ win probability | no | Dealer pricing. Needs RFQ data we lack. |
| 2509.05065v1.pdf | The Subtle Interplay between Square-root Impact, Order Imbalance and Volatility II. Maitrier, Loeper, Bouchaud. 2025 | Synthetic order flow, square-root impact law | no | Equity microstructure. Only a cost model idea transfers. |
| 2606.26350v1.pdf | OpenFinGym: A Verifiable Multi-Task Gym Environment for Evaluating Quant Agents. Zhang et al. 2026 | LLM agent benchmark | no | No credit content. |
| 61444f23-caee-47ed-9bb0-ecd48e95c54b.pdf | Business Plan Details for Xantium: Systematic Spread Fixed Income Trading. A. Koukorinis. 2024 | Fund plan: ETF-basket arbitrage, ETF flows, liquidity rules, Kelly sizing | yes (weak) | Proposes ETF flow signal and liquidity score. No evidence. |
| A simple approach to the estimation of Tukey s gh distribution.pdf | A simple approach to the estimation of Tukey's gh distribution. Bee, Trapin. J. Stat. Comput. Simul. 2016 | ABC estimation of skewed heavy-tail distribution | no | Statistics tool. Could model spread-change tails. No signal. |
| An Introduction to Gaussian Processes for the Kalman Filter.pdf | An Introduction to Gaussian Processes for the Kalman Filter. Reece, Roberts (Oxford). c. 2010 | KF and GP hybrid for spatio-temporal fields | no | Filtering method only. |
| CARRY AND ROLL-DOWN STRATEGIES: A THEORETICAL APPROACH.pdf | Estrategias de carry y roll-down: un enfoque teorico. Bajo, Rodriguez (Banco de Espana). c. 2010 | Carry, roll-down, rolling yield, breakeven rate, credit spread version | yes | Gives spread breakeven cushion. Variant of carry and roll-down. |
| Design and analysis of momentum trading strategies.pdf | Design and analysis of momentum trading strategies. R. J. Martin. arXiv v2 2023 | EMA momentum filters, skewness term structure | yes (weak) | Filter design for momentum. Futures evidence only. |
| Design_and_analysis_of_momentum_trading_strategies.pdf | Same paper, arXiv v1 2021 | Duplicate | duplicate | See above. |
| Detecting toxic flow.pdf | Detecting toxic flow. Cartea, Duran-Martin, Sanchez-Betancourt. Quant. Finance 2026 | Online Bayesian NN (PULSE) for broker toxic FX trades | no | FX broker flow. No bond selection use. |
| Factor Architecture (1).pdf | Factor Architecture diagram (internal, undated) | Software flow: return decomposition, factor engine, attribution | no | Architecture only. |
| Factor Architecture.pdf | Same diagram, other draft | Duplicate | duplicate | See above. |
| Factor_Model_Related (1).pdf | Credit Factor Framework v0.85. "AK" (internal draft). Undated | PCA, panel regressions, factor list, N-LASR AdaBoost combiner, RAMIC metric | yes | Defines credit-curve term premium, curvature, fundamental composite, DTS-scaled IC. No results. |
| FillCurveV2.pdf | Unified Framework: Factor Flow and Fill Curves. Credit Trading Group. 2025 (draft) | Three-layer factor model, RFQ factor flow, fill curves, skew | yes (weak) | Defines signed factor flow. Needs RFQ data. A TRACE proxy is possible. |
| Financial Market - 2023 - Berndt - Across-the-Curve Credit Spread Indices.pdf | Across-the-Curve Credit Spread Indices. Berndt, Duffie, Zhu. Financial Markets, Inst. and Instruments 2023 | AXI bank funding index and FXI all-issuer index from TRACE and FISD | yes | Builds a market spread index from TRACE. It can replace the Barclays OAS we lack. |
| Fixed income portfolio optimisation: Interest rates, credit, and the efficient frontier.pdf | Fixed income portfolio optimisation. R. J. Martin. 2020 | Expected return with rating migration, CSx2 and CSL stress constraints | yes | Migration-adjusted expected return and countercyclical risk limits. |
| HY_VIX (2).pdf | HY vs VIX. Trading screen, "Global Macro Fund", pricing date 2011-10-06 | Rolling z-scores of CDX HY and VIX over 1-24 months | yes (weak) | Macro relative value idea. No evidence. Needs CDX. |
| Journal of Futures Markets - 2023 - Begin - Leveraging prices ... portfolio risk.pdf | Leveraging prices from credit and equity option markets for portfolio risk management. Begin, Boudreault, Theriault. J. Futures Markets 2023 | Joint default intensity and recovery from deep OTM puts and CDS, 399 US firms 2003-2019 | yes (weak) | Market-implied recovery. Needs options and CDS that we lack. |
| MACHINE LEARNING FOR YIELD CURVE FEATURE.pdf | Machine learning for yield curve feature extraction: application to illiquid corporate bonds. Kirczenow, Hashemi, Fathi, Davison. arXiv 2018 | Denoising autoencoder fills rating x tenor yield grid | no (tool) | Curve-fill tool for sparse HY grids. 63 dates only. No signal. |
| MainCLVersionMay28th.pdf | Comprehensive Framework for Dynamic Risk-Adaptive Pricing. Quantitative Research Team. 2025 (draft) | Same framework as FillCurveV2 | duplicate in part | Factor flow eq. (4) on p2 adds CR01 weight. |
| Mean Reversion Pays, but Costs.pdf | Mean Reversion Pays, but Costs. R. J. Martin, T. Schoneborn. arXiv 2011 | Optimal no-trade buffer for a mean-reverting asset under linear costs | yes | Gives a trade rule for S1 under HY bid-ask costs. |
| Measuring Credit-Spread Risk.pdf | Measuring Credit-Spread Risk on a Single Issuer Basis. R. Pullirsch (Bank Austria). c. 2007 | Issuer zero spread curves, bond residual variances, VaR | no | Risk model. No signal. |
| Measuring changes in credit risk_ The case of CDS event studies.pdf | Measuring changes in credit risk: The case of CDS event studies. Andres, Betzer, Doumet. Global Finance J. 2021 | Size and power of CDS event-study tests, factor normal model, downgrade study | yes | Event method for our events module. Downgrade evidence with partial reversal. |
| Mid-price estimation for European corporate bonds.pdf | Mid-price estimation for European corporate bonds: a particle filtering approach. Gueant, Pu. arXiv 2019 | Bayesian particle filter for bond mid from trades, RFQs, composites | no (tool) | Mid estimation tool. Could clean TRACE marks. No signal. |
| The Trading Dynamics of Corporate Bonds and Bond ETFs.pdf | The Trading Dynamics of Corporate Bonds and Bond ETFs. Cindy Pan. PhD diss., U. Mississippi 2024 | Hidden liquidity in bond ETFs, TRACE trading around corporate events, convertibles in the money | yes (weak) | Abnormal TRACE volume around events. Volume only, no returns. |
| The behavior of dealers and clients on the European.pdf | The behavior of dealers and clients on the European corporate bond market: the case of MD2C platforms. Fermanian, Gueant, Pu. arXiv 2017 | RFQ competition model on Bloomberg MD2C | no | Dealer behaviour. Needs RFQ data. |
| The credit spread curve.pdf | The credit spread curve I: fundamental concepts, fitting, par-adjusted spread, and expected return. R. J. Martin. arXiv v3 2024 | Survival-curve fitting, par-adjusted spread, carry, roll-down, relative value | yes | Corrects the high-price-bond spread bias. Defines RV to rating curve. |

Count: 29 files triaged. 14 marked relevant (yes or yes weak), counting the two momentum files once and the two dealer-framework drafts once. 4 are duplicates.

## Factors found

### F1. Par-adjusted spread relative value to a rating curve (source: The credit spread curve.pdf, p11-12, p19-20, p24)
- Status: variant of the coupon and price effect (Ben Dor) and of S1 fair value residual.
- Source says: Z-spread and yield make high dollar price bonds look cheap at the same maturity, because they ignore recovery (p7-9). Fit a survival curve $Q(T)$ per issuer or per rating, with fractional recovery of par. Define the par-adjusted spread $s$ by eq. (9), p12:
  $$\frac{P}{100}-1=\big(c-r_b(T)-s\big)\,\Pi(T),\qquad \Pi(T)=\int_0^T B(t)Q(t)\,dt,\qquad r_b(T)=\frac{\int_0^T f(t)B(t)Q(t)\,dt}{\int_0^T B(t)Q(t)\,dt}$$
  Intuition: $s$ is the running spread that a par bond with the same risk would pay, so bonds at 60 and at 110 become comparable.
  Recovery falls with rating: $\Re=(70-3r)\%$, with $r$ the linear rating. BBB- gives 40%, BB 34%, B 25% (p19).
  Relative value to the model curve $\hat s(T)$, measured with forward duration so carry is not double counted, eq. (20), p20: $RV=(s-\hat s(T))\,\Pi(T-\Delta t)$.
  Carry eq. (18): $c'\Delta t+(s-c')(\Pi(T)-\Pi(T-\Delta t))$. Roll-down eq. (19): $(\hat s(T)-\hat s(T-\Delta t))\,\Pi(T-\Delta t)$.
- Data needed: TRACE clean price, coupon, maturity, call schedule (FISD), Treasury curve, rating. We have TRACE prices and G-spreads. We lack ratings after Feb 2017, so we need an implied rating (for example from our fair spread model) after that date.
- Evidence: worked examples only. Two Colombia 2024 bonds (p8-10, p15). BSANCI 2022 RV to the A+ bank curve settles near zero over a few years (Fig. 9, p24). No backtest. Sovereign and IG examples. No HY test.
- HY applicability: high. HY bonds trade far from par, with wide price dispersion, so the bias that this fixes is largest in HY.
- Fit to our signals: S1 (replace G-spread with par-adjusted spread as the target), S4 (tranche gap on a recovery-consistent basis). Methodology recovery and fairspread layers.
- Test: build S1 twice, on G-spread and on par-adjusted spread. Compute monthly rank IC of the residual against next-month excess return, 2005-2024 HY. Pass: par-adjusted IC exceeds G-spread IC by at least 0.01. Also pass: correlation of the residual with dollar price falls by half.

### F2. Migration-adjusted expected return hurdle (source: Fixed income portfolio optimisation.pdf, p6-7)
- Status: variant of "spread-conditioned rating transition matrices" (Ben Dor) and of carry.
- Source says: spread is not expected return. Eq. (5), p7:
  $$TR=\underbrace{ct+B_0(t)P_i(T-t,c)-P_i(T,c)}_{\text{carry + roll}}+\underbrace{B_0(t)\sum_{j=1}^{D}p_{i\to j}(t)\big[P_j(T-t,c)-P_i(T-t,c)\big]}_{\text{migration and default, negative}}+\underbrace{P_i(T,c)-P_0}_{\text{cheapness to rating curve}}$$
  Intuition: a bond must earn back its expected loss from downgrades and default before it adds return.
  HY example, p7: a B credit with 4-5% one-year PD, 30% recovery, needs about 300 bp spread. With transitions to B-, CCC+, CCC included, it needs a yield above about 5.75% (2% risk-free) to give positive expected return. Without the migration term an optimiser barbells into high yield (p7).
- Data needed: rating-curve prices per rating (from TRACE), a transition matrix (Moody's or S&P history), bond cash flows. We have TRACE. We lack ratings after Feb 2017, so we need implied ratings.
- Evidence: one numerical example. No backtest.
- HY applicability: high. The migration hurdle is small in IG and large in B and CCC.
- Fit to our signals: S1 and S6 (gives S6 a return number, not only a rating gap). Methodology section on forward and recovery layers.
- Test: rank HY bonds by $TR$ net of migration and by raw carry. Horizon 3 months. Metric: rank IC after costs per cycle (2008, 2015, 2020, 2022). Pass: migration-adjusted IC exceeds carry IC in at least 3 of 4 cycles.

### F3. No-trade buffer for a mean-reverting residual, cube-root law (source: Mean Reversion Pays, but Costs.pdf, p9-10)
- Status: NEW (execution overlay, not a factor).
- Source says: with linear cost $\varepsilon$ per unit, the optimal policy has a no-trade zone around the cost-free position. Horizontal half-width, eq. (17), p9: $\tfrac12(\hat h_+-\hat h_-)\sim\big(3\varepsilon G/(2|\hat g_0'(x)|)\big)^{1/3}$. For an OU process $dX=(a-bX)dt+\sigma dW$, eq. (21), p10:
  $$\text{half-width in } X=\Big(\frac{3\sigma^2\varepsilon}{2b}\Big)^{1/3}$$
  Intuition: trade only when the mispricing moves past a band that grows with the cube root of cost, because small rebalances lose more in bid-ask than they earn.
  Value lost to costs scales as $\varepsilon^{2/3}$ when the band is optimal, not as $\varepsilon$ (p10).
- Data needed: S1 residual series per bond (we have), its OU speed $b$ and volatility $\sigma$ (estimate from TRACE G-spread residuals), round-trip cost by bond (estimate from TRACE dealer-customer spreads).
- Evidence: theory plus numerical checks on OU (Fig. 2, p11). No market data.
- HY applicability: high. HY round-trip costs are large, so a cost band changes turnover a lot.
- Fit to our signals: S1 and S2 trade rules. Methodology outputs layer (position changes).
- Test: run S1 with the cube-root band and with a fixed z-score entry. Monthly, 2005-2024 HY, with TRACE-based costs. Pass: net information ratio rises by at least 0.1 and turnover falls by at least 25%.

### F4. Abnormal relative spread change with a credit factor normal model (source: Measuring changes in credit risk_ The case of CDS event studies.pdf, p6, p8, p11, p19)
- Status: variant of rating stop-loss cost (Ben Dor) and of S6. New method for the events module.
- Source says: use relative spread changes, not absolute (p6). Normal model, eq. (9), p8:
  $$\Delta AS_{i,\tau}=\Delta S_{i,\tau}-\hat\alpha_i-\hat\beta_{1,i}\Delta S_{index,\tau}-\hat\beta_{2,i}\Delta Level_\tau-\hat\beta_{3,i}\Delta Slope_\tau-\hat\beta_{4,i}\Delta Vola_\tau$$
  with $\Delta S$ the relative change, Level the 5y swap rate, Slope 10y minus 1y swap, Vola the VIX. They drop equity returns because of -70% correlation with VIX (p8). Only the non-parametric rank test is well specified (p11). The factor model has the most power (Table 11, p18: about 66% vs 47% for mean-adjusted, time-series t-test, +0.5% shock).
  Downgrades, 384 S&P downgrades by 287 firms, Feb 2003 to Jul 2011, relative changes (Panel A, p19): day 0 abnormal +2.64% (rank t 5.82). Window [-1,+1] +3.01%. Window [+2,+20] -1.16% (rank t -1.99). So spreads partly reverse after the downgrade.
- Data needed: daily spread per issuer, a HY spread index, swap or Treasury curve, VIX, event dates. We have TRACE G-spreads (we propose them in place of CDS). We lack CDS and post-2017 ratings, so we use other dated events (8-K filings, earnings).
- Evidence: CDS, North America and Europe, IG and non-IG (p7, p10 say results are the same for both). Not a bond test.
- HY applicability: medium. The method transfers. The reversal is CDS evidence, not HY bond evidence.
- Fit to our signals: events module and S6. Gives the normal-return model and the test the event model needs.
- Test: apply eq. (9) to TRACE issuer G-spreads around 8-K item 2.06, 3.01, 5.02 events and earnings, 2005-2024 HY. Pass: rank test rejects at 5% on day 0 for at least two event types, and the placebo dates reject at 5% plus or minus 1%.

### F5. TRACE across-the-curve spread index as market state (source: Financial Market - 2023 - Berndt - Across-the-Curve Credit Spread Indices.pdf, p5, p10-11)
- Status: NEW (macro state input). Also a substitute for the index OAS we lack.
- Source says: for each maturity bucket $m$ (1-2, 2-3, 3-4, 4-5 years) and month $t$, take the transaction-volume-weighted median spread $s_{m,t}$. Weight buckets by trailing one-year issuance share $q_{m,t}$, eq. (1), p5:
  $$X_{LT,t}=\sum_{m}q_{m,t}\,s_{m,t}$$
  Intuition: a spread index that tracks what issuers pay now, and that is hard to move with one trade.
  FXI widens the set to all corporate issuers. Covered dollar volume rises by about five times over 2014-2019. FXI and the bank index move together, most of all late in the sample (p10). Filters: senior unsecured, no 144A, convertible, putable, perpetual, Yankee (p10). Trades above $250,000 (p6, p11).
- Data needed: Enhanced TRACE trades with size (we have TRACE), FISD maturity and offering amount. We lack amount outstanding. We propose transaction-volume weights alone, or offering amount from FISD if available.
- Evidence: construction and charts only, 2002-2019. No forecast test. Bank IG focus. FXI includes all ratings, but the paper does not split HY.
- HY applicability: medium. We can build an HY-only FXI from our own TRACE data. That gives a market spread level and slope without Barclays data.
- Fit to our signals: S7 replacement input (state variable), and the market factor for the CDS-style normal model in F4.
- Test: build HY-FXI monthly 2003-2024. Regress next 12-month HY default rate (Moody's) and next 3-month HY excess return on its level and 3-month change. Pass: out-of-sample R squared above zero in rolling windows and same sign in all four cycles.

### F6. Spread breakeven cushion (source: CARRY AND ROLL-DOWN STRATEGIES.pdf, p13, p15-16)
- Status: variant of carry and maturity roll-down (Ben Dor, IPR 2018).
- Source says (Spanish text): the credit rolling yield over horizon $h$ is $RY^S\approx S_{m,t}\,\partial t-D_h\,(S_{m-h,t}-S_{m,t})$ (p15). The breakeven spread at $t+h$, p16:
  $$S^{*}_{m-h,t+h}\approx S_{m-h,t}+\frac{RY^S}{D_h}$$
  Intuition: the spread can widen by $RY^S/D_h$ before the position loses money. That is carry per unit of duration risk.
- Data needed: issuer spread curve (from TRACE), duration. We have both.
- Evidence: none. Theory with a Treasury curve example (p6).
- HY applicability: medium. HY issuer curves are often flat or inverted, so roll-down can be negative. The cushion measures that.
- Fit to our signals: carry input to S1 and the macro layer. It also normalises carry for DTS-neutral legs.
- Test: rank HY bonds by $RY^S/(D_h\,\sigma_S)$, with $\sigma_S$ the 1-year spread volatility. Horizon 3 months. Pass: rank IC after costs above 0.02 and above raw spread IC in 3 of 4 cycles.

### F7. Credit-curve term premium ("directionless slope") and curvature (source: Factor_Model_Related (1).pdf, p14-15)
- Status: NEW (proposal, no evidence).
- Source says: slope $=s_{10y}-s_{2y\text{ or }3y}$ (eq. 1, p14). Curvature $=s_{5y}-0.5\,s_{10y}+0.5\,s_{2y}$ (p15, as written; a standard butterfly uses $-0.5$ on both wings). Term premium: regress $s_{10y}-s_{5y}$ on $s_{2y}$ and keep the residual (p15):
  $$TP_t=(s_{10y}-s_{5y})_t-\hat\beta\,s_{2y,t}$$
  Intuition: the part of curve steepness not explained by the short-end spread level is a premium for duration of credit risk.
- Data needed: issuer or sector spread curves at 2, 5, 10 years (from TRACE). We have them.
- Evidence: none. The draft is a plan.
- HY applicability: medium. Many HY issuers have one or two bonds, so use sector-by-rating curves.
- Fit to our signals: new signal for the curve leg of S4, and a state input for S7.
- Test: within HY sector-rating cells, go long the long-end bucket when $TP$ is in the top tercile. Horizon 3 months. Pass: DTS-neutral long-short Sharpe above 0.3 net of costs, positive in 3 of 4 cycles.

### F8. Sector-standardised fundamental composite (source: Factor_Model_Related (1).pdf, p16)
- Status: variant of defensive or quality (IPR 2018) and of Altman Z.
- Source says: four ratios: interest coverage, free cash flow to debt, net debt to EBITDA, EBITDA margin. Standardise each within GICS sector, then add linearly into one score per company (p16):
  $$Q_i=\sum_{k=1}^{4}\operatorname{sign}_k\,\frac{x_{ik}-\mu_{sector,k}}{\sigma_{sector,k}}$$
  Intuition: one quality number that compares a firm only with peers of the same business.
- Data needed: Compustat point-in-time (we have).
- Evidence: none.
- HY applicability: medium. These are standard HY credit metrics. The signal may already sit inside our fair spread inputs.
- Fit to our signals: S1 input, and a control for S2.
- Test: add $Q_i$ to S1. Pass: out-of-sample S1 residual IC rises by at least 0.005, else drop it as redundant.

### F9. Risk-adjusted IC (RAMIC) and rank-to-normal standardisation (source: Factor_Model_Related (1).pdf, p16, p18-19)
- Status: NEW evaluation metric (not a factor).
- Source says: cross-sectional RAMIC, eq. (4)-(5), p19:
  $$RAMIC_{t,h}=\frac{252}{h}\,\mathbb E\big[\tilde s^i_t\cdot dts^i_t\cdot r^i_{t+h}\big],\qquad \tilde s^i_t\in\{+1,0,-1\}\text{ by bottom and top decile}$$
  Average over all start dates inside the horizon (for example 20 for one month) to cut start-date noise (p18). Legs are DTS-neutral at 612.5 DTS units (4.9 x 125 bp) (p19). Inputs pass through rank, divide by N+1, then inverse normal (p16).
  Intuition: an IC that weights each bond by its spread risk, so CCC bonds do not dominate.
  Note: as written, the formula multiplies the return by DTS. A risk-adjusted IC would divide by DTS. We propose to test both.
- Data needed: TRACE returns, DTS (we have).
- Evidence: none.
- HY applicability: medium. HY risk spans a wide range, so DTS scaling matters.
- Fit to our signals: evaluation for S1-S6. It complements rank IC in the definition of done.
- Test: compute RAMIC and rank IC for S1. Pass: RAMIC sign agrees with rank IC sign in each cycle. If not, record which one the DTS-neutral backtest supports.

### F10. Adaptive boosted signal combiner with sector, size and beta neutral ranks (source: Factor_Model_Related (1).pdf, p9-12)
- Status: variant of OneScore combination (Ben Dor).
- Source says: label top 30% and bottom 30% of one-month forward returns per month and sector (p9-10). Inputs are factor ranks divided by coverage, in (0,1] (p10). Train AdaBoost on three windows: trailing 12 months, same calendar month over trailing 12 years, last month (p10). Weight the three classifiers by their past rank IC (p11). Neutralise within sector x size x beta cells (p11-12). Without beta neutralisation the model was short beta, with its worst drawdown in March 2009 (p12).
- Data needed: our signal panel and TRACE returns.
- Evidence: the text cites figures that the draft does not include. No numbers.
- HY applicability: medium. The low-beta tilt warning matters most in HY junk rallies.
- Fit to our signals: signal combination layer across S1-S6.
- Test: compare AdaBoost combiner with equal-weight z-score combination. Pass: combiner rank IC higher in 3 of 4 cycles and beta to HY index within plus or minus 0.1.

### F11. Vol-normalised double-EMA momentum filter (source: Design and analysis of momentum trading strategies.pdf, p7-8, p11)
- Status: variant of momentum (HvZ 2017, IPR 2018) and of EMC.
- Source says: normalised return $U_n=\Delta X_n/\hat\sigma_{n-1}$. EMA2 signal is the difference of two EMAs, system function with poles at $\alpha=1-N_\alpha^{-1}$ and $\beta=1-N_\beta^{-1}$ (p7-8). EMA2 has finite path length, so it trades less than EMA1 under proportional costs (p8). Test uses EMA2 with N = 20, 40 and a 20-day EMA of squared changes for $\hat\sigma$ (p11). Skewness of trading returns peaks near 2.1 at period $M\approx1.7(N_\alpha+N_\beta)$ (p11).
  Intuition: a smooth trend signal on risk-scaled returns that trades less and has right-skewed payoff.
- Data needed: daily bond or sector excess returns (TRACE), daily HY index proxy (our own FXI from F5).
- Evidence: CHF/USD and S&P 500 futures only (p11). No credit evidence.
- HY applicability: low to medium. Momentum in HY single bonds is weak in the known literature. The filter may suit sector or index timing.
- Fit to our signals: market-timing overlay or S7 replacement candidate.
- Test: EMA2(20,40) on daily HY-FXI excess return, position = sign or tanh of signal. Horizon 1 month. Pass: Sharpe above 0.3 net and positive skew of monthly returns, 2003-2024.

### F12. Industry equity leads industry credit (source: 10-1108_jes-03-2016-0053.pdf, p7, p18)
- Status: variant of EMC (equity momentum), at industry level.
- Source says: daily data, 11 US industry CDS 5y indices and equity indices, Dec 14 2007 to Dec 31 2014 (p7, p18). Frequency-domain Granger tests show one-way causality from equity to CDS for all industries except banks (two-way) and utilities (none) (p18). Coherence rises in crises (p1, p18).
- Data needed: industry equity returns (we have CRSP), industry HY spread from TRACE.
- Evidence: no return test. CDS industry indices, not HY bonds.
- HY applicability: low. EMC already covers the firm level.
- Fit to our signals: sector-level version of EMC inside S7.
- Test: regress next-month HY sector spread change on past 1-3 month sector equity return. Pass: t-stat below -2 with the expected sign, excluding banks and utilities.

### F13. ETF flow pressure on HY bonds (source: 61444f23-caee-47ed-9bb0-ecd48e95c54b.pdf, p3, p5, p7)
- Status: NEW (proposal, no evidence).
- Source says: ETF flows have medium-term memory (p3). Creations and redemptions are non-fundamental demand shocks that push prices from fundamental value (p3, p5). Use ETF flows to find mispriced bonds in the eligible universe and to time entry and exit (p7).
- We propose: $FP_{i,t}=\sum_{e}w_{i,e,t}\,\text{Flow}_{e,t-k:t}/\text{AUM}_{e,t-k}$, with $w$ the bond's weight in HYG, JNK and other HY ETFs. Intuition: bonds that ETFs must sell after outflows trade cheap and then revert.
- Data needed: ETF daily shares outstanding and holdings. We lack these.
- Evidence: none in this file.
- HY applicability: medium. HY ETFs are a large marginal trader in liquid HY bonds.
- Fit to our signals: new signal, close to S6 forced flows.
- Test: long high-outflow-exposed bonds versus low, matched on rating and duration. Horizon 1 month. Pass: positive return after costs, t-stat above 2.

### F14. Signed factor flow from dealer-customer trades (source: FillCurveV2.pdf, p6-7. MainCLVersionMay28th.pdf, p2)
- Status: NEW (proposal, no evidence).
- Source says: RFQ exposure to factor $k$: $V_t^k=\beta_{b_t,k}\,s_t\,Q_t$ (eq. 2, p6). Bonds sort into $2^K$ categories by beta sign (eq. 3, p7). Factor flow sums $V$ over an interval by category and side. MainCL eq. (4) multiplies by CR01.
- We propose: replace RFQs with Enhanced TRACE customer trades and their buy and sell flag. Intuition: net customer selling of a risk factor predicts short-term cheapening of bonds loaded on it.
- Data needed: TRACE side flag and size (we have TRACE), our factor betas.
- Evidence: none.
- HY applicability: low to medium. Sides are visible in TRACE. Signal half-life may be days.
- Fit to our signals: new short-horizon signal. Low priority for a quantamental analyst.
- Test: weekly net customer sell flow by issuer, scaled by 3-month average volume. Pass: next-week return rank IC above 0.02 net of costs.

### F15. Option-implied default intensity and implied recovery (source: Journal of Futures Markets - 2023 - Begin ..., p3-5, p12, p16)
- Status: NEW (we lack the data).
- Source says: a deep OTM American put scaled by $1/K$ is a unit recovery claim. Eq. (1), p4: $URC=\lambda\,(1-e^{-(r+\lambda)(T-t)})/(r+\lambda)$. Solve for $\lambda$. Then eq. (2), p4: $R=1-CDS/\lambda$. Data: 1-year CDS, puts with delta above -15%, maturity 6-18 months, 399 US firms, 2003-2019 (p5). Leverage is the most selected driver of $\lambda$, at 73% inclusion (p12). Rate level and slope drive implied recovery (p12). Random forest out-of-sample R squared is between 80% and 90% for recovery by sector (p16).
- Data needed: OptionMetrics puts and CDS. We lack both.
- HY applicability: low for now. Many HY issuers have no listed options and no CDS.
- Fit to our signals: recovery layer and S4 cross-check.
- Test: deferred until option data exists.

### F16. HY spread versus VIX z-score gap (source: HY_VIX (2).pdf, p1-3)
- Status: NEW (proposal, no evidence).
- Source says: a screen shows rolling z-scores and percentiles of CDX HY and VIX over 1, 3, 6, 12, 24 months. On 2011-10-06 CDX HY z was 3.67 and VIX z was 2.59 over 12 months (p3).
- We propose: $G_t=z_{12m}(\text{HY spread})-z_{12m}(\text{VIX})$. Intuition: when credit is more stressed than equity volatility, credit may be cheap.
- Data needed: HY spread level (our HY-FXI from F5) and VIX (public).
- Evidence: none.
- HY applicability: medium for timing.
- Fit to our signals: S7 replacement candidate.
- Test: go long HY beta when $G_t$ is in the top quintile. Horizon 3 months. Pass: hit rate above 60% and positive excess return in 3 of 4 cycles.

### F17. Abnormal TRACE trading before corporate events (source: The Trading Dynamics of Corporate Bonds and Bond ETFs.pdf, p94-95, p106-107)
- Status: NEW event feature (weak).
- Source says: abnormal measure = event-day trading minus its mean over days [-40,-6], for quantity, trade count and volume (p94). Enhanced TRACE, 2012-2021 (p91). Bond trading rises after dividend changes, M&A, repurchases, SEOs and spin-offs, but not after CEO turnover, splits or ticker changes (p106-107). Abnormal volume spikes on day -2 before involuntary CEO turnover (p95).
- Data needed: TRACE (we have), event dates from SEC 8-K (we have).
- Evidence: volume only. No return results. IG and HY pooled.
- HY applicability: low to medium. Pre-event volume may flag information leakage.
- Fit to our signals: events module feature.
- Test: abnormal volume z-score above 3 at day -2 as a flag. Pass: flagged events show larger absolute abnormal spread change (F4 method) on day 0 than unflagged, at 5%.

### F18. Countercyclical stress constraints CSx2 and CSL (source: Fixed income portfolio optimisation.pdf, p5-6)
- Status: NEW sizing rule.
- Source says: CSx2 is the loss from a doubling of spread. CSL is the loss from moving yield to a fixed stress level, eq. (4): $CSL=(1-y_0/y^*)\,(1-(1+y^*/m)^{-mT})$. CSL falls as spreads widen, CSx2 rises. Constraining both buys risk when spreads are wide and cuts it when they are tight (p5-6).
- Data needed: yields, maturities (we have).
- Evidence: none.
- HY applicability: medium for position sizing.
- Fit to our signals: outputs layer, position limits.
- Test: backtest an HY sleeve with both limits versus a fixed DTS limit. Pass: higher Sharpe and lower max drawdown across 2008 and 2020.

## Top 3
1. F1 par-adjusted spread with rating-dependent recovery: it removes the dollar-price bias that hits HY most, and it plugs straight into S1 with data we already hold.
2. F2 migration-adjusted expected return: it turns spread into expected return net of downgrade and default loss, which matters most for B and CCC, and it gives S6 a return number.
3. F3 cube-root no-trade buffer: HY trading costs are large, and this rule converts S1 residuals into trades with a stated cost trade-off and a falsifiable turnover test.
