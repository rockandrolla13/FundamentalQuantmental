# E2 fair-line convergence takes the lowest active weight

Date: 23 October 2026. Code: `hy/groups.py` (`ESTIMATES["E2"]`). Test: `tests/test_four_groups.py::test_fair_line_has_the_lowest_active_weight`.

## Context
The user decided that the fair line should carry the lowest score weight. The panel backtest supports this (decision page `2026-10-22-alpha-backtest-design`). The fair line ranks bonds no better than the widest spread: IC 0.25 against 0.29 at 6 months. Its Mincer-Zarnowitz slope is 0.07, so it sizes its edge far too large.

## Choice
E2's v0 weight inside the G2 bucket falls from 0.10 to 0.02. The G2 bucket keeps its 18%. E2's effective weight falls from 3.0% to 0.69%, the lowest of the estimates in use. E4 stays suspended at 0. E0, E1, E3 and E6 take the freed weight in proportion: E0 8.65%, E1 5.19%, E3 and E6 1.73% each.

## Limit
E2 is not the only route of the fair line into the score. E1 (cases) and E10 (excess over cash, step 15) both use `fair_s5` as the convergence target. So the fair line still reaches the score through E1 and E10, at 15.19% together. A redesign of the fair line itself, not only its weight, removes that route.

## Test that settles it
Rerun the walk-forward with the new weights. The rank IC of the combined alpha should not fall. If the fair line is replaced (sector peers and the HY index), rerun the panel backtest on the new fair spread and compare it with the widest spread.
