# World log (batch d5f53a)

General construction, the same in all eight skeletons: `plus` and `minus` call one generator that draws from `rng` in
exactly the same order, and they differ only in the parameter carrying the claimed effect. A paired `minus` draw
therefore changes only the key that carries the effect. A self-check over 30 paired draws per brief
(`_check_worlds.py`) confirmed this. Where the claim is about predictive or partial association, `minus` replaces
the carrier of the association with an **independent copy of the same distribution**, not with nothing, so every
marginal distribution and variance stays as in `plus`. Every call takes under 4 ms.

## D-052: young vs old training improvement
- **plus:** ability is shared by pre and post (measurement error SD 5, reliability about 0.85). Old participants
  start 8 points lower and vary more. True improvement is 10 + 3.5 (young) vs 10 - 3.5 (old), with person SD 4 and a
  small within-group dependence on baseline. **minus:** both groups have a mean true improvement of 10, and nothing
  else changes.
- **Effect:** a 7-point difference, about d = 0.85 on improvement scores, so a one-sided test with 20 per group has
  about 85% power. That is the size a well-planned 20-vs-20 study would aim for.
- **Control:** age labels permuted across participants (keeps 20/20). Relational pair (`post`, `young`).
- **Judgement call:** the null keeps the average improvement over both groups at 10 instead of lowering young to
  old.

## D-055: daily predictors and future outcome
- **plus:** 6 predictors, each with a shared AR(1) factor (phi 0.9) and its own AR(1) part (phi 0.55 to 0.85). y on
  each day = a signal from 3 of the same day's standardised predictors (16% of y's variance, population r = 0.40)
  plus autocorrelated noise (AR 0.6), slow drift (AR 0.99) and a weekday cycle. **minus:** y's signal part is
  computed from an independent copy of the predictor process, so y's distribution and time structure are unchanged
  and X carries no information about y.
- **Effect:** r = 0.40 in the population, about 0.37 expected for a fitted 6-predictor model on future days. That
  leaves a margin over 0.20 given the autocorrelation-inflated sampling error, which is about 0.1 for 300 test days.
- **Control:** y circularly shifted by 200 to 800 days relative to X, which keeps both series' time structure and
  breaks their alignment. Relational pair (`X`, `y`).
- **Judgement calls:** the relation is contemporaneous; "future days" is read as later days in the series. No
  calendar seasonality is shared between X and y, because a shared deterministic cycle would itself be predictive
  information.

## D-056: ANCOVA of resting VO2 in 3 groups of rats
- **plus:** VO2 = 5 mL/min x (mass/315 g)^0.67. The groups differ in body mass (295, 315, 335 g, within-group CV
  10%). Mass-adjusted group effects are +5%, -5% and 0. There is a day-of-measurement calibration drift (3%) shared by
  animal index across groups, individual variation of 9% and measurement error of 4%. **minus:** adjusted group
  effects are 0, and the group mass differences, allometry and noise are kept. Raw VO2 therefore still differs
  between groups through mass.
- **Effect:** Cohen's f about 0.40 on the residual scale, so power is about 0.85 for 3 x 25. Mass-adjusted
  metabolic differences of 5 to 10% between strains or diets are typical.
- **Control:** animals permuted across groups together with their own body mass, which keeps the allometry and
  removes any group effect.
- **Judgement call:** the effect pattern (+, -, 0) is deliberately not aligned with the mass ordering, so raw and
  adjusted group differences do not coincide.

## D-062: femur-humerus partial correlation in 12 species
- **plus:** species have mean body lengths of 80 to 400 mm with species-specific bone ratios, slopes and variances.
  Within a species, log femur and log humerus follow log body length (which includes a 4% sex difference). Their
  residuals correlate with a fixed species-specific partial correlation (0.12 to 0.60, mean 0.40; 11 of 12 species
  at 0.2 or more). **minus:** the partial correlation is 0 in all 12 species, and everything else is unchanged.
- **Effect:** limb integration after size correction of about 0.3 to 0.6 is plausible. With n = 30 per species, a
  species at rho = 0.40 shows a sample partial r of at least 0.2 about 85% of the time.
- **Controls:** (1) within each species, humerus swapped between body-length neighbours (pairs after sorting by
  body length), which keeps the humerus-body length relation and destroys the residual link; (2) humerus permuted
  within species.
- **Judgement calls:** the null is defined with respect to the recorded body length. No latent size factor beyond
  body length is added, because it would itself create a positive partial correlation. The claim is read as "the
  share of species with partial r at least 0.2 is at least 60%", which is 8 of 12.

## D-064: expression plus clinical covariates predict tumour response
- **plus:** 1500 genes, of which 1000 form 8 co-expression modules (loadings 0.35 to 0.8). There are 4 processing
  batches and a per-sample offset. 8 clinical covariates (age, size, grade, stage, nodal, performance status, sex,
  albumin; mixed continuous, ordinal and binary, z-scored) share a latent aggressiveness factor with the
  proliferation module. Response = 30 + 25 x (0.6 x signal + 0.8 x noise), clipped at [-50, 100]. The signal comes
  from the proliferation and immune modules, tumour size and performance status. **minus:** the signal part of the
  response comes from independent patients from the same population; expression and clinical data are unchanged.
- **Effect:** the oracle correlation is 0.6. A cross-validated model on 80 patients should recover roughly 0.4 to
  0.5, because the two relevant modules are strong principal directions of the expression matrix. This is a
  plausible target for a study claiming at least 0.30.
- **Control:** response permuted across patients. Relational pair (`expression`, `response`).
- **Judgement call:** the effective signal is spread over 250 module genes plus correlated modules and two
  covariates, not over a few genes.

## D-066: 1-nearest-neighbour recovery of a rare outcome
- **plus:** prevalence 8% (about 80 of 1000). Outcome patients are shifted by 1.3 SD in 6 measurements and 0.5 SD
  in 3 more. The 15 measurements come in 3 correlated organ-system blocks (r about 0.3), with offsets from 4 sites;
  3 laboratory values are lognormal; all are in clinical units. **minus:** the same shifted subgroup exists but is an
  independent draw of the same size distribution, unrelated to y. X's distribution and the prevalence are
  unchanged.
- **Effect:** chosen so that a 1-NN on standardised data reaches a balanced accuracy of about 0.72 to 0.80 by an
  analytic approximation of nearest-neighbour distances: sensitivity about 0.5 to 0.65, specificity about 0.95. A
  1-NN with a rare class needs strong separation, so the effect is large by the standard of an optimal classifier
  (LDA AUC about 0.98) but moderate for the stated classifier. No classifier was simulated, to stay within the rules.
- **Control:** outcome permuted across patients. Relational pair (`X`, `y`).
- **Judgement call:** "rare" was taken as 8%. This is the riskiest effect size in the batch, because 1-NN
  performance was set by approximation only.

## D-067: kidney vs heart weight after body mass
- **plus:** 60 male rats from 20 litters of 3 (ICC 0.15, litter not recorded, rows in random order). Heart and
  kidney scale with body mass (exponents 0.90 and 0.85, each r about 0.70 with mass). Their residuals given body mass
  correlate 0.45 at both litter and individual level. With equal organ-mass correlations, the standardised partial
  slope equals that 0.45. **minus:** the residual correlation is 0 at both levels; allometry and clustering are
  unchanged.
- **Effect:** 0.45 against a threshold of 0.25. The SE of the standardised slope is about 0.12 at n = 60, which
  is a realistic organ-size integration effect.
- **Controls:** (1) heart weight swapped between body-mass neighbours, which keeps the heart-mass relation and
  breaks the residual link; (2) heart weight permuted across rats. Relational pair (`kidney_weight`, `heart_weight`).
- **Judgement call:** "standardised slope after accounting for body mass" is read as the standardised coefficient
  of heart weight in a regression of kidney weight on heart weight and body mass.

## D-068: wing on head width at given body length, 25 beetle populations
- **plus:** populations differ in mean size, with a between-population head-wing relation (correlation 0.4 of the
  population deviations). Within populations, head and wing follow body length (females 0.5 mm longer). Wing
  contains beta_p times the head residual at a given body length, with beta_p = 0.60 ± 0.12 mm/mm across
  populations. **minus:** that term uses an independent copy of the head residual, so each population's coefficient
  is 0, while wing's distribution, the population structure and the between-population relation are unchanged.
- **Effect:** a mean coefficient of 0.60, a within-population partial r of about 0.17 and a per-population
  coefficient SE of about 0.55. The mean over 25 populations then has an SE of about 0.11, so the estimate exceeds
  0.30 with high probability and a one-sided lower bound exceeds it in roughly 80% of datasets.
- **Controls:** (1) within each population, head width swapped between body-length neighbours; (2) head width
  permuted within population.
- **Judgement call:** the null is defined on the recorded body length (no hidden latent size).
