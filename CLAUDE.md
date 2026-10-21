# CLAUDE.md — HY Analyst

## Mission
Build a best-in-class high yield bond analyst. The system finds mispriced bonds from issuer fundamentals, forward estimates, and macro forecasts. It outputs quantamental signals and event-driven positional risk. Judge every piece of work against that mission.

## Start here
1. `docs/methodology.md` is the spine. Its section numbers are canonical. Extend sections; do not renumber them.
2. Gatto, *The Credit Investor's Handbook* (Wiley, 2023) is the base process. Page numbers in the methodology are PDF pages of that file.
3. `research/reading-list.md` holds the comparison books and the seed papers.
4. `docs/decisions/` holds one page per design decision: context, options, choice, and the test that settles it.

## How to think
- Treat every prompt as `ultrathink`. Reason at full depth before you write code or prose.
- State the assumptions first. Put the intuition in one sentence beside each formula.
- Prefer a falsifiable claim with a test over a description.
- When two sources disagree, record both, state when each is right, choose one, and say why.
- Separate three things in every note: what the source says, what the data says, what we decide.

## Research protocol
1. Pick one methodology section. Write the question in one line.
2. Search in this order: peer-reviewed journals, working papers (SSRN, arXiv q-fin), rating agency methodologies, practitioner books, sell-side primers. Open the source. Never cite a snippet.
3. Write one card per source in `research/cards/<slug>.md`: claim, method, data, result, limits, section touched.
4. Write one comparison per book in `research/comparisons/<book>.md` with a fixed structure: where it agrees with Gatto, where it disagrees, what we adopt, the test that settles the rest.
5. End each sprint with a change to `docs/methodology.md` and a decision page. A finding that changes no section is not finished.

## Engineering rules
- Python 3.12. Package `hy/` with one module per methodology layer: `inputs`, `state`, `forward`, `recovery`, `fairspread`, `signals`, `events`, `outputs`.
- Every field carries `as_of` and `available_at`. A model reads only fields available before the decision time. A test enforces this.
- Every feature function cites its methodology section and formula in the docstring.
- Tests cover: monotone signs in the fair spread model, conformal coverage per cell, PD calibration by rating, and no look-ahead.
- Vendor data stays out of git. Schemas live in `data/schemas/`.
- Notebooks explore. Code lives in `hy/`. A result counts only when a test or a script reproduces it.

## Style
- Write all prose in ASD-STE100 Simplified Technical English: short sentences, active voice, imperative for instructions, no -ing verb forms, no slashes.
- No filler. Only the context the reader needs to act.

## Definition of done for the analyst
- Every claim traces to a source card or a test.
- PD is calibrated by rating and by cycle phase.
- Conformal coverage holds in every rating and liquidity cell.
- Each signal has a positive rank IC after costs in at least three of the four cycles: 2008, 2015, 2020, 2022.
- Every position carries `replaces_position`.
- The event model's probability integral transform is near uniform.
