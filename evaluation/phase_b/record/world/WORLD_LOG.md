# World log

Conventions used in every skeleton: one private generator `_gen(rng, <switch>)` builds both worlds, so `plus` and `minus` consume the generator identically (paired draws) and differ only in the switch that carries the claim. `minus` sets the claimed quantity to its null and leaves every other quantity (noise, structure, artefacts such as shared denominators, selection hazards, measurement coupling) at its `plus` value. Controls break the theory by permuting or relabelling the variable that carries the claimed relationship inside the study's own units. I did not write or run any criterion; I only inspected shapes, dtypes, timing and descriptive quantities.

## W01
plus: femur and tibia share a limb-proportion factor; the true relative-length correlation is about 0.63 (threshold 0.4). minus: the two limb factors are independent (same variances); the correlation of the ratios is still about 0.37 because the vertebral column length is a shared denominator with its own error. Control: permute the tibia across skeletons. Judgement call: I let the artefact stay close to the threshold on purpose (it is part of "every other quantity unchanged").

## W02
plus: occupants lower energy intensity directly (-0.12 log units per sd of log occupants); observed Spearman about -0.52 (threshold -0.3). minus: that direct effect is 0, but intensity falls mildly with floor area (-0.08 per sd) in both worlds and occupants scale with area, so the raw rank correlation is still about -0.23. Control: permute occupants.

## W03
plus: treated mean +8 on sd 10 (d = 0.8, one-sided power about 0.85 with 30 per group); minus: no effect. Both arms share a small drift with recruitment order. Control: pool and re-split into arms. Judgement call: the stopping-rule hazard in the claim cannot be expressed in the data arrays; the recruitment order is kept in the row order so that a sequential analysis is possible.

## W04
plus: 150 distinct patients, 8 of 15 measurements shifted 1.0 sd by diagnosis (prevalence 0.4), plus 50 later rows that copy an earlier row and its diagnosis exactly. minus: no measurement carries information, the duplicated rows and their labels are unchanged (so a validation that lets a repeat see its original is rewarded even in minus). Control: permute diagnosis across distinct patients, repeats keep their original's label.

## W05
plus: 40% of the voxels of each subject are face selective (about 0.45 percent signal change face minus house, sd 0.15), 15% are house selective (-0.35); two runs, independent noise 0.45. minus: face selectivity set to 0, house-selective voxels kept; selecting voxels on the sign of the same data then yields a positive mean from noise alone. Control: scramble the voxel order of run 2 within each subject (breaks voxel identity across runs).

## W06
plus: 16 of 40 patients mutated; six of 20 features shifted 0.9 sd (patient-level d about 0.83 each, population AUC about 0.9); each patient has a random effect shared by its 6 patches. minus: shift 0; random effects and nesting unchanged (patch-level leakage across folds still looks like signal). Control: permute the mutation status across patients.

## W07
plus: 60% of 150 neurons are tuned (von Mises-like, amplitude about 7 spikes/s on a 2.5 spikes/s base, true index about 0.5 for tuned neurons); spike counts Poisson in a 0.5 s window, 16 repeats. minus: no neuron is tuned (amplitude 0), base rates and counting noise as in plus; picking the "preferred" orientation from 16 noisy repeats still gives a positive index (about 0.17 over all neurons, higher among neurons selected as tuned). Control: shuffle the responses across orientations and trials within each neuron.

## W08
plus: a latent program loads 0.6 on the five signature genes (columns 5-9 counting from 1, i.e. index 4:9) and drives sensitivity at 0.75; signature-score correlation about 0.64. minus: sensitivity is an independent draw with the same variance; expression unchanged. Other genes are pure noise so an off-by-one column choice dilutes but does not remove the signal. Control: permute sensitivity across cell lines.

## W09
plus: 12 of 40 voxels carry a true group difference of about 0.75 (voxel sd 1, subject offset sd 0.25), 14 + 14 subjects alternating. minus: no true group difference anywhere; choosing the voxels that favour the high-anxiety group on the same data produces a positive mean difference from noise alone. Control: permute the subjects (rows of react) relative to the group labels.

## W10
plus: everybody improves 2 points/session; the trained group gains 3.5 more per session (slope difference SE about 1.2, power about 0.8). minus: the two slopes are equal (both groups still improve, so a within-group test is significant). Control: pool the 28 participants and re-split at random.

## W11
plus: true turnover rate falls with log headcount (-0.6 log units per sd); with payroll heavy-tailed the linear R squared of rate on payroll is about 0.21 (threshold 0.1). minus: true rate independent of size (R squared about 0); leaver counts are Poisson so small firms have noisy rates. Control: permute payroll across firms. Judgement call: I did not add a ratio artefact beyond the shared headcount (payroll is proportional to headcount).

## W12
plus: ability sd 10, independent test noise sd 7, tutoring adds 7 points (sd 5) to the spring score; the lowest fifth of the autumn test gain about 12 points from autumn (5.6 of that is regression to the mean) and about 7 relative to the second pre-test. minus: no tutoring effect; the lowest fifth still gain about 5.6 from autumn because of regression to the mean. Control: subtract the average spring-minus-pretest gain (no average tutoring effect).

## W13
plus: contrast between 0.05 and 0.5 assigned between participants; attended slope -270 ms per unit contrast, unattended -150, participant speed (sd 60 ms) shared by both conditions, noise sd 20; slope difference SE about 40, power about 0.85. minus: both slopes -150 (each individually only borderline significant). Control: permute contrast across participants.

## W14
plus: eight AR(0.9) indicators, four of them enter the onset logit (0.9 each), plus a slowly moving unobserved hazard (AR 0.95); intercept calibrated per sample to 15% onsets; forward-in-time AUC of an ideal predictor about 0.8. minus: the indicator term is removed, the hazard (onsets cluster in time), the indicators and the prevalence are unchanged. Control: permute onset across rows.

## W15
plus: 25% of the 60 genes truly differ, |log2 FC| uniform 0.5 to 1 (mean 0.75), per-gene sd 0.5 to 0.9, 20 + 20 samples. minus: no gene differs (selecting genes that look different on the same data gives |log2 FC| around 0.5 from noise alone). Control: permute the tumour labels.

## W16
plus: onset 15%; six of twelve indicators shifted 0.7 sd in onset rows (shared factor 0.4); entries missing at 19% (non-onset) or 27% (onset), about 20% overall, filled with 0. minus: shifts removed; the informative missingness stays, so a model that reads the zero pattern still finds onset information (about AUC 0.68 from the missing count alone). Control: permute onset across rows.

## W17
plus: per-capita CO2 follows per-capita GDP (elasticity 0.8; Spearman about 0.8); populations very unequal (log sd 1.6). minus: per-capita CO2 independent of per-capita GDP (same marginals); the totals still correlate at about 0.74 through population. Control: permute per-capita emissions across countries and rebuild the totals with the original populations.

## W18
plus: 15 of 30 biomarkers shifted 1.1 sd in positives, prevalence 0.2 (about 20 positives), columns standardised; the nearest neighbour of a sample is usually of its own class (analytic argument, no classifier run). minus: shift 0. Control: permute the status across samples.

## W19
plus: 40% of the 60 voxels truly correlate with the trait (r 0.45 to 0.75, mean 0.6); the others 0; unit voxel variance; a subject-level global factor correlates all voxels. minus: no voxel correlates with the trait; picking the positively correlated voxels on the same 24 subjects inflates the mean correlation (the classic selection bias). Control: permute the trait across subjects.

## W20
plus: true correlations 0.15 (35 younger) and 0.60 (35 older), sample difference about 0.44, one-sided power about 0.75. minus: both 0.375 (equal), so each group alone is often significant. Control: permute recall in the older group. Judgement call: the pooled average 0.375 was used as the common value so that the overall amount of association is the same.

## W21
plus: 30% of 120 cells are excited (dF/F about +0.1, trial noise 0.1 per window, 30 trials), 7% suppressed (-0.05), slow fluctuations shared by the two windows. minus: excited cells removed, suppressed cells kept, so among cells that change significantly none is a genuine excitation. Control: randomly swap pre and post within each cell and trial.

## W22
plus: usual pressure 156 +- 13, entry noise sd 11, placebo response -2 mmHg in both arms, drug adds -10 mmHg (sd 4); about 64% of patients have entry pressure >= 150. minus: no drug effect beyond placebo, but regression to the mean (about -4.5 mmHg in the selected subset) plus the placebo response still make the drug arm fall by about 6.5 mmHg. Control: permute the drug labels.

## W23
plus: true infection rate falls with log beds (-0.22 log units per sd), admissions proportional to beds, Poisson counts; Pearson correlation of rate with beds about -0.49 (threshold -0.3). minus: no size effect on the true rate (correlation about 0). Control: permute beds across hospitals. Judgement call: I found no natural artefact in the ratio beyond heteroscedastic Poisson noise, so the world has none.

## W24
plus: residual correlation 0.5 between size-independent VO2max/kg and power/kg; both ratios also fall with body mass (exponents -0.3 and -0.25, mass log sd 0.18); R squared of per-kg power on per-kg VO2max about 0.4 (threshold 0.25). minus: residual correlation 0, the shared body-mass dependence stays (R squared about 0.1). Control: permute power per kg across athletes and rebuild absolute power with the original body mass.

## W25
plus: pond effect sd 0.4 and sample noise sd 0.3 on a log scale; fertilisation multiplies biomass by exp(0.9) = 2.5, a pond-level t of about 3 with 4 ponds per arm (power about 0.8). minus: multiplier 1, pond effects and layout unchanged (treating the 80 samples as independent would be badly anti-conservative). Control: reassign the 8 ponds to the two arms at random.

## W26
plus: true log resistance and log output correlate at -0.85 (sd 0.25 and 0.28), pressure = venous pressure + resistance x output / 80; the Spearman of resistance (computed with the Doppler output) with Doppler output is about -0.58, while resistance computed with the thermodilution output and correlated with that same output is about -0.8 (coupling). minus: true correlation 0; the coupled version still gives about -0.3, the independent one about 0. Control: give each patient another patient's resistance and rebuild MAP.

## W27
plus: 72 patients (47 A, 25 B), 8 of 60 genes shifted 0.7 sd (population AUC about 0.92), co-expression blocks of ten genes (0.4 loading). minus: shift 0 (feature selection on all patients before cross-validation would still inflate an AUC). Control: permute the subtype.

## W28
plus: true skill sd 8, block noise sd 6; total learning 6 points minus 0.6 per point of skill above 60, so the weaker half gains about 7 points more than the stronger half; with the split on block 0 the observed gap is about 11.7 (regression to the mean adds about 5.6). minus: every participant learns 6 points; the observed gap on block 0 split is still about 5.6. Control: give each participant the change scores of another participant relative to its own first block.

## W29
plus: oxygen consumption depends on delivery (0.26 mL/min per mL/min); correlation of expired-gas consumption with delivery about 0.68. minus: true consumption independent of delivery (same variance), correlation about 0; the venous saturation stays consistent with true consumption, and cardiac output carries a 15% thermodilution error, so Fick-derived consumption correlates with delivery about 0.25 even in minus. Control: permute the expired-gas consumption.

## W30
plus: six of ten features shifted 1.6 sd for the roughly 12% fraudulent transactions (Binomial, about 18 of 150), columns standardised. minus: shift 0. Control: permute the fraud labels.

## W31
plus: animal effect sd 0.35 (log scale) shared by both conditions, cell noise sd 0.45, drug multiplies amplitude by exp(0.30) (animal-specific sd 0.2); paired animal-level t about 3.5. minus: no drug effect, everything else equal (200 cells per arm would be pseudoreplication). Control: randomly swap drug and vehicle within each animal.

## W32
plus: both groups gain 3 points from retest practice, the trained group 6.5 more; pre-post correlation 0.75, sd 10, 20 per group (difference-in-gains t about 3). minus: equal gains (both still significantly positive). Control: pool the 40 participants (pre and post kept together) and re-split.

## W33
plus: responder status follows a dominant expression program (loading 0.8 on 20 genes) through a probit with coefficient 1.2 (ideal accuracy about 0.78); a second dominant nuisance program (batch-like) on another 20 genes; each gene has an arbitrary scale (0.2 to 5) and offset, which hurts PCA on unstandardised data. minus: responder status independent of expression (same 45% prevalence). Control: permute responder status. Judgement call: no accuracy was computed with any classifier; the plus accuracy is from the analytic argument.

## W34
plus: 40% of the 50 voxels carry the trait (loading 0.55 to 0.75), stable subject effects shared by the two sessions, session noise 0.7; the mean activity of the true voxels correlates about 0.7 with the trait (n = 16). minus: no voxel carries the trait; choosing voxels by their correlation with the trait in the same data still produces a high correlation. Control: permute the trait across subjects.

## W35
plus: 12 of 30 patients relapse, three of 20 markers shifted 1.4 sd; ideal-predictor AUC about 0.95 (a huge effect is needed for the claim to be true at n = 30). minus: no marker informative; with 20 markers on 30 patients a model fitted and scored on the same patients still looks excellent. Control: permute relapse.

## W36
plus: 62 tissues (40 cancer, 22 normal), 12 of 60 genes shifted 0.9 sd, co-expression blocks of ten genes. minus: no gene differs; the majority-class rate 0.645 stays. Control: permute the cancer labels.

## W37
plus: three indicators measure a persistent driver (AR 0.8, noise 0.8 each) that sets next-week admissions (coefficient 30 on a base of 300, plus an AR(0.7) residual of sd 25); three further indicators are slow drifts (AR 0.95); ideal forward R squared about 0.45. minus: admissions follow an equally persistent driver that no indicator measures; everything else unchanged. Control: permute the admissions across weeks.

## W38
plus: 10 + 10 samples, 10 of 60 genes shifted 1.3 sd (a large effect is needed for any claim to be true with n = 20). minus: no gene differs. Control: permute the labels.

## W39
plus: Poisson richness with mean 15 (unmown), mowing multiplies it by exp(0.38) = 1.46, plot effect sd 0.15, seasonal sine of amplitude 0.2, AR(0.5) noise across the 12 monthly surveys; plot-level t about 3. minus: multiplier 1 (the 72 monthly values per arm are far from independent). Control: reassign the 12 plots to the two arms at random.

## W40
plus: two outcome measures (r = 0.5, sd 10), treated mean +9 on measure 1 (d = 0.9, one-sided power about 0.85) and +7 on measure 2. minus: the primary effect is 0, the secondary keeps its +7 effect, so an analysis that picks the wrong column or the best of two columns finds an effect. Control: pool all 40 rows and re-split.

## W41
plus: lognormal true baseline rates (median 6 spikes/s), Poisson counts in 0.3 s epochs, the 30% truly lowest neurons rise by 4.5 spikes/s (sd 1.5), the others by 1. minus: the low group's effect is 0; the others keep +1. Choosing the lowest neurons by the same baseline data yields an apparent increase of about 2 spikes/s from regression to the mean when the mean of the two epochs is the baseline, and about 0.4 when the unselected epoch is the baseline. Control: replace the post count by a fresh Poisson draw from the neuron's estimated baseline (no manipulation effect).

## W42
plus: 6 animals per genotype, animal effect sd 0.35 and cell variability sd 0.7 (log scale), knockout multiplies rates by exp(0.6) = 1.8 (animal-level t about 3). minus: multiplier 1. Control: reassign the 12 animals to genotypes at random.

## W43
plus: yield per hectare rises with fertilizer per hectare (0.16 log units per sd; correlation of the per-hectare values about 0.55); farm sizes very unequal (log sd 1) so the totals correlate at about 0.89; the recorded area carries a 15% error that enters both ratios. minus: per-hectare yield independent of per-hectare fertilizer (per-hectare correlation about 0.1 from the area error, totals still about 0.8). Control: permute yield per hectare across farms and rebuild total yield with the recorded area.

## W44
plus: 10 participants, 2 sessions, between-participant correlation of true grip and thickness 0.8 (observed subject-mean correlation about 0.75, one-sided power about 0.85); the intervention shifts both measures a little (+3 kg, +0.1 mm) in both worlds. minus: between-participant correlation 0; treating the 20 measurements as independent would give a wrong significance level. Control: permute thickness across participants (both sessions together).

## W45
plus: dobutamine raises output by 35% on average (sd 25%); the true change in consumption follows the true change in delivery (0.25 per unit); thermodilution error 8% at each time, expired-gas error 8%; R squared of the measured changes about 0.46 (threshold 0.25). minus: true change in consumption independent of the change in delivery (same variance, same mean rise of 60 mL/min); Fick-derived changes still correlate with delivery changes (R squared about 0.1) through the shared errors. Control: permute the expired-gas consumption across patients.

## W46
plus: 12 tanks with doses 0 to 5 assigned at random, tank effect sd 0.8, mussel noise sd 1.5, true slope 0.45 per dose unit (tank-level t about 2.8). minus: slope 0 (using the 96 mussels as independent would be anti-conservative). Control: permute the doses over tanks.

## W47
plus: 20 countries x 15 years; high debt (> 90% of GDP) lowers growth by 2.2 points; countries with lower long-run growth carry more debt and weak growth raises next year's debt ratio in both worlds, so the observed gap in plus is about -3.2. minus: no causal effect; the observed gap is still about -1.0 from country confounding and reverse causation. Control: permute the debt records across countries. Judgement call: the 90% debt state is only about 20-25% of country-years.

## W48
plus: mean drug effect 0.6 (visual) and 0.15 (auditory), individual effect variation sd 0.3 (correlation 0.3), region baselines correlated 0.4, measurement noise 0.25; the difference of differences is about 0.45 with sd about 0.6 (power about 0.8). minus: both regions get the mean effect 0.375 (each region alone is clearly drug-responsive). Control: swap the region labels of a random half of the participants.

## W49
plus: 12 hospitals x 20 patients, 15 characteristics with a hospital-specific shift (sd 0.7) each; stay depends on six characteristics (signal variance 1.2), a hospital effect (variance 0.5) and noise (0.45); ceiling R squared in new hospitals about 0.56. minus: no patient-level effect; the hospital effect on stay and the hospital shifts in the characteristics stay, so a random split (which sees the same hospital in train and test) still finds structure. Control: permute stay among the patients of each hospital.

## W50
plus: 12 participants x 25 trials; reaction time and activity share a trial-level noise correlation of 0.2, participants' mean activity correlates 0.6 with their mean reaction time, and both drift upward across trials; within-participant correlation about 0.25, pooled about 0.34. minus: trial-level link 0, so the within-participant correlation is about 0.07 (drift only) while the pooled correlation is still about 0.2 through the between-participant link. Control: permute the activity values across trials within each participant.

## W51
plus: systolic pressure rises 7.5 mmHg per sd of relative heart weight (correlation about 0.48; threshold 0.3) and 10 mmHg per sd of body weight; relative heart weight is independent of body weight, so absolute heart weight is proportional to body weight. minus: no dependence on relative heart weight; the correlation of pressure with relative heart weight is about 0, with absolute heart weight about 0.58. Control: permute relative heart weight across rats and rebuild absolute heart weight.

## W52
plus: severity sd 8, assessment noise sd 6 at each visit, programme lowers the final score by 9 points (sd 4); among the top fifth at visit 0, 94% fall from visit 0 to visit 2 (about 83% compared with the second assessment). minus: no programme effect; regression to the mean alone makes about 73% of the top fifth fall from visit 0 (about 50% compared with visit 1). Control: subtract the average change from the second assessment to the last visit.

## W53
plus: true correlation of log end-diastolic volume index with ejection fraction -0.65 (observed with the independent radionuclide volume about -0.54); stroke volume = volume x fraction with thermodilution error 10% and thermistor error 0.04 in the fraction. minus: true correlation 0; the volume derived as stroke volume / ejection fraction still correlates about -0.22 with the fraction (coupling through the fraction's measurement error and the shared fraction). Control: permute the radionuclide volume across patients.

## W54
plus: seven of the eleven admission variables shifted 0.65 sd in sepsis (ideal admission-only accuracy about 0.8), 30% prevalence; column 11 (doses of the targeted therapy recorded during the stay) is about 3.5 for sepsis cases and 0.3 otherwise. minus: the admission variables carry no information but the dose count keeps its dependence on the diagnosis (a leak: the therapy follows the diagnosis), so a classifier that uses all twelve variables still reaches high accuracy. Control: permute the diagnosis across patients.

## Notes on the set as a whole
* The sample sizes, keys, shapes and dtypes follow the briefs; `plus` and `minus` differ only in the key(s) that the changed quantity touches (checked by comparing paired draws).
* Where the claim is a threshold (correlation at least c, accuracy at least a, mean at least m) the plus effect was set clearly above it (usually the true value is about 1.3 to 2 times the threshold) and the minus value at the null, not at the threshold. Observed minus values can still exceed the threshold through the artefacts that are deliberately left in (see each entry).
* No brief was impossible. The ones I judge ambiguous: W03 (the stopping rule is not representable in two arrays; I kept the recruitment order only), W16 (whether informative missingness belongs to the "indicators carry information" quantity; I treated it as a separate quantity that stays in minus), W41 and W47 (the null of a subgroup or threshold effect while a general effect remains elsewhere; I nulled only the subgroup), W54 (the leaking dose count is treated as a quantity that stays in minus).
* Effect-size checks used only descriptive quantities (correlations, mean differences, group sizes) computed on generated data; no classifier, cross-validation or test statistic was run, and the criterion functions are all `raise NotImplementedError`. Classifier worlds (W04, W06, W14, W16, W18, W27, W30, W33, W35, W36, W38, W54) rely on analytic separation arguments (Mahalanobis distance, nearest-neighbour distance gaps) for the claim to be true in plus.
