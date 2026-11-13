# B1-09 (W41)

1. **Case**: B1-09; world id W41; class B-1; subtype: (none); source key MAK19.

2. **Documented error** (MAK19): MAK19, section 'Circular analysis': 'They therefore split the population to sub-groups, by binning the data based on the activity levels observed at baseline. This leads to a significant interaction effect - those neurons that initially produced low responses show response increases ... could therefore be observed in pure noise.'
   Reading: Read by the earlier author as the Europe PMC full-text XML (PMC6785265), section 'Circular analysis'. I did not re-read it.

3. **Brief (exactly as in ASSIGNMENT.json)**
   * claim: In a recording of 200 cortical neurons, the neurons that fire least at baseline show an increase in firing rate after the manipulation of at least 2 spikes/s on average. The claim holds when a one-sample t-test of the per-neuron increase against zero, over the low-baseline neurons, is significant at p < 0.05 (one-sided) and the mean increase is at least 2.
   * data keys:
  * `base` (neurons, epochs) float: mean firing rate in spikes/s in two separate pre-manipulation epochs of equal length
  * `post` (neurons,) float: mean firing rate in spikes/s in the epoch after the manipulation
   * sizes: 200 neurons, 2 baseline epochs.

4. **Mapping.** Faulty: baseline = mean of the two baseline epochs; the lowest third of the neurons by that baseline (66 of 200); increase = post - the same baseline; one-sided one-sample t test p < 0.05 and mean increase >= 2 spikes/s. This is MAK19's worked example: the population is binned by baseline activity and the change from that same baseline is then tested ('could therefore be observed in pure noise'). Fixed: the lowest third is chosen by baseline epoch 0 and the increase is post - baseline epoch 1; same t test, same threshold.

5. **Pre-checks of the fixed criterion** (plain Python, `fixed.py` only; samples drawn with a generator seeded 12345; `work/precheck.py`, output in `work/precheck_round1.txt`). Revisions of the fixed criterion: 0.

   | stream | samples | holds | rate | undefined (None) |
   |---|---|---|---|---|
| plus | 200 | 181 | 0.905 | 0 |
| minus | 200 | 1 | 0.005 | 0 |
| control:no_manipulation_effect | 200 | 0 | 0.000 | 0 |
| probe: i.i.d. N(0,1) noise | 100 | 0 | 0.000 | 0 |
| probe: zeros | 10 | 0 | 0.000 | 10 |

   Controls are the skeleton's own transforms applied to `plus` samples. The noise probe replaces every array by i.i.d. N(0,1) (bool arrays by fair coin flips: my reading of the probe, not the gate's code); the zero probe uses all-zero arrays. The criterion gave the same answer on repeated calls: True.

6. **Timing** (fixed criterion): t = 3e-05 s per call (mean of 30 plus samples), g = 0.00013 s per plus generation, S = 5 (2 worlds + 1 control + 0 premises + 0 relational pairs + 2 probes); estimate 2 x 200 x (S + 1) x (t + g) = 0.4 s (limit 900 s).

7. **Deviations from the private note, problems, skeleton requests.** Ties in the baseline are broken by a stable sort (neuron order), which gives exactly 66 neurons in both files. Randomness: none (the criterion is deterministic). Skeleton requests: none.
