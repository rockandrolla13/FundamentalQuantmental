# Ivashchenko and Kosowski (2024), "Transaction Costs and Capacity of Systematic Corporate Bond Strategies"

Financial Analysts Journal 80(4), pp. 53–80, DOI 10.1080/0015198X.2024.2360390. Peer-reviewed, open access. Corporate bonds, US IG and HY, long-only. We read the journal article from Spiral, Imperial College (29 pages). Page numbers are PDF pages. Printed page = PDF page + 51.

## Claim
Low-turnover credit portfolios keep their returns after cost and have high capacity (p. 2). High-turnover portfolios hit capacity fast (p. 2). Realistic limits on rebalancing raise net Sharpe ratios for high-turnover rules and raise capacity (pp. 19–22). Costs do not absorb the corporate bond risk premium, even in the largest market portfolios (p. 2).

## Method
**Invariance illiquidity (p. 10).**

```latex
\frac{1}{L_{it}} = \Big(\frac{C\,\sigma^2_{it}}{V_{it}\, m^2}\Big)^{1/3}, \qquad C = 2000,\ m^2 = 0.25 \quad (1)
```

Intuition: more risk moved per dollar of volume means a larger cost per trade, by a law taken from equity data.

**Square-root cost (p. 10).**

```latex
C^{\%,sqrt}_{it}(X) = \frac{1}{L_{it}}\Big(j + \frac{k}{\sqrt{C L_{it}}}\sqrt{X}\Big), \qquad j \approx 0.04883,\ k \approx 0.30721 \quad (2)
```

Intuition: a fixed part plus a price impact that grows with the square root of trade size. Parameters come from Kyle and Obizhaeva (2016). The estimate requires 5 trade days a month, truncates the top 25% of illiquidity, carries the last value forward, and smooths over 3 months (p. 10).

**V-shaped cost (p. 14).**

```latex
C^{\%,V}(X) = (1 - e^{-cX})\, C^{\%,sqrt}(X) + e^{-cX}\, C^{\%,EHP}(X), \qquad c = 7 \quad (3)
```

Intuition: small trades follow the TRACE discount for size, and large trades follow the square-root impact. X is in $ million.

**Portfolios (p. 7).** Long-only, size-weighted, monthly. CRD is the lowest-rated quintile, equal across VaR, liquidity and return quintiles. VAR is the highest 5% VaR quintile. LIQ is the highest Bao-Pan-Wang illiquidity quintile. MFP blends the three. REV, R1D and REX are reversal rules.

**Limits (pp. 18–19).** (B) No trades under $100,000. (C) Also, only the largest third of rebalancing trades. (D) Also, only the largest half of holdings. (E) Also, only bonds with at least 5 trade days last month. Capacity is the AUM at which net return reaches zero (p. 21).

## Data
TRACE, FISD, CRSP and Compustat. Plain USD bonds with at least $100 million outstanding and over one year to maturity, October 2004 to December 2022, 1.58 million bond-months (pp. 5–6). Main results January 2010 to December 2022 (p. 8). A bond with no trades earns its coupon over 12 (p. 5).

## Result
**$500 million fund, V-shaped cost, January 2010 to December 2022 (Table 9, p. 20).**

| Limit | MKT net Sharpe | CRD net Sharpe, turnover | VAR net Sharpe, turnover | LIQ net Sharpe, turnover | MFP net Sharpe, turnover | REV net Sharpe, turnover |
| --- | --- | --- | --- | --- | --- | --- |
| A, none | 0.73 | 1.18, 13.15% | 0.65, 9.79% | 0.49, 43.44% | 0.74, 20.74% | 0.28, 75.00% |
| B | 0.75 | 1.24, 9.74% | 0.68, 8.62% | 0.53, 40.86% | 0.90, 10.12% | 0.35, 69.93% |
| C | 0.75 | 1.26, 5.95% | 0.66, 6.57% | 0.72, 22.25% | 0.89, 10.51% | 0.70, 28.28% |
| E | 0.72 | 1.24, 4.97% | 0.66, 5.49% | 0.67, 20.22% | 0.87, 8.47% | 0.69, 23.92% |

Gross Sharpe in row A: 0.76, 1.36, 0.73, 0.98, 1.01, 0.86. Net mean return of REV rises from 0.25% to 0.46% a month from row A to C (p. 20).

**Cost function (Table 4, p. 11), one-way, bp.** High yield, 3 to 7 years. MMI: $1m 22.3, $2m 30.7, $5m 47.3, $10m 66.1. EHP: 13.9, 10.3, 5.5, 1.7. For trades near $500,000, the two agree (p. 12). Long high yield bonds cost less than long IG bonds at the same size (p. 12).

**Capacity (Table 10, p. 22), V-shaped, $ billion.** CRD 219 unlimited, 576 with partial rebalancing. VAR 67, then 93. MFP 51, then 96. REV 4.6, then 9.9. MKT about 11,000. MIG about 4,500.

**Cost check (p. 13, p. 14).** MMI cost explains about 5% of the cross-section of fund return gaps, −2 bp a month per sd. EHP has the wrong sign and under 1%.

**Multi-factor (p. 15).** MFP saves little, because source portfolios do not overlap much.

## Limits
- Long-only returns over T-bills, so CRD is a credit beta with a long Sharpe. This is not an alpha test.
- Returns imputed as carry in no-trade months lower vol. With an alternative rule, the CRD net Sharpe falls to 0.9 (p. 16). About 30% of CRD bonds have no trade in a month (p. 8).
- The authors warn that cost estimates are least reliable for the lowest-rated bonds (p. 15).
- Short post-GFC sample. The sample misses 2008 in its main tables.
- The MMI parameters come from equity data (p. 10).

## Section touched
`docs/methodology.md` Section 9.3 (exit cost and days), Section 8 (`adv_cap`), `hy.backtest.round_trip_cost`, and `docs/decisions/2026-10-26-conviction-book.md` (turnover test T3, caps).

## Use for the two clocks
This section is our proposal, not the source's claim.

**What the source says.** Credit beta is cheap to hold. Partial rebalancing keeps most of a signal and cuts turnover by more than half. Cost rises with trade size for large trades.

**What our data says.** `round_trip_cost` is a flat proxy with no size term. `adv_cap` limits size by volume. The conviction book trades larger lots in fewer names, so a size term matters.

**What we decide.**
1. Add the V-shaped cost as a second cost model for the conviction book and the risk band. Use equation (2) with TRACE inputs and `c = 7` as the v0 value from the source.
2. Add rule C (the largest third of trades) as a rebalancing arm beside the one-step rule of the band.
3. Do not read CRD's net Sharpe of 1.18 as a signal result. It is the credit premium. Record the difference from `dickerson-nozawa-robotti-2025-factor-delays.md`: that paper tests long-short alpha, and this one tests long-only excess return.

Clock use: refinancing exposure is a slow, credit-like tilt. Run it as a long-only tilt inside the DTS band, and check it by Table 9's rows.

**Test.** For each conviction-book arm, report net return under the flat proxy and under the V-shaped cost at $5 million and $10 million per trade. Our choice, v0. Pass: the ranking of the arms does not change between the two cost models.
