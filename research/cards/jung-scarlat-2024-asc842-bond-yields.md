# Jung and Scarlat (2024), "The effect of ASC 842 leases on bond yields"

Finance Research Letters 67, 105944. DOI 10.1016/j.frl.2024.105944. The user supplied the PDF. We read the whole paper. The Online Appendix is not in our file.

## Claim
Bond yields rise when the first ASC 842 report shows more lease liability than the footnote implied. They do not fall when it shows less (p. 1).

## Method
Bond-day panel, 3 days before and after the 2019Q1 earnings date, with bond fixed effects and bond clusters (eq. 1, p. 3). `GAP` is the reported liability less a present value of the prior schedule at the firm's bond yield, over assets (Appendix).

## Data
206 December year-end firms, 6,403 bond-days. No financials or utilities. Mean yield 3.963% (Table 1).

## Result
- GAP x Post 0.297 (t 3.16), and 0.367 (t 3.91) with controls (Table 2).
- Undervalued x Post 0.594 (t 4.41). Overvalued x Post -0.070 (t -0.53) (Table 3).
- GAP in a downgrade probit: 10.875 (t 4.09) (Table 4).

## Limits
- One event, one quarter. It cannot repeat as a signal.
- No HY split. The mean yield suggests a mostly investment grade sample (our reading).
- Scale, by our arithmetic: 1% of assets as undervalued lease is about 0.6 bp.
- The authors warn of low power on the overvalued side (p. 4, footnote 5).
- The text reads the probit coefficient as a percent change. We do not use that reading.
- Table 1 prints `Size` with mean 0.435, and the Appendix defines it as log assets. Unresolved.

## Section touched
`docs/methodology.md` Section 4.7.1, M1.7. `hy/clocks.py` `lease_gap`.

## Use for the two clocks
**Source says:** the footnote did not fully show the liability, and bonds moved at the first report. **Data says:** nothing yet. **We decide:** add M1.7b to read the 3-day window on HY and the two parts apart, with `mde` first because the size is small.
