# F27. Real-yield shock regime (with the spread-rate correlation regime)

- **Rank:** 27. **Tier:** 5 (HY index timing, candidate to replace S7). **Status:** NEW at index level. It supplies the growth-against-policy split that methodology Section 9.2 asks for.
- **Level:** index. Key `index` = `"US_HY"`. One row per month end.
- **Sources** (folder `/home/ak/Documents/Quant Credit/Work_Quant (1)/`, PDF pages). All are Deutsche Bank research, February and March 2021.
  - Reid, "Yields & Credit Spreads - The long-term relationship", 3 Mar 2021. `IG & HY Strategy/6fe578e7_327e_4086_ad32_37e89cca52f2_604 (1).pdf`, pp. 1 to 6.
  - Jezek, "Macro Credit Brief - Spreads, Rates and the Common QE Factor", 22 Feb 2021. `Macro Credit Brief - Spreads, Rates and (1).pdf`, pp. 2 to 4.
  - Nicol, "Another vol test passed; Short dated BBs attractive", 2 Mar 2021. `short dated hy to position versus vol (1).pdf`, pp. 2 to 4.
  - Nicol, "Global Leveraged Finance Weekly", 5 Mar 2021. `5de4d6ff_7cf2_4fdf_8edb_d55fde385a63_604 (1).pdf`, pp. 5 to 6. It repeats the 2 Mar figures.
  - Credit Derivatives Strategy, 1 Mar 2021. `1574b3c6_68dd_11eb_8fc9_3e217c25b0c2_604 (1).pdf`, pp. 4 to 5.
  - Sparks, "Anatomy of a tantrum", 1 Feb 2021. `anatonomy of a tantrum (1).pdf`, p. 1. Context only: no spread number.
- **Reader blocks:** F-F1, F-F2 (`research/notes/quant-credit-review/out_F.md`), G-F9 (`out_G.md`). Every number below was checked on the source page.

## Claim
At a month end where the 10-year Treasury yield rose 40 bp or more over 3 months, and the breakeven rose more than the TIPS real yield, the US HY index spread tightens over the next month. Where the real yield led the rise, or yields fell 40 bp or more, it widens. **No source tests the real-against-breakeven split.** The split rests on rolling-correlation charts (Reid pp. 3, 5) and on one-episode comments.

## Definition
```latex
\Delta y_t = y^{nom}_t - y^{nom}_{t-h},\quad \Delta r_t = r^{real}_t - r^{real}_{t-h},\quad \Delta\pi_t = \pi^{be}_t - \pi^{be}_{t-h},\quad h = 3\ \text{months}
\\
\text{regime}_t = \begin{cases} \text{inflation\_selloff} & \Delta y_t \ge k,\ \Delta\pi_t > \Delta r_t \\ \text{real\_selloff} & \Delta y_t \ge k,\ \Delta r_t \ge \Delta\pi_t \\ \text{rally} & \Delta y_t \le -k \\ \text{neutral} & |\Delta y_t| < k \end{cases},\qquad
\text{score}_t = \{+1,\,-1,\,-1,\,0\}
```
Intuition: a rise in yields from growth and inflation expectations helps leveraged issuers, while a rise in real yields raises their funding cost.

What the sources say:
- Since the 1950s the 2-year rolling correlation of 3-month changes in the 10-year yield and BBB spreads is mostly negative (Reid p. 3, Fig. 3). The correlation with real yields trends up and stays positive through the pandemic (pp. 1, 3). Fig. 6 (p. 5) shows the same for USD IG and HY. "Real yields are likely the key thing to watch" (p. 1).
- Reid p. 1: a rise in nominal yields from stronger growth "and even normalising inflation" gives "little to worry about". A rise in real yields gives a leveraged market "much more to worry about".
- In the 6 largest 5-year Treasury sell-offs since the GFC (43 to 131 bp, 65 to 252 days), $HY tightened 77 bp on average and 65 bp at the median. Only 2013 widened, by 16 bp (Nicol p. 3, Fig. 4). Jezek counts 27 sharp 10-year sell-offs for USD IG 7-10y and 21 for EUR IG in two decades. Spreads tightened in the "overwhelming majority" (p. 2).
- Rolling 12-week correlation of weekly $HY spread and rate changes: range −0.2 to −0.8, average −0.6 ($HY) and −0.5 (€HY), since 2005 (Nicol p. 2). The 5-year point is "the most relevant point on the rate curve for HY given duration" (p. 2).
- The 2013 widening came from a common QE factor that lifted the term premium and illiquidity premia together (Jezek pp. 2 to 3). Under a taper fear "we would indeed expect credit spreads to widen as rates rise" (p. 4). The CDS note calls 2013 the "standout exception" with a strongly positive correlation (1574b3c6 p. 4).

What we decide:
- Nominal `DGS10`, real `DFII10`, breakeven `T10YIE`. Without `T10YIE`, π = DGS10 − DFII10 (exact split). `split_gap` = Δy − Δr − Δπ shows the gap when `T10YIE` is used.
- h = 3 months. Our choice: Reid uses 3-month changes (p. 3). Jezek uses 1-month changes (p. 3). Nicol's episodes last 65 to 252 days (p. 3).
- k = 40 bp. Our choice: the smallest episode in Fig. 4 is 43 bp, and Nicol's text says "30-40bps" (p. 3). Reader F-F2 also proposes 40.
- Endpoints: the last value on or before as_of and on or before as_of − 3 month ends, each at most 7 days old (our choice).
- Variant column `split_signal` = −(RYS − BES), with RYS = Δr / sd(Δr) and BES = Δπ / sd(Δπ). The sd uses the 24 prior month-end 3-month changes, at least 12 (our choice: Reid's 2-year window). Reader F-F1 proposes it with 1-month changes.
- **Conditioner columns.** `rho_nominal` and `rho_real`: the correlation of HY spread changes with the 5-year yield (`DGS5`, else `DGS10`) and with `DFII10`. Weekly changes over 12 weeks, at least 8 (Nicol p. 2). Fallback: monthly changes over 24 months, at least 12 (our choice). Spread: `hy_index`, else `BAMLH0A0HYM2`. `rho_positive` = ρ > 0 (G-F9 risk-off flag). With `rho_gate=True`, a sell-off with ρ > 0 scores −1 (Jezek p. 4). Default off: the evidence is one episode, 2013.
- **Quality columns (F-F2).** `rise_from_trough` = 5-year yield (else 10-year) minus its 3-month low. `compression_state` = rise ≥ 40 bp. `quality_tilt` = +1 (long B against BB, DTS-neutral) in that state, else 0. B − BB tightened 32 bp on average and 29 bp at the median, in 5 of 6 episodes (Nicol p. 3, Fig. 4). `b_bb_change` and `ccc_b_change` are the 3-month changes of B − BB and CCC − B OAS. No source gives CCC numbers: `ccc_b_change` is descriptive.

## Inputs
| Field | Production table and column | as_of | available_at rule | Have |
|---|---|---|---|---|
| Rates, real yield, breakeven | new optional long panel `macro_series` (`series_id`, `date`, `value`, `available_at`), schema of F25. Series `DGS10`, `DFII10`, `T10YIE`, `DGS5`, FRED, percent | `date` | `date` + 1 day | need |
| HY and rating OAS | `macro_series` `BAMLH0A0HYM2`, `BAMLH0A1HYBB`, `BAMLH0A2HYB`, `BAMLH0A3HYC`, FRED, percent | `date` | `date` + 1 day | need |
| Index spread | `hy_index` `spread` (decimal), `date` (wiring 4.5) | `date` | `date` + 1 day | have (monthly here) |

Required: `DGS10` and `DFII10`. Without `macro_series` the result is an empty frame. Without either series, the row has status `missing_series` and a NaN score. FRED limits ICE BofA series to a recent window (card `research/cards/forecast-ice-hy-oas.md`, not verified at ICE). The production machine needs the licensed history.

## Build steps
1. Keep rows with `available_at` <= `decision_time(as_of)` and `date` <= as_of. Keep the last vintage per series and date. Divide percent values by 100.
2. Take the endpoints of DGS10, DFII10 and the breakeven. A missing or stale endpoint gives status `stale` and a NaN score.
3. Compute Δy, Δr, Δπ, the regime, the lead (`real` or `breakeven`) and the score. Apply `rho_gate` if set.
4. Compute RYS, BES and `split_signal` from the prior 24 month ends.
5. Compute ρ: weekly on `hy_index`, weekly on `BAMLH0A0HYM2`, then monthly on each. The first with enough changes wins. Record `rho_source`, `rho_freq`, `rho_n`.
6. Compute the quality columns.

## Code placement
- `hy/factors/f27_real_yield_regime.py`. `compute(panels, as_of, window_months=3, shock=0.004, regime_scores=None, rho_gate=False)`.
- Output columns: `date`, `index`, `score`, `available_at`, `regime`, `lead`, `status`, `signal_date`, `window_months`, `d_nominal`, `d_real`, `d_breakeven`, `real_share`, `split_gap`, `be_source`, `rys`, `bes`, `split_signal`, `rho_nominal`, `rho_real`, `rho_source`, `rho_freq`, `rho_n`, `rho_positive`, `rate_tenor`, `rise_from_trough`, `compression_state`, `quality_tilt`, `b_bb_change`, `ccc_b_change`.
- Helpers: `macro_wide`, `value_at`, `yield_split`, `classify_regime`, `split_zscores`, `change_corr`, `rise_from_trough`. Reuses `hy.backtest.decision_time`. Docstrings cite Section 9.2 (yield split) and Section 8 (S7).

## Tests
- No look-ahead: rows after as_of and rows with `available_at` after the decision time change nothing.
- Sign: a breakeven-led rise of 60 bp gives +1. A real-led rise gives −1. A 60 bp fall gives −1. A 10 bp move gives 0.
- Edges: no `macro_series` gives an empty frame. No `DFII10` gives `missing_series`. A stale endpoint gives `stale`. No `T10YIE` gives the derived breakeven and `split_gap` = 0. Monthly `hy_index` falls back to `BAMLH0A0HYM2` weekly, then to monthly.
- Helpers: hand values for the split, the z-scores, the correlation and the trough rise.
- Evaluation (production machine): regress the next 1-month change of the HY index spread on the score, 2003 to 2024, Newey-West. Pass: slope < 0 with t < −2 (reader F-F1). And `split_signal` beats a nominal-only model (Δy alone) on out-of-sample R² in at least three of the four `CYCLE_WINDOWS`. Quality: DTS-neutral B minus BB excess return positive in 70% of `compression_state` episodes, bootstrap p < 0.10 (reader F-F2). ρ flag: 4- and 12-week HY excess return at least 1% a year lower when ρ > 0, t > 2 (reader G-F9).

## Risks
- **Source conflict on a real-led sell-off.** Reid reads rising real yields as bad for credit (p. 1). Nicol (p. 3) and Jezek (p. 3) read the real-led sell-off of February 2021 as a growth signal, "positive for spreads". We follow Reid, because his reading rests on decades of rolling correlations, while the other two comment on one fortnight. `regime_scores` lets the production test flip it.
- Contemporaneous, not forward. Fig. 4 measures spreads over the sell-off. After the peak, $HY widened 104 bp on average and 82 bp at the median over 6 months (5 episodes, Nicol p. 3). A 1-month signal in an ongoing episode can still lose over a longer hold.
- The episodes are chosen trough to peak with hindsight (Nicol p. 3). Our rule uses a fixed trailing window, so it triggers late and less often.
- Spikes: 50 to 100 bp temporary wides within the 2013, 2015 and 2019 episodes (Nicol p. 4).
- Horizon: the CDS correlation turns more negative as the change horizon grows from 1 day to 3 months (1574b3c6 p. 5, Figs. 16 to 17, IG CDS indices). A weekly ρ is noisier than a 3-month one.
- Overlap: the score is close to a sign of Δy whenever breakevens lead, so it overlaps a nominal rate-momentum rule. F25 and F26 also time the index.

## Open questions
- Rally split. Reid's positive real correlation implies a real-led rally helps spreads, but the nominal evidence says a rally widens (Nicol p. 2). Default: rally = −1 for both leads. The `lead` column lets the production test split it.
- Term premium. Jezek's driver is the QE-sensitive term premium (p. 2). Sparks finds it more than two standard deviations rich in Feb 2021 (p. 1). Reader F-F1 proposes the ACM term premium as a variant. Not built: no panel holds it.
- Rate tenor. Default 10-year for the split (TIPS depth) and 5-year for ρ and the quality state (Nicol p. 2).
