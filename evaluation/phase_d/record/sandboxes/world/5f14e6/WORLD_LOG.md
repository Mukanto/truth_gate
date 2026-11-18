# World log (Phase D, sandbox 5f14e6)

All eight skeletons are in `skeletons\`. In every skeleton, `plus` and `minus` call one generator with the same random draws
in the same order. The only difference is the parameter that carries the claim, so each `minus` sample is paired with
its `plus` sample. Effect sizes were chosen by analytic power reasoning. I did not simulate any analysis that could
serve as a criterion. `_check_worlds.py` is my own author-side check: AST rules, docstrings, keys/shapes/dtypes, finite
values, timing, controls that change the data, and descriptive summaries only. Every call ran in under 8 ms.

## D-052 (training gain, young vs old)
* `plus`: 40 participants, 20 young (random positions). Baseline ability differs by age (60 vs 52, between-subject SD 10).
  The true gain is 10.0 (young) vs 4.5 (old), with between-subject SD 4. Measurement error is SD 3 per session, so the
  SD of the observed improvement is about 5.8.
  The effect is d of about 0.94: a one-sided two-sample test with 20 per group has a power of about 0.9. That is a
  realistic design target, not a huge effect.
* `minus`: the young mean gain is set equal to the old mean gain (4.5). The baseline age difference, the variability and
  the measurement error are unchanged.
* Controls: `age_labels_permuted` (the young/old labels are permuted across participants) and `pre_post_swapped` (time
  reversed, so the improvement changes sign).

## D-055 (daily predictors, ridge prediction over future days)
* `plus`: 6 AR(1) predictor series (phi 0.4 to 0.95) with correlated innovations, in arbitrary units. The outcome is a
  linear function of the same-day X plus AR(1) noise (phi 0.3). The population correlation between y and its true linear
  predictor is 0.33.
  Reasoning: with a few hundred future days and autocorrelation, the SE of r is about 0.06 to 0.08. A true value of 0.33
  minus a small estimation loss gives a probability of about 0.9 that r is at least 0.20.
* `minus`: the effect of X on y is set to zero. y is the same autocorrelated noise, and X is unchanged.
* Controls: `outcome_circular_shift` (y rolled by 150 to 850 days, which keeps each series' autocorrelation and breaks
  the alignment) and `predictor_blocks_permuted` (50-day blocks of X reordered by one cycle, so no block stays aligned).
  Relational pair `("y", "X")`.
* Judgement calls: I read "on future days" as a temporal hold-out, that is, a same-day regression of y on X evaluated on
  later days. I did not read it as X(t) predicting y(t+1). Under the lagged reading this world would be weaker: the
  lag-1 correlation is only about phi times the effect. Seasonality was left out on purpose: a shared annual cycle would
  realign under the circular-shift control and would also create a spurious time link.

## D-056 (ANCOVA, oxygen uptake by group, body mass covariate)
* `plus`: 3 groups of 25 rats. Mean body mass differs between groups (285, 300, 315 g; SD 30). Oxygen uptake is
  6.0*(M/300)^0.75 mL/min plus mass-adjusted group effects (-0.30, 0, +0.32), with residual SD 0.6 (about 10% CV).
  This is Cohen's f of about 0.42, giving ANCOVA power of about 0.9 with N = 75.
* `minus`: the mass-adjusted group effects are set to zero. The group differences in body mass are kept, so the
  unadjusted group means still differ through mass alone. This tests the "once body mass is accounted for" part of the
  claim.
* Control: `rats_permuted_across_groups` (each rat's oxygen uptake and mass stay together; group membership is permuted).

## D-062 (partial correlation femur and humerus given body length, at least 60% of 12 species)
* `plus`: species mean body lengths are lognormal around 150 mm, with a within-species CV of 0.08. Femur and humerus
  are species-specific ratios times body length, plus residuals (CV 0.045). The residuals have a within-species
  correlation rho_s ~ N(0.36, 0.07), clipped to [0.15, 0.6]. Body length enters linearly, so rho_s is exactly the
  partial correlation.
  Reasoning: with n = 30 the per-species probability that r is at least 0.2 is about 0.79, so P(at least 8 of 12
  species) is about 0.9. 8/12 is the smallest count that reaches 60%.
* `minus`: rho_s is set to 0 in every species. Size scaling is unchanged, so the raw femur–humerus correlation stays
  high (about 0.75), but the partial correlation is zero.
* Controls: `humerus_permuted_within_species`, and `humerus_exchanged_among_length_matched_individuals`. The second one
  rotates humerus values within blocks of 5 individuals of similar body length and has no fixed points. It keeps the
  humerus–body length relation and breaks the residual femur–humerus link.
* Judgement call: body length has no added measurement error. Error in the measured covariate would make the partial
  correlation positive even in `minus`, which would no longer be the null.

## D-064 (expression + clinical predict tumour response, r of at least 0.30)
* `plus`: 80 patients, 1500 genes, 8 standardised clinical covariates (correlated). Expression has 10 latent programmes:
  a response-related module of 60 genes (loading 0.65, correlated 0.3 with covariate 2, "grade"), and 9 background
  programmes of 100 genes each. Gene means and SDs vary.
  The true response signal is 0.50·module - 0.30·tumour size + 0.20·age, explaining 36% of the variance (rho of about
  0.6; the module alone gives rho of about 0.5). Response = 30 + 22·standardised score, capped at 100%.
* `minus`: the response signal is set to zero, leaving the same noise. Expression and clinical data are unchanged.
* Control: `response_permuted_across_patients`. No relational pair: shuffling only expression would leave the clinical
  signal aligned with the response, so the claim would not be broken.
* Judgement call (calibration risk): with p >> n, the achieved out-of-sample r depends strongly on the analysis.
  I chose a fairly strong true signal (R² 0.36) so that a reasonable pipeline (cross-validated penalised regression,
  whether or not the clinical covariates are penalised) should exceed 0.30 most of the time. I could not check this
  without running a criterion-like analysis, which the rules forbid.

## D-066 (1-NN balanced accuracy of at least 0.65, rare outcome)
* `plus`: 1000 patients, prevalence 8% (Bernoulli). 15 Gaussian clinical measurements in realistic units, with a few
  correlated pairs. Patients with the outcome are shifted by 1.4 within-class SD on 5 measurements (creatinine up, Hb
  down, WBC up, albumin down, heart rate up), so the Euclidean shift D² is about 9.8.
* `minus`: the same abnormal profile is carried by an independent indicator of the same prevalence instead of y.
  Both the marginal distribution of X (a mixture) and the distribution of y are unchanged; X carries no information
  on y.
* Control: `outcome_permuted_across_patients`. Relational pair `("y", "X")`.
* Judgement call (calibration risk): 1-NN is weak for a rare class in 15 dimensions. A rough analytic approximation of
  nearest-neighbour distances (noncentral chi-square, cube-root normal approximation, minima over about 70 positives
  and 800 negatives) suggests sensitivity of about 0.55 to 0.6 and specificity of about 0.97, so a true balanced
  accuracy of about 0.75. That would be comfortably above 0.65 with a test-set SE of about 0.03 to 0.045. The
  uncertainty of this approximation is about ±0.1.

## D-067 (standardised slope of kidney on heart weight, given body mass, at least 0.25)
* `plus`: 60 rats. Mass N(350, 50) g. Heart weight correlates 0.7 with mass. Kidney = 0.35·mass + 0.42·heart + noise,
  in standardised units, with residual variance 0.495. The standardised partial slope is 0.42 (partial correlation
  about 0.39). Either reading of "standardised slope" gives a power of about 0.9 against 0.25 (SE about 0.11 to 0.125).
* `minus`: the heart effect is set to 0. The mass effect and the noise are unchanged.
* Controls: `heart_permuted_across_rats`, and `heart_exchanged_among_mass_matched_rats`. The second one rotates heart
  values within blocks of 6 rats sorted by mass, with no fixed points. Relational pair `("kidney_weight", "heart_weight")`.

## D-068 (mean within-population partial slope of wing on head width, at least 0.30 mm/mm)
* `plus`: 25 populations of 40 specimens. Body length is 10 mm (population SD 0.6, within SD 0.8). Head width follows
  allometry with slope 0.18, residual SD 0.10, and population intercepts. Wing = population intercept + 0.55·body +
  b_p·head + noise (SD 0.25), with b_p ~ N(0.42, 0.10).
  Reasoning: the per-population SE of the slope is about 0.41, so the SE of the mean over 25 populations is about
  0.085, and the power against 0.30 is about 0.9.
* `minus`: b_p is set to 0 in every population. I read the null as "no relationship" in each population, not as a
  mean of 0 with heterogeneity kept. All other parameters are unchanged.
* Controls: `head_width_permuted_within_population`, and `head_width_exchanged_among_length_matched_specimens`. The
  second one rotates head width within blocks of 5 specimens of similar body length, with no fixed points.
