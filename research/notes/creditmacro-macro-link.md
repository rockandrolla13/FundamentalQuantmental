# Note: how the creditmacro project links macro to credit

Project: `/media/ak/10E1026C4FA6006E/GitRepos/creditmacro/` (the user's own repo). This is a note, not a source card. It records one method worth reuse and the sources in that repo that bear on Sections 5.2 and 5.4.

## What the project is
A theme-to-trade engine. It turns a research document into a falsifiable theme and ranked strategy families, then stops at a PM memo (`README.md`). It works at the level of a macro theme and a market axis (a spread or slope series), not at the level of an issuer.

## The one method worth reuse: priced-in scenario probabilities
`engine/engine2.py`, specified in `docs/engine2_design.md` §1.5. Given scenarios `s` with an axis value `X_s` (for example an index spread) and our probabilities `p_s`:

```latex
q = \arg\min_{q} \mathrm{KL}(q \,\|\, \text{prior}) \ \text{ s.t. } \sum_s q_s X_s = X_{mkt},\ \sum_s q_s = 1 \quad\Rightarrow\quad q_s \propto \text{prior}_s\, e^{\lambda X_s}
```

```latex
\text{fair value} = \sum_s p_s X_s, \qquad \text{edge} = \langle p - q,\ X \rangle
```

Intuition: `q` is the smallest change to the prior that makes the scenario mix reproduce today's market price. The edge is the gap between our odds and the market's odds, valued at the scenario outcomes. The design notes say `q` is risk-neutral, so the edge is "gross of risk premium" until a pricing kernel maps `q` to physical odds.

**Use for Section 5.4.** Framework F6.9 puts market-implied probabilities first in the fallback order. Today the path masses come from forecast quantiles only. Proposal: for each vintage, tilt the forecast mass `p(m)` to `q(m)` so that `Σ q(m) · hy_oas(m)` equals the current `hy_oas`. Store `p`, `q`, and `⟨p − q, hy_oas⟩` beside the posterior. This is the quantity that Gatto describes in words on p. 536: our recession odds against the market's. Test: over matured vintages, compare the Brier score of the realised path under `p` and under `q`. Expect `q` to over-weight bad paths (risk premium). The size of that gap is a first estimate of `κ_t` at the path level (Section 7.1).

## Other material in the repo
- `research/macro-regime/`: Hamilton (2005) regime-switching survey and Stock and Watson (2002) principal components. Methods to infer a latent macro state. Not carded here. They are the standard alternative to the F6 majority vote, if the vote fails its test.
- `markdowns/Morgan Stanley - Cross-Asset Dispatches — Add to Credit – and How Much Do Markets Lead the Economy - 2020-03-27.md`: over past US recessions, the sequence runs curve flattens, then equities bottom and credit spreads peak, then manufacturing PMI and industrial production trough. Equities bottom about 4 to 5 months before the cycle bottom (Exhibit 14). Sell-side note, in-sample, no test. It says `pmi` lags `hy_oas` at the turn. That matters for the F6 vote and the Section 5.2 logistic: at a turn, the two inputs will disagree for a few months.
- `markdowns/Alaph Long Presentation Version July 2014.md` and `/home/ak/Documents/Macro Liquid Credit.pdf` (same fund deck): a four-quadrant cycle clock on growth against trend and leverage rising or falling (PDF p. 6), with credit quality rotation per quadrant. Marketing material. No method, no numbers that bear on the link.
- `markdowns/CollinDufresne-DeterminantsCreditSpread-2001.md` and `markdowns/Avramov-UnderstandingChangesCorporate-2007.md`: the conversions hold only JSTOR cover text and image placeholders. No body text. Both papers bear on the spread channel of Section 9.2. Get the PDFs and card them in a later sprint.

## Section touched
`docs/methodology.md` Section 5.4 (market-implied path probabilities, F6.9 fallback order) and Section 7.1 (`κ_t`).
