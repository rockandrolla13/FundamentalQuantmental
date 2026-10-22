# Mapping: PDF *High-Yield Bond Relative Value* against methodology, framework and `process.py`

As of 2026-10-22. Companion to `research/hyrv_extract.md`. Item labels (E, U, P, R, S) refer to that extract.

Reference files:
- `docs/methodology.md`: "M" plus section number (canonical numbers).
- `docs/framework.md`: "F" plus rule number.
- `scripts/process.py`: "step" plus number (1 inputs, 2 frame, 3 normalise, 4 liquidity, 5 capital structure, 6 two clocks, 7 cases under macro paths, 8 valuation, 9 relative value, 10 expected alpha, 11 gate, 12 events).

## Legend

**Status.**
- `same`: the PDF and the repo say the same thing.
- `more`: the PDF is more detailed. The repo has the idea but not the full procedure, formula or guard.
- `new`: the repo has no counterpart.
- `conflict`: the PDF and the repo disagree. The conflict number (C1 to C20) points to the last section.

**Data now** (for `new` and `more` rows).
- `NOW`: computable today for real issuers from data that the repo already loads.
- `NOW+tag`: the source is already in the repo, but the loader needs one more field or XBRL tag.
- `DOC`: needs an indenture, a credit agreement, a plan, or a note that no parser in the repo reads.
- `JUDG`: needs analyst judgement. A v0 default with a decision page can stand in.
- `NONE`: the data is not in the repo (credit registers, news, default labels, bank call reports, rating histories).

Data codes: CS = Compustat point-in-time quarterly (`saleq, oibdpq, spiq, dpq, xintq, txtq, cogsq, xsgaq, cheq, invtq, rectq, apq, dlcq, dlttq, capxq, oancfq, intpnq, txpdq`); FQ = `comp.fundq` price and shares; XB = SEC XBRL instance (debt maturity ladder, lease payment schedule, RPO, purchase obligations, customer concentration axis, interest and taxes paid); TX = filing text; TR = TRACE (price, yield, coupon, maturity, seniority, 144A flag, grade, volume, trade history); UST = Treasury par curve; FR = forecast registry (SPF, FOMC SEP, Treasury forwards, SLOOS, TRACE HY level).

Data facts that limit many rows:
1. TRACE master (`bond_master`) has no amount outstanding, no call schedule, no lien detail. Face by tranche and rank needs XB (`DebtInstrumentCarryingAmount`, where tagged) or DOC.
2. No default-event labels exist in the repo. Every PD-validation row is `NONE` until a label set exists.
3. Revolver commitment and draw are tagged for some filers only (`process.py` step 4 already flags this).

---

## 1. Process architecture (PDF Sections 1 and 2)

| ID | PDF item | Methodology | Framework | process.py | Status | Data now |
| --- | --- | --- | --- | --- | --- | --- |
| P1 | Seven steps; Step 3 has three parts | Book page, "seven-step process" table; M12 | F1 R2 order | Steps 1 to 12 follow F1 order | same | — |
| R1, R2 | PD is not OAS; OAS residual is not expected return; strong issuer can have an expensive bond | M1 "the gap is the mispricing" | F9 preamble separates opinion and call | Step 11 | conflict C1 | — |
| R3, R88 | A score or a wide spread never waives an unfinished stage | — | F9 R7; F1 R2 | Steps return `partial` and `blocked` | same | — |
| P2 | Iterative re-run of affected stages; dated decision trail | M5.4 "Revisions" | F6.7 re-run on filing, guidance, phase change | Not in process (one pass) | more | NOW (re-run on new `available_at`) |
| Three files | Issuer file, security file, decision file; one issuer analysis linked to every claim | M10 tables `issuer_state`, `tranche_state`, `bond_daily` | F12 memo | `data/raw/process/<ticker>.json` plus memo | same | — |
| R4 | Bank ratios only when the issuer is a bank | — | F2 A8 routes financials out | Not in process | same | — |
| R5 | State the best feasible alternative and why; comparison universe informs value, feasible universe decides action | M8 `replaces_position`; M11 "Who supplies what" | F1 R8; F12.2 | Not in process | more | NOW (see Top 10, item 1) |
| 2.1, R7 to R9 | Feasible opportunity set first; same-rating peers are not the whole choice; data gaps are coverage gaps; repeated bonds of one issuer are related observations | M1 universe (price above 80, spread below 1,000) | F1 R1 scope | Step 9 fits one 5-year point per issuer | more | NOW (issuer clustering in fits); mandate JUDG |
| 2.2 schema | Seven record types with update triggers | M3.1 to M3.7 | F1 R5 | Step 1 | same | — |
| R10 | TRACE gives transaction-price estimates, not executable quotes | M3.1 lists dealer quotes and TRACE prints | — | Steps 5, 9 use TRACE last-10-day yields as market | more | NOW (label TRACE-derived spreads as estimates; add a quote-age field) |
| R11 | Credit-register data and internal ratings are not public | — | — | — | new | NONE |
| U1, U2 | Dirty = clean + accrued; MV = N P_d / 100 | M3.1 `price_bid` etc. | — | TRACE price is clean; no accrued | more | NOW (accrued from TR coupon and maturity) |
| E1 to E3 | Bullet price-yield; effective annual yield; MOIC | M3.1 `ytw`, `ytm` | — | Step 5 shows TRACE yield | new | NOW (TR) |
| R12 to R15 | Dated cash flows; MOIC ignores timing; promised yield is not expected return; entry at offer, exit at bid | M7.5 carry; M9.3 exit cost | F9 G3 net of bid-ask | Step 10 cost test | more | NOW for yield conversion; bid and ask NONE (TRACE side proxy only) |
| R16 | Verify clean, dirty or flat convention per instrument, not by geography | M3.1 "clean price in the US, dirty in Europe" | — | — | conflict C18 | — |
| E4, R17 | Availability indicator with justified delay; period end is not the information date; no backfill | M3 `available_at` rule | F1 R5 | Step 1 decision time; Compustat PIT vintages; TRACE 1-day lag | same | — |
| R18 to R20 | Keep reported and adjusted definitions; accessible cash only; separate financial debt, provisions, capex types | M4.2 note on unrestricted cash | F4.1 free cash; F3 three EBITDAs | Step 5 uses total cash | same | — |
| E5 to E9 | Δ4, peer difference, relative change, stress value, data age | M4.1 `margin_peer_gap`; M4.2 `payable_days_trend` | F3.3 peer set of at least four | Not in process | more | NOW (CS; peers = run issuers of the same archetype, JUDG for the peer list) |
| R21 to R24 | Peers fixed before outcomes; flag undefined ratios; fit transforms in training only; algebraic variants are not independent | M7.2 monotone constraints | F3.3 | — | more | NOW (flags); fitting rule applies to M7 |

## 2. Step 1: sources and uses (PDF Section 3)

| ID | PDF item | Methodology | Framework | process.py | Status | Data now |
| --- | --- | --- | --- | --- | --- | --- |
| P3 | Sources and uses for originations only; secondary purchases rebuild the structure later | Book table, step 1 "Originations only" | — | Not in process | same | — |
| E10 to E12 | Closing identity; proceeds at discount; face roll | — | — | Not in process | new | DOC (8-K transaction exhibits); NOW only for E12 from successive XB debt totals |
| R25 to R30 | Count each cash move once; premium retirements; legal-entity cash; LCs use availability; no uncommitted financing plug | — | F4.1, F4.2 | — | new | DOC |
| Features | Net new face debt, proceeds per face, distributions over proceeds, sponsor cash at risk | — | F2 M1 sponsor flag | — | new | DOC; net new debt NOW from CS `dlcq + dlttq` changes |

## 3. Step 2: qualitative analysis (PDF Section 4)

| ID | PDF item | Methodology | Framework | process.py | Status | Data now |
| --- | --- | --- | --- | --- | --- | --- |
| P4 | Eight industry risks; three to five material risks each with a scenario | M4.4 flags scored 0, 1, 2 | F2 archetype, "what breaks it"; F6 downside by archetype | Step 2 archetype and break line | same in content | — |
| R31, R34, R36 | Qualitative analysis must change the forecast; do not add qualitative scores to quantitative ratios | M4.4 "the fair spread model learns a weight per flag" | F3 `eq_score` count | — | conflict C16 | — |
| P5 | Evidence ledger: assertion, support, contrary evidence, variable, magnitude, next observation | — | F1 R4 source for every number | Step outputs carry `sources` | more | JUDG (structure NOW) |
| E13, E14 | Customer HHI; top-customer share | M4.7 `cust_top1`, `cust_top3`, `cust_hhi_floor` | F2 M3 above 20% | Step 2 reads `cust_top1` | same | — |
| E15 | Fixed cost share | M5.1 variable cost ratio | F2 A4 "high fixed cost share" | — | more | JUDG (cost classification); CS `cogsq`, `xsgaq` give a crude split |
| R32 | Undisclosed split is missing, not zero | M4.7 "undisclosed is NaN, not 0" | — | Step 2 | same | — |
| 4.2, R35 | Cycle conditions scenarios through observable credit availability; a cycle label is not a mechanical clock | M3.6 `cycle_phase`; M5.4 Bayes prior | F6 phase vote of six indicators and weight table | Step 7 `phase` | conflict C20 (minor) | — |
| 4.2 sponsor | Sponsor incentives can reverse deleveraging | M4.4 `sponsor_behavior` | F2 M1; F7 LME +1 | — | same | — |

## 4. Step 3: financial statement analysis (PDF Sections 5 and 11)

| ID | PDF item | Methodology | Framework | process.py | Status | Data now |
| --- | --- | --- | --- | --- | --- | --- |
| P6, R37 | Six profitability substeps; repeated cash costs are not nonrecurring | M4.1 | F3 C1 to C10; F3.1 history length | Step 3 (special items, EQ1, EQ2, EQ5, EQ7) | same | — |
| P7, R38 | Ten liquidity substeps; a current ratio does not substitute | M4.2 | F4 | Step 4 | same | — |
| P8 | Six capital-structure substeps; table ordered by impairment risk with cumulative metrics | M3.3; M4.3 | F5 | Step 5 (bonds only, no face) | same in design; process partial | DOC for loans and face |
| P9 | Five Gatto earnings-quality tests | M4.1 `eq_flags` | F3 EQ1 to EQ10 | Step 3 runs EQ1, EQ2, EQ5, EQ7 | more | NOW for DSO and DIO parts; DOC for absorption and expense detail |
| E16, E17 | Backlog bridge; book-to-bill = orders over revenue | M4.1 "orders over shipments" | F3 EQ3; F8 band 0.9 and 1.0 | Not in process | more | NOW+tag for RPO filers: implied orders = ΔRPO + revenue (XB RPO already loaded); true orders TX |
| E18 | Demand gap g_orders − g_revenue | — | F3 EQ3 | — | new | NOW+tag (same RPO proxy) |
| E19 | Allowance ratio ADA over gross AR | — | F3 EQ1 uses days only | — | new | NOW+tag (XB `AllowanceForDoubtfulAccountsReceivableCurrent`) |
| E20 | Constant-currency organic growth with price and mix kept inside | M4.1 `organic_growth` removes price | F3 EQ4 "organic excludes FX, M&A, and price" | — | conflict C17 | DOC (acquired revenue, FX by country) |
| E21 | LTM identity | — | F3.2 | Step 3 uses four decumulated quarters | same | — |
| E22, E63 | E = unadjusted EBITDA + accepted signed adjustments | M4.1 `EBITDA^adj` formula | F3 three EBITDAs | Step 3 shows LTM EBITDA and special items | same | — |
| E23, E69, U35 | FCF = E − I_c − T_c − K − W − O; CFO route without double count | M4.2 FCF identity with `CashNR` | F4.9 burn split | Not printed in process | same formula; process lacks it | NOW (CS) |
| E24, E64, E65 | Gross and net leverage | M4.3 `net_lev` | F8 `lev_gc_total`, `net_lev` | Step 5 `net_lev` | same | — |
| E25, E66 | Cash interest coverage E/I_c | — | — | — | new | NOW (CS `oibdpq`, `intpnq`) |
| E26, E68, U9, U10 | After-capex coverage; alternative contractual coverage definitions | M4.3 `Cov = (EBITDA − Capex)/Interest` | F5 `coverage` uses cash interest; `fccr` | — | more (PDF separates I and I_c and names three contract forms) | NOW for (E − K)/I_c; contract forms DOC |
| E67 | Total coverage E/I_total | — | — | — | new | NOW (CS `xintq`) |
| E27, E70 | FCF over debt | M4.2 `fcf_to_debt` | F8 bands 0.03 and 0.10 | — | same; process lacks it | NOW |
| E71 | Add-back dependence | M4.1 `covenant_gap` | F3 EQ9; F8 | Step 3 open question | same | DOC (covenant EBITDA) |
| E72 | Cash conversion CFO_norm / E | M4.2 `fcf_conversion` = FCF/EBITDA | F3 EQ7 (CFO − capex)/EBITDA | Step 3 EQ7 | more (a third definition; keep all three) | NOW (CS `oancfq`) |
| E28 to E30, R47 | JCP liquidity bridge; static liquidity must be read with burn and trade support | M4.2 `runway_q` | F4.6 trade flag | Step 4 | same | — |
| R48 | Maintenance capex is not depreciation by rule; state the evidence | M4.2 `capex_flex` | F4.7 "use depreciation as the floor for A4 and A5" when undisclosed | — | conflict C19 | — |
| E31, U7, U8, R49 | Creation leverage: seniors at face, the whole target layer at market | M4.3 `Lev^mkt_k` puts only tranche k at market | F8 `creation_multiple_k` | Not in process | conflict C5 | DOC (face by rank); NOW+tag where XB tags instrument carrying amounts |
| E32, E33, R50 | Lease leverage: 8x rent and liability method; prefer liability | M4.3 `(debt + 8 × rent)/(ebitda + rent)` | F5 liability after 2018, 8x earlier | Step 5 `lev_lease_adj` with 8x (`hy/rv.py` default) | conflict C6 | NOW+tag (XB `OperatingLeaseLiability`; lease payments already loaded) |
| E34, E35, R51 | Pension underfunding to debt and expense less service cost to EBITDA | M4.3 `debt_adj` adds deficit only | F5 `debt_adj`; claims view uses termination liability | — | conflict C7 | NOW+tag (XB pension tags) |
| R52 | US examples are not rules for every regime | — | F1 R9 | — | same | — |
| U24 to U34 | Scalia feature dictionary (interest burden, ROD, cash buffer, current ratio, mismatch, sales to debt) | — | — | — | new | NOW for interest burden, ROD, cash buffer, sales to debt (CS); NOW+tag for current ratio and mismatch (`actq`, `lctq`); NONE for CF_source and value added |
| R107 | Keep reported, underwritten, contract-defined sets apart | M3.2 three EBITDAs | F3 | Step 3 | same | — |
| R108 to R110 | Development medians are not thresholds; do not label public CFO as CF_source; a covariate is not an underwriting test | — | F1 R9 defaults | — | more | — |
| E73, E74, R115 | DSO, DIO, DPO, CCC on 365-day TTM average balances; one declared convention | M4.2 `cash_cycle` | F8 `cash_cycle` | Step 3 uses end balance × 91 days per quarter | more (convention) | NOW (CS) |
| R116, R117 | Derive WC cash from balances; capex ratios are diagnostics | M5.1 WC from days | F6.5 | — | same | — |
| E75, E76, R118 | Funding gap G_h, its minimum, first failure date, maturity share | M4.2 `liquidity_L`, `runway_q`, `wall_cover_h`; M5.3 `liq_min_down` | F4 `L_eff`, `runway_scen_q`, `wall_cover_h`, `refi_date` | Step 4 `min_liquidity_severe_by_path` | more | NOW (CS cash, XB ladder, scenario FCF; revolver NOW where tagged, else DOC) |
| E77, R119 | Refinancing interest shock ΔI; signal is the effect on coverage, FCF and liquidity | M5.4 `ΔCashInt_h(m)`; M9.2 rate channel | F6.3 refinance at forecast + fair spread | Step 7 uses it inside the engine; no ΔI/E output | more | NOW (XB ladder, TR coupons, UST, FR forwards) |
| E78 to E80, R120 | Leverage and coverage headroom; decline to breach | M4.6 `H_t` | F8 `H_t` bands; F6.2 | Step 3 open question | same | DOC |
| R121 | Track distributions, primary proceeds, retirements, transfers; do not add overlapping baskets | M3.4 baskets | F7 LME score | — | more | DOC |
| E81 to E84, R122 | Utilization, overdraft months, unpaid sales, bank withdrawal; public proxy = disclosed revolver | — | F4 revolver inputs | Step 4 revolver capacity | new | NONE (registers); NOW+tag for disclosed revolver draw |

## 5. Step 4: forecasting (PDF Section 6)

| ID | PDF item | Methodology | Framework | process.py | Status | Data now |
| --- | --- | --- | --- | --- | --- | --- |
| R53 | Horizon includes the next material refinancing even for a short trade | M5.3 horizons 4 and 8 quarters | F6 "12 when a maturity sits inside 3 years" | Step 7 | same | — |
| P10, R54, R55 | Eight forecast items; no unexplained hardcode; coin-toss base case | M5.1; book principles | F6 case rules | Step 7 (base = trailing growth) | same | — |
| E36, R56 | Average-balance AR inversion; align day count with bucket | M5.1 WC from days | F6.5 | Engine in `hy/forward.py` | more (convention) | NOW |
| E37 | Revenue = Σ volume × price | M5.1 `Rev^s_h` growth form | F6 driver set | — | new | JUDG and DOC |
| P11 | Sweep order: surplus repays revolver, then accumulates; shortfall uses cash above minimum, then revolver; record unfunded gap | M5.1 "negative FCF draws the revolver" | F6.1 revolver first, then cash to minimum | Engine | conflict C9 | — |
| E38, E39, R57 | Separate cash and face-debt recursions; PIK accrual; fees | M5.1 `D_h = D_{h−1} − FCF_h + Draw_h` | F6.1 | Engine | conflict C8 | — |
| P12, R58 | Joint operating and financing scenarios; stress refinancing access, not only price | M5.4 refinance at path rate when `p_refi_access > 0.5` | F6.3; F4 refinance score | Step 7 `refi_fail_share` | same | — |
| Reverse stress | The smallest operating and financing change that breaks the thesis | — | — | — | new | NOW (solve the engine for the EBITDA decline and the spread at which `G_h < 0`) |
| R59 | A coverage threshold is a warning unless a verified contract test | M4.6 | F8 bands | — | same | — |
| R60, R61 | MECE states with a default state; without it returns are conditional on survival; probabilities are judgement | M5.2 fitted logistic weights; M5.4 Bayes path mass | F6 weight table; F6.10 | Step 7 `p_path` | conflict C10 | — |

## 6. Step 5: valuation (PDF Section 7)

| ID | PDF item | Methodology | Framework | process.py | Status | Data now |
| --- | --- | --- | --- | --- | --- | --- |
| P13 | Four methods: comparables, precedents, DCF, liquidation | M6.1 | F7 method by archetype | Step 8 market TEV only | same in design | — |
| R62 | A forecast and a multiple from the same forecast are not independent | — | — | — | new | — |
| R63 | Do not average methods mechanically | M6.1 lognormal from the field width | F7.6 `V_mid` = weighted mean | — | conflict C11 | — |
| Quoted-equity identity | EV = debt − cash + market cap | M6.1 "observable TEV" | F7.7 market check | Step 8 `market_tev` | same | — |
| E40 to E44, R65, R66 | UFCF, WACC, DCF, discounted terminal value, stable-state condition | M6.1 DCF row | F7.4 | — | more | NOW for UFCF (CS); discount rate JUDG |
| E45, R67, R68 | Value available to the waterfall; add accessible cash once; deduct priority once | M6.1 default value; M6.2 | F5 waterfall steps 2 to 5 | — | same | DOC and JUDG |
| R69 | Equity cushion is an EV sensitivity, not a cash reserve | — | — | Step 8 `debt_to_market_tev` | more | NOW |
| VCC case | Liquidation covers only 51–62%; the regime must be explicit | M6.2 "VCC: 67% at mid, 87% at low, still covered" | F7.8 case choice | — | conflict C11 | — |

## 7. Step 6: documents (PDF Section 8)

| ID | PDF item | Methodology | Framework | process.py | Status | Data now |
| --- | --- | --- | --- | --- | --- | --- |
| P14, P15 | Read documents; map obligors, guarantors, liens, priority, baskets, votes; Gatto's twelve review items | M3.4 document fields | F5 entity map; F7 LME score | Steps 3, 5 open questions | same | DOC |
| P16, R74 to R76 | Contractual cash-flow engine; one default state for all claims of an issuer | M7.4 "PD cancels"; M9.3 | F5 per-entity waterfall | — | same | DOC |
| E46, R72 | Covenant set with a 15–30% EBITDA cushion; cushion reduces the denominator | M4.6 (4.0x plan gives 4.7x) | F8 `H_t` | — | same | — |
| E47, E48, R73 | Debt capacity; EBITDA fall to limit; breach is an event to analyse | M4.6 `H_t` | F6.2; F11 covenant playbook | — | same | DOC |
| E49 | Floating coupon with floor | M5.4 floating follows policy rate | F6.4 | Engine | more (floor) | DOC for floor and margin; FR forwards NOW |
| R77 | Priming debt brings cash; model its use before the loss | M6.3 | F7 `R_LME` adds priming debt to `S_k` | — | conflict C13 | — |
| R78 | An uncertain right is a scenario, never a silent favourable assumption | — | F5 make-whole "two scenarios" | — | same | — |

## 8. Step 7: recommendation and comparative value (PDF Section 9)

| ID | PDF item | Methodology | Framework | process.py | Status | Data now |
| --- | --- | --- | --- | --- | --- | --- |
| P17, R79, R80 | Feasible action set with exclusions; per-action ledger | M8 force rank; `replaces_position` | F1 R8; F10 state machine | Not in process | more | NOW for bonds in the run and cash; mandate JUDG |
| E50 to E52, R81 to R83 | Common-capital terminal wealth; net return; no double counting of costs; horizon wealth before IRR | M7.5 expected alpha (return per position, no common capital) | F9 G3 | Step 10 | conflict C1, C3 | NOW (TR, UST, FR, scenario engine; recovery JUDG) |
| E53, E54 | Excess over cash; expected excess | M7.5 alpha is hedged excess over market | — | Step 10 | more | NOW (UST for cash) |
| E55 | Annualized wealth return | — | F13 annualised excess | Step 10 annualises bp | same | — |
| E56, E57 | Probability of loss; probability below cash | — | — | — | new | NOW |
| E58, E59, R84, R86 | Expected shortfall; incremental portfolio ES; joint scenarios | M9.4 limits; M10.5 `event_var_alpha` | F10 sizing | — | new | NOW (scenario engine gives joint paths across issuers in one run) |
| E60, R87 | Opportunity cost against the best admissible action; cash and retention stay valid | M8 force rank | F12.2 replaces position | — | new | NOW |
| R85 | Do not collapse to yield/PD, spread/leverage, return/CS01 or Sharpe | Book principles: "expected return per unit of that risk" (p. 119); M7.5 `info_ratio` | F13 headline information ratio | Step 10 | conflict C1 | — |
| P18 | Quarterly cross-sector force-rank plus event reviews at realizable prices | M8 force rank | F12.1 weekly | Not in process | same (repo cadence is finer) | — |
| P19 | Six-part memorandum | — | F12 full memo | `memo.py` | same | — |

## 9. Distressed extension (PDF Section 10)

| ID | PDF item | Methodology | Framework | process.py | Status | Data now |
| --- | --- | --- | --- | --- | --- | --- |
| R89 | A distressed screen is a research trigger | M1 below-universe row | F9 G5 regime switch | — | same | — |
| 10.1, E61, R90, R91 | Claim map; pro rata pool; contractual turnover; coupled multi-entity calculation | M6.2 waterfall per entity | F5 waterfall steps 1 to 7 | Step 5 open question | more (turnover, U11) | DOC |
| U12, U13 | Separate-entity against consolidation recoveries | M6.2 structural position | F5 intercompany row | — | same | DOC |
| R92 | Legal asymmetry trades are not risk-free arbitrage | M8 S4 traps | F10 S4 rules | — | same | — |
| E62, R93, R94, S15 | Plan package value; plan value sets allocation, analyst value sets worth | — | — | — | new | DOC |
| 10.3, R95 to R97 | Resolution time, burn, follow-on capital; credit bids; litigation as a separate asset | M6.2 (no time) | F5 DIP from burn | — | more | JUDG and DOC |
| 10.4, U17, R98 | LME uptier recovery 24.85% to 49.90%; credit retained new cash | M6.3 cites 24.8% to 49.9% | F7 LME score and `R_LME` | — | same numbers; conflict C13 on cash | DOC |
| R99 | CDS event, deliverable and auction basis | M3.1 `cds_5y` basis gap | — | — | more | NONE (no CDS data) |
| P20, U18, R100 | Liquidation sequence; joint stress of assets, claims, time | M6.1 liquidation rates | F7.5; F5 rejection sets | — | same | DOC |
| U19, R101 | Vendor put liquidity need | — | — | — | new | DOC |
| U20, R102, R103 | Senior-long junior-short insurance; not a zero-capital return; short not capped at 100 | M8 S4 "secured against unsecured in a frothy market" | F10 S4 | — | more | NOW (TR for two ranks where both trade) |
| U21 to U23, R104 to R106 | JCP trades: covenant catalyst; turnaround payoff; equity short | M8 S5 (documents) | F11 call and tender | — | more | DOC (indenture) |

## 10. Bank module (PDF Section 12)

| ID | PDF item | Methodology | Framework | process.py | Status | Data now |
| --- | --- | --- | --- | --- | --- | --- |
| E85 to E104, U36, U37, R123 to R135, S6 | CAMEL; ROE split; IGRC; NPL ratios; loss coverage; dead bank ratio; blended recovery; liquidity and funding; gaps; CET1, LCR, NSFR, HHI, encumbrance; linked stress ledger | — | F2 A8 "Out of scope. Route to a separate rulebook." | Not in process | new (fills the A8 gap) | NONE (no bank call reports or Pillar 3 in the repo) |

## 11. The security (PDF Section 13)

| ID | PDF item | Methodology | Framework | process.py | Status | Data now |
| --- | --- | --- | --- | --- | --- | --- |
| E105, E106 | Total and through leverage | M4.3 `Lev^face_k` | F5 `lev_gc_k` | Step 5 total only | same | DOC for rank face |
| E107, R136 | Spread per turn screen and its trap (DataFone) | M7.4 SPT between tranches (HCA) | F12 memo section 9 | — | more (the PDF adds the trap and cash-flow pairing) | NOW for total-leverage version (TR, CS) |
| R137 | Legal claim map before metrics | M6.2 | F5.1 | — | same | DOC |
| E108, R138 | Single-pool waterfall; add cash once; priming cash | M6.2 `Pay_k(V)` | F5 step 5 | — | same | — |
| E109, U38, U39, R139 | Discounted scenario recovery value; return on purchase price; delayed IRR | M6.4 `recovery_price_k = 100 × recovery_k_adj` | F9 implied recovery | — | conflict C12 | NOW (TR price; recovery, delay and rate JUDG) |
| E110, R140 | Cushion on debt and on value | M4.3 LTV | F8 `ltv_k_mid` | Step 8 `debt_to_market_tev` | more | NOW (FQ, CS) |
| E111, E112, R141, R142 | PIK accretion; blended retirement price; first call is an issuer option; YTW is not a worst outcome | M3.1 PIK; M9.1 call row | F4.5 toggle; F11 call row | — | more | DOC (call schedules) |
| P21, E113, R143 | Event pro forma with completion and failure branches | M9.2 `ΔP_i(o,m)` by re-evaluation | F11 playbooks | Step 12 lists dates only | same | DOC |

## 12. Default models (PDF Section 14)

| ID | PDF item | Methodology | Framework | process.py | Status | Data now |
| --- | --- | --- | --- | --- | --- | --- |
| E114, R144 | Define the 12-month default label; mature labels only; calls are not defaults | M7.1 `PD^12m` (label not defined) | F13 PD calibration | Step 7 `pd_12m` (v0 rule) | more | NONE (no default labels) |
| E115 to E117, R145, R146 | Modular logit; correct inverse-logit; regularized public-feature baseline | M7.1 logit on forward features | — | — | same | NONE for fitting |
| E118 to E120, R147, R148 | Intercept shift; numerical solve to a target default rate; past-only calibration sample | M7.1 calibrate to agency table by rating | F13 PD calibration | — | same idea; PDF more detailed | NOW for E120 with a fixed target table (Gatto p. 274); fitted η NONE |
| E121, R149 | Case-control prior correction | — | — | — | new | NONE |
| E122, R150, R151 | Satellite default-rate model; do not count the same macro shock in financials and PD | M5.2 macro logistic of EBITDA decline; M5.4 paths | F6.10 | Step 7 | more (different target: PD level against scenario weight) | NOW for macro series (FR); default rate NONE |
| R166 | One-year PD does not give a five-year term structure | M7.5 `PD_h = 1 − (1 − PD_12m)^h`; M7.6 `pd_5y` | — | Step 10 | conflict C4 | — |
| E123, P22, R152, R153 | Expert overlay on the logit scale; override record; test overrides on their own outcomes | — | F1 analyst supplies adjustments; F13.7 defect log | — | new | JUDG |
| E124, R154 | Stacked ML on out-of-fold predictions | — | — | — | new | NONE |
| E125, U40, R155, R156 | SHAP with baseline; aligned logit disagreement as a review flag | — | — | — | new | NONE |

## 13. Forward information (PDF Section 15)

| ID | PDF item | Methodology | Framework | process.py | Status | Data now |
| --- | --- | --- | --- | --- | --- | --- |
| E126, P23, R157, R158, S11 | News means and maxima; structured event record; LLM vintage contamination | M3.7 event calendar | F11 | Step 12 | new | NONE (news); NOW for event records from 8-K item codes in the EDGAR index |
| E127 to E132, R159 | Social and governance scores | — | — | — | new | NONE |
| U41, E133, U42, R160 | Physical-risk exposure and cash ledger | — | — | — | new | NONE |
| E134, R161 | EU allowance cost | — | — | — | new | NONE (US universe) |
| R162 | Cyber: no credit mapping exists | — | — | — | new | — |
| R163 | Seven-part admission rule for any new feature | — | F13.6 change control | — | more | — |

## 14. Fair bond value (PDF Section 16)

| ID | PDF item | Methodology | Framework | process.py | Status | Data now |
| --- | --- | --- | --- | --- | --- | --- |
| E135, R164 | Full scenario repricing; default inside cash flows, so EL is not subtracted again | M7.5 component sum minus `PD_h × LGD` | F9 G3 | Step 10 | conflict C3 | NOW |
| E136, R165 | EL = PD × LGD × EAD is not a spread model; do not map PD to OAS by × LGD or OAS to PD by ÷ LGD | M7.1 `s_anchor = κ λ LGD` | F8 and F9 `implied_lambda`, `implied_pd_12m` | Step 11 `implied_pd = 1 − exp(−s5/(κ·lgd))` | conflict C2 | — |
| U43 | Physical survival from hazards | M7.1 `λ = −log(1 − PD)` | — | — | same | — |
| R167 | One OAS convention; archive analytics version; full repricing for premium callables | M11 known gaps: OAS from a lattice | — | Step 9 uses G-spread (TRACE yield − UST) | more | DOC (call schedules) for OAS; G-spread NOW |
| E137, R168 | Fair spread from independent features; bank and nonfinancial apart; test whether PD adds | M7.2 two-stage log model | F2.2 monotone constraints by archetype | Step 9 one-variable line on lease-adjusted leverage, eight issuers | same in design; process minimal | NOW (CS, TR) |
| E138, R169 | Residual; never rebuild OAS from the bond's own price | M7.2 Term block includes `log price` | — | Step 9 | conflict C14 | — |
| U44, R170, R171, S2 | Issuer weights; leave-one-out issuer curve; shrink sparse curves | M7.2 per-bond cross-section | — | Step 9 fits each issuer curve on all its bonds | more | NOW (TR) |
| E139, U45, R172, R173 | Risk-neutral price skeleton; price residual for deep discounts; recovery-haircut robustness | M7.5 regime below 80 | F9 G5 | — | new | NOW (TR, UST; recovery JUDG) |
| E140, R174 | Z = e/u with a documented error scale; not a normal z | M7.3 `z = ε/σ̂(x)` with Mondrian conformal band | F9 G1 | Step 11 uses cross-sectional residual sd | same; process minimal | NOW |
| E141, R175 | Convergence return and cost hurdle e_cost | M7.5 `D^s (1 − ρ^h) m` | F9 G3 net of bid-ask | Step 10 `passes_cost_test` | more | NOW (TR; q JUDG or AR(1)) |

## 15. Signals (PDF Section 17)

| PDF signal | Methodology | Framework | process.py | Status | Data now |
| --- | --- | --- | --- | --- | --- |
| S1 peer value | M8 S1 | F10 S1 | Steps 9, 11 | same | — |
| S2 issuer-curve value (U46) | — | — | Step 9 fits curves but reports no leave-one-out residual | new | NOW (TR) |
| S3 credit improvement not in price (E142) | M8 S2 fundamental momentum | F10 S2 | — | same | NOW |
| S4 refinancing burden | M5.4; M9.1 maturity row | F10 S9 refinance wall | Step 7 | same idea; PDF adds ΔI/E and min G_h | NOW |
| S5 cash-quality discrepancy | M4.1 `addback_gap`, `covenant_gap` | F3 EQ7, EQ9 | Step 3 EQ7 | more | NOW for conversion; DOC for covenant EBITDA |
| S6 bank divergence | — | F2 A8 out of scope | — | new | NONE |
| S7 capital-structure RV (E143) | M8 S4 | F10 S4 | — | same | NOW where two ranks trade in TR |
| S8 call and extension value (U47) | M9.1 call row | F9 `implied_p_event`; F11 call row | — | more | DOC (call schedule) |
| S9 event pro forma | M9 | F11 | Step 12 | same | DOC |
| S10 model disagreement | — | — | — | new | NONE |
| S11 text | — | — | — | new | NONE |
| S12 technical dislocation (E144) | M8 S6 forced flows | F11 index rebalance | — | new | NOW (TR spread history; FR TRACE HY level) |
| S12b Gatto spread retracement (U48) | — | — | — | new | NOW (TR) |
| S13 stress-resilient RV (U49) | M9.4 limits | F10 sizing | — | new | NOW (scenario engine) |
| S14 forward-demand divergence | M4.1 `book_to_bill` | F3 EQ3, EQ4 | — | more | NOW+tag (RPO proxy, allowance tag) |
| S15 plan allocation | — | — | — | new | DOC |
| R176, R177, P24 | Signals generate candidates; no z-score averaging; ablation; full entry record | M8 composite of standardised signals weighted by IC | F10 composite; F10.1 to F10.6 | — | conflict C15 | — |
| R178 | No universal cutoffs from the books | — | F1 R9 thresholds are defaults | — | same | — |

## 16. Portfolio, hedging, execution (PDF Section 18)

| ID | PDF item | Methodology | Framework | process.py | Status | Data now |
| --- | --- | --- | --- | --- | --- | --- |
| E145, R179 | Spread duration and CS01 | M9.3 `sdv01` | F8 `sdv01_per_mm` | Step 7 uses modified duration as spread duration | same | NOW |
| E146, R180 | CS01-matched pair ratio; not neutral to rates, beta, JTD | M9.3 pair sizing by JTD | F10 S4 "size by jump-to-default" | `rv_pair.py` pair reports | more (both ratios should print) | NOW (TR) |
| E147 | DTS | — | — | — | new | NOW (TR) |
| E148 | Hypothetical pair arithmetic | — | — | — | example | — |
| E149, R181 | JTD = N (P_d/100 − R); stress both legs together | M9.3 `jtd` (same form) | F8 `jtd_per_mm` | Not in process | same; process lacks it | NOW (TR; R JUDG) |
| R182 | Several sizing limits | M9.4 | F10 sizing formula | — | same | — |
| E150, R183, R184 | Mean-variance objective with explicit cash and costs; ranking with limits first | M8 composite; M9.4 | F10.3 to F10.5 | — | new (objective); same (limits first) | NOW for Σ from TR; γ JUDG |
| R185 | Cost model at size; transaction prices are not quotes; implementation shortfall | M9.3 exit cost `bid_ask_bp × sdv01` | F10.4 ADV cap | Step 10 cost | more | NOW for a TRACE cost proxy; quotes NONE |
| R186 | Exit rules at entry; P&L attribution sums to actual | M9.5 | F9 G8; F10 state machine; F13 | — | same | — |

## 17. Evidence, cases, validation (PDF Sections 19 to 22)

| ID | PDF item | Methodology | Framework | process.py | Status | Data now |
| --- | --- | --- | --- | --- | --- | --- |
| Section 19 | Study results with limits; none is an HY RV backtest | M11 known gaps | F13 | — | new (evidence base) | — |
| Cases A, E | Leverage unchanged, FCF halves after refinancing | M5.4 refinance cost | F6.3 | — | supports Top 10 items 3 and 4 | — |
| Case B | Spread-per-turn trap | M7.4 | — | — | more | — |
| Cases C, F | Recovery delay and purchase price | M6.4 | F9 G5 | — | conflict C12 | — |
| Case G | Better PD with less RV; cost hurdle | M7.3, M7.5 | F9 G3 | Step 10 | more | — |
| Case H | Call defeats a higher coupon | M9.1 call row | F11 | — | more | DOC |
| Case I | Step 7 comparison with ES budget | M7.5, M8 | F9 | — | conflict C1 | — |
| Case L (HCA) | Index and peer table; 100% FCF sweep is a policy assumption | M7.4 HCA table; M11 HCA postmortem | F12 memo section 9 | Step 9 open question "no rating-index source" | more | NOW for an HY-wide benchmark by maturity bucket (`trace_bonds.benchmark_by_bucket`, `rv.benchmark_excess` exist; step 9 does not call them). BB, B and sector indices NONE (TRACE `grade` is only IG or HY) |
| 21.1 | Three validation layers with blocking failures | M11 layer table | F13 | `hy/backtest.py`, `scripts/backtest_alpha.py` | same | — |
| E168 to E170, U53, U54, R187 | Brier, log loss, O/E, AUC, calibration regression; dependence-aware intervals | M11 PD row | F13 PD calibration | — | same | NONE (labels) |
| P25 | Nine-step chronological protocol: frozen choice sets, matured labels, upstream scores out of fold, purge and embargo, keep failed claims, executable simulation, regimes | M11 backtest design | F13.1 frozen `available_at` | `hy/backtest.py` | more | NOW for TRACE-based return tests |
| E171, E172, U55, R188 | Realized dirty returns with face changes; drawdown; no overlapping Sharpe annualization | M11 backtest | F13 outcome score | — | more | NOW (TR) |
| R189 | Baselines include cash and retention; ex-ante best alternative only; ablations | M11 benchmarks: index and rating-matched index | F13 | — | more | NOW |
| E173, R190 | Rating transition matrix; PD percentile monitoring; remedies | M11 | F13.8 | — | new | NONE (no rating history; TRACE `grade` is IG or HY only) |
| P26 | Dated journal of trades and rejected alternatives; six-month postmortems | M11 HCA template | F10 step 7; F12 postmortem fields | — | same | — |
| Section 22 | Source discrepancies corrected (TV discount, VCC net debt, Kricheff p. 53) | M12 appendix | — | — | more | — |

## 18. Repo items with no PDF counterpart

| Repo item | Note |
| --- | --- |
| M4.7 two clocks; process step 6 | The PDF has no duration-mismatch measure. Its closest rule is R53 (forecast to the next contractual change) and E75 (dated obligations). Keep it; it is an extension. |
| M7.3 conformal band; M7.5 AR(1) half-life | The PDF asks for a documented error scale (R174) and an estimated q (R175). Conformal and AR(1) are valid ways to supply them. |
| M9.2 growth and policy split of Treasury moves | The PDF has no macro-rate split. Keep it. |
| F5 bankruptcy-code claim sizing | The PDF says legal descriptions are not a universal calculation (R100). F5 is more detailed than the PDF. |
| F7 LME point score | The PDF treats LME by document capacity and scenarios, not by a score. No conflict except C13. |

---

## (i) Top 10 additions to `process.py` that are computable now

Ranked by value to the mission (find mispriced bonds; give positional risk). Each runs on data the repo already loads. Where a value needs judgement, a v0 default with a decision page stands in (framework R9).

**1. Step 7 alternatives comparison against cash (E50 to E58, E60). New step "10b Alternatives".**
- Formulas, per bond a in the run plus cash, per macro path m and default state d ∈ {survive, default}:
  - q_{m,d} = p(m) × (1 − PD_H(m)) or p(m) × PD_H(m).
  - V_{H,m,survive} = price at H of the remaining coupons and principal, discounted at the Treasury forward par yield for the remaining tenor plus s_fair(m).
  - V_{H,m,default} = R / (1 + k)^τ per 100, with no further coupons.
  - W = V_H + B_0 A + Σ CF_u A − TC_H; R^net = W/K − 1; X = R^net − R^cash; µ = Σ q X; π_loss = Σ q 1{R^net < 0}; π_cash = Σ q 1{X < 0}; ES_95 from E58 with L = −R^net.
  - OC_a = max_{admissible j} µ_j − µ_a, where admissible means ES_95 ≤ budget.
- Inputs: TRACE clean price, coupon, maturity (accrued from the coupon schedule); UST par curve for R^cash at H; FR Treasury forwards for V_H; `p_path`, `pd_12m`, `s_fair(m)` from step 7; R, τ, k, ES budget, TC (JUDG, v0).
- Output: µ, π_loss, π_cash, ES, OC and the best admissible alternative. It fills a candidate for `replaces_position` (F1 R8).

**2. Price-based default loss and discounted recovery in alpha and the gate (E149, E109, U38, U39). Changes steps 10 and 11.**
- Formulas: R_PV = R / (1 + k)^τ. Default loss in return units L_def = (P_d/100 − R_PV) / (P_d/100). Replace `PD_h × LGD` in the M7.5 alpha with `PD_h × L_def`. JTD per 1 million face = 1,000,000 × (P_d/100 − R).
- Inputs: TRACE price; v0 recovery R = 1 − `scenarios.V0["lgd"]`; τ = 1 year, k = 15% (JUDG, decision page).
- Why: it resolves C3 and C12. A bond at 70 and a bond at 100 lose different amounts in the same default.

**3. Funding gap and first failure date (E75, E76). Extends step 4.**
- Formulas: G_h = C_0 + A_drawable − C_min + Σ_{u≤h} FCF_u − M_h − U_h; FundingNeed_h = max(0, −G_h); MaturityShare_h = M_h / D_0. Report min_h G_h per path and the first quarter with G_h < 0.
- Inputs: C_0 = CS `cheq`; A_drawable = XB revolver capacity minus draw where tagged, else 0 with a flag; C_min = one month of cash operating cost = (`cogsq` + `xsgaq`) / 3 (F4.4 default); FCF_u = per-quarter FCF from the scenario engine (non-overlapping); M_h = XB maturity ladder spread to quarters (10-Q rule of M4.7); U_h = 0 unless known; D_0 = `dlcq` + `dlttq`.

**4. Refinancing interest shock and its effect (E77; Cases A and E; signal S4). Extends steps 4 and 7.**
- Formulas: ΔI = Σ_k D_refi,k (c_new,k − c_old,k). Report ΔI / E; cash coverage after refinancing E / (I_c + ΔI); after-capex coverage (E − K) / (I_c + ΔI); FCF − ΔI; (FCF − ΔI) / D.
- Inputs: D_refi = XB ladder amounts due within 24 months; c_old = TRACE coupon of bonds that mature in that window, else LTM `xintq` / average debt (ROD); c_new = FR Treasury forward par yield at the maturity date for a 5-year tenor plus the issuer's current TRACE curve spread at 5 years; E = LTM `oibdpq`; I_c = LTM `intpnq`; K = LTM `capxq`.

**5. Kricheff cash bridge and coverage family (E63 to E70, E72). Extends steps 3 and 5.**
- Formulas: E = LTM `oibdpq`; FCF = E − I_c − T_c − K − W − O; gross leverage D/E; net leverage (D − C)/E; cash coverage E/I_c; total coverage E/I_total; after-capex coverage (E − K)/I_c; FCF/D; cash conversion CFO/E.
- Inputs (all CS, LTM): `oibdpq`, `intpnq` (I_c), `xintq` (I_total), `txpdq` (T_c), `capxq` (K), W = Δ over four quarters of (`rectq` + `invtq` − `apq`), `oancfq` (CFO; under US GAAP it already includes interest and taxes paid), D = `dlcq` + `dlttq`, C = `cheq`. O = 0 with a flag. Analyst add-backs stay JUDG; print the unadjusted version first.

**6. Error-scaled residual and convergence cost hurdle (E140, E141). Extends steps 9 and 10.**
- Formulas: e = s − ŝ (bp); Z = e / u; R_conv = D_s q e × 10^−4; e_cost = c / (D_s q) × 10^4. Pass only if e > e_cost and Z > the conformal threshold.
- Inputs: s and ŝ from step 9; u = leave-one-issuer-out residual standard deviation of the run (later: past out-of-time residuals by cell); D_s from TR (item 8); q = 1 − ρ^{4H} from an AR(1) on the issuer's residual history when at least eight observations exist, else 0.5 (JUDG); c = round-trip cost from TRACE (twice the median absolute gap between trade prices and the daily volume-weighted price over the last 20 days).

**7. Leave-one-out issuer-curve residual (S2, U46, R171). Extends step 9.**
- Formula: for each bond b of issuer i with at least three bonds of the same seniority, fit the issuer curve (`rv.curve_fit`) on the other bonds and compute e^curve_b = s_b − ŝ_{i,−b}(tenor_b).
- Inputs: TRACE G-spread, maturity, seniority, 144A and convertible flags (drop convertibles).
- Output: within-issuer switch candidates. Issuer PD cancels, so this needs no cross-issuer model.

**8. Spread duration, CS01, DTS and pair ratios (E145 to E147). New fields in step 5 and in `rv_pair.py`.**
- Formulas: D_s = −(1/P_d) ∂P_d/∂s by a 1 bp bump and reprice; CS01 = MV_d D_s 10^−4; DTS = D_s s; CS01-matched short N_S = N_L (P_{d,L} D_{s,L}) / (P_{d,S} D_{s,S}); JTD-matched ratio from M9.3 beside it.
- Inputs: TR price, coupon, maturity, yield; UST curve for the bump base.

**9. Abnormal spread shock and spread retracement (E144, U48; signal S12). New screen in step 12.**
- Formulas: Shock_{b,t} = Δs_{b,t} − β̂_{b,t−1} Δs_{HY,t}, with β̂ from a regression of 5-day spread changes on the HY level over the prior 120 trading days. SpreadRetracement_t = (s_peak − s_t) / (s_peak − s_pre), with the peak and the pre-shock level taken only from dates on or before t.
- Inputs: TRACE spread history per bond (`rv_pair.HISTORY_DAYS`); FR TRACE HY level (`trace_bonds.hy_benchmark`); shock threshold JUDG (for example 2 residual standard deviations).
- Use: a candidate for underwriting, not a buy signal (PDF R178 and the Gatto Macy's note).

**10. Working-capital days, the derived-feature template, and an RPO demand proxy (E73, E74, E5 to E9, E16 to E18). Extends steps 3 and 2.**
- Formulas: DSO = 365 × average receivables / TTM sales; DIO = 365 × average inventory / TTM COGS; DPO = 365 × average payables / TTM COGS; CCC = DSO + DIO − DPO. For each metric x: Δ4 x; x − peer median; Δ4 x − peer median Δ4 x; Age = t − release time. For RPO filers: implied orders_u = RPO_u − RPO_{u−1} + revenue_u; book-to-bill = orders / revenue; demand gap = g_orders − g_revenue.
- Inputs: CS `rectq`, `invtq`, `apq`, `saleq`, `cogsq`; Compustat PIT release dates; peers = run issuers with the same archetype (JUDG list); XB `RevenueRemainingPerformanceObligation` (already loaded for the clocks).
- Caveat: implied orders is a proxy. Revenue from contracts outside RPO enters the bridge. Label it as a proxy.

Also computable now but ranked lower: lease leverage on the liability method (E33, one XBRL tag; resolves C6); spread against the TRACE HY benchmark of the same maturity bucket through `trace_bonds.benchmark_by_bucket` (Case L; rating-bucket indices still need a source); realized TRACE returns E171 and E172 for the backtest.

---

## (ii) Conflicts and recommended resolutions

Each entry follows CLAUDE.md: record both, state when each is right, choose one, say why, and name the test that settles it.

**C1. What decides the trade.**
- PDF: a residual, score or yield is an input. The decision is the common-capital terminal-wealth comparison against all feasible alternatives, including cash and retention (Section 9, E50 to E60, R85, R88, R176). Do not reduce it to return per unit of risk or a Sharpe ratio.
- Repo: M1 says "The gap is the mispricing" and ranks bonds by it. M8 force-ranks by a composite. The book-principles list says "Relative value compares expected return per unit of that risk." F13 uses an information ratio as a headline number.
- When each is right: the residual rank is right for candidate generation and for a cross-sectional signal test (CLAUDE.md DoD: rank IC per cycle). The PDF is right for the allocation decision, because a residual says nothing about capital use, tail loss or the cash alternative (Case I: the highest-µ bond fails the ES budget).
- Choose: keep M8 for candidates and IC tests. Make the Step 7 comparison (Top 10, item 1) the final decision and the source of `replaces_position`.
- Test: in the backtest, compare decile returns of the composite against returns of the µ-ranked admissible set, net of cost, in each of the four cycles.

**C2. Spread and PD translation.**
- PDF R165: do not get OAS from PD × LGD and do not get PD from OAS ÷ LGD.
- Repo: M7.1 anchor `s_anchor = κ_t λ LGD`. F8 and F9 `implied_lambda = oas/(κ_t × lgd)`, `implied_pd_12m`. Step 11 computes `implied_pd = 1 − exp(−s5/(κ·lgd))` and compares it with the physical `pd_12m` in G1.
- When each is right: the repo is right when κ_t is estimated by rating bucket and date, because κ then absorbs the risk premium; the anchor is then only an offset for the second stage. The PDF is right that a spread-implied PD is not a physical PD. Step 11 uses a fixed `V0["kappa"]`, so its "market-implied PD" is not comparable with a physical PD.
- Choose: keep the anchor as a model offset. Rename the F9 row "PD at the current price of risk" and stop treating it as a physical PD in G1 until κ_t is fitted by bucket and date.
- Test: regress realized 12-month default frequency by rating bucket on spread-implied PD and on model PD. Keep the implied-PD row in G1 only if its slope is near 1.

**C3. Expected alpha construction.**
- PDF E135, R164: full scenario repricing; default and recovery inside the cash flows; expected loss not subtracted again; losses on purchase price.
- Repo M7.5: α = Σ p(m)[carry + convergence − PD_h LGD] + E[event] − c, with LGD on face.
- When each is right: the repo sum is a good small-move approximation for a performing bond near par with no call. The PDF is right for premium callables, discounted bonds, large moves and default, where the pieces overlap or LGD on face misstates the loss.
- Choose: keep the M7.5 sum as a diagnostic decomposition. Use full repricing (Top 10, item 1) for the number that enters the gate. In the sum, replace LGD with the price-based loss L_def (Top 10, item 2).
- Test: on TRACE history, compare predicted and realized horizon returns (E171) for both methods by price bucket (below 90, 90 to 103, above 103).

**C4. PD term structure.**
- PDF R166: a one-year PD does not identify a five-year curve without an explicit migration or hazard assumption.
- Repo: M7.5 `PD_h = 1 − (1 − PD_12m)^h` (constant hazard); M7.6 `pd_5y`.
- When each is right: constant hazard is right for horizons of one year or less, which covers the 1 to 6 month signal horizon. It is wrong at five years: the agency table in M4.5 gives 3.60% at one year, and constant hazard gives 1 − 0.964^5 = 16.8% against the actual 14.16%.
- Choose: keep constant hazard for h ≤ 1 year. For `pd_5y`, use the agency cumulative curve by rating, scaled by the issuer's one-year ratio, and label the assumption.
- Test: the 16.8% against 14.16% gap above. Repeat by rating bucket.

**C5. Creation leverage of a layer.**
- PDF E31: senior claims at face; every claim in the target layer at its own market price (MGEC: 45,000 at 0.79 and 2,000 at 0.795).
- Repo M4.3: `Lev^mkt_k` adds only tranche k at market; other same-rank claims drop out.
- When each is right: they agree when tranche k is the only claim at its rank. With several pari passu bonds, M4.3 understates the debt that a buyer of the layer must finance.
- Choose: the PDF formula. It is Gatto's and it is correct for multi-bond layers.
- Test: recompute MGEC; M4.3 gives a lower value than 4.27x.

**C6. Lease-adjusted leverage.**
- PDF E33, R50: prefer the reported operating-lease liability when the two methods diverge.
- Repo: M4.3 and `process.py` step 5 use 8 × rent (`hy/rv.py` default). F5 already says liability after 2018, 8x for older periods.
- When each is right: 8x is right before ASC 842 (fiscal 2019) and for comparison with old rating-agency data. The liability is right after 2018, because it reflects the remaining term.
- Choose: F5 and the PDF. Change M4.3 and step 5 to use the XBRL liability after 2018. Print both values.
- Test: report the gap between the two by archetype. Where the gap exceeds 0.5x, check which one tracks the fair-spread residual better out of sample.

**C7. Pension adjustment.**
- PDF E35: add underfunding to debt and add pension expense less service cost back to EBITDA.
- Repo: M4.3 and F5 `debt_adj` add the deficit to debt only.
- When each is right: the repo is right only when pension expense was not deducted in EBITDA. Otherwise it penalizes twice.
- Choose: the PDF form, with the reconciliation guard in R51. Keep F5's termination-liability rule for the claims view (a different question).
- Test: on issuers with pension tags, compare leverage under both forms. Flag issuers where the difference exceeds 0.25x.

**C8. Debt recursion.**
- PDF E38, E39, R114, Case L: cash and face debt run as separate recursions; mandatory amortization and the contractual sweep reduce debt; surplus cash accumulates; a 100% sweep is "a management-policy assumption to stress."
- Repo M5.1: `D_h = D_{h−1} − FCF_h + Draw_h`, so all FCF repays debt.
- When each is right: the repo is right for a loan with a 100% excess-cash sweep or a firm with a stated deleveraging policy. For HY bonds, which have no sweep, the PDF is right.
- Choose: the PDF. Debt falls only by scheduled maturities, sweeps and stated policy. Run full deleveraging as a separate case.
- Test: compare forecast and realized net debt four quarters ahead on Compustat for the run issuers under both rules.

**C9. Shortfall order.**
- PDF P11 (Gatto): a shortfall first uses cash above the operating minimum, then draws the revolver.
- Repo F6.1: draw the revolver first, then let cash fall to the minimum.
- When each is right: the F6.1 order is right when cash is trapped (abroad, at a non-guarantor, or restricted; R19). Otherwise Gatto's order is right and costs less interest.
- Choose: Gatto's order, with the F4.1 accessible-cash haircut applied first. Both give the same first-shortfall date when no cash is trapped; they differ in interest cost and drawn balance.
- Test: run both on the eight `process.py` issuers. Report the difference in `liq_min_down` and in the first refinance date.

**C10. Scenario probabilities.**
- PDF R60, R61: states must be mutually exclusive and exhaustive and must include default, or the return is conditional on survival. Named stresses do not establish the tail. Probabilities are judgement, debated in committee.
- Repo M5.2 and M5.4: weights from a fitted logistic and from Bayes on forecast quantile mass, treated as probabilities. Default enters only through `pd_12m` in alpha.
- When each is right: the repo is right that weights should move with observable macro data (R35 agrees). The PDF is right that the case set without a default state is not a full distribution.
- Choose: keep the macro weights. Add an explicit default and resolution state per path with probability PD_H(m). Label outputs "conditional on the case set" until the M11 reliability test of `w_down` passes.
- Test: M11 reliability of `w_down(m)` in its binomial band.

**C11. Valuation aggregation and regime.**
- PDF R63 and the VCC case: do not average methods mechanically; going concern can cover a loan while liquidation covers only 51–62%; state the regime.
- Repo: F7.6 sets `V_mid` as a weighted mean across methods. M6.2 says "VCC: 67% at mid, 87% at low, still covered (p. 332)" without the liquidation result.
- When each is right: a weighted mean is acceptable across the going-concern methods that share one earnings basis. It is wrong across regimes (going concern against liquidation).
- Choose: average only within the going-concern regime. Keep liquidation as a separate value. Add the VCC liquidation coverage to M6.2 beside the going-concern LTV.
- Test: on the F5 waterfall, compare recovery under the mean value against recovery under the F7.8 chosen regime for resolved cases (needs labels; DOC).

**C12. Recovery timing and price.**
- PDF E109, E151, R95: recovery arrives after a delay; P_0 = R / (1 + k)^τ (50 → 34.72 at 20% over two years).
- Repo: M6.4 `recovery_price_k = 100 × recovery_k_adj`; M9.1 "Price converges to recovery"; M9.3 JTD floor uses it undiscounted.
- When each is right: undiscounted recovery is right for claim coverage and for the final distribution amount. The discounted value is right for a price after default and for JTD in P&L.
- Choose: keep `recovery_k` undiscounted for the claims view. Add `recovery_pv_k` with τ and k (JUDG, decision page) and use it for JTD and the default state in Top 10 item 1.
- Test: compare `recovery_pv_k` with TRACE prices 30 days after default events (needs default labels).

**C13. LME and new-money cash.**
- PDF R98, R138, U17: credit any new cash still in the pool; subtracting the new senior claim while ignoring retained proceeds overstates impairment.
- Repo F7: `R_LME` adds priming debt equal to new-money capacity plus the exchanged majority to `S_k`, and adds no cash to V.
- When each is right: F7 is right in a severe downside where the new money funds burn before resolution. The PDF is right when the money stays in the estate.
- Choose: add retained new money to V by default. Assume it is consumed only in the severe downside path, and state that choice.
- Test: recompute the PU Corp uptier with 200 retained: excluded creditors recover more than 24.85% to 49.90%.

**C14. Fair-spread inputs.**
- PDF R169, R170, R171: do not feed the bond's own price or yield into the fair model; use issuer weights; leave the bond out of its own curve.
- Repo M7.2: the Term block includes `log price` (and `spread_duration`, which a price also drives).
- When each is right: `log price` is a valid regime flag (below 80, M1) if it is lagged and coarse. A current, continuous price lets the model rebuild the spread through an identity and shrinks the residual.
- Choose: replace `log price` with a lagged regime indicator (price below 80 at t − 20 days). Weight observations by 1 / number of bonds of the issuer.
- Test: refit with and without `log price`. If the residual variance drops but the residual's rank IC for later returns falls, the feature was leaking.

**C15. Signal composite.**
- PDF R177: do not average z-scores with opposite meanings and call the sum validated; use ablation.
- Repo M8 and F10: standardise each signal and weight by trailing IC per phase.
- When each is right: IC weights are a validation-based combination, so the repo is right if each signal's sign and IC are stable. The PDF is right that an IC-weighted sum is not proof that each part adds value.
- Choose: keep the IC-weighted composite. Add an ablation report per signal (drop one, re-test). Remove any signal whose removal does not lower net IC.
- Test: the ablation itself, per cycle (CLAUDE.md DoD).

**C16. Qualitative scores.**
- PDF R31, R34: qualitative risk must change the forecast; do not add qualitative scores to quantitative ratios.
- Repo: M4.4 scores eight risks 0, 1, 2 and feeds the vector to the fair spread model; F3 `eq_score` counts flags into PD.
- When each is right: the PDF route is right for underwriting (the risk becomes a downside case, as F2 and F6 already do). The repo vector is defensible as a feature set only if it adds out-of-sample information.
- Choose: the scenario route is primary. Keep the score vector as a candidate feature that must pass the R163 admission rule.
- Test: ablate the vector from M7.2; keep it only if the out-of-sample residual variance falls.

**C17. Organic growth.**
- PDF E20 (Gatto): organic constant-currency growth removes FX and acquisitions and keeps volume and price and mix.
- Repo: M4.1 and F3 EQ4 remove FX, M&A and price.
- When each is right: Gatto's definition is the standard for perimeter-clean growth. The repo's volume-only measure answers a different question ("volume is the part that persists").
- Choose: `organic_growth` follows Gatto. Add a separate `volume_growth` field. Rewrite EQ4 on Gatto's definition.
- Test: none needed for the definition. Record the two fields and check which leads EBITDA changes.

**C18. Quote convention.**
- PDF R16: verify clean, dirty or flat per instrument.
- Repo M3.1: clean in the US, dirty in Europe.
- When each is right: the repo rule is right as a default for US corporate bonds. It fails for flat-traded bonds near default (which M3.1 itself flags) and for some loans.
- Choose: add a per-instrument `quote_convention` field with the M3.1 rule as the default.
- Test: none; a data-definition change.

**C19. Maintenance capex.**
- PDF R48: Gatto rejects equating maintenance capex with depreciation; state the evidence.
- Repo F4.7: if undisclosed, use depreciation as the floor for A4 and A5.
- When each is right: F4.7 is a conservative default when no disclosure exists. Gatto is right that it is not a rule.
- Choose: keep F4.7 as a labelled default (R9) and record the evidence source when one exists (history of capex in low-growth years, guidance).
- Test: compare depreciation with capex in the issuer's lowest-growth year on Compustat.

**C20 (minor). Cycle label.**
- PDF R35: a cycle label is not a mechanical clock or a timing signal.
- Repo F6: a phase vote sets default weights; M8 S7 tilts by phase.
- When each is right: F6 votes on observable series (SLOOS, HY spread, PMI), which is what the PDF asks for. The phase table is a prior that M5.4 updates with forecasts.
- Choose: keep F6. State in F6 that the phase is a prior over observable indicators, not a clock.
- Test: M11 reliability of `w_down`.

Also note one unit issue. M8 S1 quotes Gatto's "22.9% annualised" (pp. 517–518). Gatto annualises by doubling the semiannual rate (PDF Section 2.4). Label it as a bond-equivalent rate, not an effective annual return.
