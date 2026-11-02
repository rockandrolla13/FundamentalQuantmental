# He and Xiong (2012), "Rollover Risk and Credit Risk"

Journal of Finance 67(2), pp. 391–429, April 2012, DOI 10.1111/j.1540-6261.2012.01721.x. Peer-reviewed. Theory with a calibration. We read the journal article from the author's page (`wxiong.mycpanel.princeton.edu/papers/rollover.pdf`, 39 pages). Page numbers are PDF pages of that file. Printed page = PDF page + 390. We also read NBER Working Paper 15653 (January 2010, 50 pages), which has a two-class debt model. The lineage card `two-clocks-origin.md` opened only the abstract page of the working paper.

## Claim
A fall in bond market liquidity raises the liquidity premium and the default premium together (p. 1). The default effect comes from debt rollover. Equity holders bear the loss when new bonds sell below par, and maturing holders get full par. So the firm defaults at a higher fundamental threshold (pp. 5–6, Proposition 2 on p. 14). Shorter firm-wide debt maturity amplifies this effect (Proposition 3, p. 17).

## Method
Leland and Toft (1996) with an illiquid secondary market. The firm keeps a stationary debt structure with maturities spread evenly over time (p. 5). A fraction 1/m of the debt rolls each year at the market price.

```latex
NC_t = \delta V_t - (1-\pi)C + d(V_t, m) - p \quad (4,\ \text{p. 5})
```

Intuition: equity holders take every rollover gain or loss, so their net cash falls when new bonds sell below par.

Bond holders meet a liquidity shock with intensity ξ and sell at a proportional cost k. The liquidity premium is ξk (p. 11, p. 14). The default premium is the spread less ξk (p. 14).

```latex
\beta_\xi \equiv \frac{d\,d(V_t,\xi;V_B(\xi))}{d\xi} = \frac{\partial d}{\partial \xi} + \frac{\partial d}{\partial V_B}\frac{dV_B}{d\xi} \quad (\text{p. 25})
```

Intuition: a liquidity shock lowers a bond price twice, once through the discount rate and once through the higher default boundary.

Calibration (Table I, p. 13, and pp. 14, 18): r 8%, tax benefit π 27%, recovery α 60%, payout δ 2%, ξ 1. BB firm: σ 23%, k 1.0%, spread at issue 330 bp. A firm: σ 21%, k 0.5%, spread at issue 100 bp. Maturity m is 1, 3, 6 or 10 years.

## Data
None of its own. Parameters come from other studies (pp. 12–14). The BB spread target of 331 bp comes from Rossi (2009) on TRACE (p. 14).

## Result
**Shock response by maturity (Table II, p. 19).** Each row holds the spread at issue fixed at the rating target.

| Rating, m | ξ 1 to 2: spread change, default part, share | ξ 1 to 4: spread change, default part, share |
| --- | --- | --- |
| BB, 1 year | 169.6 bp, 69.6 bp, 41.0% | 523.0 bp, 223.0 bp, 42.6% |
| BB, 3 years | 144.6 bp, 44.6 bp, 30.8% | 422.1 bp, 122.1 bp, 28.9% |
| BB, 6 years | 128.9 bp, 28.9 bp, 22.4% | 369.8 bp, 69.8 bp, 18.9% |
| BB, 10 years | 120.3 bp, 20.3 bp, 16.9% | 341.9 bp, 41.9 bp, 12.3% |
| A, 1 year | 61.7 bp, 11.7 bp, 18.8% | 190.7 bp, 40.7 bp, 21.3% |
| A, 6 years | 56.4 bp, 6.4 bp, 11.3% | 166.9 bp, 16.9 bp, 10.1% |

**Equal leverage, different maturity (Figure 3, p. 17).** With the same fundamental, coupon and face value, the 1-year firm moves from 330 bp to 500 bp. The 6-year firm moves from 215 bp to 334 bp. So at equal leverage, longer debt carries a lower spread level and a smaller shock response.

**Regression warning (pp. 23–24).** In `Spread = α + β CDS + δ LIQ`, the coefficient δ understates the liquidity effect, because the CDS spread also holds liquidity-driven default. The full effect is δ + βγ₀.

**Weak firms (p. 19).** BB spreads react more than A spreads to the same shock, and the default part takes a larger share. The authors link this to flight to quality.

**Two-class model (NBER version, p. 30).** With 5% of debt in the short class, a rise in short-debt rollover frequency from 4 to 250 lifts the default boundary from slightly above 74 to 95. The long-bond spread rises from 160 bp to 405 bp.

## Limits
- Stationary debt with evenly spread maturities (p. 5). The model has no maturity wall and no event time.
- The shock is permanent (p. 12). Footnote 10 reports a modest difference for a temporary shock when maturity is comparable to the shock length.
- Constant risk-free rate (p. 4, n. 1). The new bond has the same maturity, coupon and seniority as the old bond (p. 6). No cycle state.
- The authors state that the effects are stronger for financial firms (p. 4).
- A calibration, not a test.

## Section touched
`docs/methodology.md` Section 4.7 (refinance part of `O`), Section 7.2 (liquidity block and the reading of its coefficient), Section 9.1 (maturity and refinance window), Section 9.2 (spread channel). Replaces the abstract-only entry in `two-clocks-origin.md` Source 8 for this claim.

## Use for the two clocks
This section is our proposal, not the source's claim.

**What the source says.** Rollover risk rises with rollover frequency 1/m and with the gap between par and the price of new bonds. In their calibration, longer debt has a lower spread at equal leverage (p. 17). This compares two model firms, and it is not a test.

**What our data says.** Section 4.7 records a refinance coefficient of +0.36 (t 2.0) on log spread. The backtest spreads all RPO evenly over 2 years (`hy/sources/clock_facts.py`, lines 15–17). So `renewal_refinance_share` on file is debt principal due after year 2, over all obligations. A high value means long debt, so low rollover frequency.

**What we decide.**
1. Do not cite this paper as support for +0.36. The sign on file is opposite to the equal-leverage comparison on p. 17.
2. Add `rollover_rate_12m`: debt principal due in the next 12 months over total debt. Intuition: the share of the firm that meets the market this year.
3. Add `rollover_loss_h`: the sum over τ ≤ h of `M_τ (y_T + s − c_old)`, in years of EBITDA. It reuses the cash term of Section 9.2. Intuition: the cost that equity must absorb if the firm rolls at today's spread.
4. Read a liquidity coefficient in Section 7.2 as a lower bound when a default proxy sits in the same regression (pp. 23–24).

**Test.** Run the interaction panel of `nagler-2020-bond-rollover-channel.md` with `rollover_rate_12m`. Pass: the interaction is positive in at least three of the four cycle windows, and its size falls from CCC to B to BB. Our choice, v0.
