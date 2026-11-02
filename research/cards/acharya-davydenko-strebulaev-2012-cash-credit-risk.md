# Acharya, Davydenko and Strebulaev (2012), "Cash Holdings and Credit Risk"

Review of Financial Studies, DOI 10.1093/rfs/hhs106. Peer-reviewed journal article. We read NBER Working Paper 16995, April 2011, 39 pages. We did not open the journal version, so its numbers may differ. Page numbers below are PDF pages. PDF page = printed page + 2. Evidence class: corporate bonds, investment grade and high yield, with spreads and defaults.

## Claim
The correlation between cash and spreads is positive, and it is higher for lower ratings (p. 2). The precautionary motive explains this: riskier firms choose to hold more cash (p. 2). Spreads fall with the "exogenous" part of cash that is independent of credit risk factors (p. 2). The sign of cash in a default model depends on the horizon (pp. 2, 5-6).

## Method
**Model (pp. 9-16).** A firm with fixed debt `B` due at date 1 splits cash between a reserve `c` and a long-term project. A share `τ` of future cash flow can back new borrowing.

```latex
\frac{ds}{dx} = \frac{\partial s}{\partial x} + \frac{\partial s}{\partial c} \times \frac{dc}{dx} \quad (7)
```

Intuition: a firm trait changes the spread directly and also through the cash the firm chooses to hold, and a plain regression cannot tell the two apart.

Proposition 1: riskier firms hold more cash and still have higher spreads when financing constraints bind (p. 12). Proposition 2: spreads fall with cash moved by a variable that does not move spreads directly (p. 13). Proposition 3: more cash lowers default at date 1 and raises it at date 2 (p. 16).

**Spread tests (pp. 22-25).** OLS of the firm-month average spread on a liquidity ratio, with leverage, asset volatility, size, maturity, and rating and month dummies. Then instrument the liquidity ratio.

```latex
Cash_{i,t} = \pi_1 \text{IndRD}_{j,t} + \pi_2 \text{Agency}_{i,t} + \gamma X_{i,t} + u_{i,t}, \qquad s_{i,t} = \beta \widehat{Cash}_{i,t} + \delta X_{i,t} + e_{i,t}
```

Intuition: industry R&D shifts cash through growth options, and managerial pay at risk shifts cash through a private fear of distress. The authors argue that neither depends on the firm's own credit risk.

**Default tests (pp. 25-26).** Logit and instrumented logit at horizons of one quarter, one year and three years, on the Altman, Zmijewski and EDF models.

## Data
- Bonds in the Merrill Lynch US Investment Grade and High Yield Master II indices, December 1996 to December 2003 (p. 16).
- 82,676 bond spreads, 485 firms, 24,496 firm-months (p. 17).
- Firm-months by rating (Table 1, p. 33): BB 2,842, B 942, CCC and below 148. Junk firms are 16.4% of the sample (p. 17).
- Mean spreads (Table 2, p. 34): BBB 180.5 bp, BB 371.7 bp, B 583.8 bp.
- Cash over assets: mean 3.9%, median 2.0% (p. 19).

## Result
**OLS (Table 4, p. 36).** `Cash/TA` is 3.26 (t 2.64) alone. It is 3.25 (t 3.83) with controls and month dummies, and 1.25 (t 1.73) with rating dummies as well.

**Instrumented (Table 5, p. 37).** `Cash/TA` is -6.46 (t -3.11) alone, -4.42 (t -2.31) with controls, -2.64 (t -1.71) with month dummies, and -4.57 (t -2.63) with rating dummies.

**Horizon (Table 7, p. 39).** Coefficients on working capital over assets, Altman model:

| Horizon | Logit | Instrumented logit |
| --- | --- | --- |
| 1 quarter | -1.05 (z 2.62) | |
| 1 year | +2.28 (z 4.24) | +1.82 (z 0.35) |
| 3 years | +2.92 (z 3.70) | -73.09 (z 3.40) |

## Limits
- The sample ends in 2003, with one recession. High yield is a minority of the sample.
- Exclusion is argued and not proved. Industry R&D may move credit risk directly.
- Instrumented logit estimates are very large (-73.09) and they lose half of the sample.
- The source gives no first-stage statistic in the tables we read.
- The paper is on cash, not on leases or contracts. The transfer to the clocks is our proposal.
- Source inconsistency: one standard deviation of cash goes with about 20 bp on p. 4 and about 16 bp on p. 23. The coefficient 3.25 times the standard deviation 0.049 gives 16 bp (our arithmetic).
- Table 7 shows absolute z values in parentheses, so we state the coefficient sign from the coefficient.

## Section touched
`docs/methodology.md` Section 4.7 (test of the split), Section 7.2 (monotone constraints and sign priors), Section 11 (test design). `scripts/backtest_clocks.py` (`renewal_split_test`).

## Use for the two clocks
**What the source says.** A variable that looks safe can take the wrong sign when firms choose it in response to risk. The sign turns after the endogenous part is removed. The sign also depends on the horizon.

**What the data says.** Section 4.7 records the wrong sign on the recontract share (-2.07, t -2.4) in an OLS with no controls. The repo holds no instrument test. Here the direction runs the other way to cash: the share looks risky and it goes with lower spreads.

**What we decide (our proposal, not the source's claim).**
1. Treat the lease tail as a chosen variable, as this paper treats cash. Do not read its OLS coefficient as a risk price.
2. Run the same two-step test on the lease and purchase tail. Candidates for the first stage, each from a card in this set:
   - the leave-one-out mean tail in the same sector and year (Habib et al.)
   - distance to port and input transport cost, for purchases only (Moon and Phillips)
   - the interaction of a rejection right with the sector norm (Becker et al.), which is usable only in a cross-country panel
3. Report the first-stage F. Reject the test if F is below 10 (Our choice, v0).
4. Add the horizon split. Test the clock features against default at 1 quarter, 1 year and 3 years. Do not assume one sign.
5. Pass rule, fixed before any run. Selection explains the wrong sign if the instrumented lease tail has a coefficient above 0 with `lev_lease_adj` in the model.
