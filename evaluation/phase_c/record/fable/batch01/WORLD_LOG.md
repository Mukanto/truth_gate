# WORLD_LOG — batch01 (C01–C15)

General conventions used in every skeleton:

* `plus` and `minus` call one private generator `_gen(rng, <effect>)`, so they consume the random stream identically
  and differ only in the declared effect parameter.
* Controls are named module-level functions (not lambdas) returning `{**d, ...}`.
* No `null` world and no premises were declared. `relational` pairs were declared where a first-axis shuffle of the
  second key is a valid break of the claim (C01, C03, C06, C07, C10, C14).
* My own checks (200 draws per world, 20 control draws; script kept in the session scratchpad, not in the sandbox)
  covered: docstring equals `<id>: <claim>`, keys/shapes/dtypes, finiteness, call time (max 3.3 ms), control changes
  the data on every draw, and one descriptive statistic per brief to see the effect in `plus` and its absence in
  `minus`. No decision rule was written or tested. Truth_Gate was not run.

Two judgement calls that recur:

* **"A exceeds B" claims (C08, C15).** The null is "the two effects are equal". I set both to the average of their
  `plus` values, so the overall (pooled) effect keeps its `plus` value and only the difference is removed.
* **"Coefficient / partial association given a covariate" claims (C02, C09, C12, C13).** The association is generated
  directly on the part of the predictor not explained by the covariate, so the null is exact for the quantity named in
  the claim, and the marginal dependence of every variable on the covariate is unchanged in `minus`. Noise SDs are not
  re-scaled in `minus` (C02, C13: the outcome's conditional variance is therefore slightly smaller in `minus`; C09, C12:
  the effect is a correlation parameter, so variances are identical).

## C01
plus: 40 subjects (20/20, random order), 1000 genes with gene-specific mean/scale and 4 co-expression factors; 40 genes
differ between groups by about 1 noise SD (0.7–1.3, random sign), about 0.8 SD of total gene variance. minus: no gene
differs. Control: group labels permuted across subjects.
Effect size: chosen so an honestly validated classifier should reach roughly 0.9 balanced accuracy; with only 40
subjects a cross-validated estimate is noisy (SD about 0.06), so a true accuracy much closer to 0.60 would not be
detectable. Descriptive check: genes with |Welch t| > 4: 5.7 on average in plus, 0.3 in minus.

## C02
plus: 15 species with typical size 40–120 mm; body length CV 12%; abdomen = species ratio × body + deviation (3% of
size); claw = intercept + body term + coefficient × abdomen deviation + noise (2% of size). Mean within-species
coefficient of abdomen 0.35, species SD 0.07 (scaled with the mean so the null is exactly 0 in every species).
minus: coefficient 0; claw still scales with body, so claw and abdomen remain marginally correlated. Control: abdomen
length permuted among individuals within each species.
Check: mean coefficient 0.355 (SD over draws 0.037) vs 0.002 (0.031).

## C03
plus: subject traits (heart rate SD 8 bpm, cortisol SD 3.5) correlated 0.75; day noise SD 4 bpm and 3.5; observed
correlation of subject means about 0.71. minus: trait correlation 0. Control: cortisol rows (subjects) permuted
relative to heart rate.
Effect size: with 16 subjects a correlation near 0.7 is needed for about 0.9 power; this is large, forced by the
brief's size. Judgement call: day-to-day fluctuations of the two measures are correlated 0.3 within a subject in both
worlds (acute arousal), a property the claim is not about. It leaves a residual expected correlation of subject means
of about 0.014 in `minus` (observed mean 0.036, SD 0.26), which I judged negligible. Cortisol is floored at 1.0.

## C04
plus: true cardiac output (log-normal, CV 25%), arterial content (13.5 ± 2), delivery = CO × CaO2 × 10; true uptake
240 ± 40 mL/min correlated 0.70 with true delivery; venous content follows the Fick relation; measurement errors: CO
10%, CaO2 2%, CvO2 3%, expired-gas uptake 5% (independent of the others). Observed correlation of expired-gas uptake
with measured delivery about 0.63. minus: true uptake independent of delivery (correlation 0); Fick relation and
errors unchanged. Control: expired-gas uptake permuted across patients.
Judgement call: venous content is kept physically consistent in both worlds, so an uptake computed from the Fick
equation shares the cardiac-output measurement error with delivery in `minus` too; the claim is about the expired-gas
measurement, whose correlation with delivery is 0.005 on average in `minus`. Venous content is floored at 1.0 mL/dL.

## C05
plus: each participant has 30–50 face-selective voxels at participant-specific locations (faces − houses about 1.1) and
40 house-preferring voxels; inside the face region faces − bodies = 0.7 (participant SD 25% of the effect); outside it
faces and bodies have identical true responses; per-run voxel noise SD 0.7, run drift shared by the three conditions.
minus: inside the face region bodies are raised to the face response (difference 0), faces > houses unchanged, so the
region exists in both worlds. Control: face and body labels exchanged in a random half of the runs of each
participant.
Effect size: 0.7 inside the true region, so that a region estimated from part of the data (imperfect purity) still
yields clearly more than 0.3. Judgement call: the null was implemented by raising bodies, not lowering faces, to keep
the faces-versus-houses selectivity that defines the region. Check (all-voxel mean of faces − bodies, diluted by
design): 0.093 vs 0.000.

## C06
plus: 80 of 500 voxels have slope about 1.0 (0.6–1.4) percent signal change per unit contrast; 48 trials at each of
five contrast levels (0.0625–1); voxel noise SD 1.0 per trial plus a trial-wise fluctuation shared by all voxels
(SD 0.25). minus: slope 0 in every voxel. Control: contrast permuted across trials.
Judgement call: in `minus` no voxel follows contrast, so "the voxels whose responses follow contrast" is an empty set
in truth; the world still returns the same data layout. Check (slope of the all-voxel average, diluted): 0.156 vs
−0.004.

## C07
plus: 62 tissues (40 tumour, 22 normal, random order), 1000 genes with 4 co-expression factors; 12 strong marker genes
(about 1.5 SD of total gene variance) and 60 weak ones (about 0.4 SD). minus: no gene differs. Control: tumour labels
permuted.
Effect size: three strong markers give an expected true accuracy near 0.9. Judgement call: the class proportions
(40/62 = 0.645) are kept in `minus`, so always guessing "tumour" scores 0.645 there, below the claimed 0.70. Check:
genes with |Welch t| > 4: 11.4 vs 0.2.

## C08
plus: task effect 0.50 in region A (subject SD 0.26) and 0.10 in region B (subject SD 0.58, correlated 0.4 with A);
subject baselines shared between regions; block noise SD 0.1. Difference 0.40, SD of the within-subject difference
about 0.57 (d about 0.7, power about 0.9 at n = 24). minus: both effects 0.30 (the plus average). Control: region
labels exchanged in a random 12 of the 24 subjects.
Judgement call: region B is more variable than region A in both worlds, so in `minus` the same true effect is easier
to detect in A than in B. Check: mean difference 0.395 vs −0.005.

## C09
plus: true value uniform 20–100; each observer has own gain (0.75–1.0) and offset; error SD 8 with correlation 0.45
between observers (shared trial error). minus: error correlation 0, same error SD; estimates remain strongly
correlated through the true value. Control: trials sorted by true value, and within blocks of 10 neighbouring trials
observers 2 and 3 are shifted by different amounts, so each observer keeps its relation to the true value but loses
its trial partners.
Check: mean partial correlation 0.444 vs −0.005 (control 0.018). Responses are linear in the true value so that the
linear partial correlation is exactly 0 in `minus`.

## C10
plus: 40 cages (20 treated, random), 2 animals each; cage SD 3.5 g, animal SD 3 g (intra-cage correlation about 0.58);
compound lowers gain by 4.5 g (about 1.1 SD of a cage mean; power about 0.93 with the cage as the unit). minus: no
effect. Control: treatment labels permuted across cages.
Judgement call: the shared cage component is kept in `minus`, as the rule requires; the two animals of a cage are not
independent in either world.

## C11
plus: stable severity 55 ± 10; each visit adds fluctuation SD 10; true change over six months 13 ± 8; scores clipped
to 0–100. About 36% of patients have screening score ≥ 60, and about 0.58 of them improve by ≥ 10 from the start.
minus: mean true change 0 with the same spread (proportion about 0.27 from fluctuation alone). Control: start and
6-month scores exchanged for every patient (time order reversed), proportion about 0.08.
Judgement calls: (1) the null is "mean change zero", with the SD of individual change kept; the proportion is then
0.27, not 0. (2) A permutation of 6-month scores across patients does not break this claim (the mean improvement
survives), so the control reverses the time order instead. (3) Screening and start are separate noisy visits in both
worlds, so patients selected on a high screening score have lower scores on average at the start.

## C12
plus: humerus from a two-component (sex) mixture; femur and tibia linear in humerus with residual SDs 14 and 13 mm and
residual correlation 0.5. minus: residual correlation 0; marginal femur–tibia correlation stays about 0.6 through
humerus. Control: tibia lengths exchanged among skeletons with neighbouring humerus length (sorted blocks of 10).
Judgement call: the null is defined given humerus length itself (not a latent body size), so the claimed partial
correlation is exactly 0 in `minus`. Check: 0.501 vs 0.001.

## C13
plus: body mass 27 ± 3 g; kidney = 0.40 + 0.011 × (mass − 27) + deviation (SD 0.03 g); liver = 1.40 + 0.050 × (mass −
27) + 1.5 × kidney deviation + noise (SD 0.11 g); partial correlation about 0.38. minus: coefficient 0. Control:
kidney weights exchanged among mice with neighbouring body mass (sorted blocks of 10).
Effect size: the sampling SD of the coefficient at n = 150 is about 0.30 g/g, larger than the claim's threshold of
0.25, so a coefficient of 1.5 was needed for the claim to be demonstrable; in `minus` the estimate exceeds 0.25 by
chance in about a fifth of the draws. Check: 1.51 vs 0.01 (SD 0.30 both).

## C14
plus: 20 countries × 64 years; debt = country level (55 ± 22) + slow AR(1) swings (SD 18, rho 0.93), floored at 5;
about 11% of country-years above 90%, concentrated in a few countries; growth = 3 + country effect (SD 0.5) + world
cycle (AR(1), SD 1.2) + noise (SD 2) − 3.2 when debt > 90. minus: no dependence of growth on debt. Control: whole debt
histories reassigned to other countries (rows rolled by a random non-zero shift).
Effect size: 3.2 points; the pooled difference has a sampling SD of about 0.38 because high-debt years cluster in few
countries, so a true gap close to 2 could not be told from the threshold. Judgement call: no time trend and no
country-level link between debt and growth were added, because either would make the pooled difference non-zero in
`minus`. Check: −3.18 vs 0.02.

## C15
plus: 20 participants per group (random order); correlation 0.8 in group A and 0.0 in group B; groups differ in mean
task and symptom score. minus: correlation 0.4 in both groups (the plus average). Control: group labels permuted
across participants.
Effect size: very large, forced by the brief's size. With 20 per group the Fisher z difference has SE 0.34, so about
0.9 power needs 0.8 against 0.0; a realistic difference (for example 0.5 against 0.2) would have power below 0.2.
Check: mean difference of sample correlations 0.78 vs 0.00.

## Ambiguous or hard briefs
* C06: under the null the selected voxel set does not exist (see above).
* C11: a proportion threshold has no unique null; I used "no mean improvement" (see above).
* C08, C15: the common value under the null is not fixed by the brief; I used the plus average.
* C03, C15: the sizes in the brief only support very large effects.
* None was impossible to model.
