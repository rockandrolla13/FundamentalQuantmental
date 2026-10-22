# "High-Yield Relative Value: Algorithm and Implementation Specification", Version 1.0

Practitioner specification, not peer-reviewed. Dated 22 October 2026. 47 PDF pages: a cover (PDF p. 1), a contents page (PDF p. 2, printed "i"), and printed pages 1 to 45. Page numbers below are PDF pages. PDF page = printed page + 2. The file is `high_yield_algorithm_specification.pdf` at the repo root.

The spec is a companion to `docs/high_yield_relative_value.pdf` (the "comprehensive PDF"). The repo extracted that PDF in `research/hyrv_extract.md` and mapped it in `research/hyrv_mapping.md`. The spec calls the comprehensive PDF "M" and cites its sections as "M §n". It says that the algorithms, contracts and portfolio objective are its own implementation choices, not rules from the books (p. 1, p. 24).

Do not confuse this spec with `research/combined_framework_spec.md`. The labels "spec K14", "spec K15", "spec S14" and "spec S15" in `scripts/process.py` and `hy/groups.py` point to that internal file, not to this PDF.

## Claim
The spec turns the comprehensive PDF into an executable decision system. Its one question is: "which permitted use of capital offers the best modeled net payoff within the investor's risk and implementation constraints?" (p. 3). Its main claims:
- Gatto's seven steps are dependencies, not a single score. A changed input invalidates only the stages that depend on it (p. 4, pp. 8–9).
- The final decision is a portfolio program. It maximises expected terminal wealth over joint physical scenarios under an expected shortfall (ES) limit and other limits. Cash and retention of the current portfolio are always comparators (pp. 26–29).
- A spread residual is a candidate signal, not an expected return (p. 3, R05). Signals are never summed into an uncalibrated composite (p. 24).
- The default fair-spread model is an issuer-excluded ridge regression of log OAS. The bond's own price, yield and spread are forbidden inputs (pp. 20–21).

The cover says: "Synthetic verification; no live investment results claimed" (p. 1). The spec claims no backtest.

## Method
**Time control (p. 7).** Each record version v carries economic time and knowledge time. A decision at t uses version v only if its availability time is at or before t:

```latex
t^{avail}_v = \max\left(t^{published}_v + \ell_v,\; t^{firstseen}_v,\; t^{embargo}_v\right), \qquad \text{use } v \text{ at } t \iff t^{avail}_v \le t
```

ℓ_v is a source-specific processing delay. Intuition: a fact counts from the latest of its publication plus delay, its first sight, and its embargo end. Among eligible versions, the greatest authoritative revision wins, not the latest ingested one. Each run hashes its inputs into an immutable `DecisionSnapshot` (p. 7).

**Stage states (pp. 8–9, p. 34).** Each Gatto stage is PASS, REVIEW, BLOCK, STALE or NOT_APPLICABLE. Approval binds the exact input and evidence hashes. An edit makes it STALE. Table 4.3 (pp. 9–10) gives the minimum recalculation set for each event type: a new filing, a financing, an amendment, a default, a new quote, a curve update, a review expiry.

**Step 3 measures (pp. 10–12).**

```latex
FCF = E^{uw} - I_c - T_c - K - W - O, \qquad FCF^{CFO} = CFO_{normalized} - K
A^{undrawn} = \max\{0,\ \min(\text{Commitment}, \text{BorrowingBase}) - \text{Drawn} - \text{LOC} - \text{Reserves}\}
L_{creation,k} = \frac{D_{senior,k} + \sum_{j\in k} N_j P_j/100}{E_{relevant}}, \qquad \text{pension: } \frac{D+U}{E + \text{PensionExpense} - \text{ServiceCost}}
```

Intuition: two cash bridges must meet. Undrawn capacity counts only what the contract lets the borrower draw. The creation multiple prices the whole layer at market, with seniors at face. Nettable cash is max(0, accessible unrestricted cash − minimum operating cash) (p. 11). A nonpositive EBITDA gives a null leverage with a reason code, never zero or a negative multiple (p. 7).

**Step 4 funded path (pp. 12–13).** Monthly cash buckets at minimum, with a finer event calendar around coupon, maturity and funding dates. A seven-step ordered event ledger per scenario:
1. Use cash above the operating minimum first. Then draw accessible facility capacity.
2. Any further need is `UnfundedGap`, not a revolver plug.
3. After mandatory payments and contract sweeps, repay the revolver from surplus. Retain the rest unless a policy says otherwise.
4. Iterate interest until the cash and debt difference is inside tolerance. Nonconvergence is BLOCK.

```latex
C_u = C_{u-1} + FCF_u + \text{DebtCash}_u + \text{EquityCash}_u + \text{AssetSale}_u - \text{Retirement}_u - \text{Distributions}_u - \text{Fees}_u
D^{face}_u = D^{face}_{u-1} + \text{NewFace}_u + PIK_u - \text{FaceRetired}_u + \text{OtherContractual}_u
```

Intuition: cash and face debt run as two ledgers. Free cash flow does not repay bonds unless a contract or a stated policy says so. A path may not keep paying with negative fictional cash. It must route to a resolution branch, or its valuation is BLOCK (p. 13). The working-capital inversion with average balances is AR_u = 2 DSO_u Revenue_u / d_u − AR_{u−1}. An impossible negative balance is rejected, not clamped (p. 12).

**Joint scenarios (pp. 15–16).** A finite grid Ω of joint physical scenarios with p_ω ≥ 0 and Σ p_ω = 1. All claims of one issuer share one issuer path and one default state. An incomplete grid carries the label `CONDITIONAL_ANALYSIS`. Stress-only states with no approved probability stay out of the expected value (p. 36).

**Exit value and convergence (p. 17).**

```latex
P^{d}_{b,H,\omega} = \sum_{u>H} CF^{contract}_{b,u,\omega}\, D_{H,\omega}(u)\, e^{-s^{disc}_{b,H,\omega}(u-H)}, \qquad s_{b,H,\omega} = s_{b,0} + \Delta s^{market}_{\omega} + \Delta s^{credit}_{b,\omega} - q_{b,\omega}\, e_{b,0}
```

Intuition: price the remaining cash flows at the scenario curve and spread. Close only part q of today's residual e. A zero-closure case (q = 0) is mandatory when convergence drives the proposal. Default loss is never subtracted again from a fully repriced path.

**Fair-spread baseline (pp. 20–21).** For target bond b of issuer i, drop all bonds of issuer i. Weight each peer bond 1/n_j, where n_j is the bond count of its issuer, then normalise. Fit:

```latex
(\hat\alpha,\hat\beta) = \arg\min_{\alpha,\beta} \sum_{k:\,issuer(k)\ne i} w_k\,(\log s^{OAS}_k - \alpha - x_k^\top\beta)^2 + \lambda\lVert\beta\rVert_2^2, \qquad e_b = s^{OAS}_b - \exp(\hat\alpha + x_b^\top\hat\beta)
u_g = 1.4826\ \mathrm{wmedian}_{r\in R_g}\left|e_r - \mathrm{wmedian}_{v\in R_g} e_v\right|, \qquad Z_b = e_b/u_g
```

Intuition: each issuer gets one vote, the target never prices itself, and the residual is scaled by a robust spread of past out-of-sample residuals. Features: underwritten gross leverage, FCF to debt, after-capex cash coverage, EBITDA margin, organic growth, liquidity to debt, 24-month maturities to debt, maturity, coupon, call terms, log issue size, lagged trade counts, sector, rating grade, claim class. Ratings enter as categories, not as equally spaced notches. Preprocessing: winsorise at the 1st and 99th weighted percentiles of the peer set, then scale. A target feature outside the raw training range returns `REVIEW:OUT_OF_DOMAIN`. Ridge grid {10⁻⁴, …, 1}. Choose the largest λ within one standard error of the minimum mean absolute error. The standard error comes from 1,000 moving-block bootstraps with four-week blocks and seed 1729 (p. 21). Tuning window: 104 weekly cuts before a 26-cut calibration window, with at least 52 cuts. Illustrative minima: 50 peer issuers, 100 peer bonds, 10 issuers in the target sector (p. 22). The spec warns that exp of the log fit is not a calibrated median unless the log error has median zero (p. 21).

**Issuer curve S2 (p. 22).** Log OAS linear in maturity. Leave the target bond out. Require three distinct maturities that span at least two years, and the target maturity inside that range. Do not mix ranks or guarantee packages.

**Optional PD model (p. 22).** Regularised logit with a fixed 12-month issuer event. Calibrate the intercept and slope on later, disjoint, matured data. Too few events returns `REVIEW:PD_INSUFFICIENT_EVENTS`.

**Step 7 program (pp. 25–29).** With purchases u_b, sales v_b, holdings h_b, dirty ask a_b and dirty bid s_b per unit face net of fees, and cash factor G_ω:

```latex
K = c^{old} + \sum_b s_b h_b, \quad x_b = h_b + u_b - v_b, \quad c = c^{old} - \sum_b a_b u_b + \sum_b s_b v_b
Y_{b\omega} = V^{net}_{b\omega}(H) + \sum_{0<u\le H} CF_{b\omega}(u)\,\frac{G_\omega(H)}{G_\omega(u)}, \qquad W_\omega = c\,G_\omega(H) + \sum_b x_b Y_{b\omega}
\max \sum_\omega q_\omega W_\omega \quad \text{s.t.} \quad z + \frac{1}{1-\alpha}\sum_\omega q_\omega t_\omega \le \overline{ES},\ \ t_\omega \ge 1 - W_\omega/K - z,\ \ t_\omega, z \ge 0
```

Intuition: every alternative starts from the same bid-marked capital K and ends at the same horizon. The ES constraint is the Rockafellar–Uryasev linear form. Further constraints: a cash floor, interim cash C_ω(t) ≥ C_min at every ledger date, no shorts, a face cap, issuer and sector caps, linear exposure bounds (CS01, DV01), turnover, an optional worst-scenario floor, and dealing lots. The problem is an LP, or a MILP with lots (SciPy HiGHS `linprog` or `milp`). A second pass minimises turnover inside a tiny tolerance of the optimum. An independent check rebuilds the net tickets and recomputes every constraint and the exact ES (p. 28). Trade only when the checked proposal beats retention by a policy hurdle. Seven return statuses, from `INPUT_BLOCKED` to `ENGINE_CHECKED_RISK_REBALANCE` (p. 29). An optional robust extension maximises the worst expected wealth over several approved probability vectors. It is specified but not built (p. 29).

**Validation (pp. 32–34).** Weekly cuts at 17:00 New York time. Fill no earlier than the next business day. A nine-step walk-forward per cut. A default label at anchor τ is usable only at τ + 12 months + label delay. Three separate scorecards: issuer credit, security compensation, investment selection. Cluster by issuer and date. Use time blocks for the portfolio path. Seven required ablations and seven required stresses (p. 34). Promotion runs SPECIFIED → RESEARCH_VERIFIED → HISTORICALLY_EVALUATED → SHADOW → LIVE_APPROVED.

## Data
- No real data. Every number in the worked example is synthetic (pp. 30–32).
- The spec defines ten record contracts (p. 7): FinancialFact, Adjustment, DebtClaim, Facility, BusinessRisk, Scenario definition, ForecastBucket, ValuationCase, MarketObservation, CorporateAction.
- Each output is a `FeatureValue` with status VALID, MISSING, NOT_APPLICABLE, UNDEFINED, STALE or ERROR (p. 6). NaN is never serialised.
- Appendix A lists 82 registered features, with formulas and units (pp. 42–44). Appendix B lists 53 acceptance cases with expected status codes (pp. 45–47).
- The spec names an implementation pack: package `hy_rv/`, `config/*.json` registries, `schemas/`, `examples/`, `tests/` (pp. 37–38). Tested on Python 3.12.14, NumPy 2.3.5, SciPy 1.17.0. The repo does not hold this pack: `hy_rv/` and `config/` do not exist.

## Result
The spec defines outputs and rules. It reports no empirical result.
- **Worked example (pp. 30–32).** Securities A, B and C. Three scenarios with probabilities 75%, 20% and 5%. K = 100,000. The MILP sells 60,000 face of C and buys 17,000 of A and 70,000 of B. Expected net return is 6.35976%, against 3.44320% for retention and 4.00000% for cash. ES95 is 24.93924%, against 4.05680% for retention. The probability of a return below cash is 25%. The spec checks the solution against a full enumeration of lots.
- **ES arithmetic check (p. 27).** Losses 0.10, 0.20, 0.80 with probabilities 0.90, 0.07, 0.03 give ES95 = (0.03 × 0.80 + 0.02 × 0.20) / 0.05 = 0.56.
- **Explicit non-claims (p. 3, p. 37).** No live data feed, no legal parser, no callable pricer, no fitted default model, no historical HY return experiment, no broker link. A synthetic test pass does not imply any of these.
- **No backtest.** The spec lists a historical experiment as build stage 6 of 8 (p. 39). It does not run one.

## What our data says (hy/, scripts/process.py, data/, 22 October 2026)
**What the spec adds beyond the comprehensive PDF.**
1. A portfolio program. The comprehensive PDF compares one bond with its alternatives (E50 to E60). The spec solves an LP or MILP across all holdings and candidates, with an ES epigraph, interim cash and lots.
2. A fixed fair-spread recipe. The comprehensive PDF says to use independent features and leave the issuer out (R168 to R171). The spec fixes the estimator, weights, grid, tuning window, bootstrap, robust error scale and minimum counts.
3. Stage states, approval hashes, event invalidation, error codes and the 53 acceptance cases. The comprehensive PDF has none of these.
4. Monthly cash buckets and an `UnfundedGap` that may never be plugged. The comprehensive PDF has the funding gap G_h but no bucket size.
5. A signal mode table: S1, S2, S3, S7, S8, S12 and S13 screen. S4, S5, S9, S10 and S14 go to review. S6, S11 and S15 stay disabled (p. 24).

**What hy and process.py already implement.**
- Decision against cash for one bond. `hy/alpha.py` holds `decision_against_cash`, `expected_shortfall` and `opportunity_cost`. `scripts/process.py` step 15 `step_decision` reports µ, P(loss), P(below cash) and ES95. Default and recovery sit inside the cash flows. This matches the spec's terminal-wealth logic for one bond against cash.
- Discrete ES with a fractional boundary state. `hy/alpha.py` `expected_shortfall` takes only the part of the last state inside the tail. That is the spec's independent ES check (p. 27).
- Funding gap and refinancing shock. `hy/forward.py` holds `funding_gap` and `refinancing_shock`. `process.py` `funding_and_refi` reports the minimum G_h, the first gap quarter and ΔI/E by path.
- Shortfall order and debt recursion. `hy/forward.py` `_roll_forward` draws the revolver only when cash falls below `min_cash`. Debt runs per tranche with amortisation, and `sweep_share` defaults to 0. Both match spec step 4. Mapping conflicts C8 and C9 now hold for the docs, not for this code. I did not recheck the current text of M5.1 and F6.1.
- Mondrian conformal band in `hy/fairspread.py`. It supplies an error scale. The spec uses a weighted MAD instead.
- Process status codes `done`, `partial` and `blocked` (`process.py` line 17). They are a coarse version of PASS, REVIEW and BLOCK.

**What is not built.** A grep for `ridge`, `linprog`, `milp`, `1.4826` and leave-one-out logic in `hy/` and `scripts/` finds nothing.
- No portfolio optimiser and no retention comparator. Step 15 compares one reference bond with cash.
- No issuer exclusion in the fair line. `process.py` line 1248 fits `np.polyfit(xs["lev"], np.log(xs["s5"]), 1)` on every run issuer, the target included.
- No leave-one-out issuer curve. `process.py` line 1242 fits `rv.curve_fit` on all bonds of the issuer.
- No OAS. The market spread is a TRACE G-spread, so the spec's `NONPOSITIVE_OAS` and call-term features have no input.
- No `UnfundedGap` branch inside the engine. In `_roll_forward`, when the draw cannot restore `min_cash`, cash simply falls and can go negative. The spec forbids that path.
- No approval hashes, STALE state or invalidation graph.
- Quarterly buckets, not monthly.

**Conflicts with the comprehensive PDF, methodology and framework.**
1. **Bond price as a fair-spread feature.** Methodology 7.2 (line 562) lists `log price` and `spread_duration` in the Term block. The spec forbids the target's price, yield, spread, implied PD and price-based duration (p. 20, MODEL-004). This sharpens mapping C14. The spec is stricter than the comprehensive PDF, which bans only the bond's own price in an OAS rebuild.
2. **Estimator.** `FairSpreadModel` in `hy/fairspread.py` is a monotone gradient-boosted model with a sector-date effect η and recency weights. The spec baseline is a linear ridge with issuer exclusion and a contemporaneous intercept. The two answer the same question. The spec allows a challenger, but only after it beats the baseline.
3. **Signal composite.** Methodology 8 and `hy/signals.py` (`ic_weights`, `composite`) weight signals by trailing IC. The spec says scores are "never added into an uncalibrated universal composite" (p. 24). An IC-weighted composite is calibrated, so this is a partial conflict. It needs the per-signal ablation of mapping C15 before it passes the spec's rule.
4. **Probabilities.** Methodology 5.2 and 5.4 make scenario weights from a fitted logistic and from Bayes. The spec wants approved, versioned weights, a default branch in every path, and the label `CONDITIONAL_ANALYSIS` for an incomplete grid. This is mapping C10.
5. **Lease and pension.** The spec uses the lease liability and labels 8× rent as "historical sensitivity" (p. 12). `hy/rv.py` `lease_adjusted_leverage` defaults to `multiple=8.0`. The pension form adds back expense less service cost (mapping C6 and C7). The spec agrees with the comprehensive PDF here.
6. **Implied PD.** The spec labels a risk-neutral hazard Q and forbids its use as a physical P (p. 20). `process.py` `step_gate` already shows the v0-κ default chance as "shown, not tested" and keeps it out of G1 (mapping C2). This now agrees.

**What we could build first.** Each item runs on data the repo loads.
1. Issuer exclusion and 1/n_j weights in the step 9 fair line. Report the residual next to today's in-sample residual.
2. Leave-one-out issuer curve with the spec's three-maturity, two-year span rule (S2).
3. An `unfunded_gap` field in `_roll_forward`. Stop the path at the first quarter where accessible capacity cannot restore `min_cash`.
4. A retention comparator and a small LP across the run's reference bonds and cash. Use `scipy.optimize.linprog` with the ES epigraph. Reuse the `decision_against_cash` state tables as Y_{bω}.
5. A `q = 0` row in step 15, required when convergence drives µ.

**Falsifiable tests on our panel.**
1. **Leakage of the target.** Refit the step 9 line with and without the target issuer. If the residual rank IC with forward 6-month TRACE excess return rises when the target is excluded, the in-sample fit was absorbing the signal. Keep the issuer-excluded fit.
2. **Price feature leakage.** Fit `FairSpreadModel` with and without `log price` on the TRACE panel. Reject `log price` if the residual variance falls but the residual's rank IC falls too (mapping C14). Pass rule from CLAUDE.md: positive IC after costs in at least three of 2008, 2015, 2020 and 2022.
3. **Ridge against boosting.** On weekly cuts, compare issuer-excluded MAE of the spec ridge with that of `FairSpreadModel`. Keep the boosted model only if it wins out of sample and its residual IC is no lower.
4. **Zero convergence.** Recompute step 15 µ with q = 0. Flag every issuer whose µ changes sign. The spec says such a proposal rests on convergence alone.
5. **ES code check.** Feed the spec's three-state example to `hy/alpha.expected_shortfall` as returns −0.10, −0.20, −0.80. It must return 0.56. Add this as a unit test.

## Limits
- Not peer-reviewed. An AI-assisted engineering release dated one day after its source. It cites only four outside works: the comprehensive PDF, Rockafellar and Uryasev (2002), and two SciPy pages (p. 47).
- No empirical evidence. Every threshold is an illustrative policy value: the 95% ES level, the 25% loss limit, the 70% issuer cap, the 10 bp hurdle, the ridge grid, seed 1729, the 50 and 100 peer minima (p. 18, p. 31). Treat them as framework R9 defaults, not findings.
- The baseline is long-only, single-currency and noncallable. Most HY bonds are callable. The spec blocks a callable bond with no option-aware adapter (p. 4). Our universe would then have few eligible bonds.
- The ridge needs OAS, issue size and call schedules. TRACE `bond_master` holds none of these (mapping data fact 1).
- Expected-wealth maximisation with a linear ES limit is risk-neutral inside the limit. The worked example picks a portfolio with six times the ES of retention for a 292 bp gain (p. 31).
- The spec's approval and governance layer assumes analyst sign-off. This repo has no analyst workflow, so most of Sections 4 and 14 have no counterpart.
- pdftotext garbled the ES epigraph, the ridge objective and Equations (1) to (13). The formulas above are rebuilt from the legible fragments and checked against the worked example.

## Section touched
`docs/methodology.md` Section 5.1 and 5.4 (funded path, unfunded gap, monthly buckets, debt recursion), Section 7.2 and 7.3 (fair-spread features, issuer exclusion, error scale), Section 7.5 (convergence with a zero-closure case), Section 8 (signal composite and signal modes), Section 9.4 (portfolio limits and ES), and Section 11 (walk-forward, three scorecards, ablations). `docs/framework.md` F6.1 (shortfall order), F9 (gate statuses) and F10 (sizing). `scripts/process.py` steps 4, 9 and 15. `hy/alpha.py`, `hy/forward.py`, `hy/fairspread.py`, `hy/signals.py`, `hy/rv.py`. No decision page yet. A sprint that builds test 1 or the step 15 LP should add one.
