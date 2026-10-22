# Forecast source: Treasury forward curve

Wired: live. Code: `hy/sources/forecast_sources.py`, `forwards_from_par`, `load_ust_forwards`. Registry source `ust_forward`, variables `policy_rate` (3-month forward), `y2`, `y10`, horizons 0 to 8, method `market_implied`, point only.

## Claim
Forward rates from the par curve give a market-implied path for the short rate and for the 2-year and 10-year yields. They are biased forecasts: forward = expected rate + term premium.

## Coverage and method
- Input: the daily Treasury par yield curve (hy.sources.treasury). Treasury fits it with a monotone convex method since 6 December 2021, on indicative bid-side quotes of the most recently auctioned securities. The New York Fed collects the quotes near 3:30 p.m. Treasury posts the rates by about 6 p.m. ET. Source: "Treasury Yield Curve Methodology", US Treasury, https://home.treasury.gov/policy-issues/financing-the-government/interest-rate-statistics/treasury-yield-curve-methodology (accessed 2026-10-22).
- Our bootstrap: tenors of 6 months or less are zero-coupon. From 1 year on, par yields are interpolated on a semiannual grid, and each discount factor solves a par bond at 100. The zero rate is linear between nodes. All forwards are bond-equivalent (semiannual), like the par curve. A flat curve returns its par yield at every horizon. An upward curve returns rising forwards (tests).

## Cadence and available_at
Daily. `vintage` = curve date. `available_at` = curve date + 1 day, 00:00 (end-of-day rule of hy.sources.treasury).

## Revision policy
Treasury may change the method at its discretion (methodology page). Whether Treasury revises published values: not verified.

## Known biases
- The yield spread predicts short-rate changes about as the expectations hypothesis says. For long rates the sign is wrong: a high spread comes before a fall in the long yield. The authors attribute this to time-varying risk premia. Source: Campbell, J., and Shiller, R. (1991), "Yield Spreads and Interest Rate Movements: A Bird's Eye View", Review of Economic Studies; NBER WP 3153, https://www.nber.org/papers/w3153 (accessed 2026-10-22).
- The ACM 10-year term premium was positive for most of 1961 onward. It was negative at times in the 1960s, and compressed or negative at times after the 2008 crisis. Source: Adrian, T., Crump, R., and Moench, E., "Treasury Term Premia: 1961-Present", Liberty Street Economics, May 2014, https://libertystreeteconomics.newyorkfed.org/2014/05/treasury-term-premia-1961-present/ (accessed 2026-10-22). Model: "Pricing the Term Structure with Linear Regressions", Journal of Financial Economics 110(1), 2013; Staff Report 340, https://www.newyorkfed.org/research/staff_reports/sr340.html (accessed 2026-10-22).
- A fall in term premia explains a large share of the drop in distant forwards after 2004. Source: Kim, D., and Wright, J. (2005), FEDS 2005-33, https://www.federalreserve.gov/pubs/feds/2005/200533/200533abs.html (accessed 2026-10-22).
- Fama and Bliss (1987): not verified.

## Data (smoke run, decision time 2026-10-21)
Curve of 2026-10-20. 3-month forward: 4.26% at horizon 0, 4.46% at horizon 1, 4.59% at horizon 2. 2-year: 4.79% rising to 4.95% at horizon 2. 10-year: 5.12% rising to 5.19%.

## Limits
- The 3-month bill forward is a proxy for the fed funds path. Bills trade with a spread to fed funds.
- No term premium adjustment. The forward overstates the expected rate when the premium is positive.

## Decision
Use `ust_forward` as the market-implied policy and yield path (first in FALLBACK_ORDER) until fed funds futures are licensed. Subtract an ACM term premium estimate before a forward enters a macro path as an expectation. Test: forecast error of the forward against the realised 3-month rate, by horizon, has positive mean (forward too high) over 2010 to 2026.

Section touched: methodology 5.4
