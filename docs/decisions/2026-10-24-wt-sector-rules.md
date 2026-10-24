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

## Pass rule, set before the run

A rule passes on a layer when all four hold. Layer 1 uses quarters: one observation every 4 quarters for the t, and Holm across the 15 rules on the primary outcome.

1. **Out of sample.** After December 2011, the date of the notes, the slope of the pair return on the signal has the
   claimed sign with an EWC t above 2. The t uses one observation every h months, so the windows do not overlap.
2. **Count of tests.** The p value survives Holm across the 15 rules on that outcome.
3. **Cycles.** The pair return is in the claimed direction in at least 3 of the 4 windows 2008, 2015, 2020, 2022.
   For stocks, the 2001 window is added. The rule needs 4 of 5.
4. **After cost.** Bonds only: the long-short return on the signal's sign is positive after the round-trip cost of
   both legs each h months.

Before December 2011 the rule is in sample: Wolfe Trahan saw that data. That period is reported, but it cannot pass.

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
