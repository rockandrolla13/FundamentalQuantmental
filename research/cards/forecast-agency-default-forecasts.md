# Forecast source: rating agency default rate forecasts (Moody's, S&P)

Wired: stub. Code: `load_agency_default_forecasts` returns [] and logs one line. Fallback per `FALLBACK_ORDER`: market-implied, then the F6 table, then a logged assumption.

## Claim
The agencies publish a 12-month forecast of the speculative-grade default rate with a baseline and stress cases. F6 compares `default_rate_fcst` with `default_rate_ttm` for the phase vote.

## Coverage and method
- Moody's model: a non-linear regression model on Moody's ratings and macro variables. It predicts the default rate 12 months ahead. The drivers are rating dispersion, high yield issuance, and macro factors. The low and high bounds stress the expected monthly default counts by plus or minus 50%. Source: Hamilton, D., Ou, S., Kim, F., and Cantor, R. (2007), "Corporate Default and Recovery Rates, 1920-2006", Moody's, https://www.moodys.com/sites/products/DefaultResearch/2006400000429618.pdf (accessed 2026-10-22). The current model name and method: not verified.
- Moody's scenarios condition on a high yield spread and an unemployment path. January 2023 report: baseline 4.4% at end 2023 with a 510 bp spread and 5.0% unemployment; severe pessimistic 15.9% with a 1,371 bp spread. Secondary source: fi-desk, 16 February 2023, https://www.fi-desk.com/moodys-speculative-grade-credit-default-rate-to-rise-in-2023/ (accessed 2026-10-22).
- Latest figure seen: US trailing rate 5.3% (August 2026), baseline 4.3% for December 2026. Secondary source: First Trust, 17 September 2026, https://www.ftportfolios.com/Blogs/InvestBlog/2026/9/17/factoid---thursday,-september-17,-2026 (accessed 2026-10-22).
- S&P: a US speculative-grade default rate of 4% by September 2026 (press release, 3 December 2025, https://press.spglobal.com/2025-12-03-S-P-Global-Credit-Outlook-For-2026-Looks-Resilient,-If-Uneven,-Report-Says, accessed 2026-10-22). The S&P method, cadence, and scenario values: not verified (spglobal.com returned HTTP 403).

## Cadence and available_at
Moody's: monthly Default Report. S&P: cadence not verified. Rule when wired: `available_at` = report release date + 1 day, 00:00.

## Revision policy
Moody's revises the forecast from one report to the next and restated a January figure in 2007 (Hamilton et al. 2007). The 2023 forecast moved down month over month as the spread assumption fell (fi-desk).

## Known biases
- The Moody's forecast is conditional on a spread input. Thus it is not independent of the market: a spread-driven forecast adds little to `hy_spread` itself.
- Independent evaluation of aggregate agency default rate forecasts: not verified. Guttler and Kramer (2003) compare Moody's and S&P issuer ratings, not rate forecasts; neither agency is well calibrated (https://eldorado.tu-dortmund.de/items/190e998f-703f-4b0d-8715-af3c32d8805f/full, accessed 2026-10-22).

## Would fill
`default_rate`, horizons 0 to 4, point = baseline, q10 = optimistic, q90 = pessimistic, source `agency_default`, method `scenario_range`.

## Limits
Licensed. Secondary sources only for the recent values. Do not enter a value by hand without a decision page.

Section touched: methodology 5.4
