# Support label against support contents (Section 4.7.3)

Date: 2026-11-23. Status: built, report only, not fitted. No market test has run.

## Context
The user states a market claim: the market sorts AI-capacity borrowers by their support. Debt with a big-tech contract weakened least, and debt with no such contract weakened most. The user wants a method that finds where the market has not caught up.

What the sources say: no card on file states or tests this claim. The nearest sources are:
1. Basel slotting grades off-take tenor against debt tenor (card `two-clocks-origin`, Source 2).
2. Morningstar DBRS (2024) says that the essentiality of a data centre to its anchor tenant sets the chance of renewal (same card, Source 3).
3. Radhakrishnan (2026) says that unsecured neocloud debt is a bet on renewal, not on contracted capacity (card `radhakrishnan-2026-ai-buildout-risk`).

Two cards on file describe AI data-centre financing. Neither tests bond spreads against contract terms:
4. Van Nieuwerburgh (2026) describes the Hyperion deal of Meta and Blue Owl (card `van-nieuwerburgh-2026-financing-ai-buildout`).
5. Drehmann and Eren (2026), BIS Bulletin 140, describe who lends and who bears the loss (card `drehmann-eren-2026-building-ai-on-credit`).

What the data says: nothing yet. No panel holds contract terms per issuer.

## Options
1. **Add the label as a fair spread feature.** This copies what the market already does. It cannot find a mis-sort.
2. **Fit spread on the contents score and read the residual.** With 10 to 20 issuers, a fitted curve learns the label, because the label and the score correlate.
3. **Score the contents and compare the ranks of spread and contents.** Flag only the issuers where label and contents disagree. Test whether the gap closes after a dated event. This option needs no fitted curve.

## Choice
Option 3, as Section 4.7.3 states it. Five steps:
1. Score the contents.
2. Test what the market prices.
3. Rank the mis-sort.
4. Name the next catalyst.
5. Test the gap IC with a one-month skip.

Reasons:
1. The product form of `S` puts the weakest-link rule into the arithmetic. A cancellable or unreachable contract counts as zero.
2. Ranks need no fit, and they hold up in a cross-section of 10 to 20 names.
3. The median condition in step 3 keeps the flags to real disagreements. Before that condition, a market that prices the label flagged 21 of 40 synthetic issuers. After it, the market flagged only the 2 planted ones.
4. The one-month skip in step 5 removes the shared-price bias. Before the skip, a market that prices the contents gave a gap IC of -0.07 (t -2.29). After the skip, it gave +0.06 (t +1.53).

Our choice, with no source:
1. Half credit for revenue from a sub-investment-grade customer.
2. Half credit for an unstarted contract.
3. The Basel cut-offs of 1.25x and 0.9x.
4. The mis-sort cut of 0.25 rank.

## Sources disagree: how much does the Hyperion guarantee protect lenders?

**In plain words.** Meta rents the Hyperion data centre four years at a time, but the bonds run to 2049. If Meta leaves at a renewal date, the building is sold. Meta then promises to pay part of any shortfall in the sale price. This promise is the residual value guarantee. Both papers agree that it exists. They disagree on how much it covers.

1. **Van Nieuwerburgh (2026, p. 11) says it covers a lot.** He writes that the guarantee preserves "much of the long-duration credit support" of a conventional long-term lease.
2. **The BIS bulletin (Drehmann and Eren 2026, pp. 5-6) says it covers little.** It calls the protection "limited" for the first 16 years. It also says that such guarantees are "typically capped".

**Why they can both be partly right.** Neither paper gives the amount of the guarantee. So neither can prove its view.
1. If the guarantee pays most of the debt left after a lease ends, Van Nieuwerburgh is right. Then the bond is close to a 20-year Meta lease.
2. If the guarantee has a low cap, the BIS is right. Then the bond depends on whether Meta renews the lease every four years.

**What the price says.** The Hyperion bonds priced at 225 bp over Treasuries. Two weeks later, Meta's own long bonds priced at 88 to 98 bp (BIS, p. 6). Investors asked for about 130 bp more than for Meta itself. That fits the BIS view better: lenders did not treat the bond as Meta debt. One deal is not a test.

**What we decide.** We follow the BIS view for the score, and we give the guarantee no credit in `S` until the filings state its amount. Reasons:
1. Credit for an unknown amount would make `S` too high. A score that is too high hides real risk.
2. The cost is that `S` may be too low for a deal like Hyperion. Then step 3 may flag it as `label_too_tight` in error.
3. So a flag on any issuer with a residual value guarantee of unknown size needs one manual check before it enters a memo. The check: find the guaranteed minimum value in the filing or the rating agency pre-sale report. Then compare it with the debt left at each renewal date.

**The test that settles it.** Find the guaranteed minimum values for Hyperion. If they cover most of the debt at each renewal date, add a guarantee term to `S` and recheck this decision.

## Tests that settle it
1. **Wiring (done):** `tests/test_clocks_support.py` holds 14 tests. `scripts/support_gap.py` passes 6 checks on seed 0. Over seeds 0 to 19, there was one false rejection by the label test (seed 2). That rate is the 5% size of the test.
2. **Inputs:** collect `SUPPORT_COLUMNS` for each issuer from 10-K, 10-Q and S-1 filings, each with `available_at`. Contract exhibits give `non_cancellable` and `reach_share`. Customer concentration notes give `ig_share`. RPO and lease notes give `commenced_share` and the terms. The sample is the AI-capacity issuers that hold HY bonds or loans.
3. **Market:** run `label_test` on the cross-section at the decision time. If `prices_label_only` is false, the market already reads the terms, and the method has nothing to find.
4. **Catch-up:** the gap at the decision time has a negative rank IC on the next six months of spread change, from month 1 to month 7. Most of the change falls within six months of each issuer's catalyst. If the IC is zero, the claim fails.

## Limits
1. The sample has 10 to 20 issuers. That is below `MIN_BONDS = 20`, and the history cannot reach 3 of 4 cycles. So the output is a dated watch list for the memo. It is not a signal for the composite.
2. The score uses terms that the issuer discloses. Side letters and undisclosed amendments stay invisible.
3. The label is binary here. The real label may have tiers, for example a contract with one big-tech customer against a contract with several.
