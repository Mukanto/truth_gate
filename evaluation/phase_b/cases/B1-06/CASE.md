# B1-06 (W09)

1. **Case**: B1-06; world id W09; class B-1; subtype: (none); source key VUL09.

2. **Documented error** (VUL09): VUL09, discussion of gradations of nonindependence: Study 26 'split the data into two groups: those with high IAT scores and those with low IAT scores. They then found voxels that showed a main effect between these two groups and computed a correlation within those voxels.' The Welch-t statistic is my variant of reporting the group effect in those voxels.
   Reading: Read by the earlier author as a PDF converted to text (sections on the nonindependence error, survey, Fig. 4, reliability, gradations of nonindependence). I did not re-read it; my attempt to fetch the PDF failed.

3. **Brief (exactly as in ASSIGNMENT.json)**
   * claim: Among 28 subjects (14 high-anxiety and 14 low-anxiety by interview), in the voxels of a 40-voxel amygdala region that react more strongly to threatening pictures in the high-anxiety group, the group difference in mean reactivity has a Welch t statistic of at least 3.0.
   * data keys:
  * `react` (subjects, voxels) float: response to threat minus neutral pictures, one value per subject and voxel
  * `high_anx` (subjects,) bool: True for the 14 high-anxiety subjects; subjects ordered so that groups alternate (True, False, True, False, ...)
   * sizes: 28 subjects (14 + 14), 40 voxels.

4. **Mapping.** Faulty: voxelwise Welch t between the groups over all 28 subjects; voxels higher in the high-anxiety group with one-sided p < 0.05 are kept; per-subject mean over the kept voxels; Welch t between the groups on those per-subject means must be >= 3.0 (no voxel kept -> None). This is VUL09's 'Study 26' form: split into two groups, find voxels with a main effect between them, then report the group effect in those voxels. Fixed: subjects are split by parity of their rank within each group (balanced halves of 7 + 7); each half is evaluated with voxels chosen in the other half, so every subject is evaluated once; the final Welch t over all 28 per-subject values must be >= 3.0.

5. **Pre-checks of the fixed criterion** (plain Python, `fixed.py` only; samples drawn with a generator seeded 12345; `work/precheck.py`, output in `work/precheck_round1.txt`). Revisions of the fixed criterion: 0.

   | stream | samples | holds | rate | undefined (None) |
   |---|---|---|---|---|
| plus | 200 | 101 | 0.505 | 6 |
| minus | 200 | 2 | 0.010 | 64 |
| control:permute_subjects | 200 | 2 | 0.010 | 69 |
| probe: i.i.d. N(0,1) noise | 100 | 2 | 0.020 | 22 |
| probe: zeros | 10 | 0 | 0.000 | 10 |

   Controls are the skeleton's own transforms applied to `plus` samples. The noise probe replaces every array by i.i.d. N(0,1) (bool arrays by fair coin flips: my reading of the probe, not the gate's code); the zero probe uses all-zero arrays. The criterion gave the same answer on repeated calls: True.

6. **Timing** (fixed criterion): t = 0.00082 s per call (mean of 30 plus samples), g = 3e-05 s per plus generation, S = 5 (2 worlds + 1 control + 0 premises + 0 relational pairs + 2 probes); estimate 2 x 200 x (S + 1) x (t + g) = 2.0 s (limit 900 s).

7. **Deviations from the private note, problems, skeleton requests.** The note evaluated on the odd half only (7 per group). I used the two-fold cross-validated form so that all 28 subjects enter the final test, as in the faulty criterion. Selection is one-sided p < 0.05 (the note said t > 2). Even so the fixed criterion holds in only about half of the plus samples: with a true voxel difference of 0.75 and noise sd 1 the cross-validated t reaches 3.0 in only about half of the samples. I did not change the skeleton or the threshold; this is recorded as a limit of the skeleton's effect size. Randomness: none (the criterion is deterministic). Skeleton requests: none.
