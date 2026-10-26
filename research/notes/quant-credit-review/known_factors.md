# Factors already known to the repo (do not report these as new; DO report a new variant, new definition, new evidence, or HY evidence for them, marked "variant of X")

Book: Ben Dor et al. 2021, Systematic Investing in Credit:
- ESP excess spread to peers (rating x industry x duration peers, net of leverage); SPiDER spread per unit of debt / 10y-avg EBITDA; EMC equity momentum (1,3,6m sqrt-scaled); issuer size; OneScore (ESP+EMC within sector, DTS-neutral legs)
- Fallen angels (forced selling, 3-month reversal rule); FAR reversal score; bond-CDS basis on fallen angels
- Issuance aggressiveness (issuer debt growth; liability growth / assets); market net issuance timing; sector weight dynamics
- New-issue concession; inclusion delay (seasoning); rating stop-loss cost (downgraded bonds beat new rating peers)
- Coupon / price effect (discount bonds convexity); maturity / roll-down; ESG and governance tilt
- Post-earnings drift (EAR, CFE, BAR); equity short interest (ESI)
- Spread-conditioned rating transition matrices; spreads predict defaults 1-2 years
- Credit vs equity+Treasury replication; equity and bond variance risk premia; betting-against-beta in credit

Repo cards:
- Houweling & van Zundert 2017: size, low-risk, value, momentum (bond-only)
- Israel, Palhares, Richardson 2018: carry, defensive, momentum, value
- Correia, Richardson, Tuna 2012: default-probability-implied theoretical spread gap (value)
- Greenwood & Hanson 2013: issuer quality of new issuance (aggregate timing)
- Deutsche Bank: CDS value, low risk, momentum after DTS
- Bharath & Shumway 2008: Merton distance to default
- Gilchrist & Zakrajsek 2012: excess bond premium (EBP)
- Lopez-Salido, Stein, Zakrajsek 2017: credit market sentiment
- Altman Z-score

Repo signals (docs/methodology.md section 8):
- S1 fair value residual (spread vs fundamental fair spread, conformal band)
- S2 fundamental momentum (change in fair spread vs change in market spread)
- S3 estimate revision and consensus gap (forward leverage revisions)
- S4 capital structure relative value (tranche spread gap vs recovery gap)
- S5 document optionality (change-of-control put, liability management exposure)
- S6 rating migration and forced flows (rating gap)
- S7 macro-conditional sector tilt (FAILED its test; replacement wanted)
