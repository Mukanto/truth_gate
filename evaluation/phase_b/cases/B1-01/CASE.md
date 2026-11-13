# B1-01 (W05)

1. **Case**: B1-01; world id W05; class B-1; subtype: (none); source key KRI09.

2. **Documented error** (KRI09): KRI09, Introduction: 'In neuroimaging, an example of selection is the definition of a region of interest (ROI) by means of a statistical mapping that highlights voxels more strongly active during one condition than another.' Also: double dipping 'will give distorted descriptive statistics and invalid statistical inference'; independent data or a split-data analysis is the remedy (Fig. 4 policy). Example 2 simulates 30x30x20 voxels, 200 time points, four conditions.
   Reading: Read by the earlier author (phase 1) as the full text on PMC (PMC2841687, stripped HTML). I did not re-read it.

3. **Brief (exactly as in ASSIGNMENT.json)**
   * claim: In a 60-voxel region of ventral visual cortex, the voxels that respond more to faces than to houses show a mean face-minus-house response of at least 0.30 percent signal change. The claim holds when this mean (taken per subject and then averaged over the 20 subjects) is at least 0.30 and significantly above zero (one-sided one-sample t-test across subjects, p < 0.05).
   * data keys:
  * `face` (subjects, runs, voxels) float: percent signal change to face pictures, two scanning runs per subject
  * `house` (subjects, runs, voxels) float: percent signal change to house pictures, same layout as face
   * sizes: 20 subjects, 2 runs, 60 voxels.

4. **Mapping.** Faulty: for every subject the voxel map is the mean over both runs of (face - house); voxels above 1.645 times the root-mean-square of that map (one-sided p < 0.05, uncorrected, positive voxels only) are kept, and the per-subject mean face-minus-house contrast of the SAME kept voxels is computed from the same two runs, then tested across the 20 subjects (mean >= 0.30 and one-sided one-sample t, p < 0.05). This is the double-dipping form in KRI09 (region defined by a statistical map that highlights stronger activity for one condition, then descriptive statistics and inference on the same data). Fixed: voxels are chosen from one run and the contrast is read from the other run, in both directions (run 0 -> run 1 and run 1 -> run 0, per-subject values averaged); same map statistic, same z cut-off, same per-subject mean, same mean >= 0.30 and t test. The z cut-off (p < 0.05 uncorrected) is the conventional value; the source does not give one.

5. **Pre-checks of the fixed criterion** (plain Python, `fixed.py` only; samples drawn with a generator seeded 12345; `work/precheck.py`, output in `work/precheck_round1.txt`). Revisions of the fixed criterion: 0.

   | stream | samples | holds | rate | undefined (None) |
   |---|---|---|---|---|
| plus | 200 | 174 | 0.870 | 0 |
| minus | 200 | 0 | 0.000 | 0 |
| control:scramble_voxels_in_run_2 | 200 | 2 | 0.010 | 0 |
| probe: i.i.d. N(0,1) noise | 100 | 3 | 0.030 | 0 |
| probe: zeros | 10 | 0 | 0.000 | 10 |

   Controls are the skeleton's own transforms applied to `plus` samples. The noise probe replaces every array by i.i.d. N(0,1) (bool arrays by fair coin flips: my reading of the probe, not the gate's code); the zero probe uses all-zero arrays. The criterion gave the same answer on repeated calls: True.

6. **Timing** (fixed criterion): t = 7e-05 s per call (mean of 30 plus samples), g = 9e-05 s per plus generation, S = 5 (2 worlds + 1 control + 0 premises + 0 relational pairs + 2 probes); estimate 2 x 200 x (S + 1) x (t + g) = 0.4 s (limit 900 s).

7. **Deviations from the private note, problems, skeleton requests.** The private note had a voxelwise t over subjects and runs (shared voxel positions). The skeleton generates voxels per subject (no correspondence across subjects) and has only two runs, so the selection is per subject on the run-level contrast with a z cut-off, not a t test. The note's fix evaluated run 1 only; I used both directions (standard two-fold split-data) to keep power. Subjects with no kept voxel drop out; fewer than 5 subjects with a kept voxel returns None. Randomness: none (the criterion is deterministic). Skeleton requests: none.
