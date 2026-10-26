# F04. Volatility-adjusted and residual bond momentum

## 1. Header
- Rank 4, tier 1 (tested in credit, buildable now). Status: variant of momentum (Houweling and van Zundert 2017, Israel et al. 2018). New momentum leg in Section 8.
- Reader blocks: H-F9, H-F10, D-F5, A2-F8.
- Sources (file in `/home/ak/Documents/Quant Credit/`, page):
  - van Zundert 2017, thesis ch. 4, `Missing Papers/van-zundert-2017-volatility-momentum.pdf`: eq. 4.6 p. 104, bond data p. 111, method p. 112, results p. 113, Tables 4.6–4.7 pp. 123–124 (printed pages).
  - Jostova, Nikolova, Philipov, Stahel, FDIC WP 2010-04, `Missing Papers/jostova-2013-momentum.pdf`: pp. 12–24 (printed pages).
  - Kelly, Palhares, Pruitt, `ssrn-3720789.pdf`: pp. 13–16, 55.
  - Blitz, Huij, Martens 2011, `Factors/1-s2.0-S0927539811000041-main.pdf`: pdf pp. 1, 3–5.
  - Graef, Hoechle, Schmid 2025, `Factors/1-s2.0-S1544612325002272-main.pdf`: pdf pp. 3–4.
  - Cards: `research/cards/houweling-van-zundert-2017-factor-investing-corporate-bonds.md`, `research/cards/israel-palhares-richardson-2018-common-factors.md`.

## 2. Claim
For US HY bonds, the 6-month excess return per unit of own volatility, with the latest month skipped, predicts the next 6-month excess return beyond spread with a positive sign, in BB and B as well as CCC.

## 3. Definition
Monthly excess return of bond i in month m (end of m−1 to end of m), from `hy.backtest.realised_excess_return` rules with beta 0: r_{i,m} = total − tsy_ret. Decision at month end T.

```latex
\text{VAMOM}_{i,T}=\frac{\sum_{m=T-6}^{T-1} r_{i,m}}{\hat\sigma_{i,T}},\qquad
\hat\sigma_{i,T}=\operatorname{sd}\{r_{i,m}\}_{m=T-12}^{T-1}
```
Intuition: rank on return per unit of risk, so long-duration and CCC bonds do not fill both tails.

```latex
r_{i,m}=\lambda_{k(i),m}\,DTS_{i,m-1}+\varepsilon_{i,m},\quad \hat\lambda_{k,m}=\operatorname{median}_{j\in k}\frac{r_{j,m}}{DTS_{j,m-1}},\qquad
\text{RMOM}_{i,T}=\frac{\sum_{m=T-6}^{T-1}\hat\varepsilon_{i,m}}{\operatorname{sd}\{\hat\varepsilon_{i,m}\}_{m=T-12}^{T-1}}
```
Intuition: remove the part of the return that the market spread move explains, and keep the issuer news that diffuses slowly.

What the sources say:
- van Zundert: sort on excess return over duration-matched Treasuries over six months, the latest month skipped ("7-minus-1", p. 112). Scale each bond by 1.7% over σ̂, the monthly std of excess returns over the past 12 months, the latest month skipped. Deciles, 6-month hold, overlapping books (Table 4.6, p. 123). The source does not say if the 6-month return is a sum or a product.
- Jostova: rank on the cumulative return over t−6 to t−1, skip month t, hold t+1 to t+6, deciles, equal weight, six overlapping books (p. 12).
- Blitz: regress on three factors over t−36 to t−1, with a complete 36-month history. Sum the residuals over 12−1M. Divide by their std over the same period. Leave out alpha (pdf pp. 3–4).
- Graef: 60-month rolling betas on five factors, at least 36 returns (pdf p. 3).

Our choice:
- Return: excess over the duration-matched Treasury, not total return (van Zundert p. 112: total return mixes in Treasury momentum). Sum, not product.
- Windows: formation 6 months (T−6 to T−1), skip month T, volatility 12 months (T−12 to T−1). Hold 6 months for the main test.
- Counts: formation needs 5 of 6 months, volatility 8 of 12. Otherwise the score is NaN.
- σ̂ floor: the 10th percentile of σ̂ across the month's scored bonds. This stops a bond with stale, flat prints from a near-zero denominator.
- Residual model: a cross-sectional model per month with DTS (`mod_dur × g_spread` at m−1) as the beta (Ben Dor et al. via A2-F9). Cell k = rating class × GICS sector, fallback to rating class when a cell has fewer than `MIN_PEERS` = 5 issuers. We do not use time-series betas, because few HY bonds have 36 clean TRACE months.
- Scale: percentile rank across the month's scored HY bonds. Then `standardise_by_date`. No winsorisation is needed after the rank.
- Book weights: inverse σ̂ within each leg, each leg scaled to equal ex-ante volatility (van Zundert eq. 4.4, p. 103).

## 4. Inputs
| Field | Table and column | as_of | available_at lag rule | Status |
|---|---|---|---|---|
| Month-end price | `bond_panel.price` (from `bond_obs.price`, last 7 days) | month end | last trade in window + 1 day | have |
| Coupon, accrual end | `bond_panel.coupon`, `accrue_to` | month end | as price | have |
| Treasury yield at duration | `bond_panel.tsy_yield`, from `treasury_curve` | curve date | curve date + 1 day | have |
| Modified duration, G-spread | `bond_panel.mod_dur`, `g_spread` | month end | as price | have |
| Trade count, carried flag | `bond_panel.n_trades`, `carried` | month end | as price | have |
| Rating class | `ratings.splticrm` to Feb 2017, then implied `rclass` (`hy/peers.py`) | `datadate` | `available_at`, stale after 62 days | have |
| Sector | `gics.gsector` | `indfrom` | `available_at` | have |
| Round-trip cost | `bond_panel.bid_ask_pts` via `round_trip_cost` | month end | as price | have |
| Option-adjusted duration | none | — | — | need (optional) |

Every input of the score at T has `available_at` ≤ `decision_time(T)` = T + 1 day. Formation rows end at T−1.

## 5. Build steps
1. Load `bond_panel` with `available_at` ≤ T + 1 day. Run `assert_no_lookahead`.
2. Mark a row stale when `n_trades` ≤ 1 and the price equals the prior row's price. Treat a stale row as missing. Drop `carried` rows from formation and volatility.
3. Compute r_{i,m} for each pair of consecutive month-end rows. Gap rule: when rows exist at m−k and m (k = 2 or 3) and none between, spread the k-month return R evenly, R/k to each month, for the formation sum. Give σ̂ one observation R/√k for the gap. A gap of 4 or more months leaves those months missing.
4. Compute DTS at m−1 and the cell medians λ̂_{k,m}. Compute ε̂_{i,m}.
5. Apply the count rules and the σ̂ floor. Compute `mom_raw`, `vamom` and `rmom` at T.
6. Universe: score a bond when `eligible` is true and the rating class is BB, B or CCC. Do not score a defaulted bond: raw `splticrm` D or SD, or an empty yield (the bond trades flat). `rating_class` maps D to CCC, so read the raw symbol.
7. Rank across scored bonds, then standardise per date. Write one row per bond per month end.

Default handling in the holding period: a held bond that defaults keeps its price-based return to its last trade. The panel's carried row ends the return (`trace_panel` rule 5). Never drop it. This matches van Zundert, where a default return uses the last traded price (p. 111).

## 6. Code placement
- `hy/backtest.py`: `monthly_excess_returns(panel: pd.DataFrame, as_of: pd.Timestamp, max_gap: int = 3) -> pd.DataFrame`. Columns `cusip, date, r_ex, gap_k, stale`. It reuses the total and Treasury formulas of `realised_excess_return`, `eligible` and `FLAT_PRICE`.
- `hy/signals.py`: `dts_residuals(r_ex: pd.DataFrame, dts: pd.Series, cell: pd.Series) -> pd.Series`. And `bond_momentum(r_ex: pd.DataFrame, resid: pd.Series, month_end: pd.Timestamp, form: int = 6, skip: int = 1, vol_window: int = 12, min_form: int = 5, min_vol: int = 8) -> pd.DataFrame`.
- Docstring cite: methodology Section 8, new subsection "BM. Bond momentum", formulas BM-1 (VAMOM) and BM-2 (RMOM). The sprint adds that subsection after S7 and does not renumber.
- Output columns: `mom_raw`, `vamom`, `rmom`, `mom_sigma`, `mom_n_form`, `mom_n_vol`.
- Reuse: `assert_no_lookahead`, `round_trip_cost`, `not_distressed`, `rating_at`, `sector_at`, `peers.FALLBACK`, `standardise_by_date`, `ic_beyond`, `cycle_test`, `hac_mean`, `long_short`, `turnover_cost`.

## 7. Tests
Unit tests (`tests/test_bond_momentum.py`):
1. No look-ahead: a row with `available_at` after T + 1 day raises `LookAheadError`. A change to the month-T return, or to any later return, leaves the score unchanged.
2. Sign and volatility adjustment: with equal σ̂, the higher formation return gets the higher `vamom`. Bond A earns +6% at σ̂ 4%, bond B +3% at σ̂ 0.5%. `mom_raw` ranks A first. `vamom` ranks B first.
3. Residual: a bond whose return equals λ × DTS each month gets `rmom` near 0. Add +1% a month of own return, and `rmom` is positive.
4. Sparse trades: a 2-month gap is spread evenly. A 4-month gap leaves months missing. Four of six formation months give NaN. A carried row never enters formation.
5. Defaulted bonds: a flat bond is not scored. A held bond that defaults ends at its last price and stays in the leg.
6. Missing equity: the score builds with no `equity_monthly` panel.

Evaluation test (`scripts/f04_bond_momentum.py`, TRACE HY panel, walk-forward):
- Target: `realised_net` at h = 6 (main) and h = 1 (the Kelly horizon).
- Metric: monthly rank IC of `vamom`, `rmom` and `mom_raw` beyond spread (`ic_beyond`, control `g_spread`), after cost.
- Pass for VAMOM: mean IC beyond spread at h = 6 above 0 with HAC t ≥ 2 (`hac_mean`, 5 lags), and positive in at least 3 of the 4 cycle windows (2008, 2015, 2020, 2022). Report BB, B and CCC alone. Our choice: VAMOM must stay positive in BB alone, as in Table 4.7 (p. 124).
- The conflict test: report the IC grid {raw, VA, residual} × {h = 1, h = 6} × {all, spread < 1,000 bp, spread < 2,000 bp, ex-CCC}. This grid shows which choice moves the sign.

Decision rule (our choice):
1. VAMOM passes and RMOM does not beat it: VAMOM is the default leg.
2. RMOM beats VAMOM in mean IC and in at least 3 of 4 windows: RMOM becomes the default.
3. Both fail, and `mom_raw` at h = 1 has IC beyond spread with t ≤ −2: adopt the Kelly reading. No momentum leg. The 6-month bond return enters only as a reversal control beside EMC.
4. VAMOM passes in the full set but fails below 1,000 bp: the edge lives in distress. Route it to Section 9 and the recovery layer, not to the spread composite.

## 8. Risks
- Source conflict. Momentum exists in HY:
  - Jostova, 1991–2008: all bonds 64 bp a month (t 4.53, p. 13), NIG 190 bp (t 7.84, p. 17). The worst-rated quintile (average rating 13.61, between BB− and B+) earns 173 bp (t 7.40, p. 18).
  - van Zundert, 1994–2015: HY VA-MOM 4.02% a year (t 4.03). Quintile VA-MOM is BB 1.78% (t 2.79), B 2.71% (t 3.91), CCC–C 4.36% (t 4.98). Raw HY momentum is 2.56% (t 0.60) (Table 4.7, p. 124).
  - Kelly et al., Dec 1999–Dec 2020, IG and HY: the "Mom. 6m" managed portfolio has Sharpe −0.84, and "Mom. 6m log(Spread)" −0.80 (Table I, p. 16).
- When each source is right:
  - Rating mix: Jostova's profit falls from 63 to 28 bp (t 2.03) without D bonds (p. 20). It is insignificant without B− and worse, which are 8.27% of rated bonds (p. 21). Kelly drops spreads above 2,000 bp (p. 15) and pools IG with HY. So Kelly removes most of the region where Jostova finds the profit.
  - Return scaling: Kelly scales returns by max(DtS, 0.25) (p. 14) and ranks every bond on a [−0.5, 0.5] scale (p. 15). Jostova and van Zundert sort into extreme deciles. Raw sorts load on volatility, and van Zundert's 90/10 volatility ratio is 14.2 for bonds against 3.1 for stocks (p. 112).
  - Sample period: Jostova ends in 2008, van Zundert in 2015. Kelly adds 2016–2020. Only our test separates these explanations.
- Distress dependence: Jostova's TRACE sample, July 2002–2008, earns 114 bp (t 2.05). It loses 5% significance without CCC+ and worse, which are 4.4% of rated bonds (p. 22). VA-MOM spreads the edge into BB and B (Table 4.7), but that is untested on TRACE.
- Stale prices: TRACE gaps smooth returns and lower σ̂. That inflates `vamom` for illiquid bonds. The σ̂ floor and the stale rule cut this risk. Report IC by `n_trades` tercile.
- Crash risk: total-return equity momentum lost 8.5% a year over 2000–2009 while residual momentum earned 4.7% (Blitz, pdf p. 1). Equity residual momentum earned Sharpe 0.90 against 0.45 (1-month hold, Table 2, pdf p. 5). Graef: idiosyncratic 0.571% a month (t 3.24) against systematic 0.200% (t 1.00) (pdf p. 4). All three results are equity results.
- Overlap: Houweling and van Zundert HY value and momentum alphas correlate −36% (Table 2, PDF p. 42). Israel et al. give momentum −0.16 against value and −0.30 against carry (p. 14). Kelly's equity momentum (+1.76) has the opposite sign to bond momentum (Table I, p. 16). Measure the rank correlation with EMC, S2 and spread change. No source states it.
- Cost and turnover: HY long-only momentum turnover is 118% with a break-even cost of 1.82% (Houweling Table 3, PDF p. 43). Jostova's NIG six-month profit is 11.96%, or 6.96% after four small trades at 1.25% each (p. 24). van Zundert deducts no costs.
- Coverage: this machine's panel starts January 2008 (Houweling card). With 8 of 12 volatility months, the first score falls near October 2008. So the 2008 window is only partly covered.

## 9. Open questions
1. Formation length. Houweling HY CAPM alpha is 2.35% for 3 months and 2.15% for 6 months, and only these two are significant (Table 7, PDF p. 47). Default 6 months, to match Jostova and van Zundert. Report 3 and 12−1 as variants.
2. Skip month. Kelly's "6-2" (p. 55) and van Zundert's caption "t−6 to t−1" (p. 123) use different index styles. Default: six formation months and one skipped month, as Jostova states it in words (p. 12).
3. Rating neutrality. Rating-neutral HY momentum falls to 1.59% and loses significance (Houweling Table 8, PDF p. 48). Default: rank across all HY, because VAMOM already scales risk. Report the within-class rank too.
4. Residual factors. The bond residual model has no source. Default: DTS beta by rating × sector cell. Test a time-series beta with 24 of 36 months as a variant (D-F5 proposal).
5. Kelly's return. The source does not say if "Mom. 6m" uses total or excess return (p. 55). Default: replicate with DtS-scaled excess returns, the return of their model (p. 14).
