# Radhakrishnan (2026), "Where the risk actually sits in the AI buildout"

LinkedIn article, 18 October 2026. Practitioner essay, not peer reviewed. Author: former credit markets professional.

## Claim
Neocloud credit risk is a duration mismatch. Lease and debt obligations are long, fixed, and start on dates the provider does not control. Contracted revenue is shorter, starts on customer acceptance, and is concentrated. Unsecured neocloud debt is therefore a bet on renewal, not on contracted capacity.

## Method
Reads 10-Q, 10-K, and S-1 disclosures (CoreWeave, IREN, Oracle, Nvidia, Broadcom, SpaceX/xAI, NScale) and press reports (Anthropic draft S-1 via Reuters). Compares lease commencement and terms with revenue backlog runoff, customer concentration, contract enforceability, vendor backstops, and ring-fenced assets. No model, no charts.

## Data
Filing figures as of the June 2026 quarter (CoreWeave) and the August 2026 quarter (Oracle), plus leaked or reported S-1 terms for the AI labs.

## Result
CoreWeave: $35.5bn of signed, uncommenced leases (2026 to 2029 start, 7 to 16 years); $103.7bn RPO, about 80% recognised within 72 months; top three customers 72% of revenue. Oracle: $288bn of uncommenced leases (15 to 19 years) against customer contracts closer to five years.

## What our data says (hy/clocks.py, scripts/clock_case.py, 22 October 2026)
- Confirmed from XBRL: $35.5bn uncommenced, 7 to 16 year terms, $103.7bn RPO with 41% and 39% windows, top three 72%, $29.1bn undiscounted lease payments, 12-year average remaining term, $288bn Oracle uncommenced at 15 to 19 years.
- Differs: ring-fenced assets are $18.2bn of non-current assets securing SPV debt (10-Q Jun-2026), not $20.8bn. RPO runoff by month 78 is not stated in the 10-Q; the last 20% has no timetable.
- Not checkable from filings: Anthropic, OpenAI, and xAI commitment terms drawn from press reports and draft S-1s.

## Limits
Essay, single author, partly secondary sources. Enforceability claims (cancellation rights, no damages) come from exhibits we have not read. No quantity is offered for the size of the mismatch; Section 4.7 adds one.

## Section touched
`docs/methodology.md` Section 4.7 (new). Decision page `docs/decisions/2026-10-22-duration-mismatch.md`.
