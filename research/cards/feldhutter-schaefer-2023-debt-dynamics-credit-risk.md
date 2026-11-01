# Feldhütter and Schaefer (2023), "Debt Dynamics and Credit Risk"

Journal of Financial Economics 149(3), pp. 497–535, DOI 10.1016/j.jfineco.2023.06.007. Peer-reviewed journal article, open access under a CC BY license. **Added by citation chasing** from Huang, Nozawa, and Shi (2025, p. 107), who name this paper as the reply to Bai, Goldstein, and Yang (2020). We read the published version in LBS Research Online, at https://lbsresearch.london.edu/id/eprint/2950/1/1-s2.0-S0304405X23001216-main.pdf (40 PDF pages). PDF page 1 is a repository cover sheet. Page numbers below are PDF pages. PDF page = printed page − 495. US evidence, and the main gain is in IG.

## Claim
Debt issuance has a large random part that is imperfectly correlated with shocks to asset value (p. 2). So leverage volatility exceeds asset volatility at short horizons, and the reverse holds at long horizons (p. 2). A structural model with this feature predicts spreads more accurately in the cross-section and over time (p. 2). The gain comes mainly from short-maturity IG bonds (p. 28).

## Method
1. **Default rule (p. 9, eqs. 5, 6).** The firm defaults when asset value first hits a fixed fraction of face debt.

```latex
\tau = \inf\{t \mid V_t \le d \times K_t\} = \inf\{t \mid l_t \ge -\log(d)\}, \qquad l_t = k_t - v_t
```

Intuition: default depends on the path of leverage, so the debt path matters as much as the asset path.

2. **Four debt paths (pp. 10–11, eqs. 7 to 10).** Constant debt (BC-0G), constant growth (BC), adjustment to a target (CDG), and adjustment with shocks (SD). FL versions set a firm-specific target (p. 16).

```latex
dk_t = \lambda(\nu - l_t)\,dt + \sigma_k\,dW_{k,t}, \qquad corr(W_k, W) = \rho
```

Intuition: firms pull leverage toward a target, but debt also takes its own random shocks, so leverage can move when asset value does not.

3. **Debt parameters (pp. 12–13).** Match model debt growth to historical debt growth by initial leverage group and by equity return group.
4. **Default boundary (p. 17, eq. 16).** Choose one `d` per model. It minimizes the sum of absolute differences between model and historical annual default rates. The grid covers ratings AAA to B and horizons of 1 to 20 years.
   - The authors exclude rating C when they estimate the default boundary. They state that Bai et al. (2020) find biased leverage estimates for C-rated firms when book debt proxies market debt (p. 17). The Spec row of Table 6 still includes bonds rated C (p. 14).
   - They use US industrial default rates, and they report that these differ from Moody's global rates (p. 17).
5. **Spread (pp. 17–18, eq. 17).** Recovery is 33.48%, and the asset Sharpe ratio is 0.22 (pp. 17–18).

```latex
s = -\frac{1}{T}\log\big(1 - (1-R)\,\pi^{Q}(T)\big)
```

Intuition: the spread is the annual cost of the expected loss under risk-neutral default odds.

6. **Tests.** Mean spreads (Table 6), monthly absolute errors (Table 7), volatility of monthly changes (Table 8). Robustness uses Treasury rates (Table A5), CDS (Table A6), and market values of debt (Table A7).

## Data
- CRSP and Compustat, US industrial firms, 1988 to 2017 (pp. 4, 28).
- Yield spreads to the swap rate, April 1988 to March 2018. Lehman actual quotes to December 1996, Merrill Lynch quotes to June 2002, TRACE after that (p. 29). Quotes under three years to maturity are dropped, so short bonds start in 2002 (pp. 14, 29).
- Non-callable, fixed-rate, senior unsecured bonds (pp. 16, 29). Note 13 gives 119,765 bond-months (p. 16). Section 6.6 gives 101,059 in the main sample (p. 27). The text does not reconcile the two.
- Market values of debt from Bretscher et al. (2021), 66,438 bond-months (p. 27).

## Result
**Debt parameters (Fig. 1 note, p. 4).** SD: `lambda` 0.1814, `nu` −1.0046, `sigma_k` 0.2706, `rho` −0.1868. In SD, leverage volatility is 1.6409 times asset volatility (p. 17).

**Predictable part (p. 3, note 3).** Firm and market controls lower 1-year leverage volatility only from 40.2% to 39.0%. At 20 years, they lower it from 93.4% to 69.8%.

**Default boundary (Table 5, p. 13).** BC-0G 0.8614, BC 0.7315, CDG 0.9978, CDG-FL 0.9103, SD 0.7322, SD-FL 0.6707. Davydenko's estimate of 66% is close to the SD values (p. 17).

**Mean spreads, speculative grade, bp (Table 6, p. 14).** The 95% band is in parentheses.

| Model | All | 0–3y | 3–10y | 10–20y |
| --- | --- | --- | --- | --- |
| Actual | 413 | 409 | 387 | 470 |
| BC-0G | 392 (223 to 578) | 447 (162 to 873) | 401 (250 to 518) | 308 (240 to 354) |
| SD | 349 (210 to 466) | 423 (208 to 635) | 353 (227 to 448) | 251 (177 to 302) |
| SD-FL | 400 (249 to 518) | 408 (209 to 594) | 428 (277 to 536) | 334 (239 to 392) |

All models underpredict long-term speculative grade spreads (p. 18). Each 10–20y model value above carries the table's strongest significance mark (p. 14).

**Monthly absolute error, bp, all maturities (Table 7, p. 18).**

| Group | BC-0G | BC | CDG | CDG-FL | SD | SD-FL |
| --- | --- | --- | --- | --- | --- | --- |
| Investment grade | 44 | 55 | 75 | 62 | 45 | 39 |
| Speculative grade | 194 | 181 | 285 | 218 | 185 | 179 |

These are errors on monthly averages by rating and maturity, not on single bonds.

**Volatility of monthly changes, speculative grade, bp (Table 8, p. 20).** Data 51, BC-0G 53, SD 41, SD-FL 41.

**Market values of debt (Table A7, p. 37; p. 27).** With C-rated firms included, speculative grade errors are BC-0G 190, SD 171, SD-FL 154. The authors say that the results are similar to the main sample.

**Debt and equity returns (pp. 3, 24).** Over the conditioning window, firms with low equity returns take on more debt. In later years, firms with high returns end up with more debt.

## Limits
- The model gain is mainly in short-maturity IG (p. 28). In speculative grade, SD lowers the mean monthly error only from 194 bp to 185 bp (Table 7, p. 18).
- Debt parameters are common across firms, except for the FL target (p. 16). Debt shocks have no link to any scheduled event in the model.
- The authors do not model bank and bond debt separately (p. 17). They note that firms raise bank debt in distress.
- The bond Sharpe ratio is set equal to the asset Sharpe ratio by assumption (p. 22). The authors leave this for future work.
- The stochastic volatility and jump test uses one firm, Walmart (pp. 5, 28).
- The sample excludes callable bonds (p. 29), so much of US HY sits outside it.
- The authors say that Bai et al. (2020) reject the joint assumption of geometric Brownian motion and constant debt, and that those authors change firm value dynamics, while this paper changes debt dynamics (p. 5). We did not open Bai et al. (2020), so this is one side of the dispute.

## Section touched
`docs/methodology.md` Section 4.7 (cost clock and the phrase "risk measure"), Section 7.1 (PD calibration), Section 7.2 and Section 7.3 (residual), Section 9 (risk). `hy/clocks.py`. Related cards: `feldhutter-schaefer-2018-credit-spread-puzzle.md`, `huang-nozawa-shi-2025-global-credit-spread-puzzle.md`.

## Use for the two clocks
**What the source says.** Leverage has a debt shock that is separate from the asset shock. A model that ignores it gives spreads too high a sensitivity to leverage (p. 4). The boundary estimate depends on the debt path. Standard controls predict almost none of the 1-year leverage change (p. 3, note 3).

**What our data says.** `hy/clocks.py` holds the scheduled path of debt principal, interest, rent and purchases. Section 4.7 calls the shares risk measures, and no test on file supports this phrase. No structural residual exists on our data. Section 7.1 calibrates to one number.

**What we decide (our proposal, not the source's claim).**
1. **Test if the cost clock predicts leverage risk (new test).** The source treats debt shocks as random, but part of a maturity schedule is known in advance. Regress the 1-year change in log leverage on the controls of note 3 (p. 3), then add the cost clock features. Report the fall in residual volatility on our panel.
   - Pass rule (our choice, v0): the clock lowers the 1-year residual volatility by at least one percentage point beyond the controls.
   - A pass gives the phrase "risk measure" its first support. A fail removes that support from the leverage path.
   - This test sets no signal, so it does not duplicate E8 or F21.
2. **Fix the debt path before any boundary test.** Debt dynamics alone move `d` from 0.8614 to 0.6707 (Table 5, p. 13). So run the test `d = d0 + d1 c` of the 2018 card under both BC-0G and SD, and report `d1` under each.
3. **Use the drop of rating C.** Fit the Section 7.1 grid on AAA to B, unless market values of debt are in hand (pp. 17, 27). This narrows the seven-rating grid in the 2018 card.
4. **Do not use a structural level as an anchor for one HY bond.** The monthly error on averages is 179 bp to 285 bp in speculative grade (Table 7, p. 18). A single bond has a larger error. So a structural residual enters only as a rank inside a rating and maturity bucket.
5. **Long bonds hold the level gap.** Speculative grade spreads at 10 to 20 years sit above every model, while the 3 to 10 year bucket does not (Table 6, p. 14). `clock_overlap` rises with maturity, and so does the liquidity component (`dick-nielsen-feldhutter-lando-2012-corporate-bond-liquidity.md`). So the `clock_overlap` test needs the maturity function and the liquidity control. Otherwise it reads this gap as a clock effect.
