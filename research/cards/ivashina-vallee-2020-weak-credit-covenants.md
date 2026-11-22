# Ivashina and Vallée (2020), "Weak Credit Covenants"

NBER Working Paper 27316, June 2020, DOI 10.3386/w27316. Working paper. The cover states that NBER papers are not peer-reviewed (PDF p. 1). We read the NBER version, 60 pages. Page numbers below are PDF pages. PDF page = printed page + 1. The PDF names no later journal publication. Evidence class: hand-parsed loan credit agreements, one market-wide event study, and cross-section regressions. No default or recovery outcome.

## Claim
Negative covenants are the norm in leveraged loans, but carve-outs and deductibles that weaken them are as frequent (p. 2). Simple counts of these clauses explain the market reaction to the 2017 J. Crew restructuring (p. 2). Leveraged buyouts have weaker agreements (p. 2). A larger non-bank share of the loan goes with weaker terms (p. 2). Weak terms carry modestly higher issuance spreads (p. 2). The authors read this as sophisticated borrowers who cater to investors who reach for yield (p. 2).

**Two terms.** A carve-out removes one type of action from a restriction, with no cap (p. 4). Example: the debt covenant does not apply to second lien debt. A deductible, or "basket", lets the borrower act up to a stated amount before the restriction applies (p. 4). Example: senior secured debt up to $100 million.

## Method
**Option view of the covenants (p. 11).** The authors follow Myers (2003).

```latex
E = V - D = V - D^{riskfree} + P(V, \sigma, t, F) \quad (1)
```

Intuition: equity gains when the default put gains value, so each covenant blocks one route that raises the put.

The four routes are risk shift (dP/dσ > 0), underinvestment (dP/dV < 0), claim dilution (dP/dF > 0), and control and information (dP/dt > 0) (p. 11). Lien and debt restrictions target claim dilution (p. 12).

**Weakness proxies (pp. 17-18).** Our notation. The source states the measures in words, not in a formula.

```latex
W^{CO}_i = \sum_{c} N^{CO}_{i,c}, \qquad W^{DED}_i = \sum_{c} N^{DED}_{i,c}, \qquad S_{i,c} = \frac{\sum \text{deductible amounts on } c}{\text{EBITDA}_{i,\,t-1}}
```

Intuition: each clause is one option for the borrower, so the count measures the optionality in the contract.

Here c runs over liens, debt, restricted payments, asset sales, investments, affiliate transactions, the EBITDA definition, and other clauses (p. 42). The authors call the counts an upper bound, because some clauses exclude each other (p. 17). They weight every clause the same, and industry fixed effects absorb standard clauses (p. 18). The size measure S is used only for the debt and lien covenants (p. 18). EBITDA is the Compustat value of the prior fiscal year, not the contract EBITDA (pp. 41, 26). A first principal component of the counts has correlation 0.9 with the plain count (p. 17, fn. 18).

**Latent leverage (pp. 25-26, Table 6 p. 54).** Our notation.

```latex
L^{max}_i = \frac{D_i}{\text{EBITDA}_i} + \bar{S}_{debt}(b_i)
```

Intuition: the borrower can add the debt basket without lender consent, so contract leverage can exceed issue leverage.

Here b is the leverage bucket at issue and the second term is the mean debt deductible in that bucket (p. 26). The authors apply it to the S&P LCD leverage distribution for 2011 to 2016 (p. 25).

**Event study (Table 4 p. 52, Table 5 p. 53).** Our notation of the stated specification.

```latex
\Delta P_i = \alpha + \beta\, W_i + \lambda\, (\text{Distress}_i \times W_i) + \gamma' X_i + \delta_{sector} + \varepsilon_i
```

Intuition: if lenders priced the option at issue, the J. Crew news should not move loans with weak documents more than others.

The window is −15 to +15 days around the J. Crew amendment (p. 24). Distress is the quartile of the inverse of return on assets (p. 24). The same model with the CAPM abnormal stock return against the S&P 500 is Table 5 (p. 53).

**Cross-section (Tables 7 to 10, pp. 55-58).**

```latex
W_i = \alpha + \beta\, \text{LBO}_i + \theta' Z_i + \delta_{industry} + \delta_{quarter} + \delta_{\#covenants} + \varepsilon_i
```

Intuition: if sponsor skill drives weak terms, the buyout indicator and the sponsor expertise proxies should carry positive coefficients after controls for leverage.

Z adds the institutional share, the lead bank share, the number of lenders, size, a bond indicator, and intangibles in turn. Standard errors cluster by issue month (p. 55).

**Spread (Figure 8, p. 47).** The authors regress the all-in-drawn spread on the weakness measures with controls and fixed effects. They plot the predicted spread by quartile (pp. 28-29). Intuition: if lenders charge for the options, the spread rises with the clause count. The paper reports no coefficient table for this test.

## Data
- Street Diligence parses each credit agreement into separate carve-out and deductible items (pp. 13-14). The sources are SEC filings and client contributions, with data as of 2016 (pp. 13-14).
- 1,240 loan packages and 1,857 facilities, 2011 to 2016 (pp. 14-15). Packages by year: 53, 74, 222, 353, 350, 188 (Table 2, p. 50).
- 77.3% of packages are in the DealScan leveraged segment (Table 2, p. 50). Buyouts are 22.3% of the sample: 37.7% to 37.8% in 2011 to 2014, 16.0% in 2015, 19.7% in 2016 (Table 2, p. 50). So non-sponsor loans are the majority.
- Coverage of the leveraged loan market is 8% in 2011 and 45% in 2014 (p. 15). The authors therefore rely on the cross-section (p. 15).
- Mean loan $1,119 million, mean maturity 5.6 years, mean issuer EBITDA $747 million, mean leverage 6.2x (Table 2, p. 50). The DealScan leveraged benchmark has mean leverage 5.0x (Table 2, p. 50).
- Loan prices from Markit and stock prices from Datastream for the event study (p. 15). 404 loans (Table 4, p. 52) and 224 stocks (Table 5, p. 53).
- Sponsor expertise: CreditFlux CLO data for 2000 to 2013 with 1,229 CLOs (p. 30). Sponsor portfolio bankruptcies from Capital IQ, 2005 to 2009 (p. 31).
- Bonds are out of scope. The paper studies loan credit agreements only (pp. 9, 60).

## Result
**Restrictions are common (Figure 1, p. 40, text p. 15).** Share of agreements with each restriction: any 93%, liens 92%, debt 87%, affiliate transactions 86%, payments 81%, asset sales 73%, investments 31%.

**Deductibles are common and large (Figures 1 and 2, pp. 40-41, text p. 16).** Share with a deductible, given the restriction: any 96%, debt 92%, liens 86%, asset sales 71%, restricted payments 70%, investments 44%, affiliate transactions 14%. Mean size in turns of EBITDA: debt 2.34x, asset sales 0.39x, liens 0.35x, payments 0.24x, investments 0.23x. The median agreement has 8 deductibles (p. 16).

**Carve-outs are more common (Figure 3, p. 42, text p. 17).** The mean agreement has 79 carve-outs. 99% have at least one carve-out in each covenant category (p. 17). Mean count by covenant: liens 22.5, debt 14.5, asset sales 13.9, EBITDA definition 11.9, other 11.9, investments 9.9, affiliate transactions 8.2, payments 8.0. The mean EBITDA definition holds twelve changes from the standard definition (p. 17).

**Old measures miss most of it (Table 3, p. 51).** Covenant intensity, cov-lite and the number of financial covenants together give R² 0.503 for the carve-out count and 0.456 for the deductible count. For the size of the debt basket the R² is 0.103. For the size of the lien basket it is 0.049. A cov-lite loan has 31.309 more carve-outs (t 11.12) and 2.272 more deductibles (t 7.85).

**J. Crew (pp. 21-22).** J. Crew used an investment deductible and a carve-out to move $250 million of brand intellectual property out of the collateral into an unrestricted subsidiary (p. 21). It then pledged that property for new debt (p. 22). The proceeds refinanced the senior unsecured notes, about a third of $1.5 billion of debt (p. 22). The J. Crew loan price fell by about 10 points (p. 22).

**Market-wide event study (pp. 24-25, Tables 4 and 5).**
- Loans in the weakest quartile fell by about half a point. Loans in stronger quartiles did not move (p. 24).
- Loan price on carve-out count: −0.003 (t −2.03). On deductible count: −0.035 (t −2.77) (Table 4, col. 1 and 5, p. 52).
- Cov-lite adds −0.295 (t −2.18) with the carve-out count still significant (Table 4, col. 3, p. 52).
- With the distress interaction, the main effect is about zero: −0.000 and −0.001. The interaction is −0.002 (t −1.86) for carve-outs and −0.023 (t −2.67) for deductibles (Table 4, col. 4 and 8, p. 52).
- The number of financial covenants is not significant: 0.126 (t 1.74) and 0.133 (t 1.68) (Table 4, p. 52).
- Stock return on carve-out count: +0.035 (t 2.34). On deductible count: +0.247 (t 1.48), not significant (Table 5, p. 53).
- R² is 0.068 to 0.099 for loans (Table 4, p. 52).

**Latent leverage (Table 6, p. 54).**

| Leverage above | 4x | 5x | 6x | 7x |
| --- | --- | --- | --- | --- |
| At issue, debt to EBITDA | 67% | 56% | 47% | 41% |
| Maximum after the debt basket | 80% | 72% | 63% | 55% |

76% of firms at 5.00x to 5.99x can go above 6x. 73% of firms at 6.00x to 6.99x can go above 7x (p. 54). 71% of firms at 4.00x to 4.99x can go above 5x (p. 54). The extra room is largest in deals that already have high leverage (p. 26).

**Who gets weak terms.**
- Buyouts: +31.763 carve-outs (t 9.51) with no fixed effects, +30.197 to +30.685 with fixed effects. +1.589 to +1.961 deductibles (Table 7, p. 55). The means are 79 and 8 (p. 28).
- Institutional loans: +19.525 carve-outs (t 9.34) and +1.470 deductibles (t 9.56) (Table 8, p. 56).
- Institutional share of the loan: +21.126 carve-outs (t 5.11) and +2.097 deductibles (t 8.58) (Table 8, p. 56).
- Lead bank share: −6.556 carve-outs (t −2.40) and −1.644 deductibles (t −3.09) (Table 8, p. 56).
- Credit-expert sponsors, inside buyouts: +9.563 to +11.123 carve-outs (t 1.98 to 2.50). Deductibles +0.668 to +0.758, not significant (Table 9, p. 57).
- Sponsor with a portfolio bankruptcy in 2005 to 2009: +19.488 carve-outs (t 3.42) and +1.166 deductibles (t 1.69) (Table 9, p. 57).
- The expert gap is close to a third of the buyout gap (p. 31).
- CLOs were 41% (2011) to 62% (2016) of institutional primary participants (p. 29).

**Why: renegotiation cost does not explain it (Table 10, p. 58, text pp. 32-33).**
- Larger loans have more carve-outs: +8.164 (t 7.71).
- Issuers with a bond have fewer carve-outs: −4.496 (t −2.45). The deductible effect is −0.351 (t −1.00).
- Intangibles over assets: +39.717 carve-outs (t 5.53) and +2.904 deductibles (t 3.68).
- The authors reject the renegotiation-cost and debt-overhang stories (pp. 32-34). They do not rule out that sponsor-backed firms are safer (p. 33).

**Price (p. 29, Figure 8 p. 47).** The top quartile pays more than 40 bp above the bottom quartile at issue. The sample mean spread is 266 bp (p. 29). The event study implies that this premium did not cover the risk (p. 5).

**Cycle (Figure 7, p. 46, text p. 27).** The authors call the trend in lien and debt carve-outs "consistent with" procyclical terms. They run no test.

**Default, recovery, and later price.** Not reported. The authors state that there are too few loan defaults for such a test (p. 21).

**Terms the paper does not measure.** Builder baskets, grower baskets, unrestricted subsidiary capacity, J. Crew blockers, required-lender thresholds, and pro rata sharing are not reported as separate fields. Deductibles tied to a ratio test are added to the regular deductibles (p. 16, fn. 15). General and specific deductibles are not split in the results (p. 13, fn. 12).

## Limits
- Loans, not bonds. The authors state that bond indentures are simpler and carry fewer restrictions (p. 9). Our universe is high yield bonds.
- No credit outcome. The only test of harm is one event in 2017 (p. 21).
- The counts treat a benign cash carve-out and a collateral transfer as equal (p. 18).
- The basket size uses unadjusted Compustat EBITDA, so contract room is mismeasured (p. 26, fn. 32).
- The sample favours large loans from SEC filings, and coverage changes by year (p. 15).
- The cross-section shows association, not cause.
- The spread result has no coefficient table, only a plot (p. 47).
- The sample ends in 2016. It precedes uptier deals such as Serta, and the paper does not study the vote thresholds or the pro rata sharing terms.
- Source inconsistency: the text dates the event June 17, 2017 (p. 22). The figure and table notes use June 12 (pp. 43, 44, 52, 53).
- Source inconsistency: the text says the regressor is the quartile of the proxy (p. 24). Table 4 labels it "Number of Carve-outs" (p. 52). The text calls the dependent variable the price change (p. 24). The table header says cumulative abnormal return (p. 52).
- Source inconsistency: Section 5.2 gives mean counts of 19 carve-outs and 8 deductibles (p. 29). Elsewhere the mean is 79 carve-outs (pp. 17, 28).
- Source inconsistency: 96% of agreements have a deductible (pp. 16, 40). The text also says about 10% have none (p. 16), and Figure 2 shows about 10% at zero (p. 41).
- Source inconsistency: the text says more lenders go with fewer weak terms (p. 32). Table 10 shows −1.500 (t −0.84) and +0.164 (t 0.90), both not significant (p. 58). Table 8 shows +3.190 (t 3.02) for carve-outs (p. 56).
- Source inconsistency: the text calls sample leverage close to the DealScan leveraged benchmark (p. 15). Table 2 gives 6.2x against 5.0x (p. 50).
- Source inconsistency: the text cites "Figure 4" for the leverage distribution (p. 26) and "Figure 5" for the carve-out trend (p. 27). These are Figures 6 and 7 (pp. 45, 46).
- Source inconsistency: the Table 8 note names columns 1 to 10 (p. 56). The table has 8 columns.
- Source inconsistency: Section 1 lists investments among the six main restrictions (p. 3). Section 2.1 lists capital expenditure in its place (p. 11).

## Section touched
`docs/methodology.md` Section 6.3 (liability management adjustment) and Section 4.6 (covenant headroom). `docs/framework.md` F7 (liability management score) and F8 (covenants and documents). `hy/recovery.py` `lme_score` and `pi_lme`.

## Use for the framework
**What the source says.** Baskets and carve-outs, not cov-lite, carry most of the variation in loan document strength. The debt basket is the largest term by size, at 2.34x EBITDA on average (p. 41). The lien covenant has the most carve-outs, 22.5 on average (p. 42). A drop-down such as J. Crew needs an investment basket plus a carve-out (p. 21). Weak terms concentrate in buyouts, in institutional loans, and in deals with high leverage (pp. 26, 55, 56). The market priced the weak terms only after J. Crew, and mostly for distressed borrowers (p. 52). The source does not rank the terms by their effect on price. It ranks them by size and count only.

**What the data says.** The F7 rubric scores six document lines and one distress line in integer points (`docs/framework.md` F7). The debt and lien line fires above half a turn of EBITDA. `hy/recovery.py` `lme_score` uses a different, continuous form with uncalibrated weights (1.0, 1.0, 1.0, 1.0, 0.5). `pi_lme` adds score and `p_liq_8` in the logit with placeholder `GAMMA_LME_DEFAULT = (-3.0, 1.0, 3.0)`, and has no interaction term. F8 holds `rp_capacity_turns` and `debt_capacity_turns`, and `hy/outputs.py` lists `rp_capacity` and `debt_capacity`. No record field holds carve-out counts, the EBITDA add-back count, or basket sizes per covenant. `sponsor_behavior` is a count of prior recaps and transfers. It does not mark sponsor ownership or sponsor expertise. The rubric and the code disagree in form, and this card does not settle that.

**What we decide (our proposal, not the source's claim).**
1. Change the debt and lien line of F7. The half-turn threshold sits far below the mean debt basket of 2.34x (p. 41), so the line fires for most loans and carries little information. Replace it with a test on potential leverage against the distressed multiple of F7.3:

```latex
\text{lev\_max\_potential}_i = \text{lev\_gc\_total}_i + \text{debt\_capacity\_turns}_i, \qquad +1 \text{ if } \text{lev\_max\_potential}_i > \text{distressed multiple}_i
```

Intuition: debt room hurts the bond only when it can push claims past what the firm is worth in distress.

2. Add the interaction of document room and distress to `pi_lme`. The J. Crew loan effect sits almost wholly in the interaction (Table 4, col. 4 and 8, p. 52).

```latex
\pi_{LME} = \sigma(\gamma_0 + \gamma_1\, score_k + \gamma_2\, p^{liq}_{8} + \gamma_3\, score_k \cdot p^{liq}_{8})
```

Intuition: a weak document matters when the borrower has a reason to use it.

3. Split the sponsor line. Give +1 for sponsor ownership. Give +1 more for a prior recap or transfer, or for a credit-expert sponsor. Define credit-expert as a sponsor with a CLO platform or a portfolio bankruptcy in the prior five years (Table 9, p. 57). Keep the total cap of the rubric at 10.
4. Measure every basket in turns of `ebitda_adj_analyst`, not covenant EBITDA. The mean agreement has twelve EBITDA changes (p. 17). Baskets that grow with covenant EBITDA then grow with the add-backs. This step is our inference. The paper does not test grower baskets.
5. Add these fields to the F8 document checklist:
   - basket size in turns for liens, debt, restricted payments, investments, and asset sales
   - carve-out count for liens and debt
   - `ebitda_addback_count` from the covenant EBITDA definition
   - `lev_max_potential` from item 1
   - `institutional_share` and `lead_share` as context fields
   Keep the cov-lite flag, but never use it as a substitute. Old measures explain about half of the count variation and 5% to 10% of basket size variation (p. 51).
6. Read the credit agreement of the loan for every bond issuer that has a loan. The loan document sets how much debt can prime the bonds. This step is our inference. The paper studies loans only.
7. Test. On the observed liability management cases since 2015 (methodology Section 6.3), fit `pi_lme` with and without `gamma_3`. Item 2 holds if `gamma_3 > 0` and the out-of-sample log loss falls. Item 1 holds if the new line has a larger coefficient than the half-turn line in the same fit. A second test follows the paper. Around the announcement of a large liability management exercise, bonds of other issuers in the top `lme_score` quartile should fall more than bonds in the bottom quartile. The fall should be larger for issuers with high `p_liq_short_8`. A zero or positive gap in both tests rejects items 1 and 2.
