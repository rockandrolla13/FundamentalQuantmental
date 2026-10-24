# Decision: test signal S7, the macro-conditional sector tilt, on bond returns

Date: 2026-10-24. Sections touched: methodology Section 8 (S7), Section 5.2. Code: `scripts/s7_sector_tilt.py`.

## Context

The Wolfe Trahan study and tests S1-S4 asked whether macro data predicts EBITDA and leverage. The answer is no, beyond
the sector. That result does not settle alpha. Alpha needs a different question: does the market price macro news
late? A macro series can fail on EBITDA and still predict spreads. It can also predict EBITDA and be priced already.
S7 is the signal in the methodology that asks the spread question directly.

## Options

1. Test S7 as written, with the downside-weight term.
2. Test S7 with theta = 0. The downside weights come from the Section 5.2 model, which failed S1-S4.
3. Skip S7 and drop the macro layer.

## Choice

Option 2. Option 3 drops a layer before the spread test runs. Option 1 builds on a failed model.

## Frozen specification

- Unit: GICS sector x month end, TRACE HY panel 2008-2026, horizons 3 and 6 months.
- Signal: S7 = eta - eta_hat. eta is the sector's median log G-spread minus the cross-sector mean. eta_hat is an
  expanding ridge fit of eta on the macro vector (Baa level and 3-month change, SLOOS, Philadelphia Fed activity,
  oil, copper and CPI year-on-year, 10y minus 3m curve), at least 36 months of history.
- Outcome: sector mean credit excess return (total minus Treasury) minus the cross-sector mean.
- Pass, all three:
  1. P1: the Fama-MacBeth slope on -eta_hat, with eta in the same regression, is above 0 with an EWC t above 2.
  2. P2: the mean rank IC of S7 is above that of eta alone.
  3. P3: the top-minus-bottom tercile return after costs on both legs is positive in every testable cycle window.

## The test that settles it

The script output `data/raw/backtest/s7_sector_tilt.json`. If S7 fails, the macro layer leaves the fair spread and
the case weights. Gatto's judgement weights (p. 311) and the peer fair spread stay.

## Results

Pending the first run.
