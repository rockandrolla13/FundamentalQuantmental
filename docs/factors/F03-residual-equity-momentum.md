# F03. Residual equity momentum spillover

- **Rank:** 3. **Tier:** 1 (tested in credit, buildable now). **Status:** variant of EMC (`hy/peers.py` `equity_momentum`).
- **Source:** van Zundert (2018), PhD thesis, ch. 5 "Momentum Spillover from Stocks to Corporate Bonds". File `/home/ak/Documents/Quant Credit/Missing Papers/van-zundert-2018-thesis-full.pdf`. Pages below are printed pages. PDF page = printed page + 9.
- **Reader block:** H-F11 (`research/notes/quant-credit-review/out_H.md`). Every number below was checked on the source page.
- **Compared with:** Dynkin et al. (2021) ch. 15, `research/cards/dynkin-et-al-2021-systematic-investing-in-credit.md` and `research/cards/dynkin-et-al-2021-chapter-implementations.md` (Chapter 15).

## Claim
In US high yield, issuers with a high 6-month residual equity return (the stock return that the equity market does not explain) have higher bond excess returns over duration-matched Treasuries over the next 6 months. The rank IC beyond spread is positive. The 2009 drawdown is at most half that of total-return momentum spillover.

## Definition
```latex
E_{i,m} = \alpha_i + \beta_i\,\mathrm{RMRF}_m + \varepsilon_{i,m}, \quad m \in [t-36,\, t-1]
\qquad
\mathrm{RM}_{i,t} = \frac{\prod_{k=1}^{6}\left(1+\hat\varepsilon_{i,t-k}\right) - 1}{\operatorname{sd}\left(\hat\varepsilon_{i,t-36 \dots t-1}\right)}
```
Intuition: rank on firm-specific equity news only, because the market part of the stock return drives the default-risk tilt that crashes after equity bear markets (pp. 137–139).

What the source says:
- `E_{i,m}` is the stock return in excess of the 1-month T-bill. RMRF is the Fama-French market factor. One factor only (eq. 5.3, p. 137).
- Estimation window: 36 months, moving (p. 137). Formation: compound the last J = 6 residuals. Divide by the standard deviation of all 36 residuals of the window (p. 137).
- Lag: 1 month, "in line with total momentum spillover" (p. 137). Base case J = 6, K = 6, implementation lag 1 month (p. 132).
- Portfolios: deciles of companies. Equal weights across companies. A company's bond return is the market-value-weighted return of all its bonds (p. 131). The reader block says "equal-weight the company's bonds". That is wrong.
- Holding: K = 6 months, overlapping Jegadeesh-Titman books. The month-t return is the mean of the books formed in t−6 to t−1 (p. 132).
- Universe: Barclays US IG and US HY constituents with US-listed equity and at least 3 years of stock history, January 1994 to December 2013. 2,439 companies (p. 131). HY: 335 companies a month on average (Table 5.1, p. 147).
- Robustness: estimation windows of 24 to 60 months give Sharpe ratios 0.68 to 0.81 (p. 141). A Fama-French 3-factor residual lowers the alpha from 4.43% to 3.98% and lowers the time-varying DEF beta from 0.37 to 0.25 (ALL universe, p. 141, Table 5.7 p. 153).

**Default factor and hedge (the 0.73 to 1.14 step).** DEF is the average excess return over duration-neutral Treasuries of the bonds in the universe. For HY tests, DEF is the HY average (p. 132). The "βDEF" hedge subtracts the full-sample DEF beta times DEF from the long-short return (p. 139):
```latex
r^{h}_t = r_t - \hat\beta_{DEF}\,\mathrm{DEF}_t, \qquad \hat\beta_{DEF}^{HY,\,RM} = -0.52 \ \ (t = -5.07,\ \text{Table 5.5, p. 151})
```
Intuition: the long-short is short credit beta (losers are riskier), so adding back 0.52 of the HY market return removes the beta drag.

Our choice: estimate β on the past 36 months of long-short and DEF returns only. The source uses the full sample, which looks ahead. Expect a lower hedged Sharpe than 1.14.

**How it differs from EMC.**
| | Our EMC (`equity_momentum`) | Book EMC (Dynkin ch. 15) | Book issuer-specific EMC | Residual EMC (this page) |
|---|---|---|---|---|
| Return | total (`trt1m`) | price | price, minus S&P 500 fit | total minus 1m T-bill, minus RMRF fit |
| Market model | none | none | 12-month rolling on S&P 500 | 36-month rolling on RMRF |
| Window | 3 months compounded | 1, 3, 6 months, each over √k, averaged | as book EMC, on residuals | 6 months compounded |
| Scale | none | √k | √k | divide by sd of 36 residuals |
| Skip | none | none | none | 1 month |
| Sort, hold | within GICS sector (OneScore), 3/6/12 m tests | quintiles across universe, 1 m | same | deciles, 6 m overlapping |

## Inputs
| Field | Production table and column | as_of | available_at rule | Have |
|---|---|---|---|---|
| Monthly stock total return | `equity_monthly.ret` (`comp.secm.trt1m`, primary US issue) | `datadate` | datadate + 1 day | have, from 2007 only |
| Market excess return RMRF | none (Ken French library `Mkt-RF`) | month end | download timestamp | need |
| 1-month T-bill RF | none (Ken French `RF`) | month end | download timestamp | need |
| Bond price, coupon, duration, Treasury yield | `bond_panel` `price`, `coupon`, `mod_dur`, `tsy_yield`, `g_spread` | `date` | panel `available_at` | have |
| Issuer key | `bond_panel.gvkey` | `date` | panel `available_at` | have |
| Bid-ask for cost | `bond_panel.bid_ask_pts` | `date` | panel `available_at` | have |

## Build steps
1. Pull `equity_monthly` from January 2004. The `datadate >= '2007-01-01'` filter in `hy/sources/peer_data.py` must move, or no RM exists before January 2010 and the 2008 window is empty.
2. Load RMRF and RF. Compute `E_{i,m} = ret − RF`.
3. At each month end t, for each gvkey, take months t−36 to t−1 (skip month t). Require all 36 returns.
4. Fit OLS of E on RMRF. Keep the 36 residuals. RM = compounded last 6 residuals over the sd of all 36.
5. Copy RM to every eligible bond of the issuer in `bond_panel` at t.
6. Rank IC test: score = RM, outcome = 6-month `realised_excess_return` (h = 6, default β).
7. Portfolio test: deciles of issuers by RM. Equal weight across issuers. Inside an issuer, market-value weights (price x `amt_out`) when every bond has `amt_out`, else equal weights. Six overlapping books.
8. DEF_t = equal-weight mean of 1-month excess returns of eligible bonds (`realised_excess_return(panel, 1, as_of, beta=0.0)`). Hedge the long-short with the rolling 36-month β of step 8 on DEF.

## Code placement
- `hy/peers.py`: `residual_equity_momentum(equity, factors, month_end, decision_time, window=36, form=6, skip=1) -> pd.DataFrame`. Output columns `rm`, `rm_beta`, `rm_sd`. Reuses the `equity_momentum` window logic.
- `hy/backtest.py`: `default_factor(panel, as_of) -> pd.Series` (column `def_xr`), built on `realised_excess_return`. `def_hedged(ls, def_xr, window=36) -> pd.Series` (column `ls_hedged`).
- Docstrings cite methodology 7.4 (OneScore paragraph), Section 8 composite (E16), and Section 11 backtest design, with eq. 5.3 of the source.
- New source `hy/sources/ff_factors.py` for RMRF and RF, with `as_of` and `available_at`.

## Tests
- No look-ahead: an RM at t changes no value when returns dated after t−1 are altered.
- Market neutrality: on a synthetic panel where every stock is β × RMRF plus noise, RM is uncorrelated with β.
- Sign: a synthetic issuer with a positive residual shock in t−6 to t−1 ranks in the top decile.
- Edges: fewer than 36 returns gives NaN. A delisted stock gives NaN from the delisting month. A defaulted bond keeps its last carried row. An issuer with sparse trades uses its eligible bonds only.
- Evaluation: monthly rank IC of RM beyond `g_spread` (`ic_beyond`), 6-month horizon, after cost from `bid_ask_pts` and turnover. Pass: positive in at least three of the four `CYCLE_WINDOWS`. And the 2009 drawdown of RM long-short is at most half the drawdown of total 6-month spillover on the same panel. And the hedged RM long-short beats our current EMC on the 6-month IC beyond spread.

## Risks
- Source HY panel, before cost (Table 5.6, p. 152): total spillover 5.79% a year (t 1.59), volatility 13.25%, Sharpe 0.44. Residual 6.13% (t 2.88), volatility 8.40%, Sharpe 0.73. After the βDEF hedge, residual 7.83% (t 4.58), volatility 6.86%, Sharpe 1.14. Against rating × maturity peers, residual 5.96% (t 3.21), Sharpe 0.81.
- The hedge uses an in-sample β (p. 139). The 1.14 overstates a live result.
- 2009: total spillover drawdown 80%, residual 25%. In 2003: −51% against −14% (pp. 128, 139). Figure 5.1 does not name the universe. The p. 128 sentence pairs them with ALL-universe volatilities (8.85% to 4.80%). The source gives no HY drawdown.
- The total-return version tilts to low default risk after equity sell-offs. In the lowest RMRF quintile, the HY winner-minus-loser rating gap is −1.98 notches (Table 5.4, p. 150). The time-varying DEF beta in HY falls from 1.02 to 0.41 with residuals (p. 138, Table 5.5).
- Overlap with EMC: total spillover loads on equity momentum, which halves its alpha. RM loads less. Loading on bond momentum is negative (p. 144). The source gives no correlation number.
- Disagreement: Dynkin's issuer-specific EMC gives IR 1.40 against 1.56 for total EMC, "no gain" (Table 15.14, PDF p. 537). That test uses a 12-month window, √k scaling and a 1-month hold. Van Zundert uses 36 months and a 6-month hold. Our test settles which applies to our HY panel.
- Costs: the chapter deducts none. Overlapping 6-month books replace about one sixth of the book each month.

## Open questions
- Skip month. The source says "lagged by one month" and gives no more detail. Our choice: skip month t, because a 0-skip version is our EMC. Test 0 skip as a check.
- Factor data. The repo has no RMRF or RF. Our choice: Ken French library for research. Live default: the same file with its download time as `available_at`.
- Bond weights within an issuer. The source uses market value. Our choice: market value (price x `amt_out`) when `bond_panel` carries `amt_out` for every bond of the issuer, else equal weights. The production panel has no `amt_out` today.
- One or three factors. Our choice: RMRF only, as the base case. FF3 is a robustness run.
- Sort scope. Our choice: across the HY panel, as the source does. A within-sector rank feeds OneScore.
