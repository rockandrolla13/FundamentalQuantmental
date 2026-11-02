# Irvine, Park and Yıldızhan (2016), "Customer-Base Concentration, Profitability, and the Relationship Life Cycle"

The Accounting Review, DOI 10.2308/accr-51246. Peer-reviewed journal article. We read an earlier version: MPRA Paper 58435, dated August 2014 on its title page, 57 pages. Its title is "Customer-base concentration, profitability and distress across the corporate life cycle". We did not open the journal version, so its numbers may differ. Page numbers below are PDF pages of the MPRA file. PDF page = printed page + 2. Evidence class: listed firms, failure and rating tests, no bond spreads.

## Claim
Customer concentration helps profitable firms and hurts young and unprofitable firms (p. 3). The relation changes with the age of the customer relationship. It is negative early and turns positive as the relationship matures (p. 3). Concentration raises the chance of failure, and it worsens the credit rating (pp. 6, 23-24).

## Method
**Concentration (p. 12).**

```latex
CC_{i,t} = \sum_{j=1}^{n} \left( \frac{\text{Sales to Customer}_{i,j,t}}{\text{Total Sales}_{i,t}} \right)^2 \quad (1)
```

Intuition: a Herfindahl index over major customers rises with fewer customers and with larger shares. The authors use the decile rank, `Rank(CC)`, because `CC` is skewed (p. 14).

**Relationship age (pp. 11, 27).** `LINKAGE` is a weighted average of the log years a firm has sold to its major customers. It exists only where the customer is identified. Firm age is the fallback, and it correlates 0.42 with `LINKAGE` (p. 28).

**Failure model (pp. 20-21).** A dynamic logit in the form of Campbell, Hilscher and Szilagyi (2008), with all inputs observed 12 months before the event (p. 21, footnote 14).

```latex
\Pr(\text{Fail}_{i,t+1}) = \Lambda\big(a + b\,\text{Rank}(CC)_{i,t} + \gamma Z_{i,t}\big)
```

Intuition: concentration earns a place if it predicts failure beyond leverage, profit, volatility, size, cash and returns.

**Rating model (p. 23).** An ordered logit of the S&P rating, where a higher number means a worse rating.

**Life cycle (pp. 26-27).** Interact `Rank(CC)` with quintile dummies of `LINKAGE` in regressions of ROA, ROE and SG&A.

## Data
- CRSP and Compustat firms with customer segment data, 1977 to 2007, 49,760 firm-years (pp. 11-12).
- 22,480 firm-years have a `LINKAGE` value, and 10,836 have an operating loss (p. 12).
- Each supplier averages 1.89 major customers, who make up 33% of sales (p. 13).
- `CC` mean 10.1%, standard deviation 14.7% (p. 14).
- Disclosure covers customers above 10% of sales (p. 11).

## Result
**Failure (Table 6 Panel A, p. 47).** `Rank(CC)` is 0.401 (z 3.21). The pseudo R-squared moves from 0.209 to 0.210. There are 771 failures in 48,948 firm-years.

**Failure by group and firm traits (Table 6 Panels B and C, p. 48).**

| Group | Mean failure probability | Leverage | Cash | Volatility |
| --- | --- | --- | --- | --- |
| No major customer data | 1.8% | 47.88% | 7.84% | 49.44% |
| Lowest concentration | 1.3% | 40.19% | 7.67% | 53.49% |
| Group 2 | 1.7% | 36.18% | 9.21% | 59.89% |
| Group 3 | 2.0% | 34.03% | 10.11% | 63.29% |
| Highest concentration | 2.5% | 27.88% | 12.16% | 67.95% |

**Rating (Table 7, p. 50).** `Rank(CC)` is 1.084 (z 14.57) with no controls and 0.564 (z 7.34) with controls. A move from the 50th to the 75th percentile moves the mean rating from BB to BB- (p. 24).

**Operating leverage (p. 19).** SG&A elasticity to sales falls from 0.79 in the lowest concentration quintile to 0.56 in the highest. Demand uncertainty rises from 0.19 to 0.32.

**Relationship age (pp. 27-28).** The ROA coefficient for the youngest relationships is -0.06. The second quintile adds 0.04 and the third adds 0.059. The authors say firms remove the adverse effect once a link reaches about four years. Gross margin gets no such relief (p. 28).

**New customers (p. 26).** Firms that gain a major customer have 11.6% higher sales growth (t 6.41) than matched firms.

## Limits
- The sample ends in 2007, and it holds a broad equity universe, not bond issuers.
- The failure gain is small in pseudo R-squared (0.209 to 0.210).
- Rated firms are few: 5,954 observations (p. 50).
- Concentration is measured only from customers above the 10% line. So it is a floor.
- `LINKAGE` covers 45% of the sample, and the authors note that age is an imperfect proxy for life cycle stage (p. 11, footnote 4).
- This is the 2014 version, under an earlier title.
- Source inconsistency: the footnote on p. 22 says the regression drops `Rank(CC)_3`, and the note to Table 6 says `Rank(CC)_2` is suppressed (p. 46). Table 6 prints `Rank(CC)_1`, `_3` and `_4` (p. 47).

## Section touched
`docs/methodology.md` Section 4.7 (`cust_top1`, `cust_top3`, `cust_hhi_floor`, downside rule 4) and Section 4.4 (risk flags). `hy/clocks.py` (`concentration`).

## Use for the two clocks
**What the source says.** Customer risk depends on the age of the link. Firms with concentrated customers respond with less debt and more cash.

**What the data says.** `clocks.concentration` gives top-1, top-3 and a Herfindahl floor. Rule 4 of Section 4.7 removes the top customer's share of RPO, whatever the age of the link. CoreWeave is the only case on file with this downside (`docs/decisions/2026-10-22-duration-mismatch.md`). Section 4.7 records no spread test of `cust_hhi_floor`.

**What we decide (our proposal, not the source's claim).**
1. Add `link_age_years` for each disclosed customer above 10% of revenue, from the first filing that names it.
2. Split the concentration measure by link age.

```latex
\text{cc\_young}_{i,t} = \sum_{j:\ \text{age}_j < 4} s_{j,t}^2, \qquad \text{cc\_old}_{i,t} = \sum_{j:\ \text{age}_j \ge 4} s_{j,t}^2
```

The 4-year line follows p. 28 (Our choice, v0). Intuition: a young concentrated link still carries sunk customer-specific cost, and an old one has paid that cost.

3. Keep undisclosed as NaN and not as 0. This paper shows that firms with no major customer data are not safest (1.8% against 1.3%).
4. Use leverage as a control whenever concentration enters a spread test. In the table above, leverage falls from 47.88% to 27.88%. So concentration can also take the wrong sign through the same channel as the recontract share.
5. Test. Regress default within 24 months on `cc_young`, `cc_old` and `lev_lease_adj`. The life cycle reading passes when `cc_young` is above 0 and above `cc_old`, with a difference z above 2 (Our choice, v0).
