# ESP and spread per turn against sector and rating peers (methodology 7.2; framework F7.7; estimate E13)

## Context
The user asked for a sector version and a rating version of E13 (spread per turn, Kricheff ch. 21), built in the style of ESP. Barclays QPS lists ESP ("Excess Spread to Peers") and SPiDER ("Spread per unit of Debt To Earnings Ratio"). Barclays does not publish either method, so the definitions below are ours. Before this change, E13 compared each issuer with the other issuers in the run only, which is eight names.

Data:
- Sector: GICS history from `comp.co_hgic`. It is point in time and covers 2,818 issuers.
- Rating: S&P long-term issuer rating from `comp.adsprate`. It covers 1,732 issuers and ends in February 2017.
- Mergent FISD and Capital IQ ratings are not in the licence. `comp_ratings.erating` ends in August 2012. So no rating source covers March 2017 onward or the live issuers.

## Options
1. Sector cells only. Simple, with full coverage. Ignores credit quality.
2. Sector and actual-rating cells, 2008 to 2017 only. Clean data, but nothing after 2017 and nothing for live issuers.
3. Sector and rating cells. Use the actual rating where one is on file. Otherwise use a class implied by leverage, with cut-offs fitted on the actual ratings of earlier months only.

## Choice
Option 3. Code: `hy/peers.py`, `hy/sources/peer_data.py`, `scripts/backtest_peers.py`; live block in `scripts/process.py` (`add_peers`, step 9).

- Peer cell: GICS sector x rating class (IG, BB, B, CCC) x maturity bucket (under 3 years, 3 to 7, 7 and over).
- ESP = log spread minus the median log spread of the other issuers' bonds in the cell.
- E13 against peers = log(spread / leverage) minus the same median of the peers.
- A cell needs 5 other issuers. Otherwise the code falls back: sector x rating, then rating, then sector, then all.
- Implied class cut-offs (debt / EBITDA), fitted on 2008 to 2017: IG below 2.9x, BB below 4.1x, B below 7.6x, CCC above. Negative EBITDA reads as CCC.
- E13 in the score now uses the sector x rating peer value. It keeps Kricheff's trap guard and its 5.83% weight. ESP is reported in step 9 and in the memo. It has no weight yet.

## Test result (alpha backtest panel, 2008 to 2026, rank IC after cost)

| Signal | IC net 3m | IC net 6m | IC beyond spread 6m (t) |
| --- | --- | --- | --- |
| Buy the widest | 0.208 | 0.272 | n/a |
| E13 as built (run-wide) | 0.109 | 0.135 | +0.008 (0.3) |
| E13 vs peers, sector x rating | 0.106 | 0.126 | +0.023 (1.1) |
| ESP, sector x rating | 0.158 | 0.204 | +0.072 (2.6) |
| ESP, sector only | 0.182 | 0.234 | +0.072 (2.0) |
| ESP, rating only | 0.167 | 0.217 | +0.075 (2.6) |

What the data says:
1. E13 against peers adds nothing beyond spread level. Neither does the run-wide E13.
2. ESP adds information beyond spread level over the full sample (t 2.0 to 2.9).
3. The ESP edge sits after 2017: beyond-spread IC +0.110 (t 2.6) from 2017 to 2026, +0.033 (t 1.0) from 2008 to 2017.
4. By cycle window, the ESP beyond-spread IC is 2008 -0.05, 2015 0.00, 2020 -0.17, 2022 +0.17. It fails the three-of-four-cycles bar. The edge disappears in stress.
5. The implied rating class matches the actual class on only 36% of issuer-months (2008 to 2017). The rating cell after 2017 is a leverage cell, not a rating cell.

## Decision
- Keep E13 against peers in the score, as the user asked, at its existing weight. The backtest gives it no support beyond spread.
- Report ESP in every memo (step 9). Give it no weight until it passes the cycle bar.

## Test that settles the rest
1. A real rating feed after 2017 (licence Mergent FISD or Capital IQ ratings). Then rerun `scripts/backtest_peers.py`. If ESP beyond spread is positive in three of four cycles, give it weight under the rank-IC rule.
2. Test ESP in stress only. If it fails again in 2020, keep it as a calm-market signal and turn it off when the phase is contraction.
