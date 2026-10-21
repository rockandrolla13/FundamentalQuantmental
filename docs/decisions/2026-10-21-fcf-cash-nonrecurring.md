# FCF: charge the cash part of nonrecurring add-backs

## Context
Section 4.2 started FCF from `ebitda_adj`. Section 4.1 builds `ebitda_adj` by adding back nonrecurring items. Some of those items consume cash, for example a cash restructuring charge. The global skill `credit-model-standards` starts FCF from reported EBITDA for this reason.

## Options
1. Start from `ebitda_adj`, as before. This overstates cash in quarters with cash one-off charges.
2. Start from reported EBITDA. This understates the recurrent cash level, because non-cash charges then reduce FCF.
3. Start from `ebitda_adj` and subtract `CashNR_t`, the cash part of the items added back.

## Choice
Option 3:

```latex
FCF_t = EBITDA^{adj}_t - CashNR_t - Capex_t - CashInterest_t - CashTax_t - \Delta WC_t
```

It keeps the earnings level of option 1 and the cash truth of option 2. The data already supports it: Section 3.2 stores a cash flag on each nonrecurring item.

## Test
`tests/test_state.py::test_cash_nonrecurring_counts_only_added_back_cash_items`: only items that are added back and flagged as cash enter `CashNR_t`. The test passes.

Open test on real data: on issuers with large cash restructuring charges, option 3 must track operating cash flow minus capex more closely than option 1.

Changed: `docs/methodology.md` Section 4.2 (and the root copy), and `.claude/skills/hy-model-standards/SKILL.md`.
