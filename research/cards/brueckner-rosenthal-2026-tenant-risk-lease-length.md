# Brueckner and Rosenthal (2026), "Tenant Riskiness, Contract Length, and the Term Structure of Commercial Leases"

Management Science, DOI 10.1287/mnsc.2024.04959. Peer-reviewed journal article. We read an earlier version: CESifo Working Paper 10189, December 2022, 37 pages, EconStor copy. We did not open the journal version, so its numbers may differ. Page numbers below are PDF pages of the CESifo file. PDF page = printed page + 4. Evidence class: establishment leases, not listed bond issuers.

## Claim
Possible default on a long lease links tenant risk to lease length (p. 4). Lower-risk tenants get longer leases, but only when they are new to the building (pp. 8, 25). Risky tenants pay a higher rent premium for a long lease than low-risk tenants (p. 4).

## Method
**Model.** Two periods, two tenant types, short and long contracts (pp. 9-14). Short rent adjusts to each tenant's revenue. Long rent is fixed, and a tenant defaults in period 1 when revenue falls below it. Landlords must earn the same expected profit on both contracts.

```latex
\pi^i_{LT}(r) = (1+\delta(1-F^i))(p_0 - r) + \delta(1-F^i)k^i + \delta \int_{r-p_0-k^i}^{\bar\epsilon} \epsilon f(\epsilon)\, d\epsilon \quad (1)
```

Intuition: default cuts off the tenant's downside and fixed rent keeps the upside, so the tenant with the bigger upside values the long lease more.

Proposition 1: good tenants on long leases and bad tenants on short leases is an equilibrium when period-1 revenues diverge enough (p. 13).

**Lease length regression (p. 16).**

```latex
\log(\text{LeaseMonths}_\ell) = \beta_1 \text{Risk\_Low} + \beta_2 \text{Risk\_Med} + \beta_3 \text{Risk\_NA} + \gamma X_\ell + \eta_{\text{loc}} + e_\ell
```

Intuition: within one city, zip code or building, the regression asks whether a safer tenant signs a longer lease. High risk is the omitted class. Controls are log establishment age, log space, workers per square foot, headquarters and industry.

**Rent term structure (p. 24).** Regress log effective rent on log lease length, separately for low-risk and risky tenants.

## Data
- CompStak lease records, drawn October 2021, matched to Dun and Bradstreet establishment records from 2018 (pp. 7, 14-15).
- Final sample: 127,872 leases in seven US areas (p. 15). California cities make up 61% (p. 27).
- Mean lease length 66.65 months, median 60 (Table 1, p. 27).
- 60.4% low risk, 9.1% medium, 8.9% high, 21.6% missing (p. 27).
- New tenants 57%, renewals 43% (p. 19).

## Result
**Length (Table 2, p. 28).** The low-risk coefficient is 0.0443 (t 4.55) with no location effects. It is 0.0288 (t 3.57) in column 5 and 0.0287 (t 3.29) in column 6.

**New against renewal (Table 3, p. 29).**

| Lease type | Zip effects | Building effects |
| --- | --- | --- |
| New tenant, low risk | 0.0408 (t 4.51) | 0.0331 (t 3.06) |
| Renewal, low risk | 0.0118 (t 0.96) | 0.0248 (t 1.65) |

**Other drivers (Table 2, column 2, p. 28).** Retail is 0.4408 (t 24.97), FIRE is 0.2919 (t 14.70), and services are 0.2500 (t 18.48), each against manufacturing. Log space is 0.2059 (t 43.30). So sector and size move lease length far more than the risk class does.

**Rent (Table 6, p. 32).** With zip effects, the lease length coefficient is 0.1664 (t 10.37) for risky tenants and 0.0979 (t 11.14) for low-risk tenants. The gap holds for new tenants (0.1043 against 0.0616) and for renewals (0.2416 against 0.1957).

## Limits
- Small effect. A 3% to 4% longer lease is about 2 to 3 months on the 66.65 month mean (our arithmetic).
- Establishments in dense cities, most in offices. Few of these tenants are bond issuers.
- Risk is measured in 2018, not when the lease started (p. 16). The file also drops failed firms with a lag (p. 16). So the sample holds survivors, and the score can look ahead.
- Lease length enters the rent regression as exogenous (p. 23, footnote 21).
- Source inconsistency: the introduction says the slope is higher for low-risk tenants (p. 8). The abstract, the text and Table 6 say the slope is higher for risky tenants (pp. 4, 24, 32). We follow the table.
- Source inconsistency: the bottom rows of Table 2 appear to swap the labels of zip and building effects (p. 28).

## Section touched
`docs/methodology.md` Section 4.7 (reading of the lease tail, the sentence "large, long-lease issuers are stronger credits") and Section 7.2 (fair spread features). `hy/clocks.py`.

## Use for the two clocks
**What the source says.** Lease length is a choice, and it screens tenant risk. The effect is small and appears only for new tenants. Renewal adds no information beyond what the landlord already knows.

**What the data says.** Section 4.7 offers "large, long-lease issuers are stronger credits" as an untested reason for the wrong sign. The repo holds no test of it. `clock_facts.py` measures the lease tail only through the share of obligations due after year 2.

**What we decide (our proposal, not the source's claim).**
1. Accept selection as a partial reason only. Effects of 3% to 4% in lease length cannot alone make a coefficient of -2.07 on a share.
2. Remove the larger drivers first. Compute the lease tail within sector and size cells, because sector and size dominate lease length here.

```latex
\text{lease\_tail\_resid}_{i,t} = \log(\text{lease\_tail\_years}_{i,t}) - \text{mean}_{c(i),t}\big[\log(\text{lease\_tail\_years})\big]
```

Intuition: a lease is long or short only against firms in the same business and of the same size.

3. Test. Regress log spread on `lease_tail_resid` with `lev_lease_adj`. If selection is the reason, the coefficient stays below 0 within cells. If composition is the reason, it moves to 0 or above.
