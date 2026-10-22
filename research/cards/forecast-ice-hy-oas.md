# Forecast source: ICE BofA US High Yield Index OAS (H0A0)

Wired: stub. Code: `load_ice_hy_oas` returns [] and logs one line. Real source: ICE Data Indices (licensed). Fallback: `trace_hy_benchmark`.

## Claim
The index OAS is the standard high yield spread level and the reference for `hy_oas` in F6. Its full history is licensed.

## Coverage and method
- ICE computes OAS by a shift of the fair-value government spot curve; for callable, putable, or sinking bonds it shifts a lognormal short-rate tree. Yield to worst is the lowest yield over all redemption dates. Yields are clipped to -10% to +100% and spreads to -1,000 bp to +10,000 bp. Rebalance at month end only. Default follows the bond's legal terms; a "D" rating alone does not count. Source: ICE Data Indices, "Bond Index Methodologies", 30 April 2025, https://www.ice.com/publicdocs/data/Bond_Index_Methodologies.pdf (accessed 2026-10-22).
- Public copy: FRED series BAMLH0A0HYM2. A secondary source says that from April 2026 FRED limits all ICE BofA series to a rolling three-year window, with the full history from December 1996 only from ICE or licensed redistributors: Eco3min, "Credit spreads recession risk dataset", 2026, https://eco3min.fr/credit-spreads-recession-risk-dataset/ (accessed 2026-10-22). No ICE page confirms it: not verified at the primary source. FRED did not answer from this machine on 2026-10-22.

## Cadence and available_at
Daily index values. Rule when wired: `available_at` = index date + 1 day, 00:00.

## Revision policy
ICE decides restatements case by case. Reference-data errors found after a rebalance typically cause no restatement (ICE methodology).

## Known biases
- Credit spreads predict economic activity. The excess bond premium, the part of the spread above expected default risk, signals lower risk-bearing capacity, and its shocks come before weaker activity. Source: Gilchrist, S., and Zakrajsek, E. (2012), "Credit Spreads and Business Cycle Fluctuations", American Economic Review 102(4), 1692-1720, https://www.aeaweb.org/articles?id=10.1257/aer.102.4.1692 (abstract, accessed 2026-10-22). Spread as a default predictor: not tested there.
- The index spread mixes default risk with the risk premium, so a high level is not a default forecast by itself.

## Would fill
`hy_spread` and `distress_ratio`, horizon 0, source `ice_hy_oas`, method `market_implied`.

## Decision
License the full history before any F6 threshold uses index levels. Until then the F6 vote uses the TRACE proxy relative to its own history.

Section touched: methodology 5.4
