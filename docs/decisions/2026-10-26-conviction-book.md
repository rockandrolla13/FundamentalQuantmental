# Conviction book: a banded, phase-aware, concentrated HY book on top of the systematic factors

Date: 2026-10-26. Status: proposed. Nothing is built and no test has run. Sections touched: methodology Section 3.6 (`cycle_phase`), Section 5.4 (path probabilities), Section 7.3 (conformal band), Section 8 (composite, force rank, `replaces_position`), Section 9 (event risk and limits). Framework F4, F5, F6, F9, F10, F12. Code today: `hy/macro.py` (`phase_vote`), `hy/signals.py` (`composite`, `ic_weights`, `force_rank`, `admit_position`, `adv_cap`), `hy/factors/` (F01 to F30, `REGISTRY`), `hy/backtest.py` (`CYCLE_WINDOWS`, `round_trip_cost`).

## Context

The user wants a book of 15 to 25 issuers with high conviction. The analyst trades it with discretion, and the macro cycle sets its risk. The 30 factors and the signals S1 to S9 supply the candidates.

Four facts from the repo shape the design:

1. S7, the macro sector tilt, failed. The macro part of the sector spread did not predict sector returns (EWC t 1.44 at 3 months). Sector value predicted returns before cost, but lost money after a full round-trip cost (`2026-10-24-s7-sector-tilt.md`). The macro layer has no tested role in name or sector selection today.
2. The analyst ranks bonds, but its predicted returns cannot size positions. The out-of-sample Mincer-Zarnowitz slope is +0.08 (se 0.05) at 6 months, and 1 of 194 monthly fits gives a slope that sizes (`2026-10-23-size-calibration.md`).
3. The best tested peer signal is thin. OneScore has a 6-month rank IC beyond spread of +0.034, and it passes 3 of 4 cycles by a narrow margin (`2026-10-22-onescore.md`).
4. None of the 30 factors has a result on our data. The evaluation runs on the production machine. The current panel starts in January 2010, so the 2008 window is empty (`docs/factors/PRODUCTION_DATA.md` §1).

## What the sources say

**Regime rules and turnover.** Grube Martín-Lunas, Lazcano and Sandubete (2026), *Economies* 14, 268, file `/home/ak/Documents/CreditMacroAnalyst/economies-14-00268.pdf`. Page numbers are PDF pages. The study uses a four-state HMM on weekly European multi-asset data, a CVaR optimiser, and a rebalance every four weeks (pp. 1, 7). The evaluation window is October 2010 to April 2026, 808 weeks (p. 10).

1. The naive regime rule (Regime CVaR-A) turns over 225.8% a year. Static CVaR turns over 21.4% (Table 4, p. 10, and Table 5, p. 10).
2. At 10 bp of cost, the naive rule has a net Sharpe of 0.346. Static CVaR has 0.528 and equal weight has 0.406 (Table 5, p. 10). The naive rule also lost before cost: gross Sharpe 0.365 against 0.530 (p. 9). The authors put the loss on turnover, not on regime detection (pp. 9 to 10).
3. Weight bands per regime keep the scenario set fixed and move only group caps and floors. In stress the equity cap falls to 45% and the defensive floor rises to 30%. In risk-on states the cap is 75% and the floor 10% (p. 7).
4. The bands turn over 29.2% a year, with a net Sharpe of 0.519 at 10 bp (Table 7, p. 11). The text puts this within 0.009 of Static CVaR (p. 12, p. 18). That gap uses the Table 5 static figure of 0.528. Against the Table 7 grid benchmark (0.551 net), the gap is 0.032 (p. 11).
5. No pairwise HAC test is significant. The bootstrap Sharpe intervals span about ±0.4 (Table 6, p. 11).

What this means for us: bands cut the cost of a regime rule to near zero. They did not beat the static book. The paper does not show that regimes add value. It shows how to use them at low cost. The asset class, the frequency and the optimiser differ from ours, so the transfer is an analogy, not a result.

**Value and momentum across the cycle.** Dynkin et al. (2021), card `research/cards/dynkin-et-al-2021-systematic-investing-in-credit.md`. In index drawdowns, ESP (value) is pro-cyclical and EMC (equity momentum) is contra-cyclical (ch. 19, PDF p. 632). With a DTS-neutral leg, both make money in every drawdown episode (PDF p. 632). The evidence is investment grade only. Our HY panel agrees in stress: EMC has a beyond-spread IC of +0.10 in the 2008 window, where ESP has −0.07 (`2026-10-22-onescore.md`).

**Fallen angels and short interest.** Dynkin et al., card `research/cards/dynkin-et-al-2021-chapter-implementations.md`. Fallen angels lose 15.09% against HY peers up to the downgrade month and recover 6.63% over the next 24 months (Table 2.4, PDF p. 121). High equity short interest predicts downgrades and low bond returns in HY and IG (ch. 21, PDF p. 714).

**Odds gap.** creditmacro, `docs/engine2_design.md` §1.5. The priced-in odds `q` minimise `KL(q ‖ prior)` subject to the scenario mix matching the market level. The edge is `⟨p − q, X⟩`. `q` is risk-neutral, so the edge is "gross of risk premium" (§1.5, risk caveat). The repo note `research/notes/creditmacro-macro-link.md` proposes the same tilt for the path masses of Section 5.4. It expects `q` to over-weight bad paths.

**Gates.** creditmacro `engine/scoring.py`, `score_expression`. Gates come before the rank: Ω(τ = 0) ≥ 2, liquidity ≥ 0.40 on creditmacro's own scale, and round-trip cost ≤ 0.33 of expected P&L (the code cites Carver). A thesis with no falsifier is not emitted (`docs/SPEC_AND_STATE.md` §1.3).

**Thesis tracker.** creditmacro `docs/thesis_tracker.md`. One row per ticker holds bull, base and bear prices, their probabilities, the next catalyst and the kill criteria. The tracker never infers a number. It flags a row whose probabilities do not sum to 1.

**Sizing sheets** (`/home/ak/Documents/Quant Credit/`, read with openpyxl. Reader notes: `research/notes/quant-credit-review/out_B.md` lines 25, 26, 314, 315):

1. `Basic Sizing.xlsx`, cell K4: base target P&L per trade in bp = `R × (T/12) × 10^4 / (N × (p − (1 − p)/W))`. R is the target return, T the holding period in months, N the number of trades, p the hit ratio and W the win-to-loss ratio. The sheet's example inputs (R 0.25, T 3, N 10, p 0.6, W 2) give 156.25 bp. These inputs are the sheet's, not ours.
2. `Basic Sizing.xlsx`, cells J8 to J12: conviction 1 to 5 sizes at 1/4, 1/2, 1, 1.5 and 1.75 times the base.
3. `Conviction Sizing Grid.xlsx`, rows 18 to 25: optimal target P&L = `TotalPnL × turnover / ((1 + h) L − h)`, with h the hit ratio and L the loss severity. The formula turns negative when `(1 + h) L < h` (row L = 0.4, cells C25 to E25).
4. `Conviction Sizing Grid.xlsx`, cell F31: "Historically between 60-70% hit ratio and loss severity of 50-60%". The sheet gives no source for that history. We treat it as a claim to test.

**Breadth.** Grinold's rule of thumb: IR ≈ IC × √breadth. No card in the repo covers it. We use it as a rule of thumb, not as a result. Breadth counts independent bets a year, not names. Correlated names and long horizons cut it.

## What the data says

No data yet. The playbook table, the agreement rule, the bands and the tiers below have no result on our panel. The only phase-relevant results are the S7 failure, the OneScore stress windows, and the ESP stress failure in HY (2008 −0.05, 2020 −0.17 beyond spread, Dynkin card, "What our data says").

## Options

1. **(a) Fully systematic composite.** Section 8 and framework F10 as written: IC weights per phase, the force rank over the whole universe, and ADV caps. It has the most breadth and no analyst cost. It does not give the concentrated, discretionary book the user asked for. It also has no test result yet.
2. **(b) Regime switching that rebuilds the book.** On each phase change, swap the factor set and rebuild the book. Grube et al. show this design loses to a static book before and after cost, at about ten times the turnover (Table 5, p. 10). Our own macro layer has no tested predictive power (S7).
3. **(c) Banded conviction book.** The phase sets a band for total risk. Risk moves inside the band one step at a time. The factors pick names. Conviction comes from agreement across independent families and from the F9 gate. A shadow book of option (a) runs beside it.

## Choice

Option (c). It is the only option that gives the user's book and keeps a falsifier beside it. The shadow book is option (a), so (a) stays alive as the comparator. Option (b) is rejected on the turnover evidence. The bands come from Grube et al. That paper shows bands cost little, not that they add value. So the test below includes a static-band arm. If the static band does as well, the phase layer goes.

One correction to the lead's proposal: creditmacro does not set the cycle phase. Its product stops at a PM memo and emits no sizes (`README.md`, `SPEC_AND_STATE.md` §1.1). The phase comes from `hy.macro.phase_vote` (framework F6). creditmacro supplies three parts: the odds-gap method, the gates, and the thesis tracker.

### Layer 1. Phase band (candidate replacement for S7)

1. **Phase.** `cycle_phase` from `hy.macro.phase_vote`: six indicators, five phases, with the repair and recovery rule on the way down (framework F6, methodology Section 3.6).
2. **Odds gap.** For each vintage, tilt the forecast path mass `p(m)` of Section 5.4 to `q(m)` so that `Σ q(m) · hy_oas(m)` equals the current `hy_oas`. Store `p`, `q` and `edge = ⟨p − q, hy_oas⟩`. Intuition: the edge says how far our recession odds sit from the market's odds, in spread terms.
3. **Use the gap as a z-score.** `q` is risk-neutral and carries the risk premium. A raw gap will then look bullish in most months. Our choice: standardise the edge against its own expanding history, with `available_at` before the decision time.
4. **Band per phase.** Each phase has a band `[DTS_lo, DTS_hi]` for total book DTS against the HY index DTS. It also has a band for the rating mix (BB, B, CCC shares). The user sets the band levels on a later decision page. This page sets none.
5. **Position inside the band.** The odds-gap z-score sets the target point inside the band. A positive gap (we see less recession risk than the market) moves the target toward `DTS_hi`.
6. **Step rule.** Book DTS moves toward the target by at most one step per rebalance. A phase change moves the band, not the book. The book then walks into the new band step by step. It never flips. This is the turnover lesson of Grube et al. (pp. 10 to 12).
7. **Sector tilts.** S7 failed, so layer 1 carries no macro sector tilt. Sector value (η alone) stays a backlog candidate with a turnover-based cost (`2026-10-24-s7-sector-tilt.md`). The index-timing factors F25 to F30 are inputs to the band target only after each one passes its own spec test. F25 has synthetic evidence only (`docs/factors/F25-credit-bmi.md` §1).

### Layer 2. Phase playbook: which factor families to trust

Families (our choice). Each factor gets one family in its `META`.

| Family | Members |
| --- | --- |
| Value | S1, ESP (E14), F02, F06, F22, F24 |
| Momentum | EMC (E16), F03, F04, F18 |
| Flow | S6, F05, F12, F14, F15 |
| Fundamentals | S2, S3, F07, F09, F19, F21, F23 |
| Event risk | S5, F08, F11, F16, F17, F20 |

F01 (IPCA) is an aggregator, not a family member. F10 (carry) and F13 (illiquidity) feed the cost and carry terms and do not count as a family vote, because carry tracks spread level, which value already holds. F25 to F30 are index level and feed layer 1 only.

The playbook below is a **hypothesis to test per phase**. It is a prior over the weights `w_{j,phase}` of Section 8. Once a family has a per-phase IC, the fitted weights of Section 8 replace the prior.

| Phase | Trust (proposal) | Risk stance | Evidence today |
| --- | --- | --- | --- |
| Expansion | Momentum (F04 vol-adjusted, F03), flow, carry (F10). BB and B | Upper part of band | F04 works in BB and B where raw momentum fails (van Zundert 2017, candidates list rank 4). Raw 6-month bond momentum reverses, Sharpe −0.84 (A2-F8). No phase split in any source |
| Late cycle | Fundamentals (F21, F09), event risk (F08 as a warning), up in quality | Cut risk toward `DTS_lo` | Gatto names late-cycle markers (p. 355, methodology 3.6). 63% of LBO targets scored 7.5 or more on LEVER, against 25% of non-targets, S&P 1500, 1995 to 2005 (F08 spec, Lehman 2006 p. 15). F21 has no backtest |
| Downturn | Defensive, short duration. F05 flow reversals. EMC and F03 | Bottom of band | EMC is contra-cyclical in drawdowns (Dynkin p. 632). EMC +0.10 in our 2008 window. F05 evidence is the 2013 Taper Tantrum, not a downturn (F05 spec §3) |
| Repair | Fallen angels. F05 and S6 flow reversals | Step up from the bottom | Fallen angel recovery +6.63% over 24 months (Dynkin Table 2.4, PDF p. 121). Needs ratings after February 2017. No fallen-angel module exists |
| Recovery | Value (ESP, F02, F24). B and CCC | Upper part of band | ESP is pro-cyclical (Dynkin p. 632). ESP fails in HY stress (2008, 2020). That fits a value premium in recovery. Nobody has tested it per phase |

Where the sources disagree: the lead puts momentum in expansion. Dynkin and our 2008 window put equity momentum (EMC) in drawdowns. Both can hold, because bond momentum (F04) and equity momentum (EMC) are different signals. The table keeps EMC in the downturn row and F04 in the expansion row. The per-phase IC test decides.

### Layer 3. Conviction: entry rules

A long candidate enters the book only when all of these hold. A short takes the mirror rules.

1. **Agreement.** At least 3 of the 5 families agree in sign. A family agrees when its score (the mean of its standardised member scores) sits in the top tercile of the universe for that date. The tercile cut is our v0 choice.
2. **Fair value.** The S1 residual sits outside its conformal band: `z > q_{1−α}` (methodology Section 7.3).
3. **No warning flag.**
   - LEVER in the top category of F08 (top 20%, F08 spec).
   - Thin refinancing headroom: F21 `fails_at_zero` is true, or `wall_cover_4` is below 1 (framework F4, red).
   - High equity short interest (Dynkin ch. 21, PDF p. 714). No short-interest panel exists yet.
4. **Memo.** A full memo (framework F12) passes the F9 gate G1 to G9. It carries the F5 claims table, a catalyst with a date (G2), an invalidation observable (G8) and an exit (F10 state machine).
5. **creditmacro gates.** Compute Ω(0) over the p-weighted scenario P&L `ΔP_i(o, m)` of Section 9.2. Require Ω ≥ 2. Require round-trip cost ≤ 1/3 of the expected convergence return (Section 7.5). We use the F10.4 ADV cap in place of creditmacro's liquidity score, because the 0.40 floor sits on a different scale.
6. **Thesis-tracker row.** Bull price = upside case. Base = base case. Bear = the probability-weighted price of the two downside cases of F6 (our mapping, because F6 has four cases and the tracker has three). Kill criteria = the G8 invalidation. The row must show `probability_check = OK`.
7. **`replaces_position`.** Every entry names the position it replaces (framework F10.6, `hy.signals.admit_position`).

Discretion: the analyst may reject a candidate that passes, or cut its tier by one. The analyst may not add a name that fails a rule. Every such act goes in the override log.

### Sizing

1. **Base.** `Basic Sizing.xlsx` K4 formula, with N = the target name count and p, W from our own realised record once it exists. Until then, p and W are user inputs, logged as fallbacks (framework F6.9).
2. **Tier.** Tier = number of agreeing families: 3 gives tier 3 (1 × base), 4 gives tier 4 (1.5 ×), 5 gives tier 5 (1.75 ×) (`Basic Sizing.xlsx` J8 to J12). Tiers 1 (1/4 ×) and 2 (1/2 ×) are the entry and exit steps. A new name enters at tier 1 and steps up one tier per rebalance. This mapping is our choice.
3. **Caps**, in this order:
   - Jump-to-default: `n_i × (P_i − 100 R_i^{adj}) / 100 ≤ j × NAV` (methodology Section 9.3). This refines the lead's `size × (1 − recovery)`. It measures the loss from today's price, not from par. The user sets `j`.
   - Liquidity: `n_i ≤ k × ADV_i`, with k = 5 days to exit as the default (framework F10.4, `hy.signals.adv_cap`).
   - Band gate: scale by `1 / (q_α,t × σ_x)` (Section 9.4, F10.5).
   - Regime jump-to-default limit `g(w_down(m_t))`, decreasing (Section 9.4).
   - Total book DTS inside the phase band. Scale all names pro rata when the sum is above `DTS_hi`.
4. **Conflict with the size calibration.** That page sizes at the minimum when the slope of realised on predicted return is not above 0 by two standard errors. The tier rule sizes by agreement count, not by predicted return, so the two rules do not collide directly. The tier multipliers still need their own test (T4). If realised return does not rise with tier, all tiers flatten to 1 × base.

### Book shape and the two companion pieces

Both companion pieces are planned work and are not on disk at the time of this page.

1. **Market-neutral core:** `hy/sector/`, spec `docs/factors/SECTOR-models.md`. Sector-specific models and within-sector long-short pairs. The pairs carry near-zero net DTS, so they sit outside the phase band. Pair legs size by jump-to-default, not by DV01 (methodology S4 trap, p. 530).
2. **Directional leg:** `hy/quality/`, spec `docs/factors/QUALITY-rotation.md`. Up-in-quality and down-in-quality expressions: long the cheapest high quality, short the richest low quality. The phase band sets the net DTS and the rating tilt of this leg. It is the main tool that moves book DTS inside the band.
3. **Conviction names:** the 15 to 25 issuers of layer 3. Pair legs and quality-basket legs do not count toward the 15 to 25 (our choice).

### Shadow book

1. Run the full systematic composite (option (a)) every rebalance, with the same universe, costs and caps.
2. Log every difference between the books: name, side, tier, date, the rule or reason, and the shadow book's position.
3. After 12 months, compare net excess return after costs. If the conviction book does not beat the shadow book, raise the machine's share. This rule comes from the lead's proposal.
4. Twelve months has low power. Grube et al. report Sharpe intervals of about ±0.4 over 808 weeks (p. 11). So the 12-month review also scores each override on its own P&L against the shadow position. The machine's share rises when the override P&L is not above zero.

### The breadth trade-off

IR ≈ IC × √breadth (Grinold, rule of thumb). From about 200 names to about 20 cuts √breadth by √10 ≈ 3.2. The 200 is the lead's figure for the shadow book, not a measurement. To keep the same IR, the conviction book needs about 3.2 times the IC per name. For scale: OneScore's 6-month beyond-spread IC is +0.034, so the target is about +0.11. That gain must come from analyst work: the memo, the claims view and the gate. The factors cannot supply it alone, because the shadow book already holds them.

## The test that settles it

Run on the production machine, with history from 2004 (`PRODUCTION_DATA.md` §1), the windows of `hy.backtest.CYCLE_WINDOWS` (2008, 2015, 2020, 2022), and costs from `hy.backtest.round_trip_cost`. Freeze every parameter on a decision page before the run.

Arms:

1. A. Shadow book: option (a).
2. B. Conviction book, rules only: layers 1 to 3 with no discretion. Discretion cannot be backtested, so B tests the rules.
3. C. Static band: arm B with the band fixed at its mid point in every phase.
4. D. Regime rebuild: option (b). This is the negative control.

Pass rules:

- **T1 Book.** B beats A in net excess return in at least 3 of 4 windows. Else the conviction rules add nothing over the machine.
- **T2 Phase layer.** B beats C in at least 3 of 4 windows. Else layer 1 goes, and the book runs on a static band. This follows the Grube result.
- **T3 Turnover.** The one-way annual turnover of B is not above that of A. D shows the turnover cost of a rebuild. If D beats B after cost, reopen option (b).
- **T4 Tiers.** Mean net excess return rises with tier, and the realised hit ratio and loss severity are reported against the grid note (60–70%, 50–60%). Not monotone: flatten the tiers.
- **T5 Playbook.** For each family and phase, compute the rank IC beyond spread after costs. A cell of the table stays only when that IC is above 0 and above the family's IC in the other phases. A phase with fewer than 24 months in the sample is marked "untestable". The 24-month floor follows the size calibration page. Five phases over four windows give few episodes per phase, so expect several untestable cells.
- **T6 Independence.** Report the mean pairwise rank correlation of the five family scores. Two families above 0.5 (our v0) merge into one vote.
- **T7 Odds gap.** Over matured vintages, compare the Brier score of the realised path under `p` and under `q` (`creditmacro-macro-link.md`). The band target uses the gap only if `p` scores better.
- **T8 Live.** The 12-month shadow comparison and the override score above.

## Follow-ups (what must be built)

1. `hy/macro.py`: the KL tilt from `p(m)` to `q(m)`, and `edge`, stored beside the posterior of Section 5.4. No code for it exists in `hy/` today.
2. A family key in each factor's `META`, and family scores per date. Proposed module `hy/conviction.py`: agreement count, warning flags, gates, tiers, caps, override log.
3. Proposed module `hy/bands.py`: phase bands, odds-gap target, step rule, DTS and rating-mix checks.
4. An evaluation runner for per-phase IC by family. No runner exists (`PRODUCTION_DATA.md`).
5. Data: history from 2004, the `ratings` panel, a new `short_interest` panel, `macro_series`, `bond_terms` (`PRODUCTION_DATA.md` §1 to §4).
6. A fallen-angel factor (Dynkin ch. 2). No module exists.
7. A shadow-book runner, and schemas for the override log and book state in `data/schemas/`.
8. A thesis-tracker adapter that writes one bond row from the F6 cases.
9. The companion pieces `hy/sector/` and `hy/quality/` with their spec pages.
10. A source card for Grinold's rule, and decision pages for the band levels, `j`, and the tercile cut.
11. After T1 to T6: a new subsection "Conviction book" in methodology Section 8, and the matching rules in framework F10 and F12.

## Open

- The band levels, the step size and `j` have no source. The user sets them.
- The 60–70% hit ratio and 50–60% loss severity on the grid have no stated history.
- creditmacro failure mode 5 is open: "External context missing" (`SPEC_AND_STATE.md` §2.5). Discretion without current data carries the same risk. The memo gate and the event calendar are our guard.
