# Data contract

This page lists every kind of data that the HY Analyst reads. Use it as the checklist when you connect a new data source on another machine. The repo holds the method. The data plugs in through one connector: a class that implements the protocols in `hy/data/source.py`.

## 1. Rules for every kind

1. Every input reaches the analyst through one `DataView(source, decision_time)` (`hy/data/view.py`). The view returns only what was public at the decision time.
2. Every record carries `as_of` and `available_at`.
   - `as_of` is the date or period that the value describes.
   - `available_at` is the first moment the market could read the value.
   - `available_at` is never before `as_of`. The record class rejects such a record.
3. The view filters by `available_at`. It also checks what the source returns. A record public after the decision time raises `LookAheadError`.
4. A source that cannot supply an item raises `DataUnavailable(kind, key, reason)` (`hy/data/pit.py`). The analyst turns most of these into an open question in the memo. Section 3 states what each gap does.
5. Units:
   - Rates, yields, spreads and shares are decimals. 0.065 means 6.5%. 0.0350 means 350 bp.
   - Amounts are in USD millions.
   - Tenors, terms and maturities are in years.
   - Times are naive UTC `datetime` values. A filing's time is its EDGAR acceptance time.
6. Bond observations and the panels are pandas frames, because of their size. Each frame has an `available_at` column. All other kinds are frozen dataclasses in `hy/data/records.py`.

## 2. The kinds at a glance

| No. | Kind | Source method | View method | Required? |
|---|---|---|---|---|
| 3.1 | Issuer identity | `issuers` | `issuer` | yes |
| 3.2 | Quarterly financials | `financials` | `financials` | yes |
| 3.3 | Filing facts | `facts` | `facts` | yes |
| 3.4 | Filing list | `filings` | `filings` | no |
| 3.5 | Balance sheet and schedules | `balance_sheet` | `balance_sheet` | yes |
| 3.6 | Filing text | `filing_text` | `filing_text` | no |
| 3.7 | First-reported cash flows | `reported_cash_flow` | `reported_cash_flow` | no |
| 3.8 | Equity market value | `market_value` | `market_value` | no |
| 3.9 | Bond terms | `bonds` | `bonds` | yes |
| 3.10 | Bond observations | `observations` | `observations` | yes |
| 3.11 | Treasury curve | `curve`, `curves` | `curve`, `curve_history` | yes |
| 3.12 | HY index level | `hy_index` | `hy_index` | yes |
| 3.13 | Macro forecasts | `forecasts`, `forecast_status` | `forecasts`, `forecast_status` | no |
| 3.14 | Peer panels | `panel` | `panel` | no |
| 3.15 | Classifications, analyst inputs | `classifications`, `analyst_inputs` | same | no |

"Required" means that the run cannot form a view of the issuer without it. Section 3 gives the exact effect of each gap.

## 3. The kinds

### 3.1 Issuer identity (`Issuer`)

- Fields: `ticker` (str), `gvkey` (str or None, the key of the financials), `cik` (str or None, the key of the filings), `name` (str).
- Time stamps: none. Identity is static reference data.
- Used by: every step. The process calls `view.issuer(ticker)` first.
- When missing: `DataUnavailable`. Step 1 fails, the run prints the reason, and the issuer drops out of the run.

### 3.2 Quarterly financials (`IssuerFinancials`)

- Key: `key` is the issuer's `gvkey`. One record per quarter and per version. A restatement is a new version of the same quarter.
- Fields, all USD millions, flows for the quarter, balances at the quarter end:
  - Income: `revenue`, `cogs`, `ebitda_reported`, `ebitda_adj_company`, `ebitda_covenant`, `depreciation`, `rent_expense`.
  - Nonrecurring items: `nonrecurring_items`, a tuple of `NonRecurringItem(name, amount, recurs, cash)`.
  - Cash flows: `operating_cash_flow`, `capex_total`, `capex_maintenance`, `cash_interest`, `cash_taxes`.
  - Working capital: `inventory`, `receivables`, `payables`.
  - Liquidity: `cash`, `revolver_commitment`, `revolver_drawn`, `borrowing_base` (infinity when none), `letters_of_credit`.
  - Debt: `debt_current`, `debt_long_term`, `maturity_schedule` (five yearly amounts), `pension_underfunded`, `guarantees_weak`.
  - `source`: provenance text.
- Time stamps: `as_of` is the quarter end. `available_at` is the first moment that version of the quarter was public.
- Rule: the view returns every quarter in its latest version public at the decision time (`PointInTimeStore.as_known`).
- Used by: framework F3 normalisation (step 3: LTM table, earnings-quality tests, margin trend, FCF), F4 liquidity and the scenario start point (methodology 5.1), F5 coverage, G3 monitoring (step 12).
- When missing: step 3 runs with no quarters, so the LTM figures are empty and the memo lists open questions. The scenario start point (`scenarios.issuer_start`) needs at least one quarter. With none, the run stops with an error. This is a known gap.

### 3.3 Filing facts (`IssuerFacts`)

- Fields: `issuer_ticker` and `values`, a dict of `name: (value, source text)`. The source text travels to the memo. The names that the analyst reads:

| Name | Unit | Meaning |
|---|---|---|
| `ticker`, `name`, `cik`, `gvkey` | text | identity |
| `q`, `k` | text | accession of the latest 10-Q and the latest 10-K (`k` may be None) |
| `q_acceptance`, `k_acceptance` | time | their acceptance times |
| `balance_sheet_date` | date | the 10-Q balance-sheet date |
| `ltm_ebitda`, `ltm_revenue` | USD m | last-twelve-months totals |
| `run_rate_revenue` | USD m a year | latest quarter x 4 |
| `interest_rate` | decimal | cash interest / debt |
| `annual_lease_cost` | USD m a year | operating lease cost |
| `lease_wavg_term` | years | check only |
| `uncommenced_window`, `uncommenced_term` | years | signed leases not yet started: (start, end) and term |
| `debt_tail_years` | years | length of the "thereafter" debt bucket |
| `rpo_total` | USD m | remaining performance obligation |
| `rpo_windows` | list of (start years, length years, share) | timing of the RPO |
| `rpo_tail_years` | years | length of the RPO remainder |
| `purchase` | (USD m, years) or None | purchase commitments without a ladder |
| `archetype` | A1 to A7 | framework F2 archetype, from the analyst |
| `rating`, `recourse`, `scenario_extra_lease` | text or None | analyst judgement |
| `available_at` | time | the latest release among the inputs |

- Time stamps: `as_of` and `available_at` are the 10-Q acceptance time.
- Used by: step 1 inputs, F2 framing, methodology 4.7 clocks (`clock_case.build_case`), F5, the scenario engine.
- When missing: `DataUnavailable`. Step 1 fails and the issuer drops out of the run. A missing single value is None with a source text that says why, and the memo shows it as an open question.

### 3.4 Filing list (`Filing`)

- Fields: `issuer_ticker`, `form` (for example "10-Q"), `accession`.
- Time stamps: `as_of` and `available_at` are the acceptance time.
- Used by: framework F11 events (step 12 estimates the next results date from the filing cadence), the walk-forward audit.
- When missing: an empty list. Step 12 then has no results-date event.

### 3.5 Balance sheet and schedules (`BalanceSheet`, `Ladder`)

- One record per filing (the 10-Q and the 10-K of the facts).
- Fields, USD millions, NaN when the filing does not state the value:
  - `debt` and `debt_source`: total financial debt at the balance-sheet date and the tag or rule that gave it.
  - `operating_lease_liability`, `finance_lease_liability`, `cash`.
  - `revolver_capacity`: unused or maximum credit-line capacity. None when the filing states none.
  - `ladders`: a dict for `operating_lease`, `finance_lease`, `debt` and `purchase`. Each value is a `Ladder` or None.
    - `Ladder.amounts`: bucket amounts in USD millions. The last bucket is "thereafter".
    - `Ladder.first_length`: the first bucket's length in years. The other buckets are one year each.
    - `Ladder.total`, `Ladder.reconciles`: the stated total and whether the buckets add up to it.
  - `lease_not_commenced`: (total USD m, shortest term years, longest term years).
  - `customer_shares`: named customer to share of revenue, as a decimal.
- Time stamps: `as_of` is the balance-sheet date. `available_at` is the acceptance time.
- Used by: methodology 4.7 clocks (obligation ladders), F5 leverage (debt, leases, cash), the F4 funding gap and the scenario engine (debt lines, revolver).
- When missing: `DataUnavailable` for the 10-Q stops step 1 for the issuer. A missing ladder is None. Then the debt ladder comes from the balance-sheet total spread over ten years, and the memo states that assumption.

### 3.6 Filing text (`FilingText`)

- Fields: `issuer_ticker`, `accession`, `text` (plain text of the primary document).
- Time stamps: `as_of` and `available_at` are the acceptance time.
- Used by: F2 "what it sells" (the first two sentences of Item 1), F5 covenant levels (step 5, covenant-compliance skill).
- When missing: the business line is empty, and the memo says "no filing text". The covenant table stays open.

### 3.7 First-reported cash flows (`ReportedCashFlow`)

- Fields, USD millions for the quarter: `operating_cash_flow`, `capex`, `interest_paid`, `taxes_paid`, and the `accession` that stated them.
- Time stamps: `as_of` is the quarter end. `available_at` is the acceptance time of the first filing that reported the quarter.
- Used by: step 3 only. It fills a quarter whose cash flows the financials leave blank (methodology 3.2).
- When missing: the quarter stays blank, and the LTM uses the rule in `hy.state.ltm_total`.

### 3.8 Equity market value (`MarketValue`)

- Fields: `issuer_ticker`, `value` (price x shares, USD millions), `source`.
- Time stamps: `as_of` is the quarter end of the price. `available_at` is the report date.
- Used by: F7.7 valuation (step 8: market TEV, debt / market TEV), Kricheff and S&P ratios (step 5), estimate E9.
- When missing: the market value is NaN with the reason. Those ratios are then NaN.

### 3.9 Bond terms (`Bond`)

- Fields: `cusip`, `issuer_ticker`, `coupon` (decimal), `maturity` (date), `seniority` ("senior_unsecured", "secured", ...), `fixed` (bool), `convertible` (bool), `grade` ("H" for high yield).
- Time stamps: none. Terms are static between issue and redemption.
- Rule: the analyst keeps fixed, non-convertible, senior unsecured or secured bonds. The domain applies this rule, not the source.
- Used by: step 1 bond curve, F5 capital structure table, F4 refinancing (coupons of bonds due inside 27 months).
- When missing: an empty list. Step 1 is partial with an open question. Steps 4 to 15 do not run for the issuer, because it has no spread.

### 3.10 Bond observations (frame, `BOND_OBS_COLUMNS`)

- Columns, in this order: `cusip`, `date` (trade day), `price` (per 100 face, volume-weighted), `yield` (decimal, volume-weighted), `n_trades`, `par_volume` (USD), `available_at`.
- Time stamps: `date` is the trade day. `available_at` is when the day's trades became public (TRACE: the next day).
- Rule: the view asks for the window from 180 days before the decision to the decision, and keeps rows with `available_at` at or before it.
- Used by: step 1 latest snapshot (10 days), G-spreads and the issuer curve, the 5-year spread, the pair gap history (methodology 7.5), the recent-issue point of F4.
- When missing: an empty frame works like 3.9. A source error stops step 1 for the issuer.

### 3.11 Treasury par curve (`Curve`)

- Fields: `tenors` (years) and `yields` (decimal par yields), one value per tenor. NaN is allowed for a tenor with no quote.
- Time stamps: `as_of` is the curve date. `available_at` is when it was published (US Treasury: the next day).
- Two reads:
  - `curve(on)`: the latest curve public at `on`. It sets G-spreads, cash and Treasury returns (step 15).
  - `curves(start, end)`: every daily curve in the range. The view returns it as a frame for the pair gap history (step 9b).
- When missing: the run needs the current curve and stops without it. An empty history leaves the pair gap persistence as NaN.

### 3.12 HY index level (`IndexLevel`)

- Fields: `spread` (the market's high yield spread level, decimal) and `distress` (the share of high yield bonds wider than 1,000 bp, decimal). `name` says how the level was made.
- Time stamps: `as_of` is the market date. `available_at` is when it was public.
- Rule: the one index rule is `hy.state.hy_index_level`, and the one distress rule is `hy.state.distress_ratio`. The TRACE adapter applies both to its benchmark bonds. Another source may supply an index OAS directly, for example ICE BofA H0A0, and the method then reads that level.
- Used by: the F6 phase vote (the level now, 3 months ago, and once a year for 5 years), the fair spread fallback (methodology 7.2), DTS hedges (steps 9 and 15), estimate E0, the macro paths.
- When missing: a missing past snapshot is NaN in the phase table, and the vote uses the others. The current level is required.

### 3.13 Macro forecasts (`ForecastRow`) and their status

- Fields: `source`, `variable`, `horizon_q` (quarters ahead, 0 to 8), `vintage`, `available_at`, `point`, `q10`, `q50`, `q90`, `method`.
- Variables that the paths read: `gdp_growth`, `cpi`, `unemployment` (annual rates, decimals), `policy_rate`, `y2`, `y10` (decimals), `sloos_tightening` (net share of banks, decimal), `hy_spread`, `distress_ratio`.
- Time stamps: `vintage` is the forecast date. `available_at` is its release.
- Status: `forecast_status(decision_time)` returns one row per forecast source with the columns `source`, `status`, `last_vintage`, `last_available_at`, `rows`, `rows_after_decision_time`. The run writes it to `_run.json` as its audit trail.
- Used by: methodology 5.4 macro paths (`hy.macro.build_paths`), the F6 phase vote (SLOOS), the scenario engine.
- When missing: a source with no rows is "stubbed". The path builder then uses its fallback order and logs a stated assumption.

### 3.14 Peer panels (frames)

Every panel has an `available_at` column. The view drops rows that were not public at the decision time.

| Panel | Columns | Units | Used by |
|---|---|---|---|
| `bond_panel` | `date` (month end), `cusip`, `gvkey`, `years`, `g_spread`, `available_at`. The backtest also reads `price`, `yield`, `coupon`, `maturity`, `mod_dur`, `tsy_yield`, `bid_ask_pts`, `n_trades`, `par_volume` | years, decimal | step 9 peers, ESP and E13 (methodology 7.2, 7.4), the backtests |
| `leverage` | `date`, `gvkey`, `leverage`, `ltm_ebitda`, `debt`, `available_at` | x, USD m | peer cells and the implied rating class |
| `gics` | `gvkey`, `gsector` (two digits), `indfrom`, `indthru`, `available_at` | text, dates | the peer sector |
| `ratings` | `gvkey`, `datadate`, `splticrm` (S&P letter), `available_at` | text | the actual rating class |
| `annual_ebitda` | `gvkey`, `datadate`, `fyear`, `oibdp`, `debt`, `available_at` | USD m | SPiDER, E15 |
| `equity_monthly` | `gvkey`, `datadate` (month end), `ret` (monthly total return), `available_at` | decimal | OneScore, E16 |

- When missing: without `bond_panel`, `leverage`, `gics` or `ratings`, step 9 has no peer cell. The fair spread then falls back to the HY index, and the memo says so. Without `annual_ebitda`, SPiDER (E15) is NaN. Without `equity_monthly`, OneScore (E16) is NaN, and ESP carries its weight.

### 3.15 Classifications and analyst inputs

- `Classification`: GICS sector and rating class per issuer, valid from `as_of`. `AnalystInput`: the analyst's YAML per issuer.
- These are part of the protocols, but the process does not read them through the view today. The facts adapter applies the analyst YAML, and the peer step reads the `gics` and `ratings` panels.

### 3.16 Realised outcomes (not a new kind)

The walk-forward scores each prediction against what happened next. `hy.data.outcomes.RealisedOutcomes(source, decision_time)` reads bond observations, curves and the HY index public after the decision. It uses the same source methods as above. It refuses a time before the decision, and no step that forms a prediction imports it. A test checks this.

## 4. How to plug in a new source

1. Write one class, for example `MySource`, that implements every protocol in `hy/data/source.py`: `IssuerSource`, `FilingSource`, `BondSource`, `MarketSource`, `EquitySource`, `ReferenceSource`, `ForecastSource`, `AnalystSource` and `PanelSource`.
   - Return the record types of `hy/data/records.py` with the units of section 1.
   - Stamp every record with `as_of` and `available_at`. Never stamp a value earlier than its real release.
   - Raise `DataUnavailable` for an item that you do not have. Do not return a zero for a missing amount.
   - Keep vendor field names inside your class. `FakeSource` in `hy/data/sources.py` is a short model to copy.
2. Pass it to the view: `DataView(MySource(...), decision_time)`.
3. Run the process: `process.run(tickers, end, pairs, view=DataView(MySource(...), decision))`. A run at `end` decides at `end` plus one day.
4. Check the connector:
   - Run `tests/test_pipeline_fake_source.py`. It shows the shape of every kind and runs the whole analyst on made-up data with the network blocked.
   - Run the suite: `python3 -m pytest -q`.
   - Take a golden snapshot on the new machine, `PYTHONPATH=.:scripts python3 scripts/golden_check.py snapshot`, then run `check` after each change. The numbers will differ from this machine's numbers because the data differs. They must not move between your own runs.
5. Set `HY_DATA_ROOT` for the derived files that stay as files: the backtest summaries (`summary_full.json`, `results_h*.parquet`, `peer_signals_*.parquet`) and the run outputs. Without them, step 14b uses the v0 slope of spec S14b.

## 5. What stays outside the contract

- `scripts/backtest_alpha.py` and `scripts/backtest_clocks.py` build the warehouse panels from TRACE, Compustat and SEC data. They are panel builders for this warehouse. Another machine supplies the panels through `panel()` instead.
- The pilot subsets (`panel_pilot`, `leverage_pilot`) are warehouse files that `hy.data.history.backtest_panel` reads by tag.
- `scripts/rv_pair.py` keeps a WRDS query for the benchmark band of its figure. The report is display only.
- `scripts/walkforward.py` reads 8-K item codes from the EDGAR cache for its event marks. They are display only.
