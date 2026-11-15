# CASE B2-03

## 1. Identity
Case id B2-03; world id C21; class B-2; subtype L1.4; source key KAP23.

## 2. Source and documenting passage
KAP23 Section 2.4, over-sampling before the split leaves copies of training rows in the test set (paraphrase returned by the fetch tool in part 1). PB section 1 tie rule: copying rows is L1.4.

Who read it and how: KAP23 (Kapoor and Narayanan 2023). Read by the part-1 brief author (full text through the fetch tool's summary of https://ar5iv.labs.arxiv.org/html/2207.07048; the wording returned by that tool was not verified word for word). I (part 2) did not re-read it: the only URL I fetched, the VAR06 page, returned a reCAPTCHA page.

## 3. The brief (as in ASSIGNMENT.json)
```json
{
  "id": "C21",
  "claim": "A classifier built from the 50 sensor features separates defective units from sound units with a balanced accuracy (mean of sensitivity and specificity) of at least 0.65 on new units.",
  "data_keys": [
    {
      "key": "sensor_features",
      "shape": "(units, sensor_features)",
      "dtype": "float",
      "meaning": "50 features computed from the sensor recording of each unit"
    },
    {
      "key": "defective",
      "shape": "(units,)",
      "dtype": "bool",
      "meaning": "True when the unit is defective"
    }
  ],
  "sizes": "units = 1000; sensor_features = 50"
}
```

## 4. Mapping
Faulty: the smaller class is balanced by copying rows on the whole data, then a stratified 5-fold cross-validation, balanced accuracy (mean of sensitivity and specificity, pooled over the held-out rows, copies included). Fixed: the same oversampling inside each training fold only; balanced accuracy on the untouched held-out original rows. Classifier: ridge-penalised logistic regression (lambda = 1), threshold 0.65.

Estimand line. Faulty: balanced accuracy on held-out rows that include copies of training rows. Fixed: balanced accuracy on original rows not seen in training (new units).

Allowed-guard minimum used. Both: at least 2 rows of each class in every training fold of the 5-fold structure on the original rows (at least 3 per class); non-finite features give None.

## 5. Pre-checks of the fixed criterion (plain Python, scratch scripts in work\; the faulty criterion was never run, only syntax-checked)
Draft 5-NN, n = 60: plus 2/60, minus 0, control 0, noise 0 (and 6/100 plus on a repeat). Revision 1 (logistic), n = 100: plus 100, minus 0, control 0, noise 0. Revision 2 (smaller class oversampled), n = 100: plus 100, minus 0, control 0, noise 0. Final, n = 200 (seed 888000): plus 200/200, minus 0/200, control 0/200, noise 0/200, zeros 200 None.

Number of revisions of the fixed criterion: 2.

## 6. Timing (final fixed criterion)
t = 0.0091 s (mean of 200 calls on plus samples), g = 0.0008 s (mean plus generation), S = 5 (2 worlds + 1 control(s)/relational pair(s) + 2 probes), estimate 2 x 200 x (S + 1) x (t + g) = 24 s (limit 900 s). No size request needed.

## 7. Deviations, problems, skeleton requests
Same two revisions as B2-02. First draft used 5-nearest-neighbour on 50 standardised features; pre-check plus 0.033 (6/100 on a second run), so replaced by the logistic regression (revision 1). Revision 2 (oversample the smaller class whichever it is) was made for parity with B2-02 and changed nothing visible here (noise 0 before and after). As in B2-02 the copies may leak little through a logistic regression.

Skeleton requests: none.

## Designer lines (PREREG_PHASE_C §3; added by the designer after the fidelity audit)

- Overlap with Phase B: yes, Phase B case B2-07.
- Mechanism tag / statistic family (private note): L1.4 / classification.
- Allowed-guard minimum (private note): at least 1 row of each class in the held-out set (balanced accuracy needs both sensitivity and specificity); in each training fold at least 2 rows per class.
- Size ratio (brief size to source size): source states none.
- The estimand line is in item 4 (criterion author).
