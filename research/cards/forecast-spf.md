# Forecast source: Philadelphia Fed Survey of Professional Forecasters (SPF)

Wired: live. Code: `hy/sources/forecast_sources.py`, `load_spf`. Registry sources `spf` (medians), `spf_prob` (densities), `spf_prob_pce` (core PCE densities).

## Claim
The SPF gives a quarterly consensus for real GDP growth, CPI inflation, and unemployment, with a density forecast. Its median errors are small and only slightly biased. Its densities are miscalibrated in a way that depends on the horizon.

## Coverage
- Quarterly survey since 1968 Q4. The Philadelphia Fed took it over in 1990 Q2. Source: SPF Documentation, Philadelphia Fed, updated 28 July 2026, https://www.philadelphiafed.org/-/media/frbp/assets/surveys-and-data/survey-of-professional-forecasters/spf-documentation.pdf (accessed 2026-10-22).
- Medians: current quarter and the next four quarters (horizons 0 to 4). We use RGDP growth (`medianGrowth.xlsx`, DRGDP2 to DRGDP6), UNEMP and CPI (`medianLevel.xlsx`).
- Densities: PRGDP (annual-average growth) and PRUNEMP (annual-average rate) for the current year and the next three years. PRCCPI and PRCPCE (core, Q4 over Q4) for the current year and the next year. Core densities start in 2007 Q1. PRUNEMP starts in 2009 Q2. The bins changed in 1992 Q1, 2009 Q2, 2014 Q1 (PRUNEMP), 2020 Q2, and 2024 Q2 (documentation, Tables 7 to 9). The code holds each set of bins.

## Cadence and available_at
- The deadline falls in the second week of the middle month of the quarter. The release comes a few days later (documentation).
- `vintage` = true deadline date. `available_at` = news release date + 1 day, 00:00. Dates come from `spf-release-dates.txt` (surveys since 1990 Q2). The 2026 Q1 survey was late because of a federal shutdown (release 6 March 2026).
- The loader keeps surveys from 1990 Q2. For a survey outside the calendar, the rule is vintage = day 15 of the second month and available_at = day 1 of the third month.

## Revision policy
The documentation does not revise published forecasts. It records known errors as caveats. Examples: wrong target years in the 1985 Q1, 1986 Q1, and 1990 Q1 annual forecasts, and 9 respondents in 1990 Q2. A bin change is a break in the density series.

## Known biases
- Median CPI forecasts: mean error (realised minus forecast) is +0.20 to +0.28 pp at horizons 1 to 5 over 1997 to 2023. This is a small under-prediction. The RMSE is 0.53 of a no-change model at horizon 1 and 0.81 at horizon 5. Source: Stark, T., "Error Statistics for the SPF: CPI Inflation Rate", Philadelphia Fed, 22 August 2025, https://www.philadelphiafed.org/-/media/FRBP/Assets/Surveys-And-Data/survey-of-professional-forecasters/data-files/CPI/SPF_Error_Statistics_CPI_1_AIC.pdf (accessed 2026-10-22). The report applies no formal bias test.
- Densities: at short, within-year horizons the aggregate histograms are under-confident (too wide). A benchmark from the SPF median plus the historical error variance gives a better log score. A simple correction fitted on past data helps. Source: Clements, M. P. (2018), "Are macroeconomic density forecasts informative?", International Journal of Forecasting 34(2), 181-198, accepted version https://centaur.reading.ac.uk/72924/1/informative_densities%20final.pdf (accessed 2026-10-22).
- Over-confidence of one-year-ahead inflation intervals (Giordani and Soderlind 2003): not verified. We read this only through Clements.
- Diebold, Tay, and Wallis (1999): not verified.

## Method in our code
- Medians: method `survey_median`, no quantiles. CPI year on year at horizon h = product of (1 + r/100)^(1/4) over quarters h-3 to h, minus 1. Quarters before -1 come from CPI1 of the earlier surveys.
- Densities: method `survey_bins`. The mass is uniform inside each bin. An open tail bin has the width of its neighbour. The quantiles come from the cumulative bin probabilities. Target year Y maps to the horizon of Q4 of Y. point = q50.

## Data (smoke run, decision time 2026-10-21)
The latest vintage is the 2026 Q3 survey (deadline 2026-08-11, release 2026-08-14). Median real GDP growth at horizon 0 is 2.5%. Median unemployment is 4.2%. CPI year on year is 3.6%. The registry holds 3,204 rows from all vintages.

## Limits
- The densities are means across forecasters. They mix disagreement with individual uncertainty.
- Annual-average GDP growth and core Q4-over-Q4 inflation stand in for q/q GDP growth and headline CPI year on year. This is an approximation.
- `ForecastRegistry.as_of(latest_only=True)` keeps the newest vintage per horizon. A fixed-event target from an old survey can then stay at a horizon that no newer survey fills. Readers must filter to the newest vintage per source.

## Decision
Use `spf` medians as the point and `spf_prob` quantiles as the band. Before a band moves a path probability, widen or shrink it with `widen_factor` from the error accounting. The Clements result says the correction can go either way.

Section touched: methodology 5.4
