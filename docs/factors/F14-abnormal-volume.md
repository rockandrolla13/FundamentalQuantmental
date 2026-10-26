# F14. Bond abnormal trading volume

## 1. Header
- **Rank:** 14 of 30, Tier 3 (weak or control-only evidence). Status: NEW. A TRACE-only signal, plus a pre-event feature for Section 9.
- **Reader blocks:** C-F3, A1-F17.
- **Sources (all under `/home/ak/Documents/Quant Credit/`):**
  - Cao, Goyal, Xiao and Zhan, "Implied Volatility Changes and Corporate Bond Returns", *Management Science* 69(3), 2023, `CapArb/EBSCO-FullText-08_05_2026.pdf`. Data and filters p. 1378. Table 5 and text p. 1387. Printed journal pages.
  - "The Trading Dynamics of Corporate Bonds and Bond ETFs" (dissertation), `The Trading Dynamics of Corporate Bonds and Bond ETFs.pdf`. Data PDF p. 91, sample PDF p. 92, variables PDF p. 93, method PDF p. 94, results PDF pp. 95, 98 to 99, conclusion PDF pp. 106 to 107. PDF pages (printed page = PDF page − 14).
- **Not in the folder:** Gervais, Kaniel and Mingelgrin (2001), "The high-volume return premium", *J. Finance* 56(3). Cao et al. use "the procedure of Gervais et al. 2001" (p. 1387). The online appendix of Cao et al. is not in the folder either. So no file in the folder gives the window or the functional form of the monthly measure.

## 2. Claim
For US HY bonds, a bond whose par volume this month is high against its own trailing 12-month mean earns a higher excess return over the next month than a bond with low abnormal volume. The sign is positive. The evidence is weak: one control coefficient in one regression.

## 3. Definition
**Monthly measure (bond b, month end t).** V is the par volume of the month, n the trade count:

```latex
\text{AbnVol}_{b,t}=\ln\!\big(1+V_{b,t}\big)-\ln\!\Big(1+\tfrac{1}{K}\textstyle\sum_{k=1}^{K}V_{b,t-k}\Big),\qquad K=12
```
Intuition: this month's volume over its own trailing mean, in logs, so a bond that always trades much does not rank high only for its size.

- `abn_ratio` = V_t / mean(V_{t−1..t−K}), the plain ratio. `abn_trades` is the same log formula on n.
- **Issuer level.** V_{i,t} = Σ V_{b,t} over the bonds of issuer i that are eligible at t and have a full K-month history. The same formula gives `abn_vol_issuer`. A fixed bond set stops a new issue from inflating the issuer measure.
- **Score.** `score` = AbnVol winsorised at 0.5% and 99.5% across the month's scored bonds. Source: Cao et al. winsorise all regressors each month at 0.5% (p. 1387).

**Pre-event measure (Section 9).** The dissertation's equation (1), PDF p. 94, for firm i and day t:

```latex
\text{Abn}_{i,t}=X_{i,t}-\bar X_{i,[-40,-6]},\qquad z_{i,t}=\text{Abn}_{i,t}/\operatorname{sd}\big(X_{i,[-40,-6]}\big)
```
X is the daily average across the firm's bonds of par volume (`abn_vol_pre`) or of trade count (`abn_trades_pre`). Days count in trading days: the estimation window is "the 35 trading days prior to the event" (PDF p. 98). Intuition: trade before news flags informed or early positioning. z is our choice (reader A1-F17), because the difference in dollars does not compare across issuers.

What the sources say:
- Cao et al.: model (5) of Table 5 adds "Bond Abn. Volume" and "Stock Abn. Volume" as controls. Bond slope +0.034 (t = 2.10). Stock slope −0.016 (t = −0.89). 211,656 bond-months, adjusted R² 0.297, July 2002 to August 2017, Fama-MacBeth with Newey-West t, six lags (p. 1387). IG and HY pooled. The text: "bond abnormal volume predicts future bond returns, whereas stock abnormal volume does not" (p. 1387). Cao et al. add the control "in another attempt to control for illiquidity" (p. 1387). They keep trades under $10,000 (p. 1378).
- Dissertation: Enhanced TRACE, 2012 to 2021 (PDF p. 91). A bond enters an event when it trades once in [−5, +5] and once in [−40, −6] (PDF p. 92). Trade volume = daily average number of trades × average daily trade size (PDF p. 93). Bond trading rises after dividend changes, M&A, repurchases, SEOs and spin-offs, not after CEO turnover, splits or ticker changes (PDF pp. 106 to 107). Abnormal volume spikes on day −2 before involuntary CEO turnover in the figure (PDF p. 95). The table shows abnormal volume below normal on day −3 for the same events (PDF p. 99). The source reports volume only, no returns, and no earnings or rating events.

Our choice:
- Log of the ratio of this month to the trailing mean, K = 12 months (reader C-F3 proposal). We take the log of the mean, not the mean of logs: a zero month does not then dominate. The +1 is in par dollars and has no effect on traded bonds.
- Volume basis: `bond_panel.par_volume` covers the last 7 calendar days of the month (`hy.sources.trace_panel` rule 3). For a bond with `bond_daily` rows, the module sums the full calendar month (`volume_basis` "month"). Else it uses the panel window (`volume_basis` "window7"). The choice is per bond, so a partial `bond_daily` never sets a bond's volume to zero.
- A month with no panel row, or a carried row, after the bond's first row counts as V = 0. Months before the first row are missing. The score needs 6 of the K months (`MIN_HIST`).
- Pre-event day 0 is the first trading day after as_of. The pre window is days [−5, −1], the last 5 trading days on or before as_of. The trading-day calendar is the set of dates in `bond_daily`. Event types: `earnings`, `rating_review` (`hy.events.EventType`). The source studies other events, so this choice is untested.

## 4. Inputs
| Field | Table and column | as_of | available_at lag rule | Status |
|---|---|---|---|---|
| Month-end row, eligibility | `bond_panel` (`date`, `cusip`, `gvkey`, `years`, `price`, `yield`, `g_spread`, `mod_dur`, `carried`) | month end | last trade in window + 1 day | have |
| Par volume, trade count | `bond_panel.par_volume`, `n_trades` (last 7 days) | month end | as above | have |
| Daily par volume, trade count | `bond_daily.par_volume`, `n_trades` (extends F02's `bond_daily`: `cusip`, `date`) | trade day | trade day + 1 day | need (optional) |
| Event dates | new panel `events`: `gvkey`, `event_date`, `event_type` (`hy.events.EventType` value), `available_at` | event date | time the date is known: the earnings calendar date for a scheduled release, event day + 1 day otherwise | need (optional) |

Every row the score reads has `available_at` ≤ `decision_time(t)` = t + 1 day. Without `bond_daily` the monthly score still builds, and the `*_pre` columns are NaN. Without `events`, `next_event_type` and `days_to_event` are empty. Without `bond_panel` the result is an empty frame.

## 5. Build steps
1. Filter every panel to `available_at` ≤ t + 1 day.
2. Build monthly V and n per bond for months t − K .. t: the full-month sum of `bond_daily` for a bond with daily rows, else `bond_panel.par_volume` and `n_trades`. Zero-fill months after the bond's first row. A carried row is zero.
3. Keep bonds with an `eligible` row at t and at least `MIN_HIST` history months. Compute `abn_vol`, `abn_ratio`, `abn_trades`.
4. Winsorise `abn_vol` at 0.5% and 99.5% across the scored bonds. That is `score`.
5. Issuer level: sum V over the issuer's scored bonds with a full K-month history. Compute `abn_vol_issuer`. Copy it to each bond.
6. Pre-event: per issuer, the daily mean of `par_volume` and `n_trades` over its bonds with a trade in [−40, −6]. Compute Abn and z for days [−5, −1], and take the mean over the 5 days. Find the next known `earnings` or `rating_review` date after as_of. Write `next_event_type` and `days_to_event` (calendar days).
7. `event_abnormal(daily, events, bonds, as_of)` gives the source measure per past event (day 0 = the event day, days −5 to +5), for the Section 9 calibration on the production machine.

## 6. Code placement
- Module `hy/factors/f14_abnormal_volume.py`. `compute(panels, as_of, window=12, min_hist=6, pre_days=5, est=(-40, -6), event_types=("earnings", "rating_review"))`.
- Helpers: `monthly_volume`, `abnormal_log_volume`, `issuer_abnormal`, `daily_issuer_measure`, `abnormal_measure`, `pre_event`, `next_event`, `event_abnormal`.
- Docstring cite: methodology Section 8 (new signal) and Section 9.1 (pre-event feature of the earnings and rating review rows).
- Output columns: `date`, `cusip`, `score`, `available_at`, `gvkey`, `abn_vol`, `abn_ratio`, `abn_trades`, `n_hist`, `volume_basis`, `abn_vol_issuer`, `n_bonds_issuer`, `abn_vol_pre`, `abn_vol_pre_z`, `abn_trades_pre`, `next_event_type`, `days_to_event`.
- Reuse: `hy.backtest.decision_time`, `eligible`; `hy.factors.f02_spread_to_d2d.winsorise`; `hy.events.EventType`.

## 7. Tests
Unit tests (`tests/test_factor_f14.py`): contract columns, one row per cusip. No look-ahead: rows after t + 1 day do not change the output. Sign: a bond with a volume spike at t scores above a bond with flat volume. Helpers against hand values. Sparse trades: a missing month counts as zero, fewer than 6 history months gives NaN. Missing `bond_daily` or `events` gives NaN pre-event columns, and a missing `bond_panel` an empty frame.

Evaluation test (production machine): monthly rank IC of `score` against the next 1-month excess return (`realised_excess_return`, h = 1), beyond spread and after control for the lagged bond return. HY only. Pass: mean IC > 0 with HAC t ≥ 2, and positive in at least 3 of the 4 cycles (2008, 2015, 2020, 2022). Pre-event test (reader A1-F17): flag events with `abn_vol_pre_z` > 3. Pass when flagged events show a larger absolute day-0 spread change than unflagged events, at 5%.

## 8. Risks
- Weak evidence. One t of 2.10 in one specification, as a control, IG and HY pooled. Lag bond return enters the same model with t = −5.94 (p. 1387). So the volume slope is net of reversal, and our IC must also be net of it.
- Sign risk in HY. HY volume spikes often come with news (reader C-F3). Then a high-volume bond may fall next month. The pre-event column keeps that case apart.
- Noise. HY bonds trade little. The 7-day panel window makes the monthly measure noisier than a full-month sum. Prefer `volume_basis` "month".
- Overlap. Expected correlation with illiquidity (Amihud, rank 13) and with F05 flow pressure. No source states a value.
- New issues. Issuance volume enters the trailing mean for the first 12 months. That lowers `abn_vol` of a seasoned bond after a heavy start.
- Cost: a 1-month hold gives high turnover. Use it as a tilt or a condition on other signals, not alone.

## 9. Open questions
1. Window and form. Gervais et al. is not in the folder. Default: K = 12, log of ratio. Report K = 6 and the plain ratio as variants.
2. Volume or trade count. The dissertation reports both. Default: par volume. Report `abn_trades` IC beside it.
3. Event set. Earnings and rating reviews are our choice. The source supports M&A, dividend changes, repurchases, SEOs and spin-offs (PDF pp. 106 to 107). Pass `event_types` to add `mna_lbo`.
4. Issuer daily average. The source's "daily average ... for firm i" (PDF p. 94) does not say how it averages across bonds. Default: the mean over the bonds that trade in [−40, −6], zero on days without a trade.
