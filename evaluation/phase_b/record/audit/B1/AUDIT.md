# Fidelity audit, class B-1 (circular analysis), cases B1-01 .. B1-12

Method: read each faulty/fixed pair against its brief and private note; diffed the twins; diffed each file against the frozen skeleton (identical outside the criterion body); compared the shared helper block (identical in all 22 files); ran the helpers _tsf and _ib in isolation against known values (t=2.0, df=10 gives 0.03669; t=1.8331, df=9 gives 0.0500; F(7,120)=2.0 gives 0.0605). No criterion was called on any data and no gate was run. The source extracts (kri.txt, mak.txt, vul.txt) were searched to confirm the cited passages; BAR05 exists only as an abstract (BAR05_openalex_text.txt) and I did not obtain the full text.

FINAL (post-repair audit): 12 of 12 pairs pass. History: first audit 12 of 12; after the designer's re-examination 10 of 12 (B1-04, B1-05 failed on (a)); after the author's repair B1-04 and B1-05 pass all seven items (see the last section). Original result before the designer's request: 12 of 12 pass (superseded for those two pairs).

## B1-01 (KRI09): pass
* (a) yes. Faulty selects, per subject, voxels whose face-minus-house map (mean of both runs) exceeds 1.645 x rms, then tests the per-subject mean contrast of those same voxels from the same map (folds=[(mean,mean)]): selection and evaluation on the same data, the KRI09 double-dipping form (ROI from a statistical map, then statistics on it).
* (b) yes. Fixed is a two-fold run split (select on run 0, evaluate on run 1, and reverse), the split-data remedy of KRI09; same map, cut-off, per-subject mean, mean>=0.30 and one-sided t.
* (c) yes. The twins differ in exactly one line (the folds list), checked with diff; everything outside the criterion body equals the frozen skeleton.
* (d) yes. Listed comparisons: the incomplete-beta convergence test (numerical), x.mean()>=0.30 (the claim's own threshold), len(x)<5 and sd>0 guards (allowed). Nothing inspects the input distribution.
* (e) yes. No banned stem of PREREG section 4 occurs in the claim, data keys, meanings or sizes (substring scan of the whole brief); the brief gives a positive claim with its statistic and threshold and never says what 'claim false' means.
* (f) yes. 20 subjects, 2 runs, 60 voxels: KRI09 gives no subject counts (its Example 2 simulates 30x30x20 voxels); voxels at the 60 cap. Sizes not documented by the source; reduced to the cap.
* (g) yes. Same helpers, statistic, cut-off, threshold and test; the fixed does two cheap passes instead of one.

## B1-02 (KRI09): pass
* (a) yes. Faulty runs a one-way ANOVA across orientations on all 16 trials, takes the preferred orientation (argmax of the same means) and computes the selectivity index from the same means (sel_r, ev_r = r, r): selecting neurons by selectivity and then reporting their selectivity on the same data (KRI09 single-cell example).
* (b) yes. Fixed selects tuned neurons and preferred orientation on even trials and computes the index on odd trials (standard split-trial remedy); same ANOVA, p<0.05, index and 0.25 threshold.
* (c) yes. One line differs (sel_r, ev_r). The index clip and the den>0 guard are in both twins.
* (d) yes. Listed: idx[tuned].mean()>=0.25 (claim threshold). Borderline note only: np.clip(idx,-1,1) was added after a pre-check of the fixed criterion on noise (LOG: index ratio exploding on N(0,1) data). It is not a branch, does not test the input, is a no-op for the non-negative rates of the brief, and is identical in both twins, so I answer yes; the designer may wish to disclose it.
* (e) yes. No banned stem of PREREG section 4 occurs in the claim, data keys, meanings or sizes (substring scan of the whole brief); the brief gives a positive claim with its statistic and threshold and never says what 'claim false' means.
* (f) yes. 150 neurons, 8 orientations, 16 trials: KRI09 states no counts for single-unit studies. Sizes not documented by the source; within the 300-unit cap.
* (g) yes. Same ANOVA, index, guard and threshold; the halves change only the number of trials used.

## B1-03 (KRI09): pass
* (a) yes. Faulty splits participants at the median of block 0 and tests improvement = block 3 - block 0 between halves, so the split variable and the outcome share the noisy block-0 measurement (KRI09 Introduction: division of a group of subjects into subgroups based on task performance; also the regression-to-the-mean artefact of BAR05/MAK19).
* (b) yes. Fixed splits on block 1, a separate early measurement whose noise is independent of block 0 in the skeleton (iid per-block noise), keeping the claim's own improvement definition; a standard independent-measure correction. It differs from the private note (split on block 0, outcome block 3 - block 1) but is an equivalent device and matches CASE.md.
* (c) yes. One line differs (split = s[:,0] vs s[:,1]).
* (d) yes. Listed: only the numerical convergence test. diff>=4.0 is the claim's own constant; guards are len<3 and sp2>0 (allowed).
* (e) yes. No banned stem of PREREG section 4 occurs in the claim, data keys, meanings or sizes (substring scan of the whole brief); the brief gives a positive claim with its statistic and threshold and never says what 'claim false' means.
* (f) yes. 60 participants, 4 blocks: KRI09 states no behavioural sample sizes. Sizes not documented by the source; within caps.
* (g) yes. Same pooled t, threshold, direction and cost.

## B1-04 (VUL09): FAIL on (a) after re-examination
* (a) yes. [superseded on re-examination, see below] Faulty correlates every voxel with the trait over all 24 subjects, keeps positive significant voxels and reports their mean correlation computed on the same subjects (folds=[(all,all)]): the VUL09 nonindependence-error sentence, selection by correlation then the same correlation on the selected voxels.
* (b) yes. Fixed selects on one interleaved half of the subjects and evaluates the correlation on the other half, in both directions (cross-validated selection, the usual independent-data remedy).
* (c) yes. One line differs (the folds list).
* (d) yes. Listed: mean>=0.50 (claim threshold), convergence test, and the zero-variance guard on the trait in the selection and evaluation sets (allowed). 'if not means: return None' is an empty-selection guard (allowed).
* (e) yes. No banned stem of PREREG section 4 occurs in the claim, data keys, meanings or sizes (substring scan of the whole brief); the brief gives a positive claim with its statistic and threshold and never says what 'claim false' means.
* (f) yes. 24 subjects, 60 voxels: the VUL09 extracts state no typical n (Fig. 4 simulates 10 subjects, 10,000 voxels); studies there have thousands of voxels. Sizes not documented by the source; voxels reduced to the 60 cap.
* (g) yes. Same correlation, selection test, threshold and loop structure; only the degrees of freedom follow the half size.
* (a) NO on re-examination. VUL09's documented selection is a positive correlation with p < .01 (Fig. 4 caption). The faulty criterion uses r > 0 and two-sided p < 0.05 (tq(0.025)). CASE.md item 7 says this was chosen from the private note's two options (p < 0.05 or r > 0.4) and that VUL09's exact threshold was not re-read; the reason is not about the noise probe. The error pattern is present, but the parameter is not the documented one (nor a documented typical one), so strictly (a) is no under the wording 'documented or typical parameters'. This is a parameter judgement, not an error in the mechanism.
* Repair request (criterion bodies only): Change the selection level in BOTH twins (`keep = (r_sel > 0) & (tt > _tq(0.025, df))`) to the documented p < 0.01 (`_tq(0.005, df)`); with half-size df = 10 the fixed criterion will return None more often (allowed guard). If the designer accepts p < 0.05 as 'typical' because the source states thresholds vary, this repair can be waived, but that is the designer's decision, not mine.

## B1-05 (VUL09): FAIL on (a) after re-examination
* (a) yes. [superseded on re-examination, see below] Faulty averages the two sessions, selects voxels by correlation with the trait over the 16 subjects and then regresses the trait on the mean activity of those voxels from the same averaged data (sel_act, ev_act = mean, mean): the VUL09 selection-by-regression-across-subjects error (53% of surveyed studies).
* (b) yes. Fixed selects on session 0 and evaluates on session 1, an independent measurement of the same subjects; same slope, one-sided test and 0.50 threshold. The private note admits the second-session device is the author's construction, not in VUL09; it is a standard independent-data remedy.
* (c) yes. One line differs.
* (d) yes. Listed: var(trait)>0 and var(m)>0 guards (allowed), slope>=0.50 (claim threshold), convergence test. Nothing else.
* (e) yes. No banned stem of PREREG section 4 occurs in the claim, data keys, meanings or sizes (substring scan of the whole brief); the brief gives a positive claim with its statistic and threshold and never says what 'claim false' means.
* (f) yes. 16 subjects, 2 sessions, 50 voxels: no n in the VUL09 extracts (Fig. 4: 10 subjects). Sizes not documented by the source; voxels within the cap (50).
* (g) yes. Same selection test, slope and test; identical cost.
* (a) NO on re-examination. The documented selection in VUL09 (Fig. 4 caption, vul.txt line 375-376) is 'a positive correlation with p < .01'; the private note's faulty criterion uses r > 0 and p < 0.01. The faulty criterion in the file selects with r > 0 and two-sided p < 0.05 (tt > t(0.025)), which is neither the documented value nor a typical VUL09 value (the extract also mentions p < .001 for a surveyed study, line 524). CASE.md item 7 gives as the reason that p < 0.01 would leave the selection empty in most noise samples and the criterion None almost always: a reason tied to the gate's noise probe, and the loosened threshold makes the faulty criterion hold on noise more often, i.e. it favours detection. The error pattern (select by regression across subjects, then regress on the same data) is present, but item (a) asks for the documented or typical parameters, and they are not used.
* (d) re-examined: Item (d): the code has no branch and inspects no input property, so no gate-aware code in the strict sense; but the parameter was chosen for its behaviour on noise data, which the designer should disclose. Kept yes.
* Repair request (criterion bodies only): Change the selection level in BOTH twins (the line `keep = (r_sel > 0) & (tt > _tq(0.025, n - 2))`) to the documented p < 0.01 two-sided with r > 0, i.e. `_tq(0.005, n - 2)`; the None returns that result on empty selections are allowed guards. If the author prefers p < 0.05, the designer must treat it as a disputed pair (section 5.3).

## B1-06 (VUL09): pass
* (a) yes. Faulty selects voxels by a one-sided Welch t between the groups on all 28 subjects, averages them per subject and computes the Welch t between the same groups on the same subjects (folds=[(all,all)]): VUL09 Study 26 (split into groups, find voxels showing the group effect, then analyse those voxels).
* (b) yes. Fixed selects on a group-balanced half and evaluates on the other half, in both directions (7+7 per half), then computes the Welch t over all 28 out-of-sample values; same threshold 3.0.
* (c) yes. One line differs (the folds list; half_a and half_b are defined in both twins).
* (d) yes. Listed: a.var+b.var>0 (zero-variance guard, allowed), convergence test; len<3 and 'not keep.any()' guards (allowed).
* (e) yes. No banned stem of PREREG section 4 occurs in the claim, data keys, meanings or sizes (substring scan of the whole brief); the brief gives a positive claim with its statistic and threshold and never says what 'claim false' means.
* (f) yes. 28 subjects (14+14), 40 voxels: no n in the VUL09 extracts. Sizes not documented by the source; voxels within the cap.
* (g) yes. Same Welch statistic, selection rule and t>=3.0 decision.

## B1-07 (MAK19): pass
* (a) yes. Faulty chooses genes with a Welch p<0.05 on all 40 samples and takes the mean of the fold change times the selection sign, i.e. the absolute fold change, of the kept genes on the same samples (folds=[(all,all)]): MAK19 Circular analysis (retrospective selection criterion relevant to the outcome; KRI09 lists selected genes).
* (b) yes. Fixed chooses genes and sign on one half (balanced tumour/normal) and measures the signed fold change on the other half, in both directions; the sign alignment removes the selection bias in the effect size.
* (c) yes. One line differs.
* (d) yes. Listed: mean>=0.5 (claim threshold), convergence test, selection p<0.05 (a selection rule, not an input check). Size guards len<4 and empty-selection are allowed.
* (e) yes. No banned stem of PREREG section 4 occurs in the claim, data keys, meanings or sizes (substring scan of the whole brief); the brief gives a positive claim with its statistic and threshold and never says what 'claim false' means.
* (f) yes. 40 samples, 60 genes: MAK19 gives no numbers; real gene panels are larger. Sizes not documented by the source; genes at the 60 cap.
* (g) yes. Same Welch selection, statistic and threshold.

## B1-08 (MAK19): pass
* (a) yes. Faulty selects cells by a paired t (post>pre) over all 30 trials and counts the share with positive mean (post-pre) over the same 30 trials, which is 1.0 by construction whenever at least 5 cells pass: the circular statistic MAK19 describes (selection criterion inherently relevant to the outcome; noise recruited).
* (b) yes. Fixed selects on the first 15 trials and measures the share on the last 15 (split-trial remedy); same t test, guard and 0.70 threshold.
* (c) yes. One line differs (sel_t, ev_t).
* (d) yes. Listed: resp.sum()<5 (a selection-size guard, allowed), the proportion of positive evaluation means (the claim's own statistic) and the convergence test.
* (e) yes. No banned stem of PREREG section 4 occurs in the claim, data keys, meanings or sizes (substring scan of the whole brief); the brief gives a positive claim with its statistic and threshold and never says what 'claim false' means.
* (f) yes. 120 cells, 30 trials: MAK19's neuron example gives no numbers. Sizes not documented by the source; within caps.
* (g) yes. Same t test, guard, statistic and threshold.

## B1-09 (MAK19): pass
* (a) yes. Faulty bins neurons on the mean of the two baseline epochs and computes the increase post minus that same baseline mean for the lowest third (sel_b, ref_b = mean, mean): exactly the MAK19 example (neurons binned by baseline, low-baseline neurons show response increases that could be observed in pure noise; regression to the mean). Quote confirmed in mak.txt.
* (b) yes. Fixed selects on baseline epoch 0 and measures the increase against baseline epoch 1; same third, t test and threshold 2.
* (c) yes. One line differs.
* (d) yes. Listed: inc.mean()>=2.0 (claim threshold), convergence test; k<5 and sd>0 guards (allowed).
* (e) yes. No banned stem of PREREG section 4 occurs in the claim, data keys, meanings or sizes (substring scan of the whole brief); the brief gives a positive claim with its statistic and threshold and never says what 'claim false' means.
* (f) yes. 200 neurons, 2 baseline epochs: the MAK19 example has no numbers. Sizes not documented by the source; within the 300 cap.
* (g) yes. Same selection fraction, one-sample t and threshold.

## B1-10 (BAR05): pass
* (a) yes. Faulty restricts to patients with entry SBP>=150, then tests the mean 12-week lowering in the drug arm alone (one-sample t, mean>=5, one-sided), ignoring the placebo arm: change in a sub-sample selected on the noisy baseline value (BAR05 abstract, verified). The full text was not accessible and I did not obtain it.
* (b) yes. Fixed compares the lowering between drug and placebo among patients with entry SBP>=150 (Welch, difference>=5, one-sided): a control arm selected the same way cancels regression to the mean; a standard remedy (control-group design).
* (c) yes. The twins differ in one decision block (lines 107-114), but that block is the whole correction (the test changes from one-sample to two-sample because a control arm is added); no other line differs.
* (d) yes. Listed: convergence test, a.var+b.var>0 (zero-variance guard) in the fixed, claim thresholds x.mean()>=5.0 and diff>=5.0 (claim constants). Nothing inspects the input distribution.
* (e) yes. No banned stem of PREREG section 4 occurs in the claim, data keys, meanings or sizes (substring scan of the whole brief); the brief gives a positive claim with its statistic and threshold and never says what 'claim false' means.
* (f) yes. 160 patients (about 80 per arm), 2 visits: the BAR05 abstract states no sizes; full text not read. Sizes not documented by the source; within caps.
* (g) yes. The statistic changes from a one-sample to a two-sample Welch t, which is inherent to adding the control arm; threshold 5, the one-sided p<0.05 rule and the cost are the same. Weakest pair for (c) and (g); accepted because the difference is the correction itself. Guard sizes differ (5 vs 3 per arm), both allowed.

## B1-11 (BAR05): pass
* (a) yes. Faulty takes the top fifth at visit 0 and requires that at least 70% score lower at visit 2 than at visit 0, the selection measurement itself (BAR05: unusually extreme values are followed by values closer to the mean). Only the abstract was verified.
* (b) yes. Fixed compares visit 2 with visit 1, the second assessment just before the programme (a baseline not used for selection); a standard second-baseline remedy.
* (c) yes. One line differs (ref = s[:,0] vs s[:,1]).
* (d) yes. Listed: the single line np.mean(s[top,2]<ref[top])>=0.70 is the claim's own proportion and threshold. The len(top)<5 guard is a selection-size guard (allowed).
* (e) yes. No banned stem of PREREG section 4 occurs in the claim, data keys, meanings or sizes (substring scan of the whole brief); the brief gives a positive claim with its statistic and threshold and never says what 'claim false' means.
* (f) yes. 120 patients, 3 visits: the BAR05 abstract gives no sizes. Sizes not documented by the source; within caps.
* (g) yes. Same selection, statistic and threshold.

## B1-12 (BAR05): pass
* (a) yes. Faulty takes the lowest fifth on test 0 and tests the gain test 2 - test 0 (one-sample t, mean>=5): improvement of units selected for an extreme value of the same noisy measurement (BAR05 abstract).
* (b) yes. Fixed uses the same students but measures gain relative to test 1, a second pre-programme measurement not used for selection; a standard second-baseline remedy.
* (c) yes. One line differs (ref = s[:,0] vs s[:,1]).
* (d) yes. Listed: convergence test and gain.mean()>=5.0 (claim threshold); guards len<5 and sd>0 (allowed).
* (e) yes. No banned stem of PREREG section 4 occurs in the claim, data keys, meanings or sizes (substring scan of the whole brief); the brief gives a positive claim with its statistic and threshold and never says what 'claim false' means.
* (f) yes. 250 students, 3 tests: the BAR05 abstract gives no sizes. Sizes not documented by the source; within the 300 cap.
* (g) yes. Same selection, one-sample t and threshold.

## Class and subtype remarks

All twelve briefs fit rule B-1 of section 1 (items selected using data, an effect statistic of the selected items reported on the same data, none a prediction score) and carry no subtype, as assigned. B1-03 and B1-09 to B1-12 also resemble B-3 (a change score against its own baseline); the priority order B-2, B-6, B-1, B-3 gives B-1, so I report no disagreement.

## Claim and criterion consistency

Each criterion returns True only when the claim's statistic and threshold hold (B1-01 mean>=0.30 plus one-sided t; B1-02 mean index>=0.25; B1-03 difference>=4 plus pooled one-sided t; B1-04 mean r>=0.50; B1-05 slope>=0.50 and one-sided p; B1-06 Welch t>=3.0; B1-07 mean>=0.5; B1-08 share>=0.70; B1-09 mean>=2 plus t; B1-10 difference>=5 plus Welch p (faulty: drug-arm change); B1-11 share>=0.70; B1-12 mean gain>=5 plus t). Minor points: B1-01 drops subjects with no kept voxel; B1-04 to B1-08 return None on an empty selection (allowed guard).

## Pairs by entry P-2 of the post-freeze revisions

Sizes not documented by the source (no numbers in the extracts I read, or abstract only): all twelve (B1-01 to B1-12).
Sizes reduced to the cap of section 2: B1-01 (60 voxels), B1-04 (60 voxels), B1-05 (50 voxels), B1-06 (40 voxels), B1-07 (60 genes); the sources describe thousands of voxels or genes.

## Points the designer may want to disclose

* B1-02: np.clip(idx,-1,1) was added after a noise pre-check of the fixed criterion; it is identical in both twins, not a branch, and inert on valid data, so (d) stays yes.
* B1-10: the twins' test differs (one-sample vs Welch) because the correction adds a control arm; accepted for (c) and (g).
* B1-10 to B1-12: the BAR05 full text was not available; the error (follow-up on a sub-sample selected on baseline) is verified from the abstract, the remedies (control arm, second baseline) are standard but not verified against the paper.
* B1-03: the fixed device (split on block 1, improvement still block 3 - block 0) differs from the private note, but CASE.md describes the code correctly.

## Re-examination requested by the designer (post-freeze log): item (a) and parameter changes

Facts verified in B1\src\vul.txt: the Fig. 4 caption reads 'a positive correlation with p < .01' (lines 375-376); another passage mentions a surveyed result at p < .001 (line 524); the paper otherwise speaks of 'some threshold'. B1-05's CASE.md item 7 confirms the change to p < 0.05 with the noise-probe-style reason quoted by the designer.

* B1-05: (a) changes from yes to no (superseded answer: yes). The mechanism is the documented error, but the selection level is not the documented or a typical one, and the stated reason for the change concerns noise data, which favours detection. (d) stays yes (no branch, no input inspection) with a disclosure note.
* Other B1 cases with a comparable change against a documented parameter: only B1-04 (same source, same p < .01 documented, p < 0.05 used, reason not about noise). Marked (a) no for consistency; the designer may decide to waive it. This is a judgement on the wording 'documented or typical parameters'.
* Other deviations listed in item 7, checked and not comparable: B1-01 (z cut-off 1.645 and two-fold design: KRI09 states no cut-off), B1-02 (index clip, discussed under (d)), B1-03 (different but equivalent independent-measure device, no documented parameter), B1-06 and B1-07 (selection p < 0.05 where the sources state no level; the private notes' own t > 2 / p < 0.05 are the author's choice), B1-08 to B1-12 (no parameter change; B1-10 changes the test because of the control arm, discussed before).
* Therefore the final count is 10 pass, 2 fail (B1-04, B1-05, item (a)); the repair is the same for both: selection at p < 0.01 in both twins.

## Post-repair audit of B1-04 and B1-05 (PREREG 5.3)

Re-read both pairs after the author's repair. Checked: faulty and fixed differ in one line only (B1-04 the folds list, B1-05 the sel_act/ev_act line); the repaired selection line `keep = (r_sel > 0) & (tt > _tq(0.005, ...))` is identical in both twins; each file equals the skeleton outside the criterion body; the helper block is unchanged (same hash as the other 20 files); the mechanical report lists the same comparisons as before and no issues; ASSIGNMENT.json is unchanged (items (e) and (f) as before). The author's repair note in LOG.md and CASE.md item 7 state that nothing else changed, which matches the diffs. Criterion/claim consistency unchanged (B1-04 mean r >= 0.50; B1-05 slope >= 0.50 with one-sided p < 0.05).

* B1-04: (a) yes, (b) yes, (c) yes, (d) yes, (e) yes, (f) yes, (g) yes. Overall pass. Superseded earlier answer in this file: (a) no (re-examination), (a) yes (first audit).
* B1-05: (a) yes, (b) yes, (c) yes, (d) yes, (e) yes, (f) yes, (g) yes. Overall pass. Superseded earlier answer: (a) no (re-examination), (a) yes (first audit).
* Remarks for the report: the sidedness of the p < .01 selection is not stated in VUL09, two-sided was kept; with p < 0.01 an empty selection (None) is now the usual outcome in minus and noise samples for both twins (author's recorded consequence), so detection through those streams will be rarer; this follows from the documented level and is not a fidelity defect. Both pairs are repaired pairs and are to be reported as such (one repair each).
