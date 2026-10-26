# Folder B: root specs and BMI files — new credit factors

Scope: 16 files in `B_root_specs.txt` plus 4 files in `BMI/files/`. Paths are relative to `/home/ak/Documents/Quant Credit/`.

Main finding: the two anonymous RFQ specs and the BMI spec hold most of the buildable content. Our TRACE data can build the RFQ flow features, because Enhanced TRACE marks the side of each customer trade (verify that our extract keeps `rpt_side_cd` and the contra-party flag). No file holds a backtest on real bond data. The only real-data numbers are the Shim (2020) equity result and the hit rates that the BMI spec quotes from a Morgan Stanley note.

## Triage table

| File | What it is | Relevant (yes/no) | Why |
|---|---|---|---|
| `anonymous_rfq_alpha_prediction_only_spec.md` | Code-ready spec of 24 alpha features from anonymous RFQ flow (A1–A24), with an experiment ladder and promotion rules | yes | Defines the flow, intensity, issuer, neighbour, curve-pressure, exhaustion, factor-residual and ETF-pressure features. TRACE side data maps onto it |
| `anonymous_rfq_alpha_feature_research_spec_from_quantcraft.md` | Spec of 20 "alpha families" that adapt DB Quantcraft papers to corporate bonds | yes | Defines variance-ratio reversal, low-vol reversal, issuer-curve PCA momentum, curve-to-level spillover, curve residual, news and correlation-regime conditioners |
| `BMI/files/credit_bmi_v2.md` | Full spec of an HY index spread-forecast engine (6 factor blocks, CQR plus ACI, interval-versus-cost trade rule) | yes | Index timing factors with tickers, lags and transforms. Candidate replacement for S7 |
| `BMI/files/credit_bmi_v2.tex` | LaTeX copy of the same spec | yes (duplicate) | Same numbers as the .md. I checked the percent and bp values |
| `BMI/files/credit_bmi_v2.py` | Walk-forward driver: expanding z, Ledoit-Wolf weights, regime gate, CQR, ACI, decision rule | yes (process) | Reusable code shape. No new factor |
| `BMI/files/credit_bmi_model.py` | `DATA_SPEC` dictionary, target builder, feature builder, purged CV, quantile models | yes (data spec) | `DATA_SPEC` matches the .md table |
| `arb_comovement` (PDF, 67 pages) | Shim (2020), "Arbitrage Comovement", SSRN 3287912. Equity ETF paper | yes | Defines arbitrage sensitivity. HY ETF (HYG, JNK) version is a new bond factor |
| `combined_strategies_data_requirements.csv` | 17 strategy rows: DB Quantcraft macro models plus 6 credit research notes from 2011 | yes | Names the PPI minus CPI margin-squeeze idea, an FCF-liquidity-cyclicality screen, and an EBITDA-to-refinancing map. No formulas |
| `strategies_data_requirements.csv` | First 11 rows of the combined CSV | no | Duplicate. FX and macro models only |
| `full_signal_design_cleaned.tex` | One page: PCA growth-surprise index with a 252-day rolling z | yes (low) | Macro surprise factor. Needs consensus forecasts we lack |
| `signal_design.tex` | Section stub plus a Granger causality test of asset returns on credit spread changes | yes (low) | Lead-lag test method. Sub-files it inputs are absent |
| `Macro Liquid Credit Business Plan - Alaph Capital (1).docx` | Fund business plan: cap-structure arb, bond basis, curve RV, liquidity scoring, risk limits | yes | Sizing rules, liquidity exit limits, single-name limits by rating, curve-shape screens, spread per unit of leverage |
| `Credit Relative Value & Cross Asset Arbitrage Business Plan Master Sheet.xls` | 2008 plan: tool list, trade universe, budget by trade type with hit ratios | yes | Curve-shape z-score screens (4 variants). Planning hit ratios only |
| `Business Planning Sheet 2011.xls` | 2011 to-do list, the same Tools sheet, a mostly empty 2011 budget | no (duplicate) | Tools sheet repeats the 2008 file. Budget sheet is empty past row 32 |
| `Basic Sizing.xlsx` | One-sheet trade sizing formula from target return, hit ratio and win/loss ratio | yes (sizing) | Sizing rule |
| `Conviction Sizing Grid.xlsx` | Conviction-by-strategy risk grid and optimal target PnL by hit ratio and loss severity | yes (sizing) | Sizing rule. Notes "historically 60–70% hit ratio, loss severity 50–60%" |
| `Quick TimeLine.xlsx` | 24-month build timeline for an RFQ trading business | no | Project plan. Lists data feeds only (MarketAxess, Tradeweb, TRACE, liquidity score) |
| `Screens Master Sheet.xlsx` | 14 sheets. `Main` is a screen-build tracker. The other 13 sheets hold only pasted chart images (57 PNG) | no | No factor definitions. `Credit` sheet holds 2 images of Russia sovereign spreads against BB/B peers. `Positioning` holds CFTC rates futures charts |
| `Untitled3.py` | Notebook export: bond fair value as the median of a Gaussian mixture over dealer quotes | yes (process) | Composite mark method for sparse prices. No factor |
| `Untitled3 (1).py` | Longer copy of the same notebook plus synthetic price generators and a dispersion study | no (duplicate) | Same method. Synthetic data only |

Not read: `BMI/files/credit_bmi_v2.pdf`. It is the compiled form of the .tex file, which I read.

## Factors found

### F-B1. TRACE customer flow imbalance, pooled by issuer and neighbours (source: `anonymous_rfq_alpha_prediction_only_spec.md` §7, §8, §14, §15, §16)
- Status: NEW.
- Definition. Sign each customer trade from the dealer view: $side_u=+1$ when the customer sells. For bucket $B$ (ISIN, issuer excluding own ISIN, sector × rating × maturity, kNN set) and half-life $\tau$:
  $$N^{\pm}_{B,t}=\sum_{u<t,\,u\in B}\mathbf 1\{side_u=\pm1\}e^{-(t-u)/\tau},\quad q_{B,t}=\frac{N^+_{B,t}+\alpha}{N^+_{B,t}+N^-_{B,t}+2\alpha},\ \alpha=1$$
  $$\text{FlowAlpha}_{B,t}=-(q_{B,t}-0.5),\qquad \text{FlowLogOddsAlpha}_{B,t}=-\log\frac{\tilde q}{1-\tilde q},\ \tilde q=\text{clip}(q,\varepsilon,1-\varepsilon),\ \varepsilon\in\{0.02,0.05\}$$
  Neighbour version: $\text{NeighborFlowAlpha}_{i,t}=-\sum_{j\in N_K(i)}\omega_{ij}(q_{j,t}-0.5)$, $\omega_{ij}\propto e^{-\text{Dist}(i,j)/\eta}$ over sector, rating, maturity, spread duration, liquidity and factor beta.
  Intuition: persistent customer selling in a bond or its issuer predicts a lower price, and pooling fixes sparse HY trading.
  Windows: $\tau\in\{1d,5d\}$ for daily data. Use $u<t$ only. The spec also lists event windows $N\in\{5,\dots,250\}$ trades.
- Data needed: Enhanced TRACE side and contra-party flag, trade size, timestamp, issuer map, rating, sector. All in repo if the side field is kept.
- Evidence: none in source. The spec states the pass rule $b>0$ out of sample only.
- HY applicability: high. HY bonds trade rarely, so issuer and neighbour pooling carries more signal than own-bond flow. That is the spec's own claim (§35).
- Fit: new signal. It sits beside S2 as a technical layer and can confirm S1 (see F-B6).
- Test: monthly cross-section of HY bonds. Rank IC of issuer-pooled FlowAlpha ($\tau=5d$) against next 1-month excess return over duration-matched Treasuries. Pass if mean IC > 0.02 with Newey-West t > 2, and positive in 3 of 4 cycles (2008, 2015, 2020, 2022).

### F-B2. Signed notional pressure and size-count gap (source: RFQ prediction spec §11)
- Status: NEW.
- Definition:
  $$\text{SignedNotional}_{B,t}=\sum_{u<t,u\in B}side_u\,size_u\,e^{-(t-u)/\tau},\qquad \text{SignedNotionalAlpha}=-z_{B,c}(\text{SignedNotional})$$
  $$q^V_{B,t}=\frac{V^+ +\alpha_V}{V^+ + V^- +2\alpha_V},\qquad \text{SizeFlowGap}_{B,t}=\text{logit}(\tilde q^V_{B,t})-\text{logit}(\tilde q_{B,t})$$
  Intuition: block trades carry more information than odd lots, so a gap between dollar flow and count flow flags institutional selling.
  The z-score uses a same-clock baseline per bucket.
- Data needed: TRACE size. Note that TRACE caps reported HY size at $1MM ("1MM+"). The cap truncates the notional measure.
- Evidence: none in source.
- HY applicability: medium. The 1MM+ cap blunts the size signal for HY.
- Fit: extends F-B1.
- Test: add SizeFlowGap to a regression of 1-month excess return on FlowAlpha. Pass if the out-of-sample rank IC lift is > 0.005 with a Diebold-Mariano t > 2.

### F-B3. Flow exhaustion reversal (source: RFQ prediction spec §19–§20; Quantcraft spec Family 20)
- Status: NEW.
- Definition:
  $$\text{Acc}_{B,t}=\text{Imb}^{short}_{B,t}-\text{Imb}^{long}_{B,t},\quad \text{Extreme}_{B,t}=\mathbf 1\{|\text{Imb}^{long}_{B,t}|>q_{0.9}(|\text{Imb}^{long}_B|)\}$$
  $$\text{Exh}_{B,t}=\text{Extreme}_{B,t}\cdot[-\text{sign}(\text{Imb}^{long}_{B,t})\,\text{Acc}_{B,t}],\qquad \text{FlowReversalAlpha}_{B,t}=\text{sign}(\text{Imb}^{long}_{B,t})\,\text{Exh}_{B,t}$$
  Intuition: extreme customer selling that now fades is liquidity pressure, so the price recovers.
  Quantcraft variant: multiply by a low-news flag and by "no public-factor confirmation".
- Data needed: TRACE side. Equity returns and HY index returns for the confirmation flag.
- Evidence: none in source.
- HY applicability: high. Forced HY selling (fund outflows, downgrades) is the case this targets.
- Fit: extends F-B1. Links to the fallen-angel reversal (known), but this is flow-based and covers all bonds.
- Test: 1-month reversal regression. Pass if the FlowReversalAlpha coefficient > 0 with t > 2 out of sample, and the top-minus-bottom quintile return after 50 bp round-trip cost is > 0.

### F-B4. Issuer curve flow pressure (source: RFQ prediction spec §17; Quantcraft Family 18)
- Status: NEW.
- Definition: maturity buckets short ≤ 3y, belly 3–7y, long > 7y.
  $$\text{CurvePressure}_{a,t}=\text{Imb}_{a,long,t}-\text{Imb}_{a,short,t},\qquad \text{CurveFlowAlpha}_{i,t}=-m_i\,\text{CurvePressure}_{a,t},\ m_i\in\{+1,0,-1\}$$
  Intuition: customer selling at the long end of one issuer cheapens its long bonds against its short bonds.
- Data needed: TRACE side, maturity, issuer map.
- Evidence: none in source.
- HY applicability: medium. Only issuers with bonds in two maturity buckets qualify.
- Fit: extends S4 (capital structure relative value) along the maturity axis.
- Test: within-issuer long-minus-short bond return over 1 month. Pass if rank IC with CurveFlowAlpha > 0.03, t > 2, on issuers with at least 2 buckets.

### F-B5. Liquidity-conditioned flow (source: RFQ prediction spec §18)
- Status: NEW.
- Definition: $\text{WidthZ}_{i,t}=(W_{i,t}-\mu_{bucket})/\sigma_{bucket}$, with $W$ a TRACE bid-ask proxy (for example Roll or the customer buy-minus-sell price gap).
  $$\text{LCFlowAlpha}_{i,t}=\text{FlowAlpha}_{B,t}\times\text{WidthZ}_{i,t}$$
  Intuition: the same imbalance moves price more when the market is thin.
- Data needed: TRACE trades. Repo can compute the bid-ask proxy.
- Evidence: none in source.
- HY applicability: high.
- Fit: extends F-B1. Also usable as a conditioner for S1.
- Test: interaction coefficient $b_3>0$ with t > 2 in the 1-month excess-return panel.

### F-B6. Flow-confirmed relative value (source: RFQ prediction spec §22, §35)
- Status: variant of S1 (fair value residual).
- Definition: $\text{FlowConfirmedRV}_{i,t}=\text{RVAlpha}_{i,t}\times\text{FlowAlpha}_{B,t}$, or $\text{RVAlpha}\times\text{sign}(\text{FlowAlpha})$.
  Intuition: a cheap bond is more likely to richen when buyers are already arriving.
  The spec names this the highest-value alpha (§35).
- Data needed: S1 residual plus TRACE side.
- Evidence: none in source.
- HY applicability: high.
- Fit: S1 entry filter.
- Test: split S1 deciles by flow agreement. Pass if the S1 top-minus-bottom 3-month return is higher in the agree subset by > 25% of the unconditional spread, with a bootstrap p < 0.05.

### F-B7. Factor-residual rich-cheap with ridge betas (source: RFQ prediction spec §21)
- Status: variant of S1.
- Definition:
  $$\hat\beta_i=\arg\min_\beta\sum_{s<t}(\Delta FV_{i,s}-\beta'\Delta F_s)^2+\lambda\|\beta\|_2^2,\quad \text{RVZ}_{i,t}=\frac{FV_{i,t}-\hat\beta_i'F_t-\mu^{RV}_{i}}{\sigma^{RV}_{i}},\quad \text{RVAlpha}=-\text{RVZ}$$
  $F$ = CDX IG, CDX HY, 2y/5y/10y Treasury, LQD, HYG, JNK, issuer equity, VIX, MOVE.
  Intuition: a market-factor residual, not a fundamental residual, that mean-reverts.
- Data needed: issuer equity, Treasuries, VIX (have). HYG and JNK prices (public). CDX (lack).
- Evidence: none in source.
- HY applicability: medium. Complements the fundamental S1 residual with a short-horizon price residual.
- Fit: S1, short horizon.
- Test: 1-month rank IC of RVAlpha after removing the S1 fundamental residual. Pass if partial IC > 0.02, t > 2.

### F-B8. Cross-asset lead (source: RFQ prediction spec §23; `signal_design.tex` Granger test)
- Status: variant of EMC (equity momentum).
- Definition: $\text{CrossAssetLead}_{i,t,L}=\hat\beta_i'(F_t-F_{t-L})$, with components $\beta_{i,eq}\Delta Eq_{issuer}$, $\beta_{i,ETF}\Delta HYG$, $\beta_{i,rates}'\Delta Rates$.
  Selection rule from `signal_design.tex`: keep asset $j$ for credit $i$ only if $\gamma_1..\gamma_p$ in
  $CS^i_t=\alpha+\sum_k\beta_kCS^i_{t-k}+\sum_k\gamma_kAsset^j_{t-k}+\varepsilon_t$ are jointly significant (F-test p < 0.05), with $p$ chosen by AIC or BIC.
  Intuition: liquid markets move first and stale HY marks catch up.
  New part against EMC: a beta-weighted, multi-asset, days-scale lead, not 1–6-month raw equity momentum.
- Data needed: equity returns (have), HYG and JNK (public), Treasuries (have).
- Evidence: none in source.
- HY applicability: high for days to 2 weeks. HY prices lag equity.
- Fit: extends EMC and S2.
- Test: 5-day horizon IC of CrossAssetLead with $L=5$ trading days. Pass if IC > 0.03 and it survives EMC (1m) in a joint regression with t > 2.

### F-B9. HY ETF pressure (source: RFQ prediction spec §24)
- Status: NEW.
- Definition:
  $$\text{ETFPressure}_{E,t}=R_{E,t,L}\times z(\text{Volume}_{E,t}),\qquad \text{ETFBasisPressure}_{E,t}=\text{PremDisc}_{E,t}\times z(\text{Volume}_{E,t}),\qquad \text{ETFAlpha}_{i,t}=\beta_{i,E}\,\text{ETFPressure}_{E,t}$$
  $E\in\{\text{HYG},\text{JNK}\}$. Intuition: heavy ETF trading pushes constituent bonds later through creation and redemption.
- Data needed: HYG and JNK price, volume, NAV (public: daily price and NAV). Bond beta from TRACE.
- Evidence: none in source.
- HY applicability: high. HYG and JNK are large HY liquidity channels.
- Fit: new signal (technical, days horizon).
- Test: 5-day return of high-beta minus low-beta HY bonds after days with $|\text{ETFBasisPressure}|$ above its 90th percentile. Pass if the sign predicts the move with hit rate > 55% over at least 100 events, binomial p < 0.05.

### F-B10. ETF arbitrage sensitivity, HY version (source: `arb_comovement`, Shim 2020, eq. 5, 10, 11, 18)
- Status: NEW.
- Definition:
  $$\Lambda_{i,e,t}=\frac{c_{i,t}\,w_{i,e,t}^{\gamma}}{\sum_{j\in e}w_{j,e,t}\,c_{j,t}\,w_{j,e,t}^{\gamma}},\ \gamma=0.5,\qquad r^{\tau}_{i,m}=c_{i,t}\,\text{sign}(V_{i,m})|V_{i,m}|^{\gamma}+e_{i,t}$$
  $w$ = average weight in the ETF over at least 1 year. $c$ = price impact from signed dollar volume over 5-minute intervals (Lee-Ready signing in the paper).
  Prediction: after an ETF return beyond its 95th percentile, high-$\Lambda$ securities over-react and then revert toward the ETF return. Low-$\Lambda$ securities under-react.
  Test regression: $r_{i,t\to t+\tau}-r_{e,t\to t+\tau}=\alpha_e+\psi_{t,\tau}\Lambda_{i,e,t}+\varepsilon$.
  Intuition: arbitrageurs trade by weight, not by exposure, so illiquid large-weight bonds move too much with HYG.
- Data needed: HYG and JNK daily holdings (iShares and SPDR publish current files; history is a gap). TRACE signed volume for $c$ (side field gives the sign directly).
- Evidence (equities only): long-short of extreme deciles earns about 7.5% per year alpha in 2008–2017 (abstract and p. 3). No pattern before 2008. The effect is strongest in large caps. No bond evidence in source.
- HY applicability: medium. The mechanism fits HY ETFs. The holdings history is the bottleneck.
- Fit: new signal. Also a warning for S1 and F-B7: ETF-driven betas are partly mechanical.
- Test: on HYG return days above the 95th percentile (2012–2024), regress the 5-day post-event relative return on $\Lambda$. Pass if $\psi_{5}<0$ (reversal) with t > 2.

### F-B11. Variance-ratio and low-vol reversal (source: Quantcraft spec Families 3, 4, 5)
- Status: NEW. Our known list holds momentum but no conditional short-term reversal.
- Definition:
  $$VR_{i,t,k,W}=\frac{\text{Var}_W(r^{(k)}_{i})}{k\,\text{Var}_W(r_i)},\qquad \text{VRReversalAlpha}_{i,t}=-\text{rank\_z}(R_{i,t,L})\,\mathbf 1\{VR_{i,t}<\theta_{VR}\}$$
  $$\text{LowVolReversalAlpha}_{i,t}=-\text{rank\_z}(R_{i,t,L})\,\mathbf 1\{\text{VolZ}_{i,t}<q_{low}\},\ \text{VolZ}=\frac{\text{Vol}_{i,t,W}-\text{median}(\text{Vol}_i)}{\text{MAD}(\text{Vol}_i)}$$
  Risk-appetite version: also require $|\text{Corr}_W(r_i,RA)|<$ threshold, with $RA_t=-R_{SPX}+\Delta CDX_{HY}+\Delta VIX$ or PC1 of [VIX, MOVE, CDX HY, HYG, SPX].
  Use factor-residual returns $r_i-\beta_i'\Delta F$ as the preferred input.
  Intuition: in calm, mean-reverting bonds, a large move is liquidity noise and reverses.
  The spec leaves $\theta_{VR}$, $q_{low}$, $k$, $W$, $L$ open.
- Data needed: TRACE daily prices, equity, VIX (have). MOVE (public).
- Evidence: none in source. The source papers are on other assets.
- HY applicability: medium. Bid-ask bounce in TRACE inflates reversal. Use trade-weighted daily prices and skip one day.
- Fit: new signal. Conditioner for S2.
- Test: 1-month reversal of residual returns with a 1-day skip. Pass if VRReversalAlpha IC > 0.02 after 50 bp cost, and stronger in low-VR than high-VR bonds.

### F-B12. Issuer curve PCA momentum, curve-to-level spillover and curve residual (source: Quantcraft spec Families 6–9)
- Status: NEW.
- Definition: for issuer $a$ (or sector × rating × maturity group if sparse), standardise bond returns $\tilde R_{a,t,j}=R_{a,t,j}/\sigma_{a,j,t}$ and run rolling PCA, $\tilde R_{a,t}\approx L_{a,t}f_{a,t}$ (f1 level, f2 slope, f3 curvature).
  $$\text{PCMom}_{a,m,t,L}=\sum_{u=t-L}^{t-1}f_{a,m,u},\quad \text{CurvePCMomAlpha}_{i,t}=\ell_{i,m,t}\,\text{PCMom}_{a,m,t,L}$$
  $$\text{Spill}_{i,t}=\ell_{i,1,t}\,\hat\beta_{spill}\,\text{PCMom}_{a,2,t,L},\ \text{from } f_{a,1,t+h}-f_{a,1,t}=\alpha+\beta_{spill}\text{PCMom}_{a,2,t,L}+e$$
  $$r_{i,t}=\sum_{m=1}^3\beta_{i,m}f_{a,m,t}+e_{i,t},\quad \text{CurveResidReversal}_{i,t}=-\frac{e_{i,t}-\bar e_{i,W}}{sd_W(e_i)},\quad \text{CurveResidMom}_{i,t}=\frac{\sum_{u=t-L}^{t-1}e_{i,u}}{sd_W(e_i)}$$
  Intuition: one issuer's bonds share one credit. A bond off its own curve is mispriced against its siblings, and a slope move leads a level move.
- Data needed: TRACE prices, maturities, issuer map (have).
- Evidence: none in source.
- HY applicability: medium. Many HY issuers have 1–3 bonds. Group curves cover the rest.
- Fit: extends S4 (capital structure relative value) to same-seniority bonds.
- Test: monthly within-issuer long-short on CurveResidReversal (issuers with ≥ 3 bonds). Pass if mean monthly return after 50 bp cost > 0 with t > 2 and positive in 3 of 4 cycles.

### F-B13. Credit curve shape against spread level (source: Credit RV plan xls, sheet `Tools`, items 1–4 and 7; Alaph docx, "Credit Relative Value", Trade Identification)
- Status: NEW.
- Definition (the source gives the screen names, not the formula). Build it this way. Issuer slope $Sl_{a,t}=s_{a,long,t}-s_{a,short,t}$ from fitted issuer curves. Then four z-scores:
  1. against level: residual of $Sl$ on $s_{a,5y}$ across issuers in the same rating, $z$ of that residual;
  2. against cross-section: $z$ of $Sl_{a,t}$ within its spread bucket;
  3. against own history: $z$ of $Sl_{a,t}$ over 1 year ("steepest, flattest on own history");
  4. against spread volatility: residual of $Sl$ on 3-month spread volatility.
  Intuition: a curve too steep for its level prices too much near-term safety or too little long-term risk. It also flags distress, where curves invert.
  Source data rule: at least 3 tenors (3, 5, 10y) and 1 year of history.
- Data needed: the source uses CDS curves (lack). Build from TRACE G-spreads by issuer (have).
- Evidence: none in source. The xls gives planning hit ratios only (curve trades 0.75, HY curve roll 0.9). These are assumptions, not results.
- HY applicability: medium. Curve inversion is a distress marker. Slope residual is a roll-down trade.
- Fit: extends S4 and the maturity and roll-down known factor.
- Test: long the flattest-residual issuer curve and short the steepest, duration-neutral, 3-month hold. Pass if the return after cost > 0, t > 2.

### F-B14. HY index timing composite, BMI v2 (source: `BMI/files/credit_bmi_v2.md` §1.2–§3.4; `credit_bmi_model.py` `DATA_SPEC`)
- Status: NEW as a timing signal. Candidate replacement for S7.
- Definition. Target: $y^{(h)}_{t}=\sum_{j=1}^h r^{exc}_{HY,t+j}$, $h\in\{5,21,63\}$ days. Six blocks, each to a score in $[-10,10]$:
  $$z^{(k)}_t=\text{clip}\Big(\frac{x^{(k)}_{t-\ell_k}-\hat\mu^{(k)}_t}{\hat\sigma^{(k)}_t},-8,8\Big),\quad s^{(k)}_t=20[\Phi(z^{(k)}_t)-\tfrac12]$$
  Expanding mean and SD, at least 60 observations.
  1. Volatility: 21-day change in VIX level. Sign −. Lag 0.
  2. Momentum: 4-month exponentially decaying mean of monthly HY excess returns ÷ 4-month realised vol. No z-score. Scaled to terminal SD 10/3. Sign +. Lag 5 days.
  3. Sentiment: 21-day change in the geometric mean of (EM vs G10 bond TR) and (G10 equity vs bond TR). Sign +. Contra rule: when the 6-month rolling z of the level is > +3 or < −4, flip the sign.
  4. Liquidity: $0.5\,z(\text{NY Fed primary dealer net corporate positions})+0.5\,z(\Delta_{21d}(\text{CDX.IG 5y}-\text{C0A0 OAS}))$. Dealer data enters 9 days after the reference date. Sign −.
  5. Structural: equal-weight z of median issuer 3-month equity vol, median net debt / EV, and 3-month downgrades minus upgrades. Sign −. Lag 1 day.
  6. Systematic: PC1 of daily OAS changes across 8 rating buckets AAA–CCC. Eigenvector from trailing 250 days. Sign fixed so the IG loading is > 0. Factor = 21-day sum of PC1 scores. Sign −.
  Gate: $\tilde s^{(k)}_t=(1-\beta_kg_t)\,10\tanh(s^{(k)}_t/10)$, $g_t=\mathbf 1\{\text{21d OAS vol}>\text{expanding 80th pct}\}$, $\beta_{mom}=0.6$, else 0.
  Features: 6 signals, 2 weekly lags each, vol×liq and vol×mom (20 columns).
  Weights: $w\propto(\lambda I+(1-\lambda)\Sigma)^{-1}\rho$ (Ledoit-Wolf $\Sigma$).
  Intuition: HY index excess returns respond to risk appetite, dealer balance-sheet room, aggregate leverage and a common spread factor.
- Data needed: VIX (have). HY excess return (ICE H0A0: lack. FRED has the H0A0 OAS and total return index, so build excess return from TR minus a duration-matched Treasury return). Rating bucket OAS (FRED `BAMLC0A1CAAA` to `BAMLH0A3HYC`). NY Fed primary dealer statistics (public). Median equity vol and net debt/EV (Compustat and CRSP: have). Ratings after Feb 2017 (lack: block 5c fails after 2017). CDX (lack: run the dealer leg alone, as the spec does before 2004).
- Evidence: the spec quotes the source Morgan Stanley note. Hit rate 62% for HY and 67% for IG. The original LIBOR-OIS liquidity factor scored 51% HY and 55% IG. With all signals aligned the hit rate was 66–68% against 61% overall. Demo on synthetic data: coverage 0.899 against 0.90. No real-data backtest of v2.
- HY applicability: high for index timing and beta sizing. Low for bond selection.
- Fit: replacement candidate for S7 (failed). It times total HY beta rather than sector tilts. Its 6 blocks also feed methodology `m_t` (section on macro state).
- Test: walk-forward 2004–2024, $h=21$. Pass if HY hit rate > 55% on traded days, block-bootstrap (block 42 days) 90% interval of net Sharpe excludes 0, and coverage of the 90% interval is within 0.88–0.92.

### F-B15. Primary dealer corporate bond positions (source: BMI v2 §1.2 Liquidity block)
- Status: NEW.
- Definition: $L^{dealer}_t=z(\text{net corporate positions}_{t-9d})$, forward-filled weekly, staleness cap 5 days. Sign − for future spread change (high inventory, less room to absorb selling).
  Intuition: intermediary balance-sheet capacity sets the price of HY liquidity.
- Data needed: NY Fed Primary Dealer Statistics, weekly, from 2001 (public).
- Evidence: none for this leg alone in source.
- HY applicability: high as a market-state conditioner.
- Fit: conditioner for S6 forced-flow trades and for F-B3. Part of F-B14.
- Test: regress next 1-month H0A0 OAS change on $\Delta_{4w}$ dealer positions with OAS and VIX controls, 2001–2024. Pass if t > 2 with HAC errors.

### F-B16. Rating-bucket systematic spread factor PC1 (source: BMI v2 §1.2 Systematic block)
- Status: NEW (the source calls it the Collin-Dufresne common residual factor).
- Definition: $PC1_t=v_t'\Delta OAS_t$ over 8 buckets, $v_t$ from trailing 250-day covariance, sign so the IG loading > 0. Signal: $\sum_{j=0}^{20}PC1_{t-j}$, expanding z.
  Intuition: a common spread shock that structural variables miss.
- Data needed: FRED ICE BofA OAS by rating (public), or build bucket OAS from our TRACE G-spreads.
- Evidence: none in source.
- HY applicability: high as a timing input. Our TRACE version is a fallback.
- Fit: part of F-B14. Also a control for S1 residual drift.
- Test: incremental OOS $R^2$ of PC1 over the other five BMI blocks for $h=21$. Pass if Diebold-Mariano t > 2.

### F-B17. Sentiment contra-indicator at extremes (source: BMI v2 §1.2–§1.3, footnote 8 of the MS note)
- Status: NEW (rule), variant of Lopez-Salido-Stein-Zakrajsek sentiment.
- Definition: $s^{sent}_t$ as in F-B14. If $z^{6M}(\text{level})>+3$ or $<-4$, use $-s^{sent}_t$.
  Intuition: crowded positioning makes sentiment reverse at its extremes.
- Data needed: EM and G10 bond total return indices and equity indices (public, partly lack EM bond TR history).
- Evidence: thresholds from the MS note. No returns given.
- HY applicability: medium. The flip fires rarely.
- Fit: conditioner for S7 replacement.
- Test: compare forecast loss with and without the flip on days where the flag fires. Pass if pinball loss falls on > 60% of flagged months.

### F-B18. PPI minus CPI margin squeeze by sector (source: `combined_strategies_data_requirements.csv`, row "EBITDA Margin Trends by Sector")
- Status: NEW.
- Definition (source gives the idea only). Build it this way: $G_{s,t}=\Delta_{12m}\ln PPI^{input}_{s,t}-\Delta_{12m}\ln CPI^{output}_{s,t}$. Predict the next-4-quarter change in sector EBITDA margin and the issuer margin trend. Signal $=-z_s(G_{s,t})\times\text{cost share}_s$.
  Intuition: when input prices rise faster than selling prices, margins compress before leverage reports show it.
- Data needed: BLS PPI and CPI by industry (FRED, public). Compustat margins (have).
- Evidence: none in source.
- HY applicability: high. HY issuers have thin margins and little pricing power.
- Fit: feeds S3 (forward leverage estimate) and the `margin_trend` feature. A second S7 replacement candidate at sector level.
- Test: regress next-4-quarter sector median margin change on $G_{s,t}$. Pass if slope < 0 with t > 2. Then check that the sector tilt earns a positive 3-month rank IC in 3 of 4 cycles.

### F-B19. FCF, liquidity and low-cyclicality screen with a yield floor (source: combined CSV rows "Screen for Positive FCF…" Aug 2011 and "Cyclicality vs. Liquidity" Sep 2011)
- Status: variant of S1 and the quality or defensive factor (Israel, Palhares, Richardson 2018).
- Definition (no formula in source): yield > 10%, FCF > 0, strong liquidity (cash plus revolver over 12-month maturities), low cyclicality (beta of sector EBITDA to GDP). Plot cyclicality against liquidity by rating.
  Intuition: high yield with a cash cushion survives stress.
- Data needed: Compustat (have), TRACE yield (have).
- Evidence: none in source. The CSV rows describe 2011 European HY research notes.
- HY applicability: high.
- Fit: framework F3 liquidity sizing and S1.
- Test: 12-month default rate and excess return of screen passers against other bonds with yield > 10%. Pass if the default rate is lower by half and excess return is higher with t > 2.

### F-B20. Spread per unit of leverage (SPL) (source: Alaph docx, Capital Structure Arbitrage, Fundamental overlay)
- Status: variant of SPiDER.
- Definition: $SPL_i=s_i/(\text{Debt}_i/\text{EBITDA}_i)$. The source gives the name only. SPiDER divides by 10-year average EBITDA. SPL uses current leverage.
- Data needed: have.
- Evidence: none.
- HY applicability: medium. SPiDER is the stronger known form.
- Fit: S1.
- Test: compare rank IC of SPL against SPiDER. Keep SPL only if its partial IC > 0.01, t > 2.

### F-B21. Growth surprise index (source: `full_signal_design_cleaned.tex`)
- Status: NEW (macro).
- Definition: $X_{i,t}=(\text{Actual}_{i,t}-\text{Forecast}_{i,t})/\sigma_i$, $I_t=\text{PC1}(X_t)$, $\text{Signal}_t=(I_t-\mu_{t-252:t})/\sigma_{t-252:t}$.
  Intuition: positive growth surprises tighten HY spreads.
- Data needed: consensus forecasts (lack. Citi surprise index is a substitute but vendor).
- Evidence: none.
- HY applicability: medium.
- Fit: macro block of S7 replacement.
- Test: next 1-month H0A0 excess return on the signal. Pass if t > 2.

### F-B22. Conditioners: news volume, macro sentiment regime, correlation regime, clock and triplets (source: Quantcraft spec Families 1, 2, 11–15)
- Status: NEW, low priority.
- Definitions:
  - $\text{LowNews}_{a,t}=\mathbf 1\{z(\text{NewsCount}_{a,t,L})<q_{low}\}$. Multiply S1 by it.
  - $\text{HighCorrRegime}_t=\mathbf 1\{\overline{\text{Corr}}_W(r_i,r_j)>q_{80}\}$. Use S1 in low-correlation regimes and pooled flow (F-B1) in high ones.
  - Clock alpha $T_{B,c,h}=\bar R_{B,c,h}/se_{B,c,h}$. For daily HY, use month-end and index-rebalance dates as clocks.
  - Triplets $\rho_{B,v,l,h}=\text{Spearman}(\text{PastMove}_l,\text{FutureMove}_h)$ with FDR control. High data-mining risk.
- Data needed: news (lack). Others: have.
- Evidence: none.
- HY applicability: correlation regime medium. The others low.
- Fit: conditioners for S1 and F-B1.
- Test: correlation regime only. S1 IC in low-correlation months minus high-correlation months > 0, bootstrap p < 0.05.

## Other useful content
- Interval-versus-cost trade rule (BMI §3.4): long if $lo>c$, short if $hi<-c$, else flat. Size $\propto|point|/(hi-lo)$. HY cash cost $c=12$ bp. CDX HY 4 bp.
- Horizon alignment (BMI §2): full size only when 1W, 1M, 3M forecasts agree. Two of three gives 2/3 size. Traded horizon against both others gives flat.
- Drawdown stop (BMI §3.5): flatten when equity falls $D^*=2\times$ the 95th percentile of h-day adverse moves (about 3% for HY at h = 21).
- Hygiene (BMI §1.4): forward-fill cap 5 days, z clip ±8, dealer data on publication date, ratings on announcement date. Matches our `available_at` rule.
- Purged CV (BMI §3.0): 3 chronological folds, embargo of h rows, pinball loss, quantile-crossing repair.
- Single-name limits (Alaph, table 5, $400MM fund): IG 100, BB 70, B 40 (units not stated, likely $MM). Limits use spread-implied PD with lower recovery for wider spread buckets, so worst-case loss stays inside the 10% drawdown.
- Liquidity limits (Alaph, table 6): exit 80% of the book in 10–15 days. Cost to exit 80% under last-20-day conditions ≤ 2% of AUM. Exit 50% at market ≤ 1%. Exit last 50% at 1.5× bid-offer ≤ 1.5%.
- Liquidity score inputs (Alaph): trade frequency, volume, number of participants, cost, move volatility.
- Basic Sizing formula: target PnL per trade (bp) $=R\cdot(T/12)\cdot10^4/\big(N\,(p-(1-p)/W)\big)$, with R target return, T holding months, N trades, p hit ratio, W win/loss ratio. Size by conviction 1–5 as 1/4, 1/2, 1, 1.5, 1.75 of base.
- Conviction grid: optimal target PnL $=\text{TotalPnL}\cdot\text{turnover}/((1+h)L-h)$ by hit ratio h and loss severity L. Note in sheet: historical hit ratio 60–70%, loss severity 50–60%.
- Composite mark (`Untitled3.py`): fair value = median of a Gaussian mixture over dealer quotes, $\sigma_s^2=0.7(\text{bidask}_s/3.92)^2+0.3\sigma_{macro}^2$. Use it for sparse HY marks.
- Promotion rules (RFQ spec §31): as-of computable, OOS IC lift, stable sign, survives IG/HY, liquid/illiquid, calm/stress splits, not explained by public factors.
- Horizon classification (RFQ spec §30.2): effect grows to 3–5 days means information. Same-day only means stale mark. Sign flip means liquidity pressure.
- Bond basis trade rule (Alaph): scan lowest dollar price and highest Z-spread minus CDS basis. Needs CDS, so out of scope.

## Top 3
1. F-B1 TRACE customer flow imbalance, pooled by issuer and neighbours, with F-B3 exhaustion reversal. Reason: new, buildable now from TRACE side data, and pooling fits sparse HY trading.
2. F-B14 BMI HY timing composite, led by F-B15 dealer positions and F-B16 rating-bucket PC1. Reason: full spec with lags exists, public data covers most blocks, and it can replace the failed S7.
3. F-B12 issuer curve residual reversal, with F-B13 curve shape against level. Reason: new same-issuer relative value from TRACE, independent of fundamentals, and it extends S4.
