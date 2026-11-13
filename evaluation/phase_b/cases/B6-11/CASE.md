# B6-11

1. **Case**: B6-11; world id W44; class B-6; subtype (none); source assigned by the designer: MAK19.

2. **Source and documenting passage**: MAK19. MAK19, section "Inflating the units of analysis": "If the researchers combine the pre and post measures across participants, they will end up with df = 18, the critical R value is now 0.44, rendering it easier to observe a statistically significant effect." (10 participants, pre-post design, correct df = 8.)
   Reading: Read in full by the earlier author (Europe PMC full text XML PMC6785265, the cited section); I re-checked the quoted sentence against the saved extract src/mak.txt.

3. **Brief exactly as in `ASSIGNMENT.json`**:
   - id: W44
   - claim: Across participants, grip strength is positively correlated with cortical thickness in the motor cortex: the correlation between the two measures is greater than zero at the one-sided 0.05 level.
   - data keys:
  - `grip` (10, 2) axes: (participants, sessions: before and after the intervention), float: grip strength at each of the two sessions
  - `thickness` (10, 2) axes: (participants, sessions: before and after the intervention), float: motor cortex thickness measured at the same session
   - sizes: 10 participants, 2 sessions each (20 measurements in total).

4. **Mapping of the twins to the documented error**: Faulty: the Pearson correlation over all 20 pooled participant-by-session measurements (df 18), one-sided 0.05; MAK19 documents exactly this pooling (10 participants, pre and post measures combined, df = 18 instead of 8). Fixed: sessions are averaged within participant and the correlation is computed over the 10 participant means (df 8), one-sided 0.05. The two twins differ only inside the body of `criterion`; the statistical helpers (a Lanczos log-gamma, a continued-fraction regularised incomplete beta and the t-distribution p-values built on them, written in numpy because scipy is not available; checked against numerical integration of the t density, maximum relative difference 1.2e-12 over df 1 to 298, `work/test_helpers.py`) and the guards are identical in both. Guards return None only for non-finite values, too few values or a zero variance. No randomness is used; the criterion is deterministic.

5. **Pre-checks of the fixed criterion** (plain Python, `work/precheck_fixed.py`, output in `work/precheck_fixed_output.txt`; fixed twin only, 200 samples per stream unless stated): holds in plus 184/200 (undefined 0), in minus 8/200 (undefined 0); on the declared control (permute_thickness on plus applied to plus samples) 13/200; on i.i.d. N(0,1) noise of the same shapes 11/200 (undefined 0); on all-zero data (20 samples, guard) 0/20 (undefined 20). Repeatability: two calls on the same data agree. Revisions of the fixed criterion: 0 (first version kept).

6. **Timing** (fixed criterion, mean of 100 calls on plus samples; g mean of 200 plus generations): t = 0.03 ms, g = 0.01 ms, S = 5 (2 worlds + 1 control + 0 premises + 0 relational pairs + 2 probes). Estimate 2 x 200 x (S + 1) x (t + g) = 0.1 s (limit 900 s).

7. **Deviations from the private note, problems, skeleton requests**: none. The brief was revised by the earlier author to 10 participants x 2 sessions to match MAK19.
