# CASE B2-10

## 1. Identity
Case id B2-10; world id C48; class B-2; subtype L1.3; source key VAR06.

## 2. Source and documenting passage
VAR06 Methods/Results: SVM with Gaussian kernel, trade-off C and kernel parameter gamma tuned by leave-one-out CV over a grid (2^-5 to 2^15, 2^-15 to 2^3); the procedure 'requires that all steps of the algorithm, including classifier parameter tuning, be repeated in each CV loop' (part-1 note, from PMC1397873).

Who read it and how: VAR06 (Varma and Simon 2006, addendum source). Read by the part-1 brief author (full text of https://pmc.ncbi.nlm.nih.gov/articles/PMC1397873/ through the fetch tool's summary). I (part 2) tried the same URL through ctx_fetch_and_index; it returned a reCAPTCHA page, nothing was read, no workaround was tried. The parameters below are the ones in the part-1 private note.

## 3. The brief (as in ASSIGNMENT.json)
```json
{
  "id": "C48",
  "claim": "A kernel-based classifier built from the 1000 gene-expression measurements separates the two tumour classes with an accuracy of at least 0.60 on new samples.",
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
SUBSTITUTION as the note instructs: a Gaussian-kernel ridge classifier (closed form through an eigendecomposition of the kernel matrix; regularisation 1/C) replaces the SVM, with a 5 x 5 grid on the source's ranges (C = 2^-5, 2^0, 2^5, 2^10, 2^15; gamma = 2^-15, 2^-10.5, 2^-6, 2^-1.5, 2^3) and the 3 genes with the largest |t| (pooled-variance two-sample t on the fitting set, standardised on it) chosen again inside every fit. Faulty: leave-one-out accuracy on all 40 samples for every (C, gamma); the best accuracy over the grid is reported. Fixed: nested CV: outer stratified 10-fold; in each outer training set leave-one-out over the grid (genes reselected in every leave-one-out fit) picks (C, gamma) (ties: first in the order C ascending, gamma ascending); the whole fit (genes, kernel, parameters) predicts the outer held-out samples; accuracy pooled. Threshold 0.60.

Estimand line. Faulty: the maximum leave-one-out accuracy over the (C, gamma) grid. Fixed: accuracy of the whole tuned procedure on samples not used for tuning or fitting.

Allowed-guard minimum used. Faulty: at least 3 samples of each class (every leave-one-out fitting set keeps 2 and the t statistic is defined). Fixed: at least 3 of each class in every outer training set; non-finite expression gives None.

## 5. Pre-checks of the fixed criterion (plain Python, scratch scripts in work\; the faulty criterion was never run, only syntax-checked)
n = 20 (seed 777000): plus 18, minus 5, control 4, noise 4, zeros None 20. Final, n = 40 (seed 888000, 0.23 s per call): plus 33/40 (0.825), minus 12/40 (0.30), control 4/40, noise 8/40, zeros 40 None.

Number of revisions of the fixed criterion: 0.

## 6. Timing (final fixed criterion)
t = 0.2340 s (mean of 40 calls on plus samples), g = 0.0007 s (mean plus generation), S = 5 (2 worlds + 1 control(s)/relational pair(s) + 2 probes), estimate 2 x 200 x (S + 1) x (t + g) = 563 s (limit 900 s). No size request needed.

## 7. Deviations, problems, skeleton requests
Kernel ridge replaces the SVM and the grid is 5 x 5 (the note allows both; the substitution is stated here as the note asks). Outer folds 10 (not leave-one-out) to meet the timing estimate. The fixed criterion holds in minus at 25 to 30% (small samples, 40 per pre-check) and on the noise probe at 20%; as in B2-08 the threshold 0.60 on 40 samples is loose. Recorded, not corrected.

Skeleton requests: none.

## Repair (round after the blind fidelity audit, item (c))
Auditor's finding: `-(n_pos) // 10` is `(-n_pos) // 10`, so the fixed guard tested n + ceil(n/10) < 3 instead of n - ceil(n/10) < 3. Accepted. Changed only the guard line of `fixed.py`, now `min((n_pos - (-(-(n_pos) // 10))), (n_neg - (-(-(n_neg) // 10)))) < 3`, which is n - ceil(n/10) >= 3 per class in every outer training set (so every leave-one-out fitting set keeps 2 per class and the t statistic is defined). The faulty guard (`min(n_pos, n_neg) < 3`) is unchanged, as the structure of the faulty criterion (single leave-one-out loop) needs that. Nothing else changed; the faulty file was only syntax-checked again. New pre-check of the fixed criterion (n = 40, seed 999000): plus 32/40, minus 7/40, control 7/40, noise 7/40, zeros 40 None. Timing: t = 0.2357 s, g = 0.0007 s, S = 5, estimate 567 s (was 563 s; limit 900 s). Revisions of the fixed criterion counted so far: 1 (the guard repair).

## Designer lines (PREREG_PHASE_C §3; added by the designer after the fidelity audit)

- Overlap with Phase B: no (addendum source).
- Mechanism tag / statistic family (private note): L1.3 / classification.
- Allowed-guard minimum (private note): at least 2 samples per class in every fitting set and at least 1 sample in each scored set.
- Size ratio (brief size to source size): samples 40/40 = 1.0; genes 1000/6000 = 0.17 (reduced to the cap).
- The estimand line is in item 4 (criterion author).
