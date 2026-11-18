# AUDIT_A, class B-3 (nine cases), part A

Pairs passing: 8. Pairs failing: 1.

Failed: D-045 on item (h) only (the word 'independent' in the description of baseline_score_retest; borderline, brief cannot be repaired).

## D-008: pass
- (a) yes: Faulty body computes Fick VO2 = co*(ca-cv)*10 and regresses it on DO2 = co*ca*10 within patient: the type 2 coupling of ARC81 (two calculated variables with the common component cardiac output). The abstract gives no numeric parameters; the factor 10 is the unit conversion.
- (b) yes: Fixed body replaces the calculated VO2 by the independently measured vo2_expired_gas, the generic remedy named in the private note (not in the abstract, as the note says); nothing else changes.
- (c) yes: diff shows one line (vo2 = co*(ca-cv)*10 versus vo2 = vo); CASE.md maps it correctly.
- (d) yes: No listed comparison in MECH_CHECK; the only branches are the non-finite check, m<2, an all-zero-variance-patient case (max(do2)>min(do2)) and the non-finite result. All allowed guards; nothing inspects noise, zeros or shuffles.
- (e) yes: PB 4 list itself is not in the sandbox; no banned-term hit in my scan of the brief for ratio, coupling, spurious, shared, denominator, index, bias, measurement error, regression to the mean and similar; the claim states no negation; the designer's term check is taken as passed.
- (f) yes: 40 patients x 6 occasions; source (abstract) states no sizes; compared with a realistic supply-dependency series; far below 2000 per axis and 2e6 values. Listed as sizes not documented by the source.
- (g) yes: Same per-patient least-squares slope, mean over patients, threshold 0.1, identical cost.
- (h) yes: Brief gives sizes, axes, what each key measured and the claim. The expired-gas key is described by how it was measured, with no statement of relations; delivery is named only because the claim's estimand needs it.
- (i) yes: Claim is the mean within-patient slope of consumption on delivery, which the fixed body estimates with measured consumption.
- (j) yes: minus sets only the within-patient slope of true VO2 on true delivery to 0 (beta_mean 0.18 to 0); cardiac output, arterial content and their errors keep plus values; venous content follows from the Fick identity.
- (k) yes: venous_o2_content is read only by the faulty body, which the documented error needs (Fick VO2); vo2_expired_gas is read only by the fixed body (the correction).
- (m) yes: stat uses cardiac_output and arterial_o2_content only (share of within-patient variance of log delivery due to cardiac output), unchanged by minus, and measures the shared-term structure.
- (p) yes: Reference variances: 0.2^2+0.15^2 = 0.0625 (output), 0.075^2+0.03^2 = 0.0065 (arterial): ratio 0.906, approved value 0.9.
- Remark, criterion True exactly when claim supported: Yes: the body returns True exactly when the mean per-patient slope (patients with zero delivery variance dropped) is >= 0.1.
- Remark, class and tag: B-3, shared-measured-component, regression-slope: follows the log and SOURCES_D (ARC81, type 2 coupling).

## D-023: pass
- (a) yes: Faulty correlates head_width/body_length with wing_length/body_length, the Y = X1/X2, Z = X3/X2 case of ATC76. Threshold 0.30 is the claim's.
- (b) yes: Fixed takes residuals of each on body_length with intercept and correlates them: the standard partial correlation; nothing else.
- (c) yes: diff: the two ratio lines are replaced by the ptp(bl) guard and two residual lines; CASE.md is right.
- (d) yes: Listed comparisons are np.ptp(u)==0, np.ptp(v)==0 (both bodies) and np.ptp(bl)==0 (fixed): zero-variance guards. n<3 and non-finite guards. No other branch.
- (e) yes: PB 4 list itself is not in the sandbox; no banned-term hit in my scan of the brief for ratio, coupling, spurious, shared, denominator, index, bias, measurement error, regression to the mean and similar; the claim states no negation; the designer's term check is taken as passed.
- (f) yes: 2000 specimens, one axis, 2000 values: at the cap. The source's simulations use at least 25,000 (above the cap), so the size is reduced to the cap; listed.
- (g) yes: Same correlation, same threshold; two small regressions versus two divisions.
- (h) yes: Brief gives size, keys and the claim only. Body length is named because the partial correlation needs it.
- (i) yes: Claim is the partial correlation given body length, which the fixed body estimates.
- (j) yes: minus sets only the correlation of the size-independent parts (0.40 to 0); marginals and allometric exponents unchanged.
- (k) yes: All three keys are read by both bodies.
- (m) yes: CV of body_length, a function of one key, drawn before and independently of the latent correlation parameter.
- (p) yes: L_SIGMA = 0.14917 gives lognormal CV sqrt(exp(sigma^2)-1) = 0.150 = approved 0.15.
- Remark, criterion True exactly when claim supported: Yes: returns True exactly when the correlation of the residuals is >= 0.30.
- Remark, class and tag: B-3, ratio-shared-denominator, correlation: agrees with the log.

## D-026: pass
- (a) yes: Faulty runs principal components on the covariance of the six ratios dimension/body_length: the ATC76 passage on inflated first eigenvalue when ratios are analysed.
- (b) yes: Fixed removes the linear effect of body_length (intercept) from each dimension and runs the same PCA on the residuals; nothing else.
- (c) yes: diff: one line (division) replaced by the ptp(bl) guard and the residual lines; CASE.md is right.
- (d) yes: Listed: np.ptp(bl)==0 (fixed), zero-variance guard. first_share also returns None when the total variance is not positive (zero variance). n<3 and non-finite guards. Nothing else.
- (e) yes: PB 4 list itself is not in the sandbox; no banned-term hit in my scan of the brief for ratio, coupling, spurious, shared, denominator, index, bias, measurement error, regression to the mean and similar; the claim states no negation; the designer's term check is taken as passed.
- (f) yes: 400 specimens x 6 dimensions (2400 values): under the caps. The source's abstract states no empirical size; its simulations (at least 25,000) exceed the cap and 400 is not the cap itself. Read by P2 reading 1: order of a morphometric sample, as the note argues. Listed as sizes not documented by the source (borderline, below the source's simulation size).
- (g) yes: Same helper first_share, same threshold 0.40, same cost.
- (h) yes: Sizes, keys and claim only. The brief says the six dimensions share a common shape pattern as the claim, not as a data fact.
- (i) yes: Claim is the first-component share after removing the linear effect of body length: what the fixed body computes.
- (j) yes: minus sets the loadings on the common factor to 0 with the total size-independent variance of every dimension unchanged.
- (k) yes: Both keys read by both bodies.
- (m) yes: CV of body_length, one key, unchanged by minus.
- (p) yes: L_SIGMA 0.14917 gives CV 0.150 = approved 0.15.
- Remark, criterion True exactly when claim supported: Yes: True exactly when first-eigenvalue share >= 0.40.
- Remark, class and tag: B-3, ratio-shared-denominator, other: agrees with the log. The note's text calls this a RESERVE; it is in the case list and was audited as a case.

## D-040: pass
- (a) yes: Faulty correlates breadth/length with height/length (PEA97 indices with a common denominator); threshold 0.2 is the claim's; no numeric parameters in the abstract.
- (b) yes: Fixed uses partial correlation of breadth and height given length (residuals on an intercept and length); nothing else.
- (c) yes: diff: errstate/division lines and the correlation call; CASE.md is right.
- (d) yes: No listed comparison. Branches: non-finite, size < 3 (note says 4, the body's 3 is smaller), zero variance (_flat), a residual variance <= 1e-24 of total (degenerate-variance guard, fixed only). All allowed.
- (e) yes: PB 4 list itself is not in the sandbox; no banned-term hit in my scan of the brief for ratio, coupling, spurious, shared, denominator, index, bias, measurement error, regression to the mean and similar; the claim states no negation; the designer's term check is taken as passed.
- (f) yes: 300 skulls; source states no sizes; compared with a realistic craniometric series; listed as not documented by the source.
- (g) yes: Same correlation, threshold 0.2, closed-form cost.
- (h) yes: Sizes, keys and claim only; length is named because the partial correlation needs it.
- (i) yes: Claim is the partial correlation given length.
- (j) yes: minus sets only the partial correlation of true breadth and height given length (0.35 to 0); marginals, the 0.15 correlations with length and caliper error unchanged.
- (k) yes: All keys read by both bodies.
- (m) yes: Function of the three keys' CVs only; marginals identical in plus and minus.
- (p) yes: All three CVs 0.035 (caliper error inside the CV): value 0.5 = approved.
- Remark, criterion True exactly when claim supported: Yes: True exactly when the partial correlation >= 0.2.
- Remark, class and tag: B-3, ratio-shared-denominator, correlation: agrees with the log.

## D-045: fail
- (a) yes: Faulty correlates change (follow-up minus baseline) with the baseline reading, the coupling/regression-to-mean error named in TU07; threshold -0.30 is the claim's.
- (b) yes: Fixed correlates change with the mean of baseline and follow-up: Oldham's method, named in TU07; nothing else.
- (c) yes: diff: one line (x = b versus x = 0.5*(b+f)); CASE.md is right.
- (d) yes: Listed: np.ptp(chg)==0 and np.ptp(x)==0 in both bodies: zero-variance guards; n<2 and non-finite guards. Nothing else.
- (e) yes: PB 4 list itself is not in the sandbox; no banned-term hit in my scan of the brief for ratio, coupling, spurious, shared, denominator, index, bias, measurement error, regression to the mean and similar; the claim states no negation; the designer's term check is taken as passed.
- (f) yes: 300 patients; source states no sizes; a mid-size trial; listed as not documented by the source.
- (g) yes: Same Pearson correlation and threshold; only the correlate differs.
- (h) no: NO, borderline, by the text: the key baseline_score_retest is described as 'a second, independent reading of the severity score ... taken at the baseline visit'. 'Independent' states how two variables are related (independent reading errors), a fact beyond what the key measured. Neither body reads the key; it exists only for the structure statistic, so the allowance for an independent measurement used by a documented correction does not apply. Everything else in the brief is within the rule.
- (i) yes: Claim is the correlation of change with the mean of the two readings, which the fixed body estimates.
- (j) yes: minus sets the true follow-up spread equal to the true baseline spread (5.5 to 10), so the true change is unrelated to the true mean level; level-response correlation 0.7, reading errors and means unchanged.
- (k) yes: Neither body reads baseline_score_retest, so no key is read only by the faulty body.
- (m) yes: 0.5*var(b - retest)/var(b) uses the two baseline readings only, which minus leaves unchanged; measures the reading-error share.
- (p) yes: Error SD 5, latent SD 10: 25/125 = 0.2 = approved.
- Remark, criterion True exactly when claim supported: Yes: True exactly when the correlation of change with the mean level is <= -0.30.
- Remark, class and tag: B-3, change-vs-baseline, correlation: agrees with the log.
- Repair request: Brief (not repairable): quote of item (h) only: 'A brief may state ... what each key measured ... It may not state any other fact about how ... variables are related'; the key baseline_score_retest reads 'a second, independent reading of the severity score'.

## D-056: pass
- (a) yes: Faulty is a one-way ANOVA F test across the groups on the ratio oxygen_uptake/body_mass, the ratio analysis that CUR13 warns against; p < 0.05 is the claim's.
- (b) yes: Fixed is the ANCOVA F test (common slope on body_mass, intercept per group), the correction named by CUR13; nothing else.
- (c) yes: diff: the response and the two design matrices (plus a ptp(m) guard); CASE.md is right.
- (d) yes: Listed comparisons: abs(dd)<tiny, abs(c)<tiny, abs(de-1)<3e-16 are inside the numpy-only incomplete-beta p-value routine (numerical safeguards, identical in both); np.ptp(y)==0 and np.ptp(m)==0 are zero-variance guards; r1==0.0 (perfect fit) returns None. Nothing inspects noise or shuffles.
- (e) yes: PB 4 list itself is not in the sandbox; no banned-term hit in my scan of the brief for ratio, coupling, spurious, shared, denominator, index, bias, measurement error, regression to the mean and similar; the claim states no negation; the designer's term check is taken as passed.
- (f) yes: 3 groups x 25 animals = 75 values; source states no sizes; realistic physiology experiment; listed as not documented by the source.
- (g) yes: Both are nested-model F tests with the same p-value routine, threshold 0.05, similar cost.
- (h) yes: Sizes, keys and the claim; body mass and the ANCOVA are named in the claim, which the estimand (group effect at equal body mass) requires.
- (i) yes: Claim is the ANCOVA group effect with body mass covariate: the fixed body's quantity.
- (j) yes: minus sets only the group effects on log oxygen uptake at equal body mass ((-0.03, +0.06, -0.03) to 0); mass distribution, group mass shift, exponent and noise unchanged.
- (k) yes: Both keys read by both bodies.
- (m) yes: Between-group share of body mass variance, one key, computed from mass which minus leaves unchanged; measures the group-by-denominator imbalance.
- (p) yes: Group mass shifts of +-0.0875 (log) with log SD 0.25: expected between-group share about 0.10 (including the 2/74 chance share) = approved 0.1.
- Remark, criterion True exactly when claim supported: Yes: True exactly when the p-value of the F test is < 0.05.
- Remark, class and tag: B-3, ratio-vs-denominator-proxy, mean: agrees with the log.

## D-062: pass
- (a) yes: Faulty computes, per species, the Pearson correlation of femur/body_length and humerus/body_length (PEA97 indices with a common denominator) and the share of species at or above 0.2; thresholds 0.2 and 0.6 are the claim's.
- (b) yes: Fixed uses the partial correlation given body_length in each species; same thresholds; nothing else.
- (c) yes: diff: errstate/division lines and the correlation call only; CASE.md is right.
- (d) yes: No listed comparison. Branches: n_ind<3 (note says 4; smaller), a species with non-finite values or zero variance not counted, none counted gives None, residual-variance degeneracy guard in the fixed helper. All allowed.
- (e) yes: PB 4 list itself is not in the sandbox; no banned-term hit in my scan of the brief for ratio, coupling, spurious, shared, denominator, index, bias, measurement error, regression to the mean and similar; the claim states no negation; the designer's term check is taken as passed.
- (f) yes: 12 species x 30 individuals (360 values per array); source states no sizes; museum-series size; listed as not documented by the source.
- (g) yes: Same per-species loop, threshold and share rule; comparable cost.
- (h) yes: Sizes, axes, keys and the claim, including both thresholds; body length named for the partial correlation.
- (i) yes: Claim is the share of species with within-species partial correlation >= 0.2, which the fixed body computes.
- (j) yes: minus sets the within-species partial correlation to 0 in every species (plus: mean 0.4, SD 0.15); CVs, species means and the 0.4 correlations with body length unchanged.
- (k) yes: All three keys read by both bodies.
- (m) yes: Mean over species of cz^2/sqrt((cx^2+cz^2)(cy^2+cz^2)) from the three keys' within-species CVs, unchanged by minus.
- (p) yes: Within-species CVs about 0.05 each (log-SD of species 0.10): 0.5 = approved.
- Remark, criterion True exactly when claim supported: Yes: True exactly when the share of counted species with partial correlation >= 0.2 is >= 0.6.
- Remark, class and tag: B-3, ratio-shared-denominator, proportion: agrees with the log.

## D-067: pass
- (a) yes: Faulty regresses the index kidney/body_mass on the index heart/body_mass and standardises (their correlation): PEA97's indices with a common denominator, in slope form; threshold 0.25 is the claim's.
- (b) yes: Fixed takes the standardised coefficient of heart_weight in the regression of kidney_weight on heart_weight and body_mass (denominator as covariate); nothing else.
- (c) yes: diff: errstate/division lines and the _std_coef call; CASE.md is right.
- (d) yes: No listed comparison. Branches: non-finite, size < 3 (equals the minimum: three parameters), _flat on the response, regressor and body_mass, non-finite coefficient. All allowed.
- (e) yes: PB 4 list itself is not in the sandbox; no banned-term hit in my scan of the brief for ratio, coupling, spurious, shared, denominator, index, bias, measurement error, regression to the mean and similar; the claim states no negation; the designer's term check is taken as passed.
- (f) yes: 60 rats; source states no sizes; small organ-weight study; listed as not documented by the source.
- (g) yes: Same standardised-slope helper and threshold 0.25; a 2-parameter versus a 3-parameter fit.
- (h) yes: Sizes, keys and the claim; body mass is named because the estimand (slope at fixed body mass) requires it.
- (i) yes: Claim is the standardised slope of kidney on heart after accounting for body mass: the fixed body's quantity.
- (j) yes: minus sets only the partial correlation of kidney and heart given body mass (0.4 to 0); CVs, the 0.5 correlations with body mass and weighing error unchanged.
- (k) yes: All three keys read by both bodies.
- (m) yes: Function of the three keys' CVs, unchanged by minus.
- (p) yes: CVs 0.10 each: 0.5 = approved.
- Remark, criterion True exactly when claim supported: Yes: True exactly when the standardised coefficient >= 0.25.
- Remark, class and tag: B-3, ratio-shared-denominator, regression-slope: agrees with the log. Observation, no item: by first-order arithmetic on the reference's parameters (heart and kidney correlated 0.5 with body mass, CV 0.10 each) the correlation of the two indices in minus is about 0.25, equal to the threshold; the structure value 0.5 assumes uncorrelated numerators and denominator. Done by hand, no code run.

## D-068: pass
- (a) yes: Faulty regresses wing_length/body_length on head_width/body_length within each population (ATC76 Y = X1/X2, Z = X3/X2) and averages; threshold 0.30 is the claim's.
- (b) yes: Fixed regresses wing_length on head_width and body_length per population and takes the head_width coefficient; nothing else.
- (c) yes: diff: the response and the predictor columns only; CASE.md is right.
- (d) yes: Listed: np.ptp(X[:, j])==0 (zero-variance guard in both bodies) and np.mean(slopes) >= 0.30 (the claim's own threshold, the decision rule, same in both). n<3 and non-finite guards. Nothing else.
- (e) yes: PB 4 list itself is not in the sandbox; no banned-term hit in my scan of the brief for ratio, coupling, spurious, shared, denominator, index, bias, measurement error, regression to the mean and similar; the claim states no negation; the designer's term check is taken as passed.
- (f) yes: 25 populations x 40 specimens = 1000 values. The source's simulations (at least 25,000) exceed the cap; 1000 is below the caps and is not the cap itself. Read by P2 reading 1 (source states no empirical size; per-population morphometric design of realistic order). Listed as not documented / below the source's simulation size.
- (g) yes: Same per-population OLS, mean and threshold; two versus three columns.
- (h) yes: Sizes, axes, keys and the claim; body length named as the other predictor because the estimand requires it.
- (i) yes: Claim is the mean within-population multiple-regression coefficient of wing length on head width given body length: the fixed body's quantity.
- (j) yes: minus sets only the within-population correlation of the size-independent parts (0.20 to 0; partial slope about 0.5 to 0); population shifts, CVs and marginals unchanged.
- (k) yes: All three keys read by both bodies.
- (m) yes: Mean over populations of the within-population CV of body_length, one key, unchanged by minus.
- (p) yes: Within-population CV 0.15 (lognormal, sd/mean exactly cv): 0.15 = approved.
- Remark, criterion True exactly when claim supported: Yes: True exactly when the mean of the per-population head_width coefficients is >= 0.30 (a population with zero variance gives None).
- Remark, class and tag: B-3, ratio-shared-denominator, regression-slope: agrees with the log.

## Pairs with sizes not documented by the source or reduced
- Not documented by the source (abstract states no sizes): D-008, D-040, D-045, D-056, D-062, D-067, and D-026 and D-068 (see below).
- Reduced to the cap because the source's simulations (at least 25,000) exceed it: D-023 (2000, at the cap).
- D-026 (400 x 6) and D-068 (25 x 40) are below the caps but also below the source's simulation size; answered yes by P2 reading 1 and flagged as borderline.
- None reduced for timing.

## Observations without an item
- The PB 4 banned-term list is not in the sandbox; item (e) rests on my own scan and on the authors' logs (B3A log states a grep with no hit; the B3B log has no explicit term-check line).
- D-067: first-order arithmetic on reference parameters puts the index correlation of the faulty analysis in minus near the threshold 0.25. D-008: the same kind of arithmetic puts the Fick-on-delivery slope in minus near 0.1 (about 0.1). Hand arithmetic, no code, no gate; reported only because the reference parameters are visible.

## What I read
- Files only in the sandbox: FIDELITY_AUDIT_D.md, P2_READING_D.md, SOURCES.md, SOURCES_D.md, grep of PREREG_PHASE_D.md (sections on the case and the private note), class/logs/B3A and B3B BRIEF_LOG.md, LOG.md (B3B criterion section), STRUCTURE_LOG.md (D-008 and D-023 copies), the nine case folders (brief, PRIVATE, CASE, both bodies, reference, MECH_CHECK), and grep of the saved abstracts (ARC81 PubMed text, CUR13, TU07, PEA97 json, ATC76 json).
- URLs read: none (I relied on the saved abstract extracts inside the sandbox).
- Helper computation: none run on any criterion or data. One attempted Python read of the saved abstracts hung and produced nothing; hand arithmetic only.