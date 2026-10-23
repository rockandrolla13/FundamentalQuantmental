# Leverage: one definition per use

Date: 23 October 2026. Code: `hy/state.py` (`issuer_leverage`, `issuer_net_leverage`), `scripts/process.py` (`book_block`), `scripts/rv_pair.py` (`issuer_block`). Tests: `tests/test_state.py`. Review finding AR-DRY-001. Data module, migration step 5b. User decision, 23 October 2026.

## Context
Three leverage measures counted debt three ways:

| Measure | Debt counted | MGM, 18 Sep 2026 | Used by |
|---|---|---|---|
| Step 5 `lev_gross` | Filed debt only, over EBITDA | 2.52x | Kricheff ratios, E13 trap guard, spread per turn |
| Lease-adjusted | Filed debt + lease liabilities, over EBITDA + rent | 6.38x | Pair, gate, issuer risk |
| Compustat panel | Compustat debt over Compustat LTM EBITDA | 14.25x | Peer cells, ESP, SPiDER |

MGM's Compustat debt ($31.7bn) is close to its filed debt ($6.1bn) plus its lease liabilities ($24.1bn, mostly the VICI leases). So Compustat counts some lease liabilities as debt. The measures differ in meaning, not by error.

## Options
1. One per use, named: issuer leverage from filings, lease-adjusted, for every issuer-level use; peer leverage from the Compustat panel, for peer cells only. Chosen by the user.
2. Lease-adjusted everywhere. Peers would mix filings (live issuers) and Compustat (panel).
3. Compustat everywhere. Compustat counts leases for some issuers and not others, and lags up to a quarter.

## Choice
- **Issuer leverage** = (debt + lease liabilities) / (EBITDA + rent), from the issuer's filings. One home: `hy.state.issuer_leverage`. The Kricheff ratio set (`lev_gross`, `lev_net`), the E13 trap guard, spread per turn, the pair and the gate read it. Kricheff's own debt already counts capital leases (ch. 10, p. 50).
- **Peer leverage** = the Compustat panel's `leverage` column, only for placing issuers in peer cells, because every peer must come from the same source.
- The two must never be mixed in one comparison.

## What the data says (8-issuer run)
1. Leverage moves for the three issuers with lease data: MGM 2.52x to 6.38x, ORCL 3.70x to 4.30x, CRWV 9.45x to 8.94x. Net leverage moves the same way (MGM 1.36x to 5.79x).
2. E13 does not move: every issuer takes its E13 from its peer cell. MGM's new leverage gives one trap-guard warning sign (high leverage); the guard needs two.
3. No rank, verdict or combined score changes. The backtest summaries do not change.
4. Six of eight issuers report lease liabilities of 0. HCA and WYNN surely have leases, so the lease tags are missing and their issuer leverage is understated. This is the next fix.

## Test that settles it
`tests/test_state.py::test_issuer_leverage_is_lease_adjusted` (MGM by hand) and `test_issuer_analysis_uses_issuer_leverage` (the ratio set reads the one function). Golden snapshot retaken after this change.
