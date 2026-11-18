# Checklist log: dependence between units, per data key

For each brief: how the units of a real dataset of this kind depend on each other (order in time; groups, sites or
repeated measurements; components shared between variables; many variables relative to units), the size used and where
the size comes from. Every dependence listed here is generated identically in `plus` and `minus`; only the claimed
effect differs. Sizes are typical values from the applied literature of each field as I know it (no source was read for
this task), chosen at the moderate end.

## D-052 (pre, post, young; 40 participants)
- **Repeated measurements of the same unit.** `pre` and `post` share each participant's true ability (between-person SD
  9 points for young, 11 for old, on a scale centred near 50-60) plus independent session error SD 4: test-retest
  r = 0.84 (performance and cognitive tests typically 0.75-0.90). Because improvement = post - pre contains the `pre`
  error with a minus sign, change is negatively correlated with the baseline error; this follows from the design.
- **Groups.** Age group shifts baseline ability (young +8 points, about 0.8 SD, a typical age difference on performance
  tests) and spread (older adults more heterogeneous); between-person SD of the training gain 3.0 (young) / 3.5 (old).
- **Order in time / clusters.** Training given in 4 consecutive enrolment cohorts of 10: shared cohort effect on the gain,
  SD 1.0 point (ICC of the gain about 0.02; group-delivered training shows small instructor/group effects). Age is placed
  at random positions, so cohorts are mixed-age with chance imbalance.
- **Shared components.** True ability is the common factor of `pre` and `post`.
- **Many variables.** Not applicable (3 keys, 40 units).

## D-055 (X 1000x6, y 1000; days in order)
- **Order in time, X.** Each predictor = common slow factor, AR(1) with phi 0.9 (persistence of about 10 days, typical of
  daily weather/environmental/economic series), plus a predictor-specific AR(1) part with phi 0.6.
- **Shared components, X.** Common-factor loadings 0.40-0.70, so predictor intercorrelations 0.2-0.5. Each predictor has
  its own unit and scale.
- **Order in time, y.** Outcome noise AR(1) with phi 0.5 (lag-1 autocorrelation of daily outcomes is usually 0.3-0.6);
  day-of-week pattern (SD 0.25 of the noise SD, random weekday of day 0); slow drift of about 0.3 noise SD over the
  1000 days. The signal part of y has the persistence of the predictor process in both worlds (in `minus` it comes from
  an independent copy of that process with identical dynamics).
- **Shared between X and y.** None apart from the claimed effect. A seasonal or periodic component with the same period
  in X and y would itself let X predict y on future days, so neither world has one.
- **Consequence.** Autocorrelation reduces the effective sample size of a 300-day correlation to roughly 100 days; kept in
  both worlds. Many variables: 6 versus 1000 days, not applicable.

## D-056 (oxygen_uptake, body_mass; 3 groups x 25 rats)
- **Groups.** Group mean body mass 310 / 335 / 295 g (5-8% differences, typical of strain or diet groups); within-group
  SD 28 g (CV about 9%, typical of adult rat cohorts).
- **Clusters within groups.** Rats housed 5 per cage, 5 cages per group: cage effect on body mass SD 8 g and on log
  oxygen uptake SD 0.023 (ICC about 0.05; cage effects on physiological measures are usually 0-0.1).
- **Order in time.** Respirometry on 5 days, one rat of each cage per day (balanced across groups): day effect SD 0.03 on
  log oxygen uptake (about 3% calibration drift).
- **Shared components.** Oxygen uptake scales with body mass as mass^0.75 (Kleiber; resting uptake about 5 mL O2/min at
  300 g); residual SD 0.095 on the log scale (inter-individual variation of resting metabolic rate after mass adjustment
  is usually 8-12%).
- **Many variables.** Not applicable.

## D-062 (femur, humerus, body_length; 12 species x 30 individuals)
- **Groups (species).** Species mean head-and-body length log-uniform 70-300 mm; species limb proportions correlated across
  species (r about 0.6, shared locomotor ecology); species-specific allometric slopes (0.90 and 0.85, SD 0.05).
- **Sites within species.** 3 sampling sites of 10 individuals per species: site effect on body size SD 3%.
- **Shared components.** Both bones scale with body length (within-species r(bone, body length) about 0.8); body length
  is the common covariate. Residual SD of log bone length 4.5% (femur) and 5% (humerus), including about 0.5% caliper
  error. A site or sex effect on limb proportions shared by both bones would itself be a femur-humerus link beyond body
  length (the claimed quantity), so sites act on size only.
- **Many variables.** Not applicable (3 keys, 30 per species).

## D-064 (expression 80x1500, clinical 80x8, response 80)
- **Shared components, expression.** 10 co-expression modules of 75 genes, loadings 0.40-0.85 (module structure, a few
  components explaining a large share of variance, as in tumour transcriptomes); 750 genes outside modules. Gene means
  3-12 log2 units, gene SDs 0.15-2.
- **Groups / order.** 4 processing batches of 20 consecutive patients: gene-specific shifts SD 0.25 x gene SD (about 6% of
  gene variance; batch effects in expression data are commonly 5-20%). Batches do not affect response in either world.
- **Shared components, clinical.** Correlated covariates (tumour size-stage 0.5, stage-nodal status 0.45, age-performance
  status 0.3, others 0-0.25); sex and nodal status binary; tumour size and grade load on the proliferation module
  (0.30 and 0.35, the usual link of proliferation signatures with grade and size). Standardised within the sample.
- **Response.** Percentage shrinkage, mean 30, SD 25, capped at 100 (complete response).
- **Many variables relative to units.** 1500 genes for 80 patients (p/n about 19), the main hazard; kept in both worlds.

## D-066 (X 1000x15, y 1000)
- **Shared components, X.** Three physiological blocks of 5 measurements (cardiometabolic, haematological/inflammatory,
  renal/hepatic) with within-block correlation 0.35 / 0.30 / 0.30 (typical intercorrelation of related vitals and labs).
  Four laboratory values right-skewed (log-normal, sigma 0.45 on the log scale, as for CRP, ferritin, creatinine, ALT).
- **Groups / order.** 4 enrolment sites of 250 consecutive patients: site shift SD 0.15 SD in every measurement
  (calibration and case-mix differences).
- **y.** Prevalence 7%, the same at every site in both worlds (a site-prevalence link combined with site shifts in X
  would itself be information on y).
- **Many variables relative to units.** 15 measurements for 1000 patients, but only about 70 cases.

## D-067 (kidney_weight, heart_weight, body_mass; 60 rats)
- **Groups.** 3 cohorts of 20 killed at different ages: cohort mean mass 340 / 380 / 420 g (plus or minus 10 g), within-cohort
  SD 30 g.
- **Clusters.** Cohort (dissection day) offsets on each organ weight, independent between organs, SD 2.5% (about 9% of
  residual variance; trimming and blotting differ between days). An offset shared by both organs would itself be a
  mass-independent kidney-heart link (the claimed quantity), so offsets are organ-specific.
- **Shared components.** Both organs scale with body mass (allometric exponent 0.85; r(organ, mass) about 0.77, typical of
  rat organ-weight data); individual residual SD 7.8% for each organ.
- **Many variables.** Not applicable.

## D-068 (head_width, wing_length, body_length; 25 populations x 40 specimens)
- **Groups (populations).** Mean body length SD 0.8 mm across populations (about 7%, clinal size variation); an environmental
  population factor shifts mean head width (0.06 mm per SD) and mean wing length (0.25 mm per SD) beyond body length, so
  head width and wing length are associated between populations (not the within-population quantity of the claim);
  population-specific intercept noise (0.04 mm and 0.15 mm).
- **Shared components.** Within populations head width scales with body length (0.15 mm/mm, r about 0.7) and wing length
  with body length (0.52 mm/mm, r about 0.75); residual SDs 0.12 mm (head width) and 0.36 mm (wing), including
  micrometer error (about 0.02 mm and 0.1 mm). Between-population SD of the claimed coefficient 0.15.
- **Many variables.** Not applicable.
