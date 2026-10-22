# Fair spread from sector peers and the HY index, with a DTS-hedged total return and catalysts

Date: 23 October 2026. Code: `hy/fairspread.py` (`peer_fair_spread`, `dts_beta`), `hy/peers.py` (`esp_sd_*`, `esp_n_*`), `hy/events.py` (`catalysts_in_horizon`), `scripts/process.py` (`peer_table`, `add_peers`, `step_rv`, `step_gate`, `step_decision`), `scripts/memo.py`. Tests: `tests/test_fairspread.py`, `tests/test_peers.py`, `tests/test_events.py`.

## Context
The old fair line was an OLS fit of log 5-year spread on leverage across the issuers of one run, eight on 22 October 2026. Three problems followed:
1. Every verdict depended on which other tickers were in the run.
2. The target issuer sat inside its own fit (algorithm spec card).
3. In the panel backtest, the line ranked no better than the widest spread, and its Mincer-Zarnowitz slope was 0.07.

The user decided that the fair line should measure the bond against other bonds in the sector and against the HY index. It should produce the total hedged return and the catalysts, if any.

## Options and choices (user, 23 October 2026)
1. Peer group: sector x rating x maturity (chosen), or sector x maturity. The second compares a CCC bond with BB bonds.
2. Hedge on the HY index: DTS beta s_bond / S (chosen), beta = 1, or both.
3. Scope: replace the fair spread everywhere, in E1, E2, E10, the gate and the pair (chosen), or in E2 only.

## What we built
1. Fair spread = s exp(-ESP_sr) = the leave-own-issuer-out median spread of the issuer's peer cell on the TRACE panel. With no peer cell at any fallback level, fair = the HY index spread.
2. The live issuer joins its cell with the panel's own point-in-time leverage (`leverage_full`, available before the decision). Its peers use the same leverage. The step 5 ratio uses another debt definition: MGM shows 2.5x there and 14.3x in the panel file.
3. Noise = the peers' robust sd of log spread. The F9 gate tests the spread row against it. The row "Leverage the spread is pricing" is gone, because the peer fair spread has no leverage slope.
4. Step 15: the total hedged return = return over the horizon less a Treasury of the same tenor less DTS beta x (index carry less index expected loss). The walk-forward realises the same hedge, so prediction and test use one beta (spec K15).
5. Catalysts = the step 12 events inside the horizon: dated events, and debt due within the horizon.

## What the data says (8-issuer run, decision 18 September 2026)
1. All eight issuers get a peer fair spread. ORCL, HCA and THC have no sector x rating cell with 5 peers, so they fall back to rating x maturity across all sectors (44 to 50 peers).
2. CRWV is cheap by 323 bp against 5 peers (z 0.41). NCLH is cheap by 57 bp. The other six are rich.
3. DTS betas run from 0.40 (HCA) to 4.62 (CRWV). Total hedged returns run from -174 to +614 bp a year. The backtest slope of 0.07 for the old line says that such sizes are not yet calibrated.
4. Every issuer has an estimated results date inside the horizon. CRWV ($4.4bn), CCL ($745m) and NCLH ($478m) also have debt due within 6 months.

## Limits
1. The fallback order comes from ESP: sector x rating, then rating, then sector. A fallback to the rating cell leaves the sector.
2. The rating class after February 2017 is implied by leverage.
3. E2 now measures the same gap as E14 (ESP). E2 converts it to bp through convergence at the lowest weight (decision page `2026-10-22-e2-lowest-weight`).

## Test that settles it
Rerun the panel backtest with `fair_s5` from the peer median. Pass: the beyond-spread rank IC of the peer gap is positive at 6 and 12 months in at least three of the four cycle windows, and the MZ slope of the hedged total return rises above 0.07. Rerun the walk-forward: the DTS-hedged realised return should rank with the predicted total hedged return.

## Result of the panel backtest (23 October 2026)
Script: `scripts/backtest_peer_line.py`. Output: `data/raw/backtest/summary_peer_line.json`. Sample: TRACE high yield panel, 2008-01 to 2026-07, 223 months. Common sample with the old line: 287,720 bond-months at 3 months and 293,105 at 6 months. The 12-month cache holds no old-line forecasts, so at 12 months only widest and the peer line are scored (608,191 bond-months). Realised returns use the DTS hedge and are after cost. "Skip a month" forecasts at t and earns from t + 1. This removes the bid-ask bounce that a shared month-end price creates.

| Measure | 3 months | 6 months | 12 months |
| --- | --- | --- | --- |
| Peer line, IC after cost | +0.054 (t 3.4) | +0.038 (t 1.7) | -0.008 (t -0.3) |
| Same, skip a month | -0.000 (t 0.0) | +0.004 (t 0.2) | -0.021 (t -0.8) |
| Peer line, IC beyond spread | +0.112 (t 9.0), 4 of 4 cycles | +0.120 (t 6.1), 3 of 4 | +0.198 (t 7.4), 3 of 4 |
| Same, skip a month | +0.073 (t 6.1), 3 of 4 | +0.100 (t 5.3), 2 of 4 | +0.181 (t 6.7), 3 of 4 |
| Old line, IC beyond spread, skip a month | +0.103 (t 5.5), 2 of 4 | +0.138 (t 4.6), 2 of 4 | not cached |
| Peer line, MZ slope | -0.06 | -0.05 | -0.19 |
| Widest, IC after cost | +0.012 (t 0.5) | +0.026 (t 0.7) | -0.019 (t -0.5) |

What the data says:
1. The peer gap alone does not forecast the DTS-hedged return. Its plain IC disappears when a month is skipped, so the bid-ask bounce made it.
2. The peer gap adds to spread level, and this survives the skip. Among bonds with similar spreads, the ones cheap against their peers earn more. The edge grows with the horizon.
3. The peer gap holds in more cycle windows than the old line: 3 of 4 at 3 and 12 months against 2 of 4.
4. The forecast sizes are wrong. The MZ slope is negative at every horizon, so the bp figures carry no size information.
5. Under the DTS hedge, spread level alone (widest) earns nothing after cost.

What we decide:
1. Keep the peer fair spread. It passes the three-of-four-cycles bar beyond spread at 3 and 12 months. It fails it at 6 months after the skip (2 of 4).
2. Use it to rank bonds within a spread level, not as a return forecast. The total hedged return in the memo is a rank, not a size, until the MZ slope is positive.
3. The settling test of this page passes in part: the cycle bar holds at 12 months. The MZ slope test fails.
