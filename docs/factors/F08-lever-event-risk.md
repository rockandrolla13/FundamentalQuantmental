# F08. LEVER event-risk score and the LEVER x spread corner trade

- **Rank:** 8. **Tier:** 1 (tested in credit, buildable now). **Status:** NEW. It conditions a spread sort on event risk. ESP conditions on fundamentals instead.
- **Sources:** Trinh et al. (2006), "Introducing LEVER", file `/home/ak/Documents/Quant Credit/Screening Models/Lehman LEVER/Introducing LEVER - A Framework for Scoring Leveraging Event Risk (9 January 2006).pdf`. PDF page = printed page + 1. Pages below are PDF pages. Lehman QCR Quarterly 2007-Q1, "Trading Event Risk in Credit Markets using LEVER", file `.../Trading Event Risk in Credit Markets using LEVER (2007).pdf`, pp. 31–41. PDF page = printed page.
- **Reader blocks:** H-F1, H-F2, H-F3 (`research/notes/quant-credit-review/out_H.md`). Every number below was checked on the source page.
- **Corrections to the reader blocks.** (1) The corner sort splits each LEVER *category* (bottom 20%, middle 60%, top 20%, 2007 p. 33) into OAS terciles (p. 35). H-F2 says LEVER terciles. (2) Fig. 7 (p. 37) heads its column "HL-LH". The text and the sign show it is LH−HL.

## Claim
For US HY bonds without a change-of-control put, a long low-LEVER wide-spread, short high-LEVER tight-spread book earns a positive 3-month excess return over duration-matched Treasuries. The evidence is IG only and zero cost.

## Definition
Firm LEVER-Score (2006 p. 10, 2007 p. 32). For input V of firm i, with sign α_V and peer universe U_V:
```latex
V_i^N = \alpha_V\left(\frac{V_i}{\left|\bar V^{U_V}\right|} - 1\right), \qquad
P_{i} = \frac{1}{|P|}\sum_{V\in P}\operatorname{rank}(V_i^N), \qquad
\mathrm{LEVER}_i = 10 \cdot \operatorname{U}\!\left(\tfrac13 (P^{val}_i + P^{op}_i + P^{exe}_i)\right)
```
Intuition: a firm scores high when it is cheap, cash-rich and easy to finance against its cap-weighted norm. U maps the cross-section to a uniform 0–10 scale (2006 p. 10 fn. 9).

| Part | Input V | Definition (Compustat quarterly) | α_V | U_V | Source |
|---|---|---|---|---|---|
| Valuation | Book to market | `ceqq / (prccq x cshoq)` | +1 | GICS sector | 2006 p. 9, p. 10. 2007 p. 32 fn. 7 |
| Valuation | EV / EBITDA | `(mkcap + dlcq + dlttq − cheq) / LTM oibdpq` | −1 | GICS sector | same |
| Operation | FCF yield | `LTM (oancf − capx) / mkcap` | +1 | all | 2007 p. 32 fn. 4 |
| Operation | Capex growth | `LTM capx / LTM capx one year before − 1` | −1 | all | 2007 p. 32 fn. 5, fn. 7 |
| Execution | FCF variability | `sd(last 8 quarterly FCF) / (dlcq + dlttq)` | −1 | all | 2007 p. 32 fn. 6 |
| Execution | Cash / market cap | `cheq / mkcap` | +1 | all | 2007 p. 32 Fig. 2 |
| Execution | Firm size | `mkcap = prccq x cshoq` | −1 | all | 2006 p. 6, p. 9 |

- What the source says. $\bar V^{U_V}$ is the market-value-weighted mean over U_V (2006 p. 10). Part score = mean rank of its inputs. Firm score = mean of the three parts (2007 p. 32). Above 7.5 is high risk (2007 p. 32). Exclude financials. Exclude technology before 2001 (2006 p. 9). Recompute monthly as filers report (2007 p. 34 fn. 8).
- The 2006 version has six inputs, puts capex growth in sector peers and leaves out cash / market cap (2006 p. 10). Our choice: the 2007 version, because the trade evidence uses it.
- Our choices. Divide by |mean|, so a negative peer mean does not reverse the order. A sector mean needs `MIN_SECTOR` = 5 firms, else the whole-universe mean applies. EBITDA ≤ 0, prior capex ≤ 0, debt ≤ 0 or mkcap ≤ 0 give NaN for that input. A part needs one input. The firm needs all three parts. Financials are GICS 40 and 60 (`hy.peers.FIN_SECTORS`). Technology is GICS 45. U(x) = 10 (rank − 1) / (n − 1).
- Note. On a whole-universe input the normalisation does not change the rank. It changes the rank only for the two sector inputs.

Corner trade (2007 pp. 33–39):
```latex
\text{score}_b = \mathbb 1[LH] - \mathbb 1[HL] + w_t\left(\mathbb 1[LL] - \mathbb 1[HH]\right), \qquad w_t = 0.1 \times \text{Macro LEVER-Score}_t
```
Intuition: always hold the positive-carry event trade. Add the negative-carry defensive pair as the buyout climate warms.
- Inside each rating x duration bucket: LEVER bottom 20%, middle 60%, top 20% of bonds (p. 33). Inside each LEVER category: three equal OAS groups (p. 35). L, H = low, high. First letter LEVER, second spread. Hold 3 months, rebalance monthly, three overlapping books (pp. 33–34).
- Macro LEVER-Score: a one-year-lagged regression of the count of large LBOs (deal size above $250m) on GDP growth, 10y yield change, 2s10s slope change, S&P 500 return, dividend yield, cash-flow yield, leverage, credit spread change, and private equity raised the year before (2006 pp. 6–7, p. 11). Scale 0–10. The source prints no coefficients and no scaling rule. Our choice: expanding-window OLS. Scale = 10 x the share of in-sample fitted values below the forecast.
- Our choices. Spread = `g_spread` (a caller can pass the S1 residual). Rating class from `hy.peers.rating_at`, else the leverage-implied class (`implied_class`), else "NR". Duration bucket = `hy.peers.maturity_bucket` on `years`. A bucket needs `MIN_BUCKET` = 15 bonds, so each LEVER tail holds one bond per spread tercile. When a duration bucket is smaller, the whole rating class sorts as one bucket. A class with fewer bonds gets NaN. No Macro panel: w = 0, the static trade only. A bond with a change-of-control put at 100 or more gets NaN: S5 prices that event.

## Inputs
| Field | Production table and column | as_of | available_at rule | Have |
|---|---|---|---|---|
| Book equity, price, shares | new `compustat_quarterly`: `ceqq`, `prccq`, `cshoq` (Compustat `fundq`) | `datadate` | `rdq`, else the point-in-time snapshot day | need |
| Cash flow, capex (3-month) | `compustat_quarterly`: `oancf`, `capx` (de-cumulated `oancfy`, `capxy`) | `datadate` | same | need |
| Cash, debt, EBITDA | `compustat_quarterly`: `cheq`, `dlcq`, `dlttq`, `oibdpq` | `datadate` | same | need (in `financials`, not in a panel) |
| GICS sector | `gics.gsector`, `indfrom`, `indthru` | `indfrom` | panel `available_at` | have |
| Rating class | `ratings.splticrm`; `leverage.leverage`, `ltm_ebitda` for the implied class | `datadate`, `date` | panel `available_at` | have (to Feb 2017) |
| Spread, maturity, filters | `bond_panel` `g_spread`, `years`, `price`, `yield`, `mod_dur`, `carried` | `date` | panel `available_at` | have |
| Change-of-control put | new optional `bond_terms`: `cusip`, `coc_put_price`, `available_at` | issue date | indenture filing date | need |
| Macro LEVER-Score | new optional `macro_lever`: `date`, `macro_lever` (0–10), `available_at` | `date` | build time of the fit | need |
| Macro drivers, LBO count | for `macro_lever_score`: FRED, S&P 500 aggregates, LBO count (SDC, or SC 13E-3 filings) | year | release date | need |

## Build steps
1. Export `compustat_quarterly`, one row per gvkey, `datadate` and version. Keep the latest version with `available_at` ≤ decision time.
2. Per gvkey, take the latest 8 consecutive quarters. Drop the firm when the latest quarter is older than 270 days (our choice).
3. Compute the seven inputs. Drop financials and pre-2001 technology. Normalise, rank, average, map to 0–10: `lever`.
4. Take `bond_panel` at `date` = as_of. Keep `eligible` and `not_distressed` bonds. Drop bonds with a put.
5. Assign rating x duration buckets. Sort into LEVER categories, then spread terciles. Read w from `macro_lever`. Score.

## Code placement
- `hy/factors/f08_lever_event_risk.py`: `compute(panels, as_of, spread_col="g_spread", macro_weight=0.1)`. Helpers `quarter_inputs`, `firm_inputs`, `normalise`, `uniform`, `firm_lever`, `rating_classes`, `assign_buckets`, `corner_groups`, `corner_score`, `put_bonds`, `macro_at`, `macro_lever_score`.
- Output: `date`, `cusip`, `score`, `available_at`, `gvkey`, `lever`, `lever_val`, `lever_op`, `lever_exe`, `lever_grp`, `spread_grp`, `corner`, `bucket`, `macro_lever`, `w`.
- Cites methodology Section 8 S5 (`p_LBO`) and Section 9.1 (M&A or LBO row). Reuses `hy.backtest.decision_time`, `eligible`, `not_distressed`, and `hy.peers.rating_at`, `sector_at`, `fit_cutoffs`, `implied_class`, `maturity_bucket`, `FIN_SECTORS`, `MIN_SECTOR`.

## Tests
- Unit: no look-ahead (rows after the decision time change nothing). Sign: a cheap, cash-rich small firm scores above an expensive large one. A low-LEVER wide bond scores +1. Edges: no `compustat_quarterly` gives an empty frame. A put bond gives NaN. Fewer than 8 quarters gives NaN. No macro panel gives w = 0.
- Event test (H-F1): logit of a 12-month going-private or leveraged-recap event on `lever`, US non-financial TRACE issuers 2003–2024. Pass: out-of-sample AUC ≥ 0.65 and the top quintile holds ≥ 40% of events.
- Trade test (H-F2): LH−HL 3-month excess return, net of TRACE half-spread, US HY 2003–2024. Pass: IR ≥ 0.4, and positive in at least three of the four `CYCLE_WINDOWS`.
- Macro test (H-F3): out-of-sample correlation of the score with the next-year going-private count ≥ 0.5.

## Risks
- Evidence is IG only and zero cost (2007 pp. 33–34). LH−HL: 16 bp a month, IR 1.04 (1990–2006). 15 bp, IR 0.78 (1999–2006). 10 bp, IR 1.59 (2004–2006) (p. 37).
- Combined trade 1990–2006: 14 bp a month, IR 0.90, hit ratio 59% (p. 40). Correlation −20% with the IG index and −1% with ESPRI (p. 40).
- LL−HH alone loses: −9 bp, IR −0.30 (1990–2006). It gains 9 bp, IR 0.43 in 2004–2006 (p. 37). Slope on the Macro score 12.0 (t 2.88). LH−HL slope −2.9 (t −1.33) (p. 39).
- Event power (2006, S&P 1500, 1995–2005, 32 LBOs): top 100 caught 14, bottom 100 caught 0 (p. 14). 63% of targets scored 7.5 or more, against 25% of non-targets (p. 15).
- HY sign risk. A 101 put or a portability clause can make a buyout pay the holder. We exclude put bonds but have no portability flag.
- Carry. LH−HL is a carry trade and loses in high volatility (p. 37). It overlaps the spread factor. Test it beyond spread.

## Open questions
- Capex growth peers. 2006 uses sector peers, 2007 the whole universe. Our choice: 2007.
- FCF variability with zero debt. The source divides by debt. Our choice: NaN. The firm still scores on its other two execution inputs.
- Market cap date. Our choice: the quarter-end price, as in Compustat. A monthly price would be fresher.
- Macro scaling. The source gives no rule. Our choice is above. Replace it when we fit the LBO count.
