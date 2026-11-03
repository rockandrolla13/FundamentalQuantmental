# TRACE master version rule

Sections touched: 3.1, 11. Code: `hy/sources/trace_bonds.py` (`master_in_force`, `master_in_force_sql`, `current_version`), `hy/sources/trace_panel.py` rule 1.

## Context

The monthly panel and the HY benchmark select bonds by the TRACE master grade, 'H' for high yield. TRACE keeps one row per CUSIP and version. A correction often starts one day after the first version, but TRACE leaves the first version open. The old rule took the version with the latest `enddt`. That rule picked the stale first version.

Example: Apple 037833AJ9 reads grade H from 2013-04-30 to 2018-06-21. It reads grade I from 2013-05-01 to 2018-05-07. The old rule read Apple as high yield for five years.

## What the data says

The factor test track measured the effect on traded panel rows with an S&P rating:

| Month | Old rule, share IG | New rule, share IG |
|---|---|---|
| June 2015 | 39.4% | 14.4% |
| June 2016 | 42.3% | 14.6% |

Recall of S&P high yield bonds stays the same: 94.2% against 93.0% in 2015.

On the full master file, the new rule in June 2015 does two things:

- It moves 1,197 bonds from grade H to grade I.
- It drops 285 bonds whose only open version was a stale parent.

The rest of the 14% are mostly split ratings, where agencies disagree on the grade. A small part are unrated bank structured notes, about 36 of 8,000 rows a month. We accept both.

## Options

1. Latest `enddt` (old rule). It is wrong when a stale parent stays open.
2. Latest `stdt` among versions open in the window. It is right in most cases. It lets a stale parent come back after its correction ends.
3. End each version on the day before its successor starts, then take the latest `stdt`. Use only versions with `stdt` on or before the decision date.

## Choice

Option 3. A correction replaces its parent from the day it starts. Option 3 states that directly, and it never uses a version that started after the decision date.

## Test that settles it

`tests/test_master_version_rule.py` runs the WRDS SQL text on DuckDB and the Python rule on the Apple case. Both must read Apple as I in June 2015. Both must drop Apple in May 2018.

## Effect on cached data

The rule tag `MASTER_RULE` is part of each cache key. Months pulled under the old rule stay on disk but are not read. Rebuild the panel on the production machine before you trust any panel result made before 2026-11-03.
