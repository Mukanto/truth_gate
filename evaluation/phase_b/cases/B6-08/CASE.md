# B6-08

1. **Case**: B6-08; world id W50; class B-6; subtype (none); source assigned by the designer: LAZ10.

2. **Source and documenting passage**: LAZ10. LAZ10 abstract: "Pseudoreplication occurs when observations are not statistically independent, but treated as if they are." Also MAK19, "Inflating the units of analysis" (pooled measures across participants). The pooled trial-level correlation is an extension of the documented setting (flagged by the earlier author).
   Reading: Read in full by the earlier author (Europe PMC full text XML PMC2817684); I re-checked the quoted sentence against the saved extract src/laz.txt.

3. **Brief exactly as in `ASSIGNMENT.json`**:
   - id: W50
   - claim: Trial-by-trial neural activity in a frontal region is positively related to reaction time: the correlation between activity and reaction time is greater than zero at the one-sided 0.05 level.
   - data keys:
  - `reaction_time` (12, 25) axes: (participants, trials), float: reaction time on each trial, trials in time order within a participant
  - `activity` (12, 25) axes: (participants, trials), float: frontal activity estimate on the same trial
   - sizes: 12 participants, 25 trials each (300 trials in total).

4. **Mapping of the twins to the documented error**: Faulty: the Pearson correlation of all 300 trials of the 12 participants pooled (df 298), one-sided 0.05; repeated observations of the same participants are counted as independent (LAZ10 abstract, "multiple observations on the same subjects"; MAK19 pooled correlation). Fixed: one Pearson correlation per participant (25 trials), Fisher z transform, one-sample t-test of the 12 z values against zero (df 11), one-sided 0.05, the participant being the unit. The two twins differ only inside the body of `criterion`; the statistical helpers (a Lanczos log-gamma, a continued-fraction regularised incomplete beta and the t-distribution p-values built on them, written in numpy because scipy is not available; checked against numerical integration of the t density, maximum relative difference 1.2e-12 over df 1 to 298, `work/test_helpers.py`) and the guards are identical in both. Guards return None only for non-finite values, too few values or a zero variance. No randomness is used; the criterion is deterministic.

5. **Pre-checks of the fixed criterion** (plain Python, `work/precheck_fixed.py`, output in `work/precheck_fixed_output.txt`; fixed twin only, 200 samples per stream unless stated): holds in plus 197/200 (undefined 0), in minus 54/200 (undefined 0); on the declared control (permute_trials_within_participant on plus applied to plus samples) 11/200; on i.i.d. N(0,1) noise of the same shapes 8/200 (undefined 0); on all-zero data (20 samples, guard) 0/20 (undefined 20). Repeatability: two calls on the same data agree. Revisions of the fixed criterion: 0 (first version kept).

6. **Timing** (fixed criterion, mean of 100 calls on plus samples; g mean of 200 plus generations): t = 0.18 ms, g = 0.02 ms, S = 5 (2 worlds + 1 control + 0 premises + 0 relational pairs + 2 probes). Estimate 2 x 200 x (S + 1) x (t + g) = 0.5 s (limit 900 s).

7. **Deviations from the private note, problems, skeleton requests**: No skeleton request, but a problem for the clean pass is recorded: the fixed criterion holds in 27% of minus samples (54/200). I diagnosed this with a plain-Python check of the world function (work/diag_b608.py): the skeleton's minus world keeps a shared linear trial drift in both measures (the world author's "fatigue drift"), which gives a real within-participant correlation of about 0.065 (mean of the 12 within-participant correlations over 400 minus samples; 0.002 once the known drift terms are subtracted). The documented correction (analyse at the participant level) detects it legitimately; I did not detrend, because detrending is not part of the documented correction and would change the criterion. The fixed criterion is therefore expected to hold often in minus and may be flagged (K2_NO_SEPARATION or HIGH_RATE on minus-related streams); this is a skeleton property, not a criterion error.
