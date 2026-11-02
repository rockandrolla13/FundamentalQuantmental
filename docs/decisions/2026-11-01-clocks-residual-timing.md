# Clocks, residuals, timing: six proposed methods

Date: 2026-11-01. Status: proposed, revised after a citation audit and a method audit on the same day. Nothing is built and no market test has run. The review behind this page is a rapid systematic review, and human gates 1 to 4 stay open. Sections touched: methodology Section 4.7 (new subsection 4.7.1), Sections 7.2, 7.3, 7.5, 7.6, S1, the Composite of Section 8, Sections 9.1, 9.2, 9.3, 9.4, and 11. Framework F5, F8, S9. Decision pages: `2026-10-22-duration-mismatch`, `2026-10-22-alpha-backtest-design`, `2026-10-22-esp-peer-groups`, `2026-10-22-weights-esp-spider`, `2026-10-23-peer-fair-spread`, `2026-10-26-conviction-book`. Code today: `hy/clocks.py`, `hy/sources/clock_facts.py`, `hy/sources/schedules.py`, `scripts/backtest_clocks.py`, `hy/backtest.py`, `hy/groups.py`. Review report: `research/notes/clocks-systematic-review.md`, with the audit record in its Section 10.

## Context

The user asks for methods in four areas. The first is the two clocks. The second is the idiosyncratic residual. The third is timing. The fourth is where to take risk.

Eight facts from the repo shape the design:

1. The split test on file does not measure the revenue clock. `hy/sources/clock_facts.py` rule 3 spreads all RPO evenly over 2 years. So `revenue_runoff` is year 2 for every issuer, and RPO acts only as a filter at 25% of LTM revenue.
2. The split test has no control variable. `renewal_split_test` regresses log spread on a constant and two shares. The two shares and the share due within 2 years add to one. So each coefficient is a contrast with the near share.
3. The t values of the split test may run high. `renewal_split_test` passes monthly slopes of a level regression to `hac_mean` with `h - 1` lags, so 2 or 5. The AR(1) of those slopes is not on file. Section 7.1 of the report gives the size of this problem.
4. The backtest cost clock differs from the Section 4.7 table and from live E5. It holds no interest and no signed leases not yet started. It files operating and finance leases together, and it files purchases with rent at face. A filing that tags no debt ladder and no debt total reads a zero refinance share, because only `e5` gets the Compustat debt fill.
5. Lease ladders read ASC 842 tags only. `FAMILIES` in `hy/sources/schedules.py` holds `LesseeOperatingLeaseLiabilityPayments*` and `FinanceLeaseLiabilityPayments*`, and `keep_tag` in `clock_facts.py` drops other stems. So before an issuer's first ASC 842 filing, `rent_1y` is 0, and `e5`, `fixed_charge_years`, and the recontract share hold no operating rent. The count of affected issuer-months is not on file. Panel debt comes from `dlcq` and `dlttq`, and reported debt absorbed leases near one for one at adoption (Palazzo and Yang, Table 2). So panel `leverage` and the implied class may step at adoption too, and `lev_lease_adj` on panel debt may count leases twice.
6. RPO data starts in 2018. An RPO feature can reach only the 2020 and 2022 windows (`scripts/backtest_clocks.py`). So it cannot pass the project bar of 3 of 4 cycles, and `hy.backtest.cycle_test` counts an empty window as a fail.
7. As built, the S1 residual is the peer gap of Section 7.2. `f_t` is not fitted, E4 is suspended, and none of F01 to F30 has a result on our data.
8. After February 2017, the rating class is a leverage cell. The implied class matches the actual class on only 36% of issuer-months (`2026-10-22-esp-peer-groups`). The 2020 window, the 2022 window, and the whole RPO sample sit after that date.

## What the sources say

Page numbers and copy details are on each card. The review report holds the full evidence tables.

**The clocks.**

1. Leases and purchases differ. S&P treats leases as debt-like (para. 26, p. 7) and purchase commitments as not debt-like (para. 10, p. 5). Moon and Phillips call purchase contracts "forward contracts with escape clauses and also not as leases" (p. 9). They served as hedges in one steel futures test (Almeida et al. 2017, p. 52).
2. In manufacturing firms, users of purchase contracts have a lower raw mean default probability, 0.016 against 0.033. Medians are zero, users are larger, and the paper has no default test (Moon and Phillips, p. 47).
3. At equal reported leverage, more lease goes with a wider offering spread. Moody's lease adjustment over assets has 0.450 (t 5.24) on log offering spread (Kraft 2011 draft, p. 44). In that sample, 456 of 1,210 issues are rated Ba or lower (p. 38). The imputed lease liability has 4.130 (p 0.000) across 4,553 issues (Gordon et al. 2024 draft, p. 55). Both pool ratings, and both test amounts at issue.
4. Loans differ. In loans, lease expense carries the price and the liability adds nothing: 0.829 (p 0.013) against 0.090 (p 0.472) (Gordon et al., p. 48). Inside retail firms, the loan spread does not rise significantly with lease use (Altamuro et al. 2012 draft, pp. 22-23).
5. ASC 842 is a dated event. Operating leases reach the balance sheet in fiscal 2019 for December year ends and in 2020 for others (Kallen, p. 9). High yield funds cut holdings of exposed bonds: -0.027 (t -2.70) on the triple interaction (He et al. 2025 draft, p. 51). Fixed first-year lines fall and rent above them rises after adoption, which suggests a move to variable leases (Heese et al., p. 35). Reported debt absorbed the lease liability near one for one: 1.08 (se 0.06) (Palazzo and Yang, Table 2).
6. Lease-heavy firms report less debt. Financial leverage falls from 0.27 to 0.19 across lease deciles, and market capitalisation falls from $3,446m to $425m (Dogan, p. 583). Firms with substantial leases have lower non-lease leverage, -3.402 (se 0.501), and they are more often rated high yield or not rated (Kallen, p. 25). Rent does not fall with sales: the response is -0.02, against 0.39 for interest (Dogan, p. 598).
7. In the model of Becker et al. (Proposition 1, p. 15), rejection lowers the liquidation threshold and raises the insolvency threshold. The paper tests leverage and loan flows, not default or recovery (pp. 27, 35).
8. A chosen variable can take the wrong sign. Cash has +3.12 (t 3.48) in OLS and -4.42 (t -2.31) when instrumented, in column 2. Column 3 has +3.25 (t 3.83) and -2.64 (t -1.71) (Acharya et al., pp. 36-37). The transfer to leases is our proposal.
9. Backlog has weak disclosure rules, and firms often count cancellable orders (Toynbee 2017, pp. 4, 11). Its level goes with higher ratings: `LN_OB` 0.221 (se 0.063) (Habib et al., p. 12). Habib et al. also report slopes on the two parts of the sales gap. Read by arithmetic, those slopes lower the rating on both sides of zero, and the authors' text says otherwise (pp. 4, 8, 12).
10. ASC 606 is a dated break too. Loan cost rises by 21.6 bp (se 8.1) for firms with a material impact (Lee et al., p. 18). The rise fades by 2020 to 2021 (p. 22). That paper tests adoption and not RPO timing.
11. No opened source tests RPO or lease tail against bond spreads. Jung and Scarlat (2024) and a 2014 draft of Andrade et al. were opened after the audit. See the addendum.

**The residual.**

1. Expected loss dominates at B and below. At Ba the split is near even. One unit of spread forecasts loss of 0.46 and premium of 0.54 at Ba, and 0.89 and 0.12 at B and below (Nozawa, February 2016 draft, p. 16). The 2014 draft gives junk volatility ratios of 0.69 (se 0.17) and 0.31 (se 0.17) (p. 27). With market states they are 0.61 (se 0.19) and 0.47 (se 0.14) (p. 40). These are working paper results on spreads. That a wide residual is not mispricing by default is our inference.
2. Across all ratings, the diversification factor is 0.10 for loss and 1.19 for return (Nozawa, 2014 draft, p. 39).
3. Structural residual changes share one factor. The first component explains 81.7% (He et al., p. 45). Distress coefficients run from 0.048 to 0.499, and first-component loadings from 0.055 to 0.431, between medium AA and medium B (pp. 45-46). Inside HY the gap is smaller: 0.251 at medium BB and 0.499 at medium B.
4. A four-part liquidity composite prices speculative grade where pooled Roll does not (Dick-Nielsen et al., Table 3, p. 7). In non-callable speculative grade bonds, the median liquidity part over the swap rate is 24% and 23% (p. 11). The source says that this fraction moves with the benchmark (p. 10).
5. A price shared by signal and return inflates a premium. The bias runs from 15% of the premium for the plain spread sort to 47% for `val_ipr` (Dickerson et al. 2026, p. 37, our arithmetic). No row of that source matches S1.
6. Three contrasts may separate mispricing from risk and liquidity (Bartram et al., pp. 19-27). They are decay against survival of the characteristic, flat response across default and liquidity groups, and no effect on same-firm equity. The source's flat rows are failed rejections in an 86.3% IG sample (pp. 42, 50-51).
7. A plug-in regression on a residual keeps a bias (Chernozhukov et al., p. 3). The theorem assumes i.i.d. draws (p. 23). In panel simulations, only correlated random effects stay close to the true effect across settings (Fuhr and Papies, p. 24). The verdict on a new factor depends on the control set (Feng et al., RMW 160 bp against 15 bp, p. 36, equity evidence).
8. Fama-MacBeth errors run low when a persistent regressor meets a persistent error, and adjusted forms stay biased (Petersen, pp. 4-5, 16).

**Timing and risk.**

1. In the price evidence, a due date widens spreads in proportion to illiquidity. Nagler reads changes in yield spreads on S&P 500 firms near BBB, and the interaction uses a bond's own liquidity change (pp. 33-35, 60). Valenzuela reads non-US bonds, with 170 speculative grade bonds (pp. 8, 34). The interaction holds before and in the crisis: 1.741 (se 0.327) and 1.524 (se 0.283) (p. 35). S&P 500 firms with debt due in 2009 and rigid prices widen more after Lehman (Augustin et al., p. 35). No opened source compares calm and stress in US high yield.
2. A separate result covers investment and not price. Firms with debt due right after 2007 cut investment, with no counterpart from 2000 to 2006 (Almeida et al. 2009, p. 6).
3. In the calibration of He and Xiong, longer debt has a lower spread at equal leverage: 215 bp against 330 bp (p. 17). This compares two model firms.
4. Long debt goes with high asset beta (Chen et al., pp. 5-6). The spread response is 84 bp in high-leverage firms and negligible in low cash flow beta firms (pp. 41-42).
5. In a median A- sample, the interaction with a HY dummy adds 2.28% a year per standard deviation (conference draft, pp. 25-26). The draft has no HY-only premium. The long-short intercept keeps 58% to 90% of its size after default, term, and liquidity factors, and it loses significance (Table 10, p. 59, our arithmetic). So this draft cannot separate compensation from mispricing. The file names no authors.
6. A nonlinear function of log US EBP and the VIX forecasts 3-month bond returns (Boyarchenko and Elias, pp. 45, 61). The US column reports an in-sample R-squared of 9.2% and a source out-of-sample R-squared of 5.8% (Table 1, p. 43). The 5.8% is a covariance measure, at bond level with rating terms, on a basis chosen from 2,058 forms on the same window (pp. 43, 61-62). So no number transfers to a test on a HY return. In-sample global fit sits in 2007-2009 and 2020 (Table 6, p. 48). The paper has no cost test.
7. Of 58 long-short bond factors with significant gross means, 2 keep a significant net alpha for large trades (Dickerson et al. 2025, Table 4, p. 59). Slow accounting signals lose little to delay. Long-only credit tilts keep a net Sharpe of 1.18 (Ivashchenko and Kosowski, p. 20). That table tests return over T-bills, not alpha, and we read much of it as credit premium.
8. Issuer quality forecasts HY excess returns: -9.534 (t -3.97) at one year, 1962 to 2008 (card `greenwood-hanson-2013-issuer-quality-bond-returns`, Table 3). This is a rival state to the factor of item 6.

## What the data says

These results are on file. They come from `docs/methodology.md` Section 4.7, `2026-10-22-alpha-backtest-design`, `2026-10-22-esp-peer-groups`, and `2026-10-23-peer-fair-spread`.

1. Split test, 2018 to 2026, 187 issuers, 99 months: refinance +0.36 (t 2.0), recontract -2.07 (t -2.4), difference -2.43 (t -2.8). See context fact 3 on these t values.
2. IC beyond spread at 6 months: refinance share -0.037 (t -1.7), recontract share +0.027 (t 1.0), `renew` -0.035 (t -1.8), `dgap` +0.015 (t 1.0), `e5` -0.032 (t -1.2).
3. `e5` IC after cost: -0.082 (t -4.5) at 3 months and -0.114 (t -4.7) at 6 months, at a hedge of beta = 1. No DTS hedge rerun of `e5` is on file.
4. The hedge flips the spread level result. Widest has IC after cost of 0.22 and 0.29 at beta = 1, and +0.012 (t 0.5) and +0.026 (t 0.7) under the DTS hedge. So "under the DTS hedge, spread level alone (widest) earns nothing after cost".
5. A skip-month test on file shows the shared-price bias in the peer gap, which is S1 as built. Plain IC after cost at 3 months falls from +0.054 (t 3.4) to -0.000 (t 0.0). IC beyond spread falls from +0.112 (t 9.0) to +0.073 (t 6.1), from +0.120 (t 6.1) to +0.100 (t 5.3), and from +0.198 (t 7.4) to +0.181 (t 6.7). That is about 35%, 17%, and 9% (our arithmetic). A skip also drops one month of signal, so this measure mixes bias and decay.
6. After the skip, the peer gap passes the cycle bar at 3 and 12 months and fails it at 6 months (2 of 4).
7. With carry hedged out, the peer decile book earns +1.4% a year, and one quarter earns +37.8%. Without that quarter the book loses 0.65%. The on-file page calls the gap a tie-breaker.
8. At the TRACE-proxy cost almost every book loses. The main cost case on file is 15 bp a round trip.
9. Fixed-charge years rank with spread at +0.32 (t 36) across 1,143 issuers. This field holds all obligations and no timing, so it reads close to lease-adjusted leverage.
10. E5 reads no RPO. So the fixed run-off does not explain the E5 result.

No test on file supports the Section 4.7 phrase "risk measures". No VAR, IPCA fit, structural residual, or `lambda` control exists on our data. The 8-day gap and OneScore's bias are not measured.

## Options

1. **Keep Section 4.7 as written.** It costs nothing. It leaves the revenue clock untested and the phrase "risk measures" with no support.
2. **Rebuild the fields and rerun the same regression.** It is cheap. It keeps the absent controls and the same errors, so a new sign would still be hard to read.
3. **A ranked set of six methods.** Rebuild, test, classify, time, locate, set the band. Each method has a pass, a fail, and an untestable outcome. It costs the most work, and it can end with a result that removes the clocks from the alpha view.
4. **A structural route.** Add leases to debt in a Black-Cox model and read the residual. Single-bond R-squared is 0.13 in speculative grade (Feldhütter and Schaefer 2018, p. 36). The boundary choice moves the US HY mean error by 84.8 bp (Huang et al., p. 123). E4 is suspended. So we keep this for later.
5. **New clock weights now.** No test supports any weight.

## Choice

Option 3. It is the only option that gives a falsifiable answer to each question. It also reuses the reversal test that the repo fixed on 2026-10-22. This page changes no code, no weight, and no E5 setting.

What the audits changed in this choice:

| Method | Verdict after audit | What survives |
| --- | --- | --- |
| 1 Rebuild | The 99% run-off cut is refuted as the primary `T` | Three classes, amounts, near and far debt, a lease regime, filed shares. Cost clock work now comes first |
| 2 Residual test | Arm A as first written is refuted | Arm A with month terms, issuer means, clusters, and a permutation null. Arm B is exploratory. Arm D is report only |
| 3 Layers | The classifier as first written is refuted. The cohort step does not apply to the peer gap | The liquidity and forward layers, with a rewritten classifier |
| 4 Market state | The lease and RPO terms are refuted as first specified | The debt term, with a state that is not built from these spreads |
| 5 Map | The map as first written is refuted | One pooled test on admissible names, under the DTS hedge. The cell map is a report |
| 6 Band target | M6.1 can run. The source number does not transfer | A vintage factor on log EBP, an overlay test, and a rival arm. M6.2 waits for band levels |

### Rules for all six methods

1. Each number we choose carries the label "Our choice, v0". Freeze each one on a decision page before a run. Freeze one table of Benjamini-Hochberg family members there too, and mark each test as in or out of the family.
2. An input in `docs/data_contract.md` reads through `DataView` with `as_of` and `available_at`. `compustat_annual`, `trace_trades`, `bond_daily`, `macro_series`, and `bond_terms` sit outside contract 3.14. Add each one to 3.14 before a production run, or label its result `research_only`. Research arms that fit on all periods feed no live score.
3. Stamp a record at the first moment that version was public. Stamp annual Compustat rows from the 10-K acceptance time of contract 3.4, with `datadate` + 90 days as a floor. `comp.funda` is a restated view (`2026-10-22-esp-peer-groups`, F21 Risks). So label its 2008 fields research only, and use XBRL ladders with filing dates in the 2015 window. A stamp test cannot catch vendor backfill.
4. A clock feature has zero signal weight until it passes the signal bar. The bar is a positive rank IC beyond spread after costs in at least 3 of the 4 cycles 2008, 2015, 2020, 2022. It reads the DTS hedge (`hy.backtest.dts_realised`). Report the hedge at beta = 1 beside it. The project bar in `CLAUDE.md` stays the floor. "Beyond spread" is added, because raw IC at beta = 1 reads spread level.
5. An RPO feature can reach 2 windows at most. So it can inform a limit or a memo, and it can earn no signal weight. The project bar wins over the reversal test of `2026-10-22-alpha-backtest-design`. A pass on M1.4 moves `dgap` and `renew` to memo and limit rows only. M1.8 is the one route for a revenue clock to reach 3 windows, through a labelled proxy.
6. **Errors.** Do not read a t from `hac_mean` on a level regression. Use pooled OLS with clusters by issuer and month, as in Petersen (p. 26). Beside it, shuffle the clock feature across issuers inside sector x class, keep each issuer path, and use 1,000 draws. Read each pass from the null percentile. `driscoll_kraay_ols` with at least 12 lags is a report only, because it rejects at 0.318 in our simulation (report Section 7.1).
7. **Three outcomes.** Each test reads pass, fail, or untestable. Output `mde`, which is the smallest slope that the full test finds at 80%. Compute it by injection of a known slope into the real panel before any read. Below 80% at the smallest slope of interest, the test reads untestable (Our choice, v0). A fail then means no effect at that size.
8. **Rating.** After February 2017 the class is a leverage cell. Its cut-offs were fitted before ASC 842, so it may also shift at adoption (context fact 5). A rating feed is a required input for M2.1, M3.1, M5.1, and M5.4, as test 1 of `2026-10-22-esp-peer-groups` already asks. With no feed, M2.1 reads untestable, and the M5 cells take leverage names, L1 to L4. Read 2008 and 2015 apart from 2020 and 2022.
9. Run on the production machine, with history from 2004 (`docs/factors/PRODUCTION_DATA.md` section 1). This stage runs nothing.

Run order follows these dependencies:

1. The cost clock of Method 1 comes before Method 2.
2. The revenue clock of Method 1 starts with a pilot of 30 issuers (Our choice, v0).
3. Method 2 comes before Method 3, because Method 3 reads the features that Method 2 admits.
4. The `lambda` build of Method 3 comes before Method 4, because Method 4 reads median `lambda`.
5. M6.1 comes before the `gcc_us` arm of Method 4.
6. M6.1 and the overlay M6.5 can run first. M6.2 waits for band levels and arm B of the conviction book.

---

### Method 1. Rebuild the clocks from filed schedules

Answers: how to improve the two clocks. It comes first, because every later test reads these fields. Part A is the cost clock, which can reach all four windows. Part B is the revenue clock, which starts with a pilot.

**Assumptions.**

1. A filing states what the market could read at its acceptance time.
2. Leases are debt-like for a going concern, and purchases are not (S&P). This rests on one agency in the opened set. A finance lessor is roughly treated as a secured lender, with an aircraft exception (Gavazza, p. 64). So finance leases move to the debt class, unless `debt_includes_leases` is true.
3. Purchase lines past year one are frequently minimums (Moon and Phillips, p. 10). A purchase hurts only above what a lower cost base can use.
4. An amount over EBITDAR does not move when another class moves. A share does. EBITDAR at or below 0 reads the cap, and all amounts clip at `LEV_CAP`, by the rule of `2026-10-30-negative-ebitda-leverage`.
5. `F^RPO` reads filed windows. A filer whose filed windows cover under 50% of RPO leaves the revenue tests (Our choice, v0). A filer with no windows keeps the 2-year default and a flag, and it leaves the test sample.
6. Full rejection of real property leases gives an upper bound for the claims view, because filings hold no lease-level data.

**What the old `T` reads.** `hy.clocks.rpo` and `runoff_year` set `T` from the last window end plus an assumed tail. We ran both functions. A filer with 90% in 12 months and a filer with 30% in 12 months both get `T` = 3 with the 2-year tail. A filer with 60% in 24 months gets `T` = 4. Tails of 1, 2, and 5 years move the first filer to 2, 3, and 6. They move its share after `T` of a 10-year level ladder to 0.80, 0.70, and 0.40. So the 99% rule reads disclosure format and an assumption, not contract life. `revenue_runoff_filed` stays as a report with that flag.

**Formula, amounts.**

```latex
A^{k}_{i,t} = \frac{\sum_{\tau} \big(1 - F^{RPO}_{i,t}(\tau)\big)\, o^{k}_{i,t,\tau}}{EBITDAR_{i,t}}, \quad k \in \{debt,\ lease\}, \qquad X_{i,t} = \frac{\sum_{\tau} \max\big(0,\ PO_{i,t,\tau} - (1-d)\,COGS_{i,t}\big)}{EBITDAR_{i,t}}, \quad d = 0.30
```

Intuition: weight each fixed charge by the share of signed revenue already gone at its due date, in years of today's cash. A purchase counts only where it exceeds what a lower cost base can use. `EBITDAR` is LTM EBITDA plus rent. `F^RPO` is the filed cumulative share. `o^debt` holds principal and finance lease payments, and those payments hold imputed interest. Interest stays in its own field, because the companyfacts feed holds no rate. `d = 0.30` is Our choice, v0.

Run every RPO test at tails of 1, 2, and 5 years. Count a result only if its sign holds at all three (Section 4.7 rule 3). Report `rpo_share_12m`, `rpo_share_24m`, and `t50`, each NaN when filed windows do not reach that share. Tests that need no RPO read near amounts (3 years or less) and far amounts (over 3 years) in the same units. The 3-year line follows `RI` in Method 5 (Our choice, v0).

**Formula, claims view.**

```latex
\text{rent\_option\_gap}_{i,t} = \frac{R^{rem}_{i,t} - \max\big(R^{1y}_{i,t},\ \min(0.15\,R^{rem}_{i,t},\ R^{3y}_{i,t})\big)}{\sum_{\tau} O_{i,t,\tau}}
```

Intuition: this is the part of the fixed charges that a court could remove, as an upper bound. The cap follows framework F5 on one pooled lease. It is NaN for issuers with aircraft or vessel leases, set by framework archetype A5 or the Section 1110 text.

**Formula, signed revenue.**

```latex
\text{rpo\_intensity}_{i,t} = \frac{RPO_{i,t}}{Rev^{LTM}_{i,t}}, \qquad \text{rpo\_drift}^{+}_{i,t} = \frac{\max(0,\ \Delta Rev^{LTM}_{i,t} - \Delta RPO_{i,t})}{Rev^{LTM}_{i,t}}, \qquad \text{rpo\_drift}^{-}_{i,t} = \frac{\min(0,\ \Delta Rev^{LTM}_{i,t} - \Delta RPO_{i,t})}{Rev^{LTM}_{i,t}}, \qquad \sigma^{x}_{i,t} = \sqrt{\sum_{\tau} w^{x}_{\tau}\,(\tau - \bar\tau^{x})^2}
```

Intuition: more signed revenue may lower risk, and the source reads only the positive part of the gap as a warning. Neither part has a sign prior, because the source's two slopes point to a lower rating on both sides (Habib et al., pp. 8, 12). A lumpy clock forces one large decision on one date. Revenue replaces assets in the drift scale, because the data contract holds no asset field (Our choice, v0).

**Inputs.**

| Input | Contract field | `as_of` | `available_at` | Status |
| --- | --- | --- | --- | --- |
| Operating lease ladder, ASC 842 tags | 3.5 `ladders["operating_lease"]` | Balance-sheet date | EDGAR acceptance time | have, from the first ASC 842 filing |
| Finance lease ladder, ASC 842 tags | 3.5 `ladders["finance_lease"]` | Balance-sheet date | EDGAR acceptance time | have, from the first ASC 842 filing |
| Lease ladders before ASC 842 | Older XBRL stems `OperatingLeasesFutureMinimumPayments` and `CapitalLeasesFutureMinimumPayments`, to confirm against the taxonomy. `compustat_annual` `mrc1` to `mrc5`, `mrcta` | Balance-sheet date | 10-K acceptance time, with `datadate` + 90 days as a floor | need |
| Adoption date | First ASC 842 filing, or Compustat `acctchg` = `ASU16-02` (He et al., p. 16) | Fiscal period | Filing acceptance time | need |
| Operating lease liability | XBRL `OperatingLeaseLiability`, current and non-current (Palazzo and Yang, Section 3) | Balance-sheet date | EDGAR acceptance time | need |
| Debt ladder and total | 3.5 `ladders["debt"]`, `debt`. `debt_includes_leases` is true when the tag family names leases. In Compustat fields, subtract capital leases (Kallen, p. 9) | Balance-sheet date | EDGAR acceptance time | have the ladder, need the flag |
| Purchase ladder | 3.5 `ladders["purchase"]`, XBRL only, so 3 windows at most | Balance-sheet date | EDGAR acceptance time | have |
| Signed leases not started | 3.5 `lease_not_commenced` | Balance-sheet date | EDGAR acceptance time | have per filing, need in the panel |
| Interest rate | 3.3 `interest_rate` | 10-Q acceptance time | 10-Q acceptance time | have per filing, need in the panel |
| RPO total, windows, tail | 3.3 `rpo_total`, `rpo_windows`, `rpo_tail_years` | 10-Q acceptance time | 10-Q acceptance time | have per filing. Pull a stratified pilot of 30 issuers first, then the 343 RPO issuers |
| LTM EBITDA, LTM revenue | 3.3 `ltm_ebitda`, `ltm_revenue` | 10-Q acceptance time | 10-Q acceptance time | have |
| Rent, COGS | 3.2 `rent_expense`, `cogs` | Quarter end | First moment this version was public | have |
| RPO scope text | 3.6 `text` | Acceptance time | Acceptance time | have the text, need the parser |
| Backlog proxy | `compustat_annual` `ob`, `sale`, and 3.6 `text` for the part beyond the fiscal year | `datadate` | 10-K acceptance time, with `datadate` + 90 days as a floor | need |

**Outputs.** `amt_debt_after`, `amt_lease_after`, `amt_purch_after`, `amt_interest_after`, `amt_debt_near`, `amt_lease_near`, `amt_debt_far`, `amt_lease_far`, `purch_overhang`, `pc_cogs_1y`, `lease_regime`, `debt_includes_leases`, `lev_ex_lease`, `lease_step`, `rent_excess`, `lease_tail_years`, `rent_ratio`, `rent_option_gap`, `rpo_share_12m`, `rpo_share_24m`, `t50`, `sens_tail`, `revenue_runoff_filed`, `rpo_timing_source`, `rpo_scope_flag`, `rpo_regime`, `rpo_intensity`, `rpo_drift_pos`, `rpo_drift_neg`, `ob_sales`, `ob_beyond_fy_share`, `sigma_debt`, `sigma_obligations`, `sigma_rpo`, `n_instruments`. `rent_excess` is rent expense less the prior year's first-line commitment, over LTM revenue. It is a memo field with no sign prior (Heese et al., p. 35). `lease_step` is the change in panel `leverage` at the first ASC 842 filing, against issuers with no leases. Print it before any test reads a class after 2019. Keep `renewal_debt_share`, `renewal_lease_share`, and `renewal_purchase_share` for one release, so that a reader can see the old test split.

**Claims and tests.** M1.2, M1.3, and M1.5 run in arm A of Method 2. Report every slope per one standard deviation of its feature.

| Test | Claim | Pass | Fail | Untestable |
| --- | --- | --- | --- | --- |
| M1.1 Coverage | Filed RPO windows exist for enough issuers | Report the share of the 343 RPO issuers with tag or text windows, fresh windows per issuer-month, and the carried share. Compare filers and non-filers on spread, leverage, and sector. The median month holds at least 60 issuers (Our choice, v0). Count the issuers with a zero or an assumed debt ladder | Below 60. The revenue clock tests read untestable, and we make no claim on the result on file | The pilot shows no parseable windows |
| M1.2 Composition | The wrong sign comes from share arithmetic | Lower bound of the 90% interval of the slope on `amt_lease_after`, or on `amt_lease_far` where no RPO exists, is above `-delta`, with `lev_ex_lease` in `X`. `delta` is half of the on-file slope per one sd of the old share, fixed before the run (Our choice, v0). Report `rent_1y` beside it | Upper bound below 0 and lower bound at or below `-delta`, under lasso, the primary learner. Composition is then not the reason | Lower bound at or below `-delta` and upper bound at or above 0 |
| M1.3 Purchase line | Purchases are not rent | Lease slope above `pc_cogs_1y` slope, with permutation p below 0.05 (Our choice, v0). Report GICS retail apart (Altamuro et al.) | The lease slope does not exceed the purchase slope. Purchases then stay in the cost clock at face | Fewer than 30 issuers with `purch_overhang` above 0 in the median month (Our choice, v0). Report those issuers as a case list. Purchases reach 3 windows at most |
| M1.4 Revenue clock | The reversal test of `2026-10-22-alpha-backtest-design` | Rebuild `dgap` and `renew` with filed windows. IC beyond spread above 0 with t above 2 at 6 months, the on-file bar. The sign holds at all three tails, and with and without 2018 and 2019 (Lee et al.). A pass moves them to memo and limit rows only | Otherwise filed timing adds no edge, and zero signal weight stands | M1.1 reads below 60 |
| M1.5 Filter | The result does not depend on the RPO line | The same sign on `amt_lease_after` and the old recontract share at RPO lines of 10%, 25%, 50%, and 100% of LTM revenue. The 100% line follows the run-rate rule in `scripts/clock_case.py` | A sign flips, and both slopes clear the permutation null. The Section 4.7 result then reflects selection | Below 60 issuers in the median month at a line |
| M1.6 Claims view | Rent is an option in distress | Default within 24 months rises with `amt_lease_after`, by the F21 rule of 0.02 out-of-sample AUC gain, and realised recovery rises with `rent_option_gap` | The hazard rises and recovery does not. If the hazard does not rise, the rejection story has no support here | Few defaults. Change no weight on this test alone |
| M1.7 ASC 842 date | Bonds respond when leases reach the balance sheet | Log spread change clears the permutation null in the 3 months around the first ASC 842 10-Q. Sort on reported lease liability less the present value of the prior schedule at the Baa yield (Kallen, pp. 8-9). A placebo one year earlier stays flat. December year ends only, so the window ends before February 2020 (Our choice, v0) | No response. Then the market already priced the footnote, which fits Kraft (p. 20) | Under 30 issuers per leg (Our choice, v0) |
| M1.8 Backlog proxy | A revenue clock proxy reaches 3 windows | Read `ob_sales` and `ob_beyond_fy_share` from 2004 to 2018, inside industries with disclosure of at least 25% (Toynbee 2017, p. 19). Flag the switch to RPO with `rpo_regime`. The signal bar passes on the proxy. Cancellable orders can enter it (Toynbee 2017, p. 4), and the current rule text holds no backlog line (17 CFR 229.101) | The signal bar fails. No revenue clock earns weight | Under 60 issuers in the median month |
| M1.9 Cases | The clocks mark known failures | Read WeWork and a named list from the default list of `PRODUCTION_DATA` section 2. The clock amount, `coverage_contracted`, `max_cum_shortfall`, or `breakeven_margin` sits in the worst decile 24 months before the event (Our choice, v0). Report `duration_gap_pv` as a check | The cases do not sit in the worst decile | Fewer than 10 named cases with filings (Our choice, v0) |

Two further tests come from the same record. The first is the Section 4.7 reason, read in M2.1. The second is the open test of `2026-10-22-duration-mismatch`, a positive rank IC for spread change around renewal dates. It waits for a contract date field, and M1.9 reports it where a filing states one.

**Overlap.**

- E5: this method splits the same total. E5 stays as set. M1.3 informs the user decision on purchases in E5.
- E8 and F21: three near-debt forms exist. They are `amt_debt_near`, `due_debt_12m`, and `refi_intensity_3y`. Name `refi_intensity_3y` as the form that a score may read (Our choice, v0), and hold the other two as reports. Report each form's absolute rank correlation with `wall_cover_4` and with F21 `mat_2y`. `wall_cover_h` falls when debt due rises, so the raw correlation is negative. Above 0.5 in absolute value (Our choice, v0), the form holds no signal.
- S1: Method 3 reads these fields as its forward block.
- Conviction book: no change. The layer 3 flags stay.

**Source cards.** `sp-global-2019-ratios-and-adjustments`, `moon-phillips-2021-purchase-contracts-capital-structure`, `almeida-hankins-williams-2017-supply-contracts-risk-management`, `dogan-2016-operating-leases-operating-leverage`, `gavazza-2010-asset-liquidity-aircraft-leases`, `becker-josephson-xu-2023-executory-contract-rejection`, `toynbee-2017-order-backlog-disclosure`, `habib-ranasinghe-bhuiyan-2025-order-backlog-credit-ratings`, `coyle-2025-maturity-walls`, `choi-hackbarth-zechner-2018-debt-maturity-profiles`, `chen-xu-yang-2021-systematic-risk-maturity`, `two-clocks-origin`, `kraft-2011-rating-agency-adjustments-bond-yields`, `gordon-wang-zhao-2024-operating-lease-loan-contracts`, `altamuro-johnston-pandit-zhang-2012-operating-leases-credit`, `he-shevlin-sun-guan-2025-asc842-bond-funds`, `kallen-2026-hidden-leverage`, `palazzo-yang-2019-leverage-operating-leases`, `heese-shin-wang-2025-variable-leases`, `lee-lee-sadka-2026-asc606-cost-of-debt`.

---

### Method 2. Test a clock feature against the residual

Answers: how to test whether a clock explains the residual. It replaces the two-regressor test of Section 4.7 as the test we read. `renewal_split_test` stays for the record.

**Assumptions.**

1. A slope is a partial effect, not a cause. Double machine learning does not supply exogeneity (Chernozhukov et al., p. 31).
2. Cross-fit nuisance models read all periods. So this is a research test, and it feeds no live score.
3. The source theorem assumes i.i.d. draws and one pooled estimate (pp. 23-24). Our panel form has no source guarantee. So check interval coverage by simulation on the panel's shape before any read.
4. Folds split by issuer, because clock features are issuer-level. K = 5 and S = 100 follow the source (pp. 24, 40). The split is Our choice, v0. Chen et al. split by unit (pp. 17-18), and Fuhr and Papies warn against it (p. 20). Report a random-row split beside it.
5. `X` holds the fields that exist at panel level: `lev_ex_lease`, `lev_lease_adj` in its F8 form, `bid_ask_pts`, `n_trades`, `mod_dur`, rating class, sector, and issuer means of these fields. That is about 4 of the 25 Section 7.2 features, plus the means. So the claim reads "beyond the panel-level `X`", not "beyond Section 7.2". It leaves out `log price`, because price and spread share one trade (Our choice, v0).
6. Rating and `lev_lease_adj` hold the lease claim, because ratings already reflect capitalized leases (Altamuro et al., p. 2). So report each slope with and without them. A control near the outcome pushes any slope toward 0.
7. A CDS holds less of the bond liquidity effect. That is an assumption of the source (Longstaff et al., p. 10), and Dick-Nielsen et al. cite evidence against it (p. 9).

**Formula, arm A (across issuers).**

```latex
\hat U_{i,t} = \log s_{i,t} - \hat\ell^{(-k)}(X_{i,t}, \bar X_i), \quad \hat V_{i,t} = c_{i,t} - \hat m^{(-k)}(X_{i,t}, \bar X_i), \quad \tilde U_{i,t} = \hat U_{i,t} - \overline{\hat U}_{t}, \quad \tilde V_{i,t} = \hat V_{i,t} - \overline{\hat V}_{t}, \quad \hat\theta = \frac{\sum_{i,t} \tilde V_{i,t}\tilde U_{i,t}}{\sum_{i,t} \tilde V_{i,t}^2}
```

Intuition: ask whether the clock surprise lines up, inside each month, with the spread surprise, after fundamentals and the issuer's usual level. Month terms remove a slope that a month shock and a feature drift can build with no cross-section link. Issuer means of `X` are the correlated random effects of Mundlak, as in Fuhr and Papies (p. 16). A second column adds the issuer mean of `c` too, which is the source form. That column reads only changes inside an issuer, so report `v_var` beside it. The learners are lasso with a rich dictionary, which is primary (Our choice, v0), and boosting.

```latex
R^{2,(k)}_{partial} = 1 - \frac{\sum_{(i,t) \in k} \big(\tilde U_{i,t} - \hat\theta^{(-k)} \tilde V_{i,t}\big)^2}{\sum_{(i,t) \in k} \tilde U_{i,t}^2}
```

Intuition: fit the slope on other folds and score it on fold `k`, so the fit cannot flatter itself. With issuer-fixed `U` and `V`, noise alone gives R-squared near 1 over N. P(at least 1 point) is 0.32 at 100 issuers and 0.17 at 187 (our arithmetic). So read the bar against the permutation null.

A beta to the HY index enters `X`, because long debt goes with high asset beta (Chen et al., pp. 5-6). Estimate it on a window that ends 12 months earlier, with duration scaled out. DTS makes return volatility scale with spread times duration, so a same-window beta sits close to the outcome.

**Sign table.** Declare a sign per feature before the run. `rpo_intensity` has a declared negative sign. `amt_lease_after` has a declared positive sign. `rpo_drift_pos`, `rpo_drift_neg`, and `rent_excess` have none. A feature with no declared sign reports only.

**Formula, arm B (inside one issuer). Exploratory, our own extension.**

```latex
\log s_{b,t} = a_{i,t} + g_{l(i),t}(T_b) + \bar\phi_{g,w}\,\lambda_{b,t} + \zeta\,\text{late\_rank}_{b,t} + \theta_o\,\text{clock\_overlap}_{b,t} + e_{b,t}, \qquad \text{clock\_overlap}_{b,t} = \frac{\max(0,\ T_b - t50_{i,t})}{T_b}
```

Intuition: a bond that outlasts the signed contracts may carry the renewal bet. `a` is an issuer-by-date effect. It removes the issuer level and not the issuer slope. `g` is a maturity function fitted by leverage tercile and date. `late_rank` is the bond's place in the issuer ladder. `phi` comes from same-firm bond pairs with similar maturity, by rating group and regime (Dick-Nielsen et al., Table 7, p. 16, Our choice, v0). Use one seniority per issuer. Use maturity to worst where `bond_terms` exists, because most HY bonds may be callable.

This arm decides nothing, for three reasons:

1. A positive `theta_o` can be de facto seniority. Section 7.4 says that spreads inside one issuer pay for the recovery gap. Bao and Hou (2017) may test this, by its title, and it stays unopened.
2. If short `T` goes with weak credit, an inverted curve can give a negative `theta_o` with no fact on pricing.
3. `T` mostly reads disclosure format, as Method 1 shows.

Add a placebo: draw `t50` from other issuers in the sector, 1,000 draws. Add an event arm: when filed `t50` jumps, compare spread changes of bonds between old and new `t50` with other bonds of the same issuer.

**Arm C.** Rerun arm A with log `cds_5y` as the outcome. Run arm A and arm C on the same issuers. Report the issuer count.

**Arm D.** Rerun arm A with interactive fixed effects (Chen, Polselli, and Clarke). This arm is report only, with no conclusion. The large-sample rate needs `T log^2 T = o(N)`. At T = 99 and N = 187, `T log^2 T` is about 2,090 with the natural log (our arithmetic). So the condition does not look close to met on this panel. The Mundlak term in arm A serves the same purpose.

**Data rules that come before any read.**

1. Gap. Use the skip-month form first, because it needs no new panel (`scripts/backtest_alpha.py`). Then put at least 8 calendar days between the price in a signal and the first price in a return (Bartram et al., p. 11). Report a 1-business-day gap beside it (Dickerson et al. 2026, p. 15). A plain share has no price in it, but a test "beyond spread" does.
2. Measure the shared-price bias: `lib_bias = w_t (r^End_{t+1} - r^Bgn_{t+1})` (Dickerson et al. 2026, eq. 5). `realised_excess_return` divides by the price that supplies `g_spread`. A skip-month test on file shows this bias in the peer gap (`2026-10-23-peer-fair-spread`). The 8-day gap and OneScore are not measured.
3. Filter returns only with data through the formation month.
4. Report each result over a path grid: weight, sort coarseness, rating class, maturity bucket, hedge, and cost case. Report the non-standard error and its ratio to the standard error. A result that flips sign over the grid does not count (Our choice, v0).
5. Control the false-discovery rate at 5% with Benjamini-Hochberg over the frozen family (Our choice, v0).
6. Report each clock slope with and without leverage, with and without rating dummies, and with and without spread level. After February 2017 rating and leverage are one variable, so that report holds no separate rating row without a feed. A feature that changes sign when leverage enters reads as a leverage proxy (Friewald et al. card).
7. Place 1 over EBITDAR in place of each amount as a placebo. A shared denominator can build a link among `amt_*`, `lev_lease_adj`, and spread. Add a twin scale on LTM revenue, and use the rank form in tests.

**Inputs.**

| Input | Contract field | `as_of` | `available_at` | Status |
| --- | --- | --- | --- | --- |
| Spread, maturity, duration | 3.14 `bond_panel` `g_spread`, `years`, `mod_dur` | Month end | Panel column, TRACE next day | have |
| Cost and activity | 3.14 `bond_panel` `bid_ask_pts`, `n_trades`, `par_volume`, `last_trade` | Month end | Panel column | have |
| First price of next month | `bond_daily` (`PRODUCTION_DATA` section 3) | Trade day | Trade day + 1 | need |
| Trades for `lambda` | `trace_trades` `cusip`, `trade_time`, `price`, `par` | Trade time | Panel column, with the load lag of the F05 spec | need |
| Leverage, debt | 3.14 `leverage` | `date` | Panel column | have |
| `lev_ex_lease`, `lev_lease_adj` | Panel debt less the XBRL operating lease liability after adoption, over EBITDA. Framework F8 form for the second: balance-sheet liability after 2018, 8 times rent before. Do not add 8 times rent to panel debt after adoption | Quarter end | Later of the inputs | have the parts, need them in the panel |
| Rating class | 3.14 `ratings` | `datadate` | Panel column | have to February 2017. After it the class is a leverage cell. A rating feed is need |
| Sector | 3.14 `gics` | `indfrom` | Panel column | have |
| Bond age, call state, seniority | `bond_terms` | Issue date | Panel column | need |
| Clock features | Method 1 outputs | Balance-sheet date | Filing acceptance time | need |
| CDS spread | `cds_5y`, Section 3.1, not in the contract | Quote date | Quote date + 1 | need |
| `wall_cover_4`, `coverage`, `ltv`, `margin_trend` | Run-level fields of `hy.state` | Filing | Filing | need at panel level. List which fields enter `X` in the output |

**Outputs.** `theta`, `theta_ci`, `theta_by_learner`, `theta_within`, `ar1_slope`, `perm_pct`, `mde`, `outcome`, `partial_r2`, `v_var`, `ell_fit`, `m_fit`, `x_fields`, `theta_overlap`, `n_straddle_issuers`, `phi_pairs`, `theta_cds`, `n_cds_issuers`, `theta_ife`, `lib_bias`, `ic_gapped`, `nse`, `nse_ratio`, `bh_pass`.

**Claims and tests.**

| Test | Claim | Pass | Fail | Untestable |
| --- | --- | --- | --- | --- |
| M2.1 Firm strength | The -2.07 reflects traits of the issuer | With `X` in, the 90% interval of the slope on the old recontract share has a lower bound above -1.035. That is half of the on-file size (Our choice, v0) | Upper bound below 0 and lower bound at or below -1.035, under lasso. The sign is then a fact about the market, and the Section 4.7 reason fails | Lower bound at or below -1.035 and upper bound at or above 0. Also `v_var` below 10% of `var(c)` (Our choice, v0), or no rating feed |
| M2.2 Explanation | A clock feature explains the residual beyond the panel-level `X` | Fold-scored `partial_r2` of at least 1 percentage point, above the 95th percentile of the permutation null, with the declared sign. The declared sign and permutation p below 0.10 hold in at least 3 of 4 windows (Our choice, v0). RPO features need both of their windows. The list includes `coverage_contracted`, `max_cum_shortfall`, and `breakeven_margin` | Below either bar. The feature leaves the forward block of Section 7.2 | `mde` above the size of interest |
| M2.3 Inside one issuer | The market may price the renewal bet along the curve | Exploratory. Report `theta_o` against the `t50` placebo | This test has no fail outcome. A negative or a positive `theta_o` has rival readings | Fewer than 30 issuers with bonds on both sides of `t50` in the median month (Our choice, v0) |
| M2.4 CDS sign | The sign is a credit fact, not a bond liquidity effect | Same issuers. Same sign, and the difference between arm A and arm C has absolute t below 1 (Our choice, v0) | The sign vanishes in CDS. It then sits in the bond-only part | Below 30 CDS issuers (Our choice, v0) |
| M2.5 Signal bar | A clock feature ranks returns beyond spread | The signal bar of rule 4, gapped, past Benjamini-Hochberg | Otherwise zero signal weight | A window with no data counts as a fail, as `cycle_test` does |
| M2.6 Common shocks | Report only | Arm D keeps the sign and at least half of the size (Our choice, v0). No conclusion follows | No conclusion follows | Report only |
| M2.7 Shared price | On-file peer results survive the gap | Gapped ESP and OneScore keep their on-file bars at 3, 6, and 12 months. 6 months is primary, as the process horizon | OneScore no longer passes 3 of 4 windows. Then `2026-10-22-onescore` reopens | The first price of next month is absent |

At the on-file standard error of 0.86, the 90% half-width is 1.41, wider than the bound of 1.035 (our arithmetic). So M2.1 can read untestable on this panel, and this page says so before any run. That standard error may also be too small.

**Overlap.**

- E5: this tests `fixed_charge_years` by the same rules.
- E8 and F21: `wall_cover_4` enters `X` only after a panel build (Follow-up 3). Until then a clock feature does not add beyond it by test, and the output says so.
- S1: `ell` is a research stand-in for `f_t`. It does not replace it.
- S4, F06, F22: all three read the issuer curve. Report the rank correlation of `clock_overlap` with the F06 residual and the F22 slope. If either is above 0.5 in absolute value (Our choice, v0), `clock_overlap` is a label on those factors.
- Conviction book: no change.

**Source cards.** `chernozhukov-et-al-2018-double-machine-learning`, `feng-giglio-xiu-2020-taming-factor-zoo`, `chen-polselli-clarke-2026-panel-dml-interactive-fixed-effects`, `fuhr-papies-2024-panel-dml`, `petersen-2005-panel-standard-errors`, `dickerson-robotti-rossetti-2026-bond-factor-replication-crisis`, `bartram-grinblatt-nozawa-2025-bond-book-to-market-mispricing`, `mamaysky-shen-wu-2026-credit-information-earnings-calls`, `dick-nielsen-feldhutter-lando-2012-corporate-bond-liquidity`, `feldhutter-schaefer-2023-debt-dynamics-credit-risk`, `longstaff-mithal-neis-2005-default-liquidity-cds`, `friewald-nagler-wagner-2022-refinancing-equity-returns`, `bai-wu-2016-anchoring-cds-fundamentals`, `chen-xu-yang-2021-systematic-risk-maturity`.

---

### Method 3. Explain the residual in layers, then classify what is left

Answers: how to better explain the idiosyncratic residual. This method works on a peer gap, because no method here fits `f_t`. So it explains a cell-relative gap, and not a residual from fundamentals. The report states this limit.

**Assumptions.**

1. As built, `eps` is the peer gap: log spread less log peer median in a sector, class, and maturity cell. Cell means sit near 0 by construction. So the cohort step and M3.1 do not apply to the peer gap, except for bonds on a fallback cell. They apply when `f_t` exists.
2. When `f_t` exists, sector-by-date effects may not remove a common mode whose loading differs across ratings (He et al., pp. 45-46). That evidence is on spread changes.
3. In liquid investment grade bonds, reversal ends after a few trades and within a day (Bao et al., pp. 24, 47, 55). No opened source tests this in HY. So a one-week skip is Our choice, v0, and lag decay by rating needs a measure before the skip length is fixed.
4. Risk and liquidity premia move slowly. Bartram et al. argue this and do not test it directly (p. 23).
5. The long-run split needs a sample that covers several credit cycles (Nozawa, p. 65). The RPO panel does not meet this condition.

**Formula.**

```latex
\varepsilon_{b,t} = \mathbf{1}[f_t\ \text{fitted}]\,c_{g(b),t} + \bar\phi_{g,w,t}\,\lambda_{b,t} + \psi_t' x^{fwd}_{i,t} + \nu_{b,t}, \qquad \lambda_{b,t} = \sum_{j=1}^{4}\frac{L^{j}_{b,t} - \mu^{j}_{t}}{\sigma^{j}_{t}}
```

Intuition: take out the pay for trade friction, then forward facts, and take out what a cohort shares once a fitted model exists. What stays is a candidate for mispricing. `g` is one of 12 cohorts: the 4 classes of `hy.peers.CLASSES` by 3 maturity groups. `L` holds Amihud, imputed roundtrip cost, and the daily standard deviation of each. `mu`, `sigma`, and `phi` use expanding windows, so `lambda` stays point in time. The source uses full-sample values (Dick-Nielsen et al., p. 19).

Rules for `x^fwd`:

1. A feature enters only after it passes M2.2 on data to that date.
2. For M3.3, freeze `x^fwd` to fields in all four windows. Test RPO fields apart from 2018.
3. A NaN carries a flag. The Bai and Wu route (eqs. 9-10) can fill it, as its card says.

```latex
\text{pc1\_share} = \frac{\varphi_1}{\sum_{j=1}^{12}\varphi_j} \ \text{ of } \operatorname{Corr}\big(\overline{\Delta\nu}_{g}\big) \ \text{ on held-out issuers}, \qquad \text{pc1\_excess} = \text{pc1\_share} - Q_{0.95}\big(\text{pc1\_share}\mid \text{months shuffled per cohort}\big)
```

Intuition: a truly idiosyncratic residual has no strong common mode across rating and maturity groups, so read the first component against its noise level. Fit `c` on a random half of issuers, and read the share on the other half. A covariance form fails here. In our simulation of independent noise, 12 cohorts, and 99 months, it reads 14%, then 76% with one thin cell at 6 times the standard deviation. The correlation form reads 13.5% in both cases, with a 95th percentile near 15% (`analysis/sensitivity/close/pc1_check.py` in the track folder).

```latex
X_{b,t+1} = A X_{b,t} + B W_{b,t+1}, \qquad X_{b,t} = \big[r^{e}_{b,t},\ s^{fit}_{b,t},\ \nu^{P}_{b,t},\ D_{b,t} x_{b,t}\big]', \qquad b^{l}_{x} + b^{r}_{x} = 0
```

Intuition: a wide spread must pay back later as return or as loss. So a state beyond spread can forecast return only through an equal and opposite loss. `s` is the price spread against a Treasury twin (Nozawa, pp. 11, 18-19).

**Classifier.** Run these five rows on the signal that S1 keeps, and on each clock feature (Bartram et al., pp. 19-27). Row thresholds are Our choice, v0.

| Row | Votes for mispricing | Votes for risk or unmodelled fact | Votes for liquidity | No vote |
| --- | --- | --- | --- | --- |
| 1. IC at delay 2 months over IC at delay 0, against survival of the quintile | Ratio below 0.5, survival above 0.8, no reversal | Ratio at or above 0.5 | Ratio below 0.5, with a reversal after the skip | IC at delay 0 has permutation p at or above 0.05, or ratio below 0.5, survival at or below 0.8, no reversal |
| 2. Interaction with the worst 20% of default risk | Flat | Stronger in the worst group | Flat | Neither flat nor stronger |
| 3. Interaction with the worst 20% of `lambda` | Flat | Flat | Stronger in the worst group | Neither flat nor stronger |
| 4. Same-firm equity return, listed issuers | No effect | Same sign | No effect | Neither, or the row is absent |
| 5. Alpha against the yield gap | Lower bound of the 90% interval above the gap | Upper bound at or below the gap | Upper bound at or below the gap | The interval holds the gap |

Definitions:

1. Flat, or no effect, means that the 90% interval of the interaction sits inside a bound fixed before the run. The bound is half of the main slope (Our choice, v0). A failed rejection is not a flat vote.
2. Stronger, or same sign, means that the interval lies above 0 in the direction of the main slope and outside the bound.
3. A column needs at least 3 votes.
4. Mispricing also needs votes from rows 1 and 5, and no row may vote against it. A stronger vote on row 2 or 3, or a same-sign vote on row 4, is a vote against.
5. A tie among eligible columns reads `unresolved`. So does a case with no eligible column.

We enumerated all 324 row outcomes (`analysis/sensitivity/close/classifier_enum.py` in the track folder). Mispricing takes 7, risk 54, liquidity 54, and `unresolved` 209. Three flat rows alone read `unresolved`. So a noisy panel no longer reads as mispricing by default. Row 4 covers listed issuers only, 52% of bond-months from 2016 (`2026-10-22-onescore`). So report listed and private issuers apart.

**Inputs.**

| Input | Contract field | `as_of` | `available_at` | Status |
| --- | --- | --- | --- | --- |
| Residual history | `s1_residual` (`PRODUCTION_DATA` section 5), plus `eps` and the cell used | Month end | Panel column | need |
| Spread, rating, sector, duration | 3.14 `bond_panel`, `ratings`, `gics` | Month end, `datadate`, `indfrom` | Panel columns | have, with the class limit of context fact 8 |
| `lambda` parts | `trace_trades` | Trade time | Panel column, with the load lag of the F05 spec | need |
| Daily spreads for the skip | `bond_daily` `g_spread` | Trade day | Trade day + 1 | need |
| Forward block | Method 1 outputs | Balance-sheet date | Filing acceptance time | need |
| Same-firm equity return | 3.14 `equity_monthly` `ret` | `datadate` | Panel column | have, listed issuers only |
| Default risk group | `pd_12m` of Section 7.6, or distance to default from F02 inputs | Filing, trade day | Latest input | need. A rating class fallback is a leverage cell after February 2017 |
| Distress state | 3.12 `distress` | Market date | Record `available_at` | have, a stand-in for the intermediary distress of He et al. |
| Dealer inventory | `macro_series`, NY Fed primary dealer positions | Report date | Release date | need |
| Default list, recovery | Default list of `PRODUCTION_DATA` section 2 | Default date | Panel column | need |

**Outputs.** `resid_clean` (`nu`), `resid_var_explained`, `pc1_share`, `pc1_excess`, `partial_r2_cohort`, `partial_r2_liq`, `partial_r2_fwd`, `lambda_b`, `z_skip`, `ic_delay`, `lag_decay_by_class`, `quintile_survival`, `class_votes`, `resid_class`, `resid_class_listed`, `loss_coef`, `return_coef`, `return_share`, `return_share_spread`, `rho_state`. `resid_var_explained` is the total share of residual variance that the layers explain, on held-out issuers. `resid_class` is a run-level field, and a bond-level rule reads it.

**Claims and tests.**

| Test | Claim | Pass | Fail | Untestable |
| --- | --- | --- | --- | --- |
| M3.1 Common mode | The cohort step removes the common part, when `f_t` exists | `pc1_excess` below 10 points (Our choice, v0). The source reports 81.7% for structural residuals | At or above 10 points. `f_t` then needs loadings on the distress and inventory factors | Not applicable on the peer gap |
| M3.2 Explanation | Each layer explains the gap beyond the panel-level `X` | Each layer adds at least 1 percentage point of fold-scored partial R-squared, above the permutation null (Our choice, v0). Report `resid_var_explained`. A rating row needs a feed | The layer leaves the ladder | The cohort layer on the peer gap |
| M3.3 Signal quality | The cleaned gap ranks returns at least as well as the raw gap | On common rows, at 6 months with a skip, `resid_clean` has a rank IC beyond spread after costs at or above that of `eps`. The difference has t above -1 (Our choice, v0). The IC is positive in at least 3 of 4 cycles. Report 3 and 12 months beside it. On file, `eps` with a skip passes 2 of 4 at 6 months | Otherwise keep `eps`, and run the classifier on `eps`. If `eps` also fails the bar, S1 carries no mispricing label. If liquidity pays, `nu` loses IC by construction, so read this with F13 | The first price of next month is absent |
| M3.4 Classifier | S1 holds mispricing | `resid_class` reads mispricing | `resid_class` reads risk or liquidity. S1 keeps its place only with the label "premium trade" or "unmodelled fact". A fail changes no weight by itself. It puts the overlap below before the user | `resid_class` reads `unresolved`. S1 carries no mispricing label. A synthetic pure-noise residual must read `unresolved` |
| M3.5 Pair | The gap is return and not missed loss | `return_share` by rating group is at or above the same statistic for the whole spread on our panel (Our choice, v0). Report only, unless the sample covers all four windows | Below it. The gap may then be expected loss that the fair spread missed | Under one cycle of data |
| M3.6 Friction | The gap survives a week | The fall in IC beyond spread from month-end to skip form is below half of the month-end IC (Our choice, v0). The skip-window gap change does not forecast later return with the opposite sign | Above half. The gap then reads as friction | `bond_daily` is absent |
| M3.7 Speed by state | Convergence slows in stress | `rho` rises with the quartile of distress and of inventory, and the top against bottom difference clears a block bootstrap at 5% | Flat `rho`. The phase band then gets no such state | By `mde`, rule 7 |

**Overlap.**

- S1: this method changes its entry rule and its label. The peer fair spread feeds E1, E2, E10, the gate, and the pair (`2026-10-23-peer-fair-spread`). E14 and E16 share the same price and the same cell. `hy.groups.effective_weights()` gives E1 5.2%, E2 0.7%, E10 10%, E14 4.5%, E16 4.5%, near 25% of the score. So a label change alone leaves that gap in the score. Each takes the same gap rule.
- F13 treats illiquidity as a long signal. This method takes it out of S1. Both can hold, because the pay then sits in the F13 family and not in S1.
- F24 reads rating and tenor cells against their own history. This method removes the cell mean, so the two do not repeat each other.
- Conviction book: layer 3 rule 2 reads the S1 band. It would also read `resid_class`. The S1 member of the Value family stays.
- E5, E8, and F21: no overlap. A clock amount enters the forward block only after M2.2 admits it, and `wall_cover_4` follows the same rule.

**Source cards.** `he-khorrami-song-2022-commonality-credit-spread-changes`, `dick-nielsen-feldhutter-lando-2012-corporate-bond-liquidity`, `bao-pan-wang-2011-bond-illiquidity-gamma`, `bartram-grinblatt-nozawa-2025-bond-book-to-market-mispricing`, `nozawa-2017-credit-spread-variance-decomposition`, `dickerson-robotti-rossetti-2026-bond-factor-replication-crisis`, `feldhutter-schaefer-2018-credit-spread-puzzle`, `kelly-palhares-pruitt-2023-modeling-corporate-bond-returns`, `longstaff-mithal-neis-2005-default-liquidity-cds`, `bretscher-schmid-sen-sharma-2022-institutional-bond-pricing`.

---

### Method 4. Read clock risk through the market state

Answers: when clock risk enters prices, and whether the clocks are a risk measure at all.

**Assumptions.**

1. Old maturity dates are plausibly exogenous to a later shock (Nagler, p. 20, Almeida et al. 2009, p. 4). Firms do manage profiles (Choi et al., p. 24), and bonds prepay at about 8.6% a year in a global sample (SR 1139, p. 15). So the test shows the decay with filing age. Issuers that move debt early may leave a due share that is sparse and selected, so what stays due may be what could not move.
2. Sector-by-date effects absorb the market level and the sector shock. Only differences inside a sector identify the slopes.
3. Long debt goes with high asset beta (Chen et al., pp. 5-6). So `Z` holds the state times rating, leverage, and a beta to the HY index. `Z` also holds the state times the other panel-level fields.
4. Sources support a liquidity state for the debt term (Nagler, pp. 33, 60, Valenzuela, p. 34). Those samples are near BBB or non-US. Other states are our extension.
5. Rent does not roll in a capital market. So the lease term reads a demand state, with no prior sign. This is our extension. Dogan's equity premium in contraction fits a demand reading (pp. 586-587).
6. Log spread is the right unit for spreads up to 400 bp (Ben Dor et al., p. 14). B in stress and CCC stay unverified, because single-B spreads moved from 335 bp to 1,189 bp in 2020 (methodology Section 9.2).

**Formula, panel.**

```latex
\Delta\log s_{b,t} = a_b + g_{sec(i),t} + \beta_1 \Delta MS_t\,Due^{debt}_{i,t-1} + \beta_2 \Delta DS_{sec(i),t}\,Due^{lease}_{i,t-1} + \beta_4 \Delta MS_t\,(-\sigma^{debt}_{i,t-1}) + \gamma' Z_{b,t} + e_{b,t}
```

Intuition: a due debt amount matters when the market state makes it expensive to replace, and due rent matters when demand falls. `Due^debt` is principal due in 12 months over total debt, in a bond-only form and an all-debt form. `Due^lease` is rent due in 12 months over EBITDAR.

States:

1. `MS` is the median `lambda` across bonds, with the issuer's own bonds left out. The opened sources support a liquidity state. A median without the issuer removes the direct link.
2. `MS_check` is a state not built from panel trades or spreads: monthly HY new-issue par over par outstanding, from `bond_terms` issue dates, and `sloos_tightening`. A pass needs the same sign under both states.
3. `DS` is a `gdp_growth` forecast by vintage, or sector revenue change.
4. Report `distress`, NY Fed dealer positions, and `gcc_us` as arms. `gcc_us` and `distress` are built from spreads in this panel, so they carry the label "built from the outcome". Compute `Delta MS` inside one vintage.

Drop bonds with under 12 months to maturity from all outcomes, because a bond due in 12 months can sit in its own numerator. Report the mass at zero per cell. Add a 24-month HY arm of `Due^debt` (Our choice, v0). Add the share callable within 12 months when `bond_terms` exists.

**The RPO term is out.** The earlier form held `Uncov^RPO`, which is `max(0, 1 - RPO_12m / Rev^LTM)`. RPO can exclude short contracts, and that term then reads near 1 for a firm with short contracts out of scope. So it can read sector. It stays out until `rpo_scope_flag` exists. Undisclosed RPO is NaN, as Section 4.7 does for customer shares.

**Formula, stale ladders.**

```latex
\Delta\log s_{b,w} = a_{sec(i),w} + b\,Treat_{i,w-L} + \gamma' X_{i,w-L} + e_{b,w}, \qquad L \in \{1, 2, 3\}\ \text{years}
```

Intuition: a ladder set years before a shock cannot respond to the shock. Treat is a due share above 10%, 15%, or 20%, as in Nagler (p. 27). The 12-month age of the filing is Our choice, v0. Match on rating class, `lambda`, and leverage. Read two windows: month 0 to 6 and month 7 to 36 (Our choice, v0).

Shock months are named before the run (Our choice, v0). They are September 2008 (Lehman), December 2015 (Third Avenue, SR 1094, p. 62), and March 2020. No opened source names a 2022 credit event, so 2022 reads untestable until the user names one. The rule of Boyarchenko and Elias (p. 26) needs later data, because it asks whether the factor reaches the top quintile during the episode. So that rule feeds no live score, and it serves only as a report after the fact.

**Formula, forward risk.**

```latex
\log Y_{i,t+12} = a_{sec(i),t} + \kappa\,c_{i,t} + \gamma' Z_{i,t} + e_{i,t+12}, \qquad Y \in \{\text{sv\_12m},\ \text{max\_widen\_1m},\ \text{max\_widen\_12m}\}, \qquad c \in \{amt\_debt\_near,\ amt\_lease\_near,\ fixed\_charge\_years,\ sigma\_debt\}
```

Intuition: a risk measure must forecast risk after spread level and leverage. Read targets in logs, because spread risk targets in bp rise with spread level. The targets follow Mamaysky et al. (Table 8, p. 53). Add `Delta log Lev` (Feldhütter and Schaefer 2023, p. 3, note 3) and `default_24m`, with the F21 rule of 0.02 out-of-sample AUC gain.

**Inputs.**

| Input | Contract field | `as_of` | `available_at` | Status |
| --- | --- | --- | --- | --- |
| Debt, lease ladders | 3.5 `ladders` | Balance-sheet date | EDGAR acceptance time | have, with the lease limit of context fact 5 |
| Stale ladders for 2015 | XBRL ladders by filing date | Balance-sheet date | EDGAR acceptance time | have |
| Stale ladders for 2008 | `compustat_annual` `dd1` to `dd5`, `dltt`, new `mrc1` to `mrc5` | `datadate` | 10-K acceptance time, with `datadate` + 90 days as a floor | need, research only |
| Log spread, trades | 3.14 `bond_panel` | Month end | Panel column | have from 2010, need from 2004 |
| Rating, sector, leverage | 3.14 `ratings`, `gics`, `leverage` | Panel dates | Panel columns | have, with the class limit of context fact 8 |
| Issue dates, call dates | `bond_terms` | Issue date | Panel column | need |
| Bank lending survey | `macro_series` `DRTSCILM`, `hy.macro` `sloos_tightening` | Quarter | Release date | need in the panel |
| Dealer positions | `macro_series`, NY Fed | Report date | Release date | need |
| Demand state | 3.13 `gdp_growth` forecast rows, or sector revenue from 3.3 | Vintage | Vintage `available_at` | have the forecast source, need the panel |
| Distress state | 3.12 `distress` | Market date | Record `available_at` | have, built from the outcome |
| `gcc_us` vintage | Method 6 output | Vintage date | Vintage `available_at` | need |
| Median `lambda` | Method 3 | Month end | Latest trade input | need |
| Daily spreads for `sv_12m` | `bond_daily` | Trade day | Trade day + 1 | need |

**Outputs.** `due_debt_12m` (the same field as `rollover_rate_12m`), `due_debt_12m_bond`, `due_debt_24m`, `callable_12m`, `due_lease_12m`, `beta_due_debt`, `beta_due_debt_check`, `beta_due_lease`, `beta_sigma_debt`, `partial_r2_due`, `mass_zero_by_cell`, `event_b_w1`, `event_b_w2`, `stale_decay`, `placebo_t`, `kappa_sv`, `kappa_widen_1m`, `kappa_widen_12m`, `kappa_lev`, `auc_gain_default`.

**Claims and tests.**

| Test | Claim | Pass | Fail | Untestable |
| --- | --- | --- | --- | --- |
| M4.1 Debt | The debt clock acts through the market state | `beta_due_debt` is above 0, with permutation p below 0.05. Sign and permutation p below 0.10 hold in at least 3 of 4 windows. The sign holds under `MS_check`, and when the share is the pre-window issuer mean. Its partial R-squared beyond `Z` is at least 1 percentage point (Our choice, v0). Nagler reports a rise from 36% to 38% on spread changes (pp. 36-37) | Below that bar. The debt clock is then not a conditioning variable on our panel | `mde` above the size of interest, or mass at zero above 80% in the median cell (Our choice, v0) |
| M4.2 Lease | Rent acts through demand | `beta_due_lease` has the same sign in at least 3 of 4 windows, read by regime, with permutation p below 0.05 | Otherwise the term leaves the panel. This is our extension | The lease regime leaves fewer than 3 windows |
| M4.3 Stale ladders | The effect comes from old dates | The primary cell is 15%, L = 2, matched (Our choice, v0). `b` above 0 with permutation p below 0.05 in every window with a named shock, and at least 3 windows. Placebo months: the 90% interval sits inside half of the stress `b`. Other cells go to a report grid. Report `stale_decay`, because a `b` that vanishes at L = 3 may reflect firm quality (Chen et al., p. 42) | `b` at or below 0, or the placebo fails | A window with no named event |
| M4.4 Two windows | Short and long debt carry risk at different dates | Short remaining maturity widens more by month 6, and long remaining maturity stays wider at month 24, in 2008 and 2020. The 2020 read ends at December 2021, because month 24 sits inside the 2022 window | Otherwise report one window. The source is equity evidence, so this is a prior only | By `mde`, rule 7 |
| M4.5 Risk measure | The clocks forecast risk | At least one `kappa` on a spread risk target clears Benjamini-Hochberg over the list of `c` and the targets, or `auc_gain_default` is at least 0.02. Report the fall in 1-year leverage residual volatility, with a pass at 1 percentage point (Our choice, v0) | None passes. The phrase "risk measures" in Section 4.7 then has no support, and the Two clocks bucket rests on the user's view alone | Few defaults for the AUC leg |
| M4.6 Dispersion | A lumpy debt clock adds risk | `beta_sigma_debt` above 0 in at least 3 of 4 windows, after size, leverage, and `due_debt_12m` | Otherwise drop it. One-instrument issuers count as uninformative | By `mde`, rule 7 |

**Overlap.**

- E5: this method tests a due amount through a state. E5 is a level score with a long sign. The two can disagree.
- E8 and F21: both hold a near wall against liquidity and give a level. This method has no cash term and gives a response. Report the absolute rank correlation of `due_debt_12m` with `wall_cover_4`.
- Framework S9 and the wall limit of Section 9.4 read the same dates. A pass gives them a state-dependent size.
- S1: a pass tells the memo when a wide S1 gap may hold rollover stress.
- Conviction book: test T2 and the warning flags stay. A pass adds a clock line to each thesis tracker row.

**Source cards.** `nagler-2020-bond-rollover-channel`, `valenzuela-2016-rollover-spreads`, `augustin-cong-corhay-weber-2026-price-rigidities-credit`, `he-xiong-2012-rollover-risk-credit-risk`, `almeida-campello-laranjeira-weisbenner-2009-debt-maturity-credit-crisis`, `chen-xu-yang-2021-systematic-risk-maturity`, `chaderina-weiss-zechner-2022-maturity-premium`, `coyle-2025-maturity-walls`, `mamaysky-shen-wu-2026-credit-information-earnings-calls`, `feldhutter-schaefer-2023-debt-dynamics-credit-risk`, `he-khorrami-song-2022-commonality-credit-spread-changes`, `ben-dor-et-al-2007-dts`, `dogan-2016-operating-leases-operating-leverage`, `boyarchenko-elias-2024-debt-structure-cycle`.

---

### Method 5. Measure where clock risk pays, net of cost

Answers: where to take risk. This answer stays partial. Protocol theme 3 names bonds, rating cells, sectors, tenors, and capital structure positions. This method reads pooled HY first, then cells and sectors as a report. It cannot read secured against unsecured until `bond_terms` exists.

**Assumptions.**

1. DTS is the unit of spread risk (Ben Dor et al., p. 19). The linear fit is shown up to 400 bp. B in stress and CCC stay unverified.
2. Whether debt due soon earns compensation is open. The only bond evidence is a conference draft with a median rating of A-, and its table cannot separate compensation from mispricing. So this is a claim to test in high yield.
3. The exposure moves slowly. The source gives a hurdle near 0.08% a month at 29% monthly turnover for the Investment class (Dickerson et al. 2025, Table 4, p. 59). That figure pools IG and HY, so it needs a high yield update.
4. A report by cell is not a signal. It says where the book may be paid to carry a risk that it already wants inside the DTS band.
5. The scored universe is `not_distressed` at formation, as on file. A distressed-in arm reports apart, because carry books with distressed bonds earn 13 to 14% a year with drawdowns of -43% to -51% on file.

**Formula.**

```latex
RI_{i,t} = \frac{\sum_{\tau \le 3} D_{i,t,\tau}}{\sum_{\tau} D_{i,t,\tau}}, \qquad w_{b,t} = \frac{1}{n_{leg}\,DTS_{b,t}}, \qquad \pi^{x}_{t+h} = \sum_{b \in H_{x}} w_{b,t}\, r^{DTS}_{b,t+h} - \sum_{b \in L_{x}} w_{b,t}\, r^{DTS}_{b,t+h} - C_{t}
```

Intuition: measure what a book earns at equal spread risk from issuers with more clock exposure, then take off the cost to get there. Each leg then has a DTS of 1. Weights proportional to `1/DTS` that sum to one per leg leave a leg at the harmonic mean. DTS of 200 and 800 gives 320, and DTS of 400 and 400 gives 400. So the first form kept net DTS exposure. `x` is `refi_intensity_3y` (the `RI` above), `amt_lease_near`, or `fixed_charge_years`. `H` and `L` are top and bottom terciles. `DTS` is floored at the 5th percentile of the month (Our choice, v0). `r^DTS` is `hy.backtest.dts_realised`, gapped as in Method 2. Report beta = 1 beside it, because the hedge flips the on-file result for spread level.

```latex
C_{t} = 2\,TO_{t}\,h_{t} + C^{Delay}(TO_{t},\ g_{t}), \qquad \Pr(\text{trade in a month}) = 1 - e^{-21\lambda_{c}}
```

Intuition: the cost is half the bid-ask on each trade plus the gross return lost while a late order waits (Dickerson et al. 2025, eqs. 6, 7, 8). `TO` follows eq. 7: the sum of absolute weight changes per leg, from 0 to 200%, averaged across the long and short legs (p. 18, note 14). `h` is the half spread. Read `C^Delay` from Table 2 Panel B3 of that source for a $2 million trade (p. 57), which fixes `lambda` at the source's estimate. To use a fitted `lambda_c`, rerun the source simulation at it. Fit `lambda_c` by class on a trade dummy from `trace_trades`, with a par floor and a bond-life calendar from `bond_terms`. `n_trades` cannot supply the dummy, because a row exists only if the bond traded (`hy/sources/trace_panel.py` rules 2, 3, 5).

**Primary test.** One pooled test: HY high minus low on `RI` at 12 months, on admissible names (Our choice, v0). The source premium is 0.10% a month (t 2.18) across 7,812 bonds. If that effect holds in nine cells with equal variance, each t sits near 0.73 (our arithmetic). The first Benjamini-Hochberg bar at 54 tests is about t 3.3. So a cell-level pass rule would read no location even if a premium exists.

**Report, with no pass.** Cells of class by 1 to 3, 3 to 7, and over 7 years, and GICS sectors, with empirical Bayes shrinkage. Report the mass of each cell. Add a secured against unsecured cut once `bond_terms` exists. Compute `pi_net` after the layer 3 flags of the conviction book, and report the gap to the full-universe premium. Report the clock coverage share of the bond panel by window and cell, and label results "SEC filers only" where that holds.

**Rule that turns the report into a position (Our choice, v0).** Inside the band, cap DTS at the index share in a cell with `carry_ok` false. Allow up to 1.25 times the index share in a cell with `carry_ok` true. Test the rule in the shadow book comparison. Until M5.1 passes, `carry_ok` is false everywhere.

**Inputs.**

| Input | Contract field | `as_of` | `available_at` | Status |
| --- | --- | --- | --- | --- |
| Debt ladder | 3.5 `ladders["debt"]` | Balance-sheet date | EDGAR acceptance time | have |
| Ladder before XBRL | `compustat_annual` `dd1` to `dd3`, `dltt` | `datadate` | 10-K acceptance time, with `datadate` + 90 days as a floor | need, research only |
| Lease and charge amounts | Method 1 `amt_lease_near`, `clock_facts` `fixed_charge_years` | Balance-sheet date | Filing date + 1 day | need for the first, have for the second, with the lease limit of context fact 5 |
| Realised return, spread, duration, cost | 3.14 `bond_panel`, `hy.backtest.dts_realised`, `round_trip_cost`, `not_distressed` | Month end | Panel column | have |
| Trade dummy | `trace_trades`, `bond_terms` | Trade day | Trade day + 1 | need |
| Delay grid | Table 2 Panel B3 of the source, stored in `data/schemas` | Fixed | Fixed | need |
| Rating class | 3.14 `ratings` | `datadate` | Panel column | have, with the class limit of context fact 8 |
| Bond market factor, own default and liquidity factors | Own value-weighted series from `bond_panel`, `amt_out`, and `lambda` | Month end | Panel column | need `amt_out` and `lambda` |
| Layer 3 flags | Conviction book | Decision date | Decision date | need |

**Outputs.** `refi_intensity_3y`, `pi_net`, `pi_net_t`, `pi_net_perm`, `pi_net_within`, `ic_beyond_cell`, `turnover_cell`, `half_spread_cost`, `delay_cost`, `alpha_mktb`, `alpha_def_liq`, `premium_type` (alpha, compensation, beta, none), `carry_ok`, `coverage_share`, `flag_gap`.

**Claims and tests.**

| Test | Claim | Pass | Fail | Untestable |
| --- | --- | --- | --- | --- |
| M5.1 Paid exposure | US HY pays for clock exposure after cost | The primary `pi_net` above 0, permutation p below 0.05, positive in at least 3 of 4 windows. This sets `carry_ok` by shrunk cell | The primary test fails. The review then gives no location. Clock risk stays a limit, and the book gets no tilt | Under 15 issuers per leg in the median month (Our choice, v0), or no rating feed for a rating reading |
| M5.2 Our prior | The premium rises with lower rating and longer tenor | Within-issuer arm with issuer and year effects, as source eq. 4. `pi_net` rises from BB to CCC and from short to long tenor. This is our prior: the draft has an interaction with a HY dummy and no BB to CCC result | The pattern fails. Do not cite the draft for location | The rating feed is absent |
| M5.3 Hurdle | The premium is more than factor exposure | `alpha_def_liq`, on `mktb` and own default and liquidity factors, has t above 2. Then `premium_type` reads alpha. Read bias-adjusted Sharpe and GLS as in Dickerson et al. 2023 | Alpha fails, and loadings are positive: `premium_type` reads compensation. Otherwise beta or none | `amt_out` or `lambda` is absent |
| M5.4 Signal bar | The exposure can be a score | Rank IC of `refi_intensity_3y` beyond spread after costs positive in at least 3 of 4 cycles in the B and CCC cells | Otherwise it stays a risk report beside the book | The rating feed is absent |
| M5.5 Cost model | Cost does not decide the answer | The sign of the primary test holds under three arms: 15 bp, the TRACE proxy, and proxy plus delay | The sign changes. Report all, and read the higher cost. On file, at the TRACE proxy almost every book loses | By `mde`, rule 7 |

**Overlap.**

- E5 reads the same total with the opposite sign. E5 stays as set. The report shows the size of that conflict.
- E8 and F21: `RI` is a ratio with no cash term and a 3-year window. The layer 3 flag of the conviction book stays. An issuer with `wall_cover_4` below 1 stays out, even in a paid cell. So the premium is measured on names the book may hold.
- F24 reads valuation by cell, and F10 reads carry. This method reads realised pay per unit of DTS. Report the rank correlation with each.
- S1: none.
- Conviction book: the band sets total DTS. The rule above sets location inside it. The `QUALITY-rotation` rating tilt can read `carry_ok`.

**Source cards.** `li-wang-wu-zhang-2023-refinancing-bond-returns`, `friewald-nagler-wagner-2022-refinancing-equity-returns`, `dickerson-nozawa-robotti-2025-factor-delays`, `ivashchenko-kosowski-2024-costs-capacity`, `dickerson-mueller-robotti-2023-priced-risk-corporate-bonds`, `ben-dor-et-al-2007-dts`, `nagler-2020-bond-rollover-channel`, `valenzuela-2016-rollover-spreads`, `chen-xu-yang-2021-systematic-risk-maturity`.

---

### Method 6. Set the band target from one credit state factor

Answers: when to take risk at book level.

**Assumptions.**

1. A nonlinear function of log US EBP and the VIX forecasts credit returns in the source (pp. 45, 61, Table 1, p. 43). No number from the source transfers here, because its statistic and predictor differ. In-sample global fit sits in stress windows (Table 6, p. 48). The source has no cost test.
2. The source form was chosen on data through 2024. So a 2008, 2015, or 2020 vintage with that fixed form reads the future through its form. An arm that selects the form inside each vintage removes this.
3. The signal is contrarian. High yield spreads rise by 96.6 bp at the start of a tight episode, and they stay 48.0 bp wider at month 6 (Table 7b, p. 49). A book that steps in needs liquidity in stress. Kargar et al. estimates, as converted by Dickerson et al. 2025 (p. 28, note 24), show lower trade intensity in the COVID episode. Kargar et al. stays unopened.
4. Only a direct, real-time, net comparison counts (Cederburg et al., pp. 2-3, equity evidence).
5. The odds-gap target of the conviction book stays. This factor is a rival arm, not a replacement.

**Formula.**

```latex
rx_{p,t+3} = b_p\big(\gamma_v' X_t\big) + u_{p,t+3}, \qquad X_t = \{1,\ \log EBP_t\} \otimes \{1,\ VIX_t,\ VIX_t^2\}, \qquad b_{HY} = 1
```

```latex
gcc\_us_t = \gamma_{v(t)}' X^{clip}_t, \qquad DTS^{target}_t = DTS^{lo}_t + \big(DTS^{hi}_t - DTS^{lo}_t\big)\,\operatorname{rank}_{\le t}\big(gcc\_us_t\big)
```

Intuition: credit premium and volatility together may say how much the market pays for credit risk next quarter. The target rises when pay is high, and the book walks toward it one step at a time. Rank is against the factor's own expanding history. `X^clip` clips each input to its vintage's training range. The source places the top of its VIX basis at the 90th percentile (p. 61), and a polynomial has no such limit.

Arms of the factor:

1. EBP is the first arm, because it is the source's input. Show that EBP vintages exist before this arm claims point-in-time status.
2. The HY spread replaces `log EBP` in a second arm. This is our own extension, with no source test.
3. A selected-form arm picks the form inside each vintage, from a small grid, by the same MSE rule (Our choice, v0).
4. A rival arm uses issuer quality: the high yield share of issuance from `bond_terms` issue dates (Greenwood and Hanson card). López-Salido et al. read the same share as sentiment (card on file).

Each vintage reads only data available at its date. Do not use the published series.

**Inputs.**

| Input | Contract field | `as_of` | `available_at` | Status |
| --- | --- | --- | --- | --- |
| EBP | `macro_series`, Federal Reserve Board monthly file, by vintage | Month | Release date | need, and vintages need a check |
| HY spread | 3.12 `spread` | Market date | Record `available_at` | have monthly |
| Rating portfolio returns from 2010 | 3.14 `bond_panel`, `hy.backtest` | Month end | Panel column | have |
| Index history for a 2008 vintage | `macro_series` `H0A0_XR` and rating buckets, ICE licence | Market date | Market date + 1 | need |
| VIX | `macro_series` `VIXCLS` | Market date | Market date + 1 | need |
| Issue dates, ratings at issue | `bond_terms`, rating feed | Issue date | Panel column | need |
| Band levels | Conviction book, set by the user | Decision date | Decision date | need |

**Outputs.** `gcc_us`, `gcc_vintage`, `gcc_rank`, `dts_target_gcc`, `oos_r2`, `oos_r2_source_form`, `oos_cw_t`, `oos_r2_ex_stress`, `turnover_added`, `net_excess_gcc`, `overlay_net`.

**Claims and tests.** Add arm E to the conviction book test: arm B with `dts_target_gcc` in the place of the odds-gap target. Add arm F: the `gcc_us` target inside a static band of the same width as the phase band. Decide on F against C. E against C would test the phase band and `gcc_us` together.

| Test | Claim | Pass | Fail | Untestable |
| --- | --- | --- | --- | --- |
| M6.1 Forecast | The factor forecasts HY excess return out of sample | `oos_r2 = 1 - sum(rx - fit)^2 / sum(rx - prevailing mean)^2` above 0 at 3 months, from vintages only, with a Clark-West t above 1.65 (Our choice, v0). Use the last usable return at t - 3 in each vintage. Report the source's covariance statistic beside it, and the statistic with 2008 and March 2020 removed. A fixed form reads as conditional on a later choice | At or below 0. Drop the arm | A window with no vintage reads untestable for that window |
| M6.2 Net gain | The target beats the static band after cost | Arm F beats arm C in net excess return in at least 3 of 4 windows. One-way turnover is at most 10 points a year above arm C (Our choice, v0). Raise the half spread and lower `lambda` in stress | Otherwise drop the arm. The static band stays, as test T2 of the conviction book says | Waits for band levels and arm B. A window with no vintage counts as a fail, as `hy.backtest.cycle_test` does |
| M6.3 Rival | The target beats the odds gap and issuer quality | Arm E beats arm B in at least 3 of 4 windows, and the factor beats the issuer quality arm on `oos_r2` | Otherwise keep the odds gap, if test T7 admits it | As M6.2 |
| M6.4 Linear check | Curvature earns its place | The factor beats a linear VIX line in the form of F30 | Otherwise use the linear form, with fewer parameters | By `mde`, rule 7 |
| M6.5 Overlay | The factor adds on its own, with no band | A stand-alone overlay on HY index excess return, with an index-level cost, beats a static position over all months by a block bootstrap at 5%. It also wins in at least 3 of 4 windows | Otherwise the factor stays a report. A contrarian arm trades most in stress, so the all-month read catches turnover drag in calm months | By `mde`, rule 7 |

**Overlap.**

- F30 is one linear line in VIX. F25 to F29 are index inputs to the band under their own specs. This factor targets returns with curvature and an interaction.
- The conviction playbook puts the downturn at the bottom of the band. This factor raises the target after a jump in spreads and VIX. Test M6.2 settles that conflict, with `rho_state` of Method 3 as a check.
- E5, E8, F21, S1: none. Method 4 reports `gcc_us` as an arm of its market state.

**Source cards.** `boyarchenko-elias-2024-global-credit-cycle`, `asvanunt-richardson-2017-credit-risk-premium`, `cederburg-et-al-2020-volatility-managed-real-time`, `moreira-muir-2017-volatility-managed`, `dickerson-nozawa-robotti-2025-factor-delays`, `ivashchenko-kosowski-2024-costs-capacity`, `greenwood-hanson-2013-issuer-quality-bond-returns`, `lopez-salido-stein-zakrajsek-2017-credit-market-sentiment`.

---

### Leads we leave out for now

| Lead | Why not in the six | What brings it back |
| --- | --- | --- |
| Renewal survival curve (McCarthy et al., Fader and Hardie) | It covers only issuers that disclose counts or two retention rates | M1.2 fails, and the sticky book explanation stays open |
| Re-marketability score (Gavazza), origin card item 4 | **Reopened 2026-11-02.** Kim and Kung give a score for any industry, and Benmelech and Bergman give one for aircraft. See Addendum 2, M1.15 | The trigger is met on coverage. The credit evidence stays open |
| Slotting grade, origin card item 3 | It maps `revenue_runoff`, and Method 1 shows that this field reads format | Filed windows pass M1.1 |
| Labor as a fourth class (Favilukis et al.) | **Closed by the user on 2026-11-02.** Labor is out of the clocks. `cost_elasticity` still reads total cash costs, which hold wages | A new user decision |
| Rigid prices (Augustin et al.) | It needs an `FPA` source | A licensed price measure |
| Holder demand (Bretscher et al.) | It needs a holdings feed. Gabaix et al. (2025) stays unopened | A holdings feed |
| Intra-period debt (Kallen) | It needs an implied rate test on our panel, and it has no bond outcome | M1.7 passes |
| Customer link age (Irvine et al.) | It needs a yearly panel of named customers | `customer_shares` history by filing |
| Instrument for the lease tail (Acharya et al.) | Exclusion is argued and not proved | Arm A reads untestable on M2.1 |
| Rollover part of the fair spread (Chen et al. 2017, He and Xiong) | It needs a fitted anchor, and E4 is suspended | `kappa_t` is fitted |
| Structural residual band (Feldhütter and Schaefer, Huang et al.) | Single-bond fit is low, and the level moves with the boundary | A fitted anchor, then as a rank in a bucket only |
| Fundamental stack (Bai and Wu) | CDS evidence, and bonds need a maturity map first. It stays a research arm for `f_t` | Work on `f_t` |
| Text score (Mamaysky et al.) | It needs transcripts, and the moving-window coefficient is -0.041 against -0.197 | A dated transcript panel |
| IPCA row test (Kelly et al.) | F01 has no fit on our data. No method here builds an IPCA residual, although F01 is rank 1 of the candidates | F01 runs. Then add it to Method 3 |
| Low-dimension factor timing (Haddad et al.) | Equity evidence, and no factor return history exists | 60 months of factor returns |
| Capped volatility scale (Moreira and Muir) | Equity evidence, and real-time combinations lose in 72 of 103 cases | An arm after Method 6 |
| Tenor premium (Jankauskas) | A blog post with no HY split, and it needs `s_el` | Section 7.1 is fitted |

Origin card items 1 and 5 enter Method 1. Item 2, `duration_gap_pv`, stays a check in M1.9.

## Addendum, 2026-11-01: papers opened after the review

The user supplied full text after the audit. Status: proposed. No test ran. No weight, no E5 setting, and no Section 4.7 rule changes. The human gates stay open. A new agent or the user did not audit this addendum.

### What the sources say

| Source | Sample | Outcome | Result |
| --- | --- | --- | --- |
| Andrade, Henry, Nanda (2014 draft), Table 3 col 3 | 372 firms, 2,846 firm-quarters, 2004Q1 to 2006Q1 | Log 5-year CDS | Debt 3.25 (t 9.35), leases 2.68 (t 5.15), purchases 0.90 (t 3.00). Leases less debt -0.57 (t -1.03). Leases less purchases 1.78 (t 3.11) |
| Same, Table 4 col 3, speculative grade, 541 observations | As above | Log CDS | Debt 3.02 (t 4.47), leases 2.76 (t 2.85), purchases 1.67 (t 2.10). The source cannot reject equal lease and purchase effects (p. 22) |
| Same, Table 5 col 2, pooled | As above | Log CDS | Purchases 0.61, essential term 1.89 (t 2.91), non-essential term -0.56 (t -1.25). Sums: 2.50 against leases 2.58, and 0.05 |
| Lim, Mann, Mihov (2017), Table 3 | 3,399 new bonds, 1995 to 2011 | Offering spread | Debt 2.051 (t 14.19), S&P leases 1.804 (t 9.02), equality F 0.95 (p 0.329). Moody's leases 1.228 (t 10.65), F 19.11 (p 0.000) |
| Sengupta, Wang (2011), Tables 3, 5, 6 | 1,712 firm-years, 173 new issues, 1999 to 2001. Rated BA or above, for yields | Rating, yield | Leases on rating -4.849 (t -9.44). On yield 2.209 (t 1.70) and 2.999 (t 2.19). Off and on balance sheet lease coefficients do not differ by Wald test |
| Jung, Scarlat (2024), Tables 2, 3 | 206 firms, 6,403 bond-days, 2019Q1. Mean yield 3.963% | Yield, 3 days after the first ASC 842 earnings date | GAP x Post 0.367 (t 3.91). Undervalued 0.594 (t 4.41). Overvalued -0.070 (t -0.53) |
| Prakash, Sinha (2009 draft), Tables 2, 3, 4 | 6,684 firm-years, 1,999 firms, 2002 to 2007. No negative equity. Over 75% NASDAQ | Next-year margin, stock return | `delta_drc` on margin 2.709 (t 5.89). Interaction with margin -3.846 (t 5.24 as printed). Decile rank on size-adjusted stock return 0.090 (t 3.91). No bond test |
| Bhojraj, Bloomfield, Jang, Yehuda (2021), Tables 3, 4, 6, 7 | 462 firms, 15,398 firm-quarters, 2001 to 2017. Median market value $8.1bn | Next-quarter CDS change, on cost elasticity x change in the anxious index | Interaction -1.470 (t 2.13) with all controls. Investment grade hedge t 2.68. **Speculative grade hedge t 0.21: the source finds no predictability in HY** |
| Oliveira et al. (2017), Baker et al. (w27707), Culp et al. (w20776) | See cards | No bond return test | They supply field definitions only |

Limits of the table:

1. None of these sources tests bond returns. Prakash and Sinha test stock returns. Bhojraj et al. test forward CDS changes, and their result is absent in speculative grade. The text extraction of Bhojraj et al. drops minus signs, so we take signs from the authors' text and not from the tables.
2. Scale. Yield is in percentage points and GAP is a fraction of assets. So 1% of assets as undervalued lease moves yield by about 0.6 bp (0.594 x 0.01 x 100, our arithmetic). The source's text says "36 basis points" per "100-point" increase. So this size may be below a TRACE cost.
3. Jung and Scarlat read a probit coefficient of 10.875 as "10.87 %" per 1% of GAP. A probit coefficient is not a probability change. We do not use this number.
4. Jung and Scarlat, Table 1 Panel A, print `Size` with a mean of 0.435. The Appendix defines it as log total assets. These do not agree. We did not resolve this.
5. Andrade et al. coded essentiality by judgement, and the coded data is not in our file. The draft states a period of 2003-2005 on p. 19, and 2004 to 2006 elsewhere. Page 23 labels both essentiality distributions speculative grade.
6. Prakash and Sinha is a 2009 working draft. We did not find whether a journal version changes the result. Their sample is pre-ASC 606.

### What the data says

Nothing new. No test ran. The on-file recontract coefficient of -2.07 stays as it is. It reads a share of obligations, in 2018 to 2026, inside an RPO filter. The three lease sources read amounts in other periods. So they do not refute it, and they do not explain it. They raise the priority of M1.2, because share arithmetic is one way to reach a negative slope on a claim that prices near debt per dollar.

### What we decide

1. **Cost clock: report by class.** `hy.clocks.obligation_class` and the `renewal_<class>_amount` metrics split the cost clock into debt, lease, and three purchase groups. `obligation_kind` and E5 stay as they are.
2. **Cost clock: amounts.** `sp_present_value` gives the contractual lease value before ASC 842, with the rule that the sources share. `moodys_lease` adds the floor. `amt_lease_after` stays the test variable, and these fields supply its pre-2019 input.
3. **Do not discount purchases yet.** The pooled source says about one third of a lease per unit. Its speculative grade column cannot reject equality, and HY is our market. So purchases stay at face in E5 until M1.3b reads.
4. **Revenue clock: add `delta_drc`.** It is the first revenue field in this project that can reach all four windows. It also has a named mechanism and a return result on stock.
5. **Revenue clock: add `durable_share` and `dropped_share`.** They give a contract-life reading from named customers, where no RPO exists. Reading a dropped name as non-renewal is our extension, because the name can also fall below 10%.
6. **Cost clock: add `cost_elasticity` as a level and control.** It measures fixed cost from cash, for every issuer, with no disclosed schedule. Lower elasticity goes with higher default probability: mean EDF 0.910 in the lowest quintile and 0.420 in the highest (Bhojraj et al., Table 1 Panel C). Do not build the timing trade for HY, because the source's speculative grade hedge has t 0.21. M1.13 tests the level, and it reports the interaction only.
7. **No signal weight for any of these.** Rule 4 of this page holds.
8. **Reject** Baker's churn and similarity measures, because they need card data and the paper tests no credit outcome. Reject Beyhaghi et al. and Borochin and Yang for the clocks. The review track file `fulltext/feature_extraction_2026-11-01.md`, outside git, holds each verdict.

### Inputs

| Input | Contract field | `as_of` | `available_at` | Status |
| --- | --- | --- | --- | --- |
| Lease ladder before ASC 842 | As in Method 1 | Balance-sheet date | 10-K acceptance time, with `datadate` + 90 days as a floor | need |
| Current rent | 3.2 `rent_expense` | Quarter end | First moment this version was public | have |
| Discount rate | Baa yield, Our choice, v0. Report at the swap rate less 10 bp and at 10% too | Decision date | Date + 1 | need in the panel |
| Reported lease liability | XBRL `OperatingLeaseLiability`, current and non-current | First ASC 842 10-Q | EDGAR acceptance time | need |
| Purchase text | 3.6 `text`, the contractual obligations table and its note | 10-K date | Acceptance time | have the text, need the parser. `purchase_essentiality` is the first form |
| Current deferred revenue | Compustat `drc`. XBRL `DeferredRevenueCurrent`, then `ContractWithCustomerLiabilityCurrent`, tags to confirm | Fiscal year end | 10-K acceptance time, with `datadate` + 90 days as a floor | need |
| Cash operating costs, sales | `compustat_quarterly` `saleq`, `recchy`, `oancfy`, `xidocy`, `xintq`, `txtq`, `txdcy`, `txachy`, `txbcoy` (Bhojraj et al., p. 83) | Quarter end | 10-Q acceptance time. The source assumes 2 months | need the cash fields. 20 quarters at least, so it starts about 5 years into each issuer's file |
| Anxious index | Philadelphia Fed Survey of Professional Forecasters | Survey quarter | Release date | need. Public, and not built from spreads, so it can also serve Method 4 |
| Total assets | `compustat_annual` `at`, outside the contract | Fiscal year end | As above | need. Use the Method 1 revenue twin scale where assets are absent |
| Customer lists | 3.3 `customer_shares` for XBRL years. Compustat segment file before them | Fiscal year end | Acceptance time | have per filing, need the history and name matches |
| SG&A, revenue | `hy/sources/xbrl.py` tags | Quarter end | Acceptance time | have |

### Tests

Each test follows rules 1 to 9 of this page. All thresholds are Our choice, v0. Read each on HY issuers, and report a pooled column beside it.

| Test | Claim | Pass | Fail | Untestable |
| --- | --- | --- | --- | --- |
| M1.3b Essentiality | Purchases split by what they buy, in HY | Essential slope exceeds non-essential slope, permutation p below 0.05, and the 90% interval of the non-essential slope holds 0 | The essential slope does not exceed the non-essential slope. Then essentiality stays a memo row | Under 30 issuers per group in the median month, or the coder agrees with under 80% of 50 filings coded by hand. Audit before any return is read |
| M1.7b Lease surprise | HY bonds moved on the surprise | Slope on `undervalued` clears the permutation null in the 3 days around the first ASC 842 earnings date. A placebo one year earlier stays flat. Estimated lease at the bond's own yield, as in the source | No response. The footnote was then priced, which fits Kraft (p. 20) | `mde` above the size of interest. First compute `mde` at 0.6 bp per 1% of assets. Under 30 issuers |
| M1.10 Deferred revenue | `delta_drc` carries over to HY bonds | Two steps. Step 1: the slope on next-year margin is positive in HY, with controls of the source. Step 2: the signal bar. Report 2018 and 2019 apart, with an ASC 606 flag | Either step fails. Then `delta_drc` stays a memo input to EQ11 | Under 60 issuers in the median month. The field is sparse outside software and health, by the source Panel C |
| M1.11 Customers | Durable and dropped customers explain the residual | The M2.2 bar in a pilot of 30 issuers first, then the panel. The spread change in the 3 months after a dropped name clears the permutation null | Below either bar | Name matches fail on over 20% of pilot rows |
| M1.13 Cost elasticity | Fixed cost explains the HY residual | `cost_elasticity` meets the M2.2 bar with a declared negative sign on spread. Report beside it `lev_ex_lease` and the rank correlation with `dur_obligations`, `fixed_charge_years`, and `sigma_sales`. Report the interaction with the change in the anxious index, with no pass or fail in HY | Below the bar. It then stays a memo row | Under 60 issuers with 20 clean quarters in the median month |
| M1.12 No-RPO proxies | `rev_abs_growth` and `sga_sales` explain the residual | The M2.2 bar. No declared sign, so they report only | Below the bar | Not applicable |

**Sign table additions for Method 2.** `amt_purch_essential` has a declared positive sign. `amt_purch_non_essential`, `delta_drc` on spread level, `durable_share`, and `rev_abs_growth` have none, and they report only. `cost_elasticity` has a declared negative sign on spread level, from the source's EDF sort. `dropped_share` has a declared positive sign, as our extension. `delta_drc` has a declared positive sign on bond return, transferred from stock return, and the transfer is our inference.

**Overlap.** E5 reads the same totals. `delta_drc` overlaps `rpo_drift`, because both read a change in contracted revenue, and M1.10 reports their rank correlation. `durable_share` overlaps `cust_top1`. `lease_renewal_gap` may overlap `rent_excess`.

**Source cards.** `bhojraj-bloomfield-jang-yehuda-2021-cost-structure-cds`, `andrade-henry-nanda-2014-leases-purchase-obligations`, `jung-scarlat-2024-asc842-bond-yields`, `lim-mann-mihov-2017-operating-leases-credit-capacity`, `sengupta-wang-2011-off-balance-sheet-debt`, `prakash-sinha-2009-deferred-revenues-matching`, `oliveira-kadapakkam-beyhaghi-2017-customer-distress`, `baker-baugh-sammon-2020-customer-churn`, `culp-nozawa-veronesi-2018-option-based-credit-spreads`.

## Addendum 2, 2026-11-02: one clock by industry

Status: proposed. No test ran. No weight, no E5 setting, and no Section 4.7 rule changes. No agent audited this addendum. Agents read most of these papers. We checked a sample of the printed numbers against the text. The user has the data on a production machine, so this addendum ignores data access.

### The change in one paragraph

The clocks now ask the same two questions of every issuer, and the answer depends on the industry. The questions are "what must this firm keep paying" and "what revenue can it count on". RPO answers the second question only for contract businesses. The map below names the answer for each framework archetype. The map itself is our proposal, and no source tests it.

| Archetype | Revenue clock | Cost clock additions | Resale and recovery |
| --- | --- | --- | --- |
| A1 Lease-heavy consumer | `soft_revenue` at a stated decay. Same-store sales in the memo | Lease classes, `lease_renewal_gap` | `redeploy_r`. Retail mean recovery is 33.40, N 33 (Jankowitsch et al., p. 40) |
| A2 Health care services | `soft_revenue`. Payer mix and rate reset dates in the memo. No source here tests them | `cost_elasticity`, lease classes | `redeploy_r`, `industry_distress` |
| A3 Commodity producers | Well decline in place of churn, and the hedge ladder. Gilje et al. note that output peaks in month one (n. 3) | Essential purchases such as pipeline capacity (Andrade et al., Appendix B), `float_unhedged` | `borrowing_base_collateral`, `redet_month`. `redeploy_r` is lowest for oil and gas, at 0.12 (Kim and Kung, p. 32) |
| A4 Cyclical industrials | Backlog on assets and on sales, as revised in M1.8 | `cost_elasticity` | `asset_spec`, `industry_distress` (Acharya et al.) |
| A5 Asset-heavy contracted | Filed RPO for cable and data centres. `delta_drc` on advance ticket sales for airlines, our proposal | Fleet leases, maintenance capex | `redeploy_operators_5`, `peer_shock`, `liquidity_facility` (Benmelech and Bergman) |
| A6 Software and recurring | Filed RPO windows, `delta_drc`, `durable_share` | Capitalised development, `cost_elasticity` | `redeploy_r` is high by the score, but value is the customer base (framework F2) |
| A7 Project and single asset | Contract tenor against project debt | Debt service at the asset, essential purchases | The asset. `peer_shock` where the asset has a known type, our extension |

### What the sources say

| Source | Sample and outcome | Result | Use |
| --- | --- | --- | --- |
| Kim, Kung (2013 draft) | 91,526 firm-quarters, 1989 to 2010. Capex over assets. No credit outcome | After x R 1.508 (t 2.92), and 1.309 (t 2.60) with controls (Table 4). Placebos -0.243 (t -0.61), 0.155 (t 0.84) (Table 6) | `redeploy_r` for any industry |
| Benmelech, Bergman (2009 NBER draft w13874, JFE) | 246 tranches, 12 airlines, 1990 to 2005. Spread at issue | Operators with 5 or more: -1.277 (t -3.18) (Table 6), and -2.34 (t -4.03) holding loan-to-value (Table 12) | `redeploy_operators_5` |
| Benmelech, Bergman (2011) | 18,327 insurer trades, 127 tranches, 1994 to 2007. Spread level | Bankrupt Buyers 64.666 (se 27.984) (Table VI). Senior 41.566, junior 429.922 (Table IX). 120-240 days after exit -72.041 (se 14.136) (Table VII) | `peer_shock`. The first buyer is 19.5 bp in base 10 and 44.8 bp in natural log. The paper never states the base |
| Acharya, Bharath, Srinivasan (2007) | 1,511 instruments, 778 in regressions, 1982 to 1999. Emergence price | Distress1 -11.11 cents (Table 3). Interaction with asset specificity -1.08 (se 0.36) (Table 4). Senior x Distress1 -21.08 (se 7.16) (Table 5) | Recovery by seniority, distress, and asset type |
| Jankowitsch et al. (2014) | 2,235 event-bonds, 2002 to 2010. Recovery price, days 0 to 30 | Speculative grade (Table 5 Model 2): financing covenant +9.4359, market default rate -4.4021, industry default rate -0.6808, maturity -1.0109. Means: secured 49.27, unsecured 39.09, subordinated 15.13 | M1.6 outcome and controls. It has no lease or purchase variable |
| Valta (2012) | 12,256 loans, 1992 to 2007. Loan spread | Competition 0.096 (t 3.00), about 17 bp (Table 3). Illiquid assets 0.243 (t 2.91), liquid 0.096 (t 2.28), difference p 0.11 (Table 11) | `competition_flag` for `adverse_competition` |
| Gilje, Loutskina, Murphy (2020) | 3,557 wells, 69 shale firms, contango of 2014-15. Months to completion | Contango x top leverage -1.002 (se 0.383) (Table IV). It fails without the top 3 firms: -0.612 (se 0.406) (Table IX) | `borrowing_base_collateral`, `redet_month`. No price test |
| Rajgopal et al. (2003) | 21,891 firm-years, 1981 to 1999. Stock return | Priced weight on backlog 0.039 against earnings weight 0.008. Backlog decile on next-year return -0.058 (t -2.38) | M1.8 revision |
| Campello et al. (w16622) | 2,718 loans, 1996 to 2002. Loan spread | Hedging -2.021 (se 0.315) in IV. Interaction with Z-score 0.496 (Table II and after) | `float_unhedged`, our extension |
| Hoberg, Phillips (w15991) | 50,673 firm-years, 1997 to 2006. No credit test | Operating income over sales R-squared 0.458 against 0.312 for SIC-3. These averages include the firm itself | Text peers as a report beside GICS |
| Gourio, Rudanko (w17191) | 648 firms, 1983 to 1999. No credit test | Churn of 0.15 is set from anecdote | `soft_revenue`, our extension |

Limits. No source here tests a US HY bond return. Only Jankowitsch et al. print a speculative grade table on a credit outcome, and that outcome is recovery. Ivashina et al. (2015) change nothing here. Deuskar and Johnson (the file `hhq132.pdf`) study S&P 500 futures, so they are off-topic.

### Disagreements

| Question | One side | Other side | When each is right (our reading) | Decision |
| --- | --- | --- | --- | --- |
| Is a hard-to-resell asset worse for the bond? | Gavazza card: rent is harder to shed | Benmelech and Bergman (2009), who cite 2007 work that we did not open: a lessor with a poor outside option accepts lower rent in distress | The first fits a going concern. The second fits distress. Secured holders read a third way: worse | Do not fix a sign on `recontract_bite`. Split by distress. M1.15 |
| Does sector-neutral value keep its pay in HY? | Houweling, van Zundert: HY value 3.72% falls to 2.43%, no longer significant | Correia et al.: inferences are, if anything, stronger, unreported and mostly IG | Houweling tabulates HY | Follow Houweling. Test within and between sector parts apart. M2.8 |
| Which bond sets the recovery price? | Methodology 6.2 reads the longest same-rank bond (Gatto, p. 530) | Jankowitsch et al.: long bonds trade lower, -0.5651 (se 0.0686), days 31 to 90 | Long bonds may carry more than recovery | Read the median same-rank price beside it. Section 6.2 stays as written until M1.6 reads |

### What we decide

1. **Labor is out of the clocks.** The user closed this on 2026-11-02. No labor field, labor flag, or labor test remains. The cards stay as a record.
2. **Resale gets a score for every industry.** `redeploy_r` uses the Kim and Kung formula, `R_j = sum_a w_ja A_a`. Airlines use `redeploy_operators_5` instead. It has no sign on spread until M1.15 reads, and it has no weight.
3. **Revenue clock works with no contracts.** `soft_revenue` feeds the same `mismatch` metrics at decay rates of 5%, 15%, and 30% (Our choice, v0). Read coverage and shortfall, and not run-off.
4. **Competition fills an open flag.** `adverse_competition` in Section 4.4 reads `competition_flag`. It uses the SIC-3 form, because the source's result falls to 0.030 (t 1.92) within SIC-3 on the text form.
5. **M1.8 changes.** Rajgopal et al. find that the stock market overprices backlog. So a negative IC in 3 windows reads as overpricing, and a retest with the sign flipped runs out of sample. Report `ob_assets` beside `ob_sales`, because a sales fall lifts `ob_sales`. Read `ob_beyond_fy_share` only where `ob_sales` exceeds 1.
6. **M1.6 gains an outcome.** Use the Jankowitsch et al. recovery price, one row per issuer event, with their controls, `industry_distress`, and `asset_spec`. Leave price dispersion out of any forecast, because it is measured after default.
7. **No code feeds these fields into a live score.** They are functions and tests.

### Seven steps

| Step | Change | Source |
| --- | --- | --- |
| 2 Qualitative | Add `competition_flag`, `redeploy_r`, and text peers as a report | Valta, Kim and Kung, Hoberg and Phillips |
| 3a Profitability | Add EQ11 | Prakash and Sinha |
| 3b Liquidity | Add `redet_month` as a date and `borrowing_base_collateral` for A3. Add `float_unhedged` | Gilje et al. Campello et al. for the direction, and the field is ours |
| 3c Capital structure | Read tranche loan-to-value with resale | Benmelech and Bergman |
| 4 Forecasting | Use `soft_revenue` where no contract exists | Ours |
| 5 Valuation | Haircut recovery by seniority, industry distress, and asset type. Add a peer filing check on collateral | Acharya et al., Jankowitsch et al., Benmelech and Bergman. No haircut size transfers, because the sample ends in 1999 |
| 6 Documents | Name liquidity facility, seniority, and aircraft type. Report financing covenants on recovery | Benmelech and Bergman, Jankowitsch et al. |
| 7 Recommendation | Split value into within and between sector parts | Houweling and van Zundert |

### Tests

Each test follows rules 1 to 9 of this page. All thresholds are Our choice, v0. Read each on HY issuers.

| Test | Claim | Pass | Fail | Untestable |
| --- | --- | --- | --- | --- |
| M1.15 Resale | Resale moves the lease bite, and the sign depends on the state | Report `amt_lease_after x (1 - redeploy_r)` apart in distressed and other issuers. The slopes differ by the permutation null | No difference. Then resale stays a recovery input | Under 30 distressed issuers in the median month |
| M1.16 Sector clock | The industry clock explains the residual inside its archetype | `coverage_contracted` on `soft_revenue` meets the M2.2 bar inside A1, A2, and A4, with the same sign at all three decay rates | The sign flips across decay rates, or it misses the bar. Then the decay model is dropped | Under 60 issuers in an archetype in the median month |
| M1.17 Competition | `competition_flag` carries to HY bonds | Positive slope clears the permutation null with `X` in, stronger for low `redeploy_r` | No slope. Then the flag stays a qualitative row | Not applicable |
| M1.18 Peer filing | Peer failures widen bonds on shared assets | In the 10 trading days after a filing, overlapping tranches widen more than other tranches of the same airline. The effect fades after exit. Run again on survivors' unsecured bonds, with no prior sign | No difference. Then `peer_shock` is dropped | Under 10 filings with overlap |
| M1.19 Float | Unhedged float bites near distress | `float_unhedged x` low coverage has a positive slope on spread, in a rate rise window | No slope | Not applicable |
| M2.8 Value split | Between-sector value holds the HY pay | Report ICs after cost for the within and between parts of S1 and ESP | No claim. The result decides how S1, ESP, and the sector spread combine | Not applicable |

**Sign table additions for Method 2.** `competition_flag` positive. `coverage_contracted` on `soft_revenue` negative. `redeploy_r`, `peer_shock` on unsecured bonds, and `delta_drc` on spread level have none, so they report only.

**Source cards.** `kim-kung-2013-asset-redeployability`, `benmelech-bergman-2009-collateral-pricing`, `benmelech-bergman-2011-collateral-channel`, `acharya-bharath-srinivasan-2007-industry-distress`, `jankowitsch-nagler-subrahmanyam-2014-recovery-rates`, `valta-2012-competition-cost-of-debt`, `gilje-loutskina-murphy-2020-drilling-debt`, `rajgopal-shevlin-venkatachalam-2003-order-backlog`, `campello-et-al-2011-corporate-hedging`, `hoberg-phillips-2010-text-based-industries`, `gourio-rudanko-2011-customer-capital`, `ivashina-iverson-smith-2016-chapter-11-claims`.

## The tests that settle it

Run all tests on the production machine, out of sample where the test says so, in the windows of `hy.backtest.CYCLE_WINDOWS`. Freeze each parameter first. Print the AR(1) of the monthly slopes of the split test and `lease_step` before anything else.

| Rank | Method | The test that decides | What a fail means |
| --- | --- | --- | --- |
| 1 | Rebuild the clocks, cost clock first | M1.2, M1.7. M1.4 is a memo test with no weight attached | Composition is not the reason, or the lease regime does not matter |
| 2 | Test against the residual | M2.1, M2.2 | The clocks do not explain the gap beyond the panel-level `X` |
| 3 | Layers and classifier | M3.3, M3.4 | S1 loses the mispricing label. Weight stays a user decision |
| 4 | Market state panel | M4.1, M4.5 | The clocks have no tested use as a condition or a risk measure |
| 5 | Pooled HY test, with a report by cell | M5.1, M5.3 | No paid exposure exists on our data |
| 6 | Credit state target | M6.1, M6.5, then M6.2 | The static band stays |

## Follow-ups (what must be built)

Each item carries its tests. Every new function cites its section and formula in the docstring.

1. Add the Method 1 fields to `hy/clocks.py`, `hy/sources/clock_facts.py`, and `hy/sources/schedules.py`. Add older lease stems, `lease_regime`, and `debt_includes_leases`. Tests in `tests/test_clocks.py`: the 90%, 30%, and 60% filers above, each debt tag family, EBITDAR at or below 0, and a `no_lookahead` fixture per new field.
2. Pull full XBRL instances for a stratified pilot of 30 issuers, and run M1.1 on it (Our choice, v0). Then pull the 343 RPO issuers, near 12,000 filings (our arithmetic). The `Bucket` grid can stay.
3. Build panel `coverage`, `ltv`, `margin_trend`, `wall_cover_4`, and F21 `S`. Without them the phrase "beyond Section 7.2" does not hold.
4. Add `compustat_annual` columns `mrc1` to `mrc5`, `mrcta`, `xrent`, `ob`, and `acctchg` to `docs/factors/PRODUCTION_DATA.md`. Add the panels of rule 2 to `docs/data_contract.md` section 3.14. Add a restatement fixture test.
5. Write `scripts/clock_harness.py` for Method 2, and leave `renewal_split_test` in place. Add two-way clusters to `hy/backtest.py` beside `driscoll_kraay_ols`. Tests: the synthetic month shock with a feature drift and no true effect, interval coverage on the panel's shape, and the `mde` injection.
6. Build `lambda_b` from `trace_trades`, with expanding normalisation. Check `docs/factors/F13-realized-illiquidity.md` for reuse. Write a runner for Method 3. Tests: pure noise reads `unresolved`, and conformal coverage per cell for `resid_clean`.
7. Add `resid_clean` to `data/schemas/bond_daily.json`, and `resid_class` as a run-level field, after M3.3 and M3.4 run.
8. Write a runner for Method 4. If a clock term enters Section 9.2, test the event model's probability integral transform. PD calibration by rating and cycle phase comes before `pd_12m` enters row 2 of the classifier.
9. Write a runner for Method 5. Add a delay term beside `hy.backtest.round_trip_cost`, and store Table 2 Panel B3 of the source in `data/schemas`.
10. Add `gcc_us` to `hy/macro.py`, and arms E and F to the conviction book runner.
11. `rent_option_gap` needs a synthetic lease test under framework F5 before use.
12. Keep unsigned features out of `f_t` until a sign is fixed. This follows the monotone sign test of `CLAUDE.md`.
13. Use `theta_idio s D` as a prior for `sigma(x)` in Section 7.3, and repeat the forecast test of Ben Dor et al. (p. 22) by rating cell. This is a small follow-up and not one of the six.

## Open (decisions for the user)

1. **The 20% Two clocks bucket.** The evidence questions it. `e5` has an IC after cost of -0.082 and -0.114 against its own sign, at beta = 1, and its IC beyond spread is not significant. No DTS hedge rerun is on file. Fixed-charge years rank with spread at +0.32, so a high E5 score tends to mean a low spread. At beta = 1 the bucket then leans against E0, which `hy/groups.py` calls the strongest tested signal. On file, under the DTS hedge, spread level earns nothing after cost. So that argument depends on the hedge. `e5` also steps up at each issuer's first ASC 842 filing. `2026-10-22-weights-esp-spider` says that a backtest positive beyond spread would support the weight, and none has passed. No opened source supports a long sign on low fixed charges. A flip of the sign has no support either. Tested `e5` also differs from live E5, which adds interest and signed leases. This page changes nothing. The user chooses to keep 20%, to set it to 0 until M2.5 or M4.5 passes, or to pick another share.
2. **The reversal rule.** Rule 5 proposes that the project bar wins over the reversal test on file. `2026-10-22-alpha-backtest-design` then needs an amendment. The user accepts or rejects this.
3. **Purchases inside E5.** E5 adds purchases at face. S&P excludes them from debt. This is a user decision after M1.3.
4. **The gap in the score.** E1, E2, E10, E14, and E16 read the peer gap, near 25% of the score. If M3.4 fails, the user decides whether those weights stay.
5. **Gates.** Human gates 1 to 4 stay open, so all screening labels stay provisional.
6. **Two archive copies.** The cards for Bao et al. and Dick-Nielsen et al. rest on Internet Archive copies of open-access files. The live hosts returned 429 and 403 to an automated fetch. We keep both cards, and the review report says so. If the user rejects them, Method 3 loses its source for `lambda` and for the lag evidence behind the skip. Method 2 loses the source for `phi`.
7. **Unopened papers.** A library login could open eight papers first: Jung and Scarlat (2024), Andrade et al. (2011), Lim et al. (2017), Xu (2018), Bao and Hou (2017), Lu et al. (2026), Hu (2020), Xu et al. (2025). By their titles, the first three may test leases in credit prices. Report Section 4 lists the rest.
8. **Rating feed.** Rule 8 needs a rating feed after February 2017, such as Mergent FISD or Capital IQ. `2026-10-22-esp-peer-groups` already asks for it. This is a licence decision.
9. **A 2022 shock date.** M4.3 reads 2022 as untestable until the user names one.
10. **Framework F5.** F5 applies the 15% cap to remaining rent. The statute text of 11 U.S.C. 502(b)(6) reads 15 percent of the remaining term. The two differ when rent escalates. Method 1 follows F5 as written. F5 should state which form it uses.
11. **F16 and F17.** Crossref marks Bai, Bali, and Wen (2019) as retracted. These two specs cite it. The review flag file holds the detail.
12. **Known gaps row.** Section 11 plans a basis feature for the liquidity gap. Dick-Nielsen et al. report that the basis is often negative in speculative grade (pp. 9-10). So keep `cds_5y` as a credit anchor, and do not read the basis as HY liquidity.
13. **Band levels.** Method 6 reads the band levels that the user sets on a later page.
