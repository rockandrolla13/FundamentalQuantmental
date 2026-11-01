# Dickerson, Nozawa and Robotti (2025), "Factor Investing with Delays"

Discussion Paper Series A No. 771, Institute of Economic Research, Hitotsubashi University, July 2025, DOI 10.2139/ssrn.5074221 (SSRN version). Working paper. Corporate bonds, US IG and HY. We read the Hitotsubashi file (105 pages). The author order follows the title page. Page numbers are PDF pages.

## Claim
Infrequent trade adds a cost that bid-ask spreads miss: the cost of delay (pp. 2, 5). This cost rises with a factor's gross return and with turnover (pp. 5, 19–20). After delay and half-spread, nearly no corporate bond factor beats the bond market (p. 2). Slow signals from accounting data carry a small delay cost (p. 7).

## Method
**Signal model (p. 13).**

```latex
r_{i,t+1} = \beta_{i,t} f_{t+1} + u_{i,t+1}, \qquad \beta_{i,t+1} = \rho\, \beta_{i,t} + v_{i,t+1}, \qquad \tau_{i,t} \sim \text{Exp}(\lambda)
```

Intuition: a fast signal (low ρ) needs frequent trades, and each late trade earns a stale position.

An order fails if the delay exceeds 21 days (p. 15). Partial months earn pro rata (eq. 4, p. 15). Simulation: 1,000 bonds, T = 244, 1,000 paths (p. 13).

**Costs (pp. 17–18).**

```latex
C^{Delay}(\lambda,\rho,\sigma_v) = \overline{(r_{Q5} - r_{Q1})} - \overline{(r^{Net}_{P5} - r^{Net}_{P1})} \quad (6), \qquad C^{Bid-Ask} = 2 \times TO^{P} \times h \quad (8)
```

Intuition: delay cost is the gross return lost to late trades, and it grows with the signal's own return.

**Trade intensity (pp. 23–28).** Monthly trade dummy on half spread instruments, investor composition and controls (eq. 11, p. 26). Set investor composition at the 99th percentile for an active investor (p. 27). Convert with `Prob = 1 − exp(−21 λ)` (eq. 10, p. 25). $100,000 trades: λ 0.145, mean delay 6.9 days. $2 million trades: λ 0.059, 17.1 days (p. 27). Half spread follows O'Hara and Zhou (2021) (eq. 13, p. 30).

**Assign costs (p. 31).** Interpolate the grids of Table 2 (p. 57) by factor turnover and gross return. Deduct from CAPM alpha on an ETF-based net market factor (pp. 29–30).

## Data
ICE and TRACE bond data, January 1998 to December 2022, 19,768 bonds and 2,110 firms for characteristics, with factors from August 2002 (pp. 11–12). 341 characteristics, of which 40 bond and 301 equity (p. 11). Intensity panel: 814,145 bond-months and 14,418 bonds, August 2002 to September 2021 (p. 12). 58 factors have significant gross means (p. 29). Decile long-short, value weight, monthly (p. 29). Market factor mixes LQD and HYG (p. 30).

## Result
**Table 4, p. 59, percent a month, large trades ($2 million).**

| Category | Count | Gross α | Turnover % | Half-spread cost | Delay cost | Net α |
| --- | --- | --- | --- | --- | --- | --- |
| Equity momentum | 9 | 0.287 | 142 | 0.205 | 0.107 | −0.025 |
| Equity reversal | 4 | 0.426 | 136 | 0.203 | 0.215 | 0.008 |
| Investment | 13 | 0.143 | 29 | 0.064 | 0.014 | 0.065 |
| Spreads | 14 | 0.437 | 47 | 0.093 | 0.105 | 0.239 |
| Value and profit | 7 | 0.160 | 35 | 0.074 | 0.023 | 0.062 |
| Volatility and risk | 11 | 0.241 | 84 | 0.125 | 0.063 | 0.053 |
| All | 58 | 0.277 | 70 | 0.115 | 0.075 | 0.087 |

Factors with a significant net alpha: 2 of 58 for large trades, 1 of 58 for small trades (p. 7, p. 59). With half-spread only, 10 are significant for large trades (p. 59).

**Machine learning (pp. 35–36).** Gross alpha 0.62% to 0.90%, turnover 97% to 126% a month. Delay cost 0.17% to 0.36% for large trades. Best net alpha: 0.41% (t 2.31), against 0.87% gross.

**Slower trading (pp. 37–38).** Staggered 3-month hold: delay cost falls to 0.03%, gross alpha falls to 0.20%, turnover falls from 70% to 34%, net alpha for large trades is 0.10%. Band of two deciles: net 0.08%, but 5 factors become significant for large trades. Above-median volume subsample: net −0.04% (p. 39).

**Cycle (pp. 40–42).** Trade intensity falls in stress: Kargar et al. λ of 0.115 and 0.072 in booms, 0.068 and 0.042 in the COVID episode (p. 28, n. 24). 37 of 58 factors earn more in recessions, which raises their delay cost (p. 42). Pro-cyclical factors have lower delay cost (p. 42).

**Short side (p. 33, n. 34, and Table A.13, p. 103).** Borrow fee averages about 0.03% a month. Indicative fee: BB+ to B− mean 4.36 bp, CCC+ to D mean 12.55 bp.

## Limits
- A lower bound. Supply of liquidity is taken as inelastic (pp. 24–25).
- Cost is fixed over time in the main results (p. 31), and λ is common to all bonds in the simulation (p. 14).
- IG and HY pooled, so no HY-only table.
- Long-short deciles, monthly. Long-only books have a different cost path.
- Working paper.

## Section touched
`docs/methodology.md` Section 8 (entry rule on cost), Section 11 (backtest design, `hy.backtest.round_trip_cost`), Section 9.3 (exit cost), and `docs/decisions/2026-10-26-conviction-book.md` tests T1 and T3.

## Use for the two clocks
This section is our proposal, not the source's claim.

**What the source says.** Cost depends on the signal's speed. Fast, strong signals lose the most. Slow accounting signals lose little to delay.

**What our data says.** `hy.backtest.round_trip_cost` charges a bid-ask proxy over price. It has no delay term. The clock signals come from filings, so they change slowly and sit near the Investment class (gross 0.143, delay 0.014, Table 4, p. 59). No turnover number for the clocks is on file.

**What we decide.**
1. Add a delay term to the cost of every signal test. Compute turnover by eq. 7 (p. 18). That turnover is the sum of absolute weight changes per leg, from 0 to 200%, averaged across the long and short legs (p. 18, note 14). It is not one-way turnover. Read delay cost from Table 2 Panel B3 (p. 57) by turnover and gross return, for a $2 million trade. Panel B3 fixes λ at the source's estimate, so a fitted λ needs a rerun of the simulation.
2. Fit λ by rating cell on TRACE, because HY intensity differs. Use the `Prob = 1 − exp(−21 λ)` map. `n_trades` in `bond_panel` cannot supply the dummy, because a row exists only if the bond traded. Build the dummy from `trace_trades` with a par floor and a bond-life calendar.
3. Set the cost hurdle for a timing rule as half-spread plus delay on the added turnover.
4. A filing-based clock feature has a hurdle near 0.08% a month at 29% monthly turnover (0.064 + 0.014, Table 4). This number is from the source for pooled IG and HY, and it needs a HY update.

**Test.** Report net IC and net alpha with and without the delay term for all signals in `hy/factors`. Reject a signal whose net alpha after delay has t below 2 in the pooled sample, unless it passes the cycle bar in `CLAUDE.md`. Our choice, v0.
