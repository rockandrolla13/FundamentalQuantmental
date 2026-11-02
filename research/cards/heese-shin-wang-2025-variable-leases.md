# Heese, Shin, and Wang (2025), "Variable leases under ASC 842: first evidence on properties and consequences"

Review of Accounting Studies 30(3), pp. 2218-2263, DOI 10.1007/s11142-025-09899-z. Peer-reviewed, open access. We read the publisher PDF, 47 pages. Page numbers are PDF pages. Journal page = PDF page + 2217. Evidence class: US listed firms, equity betas and credit ratings. No bond spreads.

**Added at the audit close.** The screen graded this paper 3, and the cap dropped it.

## Claim
ASC 842 lets firms keep variable leases off the balance sheet (p. 1). Variable lease expense is large, persistent, and predictable, with a limited response to revenue (p. 1). After adoption, firms report lower minimum commitments and higher variable expense, which suggests substitution (pp. 1, 7). Neither equity betas nor credit ratings reflect variable leases (pp. 1, 34).

## Method
**Substitution test (Table 6, p. 35).** Log first-year commitment `MRC1` and log rent in excess of the prior commitment on a post-adoption dummy, with firm effects.

```latex
\log Y_{i,t} = a_i + b\,PostASC842_{i,t} + \gamma' X_{i,t} + e_{i,t}, \qquad Y \in \{MRC1,\ RentExMRC1\}
```

Intuition: if firms move rent from fixed to variable contracts, the fixed line falls and the excess of rent over the fixed line rises.

**Rating test (Table 7 Panel C, p. 34).** Log rating on leverage and on the log ratio of variable to operating lease expense.

## Data
US public firms, fiscal years 2014 to 2022, about 3,000 unique firms (pp. 6, 16). More than 40% of firms report variable lease expense (p. 3).

## Result
- **Size.** Variable expense is 25% of operating lease expense for the average firm that reports both (p. 3). Conservative recognition would raise debt by 7.1% on average (p. 1).
- **Substitution (Table 6, p. 35).** `MRC1` falls: -0.0322 (se 0.014), and -0.0576 (se 0.018) with controls. `RentExMRC1` rises: 0.4817 (se 0.040), and 0.4003 (se 0.047) with controls.
- **Leverage (Table 7 Panel A, p. 36).** Log debt over equity rises by 0.4446 (se 0.029), and by 0.2484 (se 0.024) with controls.
- **Risk measures (p. 34).** Equity betas rise by about 5%. Ratings fall by 1.5% on average. Ratings do not vary with the extent of variable leases.

## Limits
- No bond spread. The rating result says nothing on price.
- The liability is an estimate, because filings give no schedule of variable payments.
- We read pp. 1-7, 34-36. We checked Tables 6 and 7. We did not audit the persistence tables.

## Section touched
`docs/methodology.md` Section 4.7 (lease ladders). `hy/sources/schedules.py`.

## Use for the two clocks
**What the source says.** A filed lease ladder misses variable rent. After ASC 842, the fixed line can fall while rent does not.

**What our data says.** `ladders["operating_lease"]` holds the fixed schedule only. No variable lease field exists on file.

**What we decide (our proposal, not the source's claim).** Add `rent_excess`, which is rent expense less the prior year's first-line commitment, over LTM revenue. Report it beside `amt_lease_near` in Method 1. Give it no sign prior. It may mix growth in leases with variable rent, so it stays a memo field until a test separates the two.

**Test.** Report only in M1.2. A `rent_excess` slope with the permutation null above its 95th percentile earns a place on the M2.2 list.
