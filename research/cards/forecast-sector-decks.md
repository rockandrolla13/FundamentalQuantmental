# Forecast source: sector decks by archetype (framework F2)

Wired: stub. Code: `load_sector_decks` returns [] and logs one line. Variables would be `<sector>:<driver>`.

## Claim
Each archetype has one external driver forecast that moves revenue more than macro does: energy prices (A3), reimbursement rates (A2), housing and autos (A4), AI capex and utilisation (compute infrastructure).

## Coverage, cadence, revision
- A3 energy, EIA Short-Term Energy Outlook: monthly. The October 2026 issue came out 6 October (forecast done 1 October); the next is 10 November 2026. It covers annual values for 2026 and 2027. EIA publishes a month-over-month comparison of the changes. Source: https://www.eia.gov/outlooks/steo/ (accessed 2026-10-22). Public, so it can go live first. Bank price decks are licensed.
- A2 healthcare, CMS IPPS: the FY2027 final rule (CMS-1849-F, fact sheet 31 July 2026) sets a +2.3% payment update (3.2% market basket minus 0.9 pp productivity). It takes effect 1 October 2026. Sources: https://www.cms.gov/newsroom/fact-sheets/fy-2027-hospital-inpatient-prospective-payment-system-long-term-care-hospital-prospective-payment and https://www.cms.gov/medicare/payment/prospective-payment-systems/acute-inpatient-pps (accessed 2026-10-22). The proposed rule date and OPPS timing: not verified. A schedule is a known rate, not a forecast, from the final rule date.
- A4 housing: Fannie Mae Economic and Housing Forecasts, monthly, including housing starts. The page says the views can change without notice. Source: https://www.fanniemae.com/data-and-insights/forecast (accessed 2026-10-22). Auto SAAR forecasts and the accuracy of either: not verified.
- Compute infrastructure: hyperscaler capex guidance in earnings calls. Alphabet raised 2025 capex guidance three times ($75bn, $85bn, $91bn to $93bn); Meta raised the low end from $66bn to $70bn. Source: TrendForce, 30 October 2025, https://www.trendforce.com/news/2025/10/30/news-hyperscalers-ramp-up-capex-amid-ai-boom-risks-lurk-microsoft-meta-alphabet-in-spotlight/ (accessed 2026-10-22). Revisions in 2026 and GPU utilisation forecasts: not verified.

## Known biases
- STEO, 2004 to 2024: price errors are much larger than quantity errors. Oil price forecasts show inertia near recent levels. Gaussian bands understate price spikes. Source: Agovic (2026), "Quantifying Uncertainty in Energy Forecasting", MSc thesis, Chalmers, https://odr.chalmers.se/bitstreams/93a5cc61-7247-4d98-911e-32c30ddb9088/download (accessed 2026-10-22). This is a thesis, not peer reviewed.
- Futures are about the best predictor of oil prices (Chinn, Econbrowser, 12 September 2023, https://econbrowser.com/archives/2023/09/eia-short-term-energy-outlook-oil-price-forecast, accessed 2026-10-22, citing Coibion and Chinn 2014, not opened). EIA's own retrospective: not verified.
- Capex guidance in 2025 moved one way, up. One year is not evidence of a bias.

## Rule when wired
`available_at` = publication date + 1 day, 00:00 (STEO release, CMS rule display date, earnings call date). Method `sector_deck`.

## Decision
Wire STEO first (public, monthly, A3). Prefer the futures strip as the point for oil, per the fallback order (market-implied first), and use STEO as a second source.

Section touched: methodology 5.4
