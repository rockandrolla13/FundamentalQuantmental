# Almeida, Hankins and Williams (2017), "Risk Management with Supply Contracts"

The Review of Financial Studies (2017), DOI 10.1093/rfs/hhx051. Peer-reviewed journal article. We read NBER Working Paper 23331, April 2017, 59 pages. We did not open the journal version, so its numbers may differ. Page numbers below are PDF pages. PDF page = printed page + 2. Evidence class: firm level, hedge and contract choice, no bond spreads.

## Claim
Purchase obligations are forward contracts with suppliers, and firms use them as a risk management tool (p. 2). Firms with a steel exposure substitute futures for purchase obligations after steel futures start (p. 2). Purchase obligations are non-cancelable contracts for materials or services, generally over one to three years, and most use fixed prices (p. 3).

## Method
1. Data collection. Perl search of the contractual obligations table in each 10-K, 2003 to 2010 (pp. 10-11). `Purchase Obligation` is an indicator. Amounts for the next five years are scaled by assets or COGS (p. 11).
2. Natural experiment. Steel futures start on the London Metal Exchange in April 2008 and on the Chicago Mercantile Exchange in August 2008 (p. 18). A firm has steel exposure when steel exceeds 1% of inputs in the input-output tables (p. 19).

```latex
\frac{AggPO_{i,t}}{Assets_{i,t}} = a_i + b_t + c\,(FuturesAvail_t \times SteelExposure_i) + d X_{i,t-1} + e_{i,t}
```

Intuition: a new futures market lowers the demand for supply contracts only if those contracts already serve as hedges.

3. Falsification. A placebo group of industries with no steel exposure, and a placebo date in 2006 to 2007 (p. 22). A nearest neighbour match gives the third check (p. 23).
4. Cross-section. Splits on collateral, bargaining power, settlement risk and hold-up (pp. 24-26).
5. Settlement risk proxy. `Long PO Contract` is 1 when the firm has obligations for three or more years (p. 14). The authors assert that longer contracts correspond to lower perceived risk (pp. 13-14).

## Data
- Non-financial Compustat firms with a 10-K on EDGAR, 2003 to 2010, 26,430 firm-years (p. 10).
- 21.5% of firm-years report purchase obligations, and 15.8% use commodity derivatives (p. 3).
- Users average 11.8% of assets and 21.4% of COGS in total obligations (p. 4).
- Average contract length is 2.49 years, median 3 years (p. 4).

## Result
**Term structure (p. 11).** The average user commits to 12% of COGS in year t+1, 7% in t+2, 5% in t+3, and less than 1% later.

**Firm profile (Table 1, p. 46).** Means for users against all firms: market leverage 0.180 against 0.193, cash 0.148 against 0.153, log assets 6.578 against 5.744. The authors say that users are "more similar to the median firm" than derivative users are (p. 6).

**Who uses them (Table 3 Panel B, p. 50).** In the logit with controls, leverage is -1.090 (t -2.49), firm size is 0.270 (t 13.94), and traded inputs are -1.684 (t -3.62). High ROA is 0.542 (t 9.03) without controls and 0.092 (t 1.42) with controls.

**Experiment (Table 5, p. 52).** The interaction on aggregate obligations over assets is -0.030 (t -3.10) with no controls and -0.027 (t -2.48) with full controls. Against a user mean of 11.8%, the authors call this highly significant (p. 21).

**Placebos (Table 6, p. 53).** The placebo exposure coefficient is 0.030 (t 0.61). The placebo date coefficient is 0.006 (t 0.61), and -0.007 (t -0.90) with 2008 onward out.

**Match (Table 7, p. 54).** The effect on the treated is -0.012 (z -1.92, p 0.055).

**Settlement (pp. 8-9).** The treatment of supply contracts in bankruptcy varies by court. The text quotes SunEdison, which told vendors it would no longer fulfil long-term supply contracts and expected some litigation.

## Limits
- The test is on hedge choice. It says nothing on spreads or defaults.
- One shock in one input. Steel exposure comes from 2002 industry tables, not from firm data.
- The match result is significant only at the 10% level.
- Hold-up contracts do not respond (pp. 25-26). So not every purchase obligation is a hedge.
- The sample ends in 2010.
- Source inconsistency: contract length is 2.49 years on p. 4 and 2.6 years on p. 14.

## Section touched
`docs/methodology.md` Section 4.7 (purchase commitments, `breakeven_margin`, `coverage_contracted`) and Section 9 (hedge treatment in a downside). `hy/clocks.py`.

## Use for the two clocks
**What the source says.** A fixed-price purchase commitment is a long position in an input. It hedges cost. It sits in a firm's risk management set beside futures and cash (p. 7).

**What the data says.** `clocks.mismatch` adds purchases to `O_t` at face, the same as debt principal. Section 4.7 records that the share holding purchases and rent took the wrong sign (-2.07, t -2.4). The repo holds no split of the two.

**What we decide (our proposal, not the source's claim).**
1. Do not count a purchase commitment as a fixed charge at face. Its cost is partly matched by the input it delivers. Replace it with the excess over what a downturn can absorb.

```latex
X_{i,t}(d) = \max\big(0,\ PO_{i,t} - (1-d)\,COGS_{i,0}\big), \qquad d = 0.30 \ \text{(Our choice, v0)}
```

Intuition: a commitment hurts only when the firm must take more input than its reduced sales can use.

2. Expect `X` to be 0 for most issuers, because the user mean is 12% of COGS in year one. It stays large for capacity buyers whose commitments exceed COGS. That is the case the clocks exist for.
3. Add `X` to the cost clock in the place of the face amount. Keep the face amount as a memo field.
4. Test. Refit the split regression with `X` in the place of the purchase ladder. The hedge reading passes when the coefficient on `X` is above 0 and the coefficient on the face amount, added beside it, is not above 0.
