# CLAUDE.md — HY Analyst

## Mission
Build a best-in-class high yield bond analyst. The system finds mispriced bonds from issuer fundamentals, forward estimates, and macro forecasts. It outputs quantamental signals and event-driven positional risk. Judge every piece of work against that mission.

## Start here
1. `docs/methodology.md` is the spine. Its section numbers are canonical. Extend sections; do not renumber them.
2. `docs/framework.md` is the rulebook. Apply it to every filing in order: frame, normalise, size liquidity, size claims, build cases, value, gate, then call. It holds rules only; no issuer figures ever enter it.
3. Gatto, *The Credit Investor's Handbook* (Wiley, 2023) is the base process. Page numbers in the methodology are PDF pages of that file.
4. `research/reading-list.md` holds the comparison books and the seed papers.
5. `docs/decisions/` holds one page per design decision: context, options, choice, and the test that settles it.

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
- Tests cover: monotone signs in the fair spread model, conformal coverage per cell, PD calibration by rating, no look-ahead, and the claim rules of `docs/framework.md` F5 on synthetic lease schedules.
- Vendor data stays out of git. Schemas live in `data/schemas/`.
- Notebooks explore. Code lives in `hy/`. A result counts only when a test or a script reproduces it.

## Style
- Write all prose in ASD-STE100 Simplified Technical English: short sentences, active voice, imperative for instructions, no -ing verb forms, no slashes.
- No filler. Only the context the reader needs to act.
- Apply the Communication Style rules below to every report: memos, write-ups, decision pages, research cards, and the prose that scripts such as `scripts/memo.py` generate. Where these rules and STE differ, follow the stricter rule.

## Communication Style (always on)

**Scope.** These rules govern prose: explanations, answers, summaries, markdown documents, and reports (LaTeX and PDF). They do not govern code, commands, file paths, identifiers, callout syntax, or text that must reach the reader unaltered. Signoff quotes and verbatim extraction blocks stay byte-exact.

### Sentences
- Cap an instruction at 20 words and an explanation at 25. Split anything longer.
- Get under a cap by splitting, never by deleting. Keep every subject, verb, and article.
- One instruction, or one claim, per sentence.
- No semicolons. Write two sentences.

### Verbs
- Use the active voice and name the actor: "the linter rejects the file", not "the file is rejected".
- Keep the passive where the actor is genuinely unknown. An invented actor asserts a cause you cannot support.
- Use simple tenses: "the run failed", not "the run has failed". EXCEPT where the compound carries doubt: "may have failed" keeps its auxiliary, or the hedge is deleted with it.
- Prefer the one-word verb: "configure" over "set up".
- Put the action in the verb: "verify X", not "perform verification of X".

### Words
- Use one term per concept. Do not rotate directory/folder or verify/validate/confirm.
- Prefer the short common word: "use" over "utilize".
- Keep the exact technical term your project already uses, and define it at first use. Precision outranks brevity.
- Cut words that claim quality instead of showing it: robust, seamless, powerful, comprehensive, elegant, streamlined, cutting-edge. Give the measurement.

### Honesty
- Keep real uncertainty in one modal: "the build may fail". Never stack hedges ("might possibly", "could perhaps generally").
- Never promote a hedge to a fact, and never soften a fact into a hedge.
- Never invent a cause, frequency, or mechanism to make a sentence read better.

### Structure
- Lead with the answer or the finding. Put the context after it.
- One topic per paragraph, six sentences at most. Open it with its topic sentence.
- Use a list for three or more items, steps, or conditions.
- Keep a summary proportional: a one-line change gets a one-line summary.

These are targets, not a straitjacket. Stop where the sentence cannot be misread, not where it is shortest.

## Definition of done for the analyst
- Every claim traces to a source card or a test.
- Every memo passes the gate of `docs/framework.md` F9 and carries the claims table of F5.
- PD is calibrated by rating and by cycle phase.
- Conformal coverage holds in every rating and liquidity cell.
- Each signal has a positive rank IC after costs in at least three of the four cycles: 2008, 2015, 2020, 2022.
- Every position carries `replaces_position`.
- The event model's probability integral transform is near uniform.
