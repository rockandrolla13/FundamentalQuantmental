# F21. Refinancing headroom against cyclicality

- **Rank:** 21. **Tier:** 4 (definition with no backtest, buildable now). **Status:** NEW. It sizes the two-year refinancing need against the issuer's own worst year. It feeds methodology Section 4.2 (`wall_cover_h`), Section 9 (event risk) and `docs/framework.md` F4 (liquidity, maturities, and refinance access).
- **Sources.** Pages are PDF pages. PDF page = printed page, except where the line says otherwise.
  - Morgan Stanley, "Stressing Growth and High Yield" (Sheets et al., 19 Aug 2011). File `/home/ak/Documents/Quant Credit/Screening Models/MS Credit Stategy Screens/MS_Sensitivity of EBITDA to growth & Mapping EBITD declines to refinancing needs (Aug 2011).pdf`, pp. 5–7.
  - Morgan Stanley, "High Yield: Looking for the Best in Stress" (30 Sep 2011). File `.../MS_Cyclicality vs. Liquidity (Sep 2011).pdf`, p. 4.
  - "Specification Draft: European Single Name Fundamental Analysis" (v. 080212), Step 4B. File `/home/ak/Documents/Quant Credit/Screening Models/Specification Draft_European Single Name Fundamental Analysis (v. 080212).pdf`. PDF p. 12 = printed p. 11.
  - Extra column only: Morgan Stanley, single-name screens (Apr 2011), file `.../MS_Single name screens across fundamentals and valuations (Apr 2011).pdf`, p. 3.
- **Reader blocks:** H-F4, and H-F14 for the breadth column (`research/notes/quant-credit-review/out_H.md`). Every number below was checked on the source page.
- **Corrections to the reader blocks.** (1) The European spec text sits on PDF p. 12 (printed p. 11), not PDF p. 11. (2) The 70% breadth line sits on p. 3 of the Apr 2011 note, not p. 2. (3) H-F4 names "framework.md F3" for liquidity sizing. The rule is F4.

## Claim
In US high yield, issuers whose two-year refinancing headroom exceeds their worst one-year EBITDA fall of the last 10 years default less often in the next 24 months than issuers below that line, at equal leverage. **No source tests this.** The MS notes are descriptive. The first test is a default-prediction test on the production machine. A return claim waits for that test.

## Definition
```latex
L_i = \mathrm{CHE}_i + \mathrm{RCF}_i, \qquad
A_{i,k} = L_i + k\,(E_i - \mathrm{XINT}_i - \mathrm{CAPX}_i) - \sum_{j=1}^{k} \mathrm{DD}j_i, \quad k = 1, 2
```
```latex
H_i = \operatorname{clip}_{[0,1]}\Big(\min_{k=1,2} \frac{A_{i,k}}{w_k E_i}\Big), \qquad
C_i = -\min_{y \in Y_i} \max\Big(\frac{E_{i,y} - E_{i,y-1}}{E_{i,y-1}}, -1\Big), \qquad
S_i = H_i - C_i
```
Intuition: `H` is the largest two-year EBITDA cut the issuer survives without the market. `C` is the worst one-year cut it actually had. `S > 0` means the issuer can absorb a repeat of its worst year.

What the source says:
- Refinancing risk occurs "when debt due over the next two years cannot be covered by the combination of (a) cash and, (b) LTM EBITDA, less LTM interest expense and Capex" (Aug p. 5). Negative cash generation can force refinancing with no maturity due (Aug p. 5).
- The two tests: "i) negative free cash flow burns through cash balances; or ii) available liquidity cannot cover bond maturities" in the window (Sep p. 4). The European spec says "bond and loan maturities" (p. 12).
- Inputs: cash, LTM EBITDA, LTM interest expense, LTM capex (Sep p. 4, European spec p. 12).
- The x-axis is the "Cumulative Linear EBITDA Decline Necessitating External Finance in Next 24 Months" (Aug p. 7, Exhibit 14). Sep p. 4 calls it the "Two-Year Cumulative EBITDA Decline Needed to Force Refi". Both axes run from 0% to −100% (Sep p. 4) or −70% (Aug p. 7).
- Cyclicality is the "worst year-on-year LTM EBITDA performance over the last decade" (Sep p. 4). Its axis runs from +20% to −100% (Sep p. 4).
- Names "above the line" need "one to two years of EBITDA declines worse than the worst year-on-year decline in the past ten years" before they must refinance. They are "candidates for adding risk". Names below are "candidates for reducing risk" (Aug p. 6).
- Gaps: the model ignores loan maturities and liquidity "from a parent or RCF" (Sep p. 4). The European spec asks where to get revolver data (p. 12).
- Universe: 100 European HY corporates (Aug p. 5). With zero EBITDA growth, "roughly a fifth of XOver constituents" must refinance (Aug p. 5).

What we decide (all "Our choice"):
- Path. "Linear" decline (default): year-k EBITDA is `E (1 − d k / 2)`, so the cut reaches `d` at month 24. Then `w_1 = 1/2`, `w_2 = 3/2`. A `flat` option cuts both years by `d` (`w_1 = 1`, `w_2 = 2`), the H-F4 reconstruction.
- The test runs at the end of year 1 and year 2. One cumulative test covers both MS conditions: cash burn and maturity cover.
- Maturities: Compustat `dd1` and `dd2`. They hold all long-term debt, bonds and loans. This follows the European spec, not MS (bonds only).
- Revolver: optional column `revolver_undrawn`. Missing or NaN counts as 0, flagged in `revolver_missing`. This matches the MS model (no RCF). A parameter `use_revolver=False` forces 0.
- Clip: `H` is clipped to [0, 1], the range of the source axes. `headroom_raw` keeps the unclipped value. `fails_at_zero` is True where `min_k A_k < 0`.
- `E <= 0`: `H = 0` when `fails_at_zero`, else NaN. A cut of a negative EBITDA has no meaning.
- Cyclicality uses annual `oibdp`, not quarterly LTM. `Y_i` is the fiscal years `y(t) − 9` to `y(t)` with a prior year of positive EBITDA. Each change is floored at −100%, the source axis floor. Minimum 3 changes, else NaN.
- Score `S = H − C` in fractions. `cover_ratio = H / C` where `C > 0` is a second form (Aug p. 5 and p. 6 scale stress to each name's worst experience).
- Financials (GICS 40 and 60, `hy.peers.FIN_SECTORS`) get NaN.
- Breadth (H-F14): `delever_breadth` is the share of scored issuers whose `debt / oibdp` fell from `y(t) − 1` to `y(t)`. `breadth_peak` is True above 70%, the level that "has recently marked the peak of market breadth" (Apr 2011 p. 3). One value per month, not a bond score.

## Inputs
| Field | Production table and column | as_of | available_at rule | Have |
|---|---|---|---|---|
| Cash and short-term investments | new panel `compustat_annual.che` (`comp.funda.CHE`) | `datadate` | max(panel `available_at`, datadate + 90 days) | need |
| Interest expense | `compustat_annual.xint` (`XINT`) | `datadate` | as above | need |
| Capital expenditure | `compustat_annual.capx` (`CAPX`) | `datadate` | as above | need |
| Debt due in years 1 to 5 | `compustat_annual.dd1` … `dd5` (`DD1`–`DD5`). `dd3`–`dd5` optional | `datadate` | as above | need |
| Undrawn revolver | `compustat_annual.revolver_undrawn` (10-K text, S5 parsing). Optional | `datadate` | as above | need |
| EBITDA, debt | `annual_ebitda.oibdp`, `debt`, `fyear` | `datadate` | as above | have |
| GICS sector | `gics.gsector`, `indfrom`, `indthru` | `indfrom` | panel `available_at` | have |
| Issuer key, eligibility | `bond_panel` `gvkey`, `carried`, `years`, `yield`, `price`, `g_spread`, `mod_dur` | `date` | panel `available_at` | have |

`compustat_annual` is the F09 panel (`gvkey`, `datadate`, `fyear`, `available_at`) with the columns above added. Pull it with the filter of `hy/sources/peer_data.annual_ebitda`. `compute` enforces the 90-day lag (`ANNUAL_LAG_DAYS`) again. The PD test also needs a default panel: `gvkey`, default or distressed-exchange date, `available_at` (need).

## Build steps
1. At month end t, keep rows of `compustat_annual` and `annual_ebitda` known at `decision_time(t)`. Keep the last row per (gvkey, fyear).
2. Per gvkey, take the latest fiscal year `y(t)` of `compustat_annual`. Drop it if older than 550 days (`SUST_STALE_DAYS`).
3. Take `E = oibdp` of `y(t)` from `annual_ebitda`. Compute `L`, `A_1`, `A_2` and `H`.
4. Compute the year-on-year changes of `oibdp` over `y(t) − 9` to `y(t)`. `C` = minus the worst change.
5. `S = H − C`. NaN for financials. Compute `delever_breadth` over the scored issuers.
6. Copy `S` to each eligible bond of the issuer in `bond_panel` at t.

## Code placement
- `hy/factors/f21_refinancing_headroom.py`. `compute(panels, as_of, path="linear", use_revolver=True)`.
- Output: `date`, `cusip`, `score`, `available_at`, `gvkey`, `headroom`, `headroom_raw`, `cyclicality`, `cover_ratio`, `n_changes`, `fyear`, `liquidity`, `mat_2y`, `mat_3_5y`, `fails_at_zero`, `revolver_missing`, `mat_missing`, `delever_breadth`, `breadth_peak`.
- Helpers: `headroom(cash, revolver, ebitda, xint, capx, dd1, dd2, path)`, `yoy_changes(ebitda)`, `cyclicality(ebitda, last_fyear)`, `delever_breadth(ebitda, last_fyear)`, `issuer_scores(panels, dt, path, use_revolver)`. `issuer_scores` serves the issuer-level PD test.
- Docstrings cite methodology Section 4.2 and Section 9. Reuses `hy.backtest.decision_time`, `eligible`, `hy.peers.sector_at`, `FIN_SECTORS`, `SUST_STALE_DAYS`, `hy.factors.f09_profitability_change.known_annual`.

## Tests
- Unit: no look-ahead (a 10-K after the decision time changes nothing). Sign: a cash-rich, stable issuer scores above a cash-poor, cyclical one. Edges: missing panel gives an empty frame. `E <= 0`. Fewer than 3 changes. Missing revolver and maturities flagged. Financials NaN. Hand checks of `H`, `C` and breadth.
- Evaluation (production machine). Primary: PD test. Logit of 24-month default or distressed exchange on `S`, with leverage and Merton DD as controls, US HY 2003–2024 (H-F4). Pass: `S` adds at least 0.02 out-of-sample AUC. Report the 24-month default rate by `S` quintile. It must fall from the bottom to the top quintile. Secondary: top-minus-bottom `S` quintile inside rating class, 6-month excess return, positive in at least three of the four `CYCLE_WINDOWS` (H-F4).

## Risks
- No return evidence and no default test in any source. The MS default mapping (Aug p. 6, Exhibit 11) is "subjective" by the authors' own word (Aug p. 5).
- Compustat `comp.funda` is not point in time. `dd1`–`dd5` miss maturities that a refinancing after the 10-K moves.
- Annual EBITDA hides an intra-year trough. `C` is then too small and `S` too large.
- Overlap with leverage and with `wall_cover_h`. The source gives no correlation.
- The score changes once a year. Turnover and cost are low.

## Open questions
- Path: linear (default) or flat. The axis label says "linear" (Aug p. 7). Run both in the PD test.
- Short-term debt: `dd1` excludes notes payable (`np`). Default: exclude, as the source counts maturities only.
- Revolver: default include where present. The MS model excludes it (Sep p. 4). Compare AUC with and without.
- Form of the score: `H − C` (default) or `H / C`. The source plots `H` against `C` with a line and gives no formula (Aug p. 6).
- Cash taxes and working capital: the source leaves them out. Default: leave them out.
