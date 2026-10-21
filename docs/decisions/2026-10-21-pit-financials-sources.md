# Point-in-time issuer financials: sources, release times, and the gap fill

## Context
Section 3.2 needs quarterly financials with `available_at`. The WRDS account licenses Compustat point-in-time (`comp_pit`) but not WRDS SEC Analytics. A check on 2026-10-21 found four facts:
1. `comp_pit.pithistdataus` stores month-end snapshots. A value first seen at month end was public earlier.
2. It lacks about half of fiscal Q4 quarters (1,252 of 2,395 December quarters, 2018 to 2025), and the latest quarter for some issuers.
3. The current-view table holds latest values, not first-reported values (revenue matched the latest version in 100% of HCA and Ford quarters).
4. XBRL tags and Compustat items define cash, debt, and EBITDA differently.

## Options
1. Compustat snapshot dates only. This delays every quarter by a median of 27 days and leaves the Q4 gaps.
2. Fill the gaps from the current view. This adds look-ahead, because the values contain later restatements.
3. Compustat snapshots for values; EDGAR acceptance for the first-version release time; XBRL as first filed for the gaps, with a definition bridge.

## Choice
Option 3.
- `available_at` of a first version = earlier of the 10-Q or 10-K acceptance and the day after the first snapshot. Restatements take the snapshot date.
- Gap flows = YTD in the filing minus the shorter YTD as first filed before it. Gap balances = filing instants scaled by Compustat / XBRL in the prior quarter (ratio limited to 0.5 to 2).
- Gap EBITDA is not scaled, because the prior-quarter ratio carries that quarter's special items. It is kept only when the prior-quarter ratio lies in 0.8 to 1.25; otherwise it is NaN.
- Quarters that XBRL cannot fill keep the current-view row with `pit_exact = False`. The point-in-time store excludes them by default.

## Test
Offline: `tests/test_sources.py` and `tests/test_xbrl.py` (16 tests).
Live, HCA and Ford, 2015 to 2026 (108 quarters): EDGAR matched every quarter. XBRL rebuilds agree with Compustat within 1% for revenue, capex, operating cash flow, and bridged long-term debt in all 9 rebuilt quarters. Two quarters stay flagged, because the SEC XBRL feed did not yet hold the June 2026 10-Q.

Known limit: rebuilt Q4 EBITDA includes special items. HCA Q4 2016 is 14% above Compustat for this reason. Open test: compare rebuilt Q4 EBITDA with Compustat across the universe, and widen or narrow the check range.
