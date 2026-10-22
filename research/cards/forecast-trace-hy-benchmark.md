# Forecast source: TRACE high yield benchmark (hy_spread, distress_ratio)

Wired: live. Code: `hy/sources/forecast_sources.py`, `trace_hy_rows`, `load_trace_hy`, on hy.sources.trace_bonds (`hy_benchmark`, `benchmark_by_bucket`, `g_spread`). Registry source `trace_hy_benchmark`, horizon 0, method `market_implied`.

## Claim
A G-spread median of traded high yield bonds is a free proxy for the high yield index spread. The share of bonds above 1,000 bp is a proxy for the distress ratio of framework F6.

## Coverage and method
- Universe: TRACE grade H, fixed coupon, not convertible, 1 to 15 years to maturity, trades of at least 100,000 par, volume-weighted yield over a 10-day window (hy.sources.trace_bonds).
- `hy_spread` = median G-spread of bonds with price at least 80 and yield above 0 and at most 25% (the `benchmark_by_bucket` universe, all buckets pooled).
- `distress_ratio` = share of all bonds with a positive yield and a G-spread above 1,000 bp. No price filter, because distressed bonds are the numerator.

## Cadence and available_at
- FINRA requires reports within 15 minutes. It shows non-investment-grade trades above $1 million as "1MM+" and investment-grade trades above $5 million as "5MM+". Source: FINRA, "TRACE Reporting and Dissemination", https://www.finra.org/filing-reporting/trade-reporting-and-compliance-engine-trace/trace-reporting-timeframes (accessed 2026-10-22).
- WRDS loads TRACE with a lag. On 2026-10-22 the last trade date on WRDS was 2026-09-17 (our query). The loader ends the window at the last WRDS trade date before the decision time. `vintage` = last trade date. `available_at` = last trade date + 1 day, 00:00. This is the dissemination time, not the WRDS load time. For a backtest with the WRDS lag, add the lag.
- The FINRA 2015 proposal to cut the historic TRACE delay from 18 to 6 months: WRDS comment letter, https://www.finra.org/sites/default/files/15-24-the-wharton-school-comment.pdf (accessed 2026-10-22). Whether FINRA adopted it: not verified.

## Revision policy
Reports are cancelled and corrected after the trade. hy.sources.trace_bonds keeps only the last live version. Error rates: 7.7% of reports are errors, and up to 18% should be deleted in some cases. Errors left in make the market look more liquid. Source: Dick-Nielsen, J. (2010), "Liquidity biases in TRACE", in Three Essays on Corporate Bond Market Liquidity, CBS PhD thesis, https://research-api.cbs.dk/ws/portalfiles/portal/58945017/Jens_Dick_Nielsen.pdf (accessed 2026-10-22). Dick-Nielsen (2014) on cleaning enhanced TRACE: not verified.

## Known biases
- G-spread is not OAS. ICE computes OAS on a short-rate tree for callable bonds and uses yield to worst for yields. Source: ICE Data Indices, "Bond Index Methodologies", 30 April 2025, https://www.ice.com/publicdocs/data/Bond_Index_Methodologies.pdf (accessed 2026-10-22). TRACE `yld_pt` conventions for callable bonds come from FINRA; we did not verify whether it is yield to worst.
- The volume weights cap large trades at the dissemination cap, so they understate large trades (hy.sources.trace_bonds docstring).
- What the data says: on 2026-09-17, 2,279 bonds; median yield 6.5%; Treasury 2-year 4.67%, 10-year 4.94%; median G-spread 164 bp; bucket medians 126 bp (1 to 3 years) to 241 bp (10 to 15 years). This is low against index OAS levels we expect. We have no ICE level to compare (FRED blocked), so the size of the gap is not verified.

## Data (smoke run, decision time 2026-10-21)
`hy_spread` = 0.0164, `distress_ratio` = 0.0427, vintage 2026-09-17.

## Limits
- The level is not comparable with the ICE OAS. Use changes and its own trailing five-year median (the F6 rule), not a fixed threshold from index history.
- Volume-weighted medians tilt toward large, liquid BB issues.

## Decision
Use it for the F6 phase vote (above its own trailing median and rising) until ICE data is licensed. Test: over 2008 to 2026, monthly changes of the TRACE median G-spread and of the ICE H0A0 OAS have a correlation above 0.8.

Section touched: methodology 5.4
