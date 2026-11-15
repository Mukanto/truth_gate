# CASE B2-04

## 1. Identity
Case id B2-04; world id C34; class B-2; subtype L3.1; source key KAP23.

## 2. Source and documenting passage
KAP23 Section 2.4, L3.1 'Temporal leakage': the model uses 'data from the future' during training; Appendix C: 'the training dataset could contain data from a later date than the test dataset because of being shuffled' under k-fold cross-validation (quotes as returned by the fetch tool in part 1).

Who read it and how: KAP23 (Kapoor and Narayanan 2023). Read by the part-1 brief author (full text through the fetch tool's summary of https://ar5iv.labs.arxiv.org/html/2207.07048; the wording returned by that tool was not verified word for word). I (part 2) did not re-read it: the only URL I fetched, the VAR06 page, returned a reCAPTCHA page.

## 3. The brief (as in ASSIGNMENT.json)
```json
{
  "id": "C34",
  "claim": "A classifier built from the 10 daily indicators predicts whether the series rises over the following day with an accuracy of at least 0.58 on later days.",
  "data_keys": [
    {
      "key": "indicators",
      "shape": "(days, indicators)",
      "dtype": "float",
      "meaning": "10 indicators observed on each day, days in chronological order"
    },
    {
      "key": "rises",
      "shape": "(days,)",
      "dtype": "bool",
      "meaning": "True when the series rises over the day that follows"
    }
  ],
  "sizes": "days = 500; indicators = 10"
}
```

## 4. Mapping
Faulty: ordinary 5-fold cross-validation with rows assigned to folds at random irrespective of time; 15-nearest-neighbour classifier on the standardised indicators; accuracy pooled over the held-out days. Fixed: forward evaluation with the same classifier, the same 5 test blocks and the same accuracy: the series is cut into 6 contiguous blocks, block j (j = 1..5) is scored by a classifier fitted on the blocks before it only; accuracy pooled over the 5 scored blocks. Threshold 0.58.

Estimand line. Faulty: accuracy on days interleaved with the days used to fit (later days included in the fitting data). Fixed: accuracy on days later than all days used to fit (forecasting later days).

Allowed-guard minimum used. Both: at least 2 rows of each class in every fitting set; fixed: a non-empty scored block (None otherwise); non-finite indicators give None.

## 5. Pre-checks of the fixed criterion (plain Python, scratch scripts in work\; the faulty criterion was never run, only syntax-checked)
n = 100 (seed 777000): plus 81, minus 1, control shift_rises_in_time 0, noise 0, zeros None 100. Final, n = 200 (seed 888000): plus 157/200 (0.785), minus 0/200, control 0/200, noise 0/200, zeros 200 None.

Number of revisions of the fixed criterion: 0.

## 6. Timing (final fixed criterion)
t = 0.0011 s (mean of 200 calls on plus samples), g = 0.0011 s (mean plus generation), S = 5 (2 worlds + 1 control(s)/relational pair(s) + 2 probes), estimate 2 x 200 x (S + 1) x (t + g) = 5 s (limit 900 s). No size request needed.

## 7. Deviations, problems, skeleton requests
The k-nearest-neighbour classifier (k = 15) was chosen, among the classifiers the note names (logistic regression or k-NN), because a flexible classifier on autocorrelated indicators is the case in which shuffled folds matter; it was fixed before the first pre-check and not compared with the logistic regression. The fixed criterion's plus rate is 0.785 on 200 samples (0.81 on the first 100), close to the declared power 0.8. The first scored block of the fixed criterion is trained on one sixth of the series (83 days).

Skeleton requests: none.

## Designer lines (PREREG_PHASE_C §3; added by the designer after the fidelity audit)

- Overlap with Phase B: yes, Phase B case B2-09.
- Mechanism tag / statistic family (private note): L3.1 / classification.
- Allowed-guard minimum (private note): at least 1 row in the scored later block (accuracy defined for 1 row); at least 2 rows per class in the fitting block.
- Size ratio (brief size to source size): source states none.
- The estimand line is in item 4 (criterion author).
