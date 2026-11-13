# B1-04 (W19)

1. **Case**: B1-04; world id W19; class B-1; subtype: (none); source key VUL09.

2. **Documented error** (VUL09): VUL09, 'The Nonindependence Error': 'This approach amounts to selecting one or more voxels based on a functional analysis and then reporting the results of the same analysis and functional data from just the selected voxels.' Fig. 4 simulates 10 subjects and 10,000 voxels of pure noise.
   Reading: Read by the earlier author as a PDF converted to text (sections on the nonindependence error, survey, Fig. 4, reliability, gradations of nonindependence). I did not re-read it; my attempt to fetch the PDF failed.

3. **Brief (exactly as in ASSIGNMENT.json)**
   * claim: In a 60-voxel region of anterior insula, the voxels whose activity relates positively to trait empathy show a mean Pearson correlation of at least 0.50 with the trait score across the 24 subjects.
   * data keys:
  * `act` (subjects, voxels) float: activation (beta) to a pain-observation contrast, one value per subject and voxel
  * `trait` (subjects,) float: questionnaire empathy score per subject
   * sizes: 24 subjects, 60 voxels.

4. **Mapping.** Faulty: voxelwise Pearson correlation with the trait over all 24 subjects; voxels with r > 0 and two-sided p < 0.01 are kept; the mean r of the kept voxels, computed from the same correlations, must be >= 0.50 (guard: no voxel kept -> None). This is the selection of voxels by their correlation with a measure and the report of the correlation of those voxels from the same data (VUL09, 'The Nonindependence Error'). Fixed: subjects are split into even and odd positions; voxels are chosen in one half and their correlation is taken in the other half, in both directions, the two means averaged; same selection rule, same >= 0.50.

5. **Pre-checks of the fixed criterion** (plain Python, `fixed.py` only; generator seeded 12345; `work/precheck.py`; outputs `work/precheck_round1.txt` before the repair and `work/precheck_repair.txt` after it). Revisions of the fixed criterion: 1 (the audit repair, selection level p < 0.01; it mirrors the faulty twin).

   Before the repair (p < 0.05): plus 0.845, minus 0.015 (None 39/200), control 0.00 (None 53), noise 0.03 (None 2/100).

   After the repair (final), 200 samples per world and control, 100 noise, 10 zeros:

   | stream | samples | holds | rate | undefined (None) |
   |---|---|---|---|---|
| plus | 200 | 168 | 0.840 | 0 |
| minus | 200 | 2 | 0.010 | 128 |
| control:permute_trait | 200 | 0 | 0.000 | 128 |
| probe: i.i.d. N(0,1) noise | 100 | 0 | 0.000 | 49 |
| probe: zeros | 10 | 0 | 0.000 | 10 |

   Controls are the skeleton's own transforms applied to `plus` samples. The noise probe replaces every array by i.i.d. N(0,1) (my reading of the probe, not the gate's code); the zero probe uses all-zero arrays. The criterion gave the same answer on repeated calls: True.

6. **Timing** (fixed criterion, after the repair): t = 0.00136 s per call (mean of 30 plus samples), g = 3e-05 s per plus generation, S = 5 (2 worlds + 1 control + 0 premises + 0 relational pairs + 2 probes); estimate 2 x 200 x (S + 1) x (t + g) = 3.3 s (limit 900 s).

7. **Deviations from the private note, problems, skeleton requests.** Audit repair (PREREG 5.3, item (a)): the first version selected voxels with r > 0 and two-sided p < 0.05 (my choice among the note's options). VUL09 Fig. 4 caption documents the selection as 'a positive correlation with p < .01', and the private note says r > 0 and p < 0.01. Both twins now use r > 0 and two-sided p < 0.01 (critical value `_tq(0.005, df)`); neither the source nor the note states the sidedness, so I kept my original two-sided reading and changed only the level. Nothing else changed. An empty selection still returns None (allowed guard); with the stricter level this is now much more frequent in minus (see table). The earlier deviation (single direction in the note, two directions here) stands. The exact threshold of the Fig. 4 simulation was read from the source text by the coordinator/auditor, not by me. Randomness: none (the criterion is deterministic). Skeleton requests: none.
