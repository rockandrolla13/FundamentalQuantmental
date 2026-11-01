# Cederburg, O'Doherty, Wang and Yan (2020), "On the performance of volatility-managed portfolios"

Journal of Financial Economics 138, pp. 95–117, DOI 10.1016/j.jfineco.2020.04.015. Peer-reviewed. **Evidence from equities.** **Added by citation chasing** as the direct test of Moreira and Muir (2017). We read the journal article from an author's page (`lehigh.edu/~xuy219/research/COWY.pdf`, 23 pages). Page numbers are PDF pages. Printed page = PDF page + 94.

## Claim
Volatility-managed portfolios do not outperform the original portfolios in direct comparisons (p. 1). Positive spanning alphas exist, but the strategy they imply needs weights known only after the sample (pp. 1, 3). Out-of-sample versions earn lower certainty-equivalent returns and Sharpe ratios than the original portfolios, mainly because the spanning regressions are unstable (p. 1).

## Method
**Scaled portfolio (p. 2).**

```latex
f_{\sigma,t} = \frac{c^{*}}{\hat{\sigma}^2_{t-1}} f_t \quad (1), \qquad f_{\sigma,t} = \alpha + \beta f_t + \epsilon_t \quad (2)
```

Intuition: α in equation (2) is earned by a mix of the scaled and the original portfolio, so an investor needs the mix weights in real time.

Tests:
1. Direct Sharpe comparison of scaled and unscaled portfolios, over 103 strategies (p. 2).
2. Spanning regressions (p. 2).
3. Real-time combination with weights from past data. The authors vary the window, risk aversion and leverage limit (p. 3).
4. A check on the stability of spanning parameters (pp. 2–3).

## Data
Nine factors from Moreira and Muir (2017) and 94 anomaly portfolios from Hou et al. (2015) and McLean and Pontiff (2016): 103 equity strategies (p. 2).

## Result
- Direct comparison: scaled beats original in 53 of 103 strategies. Original beats scaled in 50 (p. 2). Eight strategies have a significant Sharpe gain, mainly momentum types (p. 2).
- Five of the nine Moreira and Muir factors have a higher Sharpe when scaled (p. 2).
- Spanning: 77 of 103 alphas are positive, with 23 significantly positive and 3 significantly negative (p. 2). With market, size and value controls: 70 positive (p. 2).
- Real time: the combination earns a lower certainty equivalent than the original in 72 of 103 cases (p. 3).
- Some factors gain out of sample: momentum, profitability and betting against beta (p. 3).

## Limits
- Equities only. No credit factor.
- The real-time rule combines a scaled and an original portfolio. A band rule with a cap is a different design.
- Costs are not the focus. Performance is already weak before cost.

## Section touched
`docs/methodology.md` Section 9.4 (position scale), and `docs/decisions/2026-10-26-conviction-book.md` layer 1 and the static-band arm.

## Use for the two clocks
This section is our proposal, not the source's claim.

**What the source says.** A positive spanning alpha does not mean that a real-time investor gains.

**What our data says.** No test on our panel. The conviction-book page keeps a static-band arm, because Grube et al. show that bands cost little and did not beat the static book. This source supports the same design choice.

**What we decide.**
1. Judge any scaling rule for book risk by direct, net, real-time comparison with the static band. A spanning alpha does not count.
2. Fit no combination weights in-sample.
3. Record the disagreement with `moreira-muir-2017-volatility-managed.md`. Moreira and Muir are right on the sign of the in-sample alpha. Cederburg et al. are right on what a real-time investor gets. Our decision follows Cederburg et al., because the book must trade in real time and bond costs are higher.

**Test.** The same arm as in `moreira-muir-2017-volatility-managed.md`. Report the spanning alpha only as a note.
