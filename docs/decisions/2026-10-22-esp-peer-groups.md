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

## Rebuild to the book definitions (Dynkin et al. 2021, ch. 13 and 14)

### What the source says
1. ESP (ch. 13): excess spread over rating x industry x duration peers, after a control for excess leverage over the same peers. Monthly. The book reports that the leverage control "moderately improves" the decile spread in investment grade, 1993 to 2016.
2. SPiDER (ch. 14): issuer OAS / (debt / sustainable EBITDA). Sustainable EBITDA is the mean of the last 10 annual EBITDA figures, at least 6. Formed each end of February with a 2-month lag, held 12 months. One rank across all sectors. Financials are out.

### What we built (`hy/peers.py`)
1. `esp_lev_<cell>` = ESP minus b_t times excess log leverage over the same peers. b_t is one cross-section slope per month, pooled over all cells, because one cell holds too few issuers for its own slope. The median b_t is +0.11 and it is positive in 87% of months.
2. `spider` = log of the issuer's median bond spread / (latest quarterly debt / sustainable EBITDA). The annual EBITDA comes from `comp.funda` (`peer_data.annual_ebitda`), with available_at = fiscal year end + 90 days. `comp.funda` is the restated view, not point in time. The 10-year mean damps the effect of a restatement.
3. `spider_sr` = SPiDER against sector x rating peers. This is the book's rating-industry check.
4. Gaps against the book: G-spread, not OAS. Equal weight over the issuer's bonds, not market value, because the panel has no amount outstanding. CCC bonds stay in the universe, and the book's high yield universe drops them.

### Test result (2008 to 2026, rank IC after cost, IC beyond spread level with HAC t)

| Signal | Beyond spread 6m | Beyond spread 12m | Feb only, 12m (19 years) |
| --- | --- | --- | --- |
| ESP, sector x rating (ours) | +0.072 (2.6) | +0.096 (2.6) | +0.121 (2.4) |
| ESP with leverage control (book) | +0.029 (1.2) | +0.044 (1.3) | +0.063 (1.3) |
| SPiDER, absolute (book) | +0.016 (0.8) | +0.032 (1.3) | +0.055 (1.6) |
| SPiDER vs sector x rating | +0.012 (1.0) | +0.021 (1.3) | +0.033 (1.3) |
| E13 vs sector x rating | +0.023 (1.1) | +0.026 (0.9) | n/a |

Every signal has a positive raw IC after cost in all four cycle windows. Buy the widest has the highest raw IC at every horizon (0.342 at 12m). SPiDER covers 39% of bond-months. The rest lack 6 annual figures, are financials, or have non-positive sustainable EBITDA.

### What the data says
1. The book versions do not beat our versions in this high yield panel. No book version passes t 2 beyond spread.
2. The leverage control halves the ESP edge beyond spread. The part of the peer spread gap that leverage explains also predicts return in this panel.
3. SPiDER at the book's horizon and schedule is better than E13 at 3 to 6 months, but the edge beyond spread is small (t 1.3 to 1.6).
4. The horizon was not the problem. All edges beyond spread grow from 3 to 12 months, and the ranking of the signals stays the same.

### Decision
1. Keep ESP as built (no leverage control). It stays the best peer signal: +0.096 beyond spread at 12 months (t 2.6). It still has no weight until it passes the cycle bar.
2. Keep E13 at its weight. Report SPiDER beside it in step 9. Do not swap E13 for SPiDER: the gain (+0.032 against +0.026 beyond spread) is inside the noise.
3. CoreWeave has 3 annual EBITDA figures, so it has no SPiDER by the book rule.

### Test that settles the rest
Rerun with OAS and amount outstanding (a Bloomberg or ICE index feed). If SPiDER beyond spread passes t 2 at 12 months, swap it for E13.
