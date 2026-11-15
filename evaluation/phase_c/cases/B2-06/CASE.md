# CASE B2-06

## 1. Identity
Case id B2-06; world id C47; class B-2; subtype L3.2; source key KAP23.

## 2. Source and documenting passage
KAP23 Section 2.4, L3.2 'Nonindependence between train and test': Oner et al. 2020 (histopathology) 'uses different observations of the same patient in the training and test sets'; suggested fix block cross-validation (quote as returned by the fetch tool in part 1).

Who read it and how: KAP23 (Kapoor and Narayanan 2023). Read by the part-1 brief author (full text through the fetch tool's summary of https://ar5iv.labs.arxiv.org/html/2207.07048; the wording returned by that tool was not verified word for word). I (part 2) did not re-read it: the only URL I fetched, the VAR06 page, returned a reCAPTCHA page.

## 3. The brief (as in ASSIGNMENT.json)
```json
{
  "id": "C47",
  "claim": "A classifier built from the 20 image features of a tissue patch identifies malignant tissue in patches from new patients with an area under the ROC curve of at least 0.75.",
  "data_keys": [
    {
      "key": "patch_features",
      "shape": "(patients, patches, features)",
      "dtype": "float",
      "meaning": "20 image features of each tissue patch of each patient"
    },
    {
      "key": "malignant",
      "shape": "(patients,)",
      "dtype": "bool",
      "meaning": "True when the patient's tissue is malignant"
    }
  ],
  "sizes": "patients = 80; patches = 10; features = 20"
}
```

## 4. Mapping
Faulty: all patches are pooled into rows (patients x patches, 20 features) with the patient's label and a stratified 5-fold cross-validation is run over patch rows (patches of one patient fall in training and held-out folds); ridge-penalised logistic regression (lambda = 1); AUC over the pooled held-out patches. Fixed: the same pipeline with the folds assigned by patient (stratified by the patient's label), so that all patches of a patient stay in one fold. Threshold AUC >= 0.75.

Estimand line. Faulty: AUC on patches whose patients also contribute patches to the fitting data. Fixed: AUC on patches of patients absent from the fitting data (new patients).

Allowed-guard minimum used. Both: at least 2 patients of each class in every training fold of the patient-level 5-fold structure (at least 3 per class, counted over patients); non-finite features give None.

## 5. Pre-checks of the fixed criterion (plain Python, scratch scripts in work\; the faulty criterion was never run, only syntax-checked)
n = 100: plus 100, minus 0, control 0, noise 0, zeros None 100. Final, n = 200: plus 197/200 (0.985), minus 0/200, control 0/200, noise 0/200, zeros 200 None.

Number of revisions of the fixed criterion: 0.

## 6. Timing (final fixed criterion)
t = 0.0023 s (mean of 200 calls on plus samples), g = 0.0003 s (mean plus generation), S = 5 (2 worlds + 1 control(s)/relational pair(s) + 2 probes), estimate 2 x 200 x (S + 1) x (t + g) = 6 s (limit 900 s). No size request needed.

## 7. Deviations, problems, skeleton requests
None. (The faulty guard is stated on patients, as the fixed one, so that both twins use the same class counts.)

Skeleton requests: none.

## Repair (round after the blind fidelity audit, item (c))
Auditor's finding: the same precedence slip (`-(n_pos) // 5` is `(-n_pos) // 5`), so the fixed guard tested n + ceil(n/5) < 2, while the faulty guard was a plain `min(n_pos, n_neg) < 2`. Accepted. Both bodies now use the same patient-level guard `min((n_pos - (-(-(n_pos) // 5))), (n_neg - (-(-(n_neg) // 5)))) < 2`, that is n - ceil(n/5) >= 2 patients per class (at least 3 per class), as section 4 states. Nothing else changed; the faulty file was only syntax-checked again. New pre-check of the fixed criterion (n = 200, seed 999000): plus 198/200, minus 0/200, control 0/200, noise 0/200, zeros 200 None. Timing unchanged: t = 0.0024 s, g = 0.0003 s, S = 5, estimate 6 s. Revisions of the fixed criterion counted so far: 1 (the guard repair).

## Designer lines (PREREG_PHASE_C §3; added by the designer after the fidelity audit)

- Overlap with Phase B: yes, Phase B case B2-11.
- Mechanism tag / statistic family (private note): L3.2 / classification.
- Allowed-guard minimum (private note): at least 1 malignant and 1 non-malignant patient among the held-out patients (smallest size at which AUC is defined); in each fitting set at least 2 patients per class.
- Size ratio (brief size to source size): source states none.
- The estimand line is in item 4 (criterion author).
