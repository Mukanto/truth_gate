# B1-03 (W28)

1. **Case**: B1-03; world id W28; class B-1; subtype: (none); source key KRI09.

2. **Documented error** (KRI09): KRI09, Introduction (Fig. 1 text): 'In behavioral studies, an example of selection is the division of a group of subjects into subgroups based on task performance.' The same text states that selection inside the same data distorts descriptive statistics and tests.
   Reading: Read by the earlier author (phase 1) as the full text on PMC (PMC2841687, stripped HTML). I did not re-read it.

3. **Brief (exactly as in ASSIGNMENT.json)**
   * claim: In a study of 60 participants, those who perform worst at the start of a perceptual-learning task benefit most from training: the improvement (late-block score minus early-block score) of the lower-scoring half exceeds that of the higher-scoring half by at least 4 points, with an independent-samples t-test p < 0.05 (one-sided).
   * data keys:
  * `score` (participants, blocks) float: percent correct (0 to 100) in each of 4 consecutive blocks of the task, block 0 first and block 3 last
   * sizes: 60 participants, 4 blocks.

4. **Mapping.** Faulty: participants are split at the median of block 0 (lower/upper half of 30), improvement = block 3 - block 0 for each participant, independent-samples (pooled) t test one-sided (lower half larger), p < 0.05 and mean difference >= 4. This is the subgroup-by-performance selection of KRI09 Introduction: the split variable and the outcome share the same noisy block-0 measurement. Fixed: the split uses block 1, a separate early measurement, and the improvement is still block 3 - block 0 (the claim's own definition); same test, same threshold.

5. **Pre-checks of the fixed criterion** (plain Python, `fixed.py` only; samples drawn with a generator seeded 12345; `work/precheck.py`, output in `work/precheck_round1.txt`). Revisions of the fixed criterion: 0.

   | stream | samples | holds | rate | undefined (None) |
   |---|---|---|---|---|
| plus | 200 | 143 | 0.715 | 0 |
| minus | 200 | 6 | 0.030 | 0 |
| control:decouple_gain_from_start | 200 | 0 | 0.000 | 0 |
| probe: i.i.d. N(0,1) noise | 100 | 0 | 0.000 | 0 |
| probe: zeros | 10 | 0 | 0.000 | 10 |

   Controls are the skeleton's own transforms applied to `plus` samples. The noise probe replaces every array by i.i.d. N(0,1) (bool arrays by fair coin flips: my reading of the probe, not the gate's code); the zero probe uses all-zero arrays. The criterion gave the same answer on repeated calls: True.

6. **Timing** (fixed criterion): t = 3e-05 s per call (mean of 30 plus samples), g = 2e-05 s per plus generation, S = 5 (2 worlds + 1 control + 0 premises + 0 relational pairs + 2 probes); estimate 2 x 200 x (S + 1) x (t + g) = 0.1 s (limit 900 s).

7. **Deviations from the private note, problems, skeleton requests.** The note's fix kept the block-0 split and changed the outcome to block 3 - block 1. I changed the other side instead (split on block 1, outcome unchanged), because under the skeleton's learning curve (45% of learning by block 1) the note's version has a true group difference of about 3.4 points, below the claimed 4, so the fixed criterion could not hold even without noise; this was decided from the generator's stated parameters before any pre-check, not from pass rates. Both are the same device (a second, independent early measurement). Randomness: none (the criterion is deterministic). Skeleton requests: none.
