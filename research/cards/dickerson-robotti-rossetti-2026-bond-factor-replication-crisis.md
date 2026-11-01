# Dickerson, Robotti, and Rossetti (2026), "The Corporate Bond Factor Replication Crisis"

arXiv 2604.07880v1, April 2026 (63 PDF pages), at https://arxiv.org/pdf/2604.07880. DOI of the SSRN record: 10.2139/ssrn.6088966. **Working paper. Not peer reviewed in the version we read.** An earlier title was "Common pitfalls in the evaluation of corporate bond strategies" (p. 1). The Internet Appendix was not opened. Page numbers below are PDF pages. The sample covers IG and HY, with rating splits.

## Claim
Most corporate bond factor premia come from two biases plus researcher choice (p. 1). After correction, most of 108 factors have no significant bond CAPM alpha. Survivors are mainly credit-spread-based value factors, which keep roughly half of their premium (pp. 3–4). Momentum, idiosyncratic volatility and downside risk factors lose significance once the return filter is feasible (pp. 3–4, 40).

## Method
**Latent Implementation Bias (LIB), pp. 11–15.** The same noisy price enters both the signal and the return denominator.

```latex
\hat P_{i,t} = (1 + \delta_{i,t}) P_{i,t}, \qquad \hat s_{i,t} = s_{i,t} + \eta_{i,t}, \qquad \epsilon_{i,t} \approx \delta_{i,t+1} - \delta_{i,t}
```

Intuition: a bond priced too low this month looks cheap and also shows a high return next month, so the noise alone earns a premium.

Two repairs break the shared price (p. 15):
- Adjusted signal: compute the signal from a price at least one business day before month end, up to ten.
- Adjusted return: measure the return from the first price in the next month.

```latex
r^{End}_{i,t+1} \approx \underbrace{\frac{P^{bgn}_{i,t+1}}{P^{end}_{i,t}} - 1}_{LIB_{i,t+1}} + r^{Bgn}_{i,t+1} \quad (3), \qquad Bias_{1-2} = (\omega_t - \omega^{a}_t) \times r^{End}_{t+1}, \qquad Bias_{1-3} = \omega_t \times (r^{End}_{t+1} - r^{Bgn}_{t+1}) \quad (4,5)
```

Intuition: the price move between signal date and first possible trade is not earnable, so remove it, and the difference measures the bias with no need for the true price.

**Look-Ahead Bias (LAB), pp. 21–23.** Winsorizing returns at a full-sample threshold uses future data.

```latex
LAB_{t+1} = \tilde r^{LS}_{t+1} - r^{LS}_{t+1} = \frac{1}{N^L_t}\sum_{i \in Long}\Delta_{i,t+1} - \frac{1}{N^S_t}\sum_{i \in Short}\Delta_{i,t+1} \quad (6)
```

Intuition: if one leg holds the extreme returns, a cap on those returns flatters only that leg.

The repair uses thresholds computed only from data through month t (p. 23).

**Non-standard error (p. 30, eq. 7).** `NSE` is the interquartile range of estimates across research paths. Compare it with the sampling error.

```latex
NSE_v = Q_{0.75}(\hat\mu_v) - Q_{0.25}(\hat\mu_v)
```

Intuition: if two careful researchers can reach opposite results by defensible choices, then the t-statistic of one path overstates what we know.

**Paths (pp. 30–33).** 648 data-filter paths per signal (69,984 in total), 168 construction paths per signal (18,128 valid).

**Multiple testing (p. 4).** Benjamini-Hochberg across 432 specifications.

**Placebo (p. 19).** Non-price factors should show no bias from the return gap. Among 78 non-price factors, 10–18% show a significant gap, against 43–67% among 30 price-based factors.

**Benchmark.** One-factor bond CAPM with value-weighted MKTB (p. 9). The authors say the CAPM is a benchmark, not a claim about the true model (p. 4).

## Data
- Enhanced TRACE and Rule 144A from June 2014, merged with FISD, August 2002 to December 2024 (pp. 8–10). 269 months, 52,656 bonds, mean 6,790 bond-month observations a month (p. 10).
- Bonds stay in the sample through and after default (pp. 7, 9–10).
- Added filters beyond Dick-Nielsen: a decimal-shift corrector and a bounce-back filter (p. 8).
- 108 signals in nine clusters (p. 10). Sorts: value-weighted deciles and within-firm (p. 17).
- Open data and code: Open Bond Asset Pricing and PyBondLab (pp. 1, 6).

## Result
**LIB, Table 1 (p. 37).** Monthly percent, t in parentheses.

| Factor | Unadjusted alpha | Adjusted signal alpha | Adjusted return alpha |
| --- | --- | --- | --- |
| Spread value `val_ipr`, single sort | 0.76 (5.24) | 0.31 (2.12) | 0.33 (2.61) |
| Spread value `val_ipr`, within firm | 0.57 (7.27) | 0.18 (4.25) | 0.20 (4.30) |
| Value `val_hz`, single sort | 0.47 (3.71) | 0.12 (1.13) | 0.12 (1.08) |
| Bond book-to-market `bbtm`, single sort | 0.54 (1.69) | 0.35 (1.12) | 0.29 (1.04) |
| Bond book-to-market `bbtm`, within firm | 0.28 (4.11) | 0.10 (1.86) | 0.09 (1.64) |
| Credit spread `cs`, single sort | 0.66 (2.39) | 0.50 (1.82) | 0.38 (1.55) |
| Six-month spread change `dcs6`, single sort | −0.79 (−4.55) | −0.29 (−1.79) | −0.25 (−1.71) |
| Short-term reversal `str`, single sort | −0.77 (−3.58) | 0.12 (0.68) | 0.03 (0.18) |

The premium on `str` falls from −0.99% (t −4.46) to −0.09% (t −0.51), so bias is 91% of the premium (p. 17). The `val_ipr` bias is 45 bp, 47% of the premium (p. 17).

**LAB, Table 4 (p. 40).** Alpha with and without ex-post winsorizing.
- `ivol_bbw`: 0.53 (t 2.58) and 0.18 (t 0.72).
- `var_95`: 0.56 (t 3.01) and 0.24 (t 1.42).
- `es_90`: 0.74 (t 3.10) and 0.31 (t 1.42).
- `mom6_1`: 0.46 (t 2.39) and 0.22 (t 1.08). Its premium is 0.30 and 0.00.

LAB spikes in distress, with a convex link to VIX (pp. 26–27).

**Illiquidity (pp. 19–20, 35).** LIB for five illiquidity factors is small. Their CAPMB alphas are 0.10% to 0.20% with |t| below 1.65.

**Multiple testing (p. 4).** 26 of 432 alphas (6.0%) survive. Before correction, 119 premia are nominally significant, and 22 survive.

**Non-standard error (Tables 5, 6, pp. 41–42).**
- Data paths: NSE 0.35% a month against a mean premium of 0.33%. For alphas, 0.27% against 0.15%. Ratio to the sampling error 1.15.
- Construction paths: NSE 0.31% against 0.22%. Ratio 1.45.
- Twelve of 36 top factors flip the sign of the premium across constructions, and 29 flip the alpha (p. 34).
- 94% of construction variations do not improve the alpha (p. 34).

## Limits
- The bond CAPM alpha is a strict hurdle, but it can remove genuine premia that load on the market. The authors state that they do not argue the CAPM is right (p. 4).
- The gap repair assumes serially uncorrelated price noise. With stale prices, some correlation remains (p. 13, note 12).
- Costs are not deducted, and the paper names this as future work (pp. 35–36).
- Value-weighted deciles underweight small bonds, which is where other papers find more alpha.
- Most tables pool IG and HY, with subsamples only in the path grids. The HY-only view sits in the Internet Appendix, which we did not open.
- Their reading of the replication crisis differs from Dick-Nielsen et al. (2023), who point to data errors (p. 6). We did not open that paper.

## Section touched
`docs/methodology.md` Section 7.3 (S1 construction), Section 7.4 (value), Section 8 (composite), Section 11 (backtest design). `hy/backtest.py`. Specs: `docs/factors/F04-bond-momentum.md`, `docs/factors/F15-pca-ou-reversal.md`, `docs/factors/F16-downside-risk.md`.

## Use for the two clocks
**What the source says.** The S1 family is the family that survives. The bias runs from 15% of the premium for the plain spread sort to 47% for `val_ipr`, and 65% for `val_ipr` within firm (Table 1, p. 37, our arithmetic). No row of the source matches S1. Clock features that use no price have no shared-price link (pp. 11, 19). Any factor test needs the gap, ex-ante filters, a path grid and a false-discovery control.

**What our data says.** `realised_excess_return` in `hy/backtest.py` divides by the month-end price `P_t` of the same panel row that supplies `g_spread`. So spread-based predictors share a price with the return denominator, with no gap. That function has no ex-post return winsorizing. It deducts cost later, in `realised_net`. A skip-month test on file shows the bias in the peer gap, which is S1 as built (`docs/decisions/2026-10-23-peer-fair-spread.md`). Plain IC after cost at 3 months falls from +0.054 (t 3.4) to -0.000 (t 0.0). IC beyond spread falls from +0.112 to +0.073, from +0.120 to +0.100, and from +0.198 to +0.181. The 8-day gap and OneScore are not measured. Results such as ESP's +0.096 may hold this bias.

**What we decide (our proposal, not the source's claim).**
1. **Data rules that come before any residual test (changes Section 11).**
   - Compute `ε` from a price at least one business day before the month end, or measure the return from the first price of the next month. Report both.
   - Filter returns only with data through the formation month.
   - Report the bias: the difference between the unadjusted and gapped result, by the two formulas above.
2. **Spread-scaled clock features need the gap.** Plain shares use filing data and no price. But any feature divided by spread, or a test "beyond spread level", brings price into the signal. The clock tests of Section 4.7 condition on `widest`, so they need the gap also.
3. **Path grid for the clock.** Report the clock result over a fixed grid: weighting, sort coarseness, rating class, maturity bucket. Report the NSE and its ratio to the standard error. Our v0: a result that flips sign over the grid does not count.
4. **False-discovery control.** Treat all clock features, horizons and cells as one family, and use Benjamini-Hochberg. Our v0 uses a 5% false-discovery rate. The family holds at least the five signals in `scripts/backtest_clocks.py` at two horizons.
5. **Within-firm sort as a design.** The within-firm `val_ipr` alpha is the most precise survivor (t 4.25, p. 37). This supports the within-issuer test of `clock_overlap` in `mamaysky-shen-wu-2026-credit-information-earnings-calls.md`.
6. **Flag for F16.** `var_95` loses significance once the filter is feasible (p. 40). F16 cites this measure, so its spec needs a note. This card changes no spec.
