# B6-09

1. **Case**: B6-09; world id W31; class B-6; subtype (none); source assigned by the designer: LAZ10.

2. **Source and documenting passage**: LAZ10. LAZ10, hierarchical data and Fig. 1 example: the first (incorrect) interval "uses all 20 data points and does not account for the hierarchical nature of the data"; the correct analysis uses "the mean of the ten values for each rat". The paired drug-versus-vehicle design is a paired extension of the between-group examples (flagged by the earlier author).
   Reading: Read in full by the earlier author (Europe PMC full text XML PMC2817684); I re-checked the quoted sentence against the saved extract src/laz.txt.

3. **Brief exactly as in `ASSIGNMENT.json`**:
   - id: W31
   - claim: Applying the drug to brain slices increases the mean amplitude of synaptic responses relative to vehicle: mean response amplitude is higher with the drug than with vehicle, in slices taken from the same animals, at the two-sided 0.05 level.
   - data keys:
  - `amp_drug` (8, 25) axes: (animals, recorded cells per animal), float: response amplitude of each cell recorded in drug-treated tissue
  - `amp_vehicle` (8, 25) axes: (animals, recorded cells per animal), float: response amplitude of each cell recorded in vehicle-treated tissue from the same animals
   - sizes: 8 animals, 25 cells per condition per animal (200 cells per array).

4. **Mapping of the twins to the documented error**: Faulty: a paired t-test (two-sided 0.05, drug higher) over all 200 (animal, cell index) pairs, df 199, so the cells of one animal count as independent pairs (LAZ10 Fig. 1, "uses all 20 data points"). Fixed: the mean amplitude per animal and condition, then a paired t-test across the 8 animals (df 7), the same test and level (LAZ10: "the mean of the ten values for each rat are calculated first"). The two twins differ only inside the body of `criterion`; the statistical helpers (a Lanczos log-gamma, a continued-fraction regularised incomplete beta and the t-distribution p-values built on them, written in numpy because scipy is not available; checked against numerical integration of the t density, maximum relative difference 1.2e-12 over df 1 to 298, `work/test_helpers.py`) and the guards are identical in both. Guards return None only for non-finite values, too few values or a zero variance. No randomness is used; the criterion is deterministic.

5. **Pre-checks of the fixed criterion** (plain Python, `work/precheck_fixed.py`, output in `work/precheck_fixed_output.txt`; fixed twin only, 200 samples per stream unless stated): holds in plus 149/200 (undefined 0), in minus 5/200 (undefined 0); on the declared control (swap_conditions_within_animals on plus applied to plus samples) 3/200; on i.i.d. N(0,1) noise of the same shapes 7/200 (undefined 0); on all-zero data (20 samples, guard) 0/20 (undefined 20). Repeatability: two calls on the same data agree. Revisions of the fixed criterion: 0 (first version kept).

6. **Timing** (fixed criterion, mean of 100 calls on plus samples; g mean of 200 plus generations): t = 0.03 ms, g = 0.01 ms, S = 5 (2 worlds + 1 control + 0 premises + 0 relational pairs + 2 probes). Estimate 2 x 200 x (S + 1) x (t + g) = 0.1 s (limit 900 s).

7. **Deviations from the private note, problems, skeleton requests**: none. Raw amplitudes (the claim is about mean amplitude); extension of the documented between-group setting to a paired design is flagged in the private note.
