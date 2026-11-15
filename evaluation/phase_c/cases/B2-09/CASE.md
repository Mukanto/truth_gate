# CASE B2-09

## 1. Identity
Case id B2-09; world id C32; class B-2; subtype L1.3; source key VAR06.

## 2. Source and documenting passage
VAR06 Abstract/Results: 'The CV error estimate for the classifier with the optimal parameters was found to be a substantially biased estimate of the true error that the classifier would incur on independent data'; the correction is nested cross-validation.

Who read it and how: VAR06 (Varma and Simon 2006, addendum source). Read by the part-1 brief author (full text of https://pmc.ncbi.nlm.nih.gov/articles/PMC1397873/ through the fetch tool's summary). I (part 2) tried the same URL through ctx_fetch_and_index; it returned a reCAPTCHA page, nothing was read, no workaround was tried. The parameters below are the ones in the part-1 private note.

## 3. The brief (as in ASSIGNMENT.json)
```json
{
  "id": "C32",
  "claim": "A shrunken-centroid classifier built from the 1000 gene-expression measurements separates patients who respond to the treatment from those who do not, with an area under the ROC curve of at least 0.65 on new patients.",
  "data_keys": [
    {
      "key": "expression",
      "shape": "(patients, genes)",
      "dtype": "float",
      "meaning": "expression level of each gene in the tumour of each patient"
    },
    {
      "key": "responder",
      "shape": "(patients,)",
      "dtype": "bool",
      "meaning": "True when the patient responds to the treatment"
    }
  ],
  "sizes": "patients = 40; genes = 1000"
}
```

## 4. Mapping
Faulty: the shrunken-centroid classifier of B2-08 (same code); for each delta the AUC of the pooled held-out discriminant scores of a stratified 10-fold CV on all 40 patients; the best AUC over delta is reported. Fixed: nested CV: delta chosen by the inner 10-fold pooled AUC in each outer training set (ties go to the larger delta); the outer held-out scores are pooled and the AUC computed once. Threshold 0.65.

Estimand line. Faulty: the maximum, over the tuning grid, of the CV AUC. Fixed: AUC of the whole tuned procedure on patients not used for tuning or fitting.

Allowed-guard minimum used. Faulty: at least 2 patients of each class in every training fold of the 10-fold structure. Fixed: at least 2 of each class in every training set of the nested 10 x 10 structure; non-finite expression gives None.

## 5. Pre-checks of the fixed criterion (plain Python, scratch scripts in work\; the faulty criterion was never run, only syntax-checked)
n = 100: plus 100, minus 8, control 11, noise 9, zeros None 100. Final, n = 200: plus 200/200, minus 17/200 (0.085), control 15/200, noise 26/200 (0.13), zeros 200 None.

Number of revisions of the fixed criterion: 0.

## 6. Timing (final fixed criterion)
t = 0.0414 s (mean of 200 calls on plus samples), g = 0.0006 s (mean plus generation), S = 5 (2 worlds + 1 control(s)/relational pair(s) + 2 probes), estimate 2 x 200 x (S + 1) x (t + g) = 101 s (limit 900 s). No size request needed.

## 7. Deviations, problems, skeleton requests
Same grid and tie rule as B2-08. The AUC variant is an extension of the source's error-rate estimate (as the part-1 note says). The fixed criterion holds in minus at 8 to 8.5% (above the nominal 5% for a threshold of 0.65 on 40 samples); recorded, not corrected.

Skeleton requests: none.

## Designer lines (PREREG_PHASE_C §3; added by the designer after the fidelity audit)

- Overlap with Phase B: no (addendum source).
- Mechanism tag / statistic family (private note): L1.3 / classification.
- Allowed-guard minimum (private note): at least 1 sample of each class among the scored samples (AUC defined) and at least 2 per class in every fitting set.
- Size ratio (brief size to source size): samples 40/40 = 1.0; genes 1000/6000 = 0.17 (reduced to the cap).
- The estimand line is in item 4 (criterion author).
