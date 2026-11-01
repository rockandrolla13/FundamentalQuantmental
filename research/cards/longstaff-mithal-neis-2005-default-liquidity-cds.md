# Longstaff, Mithal, and Neis (2005), "Corporate Yield Spreads: Default Risk or Liquidity? New Evidence from the Credit Default Swap Market"

The Journal of Finance 60(5), pp. 2213–2253, DOI 10.1111/j.1540-6261.2005.00797.x. Peer-reviewed journal article. **Added by citation chasing** from Dick-Nielsen, Feldhütter, and Lando (2012, pp. 8–10). The review screen dropped it by the cap at grade 3 (`/home/ak/Gitrepos/sr-tracks/clocks-residual-timing/screening/dropped_by_cap.md`). We read NBER Working Paper 10418, April 2004 (51 PDF pages), at https://www.nber.org/system/files/working_papers/w10418/w10418.pdf. The journal text may differ. Page numbers below are PDF pages of that copy. PDF page = printed page + 2. **The sample is mostly investment grade, and it holds three BB firms.**

## Claim
CDS premia give direct measures of the default and nondefault parts of the spread (p. 2). Default is the majority of the spread at every rating and for every riskless curve (pp. 2, 18). The nondefault part links to bond illiquidity in the cross-section and to market liquidity over time (p. 2). It reverts fast (pp. 26, 28).

## Method
1. **Reduced-form model (pp. 9–11, eqs. 2 to 4, 7).** A default intensity `lambda` follows a square-root process. A nondefault process `gamma` follows a Gaussian process. The bond discounts at `r + lambda + gamma`. The CDS discounts at `r + lambda`.

```latex
CB = E\Big[c\int_0^T e^{-\int_0^t (r_s+\lambda_s+\gamma_s)ds}dt\Big] + E\Big[e^{-\int_0^T (r_t+\lambda_t+\gamma_t)dt}\Big] + E\Big[(1-w)\int_0^T \lambda_t e^{-\int_0^t (r_s+\lambda_s+\gamma_s)ds}dt\Big]
```

```latex
s = \frac{E\big[w\int_0^T \lambda_t e^{-\int_0^t (r_s+\lambda_s)ds}dt\big]}{E\big[\int_0^T e^{-\int_0^t (r_s+\lambda_s)ds}dt\big]}
```

Intuition: default risk enters both prices and the extra discount `gamma` enters only the bond, so the pair of prices separates the two.

2. **Why the CDS has no `gamma` (p. 10).** The authors give seven reasons. For example, CDS is a contract in no fixed supply, and it is as easy to sell protection as to buy it. This is an assumption of the method.
3. **Estimation (pp. 4, 12, 17).** Fit `lambda` and `gamma` per firm to the 5-year CDS and to a bracketing set of bonds with maturities around five years.
4. **Model-independent check (pp. 4, 17–19).** Take the CDS premium over the total spread. The authors show a bias of −1.7 bp to 6.6 bp against the model, on the Treasury curve (p. 19).
5. **Three riskless curves (pp. 17–19).** Treasury, Refcorp, and swap.
6. **Nondefault regressions.**
   - Cross-section per bond, on coupon, bid-ask, principal, age, maturity, a financial dummy, and an AAA and AA dummy (Table 5, p. 44).
   - Weekly change of the mean nondefault part, on its lag, money market fund flows, debt issuance, and the on-the-run spread (Table 6, p. 45).

## Data
- Citigroup desk quotes for 5-year CDS, with quotes from a variety of dealers (pp. 13, 17).
- 68 firms, March 2001 to October 2002 (p. 17). Each firm has a bracketing set of 2 to 18 bonds (p. 17).
- Rating is the rating on the last date of the firm's sample (p. 18, note 15).
- Table 4 lists 1 AAA, 6 AA, 26 A, 32 BBB, and 3 BB firms (pp. 42–43). The BB firms are Capital One, Georgia Pacific, and Goodyear.

## Result
**Default share of the spread, by model (Table 4, p. 43).** Default and spread in bp use the Treasury curve.

| Rating | Default (bp) | Spread (bp) | Treasury | Refcorp | Swap |
| --- | --- | --- | --- | --- | --- |
| AAA and AA | 53.3 | 103.6 | 0.51 | 0.62 | 1.16 |
| A | 84.0 | 150.8 | 0.56 | 0.63 | 0.89 |
| BBB | 163.0 | 229.3 | 0.71 | 0.77 | 0.94 |
| BB | 356.0 | 427.8 | 0.83 | 0.86 | 0.95 |

On the swap curve, the share rises above 100% for AAA and AA. The authors say that the swap curve probably holds a credit part (PDF pp. 18–19).

**Model-independent share, Treasury curve (Table 2, p. 39; p. 18).** 49%, 53%, 68%, and 84%.

**Time-series fit (p. 19, not tabulated).** The R² of a firm's spread on its default part is 0.37, 0.43, 0.57, and 0.62 by rating. The mean is about 0.51.

**Nondefault size (p. 21).** The firm average runs from 18.8 bp to 104.5 bp, with a mean of 65.0 bp, on the Treasury curve. It runs from −8.1 bp to 89.8 bp, with a mean of 47.7 bp, on the Refcorp curve. It runs from −57.8 bp to 50.5 bp, with a mean of 8.6 bp, on the swap curve. By rating on the Treasury curve, default runs from 53.3 bp to 356.0 bp, while nondefault runs from 50.3 bp to 71.8 bp. The authors call the nondefault part "nearly constant across rating categories".

**Cross-section regression, Treasury column (Table 5, p. 44).** R² 0.234, N = 356.

| Variable | Coefficient | t |
| --- | --- | --- |
| Coupon | 5.441 | 3.35 |
| Bid-ask spread | 0.369 | 1.96 |
| Principal amount | −0.622 | −3.16 |
| Age | −0.336 | −0.47 |
| Maturity | 2.947 | 3.25 |
| Financial | 12.399 | 2.40 |
| AAA and AA | −13.242 | −2.17 |

**Time-series regression, Treasury column (Table 6, p. 45).** R² 0.240, N = 71.
- Lagged change: −0.478 (t −4.01).
- Money market fund flow: 0.295 (t 2.33).
- Debt issuance: 0.116 (t 1.35).
- On-the-run spread: 0.519 (t 0.24). The t-statistic is 2.15 in the Refcorp column and 1.76 in the swap column.

**Speed (p. 26).** The authors say that shocks to the nondefault part "tend to dissipate within a few weeks or months".

## Limits
- Three BB firms and no firm below BB in Table 4. The evidence for HY is thin, and the sample is 20 months that include a stress period.
- We read the working paper, not the journal text.
- The default part depends on the assumption that CDS holds no liquidity effect (p. 10). Dick-Nielsen et al. (2012, p. 9) cite evidence of liquidity components in CDS.
- The model assumes that `gamma` is independent of `lambda` (p. 29). So it has no interaction of default and liquidity. The paper of Huang, Nozawa, and Shi (2025, p. 105) gives that interaction a large role.
- The nondefault part is a remainder. The authors test taxes and liquidity against it (p. 28), but it may hold other effects.
- Disagreement on size: Chen, Cui, He, and Milbradt report 64% for Ba against 83% here, by another card in this repo (`chen-cui-he-milbradt-2017-liquidity-default-cycle.md`). We did not open that paper for this theme.
- Disagreement on HY: Dick-Nielsen et al. (2012, pp. 9–10, note 9) report that the basis is smaller and often negative in speculative grade. They conclude that factors other than bond liquidity explain the basis there.

## Section touched
`docs/methodology.md` Section 3.1 (`cds_5y`) and the "Known gaps" row "No bond-CDS basis", Section 7.2 (liquidity block), Section 7.3 (residual), Section 7.5 (one AR(1) speed), Section 4.7 (clock test).

## Use for the two clocks
**What the source says.** A CDS holds far less of the bond's liquidity effect, by assumption and by the arguments of p. 10. The nondefault part reverts in weeks or months, and it links to bid-ask and principal in the cross-section. Age has no effect here.

**What our data says.** `cds_5y` is a listed field in Section 3.1, and the methodology plans "a basis feature". No test on it exists. The Section 7.2 block holds `bid_ask_bp`, `log amount_outstanding`, `trace_count`, and bond age. Section 7.5 fits one AR(1) speed for the residual. The Section 4.7 coefficients of +0.36 and −2.07 use log bond spread and no controls.

**What we decide (our proposal, not the source's claim).**
1. **Re-run the Section 4.7 sign on CDS.** Run `renewal_split_test` with log `cds_5y` as the outcome, on issuers with both CDS and material RPO. If the −2.07 stays, then the sign failure is not a bond liquidity effect. If it vanishes, then the sign sits in the bond-only part. Report the issuer count, because few HY issuers may have a CDS. This uses no new theory and needs one field.
2. **Split the clock's load.** Regress `cds_5y` and the basis `spread - cds_5y` on each clock feature. A load on the CDS part marks a credit fact. A load on the basis marks a bond-only effect. Use the model-free ratio first. The authors find a small bias against the model at BB (−1.7 bp, p. 19).
3. **Two speeds for Section 7.5.** Fit the AR(1) on the CDS-anchored part of S1 and on the basis part. Prediction from the source: the basis part has the shorter half-life. A slow part in S1 is not friction, and it needs the fact-or-risk tests of the Mamaysky card.
4. **Keep the basis out of the liquidity measure in HY.** The basis may be negative in speculative grade. So report it as its own column. Use the lambda-type measure of `dick-nielsen-feldhutter-lando-2012-corporate-bond-liquidity.md` as the HY liquidity control.
5. **Do not import the shares.** The 83% rests on three BB firms in 2001 and 2002. Use it only as an order of size.
