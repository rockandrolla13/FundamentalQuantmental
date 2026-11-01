# Chen, Xu and Yang (2021), "Systematic Risk, Debt Maturity, and the Term Structure of Credit Spreads"

Journal of Financial Economics, DOI 10.1016/j.jfineco.2020.09.002 (per the track's screening record). Peer-reviewed. Corporate debt and CDS. **Added by citation chasing** from Nagler (2015 version, p. 8), Boyarchenko and Elias, and the review's dropped list. **We did not open the journal article.** We read NBER Working Paper 18367, September 2012, 62 pages. Page numbers are PDF pages. The journal numbers may differ.

## Claim
Firms with high systematic risk choose longer debt maturity and keep a more stable maturity over the cycle (pp. 2, 5–6). Debt maturity is pro-cyclical. A fall in maturity amplifies credit spread moves, most for firms with high beta, high leverage or lumpy maturity (p. 2). So a study of rollover risk must control for systematic risk, not just compare maturity (p. 5).

## Method
A dynamic capital structure model with two aggregate states, expansion and recession. Firms trade off rollover risk against the illiquidity cost of long bonds (pp. 3, 8). Default occurs when equity holders stop service, mainly when debt rolls at high yields (p. 3).

**Measures (pp. 31–32).** Long-term debt share: `ldebt3y`, the share of debt due in more than 3 years. Asset beta from Merton unlevering, cash flow beta on 20-year windows, and a durable-goods class.

**Spread test (pp. 39–42).** Cross-section of CDS spread changes from fiscal 2007 to 2008 on the share of long-term debt due in 2008.

```latex
\Delta CDS^{\tau}_{i} = a + b\, ldebt08_i + c' X_i + e_i, \qquad ldebt08_i = \frac{dd1_i}{dd1_i + dltt_i}, \quad \tau \in \{1,5,10\}\ \text{years}
```

Intuition: a firm with a large block due in the crisis must refinance at the worst moment, whatever maturity it wanted. Controls: market leverage, asset volatility, size, market-to-book, profitability, tangibility, past equity return, rating, one-digit industry (p. 40).

**Endogeneity check (p. 42).** Rebuild the same 2008 due share from filings of fiscal 2004, 2005 and 2006 (`dd4`, `dd3`, `dd2`).

## Data
Compustat and CRSP, 1974 to 2010, without financials, utilities and quasi-public firms (p. 30). Markit CDS for 375 firms with data in both fiscal 2007 and 2008, 87% of them with the right fiscal year end (p. 40). Table 6 regressions have 261 to 272 firms (p. 53).

## Result
**Maturity choice (p. 6).** One sd of asset beta raises the long-term debt share by 6.5%, after controls for total asset volatility and leverage. The share is 3.7% lower in recessions at the 10th percentile of asset beta. It is almost unchanged at the 90th.

**Spreads (p. 41).** One sd of `ldebt08` adds 50, 40 and 32 bp to the 1, 5 and 10-year CDS changes.

| Group | 1-year | 5-year | 10-year |
| --- | --- | --- | --- |
| High book leverage (p. 41) | 84 bp | 77 bp | 55 bp |
| Low book leverage (p. 41) | 31 bp | 22 bp | 21 bp |
| High cash flow beta (p. 42) | 70 bp | 63 bp | 46 bp |
| Low cash flow beta (p. 42) | negligible | negligible | negligible |

**Table 6, p. 53.** Coefficient on `ldebt08`, all firms: 0.045 (t 2.71), 0.036 (t 2.67), 0.029 (t 2.57). High market leverage 1-year: 0.109 (t 2.17). Low market leverage 1-year: 0.012 (t 1.38).

**Endogeneity check (p. 42).** Almost identical with fiscal 2006 filings, slightly weaker with 2005, and not significant with 2004.

**Model (p. 5).** For a low-leverage firm, a cut in maturity from 5.5 to 5 years in recession barely moves spreads. A cut to 1 year raises spreads by up to 100 bp. For a high-leverage firm the effect is larger and sits at the short end of the curve.

## Limits
- CDS sample, so large names. One crisis.
- `ldebt08` covers scheduled long-term debt only. Loans due and revolvers are not separated.
- The fiscal 2004 check loses significance, so part of the effect may be firm quality (p. 42).
- Callable debt does not enter effective maturity. A logit shows that callable issuance does not relate to the risk measures (p. 39).
- We read the 2012 version. The journal version may change the numbers.

## Section touched
`docs/methodology.md` Section 4.7 (test of the split, selection), Section 7.2 (controls for clock features), Section 9.2 (spread channel), Section 9.4 (wall limit).

## Use for the two clocks
This section is our proposal, not the source's claim.

**What the source says.** Long debt goes with high asset beta, after controls (pp. 5-6). So long debt and high spreads can move together with no rollover effect.

**What our data says.** The refinance share on file is debt due after year 2, over all obligations, because the backtest fixes RPO at 2 years for every issuer (`hy/sources/clock_facts.py` lines 15–17, `docs/decisions/2026-10-22-alpha-backtest-design.md`). It has a coefficient of +0.36 (t 2.0) with no control (`renewal_split_test`). The three shares (due within 2 years, debt after 2 years, rent and purchases after 2 years) add to one. So the −2.07 on rent and purchases may read in part as less debt in the mix. These are our readings, and no test has run on them.

**What we decide.**
1. Stop reading the Section 4.7 result as a test of contract run-off. It measures long debt share and long rent share. A true revenue clock needs the XBRL timing dimensions.
2. Add a systematic-risk control to every clock regression: asset beta or the DTS beta to the high yield index, plus market leverage.
3. Report the term structure of the response: 1 to 3, 3 to 7 and over 7 years, by leverage cell.
4. Adopt the stale filing check. Rebuild due amounts from filings 1, 2 and 3 years before a shock, and show how the coefficient decays.

**Test.** Re-run the split with leverage and beta controls and with a real run-off for the issuers that have RPO timing. Pass for "selection": the +0.36 falls within one se of zero once the controls enter. Fail: it stays positive with t above 2. Our choice, v0. Do this on the production machine, not in this sprint.
