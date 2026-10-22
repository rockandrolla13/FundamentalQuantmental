# Forecast source: sell-side consensus with count and dispersion

Wired: stub. Code: `load_sellside_consensus` returns [] and logs one line. Real source: LSEG I/B/E/S or FactSet Estimates detail history (licensed).

## Claim
Consensus revenue, EBITDA, and capex forecasts give the issuer base case its anchor (`gap_consensus`, signal S3). The dispersion of the estimates is a credit signal in itself.

## Coverage, cadence, revision
- Coverage: equity-listed issuers. Many high yield issuers have no equity and no coverage.
- Estimates change at any time. A detail history stamps each estimate. The I/B/E/S stamp method (activation date and announce date): not verified.

## Known biases
- Walk-down: analysts start optimistic and then cut to a level the firm can beat. The walk-down is strongest when the firm or its insiders sell stock after the announcement. Source: Richardson, S., Teoh, S. H., and Wysocki, P. (2004), "The Walk-Down to Beatable Analyst Forecasts", Contemporary Accounting Research 21(4), 885-924, https://psc.ky.gov/pscecf/2014-00396/rateintervention@ag.ky.gov/04222015061217/Richardson_et_al_-_The_Walkdown_to_Beatable_-_2004.pdf (accessed 2026-10-22).
- Forecasts carry cash flow information but show predictable biases, and markets do not fully correct them. Source: Kothari, S. P., So, E., and Verdi, R. (2016), "Analysts' Forecasts and Asset Pricing: A Survey", Annual Review of Financial Economics 8, 197-219, https://dspace.mit.edu/handle/1721.1/111079 (abstract only, accessed 2026-10-22).
- Stocks with higher dispersion earn lower future returns, most for small stocks and past losers. Source: Diether, K., Malloy, C., and Scherbina, A. (2002), Journal of Finance 57(5), working paper https://www.kellogg.northwestern.edu/faculty/mcdonald/ftp/practicum/papers/dms3.pdf (accessed 2026-10-22).
- Bonds of firms with higher dispersion have higher spreads, and changes in dispersion predict changes in spreads. Source: Guntay, L., and Hackbarth, D. (2010), "Corporate bond credit spreads and forecast dispersion", Journal of Banking and Finance 34(10), 2328-2345, https://ideas.repec.org/a/eee/jbfina/v34y2010i10p2328-2345.html (abstract, accessed 2026-10-22).

## Would fill
`<issuer>:revenue`, `<issuer>:ebitda`, `<issuer>:capex` per fiscal quarter. point = mean, q10 and q90 from the estimate distribution. Count and standard deviation go to a side table. Method `consensus`. `available_at` = estimate activation date + 1 day.

## Decision
Remove the expected optimism before the gap enters S3: use the error accounting by horizon (bias column) to shift the point. Test: mean error of consensus EBITDA by horizon is positive (optimistic) at long horizons and near zero at the last quarter.

Section touched: methodology 5.4
