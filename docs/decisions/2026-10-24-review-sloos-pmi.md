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
