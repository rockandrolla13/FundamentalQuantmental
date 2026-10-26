# SECTOR: sector fair-spread models, sector-relative scores, and within-sector pairs

## 1. Header
- **Rank:** none. This page is not one of the 30 ranked candidates. It serves concentrated within-sector long-short positions.
- **Name:** sector fair-spread residual (`sector_fs`), sector composite (`sector_composite`), within-sector pairs (`sector_pairs`).
- **Status:** NEW. It extends the peer fair spread of methodology 7.2 ("as built", `hy.peers` ESP) from a peer median to a fitted model per sector.
- **Tier:** implementation and unit tests only. No evaluation run exists yet.
- **Sources:**
  - Methodology 7.2 (sector-by-date effects, monotone signs), 7.3 (residual and z), 7.5 (convergence, horizon of two half-lives), 8 S1, S4 and composite.
  - Gatto (2023) p. 530, through methodology S4: "in a filing both converge to one recovery price; the long loses more than the short gains". The S4 rule is "size by jump-to-default, not by DV01".
  - Dynkin et al. (2021), card `research/cards/dynkin-et-al-2021-chapter-implementations.md`: ch. 13 peer cells (PDF pp. 444 to 445), ch. 16 sector-neutral equity momentum (Table 16.1, PDF p. 545) and the momentum definition (note 4, PDF p. 552).
  - Kricheff (2012) ch. 11, PDF pp. 58 to 61: each industry has its own operating metrics. Capex as a share of revenue and gross margin are the common ones.
  - `docs/framework.md` F2: archetypes A1 to A6 and their downside drivers.
- **Evidence gap.** No source in the repo tests a sector-specific driver list against spreads or returns. Every driver list in section 3.1 is "Our choice". The F2 frames and Kricheff ch. 11 suggest the drivers. They do not test them.

## 2. Claim
Inside one GICS sector, a bond whose spread is wide against a fit on that sector's own drivers earns a higher excess return over the next 6 months than a bond that is tight against the same fit. A DTS-matched pair of the cheapest against the richest bond in the sector earns that gap with no sector spread beta.

## 3. Definition

### 3.1 Sector fair spread (`hy.sector.fairspread`)
```latex
\log s_i = b_0 + \sum_k b_k z_k(x_{ik}) + c\, z(T_i) + \sum_r d_r 1\{class_i = r\} + e_i, \quad \operatorname{sign}(b_k) = \sigma_k, \qquad score_i = \frac{e_i}{1.4826\,\mathrm{MAD}(e)}
```
Intuition: a bond is cheap when it pays more than bonds of its own sector with the same drivers, maturity and rating.

- Fit: Huber IRLS, k = 1.345 (Our choice). A driver with a coefficient of the wrong sign leaves, and the fit reruns (methodology 7.2: the constraints keep the signs).
- z_k: winsorised at the 1st and 99th percentiles in the group, then standardised. A missing value takes the group median (Our choice).
- A driver needs values for 60% of the group's bonds (Our choice). Lease-adjusted leverage falls back to plain leverage.
- A group needs 15 issuers and 10 degrees of freedom (Our choice). Otherwise the pooled model applies: `log_lev`, `coverage`, `fcf_debt`, `ebitda_cyc` plus GICS sector effects (the η of methodology 7.2).
- Financials (GICS 40) and real estate (60) get no score. Debt over EBITDA does not measure them (`hy.peers.FIN_SECTORS`).

| Group (GICS) | Drivers, sign in spread | Frame (Our choice of list) |
|---|---|---|
| energy (10) | log_lev +, ebitda_cyc +, capex_int +, coverage − | F2 A3: stress deck, maintenance capex. Kricheff p. 61 |
| materials (15) | log_lev +, ebitda_cyc +, capex_int +, margin_trend − | F2 A3 and A4 |
| industrials (20) | log_lev +, ebitda_cyc +, margin_trend −, coverage − | F2 A4: peak-to-trough, operating leverage (Kricheff p. 60) |
| consumer_disc (25) | log_lev_lease +, margin_trend −, gross_margin −, mat_wall + | F2 A1: lease-adjusted leverage. Kricheff p. 59 gross margin |
| consumer_staples (30) | log_lev +, margin_trend −, coverage − | defensive volume |
| health_care (35) | log_lev +, margin −, margin_trend −, fcf_debt − | F2 A2: labour and bad-debt margin |
| technology (45) | log_lev +, fcf_debt −, margin_trend − | F2 A6: cash after capitalised development |
| telecom_media (50) | log_lev +, fcf_debt −, capex_int +, mat_wall + | F2 A5: EBITDA less capex, capex above 15% of sales |
| utilities (55) | log_lev +, coverage −, mat_wall + | regulated, asset heavy |

Driver formulas (`hy.sector.drivers`): `log_lev` = log of debt / LTM EBITDA clipped to [0.1, 20], non-positive EBITDA reads as 20. `log_lev_lease` = log of (debt + 8 rent) / (EBITDA + rent) (Section 4.3, Gatto pp. 267 to 268). `coverage` = EBITDA / interest, clipped to [−5, 30]. `ebitda_cyc` = minus the worst YoY EBITDA change over 10 years (F21). `capex_int` = capex / sales. `fcf_debt` = (CFO − capex) / debt. `margin` and `margin_trend` come from F23 and `hy.state.margin_trend`. `gross_margin` = (sale − cogs) / sale. `mat_wall` = (dd1 + dd2) / (dlc + dltt), the F21 two-year window.

### 3.2 Sector-relative scores (`hy.sector.relative`)
```latex
r_{f,i} = \operatorname{pctrank}_{sector(i)}(score_{f,i}) - 0.5, \qquad C_i = \frac{\sum_f w_{f,g} r_{f,i}}{\sum_f w_{f,g}}, \qquad EM_i = \tfrac13\left(r_{1m} + \tfrac{r_{3m}}{3} + \tfrac{r_{6m}}{6}\right)
```
Intuition: a pair inside a sector earns only the within-sector difference, so each factor is ranked inside the sector.

- Any bond or issuer factor of `hy.factors.REGISTRY` can enter. An index factor (F25 to F30) raises an error.
- Defaults: `sector_fs`, `emc16`, F04, F10, F19 (Our choice), with equal weights.
- `ic_group_weights` sets w ∝ max(0, IC) per group (methodology 8). A group with no positive IC gets no composite.
- `emc16` is the ch. 16 equity momentum. Note 4 (p. 552) divides by the window length. Ch. 15 note 9 (p. 541) divides by the square root. We follow ch. 16.
- A sector rank needs 5 bonds (`hy.peers.MIN_SECTOR`).

### 3.3 Within-sector pairs (`hy.sector.pairs`)
```latex
h = \frac{s_L D_L}{s_S D_S}, \quad conv = q\,[D_L(s_L - f_L) - h D_S (s_S - f_S)], \quad q = 1 - \rho^{H}, \quad carry = \tfrac{H}{12}(s_L - h s_S), \quad \frac{JTD_L}{JTD_S} = \frac{1 - 100R_L/P_L}{h\,(1 - 100R_S/P_S)}
```
Intuition: equal DTS on both legs cancels a parallel sector move in log spread, so the pair earns the residual gap.

- Candidates: longs in the top quarter of the sector's scores with score > 0. Shorts in the bottom quarter with score < 0 (Our choice).
- Match `dts`: the larger DTS is at most 1.5 times the smaller. Match `bucket`: same rating class and maturity bucket (`hy.peers.maturity_bucket`).
- Each long takes the richest admissible short. The cheapest long goes first. An issuer appears once. A sector gets at most 3 pairs (Our choice).
- ρ: the pooled AR(1) of the sector's past residuals (`residual_history`, at least 24 pairs). Otherwise ρ = 0.5^(1/3), a 3-month half-life, so that H = 6 months is two half-lives (Section 7.5).
- R: the class middle notch at (70 − 3r)%: BB 34%, B 25%, CCC 16% (F06, Martin p. 19). Without a class, R = 40% (`hy.rv`).
- `jtd_ok` holds when JTD_L ≤ 1.5 JTD_S (Our choice). `hedge_jtd` gives the short size that makes the pair JTD neutral.

## 4. Inputs
| Field | Panel and column | as_of | available_at rule | Have or need |
|---|---|---|---|---|
| spread, duration, price, maturity | `bond_panel`: `g_spread`, `mod_dur`, `price`, `years` | month end | last trade + 1 day | have |
| sector | `gics`: `gsector`, `indfrom`, `indthru` | in force at t | export date | have |
| leverage, EBITDA, debt | `leverage` | month end | month end + 1 day | have |
| rating class | `ratings`: `splticrm` | datadate | datadate + 1 day | have to Feb 2017, then implied |
| capex, sales, CFO, interest, margins | `compustat_quarterly`: `capx`, `saleq`, `oancf`, `xintq`, `oibdpq` | quarter end | `rdq` | need |
| rent, cogs, debt due, debt | `compustat_annual`: `xrent`, `cogs`, `sale`, `dd1`, `dd2`, `dlc`, `dltt`, `xint`, `capx`, `oancf` | fiscal year end | max(available_at, datadate + 90 days) | need (`xrent` is new) |
| EBITDA history | `annual_ebitda`: `oibdp` | fiscal year end | as above | have (optional) |
| stock returns | `equity_monthly`: `ret` | month end | month end + 1 day | have (optional) |
| past residuals | `residual_history`: `date`, `cusip`, `resid_log` | month end | decision time of that month | need (built from this module) |

## 5. Build steps
1. Take the universe at month end t: eligible, below 1,000 bp, HY class when ratings exist, a GICS sector that is not 40 or 60.
2. Compute the issuer drivers from rows known at t + 1 day.
3. Fit the pooled model. Then fit each group with 15 or more issuers on its own driver list. Thin groups take the pooled fit.
4. Score each bond with its residual over the robust residual sd.
5. Rank each chosen factor inside the GICS sector. Combine with the group weights.
6. In each sector, pick up to 3 cheap-rich pairs. Hedge by DTS. Report convergence, carry, net duration and JTD.
7. Store the month's residuals in `residual_history` for the next month's ρ.

## 6. Code placement
- `hy/sector/fairspread.py`: `compute(panels, as_of, min_issuers=15, drivers=None, pooled_drivers=...)`. Columns `COLS`, with `attrs["models"]` per group. Reuses `hy.peers`, F04 `rating_classes`, F08, F09, F21 and F23 helpers.
- `hy/sector/relative.py`: `compute(panels, as_of, factors, weights, frames, min_components)`, `within_sector_rank`, `issuer_em`, `sector_em`, `ic_group_weights`. Reuses `hy.peers._sector_pct`, `hy.peers.equity_momentum` and `hy.signals.ic_weights`.
- `hy/sector/pairs.py`: `pairs(...)` gives one row per pair. `compute(...)` gives one row per leg (weight +1 or −h). Reuses `hy.fairspread.expected_convergence_return` and `fit_ar1`, F22 `dts_hedge`, F06 `recovery_rate` and `hy.rv.SENIOR_UNSECURED_LGD`.
- Helpers: `hy/sector/common.py` (universe, `SECTOR_GROUPS`), `hy/sector/drivers.py` (drivers, `SECTOR_DRIVERS`, `SIGNS`), `hy/sector/synthetic.py` (test panels).

## 7. Tests
- Unit (`tests/test_sector_*.py`, synthetic data):
  - Contract columns. Empty frames when a required panel is missing.
  - No look-ahead: late restatements and future rows do not change any output.
  - A planted cheap bond tops its sector and becomes the long.
  - The fit recovers the true driver signs. The sign rule drops a wrong-sign driver.
  - Huber resists an outlier. A thin sector falls back to the pooled model.
  - Pairs are DTS neutral. Match rules hold. Convergence, carry and JTD match hand checks.
  - The pooled AR(1) recovers ρ = 0.8.
- Evaluation (production):
  - `sector_fs`: monthly within-sector rank IC against the 6-month excess return beyond log spread. It must beat pooled `esp_sr` (`hy.peers`) with HAC t ≥ 2, and be positive in at least 3 of the 4 cycles (2008, 2015, 2020, 2022).
  - Composite: rank IC after costs positive in at least 3 of 4 cycles.
  - Pairs: mean 6-month pair return after costs above 0 in at least 3 of 4 cycles. Report the realised loss on defaulted longs against the gain on defaulted shorts.

## 8. Risks
- The driver lists have no source test. A sector fit may only refit noise. The pooled model and the peer ESP are the benchmarks it must beat.
- In September 2018 GICS moved media and internet names from sector 25 into sector 50. Group membership breaks at that date.
- Collinear drivers (leverage and coverage) can flip signs. The sign rule then drops one of them, and the fit keeps the other.
- `g_spread` ignores calls. A callable bond above its call price looks cheap (Kricheff pp. 33 to 34: use spread to worst).
- A concentrated book of 3 pairs per sector carries large idiosyncratic risk. Dynkin ch. 13 finds an IR near 1 only at about 50 bonds per leg (PDF p. 460).
- The pair carries Treasury duration (`net_dur`). Hedge it with Treasuries.

## 9. Open questions
1. Group level. Default: the GICS sector. Alternative: GICS industry group (`ggroup`), which would split cable from retail. The `gics` panel does not hold it yet.
2. Fit form. Default: linear Huber with signs. Methodology 7.2 asks for monotone gradient boosting. Switch when a sector has enough issuer-months for it.
3. JTD threshold 1.5 and DTS tolerance 1.5x. Both are Our choice. Calibrate on the pairs' realised default outcomes.
4. Half-life 3 months without history. Replace it with the pooled ρ once `residual_history` has 24 months.
