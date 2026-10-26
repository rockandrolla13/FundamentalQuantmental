# F16. Bond downside risk (5% VaR)

- **Rank:** 16. **Tier:** 3. **Status:** NEW risk leg. It takes the opposite sign of a low-risk tilt. Candidate control for the S1 residual (methodology Section 8) and input to F07.
- **Source:** Bali, Goyal, Huang, Jiang, Wen (2022), "Predicting Corporate Bond Returns: Merton Meets Machine Learning", SFI RP 20-110. File `/home/ak/Documents/Quant Credit/Missing Papers/bali-2022-bond-ml.pdf`. Printed page = PDF page − 2. Definitions: Appendix B items 6 to 9, printed pp. 29–30 (PDF 31–32). Returns: eq. 18, printed p. 11 (PDF 13). Feature importance: printed pp. 15–16 (PDF 17–18), Figure 4 printed p. 54 (PDF 56). Table 1: printed p. 40 (PDF 42).
- **Original measure:** Bai, Bali and Wen (2019, JFE). That paper is not in the folder. We did not open it. This page uses the definition as Bali et al. state it. Every number below was checked on the Bali et al. page.
- **Reader block:** H-F8 (`research/notes/quant-credit-review/out_H.md`). The reader cites "appendix p. 29". That is the printed page.

## Claim
In US high yield, bonds with a higher 5% VaR of their own monthly excess returns over the last 36 months earn a higher excess return over the duration-matched Treasury in the next month. The sign holds after control for rating class, duration and the S1 residual.

## Definition
```latex
\mathrm{VaR}_{q,i,T} = -\,r^{ex}_{i,(k)},\qquad
\mathrm{ES}_{q,i,T} = -\frac{1}{k}\sum_{j=1}^{k} r^{ex}_{i,(j)},\qquad
k = \max\bigl(1, \lfloor q\,n_{i,T} + 0.5 \rfloor\bigr)
```
Here r_(j) is the j-th lowest of the bond's n monthly excess returns in months T−35 to T. Intuition: a bond that lost a lot in its bad months carries tail risk, and a holder asks a premium for it.

What the source says:
- VaR5 is "the second lowest monthly return observation over the past 36 months", multiplied by −1 (item 6, p. 29). VaR10 is the fourth lowest (item 7, p. 29).
- ES5 is the average of the two lowest monthly returns over 36 months. ES10 is the average of the four lowest (items 8–9, pp. 29–30). The text states the −1 flip for VaR only.
- After the flip, a positive coefficient means "higher downside risk being related to the higher cross-sectional bond returns" (footnote 17, p. 29).
- Returns: r = (P_t + AI_t + C_t)/(P_{t−1} + AI_{t−1}) − 1. Excess return R = r − one-month T-bill (eq. 18, p. 11).
- The source gives no minimum count of returns for VaR. For the uncertainty beta it uses "the past 24 to 36 months of data (as available)" (item 34, p. 34).
- Horizon: one-month-ahead forecasts (p. 16).

What we decide:
- r_ex = total − tsy_ret of `hy.backtest.realised_excess_return` with beta 0, through `f04.monthly_excess_returns`. Our choice: the duration-matched Treasury replaces the T-bill, so the tail holds credit losses, not rate moves.
- Window T−35 to T, 36 months, no skip month (p. 29). Minimum n = 24. Our choice, after item 34.
- k rule: our choice. At n = 36 it gives k = 2 for q = 5% and k = 4 for q = 10%, the source values. At n < 36 it keeps the tail share near q.
- Gaps: only consecutive month-end pairs count (`max_gap = 1`). Our choice: a k-month return is not a monthly return. Stale and carried rows drop out (F04 rule).
- ES carries the −1 flip too. Our choice, so all four columns read "higher = more downside". No floor at zero.
- Control: `var5_ctrl` = cross-sectional OLS residual of VaR5 on rating class dummies, `mod_dur` and S1 `z` (`hy.signals.neutralise`). Without the S1 panel the control drops `z`. A bond with no `z` gets z = 0 and a missing flag in X.
- Score = standardised percentile rank of `var5_ctrl`. Higher score = long (footnote 17 sign). A date with fewer than 20 scored bonds (`hy.backtest.MIN_BONDS`) gets NaN.

## Inputs
| Field | Production table and column | as_of | available_at rule | Have |
|---|---|---|---|---|
| Monthly excess return | `bond_panel` `price`, `coupon`, `tsy_yield`, `mod_dur`, `accrue_to`, `hedge_date`, `carried`, `n_trades` | `date` | panel `available_at` | have |
| Eligibility | `bond_panel` `years`, `yield`, `g_spread`, `price` | `date` | panel `available_at` | have |
| Rating class | `ratings.splticrm`, else implied class from `leverage` | `datadate` | panel `available_at` | have |
| S1 residual | new panel `s1_residual`: `date`, `cusip`, `z`, `available_at` | `date` | z of Section 7.3 at month end, known at `decision_time` | need |

## Build steps
1. Keep rows with `available_at` <= `decision_time(T)`.
2. Universe at T: `eligible` row with a yield, class BB, B or CCC, raw S&P symbol not D or SD (F04 rule).
3. Build the monthly r_ex pairs for months T−35 to T. Drop stale and carried rows.
4. Per bond with n >= 24: compute VaR5, VaR10, ES5, ES10.
5. Neutralise VaR5 on rating dummies, duration and S1 z across the scored bonds.
6. Rank `var5_ctrl`, standardise, write `score`.

## Code placement
- `hy/factors/f16_downside_risk.py`. `compute(panels, as_of, window=36, min_obs=24, max_gap=1)`.
- Output columns: `date`, `cusip`, `score`, `available_at`, `gvkey`, `var5`, `var10`, `es5`, `es10`, `var5_ctrl`, `n_ret`, `ctrl`, `rclass`, `g_spread`, `mod_dur`, `s1_z`.
- Helpers: `tail_count(n, q)`, `value_at_risk(r, q)`, `expected_shortfall(r, q)`, `tail_measures(pairs, months, min_obs)`, `control_residual(y, rclass, mod_dur, z)`.
- Reuses `f04.monthly_excess_returns`, `f04.rating_classes`, `hy.backtest.decision_time`, `eligible`, `MIN_BONDS`, `hy.signals.neutralise`, `standardise_by_date`.
- Docstrings cite Section 8 (S1 control) and Appendix B items 6–9, p. 29.

## Tests
- No look-ahead: rows after T and revisions with `available_at` after the decision time change no score.
- Sign: a bond with two −8% months ranks above calm bonds on `var5`. VaR5 that only tracks rating class gives `var5_ctrl` near zero.
- Edges: n < 24 gives NaN. Gaps do not enter. Missing `bond_panel` or `ratings` gives an empty frame. Missing `s1_residual` drops z from the control. A D-rated issuer is not scored.
- Helpers: VaR and ES on a hand-sorted list of 36 returns. k = 2 and 4 at n = 36.
- Evaluation (production machine): Fama-MacBeth of the next-month HY excess return on VaR5 with rating, duration, S1 residual and F04 momentum controls, 2005–2024. Pass if the Newey-West t >= 2.5 (reader H-F8). Second test: monthly rank IC of `score` beyond `g_spread` (`ic_beyond`), h = 1, after cost, positive in at least three of the four `CYCLE_WINDOWS`. Third test: the same IC below 1,000 bp (`not_distressed`) stays positive.

## Risks
- No standalone premium in this file. The file reports feature importance only. The risk group (VaR, ES, coskewness, betas) ranks second after illiquidity (Figure 4, p. 54, text p. 16). Do not cite a premium from it.
- Distress proxy. VaR5 correlates with rating at 0.25, with bond market beta at 0.61 and with illiquidity at 0.19 (Table 1 Panel B, p. 40). The edge may be the CCC premium. The rating and S1 control and the sub-1,000 bp test check this.
- Factor alphas. Bali et al. report that the Bai, Bali, Wen four-factor model, with a downside risk factor, leaves no significant ML alpha (p. 17). That supports a priced factor, but the file shows no table.
- Sample. Table 1 pools IG and HY, July 2002 to December 2017, about 25% HY (p. 13). No HY-only result.
- Turnover is low: one new month enters the 36-month window each month.
- Survivorship. A bond that stops trading after a crash leaves the universe. Its loss sits in the carried row, not in a score.

## Open questions
- Benchmark. Source: T-bill excess return. Our choice: duration-matched Treasury. Rerun with `tsy_ret` = 0 to compare.
- Zero floor. Table 1 shows 5th and 25th percentiles of VaR5 at 0.00 (p. 40). The text gives no floor. Our choice: no floor. The Bai, Bali, Wen paper may settle it.
- Minimum count and k rule. Our choice: 24 and the rounded tail share. A run with fixed k = 2 and n = 36 only is the source form.
- Score form. Our choice: the controlled residual. The raw `var5` stays as a column for the Fama-MacBeth test.
