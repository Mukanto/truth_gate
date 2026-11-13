# B1-08 (W21)

1. **Case**: B1-08; world id W21; class B-1; subtype: (none); source key MAK19.

2. **Documented error** (MAK19): MAK19, 'Circular analysis': 'circular analysis recruits the noise (inherent to any empirical data) to inflate the statistical outcome'; its worked example is a neuronal population measured before and after a manipulation. KRI09 describes selecting neurons by visual responsiveness. The calcium-imaging responders with a tone are my instance.
   Reading: Read by the earlier author as the Europe PMC full-text XML (PMC6785265), section 'Circular analysis'. I did not re-read it.

3. **Brief (exactly as in ASSIGNMENT.json)**
   * claim: Of the 120 cells in a calcium-imaging field of view, those that respond to the tone are mostly genuine responders: at least 70% of them show a larger mean fluorescence after tone onset than before it.
   * data keys:
  * `pre` (cells, trials) float: mean fluorescence (dF/F) in the 1 s before tone onset, per cell and trial
  * `post` (cells, trials) float: mean fluorescence (dF/F) in the 1 s after tone onset, per cell and trial
   * sizes: 120 cells, 30 trials.

4. **Mapping.** Faulty: per cell a one-sided paired t test (post > pre) over all 30 trials (p < 0.05) defines the responders; the criterion is the proportion of responders whose mean (post - pre) over the same 30 trials is positive, >= 0.70 (guard: fewer than 5 responders -> None). By construction this proportion is 1: the 'recruiting the noise to inflate the statistical outcome' of MAK19 'Circular analysis'. Fixed: responders from trials 0-14, proportion with positive mean (post - pre) on trials 15-29 only; same test, same p, same >= 0.70, same guard.

5. **Pre-checks of the fixed criterion** (plain Python, `fixed.py` only; samples drawn with a generator seeded 12345; `work/precheck.py`, output in `work/precheck_round1.txt`). Revisions of the fixed criterion: 0.

   | stream | samples | holds | rate | undefined (None) |
   |---|---|---|---|---|
| plus | 200 | 200 | 1.000 | 0 |
| minus | 200 | 21 | 0.105 | 70 |
| control:swap_pre_post | 200 | 23 | 0.115 | 54 |
| probe: i.i.d. N(0,1) noise | 100 | 7 | 0.070 | 31 |
| probe: zeros | 10 | 0 | 0.000 | 10 |

   Controls are the skeleton's own transforms applied to `plus` samples. The noise probe replaces every array by i.i.d. N(0,1) (bool arrays by fair coin flips: my reading of the probe, not the gate's code); the zero probe uses all-zero arrays. The criterion gave the same answer on repeated calls: True.

6. **Timing** (fixed criterion): t = 0.00058 s per call (mean of 30 plus samples), g = 0.0001 s per plus generation, S = 5 (2 worlds + 1 control + 0 premises + 0 relational pairs + 2 probes); estimate 2 x 200 x (S + 1) x (t + g) = 1.6 s (limit 900 s).

7. **Deviations from the private note, problems, skeleton requests.** None from the note. Known property: with the guard at 5 responders and a 70% threshold, the fixed criterion holds in about 10% of minus samples (and of the control) and is undefined in about a third, because the few false responders that pass the screen have a held-out positive mean about half the time; I kept the note's guard rather than tune it. Randomness: none (the criterion is deterministic). Skeleton requests: none.
