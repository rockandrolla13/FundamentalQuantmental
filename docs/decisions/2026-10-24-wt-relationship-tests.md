# Test whether the Wolfe Trahan series predict issuer EBITDA and leverage

Date: 24 October 2026. Rewritten the same day: the main test is now issuer EBITDA, not the PMI. Scope set the same day: a historical study first. Status: proposed, no code yet.
Data: `research/wolfe-trahan-2011-relationships.csv`. Card: `research/cards/wolfe-trahan-2011-macro-relationships.md`.
Sections: methodology 3.6, 5.2; framework F6.
Code that a survivor changes: `hy/forward.py` (`DEFAULT_DRIVER_LINKS`, `link_drivers`, `fit_sector_beta`, `fit_decline_model`) and `hy/macro.py` (`MacroPath.extra`).

## The question in one sentence
Did a change in each macro series, in the past, tell us that the companies in a sector would report lower (or higher) EBITDA, and so higher (or lower) leverage, six to twelve months later? It must have told us more than the series the model already uses.

## Scope: a historical study first
1. **Phase 1, now: a historical study.** For each claim, use history from about 1995 to 2026 and ask whether it worked, cycle by cycle. Use models M1 and M2 below on history, plus the event count below. Build no forward tooling.
2. **Phase 2, later: only for the claims that worked.** Wire them into the engine (the "How a result changes the model" section) and build the scenario tooling M3 to M6.

**Event count, the plain view.** For each claim, find the dates when the series gave a clear signal. Example: prices paid rose by more than one standard deviation over six months. Then count how often sector EBITDA, margin, and leverage moved as the claim says in the following two to four quarters. Compare that with all other dates. Report the result per cycle (2001, 2008, 2015, 2020, 2022). Example of the output: "After 9 signals, industrial margins fell in 7 cases. On other dates they fell 40% of the time."

**Data on hand (checked 24 October 2026).** WRDS access is configured (`~/.pgpass`), and `hy/sources/compustat_pit.py` reads the point-in-time quarterly table. FRED and the Philadelphia Fed survey page answer from this machine.

## Why this question
A macro series matters to a credit analyst only through the business of the borrower. The chain is:
1. The economy changes. For example, factory input prices rise.
2. Months later, the business feels it. Sales slow, or costs rise faster than prices, so EBITDA falls.
3. The credit metrics move. Leverage (debt / EBITDA) rises and interest cover falls.
4. Default risk rises, and the spread widens.

A series that moves at step 1 warns us before the company reports step 2. That warning is what we test. The 2011 notes tested only steps 1 and 4, or one macro series against another. They never tested step 2.

## What the model does today
The forward engine builds each case from drivers (framework F6, `Scenario` in `hy/forward.py`): revenue growth `g`, variable cost ratio `v`, SG&A ratio `a`, working capital days, and capex. The engine then rolls EBITDA, cash, debt, leverage, and covenants forward each quarter (`run_scenario`). Three facts about the macro link:
1. Only revenue growth listens to the macro path: `DEFAULT_DRIVER_LINKS = {"g": "gdp_growth"}`.
2. The link has no lag. One beta per sector ties revenue growth to GDP growth in the same quarter (`fit_sector_beta`).
3. Costs do not listen to the macro path at all. No driver links `v` to input prices.

The Wolfe Trahan series can fill both gaps. Demand series (new orders, housing, copper, KOSPI) can move revenue with a lag. Cost series (prices paid, oil, commodity prices, import prices) can move the cost ratio, which is the margin squeeze.

Leverage needs no model of its own. Once the drivers move, the engine computes EBITDA, cash flow, debt, and leverage. A direct test of leverage change serves only as a cross-check.

## What the sources say, what we decide
1. **The 2011 notes say:** inflation and prices paid lead the business cycle by six to nine months. They show charts only.
2. **The literature says:** leading-indicator relationships often break down from one period to the next (Stock and Watson 2003). Credit spreads lead activity, not the reverse (Gilchrist and Zakrajšek 2012). Firms short of cash raised prices in 2008 while other firms cut them (Gilchrist, Schoenle, Sim, Zakrajšek 2017). So highly leveraged issuers may pass a cost shock to customers more than other firms do.
3. **We decide:** test each claim on issuer financials, with the lead fixed from the note. Test separately for high-leverage firms, because of point 2.

## The eight claims to test
Row numbers are rows of the sheet tab "WT Relationships" and the `sheet_row` column of the CSV.

| ID | Rows | Claim, in plain words | What it should move | Sectors |
|---|---|---|---|---|
| H1 | 38, 54, 153 | Rising factory input prices squeeze margins at once and cut sales 6 to 9 months later | `v` within 0 to 2 quarters; `g` after 2 to 3 quarters | Industrials, materials, consumer |
| H2 | 73, 82, 96 | Rising consumer inflation hurts consumer companies and helps commodity producers about 6 months later | `g` and EBITDA margin | Consumer discretionary vs energy and materials |
| H3 | 52, 78 | Rising oil lifts energy EBITDA and squeezes fuel users | `g` for energy; `v` for transport and consumer | Energy, transport, consumer |
| H4 | 58, 133, 134 | Housing activity leads housing-linked companies by 6 to 12 months | `g` and EBITDA | Homebuilders, building products |
| H5 | 42, 49, 50 | Copper and the Korean stock market give a real-time read of global demand | `g` in the next 1 to 2 quarters | Materials, industrials |
| H6 | 2, 4 | Rising factory new orders lead sales and earnings of manufacturing-linked companies | `g` in the next 1 to 2 quarters | Industrials, materials, autos |
| H7 | 112 | The real yield curve (10-year yield minus CPI) warns of broad EBITDA declines a year ahead. Race it against the nominal curve and the near-term forward spread | Odds of a 4-quarter EBITDA decline | All |
| H8 | 90 | Control: the series already in the model (`hy_oas`, `sloos_tightening`, `default_rate_fcst`, `pmi`) predict EBITDA declines at all | Odds of a 4-quarter EBITDA decline | All |

H8 comes first. If the current macro inputs do not predict EBITDA declines, the baseline is wrong. In that case, fix the baseline before you add any new series.

## The models
Use them in this order. Each model fills one slot that the engine already has.

### M1. Driver response by quarter (local projections)
For each sector `s` and each quarter ahead `h = 1 … 8`, regress the change in a driver on the series:

```latex
x_{i,t+h} - x_{i,t} = a_{s,h} + b_{s,h}\, X_t + c_{s,h}' m_t + d_{s,h}\,(x_{i,t} - x_{i,t-4}) + e_{i,t+h}
```

`x` is revenue growth or the cost ratio of issuer `i`. `X_t` is the series as known at date `t`.
Intuition: one regression per horizon traces how the driver responds quarter by quarter (Jordà 2005). That is the exact shape of the 8-quarter driver arrays in `Scenario`.

- The output replaces the single beta of `fit_sector_beta` with a path `b_{s,1} … b_{s,8}`. `link_drivers` then shifts each quarter by its own beta.
- Add an interaction with a high-leverage flag. This tests whether HY issuers respond differently (Gilchrist et al. 2017).
- Shrink each sector's betas toward the all-sector average when the sector has few issuers. A sector with ten issuers should not get its own noisy beta.
- Standard errors: the series is the same for every issuer in a quarter. Errors must allow for correlation across issuers within a date and across nearby dates (Driscoll and Kraay 1998). Without this, the test overstates the evidence many times over.

### M2. Odds of a large EBITDA decline (logistic model, already built)
`fit_decline_model` already fits the probability that EBITDA falls by more than the issuer's moderate-downside amount within four quarters. Add `X_t` as a column of `m_t`. A series passes when the out-of-sample log loss and Brier score fall in at least three of the four cycle windows. This model sets the scenario weights (`scenario_weights`).

### M3. Depth of the bad case (quantile regression)
Today the severe downside is a fixed 1.5 times the moderate revenue decline (framework F6). Fit the 25th and 10th percentiles of the 4-quarter EBITDA change on `X_t` and `m_t`. Pool all issuers, with an issuer fixed effect.
Intuition: bad conditions move the bad tail far more than the middle. Financial conditions shift the lower quantiles of GDP growth while the upper ones stay put (Adrian, Boyarchenko, Giannone 2019). The Federal Reserve staff used the same tool to stress-test bank losses: Covas, Rump, Zakrajšek (2014) found that it forecast crisis losses better than a linear model. If the fit beats the fixed rule out of sample, the moderate and severe cases take their depth from the 25th and 10th percentiles.

### M4. Macro paths to feed in (scenario generators)
The models above say how a business responds to a macro path. These sources supply the paths:
1. **The five named paths of `hy/macro.py`** (soft landing, recession, higher for longer, disinflation rally, stagflation). Each tested series goes into `MacroPath.extra`, with a stated rule per path.
2. **Historical replay.** Run each issuer through the actual macro paths of 2008, 2015 (oil), 2020, and 2022 (inflation). This is the plainest stress test. It also checks the model: the replayed EBITDA path should look like what issuers in those sectors reported.
3. **The Federal Reserve supervisory scenarios.** The 2026 severely adverse scenario has a 4.6% fall in real GDP, unemployment at a 10% peak, and a corporate bond spread of 5.7 points. The Federal Reserve publishes the scenario and the history of each variable every year. It is a standard outside stress that nobody in this project designed.
4. **Later, if needed: conditional forecasts from a vector autoregression** (Bańbura, Giannone, Lenza 2015). Shock one variable, for example oil up 50%, and the model fills in consistent paths for CPI, the PMI, and rates. Build this only when hand-written path rules disagree with each other.

### M5. Fewer series, less overfitting (principal components)
If more than a few series survive, compress them into two or three common factors (Stock and Watson 2002) and test the factors. Forty series and one hundred quarters will overfit.

### M6. Portfolio summary per path (debt at risk)
For each path, report the share of HY debt held by issuers whose interest cover falls below 1x, and the share whose leverage rises above the covenant level. The IMF reports corporate "debt at risk" this way. The engine already computes both numbers per issuer and quarter.

## The rules for every test
1. **Fix the claim before you look.** Take the sign and the lead from the 2011 note. Do not search over lags.
2. **Use only what was known at the time.** Each macro value takes its release date as `available_at`. Each EBITDA takes its filing date. Use first-release vintages for CPI. ISM data is licensed: FRED deleted all ISM series in June 2016. Use the free Philadelphia Fed Manufacturing Business Outlook Survey (from 1968: activity, new orders, prices paid).
3. **Use the note date as the cut.** Data up to November 2011 only replicates the chart. Data from December 2011 onward is a true out-of-sample test. Only that period counts.
4. **Estimate on a broad panel and apply to HY.** HY issuers alone are few, and many file privately. Estimate on all firms in the sector with point-in-time quarterly financials. Use the high-leverage interaction to read off the HY response. Compustat reports quarterly cash-flow fields year to date, so difference them first.
5. **Count the quarters, not the firms.** The macro series varies only over time. Twenty-five years give about one hundred quarters of macro information, however many firms the panel holds.
6. **Beat the current model out of sample.** The benchmark is the current `m_t` plus the driver's own past. For the regression, use the Clark–West (2007) test. For the event model, use the log loss and the Brier score.
7. **Require stability.** The sign must hold in at least three of the four cycle windows (2008, 2015, 2020, 2022), and in at least two of the three windows after the note date.
8. **Correct for eight tests.** Use the Holm correction at 5%. Any lag outside the table is exploratory. It needs |t| > 3 (Harvey, Liu, Zhu 2016) and a new decision page.

## How a result changes the model
- **Passes on revenue (M1):** add the series to `DEFAULT_DRIVER_LINKS` for `g` in that sector, with the per-quarter betas.
- **Passes on the cost ratio (M1):** add a new link from `v` to the series. This is the first macro link on costs.
- **Passes on the odds (M2):** add the series to `m_t`. The scenario weights then move with it.
- **Passes on the depth (M3):** the downside cases take their depth from the fitted percentiles.
- **Fails:** record the statistics in the card. The claim leaves the list. A failure is a result.

A macro series never becomes a reason to buy or sell one bond. It moves the drivers and the odds for every issuer in a sector. The issuer's own numbers still decide which bond is cheap.

## References
Status shows what was checked on 24 October 2026. Each source needs a card before a test cites it.

| Source | Use here | Status |
|---|---|---|
| Jordà (2005), AER 95(1), 161–182 | M1, driver response by horizon | Abstract read |
| Driscoll and Kraay (1998), REStat 80(4), 549–560 | M1 standard errors with a common time shock | Not checked today |
| Gilchrist, Schoenle, Sim, Zakrajšek (2017), AER 107(3), 785–823 | Cash-short firms raise prices; HY cost pass-through | Abstract read |
| Adrian, Boyarchenko, Giannone (2019), AER 109(4), 1263–89 | M3, macro moves the bad tail | Abstract read. A 2022 replication finds that the effect weakens on data to 2021 |
| Covas, Rump, Zakrajšek (2014), IJF 30, 691–713 | M3, panel quantile stress test | Abstract read; volume and pages from a third-party listing |
| Federal Reserve, 2026 supervisory stress test scenarios | M4, outside stress paths | Scenario release read; history tables exist in each year's document |
| Bańbura, Giannone, Lenza (2015), IJF 31(3), 739–756 | M4, conditional paths | Abstract read |
| Stock and Watson (2002), JBES 20(2), 147–162 | M5, factors from many series | Abstract read |
| Foroni, Marcellino, Schumacher (2015), JRSS A 178(1), 57–82 | Monthly series into a quarterly target | Abstract read |
| IMF, *Global Financial Stability Report*, October 2019 | M6, debt at risk at interest cover below 1x | Secondary sources only; primary annex not read |
| Novy-Marx (2011), RoF 15(1), 103–134 | Operating leverage: why `v` and fixed costs set EBITDA sensitivity | Abstract read |
| Stock and Watson (2003), JEL 41, 788–829 | Leading indicators are unstable | Abstract read |
| Gilchrist and Zakrajšek (2012), AER 102(4), 1692–1720 | Spreads lead activity; H8 | Cited in `forecast-ice-hy-oas.md`; no card of its own |
| Faust, Gilchrist, Wright, Zakrajšek (2013), REStat 95(5), 1501–1519 | Spreads predict activity in real time | Abstract read |
| Engstrom and Sharpe (2019), FAJ 75(4) | H7, the near-term forward spread | Abstract read |
| Clark and West (2007), J. Econometrics 138(1), 291–311 | Out-of-sample test for nested models | Abstract read |
| Harvey, Liu, Zhu (2016), RFS 29(1), 5–68 | The t > 3 hurdle | Abstract read |
| Croushore and Stark (2001), J. Econometrics 105, 111–130 | First-release data | Abstract read |
| Trahan and Krantz (2011), *The Era of Uncertainty*, Wiley | The framework behind the notes | Catalogue record only |

## Test that settles it
Write `scripts/wt_tests.py`. It builds the issuer-quarter panel from point-in-time data and runs H8 first, then H1 to H7, through M1 and M2. It writes one table per claim: the in-sample and out-of-sample statistics, the sign per cycle window, and a pass flag. M3 runs only when M2 passes for at least one claim.

Write `tests/test_wt_tests.py` with four checks:
1. No value enters with `available_at` after the decision date.
2. On a synthetic panel with a known effect of `X` on `v` two quarters ahead, M1 recovers the effect at `h = 2` and finds none at `h = 0`.
3. On a synthetic panel with no effect, the date-correlated standard errors reject at about 5%. The issuer-only standard errors reject far more often, which shows why rule 5 matters.
4. The lead of each claim comes from the table above. The code cannot change it.

The decision closes when the tables exist and this page records which claims passed.

## Phase 1 results

### H1: rising factory input prices (run 24 October 2026)
Run: `PYTHONPATH=. python3 scripts/wt_tests.py --claim H1`. Output: `data/raw/backtest/wt_H1.json` (vendor-derived, out of git). Tests: `tests/test_wt_tests.py`.
Signal: Philadelphia Fed prices paid (SA), quarter average, a 2-quarter rise above one standard deviation. Ten signal episodes: 1994Q2, 1999Q3, 2002Q2, 2004Q1, 2008Q1, 2009Q3, 2011Q1, 2016Q2, 2020Q4, 2025Q2.

**Verdict: the claim failed.** None of the 30 outcome tests passed: 3 sectors, all firms and high-leverage firms, 5 outcomes each. In most cases the result is not just weak. It points the other way.

What happened in the four quarters after a signal, industrials (all firms, about 500 a quarter):

| Outcome | Claim | After a signal | Other quarters |
|---|---|---|---|
| EBITDA, change over 4 quarters | Falls | +15.3% on average. It fell in 1 of 10 episodes | +5.1% on average |
| Sales growth, change | Slows | Sped up by 8.6 points on average. It slowed in 2 of 10 episodes | Slowed by 1.9 points |
| Cost ratio (COGS / sales), 2 quarters | Rises | Fell by 0.4 points. It rose in 4 of 10 episodes | Fell by 0.1 points |

Materials and consumer discretionary show the same pattern. After a signal, EBITDA grew by 29% (materials) and 13% (consumer) on average, against 2% and 6% in other quarters.

Before and after the note date:
1. **To 2011 (the period the notes could see):** weak support. With the controls in place, a one-standard-deviation rise in prices paid came before a 0.2-point rise in the industrial cost ratio over two quarters (t = +3.3). It also came before somewhat lower EBITDA growth (t = -1.8).
2. **From 2012 (the true test):** the cost effect disappeared (t = -0.5). Sales growth went the opposite way to the claim and sped up (t = +5.2). Prices paid did improve the sales forecast (Clark-West t = +2.7), but with the sign reversed. A reversed sign is a fail under the pass rule.
3. **High-leverage firms** (debt above 4x EBITDA) show no stronger margin squeeze. The closest case was the industrial cost ratio: t = +3.4 to 2011 and t = +1.5 after, with Clark-West p = 0.09. That is far from the Holm bar of 0.006.

Why the claim fails, as far as the data shows:
1. Most of the jumps in prices paid came in recoveries: 2004, 2009Q3, 2016Q2, 2020Q4. Strong demand pushed up input prices and sales together.
2. Sales are in nominal dollars, so inflation itself raises reported sales. The margin and cost-ratio outcomes carry no such bias, and they show no squeeze either.

Limits: `comp.fundq` is the current view, not point in time, so it measures outcomes after restatements. The survey seasonal factors are revised each year. Aggregates weight large firms more.

**What we decide:** prices paid does not enter the model as a warning of lower EBITDA. The reverse reading would treat prices paid as a sign of recovery and stronger demand. That is a new claim and exploratory under rule 8. It needs its own decision page and |t| > 3 on fresh data before any use.

### All claims, firm level (run 24 October 2026)
The first H1 run summed firms into sector totals, so the largest firms dominated it. For example, the 8 largest firms make 46% of consumer discretionary sales. The rerun treats each firm as one equal observation.
Run: `PYTHONPATH=. python3 scripts/wt_tests.py`. Figures: `scripts/wt_figures.py`. Write-up: `docs/writeup/wt_relationships.pdf`.
Universe: 17,767 US non-financial firms and 446,255 firm-quarters with LTM sales above $40m, 1992 to 2026.

Three tests per claim:
- A: the average firm, all firms and high-leverage firms.
- B: the group against a comparison group in the same quarter, which is the cross-section with quarter fixed effects.
- C: whether each firm's own past sensitivity carries over (Fama–MacBeth).

**Verdict:** 3 of 87 tests passed the rule set in advance. Only 1 survives Holm across all 87 tests.
1. **H1c passes.** For high-leverage industrials, the cost ratio rises 0.22 points of sales per 1 sd jump in prices paid, within 2 quarters (t +3.7 to 2011, +3.1 after; Clark–West p = 0.0001). H1 on the level of prices paid fails (0 of 18 tests).
2. **The H1 sales claim is reversed.** Sales sped up after prices-paid jumps (t +3.3 to +6.0 against the claim, after 2011). All 10 tests that went clearly the wrong way after 2011 are H1 or H1c.
3. **H5k passes the rule but is borderline.** KOSPI leads materials sales growth (p = 0.006; high leverage p = 0.0006). It misses Holm across all 87 tests.
4. **H2 and H3 hold in direction in both periods but give no forecast gain.** Inflation goes with weaker consumer EBITDA and margins. Oil goes with higher energy EBITDA and higher consumer costs.
5. **H4, H5 (copper), H6, and H7 fail.** H4 and H7 hold only after 2011.
6. **Baseline (H8):** the Baa spread change is weakly useful (high-leverage t +3.5 to 2011, +3.0 after; all firms 4 of 4 cycles). Bank lending standards predict EBITDA declines only to 2011 (t +5.3, then 0.0). The factory survey does not predict them at all.
7. **Test C:** firm sensitivities carry over for prices-paid jumps on sales (slope 0.89, t 5.3), KOSPI on sales (0.38, t 4.0), and factory activity on declines (0.20, t 3.6).

**What we decide:**
1. No Wolfe Trahan series enters `m_t`.
2. H2 and H3 set signs only in the stress paths of `hy/macro.py`.
3. A new decision page reviews the 5.2 inputs `sloos_tightening` and `pmi` on the issuer universe.
4. A sensitivity per issuer, shrunk toward its sector, is a candidate to replace `fit_sector_beta`. Test it before use.
