# Figlewski, Frydman, and Liang (2012), "Modeling the Effect of Macroeconomic Factors on Corporate Default and Credit Rating Transitions"

International Review of Economics and Finance 21(1), pp. 87–105. Peer-reviewed journal article. We read the SSRN working paper 934438, version of 5 September 2006, 55 PDF pages (`ssrn-934438.pdf` in the repo root). Page numbers below are PDF pages. The printed page number is the PDF page minus 2. The journal version may differ in sample, coefficients, and tables. Quote the journal only after a check against it.

## Claim
Macro factors add highly significant power to a hazard model of default and of major rating changes, beyond rating-history covariates (PDF pp. 2, 32). The firm-specific coefficients barely move when the macro factors enter (PDF pp. 18, 24). So the macro information is "incremental to, and largely independent of" the rating information (PDF p. 18). Single macro coefficients are unstable. Many change sign once the other macro factors enter (PDF p. 32). Macro factors matter least for issuers rated Caa, Ca, and C (PDF pp. 16, 22, 32).

## Method
**Cause-specific Cox hazard (PDF pp. 5–6).** Each credit event type j has its own hazard. Other exits censor the spell.

```latex
\lambda_j(t; Z(t)) = \lambda_{0j}(t)\,\exp\big[\beta_j' Z(t)\big], \qquad j \in J   \quad (2)
```

Intuition: each covariate scales the event rate by a fixed factor per unit, on top of a free baseline. The clock t is the time since the issuer entered its current rating class, not calendar time (PDF p. 6). So the baseline λ_0j(t) absorbs duration in the rating class without a stated form.

**Partial likelihood (PDF pp. 7–8).** Estimate β_j without the baseline. Tied event dates use the generalised form (4'). Model choice uses AIC and likelihood ratio tests (PDF p. 19).

```latex
L(\beta_j) = \prod_{n=1}^{N} \frac{\exp[\beta_j' Z_n(T_n)]}{\sum_{i \in R_n} \exp[\beta_j' Z_i(T_n)]}   \quad (4)
```

Intuition: at each event date, compare the issuer that had the event with every issuer still at risk.

**Macro lag (PDF p. 14).** Most macro series enter as an exponentially weighted average of the previous 18 months, with decay 0.88.

```latex
X_t = \frac{\sum_{k=1}^{K} \delta^{k-1} x_{t-k}}{\sum_{k=1}^{K} \delta^{k-1}}, \qquad K = 18,\ \delta = 0.88   \quad (6)
```

Intuition: macro stress builds over months, so a smooth lag replaces many lag coefficients. The mean lag is 8.33 months. The newest month weighs about 9 times the oldest. Data run to the previous month only. Windows of 12 and 24 months and decays from 0.8 to 1.0 gave results that were "not especially sensitive" (PDF p. 14). The CFNAI and the default rate enter as 3-month moving averages instead (Table 3, PDF p. 40).

**Events modelled (PDF pp. 4, 9–10).**
1. Speculative grade to default, also split into Ba and B to default, and Caa, Ca, and C to default.
2. Investment grade to speculative grade (the fallen angel event).
3. Ba and B to investment grade.
4. Caa and Ca to B or Ba.

**Covariates (PDF pp. 10–14, Table 3).**
- Firm: initial rating investment grade, initial rating C class, current rating dummies, downgraded within 2 years, upgraded within 2 years, log(years since first rated). No balance sheet or equity term, by design (PDF p. 4).
- General macro: 10-year Treasury yield, unemployment rate, CPI inflation, S&P 500 return, CFNAI.
- Direction of the economy: real GDP growth, change in industrial production, change in unemployment.
- Economic slack: real GDP minus potential, capacity utilisation, industrial production minus its 20-year trend.
- Credit market: Baa minus 10-year Treasury yield, Moody's corporate default rate.

**Selection (PDF p. 20).** Backward selection drops the least significant variable until all are significant at 5%. "Constrained" keeps the firm and general macro factors. "Full selection" may drop any variable.

## Data
- Moody's Default Research Database, all corporate issuers, January 1981 to November 2002 (PDF p. 8, Table 4 notes).
- A rating that lasts less than 14 days before default is removed. Its time joins the previous rating (PDF pp. 8–9).
- Spells (Table 2, PDF p. 39):
  - Investment grade: 3,422 spells. 788 end in a downgrade to speculative grade. 6 end in default. 944 end in withdrawal.
  - Any speculative grade: 4,327 spells. 902 end in default. 645 end in an upgrade to investment grade. 1,655 end in withdrawal.
  - Ba and B: 4,196 spells. 448 defaults. 641 upgrades to investment grade.
  - Caa, Ca, and C: 942 spells. 454 defaults. 102 upgrades to Ba or B.
- The source is inconsistent on the default rate. The text says the share defaulting "in the previous 12-month period" (PDF p. 14). It also says "over the last 3 months" (PDF p. 16). Table 3 says "3-month moving avg".
- Moody's alphanumeric modifiers and watchlist are not used (PDF p. 8).

## Result
**Macro adds power to default (Table 5, PDF pp. 42–44).**
- All speculative grades: −2 log L falls from 11,129.81 (firm only) to 10,936.90 (all 13 macro). The LR statistic is 192.91 on 13 degrees of freedom, p of order 10⁻³⁴ (PDF p. 19).
- Ba and B grades: LR 201.16. Caa, Ca, and C grades: LR 42.31.
- The firm coefficients change little. For example, "Downgraded within last 2 years" is 0.446 firm only and 0.436 with all macro (Panel A).

**Firm terms for default, all speculative grades, firm only (Table 5A, PDF p. 42).** Base class is C.
- Current rating Ba −5.305, B −3.505, Caa −1.630, Ca −1.019. All p = 0.000. The order is monotone.
- Downgraded within 2 years +0.446 (p 0.000). Upgraded within 2 years −1.465 (p 0.000). This is rating momentum.
- log(years since first rated) +0.141 (p 0.013). A newly rated issuer is less likely to default than a seasoned one (PDF pp. 17–18). This is the ageing effect.
- Initial rating C class −1.282 (p 0.000). Initial rating investment grade −0.237 (p 0.062).

**Macro terms for default, all speculative grades, constrained selection (Tables 5A and 6A, PDF pp. 42, 45).** Coefficient, p-value, then the standardised coefficient (raw × standard deviation).
- 10-year yield +0.119 (0.012), standardised 0.306.
- Unemployment +0.332 (0.024), standardised 0.498.
- Inflation −0.141 (0.003), standardised −0.285.
- S&P 500 return +0.144 (0.000), standardised 0.179. The authors call this sign anomalous (PDF p. 16).
- CFNAI −0.319 (0.000), standardised −0.245.
- Real GDP minus potential +0.438 (0.000), standardised 1.062. Wrong sign.
- Capacity utilisation +0.152 (0.000), standardised 0.417. Wrong sign.
- Industrial production minus trend −0.109 (0.000), standardised −0.939.
- Default rate +0.265 (0.000), standardised 0.283.
- The three direction-of-economy variables drop out. The Baa spread drops out. In the all-variable fit the spread is +0.185 (p 0.498).

**The spread level adds nothing to default once ratings enter (Table 4, PDF p. 41).** Alone, the Baa spread is +0.474 (p 0.000) for all speculative grades. Beside the firm terms, it is −0.140 (p 0.061). The default rate keeps its sign: +0.353 alone, +0.124 beside the firm terms (both p 0.000).

**Signs flip once the controls change (Table 4, PDF p. 41).** The 10-year yield is −0.064 alone and +0.122 beside the firm terms. Unemployment is −0.181 alone and +0.079 beside the firm terms.

**Macro effects differ by rating (Tables 5B, 5C, 6B, 6C, PDF pp. 43–47).**
- Ba and B to default, constrained: unemployment +0.714 (0.000, standardised 1.137), CFNAI −0.292 (0.003), default rate +0.407 (0.000, standardised 0.435).
- Caa, Ca, and C to default, all variables: CFNAI +0.087 (p 0.733). Default rate +0.006 (p 0.962). Unemployment −0.230 (p 0.007) in the constrained model, a wrong sign.
- The authors conclude that the macro factors "do not seem to affect the hazard of default for the lowest rated firms very much" (PDF p. 22).

**Downgrade from investment grade to speculative grade (Tables 7 and 8, PDF pp. 48–49).**
- Firm only: current rating Baa +2.734, downgraded within 2 years +0.820, upgraded within 2 years −0.823 (all p 0.000). log(years since first rated) −0.050 (p 0.258), not significant.
- Macro LR is 294.60 on 13 degrees of freedom (PDF p. 25). This gain is larger than the 192.91 for default.
- One at a time, every macro factor has the expected sign (Table 7). The Baa spread is +0.837 alone and +0.636 beside the firm terms (p 0.000). The default rate is +0.206 and +0.127 (p 0.000).
- Together, constrained: 10-year yield +0.386, Baa spread +0.437 (p 0.001), real GDP growth −1.633, S&P 500 return −0.084 (p 0.031). Wrong signs: unemployment −0.407 (p 0.016), CFNAI +0.512 (p 0.000), real GDP minus potential +0.395. The default rate drops out. In the all-variable fit it is −0.116 (p 0.067).
- The authors note a rating agency decides a downgrade, while default is "largely exogenous". Moody's rates relative risk, not absolute PD (PDF p. 22).

**Upgrade from Ba and B to investment grade (Table 10A, PDF p. 51).**
- Current rating Ba +1.821. Upgraded within 2 years +0.317. log(years since first rated) +0.321. All p ≤ 0.003.
- Macro LR 147.77. Baa spread −0.708 (p 0.008). Default rate −0.305 (p 0.000). The authors call the two credit market factors the best macro variables for this event (PDF p. 34).
- Upgrade from Caa and Ca: macro LR 23.43 (p 0.037). The authors call it barely significant (PDF p. 28).

**Stability across samples (Table 11, PDF pp. 53–55).** Fits on 1981–2002, 1981–1997, and 1986–2002.
- Default, default-rate coefficient: 0.273 (s.e. 0.065), 0.202 (0.089), 0.121 (0.105). It drops out of the 1986–2002 constrained model (PDF p. 30).
- Default, unemployment: 0.366 (0.162), 0.028 (0.417), 0.405 (0.172).
- Downgrade, CFNAI: 0.562 (0.144), 0.825 (0.159), 0.095 (0.217).
- Downgrade, unemployment, constrained: −0.407 (0.169), +0.630 (0.168), −0.495 (0.078). The sign flips between samples.
- The authors say the period changes the coefficients a lot. They say the choice of variables and the signs stay "quite robust" (PDF p. 31). The unemployment row above does not support that claim for downgrades.

**What the paper does not report.** No out-of-sample test. No AUC or accuracy ratio. No calibration table. No fitted baseline hazard, so no PD level. The fit measures are in-sample AIC and LR tests only.

## What our data says (docs/methodology.md 5.2.1, 9.1, data/raw/backtest/sp_ratings.parquet, 24 October 2026)
This section separates three things. "Source" is what the paper says. "Data" is what our files hold. "Proposal" is what we suggest. Nothing here is fitted.

**Inputs on disk.** `data/raw/backtest/sp_ratings.parquet` holds the monthly S&P issuer rating `splticrm` with `available_at`. It has 150,319 rows and 1,732 gvkeys, January 2007 to February 2017. A count of month-on-month changes between rating groups gives these transitions. The count is a data description, not a fit.
- IG to BB or B: 161. By year: 29 (2007), 23 (2008), 30 (2009), 6 (2010), 13 (2015), 20 (2016).
- BB or B to CCC or C: 237. BB or B to IG: 167.
- CCC or C to D or SD: 136. BB or B to D or SD: 15.

The file covers the 2008 and 2015 windows. It does not cover 2020 or 2022.

**Where the source supports draft 5.2.1.**
1. *Issuer ranks, macro sets the level.* Source: macro adds LR 192.91 for default while the firm coefficients barely move (Table 5A). This matches the Jacobson et al. and Duffie-Saita-Wang cards. It supports the split of `x_{i,t}` and `m_t`.
2. *Trailing default rate in `m_t`.* Source: it is the only credit market factor that survives selection for default, +0.265 (p 0.000), for all speculative grades and for Ba and B (Tables 5A, 5B). This matches Giesecke et al. Caveat: it weakens to 0.121 (s.e. 0.105) in 1986–2002 (Table 11A).
3. *The spread level is weak for default.* Source: the Baa spread turns from +0.474 alone to −0.140 beside ratings (Table 4) and drops out (Table 5A). This supports test T4 and the choice of EBP and the 4-quarter change in `hy_oas` over the level.
4. *No sign constraints.* Source: the 10-year yield, unemployment, CFNAI, and the slack factors change sign with the controls or the sample (Tables 4, 5, 8, 11). This supports the free-sign choice and test T5. It adds a third case to the short-rate dispute: FFL find +0.119 for the 10-year yield in the default model.
5. *Rating interaction in `γ_{c(i)}`.* Source: the macro LR is 201.16 for Ba and B and 42.31 for Caa, Ca, and C. Key macro terms lose significance for the C class (Tables 5B, 5C). This supports an interaction of `m_t` with the rating bucket. It predicts a near-zero macro slope for CCC.

**Where the source differs from draft 5.2.1.**
1. *Rating history is absent from `x_{i,t}`.* Source: current rating, a downgrade within 2 years, and an upgrade within 2 years are the strongest and most stable terms in every event model (Tables 5, 8, 10, 11). Draft 5.2.1 holds leverage, cover, and distance to default only. The rating enters only through `γ`. Proposal: add the rating bucket as an intercept and a "downgraded within 8 quarters" flag to `x_{i,t}`. T1 then decides whether they add rank beyond leverage.
2. *Lag form.* Source: an 18-month exponentially weighted lag, mean lag 8.33 months (PDF p. 14). Draft 5.2.1 uses point values at t − 8 quarters for `hy_oas` and issuance. FFL do not test a 2-year point lag. Their window ends at 18 months. The two forms answer different questions. The López-Salido et al. lag is a sentiment reversal at 2 years. The FFL lag is a slow build of stress. Keep both forms under T3. Do not read FFL as evidence for the t − 8 term.
3. *Horizon.* Source: an instantaneous hazard with no stated horizon and no out-of-sample test. Draft 5.2.1 is a 4-quarter logit. The source says nothing about the 4-quarter level or about the fade beyond 8 quarters.
4. *Ageing.* Source: log(years since first rated) raises default risk (+0.141) and the chance of an upgrade to IG (+0.321) (Tables 5A, 10A). Draft 5.2.1 has no age term. Proposal: test years since first rated as a candidate in `x_{i,t}`, because newly issued high yield issuers fall in this group.

**A rating-transition event beside the EBITDA event.** Source: macro factors explain the fallen angel event better than default (LR 294.60 against 192.91). The Baa spread survives for downgrades (+0.437) but not for default (Table 8). For upgrades to IG, the spread and the default rate both survive (Table 10A). The source does not model the move from B to Caa, which matters most for a high yield book. Data: we hold 237 moves from BB or B into CCC or C and 161 fallen angels in 2007–2017. Section 9.1 already lists "Rating review" as an event with `gap_rating` as its pre-event feature (Section 4.5). Proposal: add one rating event beside the EBITDA event. Model it as "downgrade into CCC or below within 4 quarters" for BB and B issuers, with the same `x_{i,t}` and `m_t`. Feed its probability to the "Rating review" row of Section 9.1. Keep the EBITDA event for the case weights of Section 5.2. The two events answer two questions. The EBITDA event says whether the business falls. The rating event says whether forced sellers arrive (Gatto p. 418).

**Falsifiable test (proposed, not run).** T7, the rating interaction.
- Panel: issuer-quarters of `sp_ratings.parquet` joined to `annual_ebitda.parquet`, 2007–2017, with `available_at` before each decision date.
- Event: the 5.2.1 EBITDA event and, separately, the downgrade into CCC or below within 4 quarters.
- Fit the 5.2.1 model with `γ` by rating bucket (BB, B, CCC). Hold out the 2008 window, then the 2015 window.
- Measure the out-of-sample log-score gain of the macro block (full model minus the model without `m_t` and `γ`) in each bucket.
- FFL predict that the gain is largest for BB and B and near zero for CCC.
- The rating interaction fails if the CCC gain is at least as large as the B gain in both held-out windows. Then drop the rating term from `γ` and keep the cyclical class only.
- The rating event earns its place only if its macro gain exceeds the macro gain of the EBITDA event in both windows.

## Limits
- Moody's rated universe, 1981–2002. The sample has two US recessions (1981–82 and 1990–91) and the 2001 recession. It ends before 2008.
- The event is default or a rating change, not an EBITDA decline. Draft 5.2.1 uses an EBITDA event. The transfer of macro signs from default to EBITDA is an assumption.
- No balance sheet or equity term (PDF p. 4). The paper cannot say how macro terms behave beside leverage or distance to default.
- The macro covariates are highly correlated. The authors tried principal components and saw no gain (PDF p. 16, footnote 15 on PDF p. 28). Single coefficients are not reliable.
- The authors fit 13 macro terms and use backward selection on in-sample p-values. The selected models may overfit. No out-of-sample test checks them.
- The spread series is the Baa minus 10-year Treasury yield. It is not a high yield spread and not the EBP (PDF pp. 11–12).
- The baseline hazard is not reported. The paper gives relative risk only, not PD levels.
- Table 6A gives two standardised values (0.265 and 0.283) for the same raw default-rate coefficient 0.265. With the Table 3 standard deviation of 1.069, 0.283 is the consistent value. We quote 0.283.
- pdftotext merged some table columns. Table 5B and 6B "Full Selection" columns have empty cells. We quote only values whose column we could place.

## Section touched
`docs/methodology.md` Section 5.2.1 (issuer term `x_{i,t}`, macro vector `m_t`, rating interaction `γ_{c(i)}`, tests T3, T4, T5, and proposed T7). Section 9.1 (the "Rating review" event). Section 4.5 (rating gap as the pre-event feature). Decision page `docs/decisions/2026-10-24-downside-weight-model.md`: its "Open" item says this paper has no card. This card closes that item once the lead updates the page.
