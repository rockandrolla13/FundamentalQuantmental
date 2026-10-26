# Production data checklist for the 30 factors

Every module in `hy/factors/` reads panels through `compute(panels, as_of)`. A missing optional panel gives an empty result or a fallback, never an error. This page lists what the production machine must add so that each factor scores. Column details and lag rules are in each spec page `docs/factors/FNN-*.md`, section "Inputs".

The repo holds the implementation and unit tests only. No evaluation runner exists. The evaluation test of each spec page (rank IC beyond spread after costs, positive in at least three of the four cycles 2008, 2015, 2020, 2022) runs on the production machine.

## 1. Changes to existing data (do these first)
1. **Start the history in 2004 or earlier.** The panel build starts in January 2010 and `hy/sources/peer_data.py` pulls equity from 2007. With those starts, the 2008 cycle is empty for every factor, and a factor must then pass all three remaining cycles. Factors that need 36 months of history (F01, F03, F07, F15) need data from 2004 to score in 2008.
2. **Daily rows in `hy_index`.** Wiring section 4.5 asks for monthly rows. F26 and F30 need daily rows. F25 and F27 use daily rows where present.
3. **Export the `ratings` panel.** F01, F02, F04, F10, F13, F16, F24 use the actual S&P class and fall back to the leverage-implied class after February 2017. Keep the `leverage` panel, which the fallback needs.
4. **Keep TRACE execution time.** `hy/sources/trace_panel.clean_trades` drops `trd_exctn_tm`. F13 needs it.
5. **Optional `amt_out` in `bond_panel`.** Par amount outstanding. With it, F03, F12 and F07 switch from equal to market-value weights inside an issuer.

## 2. New panels from WRDS and vendors
| Panel | Columns | Source | Factors |
|---|---|---|---|
| `compustat_quarterly` | `gvkey`, `datadate`, `rdq`, `ceqq`, `prccq`, `cshoq`, `cheq`, `dlcq`, `dlttq`, `oibdpq`, `saleq`, `xintq`, `dpq`, 3-month `oancf`, `capx`, `intpn`, `aqc` (de-cumulate year-to-date fields), `available_at` from `rdq` | `comp.fundq` | F08, F19, F23 |
| `compustat_annual` | `gvkey`, `datadate`, `fyear`, `sale`, `cogs`, `at`, `che`, `xint`, `capx`, `dd1` to `dd5`, `oancf`, `aqc`, `intpn`, `dp`, `dlc`, `dltt`, `available_at` | `comp.funda` | F09, F19, F21 |
| `financials` (as a panel keyed by `gvkey`) | `period_end`, `debt_current`, `debt_long_term`, optional `liabilities_total`, `minority_interest`, `available_at` | existing table 4.2 | F02 |
| `market_value` keyed by `gvkey` | as table 4.6, re-keyed from ticker | existing table 4.6 | F01, F02 |
| `equity_daily` | `gvkey`, `date`, `prc`, `shrout`, `ret`, `available_at` = trade day + 1 | CRSP daily | F02, F18 |
| `ff_factors` | `date`, `mktrf`, `rf`, `available_at` | Ken French library | F03 |
| `tbill_monthly` | `date`, `rf`, `available_at` | Ken French or FRED | F07 (zero if missing) |
| `option_iv` | `gvkey`, `date`, `cvol`, `pvol`, `available_at` = date + 1 | OptionMetrics `vsurfd`, 365 days, delta ±50, link secid to permno to gvkey | F11 |
| `bond_terms` | `cusip`, `seniority`, `callable`, `call_price`, `coc_put_price`, first call date, issue date, `available_at` | Mergent FISD | F06, F08, F22 |
| `revision_counts` | `region` (US, GLOBAL), `date`, up and down counts, `available_at` | I/B/E/S | F29 |
| `events` | `gvkey`, `event_date`, `event_type` (`hy.events.EventType`), `available_at` | earnings and rating calendars | F14 |
| LBO event list | `gvkey`, deal date, `available_at` | SDC or SEC SC 13E-3 | F08 tests |
| default list | `gvkey`, default or distressed-exchange date, `available_at` | Moody's DRD or own list | F21 tests |

## 3. New panels built from TRACE
| Panel | Columns | Builder | Factors |
|---|---|---|---|
| `trace_daily_flow` | `date`, `cusip`, `cust_sell_par`, `cust_buy_par`, `cust_sell_n`, `cust_buy_n`, `available_at` | `hy.factors.f05_flow_pressure_reversal.daily_flow_from_trades`; pass the WRDS load lag (about 5 weeks) as `load_lag`. Side data starts about 2012. | F05 |
| `trace_trades` | `cusip`, `trade_time`, `price`, `par`, `available_at` | `hy.factors.f13_realized_illiquidity.trades_from_trace` | F13 |
| `bond_daily` | `cusip`, `date`, `g_spread` (par-weighted mean of the day's trades), `par_volume`, `n_trades`, `available_at` = trade day + 1 | new export | F02, F14, F15, F18, F20, F22 |

## 4. Macro and market series
One long panel, `macro_series` (`series_id`, `date`, `value`, `available_at`), serves F25 to F30. Several vintages per date are allowed. Store first-release vintages (ALFRED) where a series is revised.

| Series | IDs | Factors |
|---|---|---|
| Treasury and TIPS | `DGS10`, `DFII10`, `T10YIE`, `DGS5`, `T10Y3M` | F27, F28 |
| HY spreads | `BAMLH0A0HYM2` and the rating buckets `BAMLH0A1HYBB`, `BAMLH0A2HYB`, `BAMLH0A3HYC` and the others the F25 spec lists. FRED serves about 3 years: full history needs an ICE licence | F25, F27 |
| HY excess return | `H0A0_XR` (ICE H0A0 daily excess return) | F25 |
| VIX | `VIXCLS` | F25, F28, F30 |
| Bank lending survey | `DRTSCILM` | F28 |
| PMI | `ism_pmi`, `global_pmi` (licensed); `philly_gac` as the proxy | F29 |
| Dealer positions | NY Fed primary dealer net corporate positions | F25 |
| Other F25 inputs | CDX IG 5y, EM and G10 bond and equity total return indices, the three structural series | F25 |

F29 uses short IDs (`ism_pmi`, `global_pmi`, `philly_gac`). The other modules use FRED IDs. Keep both naming forms in the one panel.

## 5. Other optional panels
| Panel | Columns | Factors |
|---|---|---|
| `hy_index_return` | `date`, `excess_return`, `available_at` | F26 |
| `sector_prices` | `gsector`, `date`, `ppi_input`, `price_output`, `available_at` (release lag 31 days, our choice); map in the F23 spec | F23 |
| `etf_flows`, `etf_holdings` | see the F12 spec; holdings history needs a vendor | F12 |
| `macro_lever` | `date`, `macro_lever`, `available_at` | F08 |
| `s1_residual` | `date`, `cusip`, `z`, `available_at` | F16 |
| `cell_history` | cache of `f24_cell_percentile.cell_history` | F24 (speed only) |

## 6. Factors that run on today's panels
F04, F10, F17 and F24 need only `bond_panel`, `ratings`, `leverage` and `gics`. F06, F15, F20 and F22 run on `bond_panel` and improve with `bond_daily` and `bond_terms`.
