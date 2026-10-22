HY Analyst: one combined framework Four groups of method, one pipeline, one expected alpha 

## FundamentalQuantmental repository 

22 October 2026 

## **Summary** 

1. This document defines one framework for one analyst. It merges four groups of method into a single pipeline of fifteen steps, plus a size calibration step. 

2. The four groups are: **G1** the core process (Gatto’s seven steps, the methodology, the framework rules, and the relative value PDF); **G2** the methods the code already runs; **G3** seven credit skills, written for private loans and adapted here to public bonds; and **G4** two books, Kricheff and Ganguin and Bilardello (S&P). 

3. The analyst loads data stamped with the date it became public, frames the business, cleans earnings, and measures liquidity, claims, covenants, and the gap between fixed charges and signed contracts (the two clocks). 

4. The analyst then projects the issuer under five macro stories, values the firm and each bond’s recovery, and finds the spread each bond should pay. 

5. All of this becomes one number: expected alpha, the six-month return of a hedged long after default loss and cost. The weights are the user’s: 45% on the core process, 20% on the two clocks, and 11.67% each on the rest of the built methods, the skills (which can only lower the number), and the books. 

6. The code now charges default loss on the price paid, not on face value. In the gate, the row that turned spread into a default probability no longer votes. A breakeven-default row votes instead: the default rate at which the spread only pays for its loss. 

7. The severe-case runway now funds committed capex, so it no longer hides the cash burn of growth commitments. 

8. The size calibration is built. The backtest slope is 0.079 (standard error 0.054). That is not reliably above zero, so the number ranks issuers but does not size positions. 

9. The decision against cash (S15) is built. It compares each bond with every other use of the same money, cash included, and names the position it would replace. Only this step may say “buy”. 

10. Real gaps remain. The claims, recovery and covenant work is only partly wired into the pipeline. Credit lines are untagged in the filings, so revolver capacity is missing. Gate rules G4, G5, G7, G8 and G9 are not built. 

**What this means for you.** The ranking is usable; the sizes are not. Under the earlier weights CoreWeave showed a raw alpha of +145 bp a year after cost, and +11 bp after calibration. The new weights lean on the core rules and the clocks, where CoreWeave scores poorly, so its figure is likely to fall. Agent one is rerunning; read the new figures in the memo, not here. 

## **The single analyst pipeline** 

*(Figure: see the PDF.)*

**----- Start of picture text -----**<br>
SEC filings Compustat TRACE trades Treasury curve Forecast registry<br>XBRL and text point in time<br>S1 Load<br>every field stamped with available_at<br>S2 Frame S3 Earnings S5 Claims S6 Two clocks S8 Value<br>archetype, three EBITDAs, debt, leases, charges vs<br>TEV, recovery<br>business risk add-backs covenants contracts<br>S9 Relative fair spread S7 Stories and cases S4 Liquidity<br>value<br>fair line, pair 5 macro paths × cases; PD runway, wall, gap<br>S10 Expected S13 Metrics<br>alpha S11 Gate S12 Events S15 Decision<br>panel<br>carry, convergence, price against view and monitoring bands by group against cash<br>loss<br>S14 Combined view → S14b Size calibration<br>weights: G1 45%; clocks 20%; G2 rest, G3 (one-way), G4 11.67% each<br>S1 feeds every step; S13 and S14 read every step; S6 also feeds S9<br>built partial not built (pair) and S14 (E5). S7 runs before S4, because the liquidity step<br>reads the case statistics. Only S15 may say “buy”.<br>**----- End of picture text -----**<br>


**How to read it.** One analyst runs every step, in order, for each issuer. The four groups do not run as separate pipelines. Each group adds rules, metrics or checks to the same steps. The last three steps turn the results into a decision: 

- S14 combines all the estimates into one number, the expected alpha. Expected alpha is the six-month return of a hedged long position after default loss and the cost to buy and sell. 

- S14b scales that number down to the size that history supports. 

- S15 compares the bond with every other use of the same money, cash included. 

2 

## **The four groups** 

|Group|Sources|What it brings to the one framework|Role in the score|
|---|---|---|---|
|**G1** Core|Gatto, _The Credit Investor’s_|The order of the steps; the rules (point in time,|45% of the score (E4,|
|process|_Handbook_ (2023);|two views, claims sizing, the gate); the formulas;|E7–E10); the loss on|
||`docs/methodology.md`;|the PDF’s decision against cash and its strict|price; the gate; size|
||`docs/framework.md` F1–F13;|rules on PD, loss and averaging|calibration; the|
||relative value PDF via||decision|
||`research/hyrv_extract.md`|||
||and|||
||`research/hyrv_mapping.md`|||
|**G2** Built|Two clocks (M4.7,|Working code on real data for eight issuers; the|Two clocks (E5):|
|methods|Radhakrishnan card); fair line|only measured evidence (the backtest)|20%; the rest|
||and pair||(E0–E3, E6): 11.67%|
||(`scripts/rv_pair.py`);|||
||stories and forecast sources|||
||(`hy/macro.py`,|||
||`hy/forecasts.py`, eleven|||
||forecast cards); cases and|||
||alpha|||
||(`scripts/scenarios.py`,|||
||`hy/alpha.py`); F9 gate, F8|||
||panel, combined view|||
||(`scripts/process.py`); the|||
||backtest (`hy/backtest.py`)|||
|**G3**|`hy-model-standards`;|Practitioner rules: three EBITDAs, add-back|11.67%, one-way|
|Skills|`credit-model-standards`;|push-back thresholds, FCF cross-check, covenant|(E11); E7 is one-way|
||`credit-memo-standards`;|headroom and trajectory, watchlist tiers, debt|but counted in G1|
||`ebitda-addback-treatment`;|bridges. Written for private loans; where a rule||
||`covenant-compliance`;|does not transfer to public bonds, the step says||
||`borrower-monitoring`;|so||
||`quarterly-package-`|||
||`extraction`|||
|**G4**|Krichef, _A Pragmatist’s_|Krichef: cash-fow underwriting, spread per|11.67%: cross-checks|
|Books|_Guide to Leveraged Finance_;|turn and its trap, covenant capacity, event pro|E12 (S&P score gap),|
||Ganguin and Bilardello,|formas, recovery timing. S&P: business risk|E13 (spread per|
||_Standard & Poor’s_|grading, analytical adjustments (leases,|turn)|
||_Fundamentals of Corporate_|pensions), ratio medians by rating, stress and||
||_Credit Analysis_ (2005)|default cases, recovery method||



**Out of scope.** The other reading-list books are not available locally and add nothing here: Fridson and Alvarez; Moyer; Altman, Hotchkiss and Wang; Whitman and Diz; Lando; Duffie and Singleton; Marks. The seed papers are dropped. 

**Source notes.** The Kricheff markdown lost the contents of every table; only numbers quoted in the text survive. Both books contain a few arithmetic slips (Kricheff Ch. 10 and 16; S&P Ch. 9, 10 and 11); this document does not copy them. Book page numbers are not used; chapters are. 

**How to read a step.** Each step gives, in order: purpose; what each group contributes; one merged algorithm; metrics with symbols and intuition; bands; inputs (data, documents, analyst); outputs; where groups disagree and which rule wins; the settling test; status in the code; and a short CoreWeave (CRWV) example from `data/raw/process/CRWV.json` . Status: **Built** means the code computes the step’s main output on real data; **Partial** means part of it, and the step names what is missing; **Not built** means no code runs it. Labels: “M4.3” is a methodology section; “F5” a framework rule; “E31”, “R49”, “P11”, “U17” are relative value PDF items; “C”, “K” and “B” are rows of the conflicts register (Section 18). 

3 

## **G1 Core process** 

**In one line.** G1 sets the order of the steps and the rules that every number must obey. It carries 45% of the score, the largest share. 

## **What it is** 

G1 is the base process and the rulebook. It has four sources: 

- Gatto, _The Credit Investor’s Handbook_ (Wiley, 2023). Its seven steps, Chapters 6 to 13, give the order of the analysis. 

- `docs/methodology.md` , sections M1 to M11. It gives the formulas: cases, recovery, fair spread, alpha and validation. 

- `docs/framework.md` , rules F1 to F13. It gives the rules: point in time, claims sizing, the gate and the memo. 

- The relative value PDF, read through `research/hyrv_extract.md` and `research/hyrv_mapping. md` . It adds the decision against cash and strict rules on default, loss and averages. 

## **Why it is in the framework** 

Without G1, the other groups have no common order and no common rules. G1 also holds the two hard stops. The S11 gate can block any call. Only S15 may say “buy”. 

**What it adds at each step** 

|Step|G1 contribution|
|---|---|
|S1 Load|Every feld carries `as_of` and `available_at`. A memo dated _t_ reads nothing released after _t_.|
||TRACE prices are estimates, not quotes.|
|S2 Business|Gatto step 2: industry risks, strategy, management. F2: fve lines and one archetype A1 to A8.|
|S3 Earnings|Gatto step 3a: remove one-of items. F3: keep three EBITDAs apart. Add-back classes C1 to C10.|
|S4 Liquidity|Gatto step 3b: liquidity, maturities, access to refnance. F4: efective liquidity, runway, the wall,|
||the refnance score.|
|S5 Claims|Gatto steps 3c and 6: the capital structure table and the covenants. F5: size every claim, leases|
||included.|
|S6 Clocks|M4.7: the formulas and fve rules. Gatto has no such measure.|
|S7 Cases|Gatto step 4: base and downside cases. M5: the case engine under each macro path.|
|S8 Value|Gatto step 5: comparables, DCF, liquidation. M6 and F7: value, waterfall, recovery.|
|S9 Relative value|Gatto step 7: risk is PD times LGD. M7.2: the fair spread.|
|S10 Alpha|M7.5: carry, convergence, loss and cost. The PDF: reprice each path with default inside the cash|
||fows.|
|S11 Gate|F9: rules G1 to G9. A wide spread never waives an open step.|
|S12 Events|M9 and F11: the event list and the playbooks.|
|S13 Metrics|F8: formula, unit, direction and bands for every metric.|
|S14b Size|M11: check every forecast against what happened.|
|S15 Decision|The PDF, Step 7: compare the bond with every other use of the money, cash included.|



4 

## **Its estimates in the score** 

G1 holds five estimates. They share its 45%. 

|ID|Estimate|How the code computes it|Weight|
|---|---|---|---|
|E4|Default the price|(_PDκ −PDfund_)_Ldef_. The code shows it but does not count it until|0%|
||assumes|_κ_ is ftted (confict C2).||
|E7|Earnings quality|Minus the count of F3, add-back and FCF-check fags. It can only|11.25%|
|||lower the number.||
|E8|Liquidity and|F4 score on the likely path, plus wall cover (cap 3), plus one point if|11.25%|
||refnancing|no funding gap.||
|E9|Market value check|Minus debt over market enterprise value.|11.25%|
|E10|Excess over cash|_µ/H_ from S15: the expected gain over cash, per year.|11.25%|



## **What it says about the eight issuers** 

*(Figure: see the PDF.)*

**----- Start of picture text -----**<br>
0 largest driver<br>CRWV +246 E10 +1289<br>ORCL +92 E9 +297<br>HCA +47 E9 +124<br>THC +22 E9 -106<br>CCL +72 E10 +154<br>NCLH -58 E10 +445<br>MGM -4 E7 -167<br>WYNN -22 E9 -178<br>bucket alpha, bp a year before cost<br>**----- End of picture text -----**<br>


- G1 is positive for five of the eight issuers. The values run from _−_ 58 to +246 bp a year. 

- E10 has the widest range of any G1 estimate, from _−_ 32 to +1 _,_ 289. So E10 sets the size of the bucket for most issuers. 

- CRWV ranks first because its bond yields far more than cash (E10 +1 _,_ 289). Its weak liquidity score (E8 _−_ 326) takes back part of that. 

- NCLH ranks last. It has an earnings-quality flag, a weak liquidity score and little value cover above its debt. 

## **Evidence and limits** 

- No G1 estimate has a backtest yet. The 45% is a user choice (conflict W1), not a measured result. 

- E10 is the bond’s return over cash. It is not hedged, so it carries market risk that the hedged estimates remove. 

- E4 stays at zero weight until the code fits the risk premium _κ_ by rating and cycle phase. 

## **The test that settles its weight** 

Backtest E7, E8, E9 and E10 on the same panel as the alpha backtest. First build point-in-time inputs for each. Keep an estimate only if its rank IC after cost is above zero beyond the spread rank. 

5 

## **G2 Built methods** 

**In one line.** G2 is the code that already runs on real data for eight issuers. It holds the only measured evidence. The two clocks carry 20% as their own bucket. The other G2 estimates share 11.67%. 

## **What it is** 

G2 is every method the repository runs end to end: 

- The two clocks: `hy/clocks.py` , from M4.7 and the Radhakrishnan card. 

- The fair line and the pair report: `scripts/rv_pair.py` . 

- The macro stories and forecast sources: `hy/macro.py` and `hy/forecasts.py` , with eleven forecast cards. 

- The cases and the alpha: `scripts/scenarios.py` and `hy/alpha.py` . 

- The gate, the F8 panel and the combined view: `scripts/process.py` and `hy/groups.py` . The backtest: `hy/backtest.py` . 

## **Why it is in the framework** 

G1 says what to compute. G2 computes it. G2 is also the only group with a backtest record. That record decides how far the other numbers can be trusted. 

## **What it adds at each step** 

|Step|G2 contribution|
|---|---|
|S1 Load|Compustat point-in-time quarters, XBRL, EDGAR acceptance times, TRACE yields, Treasury|
||curves, fve live forecast sources.|
|S2 Business|The archetype from the analyst fle, the 10-K Item 1 text, the customer shares.|
|S3 Earnings|Earnings tests EQ1, EQ2, EQ5 and EQ7, the 8-quarter margin trend, FCF as CFO less capex.|
|S4 Liquidity|The scenario engine. Cash, revolver, debt ladder, severe case on each path. Four of the six|
||refnance points.|
|S5 Claims|Debt, leases, gross, net and lease-adjusted leverage, coverage, FCCR, a bond table from TRACE.|
|S6 Clocks|Fixed obligations against contracted revenue, breakeven margin, renewal share, shortfall.|
|S7 Cases|The forecast registry, the path builder and the case grid.|
|S8 Value|Market enterprise value only. The recovery library exists but the process does not call it.|
|S9 Relative value|The issuer curve, the fair line, the pair with its measured half-life.|
|S10 Alpha|The hedged alpha on each path, with PD from the cases and a cost of 20 bp of spread times|
||duration.|
|S11 Gate|Five rows. The code computes gate rules G1, G3 and G6.|
|S12 Events|The next results date and the next debt bucket. The event library exists but the process does not|
||call it.|
|S13 Metrics|Eleven F8 metrics with bands.|
|S14b Size|The backtest engine: realised alpha, calibration slope, decile check.|



6 

## **Its estimates in the score** 

|ID|Estimate|How the code computes it|Weight|
|---|---|---|---|
|E5|Two clocks|Minus fxed charges in years of EBITDAR, standardised.|20.00%|
|E0|Spread level|The bond spread over the index spread.|4.86%|
|E1|Cases and stories|The alpha of the cases, weighted by path probability, before cost.|2.92%|
|E2|Fair-line convergence|_D_(1_−ρ_4_h_)(_s −sfair_)_/h_: the part of the gap to the fair line that closes|1.94%|
|||in six months.||
|E3|Pair convergence|The pair gap closed at its measured half-life. Plus for the long leg,|0.97%|
|||minus for the short leg.||
|E6|Health panel|Green metrics minus red metrics, over all metrics on the S13 panel.|0.97%|



## **What it says about the eight issuers** 

## **Two clocks (E5), 20%** 

*(Figure: see the PDF.)*

**----- Start of picture text -----**<br>
0<br>CRWV -309<br>ORCL -158<br>HCA +197<br>THC +183<br>CCL +88<br>NCLH +102<br>MGM -108<br>WYNN +4<br>bucket alpha, bp a year before cost<br>Rest of G2 (E0, E1, E2, E3, E6), 11.67%<br>0 largest driver<br>CRWV +426 E0 +571<br>ORCL -88 E3 -776<br>HCA -82 E0 -99<br>THC +60 E3 +428<br>CCL +16 E0 -39<br>NCLH +62 E0 +90<br>MGM -86 E1 -223<br>WYNN -58 E1 -164<br>**----- End of picture text -----**<br>


bucket alpha, bp a year before cost 

- The clocks score CRWV, ORCL and MGM as negative. They score the hospitals and the cruise lines as positive. 

- In the rest of G2, CRWV is highest (+426). Its spread level (+571) and its pair gap (+776) drive it. 

- E3 gives the two legs of a pair the same size with opposite signs. So CRWV gets +776 and ORCL gets _−_ 776. 

## **Evidence and limits** 

- The alpha backtest (2008 to 2026) supports spread level and the fair line. Their rank IC after cost is 0.22 to 0.29. 

- The size is too large: realised alpha is about 0.08 times the predicted alpha. S14b applies that slope. 

- The clocks backtest (2018 to 2026, 1,143 issuers) does not support E5. Its IC after cost is _−_ 0 _._ 08 to _−_ 0 _._ 11. Beyond the spread rank it is not different from zero. 

- The market already prices the clocks. Issuers with heavy fixed charges pay more spread. 

- E1 and E2 both use the fair line, so the fair line counts more than its two weights show. 

## **The test that settles its weight** 

The clocks test is done and does not support the 20%. The user decides whether the weight stays. For the rest, set each weight in proportion to its rank IC after cost in each cycle phase. Keep the combination only if it beats “buy the widest” after cost in three of the four cycles. 

7 

## **G3 Credit skills** 

**In one line.** G3 adds the checklists of seven credit skills. It can only lower the number. It carries 11.67%. 

## **What it is** 

G3 is seven skill files. One is written for this project. Six are written for private loans and adapted here to public bonds: 

- `hy-model-standards` (this project) and `credit-model-standards` : debt at face, three EBITDAs, the FCF cross-check, a severe case from the issuer’s own main risk. 

- `ebitda-addback-treatment` : the bridge from reported to adjusted EBITDA, with limits on each add-back. 

- `covenant-compliance` : headroom bands and the direction of headroom over time. 

- `borrower-monitoring` : trend per line and the watchlist tiers. 

- `credit-memo-standards` and `quarterly-package-extraction` : what a memo must hold, and how to read a statement package. 

Code: `hy/skills.py` . 

## **Why it is in the framework** 

G3 holds the checks that an experienced lender runs every quarter. They catch problems that the price models do not see. A clean checklist earns no credit, because a clean result is the normal case. So G3 is one-way. 

## **What does not transfer to public bonds** 

The code lists six rules that do not transfer ( `NOT_TRANSFERABLE` ): 

1. No compliance certificate exists for public bonds. The code computes its own ratio against a level parsed from the filing text. 

2. Equity cures and step-downs need the credit agreement and monthly revolver data. 

3. No sponsor plan is public. The proxy is the same quarters a year earlier. 

4. Add-back caps live in the credit agreement. Compustat gives one special-items line. 

5. Sources and uses at entry apply to new loans, not to bonds bought in the market. 

The sixth rule: monthly lender packages do not exist. XBRL quarters replace them. 

## **What it adds at each step** 

|Step|G3 contribution|
|---|---|
|S1 Load|Bridge the debt between the balance sheet and the documents. Flag a new line item. Do not guess|
||its place.|
|S2 Business|A top customer above 15 to 20% of revenue makes the loss of that customer the downside.|
|S3 Earnings|Flag one add-back above 5% of EBITDA, a total above 10%, or the same add-back for three|
||quarters. FCF cross-check within 15%.|
|S4 Liquidity|Thin liquidity or a maturity with no refnance path puts a name on the watchlist, even when|
||EBITDA holds.|
|S5 Claims|Debt at face. Headroom bands: comfortable above 20%, tight below 10%. Flag a falling path early.|
|S7 Cases|The severe case combines a revenue fall, a margin squeeze and working-capital stress. Report the|
||frst breach quarter.|
|S8 Value|Loan to value moves with the sector multiple, even when leverage does not.|
|S11 Gate|A memo without its key risk fails. A “pass” is a normal outcome.|
|S12 Events|Watchlist tiers from the trend: watch closely at 10% below the prior year, watchlist at 20%.|



No skill covers relative value (S9) or expected return (S10). The skills judge debt service, not price. 

8 

## **Its estimate in the score** 

|ID|Estimate|||How the code computes it|Weight|
|---|---|---|---|---|---|
|E11|Watchlist|and|covenant|Minus the watchlist tier (0 none, 1 watch closely, 2 watchlist, 3|11.67%|
||path|||workout), minus one if headroom falls. Standardised, then capped at||
|||||zero.||



E7 (earnings quality) also comes from the skills and is also one-way. The code counts it in G1. 

## **What it says about the eight issuers** 

*(Figure: see the PDF.)*

**----- Start of picture text -----**<br>
0<br>CRWV -215<br>ORCL -215<br>HCA +0<br>THC +0<br>CCL +0<br>NCLH -215<br>MGM +0<br>WYNN +0<br>bucket alpha, bp a year before cost<br>**----- End of picture text -----**<br>


- Three issuers are on the watchlist: CRWV, ORCL and NCLH. Each gets _−_ 215 bp a year. 

- The other five have no tier. They get zero, not a credit. 

- So G3 can only pull the combined number down. For CRWV it removes 25 bp a year after its 11.67% weight. 

- Covenant headroom is “open” for seven of the eight issuers. The code parsed no covenant level from their filings. So the headroom term rarely fires. 

## **Evidence and limits** 

- No backtest covers E11 yet. 

- The thresholds come from the skills. The skills set them for private loans, not for public bonds. 

- The plan proxy (the same quarters a year earlier) is weaker than a real plan. A fast grower can look safe when its plan was higher. 

- Three of eight issuers share one value. So the bucket separates names in two groups only. 

## **The test that settles its weight** 

Build the watchlist tier point in time for the backtest panel. Test whether a tier above zero predicts a lower hedged return over six months, beyond the spread rank. If it does not, keep G3 in the memo as a risk flag and remove its weight. 

9 

## **G4 Books** 

**In one line.** G4 adds two textbook cross-checks that use no repository model. It carries 11.67%. 

## **What it is** 

G4 is two books: 

- Kricheff, _A Pragmatist’s Guide to Leveraged Finance_ (2nd edition). It is a practitioner’s view of high yield: cash flow, spread per turn of leverage, covenants, events. 

- Ganguin and Bilardello, _Standard & Poor’s Fundamentals of Corporate Credit Analysis_ (2005). It is the S&P rating method: business risk, adjusted ratios, medians by rating, recovery. 

Code: `hy/books.py` . The text comes from markdown conversions of the two books. No other book is in scope, and Fabozzi is excluded. 

## **Why it is in the framework** 

G4 checks the price with methods that do not depend on our models. If our model and a textbook method agree, the call is stronger. If they disagree, the memo must explain why. 

## **What it adds at each step** 

|Step|G4 contribution|
|---|---|
|S1 Load|Start from the fled statements and the bond terms. Use several years of history.|
|S2 Business|S&P: industry risk sets a ceiling on the issuer’s grade.|
|S3 Earnings|Krichef: reconcile every EBITDA and FCF fgure to cash from operations. The analyst may|
||reject new-issue add-backs.|
|S4 Liquidity|Krichef: restricted cash does not count. A revolver counts only if the issuer can draw it. Never|
||assume a refnance.|
|S5 Claims|Krichef: leverage at each tranche level, structural subordination. S&P: add leases and pensions to|
||debt.|
|S6 Clocks|S&P: forecast past the maturity when refnance risk exists. Krichef: PIK debt raises the claim|
||without cash.|
|S7 Cases|S&P: stress the worst credible case. A high-risk issuer takes a 10 to 30% revenue fall at the start.|
|S8 Value|S&P: name the default type, value at emergence, discount the recovery for time at 10%.|
|S9 Relative value|Krichef: use spread to worst. A junior note must pay more per turn than a senior note.|
|S10 Alpha|Krichef: yield to worst is the base return. S&P: expected loss is PD times LGD times exposure.|
|S11 Gate|S&P: decide on the three to fve issues that matter. Soft factors can only lower a grade.|
|S12 Events|Krichef: pro formas for an acquisition, a takeover, an IPO, a call.|
|S13 Metrics|S&P ratio medians by rating. Krichef’s ratios: (EBITDA _−_capex) over interest, FCF over debt.|
|S15 Decision|Krichef: defne the mandate frst. Ask whether a better instrument exists.|



10 

## **Its estimates in the score** 

|ID|Estimate|How the code computes it|Weight|
|---|---|---|---|
|E12|Ratio-implied rating|_z_(log_s_)_−z_(S&P score). The S&P score (1 best, 10 worst) blends a|5.83%|
||gap|business score and a fnancial score from the 2002 medians. A wide||
|||spread for the score is cheap.||
|E13|Spread per turn against|log(spread_/_leverage) minus the median of peers in the same GICS|5.83%|
||peers|sector, rating class and maturity bucket. It counts only if FCF over||
|||debt is above zero and the value cover is above 1. Otherwise zero.||



_Intuition._ E13 holds Kricheff’s trap. A high spread per turn looks cheap. If the issuer burns cash, the spread is high for a reason, so E13 gives no credit. 

## **What it says about the eight issuers** 

*(Figure: see the PDF.)*

**----- Start of picture text -----**<br>
0 largest driver<br>CRWV +123 E12 +246<br>ORCL -16 E12 -31<br>HCA -113 E13 -249<br>THC +169 E13 +205<br>CCL +100 E12 +106<br>NCLH +11 E12 +23<br>MGM -126 E12 -308<br>WYNN -148 E12 -190<br>bucket alpha, bp a year before cost<br>**----- End of picture text -----**<br>


- THC is highest (+169). Its spread is wide for its S&P score (E12 +133) and for its peers’ spread per turn (E13 +205). 

- CRWV gets +123 from E12 alone. Its E13 is 0 because it burns cash. That is Kricheff’s trap: a wide spread per turn is no credit when FCF is negative. 

- WYNN is lowest ( _−_ 148). Its spread is tight for its score (E12 _−_ 190) and tight per turn against its peers (E13 _−_ 106). 

- For MGM the two checks disagree: E12 is _−_ 308 and E13 is +56. The memo must say which one to believe. 

- ESP, reported without weight: CRWV pays 78% more than its peers. HCA pays 52% less. 

## **Evidence and limits** 

- The peer backtest (2008 to 2026) finds that E13 adds nothing beyond spread level: IC beyond spread +0 _._ 02, _t_ 1.1. No backtest covers E12 yet. 

- ESP (excess spread to peers) does add information beyond spread level (+0 _._ 07, _t_ 2.6). But the edge disappears in the 2008 and 2020 stress windows. The memo reports ESP without weight. Decision page: `2026-10-22-esp-peer-groups` . 

- No rating source covers 2017 onward. After 2017, the rating class comes from leverage. It matches the actual class on 36% of issuer-months. 

- The S&P medians date from 2002, before the 2008 cycle. The book has no newer table. 

- The industry risk map by archetype is a v0 choice. The book’s own table did not survive the conversion. 

- The Kricheff conversion lost every table. Only numbers quoted in the text survive. 

- Both books contain a few arithmetic slips. This document does not copy them. 

## **The test that settles its weight** 

Compute the S&P score and the spread per turn point in time on the backtest panel. Test each one’s rank IC after cost beyond the spread rank. E12 is close to the fair line in idea. If it adds nothing beyond E2, drop it. 

11 

|**Contents**||
|---|---|
|**Summary**|**1**|
|**The single analyst pipeline**|**2**|
|**The four groups**|**3**|
|**G1 Core process**|**4**|
|**G2 Built methods**|**6**|
|**G3 Credit skills**|**8**|
|**G4 Books**|**10**|
|**1**<br>**S1 Load the data**|**14**|
|**2**<br>**S2 Frame the business**|**15**|
|**3**<br>**S3 Normalise earnings and add-backs**|**17**|
|**4**<br>**S4 Liquidity and the wall**|**19**|
|**5**<br>**S5 Claims, capital structure and covenants**|**21**|
|**6**<br>**S6 Two clocks**|**24**|
|**7**<br>**S7 Economic stories and cases**|**26**|
|**8**<br>**S8 Value and recovery**|**28**|
|**9**<br>**S9 Relative value and the pair**|**31**|
|**10 S10 Expected alpha**|**33**|
|**11 S11 The gate: price against view**|**34**|
|**12 S12 Events and monitoring**|**36**|
|**13 S13 Metrics panel**|**38**|
|**14 S14 Combined view**|**39**|
|**15 S14b Size calibration**|**40**|
|**16 S15 Decision against cash**|**41**|
|**17 The combined score**|**44**|



12 

|**18 **|**Conficts register**|**47**|
|---|---|---|
|**19 **|**Metrics dictionary**|**51**|
|**20 **|**Glossary**|**54**|



13 

## **1 S1 Load the data** 

**Purpose.** Load every input with the date the market could first read it, so that no later step sees the future. 

## **What each group contributes** 

- **G1** The rule: every field carries `as_of` and `available_at` ; a memo dated _t_ reads nothing released after _t_ (M3, F1 R5). Every number cites its source line (R4). The PDF adds: list the feasible opportunity set first (R7–R9); TRACE prices are estimates, not executable quotes (R10); verify clean, dirty or flat per bond (R16); dirty price and market value (U1, U2). 

- **G2** The live loaders: Compustat point-in-time quarters, XBRL instances with dimensions, EDGAR acceptance times, TRACE (10-day volume-weighted yields), Treasury par curves, and the forecast registry with five live sources (SPF, FOMC SEP, Treasury forwards, SLOOS, TRACE HY level). 

- **G3** `quarterly-package-extraction` : read the statements top down; aggregate months to quarters to LTM; flag any new line item instead of guessing its place. The debt must always bridge between balance sheet and document (OID, leases, letters of credit). In public HY there is no compliance certificate; the 10-Q and the indenture replace it. 

- **G4** Both books start from the filed statements and the bond terms. S&P adds that the analyst should use several years of history and adjust the statements before any ratio (see S3). 

## **Algorithm** 

1. Set the decision time _t_ = last TRACE date + 1 day. 

2. For each issuer, read the latest 10-Q or 10-K with acceptance time _≤ t_ . Parse the XBRL instance with dimensions. 

3. Read Compustat point-in-time quarters known at _t_ . Fill a missing fourth quarter from XBRL as first filed (decision page `2026-10-21-pit-financials-sources` ). Rebuild quarterly flows from year-to-date by differences. 

4. Read TRACE bonds: fixed coupon, not convertible, senior unsecured or secured, 1 to 15 years, price _≥_ 80. Compute G-spreads on the curve of _t_ . 

5. Read every forecast row with `available_at` _≤ t_ ; keep the newest vintage per source and variable. 

6. Reconcile debt: balance-sheet debt against the maturity ladder; put an unexplained gap in the tail and log it. 

7. Write each value with its source line and `available_at` . A value without a source is an open question. 

## **Metrics** 

$$
s^{G}_b = y_b - y^{UST}(T_b),\qquad P^{d}_b = P^{c}_b + AI_b,\qquad X^{LTM}_t = \sum_{q=t-3}^{t} X_q .
$$

_Intuition._ the G-spread is the bond’s pay over a Treasury of the same maturity; the dirty price is what a buyer pays; LTM adds the last four quarters. 

_Symbols. yb_ volume-weighted TRACE yield of bond _b_ ; _y[UST]_ ( _T_ ) Treasury par yield at maturity _Tb_ (years); _P[c]_ clean price; _AI_ accrued interest; _Xq_ a quarterly flow. 

## **Bands** 

None. Data quality flags: debt ladder does not reconcile within 5%; a quarter missing; a bond with no trade in 10 days. 

14 

## **Inputs** 

_Data:_ Compustat, XBRL, EDGAR, TRACE, Treasury, forecast registry. _Documents:_ 10-K and 10-Q text. _Analyst:_ ticker list, pairs, overrides in `data/analyst_inputs/<ticker` _>_ `.yaml` . 

## **Outputs** 

`filing` , `bonds_priced` , `curve_basis` , `decision_time` , and the source of every LTM figure. 

## **Where groups disagree** 

G1 (M3.1) says US bonds quote clean; the PDF (R16) says verify per bond (C18). **Wins:** a per-bond `quote_convention` field with M3.1 as default, because bonds near default trade flat. G3 treats the certificate as the source of truth (K6); public HY has none, so the filing and the indenture win. 

## **Settling test** 

Code tests: `tests/test_inputs.py` ; `tests/test_forecasts.py::test_as_of_never_reads_ rows_released_later` , `tests/test_sources.py` , `tests/test_xbrl.py` , `tests/test_trace_ bonds.py::test_g_spread_arithmetic_and_no_look_ahead` . Open: the M11 point-in-time replay of every feature. 

## **Status** 

**Partial** . Missing: ratings, face and call schedule by bond, accrued interest, quote convention, bid and ask, consensus, guidance, default labels, ICE OAS. 

## **2 S2 Frame the business** 

**Purpose.** Decide what kind of business this is and how risky it is before any debt, because that sets which earnings, ratios, downside and events matter. 

## **What each group contributes** 

- **G1** Gatto step 2 (Chapter 6, pp. 155–186): eight industry risks (Figure 6.2, p. 158), the strategy, management, ESG. F2: five lines (what it sells, how one unit earns, what it must spend to stand still, market structure, what breaks it); one archetype A1–A8; modifiers M1 sponsor, M2 secular decline, M3 concentration. M4.4: each risk scored 0, 1 or 2. PDF: three to five material risks, each tied to a downside case (P4); an evidence ledger (P5); risk must change the forecast, not be added to a ratio (R31, R34); undisclosed concentration is missing, not zero (R32). 

- **G2** The code reads the archetype from the analyst file, the first two sentences of 10-K Item 1, the XBRL customer shares, and the F2 downside driver of the archetype. 

- **G3** `credit-model-standards` : the downside comes from the business’s own risk profile, never from another deal’s template; a top customer above 15–20% of revenue makes loss of that customer the downside. `credit-memo-standards` : state the business in one sentence first. 

- **G4** S&P (Ganguin and Bilardello, Ch. 1–4, 10): grade country, industry and company risk; industry risk sets a ceiling on the issuer (Table 2-2 ranks steel, autos, airlines, homebuilders and paper highest; branded consumer, pharma and regulated utilities lowest); find the sector’s keys to success and the driver under each; score each key 1–10 and weight them into a business risk score (forest products: cost 50% _×_ 7, diversity 30% _×_ 8, integration 20% _×_ 4 gives 6.7); management’s past deviation from plan predicts future deviation; seventeen governance red flags. Kricheff (Ch. 11, 19, 25): competition, concentration, barriers, cyclicality, capital intensity, price setter or taker; private-equity owners almost ensure a transaction; test management targets against peers (a 15% margin target where no peer exceeds 12% deserves doubt). 

**Algorithm** 

15 

1. Write the five F2 lines. Cite the 10-K for each. 

2. Assign one archetype. If two fit, compute both views later and report the difference (F2.1). 

3. Set modifiers: M1 if a sponsor owns it; M2 if industry volume falls over five years with no cyclical cause; M3 if the top customer is above 20% of revenue. Raise a watch flag at 15%. 

4. Score the business risk profile on the G4 scale (country, industry, competitive position) from the evidence in step 1: weight the sector keys to success, score each 1–10, and cap the result at the industry ceiling (S&P). Governance red flags can only make the score worse, never better. 

5. Name three to five material risks. For each, name the forecast driver it changes and the downside case that carries it (to S7). Do not add the scores to any ratio. 

6. Re-frame on a change of business mix above 20% of revenue, an acquisition, or a change of owner (F2.4). 

## **Metrics** 

$$
HHI = \sum_j \Big(\frac{Rev_j}{Rev}\Big)^2,\qquad top_1 = \max_j \frac{Rev_j}{Rev}.
$$

_Intuition._ revenue held by few customers can vanish in one step. 

_Symbols. Revj_ revenue from customer _j_ (XBRL concentration axis); undisclosed shares stay missing. 

$$
BR = \sum_k \omega_k\, b_k,\qquad \sum_k \omega_k = 1,\qquad BR \ge BR^{ind}.
$$

_Intuition._ the business risk score is a weighted grade of what wins in this industry, never better than the industry allows. 

_Symbols. bk ∈_ [1 _,_ 10] score on key to success _k_ (1 best); _ωk_ its weight; _BR[ind]_ the best score the industry allows (S&P industry ranking). 

## **Bands** 

_top_ 1: below 15% green; 15–20% amber (watch); above 20% red (M3). Business risk score _BR_ : 1–4 low, 5–6 moderate, 7–10 high (S&P scale; cut points v0). 

## **Inputs** 

_Data:_ customer shares, LTM revenue, EBITDA, lease cost. _Documents:_ 10-K Item 1 and risk factors. _Analyst:_ archetype, modifiers M1 and M2, market structure, the business risk grade. 

## **Outputs** 

`archetype` , `modifiers` , `sells` , `earns` , `breaks` , `market_structure` , `business_risk` , `material_ risks[]` . 

## **Where groups disagree** 

G3 sets concentration at 15–20%; F2 at 20% (K7). **Wins:** 20% for the modifier and 15% for a watch flag, because the modifier changes the case set and needs a firmer trigger. G1 M4.4 feeds scores into the fair model; the PDF forbids adding scores to ratios (C16). **Wins:** the scenario route; a score vector enters a model only after the R163 admission test. G4 (S&P) combines business and financial scores into one grade (B4). **Wins:** keep the S&P grade only as a cross-check estimate in S14, never as a term in a spread or PD model. 

## **Settling test** 

F13 blind memo rubric, item 1, on held-out resolved credits. For the score: ablate it from the fair model; keep it only if out-of-sample residual variance falls. 

16 

## **Status** 

**Partial** . Built: archetype, M3, “sells” and “breaks”. Missing: market structure, M1, M2, material risks, the business risk grade, re-frame triggers. 

## **CRWV** 

Archetype A5 (asset-heavy contracted); M3, the largest customer is 36% of revenue; revenue 7.6bn a year at a 50% EBITDA margin; rent 2.07bn a year. 

## **3 S3 Normalise earnings and add-backs** 

**Purpose.** Find the earnings and the cash that recur, and flag accounts that look better than the cash. 

## **What each group contributes** 

- **G1** Gatto step 3a (Chapter 7, pp. 187–223): remove nonrecurring items (Figure 7.3, p. 192); a “nonrecurring” charge that recurs is an operating cost. F3: three EBITDA numbers kept apart (analyst, company, covenant); add-back classes C1–C10 (C6 stock compensation never; C8 projected synergies never); history of 3–5 years, a full cycle for A3 and A4; quality tests EQ1–EQ10. M4.2: FCF from adjusted EBITDA less the cash part of the add-backs. PDF: a repeated cash cost is not nonrecurring (R37); Gatto’s five quality tests (P9); backlog bridge and book-to-bill (E16, E17); add-back dependence (E71); cash conversion (E72); no double count from a CFO start (R42). 

- **G2** The code runs EQ1, EQ2, EQ5, EQ7, the 8-quarter margin trend, and FCF as CFO less capex. 

- **G3** `ebitda-addback-treatment` : build net income to reported EBITDA first, then layer each covenant add-back; split cash from non-cash add-backs; flag a category above 5% of EBITDA, the same add-back for 3–4 quarters, and small items that sum above 10–15%; track whether add-backs roll off. `hy-model-standards` : a synergy enters FCF only from the quarter it shows in reported EBITDA; cross-check FCF against CFO less capex. `quarterly-package-extraction` : an acquisition folded into reported numbers inflates growth; separate organic from acquired. 

- **G4** Kricheff (Ch. 9, 10, 16, 22): build EBITDA as net income + tax + interest + D&A; reconcile every EBITDA and FCF figure to cash from operations; footnote each add-back; the analyst may reject new-issue add-backs (sponsor fees, full planned savings, restructuring cash); normalise capex (a 75m one-off data centre inside 200m of capex leaves 125m recurring); show analyst and covenant EBITDA side by side; capex that stays below depreciation predicts a capex spike. S&P (Ch. 5, 6): spread 3–5 years; run the accounting checklist (auditor changes, restatements, consolidation, LIFO, pensions, securitisation, capitalised costs, net income that grows faster than cash flow); define FFO, OCF, FOCF and discretionary cash flow; compute hybrids at 0% and at 100% debt. 

## **Algorithm** 

1. Build reported EBITDA from the statements: net income + tax + interest + D&A. Tie it to the issuer’s own EBITDA. If it does not tie, log the gap. 

2. List every item between reported and company-adjusted EBITDA (8-K exhibit 99). Classify each as C1–C10 (F3). Mark it cash or non-cash. 

3. Decide each item by the F3 rule. Reject: stock compensation (C6), projected synergies (C8), any item present in 3 of the last 5 years (C2, EQ5), or 3–4 quarters in a row at a similar level (G3). 

4. Analyst EBITDA _E[adj]_ = reported + accepted items. Company EBITDA as reported. Covenant EBITDA by the indenture definition (or the 10-Q covenant note). 

17 

5. Compute FCF by the M4.2 identity. Compute the cross-check _CFO − Capex_ . Flag a gap above 15% of _E[adj]_ . 

6. Run EQ1–EQ10. Count the flags; EQ10 counts twice. 

7. Compute the margin trend over 8 quarters and the organic growth (Gatto definition, C17). 

8. Compute the S&P cash ladder (FFO, OCF, FOCF, discretionary cash flow). Run the S&P accounting checklist; each failed item counts as an EQ10-type flag. 

## **Metrics** 

$$
E^{adj}_t = E^{rep}_t + \sum_i a_i\,NR_{i,t},\qquad FCF_t = E^{adj}_t - CashNR_t - K_t - I^{c}_t - T^{c}_t - \Delta WC_t .
$$

_Intuition._ add back only what will not recur, then charge the cash that the add-backs hid. 

_Symbols. NRi,t_ nonrecurring item _i_ ; _ai ∈{_ 0 _,_ 1 _}_ the add-back decision; _CashNRt_ cash part of accepted items; _K_ capex; _I[c]_ cash interest; _T[c]_ cash tax; ∆ _WC_ working-capital build. 

$$
gap^{add} = \frac{E^{co}}{E^{adj}} - 1,\qquad gap^{cov} = \frac{E^{cov}}{E^{adj}} - 1,\qquad chk = \frac{FCF - (CFO - K)}{E^{adj}} .
$$

_Intuition._ how far the issuer’s and the document’s earnings sit above the analyst’s, and how far the model’s FCF sits from the cash flow statement. 

_Symbols. E[co]_ company-adjusted EBITDA; _E[cov]_ covenant EBITDA; _CFO_ operating cash flow. 

$$
conv = \frac{\sum_{4q}(CFO - K)}{\sum_{4q} E},\qquad trend = \frac{\hat b}{\mathrm{se}(\hat b)},\qquad
\text{EQ1} = 1\Big\{\frac{DSO_t}{DSO_{t-4}} - 1 > 0.10 \wedge g < 0.05\Big\}.
$$

_Intuition._ earnings that do not turn into cash, a falling margin, and receivables that outgrow sales are the first signs of soft accounts. 

_Symbols._[ˆ] _b_ OLS slope of the EBITDA margin on time over 8 quarters; _DSO_ = _AR/Rev ×_ 91; _g_ year-on-year revenue growth. 

$$
FFO = NI + NC,\quad OCF = FFO - \Delta WC,\quad FOCF = OCF - K,\quad DCF^{disc} = FOCF - Div .
$$

_Intuition._ the S&P cash ladder: cash from earnings, then after working capital, then after capex, then after dividends. 

_Symbols. NI_ net income; _NC_ non-cash items (D&A, deferred tax, write-offs, asset-sale gains and losses); _Div_ dividends. FOCF equals the code’s CFO less capex. 

## **Bands** 

`addback_gap` : _<_ 10 / 10–20 / _>_ 20% (F8). `covenant_gap` : _<_ 10 / 10–25 / _>_ 25%. One add-back category: _>_ 5% of EBITDA is amber (G3). FCF check _|chk|_ : _<_ 5 / 5–15 / _>_ 15%. `fcf_conversion` : _>_ 0.30 / 0.10–0.30 / _<_ 0.10. `eq_score` : 0 / 1–2 / _≥_ 3. `margin_trend` : _>_ 1 / _−_ 1 to 1 / _< −_ 1. 

## **Inputs** 

_Data:_ Compustat quarters (EBITDA, special items, CFO, capex, receivables, inventory, COGS, interest, tax). _Documents:_ 8-K exhibit 99 reconciliation; indenture EBITDA definition; segment and acquisition notes. _Analyst:_ the decision _ai_ per item; cash flag where the filing is silent. 

## **Outputs** 

`ebitda_rep` , `ebitda_adj` , `ebitda_covenant` , `addback_table` , `addback_gap` , `covenant_gap` , `fcf` , `fcf_check_gap` , `fcf_conversion` , `eq_flags` , `eq_score` , `margin_trend_t` , `organic_growth` . 

18 

## **Where groups disagree** 

FCF start point (K1): G3 starts from reported EBITDA; M4.2 from adjusted EBITDA less _CashNR_ ; the code from CFO less capex. **Wins:** M4.2 for the forecast, because it keeps the earnings level and charges the hidden cash; CFO less capex is the cross-check. Stock compensation (K2): G3 lists it as a non-cash add-back; F3 C6 rejects it. **Wins:** F3, because the issuer pays it in shares or buybacks. Organic growth (C17): **wins** Gatto’s definition. Kricheff calls stock compensation the “most universal” add-back (B3); F3 still wins, for the reason of K2. S&P and Kricheff use several FCF definitions (B7). **Wins:** one definition per use: the M4.2 FCF for forecasts and liquidity, FOCF for ratio benchmarks against S&P medians, unlevered FCF for valuation, and cash available for debt service for the default test. 

## **Settling test** 

Restatement audit (M11). Rank IC of `eq_score` and `addback_gap` against later EBITDA misses. FCF check against CFO less capex on issuers with large cash restructuring (decision page `2026-1021-fcf-cash-nonrecurring` ). 

## **Status** 

**Partial** . Built: EQ1, EQ2, EQ5, EQ7, margin trend, FCF as CFO less capex. Missing: the add-back table, analyst and covenant EBITDA, the gaps, six EQ tests, organic growth, the M4.2 identity in the process (it exists in `hy/state.py` ). 

## **CRWV** 

LTM EBITDA 3,760m at 49.5%; margin trend _t_ = _−_ 1 _._ 61 (red); FCF _−_ 13 _,_ 655m; conversion _−_ 3 _._ 63 (red); EQ7 raised. 

## **4 S4 Liquidity and the wall** 

**Purpose.** Measure what the issuer can spend now, the date its cash runs out, and whether the market will refinance the debt that falls due. 

## **What each group contributes** 

- **G1** Gatto step 3b (Chapter 8, pp. 224–254): static liquidity (Figure 8.3, p. 229), maturity schedule (Figure 8.4, p. 229), refinance access and levers (p. 231); a default is a liquidity event first (p. 424). F4: effective liquidity with free cash, borrowing base, springing trigger and minimum cash; runway; the wall; the 0–6 refinance access score; trade, capex and levers. PDF: funding gap _Gh_ and its first failure date (E75, E76); refinancing interest shock ∆ _I_ (E77); positive annual FCF does not prove liquidity on every date (R44); maintenance capex is not depreciation by rule (R48). 

- **G2** The scenario engine runs before this step. The code reads cash, revolver capacity, the debt ladder, the severe case on each path, and scores four of the six refinance points. 

- **G3** `borrower-monitoring` : thin liquidity, a fully drawn revolver, or a maturity with no refinancing path puts a name on the watchlist even when EBITDA holds. `covenant-compliance` : a minimum liquidity covenant, when present, is the top-priority covenant. `credit-model-standards` : report the liquidity runway in the stress case. 

- **G4** Kricheff (Ch. 9, 10, 12, 14, 18, 23): restricted cash does not count; an undrawn revolver counts only if covenants and the borrowing base allow the draw; worry about a maturity 6–12 months ahead; never assume a refinancing, test leverage in the maturity year against recent deals and price it at a higher spread; record a shortfall as a funding need, a new financing line, or a default trigger; in distress, map cash against the actual coupon dates (semiannual bonds, 30-day grace). Case: a new bank rate near twice the old one leaves leverage flat and cuts FCF and coverage sharply (Table 18-2). S&P (Ch. 5, 7, 10): only committed facilities count; list 

19 

what could cause a sudden cash call (maturities, rating triggers, covenant accelerations, pension contributions); liquidity is judged, not read off a ratio; a BB issuer should have debt service secure from operating cash flow for 24 months; for a B issuer it is not secure over 12 months, so long-dated debt and committed lines are essential. 

## **Algorithm** 

1. Free cash: unrestricted cash the parent can reach (F4.1). Drop restricted cash (G4). 

2. Revolver: count undrawn capacity only up to the borrowing base and the springing trigger, and only if the covenants allow the draw (F4.2, F4.3, G4). 

3. Minimum cash: one month of cash operating cost, ( _COGS_ + _SG_ & _A_ ) _/_ 3 per quarter (F4.4). 

4. _L[eff]_ = free cash + usable revolver _−_ letters of credit _−_ minimum cash. 

5. Static runway from LTM FCF. Scenario runway: first quarter of shortfall in the severe case, run twice: once with maintenance capex only and once with committed capex. Quote the shorter one (K14). 

6. Wall: debt due inside 18 months, plus any springing maturity and any revolver maturity in that window. 

7. Funding gap _Gh_ per quarter and path; record its minimum and the first quarter with _Gh <_ 0 (PDF E75). 

8. Refinancing shock: reprice debt due inside 24 months at the forward Treasury plus the issuer’s own 5-year spread; compute ∆ _I_ , _E/_ ( _I[c]_ + ∆ _I_ ) and _FCF −_ ∆ _I_ (E77, G4). 

9. Refinance access score (0–6) per path; map to _p[access]_ . 

10. Set the G3 liquidity watch flag if _L[eff]_ covers less than four quarters of burn, the revolver is fully drawn, or _p[access] <_ 0 _._ 5 with _wall_ 18 _m >_ 0. 

## **Metrics** 

$$
L^{eff} = Cash^{free} + \min(Cap, BB, Trig) - Drawn - LC - Cash^{min}.
$$

_Intuition._ what the issuer can spend today after the cash it needs to operate. 

_Symbols. Cap_ revolver commitment; _BB_ borrowing base; _Trig_ springing trigger; _Drawn_ drawn amount; _LC_ letters of credit; _Cash[min]_ minimum operating cash. 

$$
runway^{st} = \frac{L^{eff}}{\max(0, -FCF_{LTM}/4)},\qquad WC_h = \frac{L^{eff} + \sum_{u\le h} FCF^{base}_u}{\sum_{u\le h} M_u},\quad h\in\{4,8\}.
$$

_Intuition._ quarters of burn that today’s cash covers; and whether cash plus base-case cash flow pays the debt that falls due. 

_Symbols. Mu_ principal due in quarter _u_ ; _FCFu[base]_ base-case FCF on the most likely path. 

$$
G_h = C_0 + A_h - C^{min} + \sum_{u\le h} FCF_u - M_h - U_h,\qquad \Delta I = \sum_k D^{refi}_k\,(c^{new}_k - c^{old}_k).
$$

_Intuition._ the funding gap at each date; and the rise in interest when cheap old debt refinances at today’s price. 

_Symbols. Ah_ drawable capacity; _Uh_ other uses; _Dk[refi]_ debt refinanced in bucket _k_ ; _c[new] k_ forward Treasury at the date plus the issuer’s 5-year spread; _c[old] k_ old coupon. 

$$
n(m) = \sum_{j=1}^{6} pt_j(m),\qquad p^{access}(m) = \pi[n(m)],\quad \pi = (0.20, 0.50, 0.80, 0.92, 0.97, 0.99, 0.995).
$$

20 

_Intuition._ each sign that lenders will roll the debt adds a point; points map to a probability. 

_Symbols._ F4 points: rating B _−_ or better (proxy: spread inside 700 bp); a recent raise; unencumbered assets cover half the wall; longest bond above 90 and inside 700 bp; primary market open; a sponsor with capacity. _π_ is v0. 

## **Bands** 

`runway_scen_q` : _≥_ 8 / 4–8 / _<_ 4. `wall_cover_4` : _>_ 1 _._ 5 / 1.0–1.5 / _<_ 1 _._ 0. `refi_score` : _≥_ 4 / 2–3 / _≤_ 1. `funding_gap_min` : _≥_ 0 green, _<_ 0 red. ∆ _I/E_ : _<_ 5% / 5–15% / _>_ 15% (v0). 

## **Inputs** 

_Data:_ cash, revolver tags, debt ladder, quarterly COGS and SG&A, scenario FCF, TRACE coupons and spreads, Treasury forwards. _Documents:_ credit agreement (commitment, borrowing base, trigger, springing maturity); unencumbered assets. _Analyst:_ sponsor support; levers (asset sales, receivable lines) with amount, timing and probability. 

## **Outputs** 

`L_eff` , `runway_static_q` , `runway_scen_q` , `runway_full_capex_q` , `wall_18m` , `wall_cover_4` , `wall_cover_8` , `funding_gap_min` , `first_gap_q` , `delta_I` , `refi_score_by_path` , `p_refi_access` , `watch_liquidity` . 

## **Where groups disagree** 

Shortfall order (C9): F6.1 draws the revolver first; Gatto uses cash above the minimum first. **Wins:** Gatto, after the trapped-cash haircut, because it costs less interest; the code already does this. Minimum cash (K11): **wins** F4.4. Capex in the cases (K14): **wins** the two-run rule. One maintenance-only case hides the burn that growth commitments create. Maintenance capex (C19): F4.7 depreciation floor stays a labelled default. 

## **Settling test** 

Calibrate the score-to-probability map from realised refinancings by score and market state (F4). Check the first funding-gap quarter against realised distressed exchanges and filings. 

## **Status** 

**Partial** . Built: _L[eff]_ without borrowing base or letters of credit, static runway, the severe-case runway on both capex runs (the committed-capex run now sets the quoted runway), wall, wall cover, four of six score points, the S&P business and financial scores. Missing: revolver capacity (credit lines are untagged in the filings), _Gh_ , ∆ _I_ , points 3 and 6, levers. 

**CRWV.** _L[eff]_ 6,979m; static runway 2.0 quarters; wall 10,597m; wall cover 1.29 (amber); score 3 on the soft-landing path, 1 in recession. LTM FCF is _−_ 13 _._ 7bn. The maintenance-only severe case showed no shortfall in 8 quarters; the code now also runs the severe case with committed capex and quotes the shorter runway, so the memo no longer shows the optimistic one. 

## **5 S5 Claims, capital structure and covenants** 

**Purpose.** Count every claim in order of priority, measure it in years of earnings, and find how much room the documents leave before a breach or a priming. 

## **What each group contributes** 

- **G1** Gatto step 3c (Chapter 9, pp. 255–282): the capital structure table first (Figure 9.6, p. 261); senior claims at face, the tranche under analysis at market (p. 264); leases (pp. 267–268); 

21 

guarantees (p. 273). Gatto step 6 (Chapter 12, pp. 337–365): maintenance against incurrence covenants, add-backs, baskets, sacred rights; a 15% cushion on a 4.0x plan gives a 4.7x covenant (p. 356). F5: going-concern view and claims view kept apart (R3); allowed claims by class with bankruptcy-code rules; per-entity waterfall. F7: liability management score. PDF: creation leverage of a layer (E31, C5); lease leverage by liability (E33, C6); pension leverage (E35, C7); coverage family (E25–E27, E64–E68); covenant debt capacity and decline to breach (E46–E48, E78–E80); a coverage threshold is a warning unless it is a verified contract test (R59). 

- **G2** The code computes balance-sheet debt, lease liabilities, gross, net and lease-adjusted leverage, coverage, FCCR, and a bond table from TRACE. 

- **G3** `hy-model-standards` : debt at face even when filed net of OID; `lev_gross` beside `net_lev` ; FCCR with mandatory amortisation. `covenant-compliance` : headroom bands, trajectory (flag a falling path early), maintenance against incurrence, step-down schedule by test date, quarterend revolver window dressing, severity order (minimum liquidity, then leverage, then FCCR, then capex), equity cure count. `quarterly-package-extraction` : debt must bridge between balance sheet and document. Adaptation to public HY: bonds carry incurrence covenants only; maintenance tests sit in the loan or revolver above the bonds, and a breach there is the bondholder’s event. 

- **G4** Kricheff (Ch. 10, 15, 16, 17): leverage at each tranche level (bank 4x, total 6x; the jump drives pricing inside the structure); structural subordination (a holdco senior note ranks behind all opco debt); guarantees and priming; incurrence capacity by the leverage test and the fixed-charge test; restricted payments basket; change of control at 101; asset-sale proceeds; amendments by simple majority, money terms by 100%; the 20–25% headroom is the cushion banks set at signing, not a monitoring band; market-adjusted debt. S&P (Ch. 5, 7, 8, App. E): total debt adds leases at the present value of commitments (10% rate), pensions and OPEB net of plan assets and after tax, guarantees, securitised receivables, probable contingent payments; notching by the priority ratio; collateral liquidity ranking; read covenant definitions from the innermost outward. 

## **Algorithm** 

1. Build the capital structure table: every loan, bond, lease and debt-like claim, by legal entity, rank, collateral and guarantor. Debt at face (G3). Bridge the total to the balance sheet; an unexplained gap is an open question. 

2. Debt-like items (going-concern view): lease liability from the filing (C6, B1; S&P present value at 10% when no liability is tagged; 8 _×_ rent only before 2019); pension and OPEB deficit (B2); guarantees to weak parties; probable contingent payments. 

3. Ratios: gross, net, lease-adjusted and through-tranche leverage; cash, after-capex and fixedcharge coverage; S&P FFO/debt and FOCF/debt. 

4. Creation leverage of each layer: senior claims at face, every claim of the layer at its own price (PDF E31). 

5. Notch check (S&P): priority ratio of debt ahead of the bonds over total assets. 

6. Covenants. For each maintenance test in a loan above the bonds: headroom on the document’s own definition, at each step-down date, now and one year out (G3, G4). For each bond incurrence test: debt capacity under the leverage test and the coverage test; restricted payments capacity. 

7. Claims view (F5): allowed claim by class for the waterfall in S8. Keep the book liability beside it. 

8. LME exposure: F7 score from documents (required lenders, unrestricted subsidiary capacity, baskets, sponsor history). 

## **Metrics** 

$$
Lev^{gross} = \frac{D}{E},\quad Lev^{net} = \frac{D - Cash}{E},\quad Lev^{lease} = \frac{D + L^{op} + L^{fin}}{E + R},\quad Lev^{8x} = \frac{D + 8R}{E + R}.
$$

22 

_Intuition._ turns of earnings the debt represents; rent is debt service by another name, so the lease goes into debt and the rent back into earnings. 

_Symbols. D_ financial debt at face; _L[op]_ , _L[fin]_ operating and finance lease liabilities; _R_ annual lease cost; _E_ LTM EBITDA. 

$$
Lev^{face}_k = \frac{\sum_{j:\,r_j\le r_k} F_j}{E},\qquad
Lev^{cr}_k = \frac{\sum_{j:\,r_j<r_k} F_j + \sum_{j:\,r_j=r_k} F_j P_j/100}{E}.
$$

_Intuition._ senior claims must be paid in full first; a buyer of layer _k_ pays the market price for the whole layer. _Symbols. Fj_ face of claim _j_ ; _rj_ its rank (1 paid first); _Pj_ its price per 100. 

$$
Cov^{c} = \frac{E}{I^c},\quad Cov^{K} = \frac{E - K}{I^c},\quad FCCR = \frac{E + R - K^{m}}{I^c + R + Am},\quad \frac{FFO}{D},\quad \frac{FOCF}{D}.
$$

_Intuition._ whether earnings pay interest; after reinvestment; after rent and scheduled principal; and how fast cash flow could repay the debt. 

_Symbols. I[c]_ cash interest; _K_ total capex; _K[m]_ maintenance capex; _Am_ mandatory amortisation; _FFO_ , _FOCF_ from S3. 

$$
H = 1 - \frac{Lev^{cov}}{Lev^{max}},\qquad Cap^{lev} = m^{test} E^{cov} - D^{cov},\qquad Cap^{cov} = \frac{E^{cov}/c^{test} - I}{r^{new}}.
$$

_Intuition._ the share by which covenant EBITDA can fall before a breach; and the new debt the issuer may add under each incurrence test. 

_Symbols. Lev[cov]_ leverage on the document definition; _Lev[max]_ the limit at the test date; _m[test]_ leverage test multiple; _c[test]_ coverage test multiple; _I_ current interest; _r[new]_ rate on new debt. Kricheff: a 5x test at 4x actual and 500m EBITDA leaves about 500m. 

$$
PR = \frac{D^{prior} + L^{prior}}{TA},\qquad notch = -1\{PR \ge 0.15\} - 1\{PR \ge 0.30\}\ \text{(speculative grade)}.
$$

_Intuition._ the more debt ranks ahead of the bonds, the less value is left for them, so the bonds rate below the issuer. 

_Symbols. D[prior]_ secured and structurally senior debt; _L[prior]_ other priority liabilities; _TA_ total assets. 

## **Bands** 

_Cov[K]_ (F8 `coverage` ): _>_ 2 _._ 0 / 1.25–2.0 / _<_ 1 _._ 25. FCCR: _>_ 1 _._ 5 / 1.1–1.5 / _<_ 1 _._ 1. Headroom _H_ : _>_ 25% / 10–25% / _<_ 10%, and amber if the path falls by more than 5 points a quarter (G3 trajectory rule). FFO/debt against S&P 2002 medians: BB 19.5%, B 10.8%. FOCF/debt: BB 8.5%, B 2.5%. Notch: 0 green, _−_ 1 amber, _−_ 2 red. Leverage: rank inside the archetype (F8). 

## **Inputs** 

_Data:_ XBRL debt, leases, pension and OPEB, cash, total assets; LTM EBITDA, interest, capex, depreciation; TRACE prices. _Documents:_ debt note with face by tranche, indentures and credit agreements (covenants, baskets, guarantors), intercreditor agreement. _Analyst:_ which liabilities count; the claim class of each; the LME score points. 

## **Outputs** 

`cap_table` , `lev_gross` , `lev_net` , `lev_lease` , `lev_8x` , `lev_face_k` , `lev_creation_k` , `cash_cov` , `after_capex_cov` , `fccr` , `ffo_to_debt` , `focf_to_debt` , `priority_ratio` , `notch` , `headroom_H` , `debt_capacity` , `rp_capacity` , `lme_score` , `claims_table` . 

23 

## **Where groups disagree** 

Leases (C6, B1): M4.3 uses 8 _×_ rent; F5 and the PDF use the filed liability; S&P uses the present value at 10%; Kricheff counts only capital leases. **Wins:** the filed liability, because after ASC 842 it is already a present value of the remaining term; S&P’s 10% present value when no liability is tagged; 8 _×_ for old periods only. The code already uses the liability. Pensions (C7, B2): F5 adds the deficit to debt; the PDF also adds expense less service cost to EBITDA; S&P adds PBO plus OPEB less plan assets, after tax. **Wins:** the PDF form with OPEB included; apply the tax shield only for a cash tax payer, because most HY issuers pay little cash tax (Kricheff). FCCR (K4): **wins** F5 for lease-heavy issuers, the skill form for amortising loans; print both. Headroom bands (K5, B6): **wins** F8 bands on the F8 formula, with the G3 trajectory rule and Kricheff’s one-year-out check. Creation leverage (C5): **wins** the PDF form. 

## **Settling test** 

MGEC through-unsecured creation leverage must equal 4.27x (PDF U7). Lease gap by archetype: where the methods differ by more than 0.5x, keep the one that tracks the spread residual better out of sample. Breach rate by headroom band on matured loan tests. 

## **Status** 

**Partial** . Built: gross, net and lease-adjusted leverage (liability method), cash and after-capex coverage, FCCR without amortisation, FFO and FOCF to debt, S&P and Kricheff ratio panels, covenant headroom and tier where a covenant is disclosed, bond table. Partial: covenant wiring (only covenants the filings state). Missing: face by tranche and rank, creation leverage, pension and OPEB, notching, the claims view, the LME score. Check that the debt tag excludes finance leases, or they count twice. 

## **CRWV** 

Debt 35,551m; lease liabilities 16,540m; leverage 9.45x; lease-adjusted 8.94x; net 7.99x; after-capex coverage _−_ 12 _._ 79 (capex exceeds EBITDA); FCCR 0.54. Four senior unsecured bonds, 2030 to 2032, at 88.8 to 93.7 and 661 to 776 bp. 3.7bn of debt sits in ring-fenced vehicles that hold 18.2bn of assets: structurally ahead of the parent bonds on those assets. 

## **6 S6 Two clocks** 

**Purpose.** Compare when fixed charges fall due with when signed contracts pay, to size the part of the debt that is a bet on renewal. 

## **What each group contributes** 

- **G1** M4.7 gives the formulas, the features and five rules (read schedules as filed; a 10-Q ladder starts with the rest of the fiscal year; state every assumption; build the downside from the main risk flag; read the shortfall as a lower bound). Gatto has no such measure; the nearest are the maturity schedule (Figure 8.4, p. 229) and leases (pp. 267–268). The PDF has none either; its closest rule is R53 (forecast to the next material contractual change). 

- **G2** Built: `hy/clocks.py` , `scripts/clock_case.py` , the prose parsers in `hy/sources/clock_ inputs.py` . Source card: Radhakrishnan (2026): AI capacity providers carry long fixed leases that start on dates they do not control, against shorter and concentrated contracts; unsecured debt is a bet on renewal. 

- **G3** `credit-model-standards` : for customer concentration, model the loss of the top customer (revenue, margin, working capital). The clocks run this as their downside. 

- **G4** S&P (Ch. 6, 7): forecast beyond the maturity when refinancing risk exists; acceleration and cure timing (30 days for interest). Kricheff (Ch. 8, 13, 23): accreting and PIK debt raise the 

24 

claim without cash; bond coupons are lumpy (semiannual), so map cash against payment dates in distress. 

## **Algorithm** 

1. Put every fixed obligation on one yearly grid from the filing date: leases in force, signed leases not started, debt principal, interest on the falling balance, purchase commitments. Read each ladder as filed; check it against its stated total. 

2. Put the RPO on the same grid by the filer’s stated windows; spread the rest over a stated tail. 

3. Choose the margin _m_ as the EBITDAR margin; add a 20% stress margin. 

4. Compute the centres _DO_ , _DR_ , the gap, the breakeven margin, cover, shortfall, the renewaldependent share and its size in years of EBITDA. 

5. Downside: remove the top customer’s share of RPO (customer shares from XBRL; RPO split assumed equal to revenue split). 

6. If RPO is below one year of revenue, skip the revenue clock and report the cost clock against today’s EBITDAR held flat. 

7. Pass `revenue_runoff` and the largest contract expiry to S12 as event dates. 

## **Metrics** 

$$
D_O = \frac{\sum_t (t+\frac12) O_t}{\sum_t O_t},\quad D_R = \frac{\sum_t (t+\frac12) R_t}{\sum_t R_t},\quad gap = D_O - D_R,\quad m^{*} = \frac{\sum_t O_t}{\sum_t R_t}.
$$

_Intuition._ the centres of the two clocks; how many years the charges outlast the contracts; and the margin at which signed contracts pay every charge (above 1, no margin is enough). 

_Symbols. Ot_ fixed obligations in year _t_ ; _Rt_ RPO booked in year _t_ . 

$$
\begin{gathered}
cover = \frac{m\sum_t R_t}{\sum_t O_t},\qquad short = \max\Big(0,-\min_t \sum_{s\le t}(mR_s - O_s)\Big),\\
share = \frac{\sum_{t > T^{run}} O_t}{\sum_t O_t},\qquad yrs = \frac{share\cdot\sum_t O_t}{E}.
\end{gathered}
$$

_Intuition._ the share of charges that contracts pay; the largest cash hole that renewals or new debt must fill; the share due after the contract book is gone; and that amount in years of today’s EBITDA. 

_Symbols. m_ EBITDAR margin; _T[run]_ year by which 99% of RPO is booked; _E_ LTM EBITDA. 

## **Bands** 

_m[∗]_ : _<_ 0 _._ 6 / 0.6–1.0 / _>_ 1 _._ 0. _cover_ : _>_ 1 _._ 0 / 0.7–1.0 / _<_ 0 _._ 7. _share_ : _<_ 15% / 15–30% / _>_ 30%. _yrs_ : _<_ 2 / 2–5 / _>_ 5. All v0. 

## **Inputs** 

_Data:_ XBRL ladders, uncommenced lease total, RPO, customer shares, LTM EBITDA and lease cost. _Documents:_ 10-Q prose for commencement windows, lease terms, RPO windows. _Analyst:_ tail lengths, RPO timing after the last window, the stress margin. 

## **Outputs** 

`duration_gap` , `breakeven_margin` , `coverage_contracted` , `renewal_dependent_share` , `renewal_ dependent_ebitda_years` , `max_cum_shortfall` , `years_of_ebitdar` , scenario and sensitivity tables. 

## **Where groups disagree** 

No group disagrees on the measure. One gap: M4.7 says three clock features enter the fair spread 

25 

model. The fair line uses only leverage. **Rule:** until the M7.2 model exists, the clocks enter as estimate E5 of the combined score and as risk metrics in the pair (S9). 

## **Settling test** 

Decision page `2026-10-22-duration-mismatch` : `renewal_dependent_ebitda_years` must have a positive partial correlation with spread after the M7.2 features, and a positive rank IC for spread change around renewal dates. Code tests: `tests/test_clocks.py` (11) and `tests/test_clock_ inputs.py` (19). 

## **Status** 

**Built** . Missing only the link into a fair spread model. 

## **CRWV** 

Charges 106.4bn against RPO 103.7bn; centres at year 5.5 and 2.6 (gap 2.9 years); breakeven margin 1.03 against an EBITDAR margin of 0.77; cover 0.75; 31% of charges (32.6bn) after the runoff; largest shortfall 26.7bn. If the top customer stops paying: cover 0.48, shortfall 55.4bn. 

## **7 S7 Economic stories and cases** 

**Purpose.** Project the issuer under several company cases inside five macro stories, and weight them so the expected numbers carry the odds of each story. 

## **What each group contributes** 

- **G1** Gatto step 4 (Chapter 10, pp. 283–318): management, base and downside cases (p. 285); the base case is a coin toss (p. 285); probabilities by judgement (p. 311); if the downside looks likely, it becomes the base (p. 311). M5.1 engine; M5.2 macro logistic of a large EBITDA fall; M5.3 forward features; M5.4 forecast linkage (registry, five paths, Bayes update, refinance at the forward Treasury plus fair spread). F6: six cases, mechanics F6.1–F6.5, phase vote and weight table, archetype multipliers, F6.6 promotion, F6.9 fallback order, F6.10 Bayes. PDF: horizon must reach the next material refinancing (R53); eight forecast items (P10); separate cash and face-debt recursions (E38, E39); states must include default (R60); reverse stress. 

- **G2** Built: the forecast registry ( `hy/forecasts.py` ); the path builder ( `hy/macro.py` ); the case grid ( `hy/forward.py` ); `scripts/scenarios.py` with its v0 defaults. Forecast cards: SPF medians and density bins, FOMC SEP, Treasury forwards, SLOOS, TRACE HY level are live; agency default forecasts, fed funds futures, ICE OAS, guidance, consensus and sector decks are stubs. 

- **G3** `credit-model-standards` and `hy-model-standards` : the downside comes from the issuer’s own main risk; a severe case combines a revenue fall, a margin squeeze and working-capital stress; report first breach quarter, peak leverage, trough FCF and runway; tag a recovery shape ( `v` , `u` , structural, customer replacement); roll debt per tranche; interest on last quarter’s debt, no solver. Adaptation: the “lender case with a conservative tilt” does not transfer (K3); public HY guidance leans optimistic. 

- **G4** S&P (Ch. 6, 9): base, stress and default cases; stress the worst credible case, not a soft one (“it is too easy to remain too soft”); front-load a 10–30% revenue drop with fixed costs for high-risk issuers; cyclicals use their historical band (Honda: EBITDA down about 50%; volumes _−_ 20%, _−_ 10%, +5%, +10%, +15%); the default point is _E − T[c] − K < I_ + _Am_ ; three default types set how far cash flow falls. Kricheff (Ch. 12, 13, 21): drive revenue top down; run solve-for cases (the EBITDA fall that makes FCF negative); a rate shock for floating debt and refinancing; event horizons of 6–18 months with probabilities; base model pays scheduled amortisation and keeps the rest as cash. 

## **Algorithm** 

26 

1. Read the registry at _t_ . For GDP and CPI, fit a normal per horizon from the 10th and 90th percentiles, widened by each source’s error record. 

2. Split the standardised GDP–CPI plane into five regions (soft landing, recession, higher for longer, disinflation rally, stagflation) with cuts at the 20th and 80th percentiles. The mass of each region is the forecast probability of the path. 

3. Vote the phase from the six F6 indicators (scaled when some are missing). Take the phase prior. Posterior = prior _×_ mass, normalised. Record all three. 

4. Build each path’s rates (policy by a Taylor-type shift; yields as forwards plus a growth and a policy part) and HY spread. 

5. Build the cases: base from trailing growth (consensus when licensed), moderate downside from the archetype template, severe (1.5 _×_ the decline, a year longer, margin below the trough), upside as the mirror; M3 adds a loss-of-contract branch. Add the S&P default case: the path that first meets the default point. 

6. Run every case under every path for 8 quarters (12 when a maturity is inside 3 years). Cash and face debt run apart; a shortfall uses cash above the minimum, then the revolver; a maturity refinances at the forward Treasury plus fair spread when _p[access] >_ 0 _._ 5, else it fails and the claims view takes over. 

7. Run capex twice: maintenance only, and committed (K14). 

8. Weight the cases per path from the F6 table with the archetype multiplier; apply F6.6 when the downside weight exceeds 0.5. 

9. Per path: expected leverage, its spread, peak downside leverage, lowest downside liquidity, breach, shortfall and refinance probabilities, and the default probability. 

10. Solve-for stress (Kricheff, PDF reverse stress): the EBITDA fall and the spread at which the funding gap first turns negative. 

## **Metrics** 

$$
\sigma_h = \frac{q_{90,h} - q_{10,h}}{2\times 1.2816}\,k_{src},\qquad p(m) = \frac{\pi_{phase}(m)\,mass(m)}{\sum_{m'}\pi_{phase}(m')\,mass(m')}.
$$

_Intuition._ the forecasters’ own uncertainty sets the odds of each story; the cycle phase supplies the base rate. _Symbols. q_ 10, _q_ 90 forecast quantiles at horizon _h_ ; _ksrc_ widen factor from the source’s past band coverage; _mass_ ( _m_ ) probability of region _m_ ; _πphase_ the phase prior. 

$$
\begin{gathered}
Rev_h = Rev_{h-1}(1+g_h),\qquad E_h = Rev_h(1 - v_h - a_h),\\
FCF_h = E_h - K_h - i\,D_{h-1} - T_h - \Delta WC_h,\qquad g_h(m) = g_h + \beta\big(G_h(m) - \bar G\big).
\end{gathered}
$$

_Intuition._ revenue, margin and cash roll forward one quarter at a time; the macro story shifts growth by the sector’s sensitivity. 

_Symbols. g_ growth; _v_ variable cost ratio; _a_ SG&A ratio; _i_ interest rate on last quarter’s debt; _β_ sector sensitivity (v0 by archetype); _Gh_ ( _m_ ) GDP growth on path _m_ ; _G_[¯] trend (1.8%). 

$$
\begin{gathered}
E[Lev_{h}] = \sum_m \sum_s p(m)\,w_s(m)\,Lev^s_h(m),\\
PD^{12}(m) = \max\Big(PD^{fund}(m),\ 0.5\,need\,\big(1-p^{access}(m)\big) + 0.5\,p^{liq}_8(m)\Big).
\end{gathered}
$$

_Intuition._ expected leverage averages over stories and cases; default risk rises when debt must refinance into a shut market or cash runs short. 

_Symbols. ws_ ( _m_ ) case weight; _need_ share of debt due inside 8 quarters; _p[liq]_ 8 weighted chance of a shortfall inside 8 quarters; _PD[fund]_ a fundamental PD from the S&P route (rating implied by ratios, read off the cumulative default table). The code uses a spread-implied PD in place of _PD[fund]_ (C2). 

27 

$$
\text{default point: } E_h - T^c_h - K^m_h < I_h + Am_h .
$$

_Intuition._ S&P: default starts when cash after tax and maintenance capex no longer pays interest and scheduled principal. 

## **Bands** 

_wdown_ : _<_ 0 _._ 25 / 0.25–0.5 / _>_ 0 _._ 5 (F6.6 fires above 0.5). `p_liq_short_8` , `p_refi_4` , `p_breach_4` : _<_ 5% / 5–20% / _>_ 20%. `lev_peak_down` : below the distressed multiple is green. 

## **Inputs** 

_Data:_ the registry (SPF, SEP, Treasury forwards, SLOOS, TRACE HY level); point-in-time quarters; debt ladder; revolver capacity. _Documents:_ guidance (8-K), consensus (licensed), floating terms and floors. _Analyst:_ archetype, sector sensitivity, downside template, the base-case gap to consensus. 

## **Outputs** 

`p_path` (prior, mass, posterior), `case_weights` , `lev_fwd_4` , `lev_fwd_8` , `lev_fwd_sd` , `lev_ peak_down` , `liq_min_down` , `p_refi_4` , `refi_fail_share` , `p_liq_short_8` , `pd_12m` by path, `first_default_q` , `reverse_stress` . 

## **Where groups disagree** 

Debt recursion (C8): M5.1 text lets all FCF repay debt; PDF, Kricheff and the code keep surplus as cash. **Wins:** the PDF; bonds have no sweep. Shortfall order (C9): **wins** Gatto. Base case (K3): **wins** the coin toss. Default state (C10): the PDF requires one; the code has none. **Wins:** add the S&P default case per path with probability _PDH_ ( _m_ ). PD source (C2, B5): **wins** the fundamental route (S&P), because a spread mixes risk premium and liquidity into PD. Downside anchor (K8): **wins** F6 archetype templates; 2008–2009 only without own history. Stress depth (B10): S&P’s 10–30% front-loaded fall is deeper than the v0 A5 template ( _−_ 15%, _−_ 5%). **Wins:** the issuer’s own worst year when known, else the S&P band. 

## **Settling test** 

M11 reliability of _wdown_ ( _m_ ) inside its binomial band. Log score of the realised path: Bayes against prior alone, mass alone and linear pools (decision page `2026-10-22-bayesian-phase-prior` ). Code tests: `tests/test_macro.py` (19), `tests/test_forward.py` (16), `tests/test_forward_paths.py` (18), `tests/test_forecasts.py` (6), `tests/test_scenarios.py` (2). 

## **Status** 

**Partial** . Built: registry, paths, Bayes, cases under paths, weights, F6.6, refinance rule, PD rule (v0), the severe case with committed capex. Missing: consensus and management cases, the fitted logistic, three of six phase indicators, a default state, a fundamental PD, reverse stress, sector betas fitted on history. 

## **CRWV** 

Phase: expansion (three indicators available, none late). Soft landing 86%, higher for longer 8%, disinflation rally 4%, recession 2%, stagflation 0.3%. Base weight 0.64. Expected leverage in 4 quarters 5.73x on the soft-landing path; severe peak 9.28x. Refinancing fails on the recession and stagflation paths. PD 4.0% on soft landing, 10% in recession. 

## **8 S8 Value and recovery** 

**Purpose.** Estimate what the business is worth, in going concern and in default, and what each bond recovers, on the price paid and after the delay. 

28 

## **What each group contributes** 

- **G1** Gatto step 5 (Chapter 11, pp. 319–336): comparables, precedents, DCF, liquidation; the football field (Figure 11.19, p. 332); liquidation rates (p. 332); the market’s value is a check, not an anchor (p. 321). M6: lognormal value, waterfall as a call spread on value, LME adjustment. F7: methods by archetype, distressed multiple, liquidation table, case choice, recovery rules, LME score. PDF: value at the resolution date (E45, R67); do not average across regimes (R63, C11); discount recovery for delay (E109, C12); credit retained new money in an uptier (R98, C13); equity cushion is a sensitivity, not cash (R69). 

- **G2** Built in the process: market TEV only (equity value from Compustat plus debt less cash). Built as a library but not wired: `hy/recovery.py` (methods, lognormal value, closed-form waterfall, LME blend; 18 tests). 

- **G3** `credit-model-standards` and `hy-model-standards` : LTV moves without leverage when the sector multiple moves (6x leverage on a 10x business is 60%; at 8x it is 75%); recompute it each quarter with the current peer multiple. `borrower-monitoring` : refresh public comparables and the implied value each quarter. 

- **G4** S&P (Ch. 9, 10, 11, App. G): name the default type; set priority; choose going concern, discrete collateral, or liquidation; value emergence EBITDA at a peer multiple and by DCF (example: 2/3 DCF + 1/3 multiple); waterfall; discount for time to recovery at 10% ( _<_ 6 months for good collateral, 6–30 months for partial liquidation, _>_ 30 months for unsecured); check against sustainable debt; recovery score 1–5; advance rates by asset; LossStats discounted recoveries (secured bank debt 74%, senior unsecured bonds 37%, subordinated 15%). Kricheff (Ch. 10, 20, 23): TEV from market values; equity cushion = EV multiple over leverage; size the DIP from cash burn; strict priority; subordination agreements move value only between their parties; price today = recovery _/_ (1 + _IRR_ ) _[years]_ (50 at 20% over two years gives 34.7). 

## **Algorithm** 

1. Market check: TEV = equity value + debt _−_ cash; TEV/EBITDA; debt/TEV. 

2. Going-concern value: peer EV/EBITDA on base forward EBITDA (F7.1, F7.2) and DCF of base FCF; blend within going concern only, with stated weights (S&P 2/3 and 1/3 as default). 

3. Default value: name the S&P default type. Emergence EBITDA = EBITDA at the default point less 10% (too much debt, sound business) or less 30–50% (bad business). Multiply by the distressed multiple (F7.3). Less DIP (sized from burn) and administrative claims. 

4. Liquidation value: assets at F7.5 rates (S&P advance rates as a check). Use it when it exceeds the distressed going-concern value, or when the business is beyond repair (F7.8). 

5. Waterfall on the claims view (S5): priority, secured to collateral, unsecured pool, subordination, per entity. 

6. Recovery per bond _Rk_ (undiscounted, claims view) and _Rk[PV]_ (discounted by the S&P time bucket). 

7. LME blend with _πLME_ from the F7 score; credit any retained new money. 

8. LTV through each tranche at low, mid and high value; recompute each quarter with the current multiple. 

## **Metrics** 

$$
TEV = Mcap + D - Cash,\qquad LTV_k = \frac{\sum_{j:\,r_j\le r_k} F_j}{V},\qquad cushion = \frac{TEV/E}{D/E}.
$$

_Intuition._ what the market says the firm is worth; how much of that value the debt through tranche _k_ uses; and how many times the value covers the debt. 

_Symbols. Mcap_ equity market value; _V_ enterprise value from the chosen method. 

29 

$$
V^{def} = \mu^{dist}\,E^{emerg} - DIP - Admin,\qquad R_k = \frac{\min\big(F_k, \max(0, V^{def} - S_k)\big)}{F_k},\qquad R^{PV}_k = \frac{R_k}{(1+k)^{\tau}}.
$$

_Intuition._ value in default pays claims in order; tranche _k_ owns the slice above the claims ahead of it; money received later is worth less today. 

_Symbols. µ[dist]_ distressed multiple; _E[emerg]_ emergence EBITDA; _Sk_ claims ahead of tranche _k_ ; _τ_ years to recovery by the S&P bucket; _k_ discount rate (v0: 15%, between S&P’s 10% and the PDF and Kricheff example of 20%). 

$$
\begin{gathered}
R^{adj}_k = (1-\pi_{LME})R_k + \pi_{LME} R^{LME}_k,\\
score^{rec} = 1 + 1\{R<1\} + 1\{R<0.75\} + 1\{R<0.5\} + 1\{R<0.25\}.
\end{gathered}
$$

_Intuition._ documents can move claims ahead of yours, so blend the clean and the stressed recovery; then grade it on the S&P 1–5 scale. 

## **Bands** 

_LTVk_ at mid value: _<_ 50% / 50–80% / _>_ 80% (F8). Recovery score: 1–2 green, 3 amber, 4–5 red. Debt/TEV: _<_ 0 _._ 5 / 0.5–0.7 / _>_ 0 _._ 7 (v0). Recovery prior when no waterfall exists: senior unsecured 37–40% (S&P LossStats; the code’s v0 LGD of 0.6 agrees). 

## **Inputs** 

_Data:_ market capitalisation, debt, cash, peer multiples (point in time), asset values. _Documents:_ collateral and guarantee terms, intercreditor agreement, LME baskets. _Analyst:_ peer set, distressed multiple, default type, DIP size, time to recovery. 

## **Outputs** 

> `market_tev` , `tev_to_ebitda` , `debt_to_tev` , `v_low` , `v_mid` , `v_high` , `v_default` , `recovery_k` , `recovery_pv_k` , `recovery_adj_k` , `recovery_score` , `ltv_k` . 

## **Where groups disagree** 

Regime (C11, B8): F7.6 averages all methods; the PDF forbids averaging across regimes; S&P blends DCF and multiple. **Wins:** blend only within going concern; keep liquidation apart; state the regime. Timing (C12, B9): **wins** undiscounted for the claims view and discounted for price, jump-to-default and S15. New money (C13): **wins** the PDF. Valuation of equity (G3 LTV, Kricheff cushion, PDF R69): no conflict; the cushion is a sensitivity, not cash. 

## **Settling test** 

Recovery error by rank and archetype on resolved cases (F13). `recovery_pv_k` against TRACE prices 30 days after default. PU Corp uptier with 200 of retained new money. Library tests: `tests/test_recovery.py` (18). 

## **Status** 

**Partial** . Built: market TEV, TEV/EBITDA, debt/TEV, and a v0 discounted recovery used for the loss on price. Partial: recovery wiring (no waterfall on the claims view yet). Missing in the process: the value methods, the waterfall, LME, LTV. The library exists and is tested. 

## **CRWV** 

Market capitalisation 54.8bn; TEV 84.9bn; 22.6x LTM EBITDA; debt/TEV 0.42. No recovery estimate exists. 

30 

## **9 S9 Relative value and the pair** 

**Purpose.** Find the spread a bond should pay against its peers and its own capital structure, and measure how far and how fast the market spread should move toward it. 

## **What each group contributes** 

- **G1** Gatto step 7 (Chapter 13, pp. 366–414): risk is PD times LGD (p. 119); relative value against rating indices, peers and the issuer’s own tranches, with the risk measure beside the spread (HCA, pp. 412–413: 172 bp a turn adequate, 35 bp a turn not). M7.2 two-stage fair spread with monotone constraints; M7.3 conformal band; M7.4 spread per turn; M7.5 AR(1) half-life. F9 spread row; F10 S1 and S4. PDF: never feed the bond’s own price into the fair model (R169, C14); issuer weights; leave the bond out of its own curve (R171); error-scaled residual _Z_ = _e/u_ (E140); convergence and cost hurdle (E141); spread per turn and its trap (E107, R136, Case B). 

- **G2** Built: issuer curve (spread linear in maturity) and its 5-year point; the fair line of log 5-year spread on lease-adjusted leverage across the issuers in the run; the pair report (spread per unit of four risks, a vote, a weekly AR(1) half-life of the pair gap, convergence alpha, and the pair under each path). 

- **G3** No skill covers relative value; the skills target loans held to maturity. 

- **G4** Kricheff (Ch. 8, 21): spread to worst, not to maturity; spread per turn = STW over bond-level leverage; one sheet per security (STW, bond-level and total leverage, FCF/debt, EV cushion, spread per turn, call, size, rating); junior notes must pay more per turn than senior notes, an inversion needs a reason; never trust the widest spread per turn alone (DataFone: 7x total leverage, FCF/debt 0.1%, minimal cushion); compare with an index, CDS, IG comparables. S&P (Ch. 11, App. C, D): spread = PD + recovery + liquidity and supply; compare each bond’s OAS with the rating composite at the same maturity; map an internal score to a buy level. 

## **Algorithm** 

1. Per issuer: fit _s_ = _ai_ + _biT_ on its senior unsecured bonds (all seniorities if fewer than two); read the 5-year point. Use spread to worst once call schedules exist (Kricheff, C18). 

2. Fair line across the run: log _s_ 5 = _a_ + _b Lev[lease]_ + _ε_ , weighted one per issuer. Residual _εi_ . Later: the M7.2 model with monotone constraints, no own price (C14). 

3. Error scale _u_ : leave-one-issuer-out residual standard deviation (later: conformal by rating and liquidity cell). _Z_ = _ε/u_ . 

4. Leave-one-out issuer curve for each bond with at least three same-rank bonds (PDF U46): within-issuer cheapness. 

5. Spread per turn per security on bond-level and total leverage (Kricheff). Read it only beside FCF/debt and the EV cushion (trap guard). 

6. Pair: for issuers _a_ and _b_ , spread per unit of each risk (lease-adjusted leverage, renewaldependent EBITDA years, breakeven margin, duration gap). The verdict holds only where the metrics agree. 

7. Pair gap history: weekly mean of the 5-year spread gap; AR(1) _ρw_ ; half-life; share that closes in the horizon. 

8. Pair alpha under each path: long alpha minus short alpha (from S10), DV01-neutral at 5 years; print the jump-to-default ratio beside it (M9.3). 

## **Metrics** 

$$
\log s_{5,i} = a + b\,Lev_i + \varepsilon_i,\qquad s^{fair}_i = e^{a + b\,Lev_i},\qquad Z_i = \frac{\varepsilon_i}{u}.
$$

_Intuition._ more leverage should pay more spread; the residual is how much more (or less) the market pays than the line says, in units of the line’s own error. 

31 

_Symbols. s_ 5 _,i_ issuer _i_ ’s 5-year G-spread; _Levi_ lease-adjusted leverage; _a_ , _b_ OLS coefficients; _u_ leave-one-out residual standard deviation. 

$$
SPT_b = \frac{STW_b}{Lev^{thr}_b},\qquad slope_{a,b} = \frac{s_a - s_b}{r_a - r_b},\qquad h_{1/2} = \frac{\log 2}{-\log\rho_w}.
$$

_Intuition._ pay per turn of the leverage that sits at or ahead of the bond; the extra pay per unit of extra risk between two issuers; and how long half the pair gap takes to close. 

_Symbols. STW_ spread to worst (G-spread today); _Lev[thr]_ debt through the bond over EBITDA; _r_ a risk metric; _ρw_ weekly AR(1) coefficient of the gap. 

$$
gap^{bp} = s_{L}\,(1 - e^{-\Delta\varepsilon}),\qquad \alpha^{pair} = D_5\,(1 - \rho_w^{26})\,gap^{bp}.
$$

_Intuition._ the long leg is cheap by this many bp net of the short; the part that closes in six months, times duration, is the convergence gain. 

_Symbols. sL_ long leg’s 5-year spread; ∆ _ε_ residual gap (long minus short); _D_ 5 spread duration at 5 years; 26 weeks in the horizon. 

## **Bands** 

_|Z|_ : above the conformal threshold (v0: 1.0 until cells exist) is a signal; above 2 is strong. Spread per turn: rank inside the archetype; junior below senior per turn is red. Pair votes: all metrics agree is green; a split is amber. Half-life: _<_ 26 weeks green, 26–52 amber, _>_ 52 red. 

## **Inputs** 

_Data:_ TRACE yields, maturities, seniority; Treasury curve; lease-adjusted leverage; clock metrics. _Documents:_ call schedules (for STW and OAS). _Analyst:_ pairs; peer set by archetype. 

## **Outputs** 

> `s5_bp` , `fair_s5_bp` , `resid_log` , `z_rv` , `curve_resid_bp` , `spt_bond` , `spt_total` , `pair_price_of_ risk` , `pair_votes` , `half_life_weeks` , `pair_alpha_bp` , `jtd_ratio` . 

## **Where groups disagree** 

PD in the spread (C2, B5): G1 M7.1 builds the fair spread from PD _×_ LGD _×κ_ ; Kricheff and S&P treat spread as relative value only; the PDF forbids the PD mapping. **Wins:** the anchor stays only as an offset inside M7.2; the gate reads relative value, not a PD. Spread per turn (B11): Kricheff uses STW and bond-level leverage; the code uses G-spread and total leverage. **Wins:** print both bond-level and total, and require FCF/debt _>_ 0 and cushion _>_ 1 before the figure counts (DataFone trap). Own price (C14): **wins** the PDF. 

## **Settling test** 

CLAUDE.md definition of done: positive rank IC after costs in three of four cycles (2008, 2015, 2020, 2022). Current evidence ( `docs/writeup/backtest_alpha.tex` , 2008–2026): the fair line passes the cycle bar (positive in all four windows), but after cost it ranks below “buy the widest” (IC 0.21 against 0.22 at 3 months; 0.25 against 0.29 at 6 months). The leverage residual adds an IC of 0.036 ( _t_ 2.2) beyond the spread rank. Calendar 2008 and 2015 are negative for every rule. The fair line keeps a small weight until it beats the widest rule; the lease adjustment (not in the backtest) is the first change to test. Code tests: `tests/test_rv.py` (7), `tests/test_backtest.py:: test_fair_line_residuals_and_pooled_rho_recover_the_truth` , `tests/test_fairspread.py` (13, library). 

## **Status** 

**Partial** . Built: issuer curves, the one-variable fair line, the pair report. Missing: the M7.2 model, 

32 

conformal bands, _Z_ with a documented error scale, leave-one-out curves, spread to worst, spread per turn by bond, rating-index benchmark, JTD pair ratio. 

## **CRWV** 

5-year spread 739 bp against a fair 574 bp: cheap by 165 bp. Fair line log _s_ = _−_ 5 _._ 64 + 0 _._ 312 _Lev_ on 8 issuers. Pair with ORCL: CRWV pays more per unit on all four risk metrics; long CRWV, short ORCL; gap 159 bp; weekly _ρ_ 0.959, half-life 16.7 weeks; 66% closes in six months; convergence gain 388 bp of price; pair alpha 372 bp a year, weighted over paths. 

## **10 S10 Expected alpha** 

**Purpose.** Turn the mispricing into the return a hedged long earns over six months, after expected default loss and trading cost, averaged over the macro stories. 

## **What each group contributes** 

- **G1** M7.5: carry, convergence at the measured half-life, expected loss, event P&L, cost; `alpha_sd` and information ratio. F9 G3: alpha after cost above zero. PDF: full scenario repricing with default inside the cash flows (E135, R164, C3); loss on the price paid (E149); cost hurdle (E141); a constant hazard does not give a five-year PD (R166, C4). 

- **G2** Built: `hy/alpha.py` and `scripts/scenarios.py` : spread-proportional hedge, fair spread scaled by each path’s HY spread, PD from the scenario rule, cost of 20 bp of spread times duration. 

- **G3** No skill gives an expected return; the private credit skills judge debt service, not price. 

- **G4** Kricheff (Ch. 8, 14, 18): yield to worst is the base return; total return to an event (tender, call, recovery) by IRR; blended takeout price across call, clawback and tender; a call caps the upside. S&P (Ch. 11, App. G): _EL_ = _PD × LGD × EAD_ with cumulative PD by rating from the default table (BB 14.8% and B 32.0% at five years); discount recoveries for time. 

## **Algorithm** 

1. For each path _m_ : fair spread _s[fair]_ ( _m_ ) = _s[fair]_ 0 _× S_ ( _m_ ) _/S_ 0; hedge ratio _β_ : estimated from history ( _∂s/∂S_ by bucket), 1 until then (K15); the code uses _s/S_ 0, which sets carry to zero. 

2. Carry: ( _s − βS_ 0) _h_ . 

3. Convergence: _D_ (1 _− ρ_[4] _[h]_ )( _s − s[fair]_ ( _m_ )); _ρ_ from the issuer’s residual history when 8 points exist, else 0.85 a quarter. 

4. Default loss on price: _PDh_ ( _m_ ) _L[def] − β EL[idx]_ ( _m_ ) _h_ , with _L[def]_ from S8 ( _R[PV]_ against the dirty price). Use the S&P cumulative curve for _PDh_ beyond one year. 

5. Event P&L from S12 (zero until built). 

6. Weight by _p_ ( _m_ ); subtract the round-trip cost; record the dispersion across paths. 

7. Size it: pass the net alpha through the S14b calibration before it reaches S15 or position size. 

8. Cross-check by full repricing of the bond’s cash flows in each path and default state (S15); report the gap between the two. 

## **Metrics** 

$$
\begin{multlined}[0.9\linewidth]
\alpha_h = \sum_m p(m)\Big[(s - \beta S_0)h + D(1-\rho^{4h})\big(s - s^{fair}(m)\big)\\ - PD_h(m)\,L^{def} + \beta\,EL^{idx}(m)\,h\Big] + E[\Delta P^{ev}] - c .
\end{multlined}
$$

_Intuition._ the bond pays its spread, the hedge costs the market’s spread, the mispricing closes at its measured speed, and defaults take their share of the price paid; alpha is what is left. 

33 

_Symbols. s_ bond spread; _S_ 0 index spread now; _β_ hedge ratio; _h_ horizon in years (0.5); _D_ spread duration; _ρ_ quarterly persistence; _PDh_ = 1 _−_ (1 _− PD_[12] ) _[h]_ for _h ≤_ 1; _EL[idx]_ ( _m_ ) = _S_ ( _m_ ) _/κ_ ; _c_ = 20 bp _×D_ . 

$$
L^{def} = \frac{P^d/100 - R^{PV}}{P^d/100},\qquad JTD = N\Big(\frac{P^d}{100} - R^{PV}\Big),\qquad IR = \frac{\alpha}{sd_m(\alpha(m))}.
$$

_Intuition._ loss as a share of the money paid, not of face; the instant loss on default; and alpha per unit of disagreement across the stories. 

_Symbols. P[d]_ dirty price; _R[P V]_ discounted recovery per unit of face; _N_ face held. 

## **Bands** 

_α_ after cost: _>_ 100 bp a year green, 0–100 amber, _<_ 0 red (F9 G3 needs _>_ 0). _IR_ : _>_ 1 / 0.5–1 / _<_ 0 _._ 5. 

## **Inputs** 

_Data:_ spread, duration, path spreads and probabilities, PD by path, TRACE price. _Documents:_ call schedule (caps the upside). _Analyst:_ recovery, delay and discount rate (v0), cost. 

## **Outputs** 

`alpha_bp_yr_before_cost` , `alpha_bp_yr_after_cost` , `alpha_by_path` , `carry` , `converge` , `loss` , `cost_bp_yr` , `alpha_sd` , `info_ratio` , `l_def` , `jtd_per_mm` . 

## **Where groups disagree** 

Default loss (C3): **wins** the PDF: loss on price, discounted; full repricing for the number that enters S15. PD over the horizon (C4, B5): **wins** constant hazard up to one year, the cumulative table beyond. Hedge ratio (K15): the code hedges with _β_ = _s/S_ 0, which sets carry to zero; the backtest hedges with _β_ = 1 and finds carry is the best ranker. **Wins:** one _β_ for prediction and test, estimated from history ( _∂s/∂S_ by bucket, M9.3), with _β_ = 1 until then; carry then enters as E0. Return measure (B12): Kricheff ranks by yield to worst; the PDF says a promised yield is not an expected return (R14). **Wins:** the PDF; yield to worst is an input (the call cap), not the measure. 

## **Settling test** 

Regress realised hedged returns on predicted alpha (Mincer–Zarnowitz) by price bucket (below 90, 90–103, above 103). Current evidence: slope 0.07–0.08 over 2008–2026 (0.25–0.31 in 2019– 2026), with no loss term. Pass: the slope rises toward 1 once the loss on price is on. `tests/ test_alpha.py` (6), `tests/test_backtest.py::test_mincer_zarnowitz_recovers_truth_and_ flags_overconfidence` . 

## **Status** 

**Partial** . Built: the M7.5 sum with v0 inputs; loss charged on price ( _L[def]_ with recovery discounted for delay, v0 _R_ = 0 _._ 4, _τ_ = 1 year, _k_ = 15%). Missing: recovery from the claims view, event P&L, call cap, the cumulative PD curve, a measured _ρ_ per issuer. 

## **CRWV** 

376 bp a year before cost, 226 after (cost 149). By path: soft landing 361, higher for longer 428, disinflation rally 280, recession 951, stagflation 968. Alpha rises in the stress paths because the hedge and the fair spread scale with the index: a known limit of the v0 rule. 

## **11 S11 The gate: price against view** 

**Purpose.** Decide whether the view is a trade call or only a credit opinion, by asking what the price implies and whether the view differs from it by more than the noise. 

34 

## **What each group contributes** 

- **G1** F9: the thesis-against-implied table and rules G1–G9 (gap above noise; dated catalyst; return above cost and event budget; clean state; price regime below 80 or above 1,000 bp; signs agree; call type; invalidation; size). PDF: a score or wide spread never waives an unfinished stage (R3, R88); no favourable output exempts a candidate from the comparison against alternatives (R88). 

- **G2** Built: five rows (PD, leverage the spread prices, spread against fair, rating, recovery); G1, G3 and G6 are computed; the call is “watch” or “pass”. 

- **G3** `credit-memo-standards` : risks with mitigants; a memo without the key risk fails. Adaptation: the IC advocacy tone does not transfer; a “pass” must be a normal outcome (K9). 

- **G4** S&P (Ch. 4, 10): base the decision on the three to five issues that matter; uncertainty means a more conservative call; soft factors can only lower a grade; “would you lend your money to this?”. Kricheff (Ch. 24, 25): the snapshot order (business, cap table with liquidity, CFO against capex, adjusted EBITDA and leverage, TEV); keep credit quality apart from relative value; yield does not compensate for poor credit; do not decide on ratio sorts alone. 

## **Algorithm** 

1. Fill the table rows: market implies, analyst view, gap, noise. Rows: spread against fair; leverage the spread prices; EBITDA in 4 quarters; recovery; rating implied by spread against rating implied by ratios (S&P medians); catalyst probability; PD at the current price of risk (shown, not counted, until _κt_ is fitted; C2). 

2. G1: at least one counted row has _|gap| > noise_ . 

3. G2: a dated catalyst and a horizon. Without one, write “credit opinion” and stop. 

4. G3: expected alpha after cost _>_ 0 and above the event budget. 

5. G4: no event in the last five days. G5: below 80 or above 1,000 bp, switch the rows to price and recovery. 

6. G6: counted rows agree in sign. 

7. Credit floor (G4 books): if the S5 or S4 red count is at least three and the recovery score is 4 or 5, the call cannot be “long” on relative value alone; it needs a named catalyst that cures the red items. 

8. G7 type, G8 invalidation (one observable, threshold, date), G9 size. 

9. Call: long, short, watch, or pass. Only S15 turns “long” into an allocation. 

## **Metrics** 

$$
Lev^{impl} = Lev + \frac{\log(s/s^{fair})}{b},\qquad PD^{\kappa} = 1 - e^{-s/(\kappa\,LGD)},\qquad G1 = \bigvee_{r\in counted} \{|gap_r| > noise_r\}.
$$

_Intuition._ the leverage at which the fair line would charge today’s spread; the PD the spread implies at a stated price of risk (display only); and the gap test. 

_Symbols. b_ fair-line slope; _κ_ price of risk (v0: 2); _noiser_ : for the spread row, _u · s[fair]_ ; for the leverage row, _u/b_ ; for the PD row, 0.5 _×_ the implied PD (v0, no decision page yet). 

## **Bands** 

Pass or fail per rule. The call needs G1, G2, G3, G6 and G8. 

## **Inputs** 

_Data:_ S9 residual and error scale, S10 alpha, S7 PD. _Documents:_ event calendar. _Analyst:_ catalyst, invalidation, call type. 

35 

## **Outputs** 

`gate_table` , `G1` – `G9` , `call` , `call_type` , `invalidation` , `direction` . 

## **Where groups disagree** 

The PD row (C2): **wins** the PDF; the row is shown but not counted. Memo tone (K9): **wins** F12. Soft factors (B4): S&P lets them only lower a grade; F9 has no such rule. **Wins:** S&P’s one-way rule, added as the credit floor in step 7, because the gate exists to stop false positives. 

## **Settling test** 

Hit rate and realised return of “watch” calls against “pass” calls on held-out months. The C2 regression of default frequency on implied PD. No code test covers `step_gate` . 

## **Status** 

**Partial** . Built: the spread, leverage and breakeven-default rows; the spread-to-PD row is shown but does not vote (C2); G1, G2 (as an open question), G3, G6. Missing: G4, G5, G7, G8, G9; the rating and recovery rows; the credit floor. 

## **CRWV** 

In the first run: the spread-to-PD row read 6.0% against a view of 4.1% (now shown, not voting); leverage row 9.75x priced against 8.94x (below noise); spread row 739 against 574 bp, gap 165 bp against noise 160 bp, passing by 5 bp. The call was “watch”. The breakeven-default row now votes in place of the PD row; the rerun sets its value. 

## **12 S12 Events and monitoring** 

**Purpose.** List every dated event that can move the bond, price each outcome, and watch each name each quarter for drift toward trouble. 

## **What each group contributes** 

- **G1** M9: event taxonomy, outcome probabilities under each path, ∆ _P_ ( _o, m_ ) by re-evaluation, event VaR, limits. F11 playbooks (before, inside, after); a missed event is a defect (F11.4). Gatto: ratings lag prices (p. 274); forced sellers after a downgrade (p. 418); LME cases (pp. 498–513). PDF: event pro forma with completion and failure branches (P21, E113); abnormal spread shock and Gatto’s spread retracement (E144, U48). 

- **G2** Built: next results date (filing cadence) and the next debt bucket. Library: `hy/events.py` (event matrix, VaR, limits; 30 tests), not wired. 

- **G3** `borrower-monitoring` : read the package quarterly; trajectory per line (revenue, gross margin, opex, EBITDA, cash); one quarter is an observation, three to four a trend; watchlist tiers (watch closely at 10–15% below plan; watchlist at 20–25% below plan or within 5–10% headroom or thin liquidity; workout on breach); questions must trace the cause (second-order). `covenant-compliance` : step-downs on quarter ends; quarter-end revolver window dressing. Adaptation: public HY has no plan from the sponsor; use the analyst base case (or consensus) as “plan”. 

- **G4** Kricheff (Ch. 14, 16–18, 20): acquisition pro forma (never full credit for synergies; check where the target sits and how it is funded; existing junior bonds may be primed); issuer acquired (101 put is a floor only below about 101); IPO (primary against secondary shares, use of proceeds, clawback); call and refinancing quick test; tenders at T+50 to T+100; review at once when the stock or a peer moves 15% or more. S&P (Ch. 4, 5, 7, 11): sudden cash-call triggers; rating triggers; seventeen governance flags; management’s promises against actions; Altman Z-score and migration matrices as early warnings. 

36 

## **Algorithm** 

1. Calendar for the next 90 days: results, covenant tests and step-downs, maturities and springing dates, call dates, rating reviews, index dates, contract expiries (from S6), macro releases. 

2. For each event: outcomes, _P_ ( _o | e, m_ ) from the cases, ∆ _P_ ( _o, m_ ) by re-evaluating S9 and S10 with the outcome’s features. Event VaR; cap size to the event budget. 

3. Corporate events (Kricheff): build the pro forma for completion and failure; count synergies at a stated haircut; check incurrence capacity (S5); mark which bonds are primed. 

4. Quarterly monitoring (G3): actual against base case per line; tier the name: watch closely, watchlist, workout. Escalate early on a falling headroom path. 

5. Market triggers: abnormal spread shock against the HY level (PDF E144); stock move of 15% or more (Kricheff); rating action. 

6. After each event: record realised against predicted; clear the event flag after five days; a missed event goes to the defect log. 

## **Metrics** 

$$
\Delta P(o,m) \approx -D\,\Delta y(m) - D^s\big[\Delta s^{sys}(m) + \hat s(x(o,m)) - \hat s(x)\big] + carry_h - 1\{def\}\big(P - 100R^{adj}\big).
$$

_Intuition._ an outcome moves the bond through rates, the market spread, the issuer’s own fair spread, and default. 

$$
dev = \frac{E^{act}_{LTM}}{E^{plan}_{LTM}} - 1,\qquad Shock_t = \Delta s_t - \hat\beta\,\Delta S_t,\qquad Z^{Alt} = 1.2A + 1.4B + 3.3C + 0.6M + 1.0T .
$$

_Intuition._ how far earnings run below the plan; how much of a spread move is the issuer’s own; and S&P’s early-warning score. 

_Symbols. β_[ˆ] 120-day beta of the bond spread to the HY level; _A_ working capital, _B_ retained earnings, _C_ EBIT, _T_ sales, each over total assets; _M_ market equity over book debt. 

## **Bands** 

Watchlist tier from _dev_ : above _−_ 10% performing; _−_ 10 to _−_ 20% watch closely; below _−_ 20%, or headroom under 10%, or the S4 liquidity flag: watchlist; a breach: workout. _|Shock|_ above two residual standard deviations: review. Stock move _≥_ 15%: review. 

## **Inputs** 

_Data:_ filing cadence, debt ladder, TRACE spread history, HY level, equity prices. _Documents:_ indentures (calls, puts, step-downs), 8-K items, rating actions. _Analyst:_ outcome sets, synergy haircut, plan. 

## **Outputs** 

`events_90d` , `event_matrix` , `event_var` , `watch_tier` , `trajectory` , `spread_shock_z` , `questions` . 

## **Where groups disagree** 

Trend length (K13): **wins** both, for different uses. Plan: G3 measures against a sponsor plan that public HY lacks; **wins** the analyst base case. Synergy credit: Kricheff never gives full credit; F3 C8 gives none for analyst EBITDA. **Wins:** F3 for the base; Kricheff’s haircut only in the event pro forma. 

37 

## **Settling test** 

Probability integral transform of realised event-day spread changes against the predicted distribution must be near uniform (CLAUDE.md). Watchlist tier against later downgrades and defaults. Library tests: `tests/test_events.py` (14), `tests/test_events_paths.py` (16). 

## **Status** 

**Partial** . Built: next results and debt due, the quarterly trajectory, the G3 watch tier. Missing: the full calendar, the event matrix in the process, the shock screen, the defect log. 

## **CRWV** 

Next results about 11 November 2026 (estimated); 4,413m of debt due inside half a year. 

## **13 S13 Metrics panel** 

**Purpose.** Put every metric of S2–S12 on one page with a green, amber or red band, red first, and tag each with the group that owns it. 

## **What each group contributes** 

- **G1** F8 catalogue: formula, unit, direction, default bands, consumer; “rank” metrics judged inside the archetype. 

- **G2** Built: eleven F8 metrics with bands. 

- **G3** Headroom bands and trajectory ( `covenant-compliance` ); watchlist tier ( `borrowermonitoring` ); add-back flags ( `ebitda-addback-treatment` ); FCF cross-check ( `hy-modelstandards` ). 

- **G4** S&P ratio medians by rating (FFO/debt, FOCF/debt, EBITDA cover, debt/capital); Kricheff’s pragmatic ratios ((EBITDA _−_ capex)/interest, FCF/debt, EBITDA/debt as the highest rate for 1x cover, market-adjusted debt). 

## **Algorithm** 

1. Read every metric of Section 19 that has a value. 

2. Band it by its rule; “rank” metrics by percentile inside the archetype. 

3. Map four ratios to an S&P-implied rating: for each of FFO/debt, FOCF/debt, EBITDA cover and debt/capital, take the rating whose median is nearest; the implied rating is the median of the four. 

4. Sort red first; print the group of each metric. 

5. Count reds per group. Pass the counts to S11 (credit floor) and S14 (E6). 

## **Metrics** 

The full list is the dictionary in Section 19. The panel score: 

$$
panel = \frac{n_{green} - n_{red}}{n_{banded}},\qquad rating^{SP} = \operatorname{median}_q \arg\min_{g} \big|x_q - med_{q,g}\big|.
$$

_Intuition._ the share of greens less reds; and the rating that the issuer’s ratios look like. 

_Symbols. xq_ the issuer’s value of ratio _q_ ; _medq,g_ S&P 2002 median of ratio _q_ in rating class _g_ . 

## **Bands** 

As in the dictionary. 

## **Inputs** 

Outputs of S2–S12. 

38 

## **Outputs** 

`panel` (metric, value, band, group), `panel_score` , `red_by_group` , `rating_sp_implied` . 

## **Where groups disagree** 

Headroom bands (K5, B6) and concentration (K7) as above. S&P medians are 2002 values for industrials; they are a guide, not a rule (S&P: “guideposts, not deciding factors”). **Rule:** use them for the implied rating only, never as a pass or fail band. 

## **Settling test** 

F13.8: a band that never binds in a year is removed. Rank IC of the panel score against later spread change. 

## **Status** 

**Partial** . Built: eleven metrics. Missing: about forty, the group tag, the S&P-implied rating. 

## **CRWV** 

Red: coverage, FCCR, FCF conversion, FCF/debt, margin trend. Amber: wall cover, refinance score, EQ score. Green: downside weight, refinance probability, shortfall probability. 

## **14 S14 Combined view** 

**Purpose.** Turn every group’s evidence into one expected alpha per issuer and one rank. Section 17 gives the full rule; this section gives the step. 

## **What each group contributes** 

By the user’s bucket weights: G1 45% (liquidity, value, earnings quality, excess over cash); the two clocks 20%; the rest of G2 11.67% (spread level, cases, fair line, pair, panel); G3 11.67%, one-way; G4 11.67% (the S&P score gap and Kricheff’s spread per turn). 

## **Algorithm** 

1. Collect the estimates E0–E13 of Section 17. Drop any that is missing. 

2. Convert each score-type estimate to bp a year: standardise across the issuers in the run, times the cross-sectional standard deviation of E1. 

3. Clip the one-way estimates (E7, E11) at zero from above: soft risks can only lower alpha. 

4. Weighted sum by bucket: G1 0.45, clocks 0.20, G2 rest, G3 and G4 0.1167 each; inside a bucket, the estimates present share its weight in fixed proportions. 

5. Subtract the round-trip cost. 

6. Size it (S14b): _α[sized]_ = ˆ _a_ +[ˆ] _b α[net]_ . The raw number sets the rank; the sized number enters S15 and position size. 

7. The call may be “long candidate” only if _α[sized] >_ 0 and the gate passes. 

8. Rank across the run (F12.1). Record the agreement count and the group shares. 

## **Metrics, bands, inputs, outputs** 

See Section 17. Outputs: `rows` (estimate, group, alpha, weight, contribution), `combined_before_ cost` , `combined_after_cost` , `group_share` , `agree` , `gate_pass` , `rank` . 

## **Where groups disagree** 

Composite form (C15, B13): the PDF wants ablation; Kricheff ends in a category grid; the repo wants IC weights. **Wins:** IC weights with ablation; print Kricheff’s grid label as a reading aid. 

39 

## **Settling test** 

The ensemble’s rank IC after cost must beat E1 alone and the “widest spread” baseline in at least three of four cycles. Today only the fair line has a record, and it does not beat the baseline. 

## **Status** 

**Partial** . Built: E0–E13, one-way clipping, group shares ( `hy/groups.py` ). The user’s bucket weights (Section 17) replace the backtest-led v0 weights in the next run. Missing: the baseline test against the widest rule. 

## **CRWV** 

Under the earlier backtest-led weights: +145 bp a year raw after cost, +11 after calibration. The bucket weights shift weight to the G1 rules and the clocks, where CoreWeave scores poorly, so the figure is likely to fall. The rerun will set it. 

## **15 S14b Size calibration** 

**Purpose.** Scale the predicted alpha to the size that past predictions have actually earned, so that S15 and position size use an honest number. 

## **What each group contributes** 

**G1** M11 validation (reliability of every forecast) and F9 G9 (size by the gap over its noise). **G2** The backtest engine ( `hy/backtest.py` : realised alpha, Mincer–Zarnowitz with Driscoll–Kraay errors, decile calibration, PIT). **G3** None. **G4** None; both books size by judgement. 

## **Algorithm** 

1. Each month, take all past months whose horizon has closed. Pair each prediction _αi,t[net]_[with] its realised hedged alpha. 

2. Fit _α[real]_ = _a_ + _b α[net]_ pooled, with Driscoll–Kraay errors; by price bucket once the loss term is on. 

3. Sized alpha = ˆ _a_ +[ˆ] _b α[net]_ . If[ˆ] _b_ is not above zero by two standard errors, the model may rank but not size: set position scale to the minimum. 

4. Report the PIT histogram; widen or narrow the band so that each decile holds about 10% of outcomes. 

## **Metrics** 

ˆ _b_ (slope; 1 is perfect), _a_ ˆ (intercept; 0 is perfect), PIT decile shares (10% each is perfect). 

## **Bands** 

ˆ _b_ : 0.7–1.3 green; 0.3–0.7 amber; below 0.3 red. Today: 0.079 (red). 

## **Inputs** 

_Data:_ the backtest panel and predictions. 

## **Outputs** 

`mz_a` , `mz_b` , `alpha_sized` , `pit_deciles` . 

## **Where groups disagree** 

None. The M7.5 formula claims a size; the backtest shows the claim is about twelve times too large. The calibration wins over the formula until the loss term and the lease adjustment raise the slope. 

40 

## **Settling test** 

The slope itself, refitted each month out of sample; PIT deciles near 10%. 

## **Status** 

**Built** . The process multiplies the net alpha by the backtest slope[ˆ] _b_ = 0 _._ 079 (standard error 0.054, _a_ ˆ held at 0). The slope is not above zero by two standard errors, so the step reports “rank only, minimum size”. 

## **16 S15 Decision against cash** 

**Purpose.** Compare buying this bond with every other feasible use of the same capital, cash and the current holdings included, and pick the best one inside the risk budget. 

## **What each group contributes** 

- **G1** PDF Step 7 (Section 9): the feasible action set (P17); common-capital terminal wealth (E50–E52); excess over cash (E53, E54); probability of loss and of falling below cash (E56, E57); expected shortfall and its portfolio change (E58, E59); opportunity cost (E60); rules R79–R88 (cash and retention stay valid; no favourable model output exempts a candidate). Gatto: rank each idea against every position and name the one it replaces (p. 369); F1 R8 and F12.2: `replaces_position` . 

- **G2** Nothing built. The inputs exist: S7 paths and PDs, S8 recovery, S9 fair spreads, TRACE prices, the Treasury curve. 

- **G3** `credit-memo-standards` : the base and downside output tables of the memo come from here. Adaptation: the skill assumes a primary loan held to maturity; a secondary bond buyer must also value the exit. 

- **G4** Kricheff (Ch. 6, 21, 25): define the mandate first; compare with other bonds, loans, an index, IG comparables and equity; ask whether a better instrument exists; set the review trigger and the weight. S&P (Ch. 10, 11): report the issuer score (PD) and the recovery score (LGD); their product is expected loss. 

## **Algorithm** 

1. Action set: the top candidates of S14 that pass S11, each current holding (retain), the sale of each holding, and cash. Record exclusions and the reason. 

2. For each action _a_ , path _m_ and state _d ∈{_ survive _,_ default _}_ : probability _q_ = _p_ ( _m_ )(1 _−PDH_ ( _m_ )) or _p_ ( _m_ ) _PDH_ ( _m_ ). 

3. Survive: value at _H_ = remaining coupons and principal discounted at the path’s Treasury yield for the remaining tenor plus the bond’s spread at _H_ (the convergence rule below). Default: 100 _R[PV]_ , no further coupons. 

4. Terminal wealth from the same capital _K_ ; net return; excess over cash. 

5. _µ_ , _π[loss]_ , _π[cash]_ , _ES_ 95; admissible if _ES_ 95 _≤_ budget. 

6. Choose the admissible action with the highest _µ_ . Its opportunity cost is zero; every other action’s is the gap to it. 

7. Write `replaces_position` and the best alternative into the memo. 

## **Metrics** 

$$
W_{a,m,d} = V_{a,H,m,d} + B_{a,0}A + \sum_{u\le H} CF_{a,u,m,d}\,A_u - TC,\quad R^{net} = \frac{W}{K} - 1,\quad X = R^{net} - R^{cash}.
$$

_Intuition._ what the same money is worth at the horizon in each story and state, as a return, and above cash. 

41 

_Symbols. V_ value at _H_ ; _Ba,_ 0 unused cash; _A_ accumulation factor at the cash rate; _CF_ coupons received; _TC_ transaction cost; _R[cash]_ Treasury bill return to _H_ . 

$$
\begin{gathered}
\mu_a = \sum q\,X,\qquad \pi^{loss}_a = \sum q\,1\{R^{net}<0\},\qquad \pi^{cash}_a = \sum q\,1\{X<0\},\\
ES_{95} = \min_z\Big[z + \tfrac{1}{0.05}\sum q\,(L - z)^+\Big],\qquad OC_a = \max_{j\,adm}\mu_j - \mu_a .
\end{gathered}
$$

_Intuition._ the expected excess over cash; the odds of losing money and of doing worse than cash; the average loss in the worst 5% of outcomes; and what is given up by not taking the best admissible action. 

_Symbols. L_ = _−R[net]_ ; ( _x_ )[+] = max( _x,_ 0); “adm” = admissible. 

## **Bands** 

Admissible: _ES_ 95 _≤_ budget (v0: 25% of capital, the PDF Case I value). Act only if _µ >_ 0 and _OC_ = 0. 

## **Inputs** 

_Data:_ TRACE price, coupon, maturity; Treasury curve and forwards; S7 paths and PDs; S9 fair spreads. _Documents:_ call schedules. _Analyst:_ recovery, delay, discount rate, ES budget, transaction cost, the mandate. 

## **Outputs** 

`mu_excess` , `pi_loss` , `pi_cash` , `es95` , `opportunity_cost` , `best_admissible` , `replaces_position` . 

## **Where groups disagree** 

C1: the repo ranks by residual and composite; the PDF decides by terminal wealth. **Wins:** both, in order: S14 ranks, S15 decides. Kricheff sets no cash hurdle; the PDF does. **Wins:** the PDF, because cash is always feasible. 

## **Settling test** 

Decile returns of the S14 rank against returns of the _µ_ -ranked admissible set, net of cost, in each of four cycles. 

## **Convergence rule at the horizon** 

$$
s_H(m) = s_b\,\frac{S_H(m)}{S_0} - \big(1-\rho^{4h}\big)\,\big(s_5 - s^{fair}_5\big)\,\frac{\bar S(m)}{S_0}.
$$

_Intuition._ the bond’s spread moves with the market on each path, and its gap to fair closes only at the measured speed, not all at once. 

_Symbols._ ¯ _sb_ the bond’s spread today; _SH_ ( _m_ ) the index spread at _H_ on path _m_ ; _S_ 0 the index spread today; _S_ ( _m_ ) the path’s mean index spread over four quarters; _ρ_ quarterly persistence (v0 0.85, so about 40% of the gap closes in six months); _s_ 5 _− s[fair]_ 5 the issuer’s gap at 5 years. 

**Current choice: measured speed** , as the code does. **Alternative: full convergence by six months** , 1 _− ρ_[4] _[h] →_ 1. The alternative makes every cheap bond look better and contradicts the backtest, whose calibration slope says gaps close far more slowly than the model’s own sizes assume. Settling test: the realised share of the gap closed after six months, by decile of the gap, on the backtest panel. 

The code also reports a hedged version beside it: rates held at today’s curve, the market move removed, and _β_ = 1 times the index carry less its expected loss subtracted (K15). E10 of the combined score uses the unhedged excess over cash. 

42 

## **Status** 

**Built** . Code: `step_decision` in `scripts/process.py` and `decision_against_cash` , `opportunity_cost` in `hy/alpha.py` . It fills `replaces_position` with the best admissible alternative, cash when no bond beats it. Inputs still v0: recovery 0.4, delay 1 year, required return 15% on a defaulted claim; the claims view and documents replace them. 

43 

## **17 The combined score** 

**The idea.** Each estimate is one witness to the same quantity: the expected alpha of a hedged long over six months, in bp a year. The combination weighs the witnesses in five fixed buckets. A calibration step then resizes the result to the size that history supports. The bucket weights are a user choice (conflict W1); within each bucket, the estimates keep their earlier relative weights. 

**The five buckets and their weights (user choice, 22 October 2026). G1** core process: **45%** . The rules the number must obey (liquidity and refinancing, market value, earnings quality, the default the price assumes) and the excess over cash from S15. **Two clocks (E5): 20%** , as their own bucket. **G2** rest of the built methods (E0, E1, E2, E3, E6): **11.67%** . **G3** skills: **11.67%** , one-way: it can only lower the number. **G4** books: **11.67%** . Two cross-checks that use no repo model. 

## **The estimates and their weights** 

|ID|Estimate|Bucket|Type|How it becomes bp a year|Weight|In|
|---|---|---|---|---|---|---|
|||||||code|
|E4|Default the price|G1|alpha|(_PDκt −PDfund_)_Ldef_; held at zero until _κt_ is|0.00%|yes|
||assumes|||ftted (C2)|||
|E7|Earnings quality|G1|one-|_−_(F3 fags + G3 add-back fags + FCF check|11.25%|yes|
||||way|fag); counted in G1 as the code does|||
|E8|Liquidity and|G1|score|F4 score on the likely path + wall cover (cap 3)|11.25%|yes|
||refnancing|||+ 1{funding gap _≥_0}|||
|E9|Market value|G1|score|_−_debt/TEV|11.25%|yes|
||check||||||
|E10|Excess over cash|G1|alpha|_µ/H_ from S15|11.25%|yes|
|E5|Two clocks|Clocks|score|_−_(fxed charges in years of EBITDAR),|20.00%|yes|
|||||standardised|||
|E0|Spread level|G2 rest|alpha|(_s −S_0), hedge _β_ = 1|4.86%|yes|
||(carry)||||||
|E1|Weighted cases|G2 rest|alpha|Scenario-weighted alpha before cost (S10)|2.92%|yes|
||and stories||||||
|E2|Fair-line|G2 rest|alpha|_D_(1_−ρ_4_h_)(_s −sfair_)_/h_|1.94%|yes|
||convergence||||||
|E3|Pair convergence|G2 rest|alpha|Pair gap closed at its measured half-life, _±_ by|0.97%|yes|
|||||leg|||
|E6|Health panel|G2 rest|score|(_ngreen −nred_)_/n_ on the S13 panel|0.97%|yes|
|E11|Watchlist and|G3|one-|_−_(tier 0–3) _−_1{headroom falling}|11.67%|yes|
||covenant path||way||||
|E12|Ratio-implied|G4|score|_z_(log_s_)_−z_(S&P risk score): a wide spread for|5.83%|yes|
||rating gap|||the score is cheap|||
|E13|Spread per turn|G4|score|log_SPT_ minus the peer median (same GICS|5.83%|yes|
||against peers|||sector, rating class and maturity bucket) if|||
|||||FCF/debt _>_0 and cushion _>_1, else 0|||
||**Total**|||G1 45; clocks 20; G2 rest 11.67; G3 11.67; G4|100%||
|||||11.67|||



Two notes on the table. First, E4 keeps its zero weight inside G1, so G1’s 45% is shared by four estimates. Second, the skills bucket holds only E11, so the whole 11.67% is one-way; E7 is one-way too, but the code counts it in G1. 

44 

## **The rule, in four steps** 

## **Step 1: put every estimate in bp a year.** 

$$
\alpha_j = \frac{x_j - \bar x_j}{sd(x_j)}\,sd(\alpha_{E1})\quad (j\ \text{score type}),\qquad \alpha_j \leftarrow \min(0,\alpha_j)\quad (j\ \text{one-way}).
$$

_Intuition._ a score has no unit, so it borrows the spread of E1 across the run; a soft risk can only subtract (S&P: soft factors only lower a grade). 

_Symbols. xj_ the issuer’s raw score; _x_ ¯ _j_ , _sd_ ( _xj_ ) its mean and standard deviation across the run. 

## **Step 2: weigh the witnesses, bucket by bucket.** 

$$
\alpha^{comb} = \sum_{g} W_g\,\bar\alpha_g,\qquad \bar\alpha_g = \frac{\sum_{j\in g\cap P} w_j\,\alpha_j}{\sum_{j\in g\cap P} w_j},\qquad \alpha^{net} = \alpha^{comb} - c .
$$

_Intuition._ each bucket speaks with its own weight; inside a bucket, the estimates present share it in their fixed proportions. 

_Symbols. g_ a bucket; _Wg_ its weight (0.45, 0.20, 0.1167, 0.1167, 0.1167), renormalised over buckets with at least one estimate present; _P_ estimates present; _wj_ the in-bucket weight; _c_ the round-trip cost in bp a year. 

## **Step 3: size calibration (S14b).** 

$$
\alpha^{sized} = \hat b\,\alpha^{net},\qquad \hat b = \arg\min_b \sum_{i,t} \big(\alpha^{real}_{i,t} - b\,\alpha^{net}_{i,t}\big)^2 .
$$

_Intuition._ if a predicted 100 bp has earned 8 bp in the past, the honest forecast of a new 100 bp is about 8 bp. _Symbols. α[real]_ realised hedged alpha; the fit is the pooled Mincer–Zarnowitz slope from the alpha backtest. Current value:[ˆ] _b_ = 0 _._ 079, standard error 0.054. The slope is not above zero by two standard errors, so the number ranks issuers but sizes nothing beyond the minimum. 

**Step 4: gate and decide.** The call may be “long candidate” only if the S11 gate passes and S15 finds the bond beats cash inside the risk budget. 

## **What the backtest supported, and why the weights differ** 

The alpha backtest (2008–2026, 13,271 bonds) found: 

1. spread level ranks best: IC after cost 0.22 at 3 months and 0.29 at 6 months for “buy the widest”; 

2. the fair line ranks slightly worse (0.21 and 0.25), and the leverage residual adds an IC of 0.036 ( _t_ 2.2) beyond the spread rank; 

3. the size is far too large: calibration slope 0.07–0.08; 

4. the cycle windows all pass, but calendar 2008 and 2015 are negative for every rule. 

The earlier v0 weights followed that evidence (spread level 25%, untested estimates capped at 5%). The user replaced them with the bucket weights above. The new weights put 65% on two blocks that no backtest has scored yet: the G1 rules (45%) and the clocks (20%). Spread level, the best-tested estimate, now carries under 5%. 

## **The tests that revisit the weights.** 

1. The clocks backtest, now running: the rank IC of E5 after cost, on its own and beyond the spread rank, in each cycle window. If E5 does not beat zero beyond spread, its 20% has no support. 

2. A backtest of each G1 estimate (E7, E8, E9, E10) on the same panel, once point-in-time inputs exist for them. 

3. Then the rank-IC rule: _wj,ϕ ∝_ max(0 _, ICj,ϕ[net]_[),][shrunk][toward][the][bucket][weights][with] _[λ]_[=] _N/_ ( _N_ + 36) for _N_ months of history; ablation (drop an estimate whose removal does not lower net IC); and the ensemble must beat the “widest” rule after cost in at least three of four cycles. 

45 

**Reading aid (Kricheff Ch. 25).** Beside the number, print a grid label: credit risk high, medium or low (S13 red count and recovery score); an event qualifier (S12); and the pricing fit (sign of the alpha after cost). It maps to overweight, evenweight, underweight or avoid. It never changes the rank. 

**CRWV.** Under the earlier backtest-led weights, the code gave CoreWeave a raw alpha of +145 bp a year after cost, and +11 bp after calibration. The bucket weights move most of the weight from spread level to the G1 rules and the clocks. CoreWeave’s clocks score is poor (fixed charges near eighteen years of EBITDAR) and its liquidity score is weak. So the combined figure should fall, and may turn negative. Agent one is rerunning; the memo will carry the new figures. 

46 

## **18 Conflicts register** 

Each row records both sides, the rule that wins in this framework, the reason, and the test that settles it. “C” rows come from `research/hyrv_mapping.md` . “K” rows are conflicts that the skills (G3) add. “B” rows are conflicts that the books (G4) add. “Code” says what the code does today. “W1” records the combination weights. The box below says where C2 and C3 stand. 

**C2 and C3, which changed the call, are now resolved in the code.** C2: the row that read a default probability out of the spread (fixed _κ_ = 2, _LGD_ = 0 _._ 6) is shown but no longer votes in the gate; a breakeven-default row votes instead, _be_ = _s/L[def]_ : the yearly default rate at which the spread only pays for its loss on the price paid. C3: default loss is charged on price, _L[def]_ = ( _P[d] /_ 100 _− R[PV]_ ) _/_ ( _P[d] /_ 100), with recovery discounted for delay (v0 _R_ = 0 _._ 4, _τ_ = 1 year, _k_ = 15%). Open: the case PD in S7 still comes partly from the spread, and _κt_ is not fitted. 

|ID|Topic|The two sides; code today|Rule that wins, and why|Settling test|
|---|---|---|---|---|
|C1|What decides|PDF: common-capital terminal|Residual and composite|Decile returns of the|
||the trade|wealth against every feasible|generate and rank|composite against|
|||alternative, cash included|candidates; S15 decides. A|the _µ_-ranked|
|||(E50–E60, R85). Repo: rank by|residual says nothing about|admissible set, net of|
|||residual (M1), composite (M8),|capital use or tail loss.|cost, in each of four|
|||information ratio (F13). Code:||cycles.|
|||rank by combined view; no cash|||
|||comparison.|||
|C2|Spread into PD|PDF R165: never PD from|Keep the anchor as a|Regress realised|
|||OAS_/_LGD. Repo: anchor _κλLGD_|model ofset. Rename the|12-month default|
|||(M7.1), implied PD rows (F8, F9).|row “PD at the current|frequency by bucket|
|||Code: the S11 row is shown and|price of risk”. Drop it from|on implied PD; keep|
|||does not vote; S7 still uses it.|G1 of the gate until _κt_ is|the row only if the|
||||ftted by bucket and date.|slope is near 1.|
|C3|Default loss|PDF: full repricing; loss on price;|Use _Ldef_ =|Predicted against|
|||no double count (E135, R164).|(_Pd/_100_−RP V_ )_/_(_Pd/_100)|realised horizon|
|||Repo M7.5: _PDh LGD_ on face.|in the sum; use full|returns (E171) by|
|||Code: now on price.|repricing in S15.|price bucket.|
|C4|PD term|PDF R166: one-year PD does not|Constant hazard for _h ≤_1|Constant hazard|
||structure|give fve years. Repo: constant|year; agency cumulative|gives 16.8% at 5|
|||hazard.|curve scaled by the issuer|years against the|
||||ratio for 5 years.|table’s 14.16%.|
|C5|Creation|PDF E31: every claim of the layer|PDF; correct for layers|MGEC|
||leverage|at its own price. M4.3: only|with several bonds.|through-unsecured|
|||tranche _k_ at market.||must give 4.27x (U7).|
|C6|Lease leverage|PDF E33, F5: operating lease|Liability method; print 8_×_|Gap between|
|||liability after 2018. M4.3: 8_×_ rent.|beside it.|methods by|
|||Code: liability method already||archetype; where|
|||(`rv_pair.issuer_block`).||above 0.5x, which|
|||||tracks the residual|
|||||better out of sample.|
|C7|Pension|PDF E35: defcit to debt and|PDF, with the|Flag issuers where|
|||expense less service cost to|reconciliation guard (R51);|the two leverage|
|||EBITDA. Repo: defcit to debt|the claims view keeps the|forms difer by more|
|||only.|termination liability.|than 0.25x.|
|C8|Debt recursion|PDF E38, E39: cash and face|PDF (and the code). Fix|Forecast against|
|||debt apart. M5.1 text:|the M5.1 text.|realised net debt 4|
|||_Dh_ =_Dh−_1_−FCFh_+_Drawh_.||quarters ahead under|
|||Code: already apart; surplus cash||both rules.|
|||accumulates; sweep 0.|||
|C9|Shortfall order|Gatto P11: cash above the|Gatto, after the F4.1|Run both on the run|
|||minimum frst, then the revolver.|trapped-cash haircut. Fix|issuers; report the|
|||F6.1: revolver frst. Code: Gatto’s|F6.1 text.|change in|
|||order.||`liq_min_down`.|



47 

|ID|Topic|The two sides; code today|Rule that wins, and why|Settling test|
|---|---|---|---|---|
|C10|Scenario|PDF R60, R61: states must|Keep macro weights; add a|M11 reliability of|
||probabilities|include default; probabilities are|default state per path with|_wdown_(_m_).|
|||judgement. Repo: macro-ftted|probability _PDH_(_m_); label||
|||weights, no default state.|outputs “conditional on||
||||the case set”.||
|C11|Valuation regime|PDF R63: do not average|Average within going|Recovery under|
|||methods across regimes. F7.6:|concern only; keep|mean value against|
|||weighted mean.|liquidation apart; state the|the chosen regime on|
||||regime.|resolved cases.|
|C12|Recovery timing|PDF E109: _R/_(1 +_k_)_τ_. Repo:|Undiscounted for the|`recovery_pv_k`|
|||undiscounted.|claims view; discounted|against TRACE|
||||`recovery_pv_k` for price,|prices 30 days after|
||||JTD and S15.|default.|
|C13|LME new money|PDF R98: credit retained new|Credit retained cash;|PU Corp uptier with|
|||cash. F7: priming debt only.|consume it only in the|200 retained.|
||||severe path.||
|C14|Own price as|PDF R169: never feed the bond’s|Replace with a lagged|Reft with and|
||input|own price into the fair model.|regime fag (price below 80|without; if residual|
|||M7.2: `logprice`.|at _t −_20 days); issuer|variance falls but|
||||weights.|residual IC falls, the|
|||||feature leaked.|
|C15|Composite|PDF R177: no z-score averages|Keep IC weights; add|The ablation, per|
|||without ablation. Repo:|per-estimate ablation; drop|cycle.|
|||IC-weighted composite.|an estimate whose removal||
||||does not lower net IC.||
|C16|Qualitative|PDF R31, R34: risk must change|Scenario route frst; fag|Ablate the vector|
||scores|the forecast; no scores added to|vector only if it passes the|from M7.2.|
|||ratios. M4.4: fag vector into the|R163 admission rule.||
|||fair model.|||
|C17|Organic growth|Gatto E20: remove FX and M&A,|Gatto for `organic_growth`;|Which leads|
|||keep price and mix. M4.1, EQ4:|add `volume_growth`.|EBITDA changes.|
|||also remove price.|||
|C18|Quote|PDF R16: verify per bond. M3.1:|Per-bond feld with M3.1|None; a data|
||convention|clean in the US.|as default.|defnition.|
|C19|Maintenance|PDF R48: not depreciation by|F4.7 as a labelled default;|Depreciation against|
||capex|rule. F4.7: depreciation foor for|record evidence when it|capex in the|
|||A4, A5.|exists.|lowest-growth year.|
|C20|Cycle label|PDF R35: not a clock. F6: phase|Keep F6 as a prior over|M11 reliability of|
|||vote.|observable indicators.|_wdown_.|
|K1|FCF start|`credit-model-standards`: start|M4.2 for the forecast; CFO|On issuers with large|
|||from reported EBITDA. M4.2:|less capex as the|cash restructuring,|
|||adjusted EBITDA less _CashNR_.|cross-check|which start tracks|
|||Code (S3): CFO less all capex.|(`hy-model-standards`); a|CFO less capex.|
||||gap above 15% of EBITDA||
||||is a fag.||
|K2|Stock|`ebitda-addback-treatment`: a|F3: the issuer pays in|Spread residual with|
||compensation|non-cash add-back. F3 C6: never|shares or buybacks, so it is|and without the|
|||add back.|a cost to creditors.|add-back.|
|K3|Base case|`credit-model-standards`: lender|Coin toss|Analyst record:|
|||case tilted conservative. M5.1, F6:|(`hy-model-standards`|actuals above base|
|||a coin toss.|agrees). In public HY,|about half the time.|
||||guidance leans optimistic,||
||||not sandbagged.||
|K4|FCCR|Skills: _E/_(_Ic_ +_Amort_). F5:|F5 for lease-heavy|Which predicts the|
|||(_E_+_R−Kmaint_)_/_(_Ic_+_R_+_Amort_).|archetypes; skill form for|F4 shortfall date.|
|||Code: F5 without amortisation.|amortising loans; print||
||||both.||
|K5|Headroom bands|`covenant-compliance`: _≥_20 /|F8 bands; add the skill’s|Breach rate by band|
|||10–20 / _<_10%. F8: _>_25 / 10–25 /|trajectory rule (fag a|on matured tests.|
|||_<_10%.|falling path early).||



48 

|ID|Topic|The two sides; code today|Rule that wins, and why|Settling test|
|---|---|---|---|---|
|K6|Covenant|Skills: the signed compliance|Public HY has no|None; a data source.|
||EBITDA source|certifcate. F3, M4.6: the|certifcate. Use the||
|||document defnition.|indenture defnition; use a||
||||10-Q covenant disclosure||
||||when one exists.||
|K7|Concentration|Skills: top customer above|F2 (20%) for the modifer;|Spread residual by|
||threshold|15–20%. F2 M3: above 20%.|15% adds a watch fag.|bucket.|
|K8|Generic|Skills: anchor to 2008–2009. F6:|F6; 2008–2009 only when|Back-test case paths|
||downside|the archetype’s last cycle. Code:|the issuer has no own cycle|against 2008–2009|
|||v0 templates by archetype.|history.|and 2020 by|
|||||archetype.|
|K9|Memo form|`credit-memo-standards`:|F12. A secondary buyer|F13 blind rubric.|
|||advocacy deck, sources and uses|does not originate; the||
|||frst. F12: recommendation frst;|gate can refuse.||
|||“pass” is a valid outcome.|||
|K10|Circularity|`credit-model-standards`:|No solver (code agrees).|Interest error against|
|||iterate. `hy-model-standards`:||an iterated run below|
|||interest on _Dh−_1, no solver. PDF||1% of EBITDA.|
|||P11: may iterate.|||
|K11|Minimum cash|F4.4: one month of cash operating|F4.4 via (COGS +|Runway change|
|||cost. Code: 2% of quarterly|SG&A)/3.|under both.|
|||revenue. Mapping item 3: (COGS|||
|||+ SG&A)/3.|||
|K12|Text lags code|M4.3 (8x), M5.1 (debt recursion),|The code, after a decision|None;|
|||F6.1 (order) state rules the code|page that updates the text.|documentation.|
|||already replaced (C6, C8, C9).|||
|K13|Trend length|`borrower-monitoring`: a trend|Both: 8-quarter _t_ for the|None.|
|||needs 3–4 quarters. F8: margin|band; the last 3–4 quarters’||
|||slope _t_ over 8 quarters.|direction for the watchlist.||
|K15|Hedge ratio|`scripts/scenarios.py`:|One _β_ for prediction and|IC of E1 with and|
|||_β_ =_s/S_0, so carry is zero in E1.|test, estimated from|without carry;|
|||Backtest: _β_ = 1; carry (spread|history by bucket; 1 until|hedged P&L variance|
|||level) is the best ranker. M9.3: _β_|then. Add carry as E0|under each _β_.|
|||from the model’s _∂s/∂Smkt_.|(now in code; S15 hedges||
||||with _β_ = 1).||
|K14|Capex in the|F4.7: maintenance foor; growth|Run two cases:|For CRWV the static|
||cases|capex cuttable in two quarters.|maintenance-only and|runway is 2 quarters;|
|||Code: now runs maintenance-only|committed capex. Quote|the case shows no|
|||and committed capex; quotes the|the shorter runway.|shortfall in 8.|
|||shorter.|||
|||`credit-model-standards`: all|||
|||capex in FCF.|||
|W1|Combination|Backtest-led v0: spread level 25%,|The user’s weights, by user|The clocks backtest|
||weights|cases 15%, fair line 10%, untested|choice; they replace the|now running (IC of|
|||estimates capped at 5% (the|backtest-led weights.|E5 after cost, beyond|
|||backtest supported spread level||the spread rank, per|
|||best, IC after cost 0.22 and 0.29;||cycle); then a|
|||the leverage residual added 0.036;||backtest of each G1|
|||the clocks and G1 estimates were||estimate (E7–E10);|
|||untested). User choice (22||then the rank-IC rule|
|||October 2026): G1 45%, clocks||with ablation.|
|||20%, G2 rest, G3 and G4 11.67%|||
|||each, relative weights kept inside|||
|||each bucket.|||
|B1|Leases|S&P: present value of|Filed liability (already a|As C6.|
|||commitments at 10% (App. E),|present value after ASC||
|||“superior” to a rent factor.|842); S&P 10% PV when||
|||Krichef: capital leases only. M4.3:|untagged; 8_×_ for old||
|||8_×_ rent. F5, PDF: fled liability.|periods.||
|||Code: liability.|||



49 

|ID|Topic|The two sides; code today|Rule that wins, and why|Settling test|
|---|---|---|---|---|
|B2|Pensions|S&P: (PBO + OPEB _−_|PDF form plus OPEB; tax|As C7.|
|||assets)_×_(1_−t_) to debt;|shield only for a cash tax||
|||contributions a liquidity call.|payer.||
|||PDF E35: defcit to debt, expense|||
|||less service cost to EBITDA.|||
|B3|Stock|Krichef: the “most universal”|F3 (see K2).|As K2.|
||compensation|add-back. F3 C6: never.|||
|B4|Qualitative into|S&P: business and fnancial scores|Scenario route for the|Ablation of E12 and|
||the grade|weighted by business-risk class;|forecast; the S&P grade|of the one-way clip.|
|||soft factors only lower. PDF R34:|only as cross-check E12;||
|||never add scores to ratios.|S&P’s one-way rule for soft||
|||Krichef: subjective factors|factors (E7, E11; S11||
|||overlay, never summed.|credit foor).||
|B5|PD source|S&P: PD from a fundamental|S&P route (with C2).|As C2.|
|||grade read of cumulative default|||
|||tables; never inverts spread. Code:|||
|||PD from spread at _κ_= 2.|||
|B6|Headroom|Krichef: 20–25% is the cushion|F8 bands, with the|As K5.|
|||banks set at signing, not a|one-year-out check and the||
|||monitoring band; check one year|G3 trajectory rule.||
|||out. S&P: headroom over the|||
|||tighter of case and covenant. F8:|||
|||25 / 10%.|||
|B7|FCF defnitions|S&P: fve defnitions (FOCF,|One defnition per use:|None; a defnition.|
|||discretionary, DCF, DSCR,|M4.2 FCF, FOCF for S&P||
|||Repsol FCF); Krichef: adjusted|ratios, unlevered FCF for||
|||EBITDA less capex, cash interest,|value, cash for debt service||
|||cash tax, ∆_WC_, no amortisation.|for the default point.||
|B8|Valuation blend|S&P: 2/3 DCF + 1/3 multiple.|Blend allowed within going|As C11.|
|||PDF R63: no mechanical average.|concern only (C11).||
|B9|Recovery timing|S&P: time buckets (_<_6, 6–30,|S&P buckets for _τ_;|As C12.|
||and rate|_>_30 months) at 10%. PDF and|_k_ = 15% until calibrated.||
|||Krichef examples: 20%. Mapping|||
|||v0: 1 year at 15%.|||
|B10|Stress depth|S&P: front-load a 10–30% revenue|Issuer’s own worst year|Back-test case paths|
|||fall; “too easy to remain too soft”.|when known; else the S&P|against 2008–2009|
|||Code v0 A5: _−_15%, _−_5%.|band.|and 2020.|
|B11|Spread per turn|Krichef: STW over bond-level|Both levels, with the trap|IC of E13 with and|
|||leverage; never alone (DataFone).|guard (FCF/debt _>_0,|without the guard.|
|||Code: G-spread over total|cushion _>_1).||
|||lease-adjusted leverage.|||
|B12|Return measure|Krichef: yield to worst is the base|PDF; YTW only as the|As C3.|
|||return. PDF R14: promised yield|call cap.||
|||is not expected return.|||
|B13|Composite form|Krichef: categorical grid|Numeric ensemble ranks;|As C15.|
|||(overweight to avoid). Repo:|grid printed as a label.||
|||numeric IC-weighted ensemble.|||



50 

## **19 Metrics dictionary** 

Every metric of the framework in one table. Symbols are defined in the step that computes the metric. Bands read green / amber / red. “Rank” means a percentile inside the archetype (F8). “Rec.” means recorded, no band. All bands are v0 under framework R9. “In code” marks metrics the process computes today (“part” means partly; “bt” means only in the backtest). 

|Metric|Formula|||Unit|Band g / a / r|Group|Step|In|
|---|---|---|---|---|---|---|---|---|
|||||||||code|
|`g_spread`|_yb −yUST_ (_Tb_)|||bp|Rec.|G2|S1|yes|
|`dirty_price`|_P c_ +_AI_|||per 100|Rec.|G1|S1|yes|
|`cust_top1`|max_j Revj/Rev_|||%|_<_15 / 15–20 /|G1,|S2|yes|
||||||_>_20|G3|||
|`cust_hhi`|�<br>_j_(_Revj/Rev_)2|||index|Rank|G1|S2|no|
|`business_risk`|�<br>_k ωkbk_, capped by industry|||1–10|1–4 / 5–6 / 7–10|G4|S2|no|
|`ebitda_adj`|_Erep_ + �<br>_i aiNRi_|||USD m|Rec.|G1,|S3|no|
|||||||G3|||
|`addback_gap`|_Eco/Eadj −_1|||%|_<_10 / 10–20 /|G1,|S3|no|
||||||_>_20|G3|||
|`covenant_gap`|_Ecov/Eadj −_1|||%|_<_10 / 10–25 /|G1|S3|no|
||||||_>_25||||
|`addback_category_`|largest add-back class _/Erep_|||%|_<_5 / 5–10 / _>_10|G3|S3|no|
|`share`|||||||||
|`fcf`|_Eadj −CashNR −K −Ic _||_−T c −_∆_WC_|USD m|Rec.|G1|S3|no|
|`fcf_check_gap`|(_FCF −_(_CFO −K_))_/Eadj_|||%|_<_5 / 5–15 / _>_15|G3|S3|no|
|`fcf_conversion`|�<br>(_CFO −K_)_/_ �|_E_||ratio|_>_0_._30 / 0.10–0.30|G1|S3|yes|
||||||/ _<_0_._10||||
|`ffo`, `focf`|_NI_ +_NC_; _FFO −_∆_WC −K_|||USD m|Rec.|G4|S3|no|
|`eq_score`|count of EQ fags,|EQ10 twice||count|0 / 1–2 / _≥_3|G1|S3|yes|
|`margin_trend_t`|ˆ_b/_se(ˆ_b_), 8 quarters|||_t_|_>_1 / _−_1 to 1 /|G1|S3|yes|
||||||_< −_1||||
|`organic_growth`|growth less FX and M&A||(Gatto)|%|Rank|G1,|S3|no|
|||||||G3|||
|`L_eff`|_Cashfree_ + min(_Cap, BB,_||_Trig_)_−_|USD m|Rec.|G1|S4|part|
||_Drawn −LC −Cashmin_||||||||
|`runway_static_q`|_Leff/_max(0_, −FCFLT M/_4)|||quarters|_≥_8 / 4–8 / _<_4|G1|S4|yes|
|`runway_scen_q`|frst shortfall quarter, severe case, shorter|||quarters|_≥_8 / 4–8 / _<_4|G1,|S4|part|
||of two capex runs|||||G3|||
|`wall_18m`|debt due inside 18|months||USD m|Rec.|G1|S4|yes|
|`wall_cover_4`|(_Leff_ + �<br>4 _FCF base_)_/_�<br>4 _M_|||ratio|_>_1_._5 / 1.0–1.5 /|G1|S4|yes|
||||||_<_1_._0||||
|`funding_gap_min`|min_h Gh_|||USD m|_≥_0 / – / _<_0|G1|S4|no|
|`delta_I_to_ebitda`|∆_I/E_|||%|_<_5 / 5–15 / _>_15|G1,|S4|no|
|||||||G4|||
|`refi_score`|F4 points|||0–6|_≥_4 / 2–3 / _≤_1|G1|S4|part|
|`p_refi_access`|_π_[_n_]|||prob|_>_0_._8 / 0.5–0.8 /|G1,|S4|yes|
||||||_<_0_._5|G2|||
|`lev_gross`|_D/E_|||x|Rank|G1,|S5|yes|
|||||||G3|||
|`lev_net`|(_D −Cash_)_/E_|||x|Rank|G1|S5|yes|
|`lev_lease`|(_D_+_Lop_ +_Lfin_)_/_(_E_+_R_)|||x|Rank|G1|S5|yes|
|`lev_8x`|(_D_+ 8_R_)_/_(_E_+_R_)|||x|Rec.|G1|S5|no|
|`lev_creation_k`|senior at face + layer at price, over _E_|||x|below distressed|G1|S5|no|
||||||multiple green||||
|`cash_cov`|_E/Ic_|||x|_>_3 / 1.5–3 /|G1,|S5|yes|
||||||_<_1_._5|G4|||
|`after_capex_cov`|(_E −K_)_/Ic_|||x|_>_2_._0 / 1.25–2.0 /|G1,|S5|yes|
||||||_<_1_._25|G4|||



51 

|Metric|Formula|||Unit|Band g / a / r|Group|Step|In|
|---|---|---|---|---|---|---|---|---|
|||||||||code|
|`fccr`|(_E_+_R −Km_)_/_(_Ic_ +_R_+_Am_)|||x|_>_1_._5 / 1.1–1.5 /|G1,|S5|part|
||||||_<_1_._1|G3|||
|`ffo_to_debt`|_FFO/D_|||%|_>_19_._5 / 10.8–19.5|G4|S5|yes|
||||||/ _<_10_._8||||
|`focf_to_debt`|_FOCF/D_|||%|_>_8_._5 / 2.5–8.5 /|G4|S5|part|
||||||_<_2_._5||||
|`priority_ratio`|(_Dprior_ +_Lprior_)_/TA_|||%|_<_15 / 15–30 /|G4|S5|no|
||||||_>_30||||
|`headroom_H`|1_−Levcov/Levmax_|||%|_>_25 / 10–25 /|G1,|S5|part|
||||||_<_10|G3|||
|`debt_capacity`|_mtestEcov −Dcov_|||USD m|Rec.|G4|S5|no|
|`lme_score`|F7 points|||0–10|0–2 / 3–5 / _≥_6|G1|S5|no|
|`duration_gap`|_DO −DR_|||years|_<_1 / 1–3 / _>_3|G2|S6|yes|
|`breakeven_margin`|�<br>_O/_ �<br>_R_|||ratio|_<_0_._6 / 0.6–1.0 /|G2|S6|yes|
||||||_>_1_._0||||
|`coverage_`|_m_ �<br>_R/_ �|_O_||ratio|_>_1_._0 / 0.7–1.0 /|G2|S6|yes|
|`contracted`|||||_<_0_._7||||
|`renewal_dependent_`|share of _O_ after runof|||%|_<_15 / 15–30 /|G2|S6|yes|
|`share`|||||_>_30||||
|`renewal_dependent_`|that amount over _E_|||years|_<_2 / 2–5 / _>_5|G2|S6|yes|
|`ebitda_years`|||||||||
|`max_cum_shortfall`|max(0_, −_min_t_||�<br>(_mR −O_))|USD m|Rec.|G2|S6|yes|
|`p_path`|_π_(_m_)_mass_(_m_)_/_ �|||prob|Rec.|G2|S7|yes|
|`w_down`|sum of downside case weights|||prob|_<_0_._25 / 0.25–0.5|G1|S7|yes|
||||||/ _>_0_._5||||
|`lev_fwd_4`|�<br>_m_<br>�<br>_s p w Lev_|||x|Rank|G1,|S7|yes|
|||||||G2|||
|`lev_peak_down`|peak leverage,||severe case|x|below distressed|G1,|S7|yes|
||||||multiple green|G3|||
|`p_liq_short_8`|weight of cases with a shortfall in 8 quarters|||prob|_<_5 / 5–20 /|G1|S7|yes|
||||||_>_20%||||
|`p_refi_4`|weight with wall cover _<_1 in 4 quarters|||prob|_<_5 / 5–20 /|G1|S7|yes|
||||||_>_20%||||
|`pd_12m`|by path; fundamental route (C2)|||prob|by rating table|G1,|S7|part|
|||||||G4|||
|`tev_to_ebitda`|(_Mcap_+_D _|_−Cash_)_/E_||x|Rec.|G1,|S8|yes|
|||||||G4|||
|`debt_to_tev`|_D/TEV_|||ratio|_<_0_._5 / 0.5–0.7 /|G1|S8|yes|
||||||_>_0_._7||||
|`ltv_k`|debt through _k_ over _V_|||%|_<_50 / 50–80 /|G1,|S8|no|
||||||_>_80|G3|||
|`recovery_pv_k`|_Rk/_(1 +_k_)_τ_|||% of|Rec.|G1,|S8|no|
|||||face||G4|||
|`recovery_score`|S&P 1–5|||score|1–2 / 3 / 4–5|G4|S8|no|
|`resid_log`|log_s −_log_sfair_|||log|Rec.|G2|S9|yes|
|`z_rv`|_ε/u_|||sd|_|z| >_ threshold is|G1,|S9|no|
||||||a signal|G2|||
|`spt_bond`|_STW/Levthr_|||bp per|Rank; junior|G4|S9|no|
|||||turn|below senior red||||
|`half_life_weeks`|log 2_/_(_−_log|_ρw_)||weeks|_<_26 / 26–52 /|G2|S9|yes|
||||||_>_52||||
|`alpha_net`|S10 sum less cost|||bp a|_>_100 / 0–100 /|G1,|S10|yes|
|||||year|_<_0|G2|||
|`info_ratio`|_α/sdm_(_α_)|||ratio|_>_1 / 0.5–1 /|G1|S10|no|
||||||_<_0_._5||||
|`l_def`|(_P d/_100_−RP V_ )_/_(_P d/_100)|||ratio|Rec.|G1|S10|yes|
|`jtd_per_mm`|106(_P d/_100|_−RP V_ )||USD|limits|G1|S10|no|



52 

|Metric|Formula|Unit|Band g / a / r|Group|Step|In|
|---|---|---|---|---|---|---|
|||||||code|
|`gate`|G1–G9|pass or|all of G1, G2, G3,|G1|S11|part|
|||fail|G6, G8||||
|`watch_tier`|from _Eact/Eplan −_1, headroom, liquidity|0–3|0 / 1 / 2–3|G3|S12|yes|
|`spread_shock_z`|(∆_s −_ˆ_β_∆_S_)_/sd_|sd|_<_2 / – / _≥_2|G1|S12|no|
||||review||||
|`altman_z`|1_._2_A_+ 1_._4_B_+ 3_._3_C_+ 0_._6_M_ + 1_._0_T_|score|Rec.|G4|S12|no|
|`panel_score`|(_ng −nr_)_/n_|ratio|Rec.|G1,|S13|part|
|||||G2|||
|`rating_sp_implied`|median nearest-median rating of four ratios|rating|Rec.|G4|S13|no|
|`alpha_comb`|weighted E0–E13|bp a|Rec.|all|S14|yes|
|||year|||||
|`mz_b`|slope of realised on predicted alpha|ratio|0.7–1.3 / 0.3–0.7 /|G1,|S14b|yes|
||||_<_0_._3|G2|||
|`alpha_sized`|ˆ_a_+ˆ_b αnet_|bp a|_>_0 needed for a|G1|S14b|yes|
|||year|call||||
|`mu_excess`|�<br>_q X_|%|_>_0 to act|G1|S15|yes|
|`es95`|expected shortfall of _−Rnet_|%|_≤_budget (25%)|G1|S15|yes|
|`opportunity_cost`|max_adm µ −µa_|%|0 to act|G1|S15|yes|



53 

**20 Glossary** 

|Term|Meaning|
|---|---|
|Add-back|An amount the issuer adds to reported EBITDA because it calls the cost one-of. The|
||analyst accepts or rejects each one.|
|Archetype|One of eight business types in framework F2 (A1 lease-heavy consumer to A8 fnancials).|
||It sets which earnings, ratios, downside and events apply.|
|`available_at`|The frst moment the market could read a number. A step at decision time _t_ reads only|
||numbers with `available_at` _≤t_.|
|Basis point (bp)|One hundredth of one percent: 0.0001.|
|Business risk profle|S&P’s grade of how risky the business is (country, industry, competitive position), before|
||any debt.|
|Carry|The spread the bond pays over a period, less what the hedge costs.|
|Case|One company forecast: base, moderate downside, severe downside, upside (management|
||and consensus when data exist).|
|Claims view|Who gets paid what if the issuer fails. It uses allowed claims, not balance-sheet liabilities|
||(F5).|
|Combined view|One expected alpha per issuer from many estimates, weighted (S14).|
|Conformal band|An error band built from the model’s own past errors, so that a stated share of new bonds|
||falls inside it.|
|Convergence|The part of the gap between the market spread and the fair spread that closes over the|
||horizon.|
|Covenant|A promise in the bond or loan document. A maintenance covenant is tested each quarter;|
||an incurrence covenant only when the issuer acts (borrows, pays a dividend).|
|Coverage|Earnings over interest. Variants subtract capex or add rent.|
|Creation multiple|The value, in turns of EBITDA, at which a buyer of a tranche at its market price would|
||own the business.|
|Decision time|The date of the analysis: the last TRACE date plus one day.|
|Default state|A case in which the issuer defaults inside the horizon. The PDF requires one in every|
||scenario set.|
|Duration (spread)|The percent change in price for a one-unit change in spread.|
|EBITDA, EBITDAR|Earnings before interest, tax, depreciation and amortisation; EBITDAR also adds back|
||rent.|
|EBITDA, three kinds|Reported (as fled), adjusted (the analyst’s, by the F3 rules), covenant (by the document’s|
||defnition).|
|Expected alpha|The expected return of a hedged long position over the horizon, after expected default|
||loss and cost.|
|Expected shortfall (ES)|The average loss in the worst (1_−α_) share of outcomes.|
|Fair line|A line of log 5-year spread on lease-adjusted leverage, ftted across the issuers in the run.|
|Fair spread|The spread a bond should pay for its risk, from the fair line today (and the M7 model|
||later).|
|FCF|Free cash fow: cash left after capex, cash interest, cash tax and working capital.|
|FFO|Funds from operations (S&P): cash earnings before working capital.|
|Force rank|All candidates sorted on one score across sectors.|
|Gate|The F9 checks that turn a credit view into a trade call.|
|G-spread|Bond yield minus the Treasury par yield at the same maturity. Not option-adjusted.|
|Group (G1–G4)|The four sources of method: core process, built methods, skills, books.|
|Half-life|Time for half of a gap to close, from an AR(1) ft: log 2_/_(_−_log_ρ_).|
|Hazard rate|Default intensity: _λ_=_−_log(1_−PD_) per year.|
|Headroom|How far a covenant ratio sits from its limit.|
|Information coefcient|The rank correlation between a prediction and the later outcome.|
|(IC)||
|Jump-to-default (JTD)|What a position loses at once if the issuer defaults: face times price less recovery.|
|_κ_ (kappa)|The market price of credit risk: spread over expected loss.|
|LGD|Loss given default: one minus recovery.|
|LME|Liability management: drop-downs, uptiers and exchanges that move claims ahead of|
||yours.|



54 

|Term|Meaning|
|---|---|
|LTM|Last twelve months: the sum of the last four quarters.|
|LTV|Loan to value: debt through a tranche over enterprise value.|
|Macro path (story)|One of fve eight-quarter paths of GDP, infation, rates and spreads, with a probability.|
|Notching|Rating a debt issue above or below the issuer rating for its priority and expected recovery.|
|OAS|Option-adjusted spread: spread after the value of call options is removed. The repo has|
||none yet.|
|PD|Probability of default over a horizon.|
|Phase|The cycle state (expansion, late cycle, downturn, repair, recovery) from a six-indicator|
||vote.|
|Point in time|Data as the market knew it then, with later restatements kept apart.|
|Refnance access score|Zero to six points of evidence that lenders will roll the debt (F4).|
|Residual|Market spread minus fair spread, in logs or bp. Positive means cheap.|
|RPO|Remaining performance obligation: signed revenue not yet booked.|
|Spread per turn|Spread divided by leverage: the pay per turn of risk.|
|TEV|Total enterprise value: debt less cash plus equity value.|
|TRACE|FINRA’s record of US corporate bond trades.|
|Two clocks|Fixed charges and signed revenue on one yearly grid (M4.7).|
|v0 default|A stated starting value with a decision page, to be replaced by calibration (R9).|
|Wall|Debt that falls due in a window, usually 18 months.|
|Watchlist tier|Monitor, watchlist or workout, from performance against plan, headroom and liquidity.|



55 

