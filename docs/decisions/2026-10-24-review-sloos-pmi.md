# Review `sloos_tightening` and `pmi` as macro inputs

Date: 24 October 2026. Status: open. Nothing changes in code until the tests below run.
Sections: methodology 3.6, 5.2 (and the proposed 5.2.1); framework F6 (phase vote).
Code that uses them: `hy/macro.py` (`INDICATORS`, `_vote`, `phase_vote`; the PMI map `50 + 4 zG` in the paths), `hy/forward.py` (`fit_decline_model`, through `m_t`).
Related: `2026-10-24-downside-weight-model` (proposed 5.2.1, written by another session, not yet on main) and `2026-10-24-wt-relationship-tests`.

## Context
The model uses the two series in two places:
1. **The downside model (5.2).** Both series are columns of `m_t`. They set the probability of a large EBITDA decline, and so the scenario weights.
2. **The F6 phase vote.** "PMI below 50" and "net tightening positive for two quarters" are two of the six votes that classify the cycle phase. The phase sets the prior weights of the cases.

The proposed revision 5.2.1 already drops `pmi` from `m_t` until its test T3 admits it. It keeps `sloos_tightening`. It does not touch the F6 phase vote.

## What the sources say
1. Tighter lending standards lower output and widen credit spreads. But the raw net percentage mixes in loan demand. A demand-adjusted indicator explains about 20% of output variance (Bassett, Chosak, Driscoll, Zakrajšek 2014; card `forecast-sloos`).
2. Credit spreads, and the excess bond premium in particular, lead activity (Gilchrist and Zakrajšek 2012). The lagged default rate predicts defaults better than the lagged spread over 150 years (Giesecke et al. 2011). Neither source tests the PMI on firm results.

## What the data says (`scripts/wt_tests.py`, claims H8b and H8c)
Universe: 17,767 US non-financial firms, equal weight, 1994–2026. Outcome: the share of firms whose EBITDA falls by more than 20% over the next four quarters. Controls: the other macro inputs and the outcome's own lag. PMI proxy: the Philadelphia Fed current activity index, because ISM data is licensed.

| Input | 1994–2011 | 2012–2026 | Forecast gain from 2012 (Clark–West p) | Cycles as claimed |
|---|---|---|---|---|
| `sloos_tightening`, all firms | t +5.3 | t 0.0 | 0.28 | 2 of 4 |
| `sloos_tightening`, high-leverage firms | t +3.3 | t -0.7 | 0.75 | 1 of 4 |
| PMI proxy, all firms | t -0.1 (claimed sign negative) | t -1.1 | 0.81 | 3 of 4 |
| PMI proxy, high-leverage firms | t +1.4 | t +0.1 | 0.78 | 2 of 4 |
| Baa spread change (for comparison), high-leverage firms | t +3.5 | t +3.0 | 0.04 | 3 of 4 |

1. **Lending standards worked before 2012 and not after.** After 2012 the tightening episodes were 2020 and 2023. In 2020, standards tightened when EBITDA had already fallen, so the next four quarters show recovery. That may explain the break. The data here does not prove it.
2. **The PMI proxy predicted the average firm's declines in neither period.**
3. **But firm sensitivity to the PMI proxy persists** (test C: carry-over slope 0.20, t 3.6 after 2012). Firms that suffered more declines after weak readings before did so again. So the PMI may matter as a term that differs by firm, not as a common level.

Limits of this evidence:
- The universe is all firms, not HY issuers.
- The event uses a fixed 20% decline, not the issuer's own `δ_i`.
- Outcomes come from Compustat's current view.
- The PMI is a proxy.

## Options
1. Keep both inputs in both places. Rejected: the history above gives no support after 2012.
2. Drop both now, from `m_t` and from the phase vote. Rejected for now: the evidence comes from a different universe and a different event. A removal should rest on the model's own target.
3. **Mark both as unproven and run the tests below on the issuer universe and the issuer's own event. Keep the current code until then. Chosen.**

## Choice
1. `pmi` stays out of `m_t`, as 5.2.1 proposes. The study agrees. Add one candidate to test T3 of 5.2.1: `pmi` interacted with the cyclical class (Section 4.4), because firm sensitivity persists.
2. `sloos_tightening` stays in `m_t` only if test S1 below passes. Add the demand-adjusted indicator of Bassett et al. as a candidate, if a published series exists. Not verified yet.
3. The F6 phase vote keeps its six votes until test S3 runs. A vote that fails S3 leaves the vote. The majority then counts the remaining votes.

## Tests that settle it
Run each test on the HY issuer universe (TRACE-linked Compustat point-in-time) with the 5.2 event label (`decline_labels`, threshold `δ_i`). Run out of sample in the 2008, 2015, 2020, and 2022 windows.

| Test | Question | Fails if |
|---|---|---|
| S1 | Does `sloos_tightening` earn its place in `m_t`? | Its removal does not lower the out-of-sample log score in at least 3 of 4 windows (same rule as T3 of 5.2.1) |
| S2 | Does `pmi` earn a place, as a level or interacted with the cyclical class? | Neither form lowers the out-of-sample log score in at least 3 of 4 windows |
| S3 | Does each phase vote carry information? | The vote's late-cycle flag does not raise the realised share of issuers in their downside case over the next four quarters, in at least 3 of 4 windows. Then drop the vote |
| S4 | Is the break real or a 2020 artefact? | Rerun S1 and S3 without 2020. If `sloos_tightening` passes without 2020, record the result. Then use a rule that excludes pandemic quarters, with its own decision page |

The decision closes when S1 to S4 have run and this page records the outcome. Each change to `hy/macro.py` or `m_t` gets a test that fails on the old behaviour.

## Frozen specification for S1 to S4 (24 October 2026)
This section fixes the tests before the results run. Code: `scripts/s_tests.py`. Tests: `tests/test_s_tests.py`. Output: `data/raw/backtest/s_tests.json` (vendor-derived, out of git).

Disclosure: one run of S1 to S3 took place before this freeze. That run used the event, inputs, windows, models, and log-loss rule below. After that run, the coordinator added the attrition rule, the EWC test, and the Ibragimov–Müller test. I also added three context outputs: `m_t` against a sector-only model, the in-sample gain, and a pooled gain. No input, window, threshold, or pass rule changed after that run.

### Event
1. Unit: one issuer in one fiscal quarter `t` (gvkey, quarter end).
2. `D = 1` if `LTM EBITDA_{t+4} < (1 − δ) LTM EBITDA_t`, with `LTM EBITDA_t > 0` (`hy.forward.decline_labels`).
3. Each LTM is the first-release value. It is the sum of four consecutive quarters of `oibdp`. Each quarter takes its latest version known on the first day that the end quarter was known. Consecutive means gaps of 80 to 100 days between quarter ends.
4. `δ = 20%` is the primary. `δ = 10%` and `δ = 30%` are robustness runs. The page asks for the issuer's own `δ_i`. That value has no history, so this is a deviation.
5. Attrition, two variants:
   - "exclude": a row with no `LTM EBITDA_{t+4}` leaves the sample.
   - "exits": a row with no `LTM EBITDA_{t+4}` counts as `D = 1` when `comp.company` shows `dlrsn` 02 (bankruptcy) or 03 (liquidation), with `dldte` after `t` and no more than 21 months after `t`. Other rows with no outcome leave the sample. The outcome is known on `dldte` + 1 day.

### Universe and time
1. Universe: gvkeys with an unambiguous link to a TRACE HY bond in `panel_full` at month end `M`.
2. Decision time `τ`: the first day on which the LTM of `t` is known in Compustat point in time. `M = τ − 1 day`.
3. Windows: `hy.backtest.CYCLE_WINDOWS` (2008–2009, 2015–2016, 2020, 2022). Test rows have `τ` inside the window. Train rows have an outcome known before the window starts.
4. The 2008 window trains on HY-like Compustat firms, 1994–2007, from `comp.fundq` (current view, not point in time): debt / LTM EBITDA > 4, LTM EBITDA > 0. That window replaces the two `hy_oas` columns with the Baa spread level and its 3-month change.

### Inputs (each known at `M`)
| Column | Definition | Release rule |
|---|---|---|
| `spread_lvl` | HY index level, `hy.backtest.benchmark_spread` (`state.hy_index_level`) | TRACE row available by `M` + 1 day |
| `spread_chg3` | Change of `spread_lvl` over 3 months | Same |
| `sloos` | Latest `DRTSCILM` reading | A reading dated month m enters at the end of month m + 1 |
| `pmi` | Philadelphia Fed GAC, the PMI proxy | Month `M` |
| `baa_chg6` | Change of the monthly mean of `BAA10Y` over 6 months | Month `M` |
| `lev` | Debt / LTM EBITDA at `t`, clipped to [0, 20] | First release of `t` |
| sector | GICS sector from `gics_history` at `τ` | `available_at` ≤ `τ` |

The code standardises each column with the train mean and standard deviation.

### Models
- Base "macro": the 5.2 logistic (`fit_decline_model`) on the five `m_t` columns and the sector.
- Base "macro_lev": the same plus `lev`, because the proposed 5.2.1 adds issuer state.
- S1: the base against the base without `sloos`.
- S2: the base without `pmi` against (L) the base with `pmi`, and (I) the base with `pmi` and `pmi × cyclical`. Cyclical sectors: GICS 10, 15, 20, 25. All other sectors are defensive.
- S3: for each F6 vote, the share of `D = 1` with the flag on at `τ` minus the share with the flag off. Votes: `hy_oas` (above its trailing 60-month median and up over 3 months), `distress_ratio` (above its trailing 60-month median), `sloos_tightening` (the last two readings positive), `pmi` (GAC below 0, not 50, because GAC is centred on 0). The medians need at least 6 months, because the panel starts in January 2008. Two combined flags: majority (more than half of the available votes) and `phase_vote` late (late_cycle or downturn). `default_rate_fcst` and issuance quality cannot be built.
- S4: S1 and S3 on the windows 2008, 2015, and 2022. Two exclusions: drop rows whose `t` ends in 2020, or drop rows whose span from `t` to `t+4` touches 2020.

### Scoring and pass rules
1. Gain = log loss of the smaller model minus log loss of the larger model, per row. A positive gain means that the term helps. The page says "lower the log score". This study reads that phrase as "lower the log loss of the model that holds the term".
2. Per window, report the row mean gain with a quarter-block bootstrap 95% interval (2,000 draws, seed 42), and the Brier gain.
3. Per window, also average the gain across issuers within each quarter. Test the mean of that quarterly series with the EWC long-run variance (Lazarus, Lewis, Stock, Watson 2018): `Λ_j = sqrt(2/T) Σ_t cos(π j (t − ½)/T) u_t`, `Ω = (1/ν) Σ_{j=1..ν} Λ_j²`, `ν = max(1, floor(0.4 T^{2/3}))`, and a t distribution with `ν` degrees of freedom. The same test runs on the pooled quarterly series of all test windows.
4. A term passes S1 or S2 when its gain is positive in at least 3 of 4 windows. A vote passes S3 when its difference is positive in at least 3 of 4 windows. In S4 the rule is at least 2 of 3 windows, and the output also shows 3 of 3.
5. Next to each window count, report the Ibragimov–Müller t-test across the per-window values: `t = mean / (sd / sqrt(q))` with `q − 1` degrees of freedom, one-sided. A fair coin passes the 3-of-4 count with probability 5/16 = 31%.
6. Report the results with and without the 2008 window.

## Results (run 24 October 2026)
Run: `HY_DATA_ROOT=<data/raw> PYTHONPATH=. python3 scripts/s_tests.py`. Output: `data/raw/backtest/s_tests.json`. Units: a log-loss gain is in thousandths of a nat per issuer-quarter. A positive gain means that the term helps. Brackets hold the 95% quarter-block bootstrap interval. "IM" is the Ibragimov–Müller test across windows. All numbers are for `δ = 20%` and the "exclude" attrition variant, unless a line says otherwise.

**Verdict: S1, S2, and S3 fail. S4 gives a weak pass for `sloos_tightening` on one base only, under a rule that this study set.** A larger finding sits behind the tests. Outside 2008, the full `m_t` does not beat a model with the sector alone.

### Sample
| Step | Issuer-quarters |
|---|---|
| In the TRACE HY universe at `τ` (1,945 issuers) | 39,834 |
| Removed: a quarter missing in the LTM window (mostly the comp_pit fiscal Q4 gap) | 11,312 |
| Removed: first release more than 200 days after the quarter end (back-fill) | 479 |
| Removed: LTM EBITDA not positive | 1,103 |
| Removed: no outcome at `t+4` (5,406 of them with `t` in 2017–2025) | 8,197 |
| Final (1,430 issuers), event rate 16.1% | 16,906 |

Test rows per window: 2008: 1,819 (8 quarters). 2015: 2,056 (9). 2020: 740 (5). 2022: 701 (5). The 2008 window trains on 41,014 HY-like Compustat rows from 1994–2007 (event rate 24.1%).

Trap counts at the vintage level (156,101 issuer-quarters in the cache):
- No snapshot version: 20,557.
- A missing quarter in the LTM window: 24,737 (17,105 of them in 2018–2025).
- Year-to-date cash-flow fields: 0, because the event uses `oibdp`, an income-statement field.
- TRACE timing: the universe uses only rows with `available_at` ≤ month end + 1 day.

**Defect found in `hy/sources/trace_panel.leverage_as_of`.** The function accepts any four latest quarters that span 400 days or less. When a quarter is missing, it sums four quarters that are not consecutive and calls the sum LTM. This affects 22,122 issuer-quarters of the cache, and so it affects `leverage_full.parquet`. This study does not read `leverage_full`. It rebuilds LTM from the same vintages with a 250–300 day span. The defect needs its own fix and test.

### Context: does `m_t` help at all?
Gain of the full `m_t` over a sector-only model: 2008 +24.6 [−1.3, +55.6], 2015 −5.7 [−13.1, +1.6], 2020 −9.8 [−76.3, +60.7], 2022 −4.4 [−14.0, +1.4]. At `δ = 10%` and `δ = 30%`, the sign pattern is the same. So the 5.2 macro vector, as built here, helps in 2008 only. Each S test below removes or adds one column of a vector that does not beat its own null after 2009.

### S1: `sloos_tightening` in `m_t`. Fail.
| Window | Macro base | Macro + leverage base |
|---|---|---|
| 2008 | +2.9 [−4.9, +11.2] | −3.7 [−16.3, +9.4] |
| 2015 | +14.2 [+2.0, +27.6] | +14.4 [+2.3, +28.0] |
| 2020 | −36.2 [−83.4, +17.4] | −35.1 [−82.9, +18.6] |
| 2022 | −5.2 [−11.1, −0.9] | −4.8 [−11.0, −0.3] |
| Windows positive | 2 of 4 (IM t −0.56, p 0.69) | 1 of 4 (IM t −0.71, p 0.74) |
| Pooled, quarterly EWC | +0.8, t −0.11 (ν 3), p 0.54 | −1.2, t −0.42 (ν 3), p 0.65 |

Without 2008: 1 of 3 on both bases. At `δ = 10%` and `δ = 30%`: 1 of 4 on both bases. The Brier gains have the same signs.

### S2: `pmi` as a level or with the cyclical class. Fail.
| Window | Level | Level + `pmi × cyclical` |
|---|---|---|
| 2008 | +0.6 [+0.2, +1.0] | +10.2 [+5.4, +16.4] |
| 2015 | −1.1 [−2.8, +0.9] | −1.9 [−5.0, +1.2] |
| 2020 | +13.1 [+0.1, +23.9] | +13.6 [+0.5, +22.1] |
| 2022 | −2.8 [−6.7, +0.6] | −3.0 [−7.8, +0.1] |
| Windows positive | 2 of 4 (IM p 0.27) | 2 of 4 (IM p 0.17) |

Macro base shown. The macro + leverage base gives the same counts. The cyclical form has a pooled gain of +4.3 [+0.7, +8.2], but the quarterly EWC test gives p 0.10. Without 2008, its pooled interval holds zero (+1.2 [−2.7, +5.9]). The gain rests on the two recession windows.

### S3: the F6 votes. All fail.
Difference in the share of `D = 1`, flag on minus flag off, in percentage points:

| Vote | 2008 | 2015 | 2020 | 2022 | Positive | IM p | All rows pooled |
|---|---|---|---|---|---|---|---|
| `hy_oas` | +17.5 | −2.5 | +20.6 | −2.7 | 2 of 4 | 0.14 | +6.5 [+0.6, +13.1] |
| `distress_ratio` | +19.1 | −0.8 | −13.8 | −7.5 | 1 of 4 | 0.54 | +10.8 [+6.7, +14.9] |
| `sloos_tightening` | none | −6.8 | −20.5 | +1.1 | 1 of 3 | 0.85 | +4.7 [−0.3, +9.6] |
| `pmi` (GAC < 0) | +13.3 | −2.4 | +16.3 | −0.3 | 2 of 4 | 0.13 | +7.3 [+3.0, +11.9] |
| Majority of the four | +16.8 | −3.3 | +16.3 | −0.9 | 2 of 4 | 0.14 | +13.4 [+7.5, +19.0] |
| `phase_vote` late | none | −9.5 | −13.8 | −7.5 | 0 of 3 | 0.98 | +6.1 [+2.7, +9.6] |

"None" means that the flag was on for every row in the window. `sloos_tightening` was on through all of 2008–2009. In 2020 and 2022, `distress_ratio` and the phase flag were off for only 14 and 20 rows. Those differences rest on very few rows.

Votes not built:
- `default_rate_fcst` and `default_rate_ttm`: no point-in-time default forecast history exists in the data.
- Issuance quality: no CCC share or cov-lite share history of new issues exists in the data.

### S4: without 2020
| Exclusion | Rows | S1 macro base | S1 macro + leverage | S3 |
|---|---|---|---|---|
| `t` in 2020 | 16,164 | 2 of 3 (2008 +2.9, 2015 +14.2, 2022 −9.2 [−19.9, −2.6]); IM p 0.37 | 1 of 3 | every vote 1 of 3 or less |
| `t` to `t+4` touches 2020 | 15,399 | 2 of 3 (2022 −4.1 [−10.4, +1.4]); IM p 0.26 | 1 of 3 | every vote 1 of 3 or less |

`sloos_tightening` passes the 2-of-3 count on the macro base only. The 2008 gain has an interval that holds zero. The 2022 gain is negative. The IM test does not reject. This is not evidence that the break is a 2020 artefact. The only clear positive window is 2015.

### Attrition variant "exits"
The exit rule changes 13 issuer-quarters in the universe (1 in a test window) and 68 Compustat training rows. All S1 to S3 counts stay the same. The largest move of a gain is 1.5 (S1, 2020, macro + leverage base: −35.1 to −36.6). The rule catches few exits. Only 75 of the 3,163 panel issuers have a deletion code of 02 or 03. Most issuers that left the file carry code 01 (acquisition, 839) or 10 (no SEC filings, 321). So the "exclude" sample still drops most defaults. The event rate is therefore biased down, most of all in 2008 and 2020.

### Limits
1. The per-window EWC tests have `ν = 1`, because each window holds 5 to 9 quarters. A t distribution with one degree of freedom has no power. Only the pooled EWC tests (`ν` = 2 or 3) carry weight.
2. Four windows give the IM test three degrees of freedom. A fair coin passes the 3-of-4 count 31% of the time.
3. `δ` is fixed, not the issuer's own `δ_i`.
4. The 2008 window trains on Compustat's current view and uses the Baa spread for `hy_oas`.
5. The trailing medians of the `hy_oas` and `distress_ratio` votes use only months from January 2008, so the 2008 flags compare the level with a short history.
6. The PMI is a proxy (GAC), with the vote threshold at 0.
7. The OOS-above-IS flag of the protocol fires in 2008 and 2015 for S1, and in 2008 and 2020 for S2. Each training set averages calm and stressed quarters. A crisis window then shows a larger gain than the in-sample mean. No look-ahead explains these cases. `assert_rows_pit` and the window split tests pass.
8. The EWC formula follows the paper's abstract (`ν = 0.4 T^{2/3}`, `t_ν` critical values) and the standard type II cosine basis. Every online copy of the full text refused access (HTTP 403), so the cosine normalisation is not checked against the paper text. A unit test checks the size on white noise (5% nominal, 3% to 7% observed bound).

### What we decide
1. `sloos_tightening` leaves `m_t`. S1 fails on both bases and at all three `δ`. The S4 pass is too weak to justify a pandemic-exclusion rule. This page records it and opens no new page for it.
2. `pmi` stays out of `m_t`, as 5.2.1 proposes. The cyclical form helps in the two recession windows only. It stays a candidate for T3 of 5.2.1, and it needs a fresh hold-out before any use.
3. All four buildable F6 votes fail the rule of this page, so the rule removes them. That leaves the F6 phase vote with no tested vote. A new decision page must choose what sets the phase prior. One option is the fitted 5.2 logistic, which F6 already names. The pooled differences favour the votes (majority +13.4 points). But the rule was set before the test, and this page does not change it after the result.
4. Before any of this enters code, the 5.2 model itself needs review. The full `m_t` does not beat the sector-only model after 2009. A change to `hy/macro.py` or `m_t` gets a test that fails on the old behaviour, as this page requires. This branch changes no model code.
5. Fix `leverage_as_of`: require consecutive quarters. Rebuild `leverage_full`. Write a test with a missing fiscal Q4.

The decision closes with this section.
