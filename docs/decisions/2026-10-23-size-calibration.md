# Size calibration: a point-in-time map from predicted to realised return

Date: 23 October 2026. Code: `hy/calibration.py`, `hy/groups.py` (`size_map`, `sized_alpha`, `combine`), `scripts/calibrate_sizes.py`. Tests: `tests/test_calibration.py`. Methodology: Section 7.5, "Size calibration". Spec: S14b.

## Context
The analyst ranks bonds well. Its predicted sizes are wrong.
1. The Mincer-Zarnowitz (MZ) slope of realised on predicted return is 0.07 for the old fair line. It is -0.10 to +0.13 for the peer line, with distressed bonds out and a cost of 15 bp.
2. The largest predicted gaps come from the bonds where the method fails. A bond at a price of 42 was forecast at +1,624 bp and realised -2,283 bp.
3. The process applies one fixed v0 slope, 0.08, to every bond. That slope came from the full 2008 to 2026 sample, so it is not point in time.

The memo's expected returns therefore cannot size positions. The user asked for one command that refits the sizes from realised returns on any data source.

## Options
1. Keep the fixed v0 slope (a = 0, b = 0.08).
2. Pooled linear MZ map, refitted each month on finished outcomes, slope shrunk toward 0 (`linear`).
3. One linear map per spread band (<400, 400 to 700, 700 to 1,000 bp), slopes partially pooled toward the pooled slope (`bucket`).
4. Monotone map by decile of the forecast, fitted with PAVA (`isotonic`).
5. The linear map without shrinkage (`unshrunk`). This is a comparator only, to test the shrinkage rule.

## Choice
1. Fit every map in an expanding window. A fit at decision time T uses only rows whose outcome finished by T: formation month end + h months + 1 day. A test with a planted slope of 5 in the last 12 months fails if the window reads one unfinished row.
2. Shrink the slope with a positive-part James-Stein rule: b_s = max(0, b) x max(0, 1 - (2 se / b)^2). At t = 2 the slope is 0, which is the S14b "rank only" rule. With fewer than 24 finished months the slope is 0.
3. Choose the map out of sample. Take `linear` unless a richer map lowers the squared error with a Diebold-Mariano t above 2.
4. `hy.groups.combine` sizes with the latest chosen map of the carry-kept peer forecast at 6 months, available before the decision time. Without a decision time or a file, it uses the v0 slope.
5. Keep the S14b rule. When the raw slope is not above 0 by two standard errors, the memo ranks by the raw number and sizes at the minimum.

## What the data says (run of 23 October 2026)
Sample: TRACE high yield panel, formation months 2008-01 to 2026-07, distressed bonds out, 15 bp of price per round trip. The first map is fitted after 24 finished months. Out-of-sample scoring therefore starts in 2010 (2010-03 at 3 months, 2010-12 at 12 months). The 2008 stress window cannot be scored. Output: `data/raw/calibration/size_calibration_eval.json`.

The forecast that `hy.groups` uses (carry-kept peer forecast, `peer_carry_net`):

| Measure, out of sample | 3 months | 6 months | 12 months |
| --- | --- | --- | --- |
| MZ slope, raw forecast | +0.09 (se 0.05) | +0.08 (se 0.05) | +0.07 (se 0.06) |
| MZ slope, chosen map (`linear`) | +0.20 (se 0.39) | +0.43 (se 0.24) | +0.51 (se 0.27) |
| MZ slope, `isotonic` | +0.38 (se 0.31) | +0.37 (se 0.21) | +0.31 (se 0.23) |
| Squared error x 1e4: raw, `linear`, `isotonic` | 24.2, 17.8, 17.7 | 58.4, 37.9, 37.9 | 142.0, 87.6, 88.0 |
| Rank IC: raw, `isotonic` | +0.21, +0.20 | +0.26, +0.22 | +0.30, +0.25 |
| Monthly fits with a slope that sizes (b_s > 0) | 26 of 197 | 1 of 194 | 0 of 188 |
| Last fit (2026-08-01): raw slope, shrunk slope | +0.088 (se 0.042), 0.007 | +0.076 (se 0.046), 0 | +0.069 (se 0.057), 0 |

Other forecasts:
1. Old fair line (`fair_line_net`): `isotonic` beats `linear` (Diebold-Mariano t +3.1 at 3 months, +2.3 at 6 months). Its MZ slope rises from +0.006 raw to +0.58 at 3 months and from +0.005 to +0.53 at 6 months. The rank IC stays near the raw IC: +0.20 against +0.22, and +0.19 against +0.27.
2. Spread-move peer forecast (`peer_line_net`): the raw slope is negative at every horizon (-0.03, -0.06, -0.11). Every map flattens it to a constant. It never sizes.
3. Shrinkage: the unshrunk line has a larger squared error than the shrunk line at 6 and 12 months (38.0 against 37.9, and 88.5 against 87.6). It ties at 3 months. The shrinkage rule holds.

By stress window (MZ slope of the `isotonic` map on `peer_carry_net` at 6 months; pooled): 2015 -2.47, 2020 +3.03, 2022 -0.93. The raw forecast: +0.07, +0.32, -0.10. The sign of the size is not stable across cycles. In 2022 the forecast was wrong-signed at every horizon below 12 months.

What we decide:
1. Use `linear` with shrinkage for the memo. Out of sample it ties `isotonic`, and it is simpler.
2. On today's data the map gives b_s = 0 at 6 months. Every bond's sized return is the intercept: -108 bp a year after cost against the HY index with beta 1. The sized return carries no information about one bond against another. The memo ranks by raw alpha and sizes at the minimum (S14b), now on a point-in-time basis.
3. Calibration cuts the squared error by 25 to 40% against the raw forecast. Almost all of that cut comes from shrinking the forecast toward its mean, not from a better slope.
4. The v0 slope (0.08) gives a squared error close to the fitted maps. It was fitted on the whole sample, so that result is not out of sample. Retire it as the default once a calibration file exists.

## Typical bond
A bond with a raw carry-kept forecast of +300 bp a year after cost:
1. v0: +24 bp a year.
2. Chosen map, last fit: -108 bp a year, the same as every other bond. Use: "rank only, minimum size".
3. `isotonic` (shown, not used): +300 bp a year is +150 bp over 6 months. That falls in the decile from +34 to +157 bp, which earned -24 bp over 6 months. The top decile earned -4 bp, and the bottom decile earned -152 bp. The realised gap from the bottom to the top decile is about 300 bp a year. The raw forecast spans about 2,200 bp a year between its 10th and 90th percentile cut points.

## Limits
1. The method choice uses the whole out-of-sample record. A replay of 2015 reads the 2015 fit of the chosen map, but the choice of map uses later data.
2. The panel has no default-loss term (Section 7.5), so the realised returns of bonds that default enter only through price.
3. The intercept is the mean realised return of non-distressed bonds against the index with beta 1. It is common to every bond, so it does not change the rank. It does make the sized return negative for every bond.
4. The cost is a flat 15 bp. A cost that rises with spread would lower the wide-bond outcomes.

## Test that settles it
Rerun `scripts/calibrate_sizes.py` on the new data source. Reject the calibration, and return to the v0 slope with "rank only", if any of these holds:
1. The chosen map does not lower the out-of-sample squared error against the raw forecast.
2. The unshrunk line beats the shrunk line with a Diebold-Mariano t above 2. This means that the shrinkage is too strict.
3. A slope that sizes (`use = "size"`) appears, but the cross-sectional MZ slope of the calibrated forecast is outside 0.7 to 1.3, or is negative in two or more of the four stress windows.

Size positions from the calibrated return only when the last fit says `use = "size"` and test 3 passes.
