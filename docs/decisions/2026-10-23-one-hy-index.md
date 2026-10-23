# One high yield index rule for the live run, the registry and the backtest

Date: 23 October 2026. Code: `hy/state.py` (`HY_INDEX_RULE`, `hy_index_level`, `distress_ratio`), `scripts/scenarios.py` (`_bench_level`), `hy/sources/forecast_sources.py` (`trace_hy_rows`), `hy/backtest.py` (`benchmark_spread`). Tests: `tests/test_state.py`. Review finding: AR-DRY-001 (`reviews/2026_10_23_architecture_review.md`). Data module, migration step 5.

## Context
The HY index level `S` sets spread level (E0), the DTS hedge ratio s/S, and the total hedged return. The repo had three definitions of it:

| User | Filter | Statistic |
|---|---|---|
| Backtest (`benchmark_spread`) | price >= 80, 0 < yield <= 25%, 1 to 15 years | median G-spread |
| Forecast registry (`trace_hy_rows`) | price >= 80, 0 < yield <= 25% (1 to 15 years in the SQL universe) | median G-spread |
| Live run (`_bench_level`, `s_index_now`) | 0 < spread < 2,500 bp; no price or yield filter | median G-spread |

The distress share also had two definitions: the registry counted every bond with a positive yield; the live run first dropped bonds above 2,500 bp.

## Choice
One rule in `hy.state`: the median G-spread of bonds with price >= 80 and 0 < yield <= 25%, inside a universe of grade H, fixed-coupon, non-convertible bonds with 1 to 15 years left. One distress rule: the share of bonds with a positive yield whose spread exceeds 1,000 bp, with no cap. The universe window stays where the bonds are loaded; a test keeps those defaults equal to `HY_INDEX_RULE`.

The backtest rule wins because it is the one the published backtests used and because the price and yield bounds keep distressed bonds and print errors out of the middle.

## What the data says (8-issuer run, decision 18 September 2026)
1. The index moves from 168 bp to 164 bp.
2. DTS hedge ratios rise by about 3% (CRWV 4.62 to 4.74).
3. Combined alpha after cost moves by 0 to 14 bp a year. CRWV moves from +17 to +3 bp. No rank changes. No gate direction changes.
4. The backtest summaries do not change: the backtest already used this rule.

## Test that settles it
`tests/test_state.py`: the rule on a hand example, the distress share on a hand example, and the shared constants. The golden snapshot is retaken after this change (`scripts/golden_check.py snapshot`).
