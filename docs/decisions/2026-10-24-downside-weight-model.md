# Downside-weight model: issuer term, year term, new macro inputs

Date: 2026-10-24. Status: proposed, not fitted. Methodology section: 5.2.1.

## Context
Section 5.2 sets the downside-case weight with a pooled logistic on the macro vector and the sector. It has no issuer term. So it gives every issuer in one sector on one date the same weight, unless the thresholds differ. No source backed the specification. The research sprints of 2026-10-23 and 2026-10-24 read the sources whose cards Section 5.2.1 lists.

## Options
1. Keep the current model: macro and sector only.
2. Add an issuer term only.
3. Add an issuer term, a year random intercept, and replace the macro inputs with the ones the literature supports.

## Choice
Option 3, proposed. Three papers agree that issuer state ranks issuers and macro sets the level. One paper shows a latent year factor of about 43% a year. Two papers show the raw spread level is a weak input. The model stays unfitted until tests T1 to T6 of Section 5.2.1 run.

Disagreement recorded: Elkamhi and Lee fix macro signs by theory. Duffie-Saita-Wang and Jacobson et al. show that the short-rate sign flips with the other controls. We fit without sign constraints and test sign stability (T5).

## Test that settles it
Tests T1 to T6 in Section 5.2.1, out of sample in the 2008, 2015, 2020 and 2022 windows. T1 decides the issuer term. T2 decides the year term. T3 and T4 decide each macro input.

Added after the Figlewski, Frydman and Liang card: a rating-history flag in the issuer term, a second event (downgrade into CCC), and test T7 on the macro slope for CCC issuers.

## Open
- Five default cards use working-paper versions, Figlewski et al. included. The journal numbers may differ.
- Vassalou (2003) changes nothing here. A bond-based GDP-news factor would repeat the `hy_oas` change.
