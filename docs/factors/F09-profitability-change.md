# F09. Profitability change over 5 years

- **Rank:** 9. **Tier:** 1 (tested in credit, buildable now). **Status:** NEW. A quality trend, not a level. It extends S2 (methodology Section 8, S2 fundamental momentum).
- **Source:** Kelly, Palhares, Pruitt (2021), "Modeling Corporate Bond Returns", SSRN 3720789. File `/home/ak/Documents/Quant Credit/ssrn-3720789.pdf`. PDF page = printed page. Definition: Table A.I (p. 55). Results: Table I (p. 16), Table IX (p. 31). Managed portfolio: eq. 4 (p. 8). Sample and ranking: pp. 13–15.
- **Reader block:** A2-F7 (`research/notes/quant-credit-review/out_A2.md`). Every number below was checked on the source page.
- **Cited origin:** the paper credits the characteristic to Asness, Frazzini, Pedersen (2019), "Quality minus junk" (p. 55, reference p. 49). That paper is not in the folder. We did not open it.

## Claim
In US high yield, issuers whose gross profit over total assets rose over the last 5 fiscal years have higher DTS-scaled bond excess returns over the Treasury hedge in the next month. The monthly rank IC beyond spread is positive.

## Definition
```latex
\mathrm{Prof}_{i,y} = \frac{\mathrm{SALE}_{i,y} - \mathrm{COGS}_{i,y}}{\mathrm{AT}_{i,y}}
\qquad
\Delta\mathrm{Prof}_{i,t} = \mathrm{Prof}_{i,y(t)} - \mathrm{Prof}_{i,y(t)-W}, \quad W = 5
```
Intuition: an issuer whose gross margin on assets improves becomes safer than its spread says.

What the source says:
- Profitability is "sales minus cost-of-goods-sold, divided by assets for non-financials" (Table A.I, p. 55).
- For financials it is "sales minus total expenses plus depreciation, divided by shareholder's equity minus preferred stock" (p. 55).
- "Profitability change is the 5-year change in profitability" (p. 55). The text gives no formula beyond that.
- Each month the paper ranks every characteristic across bonds and maps it to [−0.5, 0.5] (p. 15). The managed portfolio weights each bond by that rank, over the count of bonds (eq. 4, p. 8).
- Returns: credit excess return over a Treasury hedge, divided by max(DtS, 0.25) (eq. 10, p. 14). Horizon 1 month.
- Sample: bonds of the ICE BofA H0A0 (HY) and C0A0 (IG) indices, December 1999 to December 2020. Spreads 50 to 2000 bp, duration at least 0.25 years. 14,600 bonds, 555,894 bond-months (pp. 13–15).

What we decide:
- `y(t)` is the latest fiscal year whose annual record is known at the decision time. `y(t) − W` is matched on `fyear`, not on dates. Our choice: a change of fiscal year end then keeps its year count.
- W = 5 is the default. W = 3 is a parameter for short HY histories (reader block A2-F7). Our choice.
- Minimum history: the issuer needs a valid Prof in both fiscal years `y(t)` and `y(t) − W`. Valid means SALE, COGS and AT present and AT > 0. Years between the two ends may be missing. Our choice.
- Staleness: the latest record must be at most 550 days old at the decision time (`hy.peers.SUST_STALE_DAYS`). Our choice, the rule of the SPiDER input.
- Financials: GICS sectors 40 and 60 (`hy.peers.FIN_SECTORS`) get NaN. Our choice. The financial formula needs Compustat fields we have not mapped. See open questions.
- Score = ΔProf, raw, at issuer level. The column `rank` holds the cross-bond rank mapped to [−0.5, 0.5], as on p. 15. No winsorisation: the rank controls outliers (p. 15).
- Higher score = long. The sign follows Table I: Sharpe +0.60 (p. 16).

## Inputs
| Field | Production table and column | as_of | available_at rule | Have |
|---|---|---|---|---|
| Sales, net | new panel `compustat_annual.sale` (`comp.funda.SALE`) | `datadate` (fiscal year end) | max(panel `available_at`, datadate + 90 days) | need |
| Cost of goods sold | `compustat_annual.cogs` (`comp.funda.COGS`) | `datadate` | as above | need |
| Total assets | `compustat_annual.at` (`comp.funda.AT`) | `datadate` | as above | need |
| Fiscal year | `compustat_annual.fyear` (`comp.funda.FYEAR`) | `datadate` | as above | need |
| GICS sector | `gics.gsector`, `indfrom`, `indthru` | `indfrom` | panel `available_at` | have |
| Issuer key, eligibility | `bond_panel` `gvkey`, `carried`, `years`, `yield`, `price`, `g_spread`, `mod_dur` | `date` | panel `available_at` | have |

`compustat_annual` columns: `gvkey`, `datadate`, `fyear`, `sale`, `cogs`, `at`, `available_at`. Pull it with the filter of `hy/sources/peer_data.annual_ebitda` (`indfmt = 'INDL'`, `datafmt = 'STD'`, `popsrc = 'D'`, `consol = 'C'`). Keep one row per (gvkey, fyear). The 90-day lag is `ANNUAL_LAG_DAYS` of `hy/sources/peer_data.py`. `compute` enforces it again. `annual_ebitda` has no SALE, COGS or AT, so it cannot serve. No proxy replaces them.

## Build steps
1. Pull `compustat_annual` from fiscal year 1996, so ΔProf with W = 5 exists from about 2002.
2. At each month end t, keep rows with effective `available_at` <= `decision_time(t)`. Keep the last row per (gvkey, fyear).
3. Compute Prof per row. Set NaN where AT <= 0 or a field is missing.
4. Per gvkey, take the latest fiscal year `y(t)`. Drop the issuer if that record is older than 550 days.
5. ΔProf = Prof(y(t)) − Prof(y(t) − W). NaN if either end is not valid.
6. Set NaN for issuers in GICS sector 40 or 60 at t.
7. Copy ΔProf to each eligible bond of the issuer in `bond_panel` at t. Compute `rank` across those bonds.

## Code placement
- `hy/factors/f09_profitability_change.py`. `compute(panels, as_of, window=5) -> pd.DataFrame`.
- Output columns: `date`, `cusip`, `score`, `available_at`, `gvkey`, `rank`, `prof`, `prof_lag`, `fyear`, `fyear_lag`.
- Helpers: `profitability(sale, cogs, at)`, `profitability_change(annual, decision_time, window)`, `rank_unit(x)`.
- Docstrings cite methodology Section 8 (S2) and Section 11 (backtest design), with Table A.I p. 55.
- Reuses `hy.backtest.decision_time`, `hy.backtest.eligible`, `hy.peers.sector_at`, `hy.peers.FIN_SECTORS`, `hy.peers.SUST_STALE_DAYS`, `hy.sources.peer_data.ANNUAL_LAG_DAYS`.

## Tests
- No look-ahead: a 10-K with `available_at` after the decision time, or with datadate + 90 days after it, changes no score.
- Sign: a synthetic issuer whose Prof rises from 0.20 to 0.30 scores above one whose Prof falls.
- Edges: fewer than W + 1 fiscal years gives NaN. AT <= 0 gives NaN. A missing `compustat_annual` or `gics` panel gives an empty frame. A financial issuer gives NaN. A stale latest record gives NaN. W = 3 scores an issuer with 4 years.
- Helpers: Prof and ΔProf against a hand computation. `rank_unit` maps the lowest to −0.5 and the highest to +0.5.
- Evaluation: monthly rank IC of the score beyond `g_spread` (`ic_beyond`), 1-month horizon (p. 14), DTS-scaled excess return, after cost from `bid_ask_pts` and turnover. Pass: positive in at least three of the four `CYCLE_WINDOWS`. Second test (reader block): quintile sort within rating class, long-short 3-month excess return with t > 2, and t > 2 on ΔProf in a joint regression with S2.

## Risks
- Weak multivariate evidence. Table I Sharpe 0.60, significant at 1% (p. 16). The level alone has Sharpe 0.14, not significant (p. 16). In the IPCA model the impact is 0.03, not significant, the joint lowest of the 30 instruments (Table IX, p. 31). Other characteristics may carry the same information.
- Mixed sample. The paper pools IG and HY and reports no HY-only Sharpe for this characteristic.
- The signs of Profitability (level) differ between DtS-scaled and unscaled returns (p. 17). The source says this for the level only, not for the change.
- Short histories. Many HY issuers have fewer than 6 fiscal years in Compustat. W = 5 loses them. W = 3 keeps more names but is not the source's test.
- `comp.funda` is the current view, not point in time. A restatement can replace an old year (note in `annual_ebitda`).
- Turnover is low: the score changes once a year per issuer. Cost is small. The source gives no correlation with other characteristics.

## Open questions
- Form of the change. The source says "5-year change in profitability" (p. 55). Our choice: the difference of the two ratios. Asness et al. (2019) may scale the change in gross profit by lagged assets instead. We did not open that paper. A test of both forms settles it.
- Financials. Our choice: exclude them. The financial formula needs Compustat "total expenses" and the equity fields. We did not verify the mnemonics.
- Window. Our choice: W = 5 as the base case, W = 3 as a robustness run for coverage. Report the coverage of each.
- Bond or issuer rank. The source ranks bonds (p. 15). Our score is the issuer value. `rank` follows the source across bonds.
