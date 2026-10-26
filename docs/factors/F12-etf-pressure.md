# F12. HY ETF pressure and contraflow

## 1. Header
- Rank 12. Tier 2 (tested outside credit, needs data we lack). Status: NEW. It extends S6 (forced flows, `docs/methodology.md` Section 8).
- Sources: (1) Shim (2020), "Arbitrage Comovement", `/home/ak/Documents/Quant Credit/ssrn-3287912.pdf`, PDF pp. 1–3, 12–14, 21, 35, 38–42. The file `arb_comovement` (no extension) is the same PDF: same MD5 hash, 67 pages. (2) Chao, Shah, Martin, Wei, Zhang (2019), "Why Do ETF Flows Move Prices?", Deutsche Bank, `/home/ak/Documents/Quant Credit/Why Do ETF Flows Move Prices.pdf`, PDF pp. 1–3, 7. (3) RFQ alpha spec, `/home/ak/Documents/Quant Credit/anonymous_rfq_alpha_prediction_only_spec.md` §24. (4) AK design notes, `Research Platform/contraflowsimple.pdf` pp. 1–3.
- Reader blocks: B-F9, B-F10, A2-F12, A2-F13, E-F4.

## 2. Claim
A US high yield bond that HY ETFs (HYG, JNK and others) bought through creations over the last 6 months, relative to its par outstanding, earns a lower excess return over the next month than a bond that the ETFs sold. The sign is pressure then reversal. All evidence is from equities. The test fails if the monthly rank IC of `score` after cost is not positive in at least 3 of the 4 cycles.

## 3. Definition
What the sources say.
- DB contraflow (equities). ETF flow is the change in the total dollar amount that ETFs hold, scaled by market cap (p. 1). The window is 6 months (p. 2). Each month, sort Russell 3000 stocks into deciles within sector. Long the bottom decile (largest outflow), short the top decile (p. 2). Jan 2006 to Dec 2018: decile 1 earns 11.9% a year, decile 10 earns 3.7%, the long-short Sharpe ratio is 1.29 (Figure 1, p. 2). Index reconstitution alone gives Sharpe 0.82, weight reconstitution 0.51, allocation 0.30 (p. 7). Allocation, index and weight reconstitution drive 29%, 45% and 25% of flow variance (p. 3).
- Shim arbitrage sensitivity (equities). Arbitrageurs trade each constituent by its ETF weight, not by its exposure (p. 1). `Λ_{i,e} = λ_i(w_i) / Σ_j w_j λ_j(w_j)`, `λ_i(w) = c_i w^γ` (eq. 5, PDF p. 12). The weighted mean of Λ is 1 (p. 13). `w` is the mean weight over at least one year, γ = 0.5 (eq. 10, p. 21). `c` comes from `r = c sign(V)|V|^γ` on 5-minute signed volume (eq. 11, p. 21). After ETF return days beyond the 95th percentile (2010–2017, p. 35), the slope of the relative return on Λ (eq. 18) is 0.689 at day 0 and 0.087 (t 0.29) at day 63 (Table 5, p. 40). So high-Λ stocks over-react and then revert. Monthly deciles on the prior-year Λ, 2008–2017: high minus low alpha −0.649% a month (t −2.66) for high-volume ETFs, −0.619% (t −2.35) for large-cap ETFs. The control period gives −0.150% (t −0.54) (Table 6, PDF p. 42). Mid-cap and small-cap alphas are not significant (Table 7, p. 43).
- RFQ §24 maps ETF return times volume z-score to bonds by a beta. It gives no sign and no evidence.

Our choice. Use holdings, not betas. Use par, not dollars, so the bond's own price change does not enter the flow (contraflowsimple Eq. 1 uses `P_t Q_t - P_{t-6} Q_{t-6}`, which does).

```latex
f_{e,d}=\frac{S_{e,d}-S_{e,d^-}}{S_{e,d^-}}\qquad
A_{i,t}=\sum_e\sum_{d\in W_t} f_{e,d}\,Q_{i,e,s(d)}\qquad
T_{i,t}=\sum_e\big(Q_{i,e,s(t)}-Q_{i,e,s(t-6)}\big)\qquad R_{i,t}=T_{i,t}-A_{i,t}
```
```latex
\mathrm{Press}_{i,t}=\frac{A_{i,t}}{\Pi_{i,t-6}}\ \text{(par)}\quad\text{or}\quad\frac{A_{i,t}}{\sum_{m\in W_t}V_{i,m}}\ \text{(volume)},\qquad \mathrm{score}_{i,t}=-\mathrm{Press}_{i,t}
```
Intuition: a creation of 1% of ETF shares buys 1% of every holding, so the bond takes that share of the ETF's par. That is the ETF's net flow times the bond's weight.

```latex
\Lambda_{i,e,t}=\frac{c_{i,t}\,\bar w_{i,e,t}^{\gamma}}{\sum_{j\in e}\bar w_{j,e,t}\,c_{j,t}\,\bar w_{j,e,t}^{\gamma}}\qquad
\mathrm{Arb}_{i,t}=-\sum_e \sigma_{i,e,t}\,(\Lambda_{i,e,t}-1)\,r_{e,t}
```
Intuition: after an ETF move, bonds that are illiquid for their weight moved too far with the ETF and revert.

- `S`: ETF shares outstanding. `d^-` is the prior row. With a dollar `flow` column and no shares, `f = flow / aum` of the prior row. Our choice.
- `Q_{i,e,s}`: par held in the latest holdings snapshot dated before day d (or on or before t for `T`). A bond absent from a snapshot of an ETF holds 0.
- `W_t`: the 6 months that end at t (DB p. 2). `Π`: `bond_panel.amt_out` at the window start, else at t. `V`: `bond_panel.par_volume`.
- Default basis "alloc": `score = -A / scale`, the flow times weight that the task defines. Basis "total" uses `T`. `R` is the reconstitution part (DB p. 3, contraflowsimple Eq. 4).
- `c_i`: the median over the last 12 months of `|P_m/P_{m-1} - 1| / sqrt(V_m)` from `bond_panel`, with 6 months at least. This is a monthly proxy for eq. 11, because TRACE has no 5-minute signed volume in the panels. Our choice.
- `w̄`: mean weight over the snapshots of the last 12 months (eq. 10, at least one year). Weight is `market_value` share where it exists, else par share. Weights renormalise over the bonds with a `c`, so the weighted mean Λ stays 1. Our choice.
- `σ_{i,e}`: the share of bond i's ETF par that ETF e holds at t. `r_e`: ETF return over the last month from `ret` (compounded) where it exists, else from `nav`. Our choice: the month return in place of the 95th-percentile event days.
- Horizon 1 month (DB sorts monthly, p. 2). Shim's reversal ends near 63 days (p. 40).

## 4. Inputs
| Field | Table and column | `as_of` | `available_at` lag rule | Status |
| --- | --- | --- | --- | --- |
| ETF shares and NAV | new `etf_flows`: `etf`, `date`, `shares_out` (or `flow` with `aum`), `nav`, optional `ret`, `available_at` | trade day | trade day + 1 day (issuer files post after the close). Our choice | need |
| ETF holdings | new `etf_holdings`: `etf`, `date`, `cusip`, `par_held`, optional `market_value`, `available_at` | holdings date | holdings date + 1 day. Live: the download time | need. iShares and SPDR publish the current file only. History is a gap |
| Par outstanding | `bond_panel.amt_out` (optional, as in F03) | month end | month end + 1 day | need (optional) |
| Par volume, price | `bond_panel.par_volume`, `price` (wiring 5) | month end | month end + 1 day | have |
| Eligibility | `bond_panel` (`backtest.eligible`) | month end | month end + 1 day | have |

Without `etf_flows`, `etf_holdings` or `bond_panel`, the result is empty.

## 5. Build steps
1. Load `etf_flows` and `etf_holdings`. Drop rows with `available_at` after `decision_time(as_of)` or `date` after as_of.
2. Per ETF, compute `f_{e,d}` from consecutive rows. Map each flow day to the latest holdings snapshot before it.
3. Per bond, sum `f × Q` over ETFs and days of `W_t` to get `A`. Take `T` from the snapshots at t and t-6. Set `R = T - A`.
4. Keep eligible bonds of `bond_panel` at as_of. A bond that no ETF held in a snapshot of `W_t` gets NaN (`n_etfs` = 0).
5. Scale by `Π` (basis "par") or by window par volume (basis "volume"). "auto" picks "par" where `amt_out` exists at as_of.
6. Compute `c`, `w̄`, Λ per ETF, `σ` and `r_e`. Set `Arb`.
7. Write one row per bond with the outputs of section 6.

## 6. Code placement
- `hy/factors/f12_etf_pressure.py`: `compute(panels, as_of, window=6, basis="alloc", scale="auto", gamma=0.5, lam_months=12, min_c_months=6)`.
- Helpers: `share_flow`, `snapshot_for`, `allocation_par`, `holdings_change`, `price_impact`, `mean_weights`, `arb_sensitivity`, `etf_month_return`.
- Methodology Section 8, S6. Reuses `hy.backtest.decision_time`, `eligible`.
- Outputs: `date`, `cusip`, `score`, `available_at`, `pressure_alloc`, `pressure_total`, `pressure_recon`, `scale_basis`, `n_etfs`, `arb_sensitivity`, `etf_return`, `arb_score`.

## 7. Tests
Unit tests: contract, no look-ahead (late flow and holdings rows change nothing), sign (a bond in a creating ETF scores below a bond in a redeeming ETF), Λ weighted mean equals 1, Λ hand check, missing panel gives an empty frame, bond not held gives NaN, volume scale when `amt_out` is missing.

Evaluation test (production): monthly rank IC of `score` against 1-month excess return beyond `g_spread`, after cost, positive in at least 3 of 2008, 2015, 2020, 2022. HYG holdings history before 2012 may be thin, so 2008 can fail for lack of data. Second test: `arb_score` IC, with the same pass rule.

## 8. Risks
- Equity evidence only. No source tests bonds. HY ETFs create and redeem with sample baskets and cash, so the pro-rata map `f × Q` overstates the bond-level flow (A2-F12).
- Overlap with F05. F05 sees the same sales in TRACE. No source states the correlation.
- Λ and DTS beta. Λ predicts the ETF beta (Shim p. 13). Neutralise on DTS before use.
- Cost. Contraflow in HY trades the least liquid bonds of the index. Turnover is monthly.

## 9. Open questions
1. Basis. Default "alloc", the task's definition. DB finds reconstitution carries most of the effect (p. 7). Test "total" first on production data.
2. Window. Default 6 months (DB p. 2). The earlier DB paper used 12 months (p. 2).
3. `c` proxy. Default monthly Amihud with γ = 0.5. A daily TRACE estimate of eq. 11 from F05's `trace_daily_flow` may be closer to the source.
4. Event gate. Default none. Shim uses days beyond the 95th percentile. Test that gate on daily `etf_flows`.
