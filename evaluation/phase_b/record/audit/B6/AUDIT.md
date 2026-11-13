# B-6 fidelity audit (blind)

Class B-6, cases B6-01 ... B6-12. Read: AUDIT_PHASE.md, PREREG_PHASE_B.md, REVISIONS-post-freeze.md (P-1 to P-3), the B6 class folder (ASSIGNMENT, CASE, skeleton, faulty, fixed, PRIVATE, LOG, BRIEFS, src extracts), the B6 entries of STEP5_MECH_CHECK.json. No criterion was called on any data and no gate was run. One isolated helper check: I executed the shared p-value helper (Lanczos log-gamma, Lentz incomplete beta, two-sided t p) alone on six (t, df) pairs and compared with scipy: agreement to 1e-15, so it computes what it claims. Source passages were checked in the src text extracts (MAK19 df 18, groups of 20, 10 participants; HUR84 sets of four aquaria and two-replicate-plot studies; LAZ10 100 cells per rat, ten values per rat, 5 rats per cage; NIE11 r = 0.43 example).

## Result

All 12 pairs: all seven items yes. Overall: 12 pass, 0 fail. No repair requests.

Shared notes: every comparison in the designer's list is the Lentz convergence test (`abs(de - 1.0) < 1e-14`, in the p-value helper, identical in all twins); B6-03, B6-08, B6-11 also list `abs(r) < 1.0`, which I read as a degenerate-correlation guard of the same family as zero variance (None in both twins). The twins are byte-identical in the helper block and in the unused helpers; they differ only in the diffed lines.

## B6-01: pass

a yes, b yes, c yes, d yes, e yes, f yes, g yes

- (a) Faulty runs one-sample t tests on the trained gains and on the untrained gains and requires trained p<0.05 and >0, untrained p>=0.05: the 'significant here, not there' rule of NIE11 (p.1105, Fig. 1b), alpha 0.05.
- (b) Fixed is the direct interaction test: Welch t on per-participant gains (post-pre) between groups, two-sided 0.05, trained larger. Standard correction, nothing else added.
- (c) Diff (9 lines) is exactly the two within-group tests + conjunction versus one Welch test + decision line; both define the same helpers.
- (d) Only comparisons in the designer's list: the Lentz convergence test (de - 1.0 vs 1e-14) inside the shared p-value helper, byte-identical in all files and unrelated to the data, plus no other comparison. All other conditions are the allowed guards (too few values, non-finite, zero variance/std/residual variance), each returning None. Nothing inspects noise, zeros or shuffles.
- (e) Term check re-run by me over the brief text (claim, keys, meanings, sizes): no banned term or inflection; the brief states the claim and the threshold only and does not say what a false claim means.
- (f) 20 per group equals MAK19 Fig. 1A/1B (n = 20 per group, checked in the mak.txt extract). NIE11 states no n.
- (g) Same statistic family (t test / correlation), same p<0.05 threshold and direction, same decision rule shape, negligible and comparable cost; the twins differ only in the diffed lines (helper blocks are byte-identical).
- Criterion/claim check: Fixed returns True iff p<0.05 and trained gain larger: matches the claim (two-sided 0.05, trained larger).

## B6-02: pass

a yes, b yes, c yes, d yes, e yes, f yes, g yes

- (a) Faulty tests the drug-minus-placebo difference separately in visual and auditory region (one-sample t on differences) and requires visual significant and positive, auditory not significant: NIE11 p.1105 (region comparisons) and Fig. 1d.
- (b) Fixed is the paired t test on the difference of differences (vis_drug-vis_pl)-(aud_drug-aud_pl), two-sided 0.05, visual larger: the standard within-subject interaction test.
- (c) Diff (9 lines) is only the two separate tests versus the one test on dv-da.
- (d) Only comparisons in the designer's list: the Lentz convergence test (de - 1.0 vs 1e-14) inside the shared p-value helper, byte-identical in all files and unrelated to the data, plus no other comparison. All other conditions are the allowed guards (too few values, non-finite, zero variance/std/residual variance), each returning None. Nothing inspects noise, zeros or shuffles.
- (e) Term check re-run by me over the brief text (claim, keys, meanings, sizes): no banned term or inflection; the brief states the claim and the threshold only and does not say what a false claim means.
- (f) 16 participants: NIE11 states no n (P-2 situation 1). Compared with MAK19 groups of 20 and the typical within-subject neuroimaging sample of 12-20 (the author's note); within the cap. Listed as sizes not documented by the source.
- (g) Same statistic family (t test / correlation), same p<0.05 threshold and direction, same decision rule shape, negligible and comparable cost; the twins differ only in the diffed lines (helper blocks are byte-identical).
- Criterion/claim check: True iff p<0.05 and visual effect larger: matches the claim.

## B6-03: pass

a yes, b yes, c yes, d yes, e yes, f yes, g yes

- (a) Faulty tests each group's sleep-recall correlation against zero one-sided at 0.05 (p/2 when r>0) and requires older significant, younger not: the example of NIE11 p.1105 (r = 0.43, P = 0.01 versus r = 0.19, P = 0.21) and MAK19 Fig. 1A.
- (b) Fixed is the Fisher z test of two independent correlations, z=(atanh r1-atanh r2)/sqrt(1/(n1-3)+1/(n2-3)), one-sided 0.05 (1.6449). Standard correction.
- (c) Diff (7 lines) is the two per-group tests versus the Fisher z statistic; the correlation helper is shared.
- (d) Only comparisons in the designer's list: the Lentz convergence test (de - 1.0 vs 1e-14) inside the shared p-value helper, byte-identical in all files and unrelated to the data, plus the |r| < 1 guard (undefined atanh / division; a perfect-correlation degenerate case, the same family as a zero-variance guard, returning None in both twins). All other conditions are the allowed guards (too few values, non-finite, zero variance/std/residual variance), each returning None. Nothing inspects noise, zeros or shuffles.
- (e) Term check re-run by me over the brief text (claim, keys, meanings, sizes): no banned term or inflection; the brief states the claim and the threshold only and does not say what a false claim means.
- (f) 35 per group: NIE11 states no n. The quoted example implies about 34 (r = 0.43, P = 0.01) to 46 (r = 0.19, P = 0.21) pairs by my hand calculation, and MAK19 Fig. 1A has 20 per group; 35 is inside that range. Listed as not documented explicitly.
- (g) Same statistic family (t test / correlation), same p<0.05 threshold and direction, same decision rule shape, negligible and comparable cost; the twins differ only in the diffed lines (helper blocks are byte-identical).
- Criterion/claim check: True iff z>1.645 (older higher, one-sided 0.05): matches the claim.

## B6-04: pass

a yes, b yes, c yes, d yes, e yes, f yes, g yes

- (a) Faulty pools all 10 water samples of the 4 ponds per treatment (ravel of the (4,10) arrays) in a two-sample t test, df 78: HUR84 'sacrificial pseudoreplication', samples treated as independent replicates (Fig. 5B).
- (b) Fixed averages samples within pond and runs the t test on 4 vs 4 pond means (df 6): the unit of replication is the pond; standard correction.
- (c) Diff (4 lines) is only the argument to _two: raw arrays versus row means.
- (d) Only comparisons in the designer's list: the Lentz convergence test (de - 1.0 vs 1e-14) inside the shared p-value helper, byte-identical in all files and unrelated to the data, plus no other comparison. All other conditions are the allowed guards (too few values, non-finite, zero variance/std/residual variance), each returning None. Nothing inspects noise, zeros or shuffles.
- (e) Term check re-run by me over the brief text (claim, keys, meanings, sizes): no banned term or inflection; the brief states the claim and the threshold only and does not say what a false claim means.
- (f) 4 units per treatment matches HUR84 (two sets of four aquaria in the text; two-replicate-plot studies in the survey, checked in hur.txt). 10 samples per unit is not source-stated but within the cap; listed.
- (g) Same statistic family (t test / correlation), same p<0.05 threshold and direction, same decision rule shape, negligible and comparable cost; the twins differ only in the diffed lines (helper blocks are byte-identical).
- Criterion/claim check: True iff p<0.05 and fertilised higher: matches the claim.

## B6-05: pass

a yes, b yes, c yes, d yes, e yes, f yes, g yes

- (a) Faulty regresses all 96 mussel values on the tank dose repeated per mussel (np.repeat(dose,8) aligned with the row-major ravel of the (12,8) array): slope t test with df 94, the dose-bearing unit (tank) pseudoreplicated by its mussels: HUR84 sacrificial pseudoreplication.
- (b) Fixed regresses the 12 tank means on dose (df 10); standard unit-of-treatment correction.
- (c) Diff (4 lines) is only the regression inputs.
- (d) Only comparisons in the designer's list: the Lentz convergence test (de - 1.0 vs 1e-14) inside the shared p-value helper, byte-identical in all files and unrelated to the data, plus no other comparison. All other conditions are the allowed guards (too few values, non-finite, zero variance/std/residual variance), each returning None. Nothing inspects noise, zeros or shuffles.
- (e) Term check re-run by me over the brief text (claim, keys, meanings, sizes): no banned term or inflection; the brief states the claim and the threshold only and does not say what a false claim means.
- (f) HUR84 describes no regression and gives 2-4 units per treatment (aquaria sets of four, two replicate plots). 12 tanks in total (12 dose levels) and 8 mussels per tank are of the order of that setting and within the cap (P-2 situation 1). Listed as not documented (regression extension).
- (g) Same statistic family (t test / correlation), same p<0.05 threshold and direction, same decision rule shape, negligible and comparable cost; the twins differ only in the diffed lines (helper blocks are byte-identical).
- Criterion/claim check: True iff slope>0 and one-sided p<0.05: matches the claim.

## B6-06: pass

a yes, b yes, c yes, d yes, e yes, f yes, g yes

- (a) Faulty runs a two-sample t test on all 6x12 plot-by-survey values per treatment (df 142), taking surveys as replicates: HUR84 'temporal pseudoreplication'.
- (b) Fixed averages the 12 surveys within each plot and tests 6 vs 6 plot means (df 10); standard summary-statistic correction (plots are the units).
- (c) Diff (4 lines) is only the argument to _two.
- (d) Only comparisons in the designer's list: the Lentz convergence test (de - 1.0 vs 1e-14) inside the shared p-value helper, byte-identical in all files and unrelated to the data, plus no other comparison. All other conditions are the allowed guards (too few values, non-finite, zero variance/std/residual variance), each returning None. Nothing inspects noise, zeros or shuffles.
- (e) Term check re-run by me over the brief text (claim, keys, meanings, sizes): no banned term or inflection; the brief states the claim and the threshold only and does not say what a false claim means.
- (f) HUR84 gives no exact counts for temporal designs; 6 plots per treatment and 12 monthly dates are of the order of its field examples and within the cap (P-2 situation 1). Listed as not documented.
- (g) Same statistic family (t test / correlation), same p<0.05 threshold and direction, same decision rule shape, negligible and comparable cost; the twins differ only in the diffed lines (helper blocks are byte-identical).
- Criterion/claim check: True iff p<0.05 and mown higher: matches the claim.

## B6-07: pass

a yes, b yes, c yes, d yes, e yes, f yes, g yes

- (a) Faulty treats all 6x20 cells per genotype as independent in a two-sample t test (df 238); the animals are the units: LAZ10 hierarchical data (cells within animals).
- (b) Fixed averages cells within animal and tests 6 vs 6 animal means (df 10); the standard summary-measure correction named by LAZ10 (a mixed model is the alternative).
- (c) Diff (4 lines) is only the argument to _two.
- (d) Only comparisons in the designer's list: the Lentz convergence test (de - 1.0 vs 1e-14) inside the shared p-value helper, byte-identical in all files and unrelated to the data, plus no other comparison. All other conditions are the allowed guards (too few values, non-finite, zero variance/std/residual variance), each returning None. Nothing inspects noise, zeros or shuffles.
- (e) Term check re-run by me over the brief text (claim, keys, meanings, sizes): no banned term or inflection; the brief states the claim and the threshold only and does not say what a false claim means.
- (f) LAZ10 gives examples of 1 animal x 100 cells, 2 rats x 10 values, 5 rats per cage; 6 animals x 20 cells per genotype is of the order of those and within the cap (P-2 situation 1, sizes not stated as such). Listed.
- (g) Same statistic family (t test / correlation), same p<0.05 threshold and direction, same decision rule shape, negligible and comparable cost; the twins differ only in the diffed lines (helper blocks are byte-identical).
- Criterion/claim check: True iff p<0.05 and knockout higher: matches the claim.

## B6-08: pass

a yes, b yes, c yes, d yes, e yes, f yes, g yes

- (a) Faulty pools all 300 trials of the 12 participants into one Pearson correlation (df 298, one-sided 0.05): trials treated as independent although nested in participants (LAZ10 abstract: repeated observations; MAK19 pooled correlation).
- (b) Fixed computes one correlation per participant, Fisher z, one-sample t of the 12 z values against zero, one-sided 0.05; the standard summary-statistic correction.
- (c) Diff (12 lines) is the pooled correlation versus the per-participant loop + one-sample test and the matching p-value line; unused helpers are present in both twins.
- (d) Only comparisons in the designer's list: the Lentz convergence test (de - 1.0 vs 1e-14) inside the shared p-value helper, byte-identical in all files and unrelated to the data, plus the |r| < 1 guard (undefined atanh / division, a degenerate-correlation guard like zero variance, None in both twins). All other conditions are the allowed guards (too few values, non-finite, zero variance/std/residual variance), each returning None. Nothing inspects noise, zeros or shuffles.
- (e) Term check re-run by me over the brief text (claim, keys, meanings, sizes): no banned term or inflection; the brief states the claim and the threshold only and does not say what a false claim means.
- (f) Neither LAZ10 (3 observations per rat, 100 cells per rat) nor MAK19 (10 participants) describes a trial-level correlation. 12 participants x 25 trials is of the order of those and within the cap (P-2 situation 1). Listed as not documented (extension).
- (g) Same statistic family (t test / correlation), same p<0.05 threshold and direction, same decision rule shape, negligible and comparable cost; the twins differ only in the diffed lines (helper blocks are byte-identical).
- Criterion/claim check: True iff mean z>0 and one-sided p<0.05: matches the claim. Known (designer-aware, P-3): the skeleton's minus world has a shared trial drift that the fixed criterion detects (27% in the author's pre-check); this is a skeleton matter, not a criterion defect.

## B6-09: pass

a yes, b yes, c yes, d yes, e yes, f yes, g yes

- (a) Faulty treats the 200 (animal, cell index) differences amp_drug-amp_vehicle as independent pairs in one one-sample t test (df 199); the animal is the unit: LAZ10 Fig. 1 example (all data points used, hierarchy ignored).
- (b) Fixed averages cells per animal in each condition and runs a paired t test across the 8 animals (df 7); standard correction.
- (c) Diff (4 lines) is only the argument of _one.
- (d) Only comparisons in the designer's list: the Lentz convergence test (de - 1.0 vs 1e-14) inside the shared p-value helper, byte-identical in all files and unrelated to the data, plus no other comparison. All other conditions are the allowed guards (too few values, non-finite, zero variance/std/residual variance), each returning None. Nothing inspects noise, zeros or shuffles.
- (e) Term check re-run by me over the brief text (claim, keys, meanings, sizes): no banned term or inflection; the brief states the claim and the threshold only and does not say what a false claim means.
- (f) LAZ10 examples: 10 values per rat, 100 cells per rat; 8 animals x 25 cells is within that and the cap (P-2 situation 1; paired design is an extension). Listed.
- (g) Same statistic family (t test / correlation), same p<0.05 threshold and direction, same decision rule shape, negligible and comparable cost; the twins differ only in the diffed lines (helper blocks are byte-identical).
- Criterion/claim check: True iff p<0.05 and drug higher: matches the claim. Observation (not an answer change): in the skeleton's minus world the animal-specific drug effect is multiplied by the null effect (0), so the animal effect cancels in the cell-level differences and the pooled paired test is only mildly affected there; the error is in the code, but the world gives it little to act on. Not repairable in criterion bodies.

## B6-10: pass

a yes, b yes, c yes, d yes, e yes, f yes, g yes

- (a) Faulty fits the slope of rt on contrast separately for each condition and requires attended slope significant and negative, unattended not significant, attended steeper: MAK19 'comparisons between two effects' (significant in one condition, not in the other; correlation between two variables named in the same sentence).
- (b) Fixed regresses the per-participant difference (attended-unattended) on contrast and tests that slope (negative, two-sided 0.05): the slope-difference test for a within-participant design. Standard.
- (c) Diff (10 lines) is the two regressions + conjunction versus one regression on the difference.
- (d) Only comparisons in the designer's list: the Lentz convergence test (de - 1.0 vs 1e-14) inside the shared p-value helper, byte-identical in all files and unrelated to the data, plus no other comparison. All other conditions are the allowed guards (too few values, non-finite, zero variance/std/residual variance), each returning None. Nothing inspects noise, zeros or shuffles.
- (e) Term check re-run by me over the brief text (claim, keys, meanings, sizes): no banned term or inflection; the brief states the claim and the threshold only and does not say what a false claim means.
- (f) MAK19 uses groups of 20 (Fig. 1A/1B) and gives no n for regressions; 30 participants is of the same order and within the cap (P-2 situation 1). Listed as not documented.
- (g) Same statistic family (t test / correlation), same p<0.05 threshold and direction, same decision rule shape, negligible and comparable cost; the twins differ only in the diffed lines (helper blocks are byte-identical).
- Criterion/claim check: True iff the difference slope is negative (attended steeper in the world's sign convention, where reaction time falls with contrast) and two-sided p<0.05: matches the claim as the skeleton encodes it.

## B6-11: pass

a yes, b yes, c yes, d yes, e yes, f yes, g yes

- (a) Faulty pools the 10x2 before/after measurements into one Pearson correlation (n = 20 pairs, df 18 instead of 8): the 'Inflating the units of analysis' example of MAK19 (pooled pre and post across participants, critical R 0.44 instead of 0.63).
- (b) Fixed averages the two sessions per participant and correlates the 10 participant means (df 8, one-sided 0.05): the correct unit in the passage (1 data point per participant). Standard.
- (c) Diff (4 lines) is only the arguments of _corr.
- (d) Only comparisons in the designer's list: the Lentz convergence test (de - 1.0 vs 1e-14) inside the shared p-value helper, byte-identical in all files and unrelated to the data, plus the |r| < 1 guard (degenerate correlation, None in both twins). All other conditions are the allowed guards (too few values, non-finite, zero variance/std/residual variance), each returning None. Nothing inspects noise, zeros or shuffles.
- (e) Term check re-run by me over the brief text (claim, keys, meanings, sizes): no banned term or inflection; the brief states the claim and the threshold only and does not say what a false claim means.
- (f) 10 participants x 2 sessions equals the MAK19 passage (pre-post design in 10 participants; df 18 vs 8, checked in mak.txt). Documented.
- (g) Same statistic family (t test / correlation), same p<0.05 threshold and direction, same decision rule shape, negligible and comparable cost; the twins differ only in the diffed lines (helper blocks are byte-identical).
- Criterion/claim check: True iff r>0 and one-sided p<0.05 (df 8): matches the claim. Note: the private note's 'df 38 / 40 pooled measurements' is a slip; the code and brief have 20 pooled values (df 18), as in the source.

## B6-12: pass

a yes, b yes, c yes, d yes, e yes, f yes, g yes

- (a) Faulty takes each participant's least-squares slope across the 3 sessions and runs one-sample t tests per group, requiring the trained group significantly above zero and the control not: MAK19 'a significant effect in one group but not in the other' (Fig. 1B).
- (b) Fixed is the Welch two-sample t test on the per-participant slopes, two-sided 0.05, trained larger: the direct group comparison. Standard.
- (c) Diff (9 lines) is the two one-sample tests + conjunction versus one Welch test; slope helper shared.
- (d) Only comparisons in the designer's list: the Lentz convergence test (de - 1.0 vs 1e-14) inside the shared p-value helper, byte-identical in all files and unrelated to the data, plus no other comparison. All other conditions are the allowed guards (too few values, non-finite, zero variance/std/residual variance), each returning None. Nothing inspects noise, zeros or shuffles.
- (e) Term check re-run by me over the brief text (claim, keys, meanings, sizes): no banned term or inflection; the brief states the claim and the threshold only and does not say what a false claim means.
- (f) MAK19 Fig. 1B has pre-post in 20 per group; 14 per group with 3 sessions is smaller and an extension, but of the same order and within the cap (P-2 situation 1). Listed as not documented (extension).
- (g) Same statistic family (t test / correlation), same p<0.05 threshold and direction, same decision rule shape, negligible and comparable cost; the twins differ only in the diffed lines (helper blocks are byte-identical).
- Criterion/claim check: True iff p<0.05 and trained slope larger: matches the claim.

## Class and subtype remarks
All twelve carry class B-6, subtype empty. I agree with every assignment under the section 1 rules: B6-01, 02, 03, 10, 12 are 'significant here, not there' difference claims; B6-04 to 09 and 11 are non-independent units counted as independent. Overlaps with other classes (B6-01 gain scores could meet B-3; B6-11 and B6-08 are pooled correlations, MAK19 also cited for B-1) are resolved by the order B-2, B-6, B-1, B-3 in favour of B-6. No disagreement.

## Pairs whose sizes are 'not documented by the source' (P-2 situation 1)
B6-02 (NIE11, no n; 16 participants), B6-03 (NIE11; 35 per group, implied roughly 34-46 by the quoted example), B6-04 (samples per pond not stated; 4 ponds per treatment documented), B6-05 (regression extension; 12 tanks x 8), B6-06 (6 plots x 12 surveys), B6-07 (6 animals x 20 cells), B6-08 (12 x 25 trials, extension), B6-09 (8 x 25, paired extension), B6-10 (30 participants, regression), B6-12 (14 per group, 3 sessions, extension). In each I compared with the examples of the source (MAK19 groups of 20 and 10 participants; HUR84 four aquaria per set and two-replicate plots; LAZ10 1-5 animals, 10-100 values) and with the section 2 caps; all are of the same order and under the caps.
Documented exactly: B6-01 (n = 20 per group, MAK19 Fig. 1), B6-11 (10 participants x 2 sessions, MAK19 df 18 vs 8).

## Pairs 'reduced to the cap' (P-2 situation 2)
None; every size is below the caps of section 2 (at most 300 rows or units, 60 features).

## Observations that do not change any answer
- B6-08: the skeleton's minus world has a real within-participant trial drift; the fixed criterion rejects it in about 27% of pre-check samples (author's log; P-3 already records this). Skeleton matter.
- B6-09: the skeleton's minus world removes the animal-specific drug effect (it is scaled by the effect), so the cell-level paired test has little animal-level variation to exploit there; the code error is present, but detection by the declared worlds may be weak. Not repairable in the criterion bodies.
- B6-10: the fixed criterion's direction (slope difference negative) follows the skeleton's sign convention (reaction time falls with contrast).
- B6-11: the private note says df 38 / 40 pooled measurements; code and brief have 20 pooled values (df 18), which matches MAK19.
