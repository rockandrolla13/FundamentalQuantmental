# F11. Change in option implied volatility (ΔImpVOL)

- **Rank:** 11. **Tier:** 2 (tested in credit, needs new data). **Status:** NEW. The known list holds the variance risk premium, which is an IV level. ΔImpVOL is a one-month change.
- **Source:** Cao, Goyal, Xiao, Zhan (2023), "Implied Volatility Changes and Corporate Bond Returns", Management Science 69(3), pp. 1375–1397. File `/home/ak/Documents/Quant Credit/CapArb/EBSCO-FullText-08_05_2026.pdf`. Pages below are journal pages. PDF page = journal page − 1374.
- **Reader blocks:** C-F1 (the signal) and C-F2 (lagged stock return control), `research/notes/quant-credit-review/out_C.md`. Every number below was checked on the source page.

## Claim
For US high yield bonds, an issuer whose ATM option implied volatility rose over the last month has a lower bond excess return next month. Score = −ΔImpVOL. The monthly rank IC of the score against the next 1-month excess return is positive within HY, beyond spread and beyond the lagged stock return.

## Definition
```latex
\Delta\mathrm{CVOL}_{i,t} = \mathrm{CVOL}_{i,t} - \mathrm{CVOL}_{i,t-1},\qquad
\Delta\mathrm{PVOL}_{i,t} = \mathrm{PVOL}_{i,t} - \mathrm{PVOL}_{i,t-1}
\qquad
\Delta\mathrm{ImpVOL}_{i,t} = \tfrac12\left(\Delta\mathrm{CVOL}_{i,t} + \Delta\mathrm{PVOL}_{i,t}\right),
\qquad \mathrm{score}_{b,t} = -\Delta\mathrm{ImpVOL}_{i(b),t}
```
Intuition: a bond is a short put on firm assets, so a rise in expected asset volatility lowers the bond value, and bond prices react late (pp. 1382, 1395).

What the source says:
- IV source: the OptionMetrics volatility surface (daily, kernel-smoothed, Cox-Ross-Rubinstein binomial IV). Not standardized options (p. 1378).
- Which IV: delta 0.5 (at the money), expiration 365 days, call (CVOL) and put (PVOL) separately (p. 1379). Not 30 days. The conclusion repeats "at-the-money options with 365 days of maturity" (p. 1395).
- Change: month-end observation minus the prior month-end observation (p. 1379, Table 1 notes).
- Skip: IV from one day before the date of the bond price. Skipping two days makes no material difference (p. 1379). The skip also removes the pre-March 2008 OptionMetrics 4:15 p.m. close bias (endnote 10, p. 1395).
- ΔImpVOL ≡ (ΔCVOL + ΔPVOL)/2 is the main variable (p. 1383). ΔCVOL − ΔPVOL does not predict bond returns: 10−1 return 0.13 (Table 3 Panel B, p. 1382).
- A percentage change gives a smaller 10−1 spread: −0.40% (t −3.93) (endnote 14, p. 1395). We use the simple difference.
- Winsorise all variables each month at 0.5% (Table 1 notes, p. 1379).
- Units: the paper reports IV in percentage points (mean ImpVOL 30.70, sd of ΔImpVOL 3.89, Table 1, p. 1379). OptionMetrics stores decimals. The score sign and rank do not depend on units.

Parameters (our module): month-end IV = latest IV row of the issuer in the last `WINDOW_DAYS` = 5 IV trading days of the month that end one trading day before the month's last IV date (`SKIP_DAYS` = 1). Our choice: the 5-day window copies the paper's bond price rule (last observation in the last five trading days, p. 1378). Winsorise the score across scored bonds at 0.5% each tail. Both CVOL and PVOL must exist at t and t−1, else NaN.

**Stock return control (C-F2).** The paper puts "stock return in the past month" (Lag stock return, defined p. 1388) in every controlled regression. Its slope is 0.070 (t 15.58) to 0.080 (t 14.83), and ΔImpVOL keeps a slope of −0.039 to −0.047 with it (models 2 to 5) (Table 5, p. 1387). IV rises come with stock falls: the formation-month 10−1 stock alpha is −9.93% (endnote 13, p. 1395). So the evaluation must control for it. The module returns it as the extra column `lag_stock_ret`. It is not part of the score.

## Inputs
| Field | Production table and column | as_of | available_at rule | Have |
|---|---|---|---|---|
| ATM call IV, delta 0.5, 365 days | new panel `option_iv.cvol` (OptionMetrics `vsurfd` days = 365, delta = 50, cp_flag C, `impl_volatility`) | `date` (trading day) | date + 1 day | need |
| ATM put IV, delta −0.5, 365 days | `option_iv.pvol` (`vsurfd` days = 365, delta = −50, cp_flag P) | `date` | date + 1 day | need |
| Issuer key | `option_iv.gvkey`. The export maps OptionMetrics `secid` to CRSP `permno` (WRDS OptionMetrics-CRSP link, best score), then `permno` to `gvkey` (CCM link, LC or LU, primary). One row per gvkey per date. | `date` | as above | need |
| Bond universe | `bond_panel` `date`, `cusip`, `gvkey` and the `eligible` columns | `date` | panel `available_at` | have |
| Rating class | `ratings.splticrm` via `hy.peers.rating_at` (optional) | `datadate` | panel `available_at` | have |
| Lag stock return | `equity_monthly.ret` at month t (optional) | `datadate` | panel `available_at` | have |

`option_iv` columns: `gvkey`, `date`, `cvol`, `pvol` (decimal), `available_at`. Optional `secid`. Without `option_iv` or `bond_panel` the score is empty.

## Build steps
1. Export `vsurfd` rows with days = 365 and delta ±50 from July 2002. Pivot to one row per secid and date with `cvol`, `pvol`. Map to gvkey. Set `available_at` = date + 1 day.
2. At each month end t, keep IV rows with `available_at` ≤ decision_time(t).
3. For months t and t−1, find the month's last IV date. Step back `SKIP_DAYS` trading days. Take the issuer's latest row in the 5 trading days that end there.
4. ΔCVOL, ΔPVOL, ΔImpVOL per gvkey. Also ImpVOL level = (CVOL + PVOL)/2 at t.
5. Copy to every eligible bond of the issuer in `bond_panel` at t. Score = −ΔImpVOL, winsorised at 0.5% each tail.
6. Add `rating_class` (from `ratings`) and `lag_stock_ret` (from `equity_monthly`, month t) as extra columns.

## Code placement
- `hy/factors/f11_delta_implied_vol.py`. `compute(panels, as_of, skip_days=1, window_days=5, winsor=0.005) -> pd.DataFrame`.
- Helpers: `month_end_iv`, `iv_change`, `winsorise`.
- Output columns: `date`, `cusip`, `score`, `available_at`, `gvkey`, `d_cvol`, `d_pvol`, `d_impvol`, `impvol`, `rating_class`, `lag_stock_ret`.
- Reuses `hy.backtest.decision_time`, `hy.backtest.eligible`, `hy.peers.rating_at`, `hy.peers.equity_momentum` (1 month).
- Docstrings cite methodology Section 8 (S6 rating migration: the signal predicts downgrades) and Section 9.1 (event risk).

## Tests
- Unit: no look-ahead (IV rows after decision time and rows dated after t change nothing). Skip day: a spike on the month's last IV day does not enter. Sign: an issuer with a rising IV scores below one with falling IV. Missing `option_iv` gives an empty frame. A missing call or put at t or t−1 gives NaN. Stale IV (no row in the 5-day window) gives NaN. Missing `ratings` or `equity_monthly` gives NaN extras only.
- Evaluation: monthly rank IC of score against the 1-month `realised_excess_return`, beyond `g_spread` and `lag_stock_ret`. Pass: positive in at least three of the four `CYCLE_WINDOWS` (2008, 2015, 2020, 2022). Also within the B-and-below cell, the decile 10−1 net of cost from `bid_ask_pts` has t < −1.65 (in the source's sign).

## Risks
- B and below, the source result: within rating quintile 5 ("BB+ to BB−, and below" splits quintiles 4 and 5), the 5−1 bond + stock alpha is −0.69% a month (t −2.14). Quintile 4 (BB): −0.51% (t −2.10). AAA to AA−: −0.09% (t −1.44) (Table 4 Panel A, p. 1384).
- Full sample: deciles on ΔCVOL + ΔPVOL give 10−1 −0.60% a month (t −3.62), bond + stock alpha −0.98% (t −5.57) (Table 3, p. 1382). Fama-MacBeth slope −0.051 (t −4.55) alone, −0.047 (t −4.89) with all controls (Table 5, p. 1387).
- Costs eat the HY effect. Junk, EHP $1M (30 bp): net return −0.32% (t −1.19), bond + stock alpha −0.54% (t −1.69). At $100K (100 bp) or BPW, the sign reverses. Turnover 1.71 a month (Table 11, p. 1394).
- Fast decay: predictability "declines rapidly" after the formation month (p. 1383, Online Appendix Table A1). Hold one month only.
- Overlap: ΔImpVOL correlates 0.11 with the ImpVOL level and −0.15 with the lagged bond return (Table 1 Panel B, p. 1379). A change in realized stock volatility does not replace it: ΔStock Vol slope 0.040 (t 1.43) (Table 5, p. 1387).
- Coverage: only issuers with listed options and a surface entry score. Private HY issuers get NaN.
- Sample: TRACE July 2002 to August 2017, IG and HY pooled, 881,625 bond-months, 2,327 firms (p. 1379). No post-2017 test.

## Open questions
- Maturity. The source uses 365 days. Our choice: 365 days. A 30-day IV is a robustness run only (the Online Appendix A tests other maturities, p. 1387, not read).
- Bond price date. The source skips one day before each bond's own price date. Our monthly panel has no per-bond price date. Our choice: one trading day before the month's last IV date.
- Weights. The source value-weights by prior-month bond market cap (p. 1380). Our choice: the evaluation uses `amt_out` x price when present, else equal weights.
- Score scope. Our choice: score every eligible bond. The B-and-below cell is an evaluation cut via `rating_class`.
