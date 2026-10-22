# Kricheff (2012), *A Pragmatist's Guide to Leveraged Finance: Credit Analysis for Bonds and Bank Debt*

FT Press, Upper Saddle River, NJ. First edition, first printing March 2012. ISBN 978-0-13-285523-5. Practitioner book, not peer reviewed. Page numbers below are PDF pages of the copy in the repo root (165 pages). The printed folio on each page equals the PDF page.

**Edition.** The front matter says "© 2012" and "1st ed." (PDF pp. 3–4). `research/reading-list.md` and the `hy/books.py` docstring cite a "2nd ed., 2021". The repo holds no copy of a second edition. Every chapter number and title that the repo cites (ch. 9, 10, 21, 24) matches this 2012 table of contents (PDF pp. 6–9). So the repo uses the 2012 text under a wrong edition label. The staged markdown file name (`kricheff-2012-...`) is correct.

## Claim
Relative value starts from a sheet of securities, not of companies. The core measure is spread to worst per turn of leverage at the bond level (PDF pp. 123–124). That measure "is an interesting tool, but it does not supply the full answer" (p. 124). The analyst must read it beside total leverage, FCF to debt, and the equity cushion. The analyst must also overlay structure, covenants, and events (pp. 123, 125). Credit quality and relative value are separate decisions: yield cannot make up for poor credit (p. 142). A data sort on ratios and yields can find ideas, but it must not make the final decision (p. 143).

## Method
**Spread measure (ch. 8, pp. 33–34).** Use yield to worst (YTW): the lowest of the yield to maturity and the yield to each call date. Take the spread to worst (STW) against a government bond with the maturity of the worst date. Compare spreads, not yields, across maturities.

```latex
STW = YTW - y_{gov}(T_{worst}), \qquad T_{worst} = \arg\min_{T \in \{\text{calls}, \text{maturity}\}} YTM(P, T)
```

Intuition: the investor assumes the issuer takes the option that hurts the investor most.

**Spread per turn (ch. 21, pp. 123–124, Table 21-1).** One row per security. Columns: STW, bond-level debt to EBITDA, total debt to EBITDA, FCF to debt, equity value cushion, spread per turn.

```latex
SPT_b = \frac{STW_b}{Lev_b^{bond}}, \qquad Lev_b^{bond} = \frac{\text{debt ranked at or ahead of bond } b}{\text{EBITDA}}
```

Intuition: the basis points the bond pays for each year of EBITDA that the claims ahead of it, and its own claim, represent. The book shows total leverage beside it, because the issuer must service all debt to avoid a restructuring (p. 123).

**The book's trap example (p. 124).** The DataFone 9% Senior Notes have the widest SPT. The book still calls them risky for three reasons:
1. All-in leverage is 7x, the highest in the table.
2. FCF to debt is 0.1%, "meaningfully lower" than every peer.
3. The equity market value implies "a minimal asset value cushion".

Inside one issuer, the junior note should pay more per turn than the senior note. An inverted pair (Cell Co.) points to strong covenants, an unusual call, or a rich senior note (p. 124). A richer sheet adds issue size, rating, next call, price, YTW, duration, CDS, an index spread, and an investment grade comparable (p. 124).

**Credit ratios (ch. 10, pp. 48–56).**

```latex
\text{Cov}_1 = \frac{\text{EBITDA}_{adj}}{\text{Int}}, \quad \text{Cov}_2 = \frac{\text{EBITDA}_{adj} - \text{Capex}}{\text{Int}}, \quad Lev = \frac{D}{\text{EBITDA}_{adj}}, \quad Lev_{net} = \frac{D - C}{\text{EBITDA}_{adj}}
```

Intuition: Cov₂ is "the more pragmatic ratio", because capex is an ongoing cost for many businesses (p. 48). D is current debt plus long-term debt plus capital leases (p. 50).

```latex
FCF = \text{EBITDA}_{adj} - \text{Capex} - \text{Int}_{cash} - \text{Tax}_{cash} - \Delta WC, \qquad \frac{FCF}{D}
```

Intuition: the share of the debt that one year of free cash could retire (pp. 54–55). FCF plus capex should be close to cash from operations. If it is not, the analyst must explain the gap (p. 54). Deduct a regular dividend (p. 55).

```latex
r_{max} = \frac{\text{EBITDA}}{D}, \qquad r_{max}^{after} = \frac{\text{EBITDA} - \text{Capex} - \text{Amort}}{D}
```

Intuition: the highest interest rate at which EBITDA covers interest exactly once (p. 53). The book uses it as a quick refinance and restructure test.

```latex
\text{Cushion} = \frac{EV}{D}, \qquad EV = \text{market cap} + D - C
```

Intuition: market value above the debt protects the debt. The book's example: an EV multiple of 5x against leverage of 3.42x gives "an equity cushion of about 47% (5 / 3.42)" (p. 51). So the book's 47% is EV to debt minus 1. It is not 1 − D to EV, which would give 31.6%.

Market-adjusted debt (MAD) prices each tranche at market (p. 52, Table 10-4). The book rejects MAD for junior tranches, because senior claims take face value first in a restructuring (p. 53).

**Leverage by tranche (p. 53).** Run leverage at each rank: bank 4x, total 6x in the example. "The size of the increase in leverage between the two tranches has a big impact on how the two pieces of debt trade relative to each other."

**Structure (ch. 15, pp. 86–92).** Rank: senior secured, senior unsecured, senior subordinated, subordinated, preferred, common (p. 87). Two devices override the nominal rank:
1. Structural subordination. A "senior" holdco note ranks behind all opco debt, even behind opco subordinated notes (pp. 88–89).
2. Subsidiary guarantees. A new note with subsidiary guarantees ranks ahead of an old note with none, and the old note is "primed" (pp. 90–91).
A pari passu revolver can still be "first out" by a later clause (p. 91).

**Covenants (ch. 16, pp. 93–101).** Debt incurrence uses a leverage test or a fixed charge cover test. A 5x leverage test at 4x and EBITDA of 500m allows about 500m of new debt (p. 94). A cover test reacts to the coupon on new debt (p. 94, Table 16-1). Restricted payments need the incurrence test plus a basket that builds at 50% of net income (p. 97). Change of control gives a 101 put (p. 98). Maintenance tests step down over time. Bank grids carry about 20% to 25% cushion over the company model (p. 100). Measure headroom on the covenant definition, not on the reported ratio (p. 101). Unrestricted subsidiaries sit outside the covenant group (p. 101).

**Calls and refinance (ch. 14, pp. 79–84).** A standard ten-year bond is non-call for five years, then callable at par plus half the coupon (p. 79). Equity clawback: up to 35% at par plus the coupon in the first three years (p. 81). Quick refinance test: call price times the new coupon (proxy: current YTW) against the old coupon (p. 84). Tenders price at 50 to 100 bp over the government bond (p. 84).

**Recovery (ch. 23, pp. 129–136).** Claim = principal plus accrued interest to the filing date. A discount bond claims its accreted value, not its face (pp. 130–131). DIP and administrative costs take super priority (p. 133). Value the enterprise by peer multiples, deal multiples, and DCF. Add separable assets (p. 133). The fulcrum is the most senior class not paid in full (p. 134). Price a recovery at the start of the case by discount:

```latex
P_0 = \frac{R_{exit}}{(1 + k)^{\tau}}, \qquad 34.7 = \frac{50}{1.2^2}
```

Intuition: a 50 recovery after a two-year case is worth 34.7 today at a 20% IRR (p. 136).

**New issues (ch. 22, pp. 127–128).** In a strong market, a new issue can price at or inside its peers. In a soft market, it pays a new-issue discount (p. 127). Read the use of proceeds, the risk factors, the terms, and affiliate transactions (p. 127). Check the price paid in an acquisition against deals and public multiples. The target's proxy statement can show the losing bids (pp. 127–128). The analyst may reject new-issue add-backs: sponsor fees, full planned savings, cash restructuring costs (p. 128).

**Snapshot and decision (ch. 24–25, pp. 138–143).** Snapshot order: business, debt table with cash and usable revolver, maturities, CFO against capex, LTM adjusted EBITDA, leverage and Cov₂, market EV to EBITDA (p. 138). If operating cash does not cover capex and interest, or maturities are near, do a detailed liquidity analysis (p. 139). Review triggers: a move of 15% or more in the stock or a peer stock, a large price move, or a thesis event that passes (p. 142). Grid: credit risk high, medium, or low, an event qualifier, and a pricing fit, then overweight, evenweight, underweight, or avoid (p. 142).

## Data
The book has no sample, no statistics, and no backtest. Its evidence is a set of worked examples with invented issuers:
- Table 21-1 (p. 123): five mobile telephone issuers (DataFone, Mobile Co., Cell Co., and two others). Table 21-2 (p. 125): operating metrics for the same sector.
- Chapter 9 and 10 sample company: total debt 5.150bn, adjusted EBITDA 1.505bn, leverage 3.42x, FCF 377m, FCF to debt 7.4% (pp. 50, 55).
- Table 16-1 (p. 94): incurrence capacity under a 5x leverage test and a 2.0x cover test.
- Tables 23-1 to 23-3 (pp. 132–135): BlowUp Co. subordination, and a 9x company that emerges at 3x with a 5x valuation.

The pdftotext extract lost every table body. Only the numbers in the prose survive. So the DataFone figures above are those that the prose states (7x, 0.1%). The SPT values of Table 21-1 are not legible.

## Result
What the source says:
1. SPT ranks securities, but its top rank can be a trap. The book's own top SPT bond is the riskiest one (p. 124).
2. The trap shows up as high total leverage, near-zero FCF to debt, and a thin equity cushion. The book gives no numeric cut-offs.
3. FCF to debt "can be one of the most telling and useful ratios" (p. 56).
4. Cov₂ (EBITDA less capex, over interest) beats plain EBITDA cover (p. 48).
5. Ratio sorts find ideas but must not decide alone. Structure and events must enter the decision (p. 143).

Arithmetic slips in the source (stated, not copied):
- p. 51: 5 / 3.42 = 1.46, so "47%" is the excess of EV over debt, not a share of EV.
- p. 94: at 7%, 800m of new debt adds 56m of interest. Cover is then 500 / 256 = 1.95x, below the 2.0x test. The 2.0x test allows about 714m at 7%, and about 385m at 13%, not 400m.

## What our data says (hy/books.py, hy/peers.py, scripts/process.py, 22 October 2026)
**How the repo uses the book today.**
- `hy/books.py`: `kricheff_bridge` (FCF, ch. 9–10), `kricheff_ratios` (ch. 10), `kricheff_snapshot` (ch. 24), `spread_per_turn_bp` (ch. 21).
- `scripts/process.py` step 9 computes `spt_total` = s5 × 10⁴ / gross leverage.
- E13 (weight 2.5% in G4, `hy/groups.py`) = log SPT minus the sector x rating peer median (`hy/peers.py`). Without a peer value, it falls back to the run-wide z-score of `spt_total`.
- The "trap guard" (`process.py` lines 873–875, 893): E13 = 0 unless FCF to debt > 0 and TEV to debt > 1.

**Check against the book. Five mismatches.**
1. **The guard does not catch the book's own trap.** DataFone has FCF to debt of 0.1%, which is > 0. Its cushion is "minimal", not negative, so TEV to debt is above 1. The guard gives E13 full credit for the bond that the book warns against. The book names three warning signs and the guard tests two of them at their weakest level. Total leverage, the first sign, is not in the guard at all.
2. **Total leverage replaces bond-level leverage.** The book divides by bond-level leverage and shows total leverage beside it (p. 123). The repo divides by total gross leverage. The `spread_per_turn_bp` docstring states this. The effect: all bonds of one issuer get the same denominator, so the intra-capital check (junior must pay more per turn) is not possible.
3. **Curve point replaces spread to worst.** The book uses STW (pp. 34, 124). E13 uses `s5`, the 5-year point of the issuer curve. For a callable bond above the call price, STW is lower than the spread to maturity. The decision page already lists OAS as a gap.
4. **The cushion definition differs.** `kricheff_ratios` returns `equity_cushion` = 1 − D to EV. The book's figure is EV to D minus 1 (p. 51). Both rank issuers the same way. The levels differ (31.6% against 47% for the book example). The docstring must name the definition it uses.
5. **Edition label.** The repo says 2nd ed. 2021. The copy in hand is the 1st ed. 2012 (see the header).

The repo also matches the book in four places. The FCF bridge and the CFO check match pp. 54–55. The Cov₂ ratio and `ebitda_to_debt` match pp. 48, 53. The snapshot rule matches p. 139. The step-down headroom check matches p. 125 and p. 100.

**What the backtest already says about E13.** Decision page `2026-10-22-esp-peer-groups`: E13 against peers adds +0.023 beyond spread at 6 months (t 1.1) and +0.026 at 12 months (t 0.9). It fails the t 2 bar. This agrees with the book: SPT alone "does not supply the full answer".

**Falsifiable tests on the TRACE panel (2008–2026).**
1. **Guard as the book states it.** Replace the guard with three conditions: total leverage below the peer-cell median plus one turn, FCF to debt above the peer-cell bottom quintile, and EV to D above 1.25. Compare the beyond-spread rank IC of E13 under the old guard, the new guard, and no guard. Keep the new guard only if it beats both at 6 and 12 months in at least three of the four cycle windows.
2. **Trap decile.** Take the top SPT decile each month. Split it by the three warning signs. The book predicts that the bonds with two or more signs underperform the rest of the decile in forward excess return. Reject the guard if the split shows no gap.
3. **Bond-level leverage.** Where the capital structure table (methodology 3.3) gives debt by rank, compute SPT on bond-level leverage. Test the intra-issuer rule: within an issuer, a junior bond with a lower SPT than a senior bond should underperform the senior bond. This is the S4 pair signal at the book's definition.
4. **Recovery discount.** For defaulted bonds in `sp_ratings` (D or SD), compare the price at default with the discounted recovery at k = 20% and the realised time to emergence. The book's 20% IRR is a prior, not a fit.

## Limits
- A practitioner book with no data, no statistics, and no out-of-sample test. Its rules are expert opinion.
- The examples are invented, and the extract lost every table body. Only numbers in the prose can be checked.
- No cut-offs for the trap: "high" leverage and "minimal" cushion are words, not numbers. Any guard threshold is our choice and needs a test.
- US law and US market practice from about 2011. LIBOR, pre-2017 covenant norms, and pre-ASC 842 leases (only capital leases enter debt, p. 50).
- The book treats SPT as a cross-section tool for one sector at a time. It says nothing about SPT across sectors or over time.
- The 2nd edition may differ in chapter numbers and content. This card does not cover it.

## Section touched
`docs/methodology.md` Section 7.4 (model-free check: spread per unit of risk, E13 and the intra-capital SPT), Section 4.2 (cash flow and liquidity: FCF, Cov₂), Section 4.3 (capital structure: leverage by rank, structural subordination), Section 4.6 (covenant headroom), Section 6.2 (waterfall and recovery: accreted claims, fulcrum, discounted recovery), and Section 9.1 (event taxonomy: review triggers). `docs/framework.md` F5 (claim sizing: accreted value, guarantees) and F8 (metrics catalogue). Code: `hy/books.py`, `hy/peers.py`, E13 in `hy/groups.py` and `scripts/process.py`. Decision page `docs/decisions/2026-10-22-esp-peer-groups.md`. A sprint that runs test 1 should add a decision page on the trap guard and correct the edition label in `research/reading-list.md` and `hy/books.py`.
