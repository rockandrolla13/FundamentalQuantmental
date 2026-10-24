# Decision: test the Wolfe Trahan sector rotation claims as trades

Date: 2026-10-24. Status: **rules frozen, awaiting the user's check. Nothing has run.**
Sections touched: methodology Section 8 (sector signals), Section 5.2. Source: `research/wolfe-trahan-2011-relationships.csv`.

## Context

The earlier study tested 8 claims on company EBITDA, margins and sales. Most sector rows of the sheet say something
else: a macro series leads the **relative performance** of one group of stocks against another. Those claims are
trades, and nobody has tested them yet. This page turns each such row into one rule before any data is read.

## How a row becomes a rule

1. **Signal.** The macro series in the row, known at month end t with its release lag. A diffusion index enters as
   its level. CPI, oil, new home sales and owners' equity enter as the change over 12 months. The 10-year yield
   enters as its change over 12 months, because its level trends. Each signal is standardised with its own history
   up to t only.
2. **Sign.** The direction the note states. "Inverted" in the chart title flips the sign.
3. **Lead.** "Advanced NM" in the chart title means the signal leads by N months. The holding period h equals N. A
   row with no stated lead says the series move together. For such a row, h = 3 months: the test asks whether the
   signal known at t predicts the next 3 months. A move-together claim is a trade only if this holds.
4. **Pair.** Long group minus short group. Groups follow the note's own definitions (row 85, row 96):
   - Hyper cyclicals: information technology (GICS 45) and financials (40).
   - Counter cyclicals: health care (35), consumer staples (30), utilities (55).
   - Early cyclicals: consumer discretionary (25). Late cyclicals: industrials (20).
   - Market: all sectors.

Proxies: ISM is not free. The Philadelphia Fed survey stands in: general activity (GAC) for ISM, new orders (NOC)
for ISM new orders, prices paid (PPC) for ISM prices paid. NAHB is not in our data.

## The 15 rules (19 of the 60 sector rows)

| Rule | Rows | Signal | Claimed sign | h | Long minus short |
| --- | --- | --- | --- | --- | --- |
| R1 | 85, 130 | Activity (GAC) | + | 3 | Hyper minus counter cyclicals |
| R2 | 152 | CPI, 12-month change | - | 6 | Hyper minus counter cyclicals |
| R3 | 73, 96 | CPI, 12-month change | - | 3 | Early minus late cyclicals |
| R4 | 94 | Prices paid (PPC) | + | 3 | Late minus early cyclicals |
| R5 | 47 | CPI, 12-month change | - | 3 | Consumer discretionary minus market |
| R6 | 78 | Oil, 12-month change | + | 3 | Energy (10) minus consumer discretionary |
| R7 | 114 | 10-year yield, 12-month change | - | 3 | Utilities minus market |
| R8 | 115 | Activity (GAC) | - | 3 | Utilities minus market |
| R9 | 55 | New orders (NOC) | + | 3 | Financials minus market |
| R10 | 57, 63 | Activity (GAC) | + | 3 | Financials minus market |
| R11 | 61 | 10-year yield, 12-month change | + | 3 | Financials minus non-financials |
| R12 | 66 | Prices paid (PPC) | + | 6 | Real estate (60; group 4040 before 2016) minus financials |
| R13 | 103 | Household owners' equity, 12-month change | + | 3 | Financials minus market |
| R14 | 133 | New home sales, 12-month change | + | 3 | Banks (group 4010) minus market |
| R15 | 64 | Activity (GAC) | + | 3 | Diversified financials (4020) minus insurance (4030) |

## Outcomes: three layers per rule

Each rule is tested on the same signal and the same pair at three layers. The order matters: fundamentals first,
then prices. The pattern across the layers says why a rule works or fails.

**Layer 1. Fundamentals (user decision 2026-10-24: earnings and EBITDA are the primary question).**
Compustat quarterly, 1994-2026, all US firms with LTM sales above 40m, and separately the HY issuers of the TRACE
panel. Each firm counts equally. The group value is the median firm. The pair value is long group minus short group.

| Outcome | Non-financial pairs (R1-R8) | Financial pairs (R9-R15) |
| --- | --- | --- |
| EBITDA | LTM EBITDA change over the next 2 and 4 quarters, divided by LTM sales | Not used: banks and insurers have no EBITDA |
| Earnings | LTM income before extraordinary items (`ibq`), change over 2 and 4 quarters, divided by LTM sales | Same change divided by book equity (change in ROE) |
| Margin | LTM EBITDA margin, change over 4 quarters | LTM earnings over assets, change over 4 quarters |
| Sales | LTM sales growth over 4 quarters | LTM revenue growth over 4 quarters |
| Leverage | Debt over LTM EBITDA, change over 4 quarters | Not used |

The primary fundamental outcome is EBITDA over 4 quarters for R1-R8 and earnings over 4 quarters for R9-R15. The
others are reported beside it and do not pass a rule on their own.

**Layer 2. HY bond returns.** TRACE panel 2008-2026. Sector credit excess return (total minus Treasury) over t to
t + h, equal weight per sector, from `results_h{3,6}_full`. A sector needs 10 bonds in the month. A rule whose groups
lack bonds is reported as "no data", not as a fail.

**Layer 3. Stock returns.** CRSP monthly returns 1994-2026, the 500 largest US stocks each month, value weight per
sector. This gives 32 years and the 2001 recession.

**What the pattern means.**

| Fundamentals | Bond returns | Reading | Use in the model |
| --- | --- | --- | --- |
| Pass | Fail | The signal predicts the business, and the market prices it in time | A driver shift in the cases (door B), not alpha |
| Pass | Pass | The market prices the business news late | A sector signal in Section 8: alpha |
| Fail | Pass | Prices move for another reason: risk appetite or flows | A sector timing signal, with no fundamental story |
| Fail | Fail | The claim does not hold | Drop |

A lead-lag check goes with each passing rule: does the spread move before or after the reported EBITDA?

## How the test is built

1. **Data pull (WRDS, cached, out of git).** `comp.fundq` for all sectors including financials and real estate:
   `saleq`, `oibdpq`, `ibq`, `atq`, `ceqq`, `dlttq`, `dlcq`, `rdq`. `comp.co_hgic` for the GICS sector in force on
   each date. `crsp.msf` with the CCM link for stock returns. FRED: new home sales (HSN1F) and household owners'
   equity (OEHRENWBSHNO). The existing files lack net income and financial firms.
2. **Point in time.** A quarter's numbers count as known on the report date `rdq`, or 90 days after the quarter end
   when `rdq` is empty. Each macro value counts as known after its release lag. The GICS sector is the one in force
   at t. The outcome window starts after t.
3. **Signals.** One function per rule builds the standardised signal at each month end, using only history up to t.
4. **Outcomes.** One function per layer builds the pair value for each rule and date.
5. **Scoring.** The pass rule below, applied per rule and per layer, with the same code as `scripts/wt_tests.py`
   (EWC t, Holm, cycle windows).
6. **Tests first.** Unit tests check no look-ahead in the signal, the report-date rule, the GICS date rule, the pair
   sign, and the inverted-chart sign flip. They are written before the run.

Known limit: `comp.fundq` is the current view, not the first report. Restatements can make the past look smoother.
The earlier study carried the same limit. The HY-issuer subset uses point-in-time vintages where they exist.

## Detailed specification, frozen before the run

### S1. Dates and samples

| Layer | Decision dates t | Outcome window | Sample of t | Out of sample (can pass) |
| --- | --- | --- | --- | --- |
| 1 Fundamentals | Calendar quarter ends | Fiscal quarters q+1 to q+k after the quarter q that ends at t; k = 2 and 4 | 1994Q1 to the last q with q+k reported | 2012Q1 onward |
| 2 HY bonds | Month ends | t to t+h months; h from the rule table | 2008-01 to 2026-08 minus h | 2012-01 onward |
| 3 Stocks | Month ends | t to t+h months | 1994-01 to 2026 minus h | 2012-01 onward |

The notes are dated May to November 2011. Every t before 2012 is in sample: it is reported and cannot pass.

### S2. Signals

1. **Raw value `X_t`.** The last value published by t:

| Series | Source | Release lag | Transform |
| --- | --- | --- | --- |
| Activity (GAC), new orders (NOC), prices paid (PPC) | Philadelphia Fed survey, seasonally adjusted | 0 months (published inside its month) | Level |
| CPI | FRED CPIAUCNS | 1 month | log change over 12 months |
| Oil | FRED WTISPLC | 0 months (monthly average) | log change over 12 months |
| 10-year yield | FRED GS10 | 0 months (monthly average) | change over 12 months, in points |
| New home sales | FRED HSN1F | 1 month | log change over 12 months |
| Household owners' equity | FRED OEHRENWBSHNO | 3 months (Z.1 release) | log change over 4 quarters |

2. **Standardise with the past only.** `z_t = (X_t - mean(X_s, s <= t)) / sd(X_s, s <= t)`, with at least 60 months
   of history. All series start before 1975, so every t from 1994 has a value.
3. **Apply the claimed sign.** `zs_t = sign_r * z_t`, with `sign_r` from the rule table. A positive slope then always
   means "the claim holds".

### S3. Groups

1. GICS sector of each firm at t from `comp.co_hgic` (the record with `indfrom <= t <= indthru`). For the HY layer,
   `gics_history` as before.
2. Groups as defined above. Real estate is sector 60 from September 2016 and industry group 4040 before.
3. Minimum size per group and date: 20 firms (all US firms), 5 firms (HY issuers), 10 bonds (bond layer), 5 stocks
   (stock layer). Below the minimum the date drops out for that rule.

### S4. Firm outcomes (layer 1)

All sums are over four consecutive fiscal quarters (LTM). A gap leaves the value empty. Firms need LTM sales above
40m at q.

| Name | Formula | Used for |
| --- | --- | --- |
| `d_ebitda_k` | `(EBITDA_LTM[q+k] - EBITDA_LTM[q]) / Sales_LTM[q]` | Primary, R1-R8 |
| `d_earn_k` | `(IB_LTM[q+k] - IB_LTM[q]) / Sales_LTM[q]` | Reported, R1-R8 |
| `d_roe_k` | `(IB_LTM[q+k] - IB_LTM[q]) / CEQ[q]`, CEQ > 0 | Primary, R9-R15 |
| `d_margin_4` | `EBITDA_LTM / Sales_LTM`, change q to q+4 (financials: `IB_LTM / AT`) | Reported |
| `g_sales_4` | `log(Sales_LTM[q+4] / Sales_LTM[q])` | Reported |
| `d_lev_4` | `Debt / EBITDA_LTM`, change q to q+4, EBITDA > 0 at both ends, clipped to [0, 20] | Reported, R1-R8 |

EBITDA = `oibdpq`. IB = `ibq`. Debt = `dlttq + dlcq`. Each outcome is winsorised at 1% and 99% within each quarter.
The group value is the median firm. The pair value is `P_q = G_long - G_short`.

Scaling by sales, not by EBITDA, keeps firms with small or negative EBITDA in the sample with a finite value.

### S5. Return outcomes (layers 2 and 3)

1. **Bonds.** Per bond, `x = total - tsy_ret` over t to t+h (from `results_h{h}_full`). Winsorise at 1% and 99% per
   month. The sector value is the equal-weight mean of its bonds. The pair value is long minus short.
2. **Stocks.** CRSP `msf` return with the delisting return. The universe is the 500 largest US common stocks by
   market value at t. The sector value is the value-weight mean, with weights at t. The h-month return compounds
   the monthly returns.

### S6. The regressions

**Layer 1, primary.** One regression per rule, quarterly:

`P[q -> q+k] = a + b * zs_t + c * P[q-k -> q] + e`

The control `P[q-k -> q]` is the pair's own last change. EBITDA trends persist. A signal that only repeats last
year's trend adds nothing new, and this control removes that trend.

**Layers 2 and 3.** One regression per rule, monthly:

`R[t -> t+h] = a + b * zs_t + e`

Returns have little persistence, so no lag control.

**Standard errors.** EWC (Lazarus, Lewis, Stock and Watson 2018) on all dates, overlapping windows included.
`nu = floor(0.4 * T^(2/3))`. The p value is one-sided from Student t with nu degrees of freedom. The same function
as `scripts/s_tests.py`.

**Holdout race.** An expanding-window forecast from 2000, scored on 2012 onward. Layer 1: the baseline is the
regression without `zs_t`. Layers 2 and 3: the baseline is the past mean of the pair return. The test is Clark and
West (2007), one-sided, on the losses of forecasts whose outcome is known before the forecast date.

### S7. The pass rule

A rule passes on a layer when all five hold, out of sample:

1. **P1 direction.** `b > 0` with EWC one-sided p below 0.05.
2. **P2 count of tests.** The Romano-Wolf stepdown p (Romano and Wolf 2005) across the 15 rules of that layer is
   below 0.05. The null draws come from a stationary bootstrap of the signals (Politis and Romano 1994, mean block
   8 quarters or 24 months, 1,000 draws). The bootstrap moves all signals together and keeps outcomes and controls
   fixed. Holm is reported beside it.
3. **P3 forecast gain.** The Clark-West p is below 0.05.
4. **P4 cycles.** The mean of `zs_t * P` is above 0 in at least 3 of the 4 windows (2008, 2015, 2020, 2022). The
   stock layer adds 2001 (2001-01 to 2002-12) and needs 4 of 5. A window counts by the start date of the outcome.
5. **P5 cost (bond layer only).** Hold the pair on the sign of `zs_t`, rebalance every h months, and pay the
   round-trip cost of both legs at each rebalance. The mean net return is above 0.

Layer 1 is judged on its primary outcome only: `d_ebitda_4` for R1-R8 and `d_roe_4` for R9-R15. It is judged twice,
on all US firms and on HY issuers. The rule passes layer 1 if it passes on all US firms. The HY-issuer result says
whether it also holds where we invest.

### S8. Robustness, reported, never used to pass

1. The signal as a 6-month change instead of a level (diffusion indexes), or as a level (changes).
2. k = 2 quarters.
3. Sales-weighted groups instead of the median firm.
4. Without 2020.
5. Wider late cyclicals: industrials, materials and energy.
6. The lead moved by one quarter either way.
7. The share of all 6 variants that keep the sign (a specification curve).

### S9. Data checks before scoring

1. Every firm-quarter value has `available_at = rdq`, or the quarter end plus 90 days when `rdq` is empty. An
   assertion checks that each outcome window starts after t and each signal value is known by t.
2. Count firms per group and date, and print the dates that drop out.
3. Rebuild one rule by hand for one date and compare it with the script.

### S10. Outputs

1. `data/raw/backtest/wt_sector_rules.json`: per rule and layer, `b`, EWC t and p, Romano-Wolf p, Holm, Clark-West p,
   cycle means, P1 to P5, the number of dates, and the in-sample (pre-2012) result.
2. One figure per passing rule: the signal against the pair outcome at the three layers.
3. A results section on this page and a LaTeX write-up with a one-line verdict per rule and the pattern table
   reading (fundamentals against bond returns).

## Rows not turned into rules, and why

| Rows | Reason |
| --- | --- |
| 34, 104, 105, 116, 157 | Performance leads the macro series. That is a forecast of the economy, not a trade |
| 42, 49, 52, 58, 59, 131, 134, 138 | Macro series against macro series. No sector return |
| 13, 14, 15, 16, 17, 18, 19, 20, 21, 22 | A pair inside one sector as a "leading indicator of cyclicality". No target series |
| 48, 67, 68, 69, 132 | Describe past returns or correlations (beta, P/E, style, CPI correlation). No forecast |
| 62 | Bank net interest margin. A fundamental, and HY has too few banks |
| 65 | NAHB is not in our data. Add it if a file is supplied |
| 140 to 151 | Freight and shipping series with no partner series |

## The test that settles it

`scripts/wt_sector_rules.py` writes `data/raw/backtest/wt_sector_rules.json`. A rule that passes on bonds becomes a
candidate sector signal in Section 8 and goes to the composite only after the robustness checks of the earlier
study (placebo, Romano-Wolf, specification curve).

## Results

Not run.
