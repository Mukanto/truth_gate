# CASE B2-01

## 1. Identity
Case id B2-01; world id C44; class B-2; subtype L1.1; source key KAP23.

## 2. Source and documenting passage
KAP23 Section 2.4, L1.1 'No test set': training and testing on the same data (a 'text-book example of overfitting'); setting: civil war onset case study (Section 4, Appendix B), test set of 896 rows with 19 positives.

Who read it and how: KAP23 (Kapoor and Narayanan 2023). Read by the part-1 brief author (full text through the fetch tool's summary of https://ar5iv.labs.arxiv.org/html/2207.07048; the wording returned by that tool was not verified word for word). I (part 2) did not re-read it: the only URL I fetched, the VAR06 page, returned a reCAPTCHA page.

## 3. The brief (as in ASSIGNMENT.json)
```json
{
  "id": "C44",
  "claim": "A statistical classifier built from the 30 annual indicators of a country distinguishes the country-years in which a civil war begins from the country-years in which none begins, with an area under the ROC curve of at least 0.75 on new country-years.",
  "data_keys": [
    {
      "key": "indicators",
      "shape": "(country_years, indicators)",
      "dtype": "float",
      "meaning": "30 annual political, economic and demographic indicators of the country in that year"
    },
    {
      "key": "onset",
      "shape": "(country_years,)",
      "dtype": "bool",
      "meaning": "True when a civil war begins in that country-year"
    }
  ],
  "sizes": "country_years = 896; indicators = 30"
}
```

## 4. Mapping
Faulty: a logistic regression on the 30 indicators (standardised inside the fit, L2 penalty lambda = 1 on the slopes) is fitted on all rows and the AUC is computed on the same rows (no data are held out). Fixed: stratified 5-fold cross-validation of the same fit (random assignment, seed 20260201); held-out scores are pooled and the AUC is computed once. Same classifier, same AUC function, same threshold (AUC >= 0.75), same guard family.

Estimand line. Faulty: apparent (in-sample) AUC of the fitted model on the rows it was fitted to. Fixed: AUC of the model on rows not used to fit it (new country-years).

Allowed-guard minimum used. Faulty: at least 2 rows of each class (fit and scoring defined). Fixed: at least 2 rows of each class in every training fold of the 5-fold structure (that is, at least 3 per class in the data); non-finite indicators give None.

## 5. Pre-checks of the fixed criterion (plain Python, scratch scripts in work\; the faulty criterion was never run, only syntax-checked)
n = 100 (seed 777000): plus 88/100, minus 3/100, control permute_onset_across_country_years 0/100, control permute_onset_histories_across_countries 1/100, noise 0/100, zeros 100 None. Final, n = 200 (seed 888000): plus 179/200 (0.895), minus 7/200 (0.035), controls 0/200 and 3/200, noise 0/200, zeros 200 None.

Number of revisions of the fixed criterion: 0.

## 6. Timing (final fixed criterion)
t = 0.0040 s (mean of 200 calls on plus samples), g = 0.0010 s (mean plus generation), S = 6 (2 worlds + 2 control(s)/relational pair(s) + 2 probes), estimate 2 x 200 x (S + 1) x (t + g) = 14 s (limit 900 s). No size request needed.

## 7. Deviations, problems, skeleton requests
Classifier fixed to a ridge-penalised logistic regression (the note allowed 'logistic regression with all 30 indicators, or another flexible model'). Stratified 5-fold assignment is random over rows; the skeleton's docstring says rows are laid out in country blocks, which the criterion does not use, so the fixed cross-validation is not grouped by country (the brief says 'new country-years'). The fixed criterion held in minus at 3.5% (7/200) and in the second control at 1.5%, so this did not show up as a problem in the pre-check. None else.

Skeleton requests: none.

## Repair (round after the blind fidelity audit, item (c))
Auditor's finding: Python reads `-(n_pos) // 5` as `(-n_pos) // 5`, so the fixed guard tested n + ceil(n/5) < 2 instead of n - ceil(n/5) < 2. Accepted. Changed only the guard line of `fixed.py`, now `min((n_pos - (-(-(n_pos) // 5))), (n_neg - (-(-(n_neg) // 5)))) < 2`, which is n - ceil(n/5) >= 2 per class (at least 3 per class in the data, as section 4 states). The faulty guard (`min(n_pos, n_neg) < 2`) is unchanged: its fit has no folds. Nothing else changed (same seed, fold code, statistic, threshold); the faulty file was only syntax-checked again. New pre-check of the fixed criterion (n = 200, seed 999000): plus 179/200, minus 8/200, control permute_onset_across_country_years 0/200, control permute_onset_histories_across_countries 4/200, noise 0/200, zeros 200 None. Timing unchanged: t = 0.0041 s, g = 0.0009 s, S = 6, estimate 14 s. Revisions of the fixed criterion counted so far: 1 (the guard repair).

## Designer lines (PREREG_PHASE_C §3; added by the designer after the fidelity audit)

- Overlap with Phase B: no.
- Mechanism tag / statistic family (private note): L1.1 / classification.
- Allowed-guard minimum (private note): at least 1 positive and 1 negative row among the scored rows (smallest size at which AUC is defined); in each training fold at least 2 rows per class.
- Size ratio (brief size to source size): country-years 896/896 = 1.0; indicators 30/90 = 0.33.
- The estimand line is in item 4 (criterion author).
