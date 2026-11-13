# B1-12 (W12)

1. **Case**: B1-12; world id W12; class B-1; subtype: (none); source key BAR05.

2. **Documented error** (BAR05): BAR05 abstract (verified): same sentence as B1-10 about a follow-up on a sub-sample selected using a baseline value. The education / test-score setting is NOT VERIFIED (full text not accessible).
   Reading: Only the abstract was read (by the earlier author, via Europe PMC); the full text was not accessible. I did not re-read it. Everything beyond the abstract (setting, remedy) is NOT VERIFIED against the paper.

3. **Brief (exactly as in ASSIGNMENT.json)**
   * claim: Students in the lowest fifth of the autumn test gain at least 5 points on the spring test after the tutoring programme: the claim holds when the mean gain of those students is at least 5 and one-sided one-sample t-test p < 0.05.
   * data keys:
  * `score` (students, tests) float: test scores out of 100: test 0 = autumn, test 1 = a second test given just before the tutoring began, test 2 = spring
   * sizes: 250 students, 3 tests.

4. **Mapping.** Faulty: students in the lowest fifth of the autumn test (50 of 250); the mean of (spring - autumn) must be >= 5 with one-sided one-sample t p < 0.05 (guard < 5 students -> None). Selecting on a low first score and measuring the gain from that score builds in regression to the mean (BAR05 abstract). Fixed: same students; gain = spring - the second pre-tutoring test; same test and thresholds.

5. **Pre-checks of the fixed criterion** (plain Python, `fixed.py` only; samples drawn with a generator seeded 12345; `work/precheck.py`, output in `work/precheck_round1.txt`). Revisions of the fixed criterion: 0.

   | stream | samples | holds | rate | undefined (None) |
   |---|---|---|---|---|
| plus | 200 | 178 | 0.890 | 0 |
| minus | 200 | 0 | 0.000 | 0 |
| control:remove_average_tutoring_gain | 200 | 0 | 0.000 | 0 |
| probe: i.i.d. N(0,1) noise | 100 | 0 | 0.000 | 0 |
| probe: zeros | 10 | 0 | 0.000 | 10 |

   Controls are the skeleton's own transforms applied to `plus` samples. The noise probe replaces every array by i.i.d. N(0,1) (bool arrays by fair coin flips: my reading of the probe, not the gate's code); the zero probe uses all-zero arrays. The criterion gave the same answer on repeated calls: True.

6. **Timing** (fixed criterion): t = 3e-05 s per call (mean of 30 plus samples), g = 3e-05 s per plus generation, S = 5 (2 worlds + 1 control + 0 premises + 0 relational pairs + 2 probes); estimate 2 x 200 x (S + 1) x (t + g) = 0.1 s (limit 900 s).

7. **Deviations from the private note, problems, skeleton requests.** None. The setting and the second-baseline remedy are not verified against the BAR05 full text (abstract only). Randomness: none (the criterion is deterministic). Skeleton requests: none.
