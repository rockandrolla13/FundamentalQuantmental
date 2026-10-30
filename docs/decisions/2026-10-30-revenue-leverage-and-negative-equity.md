# Debt to revenue and negative book equity: two features on test

Date: 30 October 2026. Status: proposed, not run. Script: `scripts/lev_tests.py`. Tests: `tests/test_lev_tests.py`. Methodology 4.3, framework F8.

## Context
The source is the notebook of github.com/MayCooper/Debt-to-Equity-and-Revenue-Profiling. We copy no code from it: it has no licence and no data file, and it does not run from a clean start.

- What the source says: negative debt to equity shows instability, and debt over revenue shows revenue sufficiency.
- What the data says: 6 of the 7 negative equity firms in its output show margins above 30%. Its sample is about 150 firms, with no dates, spreads, or returns. So the source settles nothing.
- What we decide: test both ideas on our own data, and add neither before the test passes.

## The two features
**L1, debt to revenue.** `log(clip(debt / sale, 0.01, 50))`. Intuition: when EBITDA is negative, leverage ties every issuer at the cap, and revenue still ranks them. Claim: inside EBITDA at or below zero, a higher ratio predicts failure beyond size.

**L2, negative book equity.** `ceq < 0`. Intuition: losses can erase equity, but a buyout or a buyback can erase it too. Claim: the flag predicts failure beyond leverage and size. The source implies this claim. Its own output argues against it.

## Options
1. Add both features to `hy/state.py` now. Rejected: no evidence.
2. Reject both now. Rejected: the capped leverage has a real blind spot among negative EBITDA issuers.
3. Test on Compustat first. Chosen.

## The step
1. In a terminal, from the repo root, run `PYTHONPATH=. python3 scripts/lev_tests.py`. WRDS may ask for a login.
2. Read the PASS or FAIL lines. The script writes `data/raw/backtest/lev_tests.json`.
3. Record the result under "Result" below.
4. For a pass: add the feature to `hy/state.py` and a row to framework F8. Then write a bond-level test against spreads.
5. For a fail: record the failure and close the idea.

## Test that settles it
- Sample: US non-financial, non-utility firm-years, 1994 to 2022, with debt of at least $150m, and EBITDA at or below zero or debt over EBITDA above 4x.
- Decision time: fiscal year end plus 90 days.
- Event: Compustat deletion for bankruptcy or liquidation (`dlrsn` 02, 03) within 36 months of the decision time.
- Windows: `hy.backtest.CYCLE_WINDOWS` (2008, 2015, 2020, 2022). Each model trains only on rows whose outcome was known before the window starts.
- L1 sample: EBITDA at or below zero. Base model: size. Full model: size and debt to revenue.
- L2 sample: all rows. Base model: capped leverage and size. Full model: the base and the flag.

Pass rule, fixed before the first run:
1. The firm-block bootstrap 95% interval of the pooled out-of-sample AUC gain lies above zero.
2. At least 3 of the 4 windows show a positive gain and a positive coefficient. A window with fewer than 5 events does not count as a pass.

## Limits
- `comp.funda` is the current view, not point in time. The 90-day lag handles the release date but not restatements.
- The sample is a proxy for high yield issuers, not the TRACE bond panel.
- The deletion date can lag a bankruptcy filing, and a firm can emerge without deletion. So the event undercounts failures.
- Failure is not mispricing. A pass earns a bond-level test and does not prove a signal.
- The synthetic tests prove the script's logic. They say nothing about the real result.

## Result
Not run. This page defines the method. The result enters here after a run.
