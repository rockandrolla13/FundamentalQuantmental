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
