# F06. Within-issuer curve residual on par-adjusted spread

## 1. Header
- **Rank:** 6 of 30, Tier 1 (tested in credit, buildable now).
- **Status:** NEW. It extends S4 capital structure relative value (Section 8) from tranche pairs to the same-seniority curve. Its spread measure is a variant of the coupon and price effect.
- **Sources (all under `/home/ak/Documents/Quant Credit/`):**
  - Osband and Goulden (J.P. Morgan, 13 February 2012), `Work_Quant (1)/JPM_Investment_Strategie_2012-02-13_784342 (1).pdf`, PDF pp. 6 to 13, 16 to 18, 21 to 23.
  - Martin, `The credit spread curve.pdf`, PDF pp. 6, 8 to 12, 14 to 15, 19 to 20. Same text in `The_credit_spread_curve_I_Fundamental_concepts_fit.pdf`, PDF pp. 10 to 11.
  - `credit_spread_stat_arb_architecture_bridge_v0_1.pdf`, PDF pp. 3 to 4.
- **Reader blocks:** G-F1, A2-F1, A1-F1, B-F12.

## 2. Claim
Among US high yield bonds of issuers with two or more bonds of one seniority, a bond with a par-adjusted spread above its leave-one-out issuer curve earns a higher excess return than its sibling bonds over the next 2 months. The sign is positive.

## 3. Definition
**Par-adjusted spread (Martin eq. 9, p. 12).** B is the Treasury discount curve, Q the survival curve, c the coupon, P the clean price:

```latex
\frac{P}{100}-1=\big(c-\hat r(T)-s\big)\,\Pi(T),\quad \Pi(T)=\int_0^T B Q\,dt,\quad \hat r(T)=\frac{\int_0^T f B Q\,dt}{\int_0^T B Q\,dt},\quad \frac{\hat P}{100}=c\,\Pi+B(T)Q(T)+\Re\,\Xi,\ \ \Xi=-\int_0^T B\,dQ
```

Intuition: s is the running spread the bond would pay if it traded at par, so bonds at 60 and at 110 compare. Source: Z-spread makes high-price bonds look cheap (p. 9).
- **Q per bond (our choice).** Martin fits Q per issuer to prices (p. 14). We take a flat hazard Q(t) = e^{−λt} per bond. λ solves P̂(λ) = P. Then s = (1 − ℜ)Ξ/Π exactly (eq. 7, p. 11). Integrals use the trapezium rule, eq. 11 (p. 12), step 0.5 years (p. 8, footnote 9).
- **Recovery (p. 19).** ℜ = (70 − 3r)%, r the linear rating: BBB− 40%, BB 34%, B 25%. r = 1 for AAA, one step per notch. Our choice: an issuer with only an implied class takes the middle notch of the class (BB 12, B 15, CCC 18, IG 10). No class at all: B (r = 15).
- **B (our choice).** Bootstrap semiannual discount factors from the Treasury par curve on a 0.5-year grid. Interpolate log B linearly.

**Issuer curve (JPM forward shock model, p. 22).** Fair spread C(x) = a₀ + Σ aᵢ(1 − e^{−λᵢx})/x. The source fixes one factor, λ = 0.4 (expected life 2.5 years). A 3 to 8 year shock changes little (p. 22). With λ fixed the fit is OLS:

```latex
\hat s_{-b}(T)=a_0+a_1\,\frac{1-e^{-\lambda T}}{\lambda T},\qquad e_b=s_b-\hat s_{-b}(T_b),\qquad z_b=e_b/\hat\sigma_{-b},\qquad RV_b=e_b\,\Pi_b(T_b-\Delta t)
```

Intuition: one issuer has one default process, so a bond off its own curve carries a technical, and technicals fade (JPM p. 9). The source divides by x, not λx. With λ fixed the constant goes into a₁, so the fit is the same.
- **Leave one out (bridge p. 3).** Fit the curve without bond b. σ̂₋b is the standard error of that fit. Positive e means cheap. RV is the price value of full convergence with the forward RPV01 (Martin eq. 20, p. 20; bridge p. 4). Δt = the 2-month horizon.
- **Tiers.** (1) `issuer`: 5 or more bonds in the issuer-seniority curve, the JPM minimum (pp. 6, 8). (2) `group_shape` (our choice, after reader B-F12): 2 to 4 bonds. The slope a₁ comes from a within-issuer regression over the other issuers of the GICS sector × rating class cell. The level a₀ is the mean of s − a₁x over the issuer's other bonds. The cell needs 5 other issuers (`hy.peers.MIN_PEERS`). Else fall back to class, then sector, then all (`hy.peers.FALLBACK["sr"]`). No cell with 5 issuers: no score. (3) `single`: one bond, no score.
- **Score.** `score` = RV_b. **Trade flags (JPM).** Base: |e| ≥ 30 bp and |z| ≥ 1 (p. 8). Strict: |e| ≥ 40 bp and |z| ≥ 1.5 (pp. 10, 13).

**Call-option distortion.** JPM excludes bonds with embedded options (p. 8). Most HY bonds are callable (G-F1). A callable bond priced at or above its call price trades to the call date. Its spread to maturity is then too low, and the bond looks rich for a reason the curve does not model. Our choice: drop such a bond from the fit and the score (`call_status = itm`). Keep a callable bond below its call price, with a flag. Without call data, use the proxy call price 100 × (1 + c/2), par plus half a coupon (our choice, no source in the folder). Option `bullets_only=True` keeps bullets only, as the source does.

## 4. Inputs
| Field | Production table and column | `as_of` | `available_at` lag rule | Status |
|---|---|---|---|---|
| Price, coupon, years, G-spread, mod. duration | `bond_panel.price`, `coupon`, `years`, `g_spread`, `mod_dur` | month end | panel `available_at` (trade day + 1) | have |
| Treasury par curve | `treasury_curve` (Section 4.7): `date`, tenor columns, `available_at` | curve date | date + 1 day | have (optional) |
| Curve fallback | `bond_panel.tsy_yield` against `years` | month end | panel `available_at` | have |
| Seniority, call terms | new panel `bond_terms`: `cusip`, `seniority`, `callable`, `call_date`, `call_price` (per 100), `available_at` | as of export | export time | need (FISD) |
| Rating | `ratings.splticrm` | `datadate` | panel `available_at`, ends Feb 2017 | have |
| Implied class | `leverage.leverage`, `ltm_ebitda` | month end | panel `available_at` | have |
| Sector | `gics.gsector` | `indfrom` | panel `available_at` | have |

Only `bond_panel` is required. Every other panel has a fallback that the output names.

## 5. Build steps
1. Filter every panel to `available_at` ≤ `decision_time(as_of)`. Keep `bond_panel` rows at `date` = as_of that pass `hy.backtest.eligible` and `not_distressed` (G-spread ≤ 1,000 bp).
2. Build B from the latest Treasury curve, else from the panel's (years, tsy_yield) pairs.
3. Per issuer: rating notch, class (actual, else leverage-implied with `hy.peers.fit_cutoffs`), ℜ.
4. Per bond: call status. Drop `itm` bonds. Solve λ. A price below the recovery floor has no λ: status `below_recovery`, no score.
5. Per bond: s, Π, Π(T − Δt).
6. Group bonds by gvkey × seniority. Apply the tiers of Section 3. Compute e, σ̂, z, RV, flags.
7. Write one row per eligible bond, NaN score where a step drops it, with `status`.

## 6. Code placement
- **Module:** `hy/factors/f06_issuer_curve_residual.py`. `compute(panels, as_of, horizon_months=2, measure="pas", bullets_only=False)`. `measure="g_spread"` builds the same residual on G-spread for the A2 test.
- **Helpers:** `recovery_rate`, `rating_notch`, `discount_factors`, `flat_hazard_legs`, `par_adjusted_spread`, `shock_basis`, `loo_curve`, `within_slope`, `call_status`.
- **Section to cite:** Section 8 S4. Recovery: Section 6.2.
- **Output columns:** `date`, `cusip`, `score`, `available_at`, `gvkey`, `seniority`, `status`, `tier`, `n_curve`, `pas`, `hazard`, `recovery`, `rpv01`, `fit`, `resid`, `se`, `z`, `signal_base`, `signal_strict`, `call_status`, `curve_source`.
- **Reuse:** `hy.backtest.decision_time`, `eligible`, `not_distressed`. `hy.peers.rating_class`, `rating_at`, `sector_at`, `fit_cutoffs`, `implied_class`, `MIN_PEERS`, `FALLBACK`. `hy.sources.treasury.interpolate`.

## 7. Tests
- **Unit.** No look-ahead (late rows and late `available_at` change nothing). Sign: a bond priced cheap to an exact curve gets the top score. Par adjustment: bonds with 3% and 12% coupons on one hazard and one recovery give equal s and zero residual. Martin p. 15 example: ℜ = 0 gives s = 258 bp and 298 bp. Edge cases: missing panels, call proxy, `itm` drop, price below recovery, a 3-bond issuer, a 1-bond issuer, NaN price.
- **Evaluation.** Horizon 2 months (JPM p. 8), also 1 month. Target: excess return minus the issuer-seniority mean, net of half the round-trip cost. Pass 1: monthly rank IC > 0 after costs in at least 3 of 4 cycles (`cycle_test`), mean IC > 0.05 (G-F1). Pass 2 (A2-F1): the `pas` residual beats the `g_spread` residual by 0.02 in 3-month IC, Newey-West t > 2. Pass 3 (A1-F1): the correlation of the residual with dollar price falls by half against the G-spread version.

## 8. Risks
- **Weak corporate evidence.** EM corporates had IR 0.32 against 1.31 for sovereigns (pp. 11 to 12). The test sample has 13 corporates and 13 sovereigns (p. 8). No US HY test exists.
- **Costs.** The base case falls from IR 1.20 to 0.10 with 20 bp bid-offer (p. 13). Only the strict signal keeps IR 0.81 at 20 bp (404 trades, p. 13). The base case breaks even at 27 bp (p. 13). HY bid-offer is often wider.
- **Crisis.** The base case lost in Sep to Nov 2008. Its 2008 IR is −0.03 (p. 10).
- **Rich leg is weak.** Cheap IR 1.62, rich IR 0.30 (p. 9). Shorting HY bonds costs repo.
- **Data.** Without `bond_terms`, secured and unsecured bonds share one curve, and the call proxy misses call schedules. Many HY issuers have 1 to 3 bonds (B-F12), so the group tier carries most bonds.
- **Overlap.** ESP (`hy.peers`) is an issuer-level gap. F06 is issuer-neutral by build. The source gives no correlation.

## 9. Open questions
1. **Per-bond flat hazard or a joint price fit.** Martin fits Q per issuer to prices (p. 14). Default: per-bond flat hazard. Reason: it is closed form and the same for every tier. It differs from the joint fit only on steep curves.
2. **Weights.** Martin weights by amount outstanding with a soft penalty (pp. 14 to 15). We lack amount outstanding. Default: equal-weight OLS, as JPM does (p. 8).
3. **Score scale.** Default: RV in price terms, which is what equal notional earns (JPM p. 8). Report z too.
4. **Recovery source.** Martin p. 15 says ℜ = 53.5% fits both COLOM bonds. His table on p. 10 gives 55.5%. Our code reproduces 55.5%.
