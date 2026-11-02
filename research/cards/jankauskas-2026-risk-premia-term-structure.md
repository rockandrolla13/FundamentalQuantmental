# Jankauskas (2026), "Estimating the Term Structure of Corporate Bond Risk Premia"

Liberty Street Economics, Federal Reserve Bank of New York, 24 February 2026, DOI 10.59576/lse.20260224. Blog post by the author. Corporate bonds, US. **This card covers the post only.** The paper it summarises, "The Term Structure of Corporate Bond Risk Premia" (DOI 10.2139/ssrn.6068187, cited in the post as Jankauskas 2024), was not opened. So the methods and tables of the paper are unknown to us. The thesis copy on the Tilburg portal is behind a browser check, and we did not pass it. The post is an HTML page with no page numbers, so we cite its section headings.

## Claim
A forward-looking risk premium, equal to the corporate yield less the maturity-matched risk-free rate and expected default loss, slopes up with duration ("The Slope of the Risk Premia Term Structure"). It is near 0 for bonds of 1 to 2 years, peaks at about 1.8% at 4 to 6 years, and levels off near 1.5% at 12 years and longer (same section).

## Method
**Decomposition ("Extracting Risk Premia from Yields").**

```latex
y_{i,\tau} = r^{f}_{\tau} + EL_{i,\tau} + RP_{i,\tau}
```

Intuition: take the yield as the promised return, remove the risk-free part and the expected default loss, and the rest is the premium. This needs no past returns, which the author says a few recessions, rate shifts and premium changes can bias.

Expected loss comes from a structural default model after Feldhütter and Schaefer (2018), with historical loss given default (same section).

**Portfolios ("Duration Varies Substantially Across Corporate Bonds").** Sort bonds on Macaulay duration each June into ten deciles, and hold each for a year. Bonds under 1 year or over 30 years are excluded.

## Data
TRACE, 2002 to 2020 (chart and table notes). The post gives the US corporate market at roughly $16 trillion at the end of 2024 (first paragraph).

## Result
Average duration by decile (table in "Duration Varies..."): 1.3, 2.4, 3.4, 4.2, 5.1, 6.0, 7.1, 8.8, 11.5, 14.1. High less low: 12.7.

From "The Slope of the Risk Premia Term Structure":
- Total expected returns slope up, with a term premium of roughly 3.4%. The risk-free slope gives 2.1%. The risk premium slope gives 1.3%.
- The risk premium is up to 20% of long-term yields, and up to 30% of total expected return.
- Credit spreads are somewhat hump-shaped. The sum of risk premium and credit loss bars shows this.
- The author ties the non-linearity to the fact that most long-term bonds come from the safest issuers.

## Limits
- A blog summary. Standard errors, rating cuts and sample filters are not in the post.
- No high yield result in the post. The hump may reflect issuer mix across tenors, as the author says.
- Rests on one structural default model. A different expected loss changes the premium directly.
- Ex-ante premium, not a realised return. No cost and no trade rule.
- Ends in 2020. Misses 2022.

## Section touched
`docs/methodology.md` Section 7.1 (expected loss spread), Section 7.7 (risk premium test), Section 8 S4 (curve position), and `docs/factors/F22` (curve shape), by name only.

## Use for the two clocks
This section is our proposal, not the source's claim.

**What the source says.** The premium is small at the short end. It is largest at intermediate duration, and it does not rise further at long duration.

**What our data says.** No result on our panel. Our arithmetic from the post: premium per year of duration is about 0.36 at 5 years (1.8 / 5) and about 0.11 at 14 years (1.5 / 14.1). This is not a claim of the source.

**What we decide.**
1. Build `rp_tenor`: our Section 7.1 `s_el` gives EL, and spread less `s_el` gives RP, by rating and tenor bucket. Report it in the memo as a guide to which tenor pays.
2. Keep the short-tenor signal of `houweling-van-zundert-2017-factor-investing-corporate-bonds.md` beside it. That card finds short bonds pay more per unit of risk. Our arithmetic above agrees in direction. A premium level that rises and a premium per unit of risk that falls can both hold.
3. Use the shape to size the debt clock. A bond due in 1 to 2 years has a premium near zero in the aggregate, so a clock long at the short end earns little carry for refinancing risk. This reading needs a high yield test.

**Test.** On the panel: mean `rp_tenor` by rating and tenor bucket, by cycle window, and the realised 12-month excess return per unit of DTS for the same buckets. Pass: the ranks of the two tables agree in at least three of four windows. Otherwise do not use `rp_tenor` to pick tenor. Our choice, v0.
