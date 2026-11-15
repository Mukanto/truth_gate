# CASE B2-11

## 1. Identity
Case id B2-11; world id C01; class B-2; subtype L1.3; source key VAR06.

## 2. Source and documenting passage
VAR06 Abstract: the CV error estimate for the classifier with the optimal parameters is a substantially biased estimate of the true error on independent data; 'model selection' in the title, correction nested cross-validation. Reading fixed in SOURCES_ADDENDUM: selection on the data of the error estimate, of features or classifier parameters.

Who read it and how: VAR06 (Varma and Simon 2006, addendum source). Read by the part-1 brief author (full text of https://pmc.ncbi.nlm.nih.gov/articles/PMC1397873/ through the fetch tool's summary). I (part 2) tried the same URL through ctx_fetch_and_index; it returned a reCAPTCHA page, nothing was read, no workaround was tried. The parameters below are the ones in the part-1 private note.

## 3. The brief (as in ASSIGNMENT.json)
```json
{
  "id": "C01",
  "claim": "A classifier built from the 1000 gene-expression measurements separates the two groups of subjects with a balanced accuracy (mean of sensitivity and specificity) of at least 0.60 on new subjects.",
  "data_keys": [
    {
      "key": "expression",
      "shape": "(subjects, genes)",
      "dtype": "float",
      "meaning": "expression level of each gene in the blood sample of each subject"
    },
    {
      "key": "group_b",
      "shape": "(subjects,)",
      "dtype": "bool",
      "meaning": "True when the subject belongs to the second group"
    }
  ],
  "sizes": "subjects = 40; genes = 1000"
}
```

## 4. Mapping
Faulty: within each training set the genes are ranked by the two-sample t statistic and the top k kept, k on the grid 1, 2, 3, 5, 10, 30, 100; nearest-centroid classifier on the standardised panel; for each k the stratified 10-fold CV balanced accuracy on all 40 subjects (gene ranking repeated in every fold); the best balanced accuracy over k is reported. Fixed: nested CV: outer stratified 10-fold; inner stratified 10-fold CV picks k in each outer training set (ties: smaller k); balanced accuracy of the whole procedure pooled over the outer held-out subjects. Threshold 0.60.

Estimand line. Faulty: the maximum, over the grid of k, of the CV balanced accuracy. Fixed: balanced accuracy of the whole procedure (gene ranking and k chosen inside the fitting data) on subjects not used for it.

Allowed-guard minimum used. Faulty: at least 2 subjects of each class in every training fold of the 10-fold structure. Fixed: at least 2 of each class in every training set of the nested 10 x 10 structure; non-finite expression gives None.

## 5. Pre-checks of the fixed criterion (plain Python, scratch scripts in work\; the faulty criterion was never run, only syntax-checked)
n = 100: plus 100, minus 23, control 28, noise 9, zeros None 100. Final, n = 200: plus 200/200, minus 45/200 (0.225), control 42/200, noise 39/200, zeros 200 None. Statistic check on 300 minus samples (modified copy of fixed.py returning the balanced accuracy): mean 0.506, sd 0.106, P(>= 0.6) = 0.207.

Number of revisions of the fixed criterion: 0.

## 6. Timing (final fixed criterion)
t = 0.0195 s (mean of 200 calls on plus samples), g = 0.0006 s (mean plus generation), S = 6 (2 worlds + 2 control(s)/relational pair(s) + 2 probes), estimate 2 x 200 x (S + 1) x (t + g) = 56 s (limit 900 s). No size request needed.

## 7. Deviations, problems, skeleton requests
Grid and tie rule are mine within the note's example. The fixed criterion holds in minus at 22 to 23% (statistic mean 0.506, sd 0.106 on 300 minus samples from a modified copy of the fixed source; P(>= 0.6) = 0.21); same reading as B2-08. Recorded, not corrected.

Skeleton requests: none.

## Designer lines (PREREG_PHASE_C §3; added by the designer after the fidelity audit)

- Overlap with Phase B: no (addendum source).
- Mechanism tag / statistic family (private note): L1.3 / classification.
- Allowed-guard minimum (private note): at least 1 subject of each class among the scored subjects (balanced accuracy defined) and at least 2 per class in every fitting set.
- Size ratio (brief size to source size): samples 40/40 = 1.0; genes 1000/6000 = 0.17 (reduced to the cap).
- The estimand line is in item 4 (criterion author).
