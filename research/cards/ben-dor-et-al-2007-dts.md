# Ben Dor, Dynkin, Hyman, Houweling, van Leeuwen and Penninga (2007), "DTS (Duration Times Spread)"

The Journal of Portfolio Management, DOI 10.3905/jpm.2007.674795. Peer-reviewed. Corporate bonds, investment grade with Ba and B. We read the SSRN version (`/home/ak/Documents/Quant Credit/ssrn-956825.pdf`, 48 pages), titled "DTS (Duration Times Spread) - A New Measure of Spread Exposure in Credit Portfolios". Page numbers are PDF pages. Authors worked at Lehman Brothers and Robeco, and Lehman held the DTS service mark (p. 1).

## Claim
Spread changes are proportional to the spread level, not parallel (p. 1). Systematic and idiosyncratic spread volatility are linear in spread (pp. 1, 14–16). Excess return volatility is linear in duration times spread (p. 19). So DTS is a better unit of credit exposure than spread duration (p. 29).

## Method
**Return identity (p. 3).**

```latex
R_{spread} = -D\,\Delta s = -D\,s\,\frac{\Delta s}{s} \quad (1, 2)
```

Intuition: DTS is the sensitivity to a relative spread move, as spread duration is the sensitivity to an absolute one.

**Spread change models (pp. 9–10).** Fit by month and sector.

```latex
\Delta s_{i,t} = \alpha_{J,t} + \epsilon \quad (7), \qquad \Delta s_{i,t} = \beta_{J,t}\, s_{i,t} + \epsilon \quad (8), \qquad \Delta s_{i,t} = \alpha_{J,t} + \beta_{J,t}\,(s_{i,t} - \bar{s}_{J,t}) + \epsilon \quad (10)
```

Intuition: if spreads move in proportion, the slope on the spread level explains the moves and the parallel shift adds little.

**Volatility (pp. 12–16).** Partition by sector, duration and spread. Fit `σ(s) = θ s` for systematic moves. Idiosyncratic change is the bond's move less the cell mean (eq. 12, p. 15).

**Forecast test (pp. 20–22).** For 24 sector-quality cells, divide the realised excess return, less carry, by a forecast: D × absolute spread vol, or DTS × relative spread vol. The sd of the result should be 1.

**Low-spread floor (p. 23).**

```latex
\sigma(\Delta s) = \sqrt{\sigma^2_{non\text{-}credit} + \theta^2 s^2} \quad (14)
```

Intuition: at very low spreads, noise sets a floor to volatility.

## Data
Lehman Brothers Credit Index and High Yield Index, September 1989 to January 2005, monthly (p. 8). 565,602 observations with Ba and B bonds (p. 14). 185 months (p. 11).

## Result
- Fit (p. 11): the proportional model gives R² 33% against 16.9% for the parallel model. The slope is significant in 73% of sector-months. Slope and shift correlate 80%.
- Systematic θ: 9.1%, or 9.4% without three outliers, per month (p. 15). The linear relation extends to spreads of 400 bp, with low outcomes in the widest Industrials bucket (p. 14).
- Idiosyncratic θ: 11.5% per month, with a zero intercept (p. 16).
- Excess return volatility on DTS: fit of 98%, slope 8.8%, no intercept (p. 19). Buckets with equal DTS have equal volatility. Example: 54 bp at 5.48 years and 127 bp at 2.53 years (p. 19).
- Stability: yearly slopes have t of 15 to 30. R² above 70% for systematic and 60% for idiosyncratic with high yield in the sample (p. 17).
- Forecast (p. 22): sd of the standardised return is 1.01 for DTS, 1.14 with full-history absolute vol, 0.92 with 36-month absolute vol. Share beyond 2 sd: 4.03% for DTS, 7.06% for absolute (p. 23). Skew: −2.67 for DTS, −1.35 for absolute (p. 23).
- Seniority (pp. 27–28): at equal DTS, the median vol ratio of subordinated to senior is 0.94 across 353 issuers. The median return difference is 1 bp a month.
- Limits on issuers (pp. 29–30): the authors propose a cap on the DTS contribution per issuer. They suggest one threshold for new buys and a higher one for forced sales. They warn that a DTS cap allows large positions in low-spread names.

## Limits
- The sample ends in January 2005, with Ba and B only. It has no CCC and no 2008.
- Relative spread changes are not normal, with strong negative skew (p. 23, p. 29).
- Relative vol rises in 1998 (p. 6). Fit in a crisis is weaker.
- Lehman Brothers held the DTS service mark (p. 1).
- We read the SSRN file. The journal text may differ.

## Section touched
`docs/methodology.md` Section 7.2 and 7.3 (log form, noise scale), Section 8 (composite neutralisation), Section 9.3 (risk measures), and `docs/decisions/2026-10-26-conviction-book.md` (DTS bands).

## Use for the two clocks
This section is our proposal, not the source's claim.

**What the source says.** The right unit is DTS, and relative spread moves are stable across rating, sector and time, for spreads up to 400 bp.

**What our data says.** Section 7.2 fits log spread, and Section 7.3 scores in log terms. The memo uses a DTS hedge ratio `s_i / S` (Section 7.2). The clock tests on file use spread levels by month, not event-time moves. No θ has been fitted on our TRACE panel.

**What we decide.**
1. Express every clock event test in relative form: Δlog s, or Δs over s. This removes the mechanical link between level and move.
2. Use `θ_idio s_i D_i` as the prior for `σ̂(x)` of Section 7.3, with θ fitted on our panel by rating cell. Use 11.5% only as a first value. Our choice, v0.
3. Keep DTS as the unit of the conviction book. Add the two-threshold rule of p. 30 to the jump-to-default cap, as a no-trade band. It lowers forced sales when spreads widen.
4. Do not trust DTS for CCC, or for B in stress, or above 400 bp, until the panel checks it (p. 14). Section 9.2 of the methodology quotes single-B spreads from 335 bp to 1,189 bp in 2020.

**Test.** On the panel: repeat the forecast test of p. 22 by rating cell, and in the four cycle windows. Pass: sd of the standardised return within 0.9 to 1.1 for BB and B in at least three of four windows. Report CCC apart. Our choice, v0.
