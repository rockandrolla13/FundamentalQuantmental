# High Yield Analyst Framework

As of 2026-10-21. Source document: https://claude.ai/artifact/NVC3B4V5qaxxAHPMR1LeCz

This framework is the rulebook that the analyst applies to every filing. It expands the *High Yield Bond Mispricing Methodology* with explicit rules, a metrics catalogue, and a signals catalogue. It holds rules only. No issuer figures, names, or answers appear in it.

## F1. Rules of use

The framework runs unmodified on any filing. The analyst, human or model, applies each rule in order and records the result in the memo fields of F12. The methodology says what the system computes; this framework says what judgement the analyst applies before, during, and after that computation.

| Rule | Statement |
| --- | --- |
| R1 Scope | US dollar high yield bonds and leveraged loans of corporate issuers with public or lender financials. Distressed and private credits use the same rules with the claims view of F5 as the primary view. |
| R2 Order | Frame the business (F2) before any ratio is read. Size the claims (F5) before any recovery is computed. Reconcile the thesis with the price (F9) before any trade call is written. |
| R3 Two views | Keep a going-concern view and a claims view for every issuer. Leverage and coverage come from the first. Recovery comes from the second. Never use a number from one view in the other. |
| R4 Source | Every number in a memo cites its source line: the filing, the table, the page. A number without a source is a question, not a fact. |
| R5 Time | Every input carries `as_of` and `available_at`. A memo dated `t` uses nothing with `available_at` after `t`. |
| R6 Claims | A balance-sheet liability is not an allowed claim. Size each claim by the rules in F5. |
| R7 Price | A fundamental view becomes a trade call only after the gate in F9 passes. The memo states which one it is. |
| R8 Rank | No position enters without the name of the position it replaces (methodology, Section 8). |
| R9 Thresholds | Thresholds in this framework are defaults. Each one carries a calibration note. Change a default only with a decision page that cites the test. |
| R10 No figures | No issuer figures, names, or answers appear in this file. Book page references are sources for rules, not for numbers. |

The framework uses the methodology's section numbers when it points to a computation. Section numbers below refer to the *High Yield Bond Mispricing Methodology* unless marked F.

## F2. Business framing

Frame the business before any ratio is read. The frame selects the EBITDA definition, the leverage and coverage formulas, the collateral basis, the claim rules, the downside driver, and the event classes. Write the frame in five lines and assign one archetype and up to two modifiers.

**The five lines.** What the company sells and to whom. How one unit earns money. What it must spend to stand still: maintenance capex and rent. What the market structure is: number of players and price discipline. What breaks it: the single largest risk, in one sentence.

### Archetype decision table

| Archetype | Identify by | EBITDA and coverage | Collateral basis | Claims rule that changes | Downside driver | Event class to add |
| --- | --- | --- | --- | --- | --- | --- |
| A1 Lease-heavy consumer: retail, restaurants, fitness, cinemas | Rent above 8% of sales or operating lease liability above net debt | EBITDAR; fixed charge coverage with rent; lease-adjusted leverage | Inventory and receivables at liquidation rates; owned real estate | Rejected lease claims capped (F5); rejection set from the store footprint in the downside case | Same-store sales and gross margin; working capital peak before the season | Holiday season results; lease decision dates in a filing |
| A2 Health care services: hospitals, physician groups, post-acute | Government payer share above a third of revenue | EBITDA after bad debt expense; labour cost ratio | Owned facilities; receivables net of contractual allowances | Government recoupment claims rank with care | Reimbursement rule changes; bad debt and labour inflation | Annual payment rule releases; policy votes |
| A3 Commodity producers: E&P, metals, coal | Revenue set by a traded price | EBITDA at the strip and at a stress deck; hedge book marked | Reserves at PV-10 or vessel and plant appraisals; borrowing base | Hedge counterparty termination claims; royalty and plugging obligations | Price deck and decline rate; maintenance capex to hold volume | Borrowing base redetermination dates; price shocks |
| A4 Cyclical industrials: autos, building products, chemicals, transport equipment | Volume moves with GDP; high fixed cost share | EBITDA through the cycle; operating leverage measured | Plant and equipment at orderly liquidation; receivables | Warranty and pension claims | Peak-to-trough revenue from the last recession; working capital release on the way down | Order and backlog releases; PMI |
| A5 Asset-heavy contracted: cable, towers, data centres, shipping, airlines | Capex above 15% of sales; long-dated contracts or assets | EBITDA less maintenance capex; contract coverage | Asset appraisals; contract value | Aircraft and vessel financings have their own rejection rules; equipment lease claims are not capped | Contract roll-off and churn; asset value cycle | Contract renewals; asset appraisal dates |
| A6 Software and recurring revenue, sponsor-owned | Recurring share above 70%; capex low; intangibles dominate | Cash EBITDA after capitalised development; ARR and net retention beside it | Little liquidation value; value is the customer base as a going concern | Deferred revenue and customer prepayments rank as claims when service stops | Net retention and bookings; cost cuts that reverse | ARR disclosures; sponsor actions |
| A7 Project-like and single-asset: casinos, power, LNG, holdco structures | One asset or one site; cash trap and distribution tests | Project EBITDA and debt service coverage at the asset; holdco coverage from distributions only | The asset | Structural subordination of holdco claims; ring-fence tests | Asset-specific shock; distribution block | Distribution test dates; licence renewals |
| A8 Financials and specialty finance | No operating EBITDA | Out of scope. Route to a separate rulebook. |  |  |  |  |

### Modifiers

| Modifier | Identify by | What it changes |
| --- | --- | --- |
| M1 Sponsor-owned | Private equity owner | Add sponsor behaviour to the flags; raise the liability management score weight; read the document baskets first |
| M2 Secular decline | Industry volume falls over five years without a cyclical cause | Treat restructuring charges as recurrent; shorten the terminal value; prefer the claims view earlier |
| M3 Concentration | One customer or one product above 20% of revenue | Add a loss-of-contract outcome to every earnings event; size the jump |

### Framing rules

- F2.1 Assign one primary archetype. If two fit, compute both views and report the difference in the memo.
- F2.2 The archetype selects the liquidation rate table, the recession template, the claim rules, and the monotone constraints of the fair spread model (Section 7.2).
- F2.3 Record `archetype`, `modifiers[]`, and the one-line reason in `issuer_state`.
- F2.4 Re-frame on any change of business mix above 20% of revenue, on an acquisition, or on a change of owner.

## F3. Statement normalisation

Build three EBITDA numbers and keep them apart: the analyst number, the company number, and the covenant number. The analyst number follows the add-back rules below. The company number is what the issuer reports as adjusted. The covenant number follows the document definition (Section 4.6). The gaps between them are metrics in their own right (F8).

### Add-back classes

| Class | Item | Analyst EBITDA rule | Covenant EBITDA |
| --- | --- | --- | --- |
| C1 | Non-cash impairments and write-offs | Add back. If the item appears in two or more of the last five years, or the archetype is A1 or the modifier is M2, treat it as recurrent and do not add back (p. 192) | Added back |
| C2 | Cash restructuring: severance, closures | Add back. Do not add back under M2 or when present in three of the last five years | Added back |
| C3 | M&A and divestiture costs | Add back for closed deals. Flag when the three-year sum exceeds 10% of EBITDA | Added back |
| C4 | Gains and losses on asset sales | Remove gains. Add back losses | Removed |
| C5 | Litigation and settlements | Add back a one-off settlement. Treat industry-wide recurrent litigation as an operating cost | Usually added back |
| C6 | Stock compensation | Do not add back. The company pays it in shares or in buybacks | Added back |
| C7 | Sponsor management fees | Add back only when the fee is subordinated and deferrable in distress by the documents | Added back |
| C8 | Projected cost savings and synergies | Never | Added back up to the cap and the sunset in the document (pp. 353–354) |
| C9 | Pro forma for acquisitions | Include closed acquisitions with audited numbers for the full period. Exclude pipeline deals | Often included |
| C10 | Capitalised development and software | Deduct capitalised costs that recur every year, for A6 always | Not deducted |

### History and peers

- F3.1 Use three to five years for a non-cyclical issuer. Use a full cycle with at least one recession for A3 and A4 (p. 191).
- F3.2 Use the last twelve months and the same quarter a year earlier. For A1, read working capital at the seasonal peak.
- F3.3 Build a peer set of at least four issuers of the same archetype on the analyst EBITDA definition. Compare medians. Compare at the EBITDA margin, not the gross margin, because cost allocation between COGS and SG&A differs by company (p. 211).
- F3.4 Record the surprise against consensus and against the analyst base case, both.

### Earnings quality tests

Each test sets one flag. The flags are inputs to the fair spread model and to the memo. Thresholds are defaults (R9).

| Test | Rule | Flag |
| --- | --- | --- |
| EQ1 Receivables | Receivable days rise more than 10% year on year while sales growth is below 5% | Channel stuffing (p. 202) |
| EQ2 Inventory | Inventory days rise more than 10% year on year while sales fall | Obsolescence or dealer dumping (pp. 211, 213) |
| EQ3 Orders | Backlog falls while sales rise | Growth overstated; orders behind shipments (p. 211) |
| EQ4 Organic | Reported growth minus organic growth exceeds 5 points; organic excludes FX, M&A, and price | Inflated growth (pp. 209–211) |
| EQ5 Recurrence | Nonrecurring items in three or more of the last five years | Recurrent costs (p. 192) |
| EQ6 Capitalisation | Capitalised costs grow faster than revenue for two years | Capitalised operating expense (p. 202) |
| EQ7 Conversion | `(CFO - capex) / ebitda_adj_analyst` below 0.3 for two years with no stated working capital build | Accrual earnings |
| EQ8 Big bath | A write-down in the quarter of a CEO change or a guidance cut, then a margin rebound | Future costs booked today (p. 202) |
| EQ9 Gap | `addback_gap` above 0.10 | Company adjustments aggressive; above 0.20 is red |
| EQ10 Control | Going-concern language, material weakness, auditor change, or restatement | Red. Stop and re-read every number |

Output: `ebitda_adj_analyst`, the add-back table with class and decision per item, `eq_flags[]`, and `eq_score` equal to the count of flags with EQ10 counted twice.

## F4. Liquidity, maturities, and refinance access

A default is a liquidity event before it is a leverage event (p. 424). This section sizes what the issuer can spend, when it runs out, and whether the market will refinance it.

### Liquidity

```latex
L^{eff}_t = Cash^{free}_t + \min(Commitment_t, BorrowingBase_t, Trigger_t) - Drawn_t - LC_t - MinCash_t
```

| Rule | Statement |
| --- | --- |
| F4.1 Free cash | Count only unrestricted cash that the parent can reach. Haircut cash held abroad or in regulated subsidiaries by the cost to move it. |
| F4.2 Borrowing base | Availability under an ABL is advance rates times eligible receivables and inventory at net orderly liquidation value, less reserves (p. 234). Recompute it in the downside case, because eligible collateral falls with sales. |
| F4.3 Springing test | If a draw above a trigger starts a covenant test the issuer would fail, cap availability at the trigger. The trigger is often near 10% of the line; read the document. |
| F4.4 Minimum cash | Deduct one month of cash operating costs, or the figure the company discloses as its operating minimum. |
| F4.5 Toggle | A PIK toggle counts as a liquidity lever equal to the cash coupon it defers, with the cost of a higher claim later (p. 125). |

### Runway and the wall

| Metric | Rule |
| --- | --- |
| `runway_static_q` | `L_eff / max(0, -FCF_quarterly_LTM)`. Infinite when FCF is positive. |
| `runway_scen_q` | First quarter in which `L_eff` falls below zero in the severe downside path of F6. This is the runway the memo quotes. |
| `wall_18m` | Debt due within 18 months, plus any springing maturity that pulls a facility inside that window, plus a revolver whose maturity falls inside it. A springing maturity sits inside a junior maturity by a stated number of months; read it (p. 372). |
| `wall_cover_h` | `(L_eff + sum of base case FCF to h) / sum of maturities to h`, for h of 4 and 8 quarters. |
| `refi_date` | First date on which the issuer must reach the market: the earlier of `wall_18m` and the quarter in which `wall_cover` falls below 1. |

Defaults: `runway_scen_q` below 4 is red, 4 to 8 amber. `wall_cover_4` below 1 is red.

### Refinance access score

Score 0 to 6. Each line adds one point. Map the score to `p_refi_access` with a calibration table built from realised refinancings by score and by market state.

| Point | Condition |
| --- | --- |
| 1 | Corporate rating at B minus or better with no negative outlook or watch |
| 2 | A debt or equity raise in the last 12 months at or near par |
| 3 | Unencumbered assets or basket capacity cover at least half of `wall_18m` |
| 4 | The issuer's longest bond trades above 90 and inside 700 bp |
| 5 | The primary market is open: trailing one-month high yield issuance above its trailing twelve-month median, and `kappa_t` below its trailing median |
| 6 | A sponsor or parent with capacity and a record of support |

### Trade credit, capex, and levers

- F4.6 Flag trade tightening when payable days fall by more than 10 days year on year, or when a credit insurer withdraws cover. For A1, read supplier terms before the seasonal build (p. 231).
- F4.7 Maintenance capex is the disclosed figure. If none is disclosed, use depreciation as the floor for A4 and A5, and the archetype norm for A1. Growth capex counts as cuttable within two quarters (p. 266).
- F4.8 List the other levers (p. 231): asset sales, receivable securitisation, a borrowing base increase or FILO tranche, a division sale. Give each an amount, a time to cash, and a probability. Count only levers that complete inside `runway_scen_q`.
- F4.9 Separate the burn into operations, cash interest, mandatory amortisation, and capex. The memo states which part the levers cover.

Output: `liquidity_L_eff`, `runway_static_q`, `runway_scen_q`, `wall_18m`, `wall_cover_4`, `wall_cover_8`, `refi_date`, `refi_score`, `p_refi_access`, `trade_flag`, `capex_flex`, `levers[]`.

## F5. Capital structure and claim sizing

Build the capital structure table first (Figure 9.6, p. 261). Then build two views from it and never mix them (R3). The going-concern view answers how much debt the business carries. The claims view answers who gets paid what if it fails. A balance-sheet liability is an input to the first view and only a starting point for the second.

### The going-concern view

| Metric | Formula | Rule |
| --- | --- | --- |
| `lev_gc_k` | Face of debt through tranche k, over `ebitda_adj_analyst` | Section 4.3; senior claims at face |
| `lev_lease_adj` | `(debt + lease_debt) / (ebitda_adj_analyst + rent)` | `lease_debt` is the balance-sheet operating lease liability plus finance leases after 2018, or 8 times rent for older periods (pp. 267–268). Use it for A1 always |
| `fccr` | `(ebitda_adj_analyst + rent - maintenance_capex) / (cash_interest + rent + mandatory_amortisation)` | Fixed charge coverage with rent; the lender's view of a lease-heavy issuer |
| `coverage` | `(ebitda_adj_analyst - capex) / cash_interest` | The book's ratio (p. 262) |
| `debt_adj` | Debt plus pension deficit plus guarantees to weak parties plus contingent liabilities likely to crystallise | For leverage, not for claims (p. 273) |

### The claims view: allowed claim by class

Size each class by the rule in the table. Keep the book figure beside the allowed figure. The ratio between them is a metric (F8).

| Class | Allowed claim rule | Rank | Code reference |
| --- | --- | --- | --- |
| DIP and super-priority | The DIP size needed to fund the case; estimate from the burn in F4 plus professional fees | First, ahead of pre-petition secured lenders where they are over-collateralised (p. 432) | §364 |
| Administrative | Professional fees, post-petition trade, goods delivered in the 20 days before filing, cure costs of assumed leases and contracts | After DIP, before all pre-petition unsecured | §503(b), §503(b)(9), §365(b) |
| Priority unsecured | Wages and benefits up to the indexed per-employee cap; certain taxes; pension contributions due in the 180 days before filing | After administrative | §507 |
| Secured funded debt | Allowed secured amount equals the lesser of the claim and the value of its collateral. The excess is an unsecured deficiency claim. Post-petition interest and fees accrue only when the collateral exceeds the claim | On its collateral, by lien priority and the intercreditor agreement | §506(a), §506(b) |
| Unsecured funded debt | Principal plus interest accrued to the petition date. Unamortised original issue discount is unmatured interest and is disallowed. A make-whole or prepayment premium is contested; carry it as two scenarios | General unsecured, or subordinated where a subordination agreement says so | §502(b)(2), §510(a) |
| Guarantees | One claim at each guarantor entity for the full amount, capped at one recovery in total; a double dip when the structure allows it (Chapter 17) | At the rank of the guarantee at that entity |  |
| Rejected real property leases | `C_j = U_j + max(Rent_j(1 year), min(0.15 × RemainingRent_j, Rent_j(3 years)))`, with rent undiscounted and unaccelerated and `U_j` the unpaid pre-petition rent. Only rejected leases create a claim. Reduce by expected re-letting (p. 433, pp. 553–554) | General unsecured | §502(b)(6), §365 |
| Assumed leases | No damage claim. Cure amounts are administrative. The lease continues at contract rent | Administrative for the cure | §365(b) |
| Equipment and aircraft leases | Not under the real property cap. Equipment rejection damages are contract damages less mitigation. Aircraft and vessel financings have their own cure-or-surrender regime; treat them as secured | Secured or general unsecured by instrument | §1110 |
| Pensions | Single-employer plan: the termination liability on the insurer's assumptions, not the accounting deficit. Multi-employer: withdrawal liability | General unsecured, with the 180-day contribution slice as priority | §507(a)(5) |
| Retiree medical | Modifiable in the case; claim small relative to the accounting liability | General unsecured | §1114 |
| Trade payables | Pre-petition payables less critical vendor payments made in the case | General unsecured |  |
| Derivatives and hedges | Termination value net of posted collateral; counterparties close out under the safe harbours | General unsecured for the net amount | §560 |
| Litigation, environmental, tort | Estimated for allowance; mass tort often channelled to a trust; some environmental obligations survive | General unsecured, or ahead of it where they survive | §502(c) |
| Rejected employment contracts | Capped at one year of compensation plus unpaid amounts | General unsecured | §502(b)(7) |
| Intercompany | Map each one. Expect recharacterisation or subordination arguments and a substantive consolidation argument when entities are entangled (Chapter 17) | Case by case | §510(c) |
| Avoidance recoveries | Transfers in the 90 days before filing, one year for insiders; transfers for less than reasonably equivalent value within two years, longer under state law. Dividend recaps and drop-downs sit here (Chapter 16) | Adds to the estate | §547, §548, §544 |

### Waterfall procedure

1. Map every claim to the legal entity it sits against. Mark guarantors and non-guarantor subsidiaries. Run the waterfall per entity and pass equity value up the ownership chain.
2. Set `V` from F7 for the case: reorganisation value for a going concern, liquidation value for a wind-down.
3. Pay DIP and super-priority, then allowed secured claims to the value of their collateral pools, then administrative, then priority unsecured.
4. Form the unsecured pool `P_U` from funded unsecured debt, secured deficiencies, capped lease claims, pension, trade, derivative, litigation, and other allowed claims.
5. Recovery to the pool is `R_U = min(1, max(0, V - S) / P_U)`, with `S` the sum of everything paid in step 3. Apply subordination agreements inside the pool.
6. Repeat for three rejection sets, low, base, and high, as the book does for its liquidation case (Figure 19.26, p. 554).
7. Record the book liability, the allowed claim, and the ratio for every class in the memo table of F12.

Defaults: professional fees for a case of about a year run at a low single-digit percent of total claims; calibrate from comparable cases by size. The rejection set in the base case equals the stores or sites that lose money in the downside path of F6.

## F6. Forward cases and macro weights

Build six cases with the driver set of Figure 10.18 (p. 306): sales growth, variable cost ratio, SG&A ratio, inventory days, payable days, capex, plus the interest rate path, cash taxes, and any PIK option. Every driver carries a one-line rationale (p. 289). Run each case for at least 8 quarters, 12 when a maturity sits inside 3 years.

### Case construction rules

| Case | Construction rule |
| --- | --- |
| Management | Guidance and stated targets, as given, with dates. If no guidance exists, mark the case absent; do not invent one (p. 285) |
| Consensus | Median of sell-side estimates. Record the count and the dispersion |
| Base | The analyst's view. It passes the coin-toss test: the analyst's own record shows actuals above the base case about half the time. A base case that is conservative by habit fails the test (p. 285) |
| Downside, moderate | The archetype's main risk at the severity of the last cycle. A4: the issuer's own peak-to-trough revenue in the last recession, with the same recovery shape (pp. 290, 306). A1: the comparable-sales decline of the last downturn and gross margin at the trough. A3: the price deck at the 10th percentile of the trailing ten years with the hedge book run off. A2: the last reimbursement change of the same kind. A6: net retention at the issuer's worst disclosed year. A7: the asset-specific shock the documents test for |
| Downside, severe | 1.5 times the moderate revenue decline, one year longer to recover, trade terms tighten by 10 payable days, margin below the historic trough (p. 386) |
| Upside | Mirror of the moderate downside unless a named catalyst exists; then the catalyst case |

### Mechanics that every case applies

- F6.1 Negative FCF draws the revolver up to the availability of F4; then cash falls to the minimum; then the case records a liquidity shortfall and its quarter.
- F6.2 Test covenants each quarter on covenant EBITDA, not analyst EBITDA (p. 354). Record the first breach quarter.
- F6.3 A maturity inside the horizon refinances at the Treasury forecast plus the fair spread when `p_refi_access` exceeds 0.5 in that quarter. Otherwise the case records a refinance failure and continues as a distressed exchange path with the claims view of F5.
- F6.4 Floating interest follows the policy rate path of the macro scenario. Fixed coupons change only at refinance.
- F6.5 Working capital follows the days assumptions and the revenue path, so a sales decline releases cash in A4 and consumes it in A1 when inventory is already bought.

### Macro phase and the weight table

Classify the phase by majority vote of six indicators. Then take the default weights from the table and adjust by archetype. Replace the defaults with the fitted logistic of Section 5.2 once it is calibrated.

| Indicator | Late cycle or downturn when |
| --- | --- |
| `hy_oas` | Above its trailing five-year median and rising over three months |
| `distress_ratio` | Above its trailing five-year median |
| `sloos_tightening` | Net tightening positive for two quarters |
| `pmi` | Below 50 |
| `default_rate_fcst` | Above `default_rate_ttm` |
| Issuance quality | CCC share and cov-lite share above their trailing medians in the prior year (p. 355) |

| Phase | Base | Downside moderate | Downside severe | Upside |
| --- | --- | --- | --- | --- |
| Expansion | 0.60 | 0.15 | 0.05 | 0.20 |
| Late cycle | 0.50 | 0.25 | 0.10 | 0.15 |
| Downturn | 0.35 | 0.35 | 0.20 | 0.10 |
| Repair | 0.50 | 0.25 | 0.10 | 0.15 |
| Recovery | 0.55 | 0.15 | 0.05 | 0.25 |

Archetype adjustment: multiply both downside weights by 1.3 for A3 and A4, by 0.7 for A2 and A5 with contracted revenue, then renormalise. Modifier M3 adds a loss-of-contract branch inside the moderate downside with the probability the analyst states.

### Weight rules

- F6.6 If the combined downside weight exceeds 0.5, the moderate downside becomes the base case and the cases shift down one step (p. 311).
- F6.7 Re-run all cases on each filing, each guidance change, and each phase change. Keep the vintage.
- F6.8 Report the weighted forward features of Section 5.3 and the path statistics: peak leverage, minimum liquidity, first breach quarter, first refinance failure quarter, each by case.
- F6.9 Forecast linkage (methodology Section 5.4). Every scenario weight and every driver shift cites a forecast row (source, variable, horizon, vintage) or a market-implied quantity. When a source is missing, fall back in this order: (1) a market-implied quantity (forward curve, index spread); (2) the F6 table; (3) a logged assumption with a decision page. The memo lists every fallback used.
- F6.10 Path probabilities combine the forecast quantile mass with the phase prior by Bayes' rule. Record the prior, the mass, and the posterior. A change of more than 0.10 in any path probability between vintages is a revision event for signal S7. Calibration note: 0.10 is a default (R9); set it from the distribution of vintage-to-vintage changes once twelve vintages exist.

## F7. Valuation, recovery, and the liability management score

Value the company three ways at least, pick the methods by archetype, and read recovery off the claims view of F5. The market's own valuation is a check against the model, never the anchor (p. 321).

### Method selection by archetype

| Archetype | Primary methods | Distressed value basis |
| --- | --- | --- |
| A1 | EV to EBITDAR with lease-adjusted peers; liquidation of inventory, receivables, owned real estate, and assignable below-market leases | Liquidation value often binds |
| A2 | EV to EBITDA peers; precedent facility deals; owned facilities at sale-leaseback value | Going concern at the trough multiple |
| A3 | Net asset value from reserves at the stress deck; precedent deals per unit of production | Net asset value at the stress deck |
| A4 | EV to mid-cycle EBITDA; DCF through the cycle | Going concern at the trough multiple |
| A5 | EV to EBITDA; asset appraisals per unit | Appraised asset value in a forced sale |
| A6 | EV to recurring revenue and EV to EBITDA; DCF with retention | Going concern; liquidation value is small |
| A7 | Project DCF over the contract life | Project DCF under the shock |

### Valuation rules

| Rule | Statement |
| --- | --- |
| F7.1 Multiples | Use the peer median of F3.3. Apply a stated discount for size and liquidity; the default is one turn below the median for an issuer under one tenth of the peer median size. |
| F7.2 Earnings basis | `V_mid` uses base case forward EBITDA. `V_default` uses the severe downside EBITDA, or mid-cycle EBITDA for A4 when the downturn is cyclical. |
| F7.3 Distressed multiple | The lower of the peer trough multiple over the last two cycles and the plan values of precedent restructurings in the archetype. |
| F7.4 DCF | Base case FCF, a peer-derived discount rate, terminal growth at or below nominal GDP. Under M2 the terminal value declines. |
| F7.5 Liquidation table | Defaults by asset class: cash 100%; receivables 85% to 95%, lower for A2 after contractual allowances; inventory 60% to 75% at net orderly liquidation value, finished goods high and work in progress low; owned real estate 70% to 80%, lower in a forced sale; machinery 10% to 20%; intangibles 0% to 15%, higher for a strong consumer brand; less liquidation expenses of about 5% and wind-down costs (p. 332; Figure 19.25, p. 553). Replace the defaults with the archetype table once calibrated. |
| F7.6 Range | `V_low` and `V_high` are the 10th and 90th percentiles across methods weighted by archetype; `V_mid` is the weighted mean; `sigma_V` follows Section 6.1. |
| F7.7 Market check | If market capitalisation implies a value above `V_high`, flag it and read the short interest. If the longest bond's price implies a value below `V_low`, flag it (p. 333). |
| F7.8 Case choice | Use reorganisation value when the distressed going-concern value exceeds liquidation value; otherwise run the liquidation case. State which one the memo uses. |

### Recovery rules

- F7.9 Run the waterfall of F5 with `V_default` for recovery and with `V_mid` for loan-to-value. Report both.
- F7.10 Report recovery by tranche for the three rejection sets, and the market-implied recovery from the price of the longest equal-rank bond when the issuer is distressed (p. 530).
- F7.11 Report the creation multiple of each tranche against the distressed multiple. A creation multiple below the distressed multiple means the market price sits below model recovery.
- F7.12 Compute `guarantor_coverage`: the share of EBITDA and of asset value at entities that guarantee the tranche. Below 0.8 is a value leakage flag.

### Liability management score

Score the documents and the owner. Each line adds its points. Map the score to `pi_lme` with the calibration of Section 6.3; the defaults below are starting points.

| Points | Condition |
| --- | --- |
| +2 | Required lenders at a simple majority and pro rata sharing amendable without each affected lender's consent (pp. 504, 358) |
| +2 | Unrestricted subsidiary and investment capacity above 10% of `V_mid`, or no restriction on transfers of material intellectual property (pp. 499–501) |
| +2 | Restricted payment and investment capacity, general plus builder baskets, above one turn of EBITDA |
| +1 | Incremental debt and lien capacity above half a turn of EBITDA |
| +1 | Collateral release possible with majority consent |
| +1 | Sponsor-owned with a prior dividend recap or asset transfer |
| +1 | `p_liq_short_8` above 0.25 |

| Score | Default `pi_lme` |
| --- | --- |
| 0 to 2 | 0.05 |
| 3 to 5 | 0.15 |
| 6 to 8 | 0.35 |
| 9 to 10 | 0.60 |

`R_LME` is the recovery after the largest drop-down the documents permit, removing that collateral value from `V`, and the largest uptier they permit, adding priming debt equal to the new money capacity plus the exchanged majority to `S_k` (Figures 18.3 and 18.4, pp. 503–504). The adjusted recovery blends the two as in Section 6.3.

## F8. Metrics catalogue

One row per metric. Each has a formula, a unit, a direction, default bands, and a consumer. Bands are defaults under R9; a metric marked "rank" is judged as a percentile inside its archetype, because its level means little across archetypes. Green, amber, and red are the three bands in that order.

### Profitability and quality

| Metric | Formula | Unit | Better when | Default bands | Consumer |
| --- | --- | --- | --- | --- | --- |
| `margin` | `ebitda_adj_analyst / revenue` | % | Higher | Rank | F9, Section 7.2 |
| `margin_trend` | Slope of margin over 8 quarters over its standard error | t-stat | Higher | > 1 / −1 to 1 / < −1 | S2, PD |
| `margin_peer_gap` | `margin - peer_median_margin` | points | Higher | > 0 / −3 to 0 / < −3 | Section 7.2 |
| `organic_growth` | Reported growth less FX, M&A, and price | % | Higher | Rank | F3, S2 |
| `book_to_bill` | Orders over shipments | ratio | Higher | > 1.0 / 0.9 to 1.0 / < 0.9 | A4 only |
| `surprise` | `(actual - consensus) / consensus` | % | Higher | Record | S3 |
| `addback_gap` | `ebitda_adj_company / ebitda_adj_analyst - 1` | % | Lower | < 10 / 10 to 20 / > 20 | F3, PD |
| `covenant_gap` | `ebitda_covenant / ebitda_adj_analyst - 1` | % | Lower | < 10 / 10 to 25 / > 25 | F4, headroom |
| `eq_score` | Count of EQ flags, EQ10 twice | count | Lower | 0 / 1 to 2 / ≥ 3 | PD, gate |
| `fcf_conversion` | `fcf / ebitda_adj_analyst` | ratio | Higher | > 0.30 / 0.10 to 0.30 / < 0.10 | PD |

### Cash and liquidity

| Metric | Formula | Unit | Better when | Default bands | Consumer |
| --- | --- | --- | --- | --- | --- |
| `fcf_to_debt` | `fcf / total_debt` | ratio | Higher | > 0.10 / 0.03 to 0.10 / < 0.03 | PD, rating gap |
| `cash_cycle` | Inventory days + receivable days − payable days | days | Lower | Rank | A1, A4 |
| `payable_days_trend` | Change in payable days over 4 quarters | days | Higher | > −5 / −10 to −5 / < −10 | Trade flag |
| `liquidity_L_eff` | F4 formula | currency | Higher | Record | Runway |
| `runway_scen_q` | First quarter of shortfall in the severe downside | quarters | Higher | ≥ 8 / 4 to 8 / < 4 | PD, events |
| `wall_cover_4` | `(L_eff + base FCF to 4q) / maturities to 4q` | ratio | Higher | > 1.5 / 1.0 to 1.5 / < 1.0 | Refinance event |
| `refi_score` | F4 score | 0 to 6 | Higher | ≥ 4 / 2 to 3 / ≤ 1 | `p_refi_access` |
| `capex_flex` | `(capex_total - capex_maintenance) / capex_total` | ratio | Higher | Rank | Downside case |

### Leverage and coverage, going-concern view

| Metric | Formula | Unit | Better when | Default bands | Consumer |
| --- | --- | --- | --- | --- | --- |
| `lev_gc_total` | `total_debt / ebitda_adj_analyst` | x | Lower | Rank; red above the covenant maximum less the cushion | Section 7.2 |
| `lev_gc_k` | Debt through tranche k over EBITDA | x | Lower | Rank | S4 |
| `net_lev` | `(debt - free_cash) / ebitda_adj_analyst` | x | Lower | Rank | Rating gap |
| `lev_lease_adj` | `(debt + lease_debt) / (ebitda_adj_analyst + rent)` | x | Lower | Rank; required for A1 | Section 7.2 |
| `coverage` | `(ebitda_adj_analyst - capex) / cash_interest` | x | Higher | > 2.0 / 1.25 to 2.0 / < 1.25 | PD |
| `fccr` | F5 formula with rent | x | Higher | > 1.5 / 1.1 to 1.5 / < 1.1 | A1, A5 |
| `lev_fwd_4` | Weighted forward leverage at 4 quarters | x | Lower | Rank | Section 7.1 |
| `delev_4` | `lev_fwd_4 - lev_gc_total` | x | Lower | < −0.25 / −0.25 to 0.25 / > 0.25 | S2, S3 |
| `lev_peak_down` | Peak leverage in the severe downside | x | Lower | Below the distressed multiple is green | Recovery |

### Claims and recovery, claims view

| Metric | Formula | Unit | Better when | Default bands | Consumer |
| --- | --- | --- | --- | --- | --- |
| `claim_haircut_leases` | Allowed rejected lease claims over the book lease liability | ratio | Informational | Record; the gap to the market's assumption feeds S8 | F9 |
| `claim_haircut_pension` | Termination liability over the accounting deficit | ratio | Informational | Record | F9 |
| `pool_ratio` | Allowed unsecured pool over book unsecured liabilities | ratio | Informational | Record | S8 |
| `ltv_k_mid` | Claims through tranche k over `V_mid` | % | Lower | < 50 / 50 to 80 / > 80 | S4, Section 7.2 |
| `recovery_k`, `recovery_k_adj` | F5 waterfall at `V_default`, clean and LME adjusted | % | Higher | Compare with market-implied; a 15-point gap is a signal | LGD, S8 |
| `creation_multiple_k` | `lev_mkt_k` | x | Lower | Below the distressed multiple is green | S4, F9 |
| `guarantor_coverage` | Share of EBITDA and assets at guarantor entities | ratio | Higher | > 0.9 / 0.8 to 0.9 / < 0.8 | Recovery |
| `lme_score`, `pi_lme` | F7 rubric and its mapping | points, prob | Lower | 0 to 2 / 3 to 5 / ≥ 6 | S5, recovery |

### Covenants and documents

| Metric | Formula | Unit | Better when | Default bands | Consumer |
| --- | --- | --- | --- | --- | --- |
| `H_t` | `1 - lev_covenant / lev_max` | % | Higher | > 25 / 10 to 25 / < 10 (p. 356) | Events |
| `p_breach_4` | Weighted share of cases with a breach inside 4 quarters | prob | Lower | < 5 / 5 to 20 / > 20 | PD, events |
| `rp_capacity_turns` | Restricted payment plus investment capacity over EBITDA | x | Lower | < 0.5 / 0.5 to 1.0 / > 1.0 | LME score |
| `debt_capacity_turns` | Incremental debt and lien capacity over EBITDA | x | Lower | < 0.25 / 0.25 to 0.5 / > 0.5 | LME score |
| `call_state` | Price minus next call price, and months to the call | points, months | Context | Record | Convexity, S5 |

### Forward and macro

| Metric | Formula | Unit | Better when | Default bands | Consumer |
| --- | --- | --- | --- | --- | --- |
| `w_down` | Combined downside weight after archetype adjustment | prob | Lower | < 0.25 / 0.25 to 0.5 / > 0.5 (F6.6) | Everything forward |
| `lev_fwd_sd_4` | Dispersion of forward leverage | x | Lower | Rank | Band width, sizing |
| `p_liq_short_8` | Weighted share of cases with a shortfall inside 8 quarters | prob | Lower | < 5 / 5 to 20 / > 20 | PD, LME |
| `p_refi_4` | Weighted share of cases with wall cover below 1 inside 4 quarters | prob | Lower | < 5 / 5 to 20 / > 20 | Events |
| `rev_lev` | Change in `lev_fwd_4` between vintages | x | Lower | Record | S3 |
| `gap_consensus`, `gap_mgmt` | Base case forward leverage minus consensus, minus management | x | Context | Record | S3, F9 |

### Market-implied and risk

| Metric | Formula | Unit | Better when | Default bands | Consumer |
| --- | --- | --- | --- | --- | --- |
| `implied_lambda` | `oas / (kappa_t × lgd_k_adj)` | per year | Context | Record | F9 |
| `implied_pd_12m` | `1 - exp(-implied_lambda)` | prob | Context | Compare with `pd_12m` | F9 |
| `implied_recovery` | Price of the longest equal-rank bond when distressed | % | Context | Compare with `recovery_k_adj` | F9, S8 |
| `implied_ebitda_fair` | EBITDA at which `s_fair` equals `oas`, holding the rest fixed | currency | Context | Compare with the base case | F9 |
| `s_fair`, `resid_bp`, `z` | Section 7 | bp, bp, sd | Context | `abs(z)` above `q_alpha_t` is a signal | S1 |
| `pd_12m`, `lgd_k_adj`, `s_el` | Section 7.1 | prob, %, bp | Lower | Calibrated by rating | Anchor |
| `jtd_per_mm`, `sdv01_per_mm`, `rdv01_eff_per_mm` | Section 9.3 | currency | Context | Limits, not bands | Risk |
| `beta_mkt`, `beta_g`, `beta_p` | Section 9.2 | ratio | Context | Record | Hedges |
| `event_var_alpha` | Section 9.2 | currency | Lower | Inside the event budget | Limits |

## F9. Market-implied quantities and the thesis-versus-implied gate

A credit opinion says what the company is. A trade call says what the price is wrong about. The gate separates them. Before any call, compute what the current price implies for each quantity the thesis rests on, put the analyst's number beside it, and require a named gap.

### Implied quantities

```latex
\lambda^{impl}_i = \frac{oas_i}{\kappa_t \, LGD^{adj}_i}, \qquad PD^{impl}_{h} = 1 - e^{-\lambda^{impl}_i h}, \qquad \Delta LGD^{impl}_{k,j} = \frac{s_k - s_j}{\kappa_t \, \lambda_i}
```

| Quantity | How to compute | Compare with |
| --- | --- | --- |
| `implied_pd_12m` | From the spread at the current market price of risk, formula above. Also report the break-even PD at `kappa = 1`, the PD at which the spread only covers expected loss | `pd_12m` from Section 7.1 |
| `implied_recovery` | Distressed: the price of the longest equal-rank bond (p. 530). Performing: the recovery gap to the secured tranche from the spread gap, formula above | `recovery_k_adj` from F5 and F7 |
| `implied_ebitda_fair` | Solve `s_fair(x; EBITDA) = oas` for EBITDA with every other feature fixed | Base case EBITDA at 4 quarters |
| `implied_lev_fair` | The forward leverage at which the bond is fair, same solve | `lev_fwd_4` |
| `creation_multiple_k` | `lev_mkt_k` (Section 4.3) | Distressed multiple of F7.3 |
| `implied_rating` | The rating bucket whose duration-matched index spread is nearest to `oas` | Agency rating and `rating_model` |
| `implied_p_event` | For a put bond against a non-put bond: the probability that makes the pair fair. For a callable bond: the probability of the call that explains the price against the schedule | The analyst's `p_LBO`, `p_call` |

### The gate

| Rule | Statement |
| --- | --- |
| G1 Gap | At least one row shows a gap larger than its noise: `abs(view - implied)` above one standard error of that quantity, or the residual outside the conformal band for the spread row. |
| G2 Catalyst | The gap maps to a catalyst with a date or a window and to a horizon in months. A gap with no catalyst is a credit opinion. The memo says so and stops. |
| G3 Return | Expected convergence return (Section 7.5) net of the round-trip bid-ask exceeds zero and exceeds the event budget of Section 9.4. |
| G4 Clean state | No event inside the last five days, unless the call is the event trade of F11. |
| G5 Regime | Below a price of 80 or above 1,000 bp, write the call in price and recovery, not in spread (p. 122). The implied rows switch to recovery and creation multiple. |
| G6 Consistency | The gaps agree in sign across rows. Mixed signs mean no call; write the open question instead. |
| G7 Type | The memo names the call type: fundamental view only; relative value (S1, S4, S7); event (S5, S6, F11); recovery (S8). |
| G8 Invalidation | One observable that flips the sign, with its threshold and date. Stored as `invalidation`. A call without it does not enter the book. |
| G9 Size | Position scale proportional to the gap over its noise, capped by liquidity and by the limits of Section 9.4. |

### The thesis-versus-implied table

Every memo carries this table, filled, even when the result is no call.

| Row | Market implies | Analyst view | Gap | Noise | Passes G1 |
| --- | --- | --- | --- | --- | --- |
| 12-month PD |  |  |  |  |  |
| Recovery of this tranche |  |  |  |  |  |
| EBITDA in 4 quarters |  |  |  |  |  |
| Leverage in 4 quarters |  |  |  |  |  |
| Rating |  |  |  |  |  |
| Catalyst probability |  |  |  |  |  |
| Spread against fair |  |  |  |  |  |

## F10. Signals catalogue

Nine signals. Seven come from Section 8 of the methodology; S8 and S9 come from the claims view and the refinance rules of this framework. Each signal is a standardised score per bond per day. Positive means long. Every signal passes the gate of F9 before it becomes a position.

### Definitions

| Signal | Formula | Inputs | Horizon |
| --- | --- | --- | --- |
| S1 Fair value residual | `z × 1[abs(z) > q_alpha_t] × 1[event_contaminated = 0]` | Section 7.3 | Two residual half-lives |
| S2 Fundamental momentum | Change in `log s_fair` from fundamentals only, with `kappa` and `eta` fixed, minus the change in `log oas`, over one quarter | Sections 7.2, 4 | 1 to 3 months |
| S3 Revision and consensus gap | `-(rev_lev / sd) - (gap_consensus / sd)` | F6 vintages | To the next earnings date |
| S4 Capital structure | `[(s_k - s_j) - kappa_t × lambda × (LGD_k - LGD_j)] / sd_pair` | F5, F7 | 1 to 3 months |
| S5 Document optionality | Put: `p_LBO × max(0, put_price - P) / P`. LME: `-pi_lme × (R - R_LME) × 100 / P` | F7 score, documents | To the catalyst |
| S6 Rating migration and flows | `[P(up) - P(down)] × w_flow` from the rating gap | Section 4.5 | 1 to 6 months |
| S7 Sector tilt | `[eta_sector - eta_hat(m)] - theta × delta w_down_sector` | Sections 7.2, 5.2 | 1 to 3 months |
| S8 Recovery mispricing | Distressed: `(recovery_k_adj - implied_recovery) × 100 / P / sd`. Performing junior tranche: `(dLGD_implied - dLGD_model) / sd` | F5 claims view, F9 implied rows | To the disclosure that reveals the claim pool; carry counts |
| S9 Refinance wall | Short when `p_refi_4 × (1 - p_refi_access) > 0.20` and the near bond trades inside the issuer's own curve. Long when a completed refinancing clears the wall and `z` stays above half the threshold for ten days | F4, F6 | 1 to 6 months |

### Rules per signal

| Signal | Entry | Exit | Invalidation | Hedge | Failure mode |
| --- | --- | --- | --- | --- | --- |
| S1 | Outside the band; convergence return above costs | `abs(z)` below half the threshold, or horizon end | A fact the model lacks: pending LME, fraud, lost contract | Index and sector beta | Stale filing; unmodelled fact |
| S2 | Score above one standard deviation; EQ flags at zero | Spread has caught up, or EQ flag appears | Improvement shown to be accounting | Index beta | Non-cash improvement |
| S3 | Gap above one standard deviation of the analyst's own revision history | The earnings release | Analyst bias record above threshold | Index beta | Conservative habit |
| S4 | Pair score above one standard deviation; both legs liquid | Pair score below half | Filing imminent for a curve pair (p. 530) | Within issuer; size by jump-to-default | Convergence to recovery; negative carry |
| S5 | Catalyst probability above the implied probability by its noise | Catalyst resolves, or fall-away triggers | Fall-away clause met; documents amended | Pair within issuer | Negative carry; fall-away |
| S6 | Rating gap above one notch; flow weight positive | Agency moves; flow passes | Agency moves the other way | Index beta | Already priced |
| S7 | Sector score above one standard deviation | Score below half | Macro forecast vintage changes sign | Index beta | Stale forecast |
| S8 | Recovery gap above 15 points, or LGD gap above its noise; claim table complete | Disclosure statement or plan sets the pool; gap below 5 points | Rejection set or pension basis proven wrong; LME event | Senior tranche of the same issuer where possible | Rejection set error; priming |
| S9 | Conditions in the definition | Refinancing completes, or `z` normalises | Market reopens and `p_refi_access` rises above 0.5 | Index beta | Market reopens faster than the model |

### Composite and sizing

```latex
C_i = \sum_{j} w_{j,phase}\, \tilde{S}_{j,i}, \qquad w_{j,phase} \propto \max(0, IC_{j,phase}), \qquad n_i = \min\Big(k \, ADV_i,\ \frac{B\,|C_i|}{\sum_l |C_l|},\ \frac{JTD^{limit}_{issuer}}{jtd\_per\_mm_i}\Big)
```

- F10.1 Standardise each signal to unit variance per date inside the universe.
- F10.2 Weight by the trailing rank information coefficient per phase; a signal with a negative IC in the current phase gets zero weight, not a negative one.
- F10.3 Neutralise the composite to index beta and to duration before the rank.
- F10.4 Cap each name at `k` times average daily volume; the default `k` is 5 days of volume to exit.
- F10.5 Scale all positions by the band gate of Section 9.4: a wide conformal band means smaller positions everywhere.
- F10.6 The force rank is the composite sorted across the whole universe, with `replaces_position` filled for every entry (R8).

### Position state machine

1. Candidate: a signal fires. Fill the thesis-versus-implied table.
2. Gate: F9 passes or the candidate is logged as a credit opinion.
3. Entry: size by the formula above; record `invalidation`, horizon, hedge, and `replaces_position`.
4. Hold: each day check `z`, the invalidation observable, the event calendar, and the band gate.
5. Reduce: inside five days of a dated event, cap to the event budget of Section 9.4.
6. Exit: target reached, horizon ended, invalidation hit, or an event reset the state.
7. Postmortem: record the two numbers of F13 and the reason for exit.

## F11. Event playbooks

An event window runs from five trading days before a dated event to five after; a macro release takes one day each side. Inside the window no new S1, S2, or S7 position opens on that issuer. An event trade opens only when F9 passes with the catalyst row filled. Each playbook names what to compute before, how to hold through, and what to update after. The event matrix of Section 10.4 stores the outcome grid.

| Event | Before the window: compute | Inside the window: position rule | After: update |
| --- | --- | --- | --- |
| Earnings and guidance | Outcome grid: beat, in line, miss, each with guidance up and down; `surprise` history; the feature changes per outcome into `s_fair`; `p_miss = w_down(m)` | Cap at the event budget. Hold S3 positions to the release. No adds | Refresh F3 to F6; rerun the gate; clear `event_contaminated` after five days |
| Covenant test | `H_t` on covenant EBITDA; `p_breach`; the waiver cost case: fee, margin step, tighter baskets; the acceleration case | Reduce junior tranches when `H_t` is red; hold secured | Record the outcome; update `covenant_gap` and the LME score if the waiver changed the documents |
| Maturity and refinance | `wall_cover`, `refi_score`, `p_refi_access`; the new coupon at the Treasury forecast plus `s_fair`; the exchange case with the claims view | S9 rules; no long in the near bond when `p_refi_4 × (1 - p_refi_access)` is above 0.20 | New capital structure table; new maturities; rerun F5 |
| Call and tender | `call_state`; `p_call` from the refinance path; price against the schedule | No long above the call price unless `p_call` is low and documented | Replace the bond in the tables; update convexity |
| Rating review | `gap_rating`; `P(up)`, `P(down)`; index weight and constrained holder share | Hold S6 to the action; buy the forced flow after a downgrade only through S1 | Update `rating_agency`; reset S6 |
| Index rebalance | Membership rule outcome; flow estimate from index weight | Fade the flow after the date, not before | Update `index_weight` |
| M&A and LBO | `p_LBO`; put value; pro forma leverage for the non-put bonds; precedent multiples | S5 pair only; negative carry budgeted | New capital structure; new documents; re-frame under M1 |
| Sponsor dividend or recap | Basket capacity in dollars; pro forma leverage; recovery after the payment | Reduce when `rp_capacity_turns` is red and the sponsor has a record | Update the LME score and `recovery_k_adj` |
| Liability management | `lme_score`, `pi_lme`, `R_LME`; which tranche is protected | S5 LME leg; never long the exposed tranche into the window | New claims map; rerun F5 and F7 |
| Asset sale | Collateral share sold; use of proceeds under the documents; deleveraging case | Secured: check the release mechanics first | Update collateral pools and `guarantor_coverage` |
| Litigation and regulation | Claim estimate for allowance; where it ranks; the reimbursement or rule case for A2 | Treat the adverse case as a jump; size by it | Add the allowed claim to the pool |
| Macro release | Rate and spread betas by the growth and policy split; `rdv01_eff` | Hedge to `rdv01_eff` and `beta_mkt`; no single-name change on the day | Update `kappa_t`, `eta_sector`, phase vote |
| Sector shock | Sector driver path; `beta_sector`; correlated jump-to-default across the sector | Apply the correlated-event limit of Section 9.4 | Rerun F6 for the sector |
| Bankruptcy filing | Recovery price per tranche; DIP size; the first-day motions to read: critical vendor, cash collateral, lease rejection | Price converges to recovery; equal-rank bonds converge (p. 530); quotes go flat (p. 119). S8 applies | Claims view becomes primary; rebuild the pool from the schedules and the disclosure statement |

### Event rules

- F11.1 Every dated event in the next 90 days appears in the memo with its playbook row filled.
- F11.2 The event budget is a fraction of the position's expected convergence return, set in Section 9.4. A position whose worst outcome exceeds the budget is cut to size before the window opens.
- F11.3 After each event, record the realised spread change against the predicted outcome distribution. F13 scores it.
- F11.4 A missed event, one that was not in the calendar, is a defect. Record it and add the source that would have caught it.

## F12. Memo template and the force rank

Two memo forms, as in the book (p. 369): a screening memo that decides whether to spend the time, and a full memo that supports a position. Both open with the recommendation and its type. Every number carries a source (R4). A field left empty is written as an open question, never dropped.

### Screening memo, one page

| Field | Content | Source |
| --- | --- | --- |
| Recommendation and type | Long, short, pass, or watch; call type per G7 | F9 |
| The five lines | Business frame, archetype, modifiers | F2 |
| Capital structure table | Tranche, face, price, yield, spread, rating, `lev_gc_k`, `ltv_k_mid` | F5 |
| Three numbers | `runway_scen_q`, `wall_cover_4`, `recovery_k_adj` for the tranche in question | F4, F5, F7 |
| Thesis-versus-implied table | Filled, with the row that passes G1 marked | F9 |
| Next events | The next two dated events and their playbook rows | F11 |
| Open questions | Ranked list for management and diligence (pp. 216, 231) | F3, F4 |

### Full memo

| Section | Content | Source |
| --- | --- | --- |
| 1. Recommendation | Direction, size, horizon, hedge, call type, `invalidation`, `replaces_position` | F9, F10 |
| 2. Thesis | Three sentences at most: what the price is wrong about, why, and what reveals it | F9 |
| 3. Business frame | The five lines; archetype and modifiers; peer set | F2, F3 |
| 4. Normalised results | Adjusted income statement; add-back table by class; EQ flags | F3 |
| 5. Cash and liquidity | `L_eff` build; runway; wall; refinance score; levers | F4 |
| 6. Capital structure, two views | Going-concern ratios; claims table with book liability, allowed claim, and ratio per class; priority map; entity map | F5 |
| 7. Cases | Driver table per case with rationale; path statistics; macro phase and weights | F6 |
| 8. Valuation and recovery | Football field; distressed value; waterfall by rejection set; market-implied recovery; creation multiples; LME score | F7 |
| 9. Relative value | Spread against the rating index, the sector index, the peers, and the issuer's own tranches, each with the risk measure beside it, as the HCA table does (pp. 412–413); spread per turn observed against model | Section 7.4 |
| 10. Risks and mitigants | Each risk with the metric that tracks it and the outcome that resolves it | F8, F11 |
| 11. Event calendar | Next 90 days with playbook rows | F11 |
| 12. Metrics panel | The F8 bands for this issuer, red items first | F8 |
| 13. Postmortem fields | Left empty at entry: exit date, realised excess return against the rating-matched index, relative trough, the reason, the rule that would have helped (p. 414) | F13 |

### Force rank

- F12.1 Rank every candidate and every position by the composite of F10, across sectors, once a week and on any day with an entry (p. 369).
- F12.2 Each entry names the position it replaces and shows both rows of the rank side by side (R8).
- F12.3 The rank sheet carries `z`, `C_i`, `jtd_per_mm`, `runway_scen_q`, `recovery_k_adj`, the next event date, and the call type.
- F12.4 A position below the median of the rank for four consecutive weeks goes to review with a one-line reason to hold or exit.

## F13. Evaluation of the framework

The framework earns its place only if memos written with it beat memos written without it, on the same filings, under blind review, and if the calls it produces make money after costs. Two scores measure this: a memo score from a rubric, and an outcome score from what happened.

### Memo rubric

Ten items, each scored 0 to 3 by two blind reviewers. 0 means absent, 1 present but wrong, 2 present and right, 3 right and used in the recommendation.

| Item | What earns a 3 |
| --- | --- |
| 1. Frame | The five lines and the archetype, and the ratios that follow match the archetype |
| 2. Normalisation | Add-back table by class; the three EBITDA numbers and their gaps |
| 3. Liquidity | `L_eff` built from sources; scenario runway; wall and refinance score |
| 4. Claims | Book liability and allowed claim per class, with the lease cap applied to a rejection set |
| 5. Recovery | Waterfall by tranche for three rejection sets; market-implied recovery beside it |
| 6. Cases | Drivers with rationale; macro phase and weights; path statistics |
| 7. Gate | Thesis-versus-implied table filled; call type named; opinion and call kept apart |
| 8. Relative value | Against rating index, sector, peers, and own tranches, with risk beside spread |
| 9. Risks | Each risk with its tracking metric and the resolving outcome |
| 10. Discipline | `invalidation`, horizon, hedge, and `replaces_position` present |

### Paired blind test

- F13.1 Hold out a set of resolved credits: defaults, refinancings, buyouts, liability management cases, and quiet maturities. Freeze `available_at` at a date before resolution.
- F13.2 Write two memos per credit from the same filings: one with this framework, one without it. Anonymise both.
- F13.3 Two reviewers score the rubric blind. At least one fifth of the sample goes to a reviewer from a different model family or to a human, because a judge from the writer's family shares its blind spots.
- F13.4 Report the win rate with a binomial test, the per-item deltas, and the items where the unaided memo won.
- F13.5 Include distressed and private credits where the data allows. The lease and claims rules matter more there, not less.

### Outcome score

For every closed position and every resolved held-out credit, record:

| Measure | Definition | Pass |
| --- | --- | --- |
| Excess return | Annualised return against the rating-matched index over the holding period (p. 414) | Positive after costs |
| Relative trough | Position trough against the index trough over the same period (p. 414) | Shallower |
| Invalidation hit | Whether the stated invalidation fired before the loss exceeded the budget | Fired first |
| Recovery error | `recovery_k_adj` minus realised recovery, in points, by rank and archetype | No bias; absolute error falls over time |
| Event calibration | Probability integral transform of realised spread changes against predicted outcome distributions | Near uniform |
| PD calibration | Brier score and reliability by rating and phase | Inside the agency band by rating (p. 274) |
| Rank quality | Rank information coefficient of the force rank, and the long-short decile return after costs, by phase | Positive in three of four cycles |

The headline analyst metric is two numbers: the paired win rate on the rubric, and the long-short decile information ratio after costs. Publish both beside every rank sheet.

### Change control

- F13.6 A rule changes only through a decision page that names the test. Rerun the paired test on the held-out set. Keep the change if the rubric rises and no outcome measure falls.
- F13.7 Every miss goes in a defect log: the event or fact missed, the rule that would have caught it, the proposed rule, and the test. The passage that prompted the claims rules of F5 is the model for a defect entry.
- F13.8 Review the defaults of F8 each quarter against the calibration tables. A default that has never bound in a year is removed.
