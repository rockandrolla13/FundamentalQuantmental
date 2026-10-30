---
name: hy-macro
description: "Method for a macro read on US high yield at one decision time: cycle phase, late-cycle votes, path probabilities, F6 case weights, and the phase playbook. Use when the user asks what phase the credit cycle is in, asks for a macro read, or edits methodology Sections 3.6, 5.2, 5.4, 9.2, or framework F6. Not for general macro views, other regions, or asset allocation (see the global macro-analysis skill)."
---

# HY Macro Read

This skill is a method. The analyst supplies the inputs. The method turns them into one macro read at one decision time.

The output is the read in Step 8. Each request produces one of two things:

- **Inputs supplied:** run Steps 1 to 8 on those inputs.
- **No inputs supplied:** return the blank input sheet below, then stop.

If a request also asks for a data pull, a backfill, or a backtest, list that request under `Out of scope` in the read. Backtests of the phase layer belong to tests T1 to T8 of `docs/decisions/2026-10-26-conviction-book.md`.

**Authority.** `docs/framework.md` F6, `docs/methodology.md` Sections 3.6 and 5.4, and `hy/macro.py` own these rules. Steps 2 to 4 copy them for ease of use. If a copy differs from its source, follow the source and report the difference. F6 says "majority vote". Steps 3 and 4 use the count map of `hy.macro.phase_vote`.

**Status of the method.** Nothing here has a tested return. The read describes conditions. It does not feed the composite, and it sets no position size.

## Input sheet

Every row carries `as_of`, `available_at`, and `source`. The last column shows which inputs are optional. A blank required row is `not_available`. `ccc_median` and `covlite_median` are trailing medians of the prior year (F6).

| Input | Fields | Required |
| --- | --- | --- |
| `decision_time` | Date | Yes |
| `hy_oas` | `level`, `median_5y`, `change_3m` | Yes |
| `distress_ratio` | `level`, `median_5y` | Yes |
| `sloos_tightening` | Net tightening of the last two quarters | Yes |
| `pmi` | `level` | Yes |
| `default_rate` | `fcst`, `ttm` | Yes |
| `issuance_quality` | `ccc_share`, `ccc_median`, `covlite_share`, `covlite_median` | Yes |
| `prior_phase`, `prior_count` | Phase and count `n` of the last read | Optional |
| `path_mass` | Five masses from the Section 5.4 registry, with vintage | Optional |
| `prior_posterior` | Path posterior of the last read | Optional |

## Where each input comes from

Derive each input as this table states. Use the first source that you can read. Use one source for all fields of a row, and name that source in the read. If no listed source is available, the row is `not_available`.

| Input | Source, in order | Derivation | `available_at` | Status in this repo |
| --- | --- | --- | --- | --- |
| `hy_oas` | 1. ICE BofA US High Yield Index OAS (H0A0), licensed. 2. `trace_hy_benchmark`, `load_trace_hy` | `level`: value at the last trade date before `decision_time`. `median_5y`: median of the series over the prior five years. `change_3m`: `level` minus the value three months earlier | Last trade date + 1 day | Source 1 is a stub. Source 2 works with WRDS or its cache. It is a median G-spread, not an OAS (`hy.state.hy_index_level`) |
| `distress_ratio` | 1. Share of ICE index par above 1,000 bp, licensed. 2. `trace_hy_benchmark`, `load_trace_hy` | `level`: share of bonds with a spread above 1,000 bp. `median_5y`: as for `hy_oas` | Last trade date + 1 day | Source 1 is a stub. Source 2 works with WRDS or its cache (`hy.state.distress_ratio`) |
| `sloos_tightening` | Fed SLOOS, series `SUBLPDCILS_N.Q`, `load_sloos` | Net share of domestic banks that tighten C&I standards for large and middle-market firms. Take the last two surveys released | Release date + 1 day (`sloos_timing`) | Works. Public |
| `pmi` | 1. ISM Manufacturing PMI, licensed. 2. Philadelphia Fed Manufacturing Business Outlook Survey, column `GAC` | `level`: latest monthly value released | Release date + 1 day | No loader. `scripts/wt_tests.py` reads source 2 from `data/raw/macro/bos_dif.csv`. Git ignores that path |
| `default_rate` | Moody's Default Report, then S&P default outlook, both licensed | `fcst`: baseline forecast of the US speculative-grade default rate, 12 months ahead. `ttm`: the trailing twelve-month rate from the same report | Report release date + 1 day | Stub (`load_agency_default_forecasts`). Blank until you supply the report figures |
| `issuance_quality` | New-issue statistics of a vendor that you name. The repo names none | `ccc_share`: CCC share of new high yield bond par. `covlite_share`: cov-lite share of new leveraged loans. Compare the latest quarter with the median of the four quarters before it | Vendor release date + 1 day | No loader and no source. Blank until you name a vendor |
| `prior_phase`, `prior_count` | Your last read | Copy `phase` and `n` from that read | Date of that read | Nothing saves them. Keep each read |
| `path_mass` | `hy.macro.build_paths(...).mass` | The forecast registry supplies the GDP and CPI quantiles (`spf`, `spf_prob`) | Latest `available_at` of the rows used | Works when the registry has rows |
| `prior_posterior` | Your last read | Copy the posterior column | Date of that read | Nothing saves it. Keep each read |

Three limits apply to these sources:

- `scripts/scenarios.py` approximates `median_5y` with one snapshot per year. The table states the full rule. Report which form you use.
- A TRACE G-spread is wider than an OAS for a callable bond. Compare a level only with a median from the same source.
- These rows have no decision page yet: the `GAC` proxy, the 12-month `fcst` horizon, and the `issuance_quality` window. Treat them as v0.

## Steps

Each step lists its input and its output.

**Step 1. Filter by date.** Input: the input sheet. Output: a status per row.
Mark a row `not_available` when its `available_at` is blank or after `decision_time` (framework R5). Keep its value in the read and record the reason.
If a row passes but has a blank `as_of` or `source`, use its vote and list the gap under `Inputs to close`. Treat a `path_mass` with no vintage the same way.

**Step 2. Vote.** Input: rows that pass Step 1. Output: one vote per indicator, `late`, `not_late`, or `not_available`.

| Indicator | Vote `late` when |
| --- | --- |
| `hy_oas` | `level > median_5y` and `change_3m > 0` |
| `distress_ratio` | `level > median_5y` |
| `sloos_tightening` | Both of the last two quarters are above 0. Fewer than two quarters vote `not_late` |
| `pmi` | `level < 50`. For the `GAC` proxy, `level < 0`, because that index has its neutral point at 0 |
| `default_rate` | `fcst > ttm` |
| `issuance_quality` | `ccc_share > ccc_median` and `covlite_share > covlite_median` |

**Step 3. Count.** Input: the votes. Output: `L`, `A`, `n`.
`L` is the number of `late` votes. `A` is the number of available votes. Then `n = L x 6 / A`.
If `A = 0`, then `n` is `not_available`. The phase is `prior_phase`, else `late_cycle`.

**Step 4. Map to a phase.** Input: `n`, `prior_phase`, `prior_count`. Output: `phase`.

1. Set `raw`: `expansion` when `n < 1.5`, `late_cycle` when `n < 3.5`, else `downturn`.
2. If `raw` is `downturn`, or `prior_phase` or `prior_count` is absent, then `phase = raw`.
3. If the prior is `downturn` or `repair` and `n < prior_count`: `phase` is `repair` when `raw` is `late_cycle`, else `recovery`.
4. If the prior is `repair`, `n = prior_count`, and `raw` is `late_cycle`, then `phase = repair`.
5. If the prior is `recovery` and `n < prior_count`, then `phase = recovery`.
6. Otherwise, `phase = raw`.

With no prior, this step cannot return `repair` or `recovery`. State this in the read.

**Step 5. Size the effect of missing votes.** Input: `L`, `A`, the prior. Output: `phase_low`, `phase_high`.
Run Step 4 twice, with `n = L` and with `n = L + (6 - A)`. These counts assume that every missing vote is `not_late`, then `late`. They use no scale to six. This step is our addition and is not in F6.

**Step 6. Path probabilities.** Input: `phase`, `path_mass`, `prior_posterior`. Output: prior, mass, and posterior per path.
Take the prior from the `phase` row of `hy.macro.PHASE_PRIOR`. Then `p(m) = prior(m) x mass(m)`, divided by the sum over all paths (Section 5.4).
If `path_mass` is absent, report `not_available`.
If `prior_posterior` is present, flag any path that moved by more than 0.10 (F6.10).

**Step 7. Look up what the phase implies.** Input: `phase`. Output: three lookups.

1. **Case weights:** copy the `phase` row of the F6 table in `docs/framework.md`.
2. **Playbook:** copy the `phase` row of layer 2 in `docs/decisions/2026-10-26-conviction-book.md`. Label it as an untested hypothesis.
3. **Band:** report the band levels from their decision page. If no decision page sets them, report `levels not set`.

**Step 8. Write the read.** Input: Steps 1 to 7. Output: the read, in this order.

```
# Macro read: <decision_time>

Phase: <phase>. Count: n = <n>, from <L> late of <A> available.
Range with missing votes: <phase_low> to <phase_high>.

| Indicator | Value | as_of | available_at | Source | Vote | Reason |

Paths: <prior, mass, and posterior table, or not_available>
Case weights: <F6 row>
Playbook (untested hypothesis): <layer 2 row>
Band: <levels, or levels not set>
Size: not set by this method.

Evidence limits:
- S7 failed: macro added nothing to the sector spread (2026-10-24-s7-sector-tilt).
- The sloos_tightening and pmi votes are under open review (2026-10-24-review-sloos-pmi).
- The G5 macro link has a weight of zero until its tests pass (Section 5.2.1).

Inputs to close: <each not_available row and its reason>
Out of scope: <requests outside this method, or none>
```

A request for a size gets the `Size` line as its answer.

Band moves follow the step rule of the conviction book: a phase change moves the band, and the book walks one step per rebalance. Quote this rule when the phase changes. Book actions come from that page and need its tests to pass first.

## Worked example

Decision time 2026-09-30. `hy_oas` has `available_at` 2026-10-01, so Step 1 removes it. `pmi` is 48.5, so it votes `late`. `sloos_tightening` is +5 and +8, so it votes `late`. The prior is `late_cycle`, count 2. The other three rows are blank.

- Step 3: `L = 2`, `A = 2`, `n = 6`.
- Step 4: `raw` is `downturn`, so `phase = downturn`.
- Step 5: `n = 2` gives `late_cycle`. `n = 6` gives `downturn`.
- Read: "Phase: downturn. Count: n = 6, from 2 late of 2 available. Range with missing votes: late_cycle to downturn."

The range tells the reader that two votes decide this phase.

## Common mistakes

| Mistake | Correct form |
| --- | --- |
| Row dated after the decision time enters the vote | Step 1 removes it and the read records why |
| Phase reported without `L` and `A` | The first line of the read carries both |
| Phase becomes a trade instruction | The read reports the band status, and `Size` stays not set |
| Playbook row reads as a result | Label it as an untested hypothesis |
