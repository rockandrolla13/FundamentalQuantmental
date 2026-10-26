# F25. Credit-BMI v2: HY index timing composite with dealer positions and a rating-bucket common factor

## 1. Header
- **Rank:** 25 of 30. **Status:** NEW. The user's own design. Candidate replacement for S7, which failed (`docs/decisions/2026-10-24-s7-sector-tilt.md`). S7 tilted sectors. F25 times the whole HY index. **Level:** index, key `index` = `US_HY`.
- **Sources (under `/home/ak/Documents/Quant Credit/BMI/files/`).** `credit_bmi_v2.md` sections 1.2 to 3.7 is the canonical spec. `credit_bmi_v2.pdf` carries the same text with page numbers: Table 1 p. 2, hygiene pp. 2 to 3, normalisation p. 3, horizons p. 3, features and model grid p. 4, purged CV p. 4, shrinkage p. 5, gate p. 5, CQR and ACI pp. 5 to 6, decision rule and costs p. 6, path control p. 6, driver p. 7, validation p. 7. The PDF numbers hygiene 1.3 and normalisation 1.4. The md numbers them 1.4 and 1.5. This page cites PDF pages. `credit_bmi_v2.py` and `credit_bmi_model.py` were read as text only, never run.
- **Reader blocks:** B-F14, B-F15, B-F16, B-F17 (`out_B.md`), A2-F11 (`out_A2.md`), H-F13 (`out_H.md`). Every number below was checked on the PDF page.
- **Evidence is second-hand or synthetic.** The hit rates 62% HY and 67% IG (p. 1), 51% HY and 55% IG for LIBOR-OIS (p. 2), and 66 to 68% aligned against 61% overall (p. 3) come from a Morgan Stanley note that is not in the folder. The coverage 0.899 against 0.90 and the 93% linear picks (pp. 1, 5, 6) come from a synthetic demo. No real-data result exists.

## 2. Claim
When the whole conformal 90% interval of the next 21-day H0A0 excess return lies above the 12 bp round-trip cost, the HY index earns a positive excess return over that horizon. Below minus the cost it earns a negative one. Net Sharpe of the timing position is above zero in at least three of the four cycles.

## 3. Definition
```latex
z^{(k)}_t = \mathrm{clip}\big((x^{(k)}_{t-\ell_k}-\hat\mu^{(k)}_t)/\hat\sigma^{(k)}_t,-8,8\big),\quad
s^{(k)}_t = 20\,[\Phi(\pm z^{(k)}_t)-\tfrac12],\quad
\tilde s^{(k)}_t = (1-\beta_k g_t)\,10\tanh(\kappa s^{(k)}_t/10)
```
```latex
y^{(h)}_t=\sum_{j=1}^{h} r^{exc}_{t+j},\quad
C_t=[\hat q_{\alpha_t/2}(x_t)-Q,\ \hat q_{1-\alpha_t/2}(x_t)+Q],\quad
\alpha_{t+1}=\alpha_t+\gamma(\alpha-\mathrm{err}_t),\quad
\mathrm{score}_t = \mathrm{pos}_t\cdot\frac{|\mathrm{point}_t|}{hi_t-lo_t}\cdot a_t
```
Intuition: six market-state blocks feed a quantile model, and the index trades only when the whole interval clears the cost.

What the source says (Table 1 p. 2, eq. 2 p. 3, eqs. 4 to 8 pp. 5 to 6):
1. **Volatility:** 21-day change of the VIX level. Expanding z, at least 60 observations, CDF map. Lag 0. Sign minus.
2. **Momentum:** 4-month exponentially decaying mean of monthly HY excess returns over 4-month realised vol. No z-score. Rescaled to standard deviation 10/3. Lag 5 days. Sign plus.
3. **Sentiment:** 21-day change of the geometric mean of (EM bond TR over G10 bond TR) and (G10 equity TR over G10 bond TR). The sign flips when the 6-month rolling z of the level is above +3 or below -4. Lag 0. Sign plus.
4. **Liquidity:** 0.5 z(NY Fed primary dealer net corporate positions) + 0.5 z(21-day change of CDX.IG 5y minus C0A0 OAS). Dealer data enters 9 days after its reference Wednesday. CDX lag 1 day. Before CDX exists the dealer leg runs alone. Sign minus.
5. **Structural:** equal-weight mean of the z of median issuer 3-month equity vol, median net debt over EV, and 3-month downgrades minus upgrades. Lag 1 day. Sign minus.
6. **Systematic:** PC1 of daily OAS changes of the rating buckets. Eigenvector from the trailing 250 days, sign fixed so the IG loading is positive. Factor = 21-day sum of PC1 scores. Expanding z, CDF map. Lag 0. Sign minus.
- Hygiene (pp. 2 to 3): NYSE days, forward fill at most 5 trading days, z clipped at plus or minus 8, weekly data on its publication date.
- Gate (p. 5): g = 1 when the 21-day std of daily OAS changes is above its expanding 80th percentile. beta_mom = 0.6, other betas 0, kappa = 1.
- Features (p. 4): the 6 gated signals, their lags 5 and 10, vol x liq, vol x mom. K = 20.
- Weights (p. 5): w proportional to (lambda I + (1 - lambda) Sigma)^-1 rho, Sigma Ledoit-Wolf. The columns are scaled by w.
- Model (p. 4): L1 linear quantile regression, lambda in {0, 0.01, 0.1}, or boosted trees: {100, 200} trees x lr {0.03, 0.07} x depth {2, 3}, leaves 7, min child 20, subsample 0.9, colsample 0.8. Selection by pinball loss in 3 purged chronological folds, embargo h. Tune at tau 0.5, reuse for alpha_t/2 and 1 - alpha_t/2. Repair crossing.
- Conformal (pp. 5 to 6): Q = the ceil((n+1)(1-alpha_t))/n quantile ("higher") of E_j = max(lo_j - y_j, y_j - hi_j) on the calibration block. alpha = 0.10, gamma = 0.02, alpha_t clipped to [0.001, 0.499].
- Decision (p. 6): +1 if lo > c, -1 if hi < -c, else 0. Size |point| / (hi - lo). HY cash c = 12 bp, CDX HY 4 bp, IG cash 5 bp, CDX IG 2 bp.
- Horizons (p. 3): h in {5, 21, 63}. Alignment a = 1 when all three points share a sign, 2/3 when the traded horizon agrees with one other, 0 when it disagrees with both.
- Windows (p. 3): train 250 days, calibration 120 days, refit every 21 days.
- Drawdown stop (p. 6): flatten when equity falls D* below its running peak. D* = 2 x the 95th percentile of h-day adverse moves in the training window.

## 4. Inputs
One new optional long panel `macro_series`: `series_id`, `date`, `value`, `available_at`. Without it, or without the target series, the result is empty. All are "need": none is in `docs/production_wiring.md` section 5.

| Block | `series_id` | Content and unit | `available_at` rule |
| --- | --- | --- | --- |
| target, momentum | `H0A0_XR` | ICE BofA H0A0 daily excess return over duration-matched Treasuries, decimal (ICE licence) | date + 1 day |
| gate, sys (HY) | `BAMLH0A0HYM2` | H0A0 OAS, FRED, percent | date + 1 day |
| systematic | `BAMLC0A1CAAA`, `BAMLC0A2CAA`, `BAMLC0A3CA`, `BAMLC0A4CBBB`, `BAMLH0A1HYBB`, `BAMLH0A2HYB`, `BAMLH0A3HYC` | ICE BofA rating-bucket OAS AAA to CCC and lower, FRED, percent | date + 1 day |
| volatility | `VIXCLS` | CBOE VIX close, FRED | date + 1 day |
| liquidity (a) | `NYFED_PD_CORP_NET` | NY Fed primary dealer statistics, net positions in corporate securities, USD millions, `date` = reference Wednesday | publication Thursday + 1 day. The module also enforces date + 9 days (p. 2) |
| liquidity (b) | `CDX_IG_5Y`, `BAMLC0A0CM` | CDX.IG 5y spread (Markit) and C0A0 OAS (FRED), both percent | date + 1 day |
| sentiment | `EM_BOND_TR`, `G10_BOND_TR`, `G10_EQUITY_TR` | total return index levels (vendor) | date + 1 day |
| structural | `STRUCT_EQVOL_MED`, `STRUCT_NDEV_MED`, `STRUCT_NET_DOWNGRADES_3M` | median 3-month realised equity vol of index issuers, median net debt over EV, 3-month count of downgrades minus upgrades (Moody's and S&P, announcement date) | date + 1 day |
| IG segment | `C0A0_XR` | C0A0 daily excess return, decimal | date + 1 day |

FRED now serves the ICE BofA series for the last 3 years only (`hy/sources/forecast_sources.py`). The production machine needs the ICE history. `NYFED_PD_CORP_NET`, `H0A0_XR`, the sentiment and the structural ids are our names. The production machine maps its vendor fields to them.

## 5. Build steps
1. Read `macro_series` rows with `available_at` <= decision_time(as_of). Trading calendar = the dates of `H0A0_XR` up to as_of.
2. Put each series on the calendar at its usable day max(date + publication lag, available_at - 1 day). Keep the newest reference date when a revision arrives. Forward fill at most 5 rows.
3. Build the six raw factors, shift each by its lag in rows, z-score (expanding, 60 observations, ddof 0), clip, CDF map, apply the sign. Momentum takes the 10/3 rescale instead.
4. Gate with the HY OAS regime flag. Build the 20 features. A missing signal enters as 0, the CDF midpoint.
5. For each h, run the walk-forward of `walk_forward` over the whole history to as_of. Only targets that matured by day t enter day t.
6. At as_of: score = pos x size x alignment for the traded horizon (21). Flat gives 0. Too little history gives NaN.

## 6. Code placement
`hy/factors/f25_credit_bmi.py`, `compute(panels, as_of, horizons=(5, 21, 63), traded=21, segment="HY", ...)`. Methodology Section 8 (S7 replacement) and Section 3.6 (macro inputs). Output: `date`, `index`, `score`, `available_at`, `point`, `lo`, `hi`, `pos`, `size`, `align`, `alpha_t`, `model_kind`, `d_star`, `stopped`, `coverage`, `point_h<h>` per horizon, `gate`, `n_blocks`, `s_vol` to `s_sys`. `walk_forward` returns the daily path, so the production machine runs it once and samples month ends. Reuses `hy.backtest.decision_time`. Boosted trees use scikit-learn `GradientBoostingRegressor(loss="quantile")`, because LightGBM is outside the allowed libraries.

## 7. Tests
Unit (`tests/test_factor_f25.py`): contract, no look-ahead (future rows and late `available_at`), 9-day dealer lag, sign (a VIX fall gives a positive vol block, and a known-answer walk-forward gives long and short calls), empty frame without the panel, missing optional blocks, hand checks of the CDF map, gate, PC1 sign, purged splits, Q, ACI step, decision, alignment and D*.
Evaluation (production machine): walk-forward from 2004, h = 21, HY cost 12 bp. Pass, all three: (a) empirical coverage of the 90% interval in [0.88, 0.92]; (b) hit rate on traded days above 55%; (c) net Sharpe, block bootstrap with block 2h = 42 days (p. 7), positive in at least three of 2008, 2015, 2020, 2022. Report the p. 7 metrics: coverage, mean and p90 width, days traded, hit rate, net Sharpe, max drawdown, turnover.

## 8. Risks
- One time series. About 12 independent monthly targets per 250-day window (p. 3). Overfit risk is high. The purged CV is the only guard.
- Data: H0A0 excess return, CDX and the structural legs are vendor data. FRED history of ICE series is short. Ratings after Feb 2017 are missing (H-F13), so the downgrade leg fails after 2017.
- Overlap: the momentum block overlaps F04 bond momentum at index level. The systematic block is the Collin-Dufresne common factor. No correlation is given in the source.
- Turnover: daily decisions with a 12 bp cost each change. The dead zone and the stop limit it.
- Unit-test observation (synthetic data, not a result): with 120 to 250 training rows, an extreme vol x mom interaction flipped the point sign against the vol block. The 20 columns can extrapolate badly at extremes.

## 9. Open questions and differences from the user's code
1. **Look-ahead in the code.** `credit_bmi_v2.py` calibrates on targets up to t - 1 and updates ACI with y_t, which mature only at t + h. We use only targets matured by t: calibration ends at t - h, ACI updates with the interval issued at t - h.
2. **P&L in the code** is pos x y^(h), an overlapping forward sum. We use the daily excess return on the unit position pos, as the code does (size does not enter the P&L). After a stop the code stays flat for ever, because a flat book cannot regain the peak. Our choice: flat for h days, then the peak resets.
3. **Features.** The code driver feeds only the 6 signals. We follow the spec: 20 columns.
4. **Weights.** lambda has no value in the source. Our choice: 0.5 on the correlation scale (columns standardised before Ledoit-Wolf). The code uses lambda = 0. The spec says lambda -> 1 gives equal weights. It gives w proportional to rho. We use equal weights 1/K only when fewer than 60 training rows are finite. The code recomputes w daily on a model fitted with old w. We fix w at each refit.
5. **Buckets.** The spec says 8 buckets. FRED has 7 (AAA to CCC and lower). We use the 7 ids. The IG loading is the sum over the four IG buckets.
6. **Windows the source leaves open (our choices):** 4 months = 84 rows, EWMA span 84, monthly vol = 84-day daily std x sqrt(21), 6-month z = 126 rows, gate percentile from 60 rows (as the code), PC1 needs 60 complete rows, D* uses |y^(h)|. Sentiment uses the log composite.
7. **L1 grid scale.** The penalties {0, 0.01, 0.1} act on targets in decimals (about 0.01). So 0.01 and 0.1 may shrink most coefficients to 0. We keep the grid as written. The production machine records the picks.
8. **No CV fold survives** at small windows: the code then has no model. Our choice: linear, L1 penalty 0.01 (the code's default).
9. The PDF says "published Thu for prior Wed" and "9d". Wednesday to Thursday of the next week is 8 days. We keep 9 days as written.
