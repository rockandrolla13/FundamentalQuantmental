# Valenzuela (2016), "Rollover Risk and Credit Spreads: Evidence from International Corporate Bonds"

Review of Finance 20(2), pp. 631–661, DOI 10.1093/rof/rfv022. Peer-reviewed. Corporate bonds, international. **Added by citation chasing** from Nagler (2015 version, p. 8) and Boyarchenko and Elias (SR 1094, p. 6). **We did not open the journal article.** The University of Chile repository returned no file. We read the working paper "Rollover Risk and Corporate Bond Spreads", Documentos de Trabajo No. 300, Universidad de Chile, 44 pages. Page numbers are PDF pages. The journal numbers may differ.

## Claim
Debt market illiquidity widens spreads more when a firm holds more short-term debt (p. 3). The effect holds in investment grade and speculative grade, is stronger in speculative grade, and is smaller for banks (p. 3).

## Method
Panel of month-end option-adjusted spreads with bond and time effects, errors clustered by bond (p. 15).

```latex
Spread_{bfct} = \gamma_0 + \gamma' X_{bfct} + \gamma_5\, \tfrac{ST}{Debt}_{fct} + \gamma_9\, Rating_{fct}\times Illiq_t + \gamma_{10}\, \tfrac{ST}{Debt}_{fct}\times Illiq_t + A_b + B_t + \epsilon_{bfct}
```

Intuition: γ₁₀ is the extra spread per unit of market illiquidity when more debt must roll soon, and the rating interaction removes flight to quality.

Illiquidity is market-wide (p. 12): the Bao, Pan and Wang Gamma, the Hu, Pan and Wang Noise measure, the on-the-run Treasury spread, the supranational AAA spread, and the KfW spread (pp. 12, 25). Short-term debt is short-term borrowings over total borrowings (p. 13).

Controls for endogeneity (pp. 19–23): interactions of volatility, leverage, size and maturity with illiquidity (p. 20), residual Libor-OIS and TED interactions (p. 21), and IV-GMM with firm effects estimated before 2007 as instruments (pp. 22–23).

## Data
Bloomberg. USD fixed-rate bonds placed in international markets, January 2004 to June 2009, S&P AAA to B− (pp. 8–9). Firms located in the US or England are excluded on purpose (p. 8). 21,375 bond-months: 16,691 investment grade and 4,684 speculative grade (p. 9). Table 3 covers 667 bonds: 497 and 170 (p. 34).

## Result
**Table 3 (p. 34), speculative grade, Gamma.** Interaction 2.616 (se 0.918). Investment grade 0.953 (se 0.335). All five measures give a positive, significant interaction in both samples (pp. 15–16).

**The main effect has the opposite sign in speculative grade.** ST debt to total debt: −177.9 to −348.9 across the five measures, each significant at 10% or better (p. 34). Investment grade: positive and mostly insignificant (p. 34). This term sits beside an interaction, inside bond and time effects, so it reads at zero illiquidity. It is not a level regression in the sense of Section 4.7.

**Size at end 2008, Gamma of 330 (p. 16).** The 75th against the 25th percentile of the short-debt ratio gives about 85 bp in investment grade and about 230 bp in speculative grade. Average spreads then were about 475 bp and 1,290 bp (p. 16).

**Subsamples (Table 4, p. 35).** Interaction: pre-crisis 1.741 (se 0.327), crisis 1.524 (se 0.283), banks 1.289 (se 0.476), non-banks 3.090 (se 0.601). So the channel also operates before 2008.

## Limits
- No US or UK firms (p. 8), so no direct US high yield evidence.
- Short sample that ends in June 2009. Only 170 speculative-grade bonds in the main table (p. 34).
- Accounting ratio interpolated to monthly (p. 14). Short-term debt is not a dated maturity ladder.
- Gamma is built from US TRACE bonds and then applied to non-US bonds (p. 25).
- Footnote 1 (p. 5) cites Gopalan et al.: firms with more short-term debt tend to be less risky. So the level term is endogenous.

## Section touched
`docs/methodology.md` Section 4.7 (test of the split), Section 7.2 (liquidity block), Section 9.2 (spread channel).

## Use for the two clocks
This section is our proposal, not the source's claim.

**What the source says.** The rollover effect is an interaction with market illiquidity, in non-US bonds. It is stronger for speculative grade, on 170 bonds and 4,684 bond-months (p. 34). It holds before the crisis as well as in it: 1.741 (se 0.327) and 1.524 (se 0.283) (p. 35).

**What our data says.** Section 4.7 reads a level coefficient. The result on file is +0.36 (t 2.0) on debt due after year 2 and −2.07 (t −2.4) on rent and purchases due after year 2 (Section 4.7, `hy/sources/clock_facts.py` lines 15–17).

**What we decide.** Leave the level coefficient of Section 4.7 unread until Method 2 runs. This source does not regress spread level on a maturity share in a monthly cross-section, so it cannot say what that coefficient means. `chen-xu-yang-2021-systematic-risk-maturity.md` gives a separate selection reason, and selection stays our hypothesis.

Adopt two parts of the design:
1. A market-wide illiquidity series as the state variable. Build it from our TRACE panel with the Gamma method. A card exists: `bao-pan-wang-2011-bond-illiquidity-gamma.md`.
2. An instrument for the share: the issuer's mean share in the years before the test window, so a share chosen in the stress does not enter the test.

**Test.** Add to the panel in `nagler-2020-bond-rollover-channel.md`. Pass: the interaction stays positive when the share is the pre-window issuer mean, in at least three of four cycle windows. Our choice, v0.
