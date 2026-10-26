# F05. Flow-induced selling pressure, same-issuer reversal

## 1. Header
- Rank 5. Tier 1 (tested in credit, buildable now). Status: NEW. It extends S6 (forced flows) and uses the S4 within-issuer frame (`docs/methodology.md` Section 8).
- Sources: (1) Dannhauser and Hoseinzade (2021), RFS, `/home/ak/Documents/Quant Credit/Research Platform/hhab031.pdf`, PDF pp. 4–5, 8, 11–12, 25–31. (2) RFQ alpha spec, `/home/ak/Documents/Quant Credit/anonymous_rfq_alpha_prediction_only_spec.md` §3, §5, §7, §8, §11, §14–§20. (3) TRACE rules: `research/cards/forecast-trace-hy-benchmark.md` (FINRA page cited there), docstrings of `hy/sources/trace_bonds.py` and `hy/sources/trace_panel.py`.
- Reader blocks: E-F3, B-F1, B-F2, B-F3, B-F5, A2-F15.

## 2. Claim
In US high yield, a bond that took more net customer sales than the other bonds of its issuer over 3 months, and whose excess sales then stop, earns a positive excess return against those sibling bonds over the next 6 months. The test fails if the pair return net of cost is zero or negative.

## 3. Definition
What the source says. ETF outflows during the Taper Tantrum (May 22 to August 31, 2013) widen the exposed bond against a bond of the same issuer. The LQD-eligible bond widens 11.3 bp more in August and 8.5 bp more in September (p. 26). The gap stays significant for 4 months (Aug–Nov) and is insignificant after November (Table 8, p. 27). The trade-based proxy stays significant for 5 months, Sep–Jan (Table 9, p. 29). A 1% rise in trade-based pressure adds 4.0 bp, and a 1% rise in hypothetical pressure adds 14.8 bp (p. 5). The peak price impact is up to 20.35 bp after duration (p. 28). The gap closes by slow reversion of the exposed bond, not by catch-up of the control bond (p. 31). The issuer fixed effect removes the issuer's credit news (pp. 4, 23).

Our choice. Replace fund holdings with TRACE customer flow. Remove the issuer's own flow by a same-issuer comparison.

```latex
NS_{i,d}=\sum_{u\in(i,d)}\mathbf 1\{cpt_u=C\}\big(\mathbf 1\{side_u=B\}-\mathbf 1\{side_u=S\}\big)\,Q_u
\qquad P_{i,t}=\frac{\sum_{d\in W_t}NS_{i,d}}{|W_t|\,\bar V_{i,t}}
\qquad RP_{i,t}=P_{i,t}-\frac{\sum_{j\in a(i),\,j\neq i}\mathrm{DTS}_j\,P_{j,t}}{\sum_{j\in a(i),\,j\neq i}\mathrm{DTS}_j}
```
```latex
\mathrm{Trig}_{i,t}=\mathbf 1\{RP_{i,t}\ge c_t\}\,\mathbf 1\{P_{i,t}>0\}\,\mathbf 1\{M_{i,t}\ge 2\},\quad
\mathrm{Exh}_{i,t}=\mathbf 1\{RP^{(10)}_{i,t}\le 0\},\quad
F05_{i,t}=\mathrm{Trig}_{i,t}\,\mathrm{Exh}_{i,t}\,RP_{i,t}
```
Intuition: the issuer's other bonds carry the same credit news, so sales in excess of theirs are a liquidity shock that should revert.

- Sign. TRACE `side` is the reporting dealer's side. `side = 'B'` with `contra_party_type = 'C'` is a customer sale to a dealer (the `px_dealer_buy` rule in `trace_panel.month_sql`). Interdealer trades (`cpt = 'D'`) drop out. Positive `NS` means net customer sales. This is the RFQ spec convention, `side = +1` for a customer sale (§3).
- `Q_u`: par in USD from `ascii_rptd_vol_tx`. A cap reads as its floor (`trace_bonds.parse_volume`). Keep trades of at least 100,000 par, as the source does (p. 8). Our choice.
- `W_t`: 63 trading days that end at month end t. Source flow window: May to August, about 3 months (p. 11). Our choice.
- `V̄_{i,t}`: mean daily customer par volume (sales plus purchases) over the 252 trading days before `W_t` starts. So `P` is the share of normal volume that went one way. A lagged scale avoids the mechanical link of a same-window volume scale (p. 12). Our choice.
- Paper scale, when amount outstanding exists: `P^{AO} = Σ NS / AmtOut` at the window start (Eq. 5, p. 11).
- `DTS_j = D_j s_j`: modified duration times G-spread at the prior month end. It weights the issuer pool so a long bond counts more. Count-based twin: replace `Q_u` by 1 (RFQ §7). Our choice.
- `c_t`: 90th percentile of `RP` over all bond-months in the 36 months before t. The RFQ spec allows the 80th or the 90th percentile (§20.2). Our choice: 90th.
- `M_{i,t}`: the number of the 3 calendar months in `W_t` with net customer sales in bond i. Persistence needs 2 of 3. Our choice.
- `RP^{(10)}`: `RP` over the last 10 trading days. Exhaustion means that the bond no longer takes more net sales than its siblings. This is RFQ §20 with a sign rule in place of the acceleration term. Our choice.
- Entry: decision time t + 1 day (`backtest.decision_time`). Hold 6 months in overlapped monthly cohorts, one sixth of the book each month. Source basis: the gap is still open at month 4 and closes in months 4 to 6 after August 31 (Tables 8–9). Our choice.
- Winsorise `RP` at the 1st and 99th percentiles per date. The source winsorises spreads at 1% and 99% (p. 10).

## 4. Inputs
| Field | Table and column | `as_of` | `available_at` lag rule | Status |
| --- | --- | --- | --- | --- |
| Customer sale par and count per bond-day | new `bond_flow.cust_sell_par`, `cust_sell_n` (WRDS `trace.trace`, `trace.trace_btds144a`: `side = 'B'`, `contra_party_type = 'C'`) | trade day | trade day + 1 day (`trace_bonds.DISSEMINATION_LAG`). Live: add the WRDS load lag | need (production). Raw fields: have on WRDS |
| Customer purchase par and count per bond-day | new `bond_flow.cust_buy_par`, `cust_buy_n` (`side = 'S'`, `cpt = 'C'`) | trade day | as above | need (production) |
| Bond to issuer map | `bonds.bond_id`, `bonds.ticker` to `issuers.issuer_id` (wiring 4.1, 4.3, contract 3.1, 3.9) | static | none | have |
| Duration, G-spread, price, years | `trace_panel` monthly panel from `bond_obs` and `treasury_curve` (wiring 4.4, 4.7, contract 3.10) | month end | last trade + 1 day | have |
| Bid-ask cost | `bond_obs.bid_ask_pts` (wiring 4.4) | trade day | trade day + 1 day | have (optional) |
| Amount outstanding | not in `bonds` (wiring 4.3). Methodology 3.1 lists `amount_outstanding` | issue date and each change | change date + 1 day | need (optional, for `P^{AO}`) |
| HY benchmark spread | `backtest.benchmark_spread` | month end | month end + 1 day | have |

TRACE rules and their effect:
1. Reporting lag. FINRA requires a report within 15 minutes (card `forecast-trace-hy-benchmark`). The repo sets `available_at` = trade day + 1 day. On 2026-10-22 the last WRDS trade date was 2026-09-17 (same card). A live run therefore sees exhaustion about 5 weeks late. A backtest must add the WRDS lag or it overstates the early part of the reversal.
2. Size caps. Dissemination shows a high yield trade above $1 million as "1MM+" and an investment grade trade above $5 million as "5MM+" (same card). The repo reads the cap as its floor. A large sale of a high yield bond therefore counts as $1 million, so par flow understates block sales and pulls `NS` toward zero. The count twin does not depend on the cap. Report both.
3. Side history. The `trace_panel` docstring says that `side` is populated from about 2012. Before that date the factor has no input.

## 5. Build steps
1. Pull customer trades per month with the `trace_panel.month_sql` clean rules (live status, no cancels, no reversals, par ≥ 100,000). Aggregate to one row per bond and trade day: sale and purchase par and counts.
2. Attach `available_at` = trade day + 1 day. Drop rows public after the decision time.
3. Per bond and month end t: compute `NS` sums over `W_t` and over the last 10 trading days, `V̄`, `P`, `M`. Require at least 5 customer trades in `W_t`.
4. Keep eligible bonds (`backtest.eligible`). Drop bonds with price below 50 (flat, `FLAT_PRICE`) and bonds with fewer than 1 year to maturity. The source drops defaulted bonds and bonds under 1 year 4 months (p. 11).
5. Map bonds to issuers. Keep issuers with at least 2 bonds that pass step 3. Compute `RP` and `RP^{(10)}` with prior-month DTS weights.
6. Compute `c_t` from the trailing 36 months of `RP`. Set `Trig`, `Exh` and `F05`.
7. Per triggered issuer, form the pair: long the triggered bond, short its sibling bond with the lowest `RP`, sized DTS-neutral.
8. Write one row per bond and month end with the outputs of section 6.

## 6. Code placement
- `hy/sources/trace_panel.py`: `flow_sql(start: str, end: str, min_par: float = MIN_PAR) -> str` and its Python twin `aggregate_flow(trades: pd.DataFrame, min_par: float = MIN_PAR) -> pd.DataFrame`. Reuse `clean_trades`, `trace_bonds.VOLUME_SQL`, `trace_bonds.parse_volume`, `trace_bonds.DISSEMINATION_LAG`.
- `hy/signals.py`: `f05_flow_reversal(flow: pd.DataFrame, panel: pd.DataFrame, bonds: pd.DataFrame, as_of: pd.Timestamp, window: int = 63, short: int = 10, vol_window: int = 252, q_trigger: float = 0.90, min_trades: int = 5) -> pd.DataFrame`.
- Docstring: cite methodology Section 8 S6 (forced flows) and S4 (within-issuer frame), and the formulas of section 3. The decision page adds a flow paragraph to S6 without a renumber.
- Outputs: `cusip`, `date`, `f05_pressure`, `f05_rel_pressure`, `f05_months_sold`, `f05_trigger`, `f05_exhausted`, `f05_score`, `available_at`.
- Reuse in evaluation: `backtest.assert_no_lookahead`, `realised_excess_return`, `round_trip_cost`, `ic_beyond`, `cycle_test`, `long_short`, `newey_west_se`, `signals.rank_ic`.
- Data contract: add a `bond_flow` kind next to 3.10 and a table next to wiring 4.4.

## 7. Tests
Unit tests:
1. No look-ahead. A flow row with `available_at` after the decision time raises `LookAheadError`. A late trade changes no score at earlier dates.
2. Side map. `side = 'B'`, `cpt = 'C'` adds to sales. `side = 'S'`, `cpt = 'C'` adds to purchases. `cpt = 'D'` adds to neither.
3. Sign on a synthetic issuer with two bonds. Bond A takes net sales for 63 days, then 10 flat days. Bond B is flat. Then `F05_A > 0` and `F05_B = 0`. Flip all sides: no trigger. Remove the 10 flat days: `Exh_A = 0`, so `F05_A = 0`.
4. Cap. A "1MM+" sale adds 1,000,000 to `cust_sell_par` and 1 to `cust_sell_n`.
5. Edge cases. A single-bond issuer gives NaN. Fewer than 5 customer trades gives NaN. A bond below price 50 gives NaN. The factor reads no equity data, so absent equity changes nothing.

Evaluation test, formation months 2012 to the panel end:
1. Horizon 6 months. Report h = 1, 2, 3, 4, 6 to show the shape. The source pattern puts most of the gain in months 4 to 6.
2. Rank IC beyond spread: `ic_beyond(pred = f05_rel_pressure, real = realised_net, control = g_spread)` on bonds of triggered issuers. The return is the bond's realised excess return net of cost minus its issuer mean.
3. Pass: mean IC after costs > 0 in at least 3 of the 4 cycles (`cycle_test`). The 2008 window has no side data, so it counts as a fail. F05 must pass 2015, 2020 and 2022.
4. Pair test: mean 6-month pair return net of cost > 0, with t > 2 from issuer-clustered errors. The source clusters by issuer (Table 8 note, p. 27).

## 8. Risks
- Proxy gap. TRACE does not name the seller. APs are often dealers (p. 3, note 7). An AP that sells redeemed bonds shows as a dealer sale or an interdealer trade, not as a customer sale. Mutual fund pressure is insignificant in the LQD design (p. 26). The proxy mixes in that flow.
- Thin evidence. One episode (2013), and the main LQD design is investment grade. The HY effect is our inference.
- Bond news. The issuer comparison removes issuer news, not bond news. Calls, tenders and exchanges move one bond only. The source drops bonds with amount outstanding changes (p. 11). We need that field to do the same.
- Cost. The source peak is 20.35 bp of price (p. 28). The mean imputed round-trip cost of ETF-held bonds is 0.21 (Table 1, p. 9, units as printed). A pair pays two legs in and two out. The HY effect must be several times the IG effect to survive cost.
- Overlap. Fallen angels: a "3-Month Reversal" portfolio beats its peers by 0.78% a month, IR 1.03 (book ch. 2, Table 2.10, PDF p. 148, per `research/cards/dynkin-et-al-2021-chapter-implementations.md`). Same mechanism. The source drops bonds that cross the IG line (p. 11). Do the same when ratings exist. Amihud illiquidity (rank 13) may load on the same bonds, so control for it. RFQ flow continuation (B-F1) has the opposite sign at short horizons. No source states a correlation.
- Coverage and turnover. Many HY issuers have one traded bond. The 20-bond floor (`MIN_BONDS`) may leave months with NaN IC. One sixth of the book turns each month, but every entry is a 2-bond pair.

## 9. Open questions
1. Window. Default 63 trading days. Test 84 (the source's 4 flow months, p. 11).
2. Scale. Default lagged volume. Use `P^{AO}` when amount outstanding arrives, because the source uses it (p. 12).
3. Stress gate. The source studies one stress episode. Default: no gate. Report the subset where the HY benchmark spread widened over `W_t`. Gate only if that subset alone passes.
4. Units. Default par, with DTS weights for the issuer pool and the count twin as the cap check (B-F2 notes the cap).
5. Exhaustion window. Default 10 days. Test 21 days. Dealer inventory half-life is 4 to 6 weeks (p. 3, note 7), so sales can continue after fund flows stop.
6. Hold. Default 6 months. Test 4 months, the significance span in Table 8.
