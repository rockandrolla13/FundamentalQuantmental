# Bartram, Grinblatt, and Nozawa (2025), "Book-to-Market, Mispricing, and the Cross Section of Corporate Bond Returns"

Journal of Financial and Quantitative Analysis 60(3), pp. 1185–1233, DOI 10.1017/s0022109024000048. Peer-reviewed journal article. We read NBER Working Paper 27655, revised March 2023 (63 PDF pages), at https://www.nber.org/system/files/working_papers/w27655/w27655.pdf. The journal text may differ. The volume and pages come from Crossref. Page numbers below are PDF pages. PDF page = printed page + 2.

## Claim
A bond's book-to-market ratio (BBM) predicts its return after non-parametric controls for yield, rating, nearness to default, liquidity and bond and equity attributes (pp. 2, 5). The authors conclude that mispricing is the best explanation, because the signal decays fast, works equally across default and liquidity groups, and does not predict Treasury returns (pp. 22–26, 33).

## Method
**Signal (pp. 11–12).** Book is the amortized issue price. `P^S` is the latest trade price that is at least eight calendar days before the return month.

```latex
BBM_{j,t} = \frac{Book_{j,t}}{P^{S}_{j,t}}
```

Intuition: a bond that trades below its amortized cost scores high, and the eight-day gap means that one price error cannot enter both signal and return.

**Return (pp. 9–10, eq. 1).** Use the first and last trades in the month as start and end prices. This needs no liquidity filter.

```latex
R_{t+1} = \frac{P^{E}_{t+1} + AI_{t+1} + C_{t+1}}{P^{B}_{t+1} + AI_{t}} - 1
```

Intuition: a fair price is close to a martingale over a few days, so a nearby trade can stand in for a month-end price.

**Fama-MacBeth (p. 17, eq. 2).** Regress the month t+1 return on BBM and on quintile dummies for each control. Industry dummies stay in every specification.

```latex
R_{j,t+1} = a_t + g_t BBM_{j,t} + \sum_{s=1}^{S} c_{s,t} X_{j,s,t} + e_{j,t+1}
```

Intuition: quintile dummies form a dense grid of peers, close to dealer matrix pricing, so BBM must add to what the grid already prices.

**Tests that separate mispricing from risk and liquidity (pp. 19–27).**
1. **Equity hedge.** Subtract a hedge ratio times the same-firm equity return, then repeat the regression (p. 19).
2. **Equity placebo.** Use the issuer's stock return as the dependent variable (p. 19).
3. **Signal delay.** Lag the signal 0 to 11 months, on one common return sample (p. 22). Compare the alpha decay with the persistence of quintile membership (p. 23).
4. **Interactions.** Multiply BBM by a dummy for the 20% of bonds nearest default, lowest rated, widest bid-ask, lowest volume, or fewest trades (pp. 24–25).
5. **Treasury placebo.** Repeat on Treasuries. Then censor Treasury prices to the trade dates of a matched corporate bond, across 1,000 runs (pp. 25–26).
6. **Yield bound.** Compare the alpha spread with the promised yield spread (p. 24).
7. **Factor tests.** Add a bond HML factor to the factor model (p. 26).
8. **Rival signal.** Run BBM against a firm-level fair value signal: market value of liabilities regressed on 28 accounting items (pp. 12, 27).
9. **Costs.** Apply monthly quintile half spreads to turnover, for all trades and for trades of at least $100,000 (pp. 30–32).

## Data
- TRACE enhanced and standard. Signals January 2003 to August 2020, returns February 2003 to September 2020 (pp. 7–8).
- Senior unsecured, fixed coupon, no embedded options other than simple calls, non-financial: 8,925 bonds, 838 firms, 458,139 bond-months (p. 8). Mean 1,149 bonds a month in the regressions (p. 8, note 5).
- Sample mix: 86.3% investment grade. Q5 holds 27.4% non-investment grade, and Q1 holds 4.6% (Table 2, p. 42).
- Robustness: Merrill Lynch month-end marks to December 2016, 140,808 bond-months (p. 8). All TRACE fixed coupon bonds, 565,093 observations (p. 8).

## Result
**Raw spread (Table 2, p. 43).** Q5 minus Q1: 44 bp a month equal weight (t 3.86), 41 bp value weight (t 3.58). Annualized Sharpe ratios are 0.92 and 0.85 (p. 16).

**Controls (Table 3 Panel A, p. 45).** BBM Q5 coefficient: 0.441 (t 3.62) with industry, 0.445 (t 3.64) with microstructure, 0.265 (t 3.21) with bond controls, 0.320 (t 4.05) with equity controls.

**Separation tests.**

| Test | Result | Page |
| --- | --- | --- |
| Equity-hedged bond return | 0.316 (t 4.82) | 46 |
| Same-firm stock return | −0.082 (t −0.71) | 46 |
| Investment grade only | 0.307 (t 5.97) | 46 |
| Delay of 0 and 2 months | 30 bp and 9 bp | 22 |
| Survival in extreme quintiles at 1 month | Q1 89%, Q5 82% | 23 |
| Interaction with nearest-default Q5 | −0.100 (t −0.73) | 50 |
| Interaction with widest bid-ask Q5 | 0.027 (t 0.28) | 51 |
| Q5 minus Q1 yield spread | under 13 bp a month | 24 |
| Treasury placebo, censored | 0.039, insignificant | 26 |
| Bond HML in the factor model | alpha 15 bp (t 3.11) | 26 |
| BBM with the firm-level signal | 25 bp (t 3.32), against 29 bp (t 3.79) alone | 27 |

Decay arithmetic (p. 23): one month of delay cuts efficacy by 42% while more than 85% of the extreme quintiles stay in place. Two months cut it by 70% while more than 80% stays in place.

**Factor alphas (pp. 21–22).** Equal weight Q5 minus Q1: 19 bp on the BBW 5-factor model, 23 bp with a term structure factor. Value weight: 12 bp, not significant, and 18 bp. Small bonds 28 bp, large bonds 20 bp.

**All bonds (p. 28).** With junior bonds, the Q5 coefficient is 38 bp (t 4.26).

**Costs (Table 12, p. 60).** Monthly rebalance turnover is 31%. Net alpha is −25.0 bp (t −2.46) with all-trade costs, and 2.0 bp (t 0.22) with institutional costs. Annual buy-and-hold on the augmented model: net 12.3 bp (t 2.06) with institutional costs and 6.4 bp (t 1.04) with all-trade costs.

## Limits
- The evidence is mostly investment grade, and the IG result drives the headline (p. 46). The paper gives no separate HY-only estimate that we found. The rating interaction only compares the lowest 20% with the rest (p. 50).
- The factor tests use the Bai, Bali and Wen (2019) model (p. 14). Crossref marks that paper as retracted (`flags.md` in the review track). The Fama-MacBeth tests do not depend on it.
- The delay argument assumes that risk and liquidity premia are slow. A premium that moves fast would also decay fast. The authors argue against this with a size calculation, not a direct test (p. 23).
- BBM mixes rate moves and credit moves. It is close to a price sort, and the authors call the difference possibly semantic (p. 34).
- Intra-month return construction gives noise and a small Jensen bias (pp. 5, 10). The authors argue that the net bias is conservative.
- Short sale cost is not in the net figures (p. 32).
- Dealer quotes in the Merrill sample give a smaller alpha of 20 bp (t 2.52) (p. 19).

## Section touched
`docs/methodology.md` Section 7.3 and S1 (classify the residual), Section 7.5 (decay and half-life), Section 8 (signal test design), Section 11 (backtest design). Cross-reference: `houweling-van-zundert-2017-factor-investing-corporate-bonds.md` (value V2, par over price, HY alpha 3.70%).

## Use for the two clocks
**What the source says.** Three contrasts separate mispricing from a risk or liquidity proxy: alpha decay against the persistence of the characteristic, equal efficacy across default and liquidity groups, and no effect on the same firm's equity or on Treasuries.

**What our data says.** No such test has run. Section 4.7 reports a 6-month IC beyond spread of −0.037 (t −1.7) for the refinance share and +0.027 (t 1.0) for the recontract share. Clock features update at filing dates, so they are slow by construction.

**What we decide (our proposal, not the source's claim).** Run one classifier on the S1 residual and on each clock feature.

| Check | Mispricing reading | Risk or unmodelled fact reading | Liquidity reading |
| --- | --- | --- | --- |
| Delay of 0 to 11 months against the survival of the feature's quintile | Fast decay, feature still in place | Slow decay | Fast decay, with a reversal after a skip |
| Interaction with the worst 20% of default risk | Flat | Stronger in the worst group | Flat |
| Interaction with the worst 20% of liquidity | Flat | Flat | Stronger in the worst group |
| Same-firm equity return | No effect | Same sign | No effect |
| Alpha against the yield spread | Alpha above the yield spread | Alpha at or below it | Alpha at or below it |

1. **Clock delay in filing time.** Measure the delay from the filing's `available_at`, not from the month end. A clock effect that lasts many months while the feature stays in place reads as a priced characteristic or a slow fact, not as a price error.
2. **S1 entry rule.** S1 needs evidence of the mispricing column before it gets weight as mispricing. Otherwise the memo labels the position as a premium trade. The source's flat rows are failed rejections in an 86.3% IG sample (-0.100, t -0.73, and 0.027, t 0.28, pp. 42, 50-51). So a flat row counts only as an equivalence vote, by the rule of Method 3 in `docs/decisions/2026-11-01-clocks-residual-timing.md`.
3. **Clock as a conditioner of S1, not a signal.** Interact the S1 residual with the clock quintile. If S1 fails in the worst clock quintile, then the clock names the "unmodelled fact" failure mode of S1. This uses the clocks with no signal weight, in line with Section 4.7.
4. **Gap rule.** Build every test with a gap of at least eight days between the price in the signal and the first price in the return (p. 11). Our v0 uses the same eight days.
5. **Horizon.** The paper's net alpha survives only at low turnover (p. 60). The clock classifier therefore reports net results at a 12-month hold.
