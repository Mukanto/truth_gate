# CASE B2-02

## 1. Identity
Case id B2-02; world id C37; class B-2; subtype L1.4; source key KAP23.

## 2. Source and documenting passage
KAP23 Section 2.4, L1.2 text on over-sampling before the split, which leaves copies of training rows in the test set (paraphrase returned by the fetch tool in part 1; wording not verified). PB section 1 tie rule: oversampling by copying rows is L1.4.

Who read it and how: KAP23 (Kapoor and Narayanan 2023). Read by the part-1 brief author (full text through the fetch tool's summary of https://ar5iv.labs.arxiv.org/html/2207.07048; the wording returned by that tool was not verified word for word). I (part 2) did not re-read it: the only URL I fetched, the VAR06 page, returned a reCAPTCHA page.

## 3. The brief (as in ASSIGNMENT.json)
```json
{
  "id": "C37",
  "claim": "A classifier built from the 12 clinical measurements detects at least 60% of the patients who have the less frequent outcome among new patients (sensitivity of at least 0.60).",
  "data_keys": [
    {
      "key": "measurements",
      "shape": "(patients, measurements)",
      "dtype": "float",
      "meaning": "12 clinical measurements of each patient"
    },
    {
      "key": "outcome",
      "shape": "(patients,)",
      "dtype": "bool",
      "meaning": "True when the patient has the less frequent of the two outcomes"
    }
  ],
  "sizes": "patients = 400; measurements = 12"
}
```

## 4. Mapping
Faulty: the smaller class is oversampled by copying randomly drawn rows (with replacement) until the two classes are balanced, on the whole data, and only then is a stratified 5-fold cross-validation run (copies of one row fall in training and held-out folds); sensitivity is pooled over the held-out rows, copies included. Fixed: the same 5-fold structure on the original rows, the same oversampling function applied to each training fold only, sensitivity pooled over the untouched held-out original rows. Classifier: ridge-penalised logistic regression (lambda = 1), threshold 0.60.

Estimand line. Faulty: sensitivity on held-out rows that include copies of rows used for training. Fixed: sensitivity on original rows not seen in training (new patients).

Allowed-guard minimum used. Both: at least 2 rows of each class in every training fold of the 5-fold structure on the original rows (at least 3 per class); non-finite measurements give None.

## 5. Pre-checks of the fixed criterion (plain Python, scratch scripts in work\; the faulty criterion was never run, only syntax-checked)
Draft 5-NN, n = 100: plus 49, minus 1, control 0, noise 10, zeros None 100. Revision 1 (logistic, positive class oversampled), n = 100: plus 100, minus 0, control 1, noise 23. Revision 2 (smaller class oversampled), n = 100: plus 100, minus 0, control 1, noise 0. Final, n = 200 (seed 888000): plus 199/200, minus 0/200, control 0/200, noise 1/200, zeros 200 None.

Number of revisions of the fixed criterion: 2.

## 6. Timing (final fixed criterion)
t = 0.0017 s (mean of 200 calls on plus samples), g = 0.0001 s (mean plus generation), S = 5 (2 worlds + 1 control(s)/relational pair(s) + 2 probes), estimate 2 x 200 x (S + 1) x (t + g) = 4 s (limit 900 s). No size request needed.

## 7. Deviations, problems, skeleton requests
The note suggested a classifier able to use exact copies (1-nearest-neighbour or an unregularised flexible fit). First draft used 5-nearest-neighbour; its pre-check gave plus 0.49 and noise 0.10, so it was replaced by the logistic regression (revision 1). A second pre-check (logistic, oversampling of the positive class only) gave noise 0.23 because with balanced random labels the training set was majority-positive half of the time and the fit then predicted positive too often; oversampling was changed to copy the smaller class whichever it is, as a standard random oversampler does (revision 2). With a logistic regression, exact copies leak little, so the faulty criterion may differ little from the fixed one in these worlds (not tested: the faulty criterion was not run); if so this is 'error too small in the declared worlds at this size'.

Skeleton requests: none.

## Designer lines (PREREG_PHASE_C §3; added by the designer after the fidelity audit)

- Overlap with Phase B: yes, Phase B case B2-07.
- Mechanism tag / statistic family (private note): L1.4 / classification.
- Allowed-guard minimum (private note): at least 1 positive row in the held-out set to define sensitivity (and at least 2 positive rows in the data before oversampling); in each training fold at least 2 rows per class.
- Size ratio (brief size to source size): source states none.
- The estimand line is in item 4 (criterion author).
