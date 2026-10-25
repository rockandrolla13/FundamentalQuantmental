# Production wiring guide

This guide connects the HY Analyst to your own data on another machine, then runs every part of it end to end. You need no WRDS. You export your data into a fixed set of tables, and the analyst reads them.

`docs/data_contract.md` defines every data kind. This guide tells you what to export, in which file, with which columns. It also gives the commands in order.

## 1. The picture

The analyst reads every input through one `DataView` at one decision time. One setting, `HY_SOURCE`, chooses the source behind the view.

| Data | Who supplies it | Where it goes |
| --- | --- | --- |
| Issuers, quarterly financials, bonds, daily bond prices, HY index level, equity value, peer panels | You | Tables under `<HY_DATA_ROOT>/tables/` (section 4) |
| SEC filings: facts, filing list, balance sheets and schedules, filing text, first-reported cash flows | Public SEC EDGAR | Read by the code, cached under `<HY_DATA_ROOT>/edgar/` |
| US Treasury par curve | Public US Treasury, or your table | Read by the code, or `tables/treasury_curve` |
| Macro forecasts: SPF, FOMC SEP, SLOOS | Public Fed sites | Read by the code, cached under `<HY_DATA_ROOT>/forecasts/` |
| Analyst judgement: archetype, ratings override | You | `data/analyst_inputs/<TICKER>.yaml` |

`HY_SOURCE=hy.data.tables:make_source` joins your tables with the public part. Each data kind asks your tables first. When a table does not hold the item, the public part answers. `scripts/check_source.py` prints which part serves each kind.

## 2. The steps on the work machine

Run every command from the repository root.

1. Install the package.
   ```
   pip install -e ".[test]"
   python3 -m pytest -q
   ```
   The tests need no data. Expect about 600 passes and 1 skip.
2. Set the four settings (section 3).
3. Export your data into the tables (section 4). Start with one issuer.
4. Download the SEC files for your issuers (section 3).
   ```
   SEC_USER_AGENT="Your Name your@email" python3 scripts/download_sec.py --from-tables --start 2018-01-01
   ```
5. Build the two large panels from your tables (section 5).
   ```
   python3 scripts/build_panels.py --start 2010-01-31 --end 2026-08-31
   ```
6. Check the source. Fix every failed `required` row, then run the check again.
   ```
   python3 scripts/check_source.py AAPL F --decision 2026-09-18
   ```
7. Run the backtests and the size calibration (section 7, rows 1 to 5).
8. Run the issuer process and the memos (section 7, rows 6 and 7).
9. Take a golden snapshot. Compare against it after each later change.

Time: about one day for the export of one issuer and its bonds. The panels for the whole high yield universe take longer, because they cover every bond since 2008.

## 3. Settings

| Variable | Value | Effect |
| --- | --- | --- |
| `HY_SOURCE` | `hy.data.tables:make_source` | Read your tables, then the public data. Unset means this machine's WRDS warehouse. A value `package.module:function` calls your own factory with the run's config. |
| `HY_DATA_ROOT` | `/path/to/data` | The data root. Tables go in `tables/` under it. Caches, backtest outputs, calibration and process outputs go under it too. |
| `HY_OFFLINE` | `1` or unset | `1` forbids every network read. The code then reads only the caches and your tables. |
| `SEC_USER_AGENT` | `Your Name your@email` | The SEC asks for a name and an email in each request. |
| `PYTHONPATH` | `.` (some scripts need `.:scripts`) | The repository root on the import path. |

**Download the SEC files.** `scripts/download_sec.py` fills the SEC cache under `HY_DATA_ROOT` with the code's own loaders: the filing index, the XBRL company facts, and the XBRL instance and text of every original 10-Q and 10-K since `--start`. A rerun fetches the two index files again and skips the filings already in the cache. Each file's outcome goes to `edgar/download_log.csv`.

```
SEC_USER_AGENT="Your Name your@email" python3 scripts/download_sec.py --from-tables --start 2018-01-01
```

`--from-tables` takes every issuer with a CIK in `tables/issuers`. `--tickers` and `--ciks` name issuers directly. The SEC refuses a request without a name and an email (HTTP 403), so the script stops when `SEC_USER_AGENT` is not set. Time: each filing takes four requests, and the loaders keep under the SEC limit of 10 a second. Expect about 2 seconds a filing, so about 1 minute for an issuer with 8 years of quarterly filings and about 8 hours for 500 issuers.

**A machine without internet.** Run `scripts/download_sec.py` on a machine that reaches sec.gov, then copy the folder `edgar/` under `HY_DATA_ROOT`. Supply the Treasury curve as a table. Copy the folder `forecasts/` too: run `scripts/check_source.py` once on the machine with internet, and the code fills it. Then set `HY_OFFLINE=1`. Without the SEC cache, the facts kind fails and step 1 stops for the issuer.

## 4. The tables

Put each table in `<HY_DATA_ROOT>/tables/` as `<name>.parquet` or `<name>.csv`. Parquet wins when both exist.

Rules for every table:

- Rates, yields, spreads, coupons and returns are decimals. 0.065 means 6.5%. 350 bp is 0.035.
- Amounts are USD millions. One exception: `par_volume` in `bond_obs` is in USD.
- Dates are calendar dates. Times are naive UTC.
- `available_at` is the first moment the value was public. Never put a time earlier than the real release. The view refuses a value with `available_at` after the decision time.
- Leave a cell empty when you do not have the value. Never write a zero for a missing amount.
- The issuer key `issuer_id` is any string. Use the same key in every table and in every panel's `gvkey` column. On this machine the key is the Compustat gvkey.

The column "This machine" names the WRDS field that fills the column here. Use it to find the matching field in your data.

### 4.1 `issuers` (required)

One row per issuer that you run or that enters the peer panels.

| Column | Type | Meaning | This machine |
| --- | --- | --- | --- |
| `ticker` | text | The ticker that you pass to the run | Compustat `tic` |
| `issuer_id` | text | Your issuer key | Compustat `gvkey` |
| `cik` | text, optional | SEC central index key. The SEC kinds need it for every issuer you run. | Compustat `cik` |
| `name` | text, optional | Company name | Compustat `conm` |

### 4.2 `financials` (required)

One row per issuer, per fiscal quarter, per version. A restatement is a new row with the same `period_end` and a later `available_at`. The view keeps the latest version public at the decision time.

Flows are for the 3-month quarter, not year to date. Balances are at the quarter end.

| Column | Required | Meaning | This machine |
| --- | --- | --- | --- |
| `issuer_id` | yes | Issuer key | `gvkey` |
| `period_end` | yes | Fiscal quarter end | `datadate` |
| `available_at` | yes | First public time of this version: the 10-Q or 10-K acceptance time for a first version | EDGAR acceptance, else the Compustat point-in-time snapshot day |
| `revenue` | yes | Revenue | `saleq` |
| `ebitda_reported` | yes | EBITDA after special items | `oibdpq + spiq` |
| `ebitda_adj_company` | yes | EBITDA before special items. The leverage panel uses it. | `oibdpq` |
| `special_items` | no | Special items. A charge is negative. The add-back is minus this value. | `spiq` |
| `special_items_cash` | no | True when the special items used cash | not given (False) |
| `cash_interest` | no | Interest paid | `intpnq` de-cumulated, else `xintq` |
| `cash_taxes` | no | Taxes paid | `txpdq` de-cumulated, else `txtq` |
| `capex_total` | no | Capital expenditure | `capxq` de-cumulated |
| `capex_maintenance` | no | Maintenance capex | not given (empty) |
| `operating_cash_flow` | no | Cash from operations | `oancfq` de-cumulated |
| `depreciation` | no | Depreciation and amortisation | `dpq` |
| `cogs` | no | Cost of goods sold | `cogsq` |
| `inventory`, `receivables`, `payables` | no | Working capital balances | `invtq`, `rectq`, `apq` |
| `cash` | no | Cash and equivalents | `cheq` |
| `debt_current`, `debt_long_term` | no | Debt due inside one year, and the rest | `dlcq`, `dlttq` |
| `revolver_commitment`, `revolver_drawn`, `letters_of_credit`, `borrowing_base` | no | Credit line terms | not given |
| `maturity_y1` to `maturity_y5` | no | Debt due in each of the next five years | not given |
| `rent_expense`, `pension_underfunded`, `guarantees_weak` | no | Lease cost and two debt-like claims | not given |
| `ebitda_covenant` | no | EBITDA under the credit agreement | not given (empty) |
| `source` | no | Provenance text for the memo | `compustat_pit+edgar` |

A column that you leave out takes the value that this machine uses for it. That value is 0 for the six "not given" balance fields and the maturity schedule. The borrowing base then sets no cap. Every other left-out column is empty. An empty cell in a column that you give stays empty.

The LTM figures need four consecutive quarters. With fewer, the LTM figures are empty and the memo lists open questions. With no quarter at all, steps 4 to 15 show as blocked for that issuer, with the reason. The run continues for the other issuers.

### 4.3 `bonds` (required)

One row per bond. The terms are static between issue and redemption.

| Column | Meaning | This machine |
| --- | --- | --- |
| `bond_id` | Bond identifier, for example a CUSIP. Use the same value in `bond_obs`. | TRACE `cusip_id` |
| `ticker` | The issuer's ticker, as in `issuers` | TRACE master `company_symbol` |
| `coupon` | Coupon rate, decimal | `cpn_rt` / 100 |
| `maturity` | Maturity date | `mtrty_dt` |
| `seniority` | `senior_unsecured`, `secured`, or another word | TRACE master |
| `fixed`, `convertible` | True or False | TRACE master |
| `grade` | Optional. `H` for high yield. | TRACE master |

The analyst keeps fixed, non-convertible, senior unsecured or secured bonds. It applies this rule itself. Export every bond.

### 4.4 `bond_obs` (required)

One row per bond and trade day.

| Column | Meaning | This machine |
| --- | --- | --- |
| `bond_id` | As in `bonds` | `cusip_id` |
| `date` | Trade day | `trd_exctn_dt` |
| `price` | Price per 100 face, volume weighted over the day | TRACE, par weighted |
| `yield` | Yield to maturity, decimal, volume weighted. Empty when the bond trades flat. | TRACE `yld_pt` / 100, par weighted |
| `n_trades` | Number of trades that day | count |
| `par_volume` | Par traded that day, in USD | sum of the par of the day's trades |
| `available_at` | When the day's prices became public | trade day + 1 day |
| `bid_ask_pts` | Optional. Quoted bid-ask in price points. The backtest cost uses it. | dealer-side gap, else the day's high-low |

The process reads the last 180 days before the decision. The panel builder reads the last 7 calendar days of each month. A dealer quote feed works too: put the mid price in `price`, the mid yield in `yield`, and 1 in `n_trades`.

### 4.5 `hy_index` (required)

One row per market date.

| Column | Meaning | This machine |
| --- | --- | --- |
| `date` | Market date | TRACE benchmark window end |
| `available_at` | When the level was public | date + 1 day |
| `spread` | The high yield market spread, decimal. An index OAS such as ICE BofA H0A0 is fine. | TRACE benchmark median G-spread (`hy.state.hy_index_level`) |
| `distress` | Share of high yield bonds wider than 1,000 bp, decimal | `hy.state.distress_ratio` |
| `name` | Optional. How you made the level. | `TRACE HY benchmark` |

The F6 phase vote reads the level now, 3 months ago, and once a year for 5 years. Give at least monthly rows for the last 5 years.

### 4.6 `market_value` (optional)

| Column | Meaning | This machine |
| --- | --- | --- |
| `ticker` | Issuer ticker | |
| `period_end` | Quarter end of the price | `datadate` |
| `available_at` | Report date | `rdq` |
| `value` | Price times shares, USD millions | `prccq x cshoq` |
| `source` | Optional provenance | |

Without it, the market TEV ratios of step 8 are empty.

### 4.7 `treasury_curve` (optional)

Give it when the machine cannot reach `home.treasury.gov`, or when you prefer your own curve.

| Column | Meaning |
| --- | --- |
| `date` | Curve date |
| `available_at` | When the curve was public (the US Treasury: the next day) |
| one column per tenor | Par yield, decimal. The column name is the tenor in years, for example `0.0833`, `0.25`, `2`, `10`, `30`. |

## 5. The panels

The peer step (step 9) and the backtests read six panels from `tables/panels/`. Each has an `available_at` column. `gvkey` holds your issuer key.

| Panel | Columns | Build |
| --- | --- | --- |
| `bond_panel` | `date` (month end), `cusip`, `gvkey`, `years`, `g_spread`, `available_at`. The backtests also read `price`, `yield`, `coupon`, `maturity`, `mod_dur`, `tsy_yield`, `bid_ask_pts`, `n_trades`, `par_volume`, `carried`, `accrue_to`, `hedge_date`. | `scripts/build_panels.py` |
| `leverage` | `date`, `gvkey`, `leverage`, `ltm_ebitda`, `debt`, `available_at` | `scripts/build_panels.py` |
| `gics` | `gvkey`, `gsector` (two-digit GICS sector), `indfrom`, `indthru` (empty while current), `available_at` | Export |
| `ratings` | `gvkey`, `datadate`, `splticrm` (letter on the S&P scale: AAA to D with + and -), `available_at` | Export |
| `annual_ebitda` | `gvkey`, `datadate`, `fyear`, `oibdp` (annual EBITDA before special items), `debt`, `available_at` | Export (optional) |
| `equity_monthly` | `gvkey`, `datadate` (month end), `ret` (monthly total return, decimal), `available_at` | Export (optional) |

`scripts/build_panels.py` applies this machine's rules to your tables:

- `bond_panel`: per bond and month end, the par-weighted price and yield over the month's last 7 days, the G-spread on the Treasury curve dated on or before the month end, the duration, and the bid-ask. A bond gets one extra "carried" row in the month after its last price, so its return ends where its prices end.
- `leverage`: debt over LTM EBITDA before special items, as known at each month end plus one day. It needs four consecutive quarters, or three with the fourth scaled in.

Gaps: without `bond_panel`, `leverage`, `gics` or `ratings`, step 9 has no peer cell. The fair spread then falls back to the HY index, and the memo says so. Without `annual_ebitda`, SPiDER (E15) is empty. Without `equity_monthly`, OneScore (E16) is empty.

## 6. Analyst inputs

Write one YAML per issuer in `data/analyst_inputs/<TICKER>.yaml`. The file holds judgement, not data. The key that every issuer needs is the framework F2 archetype:

```yaml
archetype:
  value: A5
  source: "framework F2 A5 asset-heavy: airlines"
```

Copy the files in `data/analyst_inputs/` as examples. Without an archetype, step 2 shows as blocked and asks for one. Run the scripts from the repository root, because the code finds this folder from there.

## 7. Run everything end to end

Set the variables of section 3 first. Run the rows in order. Each row needs the outputs of the rows above it.

| No. | Task | Command | Writes under `HY_DATA_ROOT` |
| --- | --- | --- | --- |
| 1 | Alpha backtest replay | `python3 scripts/backtest_alpha.py --from-panels --tag full --start 2010-01 --end 2026-08 --h 3 6 12` | `backtest/results_h*_full.parquet`, `summary_full.json` |
| 2 | Peer signals | `python3 scripts/backtest_peers.py --tag full` | `backtest/peer_signals_full.parquet` |
| 3 | Peer-line backtest | `python3 scripts/backtest_peer_line.py --cost-bp 15` | `backtest/summary_peer_line_*.json` |
| 4 | OneScore test | `python3 scripts/backtest_onescore.py --tag full` | `backtest/` |
| 5 | Size calibration | `python3 scripts/calibrate_sizes.py` | `calibration/size_calibration.json` |
| 6 | Issuer process | `python3 scripts/process.py --tickers AAPL F --pairs AAPL:F --end 2026-09-17` | `process/<TICKER>.json` |
| 7 | Memos | `python3 scripts/memo.py` | `docs/writeup/issuer_memos.tex` |
| 8 | Walk-forward replay | `PYTHONPATH=.:scripts python3 scripts/walkforward.py all --tickers AAPL F --pairs AAPL:F --first 2024-03-31 --last 2026-09-17` | `walkforward/` |
| 9 | Golden snapshot | `PYTHONPATH=.:scripts python3 scripts/golden_check.py snapshot --tickers AAPL F --pairs AAPL:F --end 2026-09-17` | `golden/` |

`--end` is the last trade day of your bond data. The run decides at the next day, with the filings known by then.

Rows 1 to 5 are optional for a first run. Without them, step 14b uses the spec S14b v0 slope, and the memo says so.

The snapshot saves its tickers, pairs and end date. `golden_check.py check` reruns the same run and compares every number. Run the check after each change that must not move a number. Your numbers will differ from this machine's numbers, because the data differs. They must not move between your own runs.

## 8. When the check fails

`scripts/check_source.py` writes `check_source.csv` under the data root. Fix the failed rows in this order.

| Failed row | Detail says | Fix |
| --- | --- | --- |
| `issuer` | missing `cik` | Add the SEC CIK to `issuers`. The SEC kinds need it. |
| `financials` | fewer than 4 quarters | Export more quarters. Check that `issuer_id` matches `issuers`. |
| `financials` | expect USD millions | Divide amounts in dollars by 1,000,000. |
| `facts` | unavailable, HTTP or NetworkDisabled | Run `scripts/download_sec.py` for the issuer, then look up its rows in `edgar/download_log.csv`. Set `SEC_USER_AGENT`. |
| `facts` | missing keys | A custom facts source left out a key of `hy.data.source.FACT_KEYS`. Add the key; its value may be None. |
| `observations` | expect yield decimal | Divide yields in percent by 100. |
| `observations` | no observations in the last 180 days | Check the `date` range and `available_at`. |
| `bonds` | expect decimals | Divide coupons in percent by 100. |
| any | look-ahead | `available_at` is later than the decision time for a record the source returned. Use the real release time. |
| `curve` | unavailable | Allow access to `home.treasury.gov`, or give `treasury_curve`. |
| `hy_index` | expect decimal | Divide spreads in percent by 100, or spreads in bp by 10,000. |

## 9. Your own class instead of tables

A database connection can replace the tables. Write a factory that returns a source object, then name it in `HY_SOURCE`:

```python
# mydata/hy_source.py
from hy.data.sources import CompositeSource, PublicSource

class MyVendor:
    def __init__(self, cfg): ...
    def issuers(self, tickers): ...          # list[hy.data.records.Issuer]
    def financials(self, issuer): ...        # list[IssuerFinancials], every version
    def bonds(self, issuer): ...             # list[Bond]
    def observations(self, bonds, start, end): ...  # frame with BOND_OBS_COLUMNS
    def hy_index(self, on): ...              # IndexLevel public at `on`
    def market_value(self, issuer, decision_time): ...
    def panel(self, name, columns=None): ...  # frames with PANEL_COLUMNS[name]

def make_source(cfg):
    mine = MyVendor(cfg)
    return CompositeSource(mine, PublicSource(cfg, fundamentals=mine, market=mine))
```

Then set `HY_SOURCE=mydata.hy_source:make_source`. `hy/data/tables.py` is a full example. A method that cannot supply an item raises `hy.data.pit.DataUnavailable`. The composite source then asks the next part.

## 10. Limits

- The SEC facts come from US SEC filings. A private issuer, or an issuer that files outside EDGAR, has no facts. Step 1 then stops for that issuer. Supplying the facts yourself needs a source with a `facts` method that returns all the keys of `FACT_KEYS`.
- The peer panels define the peer universe. A thin universe gives thin peer cells.
- The study scripts (`scripts/wt_*.py`, `s_tests.py`, `s7_sector_tilt.py`, `pull_sector_data.py`) read this machine's warehouse files directly. They are research, not the production run, and this guide does not cover them.
- `scripts/rv_pair.py` keeps a WRDS query for the benchmark band of one figure. The process does not use it.
- When every issuer of a run drops out at step 1, `process.run` stops with `KeyError: 's5'`. The walk-forward records such a date as failed and continues. Check the step 1 message of each issuer.
- The study script `scripts/wt_sector_rules.py` assigns a firm's first GICS sector to dates before that sector was published. That is a look-ahead in a research script, outside the production run.
