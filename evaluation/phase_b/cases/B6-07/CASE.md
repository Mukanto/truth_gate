# B6-07

1. **Case**: B6-07; world id W42; class B-6; subtype (none); source assigned by the designer: LAZ10.

2. **Source and documenting passage**: LAZ10. LAZ10 (Lazic 2010, BMC Neurosci 11:5), section on hierarchical data: "Consider an experiment with two experimental conditions (treatment vs. control), with one rat in each condition. The outcome variable is the number of synapses on cells in the CA3 region of the hippocampus, and 100 cells are examined in each rat." (cells within animals; the animal is the unit of replication. Type I error rate rises with the intraclass correlation, e.g. alpha 0.37 at n = 10 per group, IC = 0.30.)
   Reading: Read in full by the earlier author (Europe PMC full text XML PMC2817684); I re-checked the quoted sentence against the saved extract src/laz.txt.

3. **Brief exactly as in `ASSIGNMENT.json`**:
   - id: W42
   - claim: Neurons in knockout mice have larger mean firing rates than neurons in wild-type mice, at the two-sided 0.05 level.
   - data keys:
  - `rate_knockout` (6, 20) axes: (animals, recorded cells per animal), float: firing rate of each recorded cell, knockout animals
  - `rate_wildtype` (6, 20) axes: (animals, recorded cells per animal), float: firing rate of each recorded cell, wild-type animals
   - sizes: 6 animals per genotype, 20 cells per animal (240 cells in total).

4. **Mapping of the twins to the documented error**: Faulty: the 120 cells per genotype are treated as independent units in a two-sample Student t-test (two-sided 0.05, knockout higher), ignoring that cells share an animal: LAZ10 hierarchical data / pseudoreplication (the animal is the experimental unit); 6 animals x 20 cells within the range of the source examples. Fixed: cells are averaged within animal and the same t-test is applied to the 6 versus 6 animal means (df 10), one of the corrections LAZ10 gives (averaging; a mixed model is the other). The two twins differ only inside the body of `criterion`; the statistical helpers (a Lanczos log-gamma, a continued-fraction regularised incomplete beta and the t-distribution p-values built on them, written in numpy because scipy is not available; checked against numerical integration of the t density, maximum relative difference 1.2e-12 over df 1 to 298, `work/test_helpers.py`) and the guards are identical in both. Guards return None only for non-finite values, too few values or a zero variance. No randomness is used; the criterion is deterministic.

5. **Pre-checks of the fixed criterion** (plain Python, `work/precheck_fixed.py`, output in `work/precheck_fixed_output.txt`; fixed twin only, 200 samples per stream unless stated): holds in plus 126/200 (undefined 0), in minus 6/200 (undefined 0); on the declared control (reassign_animals on plus applied to plus samples) 3/200; on i.i.d. N(0,1) noise of the same shapes 4/200 (undefined 0); on all-zero data (20 samples, guard) 0/20 (undefined 20). Repeatability: two calls on the same data agree. Revisions of the fixed criterion: 0 (first version kept).

6. **Timing** (fixed criterion, mean of 100 calls on plus samples; g mean of 200 plus generations): t = 0.04 ms, g = 0.01 ms, S = 5 (2 worlds + 1 control + 0 premises + 0 relational pairs + 2 probes). Estimate 2 x 200 x (S + 1) x (t + g) = 0.1 s (limit 900 s).

7. **Deviations from the private note, problems, skeleton requests**: No log transform in either twin (the claim is about mean firing rates). The fixed criterion has limited power in plus (see pre-check); recorded, not changed.
