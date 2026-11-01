# Dogan (2016), "Non-cancellable Operating Leases and Operating Leverage"

European Financial Management 22(4), pp. 576-612, DOI 10.1111/eufm.12069. Peer-reviewed journal article. We read the published pages on the Bilkent University repository, 37 pages. Page numbers below are journal pages. Journal page = PDF page + 575. Evidence class: equities, not credit. The paper has no bond data except a rating-implied debt return in the unlevered test (p. 598).

## Claim
Firms with more non-cancellable operating lease commitments earn higher stock returns, and the premium is countercyclical (p. 576). Their cash flows are more sensitive to aggregate shocks, so leases act as operating leverage (p. 576). The relation is stronger in small firms (p. 576).

## Method
**Measure (p. 581).**

```latex
\text{Operating Lease Ratio}_{i,t} = \frac{MRC1_{i,t-1}}{Assets_{i,t}} \quad (1)
```

Intuition: the rent the firm cannot avoid next year, over its assets, shows how much of its cost is fixed by contract.

The author uses the first-year line and not a present value (p. 580). Present values rest on discount rates, and the "thereafter" field is limited before 2000 (p. 580).

**Portfolios (p. 582).** Decile sorts each June, equal and value weighted, with returns from July. Business cycle state is set by NBER dates in June (p. 585).

**Fama-MacBeth (p. 588).** Monthly cross-sections of returns on the ratio and controls, with Newey-West errors.

**Factor tests (pp. 592-596).** CAPM, Carhart and Fama-French five-factor alphas.

**Cost stickiness (p. 597).**

```latex
\log\frac{Cost_{i,t}}{Cost_{i,t-1}} = b_0 + b_1 \log\frac{Sales_{i,t}}{Sales_{i,t-1}} + b_2 D_{i,t} \log\frac{Sales_{i,t}}{Sales_{i,t-1}} + e_{i,t} \quad (3)
```

Intuition: `b1` is the response of cost to a rise in sales, and `b1 + b2` is the response to a fall. Near zero means a true fixed cost.

## Data
- US firms in CRSP and Compustat, 4,926 firms, accounting data 1975 to 2012, returns July 1976 to December 2013 (p. 581).
- Without regulated and financial firms. December fiscal year only, with a check that drops this rule (pp. 581-582).
- About 70% of Compustat firms report the lease line (p. 581).

## Result
**Firm profile (Table 1, p. 583).** From the lowest to the highest lease decile:

| Variable | Low | High |
| --- | --- | --- |
| Lease ratio | 0.2% | 8.3% |
| Market capitalisation ($m) | 3,446 | 425 |
| Financial leverage | 0.27 | 0.19 |
| Cash flow over assets | 0.08 | 0.00 |
| Cash over assets | 0.14 | 0.17 |
| ROA | 0.04 | -0.06 |
| Interest over lease payments | 16.93 | 0.30 |

**Returns (Table 3, pp. 586-587).** High minus low, monthly percent:

| State | Equal weight | Value weight |
| --- | --- | --- |
| All, 450 months | 0.92 (t 5.14) | 0.39 (t 1.98) |
| Expansion, 378 months | 0.60 (t 3.20) | 0.14 (t 0.67) |
| Contraction, 72 months | 2.42 (t 5.42) | 1.69 (t 2.52) |

In annual terms the equal-weight spread is 29.0% in contractions and 7.2% in expansions. The value-weight spread is 20.3% in contractions (p. 585). The two-sample t for expansion against contraction is -3.84 and -2.53 (p. 585).

**Fama-MacBeth (Table 4, p. 589).** The lease ratio alone is 15.98 (t 5.13). With all controls in the last column it is 4.42 (t 1.96).

**By size (Table 5, p. 592).** Micro-cap 6.27 (t 2.86), small-cap 5.48 (t 1.57), big-cap 7.19 (t 1.65).

**Alphas (Table 6, pp. 593-596).** Equal-weight five-factor alpha is 0.84 (t 4.25). Value-weight five-factor alpha is -0.16 (t -0.79). The author does not propose a separate factor, and links the ratio to SMB (p. 596).

**Cost stickiness (Table 8, p. 598).** Response to a fall in sales, `b1 + b2`: operating lease -0.02, interest 0.39, pension 0.45.

**Within and across industry (p. 599).** The intra-industry part has more power than the industry part.

## Limits
- Equity evidence. The return premium may not carry to spreads or bond returns.
- The value-weight alpha is not significant, so the premium rests on small stocks.
- The sample is broad. It is not limited to bond issuers or to high yield.
- The ratio uses the first-year line, so it measures intensity and not the tail of the lease.
- Non-cancellable leases are "non-cancellable except when the firm enters into Chapter 11" (p. 596). So the test does not price rejection.
- Source inconsistency: the text gives `b1 + b2` of 0.13 for a combined measure of interest and pension costs (p. 597). Table 8 gives 0.39 and 0.45 (p. 598).
- Source inconsistency: Table 3 labels the contraction standard deviation row `deV W` in the place of `deEW` (p. 587).

## Section touched
`docs/methodology.md` Section 4.7 (lease part of `O_t`, the reason offered for the wrong sign), Section 8 (composite), Section 9 (cycle state). `hy/clocks.py`.

## Use for the two clocks
**What the source says.** Lease-heavy firms are small, less profitable, and hold more cash and less debt. Their risk premium is highest in recessions. Rent behaves as a truly fixed cost when sales fall.

**What the data says.** Section 4.7 offers "large, long-lease issuers are stronger credits" as a possible reason for the wrong sign. This paper contradicts that for lease intensity in equities. Section 4.7 also records that neither share ranks hedged returns beyond spread level (recontract +0.027, t 1.0, at 6 months).

**What we decide (our proposal, not the source's claim).**
1. Separate intensity from tail. Add `rent_ratio = rent_1y / assets` beside the lease tail in years of EBITDAR. The two measures need not share a sign.
2. Read the fall in leverage in Table 1 as the main warning about the shares. In `renewal_recontract_share` the denominator holds debt, so a lease-heavy issuer with little debt has a high share by construction. Replace shares with amounts over EBITDAR and control for `lev_lease_adj`.
3. Test by cycle state. Refit the split test separately for months of credit stress and months without. The source's logic predicts a coefficient on the lease measure that is higher in stress.
4. Build the bond version of this sort, for method only. Form decile portfolios on `rent_ratio`. Take the excess return over the duration-matched Treasury, hedged as in `hy/backtest.py`. Report it in expansion and in stress. It passes as a timing input if the top minus bottom spread in stress is above the spread in expansion, with t above 2 (Our choice, v0).
5. Use `b1 + b2` as a per-issuer check on what is fixed. An issuer whose rent falls with sales has some flexibility that the ladder does not show.
