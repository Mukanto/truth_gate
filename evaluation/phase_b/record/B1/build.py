import json, re, os
D = os.path.dirname(os.path.abspath(__file__))

def k(key, shape, dtype, meaning):
    return {"key": key, "shape": shape, "dtype": dtype, "meaning": meaning}

B = []  # (brief, private)

def add(lid, claim, keys, sizes, src, passage, faulty, fixed, notes):
    B.append(({"local_id": lid, "claim": claim, "data_keys": keys, "sizes": sizes},
              {"local_id": lid, "source": src, "passage": passage, "faulty": faulty, "fixed": fixed,
               "subtype": "", "notes": notes}))

add("B1-01",
    "In a 60-voxel region of ventral visual cortex, the voxels that respond more to faces than to houses show a mean "
    "face-minus-house response of at least 0.30 percent signal change. The claim holds when this mean (taken per subject "
    "and then averaged over the 20 subjects) is at least 0.30 and significantly above zero (one-sided one-sample t-test "
    "across subjects, p < 0.05).",
    [k("face", "(subjects, runs, voxels)", "float", "percent signal change to face pictures, two scanning runs per subject"),
     k("house", "(subjects, runs, voxels)", "float", "percent signal change to house pictures, same layout as face")],
    "20 subjects, 2 runs, 60 voxels (voxel count capped; fMRI regions in the source are larger).",
    "KRI09",
    "KRI09, Introduction: 'In neuroimaging, an example of selection is the definition of a region of interest (ROI) by means of a statistical mapping that highlights voxels more strongly active during one condition than another.' Also: double dipping 'will give distorted descriptive statistics and invalid statistical inference'; independent data or a split-data analysis is the remedy (Fig. 4 policy). Example 2 simulates 30x30x20 voxels, 200 time points, four conditions.",
    "Per voxel, compute a face-minus-house t (or mean) over subjects and runs from ALL data; keep voxels with p<0.05 (or the "
    "top fraction, e.g. top 20%) positive; per-subject mean face-minus-house over the kept voxels and ALL runs; mean across "
    "subjects >= 0.30 and one-sided one-sample t p<0.05. Parameters: p<0.05 uncorrected, positive voxels only.",
    "Choose voxels from one run (run 0; or run 0 chosen and run 1 evaluated), compute the per-subject contrast of those "
    "voxels from the other run only, then the same mean>=0.30 and t-test. Same computational structure.",
    "Selection key: independent runs. In a world without the face/house difference the faulty rule still passes because "
    "voxels with positive noise are kept.")

add("B1-02",
    "Among 150 recorded V1 neurons, the neurons that are tuned to orientation have a mean orientation selectivity index of at "
    "least 0.25, where each neuron's index is (r_pref - r_orth) / (r_pref + r_orth), r_pref is its mean rate at its preferred "
    "orientation and r_orth its mean rate at the orientation 90 degrees away.",
    [k("rate", "(neurons, orientations, trials)", "float",
       "non-negative firing rate in spikes/s of each neuron to each of 8 equally spaced grating orientations (0 to 157.5 degrees), 16 repeats of each"),],
    "150 neurons, 8 orientations, 16 trials (single recording session; source discusses typical single-unit samples of this size).",
    "KRI09",
    "KRI09, Example 1 discussion: 'In single-cell recording, for example, it is common to select neurons according to some criterion (e.g. visual responsiveness or selectivity) before applying further analyses to the selected subset. If the selection is based on the same data set as used for selective analysis, biases will arise.' (orientation tuning index is my instance of 'selectivity')",
    "Per neuron, one-way ANOVA across orientations on ALL trials; keep neurons with p<0.05; preferred orientation = argmax of "
    "the mean over ALL trials; index from the same means; criterion = mean index of kept neurons >= 0.25. Guard: at least "
    "one neuron kept.",
    "Tuned neurons and preferred orientation determined from odd trials (trial 0,2,..), index computed from even trials only; "
    "same mean>=0.25 criterion; same guard.",
    "Statistic: mean of a bounded index. Pure-noise neurons with p<0.05 show a positive index because argmax is picked on the same means.")

add("B1-03",
    "In a study of 60 participants, those who perform worst at the start of a perceptual-learning task benefit most from training: the "
    "improvement (late-block score minus early-block score) of the lower-scoring half exceeds that of the higher-scoring half by at "
    "least 4 points, with an independent-samples t-test p < 0.05 (one-sided).",
    [k("score", "(participants, blocks)", "float", "percent correct (0 to 100) in each of 4 consecutive blocks of the task, block 0 first and block 3 last")],
    "60 participants, 4 blocks.",
    "KRI09",
    "KRI09, Introduction (Fig. 1 text): 'In behavioral studies, an example of selection is the division of a group of subjects into subgroups based on task performance.' The same text states that selection inside the same data distorts descriptive statistics and tests.",
    "Split participants at the median of block 0 (lower vs upper half); improvement = block 3 - block 0 per participant; independent-samples t (one-sided, lower half larger) p<0.05 and mean difference >= 4.",
    "Split participants at the median of block 0; improvement = block 3 - block 1 per participant (block 1 not used for the split); same one-sided independent t and mean difference >= 4.",
    "Replaces the earlier EEG time-window draft (see LOG). Statistic: independent-samples t / mean difference of change between two data-defined subgroups. The fix uses a second early block as an independent baseline; it is a standard correction (BAR05-style) and the split-data policy in KRI09 Fig. 4.")

add("B1-04",
    "In a 60-voxel region of anterior insula, the voxels whose activity relates positively to trait empathy show a mean "
    "Pearson correlation of at least 0.50 with the trait score across the 24 subjects.",
    [k("act", "(subjects, voxels)", "float", "activation (beta) to a pain-observation contrast, one value per subject and voxel"),
     k("trait", "(subjects,)", "float", "questionnaire empathy score per subject")],
    "24 subjects, 60 voxels (VUL09 reports about 8-30 subjects and thousands of voxels; voxel count capped).",
    "VUL09",
    "VUL09, 'The Nonindependence Error': 'This approach amounts to selecting one or more voxels based on a functional analysis and then reporting the results of the same analysis and functional data from just the selected voxels.' Fig. 4 simulates 10 subjects and 10,000 voxels of pure noise.",
    "Voxel-wise correlation of act with trait over all 24 subjects; keep voxels with r > 0 and p<0.05 (or above a threshold of r such as 0.4); report the mean r of kept voxels and require >= 0.50. Guard: at least one voxel kept (else None).",
    "Split subjects in two halves (e.g. even and odd subject index); choose voxels in half A, compute their mean correlation in half B (and optionally the reverse, averaged); require >= 0.50.",
    "Alternative acceptable fix: leave-one-out selection. Sample size note: halves of 12 subjects give a weak test; the world author must use a realistic true correlation.")

add("B1-05",
    "In a 50-voxel region of medial prefrontal cortex, the voxels that track trait social anxiety have a mean activity "
    "that predicts the trait: the least-squares slope of the standardized trait score on the standardized mean activity of "
    "those voxels across the 16 subjects is at least 0.50, with one-sided p < 0.05.",
    [k("act", "(subjects, sessions, voxels)", "float", "activation (beta) to a social-evaluation task; two scanning sessions on separate days"),
     k("trait", "(subjects,)", "float", "questionnaire social-anxiety score per subject")],
    "16 subjects, 2 sessions, 50 voxels (VUL09: typical n around 16).",
    "VUL09",
    "VUL09, survey section: 53% of respondents said 'regression across subjects' was the functional constraint used to select voxels; the reliability discussion mentions two scanning sessions (Manoach et al. 2001). Using a second session as the independent measure is my construction, not stated in VUL09.",
    "Average the two sessions; voxel-wise correlation with trait on all 16 subjects; keep voxels with r>0 and p<0.01; average their activity per subject; slope of z(trait) on z(mean activity) with one-sided slope t-test p<0.05, slope >= 0.5.",
    "Choose voxels from session 0 only; compute mean activity of those voxels from session 1 only; same slope and test.",
    "Statistic: regression slope. Independent measurement session rather than independent subjects.")

add("B1-06",
    "Among 28 subjects (14 high-anxiety and 14 low-anxiety by interview), in the voxels of a 40-voxel amygdala region that react more "
    "strongly to threatening pictures in the high-anxiety group, the group difference in mean reactivity has a Welch t statistic of at "
    "least 3.0.",
    [k("react", "(subjects, voxels)", "float", "response to threat minus neutral pictures, one value per subject and voxel"),
     k("high_anx", "(subjects,)", "bool", "True for the 14 high-anxiety subjects; subjects ordered so that groups alternate (True, False, True, False, ...)")],
    "28 subjects (14 + 14), 40 voxels.",
    "VUL09",
    "VUL09, discussion of gradations of nonindependence: Study 26 'split the data into two groups: those with high IAT scores and those with low IAT scores. They then found voxels that showed a main effect between these two groups and computed a correlation within those voxels.' The Welch-t statistic is my variant of reporting the group effect in those voxels.",
    "Voxel-wise Welch t between groups on all subjects; keep voxels with t>2 (p<~0.05, high > low); average kept voxels per subject; Welch t between groups; require >= 3.0.",
    "Split subjects by index parity within each group (even half selects voxels, odd half evaluates, groups stay balanced) and compute the Welch t on the evaluation half only; require >= 3.0. Guard on group size >= 3.",
    "Statistic: Welch t. Evaluation half has 7 subjects per group so the threshold should be reachable only for a real effect; world author sets effect size. Note alternation convention given in the key meaning so the criterion can split by parity.")

add("B1-07",
    "In a panel of 60 candidate genes, the genes that differ between tumour and normal tissue have a mean absolute log2 fold "
    "change of at least 0.5, in 20 tumour and 20 normal samples.",
    [k("expr", "(samples, genes)", "float", "log2 expression level, one value per sample and gene"),
     k("tumour", "(samples,)", "bool", "True for tumour samples (20), False for normal (20)")],
    "40 samples (20 + 20), 60 genes (source studies use thousands of genes; capped).",
    "MAK19",
    "MAK19, 'Circular analysis': 'circular analysis is used to divide ... or reduce (e.g. defining a region of interest ...) the complete dataset using a selection criterion that is retrospective and inherently relevant to the statistical outcome.' KRI09 Introduction lists 'inferential analysis performed for a statistically selected subset of genes'. The tumour/normal panel is my instance.",
    "Per gene Welch t on all 40 samples; keep genes with p<0.05; mean of |difference in group means| over kept genes >= 0.5. Guard: >=1 gene kept.",
    "Split samples into two halves with equal tumour/normal counts (alternate within each group); choose genes in half A; compute absolute fold change in half B with the sign of half A's change (so the quantity is the signed change in the direction found in A); mean >= 0.5.",
    "Fixed must align signs: independent half-B fold change multiplied by sign found in half A. The faulty absolute value is the documented biased effect size.")

add("B1-08",
    "Of the 120 cells in a calcium-imaging field of view, those that respond to the tone are mostly genuine responders: at least 70% of "
    "them show a larger mean fluorescence after tone onset than before it.",
    [k("pre", "(cells, trials)", "float", "mean fluorescence (dF/F) in the 1 s before tone onset, per cell and trial"),
     k("post", "(cells, trials)", "float", "mean fluorescence (dF/F) in the 1 s after tone onset, per cell and trial")],
    "120 cells, 30 trials.",
    "MAK19",
    "MAK19, 'Circular analysis': 'circular analysis recruits the noise (inherent to any empirical data) to inflate the statistical outcome'; its worked example is a neuronal population measured before and after a manipulation. KRI09 describes selecting neurons by visual responsiveness. The calcium-imaging responders with a tone are my instance.",
    "Per cell paired t (post vs pre) over all 30 trials; responders = p<0.05 (either sign allowed? use post>pre only); proportion of responders with mean(post-pre) over all 30 trials > 0 must be >= 0.70. (Equals 1 by construction.)",
    "Responders determined from trials 0..14; proportion of responders with mean(post-pre) > 0 computed on trials 15..29 only; >= 0.70.",
    "Statistic: proportion. Under no tone effect the faulty proportion is 1.0 for every cell that passes the screen; the fixed one is about 0.5. Guard: at least 5 responders.")

add("B1-09",
    "In a recording of 200 cortical neurons, the neurons that fire least at baseline show an increase in firing rate after the "
    "manipulation of at least 2 spikes/s on average. The claim holds when a one-sample t-test of the per-neuron increase against zero, "
    "over the low-baseline neurons, is significant at p < 0.05 (one-sided) and the mean increase is at least 2.",
    [k("base", "(neurons, epochs)", "float", "mean firing rate in spikes/s in two separate pre-manipulation epochs of equal length"),
     k("post", "(neurons,)", "float", "mean firing rate in spikes/s in the epoch after the manipulation")],
    "200 neurons, 2 baseline epochs.",
    "MAK19",
    "MAK19, section 'Circular analysis': 'They therefore split the population to sub-groups, by binning the data based on the activity levels observed at baseline. This leads to a significant interaction effect - those neurons that initially produced low responses show response increases ... could therefore be observed in pure noise.'",
    "Baseline = mean of the two baseline epochs; lowest-baseline third of neurons; increase = post - baseline for those neurons; one-sample t vs 0 (one-sided) p<0.05 and mean >= 2. Guard: >=5 neurons.",
    "Choose the lowest third by baseline epoch 0; increase = post - baseline epoch 1; same one-sample t and mean >= 2.",
    "Replaces the earlier compound-screen draft (setting not in any source). Statistic: one-sample t over a data-defined subgroup. Source example is exactly neurons binned on baseline.")

add("B1-10",
    "In patients whose systolic blood pressure is at least 150 mmHg at entry, the drug lowers systolic pressure by at least 5 mmHg "
    "over 12 weeks. The claim holds when the estimated lowering is at least 5 mmHg and one-sided p < 0.05.",
    [k("sbp", "(patients, visits)", "float", "systolic pressure in mmHg at entry (visit 0) and after 12 weeks (visit 1)"),
     k("drug", "(patients,)", "bool", "True for patients given the drug, False for patients given placebo")],
    "160 patients (about 80 per arm), 2 visits.",
    "BAR05",
    "BAR05 abstract (verified): 'The effect of RTM in a sample becomes more noticeable with increasing measurement error and when follow-up measurements are only examined on a sub-sample selected using a baseline value.' Remedy per abstract: 'better study design and use of suitable statistical methods'. Full text not accessible: the blood-pressure setting and the placebo-arm remedy are NOT VERIFIED against the full text.",
    "Among drug-arm patients with entry sbp >= 150, paired change (entry - follow-up) mean >= 5 and one-sided paired t p<0.05; control arm not used. Guard: >=5 such patients.",
    "Among all patients with entry sbp >= 150, compare the change (entry - follow-up) between drug and placebo arms: difference in means >= 5 and one-sided Welch t p<0.05. Guard: >=3 per arm.",
    "Threshold selection on the noisy baseline. Statistic: mean change, with control arm in the fix. Entry is ~ true level plus noise (sd about 10).")

add("B1-11",
    "Among patients with a depression score in the top fifth at the first assessment, at least 70% have a lower score after the 8-week "
    "programme than before it.",
    [k("score", "(patients, visits)", "float", "depression questionnaire score: visit 0 = first assessment, visit 1 = second assessment just before the programme, visit 2 = after the programme"),],
    "120 patients, 3 visits.",
    "BAR05",
    "BAR05 abstract (verified): 'unusually large or small measurements tend to be followed by measurements that are closer to the mean.' The second-baseline remedy is NOT VERIFIED (full text not accessible). MAK19 'Circular analysis' also describes binning on baseline and then showing change as an artefact.",
    "Select patients in the top fifth of visit 0; proportion with visit 2 < visit 0 must be >= 0.70. Guard: >=5 selected.",
    "Select patients in the top fifth of visit 0; proportion with visit 2 < visit 1 (a baseline not used for selection) must be >= 0.70.",
    "Statistic: proportion. Faulty compares to the selection measurement. Note the world author should place the programme effect only between visit 1 and visit 2.")

add("B1-12",
    "Students in the lowest fifth of the autumn test gain at least 5 points on the spring test after the tutoring programme: the claim holds "
    "when the mean gain of those students is at least 5 and one-sided one-sample t-test p < 0.05.",
    [k("score", "(students, tests)", "float", "test scores out of 100: test 0 = autumn, test 1 = a second test given just before the tutoring began, test 2 = spring")],
    "250 students, 3 tests.",
    "BAR05",
    'BAR05 abstract (verified): same sentence as B1-10 about a follow-up on a sub-sample selected using a baseline value. The education / test-score setting is NOT VERIFIED (full text not accessible).',
    "Students in the bottom 20% of test 0; mean (test 2 - test 0) >= 5 and one-sided one-sample t p<0.05. Guard: >=5 students.",
    "Same students (bottom 20% of test 0); mean (test 2 - test 1) >= 5 and one-sided one-sample t p<0.05.",
    "Statistic: mean gain with t test, low-extreme selection, larger n. Overlaps B1-11 in the fixing device but differs in statistic, extreme direction, n.")

briefs = [b for b, _ in B]
priv = [p for _, p in B]
json.dump(briefs, open(os.path.join(D, "BRIEFS.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
json.dump(priv, open(os.path.join(D, "PRIVATE.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)

banned = ["circular","double dip","leak","pseudorepl","coupl","spurious","non-independ","nonindepend",
          "regression to the mean","selection bias","overfit","inflat","contaminat","optimis"]
txt = json.dumps(briefs).lower()
for w in banned:
    if re.search(w, txt):
        print("BANNED", w)
for b in briefs:
    for kk in b["data_keys"]:
        assert kk["dtype"] in ("float", "bool")
print(len(briefs), "ok")
