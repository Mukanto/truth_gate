# B1-11 (W52)

1. **Case**: B1-11; world id W52; class B-1; subtype: (none); source key BAR05.

2. **Documented error** (BAR05): BAR05 abstract (verified): 'unusually large or small measurements tend to be followed by measurements that are closer to the mean.' The second-baseline remedy is NOT VERIFIED (full text not accessible). MAK19 'Circular analysis' also describes binning on baseline and then showing change as an artefact.
   Reading: Only the abstract was read (by the earlier author, via Europe PMC); the full text was not accessible. I did not re-read it. Everything beyond the abstract (setting, remedy) is NOT VERIFIED against the paper.

3. **Brief (exactly as in ASSIGNMENT.json)**
   * claim: Among patients with a depression score in the top fifth at the first assessment, at least 70% have a lower score after the 8-week programme than before it.
   * data keys:
  * `score` (patients, visits) float: depression questionnaire score: visit 0 = first assessment, visit 1 = second assessment just before the programme, visit 2 = after the programme
   * sizes: 120 patients, 3 visits.

4. **Mapping.** Faulty: patients in the top fifth of the first assessment (24 of 120); the proportion with a lower score after the programme than at the first assessment must be >= 0.70 (guard < 5 selected -> None). Selecting on an extreme first reading and comparing to that reading shows a fall through regression to the mean (BAR05 abstract: unusually large or small measurements tend to be followed by measurements closer to the mean). Fixed: the same patients, compared with the second assessment (a pre-programme reading not used for the selection); same proportion >= 0.70.

5. **Pre-checks of the fixed criterion** (plain Python, `fixed.py` only; samples drawn with a generator seeded 12345; `work/precheck.py`, output in `work/precheck_round1.txt`). Revisions of the fixed criterion: 0.

   | stream | samples | holds | rate | undefined (None) |
   |---|---|---|---|---|
| plus | 200 | 191 | 0.955 | 0 |
| minus | 200 | 6 | 0.030 | 0 |
| control:remove_average_programme_effect | 200 | 16 | 0.080 | 0 |
| probe: i.i.d. N(0,1) noise | 100 | 2 | 0.020 | 0 |
| probe: zeros | 10 | 0 | 0.000 | 0 |

   Controls are the skeleton's own transforms applied to `plus` samples. The noise probe replaces every array by i.i.d. N(0,1) (bool arrays by fair coin flips: my reading of the probe, not the gate's code); the zero probe uses all-zero arrays. The criterion gave the same answer on repeated calls: True.

6. **Timing** (fixed criterion): t = 1e-05 s per call (mean of 30 plus samples), g = 2e-05 s per plus generation, S = 5 (2 worlds + 1 control + 0 premises + 0 relational pairs + 2 probes); estimate 2 x 200 x (S + 1) x (t + g) = 0.1 s (limit 900 s).

7. **Deviations from the private note, problems, skeleton requests.** None. The second-baseline remedy is not verified against the BAR05 full text (abstract only). Randomness: none (the criterion is deterministic). Skeleton requests: none.
