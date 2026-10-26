# Folder G: Work_Quant systematic research. Credit factor scan

Scope: 71 list entries under `/home/ak/Documents/Quant Credit/Work_Quant (1)/`. Page numbers are PDF pages. For `.md` files, page numbers are the "Page N" footers in the md.

Duplicates (same note, read once):
- `244e95d4_..._604 (1).pdf` = `DB Quantcraft_ Taming_Bulls and Bears (1).pdf`
- `92fb088c_..._604 (1).pdf` = `commodity curve presentation (1).pdf`
- `Persistent Patterns in Short Term (1).pdf` = `Persistent patterns in short term returns (1).pdf`
- `JPM_Exchange_Rate_Model__2003-03-20_166934 (1).pdf` = `JPM_JPMorgan_s_FX_Model__2000-04-03_329848 (1).pdf`
- `The Intraday Lab Catching the Beat (1).pdf` = `QuantCraft/11ceb80a_... (1).md` = `QuantCraft/11ceb80a_... (1).pdf`
- `The Intraday Lab Trading the Clock (1).pdf` = `QuantCraft/fc49bb54_... (1).md` = `QuantCraft/fc49bb54_... (1).pdf`
- Each other QuantCraft `.md` is the text of the `.pdf` next to it.

## Triage table

| File | Title, bank or authors, year | Topic | Transfers to HY credit (yes/no) | Why |
|---|---|---|---|---|
| 1574b3c6_68dd_11eb_8fc9_3e217c25b0c2_604 (1).pdf | Macro Credit Trades: Spreads vs Rates in the Liquid Space, DB (Jezek), Mar 2021 | CDS index vs OIS rate correlation, credit options trades | yes (medium) | Spread-rate correlation by horizon and regime. Conditioning variable for HY timing. |
| 15_TwoScaleRV (1).pdf | Two-Scale Realized Volatility, Tauchen lecture notes, 2017 | HF realized volatility under noise | no | Intraday econometrics. TRACE is too sparse. |
| 1707.03003 (1).pdf | tick: a Python library for statistical learning, Bacry et al., 2018 | Hawkes process software | no | Software paper. No factor. |
| 1807.08278 (3).pdf | Liquidity in Competitive Dealer Markets, Bank, Ekren, Muhle-Karbe, 2018 | Dealer inventory theory | no | Theory of intermediation. No signal. |
| 200521pap (1).pdf | A Review of Backtesting and Backtesting Procedures, Campbell, Fed FEDS 2005-21 | VaR backtests (Kupiec, Christoffersen) | yes (method only) | Coverage tests for our conformal bands and event model. Not a factor. |
| 244e95d4_a950_4149_9a1d_461ca0b1c810_604 (1).pdf | DB Quantcraft: Taming Bulls and Bears, DB (Anand), Feb 2021 | Capital allocation, smart beta plus defensive | no | Portfolio construction for equity overlay. Duplicate of row below. |
| 5de4d6ff_7cf2_4fdf_8edb_d55fde385a63_604 (1).pdf | Global Leveraged Finance Weekly, DB (Nicol), 5 Mar 2021 | HY spreads, flows, supply, rate shocks, valuation by cell | yes (high) | HY-specific. Reinvestment cash flow, rate-shock response, cell percentile valuation. |
| 72d00fea_7cfe_11eb_a3f3_29224d3fd3be_604 (1).pdf | CEEMEA Macro and Strategy Weekly, DB (Wietoska), Mar 2021 | EM macro commentary | no | Regional macro. No systematic rule. |
| 92fb088c_d471_4632_a3a6_c68acb48e00b_604 (1).pdf | Dissecting the Commodity Curve, DB QIS (Gonzalez), Jul 2021 | Commodity curve PCA | no (see 342205) | Same idea as Speeding Into The Curve. Read that one. |
| 9b070dd5_8bd1_40c7_ace2_768097379409_604 (1).pdf | Reversion: new horizons, DB Quantcraft (Tomasi), Mar 2021 | PCA plus OU mean reversion in equities | yes (medium) | Residual spread reversion for bonds. |
| CASTELLOBRANCO_JONATHAS_01461378 (1).pdf | ETF Market Making, Castello Branco, Imperial MSc thesis, 2018 | ETF market making | no | Microstructure. No HY selection signal. |
| CTA trading model paper 1 (1).pdf | Real-Time Trading Models and FX Statistical Properties, Gencay et al., 2000 | Intraday FX trading models | no | HF FX. |
| CTA trading model paper 2 (1).pdf | High-frequency Trading (pairs), Stanford MS&E 445 students, 2010 | Statistical pairs trading | no | Student project, HF equities. |
| CTA trading model paper 3 (1).pdf | Improving Accuracy of HFT Forecasts, Aldridge, 2009 | HF forecasting slides | no | HF. |
| DB Quantcraft_ Taming_Bulls and Bears (1).pdf | Same as 244e95d4 | Same | no | Duplicate. |
| Emergence of statistically validated financial intraday lead lag relationships (1).pdf | Curme, Tumminello, Mantegna, Stanley, Kenett, Quant Finance 2015 | Intraday equity lead-lag networks | no | Intraday. Equity-to-bond lead-lag is already in EMC. |
| Gatheral60 - Oomen (3).pdf | Internalisation by electronic FX spot dealers, Oomen, DB, 2017 | FX dealer internalisation | no | FX microstructure. |
| Hasbrouck (3).pdf | High-Frequency Quoting, Hasbrouck, slides | HF quoting measurement | no | HF equities. |
| JPM_24_hour_party_people_2016-01-27_1925804 (2).pdf | 24 hour party people redux, JPM NA FI Strategy, Jan 2016 | Treasury futures liquidity | no | Rates liquidity. |
| JPM_A_new_fair_value_mod_2008-09-06_470005 (1).pdf | A new fair-value model for G10 currencies, JPM (de Kock), Sep 2008 | FX fair value regression | yes (low) | Model behind the 2009 note. Index fair value idea taken from 2009 note. |
| JPM_A_season_for_everyth_2017-07-03_2380131 (1).pdf | A season for everything, JPM Australia FI, Jul 2017 | Swap spread seasonality, RV model, issuance flow | yes (medium) | "Smart seasonal" rule: seasonal drift gated by a z-score. |
| JPM_Drivers_of_price_imp_2017-01-13_2227901 (3).pdf | Drivers of price impact and hidden liquidity, JPM NA FI, Jan 2017 | Treasury price impact | no | Treasury microstructure. |
| JPM_Exchange_Rate_Model__2003-03-20_166934 (1).pdf | JPM EM Real Exchange Rate Model: Theory and Econometrics, Giacomelli, 2000 | EM FX equilibrium model | no | FX valuation. |
| JPM_Exchange_Rate_Model__2003-03-20_166938 (1).pdf | Market brief: JPM EM Real Exchange Rate Model, Giacomelli, May 2000 | Same model, short brief | no | FX. |
| JPM_FX_alpha_strategies__2009-11-24_348456 (1).pdf | FX alpha strategies in 2010, JPM (Normand), Nov 2009 | FX carry, momentum, value review | no | FX performance summary. No new definition. |
| JPM_FX_at_the_crossroads_2000-04-01_135339 (1).pdf | FX at the Crossroads of an e-Integrated World, JPM conference, Apr 2000 | E-trading in FX (273 p) | no | Conference pack. Triaged by contents only. |
| JPM_Investment_Strategie_2002-04-12_78445 (1).pdf | A Framework for Long-term Currency Valuation, JPM Investment Strategies No. 6, 2002 | FX fundamental valuation | no | FX. Same family as 2009 note. |
| JPM_Investment_Strategie_2009-04-29_287192 (1).pdf | Trading and Hedging Long-Term FX Fundamentals, JPM (de Kock), Apr 2009 | Fair-value misalignment vs carry rule | yes (medium) | Misalignment-net-of-carry rule and out-of-sample protocol for an HY index fair value. |
| JPM_Investment_Strategie_2012-02-13_784342 (1).pdf | Trading Rich/Cheap Signals in EM Sovereigns and Corporates, JPM (Osband), Feb 2012 | Within-issuer bond curve residual | yes (high) | Direct bond-selection signal. Credit, USD bonds. |
| JPM_JPMorgan_s_FX_Model__2000-04-03_329848 (1).pdf | Same as 166934 | Same | no | Duplicate. |
| JPM_Market_neutral_carry_2018-10-04_2790721 (1).pdf | Market-neutral carry strategies, JPM QDS (Tzotchev, Kolanovic), Oct 2018 | Factor-hedged carry across assets, incl. CDS indices | yes (high) | Carry with market factors hedged out. Has a credit section. |
| JPM_Momentum_Strategies__2015-04-15_1681565 (1).pdf | Momentum Strategies Across Asset Classes, JPM (Kolanovic, Wei), Apr 2015 | Trend following, seasonality (188 p) | yes (medium) | Credit index trend rule (p41). HY seasonality references (p87). |
| JPM_Sweating_the_small_s_2016-05-05_2017358 (1).pdf | Sweating the small stuff: Treasury RV, JPM NA FI, May 2016 | Treasury curve RV | no | Rates RV. Curve-residual idea covered by the 2012 note. |
| JPM_Systematic_Strategie_2013-12-11_1277971 (2).pdf | Systematic Strategies Across Asset Classes, JPM (Kolanovic, Wei), Dec 2013 | Risk premia taxonomy (205 p) | yes (low) | Credit carry-to-risk via CDS indices (p29). No new credit definition beyond known carry. |
| JPM_Systematic_fixed_inc_2015-04-13_1679171 (1).pdf | Systematic fixed income trading strategies, JPM (Inkinen, Bassi), Apr 2015 | Duration signals: PMI, revision ratio, momentum, carry-to-risk | yes (medium) | Macro momentum signals for HY index timing. S7 replacement candidates. |
| JPM__Implied_Weights_in__2011-05-25_600988 (1).pdf | Implied Weights in Yield Curve RV Trades, JPM (Ramaswamy et al.), May 2011 | Swap butterfly weights | no | Rates curve trades. |
| OFRwp-19_04_cross-asset-market-order-flow-liquidity-and-price-discovery (1).pdf | Cross-Asset Market Order Flow, Liquidity, and Price Discovery, OFR WP 19-04, 2019 | Treasury and equity futures order flow | no | Needs order flow data. Not HY bonds. |
| Oomen_Execution aggregator_2016 (3).pdf | Execution in an aggregator, Oomen, Quant Finance 2016 | FX execution | no | Execution. |
| Persistent Patterns in Short Term (1).pdf | Persistent Patterns in Short Term Returns, DB Quantcraft (Natividade, Anand, Gonzalez), May 2019 | 3-20 day time-series reversal and momentum, includes 4 credit indices | yes (low) | Short-horizon index reversal. Weak fit to monthly HY selection. |
| Persistent patterns in short term returns (1).pdf | Same as above | Same | yes (low) | Duplicate. |
| Presentation Modern Portfolio Construction Meets FX (1).pdf | Modern Portfolio Construction Meets FX, DB (Anand et al.), 2018 | FX PCA drivers, portfolio construction | no | FX-specific factor model. |
| Quantcraft _ Playing Defense 2.0_ ... (1).pdf | Playing Defense 2.0, DB Quantcraft (Anand, Natividade, Gonzalez), Apr 2019 | Tail risk hedging, efficiency parity | no | Equity options hedges. Only CDX IG CAGR stat (p2). |
| RSI A selective study across asset classes (1).pdf | DB Global Sentiment Indicator: A selective study across asset classes, DB, Jun 2019 | Cross-asset risk sentiment composite | yes (medium) | Risk-appetite regime for HY timing. Convex response. |
| Robe Roberts ag paper who does what ... (1).pdf | Who Holds Positions in Agricultural Futures Markets, Robe and Roberts, CFTC, 2019 | Ag futures positioning | no | Positioning data, commodity. |
| SG FX Timing Indicator Strategy (1).pdf | FX timing indicators, SG (Ravagli, Huang), Apr 2010 | Trend from derivatives of smoothed series | yes (low) | Variant trend rule for HY index. |
| Selection of balanced portfolios to track ... (1).pdf | Tafin Djoko and Tille, Quant Finance 2015 | Balanced sampling for index tracking | no | Index replication sampling. Possible use for HY universe sampling only. |
| The Intraday Lab Catching the Beat (1).pdf | The Intraday Lab: Catching the Beat, DB Quantcraft (Zlicar), Dec 2020 | Intraday futures patterns | no | Intraday. |
| The Intraday Lab Trading the Clock (1).pdf | The Intraday Lab: Trading the Clock, DB Quantcraft (Zlicar), Jun 2020 | Time-of-day patterns | no | Intraday. |
| The_Future_of_Payments_-_Part_III__Digital_Currenc (1).pdf | The Future of Payments Part III: Digital Currencies, DB Research, Jan 2020 | CBDC policy | no | Not a signal. |
| Todorov_Tauchen-2008b (3).pdf | Activity Signature Functions for HF Data, Todorov and Tauchen, 2008 | Jump activity estimation | no | HF econometrics. |
| Ultra high frequency lead lag relationship and information arrival (1).pdf | Dao, McGroarty, Urquhart, Quant Finance 2018 | UHF lead-lag | no | HF. |
| [Foucault_Michel,_Kadan]_Limit_Order_Book_As_A_Mar... (3).pdf | Limit Order Book as a Market for Liquidity, Foucault, Kadan, Kandel | LOB theory | no | Theory. HY trades OTC. |
| commodity curve presentation (1).pdf | Same as 92fb088c | Same | no | Duplicate. |
| e2013_7 (1).pdf | Trading duration, volume and volatility: a vector MEM, Xu, Cardiff WP E2013/7 | Intraday duration models | no | HF econometrics. |
| fx quant model db (1).pdf | FX Cookbook, DB Quantcraft (Anand), Jan 2019 | FX carry, value, momentum recipes | no | FX-specific. Ideas covered by carry and momentum cards. |
| reinforcementlearninginalgorithmicexecution-...(3).pdf | Active learning in trading algorithms, JPM (Fellah), QuantCon 2016 | RL execution | no | Execution. |
| the-october-2016-sterling-flash-episode (3).pdf | The October 2016 sterling flash episode, BoE SWP 687, 2017 | FX flash crash liquidity | no | Event study in FX. |
| time of day strategy (1).pdf | Modelling of intraday pulse, DB (Zlicar), Apr 2020 | Time-of-day strategy | no | Intraday. |
| QuantCraft/11ceb80a_..._604 (1).md | Same as Catching the Beat | Intraday | no | Duplicate. |
| QuantCraft/11ceb80a_..._604 (1).pdf | Same as Catching the Beat | Intraday | no | Duplicate. |
| QuantCraft/21f659cb_..._604 (1).md | News-based alphas for cash equity portfolios, DB Quantcraft (Tomasi), Oct 2022 | RavenPack and MarketPsych equity news signals | no | Source finds negative net returns from fast alpha decay. HY costs are higher. |
| QuantCraft/21f659cb_..._604 (1).pdf | Same as above | Same | no | Duplicate of md. |
| QuantCraft/Catching the sentiment waves (1).md | Catching the sentiment waves, DB Quantcraft (Zhang), Nov 2022 | Media sentiment factors, incl. a Credit Spread sentiment factor | yes (low) | Credit sentiment factor on CDX HY constituents. We lack the vendor data. |
| QuantCraft/Catching the sentiment waves (1).pdf | Same as above | Same | yes (low) | Duplicate of md. |
| QuantCraft/GDPBD00000313269 (1).md | Protect, Diversify or Track Your Core, DB Quantcraft (Anand et al.), Aug 2017 | Asset-level covariance portfolio construction | no | Portfolio construction. No credit signal. |
| QuantCraft/GDPBD00000342205 (1).md | Speeding Into The Curve, DB Quantcraft (Gonzalez), Oct 2021 | Commodity curve momentum and spillover | yes (medium) | Slope momentum and slope-to-level spillover transfer to the HY quality curve. |
| QuantCraft/GDPBD00000342205 (1).pdf | Same as above | Same | yes (medium) | Duplicate of md. |
| QuantCraft/Gearing into Reverse (1).md | Gearing into Reverse, DB Quantcraft (Natividade), Oct 2013 | Intraday FX reversal | no | Intraday FX. |
| QuantCraft/Gearing into Reverse (1).pdf | Same as above | Same | no | Duplicate of md. |
| QuantCraft/fc49bb54_..._604 (1).md | Same as Trading the Clock | Intraday | no | Duplicate. |
| QuantCraft/fc49bb54_..._604 (1).pdf | Same as Trading the Clock | Intraday | no | Duplicate. |

Counts: 71 entries triaged. 20 entries marked yes. These 20 entries are 17 distinct notes. One of the 17 gives a method only (Campbell 2005).

## Factors found

### F1. Within-issuer curve residual (source: JPM_Investment_Strategie_2012-02-13_784342 (1).pdf, p6, p8-p10, p13, p21-p22)
- Status: variant of ESP (excess spread to peers). ESP compares across issuers. This compares bonds of one issuer to that issuer's own fitted curve. Extends S4.
- Original asset class and definition: EM USD sovereign and corporate bonds. Fit a smooth issuer curve with a "forward shock" model. Instantaneous forward spread:
  $$f(s)=a_0+\sum_i a_i e^{-\lambda_i s}$$
  Fitted spread to maturity $T$:
  $$\hat S(T)=a_0+\sum_i a_i\,\frac{1-e^{-\lambda_i T}}{\lambda_i T}$$
  The base case fixes one factor with $\lambda=0.4$ (expected life 2.5 years). The fit is then a linear regression on $x(T)=(1-e^{-0.4T})/(0.4T)$ (p22). The signal is the residual:
  $$e_{b,t}=S_{b,t}-\hat S_{i(b),t}(T_b)$$
  Trade when $|e_{b,t}|\ge 30$ bp and $|e_{b,t}|\ge 1$ standard error of the fit (p8). Go long the cheap bond against the curve point. Go short the rich bond. Hold one month.
  Intuition: one issuer has one default process, so a bond far off its own curve reflects a technical, and technicals fade.
- Credit translation: for each US HY issuer with at least 5 bullet bonds of the same seniority, fit $\hat S(T)$ on G-spread versus maturity each month. Compute $e_{b,t}$ and its z-score against the fit standard error. Exclude callable bonds or use yield-to-worst maturity. Most HY bonds are callable, so the universe shrinks. A variant: fit on spread-to-worst with workout date as $T$, and add coupon and price controls (known coupon effect).
- Data needed: TRACE prices and G-spreads, bond terms (maturity, call schedule, seniority). All in repo.
- Evidence in the source (EM USD bonds, not US HY): regression slope of next-month residual on this-month residual is 0.86, $R^2=0.71$ (p6). Base case Nov 2006 to Oct 2011: 4.06% annual return, 66% success rate, information ratio 1.20 before costs (p9). With 20 bp bid-offer and a 40 bp, 1.5 standard error threshold: 57.43% success, 2.90% return, IR 0.81 (p13). Cheap leg IR 1.62 versus rich leg IR 0.30 (p10). The strategy lost in Sep-Nov 2008 (p10).
- HY applicability: high. The signal is pure bond selection inside an issuer. It is neutral to the issuer view, so it stacks on S1 to S3. The risk is the call-option distortion in HY and few bullet bonds per issuer.
- Fit to our signals: extends S4 (capital structure RV) to the same-seniority curve. Gives the "which bond" choice after S1 picks the issuer.
- Test: monthly, US HY issuers with at least 4 bonds of one seniority. Signal $-e_{b,t}$ z-score. Horizon 1 month. Metric: rank IC of signal versus next-month excess return relative to the issuer curve, net of half the TRACE effective spread. Pass: mean IC above 0.05 and positive net IC in at least 3 of the 4 cycles (2008, 2015, 2020, 2022).

### F2. PCA residual with Ornstein-Uhlenbeck s-score (source: 9b070dd5_8bd1_40c7_ace2_768097379409_604 (1).pdf, p3-p5)
- Status: NEW. The known list has no short-term reversal factor for bonds.
- Original asset class and definition: global equities (Avellaneda and Lee 2009). Step 1: run PCA on standardised returns. Regress each return on the first $k$ PCs to get the residual $\epsilon_{i,t}$. Step 2: fit an OU process to the cumulative residual $X_{i,t}=\sum \epsilon_{i}$:
  $$dX_{i,t}=\kappa_i(m_i-X_{i,t})\,dt+\sigma_i\,dW_{i,t}$$
  Signal (s-score):
  $$s_{i,t}=\frac{X_{i,t}-m_i}{\sigma_i/\sqrt{2\kappa_i}}$$
  Short when $s$ is high. Long when $s$ is low.
  Intuition: after the common factors are removed, the residual price drifts back to its own mean.
- Credit translation: use weekly bond excess returns from TRACE. Remove 3 to 6 PCs (these load on level, DTS, rating and sector). Fit OU on each bond's cumulative residual over a 26 to 52 week window. Use the s-score as a contrarian signal. Keep bonds with half-life $\ln 2/\kappa$ under 8 weeks.
- Data needed: TRACE prices, Treasury curve for excess returns. In repo.
- Evidence in the source (equities, not credit): best net Sharpe ratio 0.75 global, 0.77 North America, 0.80 Europe, 1.19 Asia. The "standard" EWMA reversal gave 0.34, 0.55, 0.39 and 0.84 (p5). Costs 4 bp per trade, 1 to 2 day lag (p4).
- HY applicability: medium. TRACE bid-ask bounce creates false reversal. The test must use trade prices at least one day after the signal. HY costs are 10 to 50 times the equity cost assumed.
- Fit to our signals: new signal. It is a short-horizon overlay for entry timing of S1 to S3 trades.
- Test: weekly, bonds with at least 10 trades per week. Signal $-s_{i,t}$. Horizon 2 to 4 weeks, skip one day. Metric: rank IC and net return after half the effective spread. Pass: net IC above 0.03 with Newey-West t above 2, in at least 3 of 4 cycles.

### F3. Market-neutral (factor-hedged) credit carry (source: JPM_Market_neutral_carry_2018-10-04_2790721 (1).pdf, p4-p5, p16-p18, p40)
- Status: variant of carry (Israel, Palhares, Richardson 2018) and of roll-down.
- Original asset class and definition: CDS indices (iTraxx Main 3/5/10y, Crossover, CDX IG 3/5/10y, CDX HY 5y). Daily carry of sold protection:
  $$c_{i,t}=\frac{\text{Coupon}_i}{365}-CD_{i,t}\left(S^{\text{impl}}_{i,t}(T-1)-S_{i,t}(T)\right)$$
  Return $= c_{i,t}-CD_{i,t}\,\Delta_{i,t+1}$, where $\Delta$ is the realised spread minus the rolled-down implied spread. Model $\Delta=B f+a+\varepsilon$ with $m$ factors. Choose weights $w$ to maximise $w^\top c$ subject to $B^\top(CD\circ w)=0$ (no factor exposure) and a risk target (p4-p5, p17).
  Intuition: if the factor exposure is zero, the expected return is the carry, without the crash beta.
- Credit translation: for each US HY bond, carry $c_b=\text{OAS}_b/12+D_b\cdot\text{rolldown}_b$ per month, with roll-down from the issuer curve of F1 or the rating-sector curve. Estimate 3 to 5 PCs of bond spread changes. Solve the constrained optimisation within rating buckets. The portfolio is long high carry-per-risk bonds and short low ones, with zero PC exposure.
- Data needed: TRACE, G-spreads, Treasury curve. In repo.
- Evidence in the source (CDS indices, partly credit): comprehensive solution 7.29% return, 8.44% volatility, Sharpe 0.86 after costs, max drawdown 16.25% (Table 12, p18). Carry income fell after the GFC (p18).
- HY applicability: medium-high. Raw HY carry is mostly beta. Hedging the beta isolates the part that pays. Short legs in cash HY are costly. A long-only version can hedge with CDX HY or HYG.
- Fit to our signals: new signal, or an overlay that removes beta from S1. It also supports DTS-neutral legs in OneScore.
- Test: monthly. Compare raw carry rank and factor-hedged carry within rating buckets. Horizon 1 month. Metric: net Sharpe ratio and correlation with the HY index. Pass: hedged version Sharpe above 0.4 net, index correlation below 0.3, and a better Sharpe than raw carry in 2008 and 2020.

### F4. HY index time-series trend (source: JPM_Momentum_Strategies__2015-04-15_1681565 (1).pdf, p41, p120. Variant from SG FX Timing Indicator Strategy (1).pdf, p1)
- Status: NEW. The known momentum factors are cross-sectional bond or equity momentum. This is time-series timing of the index.
- Original asset class and definition: iTraxx Crossover 5y excess return index. Short average STA = 5-day MA, long average LTA = 50-day MA of the index level. Each day: if $\text{STA}_t\ge\text{LTA}_t$, raise long exposure by 0.25, capped at 1. Else raise short exposure by 0.25, capped at 1:
  $$x_t=\text{clip}\left(x_{t-1}+0.25\,\text{sign}(\text{STA}_t-\text{LTA}_t),-1,1\right)$$
  Intuition: credit spreads trend because default news arrives slowly, and the step size cuts turnover on false signals.
  SG variant: smooth the series with a moving average, then trade on the sign of its first and second derivatives (velocity and acceleration).
- Credit translation: build a daily US HY excess return index from TRACE (or use HYG total return minus Treasury return). Apply the rule to set the HY beta budget of the book. Use a weekly step for cash HY to cut costs.
- Data needed: TRACE or ETF price, Treasury curve. In repo or public.
- Evidence in the source (European crossover CDS index, credit): live from Jan 2012 to Mar 2015, 6.2% annual return, Sharpe 1.0, max drawdown -7.4%. During Aug 2007 to Mar 2009, the strategy had 6.2% return and Sharpe 1.0. The index had -8.8% and Sharpe -0.8 (p41).
- HY applicability: medium. The rule times the index, not bonds. Cash HY cannot switch daily at low cost. The rule fits a beta overlay with CDX HY or ETFs.
- Fit to our signals: S7 replacement candidate (macro tilt), as a beta scaler. Not a selection signal.
- Test: weekly rebalance, 2000 to 2024. Signal $x_t$ on HY excess return index. Horizon 1 week. Metric: Sharpe of $x_t\cdot r_{t+1}$ net of 0.5 bp per 0.25 step (CDX cost proxy). Pass: Sharpe above 0.3 net and drawdown smaller than the index in 2008 and 2020.

### F5. HY index fair-value misalignment net of carry (source: JPM_Investment_Strategie_2009-04-29_287192 (1).pdf, p1-p3. Model from JPM_A_new_fair_value_mod_2008-09-06_470005 (1).pdf)
- Status: NEW at index level. S1 is a bond-level fair value. This is an index or rating-cell fair value used for timing.
- Original asset class and definition: G10 FX. Estimate a fair value $e^*_t$ from fundamentals. Misalignment $m_t=100(\ln e_t-\ln e^*_t)$. Trade only if the misalignment exceeds the carry cost by a threshold $\tau$:
  $$\text{position}_t=\begin{cases}+1 & -m_t-\text{carry}_t>\tau\\-1 & m_t+\text{carry}_t>\tau\\0 & \text{else}\end{cases}$$
  Re-estimate the model each quarter with only past data. Lag the fair value one quarter because the macro data arrive with a lag (p2).
  Intuition: valuation gaps close slowly, so the gap must beat the cost of waiting.
- Credit translation: regress the HY index OAS (or each rating cell) on fundamentals available at the decision date: trailing default rate, Senior Loan Officer survey, ISM, leverage of HY issuers from Compustat, VIX. Misalignment $m_t=\text{OAS}_t-\widehat{\text{OAS}}_t$. In credit the carry favours the long side. So the short rule needs $-m_t>\text{carry}_t+\tau$, and the long rule needs $m_t>\tau$. Use expanding-window estimation and `available_at` lags.
- Data needed: macro series, Compustat point-in-time, index OAS (from TRACE aggregate). In repo.
- Evidence in the source (FX, not credit): misalignments predict moves over 6 to 18 months. About 25% of the gap closes in 3 quarters and about 50% in 18 months. Misalignments explain only 15% to 16% of 18-month moves (p2). With a 10% threshold, the rule beat carry by about 3% over 6, 12 and 18 months, 2004 to 2008 (p3). Short sample.
- HY applicability: medium-high. The structure fits HY spreads, which mean-revert to a macro anchor. The risk is a regime break in the anchor (2008).
- Fit to our signals: direct S7 replacement. It extends the methodology fair-spread layer from bond to index.
- Test: quarterly, 1997 to 2024, expanding window. Signal $m_t$. Horizon 6 and 12 months. Metric: out-of-sample slope of future index excess return on $m_t$, and hit rate of the thresholded rule. Pass: positive slope with HAC t above 2, and rule return above buy-and-hold HY in at least 3 of 4 cycles.

### F6. Macro momentum for HY timing: PMI momentum and earnings revision ratio momentum (source: JPM_Systematic_fixed_inc_2015-04-13_1679171 (1).pdf, p2, p7)
- Status: NEW at index level. S3 is issuer-level estimate revision. This aggregates revisions to time the market.
- Original asset class and definition: 10y government bond duration in 10 markets.
  1. PMI momentum: short duration if both local and global manufacturing PMI rose over the past 2 months. Long if both fell. Else neutral.
  2. Earnings revision ratio momentum: short duration if the local and global IBES revision ratio rose over the past 3 months. Long if both fell. Else neutral. Revision ratio $RR_t=(N^{up}_t-N^{down}_t)/(N^{up}_t+N^{down}_t)$.
  $$x_t=\tfrac12\left[\text{sign}(\Delta_2\text{PMI}^{loc}_t)+\text{sign}(\Delta_2\text{PMI}^{glob}_t)\right]\cdot\mathbb 1\{\text{signs agree}\}$$
  Intuition: macro data are serially correlated, and markets absorb them slowly.
- Credit translation: the sign flips for HY. Rising PMI and rising revision ratio mean tighter spreads, so go long HY beta. Build the US revision ratio from our S3 estimate panel for HY issuers, or from IBES for all US equities. Combine the two rules with F5 (value), because momentum and value returns correlate negatively (p2).
- Data needed: ISM PMI (macro series, in repo). Analyst estimate revisions (repo has forward estimates for S3. IBES may be needed for breadth).
- Evidence in the source (government bonds, not credit): since 1998, IR 0.59 for PMI momentum, 0.84 for revision ratio momentum. Combined five-signal IR 1.31 (Exhibit 9, p7). Revision ratio correlates 0.61 to 0.62 with equity momentum and PMI (p2).
- HY applicability: medium. HY spreads link to the cycle more than Treasury yields do. Evidence is from rates, so the sign and size in HY need a test.
- Fit to our signals: S7 replacement candidate. Its index-level version of S3 shares data with S3.
- Test: monthly, 1998 to 2024. Signal $x_t$ (PMI rule, revision rule, and average). Horizon 1 and 3 months. Metric: IR of $x_t$ times HY index excess return. Pass: IR above 0.3 for the combined rule, positive in at least 3 of 4 cycles.

### F7. Cross-asset risk sentiment composite with a convex response (source: RSI A selective study across asset classes (1).pdf, p2-p5. Use as regime in Persistent Patterns in Short Term (1).pdf, p3)
- Status: NEW. The known LSZ credit sentiment uses spread and issuance quality. This composite uses implied volatility and funding stress across assets.
- Original asset class and definition: DB GSI aggregates 9 risk barometers: equity implied vol, rates implied vol, non-financial CDS spreads, FX implied vol, FX vol slope, FX vol skew, financial sector risk (equity and rates view), short-term rate liquidity risk (p2). GSI is on 0 to 100 (100 = risk averse). Signal:
  $$S_t=1-\frac{2\,\text{GSI}_t}{100}\in[-1,1]$$
  Split $S_t$ into 5 buckets and compute mean forward return per bucket, $\bar r(B_i)=E[r_{t+h}\mid S_t\in B_i]$ for $h$ = 1 week, 2 weeks, 1 month (p3). Regimes in the 2019 note: risk seeking, intermediate, and risk averse (above 67).
  Intuition: extreme fear and extreme calm both precede rallies in some assets, so the response is U-shaped, not linear.
- Credit translation: build a US version from public series. Use VIX, MOVE (if licensed), Treasury implied vol proxy from realised vol, the 3m FRA-OIS or commercial paper spread, financial-sector equity drawdown, and IG spread. Take the average percentile rank over a 10-year window. Test HY index excess return by bucket.
- Data needed: VIX and funding spreads (public macro series). We lack option data beyond VIX. MOVE may need a licence.
- Evidence in the source (equities, bonds, commodities, FX, no credit target): bonds and equities show a convex relationship. Bonds rally after both low-risk and high-risk zones (p4). Equities reverse after the high-risk zone and continue after the low-risk zone (p3). The note gives charts only. It states no point estimates in the text. The sign changed from pre-2008 to post-2008 (p3-p4).
- HY applicability: medium. HY is a risky asset with equity-like tail behaviour. The sign change across eras is a warning.
- Fit to our signals: S7 replacement candidate as a regime filter. It can also condition F2 and F4.
- Test: weekly, 1997 to 2024. Signal: bucket of the US composite. Horizon 1 and 4 weeks. Metric: HY excess return per bucket, and a test for a U-shape (quadratic term). Pass: quadratic term significant at 5% with HAC errors, with the same sign in pre-2008 and post-2008 halves.

### F8. HY reinvestment cash flow (source: 5de4d6ff_7cf2_4fdf_8edb_d55fde385a63_604 (1).pdf, p1-p2)
- Status: NEW. The known supply factors use issuance. This is the demand-side flow from coupons, maturities, calls and tenders.
- Original asset class and definition: US and euro HY. "Forward organic cash flow" is the projected cash paid to holders over the next 1 and 4 weeks, as a share of index AUM:
  $$\text{RCF}_{t,h}=\frac{\sum_{b}\left(\text{Coupon}_{b,t:t+h}+\text{Maturity}_{b,t:t+h}+\text{Call/Tender}_{b,t:t+h}\right)}{\text{Index market value}_t}$$
  Net technical $=\text{RCF}_{t,h}-\text{Net issuance}_{t,h}/\text{AUM}_t+\text{Fund flow}_{t}$.
  Intuition: holders must reinvest cash they receive, so large scheduled cash flow supports prices.
- Credit translation: compute from bond terms for the HY universe: coupon dates, maturities, announced calls and tenders (8-K filings). Combine with net issuance from TRACE new issues. Fund flows need EPFR or ICI, which we lack. Use ETF shares outstanding as a proxy.
- Data needed: bond terms, SEC 8-K call and tender notices, TRACE new issues. Fund flows are missing.
- Evidence in the source (US HY, credit): levels only. Next week $6.6bn (+0.4% of AUM), next 4 weeks $28.1bn (+1.9%) for $HY (p1). The note offers no predictive test. The idea needs our own evidence.
- HY applicability: medium-high. It is HY-specific and built from data we hold. The effect may be small against macro news.
- Fit to our signals: S7 replacement candidate (technical timing). It also extends the market net issuance timing factor in the known list.
- Test: monthly, 2003 to 2024. Signal: next-month net technical as % of AUM. Horizon 1 month. Metric: slope of HY index excess return on the signal, controlling for F5 misalignment. Pass: positive slope with HAC t above 2.

### F9. Spread-rate correlation regime (source: 5de4d6ff_7cf2_4fdf_8edb_d55fde385a63_604 (1).pdf, p5-p6. 1574b3c6_68dd_11eb_8fc9_3e217c25b0c2_604 (1).pdf, p4-p5)
- Status: NEW conditioning variable.
- Original asset class and definition: HY cash spreads vs 5y Treasury. CDS indices vs OIS rates. Rolling 12-week correlation:
  $$\rho_t=\text{corr}_{52\to12\text{w}}\left(\Delta s_{w},\Delta y^{5y}_{w}\right)$$
  The normal state is $\rho<0$ (rates up means growth up means spreads in). A positive $\rho$ marks a liquidity or QE shock (2013 taper tantrum).
  Intuition: when spreads and rates widen together, the driver is the discount-rate or liquidity channel, not growth.
- Credit translation: compute $\rho_t$ for the US HY index and each rating cell from TRACE G-spreads and the Treasury curve. Use $\rho_t>0$ as a risk-off flag. Use the rating-cell response to rate shocks to choose BB versus CCC.
- Data needed: TRACE, Treasury curve. In repo.
- Evidence in the source (US and euro HY, credit): since 2005 the correlation is mostly between -0.2 and -0.8, with average -0.6 for $HY and -0.5 for €HY (p5). In the six largest rate sell-offs since the GFC, $HY spreads tightened 60 to 80 bp on median or average. Only 2013 widened, by 16 bp. The B-BB gap tightened 30 bp on average (p6). The CDS note: the correlation becomes more negative as the measurement horizon grows from 1 day to 3 months (p5).
- HY applicability: medium. The idea is descriptive. It needs a forecast test.
- Fit to our signals: S7 replacement input. It also conditions duration hedging in the events layer.
- Test: weekly. Signal $\mathbb 1\{\rho_t>0\}$. Horizon 4 and 12 weeks. Metric: mean HY excess return when the flag is on versus off. Pass: excess return lower by at least 1% annualised when on, with t above 2.

### F10. Rating-maturity cell valuation percentile and quality-curve ratio (source: 5de4d6ff_7cf2_4fdf_8edb_d55fde385a63_604 (1).pdf, p7-p8)
- Status: variant of value (Houweling and van Zundert, Israel et al.). The known value factors are cross-sectional. This is time-series value per cell.
- Original asset class and definition: US and euro HY. For each rating $r$ and maturity bucket $m$, the percentile rank of today's spread in its post-2010 history:
  $$P_{r,m,t}=\frac{1}{N}\sum_{\tau\le t}\mathbb 1\{s_{r,m,\tau}\le s_{r,m,t}\}$$
  Spread ratios $s_{BB,1\text{-}3y}/s_{BBB,1\text{-}3y}$ and $s_{B}/s_{BB}$ measure compression.
  Intuition: when long BB spreads are near their tights but short BB are not, short BB gives more cushion per unit of risk.
- Credit translation: compute $P_{r,m,t}$ from TRACE for 4 ratings by 4 maturity buckets with an expanding window. Tilt toward cells with high $P$ and high spread ratio, DTS-neutral.
- Data needed: TRACE, ratings. In repo.
- Evidence in the source (HY, credit): March 2021 snapshot only. $BB 1-3y at 60th percentile versus 7-10y at 92nd. $B 58th versus 96th (p8). Typical 6-month HY spread range 100 to 200 bp (p7). No backtest.
- HY applicability: medium. Easy to build. It may duplicate F5 at cell level.
- Fit to our signals: S7 replacement candidate as a cell-level tilt.
- Test: monthly. Signal $P_{r,m,t}$ rank across 16 cells. Horizon 3 months. Metric: rank IC versus cell DTS-adjusted excess return. Pass: mean IC above 0.05, positive in at least 3 of 4 cycles.

### F11. Quality-curve momentum and slope-to-level spillover (source: QuantCraft/GDPBD00000342205 (1).md, p2, p10-p11, p14, p17-p18, p25-p26)
- Status: NEW.
- Original asset class and definition: commodity futures term structures (31 markets, 1985 to 2021). Decompose curve returns into PCs: $r_t\approx\sum_k \text{score}_{k,t}\,\ell_k$. "PC1 residual momentum" is the cumulative return not explained by PC1 (level):
  $$M^{(-1)}_{t}=\prod_{j=0}^{n}\left(1+r_{t-j}-r^{PC1}_{t-j}\right)-1$$
  Curve Momentum takes slope trades inside each curve, neutral to PC1. Curve Spillover Momentum uses recent slope moves (PC2) to predict the future level (PC1) return across markets. It relates to the basis-momentum factor of Boons and Prado (2018).
  Intuition: shifts in the curve shape carry slow supply and demand news, and the level follows.
- Credit translation: treat the HY rating curve (BB, B, CCC) or maturity curve as the term structure. Run PCA on cell spread changes. PC1 is level, PC2 is quality slope. Curve momentum: go long the cell whose PC1-residual return is highest and short the lowest, DTS-neutral. Spillover: use the 1 to 3 month PC2 change (CCC minus BB steepening) to predict the next-month PC1 (index level) move.
- Data needed: TRACE cell spreads. In repo.
- Evidence in the source (commodities, not credit): curve momentum is near zero in correlation with the commodity benchmark (Figure 24, p17). The note shows Sharpe distributions in Figures 22 and 27 (p17, p19). I did not extract a point Sharpe from the md text. Slope moves link to global activity (p25).
- HY applicability: medium. CCC-BB slope moves often lead HY level moves. The mechanism differs from commodity storage.
- Fit to our signals: S7 replacement candidate (spillover part). The cell rotation part extends S6 rating flows.
- Test: monthly, 1997 to 2024. Signal: 3-month change in the PC2 score. Horizon 1 month. Metric: slope of next-month PC1 change on signal, out-of-sample. Pass: correct sign with HAC t above 2 and positive in at least 3 of 4 cycles.

### F12. Smart seasonality: calendar drift gated by a z-score (source: JPM_A_season_for_everyth_2017-07-03_2380131 (1).pdf, p1, p3-p4. HY references in JPM_Momentum_Strategies__2015-04-15_1681565 (1).pdf, p87)
- Status: NEW. The known list has no seasonality factor.
- Original asset class and definition: Australian 3y and 10y swap spreads. Naive seasonal: enter in the direction of the historical mean drift one month before each futures roll date. Smart seasonal: enter 2 to 4 weeks before the roll only if the 3-month z-score agrees:
  $$x_t=\text{sign}(\bar d_{\text{season}})\cdot\mathbb 1\left\{\text{sign}(-z^{3M}_t)=\text{sign}(\bar d_{\text{season}})\right\},\quad z^{3M}_t=\frac{s_t-\bar s_{3M}}{\sigma_{3M}}$$
  Intuition: a seasonal push works best when the spread has not already moved in that direction.
- Credit translation: HY has known calendar effects: turn-of-year (Chang and Huang 1990, Wilson and Jones 1990), January effect, Fridson (2000) HY spread seasonality, week-of-month effects (Jordan and Jordan 1991) (all cited on p87). It also has a supply calendar (heavy issuance in March, May, September). Estimate the mean monthly drift of HY index OAS change by calendar month with an expanding window. Trade only when the 3-month z-score of OAS agrees.
- Data needed: TRACE index OAS, issuance calendar. In repo.
- Evidence in the source (rates, not credit): smart seasonal on 3y spread: 4.34 bp average P/L, Sharpe 3.15, hit rate 64%, full sample (Exhibit 7, p4). Naive seasonal: 0.04 bp, Sharpe 0.46 (Exhibit 6, p3). Most smart-rule P/L comes in 2008-2009 (16.40 bp, p4).
- HY applicability: medium-low. Calendar effects in HY are small next to macro shocks. Data mining risk is high with 12 months.
- Fit to our signals: S7 replacement input, minor.
- Test: monthly, 1997 to 2024. Expanding-window seasonal drift. Signal $x_t$. Horizon 1 month. Metric: hit rate and mean excess return. Pass: hit rate above 55% out of sample, with a binomial p-value below 0.05.

### F13. Short-horizon time-series reversal of the index (source: Persistent Patterns in Short Term (1).pdf, p1-p3, p16-p17)
- Status: NEW at index level. It is related to F2 (cross-section) and F4 (trend).
- Original asset class and definition: 100 futures and FX markets, including 4 corporate credit indices, since 1970. Naive reversal signal for formation window $h\in\{5,10,15,20\}$ business days:
  $$s_t(h)=-\frac{S_t-\bar S_{t-h,t}}{\sqrt h\,\sigma_r}$$
  Clip to $[-2,2]$. Position $w_t=\tfrac14\sum_h s_t(h)$ (p2-p3). Market selection uses the persistence of reversal or momentum by asset.
  Intuition: sub-month moves overshoot, then revert, in some markets.
- Credit translation: apply to the HY excess return index or HYG. Test whether HY sits in the reversal group or the momentum group.
- Data needed: ETF or TRACE index. In repo or public.
- Evidence in the source (multi-asset): the reversal portfolio is mostly equity indices and non-USD FX. Credit appears in both legs (Figure 22, p17). The note gives no credit-only statistic.
- HY applicability: low. The horizon is short for cash HY. HY index returns show positive autocorrelation at weekly frequency because of stale prices, which goes against reversal.
- Fit to our signals: none directly. It can flag entry timing only.
- Test: daily HYG excess return 2008 to 2024. Signal $w_t$. Horizon 1 week. Metric: Sharpe net of 1 bp. Pass: Sharpe above 0.3 net. Expect a fail.

### F14. Media sentiment factor on HY constituents (source: QuantCraft/Catching the sentiment waves (1).md, p7-p9, p20)
- Status: NEW, but data are missing.
- Original asset class and definition: the "Credit Spread" sentiment factor uses MarketPsych and RavenPack equity sentiment for CDX HY and IG constituents (p9). Steps: volume-weighted 21-day moving average of daily sentiment, z-score over 3 years. Build a signal-weighted portfolio with weights proportional to the percentile rank of sentiment. Regress portfolio returns on 11 macro factor returns. The residual is the sentiment factor (p8-p9).
- Credit translation: replace vendor news with SEC filing tone. Score 8-K and 10-Q text per issuer with a finance word list (Loughran-McDonald). Z-score per issuer over 3 years. Orthogonalise to known factors.
- Data needed: SEC filings (in repo). Vendor sentiment (missing).
- Evidence in the source (multi-asset, risk model use): the note uses the factors for risk attribution, not alpha. Bond direction is predictable at about 1 week with long smoothing (p20). The sister note `21f659cb` finds news alphas negative after costs for equities (p1).
- HY applicability: low. Fast decay and high HY costs work against it.
- Fit to our signals: S5 (document optionality) could share the filing text pipeline. Not a standalone signal.
- Test: monthly. Signal: 3-month change in filing tone z-score. Horizon 3 months. Metric: rank IC versus bond excess return, controlling for EMC. Pass: partial IC above 0.03 with t above 2.

### Method note (not a factor): VaR backtest procedures (source: 200521pap (1).pdf)
- Campbell (2005) reviews unconditional coverage (Kupiec), independence and conditional coverage (Christoffersen) tests. These tests apply to our conformal bands per rating and liquidity cell, and to the event model. Add them to the coverage test suite in `hy/` tests.

## Top 3
1. F1 within-issuer curve residual: a direct US HY bond-selection signal, credit evidence (IR 1.20 gross, 0.81 net of 20 bp, p9, p13), all data in repo, and it stacks on S1 to S4 without macro risk.
2. F5 HY index fair-value misalignment net of carry: the cleanest replacement for failed S7, with an out-of-sample protocol and a cost-of-waiting threshold that fits HY carry. Evidence is FX only.
3. F3 factor-hedged credit carry: it isolates the part of HY carry that is not beta. Credit index evidence shows Sharpe 0.86 after costs (p18), and it builds from TRACE and the Treasury curve.
