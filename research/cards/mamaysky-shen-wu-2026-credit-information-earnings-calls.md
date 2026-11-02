# Mamaysky, Shen, and Wu (2026), "Credit Information in Earnings Calls"

Journal of Banking & Finance 191, article 107798, October 2026, DOI 10.1016/j.jbankfin.2026.107798. Peer-reviewed journal article. We read arXiv 2209.11914v2, dated September 12, 2023 (84 PDF pages), with its online appendix pages. The journal text may differ. The volume comes from Crossref. Page numbers below are PDF pages. PDF page = printed page + 1 in the main text. Evidence is from CDS, not bonds.

## Claim
Credit-relevant language in earnings calls forecasts credit spread changes, and it is "not spanned by fundamental or market variables" (p. 1). The measure also forecasts spread risk and firm fundamentals (p. 1). Complexity of the firm and the call raises the forecast power. Out-of-sample portfolios earn returns above a no-predictability null (pp. 1, 38).

## Method
1. **Target.** Transform the five-year CDS spread `S` into PVLGD (p. 11, eq. 1). The authors argue that PVLGD is a cleaner scale than the spread, because PV01 falls fast as `S` rises (p. 12).

```latex
S \times PV01 = PVLGD
```

Intuition: PVLGD is the up-front cost of protection, close to a bond's discount from par, so a one-point move means the same money at any spread level.

2. **Text window (p. 14).** Find sentences with a credit word from a hand list. Keep the five sentences before and after. Stem, and count words, bigrams and trigrams.
3. **Forward selection (p. 15, eq. 3).** Pick the token with the highest absolute correlation with the current residual, regress it out, and repeat. Run it separately for IG and HY (p. 16). Drop tokens concentrated in one sector (pp. 16–17, eq. 4).
4. **Lasso map and credit score (p. 17, eqs. 5, 6).** The penalty comes from 10-fold cross-validation.

```latex
PV_{i,t} = S_{k(i)} + L_{i,t}\beta + \varepsilon_{i,t}, \qquad CS_{i,t} = PV_{i,t} - \widehat{PV}_{i,t}
```

Intuition: the text sets a fair level for the firm's credit, and the score is how far the market sits above that level.

5. **Rolling form (pp. 18–20).** 90 variants of the text model. In each window, the model with the most predictive score is selected, with no future data.
6. **Contemporaneous test (p. 24, eq. 7).** This follows Collin-Dufresne, Goldstein and Martin (2001).

```latex
\Delta PV_{i,t+\ell} = \alpha + \beta_{lev}\Delta LEV_{i,t+\ell} + \beta_{rf}\Delta R^{(f)}_{t+\ell} + \beta_{vol}\Delta IV_{i,t+\ell} + \beta_{pv} PV_{i,t} + \beta_{cs} CS_{i,t} + \beta_{fac}^{\top} X_{i,t} + \varepsilon_{i,t}
```

Intuition: if the lagged score still works when the regression sees the actual future moves in leverage, rates and volatility, then it holds something those moves do not.

7. **Pure forecast (p. 26, eq. 8).** Drop the contemporaneous terms. Then repeat with firm and time fixed effects (p. 27).
8. **Channel tests (pp. 28–33).**
   - Delayed rational response: the score forecasts next-year spread volatility, largest monthly widening and largest cumulative widening (eq. 9), and two-year changes in profit, leverage and assets.
   - Constrained information: interact the score with call length, reading grade, analyst count and analyst dispersion (eq. 10).
9. **Portfolio test (pp. 34–39).** Maximise total score subject to zero total PVLGD, name limits, and gross limits of −4 and 4. Evaluate against 100 portfolios simulated under no predictability.

## Data
- 202,788 S&P Global call transcripts, January 2009 to December 2020 (p. 13).
- 13,899 firm-quarters matched to five-year Markit CDS and controls. Monthly observations: 9,830 IG and 4,069 HY (pp. 13–14).
- Compustat data are time stamped at data date plus three months (p. 12). CRSP, OptionMetrics, I/B/E/S.
- Financials are out (p. 13). 267 observations with PVLGD above 30 are out, 1.9% of the sample (p. 23).

## Result
**Table 7, 12-month PVLGD change (p. 52).**

| Specification | CreditScore (t) | PVLGD (t) | R² | N |
| --- | --- | --- | --- | --- |
| Contemporaneous Merton terms only | | | 0.261 | 11,387 |
| Plus factors and PVLGD | | −0.223 (−10.62) | 0.368 | 9,470 |
| Plus credit score | −0.177 (−9.75) | −0.180 (−8.89) | 0.387 | 9,470 |
| Pure forecast | −0.197 (−9.35) | −0.206 (−7.94) | 0.180 | 9,470 |

**Robustness (pp. 26–27).** Six-month horizon: −0.121. Log CDS as target: −0.027. Firm and time fixed effects: −0.095 (t −5.77), about half of the base effect, so a good part of the forecast is cross-section. Rolling text model: −0.041, significant at 1%.

**Risk and fundamentals, IQR units (Table 8, p. 53).**
- Next-year spread volatility: −0.081 (t −4.98).
- Largest monthly widening: −0.141 (t −6.13).
- Largest cumulative widening: −0.280 (t −7.78).
- Two-year profit change: +0.075 (t 2.01).
- Two-year leverage change: −0.033 (t −1.79).
- Two-year log asset change: +0.006 (t 0.31).

**Complexity (Table 9, p. 54).** Interaction with analyst count: −0.026 (t −3.42). With transcript length: −0.033 (t −4.63). With reading grade: −0.007 (t −1.03). With analyst dispersion: −0.002 (t −0.27).

**Portfolios (Table 10, p. 55; p. 38).** At limits −0.3 and 0.1: 2.934% a year in IG and 4.135% in HY. 24 of 25 IG variants are significant at 5% or better. In HY, 12 of 25 are significant at 5% or better. The joint probability under the null is below 0.5% for both (p. 39).

**HY tokens (p. 16).** Higher spreads: "matur", "amend", "net.loss". Lower spreads: "growth", "share repurchas", "earn".

**Event study (p. 22).** High-score quarters, without extreme PVLGD, see PVLGD fall by about 25% over two years. High PVLGD without extreme score sees about 15%.

## Limits
- CDS, not cash bonds. Most HY issuers have no liquid CDS, so the sample is selected. The authors drop the most distressed names (p. 23).
- The main results use the full-sample text model, which holds look-ahead (p. 18). The rolling coefficient of −0.041 is about one fifth of −0.197 (p. 27).
- The portfolio test reports no deduction for trading cost in the text that we read (pp. 33–39). It allows gross leverage of four (p. 37).
- The two channels are not exclusive. The authors find support for both (p. 28). Neither test isolates a risk premium.
- The complexity proxies are indirect. The authors read analyst count as business complexity (p. 32).
- The sample starts in 2009, so it holds no default wave except 2020.
- The sign is a CDS convention: a long is a sale of protection (p. 34). Our S1 has the same sense: positive means cheap.

## Section touched
`docs/methodology.md` Section 7.2 (blocks of `x`), Section 7.3 and S1 (residual), S3 (estimate gap), Section 9.5 (post-event update), Section 3.5 and Section 4.7 (forward text inputs). Related: estimate E7 and the memo gate of Framework F9.

## Use for the two clocks
**What the source says.** A fair level built from one new information set gives a residual that forecasts spreads beyond structural inputs (p. 25). The same residual forecasts spread risk (p. 53). A fixed-maturity contract can move slowly when news concerns years beyond its life (pp. 5, 28).

**What our data says.** Section 4.7 says to keep the two shares as risk measures. No test on file shows that they forecast risk. No text feature exists on our panel.

**What we decide (our proposal, not the source's claim).**
1. **Test the claim that the clock is a risk measure.** Regress realised spread volatility, largest monthly widening and largest cumulative widening over the next 12 months on each clock share, with the Table 8 controls. If no share forecasts these, the phrase "risk measure" has no support, and the 20% bucket needs a user decision.
2. **Spanning test for a clock feature.** Use equation (7) and equation (8) with the clock feature in place of `CS`. The feature counts as an explanation of the residual only if it passes three steps on an expanding sample. The steps are the contemporaneous Merton terms, then the pure forecast, then firm and time fixed effects.
3. **Clock exposure by bond maturity (new feature).** The horizon argument implies that only obligations inside a bond's life enter its spread. Define `clock_overlap = max(0, T_bond - revenue_runoff) / T_bond`. Then test within one issuer on one date, with issuer-by-date fixed effects. These effects remove every issuer-level control at once. The size and quality confound that Section 4.7 names is one of them. The prediction is a positive slope of log spread on `clock_overlap`. The liquidity component also rises with maturity (`dick-nielsen-feldhutter-lando-2012-corporate-bond-liquidity.md`, Table 4). So the test needs a maturity function and a liquidity control beside the issuer-by-date effects.
4. **Text fill for "re-marketability".** `two-clocks-origin.md` lists re-marketability as a missing input. Use the window method around a word list for renewal, backlog, lease expiry and take-or-pay. Fit the lasso on log spread, and keep the fit rolling. The paper tested no such words, so this is untested.
5. **Delay check.** Use `available_at` as the call or filing date, and apply the rolling form only. The drop from −0.197 to −0.041 shows how much look-ahead can flatter a text score.
