# Ciliberto and Schenone (2012), "Bankruptcy and product-market competition: Evidence from the airline industry"

International Journal of Industrial Organization (2012), DOI 10.1016/j.ijindorg.2012.06.004. Peer-reviewed journal article. We read the MPRA working paper 25714, dated August 2010, 52 pages. Page numbers below are PDF pages of that working paper. They may differ from the journal pages, and the journal numbers may differ from the numbers here. Evidence class: product-market outcomes in one industry, US national carriers, quarterly panel, no bond spreads, no credit outcome.

## Claim
A Chapter 11 airline permanently cuts its national routes, its airport networks, and its flight frequency and seats on each route (p. 2). It cuts fares while in court and raises them after it emerges (p. 2). The authors find no robust change by its rivals on any of these measures (p. 2). They read the result as a war of attrition over capacity, in which the weakest carrier files and shrinks (pp. 5-6).

## Method
**Regression (eq. 1, p. 21).**

```latex
\ln Q_{jgt} = \alpha^{OWN} Bkt^{Own}_{gt} + \alpha^{OTH} Bkt^{Others}_{gt} + \beta^{OWN} AftBkt^{Own}_{gt} + \beta^{OTH} AftBkt^{Others}_{gt} + \varepsilon_{jgt} \quad (1)
```

Intuition: compare the filer and the carriers that share its route, before the filing, in court, and after emergence.

`Q` is national network, airport network, frequency, seats, median fare, or load factor (p. 21). `Bkt` is 1 when a carrier in court serves unit `g` at time `t` (p. 16). `AftBkt` is 1 when a carrier that was in court earlier now serves `g` (p. 17). The "after" window runs from emergence to the end of the sample (p. 21).

**Error terms (p. 22).**

```latex
\varepsilon_{jgt} = \gamma\, In_{gt} + u_{jg} + u_t + u_{jgt} + \delta_{o(g)} \cdot o(g)_{gt} \cdot Trend_t + \delta_{d(g)} \cdot d(g)_{gt} \cdot Trend_t, \quad g \in \{r, m\}
```

Intuition: route-carrier effects, quarter effects, and origin and destination trends remove fixed route traits, common shocks such as 9/11, and slow local demand drift.

`In_gt` is 1 when a future or past filer serves `g` at any time (p. 20). It separates the effect of the filing from the effect of the filer's presence. `Trend_t` runs from 1 to 48 (p. 22). At the national level the error is only `u_t + u_jt`, so the national table has no quarter effects (pp. 22-23).

**Percentage effect (p. 23).**

```latex
\tilde{\alpha} = \exp(\hat{\alpha}) - 1
```

Intuition: a dummy coefficient in a log regression is not a percentage until it goes through this transform (Halvorsen and Palmquist).

**Identification checks (pp. 19-21).** The authors drop the two quarters before each filing in the filer's markets, after Ashenfelter (p. 19). A second form adds lags of the bankruptcy dummies for the quarters before the filing (p. 25). Errors are clustered by route, airport, or market (p. 22). A random-effects form tests sample selection (p. 21).

## Data
- Nine national carriers, 1997 to 2007, plus an LCC group (p. 14). Airtran, ATA, and National stay out of the LCC group (p. 14).
- Filers in court in the sample: United, US Airways twice, ATA, Delta, Northwest (p. 15). The filer set has K = 7 and includes National (p. 16).
- Days in court: US Airways 230 and 375, ATA 490, Delta 563, Northwest 611, United 1,513 (Table 1, p. 41).
- Markets: airport pairs among the top 50 metropolitan areas (p. 15). Sources: BTS schedule data, T-100 segment data, and the DB1B 10% ticket sample (p. 14).
- Frequency and seats: 188,610 route-carrier quarters, 7,328 route-carrier groups (Tables 6 and 7, pp. 46-47). Fares: 448,683 market-carrier quarters (Table 8, p. 48). National network: 436 carrier quarters (Table 4, p. 44).
- Means: 446.14 national markets, 18.89 airport markets, 362.29 flights per route quarter, 45,846.46 seats, load factor 0.671, fare $126.19 in 1993 dollars (Table 2, p. 42).

## Result
All numbers are column 1, the main form, unless marked. Brackets give the percentage effect.

**Seats on a route (Table 7, p. 47).** Filer in court -0.351 (se 0.019) [-29.6%]. Filer after emergence -0.426 (se 0.027) [-34.7%]. Rivals in court -0.036 (se 0.017) [-3.5%]. Rivals after -0.059 (se 0.021) [-5.7%]. Without the trends, the rival effects are +0.008 and +0.020 and not significant (column 3).

**Frequency on a route (Table 6, p. 46).** Filer in court -0.242 [-21.5%]. Filer after -0.397 [-32.8%]. Rivals -0.014 (se 0.015) and -0.019 (se 0.019), both not significant. Without quarter effects the filer effects fall to -13.7% and -23.3% (column 4, p. 24).

**Airport network (Table 5, p. 45).** Filer in court -0.302 (se 0.037) [-26.1%]. Filer after -0.270 (se 0.065) [-23.7%]. Rivals in court -0.136 (se 0.027) [-12.7%]. Rivals after +0.080 (se 0.037) [+8.3%].

**National network (Table 4, p. 44).** Filer in court -0.233 (se 0.089) [-20.8%]. Filer after -0.471 (se 0.098) [-37.5%]. Without ATA, the after effect is -0.275 [-24.0%] (column 2). Rivals +0.256 [+29.2%] in court and +0.259 [+29.5%] after. This table has no quarter effects (p. 25). The authors do not confirm the rival result at the airport level (p. 4).

**Fares (Table 8, p. 48).** Filer in court -0.031 (se 0.003) [-3.0%]. Filer after +0.044 (se 0.003) [+4.5%]. Rivals in court -0.005 (se 0.002) [-0.5%]. Rivals after +0.008 (se 0.003) [+0.8%]. Without quarter effects the filer in court is -0.093 [-8.9%] and after is -0.032 [-3.1%] (column 4, pp. 29-30).

**Load factor (Table 9, p. 49).** Filer -0.011 (se 0.004) in court and -0.0141 (se 0.005) after. Rivals +0.029 (se 0.004) in court and +0.036 (se 0.006) after. The dependent variable is the log of the load factor (p. 31). The authors read this as a shift of demand toward the rivals (p. 31).

**Before the filing.** Filer fare lags for one, two, and three quarters before the filing are -0.028, -0.023, and -0.019, all at p < 0.01 (Table 8, column 6, p. 48). The one-quarter lag on seats is -0.044 (se 0.014) (Table 7, column 6, p. 47). The two-quarter lag on the airport network is -0.212 (se 0.026) (Table 5, column 5, p. 45). The authors say the filer starts to change its network before it files (p. 26).

**Costs (Table 10, p. 50).** Cost per seat mile, before, in court, after: United 9.4, 9.8, 10.6 cents. Delta 8.8, 10.9, 11.1 cents. Northwest 9.5, 11.6, 11.0 cents. US Airways second filing 12.5, 11.4, 11.0 cents. The lowest fare, the paper's proxy for marginal cost, shows no fall that lasts (p. 34). The table gives means and standard deviations, not test statistics.

**Law and lessors (p. 12).** Section 1110 gives a 60-day grace period before a lessor can repossess an aircraft. Most lessors renegotiate, because redeployment in a distressed industry can cost more. A rejected lease becomes a general unsecured claim. Repossessions occurred only at small carriers (p. 12, note 14).

## Limits
- No bond prices, no equity prices, and no default outcome. The paper does not measure any credit effect.
- Five named carriers with six filings drive the in-court and after effects (p. 15). The filer set also lists National (p. 16). All six named filings start between 2002 and 2005 (p. 15).
- The "after" window ends with the sample in 2007 (p. 21). Delta and Northwest emerged in 2007 (Table 1, p. 41). So "permanent" rests on very few quarters for two of the six filings.
- US Airways emerged from its second filing through a merger with America West (p. 10). Its after effects mix the merger with the filing.
- The rival dummy averages over all carriers on a shared route (p. 16). The paper does not test rival effects by overlap share or by rival leverage.
- The claim that the filing cuts fixed costs but not marginal costs (p. 31) has no fixed-cost measure behind it. The cost table has no test.
- Source inconsistency: the abstract and p. 4 say fares rise "almost 5 percent" after emergence. Page 29 says 4.4%, and p. 31 says "more than 5 percent". Table 8 gives 0.044 [0.045].
- Source inconsistency: note 30 (p. 24) computes exp(-0.595) - 1 = -44.8%. No coefficient of -0.595 appears in Table 4.
- Source inconsistency: p. 24 says all four national coefficients are "precisely estimated". Table 4, column 5 gives the rival in-court effect 0.186 with se 0.173 and three stars (p. 44).
- Source inconsistency: p. 30 says the random-effects fare result is "essentially identical" to column 1. Table 8, column 5 gives the filer after effect as -0.041, against +0.044 in column 1 (p. 48).
- Source inconsistency: Table 8, column 2 prints [-0.259] for a coefficient of -0.030 (p. 48). Table 6, column 1 prints [0.014] for a coefficient of -0.014 (p. 46).
- Source inconsistency: the rows for the rival after effect carry the label "In-Bankruptcy Effect" in Tables 4 to 8 (pp. 44-48).
- Source inconsistency: p. 15 says six carriers were in court, but it names five. Table 1 dates Delta and Northwest emergence at 4/25/2007 and 5/18/2007. Page 15 gives May 1 and May 31, 2007.
- Source inconsistency: the text on p. 34 gives US Airways first filing at $54.14 and ATA at $49.67 and $51.64. Table 10 gives $52.137 for US Airways. It gives $49.667 and $51.643 for the US Airways second filing, and $57.523 and $61.393 for ATA (p. 50).
- Source inconsistency: the mean fare is $126.46 on p. 18 and $126.19 in Table 2 (p. 42).

## Section touched
`docs/framework.md` F2, the A5 row "Event class to add" and "Downside driver" columns. `docs/framework.md` F11, the "Bankruptcy filing" and "Sector shock" rows. `docs/methodology.md` Section 9.1 (event taxonomy) and Section 4.7.1 (`peer_shock`). `hy/events.py` `EventType.BANKRUPTCY` and `OUTCOMES`.

**How it adds to the two airline cards.** `gavazza-2010-asset-liquidity-aircraft-leases` gives the law of Section 1110 and the lease forms. This paper shows what a filer does with that law: it sheds about 30% of seats on the routes it keeps (Table 7, p. 47). Lessors mostly renegotiate (p. 12), which fits the Gavazza point that a lessor with an illiquid asset avoids repossession. `benmelech-bergman-2011-collateral-channel` shows that a peer filing widens secured tranches on shared aircraft types for a time. This paper shows that the product-market channel to rivals is close to zero. So the rival effect that the repo can source runs through collateral, not through demand or fares.

## Use for the A5 archetype
**What the source says.** A filer shrinks by 21% to 35% on its retained routes and networks, and the cut holds after emergence (Tables 5 to 7, pp. 45-47). Its fares fall 3.0% in court and rise 4.5% after emergence (Table 8, p. 48). Rivals do not change seats, frequency, or fares by an economic amount (Tables 6 to 8). Rival load factors rise by about 3 log points (Table 9, p. 49). The filer cuts fares and capacity in the quarters before it files (Tables 5, 7, 8).

**What the data says.** The A5 row lists "Contract renewals; asset appraisal dates" as event classes and "Contract roll-off and churn; asset value cycle" as the downside driver (`docs/framework.md` line 40). Neither item cites a source. `hy/events.py` has `EventType.BANKRUPTCY` with one outcome, `("filed",)`, and `EventType.SECTOR_SHOCK` with one outcome, `("path",)`. No event type exists for a peer filing. The F11 bankruptcy row covers only the bonds of the filer. `hy/clocks.py` `peer_shock` carries the collateral channel of Benmelech and Bergman. Nothing in the repo models a rival effect through the product market. `docs/factors/SECTOR-models.md` 3.1 gives airlines no group of their own. Airlines fall in GICS 20 `industrials`, which carries the A4 frame. The A5 frame appears only under `telecom_media`.

**What we decide (our proposal, not the source's claim).**
1. Add "Peer Chapter 11 filing" to the A5 event class column for airlines. Split its outcome into two channels: `collateral` and `product_market`.
2. For the bond of a rival, set the `product_market` channel to zero in every case of F6. Do not book a competitive benefit, and do not book a demand contagion. Keep the `collateral` channel for secured tranches on shared types through `peer_shock`. This source gives no basis to move rival unsecured bonds.
3. For the bond of the filer, build the claims view on a smaller carrier. Scale going-concern revenue and fleet by the seat cut of Table 7, about -35%, as a default under R9. Size the rejected aircraft and gate leases as claims under F5.
4. Add a pre-filing flag for A5 airlines. Set it when the carrier cuts fares and seats against peers on shared routes for two quarters in a row. Treat it as a hazard input, not as a signal.

```latex
\text{rival\_jump}_{i,e} = \Delta s_{i,[-5,+5]} = a + b \cdot \text{overlap}_{i,e} + c \cdot \text{secured}_i + d \cdot \text{peer\_shock}_{i,e} + u_{i,e}
```

Intuition: if a peer filing helps or hurts a rival through its routes, the rival spread move scales with the share of the rival's seats on the filer's routes.

5. Test. Take every US airline Chapter 11 filing with TRACE coverage. For each rival bond, compute the spread change over the event window and over the next four quarters. `overlap` is the rival's seat share on routes that the filer serves. The rule in item 2 holds when `b` is not different from zero at the 5% level in both windows. It fails when `b < 0` (competitive benefit) or `b > 0` (contagion through routes). Run the test with the overlap measured before the filing, so that no field has `available_at` after the event date.
