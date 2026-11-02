# Gilje, Loutskina, Murphy (2020), "Drilling and Debt"

Journal of Finance 75, DOI 10.1111/jofi.12884. An agent read it, and we checked one printed number against the text.

## Claim
Leveraged shale firms speed up well completions before a borrowing base reset.

## Method
Well-level time to completion in the contango of 2014-15, by leverage.

## Data
3,557 wells, 69 firms, 13 high-leverage.

## Result
- Contango x top leverage -1.002 (se 0.383) (Table IV).
- Continuous leverage -1.088 (se 0.848) fails.
- Without the top 3 firms -0.612 (se 0.406) fails (Table IX).
- Lendable share of PV-10: producing 90-95%, nonproducing 65-75%, undeveloped 25-50%, unproved 0 (Fig. 3, p. 1319).

## Limits
- One episode, and no price test.
- The result leans on a few firms.

## Section touched
`docs/methodology.md` Section 4.7.1. `hy/clocks.py` `borrowing_base_collateral`.

## Use for the two clocks
**Source says:** the reset date changes behaviour. **Data says:** nothing yet. **We decide:** add the date and the collateral value to Step 3b for A3. A haircut on production growth before a reset is our extension.
