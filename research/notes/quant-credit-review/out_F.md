# Folder F: Work_Quant credit and quant notes. New factors for the HY analyst

Scope: 58 files. All files open with `pdftotext`. No file failed.
Page numbers are PDF pages. "Source says" marks the claim of the note. "We propose" marks our build.

Duplicates:
- `Market timing ... (2).pdf` and `Market timing ... (3).pdf` hold the same paper (same text).
- `investor positioning 4th of march (1).pdf` and `ChartPack/170974b6_..._604 (1).pdf` hold the same note (same text after the download stamp).
- `Inflation, Stagflation Relax Presentation` is the slide version of `Inflation, Stagflation Relax Main Piece`.
- `reversion_presentation_2` is the slide version of `reversion_long_doc`.
- `PROTECTING YOUR CORE -Q4 2017` is the slide version of `protect your core`.
- `Presentation Systematic Investing in Currency Markets` is the slide version of `FX Cookbook`.

## Triage table

| File | Title, bank or authors, year | Topic | Relevant (yes/no) | Why |
|---|---|---|---|---|
| 9_30_Joe_Mezrich_Ensemble_Alpha_050715 (1).pdf | Ensemble Alpha, Nomura (Mezrich), May 2015 | Aggregate mutual fund active weights as stock alpha | no | Equity. Bond version needs fund holdings data, which we lack. |
| A Quant Guide to Duration Investing when Rates are at Near-Zero Levels (1).pdf | A Quant Guide to Duration Investing, DB QIS (Gonzalez), Oct 2020 | Rates factors: momentum, carry, low beta, value (cycle, real rates) on 22 swap markets | no | Rates only. No credit signal. |
| Building a Better Risk Switch (1).pdf | Building a Better Risk-Switch, DB Quant Snaps (Natividade), 6 Nov 2012 | Risk sentiment index (11 barometers, 3 are credit spreads), 3-state Gaussian mixture, Markov transitions, state-conditioned strategy weights | yes | Regime method transfers to timing of HY signals. |
| Cross Asset Carry A Study (1).pdf | Cross-Asset Carry: A Study, DB (Anand, Natividade, Lyu), Jun 2018 | Carry portfolio construction in FX, commodities, rates, equity | no | No credit carry. Slides only. |
| Delving Into New Territories (1).pdf | Quantcraft: Delving Into New Territories, DB (Natividade et al.), 10 Nov 2015 | Macro beat and shock nowcast indices, GSI timing deflator, sentiment, monetary policy momentum | yes | Macro inputs and timing rule are candidates to replace S7. |
| Designing a Liquidity based Toolkit (1).pdf | Designing a Liquidity based Toolkit, DB (Capra et al.), 18 Oct 2016 | Equity liquidity level, volatility, change, liquidity beta, Corwin-Schultz spread | yes | Liquidity dimensions transfer to TRACE bond data. |
| Dodge the Sting in the Tail_ Integrating (1).pdf | Dodge the Sting in the Tail, DB (Ward, Tentes, Leng et al.), 15 Jan 2019 | Tail-risk-adjusted covariance for portfolio construction | no | Portfolio construction method, not a signal. |
| Does Simple Pairs Trading Still Work (1).pdf | Do and Faff, FAJ 66(4), 2010 | Equity pairs trading | no | Equity. No credit content. |
| ECB - Attentive, Unwilling for now, but (1).pdf | ECB - Attentive, Unwilling, DB Euroland rates (Sokos), 3 Mar 2021 | PEPP purchases | no | EUR rates. |
| FX Cookbook A Recipe for Systematic Investing in Currency Markets (1).pdf | Quantcraft: FX Cookbook, DB (Anand, Natividade et al.), 15 Jan 2019 | FX factors | no | FX only. |
| Inflation, Stagflation Relax Main Piece (1).pdf | Quantcraft: Inflation, Stagflation? Relax, DB (Anand et al.), 22 Jun 2021 | Regime-conditioned macro factor model, stressed Sharpe ratios, scenario baskets. Credit factor = HY minus IG | yes | Method for a macro-conditional sector tilt (S7 replacement). |
| Inflation, Stagflation Relax Presentation (1).pdf | Slide version of the main piece, DB, Jul 2021 | Same | no | Duplicate content. Read the main piece. |
| Investor Positioning 26th f Feb (1).pdf | Investor Positioning and Flows chart pack, DB (Thatte), 26 Feb 2021 | Equity positioning z-scores, EPFR fund flows incl. US HY | no | Positioning and flow data we lack. Charts only, no test. |
| JPM_US_Treasury_Market_D_2018-11-01_2821053 (1).pdf | US Treasury Market Daily, JPM (Barry et al.), 1 Nov 2018 | 10y UST fair value model | no | Rates. |
| Learning to drive in the fast lane (1).pdf | Portfolios Under Construction, DB (Alvarez, Luo et al.), 26 Apr 2011 | Grinold signal decay and cost-aware signal weighting | no | Method only. Useful later for signal blending. |
| Linear Signal Blending (1).pdf | DB Foundations: Linear Signal Blending, DB (Mesomeris et al.), 15 Jun 2017 | Equal, risk parity, mean-variance blending of equity signals | no | Method only. |
| Macro Credit Brief - Spreads, Rates and (1).pdf | Macro Credit Brief: Spreads, Rates and the Common QE Factor, DB (Jezek), 22 Feb 2021 | Spread moves in sharp rate sell-offs, spread-rate correlation, common QE factor, percentile-rank heatmaps | yes | HY spread timing rule conditional on rate shock type. |
| Market timing and trading strategies ... (2).pdf | Schizas and Thomakos, Quant Finance 15(2), 2015 | Pairwise rotation between two equity ETFs | no | Equity ETFs. Duplicate of (3). |
| Market timing and trading strategies ... (3).pdf | Same paper | Same | no | Duplicate of (2). |
| PROTECTING YOUR CORE -Q4 2017 (1).pdf | Protecting Your Core Q4 2017, DB slides, 2017 | Portfolio protection | no | Slide version of "protect your core". |
| Presentation Systematic Investing in Currency Markets (1).pdf | Systematic Investing in Currency Markets, DB slides, Jun 2019 | FX | no | FX only. |
| Quantcraft Presentation Systematic Investing in Commodity Markets (1).pdf | Systematic Investing in Commodity Markets, DB QIS slides, May 2021 | Commodities | no | Commodities only. |
| Realized Illiquidity.pdf | Lacava, Ranaldo, Santucci de Magistris, working paper, 3 Jan 2023 | Realized Amihud and high-low Amihud, expected vs unexpected illiquidity | yes | Computable from TRACE intraday trades. Gives a bond liquidity factor. |
| Research October 2022 (1).pdf | Global Factor Monitor, DB QIS, Jan 2022 | Monitor of DB strategies incl. credit factors and macro scenario sensitivities | yes (low) | Confirms live DB credit factor definitions. No new numbers in text. |
| Riding Carry (1).pdf | Quantcraft: Riding Carry, DB (Anand, Natividade et al.), 3 Sep 2014 | Carry strategies, GSI definition (Appendix A) | yes | GSI recipe with two credit inputs. |
| Risk Sentiment Index EM Specific (1).pdf | EM FX: New EM Risk Monitor, DB (Zhang, Sha et al.), 5 Feb 2020 | EM FX risk monitor | no | EM FX. |
| SSRN-id1628020 (1).pdf | Girardin, Tan, Wong, HKIMR WP 02/2010 | Order flow cross-market effects, Chinese stocks, Treasuries, corporate bonds | no | China exchange data. No US transfer we can build. |
| SSRN-id3169832 (3).pdf | Price Signatures, DB (Oomen), Apr 2018 | Execution price signatures, functional bootstrap | no | Execution analytics. |
| SSRN-id37063901 (1).pdf | Capponi and Cont, Multi-asset market impact and order flow commonality, Oct 2020 | Cross-impact | no | Microstructure. |
| SSRN-id4284177.pdf | Elkamhi, Jo, Lee, Salerno, Volatility Timing (slides), Nov 2022 | Risk-based allocation, clustering | no | Allocation method. |
| Systematic Investing in Options Markets (1).pdf | Systematic Investing in Options Markets, DB slides, Sep 2018 | Variance risk premia | no | Options. States PC1 of US corporate credit at about 33% only. |
| U.S. Treasury Market Structure and liquidity (1).pdf | US Treasury Market Structure and Liquidity, JPM (Barry, Roever), 2 Apr 2015 | UST liquidity | no | Rates. |
| Value Anatomy (1).pdf | Value Anatomy, DB (Leng, Ward et al.), 18 Feb 2019 | Owner earnings and owner book value | yes | Maintenance-capex-adjusted cash flow transfers to leverage and coverage. |
| anatonomy of a tantrum (1).pdf | Anatomy of a tantrum, DB US rates (Sparks), 1 Feb 2021 | Term premium model, positioning before taper | yes (low) | Supports the term-premium split of rate moves in factor F1. |
| investor positioning 4th of march (1).pdf | Investor Positioning: Rising Rates and Bond Positioning, DB (Thatte), 5 Mar 2021 | Bond positioning, fund flows | no | Positioning data we lack. Duplicate of ChartPack/170974b6. |
| jofi.12738 (1).pdf | Boons and Porras Prado, Basis-Momentum, JF 74(1), 2019 | Momentum difference across futures maturities | yes | Transfers to issuer curve momentum. |
| protect your core (1).pdf | Quantcraft: Protect, Diversify or Track Your Core, DB (Anand et al.), 17 Aug 2017 | Asset-level portfolio construction | no | Method only. |
| return of the machines (1).pdf | Quantcraft: The Return of the Machines, DB (Tomasi), 23 Apr 2020 | N-LASR AdaBoost alpha aggregation | no | Equity ML aggregation. Method only. |
| reversion_long_doc (1).pdf | Quantcraft: Reversion: new horizons, DB (Tomasi), 17 Mar 2021 | PCA residual plus Ornstein-Uhlenbeck reversion | yes | Transfers to bond residual excess returns. |
| reversion_presentation_2 (1).pdf | Slide version, DB, Mar 2021 | Same | no | Duplicate content. |
| short dated hy to position versus vol (1).pdf | Another vol test passed; Short dated BBs attractive, DB HY (Nicol), 2 Mar 2021 | HY spreads in rate sell-offs, rating x tenor percentile ranks, BB/BBB ratio | yes | Direct US HY evidence. |
| slopes em (1).pdf | EM Credit Strategy Note: basis and curves, DB (Jiang, Sha), 14 Aug 2020 | EM sovereign CDS-bond basis and curve RV | no | EM sovereigns. Needs CDS. |
| strat_dev_process (1).pdf | Peterson, Developing and Backtesting Systematic Trading Strategies, Jun 2017 | Backtest process, overfit control | no | Process only. |
| what our quants say (1).pdf | Here is what our quants say, DB FX (Saravelos, Natividade), 17 Jul 2019 | FX signals | no | FX. |
| AI Edition/4a3ff00c_..._604 (1).pdf | Academic Insights, DB (Natividade et al.), 25 Jun 2020 | Paper digest | no | One credit mention (recession prediction markets). No signal definition. |
| ChartPack/170974b6_..._604 (1).pdf | Investor Positioning, DB (Thatte), 5 Mar 2021 | Same as "investor positioning 4th of march" | no | Duplicate. |
| ChartPack/2d668770_..._604 (1).pdf | Investor Positioning chart pack, DB (Thatte), 16 Jul 2021 | Positioning, flows | no | Positioning data we lack. |
| ChartPack/3b17335a_..._604 (1).pdf | Global Fixed Income Weekly, DB (Yared et al.), 9 Jul 2021 | Rates digest | no | Rates. |
| ChartPack/aff40b50_..._604 (1).pdf | Investor Positioning: Moving Towards Neutral, DB (Thatte), 9 Jul 2021 | Cross-asset momentum breadth, positioning | no | Charts only, no test. |
| IG & HY Strategy/19b1f580_..._604 (1).pdf | EM Debt: Technicals Monitor, DB (Sha, Jiang), 2 Mar 2021 | EM supply, flows, fund beta | no | EM sovereigns. Fund beta has no definition in text. |
| IG & HY Strategy/6fe578e7_..._604 (1).pdf | Yields and Credit Spreads - The long-term relationship, DB (Reid), 3 Mar 2021 | Nominal vs real yield correlation with BBB, IG, HY spreads | yes | Real-yield regime for HY spreads. |
| IG & HY Strategy/EM Credit Strategy Note (1).pdf | EM Credit Strategy Note: MENA RV, DB (Jiang), 22 Jan 2021 | EM sovereign cash RV | no | EM sovereigns. |
| IG & HY Strategy/EM Special Publication_ EM Flows and Risk Sentiment (1).pdf | EM Flows and Risk Sentiment, DB (Zhang et al.), 5 Aug 2020 | EM flow indicator, risk monitor | no | EM local markets. Flow data we lack. |
| Factors/ebec8f2e_..._604 (1).pdf | Quantcraft: Time To Cross the Bridge: Factor Investing in Credit Markets, DB (Gonzalez, Natividade, Anand), 3 May 2019 | CDS factors: quality (DTD), low duration, value, low beta, market and residual momentum, DTS neutralisation, cost control | yes | Core credit note. Mostly known (DB card). Gives exact definitions for variants. |
| Rel Val/9be8a31d_..._604 (1).pdf | USD-EUR 5s10s30s convergence, DB (Giannopoulos), 11 Feb 2021 | Rates fly RV | no | Rates. |
| Rel Val/An intuitive top down view on USTs.pdf | An intuitive top down view on USTs, DB (Yared, Sparks), 4 Mar 2021 | UST level | no | Rates. |
| Rel Val/ab5ed45a_..._604 (1).pdf | EUR positive carry steepeners, DB (Giannopoulos), 3 Mar 2021 | EUR rates vol | no | Rates. |
| Quantmental Macro/4ccd49fc_..._604 (1).pdf | When shocks no longer shock, DB (Luo, Kocic), 18 Jul 2021 | Rates reaction to CPI surprises | no | Rates. |

Count: 58 files triaged. 15 files relevant (3, 5, 6, 11, 17, 23, 24, 25, 33, 34, 36, 39, 41, 51, 54 in list order).

## Factors found

### F1. Real-yield shock regime for HY spreads (source: IG & HY Strategy/6fe578e7, pp. 1-6. Macro Credit Brief, pp. 2-4. short dated hy, pp. 2-4. anatomy of a tantrum, p. 1)
- Status: NEW. Candidate replacement for S7.
- Source says:
  - Since the 1950s, 3-month changes in 10y nominal UST yields and BBB spreads correlate negatively on a 2-year rolling window (6fe578e7, p. 3).
  - The correlation of BBB spreads with real yields trends upward and stays positive through the pandemic (6fe578e7, pp. 1, 3).
  - "Real yields are likely the key thing to watch" (6fe578e7, p. 1).
  - Jezek: the taper tantrum widening came from a common QE factor that lifts the term premium and the illiquidity premium together. The rate move did not cause it (Macro Credit Brief, pp. 2-3).
- Definition (we propose): split each 1-month change in the 10y UST yield into a real-yield part and a breakeven part. Use TIPS real yield $r^{real}$ and breakeven $\pi^{be}=y^{nom}-r^{real}$.
  $$\text{RYS}_t=\frac{\Delta_{21} r^{real}_t}{\sigma_{252}(\Delta_{21} r^{real})},\qquad \text{BES}_t=\frac{\Delta_{21} \pi^{be}_t}{\sigma_{252}(\Delta_{21}\pi^{be})}$$
  $$\text{Signal}_t=-\left(\text{RYS}_t-\text{BES}_t\right)$$
  Intuition: a rise in nominal yields led by inflation expectations signals growth and tightens HY. A rise led by real yields raises funding cost for levered issuers and widens HY.
  - Variant: replace the real-yield part with the ACM term premium change. This follows the common QE factor of Jezek.
  - Lag the signal one day. Use only data published before the decision date.
- Data needed: 10y nominal and 10y TIPS yields (FRED DGS10, DFII10), ACM term premium (NY Fed), HY G-spread index built from TRACE. All available.
- Evidence (source):
  - USD HY 12-week rolling correlation of weekly spread and rate changes averages -0.6. EUR HY averages -0.5 (short dated hy, p. 2).
  - In the 6 largest 5y UST sell-offs since the GFC, USD HY spreads moved -77bp on average and -65bp at the median. Only 2013 widened, by 16bp (short dated hy, p. 3, Fig. 4).
  - USD IG 7-10y: 27 sharp 10y UST sell-off episodes in two decades. EUR IG: 21 episodes. Spreads tightened in most of them (Macro Credit Brief, p. 2, Figs. 1-2).
  - The sources give no out-of-sample test of the real vs breakeven split. The real-yield claim rests on rolling correlations in charts (6fe578e7, pp. 3, 5-6).
- HY applicability: high. HY has the most leverage, so funding-cost shocks bite hardest. The source gives HY-specific charts (6fe578e7, p. 5, Fig. 6).
- Fit to our signals: replaces S7 as the macro input. Use it to tilt HY beta and HY sector duration exposure. It also conditions S1 and S2 sizing.
- Test: on monthly data 2003-2024, regress the next 1-month change in the HY G-spread index on Signal. Pass if the slope is negative with Newey-West t < -2. The model must also beat a nominal-yield-only model on out-of-sample R² in at least 3 of the 4 cycles (2008, 2015, 2020, 2022).

### F2. Quality compression in rate sell-offs (source: short dated hy, pp. 3-4)
- Status: NEW.
- Source says: during the 6 largest US rate sell-offs since the GFC, the B minus BB spread differential tightened by 32bp on average and 29bp at the median (p. 3, Fig. 4). EUR shows 35bp and 19bp (p. 4, Fig. 5). The source also warns of temporary 50-100bp spread spikes within the episodes of 2013, 2015, and 2019 (p. 4).
- Definition (we propose): define a sell-off state $S_t=1$ when the 5y UST yield rises more than $k$ bp from its trailing 3-month trough. Take $k=40$, the lower end of the episodes in Fig. 4. In state $S_t=1$, go long single-B and short BB, DTS-neutral:
  $$w^{B}_t\cdot\text{DTS}^{B}_t=w^{BB}_t\cdot\text{DTS}^{BB}_t$$
  Intuition: rate sell-offs in this sample came with growth upgrades, so the lower-rated bonds rallied more.
- Data needed: TRACE G-spreads, rating buckets, 5y UST. Gap: we lack ratings after Feb 2017. Proxy the rating bucket with the S1 implied rating or a spread bucket after Feb 2017.
- Evidence: 6 US episodes and 6 EUR episodes only (pp. 3-4). The sample is small. The source runs no significance test.
- HY applicability: high. It is a pure intra-HY trade.
- Fit to our signals: new conditional overlay on S6 rating buckets. It also feeds the event model (rate-shock events).
- Test: identify all episodes 2003-2024 with the rule above. Pass if the DTS-neutral B minus BB excess return is positive in at least 70% of episodes and the mean is positive with a bootstrap p < 0.10.

### F3. Rating x tenor cell valuation percentile and cross-rating spread ratio (source: short dated hy, p. 5. Macro Credit Brief, pp. 11-13)
- Status: NEW. It is a variant of value, but at the cell level, not the issuer level.
- Source says: rank the current spread of each rating x maturity cell against its own history since 2009. 100% means the spread sits at its tights. In March 2021, short BB and B sat near the 60th percentile. 7-10y cells sat at the 92nd-96th (p. 5, Fig. 7). The 1-3y BB/BBB spread ratio was above 3.5x, which is wide versus history (p. 5, Fig. 8). Jezek's heatmaps rank cells since 2000 and since 2015 (Macro Credit Brief, p. 11).
- Definition (we propose): for cell $c$ (rating r x tenor bucket m),
  $$P_{c,t}=\frac{1}{N}\sum_{\tau\in W_t}\mathbf{1}\{s_{c,\tau}\le s_{c,t}\},\qquad R^{BB/BBB}_{m,t}=\frac{s_{BB,m,t}}{s_{BBB,m,t}}$$
  Use an expanding window $W_t$ from 2003, or a rolling 10-year window. Overweight the cells with the lowest $P$ (cheapest relative to own history), DTS-matched to the benchmark.
  Intuition: cells move with the cycle, so each cell's own history is a peer group that controls for its structural spread level.
- Data needed: TRACE G-spreads aggregated to cells. Rating gap after Feb 2017 (use a spread-implied rating).
- Evidence: one snapshot (Mar 2021). The source gives no backtest.
- HY applicability: high. It gives the curve and quality tilt that S1 does not set.
- Fit to our signals: new signal for sector and curve allocation. It is a second replacement candidate for S7.
- Test: monthly, sort cells into terciles on $P$. Pass if the cheapest-minus-richest DTS-neutral excess return over 3 months has a rank IC > 0.03 and stays positive in at least 3 of the 4 cycles.

### F4. Global Sentiment Indicator (GSI) with a continuous deflator (source: Riding Carry, p. 21 (App. A). Delving Into New Territories, pp. 6, 11. Building a Better Risk Switch, pp. 1-2)
- Status: NEW. It is a timing overlay. It differs from the EBP and the sentiment cards in the repo, which are aggregate predictors. This is a state classifier and a position scaler.
- Source says: the GSI aggregates 11 barometers (Riding Carry, p. 21):
  1. VIX.
  2. MSCI Financials over MSCI World.
  3. 30y minus 2y asset swap spread.
  4. Swaption implied vol.
  5. TED spread.
  6. Moody's BAA minus 10y UST.
  7. iBoxx US Non-Financials CDS.
  8. CVIX.
  9. FX vol slope.
  10. FX risk reversals.
  11. EMBI+ spread.

  Each series is ranked as a quantile in a 1-year rolling window. The GSI is the first principal component, bounded in [0,1], with negative covariances set to zero. Higher GSI means higher risk. The risk switch note fits a 3-state Gaussian mixture to the GSI with Markov transitions (Risk Switch, p. 2).
- Definition (from source, Delving, p. 6): scale each position by a deflator. Use it only when the position goes against the risk state.
  - For negatively skewed assets (HY credit falls in this class) held long when $\text{GSI}_t>0.5$: $D_t=2-2\,\text{GSI}_t$.
  - For the same assets held short when $\text{GSI}_t<0.5$: $D_t=2\,\text{GSI}_t$.
  - Re-standardise the gross weights to 1 afterwards.

  Intuition: shrink a bet that fights the prevailing risk regime, without a binary switch.
- Data needed: we propose a US-only GSI from series we hold or can download free. Use the VIX, BAA-10y (FRED), the TED spread or its SOFR successor, the financials-over-market equity ratio (equity returns), the HY G-spread (TRACE), and Treasury implied vol (MOVE if licensed, otherwise realized UST vol). We lack CDS and FX option data.
- Evidence (source):
  - The macro factor commodity strategy Sharpe rises from 0.31 to 0.63 with GSI timing, pre-cost, about 11 years (Delving, p. 11, Fig. 12).
  - The regime-based minimum-variance portfolio reached a YTD 2012 Sharpe of 1.9. The time-based version reached 0.8 (Risk Switch, p. 2, Fig. 4). This covers less than one year, so it is weak evidence.
  - No HY credit test exists in these notes.
- HY applicability: medium. Two of the 11 inputs are credit spreads, so the indicator partly restates the HY spread.
- Fit to our signals: overlay on S1-S6 gross exposure. It also gives cycle-phase labels for the PD calibration "by cycle phase" in the definition of done.
- Test: apply the deflator to the S1 long-short HY portfolio, 2004-2024, monthly. Pass if the max drawdown falls by at least 20% and the Sharpe does not fall, in at least 3 of the 4 cycles.

### F5. Macro beat and shock indices (nowcast z-score changes) (source: Delving Into New Territories, pp. 3-7)
- Status: NEW. It replaces the macro input of S7.
- Source says: build a growth index and an inflation index per country. Follow the PC1 recipe of Beber et al. (2014) on unrevised releases, indexed on announcement dates (p. 4). The "beat" index tracks level and pace. The "shock" index uses actual minus Bloomberg median survey. The signal uses the 1-year z-score of the index, not its level, because the market already prices the level (p. 7).
- Definition (from source, pp. 4, 7):
  1. Make each release stationary. Use 3-month changes for YoY or level series.
  2. Forward-fill on business days.
  3. Build a Spearman correlation matrix with correlation averaging. Set negative values to 0.
  4. Standardise each series on a 5-year window.
  5. Take PC1 loadings, normalise them to sum to 1, and set $I_t=I_{t-1}+\sum_j w_j z_{j,t}$.
  6. Standardise $I_t$ on a 5-year window.
  7. Predict 1-month asset returns with the 1-year z-scores:
  $$r_{i,t\to t+1M}=a_i+\sum_j b_{ij}\, z_{t-1Y,t}(I_{j,t})+\varepsilon_{i,t}$$
  Intuition: surprises and changes in macro conditions move risk premia. Levels do not.
- Data needed: US macro releases with release dates and surveys (ALFRED vintages for hard and soft data. The survey median needs Bloomberg or a substitute). Macro series are in the repo. Survey consensus may be missing.
- Evidence (source): FX, equity, bond futures and commodities only. Bond futures inflation strategy: about 0.6 pre-cost Sharpe over 11 years (p. 12). No HY test.
- HY applicability: medium. Ang (2014), cited at p. 6, says growth explains about 60% of the equity risk premium variation. HY spreads load on growth. No source tests HY directly.
- Fit to our signals: input to the S7 replacement. Predict next-month HY sector excess returns from the growth and inflation z-scores.
- Test: monthly 2003-2024, expanding-window regression of next-month HY sector excess returns on the US growth and inflation beat z-scores. Pass if the sector tilt has a positive rank IC after costs in at least 3 of the 4 cycles.

### F6. Regime-conditioned stressed Sharpe ratio (SSR) for sector selection (source: Inflation, Stagflation Relax Main Piece, pp. 3-6)
- Status: NEW method. It replaces the S7 portfolio rule.
- Source says: there are 11 market-implied macro factors. One is "Credit Spread" = long US HY index, short US IG index (p. 3, Fig. 2). Split months into growth x inflation regimes at the factor medians. Within each regime, estimate the factor covariance and stepwise betas of 59 return streams. Shock the explicit factors by ±1σ and propagate the shock to the implicit factors:
  $$R_I^*=\Sigma_{IE}\Sigma_{EE}^{-1}R_E^*,\qquad r_A^*=\beta_A^{\top}\begin{pmatrix}R_E^*\\R_I^*\end{pmatrix},\qquad \text{SSR}_A=r_A^*/\sigma_A$$
  A stream qualifies for a scenario if both tests pass at p ≤ 0.2 (pp. 4-5):
  - its SSR is significantly positive in the scenario.
  - its SSR spread versus the opposite scenario is significant.

  Average all metrics over 21 tranches of 21-day returns (p. 3).
  Intuition: an asset hedges a scenario only if it wins in that scenario and loses in the opposite one.
- Data needed: HY sector excess returns (TRACE), plus market proxies for growth (equity index), inflation (TIPS minus nominal), and rates (UST). Credit-spread factor: build HY minus IG from TRACE. We lack the Barclays indices.
- Evidence: the inflation basket holds TIPS, breakevens, credit and commodities (p. 5). The text gives no out-of-sample performance numbers.
- HY applicability: medium. The method fits sector tilts. The source applies it to asset classes, not HY sectors.
- Fit to our signals: S7 replacement. Choose HY sectors that qualify for the scenario given by F1 or F5.
- Test: estimate on 2003-2012, then evaluate the 2013-2024 sector baskets out of sample. Pass if a qualifying sector beats a non-qualifying sector in the realized regime in at least 60% of months.

### F7. Realized Amihud bond illiquidity, level and shock (source: Realized Illiquidity, pp. 7, 11, 23-25)
- Status: NEW. No bond liquidity factor exists in the known list.
- Source says: realized Amihud = realized absolute variation over volume (p. 7):
  $$\mathcal{A}_t=\frac{\sum_{i=1}^{I}|r_{t,i}|}{\nu_t}$$
  The high-low Amihud (p. 11):
  $$\mathcal{A}^{HL}_t=\frac{\sqrt{\tfrac{1}{4\log 2}}\,(p^H_t-p^L_t)}{\nu_t}$$
  The paper splits illiquidity into expected illiquidity (MEM-HAR conditional mean) and unexpected illiquidity (residual) (pp. 23-24).
  Intuition: price moves per dollar traded measure price impact. Intraday data measure it with less noise than one daily return.
- Definition (we propose for bonds):
  - Per bond-day, take $r_{t,i}$ as log price changes between consecutive TRACE trades, filtered for size above $100k. Take $\nu_t$ as dollar par volume.
  - Average over 21 days to get $\text{ILLIQ}_{b,t}$.
  - Cross-sectional signal: z-score of $\log\text{ILLIQ}$ within rating x duration peers. Long the illiquid bonds, DTS-neutral (illiquidity premium).
  - Time-series signal: aggregate HY unexpected illiquidity $\hat\varepsilon_t$ from a HAR model on the market-average $\log\mathcal{A}$. Expect a negative contemporaneous return and a positive return after the shock.
- Data needed: TRACE trade-level prices and volumes. We have them.
- Evidence (source, SPY 2006-2018, Table 7, p. 24):
  - Realized Amihud on excess return: coefficient -3.67 daily (1% level).
  - Unexpected illiquidity: -37.79 monthly (1% level), R² 0.16.
  - Expected illiquidity: +3.63 monthly (10% level).
  - All coefficients are x100.
  - No bond evidence.
- HY applicability: high. HY bonds trade rarely, so the illiquidity premium is likely larger. The realized measure also beats the daily Amihud in sparse-trade simulations (pp. 10-13).
- Fit to our signals: new signal. It also refines the "size liquidity" step of the framework and the liquidity cells of the conformal coverage test.
- Test: monthly 2005-2024, quintile sort on peer-relative $\log\text{ILLIQ}$. Pass if the top-minus-bottom DTS-neutral excess return after costs is positive with t > 2. It must stay positive in at least 3 of the 4 cycles, with the 2008 drawdown reported.

### F8. Liquidity change and liquidity beta for bonds (source: Designing a Liquidity based Toolkit, pp. 7-8, 14, 20-21)
- Status: NEW (companion to F7).
- Source says: there are 4 liquidity dimensions (p. 14):
  - Level: long illiquid stocks.
  - Volatility of liquidity: long volatile liquidity.
  - Liquidity beta from a modified Pastor-Stambaugh model: long bad hedges.
  - Liquidity change: long improving liquidity. It is a continuation signal with fast decay and weekly rebalance.

  The final strategy weights level, volatility and beta equally. It adds liquidity change, neutralises size, and smooths the signal to an 80% correlation target (p. 20). The bid-ask spread uses the Corwin-Schultz high-low estimator (p. 12, App. A).
- Definition (we propose):
  $$\Delta L_{b,t}=-\left(\log\text{ILLIQ}_{b,t}-\log\text{ILLIQ}_{b,t-63}\right)$$
  $$\beta^{L}_b=\text{slope of } r^{ex}_{b,t} \text{ on } \Delta \overline{\log\text{ILLIQ}}^{HY}_t \text{ over 36 months}$$
  Intuition: improving liquidity attracts flow and lifts prices. High liquidity-beta bonds must pay a premium.
- Data needed: TRACE. We have it.
- Evidence (source, European equities):
  - 2008 annual returns: level -11%, volatility -8%, beta -2%, change +15% (p. 21).
  - The other results are in charts, with no numbers in the text.
- HY applicability: medium. Liquidity change may proxy dealer inventory shifts. No bond evidence.
- Fit to our signals: new signal. It also gives a defensive leg against the F7 premium leg.
- Test: weekly sort on $\Delta L$. Pass if the 1-month excess return spread is positive with t > 2 and the factor correlates below 0.3 with F7.

### F9. PCA residual reversal with an Ornstein-Uhlenbeck s-score (source: reversion_long_doc, pp. 4-7, Appendix)
- Status: NEW for bonds. The repo has fallen-angel reversal (FAR) only.
- Source says (Avellaneda and Lee 2009 method, pp. 5-6):
  1. z-score weekly returns over T = 3 or 5 years.
  2. Run an SVD. Keep n PCs (fixed n in {1,2,3,4,6,12}, or n set by variance explained).
  3. Regress each asset's last T' = 13, 26 or 52 weeks of returns on the PCs.
  4. Fit an OU process to the cumulative residual:
  $$dS=\theta(\mu-S)\,dt+\sigma\,dW$$
  5. The signal is the distance from equilibrium, scaled by the equilibrium standard deviation.
  6. Skip assets where the AR(1) slope b falls outside (0,1).
- Definition (we propose for bonds): take weekly bond excess returns over duration-matched Treasuries. Remove 3-5 PCs from the HY panel, then form the cumulative residual $X_{b,t}$. Fit an AR(1), $X_{t+1}=a+bX_t+\eta$, and set $\theta=-\ln b$, $\mu=a/(1-b)$, $\sigma_{eq}=\sigma_\eta/\sqrt{1-b^2}$.
  $$s_{b,t}=\frac{X_{b,t}-\mu_b}{\sigma_{eq,b}}$$
  Trade $-s$, DTS-neutral, with entry and exit bands (hysteresis).
  Intuition: residual price moves away from peers revert, faster when $\theta$ is high.
- Data needed: TRACE prices and G-spreads, Treasury curve. We have them.
- Evidence (source, equities, 2001-2020, net of costs): the best PCA-OU net Sharpe is 0.75 global, 0.77 North America, 0.80 Europe and 1.19 Asia. Standard EWMA reversion reaches 0.34, 0.55, 0.39 and 0.84 (p. 7). Returns are highest in the top decile of market volatility (p. 5, Fig. 4).
- HY applicability: medium. Bond bid-ask costs are high. The source shows reversion works best combined with slow alphas (p. 2), and that suits S1.
- Fit to our signals: extends S1. Use the OU s-score as an entry-timing filter on the S1 fair-value residual.
- Test: weekly 2005-2024, after TRACE-estimated costs. Pass if S1 timed by $s$ beats S1 alone on net IR by at least 0.1 in at least 3 of the 4 cycles.

### F10. Issuer curve basis-momentum (source: jofi.12738, pp. 2, 6, 22-24)
- Status: NEW (transfer from futures).
- Source says: basis-momentum is the 12-month compounded return of the first-nearby contract minus that of the second-nearby (p. 6, eq. 3):
  $$BM_t=\prod_{s=t-11}^{t}(1+R^{T_1}_{s})-\prod_{s=t-11}^{t}(1+R^{T_2}_{s})$$
  It captures curvature and slope change. It reflects supply-demand imbalance when intermediaries cannot clear the market (p. 5).
- Definition (we propose): for issuer $i$ with a short bond $S$ (1-4y) and a long bond $L$ (above 7y), take 12-month compounded excess returns:
  $$BM^{credit}_{i,t}=\prod(1+r^{ex}_{S})-\prod(1+r^{ex}_{L})$$
  - Signal A: go long the issuer (short bond) when $BM$ is high.
  - Signal B: run an issuer curve steepener when $BM$ is high.

  Intuition: persistent outperformance of the short end shows informed or constrained demand at that tenor.
- Data needed: TRACE. Many HY issuers have only one or two bonds, which limits the sample.
- Evidence (source): 21 commodities since 1959, high-minus-low nearby return 18.38% a year (t = 6.73), Sharpe about 0.9 (p. 2). Bond indexes 1991-2009: 2.69% a year (t = 2.23), Sharpe 0.52 (p. 24, Table VI Panel C). No credit test.
- HY applicability: low to medium. The issuer coverage is thin.
- Fit to our signals: extends S4 (capital structure relative value) along the maturity axis.
- Test: on issuers with at least 2 bonds, monthly sort. Pass if the 3-month next-period issuer excess return spread is positive with t > 2.

### F11. Owner cash flow to debt (maintenance-capex-adjusted) (source: Value Anatomy, pp. 11-13)
- Status: variant of fundamental leverage and coverage (inputs to S1 and S3, framework F2 normalise).
- Source says: Owner Earnings = net income + D&A + deferred taxes + other non-cash items − ΔNWC − maintenance capex − maintenance acquisitions − preferred dividends. Interest is excluded (pp. 12-13). Maintenance capex = min(capex_t, 3-year average capex) (p. 12). Acquisitions get the same treatment. R&D counts as growth and stays in.
- Definition (we propose for credit): add interest back to keep the cash flow available to all capital, then deduct only maintenance capex.
  $$\text{OCF}^{debt}_{i,t}=\text{CFO}_{i,t}+\text{Int}_{i,t}(1-\tau)-\min\!\left(\text{Capex}_{i,t},\overline{\text{Capex}}_{i,t-2:t}\right)$$
  $$\text{Signal}_{i,t}=\frac{\text{OCF}^{debt}_{i,t}}{\text{Total debt}_{i,t}}\ \text{(peer z-score)}$$
  Use the LTM point-in-time Compustat, lagged to `available_at`.
  Intuition: growth capex is optional in a downturn, so creditors should not count it as a fixed drain.
- Data needed: Compustat cash flow items (oancf, xint, capx, aqc). We have them.
- Evidence (source): equities 1997-2018. The text says Owner Earnings-to-price has higher Sharpe and lower turnover than earnings-to-price in North America, Europe and Asia (pp. 22-23). The numbers sit in charts only. Note the conflict: the DB credit note (Factors/ebec8f2e, p. 11) found plain FCF/debt "inconclusive" for CDS.
- HY applicability: medium. HY issuers in capex-heavy sectors (energy, telecom, cable) separate maintenance from growth capex poorly. The proxy may help most there.
- Fit to our signals: an S1 fair spread input and an S3 forward input. Test it as an added regressor in the fair spread model.
- Test: add the signal to the S1 fair spread regression. Pass if out-of-sample spread R² rises by at least 0.01 and the monotone sign test (higher OCF lowers the fair spread) holds in every rating cell.

### F12. DB CDS factor variants: exact definitions (source: Factors/ebec8f2e, pp. 5-29. Research October 2022, p. 45)
- Status: variant of "Deutsche Bank: CDS value, low risk, momentum after DTS". Report only what is new against that card.
- Source says (new details):
  1. Residual momentum, sign-averaged (p. 22).
     - Residual: $e^i_{t,h}=r^i_{t-h,t}-\beta^i_t r^{mkt}_{t-h,t}$, with no alpha removed. Beta comes from 3-day non-overlapping returns over 5 years, with half-lives of 1 year (diagonal) and 3 years (off-diagonal) (pp. 10, 19).
     - Raw signal: the average of $\text{sign}(e_{t,h})$ for $h\in[126,252]$ days.
     - Hysteresis: keep the old signal if $|\bar s|<1/3$.
     - Final signal: $s=\tilde s/\sigma(\hat s)$.
  2. Market momentum for index timing (p. 22): the average sign of CDX IG+HY cumulative returns over $h\in[21,252]$, with the same hysteresis and dispersion scaling. The position is long in 76% of the sample, and the signal turns short in drawdowns (p. 23).
  3. Value as a time-series DTD fit (pp. 16-17). Over the last 90 days, regress $\log CDS^i_t=\alpha^i+\beta^i\log DTD^i_t$. The signal is $10^{\hat l}-CDS$. Standardise it within DTS quintiles. The RAMIC is negative at 1M and rises out to 1Y (p. 17).
  4. DTS-quintile standardisation, $\hat s=(s-\bar s_k)/(s^{max}_k-s^{min}_k)$, in place of sector neutralisation (p. 9).
  5. Cost control by transfer coefficient (TC) (p. 26). If the TC of target vs traded weights exceeds 0.95, spend 60% of the cost budget on the largest DTS mismatches.
  6. The RAMIC metric weights IC by DTS (p. 8).
- Evidence (source, US CDX IG+HY constituents 2004-2018):
  - Residual momentum sign-dependency κ is about 0.10-0.15 for all windows, so it is slow (p. 21, Fig. 36). Market κ reaches 0.55 (p. 21, Fig. 35).
  - Company-specific sub-portfolio Sharpe after costs: 0.67 with TC control, 0.55 without. Turnover is 1.29 vs 1.98 (p. 27, Fig. 47).
  - Absolute return portfolio Sharpe 0.88, market correlation -0.01 (p. 28, Fig. 49).
  - Overlay on an IG+HY cash index: Sharpe 1.74 vs 1.46 (p. 29, Fig. 50).
  - Low duration Sharpe 0.72 (DV01 weights). The source restricts it to IG because of HY jump-to-default risk and the illiquid HY tenors (p. 14, Fig. 17).
- HY applicability:
  - High for residual momentum and the market momentum timing. The source says HY shows momentum on residuals too (p. 21).
  - Low for low duration (the source excludes HY).
- Fit to our signals: market momentum gives a third S7 replacement candidate (HY beta timing). The DTS-quintile standardisation and TC cost control apply to all of S1-S6.
- Test: build market momentum on the TRACE HY excess return index, 2004-2024. Pass if the time-series long/short HY beta beats buy-and-hold on Sharpe, after a 0.5% index cost, in at least 3 of the 4 cycles.

## Top 3

1. F7 realized Amihud bond illiquidity (level and shock). It is fully buildable from TRACE, which we hold. It fills a factor gap in the known list. HY sparse trading makes the precise realized measure most useful.
2. F1 real-yield shock regime. It is the best direct S7 replacement. It uses free data and comes with US HY evidence (correlation -0.6, -65bp median in 6 sell-offs). It also gives a falsifiable split: a real-yield move against a breakeven move.
3. F3 rating x tenor cell percentile with the BB/BBB ratio. It gives the curve and quality allocation that S1 lacks. It builds from TRACE cells, but it needs a spread-implied rating after Feb 2017.
