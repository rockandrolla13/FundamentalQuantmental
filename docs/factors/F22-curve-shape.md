# F22. Credit curve shape against level (term premium)

## 1. Header
- **Rank:** 22 of 30, Tier 4 (proposal from the user's own desk plans, no test in any source).
- **Status:** NEW. It extends S4 capital structure relative value (Section 8) from the bond off its curve (F06) to the shape of the whole issuer curve. It reuses the F06 issuer curve fit.
- **Sources (all under `/home/ak/Documents/Quant Credit/`):**
  - `Factors/Credit Factor Framework` (no extension, a PDF: the user's own v0.85 draft), PDF pp. 14 to 15. PDF pages equal printed pages.
  - `Factor_Model_Related (1).pdf`, PDF pp. 14 to 15. The text on these pages is the same as the Framework text.
  - `Credit Relative Value & Cross Asset Arbitrage Business Plan Master Sheet.xls`, sheet `Tools`, column "Credit Relative Value", items 1 to 4 and 7, and the data note in the row "Curve Tool(s)". Sheet `Budget 2009` holds the hit ratios.
  - `Macro Liquid Credit Business Plan - Alaph Capital (1).docx`, section "Credit Relative Value: Long /Short & Term Structure Trades", "Trade Identification".
  - Curve form for the curvature fit: Elton, Gruber, Agrawal, Mann (2004), `Factors/1-s2.0-S0378426604001074-main (1).pdf`, eq. 2, PDF p. 5.
- **Reader blocks:** B-F13, A1-F7, D-F8, D-F9.
- **No backtest.** None of these sources holds a backtest or a statistic. The Framework gives one narrative example (November 2022, p. 15). The xls gives budget hit ratios for planned trades: 0.75 for "Curve Trades" and 0.9 for "HY Curve Roll Trades" (`Budget 2009`, column "Hit Ratio"). These are assumptions, not results.

## 2. Claim
Among US high yield issuers with three or more bonds of one seniority, an issuer whose 5s10s spread slope sits above the slope that its 2-year spread level predicts earns a higher long-end-minus-short-end excess return over the next 3 months. The sign is positive.

## 3. Definition
**What the sources say.**
- Slope (Framework eq. 1, p. 14): Slope = 10yr spread − 2 or 3yr spread. PC2 "represents long risk on front-dated bonds" and "short risk on long-dated bonds". It "will also do poorly when the term structure aggressively inverts" in broad-based stress (p. 14).
- Curvature (p. 15, as written): Curvature = s₅ − 0.5 s₁₀ + 0.5 s₂. The text calls it a control variable and links it to the Cochrane and Piazzesi tent factor (p. 15).
- Term premium, the "directionless slope" (p. 15): regress the 5s10s slope on the 2y spread, α + β·2s + ε = 5s10s, and TP = 5s10s − β·2y. "Higher TP rankings (level and percentile) should imply higher returns on duration" (p. 15).
- xls `Tools`: (1) "Shape of Curve vs Level of Spreads - z score", (2) "Shape of Curve vs Cross Section of Curves (Spread Bucket) - z score", (3) "Shape of Curve vs Bond Basis", (4) "Shape of Curve vs Volatility of Spreads", (7) "Curve Reports (steepest, flattest on own history and versus cross section)". Data: "Single Name Spreads with at least 3 different tenors (3,5,10yr) with at leat 1yr of data".
- docx "Trade Identification": "level of curves / fly versus level of spreads or volatility of spreads". The trades are CDS curve trades, sized "duration neutral, beta neutral or ad-hoc".

**Issuer curve (F06, imported).** Per issuer and seniority, fit the F06 forward shock curve on the par-adjusted spreads of all its bonds. Read the fitted spread at 2, 5 and 10 years:

```latex
\hat s_i(T)=a_{0i}+a_{1i}\,\frac{1-e^{-\lambda T}}{\lambda T},\ \lambda=0.4,\qquad
Sl_i=\hat s_i(10)-\hat s_i(5),\qquad L_i=\hat s_i(2)
```

```latex
Sl_i=\alpha_c+\beta_c L_i+\varepsilon_i\ \ \text{(OLS across issuers, one month, cell } c\text{)},\qquad
\mathrm{score}_i=e_i=Sl_i-\hat\alpha_c-\hat\beta_c L_i,\qquad z_i=e_i/\hat\sigma_c
```

Intuition: the slope that the front-end level does not explain is a premium for holding the issuer's long end.
- **Cross-section (our choice).** The source does not say if the regression runs over time or across names. Its examples are market curves over time. We run it across issuers each month, as reader B-F13 proposes. Cell c is the rating class (actual, else leverage-implied, from F06). A class with fewer than 10 issuers uses the pooled regression of all issuers (our choice). Fewer than 10 issuers in total: no score.
- **Slope and level (source p. 15).** Slope 5s10s, level 2y. Option `slope_def="2s10s"` uses eq. 1 (p. 14) instead, with the same 2y level.
- **Curvature (our choice: tent form).** s₅ − 0.5(s₂ + s₁₀). The source as written has +0.5 s₂ (p. 15). That form is not a butterfly, so we keep it only as option `curvature_form="as_written"`. The F06 curve has two parameters. On it the curvature is a fixed multiple of the slope. So for curvature only we fit the Nelson-Siegel form with a hump term, ŝ = a₀ + a₁x(T) + a₂(x(T) − e^{−λT}) (Elton et al. eq. 2, p. 5), λ = 0.4, when the curve has 4 or more bonds (our choice). Curvature is a control (p. 15). Option `control_curvature=True` adds it to the regression.
- **Minimum curve (xls).** 3 bonds, "at least 3 different tenors". Our choice: the shortest bond at most 5 years and the longest at least 7 years, so the 2y and 10y points are close to data.
- **Extras (xls items 2, 4, 7).** `z_bucket`: z of Sl within its spread bucket, 5 buckets of L (our choice). `resid_vol`: residual of Sl on the issuer spread volatility, the standard deviation of 12 monthly changes of the issuer median G-spread, at least 6 changes (our choice). `z_own`: z of Sl over the last 12 month ends, all 12 required ("at least 1yr of data"). It is off by default (`history_months=0`) because it refits 12 past months. Item 3 (bond basis) needs CDS. We lack CDS, so we do not build it.

**Sign (our choice, marked).** Two readings exist.
1. Steep for its level means a cheap long end. The Framework supports it: higher TP implies higher returns on duration (p. 15). The positive premium of PC2 (p. 14) is the same statement for the front leg.
2. Inversion means distress. Reader B-F13 adds it. The xls and docx do not say it. The Framework says only that the front-long trade loses when the market curve inverts in broad stress (p. 14). That is a market-level loss condition, not an issuer selector.

**Our choice: reading 1, score = +e.** The output flags `inverted` (2s10s < 0) so the production test can check reading 2 on the negative tail.

## 4. Inputs
| Field | Production table and column | `as_of` | `available_at` lag rule | Status |
|---|---|---|---|---|
| Par-adjusted spread, tier, status | F06 `compute` on `bond_panel`, `treasury_curve`, `bond_terms`, `ratings`, `leverage`, `gics` | month end | as F06 | have |
| Years, mod. duration, G-spread | `bond_panel.years`, `mod_dur`, `g_spread` | month end | panel `available_at` | have |
| Rating class | F06 `_issuer_rating`: `ratings.splticrm`, else `leverage` implied | `datadate` | panel `available_at` | have |
| Single-name CDS curves | none | | | need (the source instrument, not required) |

Only `bond_panel` is required. Without it the result is an empty frame.

## 5. Build steps
1. Filter every panel to `available_at` ≤ `decision_time(as_of)`. Run F06 `compute` with `measure="pas"`. Keep bonds with status `ok`.
2. Add `years`, `mod_dur` and `g_spread` from `bond_panel` at as_of.
3. Per issuer: take the seniority curve with the most `ok` bonds. Apply the minimum curve rule.
4. Fit a₀, a₁ (F06 `shock_basis` and `_ols`). Read ŝ(2), ŝ(5), ŝ(10). Compute Sl, L, 2s10s, curvature.
5. Per rating class (else pooled): OLS of Sl on L. Write e, z, β, the cell.
6. Write extras: `z_bucket`, `resid_vol`, `inverted`, the longest and the shortest bond, the DTS hedge ratio. With `history_months` > 0, write `z_own`.
7. One row per gvkey that F06 scores. NaN score where a step drops it, with `status`.

## 6. Code placement
- **Module:** `hy/factors/f22_curve_shape.py`. `compute(panels, as_of, slope_def="5s10s", curvature_form="tent", control_curvature=False, history_months=0, measure="pas")`.
- **Helpers:** `tenor_spreads`, `curvature`, `ns_curvature`, `slope_residual`, `bucket_z`, `own_history_z`, `spread_vol`, `dts_hedge`.
- **Section to cite:** Section 8 S4.
- **Output columns:** `date`, `gvkey`, `score`, `available_at`, `status`, `seniority`, `n_bonds`, `min_years`, `max_years`, `s2`, `s5`, `s10`, `level`, `slope`, `slope_2s10s`, `curvature`, `beta`, `reg_cell`, `resid`, `z`, `z_bucket`, `spread_vol`, `resid_vol`, `z_own`, `inverted`, `long_cusip`, `short_cusip`, `hedge_ratio`.
- **Reuse:** `hy.factors.f06_issuer_curve_residual.compute`, `shock_basis`, `_ols`, `_issuer_rating`, `SHOCK_LAMBDA`. `hy.backtest.decision_time`, `eligible`.

## 7. Tests
- **Unit.** No look-ahead. Sign: two issuers at one level, one steeper, the steeper gets the higher score. Residual: an exact line Sl = α + βL gives zero residual, one bump gives the top score. Curvature: tent and as-written forms on hand numbers, and the NS fit recovers a hump. Edge cases: no `bond_panel`, a 2-bond issuer, a short tenor span, too few issuers, class fallback to pooled.
- **Evaluation (production machine).** Target: the issuer's long-end bond (7 years or more) excess return minus the DTS-hedged short-end bond excess return, over 3 months (our choice: the sources give no horizon, readers B and A1 use 3). Also the issuer's mean excess return. Pass: monthly rank IC > 0 after costs in at least 3 of the 4 cycles (`hy.signals.passes_cycle_test`), Newey-West t > 2 on the long-short return (B-F13). Check reading 2: the bottom decile with `inverted` true against its rating class.

## 8. Risks
- **No evidence.** The sources are plans. The Framework talks about rates and EM curves for TP. Its credit claim is a proposal.
- **Nonlinear level effect.** HY curves flatten and invert as the level rises (Framework p. 14). A linear β leaves this in e. The rating class cells take some of it out.
- **Distress cut.** F06 drops bonds above 1,000 bp. So the most inverted curves never enter.
- **Calls.** Long callable HY bonds trade to the call. F06 drops in-the-money calls. Callable bonds below the call price still bias the long end.
- **Sparse curves.** Many HY issuers have 1 to 3 bonds (B-F12). Few pass the 3-bond and span rule.
- **Overlap.** F06 uses the same fit. F06 is a bond off its curve, F22 is the curve itself. The source gives no correlation. Overlap with maturity and roll-down (D-F8) and with F10 carry (roll-down) is likely.
- **Costs.** A curve trade pays bid-ask on two bonds. The DTS hedge ratio can be large on steep curves.

## 9. Open questions
1. **Time series or cross-section.** The source is silent. Default: cross-section per month (B-F13). D-F9 proposes a market-level timing signal. A sector curve variant can reuse `slope_residual` over time.
2. **Sector by rating curves for 1- and 2-bond issuers (A1-F7, D-F8).** Default: issuer curves only. Reason: a pooled curve has no issuer premium to score.
3. **Score scale.** Default: e in spread units (decimal). z is in the output.
4. **Quadratic level term.** Default: linear, as the source. Test a quadratic L term on the production machine.
