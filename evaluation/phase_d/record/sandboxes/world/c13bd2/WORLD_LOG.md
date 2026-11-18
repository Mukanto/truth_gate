# World log (Phase D, batch c13bd2)

General rule used in every skeleton: `plus` and `minus` call one generator `_world(rng, effect)` that draws exactly
the same random numbers in the same order. The quantity that carries the claim is driven, in `minus`, by an
independent copy of its cause with the same distribution (copied labels, copied latent scores, a copied process, or a
random reassignment), so every key keeps its `plus` distribution and only the claimed relationship is nulled. With the
gate's pairing (minus generated with the plus seed) only the effect-carrying key differs (checked for all 12). Effect
sizes below are population values computed from the generating parameters, not from any analysis of generated data.

## D-007 (expression predicts survival, out-of-sample R^2 >= 0.10)
- `plus`: 50 x 2000 log2 expression with 8 co-expression modules, 4 processing batches, sample normalisation shift;
  log survival = log 20 - 0.45 x proliferation score + 0.20 x immune score + N(0, 0.62^2), no censoring (per brief).
  Oracle R^2 0.39 (log scale), 0.32 (raw months): a strong but plausible prognostic signature, so that a predictor
  learned from 50 patients can reach 0.10 without the effect being huge.
- `minus`: survival driven by independent copies of the two module scores (expression unchanged, survival distribution
  unchanged). Control: survival permuted across patients.

## D-008 (mean within-patient slope of VO2 on DO2 >= 0.1)
- `plus`: 40 patients x 6 occasions; true VO2 = patient level (scaled by body size) + slope_i x (true DO2 - usual DO2)
  + metabolic AR(1) noise, slope_i ~ N(0.25, 0.08). Measured CO (CV 6%), one Hb measurement shared by both contents
  (CV 2%), saturations, and an independent expired-gas VO2 (CV 6%). DO2 measurement error attenuates the observable
  slope to about 0.21; 0.25 is the size reported for pathological supply dependency and leaves room above 0.1.
- `minus`: true VO2 driven by an independent copy of the DO2 fluctuations (slope 0 within patients). Judgement call:
  the venous content changes with VO2 because it is tied to it by the Fick principle (its SD is about 10% larger in
  `minus`); CO and arterial content are unchanged. The Fick-derived VO2 shares CO and Hb errors with DO2 (coupling
  bias about +0.05) in both worlds. Control: the consumption side (expired-gas VO2 and venous content, jointly)
  permuted across occasions within each patient.

## D-010 (district + 3 covariates predict y, r >= 0.25)
- `plus`: 1200 patients in 150 districts of uneven size (0-45 patients, ~6 empty); y depends on age, BMI, SBP
  (explained share ~0.10) and a district effect (ICC 0.06, partly tied to a deprivation index that also shifts BMI and
  SBP). Oracle r 0.41; with district means shrunk at ~8 patients per district about 0.35, a moderate, typical effect.
- `minus`: y built from an independent copy of the cohort (same districts and effects, re-drawn patients), so neither
  the observed districts nor the covariates carry information. Control: y permuted across patients.

## D-011 (expression distinguishes AML from ALL, AUC >= 0.90)
- `plus`: 72 samples (25 AML, 47 ALL; the brief gives no split, so the classic proportions), two collection batches,
  8 lineage-unrelated modules; a 40-gene lineage programme whose score differs by 2.4 within-type SD between types
  (oracle AUC 0.955) plus 40 weak independent differences (oracle AUC 0.98). The types are biologically very distinct,
  so a well-designed study expects an AUC in the mid 0.90s.
- `minus`: the type-related shifts follow an independent copy of the labels with the same class sizes. Control:
  myeloid labels permuted across samples.

## D-012 (fenced minus open occupancy >= 0.10 and significant, one-sided 0.05)
- `plus`: 10 plots (5 fenced, assumed balanced), 30 quadrats each; occupancy from a latent probit model with plot
  random effect (SD 0.3), shore shift (SD 0.2) and AR(1) patchiness along the transect (rho 0.5). Expected occupancy
  0.32 open vs 0.65 fenced (difference 0.33): grazer exclosures typically have large effects, and with only 5 plots per
  arm a smaller difference would leave a plot-level test badly underpowered.
- `minus`: the fence effect follows an independent copy of the fence assignment, so occupancy is unrelated to the
  observed exclosure. Control: exclosure labels permuted across plots (always a changed assignment).

## D-022 (66-term polynomial OLS predicts new runs, r >= 0.30)
- `plus`: 300 runs in production order; readings driven by a drifting process state (AR(1) 0.8), own AR(1) drifts and
  feedstock lots of 10 runs, with sensor noise; quality = quadratic function of the readings (terms inside the
  polynomial basis) explaining 30% of its variance, plus lot effect and AR(1) drift. Rough expected new-run r of the
  66-term fit about 0.43, i.e. the effect clears 0.30 despite the overfitting penalty without being large.
- `minus`: quality driven by an independent copy of the process with the same time structure. Control: y circularly
  shifted against X by 30-270 runs (keeps autocorrelation, breaks alignment). Relational pair (X, y) added.

## D-023 (beetles: partial corr(head, wing | body) >= 0.30)
- `plus`: 2000 specimens from 12 localities; log head and log wing depend allometrically on size (slopes 0.9, 1.1),
  share a factor beyond size, and have own variation, locality offsets and 1% measurement error; body length has 1%
  error. Population partial correlation 0.40 (of which ~0.06 comes from residual size). A moderate effect; n = 2000
  makes it clearly separable from 0.30.
- `minus`: wing length built from an independent copy of size drawn from its distribution given measured body length
  and from an independent copy of the shared factor: population partial correlation exactly 0, (body, wing) and
  (body, head) distributions unchanged. Judgement call: the null is defined on the stated quantity (partial
  correlation given measured body length), not on "true size". Control: wing permuted within blocks of 10 specimens
  of similar body length.

## D-027 (OLS on 25 measurements, MAE improvement >= 10% for new samples)
- `plus`: 60 samples, 25 measurements from 3 latent factors with measurement error and two assay runs; y linear in the
  true values, population R^2 of the best linear predictor from X = 0.70. With 26 parameters on 60 samples the
  new-sample error of OLS is inflated by roughly 1.8-2.2x, so an R^2 near 0.7 is what the claim needs (expected
  improvement ~0.18-0.27); a smaller R^2 would make the claim false even with a real relationship.
- `minus`: y driven by an independent copy of the true values. Control: y permuted across samples.

## D-035 (classifier balanced accuracy >= 0.65)
- `plus`: 1500 records, prevalence 15% (not given in the brief; chosen to make class imbalance realistic), 20
  variables from 3 latent factors, 8 log-normal lab values, 4 sites with calibration offsets (same prevalence); the
  positive class is shifted on 9 variables, Mahalanobis distance ~1.32, best attainable balanced accuracy ~0.745.
- `minus`: the class shift follows an independent copy of the labels. Control: labels permuted across records.

## D-040 (skulls: partial corr(breadth, height | length) >= 0.2)
- `plus`: 300 skulls, both sexes (dimorphism 1.5 SD of general size), three burial phases with independent offsets in
  breadth and height, a general size factor, a vault factor shared by breadth and height, 1 mm measurement error.
  Population partial correlation 0.35 (0.18 from residual size, the rest from the vault factor): moderate, with
  reasonable power at n = 300 against 0.2.
- `minus`: height built from an independent copy of size drawn from its exact conditional distribution given
  measured length (sex mixture included) and an independent copy of the vault factor: partial correlation 0. Same
  judgement call as D-023. Control: height permuted within blocks of 10 skulls of similar length.

## D-042 (1-NN on standardised descriptors predicts new compounds, r >= 0.30)
- `plus`: 1200 records of 900 unique compounds (300 replicate records with identical descriptors), 80% of compounds
  in 60 congeneric series clustered in descriptor space; activity = series level + global and local SAR +
  compound-specific part; records add assay-source offsets and replicate noise (replicate ICC ~0.8). Approximate
  new-compound 1-NN r ~0.44 (series-level similarity), moderate.
- `minus`: compound activities reassigned at random across unique compounds (replicates still share their compound's
  value). Control: compound-mean activity permuted across compounds, within-compound deviations kept. Relational pair
  (X, y) added. Judgement call: "records" vs "new compounds" read as replicate measurements of some compounds.

## D-047 (>= half of patients with screening >= 60 improve >= 10 points from entry to week 12)
- `plus`: 600 patients, 20 sites; stable severity, OU symptom fluctuation (time constant 4 weeks), rating error;
  true improvement entry -> week 12 ~ N(14, 8). Proportion in the selected group ~0.67 (realistic treatment effect on a
  0-100 severity scale; selected group ~185 patients).
- `minus`: mean true change set to 0, between-patient spread of change kept (the null of an improvement claim). The
  proportion is then ~0.32, which includes the regression to the mean carried from screening into entry. Control:
  entry and week 12 swapped at random within each patient.
