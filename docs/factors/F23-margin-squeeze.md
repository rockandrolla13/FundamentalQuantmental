# F23. Margin squeeze: producer minus consumer prices by sector

- **Rank:** 23. **Tier:** 4 (definition with no backtest, buildable now). **Status:** NEW. A sector input with an issuer exposure. It feeds S3 (methodology Section 8, forward leverage) and the `margin` and `margin_trend` features of Section 4.1.
- **Sources:** (1) `/home/ak/Documents/Quant Credit/combined_strategies_data_requirements.csv`, row 13 "EBITDA Margin Trends by Sector". (2) Morgan Stanley European Credit Strategy, Sheets et al., "On the Margin", 18 February 2011. File `Screening Models/MS Credit Stategy Screens/MS_Screening for EBITDA margin trends by sector [addresses inflation] (Feb 2011).pdf`, 11 PDF pages. PDF page = printed page.
- **Reader block:** B-F18 (`research/notes/quant-credit-review/out_B.md`, heading F-B18). Every number below was checked on the source page. The reader formula (log changes, CPI by sector, cost share) is the reader's proposal, not the source's.
- **No backtest.** Neither source tests a signal. The note shows one chart (Exhibit 5, p. 3) and one screen (p. 7). No hit rate, IC or return appears.

## Claim
In US high yield, issuers in a sector where input prices rose faster than output prices over the last 12 months, and whose EBITDA margin is thin or falling, have lower bond excess returns over the next 3 months. The monthly rank IC of the score beyond spread is positive.

## Definition
```latex
G_{s,t} = \Big(\tfrac{PPI^{in}_{s,t}}{PPI^{in}_{s,t-12}} - 1\Big) - \Big(\tfrac{P^{out}_{s,t}}{P^{out}_{s,t-12}} - 1\Big)
\qquad
x_i = \frac{1-\tilde m_i}{\tilde m_i},\ \tilde m_i = \max(m_i, 0.02)
\qquad
I_i = -\,G_{s(i),t}\, x_i
\qquad
\mathrm{score}_i = \frac{z(I_i) + w\, z(\tau_i)}{1+w},\ w = 0.5
```
Intuition: if sales move with output prices and all non-EBITDA cost moves with input prices, then Δm ≈ −(1 − m) G. So EBITDA moves by about −G (1 − m) / m. A thin margin magnifies the same squeeze.

What the source says:
- The CSV row: "Analyzes inflation, margins, and corporate credit, focusing on the impact of rising gaps between PPI and CPI on sector and single-names margins." Frequency: monthly. No formula.
- The PPI-CPI gap acts "as a proxy for pricing power, with PPI tracking input costs and CPI more closely tracking where final goods can be sold" (p. 3). The note borrows this from a US note, "Margin Misgivings", 21 January 2011 (p. 3). That note is not in the folder.
- The gap is the difference of year-on-year % changes ("% Chg. YoY", Exhibit 4, p. 3). It is a country average of Germany, France, Spain, Sweden and the UK (p. 3). It is not by sector.
- In Europe the gap was "near a 20-year extreme" (p. 1) and "close to the widest margin in 22 years" (p. 3).
- Exhibit 5 (p. 3) sets the gap against the share of MSCI Europe that beats on earnings minus the share that beats on revenue. The note shows the chart only. It gives no correlation.
- Exposure: firms that "source globally" but "sell locally" to consumers are most exposed. Business-to-business firms share the gain. Firms with a high labour cost share may gain (p. 4).
- Dispersion: chemical EBITDA margins rose 400 bp year on year to 3Q09, utilities fell 150 bp (p. 4). The appendix screens the top and bottom 3 names per sector by LTM EBITDA margin change, with margin level, net leverage and 5Y CDS (p. 7). The page gives no unit for the change. The values (for example 1,044 for Volvo) read as bp.

What we decide:
- `G` uses simple YoY % changes over 12 months, as in Exhibit 4. Our choice: we follow the source, not the reader's log form. The two differ by less than 1 point of G below 10% inflation.
- `G` is by GICS sector (`gsector`), not by country. Our choice. The source sector story (utilities, telecom, gaming, pp. 4–6) supports a sector cut.
- `m` is the LTM EBITDA margin: sum of the last 4 `oibdpq` over the sum of the last 4 `saleq`. This matches the "LTM EBITDA margin" of p. 7.
- Margin floor 0.02. Our choice: it caps x at 49 and keeps negative-EBITDA issuers at the most exposed end.
- `τ` is `hy.state.margin_trend` over 8 quarterly margins (methodology 4.1). `margin_chg_12m` = LTM margin now minus LTM margin 4 quarters back, the "L12M change" of p. 7. It is an output column, not in the score.
- z is the cross-issuer z-score at t, clipped to ±3. w = 0.5. Our choice: the squeeze is the factor, the trend adds the issuer's own path. With no trend, score = z(I).
- Financials (GICS 40, 60) get NaN. Our choice: EBITDA margin has no meaning for them.
- Horizon 3 months. Our choice: the source gives none. The reader block tests 3 months.
- Higher score = long. More squeeze on a thin or falling margin = short.

## Inputs
| Field | Production table and column | as_of | available_at rule | Have |
|---|---|---|---|---|
| Input price index | new panel `sector_prices.ppi_input` | `date` (reference month end) | max(`available_at`, date + 31 days) | need |
| Output price index | `sector_prices.price_output` | `date` | as above | need |
| Sector key | `sector_prices.gsector` (two-digit GICS) | | | need |
| Quarterly EBITDA | `compustat_quarterly.oibdpq` (F08 panel) | `datadate` | panel `available_at` (rdq, else snapshot day) | need |
| Quarterly sales | `compustat_quarterly.saleq` (`comp.fundq.SALEQ`) | `datadate` | as above | need (new column) |
| GICS sector | `gics.gsector`, `indfrom`, `indthru` | `indfrom` | panel `available_at` | have |
| Issuer key, eligibility | `bond_panel` `gvkey`, `carried`, `years`, `yield`, `price`, `g_spread`, `mod_dur` | `date` | panel `available_at` | have |

`leverage.ltm_ebitda` cannot serve alone: the margin needs sales, and no production panel holds sales. So the margin comes from `compustat_quarterly`, the panel F08 defines, with `saleq` added.

`sector_prices` columns: `gsector`, `date`, `ppi_input`, `price_output`, `available_at`. Index levels, any base. BLS publishes PPI and CPI for month m in the middle of month m + 1 (BLS release calendar, not in the folder). The 31-day floor is our choice: a month is known at the end of the next month. Store the first-release vintage (ALFRED) where possible, because BLS revises PPI. Default map, our choice, US BLS series by title (the production machine picks the FRED IDs and stores them in the map):

| gsector | `ppi_input` | `price_output` |
|---|---|---|
| 10 Energy, 15 Materials | PPI intermediate demand, unprocessed goods | PPI final demand, goods |
| 20 Industrials, 45 IT | PPI intermediate demand, processed goods | PPI final demand, goods less foods and energy |
| 25 Cons. discretionary | PPI intermediate demand, processed goods | CPI-U commodities less food and energy |
| 30 Cons. staples | PPI intermediate demand, processed foods and feeds | CPI-U food |
| 35 Health care | PPI final demand, services | CPI-U medical care |
| 50 Communication | PPI final demand, services | CPI-U communication |
| 55 Utilities | PPI intermediate demand, unprocessed energy materials | CPI-U energy services |

## Build steps
1. Build `sector_prices` monthly from 1995 from the map. Store `available_at` per release.
2. At month end t, keep rows with max(available_at, date + 31 days) <= `decision_time(t)`. Keep the last vintage per (gsector, date).
3. Per sector, take the latest month T. Drop it if T is more than 120 days before the decision time. Compute G from T and T − 12 months. NaN if T − 12 is missing.
4. From `compustat_quarterly`, keep the latest version of each quarter public at the decision time. Per gvkey take the last 8 quarters. Drop the issuer unless all 8 exist, they are consecutive, and the latest is at most 270 days old.
5. Compute m, `margin_chg_12m`, τ, x and I = −G x per issuer, with G from the issuer's GICS sector at t.
6. z-score I and τ across issuers with an eligible bond at t, clip to ±3, combine to the score. Financials get NaN.
7. Copy the issuer score to each eligible bond of the issuer in `bond_panel` at t.

## Code placement
- `hy/factors/f23_margin_squeeze.py`. `compute(panels, as_of, trend_weight=0.5) -> pd.DataFrame`.
- Output columns: `date`, `cusip`, `score`, `available_at`, `gvkey`, `gsector`, `squeeze`, `ppi_input_yoy`, `price_output_yoy`, `price_date`, `margin`, `margin_chg_12m`, `margin_trend`, `exposure`, `impact`.
- Helpers: `yoy_change`, `sector_squeeze`, `issuer_margins`, `margin_exposure`, `squeeze_impact`, `clipped_z`.
- Docstrings cite methodology Section 4.1, Section 8 (S3) and p. 3 of the MS note.
- Reuses `hy.backtest.decision_time`, `hy.backtest.eligible`, `hy.peers.sector_at`, `hy.peers.FIN_SECTORS`, `hy.state.margin_trend`.

## Tests
- No look-ahead: a price month inside the 31-day floor, a later vintage, or a quarter with `available_at` after the decision time changes no score.
- Sign: in a sector with G > 0, a 5% margin issuer scores below a 30% margin issuer. With G < 0 the order flips. A falling margin scores below a flat one at equal G and m.
- Edges: no `sector_prices` gives an empty frame. A missing T − 12 month, a stale price month, fewer than 8 quarters, non-positive LTM sales, or a financial gives NaN.
- Helpers: G, x and I against a hand computation.
- Evaluation (production machine): monthly rank IC beyond `g_spread`, 3-month horizon, after cost from `bid_ask_pts`. Pass: positive in at least three of the four `CYCLE_WINDOWS`. First the reader test: regress the next-4-quarter change in sector median LTM margin on G. Pass if the slope is below 0 with t > 2.

## Risks
- No evidence. The sources give an idea and a European chart, no test. The gap may carry no information on US HY returns.
- Coarse map. Two-digit GICS mixes buyers and sellers of the same input (p. 4: B2B firms gain). Energy and materials sell the inputs, so their sign may flip.
- Pass-through and hedges. Regulated utilities and hedged producers do not take the squeeze (p. 5, ENEL 72–84% of EBITDA regulated or fixed).
- Overlap: `margin_trend` overlaps S2 and F09. The sector part overlaps sector value (S7 test, Section 8).
- Turnover is low: G moves monthly, margins quarterly. PPI revisions add noise if the store keeps only the latest vintage.

## Open questions
- Map granularity. Default: two-digit GICS. A GICS industry (six-digit) to NAICS map is better. The `gics` panel holds only `gsector`.
- Cost share. The reader proposes G × cost share. Our x = (1 − m) / m is the cost share over margin. A test of x against m alone settles it.
- Trend weight. Default w = 0.5, our choice. Report the IC of z(I) alone and of the combined score.
- Lag. Default 31 days. The exact BLS release day can replace it when the store keeps release dates.
