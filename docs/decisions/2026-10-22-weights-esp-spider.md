# Bucket weights, second revision: ESP and SPiDER enter the score

Date: 22 October 2026. Supersedes the bucket shares in `2026-10-22-four-group-combination.md`. Code: `hy/groups.py` (`BUCKETS`, `ESTIMATES`).

## Context
ESP and SPiDER were rebuilt to the definitions of Dynkin et al. (2021) and backtested (`2026-10-22-esp-peer-groups.md`). The user asked to add them to the score and to set new weights.

## Options
1. Keep the bucket shares and put ESP and SPiDER inside G4's 11.67%.
2. Evidence tilt: G1 45%, clocks 10%, G2 rest 20%, G4 20%, G3 5%.
3. Fully backtest-led: clocks 0%, G1 35%.

## Choice (user, with the split of the rest by Claude)
The user set three shares: the clocks stay at 20%, G1 moves to 40%, and G4 moves to 17%. The user left the rest (23%) to Claude.

| Bucket | Before | Now | Why |
| --- | --- | --- | --- |
| G1 core process | 45% | 40% | User |
| Two clocks (E5) | 20% | 20% | User. The clocks backtest finds no edge beyond spread (-0.03 at 6 months). |
| G2 rest (E0 to E3, E6) | 11.67% | 18% | Holds spread level, the best-tested signal (IC after cost 0.27 at 6 months). |
| G3 skills (E11) | 11.67% | 5% | One-way only, and not backtested. |
| G4 books and peers | 11.67% | 17% | User |

Inside G4 (17%), the weight follows the IC beyond spread at 12 months:

| Estimate | Weight | IC beyond spread, 12m (t) |
| --- | --- | --- |
| E14 ESP, sector x rating | 9% | +0.096 (2.6) |
| E15 SPiDER | 3% | +0.032 (1.3) |
| E12 S&P score gap | 2.5% | not tested |
| E13 spread per turn vs peers | 2.5% | +0.026 (0.9) |

## Effect on the eight issuers (combined alpha after cost, bp a year)

| Issuer | Before | Now |
| --- | --- | --- |
| CRWV | -61 | -9 |
| ORCL | -201 | -195 |
| HCA | -139 | -169 |
| THC | -101 | -111 |
| CCL | -110 | -126 |
| NCLH | -190 | -162 |
| MGM | -220 | -196 |
| WYNN | -205 | -214 |

All eight stay below zero after cost. CRWV moves most: ESP says it pays 78% more than its peers.

## Test that settles it
1. ESP keeps 9% only if it passes the cycle bar beyond spread in a rerun with OAS and a rating feed after 2017.
2. SPiDER takes E13's weight if it passes t 2 beyond spread at 12 months.
3. The clocks keep 20% by user choice. A later backtest that finds them positive beyond spread would support the weight.

## Amendment (same day)
E14's 9% is split: ESP 4.5% and OneScore (E16) 4.5%. See `2026-10-22-onescore.md`.
