# Factor specs

One page per candidate factor from `research/notes/quant-credit-factor-candidates.md`. The production machine builds each factor from its page. File name: `FNN-<slug>.md`, where NN is the rank in that list.

## Page template
Each page fits on about one printed page (60 to 100 lines). It uses these headings in this order.

1. **Header.** Rank, name, status (NEW or variant of X), tier, sources with file and page, reader block IDs.
2. **Claim.** One falsifiable sentence: what the factor predicts, for which bonds, over which horizon, with which sign.
3. **Definition.** The formula in a LaTeX block, with a one-line intuition. Every parameter with its value: windows, lags, peer groups, scaling, winsorisation.
4. **Inputs.** A table: field, production table and column (`docs/production_wiring.md` section 4 and `docs/data_contract.md`), `as_of`, `available_at` lag rule. Mark each field "have" or "need".
5. **Build steps.** Numbered. From raw table to a score per bond (or per issuer, or per index) per month-end.
6. **Code placement.** Module in `hy/`, function name and signature, the methodology section to cite in the docstring, the output column names. Name the existing functions it reuses.
7. **Tests.** Unit tests: no look-ahead, sign on a synthetic case, edge cases (sparse trades, missing equity, defaulted bonds). Evaluation test: monthly rank IC beyond spread, after costs, positive in at least three of the four cycles (2008, 2015, 2020, 2022). Give the horizon and the pass threshold.
8. **Risks.** Failure modes, overlap with known factors (give the expected correlation if the source states it), cost and turnover.
9. **Open questions.** Choices the source leaves open, with the default we pick and why.

## Rules
- Separate what the source says from what we decide. Label our choices "Our choice".
- Never invent a number. Cite the source page for every number.
- Simplified Technical English. Short sentences, active voice, no semicolons.
