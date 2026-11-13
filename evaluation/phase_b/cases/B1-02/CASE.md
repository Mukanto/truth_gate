# B1-02 (W07)

1. **Case**: B1-02; world id W07; class B-1; subtype: (none); source key KRI09.

2. **Documented error** (KRI09): KRI09, Example 1 discussion: 'In single-cell recording, for example, it is common to select neurons according to some criterion (e.g. visual responsiveness or selectivity) before applying further analyses to the selected subset. If the selection is based on the same data set as used for selective analysis, biases will arise.' (orientation tuning index is my instance of 'selectivity')
   Reading: Read by the earlier author (phase 1) as the full text on PMC (PMC2841687, stripped HTML). I did not re-read it.

3. **Brief (exactly as in ASSIGNMENT.json)**
   * claim: Among 150 recorded V1 neurons, the neurons that are tuned to orientation have a mean orientation selectivity index of at least 0.25, where each neuron's index is (r_pref - r_orth) / (r_pref + r_orth), r_pref is its mean rate at its preferred orientation and r_orth its mean rate at the orientation 90 degrees away.
   * data keys:
  * `rate` (neurons, orientations, trials) float: non-negative firing rate in spikes/s of each neuron to each of 8 equally spaced grating orientations (0 to 157.5 degrees), 16 repeats of each
   * sizes: 150 neurons, 8 orientations, 16 trials.

4. **Mapping.** Faulty: per neuron a one-way ANOVA across the 8 orientations on all 16 trials (p < 0.05 = tuned), preferred orientation = argmax of the all-trial means, index (r_pref - r_orth)/(r_pref + r_orth) from the same all-trial means, criterion = mean index of the tuned neurons >= 0.25. This is the selection of neurons by a criterion on the same data that is then analysed (KRI09, Example 1 discussion). Fixed: tuned neurons and preferred orientation come from the even-numbered trials (0, 2, ...), the index from the odd-numbered trials only; same ANOVA, same p, same index, same threshold, same guard. The p < 0.05 cut-off is conventional, not stated by the source.

5. **Pre-checks of the fixed criterion** (plain Python, `fixed.py` only; samples drawn with a generator seeded 12345; `work/precheck.py`, output in `work/precheck_round1.txt`). Revisions of the fixed criterion: 1.

   | stream | samples | holds | rate | undefined (None) |
   |---|---|---|---|---|
| plus | 200 | 200 | 1.000 | 0 |
| minus | 200 | 4 | 0.020 | 0 |
| control:shuffle_across_orientations | 200 | 2 | 0.010 | 1 |
| probe: i.i.d. N(0,1) noise | 100 | 20 | 0.200 | 0 |
| probe: zeros | 10 | 0 | 0.000 | 10 |

   Controls are the skeleton's own transforms applied to `plus` samples. The noise probe replaces every array by i.i.d. N(0,1) (bool arrays by fair coin flips: my reading of the probe, not the gate's code); the zero probe uses all-zero arrays. The criterion gave the same answer on repeated calls: True.

   Revision 1: first version had an unbounded index ratio; pre-check on 100 N(0,1) noise samples: holds 37/100. Reason: with N(0,1) probe data the denominator (r_pref + r_orth) is near zero or negative and the ratio explodes. Added a clip of the index to [-1, 1] (no effect on non-negative rates); the faulty body mirrors it. Result after revision: noise 20/100 (see table). The remaining noise rate comes from the mean being taken over the few (about 7 of 150) neurons that pass the ANOVA at p < 0.05 with a bounded index; I left the guard (at least one tuned neuron) and p unchanged.

6. **Timing** (fixed criterion): t = 0.00184 s per call (mean of 30 plus samples), g = 0.00059 s per plus generation, S = 5 (2 worlds + 1 control + 0 premises + 0 relational pairs + 2 probes); estimate 2 x 200 x (S + 1) x (t + g) = 5.8 s (limit 900 s).

7. **Deviations from the private note, problems, skeleton requests.** The index is clipped to [-1, 1] (it is bounded by construction for non-negative rates, so this changes nothing on legitimate data); added after the first pre-check showed the unbounded ratio exploding on N(0,1) probe data (see revision). A zero or negative denominator gives index 0. Selection/evaluation trial halves are interleaved (0::2 and 1::2), as in the note. Randomness: none (the criterion is deterministic). Skeleton requests: none.
