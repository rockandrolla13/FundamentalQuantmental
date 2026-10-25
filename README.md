# HY Analyst

A high yield bond analyst in code. It finds bonds whose price does not match the issuer's credit risk. For each issuer it reads the filings, the bond prices, the Treasury curve and macro forecasts. It then judges the issuer and compares each bond with similar bonds and with the high yield market. The output is a ranked verdict with the coming events that could move the price.

The purpose of this repository is the **methodology**. The data is plugged in through one connector, so the same analyst runs on another machine with another data source.

## What it does

1. **Collect the facts** as they were known on the decision date: filings, quarterly financials, bond prices, the Treasury curve, forecasts.
2. **Judge the issuer:** earnings quality, liquidity and refinancing, capital structure, the duration mismatch between costs and revenue ("two clocks"), cases under macro paths, valuation and recovery.
3. **Compare the price:** the bond's spread against the median of bonds in the same sector, rating and maturity, and against the high yield index.
4. **Give a verdict:** 18 estimates in six weighted groups give the alpha: one weighted number in bp a year, before trading costs. One of these estimates is the risk premium test: does the spread pay enough for the bond's risk, at the price the high yield index pays for risk? The verdict also carries a gate, the catalysts inside the horizon, and the decision against holding cash.

The full method is in `docs/methodology.md`. The per-filing rulebook is `docs/framework.md`. Each design choice has a decision page in `docs/decisions/`.

## What the evidence says

- The peer gap ranks bonds within a spread level. It holds in 3 of the 4 stress windows (2008, 2015, 2020, 2022). It does not forecast the hedged return on its own. Write-up: `docs/writeup/backtest_peer_line.pdf`.
- Carry earns most of the return. At 15 bp of trading cost, the peer-gap-plus-carry book earns about 3.7% a year (Sharpe 0.48). "Buy the widest" earns about 4.1% (Sharpe 0.37).
- The predicted return sizes do not match realised returns. The size calibration (`hy/calibration.py`) refits that link each month. On the current data it says "rank only": use the analyst to rank bonds, not to size positions. Decision page: `docs/decisions/2026-10-23-size-calibration.md`.

## Layout

| Path | What it holds |
| --- | --- |
| `hy/` | The methodology, one module per layer: `state` (issuer quantities, one definition each), `fairspread`, `peers`, `recovery`, `forward`, `clocks`, `groups` (the combined score), `calibration`, `backtest`, `events` |
| `hy/data/` | The data module: typed records, the point-in-time rule, the source protocols, the `DataView`, the config and the adapters |
| `hy/sources/` | The current adapters' vendor code (WRDS Compustat and TRACE, EDGAR, XBRL, Treasury.gov, public forecasts) |
| `scripts/` | Entry points: the issuer process, memos, backtests, walk-forward, calibration, golden check |
| `tests/` | About 500 tests, including a whole-analyst run on made-up data |
| `docs/` | Methodology, framework, data contract, decision pages, write-ups (`docs/writeup/*.pdf`) |
| `research/` | One card per source (papers and books) and the reading list |
| `reviews/` | Architecture reviews |

## Set up

Python 3.12. Install the package and the test extra:

```
pip install -e ".[test]"
python3 -m pytest -q
```

The tests need no vendor data. The whole-analyst test runs on made-up data with the network off.

## Plug in your data

The analyst reads every input through one `DataView(source, decision_time)`. The view returns only what was public by the decision time.

1. Read `docs/data_contract.md` (PDF: `docs/writeup/data_contract.pdf`). It lists every data kind, every field, its units, and the meaning of `as_of` and `available_at`.
2. Write one class that implements the protocols in `hy/data/source.py`. `hy/data/sources.py` has two examples: `WarehouseSource` (the local caches) and `FakeSource` (memory).
3. Pass it to the run: `process.run(tickers, end, pairs, view=DataView(YourSource(...), decision))`.
4. Point cached runs at your data folder with `HY_DATA_ROOT=/path/to/data`. Set `HY_OFFLINE=1` to forbid any network access.

When an issuer lacks quarterly financials, its later steps show as blocked with the reason, and the run continues for the others.

Vendor data is not in this repository. `data/raw/` is git-ignored.

## Run it

All commands run from the repository root.

| Task | Command |
| --- | --- |
| Issuer process and memos | `PYTHONPATH=. python3 scripts/process.py --tickers CRWV ORCL HCA THC CCL NCLH MGM WYNN` |
| Peer-line backtest and quarterly books | `PYTHONPATH=. python3 scripts/backtest_peer_line.py --cost-bp 15` |
| Backtest write-up figures and tables | `PYTHONPATH=. python3 scripts/backtest_peer_report.py` |
| Refit the return-size calibration | `HY_DATA_ROOT=/path/to/data PYTHONPATH=. python3 scripts/calibrate_sizes.py` |
| Walk-forward (quarterly replay) | `PYTHONPATH=.:scripts python3 scripts/walkforward.py all` |
| Golden check (outputs unchanged) | `PYTHONPATH=.:scripts python3 scripts/golden_check.py check` |

The golden check reruns the 8-issuer process and the backtest summary, and compares every number with a saved snapshot. Run it after any change that should not move a number.

## Rules the code follows

- **Point in time.** Every record carries `as_of` and `available_at`. One guard (`hy/data/pit.py`) raises `LookAheadError` when a model reads a value that was not yet public.
- **One definition per quantity.** LTM, FCF, the high yield index and leverage each have one home in `hy/state.py`. Leverage has one definition per use: lease-adjusted for the issuer, the Compustat panel for peer cells.
- **Every formula cites its methodology section.** Every claim traces to a research card or a test.
- **A finding that changes no section of the methodology is not finished.**

## Status and known limits

- The rating class after February 2017 is implied by leverage, because the S&P rating series in the local data ends then.
- Spreads are G-spreads, not option-adjusted spreads. Most high yield bonds are callable.
- In the local data, six of eight issuers report no lease liabilities. Their lease-adjusted leverage is too low.
- The pipeline still lives in `scripts/`. Moving it into `hy/pipeline/` is the next refactor step.

The vendor-derived memos in `docs/writeup/` hold numbers from licensed data (WRDS: TRACE, Compustat). Check your licence terms before you redistribute them.
