# World log (batch 3d2b82)

Eight skeletons in `skeletons\`. In every skeleton `plus` and `minus` call one shared generator that consumes the random
generator identically; only the claimed quantity differs. Own checks (scratch scripts `_check_worlds.py`,
`_effect_checks.py` in this folder): every world and control returns the brief's keys, shapes, dtypes and finite values,
every control changes the data, and calls take at most about 4 ms. Effect checks used population quantities averaged
over draws (no decision rule).

## D-052 (young vs old training improvement)
- **plus:** mean gain 9.0 points for young and 3.5 for old (difference 5.5, about d = 0.85 on the change score). That gives
  roughly 85% power for a one-sided two-sample test with 20 per group, the size a well-powered design would plan for.
  Young start higher and old are more variable. Test-retest r(pre, post) = 0.84.
- **minus:** both groups' mean gain is 6.25 (the plus average), so the overall improvement is unchanged. Judgement call:
  the null "equal improvements" is placed at the plus average rather than at either group's value.
- **controls:** `age_labels_shuffled` (age labels permuted across participants); `pre_post_swapped` (the sessions are
  exchanged, so the improvement changes sign).
- Check: mean young-old difference 5.53 (plus) and 0.03 (minus), with the same SD of 2.04 across draws.

## D-055 (daily predictors forecast y on future days)
- **plus:** y_t depends on the same day's predictors through a fixed linear signal (R^2 = 0.16). With the weekly
  pattern and drift added, the correlation of y with the true signal over the last 300 days is about 0.38. Ridge with
  6 predictors fitted on about 700 days should come close to that, a realistic but clear margin over 0.20. The
  predictors are persistent and correlated, and y has AR(1) noise, a weekly pattern and a slow drift.
- **minus:** y is built from an independent copy of the predictor process (same dynamics, loadings and coefficients), so
  y keeps its plus distribution and autocorrelation but the recorded X carries no information about it. Check: the
  oracle correlation over the last 300 days is 0.002 (SD 0.082, inflated by autocorrelation).
- **control:** `y_circularly_shifted` (y rotated by 150-850 days relative to X: keeps y's autocorrelation and breaks the
  alignment; the factor autocorrelation at 150 days is about 0).
- Judgement calls: "future days" is read as a chronological out-of-sample period, and the relation is taken to be
  same-day (X_t to y_t). No periodic component is shared by X and y, because that would itself be predictive
  information.

## D-056 (ANCOVA group effect on oxygen uptake)
- **plus:** mass-adjusted group effects of 0, +6.5% and -3.5% on oxygen uptake (Cohen's f about 0.4 against a residual
  of about 10%, about 80-85% power for the F test with 75 rats). Oxygen uptake scales as mass^0.75. The groups also
  differ in body mass (310 / 335 / 295 g), so raw means differ more than adjusted means.
- **minus:** adjusted group effects all equal to the plus mean (+1%). The body-mass differences between groups stay, so
  raw oxygen uptake still differs between groups (check: raw log means -0.009 / +0.054 / -0.045, adjusted about 0).
  This is a world where an analysis that ignores the covariate would be fooled.
- **control:** `animals_relabelled_across_groups` (whole animals, mass and uptake together, reassigned to groups at random).
- No relational pair: the shuffle probe would permute whole groups, which keeps differences between group means.

## D-062 (partial correlation femur-humerus | body length in at least 60% of species)
- **plus:** the within-species residual correlation of log femur and log humerus given body length is drawn per species
  from N(0.38, 0.15), clipped to [0, 0.8]. About 89% of species have a true value of 0.2 or more, and the mean sample
  partial correlation is 0.365. Morphological integration of limb bones after size adjustment is typically moderate.
  With 30 individuals per species, most species should show at least 0.2.
- **minus:** residual correlation 0 in every species, with the same residual SDs, allometry, species and site structure.
  Check: mean partial correlation -0.001.
- **control:** `humerus_permuted_within_species`; **relational:** (femur, humerus): the shuffle permutes species rows.
- Judgement call: the world is specified on measured body length (the partial correlation in the claim conditions on the
  measured value), so measurement error in body length is part of the residuals and cannot produce a spurious partial
  correlation in `minus`.

## D-064 (expression + clinical predict tumour response, r >= 0.30)
- **plus:** the response depends on tumour size (-), grade (+), a 75-gene "sensitivity" module and the proliferation module.
  The oracle correlation is 0.6 (R^2 = 0.36), of which the clinical part is about 40%. A model trained on 80 patients
  with 1500 genes recovers only part of that, so the realistic out-of-sample correlation is about 0.35-0.5, a modest
  margin over 0.30. Check: corr(response, module-1 average) 0.47, corr(response, tumour size) -0.16.
- **minus:** the response is built from an independent copy of the same drivers (clinical latents and module factors),
  so neither block carries predictive information. The response distribution and all X structure (modules, batches,
  clinical-module links) are unchanged. Check: both correlations about 0.
- **control:** `response_permuted_within_batch`; **relational:** (expression, response).
- Judgement call: the null is "no predictive information from expression and clinical together", not "expression adds
  nothing beyond clinical", because the claim is about the combined prediction.

## D-066 (1-NN balanced accuracy >= 0.65 for a rare outcome)
- **plus:** prevalence 7%. Cases are shifted by 1.4 latent SD on 6 of the 15 measurements, with opposite signs within each
  block (for example one value up, a related one down). The other 9 measurements carry no signal, and 4 lab values are
  log-normal. A one-neighbour rule in 15 dimensions with about 70 cases needs a distinct case profile to reach 0.65.
  Judgement call: I sized the shift with an analytic design calculation (`_calib_066_theory.py`, output
  `_calib_066_out.txt`). It gives the expected 1-NN sensitivity and specificity from the exact distance distributions
  of an idealised Gaussian model (noncentral chi-square), using an effective-dimension correction for the
  correlations. No classifier was run on generated data. The predicted true balanced accuracy is about 0.72-0.78
  (sensitivity about 0.5, specificity about 0.99). This is an approximation; skew and site shifts may lower it
  slightly.
- **minus:** the case profile in X follows an independent label with the same prevalence, so X keeps its plus mixture
  distribution and y its prevalence, but X carries no information on y. Check: standardised case-control differences
  about 0 in minus and about 1.3 in plus on the six profile measurements.
- **control:** `y_permuted_within_site`; **relational:** (X, y).

## D-067 (standardised slope kidney on heart given body mass >= 0.25)
- **plus:** residual correlation of log kidney and log heart weight given body mass of 0.46. With the organ-specific
  cohort offsets the effective partial correlation is about 0.42 (check: 0.433), a moderate effect that a study with
  60 rats can show above 0.25.
- **minus:** residual correlation 0, with the same residual SDs, allometry (exponent 0.85) and cohort structure. Check:
  mean partial correlation 0.000 (SD 0.129).
- **controls:** `heart_permuted` (across all rats); `heart_swapped_within_body_mass_blocks` (rats sorted by mass in blocks
  of 5, each receives the heart weight of another rat in its block: keeps the heart-mass relation and breaks the residual
  link); **relational:** (kidney_weight, heart_weight).
- Ambiguity: "standardised slope" can mean the standardised partial regression coefficient or the slope between
  standardised residuals (the partial correlation). Both organs have the same correlation with body mass (about 0.77),
  so the two readings agree closely in this world.

## D-068 (mean within-population coefficient of wing on head width given body length >= 0.30)
- **plus:** population coefficients drawn from N(0.55, 0.15) mm/mm. Check: mean over populations 0.551, SD across draws
  0.105, so a margin of about 2.4 SE over 0.30. The partial correlation is small (about 0.18 within a population), as
  is usual for shape traits once size is held fixed. An environmental population factor raises mean head width and
  mean wing length together, so a pooled analysis that ignores populations would be biased.
- **minus:** coefficient 0 in every population. The head-width component of wing length is replaced by unrelated noise of
  the same variance, so wing length keeps its plus distribution and its relation to body length. Check: mean -0.001.
- **control:** `head_width_permuted_within_population`; **relational:** (wing_length, head_width).
- Judgement call: as in D-062 and D-067, the world is specified conditionally on the measured covariate.
