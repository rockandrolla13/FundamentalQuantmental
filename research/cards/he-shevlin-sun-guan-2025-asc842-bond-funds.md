# He, Shevlin, Sun, and Guan (2025 draft), "Accounting for Leases and Portfolio Decisions of Active Corporate Bond Funds"

Working paper, DOI of the SSRN record 10.2139/ssrn.5373290. **Not peer reviewed in the copy we read.** We read the file dated July 2025 from the Columbia Accounting Design Project page (59 pages). Page numbers are PDF pages. PDF page = printed page + 1. Evidence class: US corporate bond holdings, with a high yield fund split. No spread regression.

**Added at the audit close.** The screen graded this paper 2, and the cap dropped it. A search for Jung and Scarlat (2024) found this draft.

## Claim
After ASC 842 starts, active bond funds cut their holdings of bonds from issuers with large recognized operating leases (p. 1). The effect sits in high yield funds (p. 24). Funds that hold more exposed issuers perform better after the standard (p. 1).

## Method
**Difference in differences (p. 16, eq. 1).** The unit is the fund, bond, and month, in a six-month window around adoption.

```latex
Holding\_Pct_{j,i,t} = \beta_0 + \beta_1\,Post_{i,t} \times Large\_ROUA_i + \sum_k \varphi_k Controls + \gamma_i + \mu_j + \eta_y + \delta_t + \epsilon_{i,t}
```

Intuition: compare holdings of bonds from lease-heavy issuers with holdings of other bonds, in the same fund, around the month that the issuer first reports under the new standard. Month 0 is the first holding report after the first 10-K under ASC 842, read from the Compustat field `ACCTCHG` = `ASU16-02` (p. 16). `Large_ROUA` marks issuers above the median first recognized right-of-use asset (p. 19).

## Data
Morningstar monthly holdings. 92,346 fund, bond, and month rows. 289 funds, 2,493 bonds, 409 firms (pp. 15-16). On average the bonds are investment grade (p. 19).

## Result
- **Baseline (Table 3, p. 47).** `Post` x `Large_ROUA` is -0.009 (t -3.15) with no controls and -0.008 (t -2.72) with controls. The authors state 4.7% of the sample mean (p. 19).
- **High yield funds (Table 5 Panel A, p. 51).** The triple interaction is -0.026 (t -2.59) and -0.027 (t -2.70). The plain interaction is -0.002 (t -0.75 and t -0.65). So the effect sits in high yield funds (p. 24).
- **Pre-trends.** The authors report no significant pre-period trend (p. 4).
- **COVID control (Table 8 Panel A, p. 57).** -0.008 (t -2.47).
- **Second-hand result.** The authors report that Jung and Scarlat (2024) find higher bond yields after adoption (p. 3). We did not open that paper, so this is second hand and supports no claim here.

## Limits
- This is a holdings result. It shows no price effect.
- The window around the first 10-K can sit in early 2020 for December year ends, close to the COVID shock. The authors add a control.
- `Large_ROUA` is an unscaled amount, so it leans to large issuers (p. 19).
- Draft. Peer review unknown.

## Section touched
`docs/methodology.md` Section 4.7. `docs/decisions/2026-11-01-clocks-residual-timing.md` Method 1, test M1.7.

## Use for the two clocks
**What the source says.** ASC 842 is a dated event for bond investors, and high yield funds respond to it.

**What our data says.** `hy/sources/schedules.py` reads lease ladders only under ASC 842 tags. So `e5` and `fixed_charge_years` step up at adoption for lease-heavy issuers, with no change in the economics. The step has no count on file.

**What we decide (our proposal, not the source's claim).**
1. Add `lease_regime` to the cost clock, and date it from the first ASC 842 filing or from `ACCTCHG`.
2. Use the adoption date in M1.7, because it needs no RPO and it has a date. Take the first 10-Q under ASC 842 as the primary date for December year ends, because that date comes in 2019 and avoids the COVID window (Our choice, v0).

**Test.** M1.7.
