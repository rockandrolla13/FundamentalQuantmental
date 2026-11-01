# Friewald, Nagler and Wagner (2022), "Debt Refinancing and Equity Returns"

Journal of Finance 77(4), pp. 2287–2329, DOI 10.1111/jofi.13162. Peer-reviewed. **Evidence from equities.** **Added by citation chasing.** The shortlist names it as the counterpart of Chaderina, Weiss and Zechner (2022). **We did not open the journal article.** We read the working paper of 14 June 2017, 51 pages, from the Católica Lisbon site (`clsbe.lisboa.ucp.pt/research-2-17-paper-christian-wagner`). Page numbers are PDF pages. The journal numbers may differ.

## Claim
Shareholders cover shortfalls when debt rolls, so expected equity returns rise with leverage and with refinancing intensity (p. 2). Leverage alone is not enough (p. 3). Refinancing intensity carries return information beyond size and book-to-market (p. 2).

## Method
A Leland (1998) model in which the firm picks leverage and the mix of a short and a long bond (p. 3). Refinancing intensity stays fixed after t = 0, and leverage moves with equity value (pp. 13–14).

Empirical tests: 10 x 10 portfolio sorts on refinancing intensity and leverage (p. 17), and Fama-MacBeth regressions by firm (pp. 19–21).

```latex
RI_{i,t} = \frac{DD1_{i,t}}{BD_{i,t}}, \qquad MLEV_{i,t} = \frac{BD_{i,t}}{BD_{i,t} + ME_{i,t}} \quad (\text{p. 20})
```

Intuition: RI is the share of book debt due within one year, and it measures how soon equity holders must meet the market. Data lag six months (p. 17). Newey-West errors (p. 33).

## Data
CRSP and Compustat, January 1972 to December 2014. 12,130 firms and 1,382,615 firm-months, without financials and utilities (p. 16).

## Result
**Table III, p. 33 (log variables).** RI alone 0.10 (t 3.35). With leverage: RI 0.14 (t 4.85), leverage 0.14 (t 3.05). With beta and size: RI 0.07 (t 5.33), leverage 0.07 (t 2.00). With book-to-market: RI 0.05 (t 4.34), leverage −0.02 (t −0.57). With further controls: RI 0.05 (t 4.17) (p. 33, p. 20). So leverage loses significance once book-to-market enters, and RI does not.

**Pattern (pp. 14, 17–18).** Returns rise with leverage for a given RI and with RI for a given leverage. The biggest firms have low leverage and low RI (p. 18).

## Limits
- Equities. Credit returns are not in this paper.
- One-year window. Compustat data carries the lag.
- The text gives two definitions: debt due within one year over total assets (p. 17) and over total book debt (p. 20). The tables use book debt (p. 33).
- Sample ends in 2014. No high yield split.
- Model holds the maturity structure fixed after t = 0 (p. 13).

## Section touched
`docs/methodology.md` Section 4.7 and Section 8 (the premium reading of refinancing need).

## Use for the two clocks
This section is our proposal, not the source's claim.

**What the source says.** Refinancing intensity earns a positive equity premium with leverage held fixed.

**What our data says.** None on our data. The repo holds no equity return test of the clocks.

**What we decide.** Record the disagreement with `chaderina-weiss-zechner-2022-maturity-premium.md`. Chaderina et al. report that long-maturity firms earn more (0.21% a month, t 2.93, p. 6 of that file). The two tests hold different things fixed. This paper holds leverage fixed. Chaderina et al. sort on maturity within size, and their long buckets have higher leverage (32.08% against 23.89%, Table 2, p. 5 of that file). Chaderina et al. also read the short-term result as consistent with short-horizon risk (p. 3 of that file).

Choose: use this paper's design for the clocks. Compare issuers at equal leverage, because both clock shares mix leverage and timing. This choice follows the reading above, which we have not tested.

**Test.** In any clock regression, report the coefficient with and without leverage and with and without the spread level. A clock feature that changes sign when leverage enters reads as a leverage proxy, not a timing effect. Our choice, v0.
