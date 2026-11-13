# B6-12

1. **Case**: B6-12; world id W10; class B-6; subtype (none); source assigned by the designer: MAK19.

2. **Source and documenting passage**: MAK19. MAK19, section "Interpreting comparisons between two effects without directly comparing them": "A similar issue occurs when estimating the effect of an intervention measured in two different groups: the intervention could yield a significant effect in one group but not in the other." (Fig. 1B, n = 20 per group; the 3-session per-participant slope and 14 per group are a small extension flagged by the earlier author.)
   Reading: Read in full by the earlier author (Europe PMC full text XML PMC6785265, the cited section); I re-checked the quoted sentence against the saved extract src/mak.txt.

3. **Brief exactly as in `ASSIGNMENT.json`**:
   - id: W10
   - claim: Over three practice sessions the trained group improves faster than the control group: the average per-session change in performance is larger in the trained group than in the control group, at the two-sided 0.05 level.
   - data keys:
  - `perf_trained` (14, 3) axes: (participants, sessions in time order), float: performance score of each trained participant at each session
  - `perf_control` (14, 3) axes: (participants, sessions in time order), float: performance score of each control participant at each session
   - sizes: 14 participants per group, 3 sessions each (84 values in total).

4. **Mapping of the twins to the documented error**: Faulty: a least-squares slope across the 3 sessions is computed for each participant, then one one-sample t-test per group (two-sided 0.05); the claim holds when the trained slopes are significantly positive, the control slopes are not significant, and the trained mean slope is larger (MAK19, "a significant effect in one group but not in the other"). Fixed: a Welch two-sample t-test of the per-participant slopes of the two groups (two-sided 0.05, trained larger), the direct group comparison. The two twins differ only inside the body of `criterion`; the statistical helpers (a Lanczos log-gamma, a continued-fraction regularised incomplete beta and the t-distribution p-values built on them, written in numpy because scipy is not available; checked against numerical integration of the t density, maximum relative difference 1.2e-12 over df 1 to 298, `work/test_helpers.py`) and the guards are identical in both. Guards return None only for non-finite values, too few values or a zero variance. No randomness is used; the criterion is deterministic.

5. **Pre-checks of the fixed criterion** (plain Python, `work/precheck_fixed.py`, output in `work/precheck_fixed_output.txt`; fixed twin only, 200 samples per stream unless stated): holds in plus 161/200 (undefined 0), in minus 6/200 (undefined 0); on the declared control (reshuffle_groups on plus applied to plus samples) 2/200; on i.i.d. N(0,1) noise of the same shapes 5/200 (undefined 0); on all-zero data (20 samples, guard) 0/20 (undefined 20). Repeatability: two calls on the same data agree. Revisions of the fixed criterion: 0 (first version kept).

6. **Timing** (fixed criterion, mean of 100 calls on plus samples; g mean of 200 plus generations): t = 0.06 ms, g = 0.02 ms, S = 5 (2 worlds + 1 control + 0 premises + 0 relational pairs + 2 probes). Estimate 2 x 200 x (S + 1) x (t + g) = 0.2 s (limit 900 s).

7. **Deviations from the private note, problems, skeleton requests**: Per-participant slope is the ordinary least-squares slope over the three sessions (time index 0, 1, 2); the private note did not specify the estimator.
