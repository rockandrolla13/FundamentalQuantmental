# Dick-Nielsen, Feldhütter, and Lando (2012), "Corporate Bond Liquidity Before and After the Onset of the Subprime Crisis"

Journal of Financial Economics 103(3), pp. 471–492, DOI 10.1016/j.jfineco.2011.10.009. Peer-reviewed journal article, final published version under a CC BY-NC-ND license. **Added by citation chasing** from He, Khorrami, and Song (2022, pp. 4, 22). The live CBS repository file returned HTTP 403. So we read the Internet Archive copy of that same file: https://web.archive.org/web/2023/https://research.cbs.dk/files/58847171/corporate_bon_liquidity_david_lando.pdf (23 PDF pages). Page numbers below are PDF pages. PDF page = printed page − 469. We checked the signs of Tables 3, 4, and 7 against a page image, because text extraction drops minus signs.

## Claim
"Our liquidity measure outperforms the Roll (1984) measure used in Bao, Pan, and Wang (2011) and zero-trading days" in explaining spread variation (p. 2). In speculative grade, the liquidity component rose from 57.6 bp before the subprime crisis to 196.8 bp after its onset (Table 4, p. 10). A same-firm paired design keeps the result (Table 7, p. 16).

## Method
1. **Component measures (pp. 18–19).** Quarterly, per bond.

```latex
Amihud_t = \frac{1}{N_t}\sum_{j=1}^{N_t}\frac{|r_j|}{Q_j}, \qquad IRC = \frac{P_{max} - P_{min}}{P_{max}}
```

Intuition: Amihud is the price move per million dollars traded, and IRC is the dealer markup inside a set of same-size trades on one day.

2. **The composite `lambda` (pp. 3, 5, 19).** The first principal component of eight proxies explains 39% (Table 1, p. 5). It loads evenly on four: Amihud, IRC, and the daily standard deviation of each.

```latex
\tilde L^j_{it} = (L^j_{it} - \mu_j)/\sigma_j, \qquad \lambda_{it} = \sum_{j=1}^{4} \tilde L^j_{it}
```

Intuition: price impact, cost, and the variability of each are four views of one friction, so an even sum is a steadier proxy than any single view.

3. **Regression by rating and regime (p. 4, eq. 1).** Bond controls are age, amount issued, coupon, and time to maturity. Issuer controls are equity volatility, operating income over sales, leverage, long-term debt over assets, four pretax coverage dummies, and forecast dispersion. Market controls are the swap level and slope. Errors cluster in two dimensions.

```latex
Spread^R_{it} = \alpha^R + \gamma^R L_{it} + \text{Credit risk controls}_{it} + \epsilon_{it}
```

Intuition: inside a rating class and after credit controls, the slope is the spread paid per unit of friction.

4. **Liquidity component (pp. 8, 10).** Sort inside each rating and maturity bucket.

```latex
LC = \beta^R(\lambda_{50} - \lambda_{5})
```

Intuition: this is the extra spread of a median bond over a very liquid bond of the same rating and maturity bucket.

5. **Paired regression (pp. 15–16, Table 7).** Pair bonds of one firm with similar maturity, and add a dummy for each firm, maturity, and quarter. The authors state that this removes credit risk, so the slope is free of endogeneity from omitted credit variables (p. 15).
6. **Liquidity beta (p. 16, Table 6).** Regress spreads on the bond's covariance with market-wide `lambda`.
7. **Endogeneity (p. 20).** Durbin-Wu-Hausman tests over nine measures, five rating classes, and two regimes. The authors report that 80% of the 90 statistics are not significant at 10%.

## Data
- Enhanced TRACE, 2005 Q1 to 2009 Q2, with fixed-rate bullet bonds that are not callable, convertible, or putable and have no sinking fund (pp. 3–4).
- 10,785 issues fall to 5,376 with ratings. Trades below $100,000 are dropped. 8,212,990 trades remain (p. 4). The final sample has 2,224 issues and 380 issuers (Table 2, p. 6).
- A bond in a quarter needs a full set of accounting variables and at least four trades (p. 7).
- Spreads to the swap rate at the end of each quarter (p. 4). Liquidity variables winsorized at the 99.5th percentile, and spreads at the 0.5th and 99.5th percentiles (p. 18).

## Result
**Pooled regressions, speculative grade (Table 3, p. 7).** t in parentheses.

| Measure | Pre-subprime | Post-subprime |
| --- | --- | --- |
| `lambda` | 0.1726 (5.34) | 0.6746 (6.73) |
| Amihud | 36.26 (4.14) | 84.58 (4.18) |
| Roll | −0.01 (−0.12) | −0.58 (−1.16) |
| IRC | 267.38 (4.82) | 406.25 (4.36) |

`lambda` is significant in all five rating classes in both regimes, nine of ten at 1% (p. 7). Roll has a negative sign and no significance in speculative grade.

**Liquidity component, mean bp (Table 4, p. 10).**

| Rating | Pre-subprime | Post-subprime | Post-subprime 0–2y, 2–5y, 5–30y |
| --- | --- | --- | --- |
| AAA | 0.8 | 4.9 | 2.5, 4.5, 7.9 |
| AA | 1.0 | 41.8 | 23.5, 37.1, 64.7 |
| A | 2.4 | 50.7 | 26.6, 51.0, 74.5 |
| BBB | 3.9 | 92.7 | 64.3, 115.6, 98.1 |
| Spec | 57.6 | 196.8 | 123.6, 224.0, 242.7 |

Pre-subprime Spec by maturity is 45.0, 44.0, and 83.9 bp. The premium for long bonds is about twice that for short bonds (p. 10).

**Share of the spread (Table 5, p. 11).** Spec is 24% pre-subprime (band 18% to 30%) and 23% post-subprime (band 16% to 30%). The authors call the Spec fraction stable (p. 11). By maturity post-subprime, the share runs from 11% at under one year to 43% at 10 to 30 years.

**Paired regression (Table 7, p. 16).** t in parentheses.

| Measure | Pre, investment | Pre, speculative | Post, investment | Post, speculative |
| --- | --- | --- | --- | --- |
| `lambda` | 0.01 (3.79) | 0.09 (2.43) | 0.12 (3.58) | 0.41 (1.95) |
| Roll | 0.03 (3.56) | 0.16 (2.54) | 0.05 (2.14) | 0.39 (1.44) |
| Amihud | 2.26 (5.11) | 16.80 (3.51) | 16.10 (3.04) | 54.65 (1.54) |

So inside one firm, Roll has the expected sign and is significant before the crisis, in speculative grade also.

**Liquidity beta (Table 6, p. 16).** Spec pre-subprime: beta 0.0162 (t 1.31). Spec post-subprime: beta 1.3140 (t 2.73), with `lambda` 0.4155 (t 7.08).

**Basis (pp. 9–10, note 9).** The nondefault part from the swap basis is smaller and often negative in speculative grade. The note quotes 17.6 bp for BB from Longstaff et al., and 2.8, −53.5, and −75.4 bp for BB, B, and CCC from Han and Zhou. The authors conclude that factors other than bond liquidity explain the basis there.

**Benchmark (p. 20).** With Treasury in place of swap, the component in bp changes by less than 10 bp for all ratings. The fraction of the spread does depend on the benchmark.

**Reduced sample (p. 16).** With bonds in existence by February 2005 only, the results are noisier for speculative grade, and the component in November 2008 is small.

## Limits
- The sample holds no callable bonds (pp. 3–4). Most HY bonds are callable (`docs/methodology.md`, Known gaps). So the Spec row covers an unusual part of HY.
- A bond needs at least four trades in a quarter (p. 7). This drops the least liquid bonds, so the liquidity component may be too low for them.
- The component is relative to the 5th percentile of each bucket, so it leaves out any premium in the most liquid bonds.
- The sample has one crisis and ends in 2009 Q2. The pre and post split is one regime break.
- The normalization of `lambda` uses the mean and standard deviation across all bonds and quarters (p. 19). This is full-sample data. It cannot go into a live score as written.
- Regressions are contemporaneous. A high spread may itself cause low liquidity. The authors test this (p. 20), but 20% of the statistics are significant.
- Rating classes are coarse. Spec pools all speculative grade ratings, with no split in Table 4.

## Section touched
`docs/methodology.md` Section 7.2 (liquidity block), Section 7.3 (`sigma(x)`), Section 4.7 (clock test), Section 3.1 (`cds_5y`) and the "Known gaps" rows on the basis and on the liquidity model. Spec: `docs/factors/F13-realized-illiquidity.md`.

## Use for the two clocks
**What the source says.** A four-part composite prices liquidity in speculative grade where Roll does not, in pooled data. Inside one firm, both have the expected sign. The liquidity component rises with maturity. The swap basis is a poor liquidity measure in speculative grade.

**What our data says.** Section 7.2 uses `bid_ask_bp`, `log amount_outstanding`, `trace_count`, and bond age. It has neither `lambda` nor gamma. `docs/factors/F13-realized-illiquidity.md` uses Amihud. The methodology plans a basis feature in its Known gaps table. No liquidity control has entered any clock test, since `renewal_split_test` has no controls.

**What we decide (our proposal, not the source's claim).**
1. **Add a `lambda`-type measure to the Section 7.2 block.** Normalize by an expanding window, not by the full sample, so that the measure stays point-in-time. Use gamma as a second column, since `bao-pan-wang-2011-bond-illiquidity-gamma.md` shows its use in investment grade.
2. **Control for maturity in `clock_overlap`.** The feature in `mamaysky-shen-wu-2026-credit-information-earnings-calls.md` rises with bond maturity, and so does the liquidity component here (Table 4, p. 10). So a positive slope on `clock_overlap` may be liquidity. The test needs three parts:
   - Issuer-by-date effects.
   - A maturity function fitted across all bonds in the same rating and date.
   - `lambda` as a control.
   
   The source's firm and maturity dummy would absorb the feature, so use only a firm and date effect.
3. **Paired design as a clean liquidity slope.** Same-issuer bonds with similar maturity share every issuer-level clock feature and nearly the same `clock_overlap`. So the paired slope on `lambda` is free of the clock. Table 7 (p. 16) shows that the slope differs by regime and rating, and the post-crisis speculative slope reaches only the 10% level. So fit the slope by rating group and regime on our panel (Our choice, v0), and use it in the `clock_overlap` regression, in place of an estimate from the same data. A clock slope that falls to zero after this step has no room left beyond liquidity.
4. **Do not use the basis as the HY liquidity measure.** This changes the Known gaps row: keep `cds_5y` as a credit anchor and as a sign test (`longstaff-mithal-neis-2005-default-liquidity-cds.md`). Do not read the basis as liquidity.
5. **Read S1 with the share in mind.** In non-callable speculative grade bonds, the median liquidity part over the swap rate is 24% and 23% (p. 11). The source says that this fraction moves with the benchmark (p. 10). A wide S1 may hold this part. Report the S1 rank IC inside `lambda` quintiles before any reading of it as cheapness.
6. **Cost clock has no credit-free test here.** Clock features are issuer-level, so the paired design cannot test them. Only `clock_overlap` varies inside one issuer.
