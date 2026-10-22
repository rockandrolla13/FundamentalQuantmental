# Forecast source: management guidance

Wired: stub. Code: `load_management_guidance` returns [] and logs one line. Real source: guidance in 8-K Item 2.02 exhibits and call transcripts (EDGAR is public; structured guidance feeds are licensed).

## Claim
Guidance sets `gap_mgmt`, the distance between the analyst case and the issuer's own forecast. For high yield issuers it is the least reliable source, because distress raises optimism.

## Coverage, cadence, available_at
- An 8-K is due within four business days. Item 2.02 applies when a firm releases non-public results for a completed quarter or year. Item 2.02 and 7.01 content is furnished, not filed, so liability is lighter. A call held within 48 hours after a furnished release needs no separate 8-K. Source: SEC Form 8-K instructions, https://www.sec.gov/files/form8-k.pdf (accessed 2026-10-22).
- Regulation FD: after an unintentional selective disclosure, the firm must disclose publicly no later than 24 hours or the next NYSE open, whichever is later. Source: 17 CFR 243.101, https://www.law.cornell.edu/cfr/text/17/243.101 (accessed 2026-10-22).
- Rule when wired: `available_at` = 8-K acceptance time (EDGAR timestamp, as in hy.sources.edgar), or the call start time when the call comes first.

## Revision policy
Firms update or withdraw guidance at any time, usually at the next earnings release. Each update is a new vintage. There is no rule that forces a firm to update stale guidance (not verified as a general statement).

## Known biases
- Distressed firms issue more optimistic forecasts than healthy firms, where bias is hard to detect. Firms in concentrated industries forecast more pessimistically. The market corrects for expected bias in good-news forecasts at once, but not in bad-news forecasts. Source: Rogers, J., and Stocken, P. (2005), "Credibility of Management Forecasts", The Accounting Review 80(4); working paper https://rodneywhitecenter.wharton.upenn.edu/wp-content/uploads/2014/04/0207.pdf (accessed 2026-10-22).
- Hutton, Miller, and Skinner (2003) and Hirst, Koonce, and Venkataraman (2008): not verified.

## Would fill
`<issuer>:revenue`, `<issuer>:ebitda`, `<issuer>:capex` for the guided period. q10 = low end, q90 = high end, point = midpoint. Method `guidance_range`.

## Decision
Never use guidance as the base case for an issuer near distress. Use it for `gap_mgmt` only. Test: the bias of guidance against realised EBITDA is larger for issuers with leverage above the F3 red threshold.

Section touched: methodology 5.4
