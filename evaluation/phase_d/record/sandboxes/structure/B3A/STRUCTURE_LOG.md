# STRUCTURE_LOG, structure author B3A (Phase D, class B-3, 15 cases)

Common method. Each `reference.py` holds a generator `_gen(rng, effect_parameter)`. `plus` calls it with the claimed effect,
`minus` with the null of that effect; everything else in `_gen` is identical in both worlds. Structure statistics were
measured with the note's own `stat` code on 200 draws of each world (my own seeds, `SeedSequence([4242, world, i])`). No
analysis that could serve as a criterion was written or run; the claimed effect is set by the parameters below and is not
estimated from samples. All checks (keys, shapes, dtypes, finite values, call time at most 1 ms, control returns changed
data with the same keys, shapes and dtypes) passed. Every criterion is the placeholder `raise NotImplementedError`.

Measured statistic: mean (sd over draws) on 200 samples. "eq" = |mean_plus - mean_minus| against 3 SE.

Online sources: one fetch, listed at the end. The settings of PEA97, KRO93 and ARC81 come from the abstracts only (no
numbers); sizes there are my own and are justified per case.

## BMI family (source CHI13): D-006, D-015, D-053, D-037

Setting values from the full text (Simulations): 500 children, true BMI at age 5 mean 15.0, SD 1.2; yearly slope mean 0.4,
slope SD 0.2 (realistic scenario; 0.4 in the alternative); measurement-error SD 0.3 (ICC about 95%) or 1.2 (ICC about 50%);
the source's level-slope correlation is +0.6. Linear individual growth, as in the text.

Common dependencies in all four: between-child level SD 1.2, between-child slope SD 0.2, linear true trajectories, independent
measurement error at every reading (D-006 error SD 0.3, giving 0.3^2 / (1.2^2 + 0.3^2) = 0.059; D-015, D-053, D-037 error SD 0.275,
giving 1 - ICC = 0.0499 so that the approved 0.05 is met).

### D-006
- Structure value: approved 0.06 = resid_var / var(first visit) = error variance share. Source: CHI13 simulation (SD of error 0.3 against level SD 1.2).
- Other dependencies: slope mean 0.4 per year, slope SD 0.2, level SD 1.2, linear trajectories, error SD 0.3 independent at each of the 6 visits.
- `minus` sets to null: the correlation between a child's true level at age 5 and true yearly slope, from -0.5 to 0 (level SD, slope SD, error unchanged).
- Keys the error needs: none beyond `bmi`.
- Generator parameters: `rho = -0.5` in plus (true level-slope correlation), 0 in minus.
- Measured: plus 0.0592 (0.0043), minus 0.0590 (0.0043); target 0.06 +- 0.012; eq diff +0.0003 vs 3 SE 0.0013.
- Control: `permute_change_profiles`, the within-child deviation profile (visit minus first visit) is permuted across children; level kept.

### D-015
- Structure value: approved 0.05 = 1 - corr(baseline, retest) (ICC 95%, CHI13 Results).
- Other dependencies: as above; `bmi_baseline_retest` is a second reading at the same visit (independent error); follow-up = level + 5 x slope + error.
- `minus` sets to null: the correlation between true baseline level and true five-year change, from +0.6 (the source's value) to 0.
- Keys the error needs: `bmi_baseline_retest` is in the brief (the correction uses it); no key is added.
- Generator parameters: `rho = +0.6`, 0 in minus (true share of change variance explained by baseline level is rho^2 = 0.36 in plus).
- Measured: plus 0.0499 (0.0042), minus 0.0498 (0.0044); tolerance +-0.010; eq diff +0.0001 vs 3 SE 0.0013.
- Control: `permute_change`, the follow-up minus baseline change is permuted across children (retest kept).

### D-053
- Structure value: approved 0.05, same statistic and source as D-015.
- Other dependencies: as D-015.
- `minus` sets to null: correlation between true baseline level and true five-year change, from -0.5 to 0.
- Keys the error needs: `bmi_baseline_retest` (brief key, used by the correction).
- Generator parameters: `rho = -0.5` plus, 0 minus (slope SD 0.2, change SD from slope 1.0).
- Measured: plus 0.0499 (0.0042), minus 0.0498 (0.0044); eq diff +0.0001 vs 3 SE 0.0013.
- Control: `permute_change`, as D-015.

### D-037
- Structure value: approved 0.05 = error variance (from the 100 x 2 retest sample) over variance of baseline BMI; CHI13 ICC 95%.
- Other dependencies: as above; `bmi_retest` is a separate test-retest sample of 100 children from the same level distribution, two sessions with independent error SD 0.275.
- `minus` sets to null: correlation between true level and true five-year change, from -0.5 to 0.
- Keys the error needs: `bmi_retest` (brief key).
- Generator parameters: `rho = -0.5` plus, 0 minus. True slope of true change on true level = 5 x rho x 0.2 / 1.2 = -0.417 in plus, 0 in minus.
- Measured: plus 0.0503 (0.0077), minus 0.0501 (0.0075); tolerance +-0.010; eq diff +0.0002 vs 3 SE 0.0023.
- Control: `permute_change` (retest sample unchanged).

## Cardiac-output family (source ARC81): D-008, D-071, D-036

Sizes are mine (abstract has none). Measurement errors of cardiac output are set to log-SD 0.15 for both thermodilution and Fick-type
measures (published method precision about 10 to 20%). Mean values: cardiac output about 5 L/min, arterial O2 content about 17 mL/dL,
VO2 about 250 mL/min. Venous O2 content is generated from the physiological identity Cv = Ca - VO2 / (10 CO) with an assay error of 0.3 mL/dL,
so the Fick consumption computed from the keys, CO x (Ca - Cv) x 10, equals true VO2 times exp(CO error) plus assay terms.

### D-008
- Structure value: approved 0.9; source: the note's own computation, 0.0625 / (0.0625 + 0.0064) for within-patient CVs 0.25 and 0.08.
- Other dependencies: between-patient log SD of CO 0.25, of Ca 0.12, of VO2 0.20; within-patient log SD of true CO 0.20 (observed 0.25 with error 0.15), of true Ca 0.075 (observed 0.081 with error 0.03); VO2 noise 15 mL/min; expired-gas measurement error log SD 0.07; venous assay error 0.3 mL/dL; VO2 floored at 60 and Cv at 2 (rarely active).
- `minus` sets to null: the within-patient slope of true VO2 on true delivery, from mean 0.18 (relative SD 0.33 across patients) to exactly 0.
- Keys the error needs: `venous_o2_content` and `arterial_o2_content` with `cardiac_output` (Fick consumption is computed from them); all four are in the brief.
- Generator parameters: `beta_mean = 0.18` mL/min per mL/min (patient slopes 0.18 x (1 + 0.33 z)); 0 in minus.
- Measured: plus 0.9122 (0.0383), minus 0.9107 (0.0379); tolerance +-0.18; eq diff +0.0014 vs 3 SE 0.0114.
- Control: `permute_vo2_across_patients`, the expired-gas consumption series are permuted across patients.

### D-071
- Structure value: approved 0.85; source: the note (0.09 / (0.09 + 0.0144)).
- Other dependencies: log SD of true CO 0.225 plus error 0.15 (observed 0.27); true Ca log SD 0.137 plus error 0.03 (observed 0.14); correlation of true log CO and log Ca -0.12 (anaemia compensation); VO2 median 250, true log SD 0.205, expired-gas error 0.08; assay error 0.3 mL/dL.
- `minus` sets to null: the correlation between log true delivery and log true consumption, from 0.75 to 0; the consumption variance is kept.
- Keys the error needs: `venous_o2_content`, `arterial_o2_content`, `cardiac_output` (shared term of the calculated quantities); all in the brief.
- Generator parameters: `rho = 0.75` plus, 0 minus (log scale, before measurement error).
- Measured: plus 0.8545 (0.0728), minus 0.8547 (0.0742); tolerance +-0.17; eq diff -0.0002 vs 3 SE 0.0221.
- Control: `permute_vo2`.

### D-036
- Structure value: approved 0.3 = CV of thermodilution cardiac output; source: the note ("proposed mixed patient series").
- Other dependencies: true CO log SD 0.218 and thermodilution and Fick errors each log SD 0.15 (observed CV 0.27); perfusion pressure MAP - CVP median 85 mmHg with log-noise SD 0.10; CVP gamma(6, 1.2), mean 7.2 mmHg; the two CO measures have independent errors.
- `minus` sets to null: the dependence of true systemic vascular resistance on true cardiac output. Plus: log(MAP - CVP) rises with log CO with elasticity 0.35, so resistance falls with CO (true correlation of log resistance and log CO about -0.82, true R-squared about 0.67; with the Fick measure about 0.45 after attenuation by reliability 0.68). Minus: elasticity 1.0, pressure scales with flow, so resistance is independent of CO.
- Consequence stated: in minus the MAP - CVP distribution is wider (log SD about 0.22 against 0.14 in plus) because independence of resistance and flow forces pressure to carry the flow variation. The keys `mean_arterial_pressure` and `central_venous_pressure` therefore do not keep their plus distribution in minus; the structure statistic (CO CV only) is unaffected.
- Keys the error needs: `mean_arterial_pressure`, `central_venous_pressure` and `co_thermodilution` (the resistance is calculated from them), `co_fick` (independent measure for the correction); all in the brief.
- Generator parameters: `b = 0.35` plus, `1.0` minus.
- Measured: plus 0.2677 (0.0219), minus 0.2677 (0.0230); tolerance +-0.06; eq diff -0.0001 vs 3 SE 0.0067.
- Control: `permute_co_fick`, the Fick cardiac output is permuted across patients.

## Ratio / common-denominator family (source KRO93): D-017, D-031, D-038, D-050

### D-017
- Structure value: approved 0.1 = |point-biserial correlation of smoker and height|. Mechanism: mixed-sex sample (50% male), male height 176 (SD 7), female 163 (SD 6.5); smoking 26% in men, 15% in women, so smokers are about 2.2 cm taller (true correlation about 0.094).
- Other dependencies: FVC = -4.0 + 0.05 x height + noise SD 0.45 L (intercept makes FVC non-proportional to height); no sex effect on FVC beyond height (sex is only a latent source of the height-smoking link, not a key).
- `minus` sets to null: the smoker effect on FVC at a given height, from -0.30 L to 0.
- Keys the error needs: none beyond the three brief keys (height is the denominator).
- Generator parameters: `delta = 0.30` L plus, 0 minus.
- Measured: plus 0.0959 (0.0361), minus 0.0944 (0.0409); tolerance +-0.02; eq diff +0.0015 vs 3 SE 0.0116.
- Control: `permute_smoker_within_height`, smoker labels permuted within blocks of 60 subjects of similar height.

### D-031
- Structure value: approved 0.3 = |corr(median age, population)|; set by a loading of -0.3 of age on standardised population (larger cities somewhat younger).
- Other dependencies: population lognormal, median 60 thousand, log SD 0.8; median age mean 38, SD 4.5; log offences = log 20 + 1.15 x log population + effect x standardised age + noise SD 0.30 (superlinear scaling, so offences are not proportional to population).
- `minus` sets to null: the effect of median age on log offences, from -0.25 per SD of age to 0.
- Keys the error needs: none beyond the brief.
- Generator parameters: `beta = -0.25` per SD of age on the log scale (partial correlation on the log scale about -0.6; on raw offences, not estimated, smaller).
- Measured: plus 0.3014 (0.0399), minus 0.2999 (0.0392); tolerance +-0.06; eq diff +0.0015 vs 3 SE 0.0119.
- Control: `permute_age_within_population`, ages permuted within blocks of 25 cities of similar population.

### D-038
- Structure value: approved 0.3 = |corr(per-capita sales, population)|. Set by a loading of 0.25 of log per-capita sales on standardised population (calibrated by running the note's stat; load 0.6 gave 0.74, so reduced).
- Other dependencies: population lognormal, median 9 million, log SD 1.1; per-capita sales median 1500 cigarettes per person-year, log SD 0.45; lung-cancer death rate 0.3 thousand per million inhabitants (30 per 100 000) with log noise SD 0.30; deaths proportional to population in both worlds.
- `minus` sets to null: the elasticity of the death rate to per-capita sales, from 0.6 to 0.
- Keys the error needs: none beyond the brief.
- Generator parameters: `beta = 0.6` plus, 0 minus (deaths = 0.3 x pop x (per-capita sales / 1500)^beta x noise).
- Measured: plus 0.2940 (0.1179), minus 0.3031 (0.1163); tolerance +-0.06; eq diff -0.0091 vs 3 SE 0.0351. The statistic is noisy per draw (heavy-tailed population); the mean over 200 draws is within tolerance.
- Control: `permute_per_capita_sales`, per-capita sales permuted within blocks of 15 countries of similar population, sales rebuilt as permuted rate x population.

### D-050
- Structure value: approved 0.8 = |corr(age, body mass)|; saturating growth curve 520 x (1 - exp(-0.028 (age - 30))) with lognormal noise SD 0.12, age uniform on 45 to 150 days.
- Other dependencies: log liver = log 0.06 + 0.9 log body mass + effect x standardised age + noise SD 0.10 (liver grows less than proportionally with body mass).
- `minus` sets to null: the effect of age on log liver mass at a given body mass, from -0.17 per SD of age to 0 (relative liver size falls with age in plus).
- Keys the error needs: none beyond the brief.
- Generator parameters: `beta = -0.17` per SD of age; the unique share of liver variance due to age is about 0.2 on the log scale by algebra (not estimated from samples).
- Measured: plus 0.8129 (0.0352), minus 0.8158 (0.0375); tolerance +-0.16; eq diff -0.0029 vs 3 SE 0.0109.
- Control: `permute_age_within_mass`, age permuted within blocks of 10 rats of similar body mass.

## Index family (source PEA97): D-020, D-040, D-062, D-067

### D-020
- Structure value: approved 0.35 = expression of the three CVs; CVs set to 0.12 (body mass), 0.15 (heart), 0.18 (liver) on the log scale (observed CVs 0.120, 0.151, 0.181).
- Other dependencies: log heart on log body mass slope 0.6; log liver on log body mass slope 0.8; weighing error log SD 0.02 on each organ; medians 28 g, 0.14 g, 1.5 g.
- `minus` sets to null: the dependence of log liver on the mass-independent part of log heart, from 0.6 to 0; the liver residual variance is raised so that the liver CV (and so the structure value) is unchanged.
- Keys the error needs: none beyond the brief.
- Generator parameters: `c_heart = 0.6` plus (unique share of log liver variance from heart about 0.19 by algebra), 0 minus.
- Measured: plus 0.3450 (0.0094), minus 0.3456 (0.0088); tolerance +-0.07; eq diff -0.0007 vs 3 SE 0.0027.
- Control: `permute_heart_within_mass`, heart weights permuted within blocks of 100 mice of similar body mass.

### D-040
- Structure value: approved 0.5, the equal-CV reference case; all three CVs 0.035 (length 185 mm, breadth 142 mm, height 132 mm; caliper error 1 mm included in the CV).
- Other dependencies: latent correlation breadth-length 0.15 and height-length 0.15; caliper error 1.0 mm on each dimension.
- `minus` sets to null: the partial correlation of breadth and height given length, from 0.35 to 0.
- Keys the error needs: none beyond the brief.
- Generator parameters: `partial = 0.35` plus, 0 minus.
- Measured: plus 0.5034 (0.0268), minus 0.4959 (0.0259); tolerance +-0.10; eq diff +0.0075 vs 3 SE 0.0079 (close; the two worlds have identical marginals, so this is chance).
- Control: `permute_height_within_length`, height permuted within blocks of 30 skulls of similar length.

### D-062
- Structure value: approved 0.5, mean over species; within-species CVs near 0.05 each, varying across species (log SD 0.10), mean 0.4958 to 0.4987 over the two worlds.
- Other dependencies: species means (body length median 150 mm, log SD 0.4 across species; femur 0.20 and humerus 0.17 of body length with log SD 0.10 across species); within-species correlation of each bone with body length 0.4.
- `minus` sets to null: the within-species partial correlation of femur and humerus given body length, from a mean of 0.4 (SD 0.15 across species, clipped to +-0.9) to exactly 0 in every species.
- Keys the error needs: none beyond the brief.
- Generator parameters: `partial_mean = 0.4`, species SD 0.15 (about 91% of species truly at or above 0.2); 0 in minus.
- Measured: plus 0.4990 (0.0285), minus 0.4994 (0.0267); tolerance +-0.10; eq diff -0.0005 vs 3 SE 0.0083.
- Control: `permute_humerus_within_species`, humerus permuted within blocks of 6 individuals of similar body length inside each species.

### D-067
- Structure value: approved 0.5, equal-CV reference case; CVs 0.10 for body mass (mean 300 g), heart (1.1 g) and kidney (2.3 g), with organ weighing error CV 0.01.
- Other dependencies: latent correlation of heart with body mass 0.5 and of kidney with body mass 0.5.
- `minus` sets to null: the partial correlation of kidney and heart given body mass, from 0.4 to 0 (standardised partial slope equals it because both mass correlations are 0.5).
- Keys the error needs: none beyond the brief.
- Generator parameters: `partial = 0.4` plus, 0 minus.
- Measured: plus 0.4982 (0.0464), minus 0.4971 (0.0447); tolerance +-0.10; eq diff +0.0010 vs 3 SE 0.0137.
- Control: `permute_heart_within_mass`, heart permuted within blocks of 10 rats of similar body mass.

## Observations for the designer

- BMI cases D-006, D-015, D-053, D-037. The approved structure value 0.05 to 0.06 (ICC about 0.95) fixes the error variance at about 5% of the baseline variance. By algebra on the generator's parameters (not by running any analysis), the bias that this error adds to a correlation of baseline with change is of the order -0.05 to -0.15 in minus (largest for D-006), and to a slope of change on baseline about -0.06. The briefs' thresholds are -0.25 (correlation), R-squared 0.10 and slope -0.2. Whether the error matters at the brief's size is therefore doubtful for these four cases. The world is realistic; I did not enlarge the error beyond the approved value.
- D-036: the minus world cannot keep the plus distribution of MAP - CVP (see its entry): a resistance independent of flow requires pressure to vary with flow.
- The seed of my own checks is not the check script's seed; D-037 and D-040 sat near the 3 SE limit for the equality test on one seed (chance, identical distributions), and passed on the other.

## Sources read

- Files: STRUCTURE_AUTHOR_D.md, SOURCES_D.md, all 15 `brief.json` and `NOTE.json`, agent_docs (SPEC.md, GATE.md searched for the Study/Control API only), pkg/truth_gate/study.py (API and validation).
- URL: https://pmc.ncbi.nlm.nih.gov/articles/PMC3854983/ (CHI13 full text, Simulations section; fetched once through WebFetch).
- No criterion seen or run; Truth_Gate not run; no helper agents; no git; no ctx tools.
