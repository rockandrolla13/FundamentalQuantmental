# Gavazza (2010), "Asset liquidity and financial contracts: Evidence from aircraft leases"

Journal of Financial Economics 95 (2010), pp. 62-84, DOI 10.1016/j.jfineco.2009.01.004. Peer-reviewed journal article. We read the author's copy of the published pages, 23 pages. Page numbers below are journal pages. Journal page = PDF page + 61. Evidence class: asset-level contracts in one industry, no bond spreads.

## Claim
More liquid assets are more likely to be leased, in particular under operating leases (p. 62). They have shorter operating leases, longer capital leases, and lower markups of operating lease rates (p. 62). Operating and capital leases are different contracts (p. 74).

## Method
**Liquidity proxy.** `AIRCRAFT PER TYPE` is the stock of aircraft of the same type when the carrier acquired the aircraft (p. 68). Intuition: more units in use means more potential next users. The source reports that this proxy goes with higher turnover and lower price dispersion (p. 68).

**Lease choice (p. 71).**

```latex
Leased_{lijt} = f\big(\alpha Y_{lijt} + \beta \log(\text{AircraftPerType}_{it}) + \mu_i + \gamma X_j\big) \quad (2)
```

Intuition: within one aircraft type, a thicker market raises the chance that the aircraft is leased.

**Lease maturity (p. 73).** The sample holds leases active in April 2003, so it is truncated. The author estimates by maximum likelihood with the truncation in the likelihood.

```latex
Duration_{lijt} = \alpha Y_{lijt} + \beta \log(\text{AircraftPerType}_{it}) + \mu_i + \gamma_j + \eta_t + e_{lijt} \quad (3)
```

Intuition: a lessor who must re-lease an aircraft accepts a shorter contract when it can find the next user with ease.

**Markup (pp. 68, 74).**

```latex
m_{skit} = \frac{l_{skit}}{p_{skit} - b\,E_t p_{s+1,k,i,t+1}} \quad (1)
```

Intuition: the markup compares the lease rate with the cost to buy the aircraft and sell it a year later.

**Identification (pp. 79-80).** Instruments interact aluminum prices with weight and seats, and oil prices with engines, weight and time since production ended.

## Data
- Each Western-built commercial aircraft active in April 2003: 14,301 passenger aircraft, 35 types, 713 carriers (p. 69).
- 52.1% leased: 33.5% operating and 18.6% capital (p. 69).
- Lease contracts with maturity: 2,086 operating, mean 100.34 months, and 1,814 capital, mean 223.21 months (p. 69).
- Price and lease rate panel: 3,927 model-vintage-years, 1967 to 2003 (pp. 67, 69).

## Result
**Lease choice (Table 3, p. 72).** The coefficient on log aircraft per type is 0.33418 (se 0.06552) in the probit and 0.09351 (se 0.02016) in the linear model with carrier effects. A 10% rise in liquidity raises the chance of a lease by 1.3 points in the probit (p. 71) and by 0.9 points with carrier effects (p. 71).

**Maturity (Table 5, p. 74).** The operating lease coefficient is -13.70 (se 6.73). The capital lease coefficient is +12.96 (se 6.84). The Boeing 737 stock rises from about 1,000 to about 4,000. Over that rise, operating maturity falls from 100 to 80 months, and capital maturity rises from 205 to 225 months (pp. 73-74).

**Pair example (Table 2, p. 70).** MD-80 against A300-600: leased 59.3% against 36.2%, operating maturity 98.6 against 120 months, capital maturity 247.7 against 226.5 months.

**Markup (p. 74).** A 10% rise in liquidity lowers the markup by 1.4 to 2.0 percentage points.

**Instruments (p. 80).** The first-stage F is above 15. A 10% rise raises the chance of a lease by 1.2 to 1.5 points.

**Law (pp. 64-65).** An operating lessor counts as the owner, and it can repossess when the lessee rejects the lease. Roughly speaking, a capital lessor counts as a secured lender (p. 64), with an aircraft exception under Section 1110. Section 1110 lets a lessor foreclose an aircraft after 60 days.

## Limits
- One asset class, with a single global market and a measured stock. Most issuer assets have no such count.
- The author says that carrier analysis is "suggestive at best", because the data has few carrier characteristics (p. 67).
- The tests do not include a credit outcome.
- Source inconsistency: the text says that twice the stock shortens operating leases by about 14 months and lengthens capital leases by about 13 months (p. 73). With a natural log, twice the stock gives about 9.5 and 9.0 months (our arithmetic: 13.70 and 12.96 times 0.693). The Boeing 737 example fits the natural log.
- Source inconsistency: the instrument section says markups "increase" with liquidity (p. 80), while its own text confirms that markups are lower.

## Section touched
`docs/methodology.md` Section 4.7 (lease types in `O_t`, a missing re-marketability input), Section 6.2 (recovery). `docs/framework.md` F5 (equipment and aircraft leases). `research/cards/two-clocks-origin.md` (re-marketability listed as missing).

## Use for the two clocks
**What the source says.** A long operating lease can mark an illiquid asset. The lessor wants a long contract when the next user is hard to find. A capital lease behaves like debt.

**What the data says.** `clock_facts.py` puts operating and finance leases into one bucket, "Leases in force", and `obligation_kind` files that bucket as recontract. `research/cards/two-clocks-origin.md` lists re-marketability as missing. The repo has no measure of it.

**What we decide (our proposal, not the source's claim).**
1. Move finance leases to the debt side of the clock. Keep operating leases on the recontract side.
2. Add `remarket_score`, the count of other users or same-type assets, as a sector-specific field. Undisclosed is NaN, not 0.
3. Let the recontract risk depend on it.

```latex
\text{recontract\_bite}_{i,t} = \text{lease\_tail\_years}_{i,t} \times \big(1 - \text{rank}(\text{remarket\_score}_{i,t})\big)
```

Intuition: an obligation past the contract end hurts less when another user can take the asset.

4. Test. On sectors where the score exists, regress log spread on the lease tail and on `recontract_bite`. Re-marketability matters when the coefficient on `recontract_bite` is above 0 with the lease tail in the model. This paper predicts longer operating leases on less liquid assets, so a raw lease tail mixes two effects with opposite signs for credit risk.
