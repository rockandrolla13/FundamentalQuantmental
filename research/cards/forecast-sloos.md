# Forecast source: Senior Loan Officer Opinion Survey (SLOOS)

Wired: live. Code: `hy/sources/forecast_sources.py`, `load_sloos`. Registry source `sloos`, variable `sloos_tightening`, horizon 0.

## Claim
The net share of banks that tighten C&I standards for large and middle-market firms leads credit spreads and output. It is a phase indicator in framework F6: late cycle when net tightening is positive for two quarters.

## Coverage
- Panel: up to 80 large domestic banks and 24 US branches and agencies of foreign banks. Source: https://www.federalreserve.gov/data/sloos.htm (accessed 2026-10-22).
- Series `SUBLPDCILS_N.Q`: net percentage of domestic banks that tighten standards for C&I loans to large and middle-market firms, 1990 onward, from the Data Download Program file `Output.aspx?rel=SLOOS&filetype=zip`.
- Net percentage = share that tightened (considerably or somewhat) minus share that eased. Source: July 2026 survey, https://www.federalreserve.gov/data/sloos/sloos-202607.htm (accessed 2026-10-22). 56 domestic banks and 18 foreign branches replied; the survey went out 17 June and responses were due 2 July 2026.

## Cadence and available_at
- Quarterly, timed to FOMC meetings, with one or two extra surveys in some years (landing page).
- The DDP labels a survey by the quarter of its survey month: the July 2026 survey has the label 2026-09-30.
- `vintage` = first day of the label quarter. `available_at` = release date + 1 day, 00:00, when known. The SLOOS landing page "Last Update" stamp gives the date of the latest release (3 August 2026). For older surveys the rule is day 1 of the third month of the quarter. This is late by up to four weeks and never early.

## Revision policy
Not verified. No page we opened states one.

## Known biases
- Bank-level SLOOS answers, 1991 Q3 to 2012 Q3, with loan-demand factors removed: a tightening shock lowers bank borrowing capacity by about 4%, lowers GDP, and widens corporate credit spreads. The adjusted indicator explains about 20% of output variance. The raw net percentage gives implausibly large shares (above 50% of spread variance), because demand factors contaminate it. Source: Bassett, W., Chosak, M., Driscoll, J., and Zakrajsek, E. (2014), "Changes in Bank Lending Standards and the Macroeconomy", Journal of Monetary Economics; FEDS 2012-24, https://www.federalreserve.gov/pubs/feds/2012/201224/201224pap.pdf (accessed 2026-10-22).
- Lown and Morgan (2006): not verified.

## Data (smoke run, decision time 2026-10-21)
Latest value 0.0 (July 2026 survey). Previous: 8.1 (April 2026), 5.3 (January 2026). The registry holds 146 rows.

## Limits
- We use the raw net percentage. Bassett et al. say it mixes supply and demand. A demand adjustment needs the bank-level data, which is not public.
- The Fed will remove the DDP "Build Your Package" feature in the week of 9 November and later retire the DDP (landing page notice). The full-release zip may also go. The fallback is the release page tables.

## Decision
Use the raw series for the F6 phase vote only, where only the sign and the persistence matter. Do not use its level in a regression on spreads until a demand adjustment exists.

Section touched: methodology 5.4
