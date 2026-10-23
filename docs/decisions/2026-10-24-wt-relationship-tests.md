# Test the Wolfe Trahan relationships before any of them enters the macro layer

Date: 24 October 2026. Status: proposed, no code yet. Data: `research/wolfe-trahan-2011-relationships.csv`. Card: `research/cards/wolfe-trahan-2011-macro-relationships.md`. Sections: methodology 3.6, 5.2; framework F6 (phase vote). Code that a survivor changes: `hy/macro.py` (`phase_vote`, the PMI map `50 + 4 zG`, `estimate_rho`).

## Context
The sheet holds 156 rows from 25 notes of 2011. Each row is a chart: series 1, shifted forward by n months ("Advanced nM") and sometimes flipped in sign ("Inverted"), laid over series 2. A chart is not a test. Five problems make a chart overlay unreliable:
1. Both series are year-on-year changes or diffusion indexes. Both are persistent, so two unrelated series show large cross-correlations at many lags (Haugh 1976; Ferson, Sarkissian, Simin 2003).
2. The analyst picked the lead (6M, 9M) by eye. That is a search over lags, and the chart shows only the winner.
3. Overlapping year-on-year changes inflate the apparent fit. Standard errors that ignore the overlap overstate the evidence (Boudoukh, Richardson, Whitelaw 2008).
4. The charts use today's data, not the data an investor had on the date. CPI and payrolls are revised (Croushore and Stark 2001).
5. Leading-indicator relationships are unstable. Most published predictors of output and inflation work in one period and fail in the next (Stock and Watson 2003). In-sample fit does not imply out-of-sample skill (Rossi 2013; Goyal and Welch 2008).

The project already uses `pmi` as one of the six votes of the F6 phase classifier. Several rows claim that prices paid and CPI lead the ISM index by six to nine months. If that claim survives, the phase vote can move six months earlier. That is the main prize.

## What the sources say, what the data says, what we decide

| Question | Wolfe Trahan (2011) | Literature | Status |
|---|---|---|---|
| Does inflation lead the business cycle? | Yes. CPI and prices paid, inverted, lead ISM by about 6 months (rows 82, 153) | Asset-price and inflation leads are unstable across periods (Stock and Watson 2003) | Untested on our data |
| Do spreads follow or lead activity? | ISM leads Baa spreads (row 90) | Credit spreads lead activity, in real time (Gilchrist and Zakrajšek 2012; Faust, Gilchrist, Wright, Zakrajšek 2013) | Conflict. Test both directions |
| Is rising inflation bad for credit? | Yes, through weaker leading indicators 6 months later | Credit excess returns have a positive inflation beta, larger for riskier bonds, 2004–2022 (Lu, Nozawa, Song 2025) | Both can hold at different horizons. Test the sign at h = 0 and at h = 6M |
| Does sector rotation by cycle pay? | Yes. Early vs late cyclicals follow CPI (rows 73, 96) | The gain is small even with perfect cycle timing, and it vanishes after costs (Stangl, Jacobsen, Visaltanachoti 2009; Molchanov and Stangl 2023). Cyclical industries have a negative relation to expected inflation (Boudoukh, Richardson, Whitelaw 1994) | Use sector effects for scenario weights only, not as a trade |
| Which yield curve? | The real curve (10Y minus CPI) beats 10Y minus Fed funds at the zero bound (row 112) | A near-term forward spread beats the long-term spreads (Engstrom and Sharpe 2019) | Race the three curves |

## Options
1. Use the rows as stated. Rejected: problems 1 to 5 above.
2. Fit every row at every lag and keep the best. Rejected: this repeats the search that made the charts.
3. Pre-register a short list. Fix sign, lead, and transform from the 2011 note. Test on point-in-time data. Treat everything after November 2011 as a true holdout. **Chosen.**

The note dates give a clean holdout. The analyst could not see data after the note date, so a test on December 2011 onward is out of sample by construction. No lag search is allowed, so no multiple-lag correction is needed for the main test.

## Choice: eight hypotheses, one protocol

Triage first. Most of the 156 rows fall outside the scope of an HY analyst:
- Equity-only relative value, for example semiconductors vs the S&P or wireless vs telecom. These are out of scope.
- Data-source lists, such as the 12 freight series. These are candidate sector drivers, not hypotheses.
- Narrative rows, for example "Do corporate profits still generate jobs?". These cannot be tested.

The eight hypotheses below map to an HY use. Row numbers are the rows of the sheet tab "WT Relationships" (row 1 is the header).

| ID | Rows | Hypothesis (sign, lead) | Target | Use if it passes |
|---|---|---|---|---|
| H1 | 38, 54, 153 | Survey prices paid, inverted, leads the survey activity index by 6M | `pmi` | Forward PMI vote in F6 |
| H2 | 81, 82 | CPI YoY, inverted, leads the ISM by 6M | `pmi` | Replace the PMI map `50 + 4 zG` in `hy/macro.py` |
| H3 | 90, 89 | ISM leads Baa and HY spreads, inverted. Reverse: spreads lead ISM | `hy_oas` change over 3M and 6M | Settles the direction. A spread lead strengthens the `hy_oas` vote |
| H4 | 112, 110 | The real curve (10Y minus CPI), advanced 6M, leads ISM. Race it against 10Y minus 3M and the near-term forward spread | `pmi`, `default_rate_ttm` 12M ahead | Add the winner to `m_t` |
| H5 | 49, 50 | Copper YoY and KOSPI YoY track the global PMI in real time | PMI release, nowcast error | Daily nowcast of `pmi` between releases |
| H6 | 73, 94, 96, 152 | Falling CPI leads early (consumer) over late (industrial, energy, materials) cyclicals | Sector OAS change; sector share of 4-quarter EBITDA declines | Sector term `θ_sector × ΔCPI` in the 5.2 logistic |
| H7 | 65, 133, 134 | Housing (NAHB, new home sales) leads housing-linked sectors | Homebuilder and building products OAS and EBITDA | `sector_drivers[]` for those sectors |
| H8 | 78, 52 | Oil up leads energy over consumer discretionary | Energy vs consumer OAS; EBITDA declines | `sector_drivers[]`; the 2015 cycle is the key window |

### Protocol for each hypothesis
1. **Fix the claim.** Write the sign, the lead `h`, and the transform from the note. Do not search over lags.
2. **Use point-in-time data.** Read every series as of its release date. Set `available_at` to the release date. Use ALFRED or Philadelphia Fed vintages for CPI. ISM data is licensed: FRED deleted all 22 ISM series in June 2016. Use the Philadelphia Fed Manufacturing Business Outlook Survey as the free survey. It runs from May 1968 and has activity, new orders, and prices paid diffusion indexes. Use ISM only under a license.
3. **Split the sample.** In-sample: up to the note date. This replicates the chart. Holdout: the month after the note date to the latest release. Report both. Only the holdout counts.
4. **Measure.** Report three statistics:
   - (a) The cross-correlation at lag `h` after a univariate ARMA filter of each series (Haugh 1976). This removes the spurious correlation of problem 1.
   - (b) A predictive regression of the target change from `t` to `t+h` on `x_t`, the target's own lags, and the current `m_t`. Use Newey–West standard errors with at least `h` lags for the overlap. Also report a non-overlapping version.
   - (c) An expanding-window forecast. Compare it with the benchmark: the own lags plus the current `m_t`. Report the out-of-sample R² and the Clark–West (2007) test for nested models.
5. **Check stability.** Report the sign and the Clark–West statistic in each cycle window: 2008, 2015, 2020, 2022. Run a Bai–Perron (2003) break test on the slope.
6. **Correct for eight tests.** Use the Holm correction at a 5% family-wise level. Any lag outside the pre-registered set is exploratory. Any such lag needs |t| > 3 (Harvey, Liu, Zhu 2016) and a new decision page.

### Pass rule
A hypothesis passes when all three hold:
1. The holdout sign matches the note.
2. The holdout Clark–West p-value passes Holm at 5%.
3. The sign holds in at least three of the four cycle windows.

The 2008 window is in-sample for the 2011 notes. So the holdout must also hold in at least two of 2015, 2020, and 2022.

### Second gate for HY use
A passing series enters `m_t` only if it improves the 5.2 logistic out of sample. The target is the 4-quarter EBITDA-decline event. The measure is the log loss and the Brier score, by sector, against the current `m_t` (`hy_oas`, `sloos_tightening`, `default_rate_fcst`, `pmi`). A macro series never becomes a bond-level signal. It is common to every bond in a sector, so it sets scenario weights and sector tilts only. Bond selection stays with the fundamentals.

## How to read the results
- **H1 or H2 passes.** The F6 PMI vote reads the expected PMI six months ahead, not the current PMI. The phase classifier turns earlier. Check that the earlier turn improves PD calibration by cycle phase.
- **H3 shows that spreads lead ISM.** This is the expected result under Gilchrist and Zakrajšek. Keep `hy_oas` as the lead and drop ISM-to-spread claims.
- **H6 to H8 pass.** Sector sensitivity enters the downside probability, not a sector rotation trade. The sector-rotation literature says that the trade loses after costs.
- **A hypothesis fails.** Record the failure in the card with the statistics. The row leaves the candidate list. A failure is a result.

## References to card before the tests run
Each source below needs a card in `research/cards/` before a test cites it. Status gives what was checked on 24 October 2026.

| Source | Role | Status |
|---|---|---|
| Trahan and Krantz (2011), *The Era of Uncertainty*, Wiley, 228 pp. | The published long form of the Wolfe Trahan framework | Catalogue record found; text not read |
| Stock and Watson (2003), JEL 41, 788–829 | Instability of leading indicators; the yield spread is the exception | Abstract read |
| Faust, Gilchrist, Wright, Zakrajšek (2013), REStat 95(5), 1501–1519 | Credit spreads lead activity in real time | Abstract read |
| Gilchrist and Zakrajšek (2012), AER 102(4), 1692–1720 | Already on the reading list | Cited in `forecast-ice-hy-oas.md`; no card of its own |
| Engstrom and Sharpe (2019), FAJ 75(4) | The near-term forward spread for H4 | Abstract read |
| Goyal and Welch (2008), RFS 21(4), 1455–1508 | Out-of-sample discipline | Abstract read |
| Clark and West (2007), J. Econometrics 138(1), 291–311 | The nested-model test | Abstract read |
| Ferson, Sarkissian, Simin (2003), JF 58, 1393–1413 | Spurious regression with persistent predictors | Abstract read |
| Boudoukh, Richardson, Whitelaw (2008), RFS 21(4), 1576–1605 | Overlapping-horizon artefacts | Abstract read |
| Haugh (1976), JASA | Prewhitened cross-correlation | Title confirmed; volume and pages not confirmed |
| Bai and Perron (2003), JAE 18(1), 1–22 | Break test | Abstract read |
| Rossi (2013), *Handbook of Economic Forecasting* 2, 1203–1324 | Forecasting under instability | Abstract read |
| Harvey, Liu, Zhu (2016), RFS 29(1), 5–68 | The t > 3 hurdle for exploratory lags | Abstract read |
| Croushore and Stark (2001), J. Econometrics 105, 111–130 | Real-time vintages | Abstract read |
| Boudoukh, Richardson, Whitelaw (1994), JF 49(5), 1595–1615 | Industry inflation sensitivity follows cyclicality | Abstract read |
| Stangl, Jacobsen, Visaltanachoti (2009); Molchanov and Stangl (2023), IJFE | Sector rotation fails after costs | Working paper via an unofficial copy; journal version abstract only |
| Lu, Nozawa, Song (2025), working paper | Positive inflation beta of credit excess returns | Abstract read from the AEA 2026 PDF |
| Asvanunt and Richardson (2017), JFI 26(3), 6–24 | The credit risk premium varies with growth and default rates | Abstract read |
| Jonsson and Fridson (1996), JFI; Helwege and Kleiman (1996), NY Fed *Current Issues* 2(6) | Macro and aging models of HY default rates | Seen through the NY Fed summary; Jonsson and Fridson not opened |
| Merrill Lynch, "The Investment Clock" (about 2004) | Practitioner growth × inflation quadrants | Not verified. Primary source not found. Do not cite until found |

## Test that settles it
Write `scripts/wt_tests.py`. It reads the point-in-time panel and runs the protocol for H1 to H8. It writes one table per hypothesis with the in-sample and holdout statistics and the pass flag. Write `tests/test_wt_tests.py` with four checks:
1. No series value enters with `available_at` after the decision date.
2. On two independent AR(1) series, the prewhitened cross-correlation stays inside its 95% band in about 95% of draws.
3. The Clark–West statistic is near zero when `x` adds nothing.
4. The lead `h` comes from the hypothesis table and the code cannot change it.

The decision closes when the table exists and this page records which hypotheses passed.
