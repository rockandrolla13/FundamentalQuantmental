# Correia, Richardson and Tuna (2012), "Value Investing in Credit Markets"

SSRN 1800212, London Business School. Conference version for Review of Accounting Studies. The PDF does not print a journal volume or page range. Three facts support the RAST attribution: the PDF metadata title reads "CONFERENCE_RAST_EM2413_Final", the file dates from 16 October 2012, and the acknowledgements thank Jim Ohlson as editor and Itzhak Venezia as discussant (p. 44). Treat "Review of Accounting Studies, 2012" as the brief's citation, not a fact the PDF states. Page numbers below are PDF pages. PDF page = printed page + 1.

## Claim
A default probability from accounting and equity data, mapped into a theoretical spread, predicts credit returns (pp. 3–4). The log gap between the actual spread and the theoretical spread mean-reverts. About 67% of the gap closes in six months (p. 27). A wide actual spread against the theoretical spread predicts a high credit return over the next one to three months (pp. 30–31). Eight macro and equity risk factors do not explain the long-short return (p. 32). The authors call this "value" in credit, the analogue of book-to-price in equities (p. 3).

## Method
Four steps: forecast a physical PD, map it to a theoretical spread, take the log gap, and test whether the gap predicts returns (pp. 10–13).

**Step 1. Physical PD from distance to default (pp. 5–6, 17).**

```latex
PD_{i,t} = \Pr\left[ -\frac{\ln(V_{A,i,0}/X_{i,t}) + (\mu_i - \sigma^2_{A,i,t}/2)\,t}{\sigma_{A,i,t}\sqrt{t}} \ge \varepsilon_{i,t} \right]   \quad (3)
E[PD^{D2D}_{i,t}] = f\left( \frac{\ln(V_{A,i,0}/X_{i,t})}{\sigma_{A,i,t}\sqrt{t}} \right)   \quad (10)
```

Intuition: default is more likely when the asset value sits few volatility units above the debt. The D2D inputs (p. 17):
1. X: debt in current liabilities `dlcq` plus half of long-term debt `dlttq`, from the latest quarter, as in Bharath and Shumway (2008).
2. V_A: market equity from CRSP plus the book value of X.
3. σ_A: the standard deviation of the prior 12 monthly stock returns, de-levered with market leverage.
4. Drift μ: set to zero.

f is a logistic map. The authors fit each model as a Shumway (2001) discrete-time hazard on bankruptcy within 12 months (pp. 15–16). They re-fit on an expanding window each month, so every forecast is out of sample (p. 15, footnote 2). Market data is at month end. Accounting data must be public before the second month after the quarter end (p. 15).

The paper compares four PD models: D2D, BCM-BOTH (Beaver, Correia and McNichols 2012, accounting and market ratios with loss interactions), BS (Bharath and Shumway 2008, with the naive DD), and the Moody's KMV EDF taken as given (pp. 17–20). Five more models, among them Altman, Ohlson and agency ratings, did worse and are not tabulated (p. 16).

**Step 2. Physical PD to theoretical spread (pp. 8–9, 24).**

```latex
CPD_{i,t} = 1 - (1 - PD_{i,t})^{T}
CQDF_{i,t} = N\left[ N^{-1}(CPD_{i,t}) + \lambda \sqrt{r^2_{i,t}}\,\sqrt{T} \right]   \quad (7)
CS^{*}_{i,t} = -\frac{1}{T} \ln\left[ 1 - (1 - R_{i,t})\,CQDF_{i,t} \right]   \quad (6)
```

Intuition: shift the physical default point up the normal curve by a risk premium, then price a zero-coupon bond with that risk-neutral default rate. The constants are fixed across firms and models: T = 5, R = 40%, market Sharpe ratio λ = 0.5, and "average asset correlation" 40% (p. 24). The text does not say whether 40% is r or r². Equation (7) holds r² under the root, so the plain reading is r² = 0.40.

**Step 3. Credit relative value (p. 12).**

```latex
CRV_{i,t} = \ln\left( CS_{i,t} \,/\, CS^{*}_{i,t} \right)
```

Intuition: a positive CRV says the market charges more default than the model sees, so the bond is cheap.

**Step 4. Tests (pp. 13, 21, 28).**

```latex
CRV_{i,t+K} - CRV_{i,t+K-1} = \alpha_i + \beta_i\,CRV_{i,t} + \varepsilon_{i,t}   \quad (8)
RET_{i,t+k} = \gamma_t + \gamma_{CRV} CRV_{i,t} + \gamma_{MOMS} MOMS_{i,t} + \gamma_{MOML} MOML_{i,t} + \gamma_{BTM} BTM_{i,t} + \gamma_{SIZE} SIZE_{i,t} + \gamma_{E/P} E/P_{i,t} + \gamma_{BETA} BETA_{i,t} + \epsilon_{i,t}   \quad (14)
RET_{i,t-1 \to t} \approx \frac{CS_{i,t-1}}{12} - Duration_{i,t}\,\Delta CS_{i,t}   \quad (13)
```

Intuition for (8): a negative β_i means the gap shrinks. Intuition for (14): a positive γ_CRV means a cheap bond earns more next month after equity momentum and value controls. Intuition for (13): the credit return is one month of carry less the duration loss on a spread change.

Notes on the tests:
- The authors run (8) bond by bond, with at least 12 months of data (p. 27).
- They run (14) each month as a Fama-MacBeth cross-section in weighted least squares. The weight is −ln(CS), so the regression puts less weight on wide spreads (pp. 29–30).
- MOMS is the prior-month stock return. MOML is the 11-month return before it, with a 3-month half-life weight (p. 28).
- RET is month t+k alone, not a cumulative return (p. 13).
- Portfolios: quintiles of CRV each month, risk-weighted, rebalanced monthly, no costs (p. 31). Table 8 regresses the hedge return on dRP, dTS, dVIX, dIP, MKT, SMB, HML and MOM (pp. 31–32).

## Data
- Bankruptcies: Chapter 7 and Chapter 11, 1980–2010, from four sources (p. 15). Abstract and introduction: 1,767 bankrupt and 194,981 non-bankrupt firm-years (p. 3). Financial SIC codes 6021, 6022, 6029 and 6036 are out. All inputs are winsorised at 1% and 99% (p. 15).
- PD panel: 367 months, January 1980 to July 2010. EDF only from January 1997 (p. 22).
- Bonds: Merrill Lynch corporate index constituents, investment grade and high yield. Per issuer, the authors keep the bond with the largest market value and duration between 3 and 8 years, closest to 5 (pp. 20–21). About 2,000 bonds, 1997–2010. The spread is the Merrill Lynch option-adjusted spread (p. 24).
- Return tests: 149 months, January 1997 to May 2009, with 380 to 459 bonds a month (Table 6, pp. 61–64).
- CDS: DataStream, 5-year senior USD contracts with modified restructuring clauses, January 2005 to April 2010, 484 issuers (p. 21).
- Bond-sample firms differ from the full sample (Table 2, pp. 54–55): ROA 0.0428 against −0.0408, TL/TA 0.6997 against 0.5034, and 19.66% finance firms against 27.92%.

## Result
- **Default ranking (Figure 2, p. 52).** AUC on a constant sample: EDF 0.9325, BCM-BOTH 0.9262, D2D 0.9244, BS 0.9216. EDF is best, but the gaps are small and not significant (p. 23). A PD backed out of actual spreads is worse than EDF (p. 23, unreported).
- **PD models agree.** Average monthly Pearson correlations run from 0.465 to 0.675 (Table 1, p. 53).
- **Spread levels (Table 4, pp. 57–58).** Mean actual spread: 342 bp. Mean theoretical spreads: 148 bp (D2D), 128 bp (BCM), 142 bp (BS), 197 bp (EDF). The model spread is below the actual spread in 85%, 76%, 78% and 71% of bond-months. Pearson correlation with the actual spread: 0.394 (D2D), 0.557 (BCM), 0.545 (BS), 0.651 (EDF).
- **Default skill links to spread skill (p. 26).** Across models, AUC and spread correlation correlate at 0.637 (Pearson) and 0.800 (Spearman).
- **Mean reversion (Table 5, pp. 59–60).** Mean β_i at one month: −0.1692 (D2D), −0.2102 (BCM), −0.2125 (BS), −0.2028 (EDF). The cumulative six-month mean is −0.6456, −0.7440, −0.6584 and −0.6397. Between 71% and 80% of bonds show a significant six-month reversion (p. 27).
- **Cross-section of returns (Table 6, pp. 61–64).** One-month γ_CRV: 0.0012 (t 5.9, D2D), 0.0013 (t 4.69, BCM), 0.0033 (t 6.83, BS), 0.0022 (t 9.1, EDF). At three months: t 1.57, 5.49, 1.37 and 4.63. From month 4 on, only D2D, BCM and EDF stay positive and significant in most months. MOMS is the strongest control: t 7.27 to 8.89 at one month (p. 30).
- **Quintile hedge (Table 7, pp. 65–66).** Month-1 hedge return: 41 bp (D2D), 59 bp (BCM), 77 bp (BS), 44 bp (EDF). Month-1 Sharpe ratio: 1.46, 1.84, 2.44 and 0.94. Month-3 Sharpe ratio: 0.25, 1.20, 0.65 and 0.69. The D2D quintiles are not monotone: the top quintile returns −6 bp in month 1, below quintiles 3 and 4.
- **Risk factors (Table 8, p. 67).** Monthly alpha: 45 bp (D2D, t 7.7), 58 bp (BCM, t 7.85), 80 bp (BS, t 8.99), 43 bp (EDF, t 5.22). Adjusted R²: 0.51, 0.38, 0.10 and 0.64. The hedge return loads positive on dRP and negative on MKT and dIP. The authors explain this as a tilt to low spreads that gains in a flight to quality (p. 33). The return predictability is stronger in NBER recessions (p. 33, unreported).
- **Not carry (p. 40).** The authors regress CRV on the spread level each month and keep the residual. Return predictability is "slightly stronger" with the residual.
- **Costs (pp. 37–38).** Long-short cost estimate: 52 bp to 70 bp, from 18 bp to 27 bp round trip on each leg and a 16 bp borrow fee. Cumulative gross hedge return: 113 bp at 3 months and 169 bp at 6 months. These are the sums of the Table 7 monthly hedges, averaged over the four models. The authors conclude that an institution covers the cost and a retail investor does not.
- **High yield (pp. 40–41, unreported).** The effect holds in investment grade and in high yield. It is "in some cases" stronger in high yield.
- **Robustness (pp. 34–39, unreported).** The results hold with CDS spreads, total bond returns, industry demeaning, a Moody's default list, λ from 0.3 to 0.6, and a rolling firm correlation floored at 0.1 and capped at 0.7.

## What our data says (hy/fairspread.py, hy/signals.py, hy/groups.py, hy/backtest.py, data/raw/backtest, 22 October 2026)
**What the source maps to.** CRV is our Section 7.3 residual: `residuals()` in `hy/fairspread.py` returns ε = log s − log ŝ, with positive meaning cheap. CRT's theoretical spread corresponds to our Section 7.1 anchor alone, with no second stage f_t. CRT shift the default point by λ√(r²)√T in normal space. Our `kappa_by_bucket` instead multiplies expected loss by one ratio per bucket. S1 in `hy/signals.py` uses ε after the conformal gate. E4 "Default the price assumes" in `hy/groups.py` has weight 0.00 until κ_t is fitted.

**What we hold.** A grep for "Correia" in `hy/`, `docs/` and `research/` finds only the reading-list entry in `research/reading-list.md`, Section 8 row. No module computes a Kealhofer CQDF, a D2D, or a CRV from a PD.
- `data/raw/backtest/panel_full.parquet`: TRACE bond-months, 737,379 rows, 34,542 CUSIPs, 3,163 gvkeys, January 2008 to August 2026. It holds a G-spread (`g_spread`), not an option-adjusted spread, with `mod_dur` and `available_at`.
- `data/raw/backtest/results_h6_full.parquet`: realised returns at 6 months, `realised` and `realised_net`, with `cost_rt`. `results_h3_full` and `results_h12_full` cover 3 and 12 months.
- `data/raw/backtest/peer_signals_full.parquet`: 608,191 bond-months. The rating class is actual for 120,849 rows and leverage-implied for 487,286 rows.
- `equity_monthly.parquet`, `leverage_full.parquet` and `sp_ratings.parquet` are as the Bharath and Shumway card describes. There are 141 issuers with D or SD, and the ratings end in February 2017. We hold no market equity and no `dlcq`/`dlttq` split yet. So the D2D inputs V_A and X are one Compustat pull away.
- `hy/backtest.py` already has `ic_beyond`, `cycle_test`, `long_short` and `evaluate`. These run the paper's tests on our panel with no new statistics code.

**What we decide.**
1. Keep the S1 sign and the log form. The paper is direct evidence that a log gap against a default-based fair spread predicts returns with a positive sign.
2. Use the paper's reversion speed as the prior for Section 7.5. A one-month β of −0.17 to −0.21 gives ρ = 0.79 to 0.83 a month. The half-life is then 2.9 to 3.7 months, so the S1 horizon of two half-lives is about 6 to 7 months. This is our arithmetic on the Table 5 means, not a number the paper reports.
3. Do not fix κ by hand. The fixed constants left the model spread below the market spread in 71% to 85% of cases. Fit κ_t from the data, as Section 7.1 already says.
4. Always test the gap net of the spread level. The paper's own carry check (p. 40) is our `ic_beyond` with `g_spread` as the control.
5. Do not rely on the paper's Sharpe ratios for high yield. The paper is mostly investment grade, gives no high-yield table, and reports no return after costs.

**Falsifiable tests on our panel.**
1. **Gap reverts.** Build ε each month from the anchor alone (PD from naive DD, `kappa_by_bucket`). Fit `fit_ar1` per bond with at least 12 months of data. Pass if the median monthly ρ is below 0.9 and at least half of the bonds show significant reversion at six months. CRT report 71% to 80%.
2. **Gap predicts return beyond spread.** Run `ic_beyond(df, "crv", "realised_net", control="g_spread")` at 3 and 6 months. Pass if the IC is positive after costs in at least three of the 2008, 2015, 2020 and 2022 windows (`cycle_test`).
3. **Anchor against full model.** Compare the IC of the anchor-only gap with the S1 residual after f_t. Keep the second stage only if it raises the IC beyond spread. CRT show that the anchor alone is enough in their sample.
4. **Normal shift against ratio.** Fit both mappings on the same PD. Within each rating bucket, regress log(spread ÷ expected loss) on log PD. The Kealhofer form predicts a negative slope, and a constant κ predicts zero. Replace `kappa_by_bucket` with the Kealhofer shift if the slope is significantly negative in most months.
5. **Flight-to-quality exposure.** Regress the monthly long-short S1 return on the change in the BAA minus 10-year spread and on the equity market return. A loading of the same sign as Table 8 says the signal tilts to low spreads. Check whether that tilt survives the conformal gate.

## Limits
- The sample is mostly investment grade. The bond sample has a mean OAS of 342 bp and a median of 187 bp (Table 4, p. 57). The high-yield result is one unreported sentence (p. 41).
- The authors exclude transaction costs from all tables. The cost argument uses investment-grade costs from 2003–2007 (pp. 37–38). High-yield costs are higher.
- The bond universe is index bonds only, one bond per issuer, duration 3 to 8 years. Callable bonds enter through the OAS. We hold a G-spread, so call value sits inside our spread.
- Recovery, λ and r² are fixed across firms. CRV therefore carries recovery and seniority error (pp. 39–40).
- Bankruptcy is the default event. Distressed exchanges and other liability management defaults are absent from the calibration.
- The return regressions end in May 2009. They miss 2015, 2020 and 2022.
- The PDF disagrees with itself in several places:
  - Bankruptcy count: 1,767 (p. 3) against 1,797 (p. 42).
  - CDS issuers: 484 (p. 21) against 453 (p. 42).
  - Bond-data months: 150 (Tables 3 and 4) against 149 (Table 6).
  - Three-month t-statistic range: 1.37 to 4.63 in the text (p. 30), but Table 6 Panel B shows 5.49 for BCM at t+3 (p. 62).
  - Short-term debt: the appendix writes 'DLCC' where the text writes 'DLCQ' (pp. 17, 50).
- pdftotext garbled equations (3), (6), (7), (8) and (14). We rebuilt (3) and (7) from page images of pp. 6 and 9. We rebuilt (6), (8) and (14) from the legible fragments and the table headers.

## Section touched
`docs/methodology.md` Section 7.1 (anchor spread and κ_t), Section 7.3 (log residual), Section 7.5 (residual reversion and half-life), and Section 8 S1 (fair value residual). Estimate E4 "Default the price assumes" in `hy/groups.py`. No decision page yet. A sprint that runs tests 1 to 4 should add one and settle the κ mapping.
