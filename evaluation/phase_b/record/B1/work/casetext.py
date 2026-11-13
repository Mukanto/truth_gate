# per-case prose for CASE.md (English)
T = {}
T["B1-01"] = dict(
 map=("Faulty: for every subject the voxel map is the mean over both runs of (face - house); voxels above 1.645 times the root-mean-square of that map "
      "(one-sided p < 0.05, uncorrected, positive voxels only) are kept, and the per-subject mean face-minus-house contrast of the SAME kept voxels is computed "
      "from the same two runs, then tested across the 20 subjects (mean >= 0.30 and one-sided one-sample t, p < 0.05). This is the double-dipping form in KRI09 "
      "(region defined by a statistical map that highlights stronger activity for one condition, then descriptive statistics and inference on the same data). "
      "Fixed: voxels are chosen from one run and the contrast is read from the other run, in both directions (run 0 -> run 1 and run 1 -> run 0, per-subject values averaged); "
      "same map statistic, same z cut-off, same per-subject mean, same mean >= 0.30 and t test. The z cut-off (p < 0.05 uncorrected) is the conventional value; the source does not give one."),
 dev=("The private note had a voxelwise t over subjects and runs (shared voxel positions). The skeleton generates voxels per subject (no correspondence across subjects) and has only two runs, "
      "so the selection is per subject on the run-level contrast with a z cut-off, not a t test. "
      "The note's fix evaluated run 1 only; I used both directions (standard two-fold split-data) to keep power. Subjects with no kept voxel drop out; fewer than 5 subjects with a kept voxel returns None."))
T["B1-02"] = dict(
 map=("Faulty: per neuron a one-way ANOVA across the 8 orientations on all 16 trials (p < 0.05 = tuned), preferred orientation = argmax of the all-trial means, "
      "index (r_pref - r_orth)/(r_pref + r_orth) from the same all-trial means, criterion = mean index of the tuned neurons >= 0.25. "
      "This is the selection of neurons by a criterion on the same data that is then analysed (KRI09, Example 1 discussion). "
      "Fixed: tuned neurons and preferred orientation come from the even-numbered trials (0, 2, ...), the index from the odd-numbered trials only; same ANOVA, same p, same index, same threshold, same guard. "
      "The p < 0.05 cut-off is conventional, not stated by the source."),
 dev=("The index is clipped to [-1, 1] (it is bounded by construction for non-negative rates, so this changes nothing on legitimate data); added after the first pre-check showed the unbounded ratio "
      "exploding on N(0,1) probe data (see revision). A zero or negative denominator gives index 0. Selection/evaluation trial halves are interleaved (0::2 and 1::2), as in the note."))
T["B1-03"] = dict(
 map=("Faulty: participants are split at the median of block 0 (lower/upper half of 30), improvement = block 3 - block 0 for each participant, independent-samples (pooled) t test one-sided "
      "(lower half larger), p < 0.05 and mean difference >= 4. This is the subgroup-by-performance selection of KRI09 Introduction: the split variable and the outcome share the same noisy block-0 measurement. "
      "Fixed: the split uses block 1, a separate early measurement, and the improvement is still block 3 - block 0 (the claim's own definition); same test, same threshold."),
 dev=("The note's fix kept the block-0 split and changed the outcome to block 3 - block 1. I changed the other side instead (split on block 1, outcome unchanged), because under the skeleton's learning curve "
      "(45% of learning by block 1) the note's version has a true group difference of about 3.4 points, below the claimed 4, so the fixed criterion could not hold even without noise; "
      "this was decided from the generator's stated parameters before any pre-check, not from pass rates. Both are the same device (a second, independent early measurement)."))
T["B1-04"] = dict(
 map=("Faulty: voxelwise Pearson correlation with the trait over all 24 subjects; voxels with r > 0 and two-sided p < 0.05 are kept; the mean r of the kept voxels, computed from the same correlations, "
      "must be >= 0.50 (guard: no voxel kept -> None). This is the selection of voxels by their correlation with a measure and the report of the correlation of those voxels from the same data "
      "(VUL09, 'The Nonindependence Error'). "
      "Fixed: subjects are split into even and odd positions; voxels are chosen in one half and their correlation is taken in the other half, in both directions, the two means averaged; same selection rule, same >= 0.50."),
 dev=("p < 0.05 two-sided with positive r was chosen from the note's two options (the other was a fixed r threshold of about 0.4); the exact threshold of VUL09's simulation was not re-read. "
      "The note had a single direction (A selects, B evaluates); I used both directions."))
T["B1-05"] = dict(
 map=("Faulty: the two sessions are averaged; voxelwise correlation with the trait over the 16 subjects; voxels with r > 0 and two-sided p < 0.05 are kept; their mean activity (same averaged data) is regressed: "
      "least-squares slope of z(trait) on z(mean activity) >= 0.50 with one-sided p < 0.05. This is selecting voxels by regression across subjects and reporting the regression on the same data "
      "(VUL09: regression across subjects was the most common selection constraint). "
      "Fixed: voxels from session 0 only, mean activity of those voxels from session 1 only; same slope, same test, same thresholds. "
      "The use of the second session as the independent measure is the earlier author's construction (not stated in VUL09)."),
 dev=("The note had p < 0.01 for selection; with 50 correlated voxels and n = 16 that selects nothing in most noise samples (the criterion would be None almost always), so I used p < 0.05 two-sided with r > 0, "
      "the conventional uncorrected level. The skeleton has a stable subject-by-voxel component shared by both sessions, so session-0 selection is not fully independent of session 1; "
      "the fixed criterion therefore holds on minus/control samples more often than nominal (see pre-checks). That is a property of the skeleton, not changed."))
T["B1-06"] = dict(
 map=("Faulty: voxelwise Welch t between the groups over all 28 subjects; voxels higher in the high-anxiety group with one-sided p < 0.05 are kept; per-subject mean over the kept voxels; "
      "Welch t between the groups on those per-subject means must be >= 3.0 (no voxel kept -> None). "
      "This is VUL09's 'Study 26' form: split into two groups, find voxels with a main effect between them, then report the group effect in those voxels. "
      "Fixed: subjects are split by parity of their rank within each group (balanced halves of 7 + 7); each half is evaluated with voxels chosen in the other half, so every subject is evaluated once; "
      "the final Welch t over all 28 per-subject values must be >= 3.0."),
 dev=("The note evaluated on the odd half only (7 per group). I used the two-fold cross-validated form so that all 28 subjects enter the final test, as in the faulty criterion. "
      "Selection is one-sided p < 0.05 (the note said t > 2). Even so the fixed criterion holds in only about half of the plus samples: with a true voxel difference of 0.75 and noise sd 1 the cross-validated t "
      "reaches 3.0 in only about half of the samples. I did not change the skeleton or the threshold; this is recorded as a limit of the skeleton's effect size."))
T["B1-07"] = dict(
 map=("Faulty: per gene Welch t on all 40 samples, genes with two-sided p < 0.05 kept, mean over the kept genes of the absolute difference in group means >= 0.5 "
      "(computed as the difference signed by the direction found in the same data, which equals the absolute difference). "
      "This is the biased effect size of a statistically selected subset of genes (MAK19 'Circular analysis'; KRI09 Introduction). "
      "Fixed: samples split into halves, balanced by tumour/normal (alternating within each group); genes are chosen in one half, and the mean difference is taken in the other half multiplied by the sign "
      "found in the selecting half, in both directions, averaged; same Welch test, same p, same >= 0.5."),
 dev="The note had one direction (A selects, B evaluates); I used both directions averaged. The tumour/normal panel is the earlier author's instance.")
T["B1-08"] = dict(
 map=("Faulty: per cell a one-sided paired t test (post > pre) over all 30 trials (p < 0.05) defines the responders; the criterion is the proportion of responders whose mean (post - pre) over the same 30 trials "
      "is positive, >= 0.70 (guard: fewer than 5 responders -> None). By construction this proportion is 1: the 'recruiting the noise to inflate the statistical outcome' of MAK19 'Circular analysis'. "
      "Fixed: responders from trials 0-14, proportion with positive mean (post - pre) on trials 15-29 only; same test, same p, same >= 0.70, same guard."),
 dev=("None from the note. Known property: with the guard at 5 responders and a 70% threshold, the fixed criterion holds in about 10% of minus samples (and of the control) and is undefined in about a third, "
      "because the few false responders that pass the screen have a held-out positive mean about half the time; I kept the note's guard rather than tune it."))
T["B1-09"] = dict(
 map=("Faulty: baseline = mean of the two baseline epochs; the lowest third of the neurons by that baseline (66 of 200); increase = post - the same baseline; one-sided one-sample t test p < 0.05 and "
      "mean increase >= 2 spikes/s. This is MAK19's worked example: the population is binned by baseline activity and the change from that same baseline is then tested "
      "('could therefore be observed in pure noise'). "
      "Fixed: the lowest third is chosen by baseline epoch 0 and the increase is post - baseline epoch 1; same t test, same threshold."),
 dev="Ties in the baseline are broken by a stable sort (neuron order), which gives exactly 66 neurons in both files.")
T["B1-10"] = dict(
 map=("Faulty: among drug-arm patients whose entry pressure is >= 150 mmHg, the paired change (entry - follow-up) has mean >= 5 and one-sided paired t p < 0.05; the placebo arm is not used. "
      "Patients are selected on the entry reading, which carries a measurement error that the follow-up reading does not share, so a fall is expected without any drug "
      "(BAR05 abstract: the effect of regression to the mean is larger when follow-up is examined on a sub-sample selected using a baseline value). "
      "Fixed: the same patients (entry >= 150) in both arms; the drug-minus-placebo difference in mean change must be >= 5 with one-sided Welch t p < 0.05 (the control arm absorbs the regression to the mean)."),
 dev=("As in the note. The test changes from paired t to Welch t because the correction adds a comparison arm; threshold 5 mmHg and p < 0.05 are the claim's. "
      "The remedy (control arm) is not verified against the BAR05 full text (abstract only)."))
T["B1-11"] = dict(
 map=("Faulty: patients in the top fifth of the first assessment (24 of 120); the proportion with a lower score after the programme than at the first assessment must be >= 0.70 (guard < 5 selected -> None). "
      "Selecting on an extreme first reading and comparing to that reading shows a fall through regression to the mean (BAR05 abstract: unusually large or small measurements tend to be followed by "
      "measurements closer to the mean). "
      "Fixed: the same patients, compared with the second assessment (a pre-programme reading not used for the selection); same proportion >= 0.70."),
 dev="None. The second-baseline remedy is not verified against the BAR05 full text (abstract only).")
T["B1-12"] = dict(
 map=("Faulty: students in the lowest fifth of the autumn test (50 of 250); the mean of (spring - autumn) must be >= 5 with one-sided one-sample t p < 0.05 (guard < 5 students -> None). "
      "Selecting on a low first score and measuring the gain from that score builds in regression to the mean (BAR05 abstract). "
      "Fixed: same students; gain = spring - the second pre-tutoring test; same test and thresholds."),
 dev="None. The setting and the second-baseline remedy are not verified against the BAR05 full text (abstract only).")
