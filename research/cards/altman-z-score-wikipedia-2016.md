# Wikipedia contributors (2016), "Altman Z-score", in the compiled book *Altman Z-Score* — NOT Altman (1968)

Encyclopedia compilation, not peer reviewed. The PDF is a LaTeX book built from Wikipedia on 18 March 2016 (CC BY-SA 3.0). It has 39 pages and eight articles. Only Chapter 1 ("Altman Z-score", revision oldid 710491791) is on topic. Chapters 2 to 8 cover bankruptcy law, financial distress, creditor, debtor, IVA, liquidation, and receivership. They carry no model content. File: `/media/ak/10E1026C4FA6006E/GitRepos/altman_z_score/Altman_Z-Score.pdf`. Page numbers below are PDF pages. Printed page 1 is PDF page 4.

The 1968 seed paper is still not on disk: Altman, E. I. (1968), "Financial Ratios, Discriminant Analysis and the Prediction of Corporate Bankruptcy", *Journal of Finance* 23(4), 189–209. The same folder holds a second third-party note (Ahmed and Govind, "An Evaluation of the Altman Z Score"). This card does not cover it.

## Claim
A linear score of five accounting ratios separates firms that go bankrupt within two years from firms that survive (p. 4). Altman later re-fitted the score for private firms (Z') and for non-manufacturers and emerging markets (Z'') (p. 5). The article says that no balance sheet model suits financial firms (p. 5).

## Method
Fisher (1936) linear discriminant analysis on a matched sample. Altman matched each bankrupt firm to a survivor by industry and approximate asset size (p. 4). Beaver (1966, 1968) tested one ratio at a time. Altman's step was to weigh several ratios at once (p. 5).

Ratio definitions (pp. 4–6):

| Ratio | Z (public manufacturers) | Z' (private firms) | Z'' (non-manufacturers, emerging markets) |
| --- | --- | --- | --- |
| X1 | Working capital / total assets | (Current assets − current liabilities) / total assets | Same as Z' |
| X2 | Retained earnings / total assets | Same | Same |
| X3 | EBIT / total assets | Same | Same |
| X4 | Market value of equity / book total liabilities | Book value of equity / total liabilities | Book value of equity / total liabilities |
| X5 | Sales / total assets | Same | Not used |

Formulas and zones as the article prints them:

- Z = 1.2 X1 + 1.4 X2 + 3.3 X3 + 0.6 X4 + 1.0 X5 (p. 4). Section 1.4 prints 0.999 X5 (p. 5). Zones: safe above 2.99, grey 1.81 to 2.99, distress below 1.81 (p. 5).
- Z' = 0.717 X1 + 0.847 X2 + 3.107 X3 + 0.420 X4 + 0.998 X5 (p. 6). Zones: safe above 2.9, grey 1.23 to 2.9, distress below 1.23 (p. 6).
- Z'' (non-manufacturers, as labelled) = 3.25 + 6.56 X1 + 3.26 X2 + 6.72 X3 + 1.05 X4 (p. 6).
- Z'' (emerging markets, as labelled) = 6.56 X1 + 3.26 X2 + 6.72 X3 + 1.05 X4 (p. 6).
- Z'' zones: safe above 2.6, grey 1.1 to 2.6, distress below 1.1 (p. 6). The article gives one zone set and does not say which Z'' version it fits.

## Data
Original sample: 66 publicly held manufacturers, half of them Chapter 7 filers. Firms with assets under $1 million were dropped (p. 4). The article gives no sample period and no sample for Z' or Z''. It cites Altman (2000), Altman (2002), and an Altman 2014 IRMC paper for the later variants (p. 6).

## Result
- Mean score: −0.25 for the bankrupt group and +4.48 for the survivors (p. 5).
- Two years before failure: 72% accurate, with a 6% Type II error (Altman 1968, as cited, p. 5).
- One year before failure: about 80% to 90% accurate in three later test periods up to 1999. The Type II error was about 15% to 20% (Altman 2000, as cited, p. 5).
- The article gives no one-year accuracy for the 1968 sample and no accuracy for Z' or Z''.

Defects in the source. Read these before any number enters code:
1. The article defines Type II error twice, with opposite meanings: "false negatives" and "classifying the firm as bankrupt when it does not go bankrupt" (p. 5).
2. The two Z'' versions differ only by the 3.25 constant. One zone set cannot fit both. The label assignment needs a check against Altman (2000) or the 2014 paper.
3. The Z' formula uses T1 to T5 for the ratios it defines as X1 to X5 (p. 6).
4. The X5 coefficient appears as 1.0 and as 0.999 (pp. 4–5).

## What our data says (grep of docs/, hy/, scripts/, 22 October 2026)
- **No Z-score in code.** `hy/` and `scripts/` contain no Altman score. The `zscore` and `z_score` functions in `hy/groups.py`, `hy/fairspread.py`, and `hy/rv.py` are statistical standard scores, not Altman.
- **Listed but not built.** `docs/writeup/combined_framework.md` (metrics table, line 2354) lists `altman_z` as 1.2A + 1.4B + 3.3C + 0.6M + 1.0T. It sits in group G4, step S12, band "Rec.", and "In code: no". It is the manufacturer Z, not Z''.
- **Absent from the rulebook and the spine.** `docs/framework.md` F8 has no Altman row. The health panel E6 (`hy/groups.py`, weight 0.05, step S13) does not use it. The Section 7.2 PD logit in `docs/methodology.md` has no Z term. `research/reading-list.md` names Altman (1968) as the PD seed paper.
- **Inputs not yet loaded.** `hy/sources/compustat_pit.py` reads `comp_pit.pithistdataus`. Its field map has `saleq`, `oibdpq`, and `dpq`. It lacks `atq`, `actq`, `lctq`, `req`, `ltq`, `ceqq`, and `oiadpq`. So no Z variant is computable today. EBIT can come from `oibdpq − dpq`. The current `comp.fundq` view is not point in time, so do not use it for a backtest.
- **Variant choice: Z''.** Our issuers include casinos, cruise lines, hospitals, and cloud providers. X5 (asset turnover) varies with industry, and Z'' drops it. Z'' uses book equity, so it works for issuers without listed equity. Z needs market cap (`prccq × cshoq`) and fits manufacturers only.

**Proposed test (falsifiable).** Z'' adds rank IC after costs beyond spread level on the 2008–2026 TRACE HY panel.
1. Each month t, compute Z'' (no-constant form) per issuer from the last `comp_pit` filing with `available_at` before t.
2. Regress the cross-sectional rank of Z'' on the rank of log OAS. Keep the residual. A high residual means a healthy balance sheet at a given spread.
3. Score the residual against next-month excess return with `hy.signals.rank_ic` after costs. Use the `CYCLE_WINDOWS` of `hy/backtest.py`: 2008–2009, 2015–2016, 2020, 2022.
4. Pass: IC after costs above zero in at least three of four windows (`hy.backtest.cycle_test`). Fail: IC at or below zero in two or more windows.
5. Second check: add Z'' to the Section 7.2 PD logit. Keep it only if AUC by rating improves out of sample.

## Limits
- Secondary source. The article is a Wikipedia summary of Altman's papers, so every number is second hand. Cite Altman (1968) and Altman (2000) once they are on disk.
- 1960s manufacturers, 66 firms, no holdout sample described. Coefficients may not carry to 2008–2026 HY issuers.
- Leveraged buyout issuers often carry negative book equity and negative retained earnings. Then X2 and X4 are negative, and Z'' falls in the distress zone whatever the cash flow.
- Z'' uses trailing book ratios. Section 7.2 fits PD on forward features. A trailing score may add nothing that `lev_fwd` and `cov_fwd` do not already hold.
- Excludes financial firms, as the article states (p. 5).

## Section touched
`docs/methodology.md` Section 7.2 (the PD logit, candidate covariate). `docs/framework.md` F8 (candidate metric `altman_z2`, which feeds the E6 health panel at step S13). No section changes until the test above runs.
