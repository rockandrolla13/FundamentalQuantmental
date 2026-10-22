# Alpha backtest design (Sections 7.5 and 11)

## Context
Section 7.5 predicts the alpha of a hedged long: carry plus the part of the fair-line gap that closes inside the horizon, less cost and expected loss. No test showed that the prediction ranks bonds or has the right size. The writeup `docs/writeup/rv_pairs.tex` lists five test steps. The project bar (CLAUDE.md) asks for a positive rank IC after costs in at least three of the four cycles 2008, 2015, 2020, 2022. The test must beat the simplest rule, "buy the widest bonds", or the model adds nothing.

## Options
1. Weekly replay, bond-level OAS, rating-based PD. Not possible now: no OAS, no ratings, and a weekly TRACE pull costs four times the monthly one.
2. Monthly replay on TRACE month-end prices and G-spreads, Compustat point-in-time leverage, and the Section 7.5 formula without the macro paths and without the loss term. Compare against `widest` on the same bonds.
3. Option 2 on the issuers of the existing pair report only (8 issuers). Too small for a cross-sectional IC.

## Choice
Option 2. Code: `hy/sources/trace_panel.py` (panel, link, leverage), `hy/backtest.py` (realised alpha, predictors, scores, look-ahead guard), `scripts/backtest_alpha.py` (run). Write-up: `docs/writeup/backtest_alpha.pdf`.

Decisions inside the choice:
1. **Universe.** TRACE grade 'H' from the master version in force at each month end, fixed coupon, not convertible. Rule: no look-ahead on the master.
2. **Price.** Par-weighted over the last 7 calendar days of the month, trades of 100k par or more, cancels and corrections removed in all three TRACE status eras (T/C/W, G/H/I, M/N/O; each links by `orig_msg_seq_nb`, checked on WRDS), reversals dropped.
3. **Survivorship.** A bond that stops trading keeps one carried row at its last price, then leaves. Coupon accrual stops at the last trade. A matured bond redeems at 100.
4. **Realised alpha.** Total return minus the duration-matched Treasury total return (carry and price) minus beta x the benchmark spread return (carry and price), beta = 1. The carry parts are in both hedges so that realised alpha matches the Section 7.5 carry term (s - beta S) h. The benchmark is the month's median G-spread of eligible bonds priced 80 or more, 1 to 15 years.
5. **Predictors.** `widest` = G-spread. `fair_conv` = D (1 - rho^h)(s - s_fair). `fair_line` = carry + `fair_conv`. `fair_line_net` = `fair_line` - round-trip cost. s_fair = s exp(-eps), where eps is the issuer's log residual from log s_5y = a + b leverage, fitted each month on that month's data only. rho is one pooled monthly AR(1) slope over past residuals (expanding window; the prior 0.85^(1/3) until 3,000 pairs exist).
6. **Leverage.** Plain debt over LTM EBITDA before special items. The Compustat PIT history has no lease field, so the lease adjustment of Section 4.3 is off (flagged).
7. **Cost.** Bid-ask in price points: dealer-sell minus dealer-buy price to customers (the `side` field, from about 2012), else the mean intraday high-low on days with two or more trades, else the month's median. Round trip = one full spread.
8. **Loss term.** Off. No PD in the panel.
9. **Inference.** Newey-West with h - 1 lags on the monthly IC and long-short series; Driscoll-Kraay standard errors (Newey-West on per-date score sums) for the pooled Mincer-Zarnowitz regression.
10. **Cycle windows (formation month).** 2008-01 to 2009-12; 2015-01 to 2016-12; 2020; 2022.

## Result (2008-01 to 2026-08, 224 months, 13,271 bonds of 1,964 issuers in the scored set)
1. **`fair_line` does not beat `widest`.** IC after cost: widest 0.22 (t 6.8) against fair_line_net 0.21 (t 7.7) at 3 months; 0.29 (t 6.2) against 0.25 (t 6.2) at 6 months.
2. **The leverage residual adds a little.** IC of `fair_conv` against realised alpha with the spread rank removed: 0.036 (t 2.2) at 3 months, 0.048 (t 1.9) at 6 months.
3. **The size is wrong.** Mincer-Zarnowitz slope 0.07 (se 0.05) for fair_line at 3 months, 0.08 at 6 months. The pilot 2019-2026 gives 0.25 to 0.31. The model predicts the right order but sizes far too big, most of all in the tails.
4. **The cycle bar passes, with a caveat.** IC after cost is positive in all four cycle windows for every predictor. In calendar years 2008 and 2015 the IC is negative for every predictor; the recovery years 2009 and 2016 carry the two-year windows.
5. **Long-short after cost does not compound.** Top-minus-bottom decile, fair_line at 3 months: mean +5.3% a year (t 0.8), compounded -0.9% a year, drawdown -65%. Widest: +7.1% (t 1.1), compounded +1.4%.
6. **Robustness.** Skip a month between signal and return: ICs fall by about 0.02, ranking unchanged (no bid-ask bounce). Issuers linked by CUSIP only: same ICs.

## Test
Offline: `tests/test_backtest.py` (realised alpha by hand, exit at last price, flat trading, Newey-West against the AR(1) long-run variance, IC of a perfect and a noise predictor, Mincer-Zarnowitz recovers b = 1 and b = 1/3, decile long-short sign and cost, PIT uniformity, cycle windows, fair-line and rho recovery, the look-ahead fixture that must fail, and a replay spy). `tests/test_trace_panel.py` (cleaning in all three status eras, volume parsing, the monthly aggregate, bid-ask proxy, exit rows, link order, point-in-time leverage with a restatement).

Open tests that settle the rest:
1. Add a PD by rating cell and turn on the loss term. Pass: the MZ slope of `fair_line_net` rises toward 1 and the widest decile stops dominating the error.
2. Add lease liabilities from XBRL (`hy/sources/xbrl_instance.py`). Pass: the beyond-spread IC of `fair_conv` rises above t = 3.
3. Replace modified duration by an option-adjusted duration. Pass: the mean realised alpha of the middle deciles moves toward zero.

## Addendum: two-clocks signals (Section 4.7, combined-score estimate E5)

### Context
The combined score uses E5 = -(fixed charges in years of EBITDAR), untested. The pair report uses the duration gap and the renewal-dependent share as risk metrics. The question: does any clock measure predict hedged excess return beyond spread level?

### Options
1. Full XBRL instances per filing (`clock_case`): RPO timing included, but about 50,000 instance downloads.
2. SEC companyfacts, one document per issuer: every filing's undimensioned facts, no RPO timing.
3. Analyst inputs for a few issuers: no cross-section.

### Choice
Option 2. Code: `hy/sources/clock_facts.py` (fetch, per-filing clocks, monthly signals), `scripts/backtest_clocks.py` (run), `backtest.ic_beyond` (incremental IC). The clock code runs unchanged on each filing (`schedules.ladder`, `reconcile_debt`, `clocks.mismatch`). Decisions:
1. Obligations = lease, debt principal, and purchase ladders. No interest, no leases not yet commenced. Compustat debt fills a filing with no debt tag (5% of issuer-months).
2. RPO timing = the `clock_inputs` default (even over 2 years), because companyfacts drops timing dimensions.
3. Point in time: filing date + 1 day. A missing ladder carries forward up to 400 days, aged.
4. Signals signed as the score uses them: `e5`, `dgap` = -duration gap, `renew` = -renewal-dependent share where RPO >= 25% of LTM revenue.

### Result (formation months 2018-01 to 2026-08; 1,143 issuers for e5, 343 for dgap, 187 for renew)
1. Fixed-charge years rank with spread as expected: rank correlation +0.32 (t 36).
2. IC after cost: e5 -0.082 (t -4.5) at 3 months, -0.114 (t -4.7) at 6 months. Opposite to the E5 sign: high-charge issuers earned their extra spread.
3. IC beyond spread: e5 -0.011 (t -0.7) and -0.032 (t -1.2); dgap +0.015 (t 1.2) and +0.015 (t 1.0); renew -0.021 (t -1.4) and -0.035 (t -1.8). None is significant.
4. Cycles covered (2020, 2022): e5 negative in both; dgap positive in both at 3 months only; renew mixed.
5. Recommendation: set the E5 weight in the alpha estimate to 0 and keep the clocks as risk measures (S9 pair report, memo section 5). The market prices the clock; we found no edge in it. Not adopted: the user set the clocks bucket to 20% (decision page 2026-10-22-four-group-combination.md), and that choice stands until the user changes it.

### Test
Offline: `tests/test_clock_facts.py` (tag mapping, ladder gap fill, per-filing clocks against `hy.clocks` by hand, carry and ageing, the 400-day limit, monthly signals with the look-ahead guard, Compustat debt fallback, extraction filter, sec.gov-only fetch, and `ic_beyond` on synthetic data).
Open test that would reverse the decision: rebuild dgap and renew with the dimensional RPO timing from full instances for the 343 RPO issuers. Pass: IC beyond spread above zero with t > 2 at 6 months.
