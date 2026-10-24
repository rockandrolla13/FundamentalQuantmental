# Elkamhi and Lee (2026), "A Seat at the Table: Turning AI Macroeconomic Views into Portfolios with a Factor Framework"

SSRN 7128169, July 2026. Working paper, not peer reviewed. Copy: `/media/ak/10E1026C4FA6006E/GitRepos/creditmacro/ssrn-7128169.pdf`. Page numbers are PDF pages (51 pages). The authors are a finance professor (Rotman) and a pension fund director (HOOPP).

## Claim
1. Express a macro view as probabilities over four regimes (growth up or down times inflation up or down) plus a confidence `γ`, not as point forecasts (pp. 5, 17).
2. Turn macro states into factor views with a pinned table of signed loadings. Theory sets each sign. History sets each magnitude. Noise may shrink a loading to zero but never flip its sign (pp. 13–14).
3. Tilt the approved neutral inputs by the view in proportion to `γ`. Always show the no-view twin (`γ = 0`), so the effect of the view is visible (pp. 7, 18).
4. Consensus forecasts and market positioning are the benchmark for "surprise". They never count as evidence in the probability (pp. 8–9, 13).
5. The regime probabilities are "unvalidated" conviction scores until a dated, scored track record exists (p. 15).

## Method
**Ensemble average (Eq. 1, p. 13).** Five judges give a probability for each state `j`. Average them and keep the spread:

```latex
\bar{p}_j = \frac{1}{n}\sum_{i=1}^{n} p_{ij}, \qquad SE(\bar{p}_j) = \max\!\Big(\frac{\hat{\sigma}_j}{\sqrt{n}},\ 1\,pp\Big)   \quad (1)
```

Intuition: disagreement among judges becomes a band, with a one-point floor so that a unanimous panel does not claim false precision.

**State to factor (Eqs. 2–3, p. 14).** Each validated state `j` has a signed loading `β_j` on a factor (growth, inflation, real rate):

```latex
g_j = \bar{p}_j\,\beta_j   \quad (2), \qquad P(+) = \frac{\sum_{j \in S^+} \max(g_j, 0)}{\sum_{j \in S^+} \beta_j}   \quad (3)
```

Intuition: probability of the state times the push the state delivers, clamped at zero so that noise cannot reverse the theory. A seeded Monte Carlo (10,000 draws) draws judge error, loading error, and a pinned cross-component correlation together (p. 14). The contribution variance is (p. 42):

```latex
\mathrm{Var}(g) = \beta^2 \sigma_p^2 + \tfrac{1}{n_{states}}\,\sigma_\beta^2 + \sigma_p^2 \sigma_\beta^2
```

The loading error is weighted by the uniform `1/n_states`, not by `p̄`. A state that becomes unlikely does not make history's uncertainty about its effect smaller (p. 42).

**Loading calibration (footnote 2, p. 41).** Three strength grades: `|β|` = 0.45, 0.825, 1.25 (return over volatility). Loading error `σ_β = max(0.40, |β|/2)` times 1.00, 1.15, or 1.30 for strong, medium, or weak evidence. The 0.40 floor caps each loading's t-statistic near 2. A state enters the table only if it passes a minimum historical hit rate and effect size with the right sign (p. 41).

**Credit example (pp. 41–42).** Bank lending standards from the Fed loan officer survey (SLOOS) have three states. "Aggressive tightening" loads negative on growth at medium strength. "Accommodative" loads positive. "Moderate tightening" fails the validation bar and has no loading.

**Derived layer (p. 42).** Corporate credit spreads have no hand-calibrated loading. "Spreads widening" inherits a loading from the bundle of anchor states it co-moves with (GDP below trend, credit impulse negative, bear flattening), via a calibrated linkage regression. Its uncertainty is inherited the same way. The spreads link passed for growth and inflation and failed for the real rate.

**Regime join (Eq. 4, p. 17).** Split the in-line mass equally, then join growth and inflation as independent:

```latex
\pi_{\uparrow\uparrow} = P_G(\uparrow)\,P_I(\uparrow), \ \dots, \qquad P_G(\uparrow) = P_G(+) + \tfrac{1}{2}P_G(0)   \quad (4)
```

The authors call independence a convention, not a theorem. Their own work finds GDP and CPI surprises only weakly correlated over the long run, "even though the correlation can run high in selected periods" (p. 17).

**View tilt (Eq. 6, p. 18).** Per regime `s`, a pinned premia tilt `δ_s` and covariance tilt `Δ_s`:

```latex
\mu_a(\pi, \gamma) = m_{cma} + g\,B\lambda^0_f + \gamma\,B\sum_s \pi_s \delta_s, \qquad \Sigma_a(\pi, \gamma) = \Sigma^0_a + B\Big(\gamma \sum_s \pi_s \Delta_s\Big)B'   \quad (6)
```

Intuition: the view moves the neutral inputs, scaled by confidence. `γ = 0` returns the neutral inputs exactly.

**Surprise axis (pp. 8, 15).** Factor probabilities are for the outcome "above, in line with, or below what forecasters already expect". Consensus is the benchmark, never a vote.

## Data
A live system run weekly. The worked output is dated 28 June 2026: `π = (42.0, 28.6, 17.6, 11.9)%` over (G↑I↑, G↑I↓, G↓I↑, G↓I↓), `γ = 0.5` (p. 24). Stress views: stagflation `π = (15, 5, 65, 15)%` and recession `π = (5, 15, 15, 65)%`, both with `γ = 0.8` (p. 24). Universe: 30 assets on 3 factors. Loadings come from the authors' earlier work (Elkamhi et al. 2021, Lee and Salerno 2023), not from this paper.

## Result
No out-of-sample result. The authors say directly: "It is not evidence that AI regime views make money" (p. 4). Calibration "can only be earned by a live, dated, scored track record that does not yet exist" (p. 15).

## What our data says
No fit on our data yet. The paper solves a problem close to link 1 for a different target (asset allocation, not issuer cases). Effect on the three macro links:

1. **Link 1, path probabilities (5.4).**
   - Agreement. Both use a growth and inflation grid and both turn forecast evidence into region probabilities. Their four regimes map to our recession, stagflation, higher for longer, and disinflation rally. Our soft landing is a middle region they do not have.
   - Disagreement on correlation. Decision page `2026-10-22-macro-path-construction` uses `ρ = −0.2` or `estimate_rho`. The paper uses `ρ = 0` and cites weak long-run correlation with high episodic correlation (p. 17). When is each right? Zero is right on average. A fitted `ρ` is right only if it is fitted on a window that matches the current regime. Proposal: keep `estimate_rho`, but log the mass under `ρ = 0` beside it. Test: over matured vintages, compare the Brier score of the realised region under both. Keep the one with the lower score.
   - Disagreement on the axis. The paper scores growth and inflation against the consensus (surprise axis). Our decision page cuts regions on a historical axis, because "on the forecast's own scale every forecast gives the same masses". Both are coherent. A surprise axis answers "what is not priced". A historical axis answers "what state will the economy be in". Section 5.2 needs the state, because a recession hurts EBITDA whether or not it was expected. So we keep the historical axis for case weights. A surprise axis fits S7 (the sector tilt), which trades what the market has not priced.
   - Confidence dial. Our Bayes update in 5.4 has no `γ`. Proposal: write the posterior as `p_γ(m) = (1 − γ) π_phase(m) + γ p(m)` and report `γ = 0` (the phase prior alone) as the no-view twin in every memo. Set `γ` from the forecast band width. Test: a `γ` below 1 must lower the Brier score of the realised region over matured vintages, or `γ = 1` stays.
2. **Link 2, downside weights (5.2).**
   - Supports `sloos_tightening` as an input with a fixed negative sign on growth. The paper's validation bar (minimum hit rate and effect size, sign from theory) is a usable rule for which macro inputs the logistic may keep.
   - Proposal: constrain the logistic signs. A rise in `hy_oas`, `sloos_tightening`, or `default_rate_fcst`, or a fall in `pmi`, must not lower `p`. Fit with sign constraints, and drop any input whose unconstrained sign is wrong, as the paper drops "moderate tightening" (p. 42). This matches the CLAUDE.md test on monotone signs in the fair spread model.
   - The derived layer is the paper's answer to a missing loading: borrow the loading from anchors the series co-moves with, and carry the anchors' error. We could use the same rule for a sector with too little EBITDA history to fit `θ_sector`.
3. **Link 3, revenue shift (5.2).** Nothing direct. The loading error floor (t-statistic capped near 2) is a usable rule for `β_sector`: shrink a sector beta whose t-statistic exceeds 2 on a short sample.

## Limits
- Not peer reviewed. No out-of-sample evidence. The regime probabilities are unvalidated by the authors' own statement.
- Asset allocation across 30 assets. Nothing on single issuers, default, or EBITDA.
- The loading magnitudes come from earlier papers that this card has not read.
- The judges are language models from one base model, so the ensemble spread is a lower bound on the true uncertainty (p. 13).

## Section touched
`docs/methodology.md` Section 5.4 (path masses, correlation `ρ`, confidence `γ`, no-view twin), Section 5.2 (sign constraints on the logistic, `sloos_tightening`), and Section 8 S7 (surprise axis). Decision page `docs/decisions/2026-10-22-macro-path-construction.md` (`ρ` and the axis choice).
