# Whitman and Diz (2009), *Distress Investing: Principles and Technique*

John Wiley & Sons, Wiley Finance series, ISBN 978-0-470-11767-5. Practitioner book. Page numbers below are PDF pages of the repo copy (280 pages). Printed page = PDF page − 28. The card covers only the parts that feed this repo: control and the fulcrum security, valuation in distress, recovery and the absolute priority rule, voluntary exchanges, and the Chapter 11 process.

## Claim
A distress analyst does not forecast whether a money default occurs. The analyst assumes some probability of default and forecasts what happens next (p. 105). Chapter 11 rules drive every reorganization, in court or out of court (p. 110). So value a distressed bond as the claim it becomes in a plan: its class, its share of reorganization value, and the form of the consideration (p. 67). The absolute priority rule (APR) binds only when a court crams a plan down on a dissenting class. A consensual plan can pay a junior class before a senior class is paid in full (p. 143). Control decides the outcome. The holder of the fulcrum security and of a blocking position shapes the plan (pp. 147, 197, 242).

## Method
The book is a set of rules and worked cases, not a model. Five constructs feed this repo.

**1. Fulcrum security (p. 242 and note 10, p. 262).** The fulcrum security is "the most senior security that will participate in the reorganization", where participation means that it will likely convert to equity. Classes above it are reinstated or paid in full. Classes below it get little or nothing.

```latex
f = \min\{\,k : V_{plan} - S_k < F_k\,\}, \qquad R_k = 1 \;\text{for}\; k < f, \qquad R_f = \frac{V_{plan} - S_f}{F_f}, \qquad R_k \approx 0 \;\text{for}\; k > f
```

`S_k` is the allowed claim ahead of class k, `F_k` is the class claim, and `V_plan` is the plan reorganization value. Intuition: the fulcrum class is the first class that the plan value does not cover in full, so it takes the new equity. The book gives no formula. The notation above is ours and uses the waterfall of Section 6.2.

**2. Class vote and the blocking position (pp. 141, 197).** A class of claims accepts a plan when holders of at least two thirds in amount and more than one half in number of the claims that vote accept it.

```latex
\text{accept}_c \iff \frac{\sum_{i \in \text{yes}} a_i}{\sum_{i \in \text{voted}} a_i} \ge \tfrac{2}{3} \;\wedge\; \frac{n_{\text{yes}}}{n_{\text{voted}}} > \tfrac{1}{2}, \qquad \text{block}_c \iff b_c > \tfrac{1}{3}
```

`b_c` is one holder's share of the amount that votes in class c. Intuition: a holder with more than one third of a class can stop a consensual plan. A cram-down threat limits that power (p. 197).

**3. Cram-down payment for a secured class (pp. 141–142).** An impaired secured class that dissents must keep its lien and get deferred cash with a present value at least equal to its collateral value.

```latex
\text{Payment} = \frac{PV \times i}{1 - (1+i)^{-n}}, \qquad \$7{,}000{,}000,\; i = 8\%,\; n = 5 \;\Rightarrow\; \$1{,}753{,}195.2 \text{ per year}
```

Intuition: the plan can stretch a secured claim into a five-year note that pays down principal each year at a court-set rate. Under a §1111(b) election the whole claim ($10 million in the example) counts as secured, so the sum of payments must reach $10 million (p. 142).

**4. Valuation multiple as an annuity factor (pp. 170–171).** The book reads an EBITDA multiple as the present value of an annuity that grows at rate g for 25 periods. The printed formula is illegible in the PDF text. The form below reproduces Exhibit 10.8 (10% and 0% give 9.1x, 10% and 2% give 10.6x, 15% and 4% give 8.4x):

```latex
M(r, g) = \sum_{t=1}^{25} \frac{(1+g)^{t-1}}{(1+r)^{t}}
```

Intuition: a distressed multiple is a high discount rate and a low growth rate in disguise. At 25% and 0% the multiple is 4.0x.

**5. Three-path value of a distressed bond (GMAC, pp. 106–107).** The book prices a bond across three outcomes: it stays a performing loan, it enters Chapter 11, or the owner runs a voluntary exchange.

```latex
E[\text{value}] = p_{perf}\, PV(\text{contract cash flows}) + p_{11}\, W_{11} + p_{ex}\, W_{ex}
```

`W_11` is the workout value of the plan consideration, and `W_ex` is the value of the exchange package. GMAC 7¾% notes due January 2010, price 62, YTM 53.42%. The authors put 70% to 75% on the performing path and 25% to 30% on Chapter 11, with a workout value of 60 to 90 (p. 107). They put almost no weight on a successful exchange. Intuition: outside Chapter 11 no one can take a holder's right to a money payment, so a short maturity gives de facto seniority (p. 106).

## Data
The book uses cases and statute, not a sample. The main evidence:
- **Statute.** Trust Indenture Act §316(b): money terms change only with each holder's consent (p. 108). §316(a)(2): 75% can postpone interest for at most three years. Home Products indenture §9.2: a majority can amend nonmoney terms (p. 109).
- **Case counts.** LoPucki Bankruptcy Research Database, 2000–2007: 368 large Chapter 11 dispositions. 73% were conventional filings and 27% were prenegotiated or prepackaged. 46 cases (12.5%) ended as §363 asset sales (Exhibit 9.1, p. 148).
- **Kmart (Chapter 16, pp. 239–252).** Filed 22 January 2002. Plan reorganization value $2.25 billion to $3.0 billion, about 6x pro forma 2004 EBITDA (pp. 246–247). Prices and plan recoveries by class (Exhibits 16.8 and 16.9, pp. 246–247):

| Class | Claim | Price 11/01 | Price 2/02 | Plan recovery | Form |
| --- | --- | --- | --- | --- | --- |
| Secured | $61 million | 100 | 100 | 100% | Reinstated |
| Prepetition lender (unsecured bank) | $1,076 million | 90 | 60 | 40.0% | Cash |
| Notes and debentures | $2,277 million | 85 | 40 | 14.4% | Common stock |
| Trade and lease rejection | $4,300 million | 75 | 30 | 9.7% | Common stock |
| Trust preferred | $648 million | — | — | Litigation trust share | — |

- **Kmart control.** ESL and Third Avenue held 55.3% of the note class. ESL held 35.6% of the lender class. Both were blocking positions (Exhibit 16.6, p. 245).
- **Kmart DIP.** $2.0 billion super-priority facility. Direct cost $71 million, 3.5% of the limit (p. 246).
- **Third Avenue Value Fund in Kmart (Exhibit 16.11, p. 251).** Cost basis 57% of claim at filing, 52.51% after more purchases. Plan value of the claims was 12.31% of claim, $13.08 per share. The fund bought new shares at $10 under the plan investment agreement. The shares traded at $40 one year after emergence and $100 two years after (p. 252).
- **Home Products International (Chapters 10 and 15).** Prepackaged plan in 2007. Plan multiple 4.63x EBITDA, well below the public peer multiples (p. 174). Chapter 7 liquidation analysis with recovery rates per asset class (Exhibit 10.10, p. 177).

## Result
- **APR binds only under cram-down.** "Nothing in the statute says that distributions in a consensual plan need to comply with the absolute priority rule" (p. 143). The new value exception lets old equity keep an interest if it adds new value (p. 139).
- **Equal-rank unsecured classes can recover different amounts.** At Kmart the unsecured bank lenders got 40% in cash, the notes got 14.4% in stock, and trade got 9.7% in stock (p. 247). The 40% came from a settlement over affiliate guarantees and substantive consolidation (pp. 247–248). Kmart used deemed consolidation for distributions (p. 191).
- **Plan value is a negotiated number.** Junior classes push for a high value. Senior classes and banks often prefer a low value because it makes the plan feasible (p. 195). Banks sometimes back a high value to get more cash-pay paper (p. 200). The more cash-pay senior paper a plan issues, the less feasible it is (p. 195).
- **Plan value understated Kmart.** Plan consideration valued the stock at $13.08. The market price was $40 one year later and $100 two years later (pp. 251–252).
- **Comparable multiples are upper bounds.** Distressed multiples sit below healthy peers (p. 174).
- **Resource conversion value matters.** Below-market leases and NOLs are assets in Chapter 11. Kmart sold rights to up to 72 properties for more than $800 million (p. 175). §382 limits NOLs after an ownership change, with an exception under §382(l)(5) for "old and cold" claims (pp. 175–176).
- **Voluntary exchanges fail without a downside for holdouts.** XYZ example: 6% bonds at 60, an exchange into PIK bonds worth 72 to 73, and holdouts trade near 80 (p. 122). Exchanges often fail when the issuer seeks 80% or more of an issue (p. 120). The fix is an exit consent: the majority that exchanges subordinates the holdouts' bonds, or the new bonds mature first (p. 122).
- **A prepack removes the holdout problem.** It reaches a whole class at two thirds in amount and one half in number (p. 152).
- **Time cuts unsecured recovery.** Time in Chapter 11 runs 18 months to three years (p. 151). "Time is the enemy of unsecured creditors" (p. 198). Professional fees grow with time and with the number of firms (pp. 197–198).
- **Measure fees against cash, not book value.** The book rejects the Weiss (1990) estimate of 3.1% of book debt plus market equity. Fees are cash administrative claims, so they belong on the confirmation-date value or on the cash at reorganization (pp. 114–115).
- **Legal leverage moves claims.** The leverage sources are equitable subordination, lien perfection defects, fraudulent conveyance attacks on upstream guarantees, substantive consolidation, and critical vendor payments. Each one moves value between classes (pp. 155–157, 186–192). At Kmart the critical vendor order paid 2,330 suppliers about $300 million, funded by the DIP (pp. 191–192).
- **The Home Products liquidation rates differ from our defaults.** Receivables 60%, inventory 41%, land and buildings 100%, machinery 75%, dies 20% (p. 177). Net value for unsecured claims was $2.6 million against $175 million of claims. The PDF text shows the unsecured recovery as "15%". The figures imply about 1.5%.

## Where Whitman and Diz disagree with Gatto
The methodology takes Gatto as its base. The points below compare this book with Section 6 and with framework F5 and F7.

| Topic | Gatto (methodology) | Whitman and Diz | When each is right | What we adopt |
| --- | --- | --- | --- | --- |
| Recovery mechanics | Recovery is a call spread on value under strict priority. Equal-rank claims pool pro rata (Section 6.2, `waterfall`) | APR binds only under cram-down. Settlements over guarantees and consolidation pay equal-rank classes differently (pp. 143, 247) | Gatto: one entity, a clean structure, a credible cram-down. Whitman and Diz: several entities, upstream guarantees, a contested consolidation | Keep the strict waterfall as the base. Add a plan-deviation term for multi-entity issuers (test 2) |
| Value basis | Four methods, a lognormal value, a distressed multiple (Section 6.1, F7.3) | Comparables are upper bounds. Plan value is negotiated and tends to be low. Add below-market leases and NOLs | Gatto: the court-tested going-concern value. Whitman and Diz: the value a control buyer realises later | Keep F7.3. Add lease and NOL lines to `V_default`. Test plan value against later market value (test 3) |
| Liquidation rates | Receivables 85% to 95%, inventory 60% to 75%, machinery 10% to 20% (F7.5, p. 332) | Home Products: 60%, 41%, 75% (p. 177) | One case each. The rates depend on the asset mix of the archetype | Keep F7.5 as defaults. Calibrate per archetype from disclosure-statement liquidation analyses (test 5) |
| Liability management | Drop-downs and uptiers by a bare majority (Section 6.3, pp. 499–504) | Exit consents by a majority subordinate holdouts. Money terms stay protected by TIA §316(b) (pp. 108, 122) | Both. The 2009 book predates the drop-down and uptier wave. Gatto covers loans, where §316(b) does not apply | The 2009 exit consent is the bond form of the same threat. Score bond exit-consent capacity in F7 at +1 when nonmoney terms amend at a majority |
| Professional fees | A low single-digit percent of total claims (F5 defaults) | Measure against cash at reorganization. Fees grow with time and with the count of firms (pp. 115, 198) | Gatto: a large case with ample cash. Whitman and Diz: a small case, where fees can consume the unsecured recovery | Size fees as a monthly burn times the expected case length, capped by cash. Record both figures in the memo |

## What our data says (hy/recovery.py, hy/inputs.py, data/raw/backtest, 22 October 2026)
**What we hold.**
- `hy/recovery.py` implements Section 6. It has the value methods, the lognormal closed-form and Monte Carlo recovery, and `waterfall` with pari passu pools by `rank`. It also has `default_value` (with DIP and costs), `market_implied_recovery`, `recovery_pv`, `lme_score`, `pi_lme`, `recovery_lme`, and `recovery_adj`.
- A grep for "fulcrum", "absolute priority", and "reorganization value" in `hy/` finds nothing. No code finds the fulcrum class. No code models a class vote, a cram-down, or a plan deviation from strict priority.
- `Tranche` in `hy/inputs.py` carries `rank` and `face` but no `issuer_entity` or `guarantors` field. Section 6.2 and F5 step 1 need both for a per-entity waterfall. So the code cannot yet express the Kmart guarantee settlement.
- `data/raw/backtest` holds no plan, recovery, or disclosure-statement data. The defaults it holds are S&P D and SD ratings in `sp_ratings.parquet`, as the Bharath and Shumway card records.

**What we could build.**
1. `fulcrum_k`: the index f from Method 1, run on `V_default` and on `V_low`, `V_mid`, `V_high`. Report it in Section 6.4. A bond whose fulcrum status changes across the value range is the bond where valuation risk is largest.
2. `apr_deviation_k`: plan recovery minus strict-waterfall recovery, by class, on historical plans. Use it as a prior for multi-entity issuers.
3. Lease and NOL lines in `V_default`: the present value of below-market leases for A1 issuers, and the §382 floor value of NOLs.
4. A fee burn model: monthly professional fees times the case length (18 to 36 months, p. 151), charged ahead of unsecured claims through `admin_claims`.

**Falsifiable tests.**
1. **Fulcrum identification.** For each default with a confirmed plan, compute the model fulcrum class at `V_default`. Compare it with the most senior class that received most of the new equity. The proposed default pass rate is 70% (a default under R9). Reject the model fulcrum as a signal input if it fails. Source: disclosure statements, and the LoPucki database that the book uses (p. 148).
2. **APR deviation.** Regress `apr_deviation_k` on the guarantor count, a multi-entity flag, and a consensual-or-cram-down flag. The book predicts larger deviations with guarantees and in consensual plans (pp. 143, 247). Reject the plan-deviation term if the coefficients do not differ from zero.
3. **Plan value against market value.** For fulcrum classes paid in new equity, compare the plan value per share with the market price 12 months after emergence. Kmart went from $13.08 to $40 (p. 252). If the median ratio is above 1 across cases, recovery at plan value understates the economic recovery. Then `recovery_price_k` should use the post-emergence price, not the plan value.
4. **Pre-filing price convergence.** Kmart notes fell from 85 to 40 around the filing and recovered 14.4% at plan value (p. 246). Measure whether the bond price one month after filing predicts the plan recovery better than our model `recovery_k` does. This test needs a PIT bond price. Our marketdb notes say TRACE is not point in time, so test 4 waits for a PIT price source.
5. **Liquidation rates.** Collect the Chapter 7 liquidation exhibits from disclosure statements. Compare the rates per asset class with F7.5 and with Home Products (p. 177). Replace an F7.5 default when the median across ten or more cases in the archetype falls outside its range.

## Limits
- This is a practitioner book. Its evidence is a few cases, mostly Kmart, Home Products, and GMAC. Its fund (Third Avenue) took part in two of them. It has no sample statistics on recovery or on APR deviations.
- The law is US law as of 2008, after the 2005 BAPCPA. It predates the LME wave of 2015 onward and later case law on uptiers and make-wholes. The TIA protection does not reach loans, and the book says it does not hold in Canada (p. 109).
- The GMAC probabilities and workout values are the authors' guesses. They call the workout range "a stab in the dark" (p. 107).
- Kmart's later share price reflects the Sears merger and a strong retail property market. One case cannot show that plan values are biased low.
- The PDF text garbles the multiple formula (p. 171) and Exhibit 10.9 (p. 173). The Method 4 formula is rebuilt from Exhibit 10.8. The Exhibit 10.9 peer multiples are not quoted here.
- The book has no model for the price of a bond before default. It gives the claim view, not the spread.

## Section touched
`docs/methodology.md` Section 6.1 (value: distressed multiple, resource conversion, NOLs, leases), Section 6.2 (waterfall: fulcrum class, APR deviations, guarantees, and consolidation), Section 6.3 (liability management: exit consents and holdouts), and Section 6.4 (new output `fulcrum_k`). `docs/framework.md` F5 (waterfall steps 1 and 5, professional fee default) and F7 (F7.3, F7.5, F7.8, LME score). Section 9.1 event taxonomy for exchange offers and filings. `hy/recovery.py` and `Tranche` in `hy/inputs.py`. No decision page yet. A sprint that builds `fulcrum_k` and runs tests 1 to 3 should add one.
