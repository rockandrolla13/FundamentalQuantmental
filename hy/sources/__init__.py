"""Data sources that feed the input layer (methodology Section 3).

- `compustat_pit`: Compustat point-in-time quarterly vintages from WRDS.
- `edgar`: SEC EDGAR filing index with acceptance timestamps.
- `financials`: joins the two into `IssuerFinancials` records with `available_at`.

Raw vendor pulls are cached under `data/raw/`, which git ignores.
"""
