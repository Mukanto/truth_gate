# CASE B2-07

## 1. Identity
Case id B2-07; world id C42; class B-2; subtype L3.2; source key KAP23.

## 2. Source and documenting passage
KAP23 Section 2.4, L3.2 'Nonindependence between train and test': the same people or units appear in both sets; suggested fix block cross-validation (Roberts et al. 2017; Valavi et al. 2021) (as returned by the fetch tool in part 1; wording not verified).

Who read it and how: KAP23 (Kapoor and Narayanan 2023). Read by the part-1 brief author (full text through the fetch tool's summary of https://ar5iv.labs.arxiv.org/html/2207.07048; the wording returned by that tool was not verified word for word). I (part 2) did not re-read it: the only URL I fetched, the VAR06 page, returned a reCAPTCHA page.

## 3. The brief (as in ASSIGNMENT.json)
```json
{
  "id": "C42",
  "claim": "A regression on the 10 session measurements predicts a participant's score in a session, with a Pearson correlation of at least 0.30 between predicted and observed scores for new participants.",
  "data_keys": [
    {
      "key": "measurements",
      "shape": "(participants, sessions, measurements)",
      "dtype": "float",
      "meaning": "10 measurements recorded in each session of each participant"
    },
    {
      "key": "score",
      "shape": "(participants, sessions)",
      "dtype": "float",
      "meaning": "score of the participant in that session"
    }
  ],
  "sizes": "participants = 40; sessions = 4; measurements = 10"
}
```

## 4. Mapping
Faulty: sessions are pooled into rows (participants x sessions, 10 measurements), 5-fold cross-validation with random assignment of rows, ordinary least squares (standardised inputs); Pearson correlation between predicted and observed scores over the pooled held-out rows. Fixed: the same pipeline with participants assigned to folds, so that all sessions of a participant stay in one fold. Threshold r >= 0.30.

Estimand line. Faulty: correlation of predicted and observed scores on sessions of participants who also have sessions in the fitting data. Fixed: correlation on sessions of participants absent from the fitting data.

Allowed-guard minimum used. Both: at least 2 participants, at least 3 pooled scored rows, non-zero variance of predictions and of scores, finite values (None otherwise).

## 5. Pre-checks of the fixed criterion (plain Python, scratch scripts in work\; the faulty criterion was never run, only syntax-checked)
n = 100: plus 98, minus 4, control 0, noise 0, zeros None 100. Final, n = 200: plus 200/200, minus 2/200 (0.010), control 2/200, noise 0/200, zeros 200 None.

Number of revisions of the fixed criterion: 0.

## 6. Timing (final fixed criterion)
t = 0.0005 s (mean of 200 calls on plus samples), g = 0.0001 s (mean plus generation), S = 5 (2 worlds + 1 control(s)/relational pair(s) + 2 probes), estimate 2 x 200 x (S + 1) x (t + g) = 1 s (limit 900 s). No size request needed.

## 7. Deviations, problems, skeleton requests
Ordinary least squares is a low-capacity model, so leakage through the participant's stable measurements is limited; the faulty criterion may be close to the fixed one in the declared worlds (not tested). The fixed criterion held in minus at 1.0 to 4.0% over two pre-checks.

Skeleton requests: none.

## Designer lines (PREREG_PHASE_C §3; added by the designer after the fidelity audit)

- Overlap with Phase B: no.
- Mechanism tag / statistic family (private note): L3.2 / correlation.
- Allowed-guard minimum (private note): at least 3 held-out rows (smallest size for a correlation) with non-zero variance of predictions and of scores.
- Size ratio (brief size to source size): source states none.
- The estimand line is in item 4 (criterion author).
