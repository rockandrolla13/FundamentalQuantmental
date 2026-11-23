# What to expect from the HY Analyst agent

Date: 2026-11-23. This page tells you what the agent can do and what it produces when it uses the skills and the workflow of this repository. It also tells you what it cannot do yet.

## The short answer

Expect a research analyst that works like a junior credit team with a strict rulebook:
1. It reads the filings of a high yield issuer and gives a fundamental opinion with a call.
2. It builds and tests models that look for mispriced bonds.
3. It finds and reads the literature, and it writes a card for each source.
4. It turns every finding into a methodology change, code, a test and a decision page.

Do not expect a trading system that you can trust today. Most methods have passed tests on synthetic data, and some have passed backtests. A method counts as proven only when its decision page shows a positive rank IC after costs in at least three of the four cycles: 2008, 2015, 2020 and 2022.

## What you give it and what you get back

### 1. Ask about an issuer
| You give | You get |
| --- | --- |
| A ticker, or several tickers | `scripts/process.py` runs the framework steps in order: frame, normalise, liquidity, claims, cases, value, gate, call. |
| A request for a memo | A plain-English issuer memo from `scripts/memo.py`. The memo opens with the call and carries the claims table of framework F5. It must pass the gate of framework F9. |
| Two issuers to compare | A relative value report from `scripts/rv_pair.py`: lease-adjusted leverage, cost-clock metrics and the bond curves. |
| A question on a covenant, an add-back or a liability management risk | An answer from the credit skills (`covenant-compliance`, `ebitda-addback-treatment`, `credit-memo-standards`), applied to what public filings show. |

### 2. Ask about the market or the cycle
| You give | You get |
| --- | --- |
| "What phase is the credit cycle in?" | A macro read from the `hy-macro` skill: cycle phase, late-cycle votes, path probabilities and case weights. |
| "Which sectors suffer if the Fed hikes and inflation stays high?" | A stress screen (`scripts/rate_inflation_stress.py`) and a per-author answer from the topic skills (`fed-rate-hike`, `credit-cycle`). |
| A market claim of your own | A falsifiable test of the claim. The support-gap method of Section 4.7.3 is the example: your claim became a score, a test and a watch list. |

### 3. Ask for research
| You give | You get |
| --- | --- |
| A methodology section or a gap | A search across journals, working papers and rating agency texts, then a shortlist in `research/notes/`. |
| "Read this paper" | A card in `research/cards/`: claim, method, data, result, limits and the sections it touches, with page numbers. |
| A book | A comparison with Gatto in `research/comparisons/`. That folder is still empty. |
| "Fan out agents" | Several agents search in parallel. You get one merged shortlist with every DOI checked. |

### 4. Ask for a model
| You give | You get |
| --- | --- |
| A model idea, for example fallen angels or peer spreads | A method section with formulas, code in `hy/`, tests, a synthetic script with planted errors and a decision page. |
| A request to backtest | A backtest script with a point-in-time check, rank IC by cycle and HAC t-statistics. |
| A request to explain | An HTML page or a markdown note that walks through the method step by step. |

## How the workflow runs

Every piece of work follows the same chain. Each link leaves a file that you can check.

1. **Question.** One line, tied to one methodology section.
2. **Skills.** A topic skill routes the question to book and paper skills. A skill is a map, not evidence.
3. **Card.** The agent opens the full text and writes a card with page numbers. Only a card or a test counts as evidence.
4. **Methodology.** The finding changes `docs/methodology.md`. Each formula carries its intuition in one sentence.
5. **Code and test.** The code in `hy/` cites its section. A test checks the signs, the caps and that no input comes from the future.
6. **Synthetic check.** A script plants known errors and a placebo. The method must find the errors and find nothing in the placebo.
7. **Decision page.** `docs/decisions/` records the options, the choice, the numbers that decided it and the test that would change it.
8. **Git.** A feature branch, a merge into main at 3 or more commits, the regression and smoke tests, and a push only when you say yes.

## What the agent produces, by folder

| Folder | What you find |
| --- | --- |
| `docs/methodology.md` | The method. Section numbers never change. |
| `docs/framework.md` | The rules for reading a filing. It holds no issuer figures. |
| `docs/decisions/` | One page for each design choice. There are 38. |
| `research/cards/` | One card for each source read. There are 136. |
| `hy/` | One module for each layer: inputs, state, forward, recovery, fair spread, signals, events and outputs. |
| `tests/` | About 1,390 tests. They need no data. |
| `scripts/` | Reports, backtests, memos and synthetic checks. |

## What it does well

1. **It shows its sources.** Every claim points to a card with a page, or to a test.
2. **It records disagreements.** When two sources disagree, it explains the disagreement in plain words, says when each is right and picks one.
3. **It prevents look-ahead.** Every field carries `available_at`, and the code refuses data that was not public at the decision time.
4. **It tests before it trusts.** A new method must find planted errors before it touches real data.
5. **It writes in plain English.** Short sentences, active voice, and one idea for each sentence.

## What it cannot do, or will not do

1. **No vendor data in git.** WRDS, TRACE and Compustat stay on your machine. The repository is public.
2. **No paywalls and no logins.** It does not bypass SSRN, library logins or data rooms. Some facts stay out of reach, for example the guarantee schedule of the Hyperion offering memorandum.
3. **No proven alpha yet for new methods.** The support gap, for example, has run only on synthetic data.
4. **No invented numbers.** If a source does not give a number, the agent labels its own choice "Our choice". Four such numbers exist in Section 4.7.3 alone.
5. **No trades.** The output is a signal, a memo or a watch list. You make the decision.

## How to judge an output

Ask five questions of any result:
1. Does each claim point to a card page or a test?
2. Does the decision page say what would prove the choice wrong?
3. Did the synthetic check find the planted errors and pass the placebo?
4. Is each "Our choice" number marked as one?
5. Did the regression and smoke tests pass after the merge?

If any answer is no, the work is not finished.

## Example requests

1. "Run the process on CRWV and ORCL and write the memos."
2. "Is the market pricing the big-tech label or the contract terms? Build a test."
3. "Find papers on covenant-lite loans and write cards for the best two."
4. "Which HY sectors break if the Fed hikes twice more?"
5. "Explain the fair spread model to me step by step as a page."
