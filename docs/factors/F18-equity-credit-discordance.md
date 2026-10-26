# F18. Equity-credit discordance

- **Rank:** 18. **Tier:** 3. **Status:** variant of EMC (`hy/peers.py` `equity_momentum`): it reads the same stock move, but trades only when the spread moved the wrong way.
- **Source:** Kapadia and Pu (2012), "Limited arbitrage between equity and credit markets", JFE 105, 542–564. File `/home/ak/Documents/Quant Credit/CapArb/limited arb.pdf`. Pages below are journal pages. PDF page = journal page − 541. Minus signs in Tables 6 and 7 were checked on the page image, because text extraction drops them.
- **Reader block:** C-F4 (`research/notes/quant-credit-review/out_C.md`). Every number below was checked on the source page.
- **Substitution:** the source uses 5-year CDS spreads. We put the issuer's TRACE G-spread in their place.

## Claim
In US high yield, when an issuer's stock moved more than 3% over 5 trading days and its median bond G-spread moved the same direction as the stock, the bond spread catches up with the stock over the next month. So D = +1 bonds (stock up, spread wider) beat D = −1 bonds (stock down, spread tighter) in excess return over duration-matched Treasuries over 1 month. The source HY evidence for this claim is weak.

## Definition
```latex
\text{discordant}_{i,t} = \mathbb 1\!\left[\Delta S^{\tau}_{i,t}\; r^{\tau}_{i,t} > 0\right],\qquad
D_{i,t} = \operatorname{sign}\!\big(r^{\tau}_{i,t}\big)\,\text{discordant}_{i,t}\;\mathbb 1\!\left[\,|r^{\tau}_{i,t}| > 3\%\right]
```
```latex
\hat k_i = \sum_{\tau=1}^{M-1}\sum_{k=1}^{M-\tau}\mathbb 1\!\left[\Delta S^{\tau}_{i,k}\,\Delta P^{\tau}_{i,k} > 0\right],\qquad
\kappa_i = \frac{4\hat k_i}{M(M-1)} - 1,\qquad \bar\kappa_i = \tfrac12\ln\frac{1+\kappa_i}{1-\kappa_i}
```
Intuition: in the Merton model a stock rise always tightens the spread. A spread that moved with the stock is a price gap, and the gap closes.

What the source says:
- A pricing discrepancy is ΔCDS^τ ΔP^τ > 0 (eq. 2, p. 546). The Table 4 version uses the stock return ΔP/P including dividends over non-overlapping τ-day periods (p. 551). A zero product is not a discrepancy (p. 551).
- κ is the Kendall correlation of stock and CDS over all M(M−1)/2 date pairs (eq. 3, p. 546). κ = −1 is full integration. A higher κ is a less integrated market (p. 546).
- κ is estimated per firm for each calendar quarter, at weekly (τ = 5) or biweekly (τ = 10) intervals (pp. 547, 555). A 52-week history cuts the sensitivity of κ to mispricing from 1.35 to 0.82 (p. 548). Regressions use the Fisher z, κ̄ (p. 555).
- Trade rule: open a trade at t if ΔCDS^τ ΔP^τ > 0 and |ΔP^τ/P| > 3%, and no trade on the firm is open. Long stock and long CDS if the stock fell. Short both if it rose. τ = 5 with a 1-month hold, or τ = 10 with a 2-month hold. Stop at a 10% loss of initial equity. The hedge ratio comes from a regression of monthly ΔCDS on stock returns (p. 553).
- The 3% is "roughly consistent with the average absolute stock return for τ = 5 in Table 4" (p. 553). Table 4 gives 3.52% for discordant 5-day moves, all firms (p. 551).

Our choices:
- ΔS^τ_i = median over the issuer's bonds of the bond's g_spread change between the two days. A bond enters only with a spread on both days (exact days).
- The calendar is the issuer's equity trading days. r^τ compounds daily `ret` over the τ days. A missing `ret` counts as zero.
- κ: the last 63 trading days, sampled every τ days back from the last day. That gives M = 13 dates and 12 weekly steps, as in the source simulation (p. 547). A pair with no common bond is dropped. κ = 2 × (discordant pairs / valid pairs) − 1, which equals eq. 3 when all pairs are valid. κ needs 39 valid pairs (half of 78). κ̄ uses κ clipped to ±0.99.
- `score` = D at the last trading day on or before as_of (entry at the decision). `open_dir` applies the full source rule (one open trade per issuer, 1-month hold) to the daily series, and gives the direction of the trade open at as_of. No stop loss: a bond-only score has no hedged P&L.
- Bond leg only. The source trades stock and CDS together and does not say which leg converges. The bond leg may carry none of the return.

**Monthly fallback (flagged `freq_source = "monthly"`).** Without daily data for the issuer, r = the month's `equity_monthly.ret`, ΔS = median month-over-month change of `bond_panel.g_spread` over bonds with real rows at both month ends. The threshold is 6.73%: the source's rule (mean |ΔP/P| of discordant moves) at τ = 25 days, all firms (Table 4, p. 551). κ uses the last 13 month ends. The source warns that κ loses power over long windows (p. 548).

## Inputs
| Field | Production table and column | as_of | available_at rule | Have |
|---|---|---|---|---|
| Bond G-spread, month end; issuer key | `bond_panel` `g_spread`, `gvkey`, `carried` and the `eligible` columns | `date` | panel `available_at` | have |
| Daily stock total return | new `equity_daily` (`gvkey`, `date`, `ret`; same panel as F02) | trade day | trade day + 1 day | need |
| Daily bond G-spread | new `bond_daily` (`cusip`, `date`, `g_spread`; same panel as F02) | trade day | trade day + 1 day | need |
| Monthly stock total return (fallback) | `equity_monthly.ret` | `datadate` | datadate + 1 day | have, from 2007 only |

## Build steps
1. Keep rows with `available_at` ≤ decision_time(as_of). Map each cusip to its latest gvkey in `bond_panel` over the last 126 calendar days.
2. Per issuer, build the equity calendar and the price index P = cumprod(1 + ret).
3. Pivot `bond_daily` g_spread onto that calendar. Per day, ΔS^τ = median over bonds of the τ-day change. r^τ = P_t / P_{t−τ} − 1.
4. Take the last day e ≤ as_of. Drop the issuer from daily mode if e is more than 7 days before as_of. D = sign(r) where ΔS r > 0 and |r| > 3%, else 0. NaN where r or ΔS is missing.
5. κ over the 13 sampled dates. `open_dir` from the no-overlap trade scan over the last three months.
6. Issuers without a daily score use the monthly fallback.
7. Copy the issuer D to each eligible bond of the issuer at as_of.

## Code placement
- `hy/factors/f18_equity_credit_discordance.py`. `compute(panels, as_of, tau=5)`. Helpers `discordance_signal`, `kendall_kappa`, `fisher_z`, `trade_entries`, `issuer_spread_change`.
- Output columns: `date`, `cusip`, `score`, `available_at`, `gvkey`, `freq_source`, `stock_ret`, `d_spread`, `n_bonds`, `discordant`, `kappa`, `kappa_z`, `n_pairs`, `open_dir`, `open_since`.
- Methodology Section 8: a short-horizon overlay on S2. κ can also condition S1 (trust S1 less when κ is high).

## Tests
- Unit: no look-ahead (rows after as_of change nothing). Sign: stock −5% with a tighter spread gives −1, stock +5% with a wider spread gives +1, a concordant move gives 0. κ = −1 on a Merton path, +1 on a fully discordant path, and the eq. 2 example of p. 546. Missing optional panels give the monthly fallback or an empty frame. Sparse trades give NaN, never 0.
- Evaluation: weekly D on HY issuers, 2005–2024. Mean 20-day bond excess return of D-signed positions > 0 with t > 2 after 30 bp round trip, hit rate > 52% (reader block proposal). Also the monthly rank IC beyond spread, 1-month horizon, positive in at least three of the four cycles (2008, 2015, 2020, 2022).

## Risks
- **Weak HY evidence.** HY firms, per-trade mean excess return, 1-month rule: −0.05% before the crisis (median 0.00%, 92 firms) and 0.19% in 2008 to March 2009 (median −1.18%). The 2-month rule: 0.27% and 3.25% (Table 6, p. 554). All firms: 0.24% and 1.21%. The source gives no t-statistic per rating group.
- **Costs are large.** The source deducts only funding cost (p. 553). A trade lasts at most a month, and firms average 32.6 trades in 2001–2007 (HY, Table 6). One HY bond round trip can cost more than the 0.24% gross mean of all firms. The HY 5-day discrepancy is a mean |ΔCDS| of 19.75 bp against 35.27 bp for concordant moves (Table 4, p. 551).
- **Risky trades.** About 8 of 32 trades hit the stop before the crisis. In the crisis it was 5.7 of 10.7 (p. 555). The strategy lost much money in late 2007 and 2008 (Fig. 4).
- **Frequency.** 5-day discrepancies are 40.75% of all observations, 38.79% in HY (Table 4, p. 551). HY κ̄ has a mean of −0.34 at τ = 5 (Table 7, p. 555).
- **TRACE noise.** A bid-ask bounce in a thinly traded bond can look like a discordant move. The median across bonds damps this only for issuers with several bonds.
- **Overlap.** D is short-term stock momentum on a subset, so expect overlap with EMC and F03. The source gives no correlation number.

## Open questions
- Exact days for bond spreads. Our choice: exact. A 1-day tolerance raises coverage but mixes stale prints. Test both.
- τ = 5 or 10. Our choice: 5, the stronger rule for all firms. HY pre-crisis favours τ = 10 (0.27% against −0.05%).
- Fallback threshold. Our choice: 6.73% (all firms). The HY row of Table 4 gives 8.63%.
- Score at month end or open trade. Our choice: `score` = entry at as_of. `open_dir` is the source-rule version for the daily test.
