# B6-10

1. **Case**: B6-10; world id W13; class B-6; subtype (none); source assigned by the designer: MAK19.

2. **Source and documenting passage**: MAK19. MAK19 (Makin and Orban de Xivry 2019, eLife 8:e48175), section "Interpreting comparisons between two effects without directly comparing them": "Researchers often base their conclusions regarding the impact of an intervention (such as a pre- vs. post-intervention difference or a correlation between two variables) by noting that the intervention yields a significant effect in the experimental condition or group, whereas the corresponding effect in the control condition or group is not significant." (regression slopes of the same participants in two conditions: extension flagged by the earlier author.)
   Reading: Read in full by the earlier author (Europe PMC full text XML PMC6785265, the cited section); I re-checked the quoted sentence against the saved extract src/mak.txt.

3. **Brief exactly as in `ASSIGNMENT.json`**:
   - id: W13
   - claim: Reaction time depends more strongly on stimulus contrast in the attended condition than in the unattended condition: the regression slope of reaction time on contrast is steeper in the attended condition than in the unattended condition across 30 participants, at the two-sided 0.05 level.
   - data keys:
  - `contrast` (30,) axis: participants, float: stimulus contrast level shown to each participant
  - `rt_attended` (30,) axis: participants (same order), float: mean reaction time in the attended condition
  - `rt_unattended` (30,) axis: participants (same order), float: mean reaction time in the unattended condition, same participants
   - sizes: 30 participants, each measured in both conditions.

4. **Mapping of the twins to the documented error**: Faulty: the least-squares slope of reaction time on contrast is tested separately in each condition (two-sided 0.05); the claim holds when the attended slope is significantly negative (reaction time falls with contrast; "steeper" = more negative), the unattended slope is not significant, and the attended slope is the steeper (MAK19 "significant effect in the experimental condition, not in the control condition", applied to a regression slope). Fixed: the slope of the per-participant difference rt_attended - rt_unattended on contrast, two-sided 0.05, negative (the slope-difference test). The two twins differ only inside the body of `criterion`; the statistical helpers (a Lanczos log-gamma, a continued-fraction regularised incomplete beta and the t-distribution p-values built on them, written in numpy because scipy is not available; checked against numerical integration of the t density, maximum relative difference 1.2e-12 over df 1 to 298, `work/test_helpers.py`) and the guards are identical in both. Guards return None only for non-finite values, too few values or a zero variance. No randomness is used; the criterion is deterministic.

5. **Pre-checks of the fixed criterion** (plain Python, `work/precheck_fixed.py`, output in `work/precheck_fixed_output.txt`; fixed twin only, 200 samples per stream unless stated): holds in plus 163/200 (undefined 0), in minus 8/200 (undefined 0); on the declared control (permute_contrast on plus applied to plus samples) 7/200; on i.i.d. N(0,1) noise of the same shapes 4/200 (undefined 0); on all-zero data (20 samples, guard) 0/20 (undefined 20). Repeatability: two calls on the same data agree. Revisions of the fixed criterion: 0 (first version kept).

6. **Timing** (fixed criterion, mean of 100 calls on plus samples; g mean of 200 plus generations): t = 0.03 ms, g = 0.01 ms, S = 5 (2 worlds + 1 control + 0 premises + 0 relational pairs + 2 probes). Estimate 2 x 200 x (S + 1) x (t + g) = 0.1 s (limit 900 s).

7. **Deviations from the private note, problems, skeleton requests**: Sign convention for "steeper" (more negative slope, reaction time falling with contrast) follows the private note; the brief does not state the sign.
