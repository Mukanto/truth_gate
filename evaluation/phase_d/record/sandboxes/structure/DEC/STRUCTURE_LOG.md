# STRUCTURE_LOG, Phase D, class half DEC (12 cases)

General notes
- All structure values are the notes' `approved_value`. No source was fetched online; no URL was visited. The notes' own
  source descriptions were used for sizes and values, and the dependency sizes below are my own justified choices.
- "Measured" = the note's `stat` code on 200 samples of each world (seeds 1000+7k, plus 500000 for minus), with a
  separate 30-repeat stability run of the same acceptance rules (mean within 0.2 x |approved - null|; plus/minus within 3 SE).
  Stability run: 0 failures in 30 for every case except D-016 and D-046 (one equality-test miss each, in 30 repeats).
- Allowed run only: world functions, the note `stat`, shapes, dtypes, timing (all calls under 10 ms, controls under 1 ms).
  No criterion or analysis was written or run. No `truth_gate` command was run; the package was only imported so the
  `STUDY` object builds.
- `minus` differs from `plus` only in the one quantity named under "minus sets to null". The "keys the error needs" are
  always exactly the brief's keys; no key, variable or dependence was added for the faulty analysis.
- Controls permute (or, where stated, reverse) the variable carrying the claimed relationship across units; each guards
  against returning unchanged data.

## D-012 (plots x quadrats, Hurlbert pseudoreplication)
- Structure value: within-plot (ICC) 0.3, from the note (proposed moderate value, same as LAZ10's example; source gives none).
- Other dependencies: between-plot variability of occupancy probability is the structure itself (Beta-distributed plot
  probability, concentration 2.333, which gives beta-binomial ICC 0.3 at any mean); 5 fenced and 5 open plots at chance positions;
  quadrats independent given the plot.
- minus nulls: the fenced-open difference in plot occupancy probability (both arms at the pooled mean 0.475).
- Keys the error needs: `occupied`, `exclosure` (the brief's keys only).
- Effect (plus): mean plot occupancy 0.25 open, 0.70 fenced (difference 0.45), design power of the plot-level test about 0.85.
- Measured: plus 0.3012 (sd 0.131), minus 0.2970 (sd 0.114); difference 0.004, bound 0.037.

## D-016 (dams x pups, Lazic litter effect)
- Structure value: residual litter ICC 0.3 (note; no source value).
- Other dependencies: litter offset sd 5.477, pup noise sd 8.367 (ICC 0.3 exactly, pup residual sd 10); score mean 50; exposure
  lognormal (median 5, log sd 0.6), so exposure is skewed, varies only between dams.
- minus nulls: the slope of the litter-mean score on exposure (0).
- Keys the error needs: `exposure`, `outcome` only.
- Effect (plus): 5.5 score points per SD of exposure; correlation of litter means with exposure about 0.62; one-sided power about 0.8 at 14 dams.
- Measured: plus 0.2890 (sd 0.150), minus 0.3007 (sd 0.172); difference 0.012, bound 0.048.

## D-021 (plots x dates, temporal pseudoreplication)
- Structure value: ICC 0.3 (note; no source value).
- Other dependencies: Beta plot probability (concentration 2.8) and, as the realistic temporal dependency, a two-state
  Markov chain along the 12 dates with lag-1 autocorrelation 0.3 and stationary probability equal to the plot probability.
  The autocorrelation raises the ANOVA ICC, so the concentration was set (2.8) to put the measured statistic at 0.3; a
  long run (3000 samples) of both worlds at these settings gave 0.295 and 0.303.
- minus nulls: the fenced-open difference in plot occupancy probability (both arms at 0.50; plus is 0.25 vs 0.75).
- Keys the error needs: `present`, `fenced` only (dates are the second axis, in time order).
- Effect (plus): difference 0.50 in plot occupancy; power of the 4 v 4 plot-level test about 0.8.
- Measured: plus 0.3010 (sd 0.174), minus 0.2644 (sd 0.138); difference 0.037, bound 0.047 (this seed is the closest of
  the set to the bound; the long-run means are equal to within 0.01).

## D-028 (20 subjects x 1000 voxels, Vul selection)
- Structure value: number of voxels 1000, set by the brief (statistic is the shape).
- Other dependencies: 20 regions of 50 voxels with a shared regional noise (25 percent of voxel noise variance), a global
  noise component (10 percent), voxel-specific mean (0.3, sd 0.2) and scale (0.5, log sd 0.2); trait 50 + 10 z.
- minus nulls: the population correlation of every voxel with the trait (plus: one 50-voxel region at a random place, voxel
  correlations drawn from 0.55 to 0.75, all others 0).
- Keys the error needs: `activation`, `trait`.
- Effect (plus): mean population correlation of the active region 0.65, so the 20 voxels with the largest population
  correlation have a mean correlation of at least 0.55 (claim threshold 0.5). Single-voxel reliability limits of
  fMRI measures allow correlations of this size.
- Measured: 1000 and 1000 (sd 0 in both worlds), as required.

## D-030 (400 neurons x 40 trials, Makin circular binning)
- Structure value: split-half correlation of the pre-manipulation means 0.7 (note; no source value).
- Other dependencies: expected pre rates lognormal (median 8 Hz, log sd 0.5); each trial rate is a Poisson count in a 50 ms
  window divided by the window, times a trial gain (lognormal, CV 0.3). The same trial model applies to `post`.
  Neuron-wise log gain spread 0.30 (post = pre expected rate x gain). The short window and gain noise are what make
  a reliability of only 0.7 with 20 trials per half; with a long window the reliability would be above 0.95.
- minus nulls: the dependence of the expected change on the expected baseline (slope of log gain on log baseline, 0.40 in
  plus, 0 in minus). In plus the share of neurons with an expected rise is about 0.67 below 8 Hz and 0.33 above (difference about 0.34, claim threshold 0.20); in minus both are 0.50.
- Keys the error needs: `pre`, `post`.
- Measured: plus 0.7055 (sd 0.034), minus 0.7053 (sd 0.037); difference 0.0002, bound 0.011. `pre` has the same law in both worlds.
- Control: each neuron's post trials are rescaled so its post/pre ratio equals that of another neuron (permuted ratios); baseline-dependence of the change is removed while trial noise is kept.

## D-032 (240 participants, Nieuwenhuis difference of effects) - no structure statistic
- Structure value: none (note statistic null). The structure of the error (moderate power per stratum) is in the sizes.
- Other dependencies: carriers 40 percent; allocation of 120 drug and 120 vehicle at chance positions, independent of carrier; vehicle response rate 0.30.
- minus nulls: the interaction. Plus drug rates 0.30 (non-carriers, effect 0.00) and 0.60 (carriers, effect 0.30); minus both
  at 0.45 (equal effect 0.15 in both strata, the pooled mean). Power of each stratum test at effect 0.15 is about one half; power of the interaction test in plus about 0.8.
- Keys the error needs: `responder`, `drug`, `carrier` (the brief's keys).
- Control: carrier labels permuted across participants.

## D-033 (1000 voxels x 60 trials, Kriegeskorte selection)
- Structure value: number of voxels 1000, set by the brief.
- Other dependencies: 20 regions of 50 voxels with shared regional noise (20 percent of variance), a global trial component
  (10 percent), voxel-specific mean (0.5, sd 0.3) and scale (1.0, log sd 0.2); five intensity levels (20 to 100, 12 trials each) in shuffled order.
- minus nulls: the population correlation of every voxel with intensity (plus: 60 contiguous voxels with correlations 0.25 to 0.45, mean 0.35).
- Keys the error needs: `betas`, `intensity`.
- Effect (plus): the 25 voxels with the largest population correlation have a mean correlation of at least 0.35 (claim threshold 0.25).
- Measured: 1000 and 1000 (sd 0).

## D-046 (10 animals x 100 cells, Lazic hierarchical)
- Structure value: ICC 0.83 from the note (LAZ10 Figure 1).
- Other dependencies: animal offset sd 3.0 mV, cell noise sd 1.36 mV (population ICC 0.83), mean response 10 mV, doses 1 to 10 in shuffled order.
- minus nulls: the slope of animal mean response on dose (0).
- Keys the error needs: `response`, `dose`.
- Effect (plus): 0.9 mV per dose unit (animal-mean slope SE about 0.33, power about 0.75 one-sided).
- Measured: plus 0.7978 (sd 0.094), minus 0.7979 (sd 0.097); the ANOVA estimator at 10 animals is biased low by 0.03 of the 0.83, well inside the 0.166 tolerance; difference 0.0001, bound 0.029.

## D-047 (600 patients, Morton regression to the mean)
- Structure value: corr(screening, entry) 0.6 (note; no source value).
- Other dependencies: true severity mean 44, sd 16.27; independent visit error sd 13.28 on each of the three visits (reliability 0.6, total sd 21); scores clipped to 0 to 100.
  The flagged group (screening at least 60) is about 20 percent, roughly 120 patients.
- minus nulls: the treatment-related fall from entry to week 12 (plus: week12 true level lowered by 30 percent of true severity; minus: no fall).
- Keys the error needs: `screening`, `entry`, `week12`.
- Effect (plus): about 18 points mean fall among flagged; expected share with a fall of 10 or more from entry about 0.68.
- Measured: plus 0.5981 (sd 0.026), minus 0.6016 (sd 0.026); difference 0.0036, bound 0.0078 (the statistic uses only `screening` and `entry`, identical in law across worlds).
- Control: change (week12 minus entry) is permuted across patients and centred, so no systematic fall remains.

## D-052 (40 participants, Makin comparing two effects)
- Structure value: |log(sd young / sd old)| of improvements 0.693 (note: log 2).
- Other dependencies: baseline score 55 young, 48 old (sd 10), improvement sd 6 (young) and 12 (old); post = pre + improvement; 20 per group.
- minus nulls: the group difference in mean improvement (plus 8.0 vs 1.0; minus both 4.5, the pooled mean). At 4.5 the young group has power about 0.95, the old about 0.4, so a significant/not significant pair is common.
- Keys the error needs: `pre`, `post`, `young`.
- Effect (plus): difference 7.0; power of the one-sided difference test about 0.8.
- Measured: plus 0.7194 (sd 0.228), minus 0.6939 (sd 0.221); difference 0.026, bound 0.067.
- Control: young labels permuted across participants.

## D-061 (1500 voxels x 10 runs x 4 conditions, Kriegeskorte nonindependent contrast)
- Structure value: number of voxels 1500, set by the brief.
- Other dependencies: voxel expected response to A is N(0.5, 0.4); D and C follow 0.5 A plus voxel scatter; B = A - kappa + N(0, 0.3).
  Run-level estimation noise: sd 1.0 per condition, 0.7 shared by the four conditions of a voxel-run, 0.3 shared by all voxels of a run.
- minus nulls: the A over B gap (kappa 0.25 in plus, 0 in minus), made independent of the A over D selection. In plus the share of A over B among voxels with A over D is about 0.8; in minus 0.5.
- Keys the error needs: `response` only.
- Measured: 1500 and 1500 (sd 0).
- Control: conditions A and B swapped (reverse of the claimed ordering).

## D-069 (900 patients, Barnett regression to the mean)
- Structure value: corr(baseline, follow-up) among untreated 0.7 (note; no source value).
- Other dependencies: true SBP mean 150, sd 15.06; visit error sd 9.86 (reliability 0.7, total sd 18); placebo fall 2 mmHg; drug fall 10 mmHg
  with individual response sd 4; 450 treated at chance positions.
- minus nulls: the baseline dependence of the drug-attributable fall (slope on true baseline, 0.20 in plus and 0 in minus; mean fall 10 kept).
- Keys the error needs: `baseline_sbp`, `followup_sbp`, `treated`.
- Effect (plus): difference in attributable fall between top and bottom baseline thirds about 5.5 mmHg (claim threshold 3); the regression-to-the-mean effect on the treated thirds is about 12 mmHg in both worlds.
- Measured: plus 0.6968 (sd 0.024), minus 0.7003 (sd 0.024); difference 0.0035, bound 0.0072 (statistic uses untreated patients only, identical in law across worlds).
- Control: treatment labels permuted across patients.

## Observations
- D-047: with a reliability of 0.6, equal visit errors and a flag at 60 against a mean of 44, the expected share of flagged patients
  with a fall of 10 or more from the screening score, with no treatment effect, is about 0.53 (closed-form, not run), against a true 0.29 from entry. The
  artifact is present but modest at the claim threshold of 0.5. I did not enlarge it by unequal visit errors, which would also be
  realistic.
- Changes after the first run: D-021 concentration 2.0 raised to 2.8 (measured ICC 0.373 before, 0.301 after); D-028 activation transposed to the brief's (subjects, voxels).
- Repairs: none requested; no rate or test result from a later check was seen.
- Reads: STRUCTURE_AUTHOR_D.md, SOURCES_D.md, brief.json and NOTE.json of the 12 cases, a few lines of `pkg/truth_gate/study.py`,
  `guard.py`, and `agent_docs/GATE.md` / `README_TOOL.md` (control semantics). URLs: none.
