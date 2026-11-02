# Rajgopal, Shevlin, Venkatachalam (2003), "Does the Stock Market Fully Appreciate the Implications of Leading Indicators for Future Earnings? Evidence from Order Backlog"

Review of Accounting Studies, author copy at the project root. An agent read it, and we checked one printed number against the text.

## Claim
The stock market overprices backlog.

## Method
`BKLG` is Compustat item 98 over average assets (p. 11). Mishkin test and decile returns.

## Data
21,891 firm-years, 1981 to 1999, mostly small firms.

## Result
- Earnings weight 0.008 against priced weight 0.039 (p. 46).
- Decile rank on return -0.058 (t -2.38) (p. 47).
- Only 7% have backlog above 100% of sales (p. 10).

## Limits
- Stocks only.
- Compustat lacks the share beyond the fiscal year.

## Section touched
Test M1.8.

## Use for the two clocks
**Source says:** backlog can be overpriced. **Data says:** nothing yet. **We decide:** M1.8 gains an overpricing branch, `ob_assets`, and reads the beyond-year share only where `ob_sales` exceeds 1.
