# Benmelech and Bergman (2011), "Bankruptcy and the Collateral Channel"

Journal of Finance 66, DOI 10.1111/j.1540-6261.2010.01636.x. An agent read it, and we checked one printed number against the text.

## Claim
Peer bankruptcies widen spreads on tranches that share an aircraft type.

## Method
Seat-weighted failed operators of the pool's types, `log(1 + Bankrupt Buyers)` (eq. 2, p. 355). Tranche and year effects. Clusters by tranche.

## Data
18,327 insurer trades, 127 tranches, 12 airlines, 1994 to 2007. Spread level.

## Result
- Bankrupt Buyers 64.666 (se 27.984) (Table VI, p. 356).
- Senior 41.566, junior 429.922 (Table IX).
- 120-240 days after exit: -72.041 (se 14.136) (Table VII). The effect is temporary.

## Limits
- The paper gives no log base and prints effects on mixed scales. The first buyer is 19.5 bp in base 10 and 44.8 bp in natural log.
- No returns. No speculative grade split. Junior evidence is 20 tranches.
- Most variation comes after 9/11.

## Section touched
`docs/methodology.md` Section 4.7.1. `hy/clocks.py` `peer_shock`.

## Use for the two clocks
**Source says:** a peer filing lowers collateral value for like assets. **Data says:** nothing yet. **We decide:** fit our own slope, run M1.18, and do not infer contagion to unsecured bonds.
