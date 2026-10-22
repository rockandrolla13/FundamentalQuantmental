# Houweling and van Zundert (2017), "Factor Investing in the Corporate Bond Market"

Financial Analysts Journal 73(2), pp. 100–115, April 2017, DOI 10.2469/faj.v73.n2.1. Peer-reviewed journal article. Authors from Robeco. We read the SSRN version of September 2016 (ssrn-2516322.pdf, 49 pages). Its title page names the FAJ issue (p. 1). The FAJ page range comes from the RePEc and CFA Institute listings, not from the PDF. Page numbers below are PDF pages. PDF page = printed page + 2.

## Claim
Four bond-only factors give significant alphas in US corporate bonds: size, low-risk, value and momentum (p. 2). The authors build each factor separately for investment grade (IG) and high yield (HY) (pp. 8–9). Pairwise alpha correlations are low, so an equal-weight multi-factor portfolio has a lower tracking error and a higher information ratio than any single factor (p. 18). Alphas stay positive after transaction costs (p. 21). Equity definitions of the same factors work less well, except momentum (p. 27).

## Method
1. Universe. All bonds in the Barclays US Corporate IG index and the Barclays US Corporate HY index, monthly (p. 6). The authors rank IG and HY separately, because ratings segment the market (pp. 8–9).
2. Return. Bond excess return over duration-matched Treasuries, from Barclays (p. 7).
3. Portfolios. Each month, the top (bottom) portfolio holds the 10% of bonds with the highest (lowest) exposure, equal weight (p. 8).
   - Long-short: top minus bottom, one-month horizon (p. 8).
   - Long-only: top portfolio, 12-month holding, with the overlapping method of Jegadeesh and Titman (1993) (p. 8).
   - Multi-factor: 25% in each long-only single-factor portfolio (p. 8).
4. Factor definitions use bond data only: no accounting data and no equity data. So every bond enters, listed issuer or not (p. 10).

**Size (p. 11).** Rank bonds on the issuer's total index weight. The top portfolio holds the bonds of the 10% smallest issuers.

```latex
Size_{c,t} = \sum_{i \in c} \frac{MV_{i,t}}{\sum_{j} MV_{j,t}}
```

Intuition: a small issuer carries less information, more default risk and smaller, less liquid bonds, so it may pay a premium.

**Low-risk (p. 12).** Two filters, rating then maturity.

```latex
LR^{top}_t = \{\, i : r_i \in R^{high},\ M_i < M^{*}_t \,\}, \qquad |LR^{top}_t| = 0.10\, N_t
R^{high}_{IG} = \{AAA, \dots, A-\}, \qquad R^{high}_{HY} = \{BB+, \dots, B-\}
```

M*_t is the maturity cut that fills 10% of the bonds. Its mean is 3.1 years in IG and 3.6 years in HY. The bottom portfolio holds the longest 10% of bonds rated below AA- (IG) or below BB- (HY). Its mean cut is 26.4 and 11.6 years. Intuition: short, better-rated bonds earn more per unit of risk than long, low-rated bonds.

**Value (p. 13).** Each month, regress spread on rating dummies, maturity and the 3-month spread change. Score each bond by its percentage gap to the fitted spread.

```latex
S_i = \alpha + \sum_{r=1}^{21} \beta_r I_{ir} + \gamma M_i + \delta\, \Delta S_i + \varepsilon_i   \quad (3)
V_i = \frac{S_i - \hat{S}_i}{\hat{S}_i}
```

Intuition: a bond is cheap when its spread pays more than its rating, maturity and recent spread move justify. The ΔS term enters because spreads tend to rise about three months before a downgrade (Norden and Weber 2004). So a recent widening raises the fitted spread, and the bond does not look cheap for that reason alone.

**Momentum (p. 14).** Past 6-month excess return, with a one-month implementation lag (Jostova et al. 2013).

```latex
MOM_{i,t} = \prod_{k=2}^{7} (1 + x_{i,t-k}) - 1
```

Intuition: bonds with high past excess returns continue to outperform. The source says only "6-month return with a one-month lag". The index range above is our reading of that text.

**Evaluation (pp. 9–10).** CAPM alpha against the own-segment market excess return DEF. Fama-French-Carhart alpha adds RMRF, SMB, HML, MOM and TERM.

```latex
R_t = \alpha + \beta\, DEF_t + \varepsilon_t   \quad (1)
R_t = \alpha + \beta_1 RMRF_t + \beta_2 SMB_t + \beta_3 HML_t + \beta_4 MOM_t + \beta_5 TERM_t + \beta_6 DEF_t + \varepsilon_t   \quad (2)
```

Newey-West t-tests for alphas. Jobson-Korkie tests for Sharpe ratios against the market (p. 43).

**Break-even cost (pp. 19–20).** The overlapping weight of a bond is its mean weight over the 12 portfolios formed at t−11 to t. Turnover is the sum of weight increases.

```latex
w_{i,t} = \frac{1}{12} \sum_{k=0}^{11} w^{form}_{i,t-k}, \qquad TO_t = \sum_i \max(0,\, w_{i,t+1} - w_{i,t}), \qquad c^{BE} = \frac{\alpha^{CAPM}}{TO}
```

Intuition: the break-even cost is the one-way cost per unit of turnover that takes the CAPM alpha to zero.

## Data
- Barclays US Corporate IG and HY index constituents, January 1994 to June 2015. Survivorship-bias free: a defaulted bond returns its final traded price (pp. 6–7).
- More than 1.3 million bond-months: about 900,000 IG and 400,000 HY. The mean month holds 3,520 IG bonds and 1,473 HY bonds (p. 7).
- HY means (Table 1, p. 41): spread 481 bp (median 441 bp), maturity 7.74 years, issuer index value USD 3.27bn (median 0.77bn). IG means: spread 148 bp, maturity 10.89 years.
- Rating: middle of S&P, Moody's and Fitch, or the worse of two (Table 1 note, p. 41).
- In HY, 65% of issuers have one bond in the index. In IG, 30% do (p. 26).
- Equity link for the spillover test: 1.1 million of 1.3 million bond-months (p. 27).

## Result
**Long-short, one month (Table 2, p. 42).** HY CAPM alphas: size 3.28% (t 1.21), low-risk 2.02% (t 2.04), value 5.14% (t 2.70), momentum 8.49% (t 2.80). IG: size 1.15% (t 1.63), low-risk 1.27% (t 2.49), value 2.56% (t 3.14), momentum −1.38% (t −0.77). Fama-French-Carhart alphas are close, except HY low-risk falls to 1.19% (t 1.18).

**Alpha correlations, long-short (Table 2, p. 42).** In HY, value and size correlate 51%. Value and momentum correlate −36%. Low-risk correlates −19% with size and −18% with value. In IG, value and size correlate 41%.

**Long-only, 12-month holding, HY (Table 3, p. 43).**

| HY portfolio | Mean | Sharpe | Outperf. | TE | IR | CAPM α (t) | FFC α (t) | Turnover | Break-even |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Market | 2.33% | 0.23 | | | | | | 55% | |
| Size | 7.83% | 0.64 | 5.50% | 7.95% | 0.69 | 5.68% (2.36) | 6.36% (2.78) | 86% | 6.60% |
| Low-risk | 3.78% | 0.56 | 1.45% | 5.02% | 0.29 | 2.39% (3.43) | 2.28% (3.61) | 92% | 2.60% |
| Value | 6.58% | 0.49 | 4.26% | 5.66% | 0.75 | 3.72% (2.49) | 3.62% (2.64) | 96% | 3.88% |
| Momentum | 4.37% | 0.42 | 2.04% | 3.86% | 0.53 | 2.15% (2.24) | 2.36% (2.88) | 118% | 1.82% |
| Multi-factor | 5.64% | 0.56 | 3.31% | 3.88% | 0.85 | 3.49% (3.12) | 3.65% (3.61) | 98% | 3.56% |

**Long-only, IG (Table 3, p. 43).** Market mean 0.50%, Sharpe 0.12. CAPM alphas: size 1.24% (t 2.08), low-risk 0.70% (t 3.12), value 1.06% (t 1.87), momentum 0.35% (t 0.81). Multi-factor: Sharpe 0.32, IR 0.66, CAPM and FFC alpha 0.84%. Momentum break-even cost is 0.34%, the only one below the cited bid-ask spreads (p. 21).

**Costs (p. 20).** The authors cite HY bid-ask spreads of 81 bp (Chen et al. 2007, 1995–2003) and 51 bp (Harris 2015, 2014–2015). All HY break-even costs exceed both.

**Alternative definitions, HY CAPM alpha (Table 7, p. 47).**
- Size by bond, not issuer: 5.34%, significant.
- Low-risk by lowest DTS (duration times spread): 1.80%, Sharpe 0.67, the highest low-risk Sharpe in HY.
- Value V1, the widest spread within rating x maturity peer cells: 1.53%, not significant. Sharpe 0.30, not significant.
- Value V2, bond book-to-market (par over price): 3.70%, significant, with 21.45% volatility.
- Momentum formation: 3 months 2.35%, 6 months 2.15%, 9 months 1.52%, 12 months 0.78%. Only 3 and 6 months are significant.
- Equity definitions: size 2.42%, low-risk 1.18%, value 0.58%, momentum 1.13%. None is significant in HY. In IG, equity momentum gives 0.60% and is significant (p. 27).

**Neutral portfolios, HY (Table 8, p. 48).** Rating-neutral size falls to 3.64% from 5.68%. Sector-neutral value falls to 2.43% and loses significance. Rating-neutral momentum falls to 1.59% and loses significance.

**Liquid subsample (Table 9, p. 49).** One bond per issuer: the youngest (age at most 2 years, else 4) and then the largest. HY multi-factor CAPM alpha is 3.72%, against 3.49% for all bonds. Every HY factor stays significant.

**Subperiods (p. 30).** HY multi-factor CAPM alpha: 3.41% (t 2.21) for 1994–2003, 3.37% (t 2.28) for 2004–2015. Market-value weights cut HY multi-factor alpha to 2.78% (t 3.21). Quintiles in place of deciles cut it to 2.50%.

**Multi-asset (Table 6, p. 46).** Bond factors on top of equity factors raise the four-market alpha from 1.26% to 2.53%.

## What our data says (hy/peers.py, hy/backtest.py, data/raw/backtest, 22 October 2026)
**What we hold.**
- `data/raw/backtest/panel_full.parquet`: TRACE HY panel, 737,379 bond-months, 34,542 CUSIPs, 3,163 gvkeys, January 2008 to August 2026. Columns include `years`, `g_spread`, `mod_dur`, `price` and `available_at`.
- The panel holds no amount outstanding. `par_volume` is traded volume, not issue size. No source in `hy/sources/` maps an amount outstanding.
- `data/raw/backtest/peer_signals_full.parquet` holds `rclass` (IG, BB, B, CCC). It is the S&P class to February 2017 and a leverage-implied class after that (`hy/peers.py`).
- `results_h3_full`, `results_h6_full`, `results_h12_full` hold `realised_net`: bond return less the duration-matched Treasury, less beta times the HY benchmark spread return, less round-trip cost (`hy/backtest.py`).
- `data/raw/backtest/leverage_full.parquet` holds quarterly issuer `debt`.

**Where the paper agrees with our data.**
1. Peer-cell value is weak in HY. Their V1 (widest spread in rating x maturity cells) gives 1.53%, not significant (Table 7). Our ESP uses sector x rating x maturity cells. It adds +0.072 beyond spread at 6 months (t 2.6) but fails three of four cycle windows (decision page `2026-10-22-esp-peer-groups`).
2. Short formation works best in HY momentum. Their 3-month alpha (2.35%) beats 6, 9 and 12 months (Table 7). Our EMC uses 3 months and adds +0.038 beyond spread at 3 months (t 4.8).
3. The 12-month horizon carries the edge. They hold long-only portfolios for 12 months. Our `widest` rule has net IC 0.34 at 12 months.

**Where the paper differs from our data.**
1. Equity momentum. Their equity spillover momentum is not significant in HY (1.13%, Table 7). Our 3-month equity momentum is our most significant beyond-spread signal. Their test uses 12-1 month equity returns, ours uses 3 months. We have not tested 12-1.
2. Size and spread level. Their HY size alpha is the largest (5.68%), and it falls to 3.64% when rating-neutral (Table 8). Small HY issuers may simply pay wider spreads. Our `widest` rule may already hold most of this premium.
3. Their CAPM alpha removes DEF beta. Our beyond-spread test removes the spread rank. Value and size load on spread, so our test is harder on both.

**What we could build.**
1. Low-risk L1: the shortest bonds in classes BB and B, cut at the 10% count each month. All inputs exist today (`rclass`, `years`). Also build the DTS form: `mod_dur × g_spread`, lowest decile.
2. Value V3: equation (3) with our data. Regress `g_spread` on `rclass` dummies, `years` and the 3-month change in `g_spread`, each month. Take V = (S − Ŝ) / Ŝ. It needs no fundamentals, so it covers private issuers.
3. Size S1: issuer debt from `leverage_full`, or the count of TRACE CUSIPs per gvkey as a proxy. A true index weight needs amount outstanding, which we do not hold.
4. Credit momentum: the 3-month and 6-month `realised` return of each bond, with a one-month lag. Compare it with EMC on one common sample.

**Falsifiable tests on our panel (rank IC after cost, cycle windows 2008, 2015, 2020, 2022).**
1. **Low-risk beyond spread.** Keep L1 only if its 12-month IC beyond spread is positive in at least three of four windows. Low-risk picks low spreads, so a raw IC may be negative while the beyond-spread IC is positive.
2. **ΔS term.** Compare V3 with V3 minus the ΔS regressor and with ESP. Keep the ΔS term if it raises the 6-month beyond-spread IC and the cycle count.
3. **Size after spread.** Reject S1 if its 12-month IC beyond spread is not positive. This tests whether size is more than spread level.
4. **Bond against equity momentum.** Reject credit momentum as a separate input if it adds nothing beyond spread and EMC at 3 months.
5. **Break-even check.** For each new signal, compute top-decile 12-month alpha over turnover, as in the paper. Compare it with our median `cost_rt`.

## Limits
- US Barclays index bonds only, January 1994 to June 2015. The sample covers 2008 and ends in mid-2015. It misses 2020 and 2022.
- Portfolio Sharpe ratios and alphas, not IC. Our IC results and their figures are not directly comparable.
- Long-only alphas use equal weights in decile portfolios. Small issuers get a large weight. Market-value weights lower the HY multi-factor alpha by 0.71 points (p. 30).
- Excess returns come from Barclays index data, not from TRACE trades. The paper does not state how Barclays prices each bond.
- Costs are not deducted. Only break-even costs are compared with bid-ask figures from other studies.
- The authors work at Robeco, which sells products built on these factors.
- Source inconsistencies:
  - The IG size CAPM alpha is 1.24% in Table 3 (p. 43) but 1.12% in Tables 7 and 8 (pp. 47–48). 1.12% equals the Table 3 outperformance.
  - The Table 9 "all bonds" size row (IG mean 1.25%, HY mean 7.89%) does not match Table 3 (1.61%, 7.83%) (p. 49).
  - The Table 2 caption names Panels A, C and D. The table shows Panels A, B and C (p. 42).
  - The low-risk bottom portfolio is "below AA- (BB-)" in the text (p. 12) but "A/BBB resp. B/C" in the Table 2 caption (p. 42).

## Section touched
`docs/methodology.md` Section 8 (Quantamental signals: candidate low-risk, size and credit momentum signals, and the composite weights) and Section 7.4 (a bond-only value regression with a ΔS term beside ESP and SPiDER). Cross-reference: `israel-palhares-richardson-2018-common-factors.md` and `deutsche-bank-factor-investing-corporate-credit.md`. No decision page yet. A sprint that builds L1 and V3 and runs the tests above should add one.
