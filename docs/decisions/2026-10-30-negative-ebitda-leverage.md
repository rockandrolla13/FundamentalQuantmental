# Leverage when EBITDA is negative

Date: 30 October 2026. Code: `hy/state.py` (`_capped_lev`, `LEV_CAP`), `hy/books.py` (`kricheff_ratios`), `scripts/process.py`, `scripts/rv_pair.py`. Tests: `tests/test_state.py`. Methodology 4.3, framework F8.

## Context
Debt over negative EBITDA is a negative ratio. A negative ratio ranks below every healthy issuer. `hy/state.py` guarded only a zero denominator, so $1,000m of debt on EBITDA of −$50m gave −20x.

The E13 trap guard read that −20x as no high leverage sign. An issuer with +$50m EBITDA, free cash flow to debt of 3%, and TEV to debt of 1.2 was a trap. The same issuer with −$50m EBITDA was not.

The hard floor of the guard still fails an issuer with free cash flow at or below zero. So the miss needs negative EBITDA, positive free cash flow, and TEV above 1.25x debt.

`hy/quality/score.py`, `hy/sector/drivers.py`, `hy/sources/trace_panel.py`, and `hy/forward.py` already read EBITDA at or below zero as the worst case.

## Options
1. Return NaN. Rejected: the guard counts NaN as no sign, so the miss stays.
2. Return infinity, as `hy/quality/score.py` does for its ranks. Rejected here: a peer quantile over infinity can give NaN, and spread per turn becomes zero.
3. Return the panel cap of 20x. Chosen.

## Choice
- Denominator below zero: `LEV_CAP` when there is debt to carry, else 0.
- Denominator of zero: NaN, as before. The code uses a zero EBITDA for a missing one.
- Every ratio clips above at `LEV_CAP`. Without the clip, a thin positive EBITDA reads worse than a negative one.
- EBITDA plus rent is the denominator of the lease-adjusted ratios. Rent can lift a negative EBITDA above zero, and the ratio then stays a real number.
- `hy/forward.py` keeps its scenario cap of 50x, which has another purpose: finite scenario moments.

## What changes
- An issuer below 20x with positive EBITDA keeps its value. A true leverage above 20x now reads 20x.
- Spread per turn of a negative EBITDA issuer was NaN. It is now the spread over 20 turns, the rule that the peer panel already uses. This value is a ceiling on the true figure, and a low value never makes the bond look cheap.
- A maximum leverage covenant test now reads a negative EBITDA issuer at 20x, not at a negative number that passes.

## Known limit
Zero EBITDA stays NaN, and the guard counts it as no sign. `ev_to_ebitda` and `tev_to_ebitda` stay negative when EBITDA is negative. They are valuation multiples, and no rule reads them as leverage.

## Test that settles it
`tests/test_state.py::test_negative_ebitda_reads_as_the_cap_not_as_low_leverage` and `test_lev_cap_is_the_panel_cap`. Retake the golden snapshot at the next data run (`scripts/golden_check.py`).
