# B1-05 (W34)

1. **Case**: B1-05; world id W34; class B-1; subtype: (none); source key VUL09.

2. **Documented error** (VUL09): VUL09, survey section: 53% of respondents said 'regression across subjects' was the functional constraint used to select voxels; the reliability discussion mentions two scanning sessions (Manoach et al. 2001). Using a second session as the independent measure is my construction, not stated in VUL09.
   Reading: Read by the earlier author as a PDF converted to text (sections on the nonindependence error, survey, Fig. 4, reliability, gradations of nonindependence). I did not re-read it; my attempt to fetch the PDF failed.

3. **Brief (exactly as in ASSIGNMENT.json)**
   * claim: In a 50-voxel region of medial prefrontal cortex, the voxels that track trait social anxiety have a mean activity that predicts the trait: the least-squares slope of the standardized trait score on the standardized mean activity of those voxels across the 16 subjects is at least 0.50, with one-sided p < 0.05.
   * data keys:
  * `act` (subjects, sessions, voxels) float: activation (beta) to a social-evaluation task; two scanning sessions on separate days
  * `trait` (subjects,) float: questionnaire social-anxiety score per subject
   * sizes: 16 subjects, 2 sessions, 50 voxels.

4. **Mapping.** Faulty: the two sessions are averaged; voxelwise correlation with the trait over the 16 subjects; voxels with r > 0 and two-sided p < 0.01 are kept; their mean activity (same averaged data) is regressed: least-squares slope of z(trait) on z(mean activity) >= 0.50 with one-sided p < 0.05. This is selecting voxels by regression across subjects and reporting the regression on the same data (VUL09: regression across subjects was the most common selection constraint). Fixed: voxels from session 0 only, mean activity of those voxels from session 1 only; same slope, same test, same thresholds. The use of the second session as the independent measure is the earlier author's construction (not stated in VUL09).

5. **Pre-checks of the fixed criterion** (plain Python, `fixed.py` only; generator seeded 12345; `work/precheck.py`; outputs `work/precheck_round1.txt` before the repair and `work/precheck_repair.txt` after it). Revisions of the fixed criterion: 1 (the audit repair, selection level p < 0.01; it mirrors the faulty twin).

   Before the repair (p < 0.05): plus 0.98, minus 0.06 (None 100/200), control 0.11 (None 111), noise 0.02 (None 30/100).

   After the repair (final), 200 samples per world and control, 100 noise, 10 zeros:

   | stream | samples | holds | rate | undefined (None) |
   |---|---|---|---|---|
| plus | 200 | 185 | 0.925 | 5 |
| minus | 200 | 6 | 0.030 | 169 |
| control:permute_trait | 200 | 10 | 0.050 | 170 |
| probe: i.i.d. N(0,1) noise | 100 | 0 | 0.000 | 75 |
| probe: zeros | 10 | 0 | 0.000 | 10 |

   Controls are the skeleton's own transforms applied to `plus` samples. The noise probe replaces every array by i.i.d. N(0,1) (my reading of the probe, not the gate's code); the zero probe uses all-zero arrays. The criterion gave the same answer on repeated calls: True.

6. **Timing** (fixed criterion, after the repair): t = 0.00074 s per call (mean of 30 plus samples), g = 4e-05 s per plus generation, S = 5 (2 worlds + 1 control + 0 premises + 0 relational pairs + 2 probes); estimate 2 x 200 x (S + 1) x (t + g) = 1.9 s (limit 900 s).

7. **Deviations from the private note, problems, skeleton requests.** Audit repair (PREREG 5.3, item (a)): the first version used p < 0.05 two-sided with r > 0 instead of the note's p < 0.01, for a reason about the noise probe (an empty selection in most noise samples). That is not a reason item (a) accepts: VUL09 Fig. 4 caption documents 'a positive correlation with p < .01' and the note says r > 0 and p < 0.01. Both twins now use r > 0 and two-sided p < 0.01 (critical value `_tq(0.005, n - 2)`); neither source nor note states the sidedness, so I kept my original two-sided reading and changed only the level. Nothing else changed. An empty selection returns None (allowed guard), which is now the usual outcome in minus and in the control (see table). The skeleton's stable subject-by-voxel component still carries session-0 selection into session 1; reported, not changed. Randomness: none (the criterion is deterministic). Skeleton requests: none.
