---
name: hy-model-standards
description: "Rules for issuer financial features in the HY Analyst: EBITDA basis, free cash flow, credit ratios, LTV, scenario cases, and debt roll-forward. Use when you write or review code in hy/state, hy/forward, or hy/recovery, or edit methodology Sections 4, 5, or 6. Adapted from the global credit-model-standards skill; docs/methodology.md wins on any conflict."
---

# HY Model Standards

These rules apply to the issuer layers of the pipeline: `hy/state` (Section 4), `hy/forward` (Section 5), and `hy/recovery` (Section 6). `docs/methodology.md` is the authority. This skill adds checks that the methodology does not state. It does not replace any formula.

Source of the rules: the global skill `~/.claude/skills/credit-model-standards`. That skill targets private credit Excel models. It has no source card. Treat each rule below as a practitioner claim until a test or a card supports it.

## Rules that apply to every feature

1. Cite the methodology section and formula in the docstring.
2. Read only fields with `available_at` before the decision time. This includes peer multiples, consensus, and ratings.
3. Show debt at face, also when the filing reports it net of OID (original issue discount). Section 4.3 enters senior claims at face.
4. Label units in the field name or schema: `_usd_m`, `_x` for multiples, `_pct`.

## 1. EBITDA basis (Sections 4.1, 4.2, 4.6)

Keep three EBITDA figures apart. Never mix them in one ratio.

| Field | Use |
| --- | --- |
| `ebitda_rep` | Reported figure. Start of the cash check. |
| `ebitda_adj` | Analyst adjusted, by the rule in Section 4.1. Use for leverage, coverage, valuation. |
| `ebitda_covenant` | Per the credit agreement, with all permitted add-backs and synergies. Use only for covenant headroom (Section 4.6). |

**Synergy timing.** Covenant EBITDA counts projected synergies at once. Cash comes only when the synergy shows in reported EBITDA. Store the quarter in which each synergy enters `ebitda_rep`. Before that quarter, the synergy can change `ebitda_covenant` but never FCF.

**FCF start point (decided 2026-10-21).** Section 4.2 starts FCF from `ebitda_adj` and subtracts the cash part of the add-backs. An add-back for a cash charge (for example, cash restructuring cost) raises EBITDA but not cash. See `docs/decisions/2026-10-21-fcf-cash-nonrecurring.md`:

```latex
FCF_t = EBITDA^{adj}_t - CashNR_t - Capex_t - CashInterest_t - CashTax_t - \Delta WC_t
```

Intuition: keep the adjusted earnings level, but charge the cash that the add-backs hid.

## 2. Free cash flow checks (Section 4.2)

1. Split capex into maintenance and growth when the filing allows it. `capex_flex` needs the split. Keep capitalised software as its own line for software issuers.
2. Subtract the sponsor management fee if it sits below reported EBITDA.
3. Cross-check: operating cash flow minus capex from the cash flow statement must be near the waterfall FCF. Write a test that flags a gap above a set tolerance. A large gap means an error in the build or an earnings quality issue (Section 4.1 `eq_flags`).

## 3. Credit ratios (Section 4.3)

Section 4.3 defines leverage, LTV, and coverage. Add these only where the cell needs them:

| Feature | Formula | When |
| --- | --- | --- |
| `fccr` | `ebitda_adj / (cash_interest + mandatory_amort)` | Issuers with amortising term loans in the structure. Most HY bonds do not amortise, so `coverage` is enough for them. |
| `lev_gross` | `total_debt / ebitda_adj`, no cash offset | Beside `net_lev`, to show structural exposure |

Industry add-ons: tangible net worth for asset-heavy or regulated issuers; borrowing base for ABL structures; recurring revenue coverage for software; same-store growth for multi-site issuers.

**LTV moves without leverage.** LTV can rise while leverage stays flat, because peer multiples fall. Example: 6x leverage on a 10x business is 60% LTV. If the sector multiple falls to 8x, LTV goes to 75%. Recompute `ltv_k` each quarter with the current peer multiple (Section 6.1). Never freeze the TEV at origination.

## 4. Scenario cases (Section 5.1)

**Management case direction depends on the market.** In private credit, the sponsor case is usually conservative, to win covenant cushion. In public HY, guidance is usually optimistic; `gap_mgmt` measures the haircut. Do not assume a direction. Measure it per issuer from past guidance against actuals.

**Base case.** Section 5.1 wins: the base case is a coin toss, not conservative by habit. Do not build a "lender case" with a fixed tilt.

**Downside driver comes from the issuer's main risk (Section 4.4).** Never reuse another issuer's template.

| Flag in Section 4.4 | Downside to model |
| --- | --- |
| `cyclicality` | Full down-cycle; revenue fall from the issuer's last recession |
| `customer_concentration` (top customer above 15% to 20%) | Loss of the top customer: revenue, margin, and working capital |
| Single-source supplier | Margins fall to the industry norm |
| Roll-up growth | No acquisitions; organic growth only; integration cost continues |
| Discretionary consumer demand | Demand fall anchored to 2008 to 2009 for comparable issuers |

If no flag stands out, use a general recession anchored to 2008 to 2009.

**Severe downside.** Combine revenue fall, margin squeeze, and working capital stress. Report: the quarter of first covenant breach, peak leverage (`lev_peak_down`), trough FCF, and liquidity runway (`liq_min_down`, `runway_q`).

**Recovery shape.** Tag each downside with one shape. Store it as `recovery_shape`.

| Shape | Path |
| --- | --- |
| `v` or `u` | Cyclical. Back to prior level in 2 to 4 quarters from trough. |
| `structural` | Permanent shift. New lower level; no full recovery. |
| `customer_replace` | Partial or full replacement over 4 to 8 quarters. |

## 5. Debt roll-forward (Section 5.1)

Roll each tranche on its own:

```latex
D_{k,h} = D_{k,h-1} + Draw_{k,h} - Amort_{k,h} - Prepay_{k,h} + PIK_{k,h}
```

Interest per tranche: base rate path `i_h(m)` plus spread, with any rate floor. Split cash and PIK interest. Charge the commitment fee on the undrawn revolver.

Section 5.1 computes interest on `D_{h-1}`. This removes the circular link between interest and cash. Keep it that way. Do not add an iterative solver.

## Tests to write

1. FCF cross-check against operating cash flow minus capex.
2. No ratio mixes `ebitda_covenant` with `ebitda_adj`.
3. A synergy adds to FCF only on or after its realisation quarter.
4. `ltv_k` rises when the peer multiple falls with debt and EBITDA fixed.
5. Debt roll-forward balances per tranche for every quarter.
