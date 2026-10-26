# F17. Bond return skewness

- **Rank:** 17. **Tier:** 3. **Status:** NEW. A control, not a standalone signal. Candidate control for the S1 residual and for the S8 IPCA forecast (methodology Section 8).
- **Source:** Kelly, Palhares, Pruitt (2021), "Modeling Corporate Bond Returns" (KPP), SSRN 3720789. File `/home/ak/Documents/Quant Credit/ssrn-3720789.pdf`. PDF page = printed page. Definition: Table A.I (p. 55). Result: Table I (p. 16), text p. 17. IPCA impact: Table IX (p. 31). Returns: p. 14. Sample and ranking: p. 15.
- **Cited origin:** KPP credit the characteristic to Bai, Bali, Wen (2019) (p. 55, item 24). That paper is not in the folder. We did not open it.
- **Reader block:** A2-F6 (`research/notes/quant-credit-review/out_A2.md`). Every number below was checked on the source page.

## Claim
In US high yield, bonds with a lower skewness of their own monthly credit excess returns over the last 60 months earn a higher credit excess return over the Treasury hedge in the next month. The effect is not expected to survive a control for bond volatility, spread and duration.

## Definition
```latex
\mathrm{Skew}_{i,t} = \frac{\sqrt{n(n-1)}}{n-2}\cdot
\frac{\frac{1}{n}\sum_{k=0}^{n-1}(\tilde r_{i,t-k}-\bar r_i)^3}{\big(\frac{1}{n}\sum_{k=0}^{n-1}(\tilde r_{i,t-k}-\bar r_i)^2\big)^{3/2}},
\qquad n \le 60,\ n \ge 24,
\qquad \mathrm{score}_{i,t} = -\,\mathrm{Skew}_{i,t}
```
Here r~ is the one-month credit excess return that ends at month end t − k. Intuition: a bond with a left-skewed history carries crash risk and pays for it. A bond with a right-skewed history is a lottery and pays less.

What the source says:
- "Bond skewness is bond return skewness over the past 60 months" (Table A.I, p. 55). The text gives no return type, no minimum count and no estimator.
- Returns in the paper are monthly. The credit excess return is "the total return minus a hedging portfolio of treasuries" (p. 14). The model divides it by max(DtS, 0.25) (eq. 10, p. 14).
- Table I: Bond skewness managed portfolio Sharpe −0.67, significant at 1% (p. 16). "The sign of reported average returns indicate the direction of the strategy" (p. 16). So buy low skew, sell high skew.
- The sign is the same with unscaled returns (text p. 17, Table IA.II).
- Table IX: IPCA impact 0.05, not significant (p. 31). Other characteristics carry its information once they enter the model.
- Related tail measure: Value-at-risk, Sharpe 0.07, not significant (p. 16). Impact 0.06, not significant (p. 31).
- Each month the paper ranks every characteristic across bonds and maps it to [−0.5, 0.5] (p. 15).
- Sample: spreads 50 to 2000 bp, duration at least 0.25 years, ICE BofA H0A0 and C0A0, December 1999 to December 2020 (pp. 14–15).

What we decide:
- The estimator is the one F01 already uses: `f01.bond_return_features`, column `bond_skew`. It is pandas `rolling(60, min_periods=24).skew()`, the bias-adjusted sample skewness G1 above. Our choice (F01): one definition in the repo.
- Return: r~ = total − tsy_ret, one month, from `f01.bond_return_history` (`hy.backtest.realised_excess_return`). The duration-matched Treasury stands in for the KPP hedge portfolio. Not DtS-scaled: skewness is scale-free per bond, and the sign holds unscaled (p. 17).
- Window: the 60 month ends t − 59 to t, no skip month (`f01.SKEW_MONTHS`, p. 55). Minimum 24 returns (`f01.SKEW_MIN`, our choice in F01). A missing month leaves a gap. The window does not extend.
- Flat history: a bond whose window returns have sd <= 1e-12 gets NaN. Pandas returns 0 there, but the ratio is 0 / 0. Our choice.
- Universe: `f01.screen` at t (eligible, spread 50 to 2000 bp, duration >= 0.25 years, p. 15).
- score = −Skew, raw. Higher score = long. The column `rank` holds Skew ranked across the scored bonds and mapped to [−0.5, 0.5] (`f01.rank_scale`, p. 15). No winsorisation: the rank controls outliers.
- Use: a control column, not a signal. No weight in S1 or the composite until the evaluation below passes.

## Inputs
| Field | Production table and column | as_of | available_at rule | Have |
|---|---|---|---|---|
| Monthly credit excess return | `bond_panel` `price`, `coupon`, `tsy_yield`, `mod_dur`, `accrue_to`, `hedge_date`, `carried` | `date` | panel `available_at` | have |
| Universe screen | `bond_panel` `years`, `yield`, `g_spread`, `price`, `mod_dur` | `date` | panel `available_at` | have |
| Issuer key | `bond_panel.gvkey` | `date` | panel `available_at` | have |

No other panel. Without `bond_panel` the result is empty.

## Build steps
1. Keep `bond_panel` rows with `available_at` <= `decision_time(t)` and `date` <= t.
2. Build r~ per bond and start month with `f01.bond_return_history`. The start row must be `eligible`.
3. Index each return by its end month. Keep the 60 end months t − 59 to t.
4. Per bond, compute Skew with `f01.bond_return_features`. NaN below 24 returns. Count the returns in `n_ret`.
5. Universe: bonds that pass `f01.screen` at t.
6. score = −Skew. `rank` = `rank_scale` of Skew. Copy `bond_vol` from the same call as a control column.

## Code placement
- `hy/factors/f17_return_skewness.py`. `compute(panels, as_of) -> pd.DataFrame`. Window and minimum are the F01 constants, so the two modules cannot drift.
- Output columns: `date`, `cusip`, `score`, `available_at`, `gvkey`, `bond_skew`, `rank`, `n_ret`, `bond_vol`, `g_spread`, `mod_dur`.
- Helpers: `skew_history(panel, as_of, dt)`, `skew_score(skew)`.
- Reuses `f01.bond_return_history`, `f01.bond_return_features`, `f01.screen`, `f01.rank_scale`, `f01.SKEW_MONTHS`, `f01.SKEW_MIN`, `hy.backtest.decision_time`.
- Docstrings cite Section 8 and Table A.I, p. 55.

## Tests
- No look-ahead: rows dated after t and rows with `available_at` after the decision time change no score.
- Sign: a bond with one large negative month (left skew) scores above a bond with one large positive month (right skew).
- Edges: fewer than 24 returns gives NaN. A missing `bond_panel` gives an empty frame. A bond outside the screen (spread above 2000 bp) is not scored. Constant returns give NaN.
- Helpers: Skew against a hand G1 on a short series. `skew_score` flips the sign and keeps NaN.
- Evaluation (production machine): monthly rank IC of `score` beyond `g_spread` (`ic_beyond`), 1-month horizon, DTS-scaled excess return, after cost. Pass: positive in at least three of the four `CYCLE_WINDOWS`. Control test (reader A2-F6): quintile sort within rating class, low-minus-high skew with t > 2, and t > 2 on Skew in a Fama-MacBeth regression with `bond_vol`, `g_spread` and `mod_dur`. The source predicts a fail on the control test (Table IX, p. 31).

## Risks
- Not significant in the multivariate model: impact 0.05 (Table IX, p. 31). Expect the univariate edge to vanish once spread and bond volatility enter. That is why F17 is a control.
- Mixed sample. KPP pool IG and HY and report no HY-only result for this characteristic.
- Sample skewness on 24 to 60 points is noisy. One crash month dominates it. A bond that crashes and stops trading leaves the universe, so its skew never scores (survivorship).
- Stale prints. A carried row is never a start row, but a bond that trades rarely has gaps and a short n.
- Overlap with F16 (VaR) and F01 (item 24). The source gives no correlation figure. Turnover is low: one month enters the 60-month window each month.

## Open questions
- Estimator. The source does not state it. Our choice: G1 (bias-adjusted), the F01 code. The population g1 differs by sqrt(n(n−1))/(n−2), so the rank changes only where n differs across bonds. Bai, Bali, Wen (2019) may settle it.
- Return type. The source does not say total or credit excess. Our choice: credit excess, as the KPP model returns (p. 14). The sign holds both scaled and unscaled (p. 17).
- Minimum count. Our choice: 24 (F01). A run with 36 tests the sensitivity.
- Score form. Our choice: raw −Skew. The `rank` column follows the source's [−0.5, 0.5] map.
