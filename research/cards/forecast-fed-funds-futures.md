# Forecast source: fed funds futures (CME ZQ)

Wired: stub. Code: `load_fed_funds_futures` returns [] and logs one line. Real source: CME 30-Day Federal Funds futures settlement prices, CME DataMine (licensed). Fallback: `ust_forward` policy_rate.

## Claim
Futures give the market path of the policy rate month by month. They are risk-adjusted forecasts: the price contains a premium that rises with horizon.

## Coverage and method
Implied average effective fed funds rate for the contract month = 100 - price. CME FedWatch builds meeting probabilities with a binary tree from months without a meeting, assumes 25 bp steps, and floors the rate at zero. The methodology does not mention a risk premium. Source: CME Group, "Understanding the CME Group FedWatch Tool Methodology", 2023, https://www.cmegroup.com/articles/2023/understanding-the-cme-group-fedwatch-tool-methodology.html (accessed 2026-10-22).

## Cadence and available_at
Daily settlement. Rule when wired: `available_at` = settlement date + 1 day, 00:00.

## Revision policy
Settlement prices are final. Not verified as a CME statement.

## Known biases
Over 1988 to 2003, average excess returns on fed funds futures are positive and significant, about 41 to 73 bp a year, rising with horizon. After 1994 the premia for 1 to 6 months ahead were 32, 35, 38, 44, 49, and 57 bp a year. The premium is countercyclical; employment growth and Treasury and corporate spreads predict it (R squared 8% at 2 months, 35% at 6 months). Source: Piazzesi, M., and Swanson, E. (2008), "Futures Prices as Risk-Adjusted Forecasts of Monetary Policy", Journal of Monetary Economics; NBER WP 10547, https://www.nber.org/system/files/working_papers/w10547/w10547.pdf (accessed 2026-10-22).

## Would fill
`policy_rate`, horizons 0 to 8, point = 100 - price averaged over the months of the quarter, source `ff_futures`, method `market_implied`. q10 and q90 from options on ZQ or SOFR futures.

## Decision
When wired, subtract a horizon premium (start with the Piazzesi and Swanson post-1994 values, then re-estimate) before the path enters hy.macro as an expectation. FedWatch probabilities are not risk-neutral-adjusted; do not use them as physical probabilities.

Section touched: methodology 5.4
