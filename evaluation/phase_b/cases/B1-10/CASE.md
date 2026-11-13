# B1-10 (W22)

1. **Case**: B1-10; world id W22; class B-1; subtype: (none); source key BAR05.

2. **Documented error** (BAR05): BAR05 abstract (verified): 'The effect of RTM in a sample becomes more noticeable with increasing measurement error and when follow-up measurements are only examined on a sub-sample selected using a baseline value.' Remedy per abstract: 'better study design and use of suitable statistical methods'. Full text not accessible: the blood-pressure setting and the placebo-arm remedy are NOT VERIFIED against the full text.
   Reading: Only the abstract was read (by the earlier author, via Europe PMC); the full text was not accessible. I did not re-read it. Everything beyond the abstract (setting, remedy) is NOT VERIFIED against the paper.

3. **Brief (exactly as in ASSIGNMENT.json)**
   * claim: In patients whose systolic blood pressure is at least 150 mmHg at entry, the drug lowers systolic pressure by at least 5 mmHg over 12 weeks. The claim holds when the estimated lowering is at least 5 mmHg and one-sided p < 0.05.
   * data keys:
  * `sbp` (patients, visits) float: systolic pressure in mmHg at entry (visit 0) and after 12 weeks (visit 1)
  * `drug` (patients,) bool: True for patients given the drug, False for patients given placebo
   * sizes: 160 patients (about 80 per arm), 2 visits.

4. **Mapping.** Faulty: among drug-arm patients whose entry pressure is >= 150 mmHg, the paired change (entry - follow-up) has mean >= 5 and one-sided paired t p < 0.05; the placebo arm is not used. Patients are selected on the entry reading, which carries a measurement error that the follow-up reading does not share, so a fall is expected without any drug (BAR05 abstract: the effect of regression to the mean is larger when follow-up is examined on a sub-sample selected using a baseline value). Fixed: the same patients (entry >= 150) in both arms; the drug-minus-placebo difference in mean change must be >= 5 with one-sided Welch t p < 0.05 (the control arm absorbs the regression to the mean).

5. **Pre-checks of the fixed criterion** (plain Python, `fixed.py` only; samples drawn with a generator seeded 12345; `work/precheck.py`, output in `work/precheck_round1.txt`). Revisions of the fixed criterion: 0.

   | stream | samples | holds | rate | undefined (None) |
   |---|---|---|---|---|
| plus | 200 | 185 | 0.925 | 0 |
| minus | 200 | 6 | 0.030 | 0 |
| control:permute_drug_labels | 200 | 9 | 0.045 | 0 |
| probe: i.i.d. N(0,1) noise | 100 | 0 | 0.000 | 100 |
| probe: zeros | 10 | 0 | 0.000 | 10 |

   Controls are the skeleton's own transforms applied to `plus` samples. The noise probe replaces every array by i.i.d. N(0,1) (bool arrays by fair coin flips: my reading of the probe, not the gate's code); the zero probe uses all-zero arrays. The criterion gave the same answer on repeated calls: True.

6. **Timing** (fixed criterion): t = 7e-05 s per call (mean of 30 plus samples), g = 2e-05 s per plus generation, S = 5 (2 worlds + 1 control + 0 premises + 0 relational pairs + 2 probes); estimate 2 x 200 x (S + 1) x (t + g) = 0.2 s (limit 900 s).

7. **Deviations from the private note, problems, skeleton requests.** As in the note. The test changes from paired t to Welch t because the correction adds a comparison arm; threshold 5 mmHg and p < 0.05 are the claim's. The remedy (control arm) is not verified against the BAR05 full text (abstract only). Randomness: none (the criterion is deterministic). Skeleton requests: none.
