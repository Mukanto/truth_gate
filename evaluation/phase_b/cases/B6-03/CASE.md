# B6-03

1. **Case**: B6-03; world id W20; class B-6; subtype (none); source assigned by the designer: NIE11.

2. **Source and documenting passage**: NIE11. NIE11, p. 1105: "A fictive example would be 'Hippocampal firing synchrony correlated with memory performance in the placebo condition (r = 0.43, P = 0.01), but not in the drug condition (r = 0.19, P = 0.21)'." (MAK19 Fig. 1A: correlations in two groups of 20.)
   Reading: Read in full by the earlier author (author-hosted PDF, whole text); I re-checked the quoted sentence against the saved extract src/nie.txt and src/nie2.txt.

3. **Brief exactly as in `ASSIGNMENT.json`**:
   - id: W20
   - claim: The relationship between sleep duration and memory score is stronger in older adults than in younger adults: the correlation between hours of sleep and recall score is higher in the older group than in the younger group, at the one-sided 0.05 level.
   - data keys:
  - `sleep_young` (35,) axis: participants, float: average nightly sleep in hours, younger group
  - `recall_young` (35,) axis: participants (same order), float: recall score, younger group
  - `sleep_old` (35,) axis: participants, float: average nightly sleep in hours, older group
  - `recall_old` (35,) axis: participants (same order), float: recall score, older group
   - sizes: 35 participants per group (70 in total).

4. **Mapping of the twins to the documented error**: Faulty: Pearson correlation tested separately in each group (one-sided 0.05, the level in the brief); the claim holds when the correlation is significantly positive in the older group, not significant in the younger group, and larger in the older group (the NIE11 correlation example "significant in one condition but not in the other"). Fixed: Fisher z test of the difference between two independent correlations, z = (z_old - z_young)/sqrt(1/(n_old-3) + 1/(n_young-3)), one-sided 0.05 (critical z 1.6448536269514722). The two twins differ only inside the body of `criterion`; the statistical helpers (a Lanczos log-gamma, a continued-fraction regularised incomplete beta and the t-distribution p-values built on them, written in numpy because scipy is not available; checked against numerical integration of the t density, maximum relative difference 1.2e-12 over df 1 to 298, `work/test_helpers.py`) and the guards are identical in both. Guards return None only for non-finite values, too few values or a zero variance. No randomness is used; the criterion is deterministic.

5. **Pre-checks of the fixed criterion** (plain Python, `work/precheck_fixed.py`, output in `work/precheck_fixed_output.txt`; fixed twin only, 200 samples per stream unless stated): holds in plus 137/200 (undefined 0), in minus 4/200 (undefined 0); on the declared control (permute_recall_old on plus applied to plus samples) 1/200; on i.i.d. N(0,1) noise of the same shapes 9/200 (undefined 0); on all-zero data (20 samples, guard) 0/20 (undefined 20). Repeatability: two calls on the same data agree. Revisions of the fixed criterion: 0 (first version kept).

6. **Timing** (fixed criterion, mean of 100 calls on plus samples; g mean of 200 plus generations): t = 0.02 ms, g = 0.01 ms, S = 5 (2 worlds + 1 control + 0 premises + 0 relational pairs + 2 probes). Estimate 2 x 200 x (S + 1) x (t + g) = 0.1 s (limit 900 s).

7. **Deviations from the private note, problems, skeleton requests**: none.
