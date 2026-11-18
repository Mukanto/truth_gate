# STRUCTURE_LOG, sandbox B3B (structure author, Phase D)

15 reference worlds written, one `reference.py` per case folder: D-001, D-002, D-009, D-019, D-023, D-025, D-026,
D-045, D-048, D-051, D-056, D-057, D-063, D-068, D-072.

## General

- Sources online: none read, no URL fetched. Every structure value is the note's `approved_value`; the notes state that
  the abstracts give no size, so the sizes of the other dependencies are my own assumptions, justified per case below.
- Every world uses only the brief's keys, shapes and dtypes. No key, variable or dependence was added for the faulty
  analysis. The replicate keys (`*_2`, `*_retest`) are in every brief; they carry the structure statistic and are
  generated as an independent second determination of the same true value, the same for both worlds.
- Both worlds draw the random numbers in the same order and carry the same structure parameters. The structure
  statistic does not read the nulled quantity, so on identical seeds it is identical in the two worlds. With different
  seeds the two worlds have the same distribution of the statistic.
- Measurement script (my own, in `work\`): 200 samples of each world, seeds 7000..7199, the note's `stat` code. Shapes
  and dtypes checked against the briefs. A control call or world call took at most 1 ms. No analysis resembling a
  criterion was written or run, and no effect was estimated from samples: the claimed effects below are generator
  parameters. Figures labelled "analytic" are algebra on the parameters, not simulation output.
- Every control returns the full data dict, changed, with the same shapes and dtypes (checked on one `plus` sample).

## Blood pressure, rate of change against initial value (BLO77)

### D-001 (150 individuals, 3 visits)
- Structure: reading-error variance over the variance of the first reading (the note's `stat`), 0.15. Note value, from
  the note: error SD about 6 mmHg against between-person SD about 15 mmHg.
- Other dependencies: x_ij = a_i + s_i * t_j + e_ij, t = 0, 1, 2. Initial level a_i ~ N(130, 14.28^2) (so that
  36 / (204 + 36) = 0.15), reading error e ~ N(0, 6^2) independent per reading. Yearly slope s_i has mean 1.0 mmHg/yr and
  SD 3.0 mmHg/yr between individuals, correlated with a_i (below). The SD of 3 mmHg/yr is at the high end of published
  between-person SDs of long-term systolic slopes; I chose it because a smaller SD makes the correlation unestimable with
  three visits. Individual trajectories are straight lines.
- `minus` sets to null: the correlation between true slope and true initial level, -0.65 to 0. Slope SD, level SD,
  error SD unchanged.
- Keys the error needs: `systolic_bp` only.
- Effect parameters: correlation of true slope and true initial level -0.65 (claim: at most -0.30).
- Measured statistic: plus 0.1553 (sd 0.0249), minus 0.1553 (sd 0.0249). Tolerance 0.030.
- Control: each individual's fitted slope is replaced by the slope of another individual (permuted), the mean level and
  the residuals are kept.
- Remark (analytic): with 3 visits and these sizes, the analysis that corrects for the reading error has a standard error
  of the order of half the distance between -0.65 and -0.30, so its power at n = 150 is moderate. I did not raise the
  effect above -0.65.

### D-019 (400 individuals, 5 visits)
- Structure: same statistic, 0.15, same source of the value.
- Other dependencies: same generator with t = 0..4; slope SD 2.0 mmHg/yr, mean 1.0.
- `minus` sets to null: the correlation between true slope and true initial level, -0.45 to 0 (the true regression
  slope of the true slope on the true initial level -0.063 to 0).
- Keys the error needs: `systolic_bp` only.
- Effect parameters: correlation -0.45, which gives a true regression slope of -0.45 * 2.0 / 14.28 = -0.063 (claim: at
  most -0.03).
- Measured statistic: plus 0.1513 (sd 0.0121), minus 0.1513 (sd 0.0121). Tolerance 0.030.
- Control: as D-001.
- Remark (analytic): the bias of the naive slope under `minus` is -0.2 * 36 / 240 = -0.03, the claim's threshold.

## Oxygen consumption, delivery and content (MOR86, STR87)

### D-002 (120 animals)
- Structure: 0.5 * var(a - a2) / var(a) = 0.1, share of arterial-content variance that is determination error (note's
  assumed share).
- Other dependencies: true arterial content ~ N(18, 1.4^2) mL/dL, determination error SD 0.4667 (share 0.1). True
  arterial-minus-venous difference: mean 4.5, SD 0.8 mL/dL, correlated with true arterial content (below). Venous
  determination error SD 0.35 mL/dL, two independent determinations of each content.
- `minus` sets to null: the correlation between the true content difference and the true arterial content, 0.5 to 0.
  The SD of the difference is unchanged.
- Keys the error needs: the four brief keys (the second determinations carry the structure).
- Effect parameters: correlation 0.5 (claim: at least 0.30).
- Measured statistic: plus 0.1033 (sd 0.0175), minus 0.1033 (sd 0.0175). Tolerance 0.020.
- Control: the arterial-minus-venous difference is permuted across animals and the venous contents re-derived
  (second determination keeps its error difference).
- Remark (analytic): the correlation that the arterial error alone creates under `minus` is about 0.15.

### D-048 (40 dogs)
- Structure: 0.5 * var(c - c2) / var(c) = 0.05, cardiac output error CV about 7% against between-animal CV about 30%.
- Other dependencies: true cardiac output lognormal, mean 3.0 L/min, CV 0.30; determination error SD 0.20 L/min,
  additive, two independent determinations. Arterial content ~ N(18, 1.2^2) mL/dL, independent of cardiac output.
  True consumption mean 120 mL/min, SD 14.4 (CV 12%). Venous content is derived so that the Fick calculation with the true
  cardiac output returns the true consumption. Arterial and venous contents are taken as error-free (blood gas
  analysis error of about 0.1 mL/dL is small beside the 1.2 spread), so the cardiac output error is the one coupled error.
- `minus` sets to null: the correlation between true consumption and true delivery (10 * CO * Ca), 0.65 to 0.
  Consumption keeps its mean and SD.
- Keys the error needs: the four brief keys.
- Effect parameters: correlation of true consumption and true delivery 0.65 (claim: at least 0.40).
- Measured statistic: plus 0.0528 (sd 0.0191), minus 0.0528 (sd 0.0191). Tolerance 0.010.
- Control: computed consumption permuted across dogs, venous content re-derived from the permuted value.
- Remark (analytic): with this share and a consumption CV of 12%, the correlation that the cardiac output error alone
  creates is about 0.05 * 0.30 / 0.12 = 0.12.

### D-063 (600 dogs)
- Structure: as D-048, 0.05.
- Other dependencies: as D-048, n = 600.
- `minus` sets to null: the correlation between true consumption and true cardiac output, 0.60 to 0 (true R-squared
  0.36 to 0). Consumption marginal unchanged.
- Keys the error needs: the four brief keys.
- Effect parameters: correlation 0.60 (claim: R-squared at least 0.25).
- Measured statistic: plus 0.0469 (sd 0.0045), minus 0.0469 (sd 0.0045). Tolerance 0.010.
- Control: as D-048.
- Remark (analytic): the R-squared that the error alone creates is about 0.015.

### D-051 (12 dogs, 8 steps)
- Structure: mean over dogs of 0.5 * var(c - c2) / var(c) within the dog = 0.1.
- Other dependencies: dog-level cardiac output lognormal (mean 3.0, CV 0.30); within a dog the 8 steps vary by a
  lognormal factor with SD 0.15; determination error SD 0.11 L/min (calibrated so the mean within-dog share is 0.1).
  Arterial content: dog mean ~ N(18, 1.2^2), step noise SD 0.3. Consumption: dog level mean 120, SD 14.4, noise SD 7
  mL/min, slope on delivery varying between dogs. Contents error-free, as D-048.
- `minus` sets to null: the mean within-dog slope of true consumption on true delivery, 0.25 to 0 (between-dog slope SD
  0.08 to 0). Consumption noise unchanged (so consumption variance is lower in `minus`).
- Keys the error needs: the four brief keys.
- Effect parameters: mean slope 0.25, between-dog SD 0.08 (claim: mean at least 0.15).
- Measured statistic: plus 0.0945 (sd 0.0348), minus 0.0945 (sd 0.0348). Tolerance 0.020.
- Control: computed consumption permuted over the steps within each dog, venous content re-derived.
- Remark (analytic): the within-dog slope that the error alone creates is about (120 / 540) * 0.1 = 0.02.

## Compounded ratios in beetles (ATC76)

### D-023 (2000 specimens)
- Structure: CV of body length 0.15 (note's value, a realistic adult CV).
- Other dependencies: body length lognormal, mean 12 mm, CV 0.15. Head width 3.4 mm and wing length 9.6 mm at mean
  length, with allometric exponents on body length of 0.6 and 0.7 (static allometry below 1, as body length is measured
  with error from abdomen telescoping), and independent size-free variation of 7% (log SD) each.
- `minus` sets to null: the correlation of the size-free variation of head and wing, 0.40 to 0. Both marginals unchanged.
- Keys the error needs: the three brief keys.
- Effect parameters: correlation of the size-free variation 0.40 (partial correlation about 0.40; claim: at least 0.30).
- Measured statistic: plus 0.1498 (sd 0.0026), minus 0.1498 (sd 0.0026). Tolerance 0.030.
- Control: wing length permuted across specimens.
- Remark (analytic): with exponents below 1, the log ratios share the term -(1 - b) log(length); the correlation of the two
  ratios under `minus` is about 0.35.

### D-026 (400 specimens, 6 dimensions)
- Structure: CV of body length 0.15.
- Other dependencies: body length as D-023. Six dimensions with means 3.0, 8.0, 5.5, 4.2, 6.5, 2.4 mm at mean length;
  exponents on body length 0.55 to 0.70; size-free log SD 0.07 to 0.09 per dimension.
- `minus` sets to null: the loadings of the six dimensions on a common shape factor (0.045 to 0.06, log scale) set to 0, with
  the total size-free variance of each dimension unchanged (unique variance enlarged).
- Keys the error needs: `skeletal` and `body_length`, both in the brief.
- Effect parameters: loadings 0.045 to 0.06 against total SD 0.07 to 0.09 (analytic share of the first component of the
  size-free covariance about 0.55; claim: at least 40%).
- Measured statistic: plus 0.1497 (sd 0.0056), minus 0.1497 (sd 0.0056). Tolerance 0.030.
- Control: each dimension permuted independently across specimens.

### D-068 (25 populations x 40 specimens)
- Structure: mean over populations of the within-population CV of body length, 0.15.
- Other dependencies: population mean length 12 mm times a lognormal factor (SD 0.08); within-population CV 0.15 times a
  lognormal factor (SD 0.10); head and wing as in D-023 with a population shift of 3% (log SD) in each allometric intercept;
  size-free variation 7% each.
- `minus` sets to null: the within-population correlation of the size-free variation of head and wing, 0.20 to 0.
- Keys the error needs: the three brief keys.
- Effect parameters: correlation 0.20, which gives a partial slope of wing on head at fixed length of about
  0.20 * 9.6 / 3.4 = 0.56 mm/mm (claim: mean at least 0.30).
- Measured statistic: plus 0.1488 (sd 0.0048), minus 0.1488 (sd 0.0048). Tolerance 0.030.
- Control: wing length permuted within each population.

## Change against baseline (TU07, TU04)

For D-045, D-057 and D-025 the claim is about the association of change with the average of the two readings, which is
non-zero exactly when the true spread shrinks from baseline to follow-up. `minus` therefore sets the true follow-up SD equal
to the true baseline SD; the persistence between the true baseline and the true follow-up, the error SD and the means are
unchanged. Regression to the mean (true follow-up on true baseline slope below 1) is present in both worlds.

### D-045 (300 patients)
- Structure: 0.5 * var(b - r) / var(b) = 0.2 (reliability 0.8).
- Other dependencies: true baseline ~ N(50, 10^2), reading error SD 5 on every reading (baseline, retest, follow-up);
  true follow-up mean 38, correlation with true baseline 0.7.
- `minus` sets to null: true follow-up SD 5.5 to 10 (equal to baseline).
- Keys the error needs: `baseline_score`, `baseline_score_retest`, `followup_score` (all in the brief).
- Effect parameters: true follow-up SD 5.5 (observed spread 7.4 against 11.2 at baseline); analytic correlation of observed
  change with observed mean level about -0.43 (claim: at most -0.30).
- Measured statistic: plus 0.2017 (sd 0.0209), minus 0.2017 (sd 0.0209). Tolerance 0.040.
- Control: follow-up scores rescaled about their mean to the baseline SD.

### D-057 (24 defects)
- Structure: 0.2 (probing error SD 0.9 mm against between-defect SD about 2 mm).
- Other dependencies: true baseline depth ~ N(7.5, 1.8^2) mm, error SD 0.9 mm on every probing; follow-up mean 3.5 mm,
  correlation with baseline 0.5.
- `minus` sets to null: true follow-up SD 0.65 to 1.8 mm.
- Keys the error needs: the three brief keys.
- Effect parameters: true follow-up SD 0.65 mm; analytic correlation of the change with the mean level about -0.55,
  R-squared about 0.30 (claim: at least 0.15).
- Measured statistic: plus 0.2148 (sd 0.0823), minus 0.2148 (sd 0.0823). Tolerance 0.040.
- Control: follow-up depths rescaled about their mean to the baseline SD.

### D-025 (12 trials x 20 defects)
- Structure: mean over trials of 0.5 * var(b - r) / var(b) = 0.2.
- Other dependencies: trial mean baseline attachment loss ~ N(8.0, 0.7^2) mm; trial mean gain 2.0 mm (SD 0.6); within trial true
  baseline SD 1.8 mm, error SD 0.86 mm (set so the mean over trials of the sample ratio is 0.2); correlation of true
  baseline and follow-up 0.7.
- `minus` sets to null: true follow-up SD 1.17 to 1.8 mm in every trial.
- Keys the error needs: the three brief keys.
- Effect parameters: true follow-up SD 1.17 mm; analytic within-trial slope of change on the mean level about -0.41 (claim:
  mean at most -0.20).
- Measured statistic: plus 0.2035 (sd 0.0257), minus 0.2035 (sd 0.0257). Tolerance 0.040.
- Control: follow-up values rescaled about the trial mean to the baseline SD, per trial.

## Ratio against covariate adjustment (CUR13)

### D-009 (60 mice)
- Structure: standardised difference of body mass between groups, 0.5 pooled SD (note's value).
- Other dependencies: 30 per group, assignment order random. Mass within group SD 3 g, group means 24.25 g (treated) and
  25.75 g (untreated). Force = 35 + 1.0 * mass + effect + noise, noise SD 4.5 mN: force is not proportional to mass
  (intercept 35 mN, 58% of the force at 25 g). Treated animals are lighter, so the per-mass force of the treated is higher without
  any effect.
- `minus` sets to null: the treatment effect on force at equal mass, +3.6 mN to 0.
- Keys the error needs: `body_mass`, `treated`, `peak_force` (all in the brief).
- Effect parameters: +3.6 mN (0.8 residual SD; analytic power of the adjusted comparison about 0.85).
- Measured statistic: plus 0.4936 (sd 0.2462), minus 0.4936 (sd 0.2462). Tolerance 0.100.
- Control: treatment labels permuted across animals.

### D-056 (3 groups x 25 rats)
- Structure: between-group share of the body mass sum of squares, 0.1 (null value 0.027).
- Other dependencies: body mass lognormal, mean 300 g, log SD 0.25 (mixed ages); group mean log shift -0.0875, 0, +0.0875.
  Uptake = 10 * (mass / 300)^0.67 * exp(group effect + noise), noise log SD 0.10; the exponent below 1 makes uptake not proportional to mass.
- `minus` sets to null: the group effects on log uptake at equal mass, (-0.03, +0.06, -0.03) to 0. The pattern is orthogonal to
  the order of the mass shifts, so the group effect does not align with the mass artefact.
- Keys the error needs: `body_mass`, `oxygen_uptake`.
- Effect parameters: group effects (-0.03, +0.06, -0.03) with residual log SD 0.10 (analytic noncentrality about 13.5,
  power about 0.9).
- Measured statistic: plus 0.0977 (sd 0.0582), minus 0.0977 (sd 0.0582). Tolerance 0.0146.
- Control: animals shuffled across groups with uptake and mass kept in pairs.

### D-072 (30 subjects, crossover)
- Structure: |mean area difference| / SD of area difference = 0.5.
- Other dependencies: subject area ~ N(75, 12^2) cm2; session deviation SD 2.12 cm2 in each session (difference SD 3.0 cm2); drug-session
  area +1.5 cm2 on average. Force = 400 + 3.5 * session area + subject effect (SD 60 N) + effect + session noise (SD 33 N, 5%): force is not
  proportional to area.
- `minus` sets to null: the drug effect on force at equal area, +28 N to 0.
- Keys the error needs: the four brief keys.
- Effect parameters: +28 N (analytic power of the adjusted paired comparison about 0.9).
- Measured statistic: plus 0.5162 (sd 0.1979), minus 0.5162 (sd 0.1979). Tolerance 0.100.
- Control: the two sessions swapped at random within subjects (force and area together).

## Cases where the note's value or the brief limits realism

- D-048, D-051, D-063 (STR87): at the notes' error shares (0.05, 0.1, 0.05) and realistic variability of consumption, the
  coupled cardiac output error alone creates a correlation of about 0.12, a within-dog slope of about 0.02, and an R-squared of
  about 0.015, far below the brief thresholds (0.40, 0.15, 0.25). The source says the effect is small in such settings. I did not
  tune consumption variability to enlarge it.
- D-002: about 0.15 against 0.30, with the arterial error share fixed at 0.1.
- D-001: moderate power of the corrected analysis (see D-001).
- D-009, D-056, D-072: the ratio artefact is real but modest (a fraction of an SD of the per-unit ratio).
- No structure value made a world impossible.

## Repairs

None requested.
