# CASE B2-08

## 1. Identity
Case id B2-08; world id C26; class B-2; subtype L1.3; source key VAR06.

## 2. Source and documenting passage
VAR06 Abstract/Results: 'The CV error estimate for the classifier with the optimal parameters was found to be a substantially biased estimate of the true error that the classifier would incur on independent data'; the correction is nested cross-validation. Results: shrunken centroid, null data, mean CV error 37.8% against a true error of 50.0%.

Who read it and how: VAR06 (Varma and Simon 2006, addendum source). Read by the part-1 brief author (full text of https://pmc.ncbi.nlm.nih.gov/articles/PMC1397873/ through the fetch tool's summary). I (part 2) tried the same URL through ctx_fetch_and_index; it returned a reCAPTCHA page, nothing was read, no workaround was tried. The parameters below are the ones in the part-1 private note.

## 3. The brief (as in ASSIGNMENT.json)
```json
{
  "id": "C26",
  "claim": "A shrunken-centroid classifier built from the 1000 gene-expression measurements separates the two tumour classes with an accuracy of at least 0.60 on new samples.",
  "data_keys": [
    {
      "key": "expression",
      "shape": "(samples, genes)",
      "dtype": "float",
      "meaning": "expression level of each gene in each tumour sample"
    },
    {
      "key": "class_b",
      "shape": "(samples,)",
      "dtype": "bool",
      "meaning": "True when the sample belongs to the second tumour class"
    }
  ],
  "sizes": "samples = 40; genes = 1000"
}
```

## 4. Mapping
Faulty: nearest shrunken centroid (Tibshirani et al. form: standardised centroid differences, s0 = median of the gene-wise pooled SD, class priors, soft threshold delta) with delta on a grid of 20 values from 1 down to 0.01; for each delta the stratified 10-fold CV accuracy on all 40 samples; the criterion reports the best CV accuracy over delta (the source's 'CV error of the classifier with the optimal parameter'). Fixed: nested cross-validation: outer stratified 10-fold; in each outer training set an inner stratified 10-fold CV picks delta (ties go to the larger delta); the classifier with that delta predicts the outer held-out samples; accuracy pooled over the outer folds. Threshold 0.60.

Estimand line. Faulty: the maximum CV accuracy over the tuning grid. Fixed: accuracy of the whole tuned procedure on samples not used for tuning or fitting.

Allowed-guard minimum used. Faulty: at least 2 samples of each class in every training fold of the 10-fold structure. Fixed: at least 2 of each class in every training set of the nested 10 x 10 structure (inner training sets included); non-finite expression gives None.

## 5. Pre-checks of the fixed criterion (plain Python, scratch scripts in work\; the faulty criterion was never run, only syntax-checked)
n = 100: plus 100, minus 17, control 28, noise 26, zeros None 100. Final, n = 200: plus 200/200, minus 47/200 (0.235), control 39/200, noise 69/200 (0.345; labels are Bernoulli(0.5), so the classes are often unbalanced and the priors favour the majority), zeros 200 None. Statistic check on 300 minus samples (modified copy of fixed.py returning the accuracy; work\null_stat_check.py): mean 0.496, sd 0.114, P(>= 0.6) = 0.237.

Number of revisions of the fixed criterion: 0.

## 6. Timing (final fixed criterion)
t = 0.0372 s (mean of 200 calls on plus samples), g = 0.0006 s (mean plus generation), S = 5 (2 worlds + 1 control(s)/relational pair(s) + 2 probes), estimate 2 x 200 x (S + 1) x (t + g) = 91 s (limit 900 s). No size request needed.

## 7. Deviations, problems, skeleton requests
Grid, folds and tie rule are my choices within the note ('about 0.01 to 1', for example 20 values; outer 10-fold or LOOCV). Gene count 1000 (the skeleton), not the source's 6000. The fixed criterion holds in minus at 17 to 24% and on the noise probe at 26 to 35%: the claim's threshold 0.60 on 40 samples is loose (chance 13% for a binomial) and nested CV at n = 40 has a larger variance than a binomial (checked on 300 minus samples with a copy of the fixed source that returns the accuracy: mean 0.496, sd 0.114, P(>= 0.6) = 0.24). Recorded, not corrected; the criterion was not bent.

Skeleton requests: none.

## Designer lines (PREREG_PHASE_C §3; added by the designer after the fidelity audit)

- Overlap with Phase B: no (addendum source).
- Mechanism tag / statistic family (private note): L1.3 / classification.
- Allowed-guard minimum (private note): at least 2 samples per class in every fitting set (inner and outer) and at least 1 sample in each scored set.
- Size ratio (brief size to source size): samples 40/40 = 1.0; genes 1000/6000 = 0.17 (reduced to the cap).
- The estimand line is in item 4 (criterion author).
