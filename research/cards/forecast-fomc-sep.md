# Forecast source: FOMC Summary of Economic Projections (SEP)

Wired: live. Code: `hy/sources/forecast_sources.py`, `load_fomc_sep`. Registry source `fomc_sep`.

## Claim
The SEP gives each FOMC participant's projection of GDP growth, unemployment, PCE inflation, and the appropriate fed funds rate, for each year to three years ahead. The median is a consensus of policymakers. The range shows disagreement, not forecast uncertainty.

## Coverage
- Variables: real GDP growth and PCE inflation (Q4 over Q4), unemployment (Q4 average), fed funds (midpoint of the target range at year end). The longer run column has no date, so we drop it. Source: SEP tables, 16 September 2026, https://www.federalreserve.gov/monetarypolicy/fomcprojtabl20260916.htm (accessed 2026-10-22).
- Median = the middle projection. Central tendency = all projections except the 3 highest and the 3 lowest. Range = all participants. 18 participants submitted in September 2026.
- The loader reads every SEP linked from https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm (2021 onward in the smoke run).

## Cadence and available_at
- Four SEPs a year: March, June, September, December (FOMC calendar page).
- The tables carry "For release at 2:00 p.m., EDT" on the second day of the meeting, the same time as the statement (statement of 16 September 2026, https://www.federalreserve.gov/newsevents/pressreleases/monetary20260916a.htm, accessed 2026-10-22).
- `vintage` = second day of the meeting. `available_at` = that day + 1 day, 00:00 (end of the release day).

## Revision policy
Not verified. We found no page that revises a published SEP. Each table repeats the previous SEP median as "June projection" (or similar). We drop those rows.

## Known biases
- Table 2 of each SEP gives the RMSE of fall forecasts by private and government forecasters, 2006 to 2025. For the 2026 to 2029 columns: GDP 1.4, 1.8, 2.1, 2.3; unemployment 0.5, 1.3, 1.9, 2.1; short rates 0.5, 1.7, 2.3, 2.8. The Fed reads plus or minus one RMSE as about a 70% band. The page also says the rate band does not strictly match the dots, because the dots show appropriate policy, not the most likely outcome.
- About 72%, 78%, and 75% of SEP errors for GDP, unemployment, and PCE inflation since late 2007 fell inside plus or minus one RMSE. Forecasters noticeably over-predict the 3-month bill rate, back to the mid-1980s; the paper ties part of this to a falling neutral rate. For other variables, Wald tests do not reject zero bias. Source: Reifschneider, D., and Tulip, P. (2017), "Gauging the Uncertainty of the Economic Outlook Using Historical Forecasting Errors: The Federal Reserve's Approach", FEDS 2017-020, https://www.federalreserve.gov/econresdata/feds/2017/files/2017020pap.pdf (accessed 2026-10-22).
- Comparison of participant dispersion against error size: not verified. The paper above does not make it.
- Studies of dots too high in 2015 to 2018: not verified.

## Method in our code
Method `dot_range`: q50 = point = median, q10 = range low, q90 = range high. Year Y maps to the horizon of Q4 of Y. Quarters between two Q4 anchors use linear interpolation (method `dot_range_interp`). PCE inflation enters as variable `cpi`; this is a stated approximation.

## Data (smoke run, decision time 2026-10-21)
The September 2026 SEP: fed funds median 4.1% at end 2026 (range 3.9% to 4.4%). GDP growth 2.3% (2.1% to 2.6%). Unemployment 4.1%. PCE inflation 3.7%. The registry holds 968 rows from 23 meetings.

## Limits
- The range of all participants is narrower than the historical error band. At 2027, the fed funds range is about 1 pp wide while the RMSE band is plus or minus 1.7 pp. The `dot_range` quantiles therefore understate uncertainty. Expect `widen_factor` above 1.
- The policy path is "appropriate policy", a conditional plan, not a forecast of the market rate.

## Decision
Use `fomc_sep` for the policy_rate anchor of the path builder, with q10 and q90 from the range only after the error accounting widens them. Test: coverage of the 80% band on matured horizons. We expect it below 0.8 before the widening.

Section touched: methodology 5.4
