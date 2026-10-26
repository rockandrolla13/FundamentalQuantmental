# F24. Rating x tenor cell valuation percentile (with the BB/BBB and B/BB spread ratios)

- **Rank:** 24. **Tier:** 4. **Status:** NEW. It is time-series value per cell. The known value factors (S1, Houweling and van Zundert) are cross-sectional.
- **Sources** (folder `/home/ak/Documents/Quant Credit/Work_Quant (1)/`, PDF pages):
  - Nicol, "Another vol test passed; Short dated BBs attractive", Deutsche Bank HY Strategy, 2 March 2021. File `short dated hy to position versus vol (1).pdf`, p. 5 (Figures 7 and 8).
  - Nicol, Global Leveraged Finance Weekly, Deutsche Bank, 5 March 2021. File `5de4d6ff_7cf2_4fdf_8edb_d55fde385a63_604 (1).pdf`, pp. 7 and 8.
  - Jezek, "Macro Credit Brief - Spreads, Rates and the Common QE Factor", Deutsche Bank IG Strategy, 22 February 2021. File `Macro Credit Brief - Spreads, Rates and (1).pdf`, pp. 11 to 13.
- **Reader blocks:** F-F3 (`research/notes/quant-credit-review/out_F.md`), G-F10 (`out_G.md`). Every number below was checked on the source page.
- **Evidence:** snapshots only (19 February and early March 2021). No source gives a backtest, a hit rate or a horizon. This page proposes the test.

## Claim
In US high yield, bonds in a rating x tenor cell whose median spread ranks high against the cell's own history earn a higher excess return over duration-matched Treasuries over the next 3 months. The monthly rank IC beyond spread is positive.

## Definition
```latex
m_{c,t} = \operatorname{median}_{i \in c,\,t}\, s_{i,t}, \qquad
P_{c,t} = \frac{1}{N_{c,t}} \sum_{\tau \in W_t,\ \tau < t} \mathbf{1}\{m_{c,\tau} < m_{c,t}\}, \qquad
\mathrm{score}_{i,t} = P_{c(i),t}
```
```latex
R^{BB/BBB}_{k,t} = \frac{m_{BB,k,t}}{m_{BBB,k,t}}, \qquad R^{B/BB}_{k,t} = \frac{m_{B,k,t}}{m_{BB,k,t}}, \qquad k = 1\text{-}3\text{y}
```
Intuition: every cell moves with the cycle, so the cell's own history is the peer group that controls for its structural spread level.

What the sources say:
- Cells: rating BBB, BB, B, CCC x tenor 1-3, 3-5, 5-7, 7-10 years (p. 5 Fig. 7, deck p. 8). CCC has only an "Overall" figure: the note excludes CCC curve points "given the lack of market size" (p. 5). The IG tables add 10-15y and 15+y, or one 10+y bucket (pp. 11 to 13).
- History: "since 2009" in the note (p. 5). The deck prints the same table as "since 2010" (p. 8). The IG brief ranks "since 2000" and "since 2015" (p. 11).
- Sign convention. The HY note: 100% means spreads at tights, 0% at the wides (p. 5). The IG brief: x% means the series "has been lower x% of the time" (p. 11). The two are opposite. We use the IG brief form, so a high P means wide, which means cheap.
- March 2021 snapshot in the note convention (p. 5, deck p. 8): $HY BB 1-3y 60%, 7-10y 92%. $HY B 1-3y 58%, 7-10y 96%. BBB 99% to 100% at every tenor.
- Spreads (p. 5 Fig. 7, $HY, 1-3y): BBB 63 bp, BB 224 bp, B 429 bp. The table prints four spreads under five headers. Only the 1-3y reading gives the stated "above 3.5x" BB/BBB ratio (224 / 63 = 3.56). €HY: 199 / 77 = 2.58, "closer to 2.5x" (p. 5).
- Ratios: 1-3y BB/BBB and 1-3y B/BB (p. 5 Fig. 8, deck p. 8). The text calls BB/BBB "historically wide" and B/BB "closer to the long-run average" (p. 5). No number for the long-run average is printed.
- Range context: rolling 6-month HY spread ranges are 100 to 200 bp in a benign period (deck p. 7).

Parameters (our choices unless a page is cited):
- Tenor buckets: 1-3, 3-5, 5-7, 7-10 years (p. 5), plus 10+ years (p. 12 "10+y"). Bonds under 1 year fail `eligible`.
- CCC: one pooled cell across tenors (p. 5).
- Rating: S&P class to February 2017, then the leverage-implied class, as `hy.factors.f04_bond_momentum.rating_classes`. BBB = class IG with a BBB symbol, or class IG implied (no symbol). A to AAA bonds have no cell. Defaulted symbols D and SD are out.
- Cell median: needs 5 distinct issuers in the cell that month (`hy.peers.MIN_PEERS`). Else no median.
- Window W: expanding, all prior months with a median. A rolling window is a parameter (`window_months`).
- Minimum history: 3 years of prior cell medians (36 months). The source windows are 6 to 21 years. 3 years lets the 2008 cycle score from a 2005 start.
- Ties: strict "<" (p. 11 wording "has been lower"). The current month is not in its own history.
- Ratio bucket: 1-3y only (p. 5). The ratio also gets an expanding percentile with the same minimum history.

## Inputs
| Field | Production table and column | as_of | available_at rule | Have |
|---|---|---|---|---|
| G-spread, years to maturity, eligibility fields | `bond_panel` `g_spread`, `years`, `price`, `yield`, `mod_dur`, `carried` | `date` | panel `available_at` | have |
| Issuer key | `bond_panel.gvkey` | `date` | panel `available_at` | have |
| S&P rating | `ratings.splticrm` | `datadate` | panel `available_at`, stale after 62 days | have, to Feb 2017 |
| Leverage, LTM EBITDA (implied class) | `leverage` `leverage`, `ltm_ebitda` | `date` | panel `available_at` | have |
| Cell history (optional cache) | `cell_history` (new): `date`, `cell`, `rating`, `tenor`, `median_spread`, `n_bonds`, `n_issuers`, `available_at` | `date` | decision_time(date) | built by `cell_history` |

## Build steps
1. For each month end t, keep `eligible` rows of `bond_panel` with `available_at` <= decision_time(t) and a gvkey.
2. Give each bond its rating class at t (step 1 rule). Map IG to BBB as above. Drop A and better, D and SD.
3. Give each bond its tenor bucket from `years`. CCC bonds take the pooled cell.
4. Cell median spread m_{c,t} where the cell has 5 or more issuers.
5. Stack the medians into the cell history. The production machine may cache it as the panel `cell_history`.
6. At as_of, P_{c,t} = share of the cell's prior medians strictly below today's median. NaN with fewer than 36 prior medians.
7. Score each BB, B and CCC bond with its cell P. Add the 1-3y ratios and their percentiles to every row.

## Code placement
- `hy/factors/f24_cell_percentile.py`. `compute(panels, as_of, window_months=None, min_history_years=3, min_issuers=5)`. The optional panel `cell_history` is the cache. Without it, compute rebuilds the history from `bond_panel`.
- Helpers: `tenor_bucket`, `cell_rating`, `cell_key`, `month_cells`, `cell_medians`, `cell_history`, `own_history_percentile`, `spread_ratios`.
- Reuses `hy.factors.f04_bond_momentum.rating_classes`, `hy.peers.rating_class`, `hy.peers.MIN_PEERS`, `hy.backtest.decision_time` and `eligible`.
- Methodology Section 8, S7 (the sector-tilt slot) and S1 (value). Output columns: `score`, `cell`, `rating`, `tenor`, `cell_spread`, `cell_pct`, `cell_n_hist`, `ratio_bb_bbb`, `ratio_b_bb`, `ratio_bb_bbb_pct`, `ratio_b_bb_pct`.

## Tests
- Unit: no look-ahead (rows after as_of and late `available_at` change nothing). Sign: a cell at its widest gets P = 1, at its tightest P = 0. History shorter than 36 months gives NaN. A cell with fewer than 5 issuers gives NaN. CCC pools tenors. Missing panels give an empty frame. Ratio check against p. 5: 224 / 63 = 3.56.
- Evaluation (production machine): monthly rank IC of score against the 3-month `realised_excess_return`, beyond `g_spread` (`ic_beyond`), after cost from `bid_ask_pts`. Pass: positive in at least 3 of the 4 `CYCLE_WINDOWS`. Reader thresholds: F-F3 asks IC > 0.03 on cell terciles. G-F10 asks mean IC > 0.05 across 16 cells.

## Risks
- No backtest exists. The only evidence is one snapshot that says short BB and B looked better value than long tenors.
- Few cells: 16 in all, 11 of them scored (BB and B x 5 tenors, CCC pooled). The score is constant inside a cell, so the bond-level IC has large ties and few independent bets.
- Regime drift: a cell's "normal" level moves with index composition, so an expanding history can call a cell cheap for years (2009 wides dominate the history).
- Overlap: cell value overlaps S1 value and the curve shape factor (rank 22). The sources give no correlation.
- Rating gap after February 2017: the implied class is noisier than the actual rating. The BBB cell becomes "implied IG", which in an HY-heavy panel holds few issuers.
- Cost: cell membership changes slowly. Turnover comes from tenor roll-down across bucket edges and rating moves.

## Open questions
- Window. Expanding (default) against rolling 10 years (F-F3) or since 2015 (p. 11). Our choice: expanding, because it uses the most data.
- Horizon. The sources give none. Default 3 months, as both reader tests propose.
- Ratio use. The sources read the BB/BBB ratio as value of BB against BBB. Default: index-level columns only, not in the score. A ratio tilt needs its own test.
- Spread measure. The sources use ICE index OAS. We use the median bond G-spread. Default G-spread, the panel measure.
