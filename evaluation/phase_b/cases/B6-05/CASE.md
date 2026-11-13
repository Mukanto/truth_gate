# B6-05

1. **Case**: B6-05; world id W46; class B-6; subtype (none); source assigned by the designer: HUR84.

2. **Source and documenting passage**: HUR84. HUR84, same passage as B6-04 (several samples from each experimental unit treated as independent replicates; the tanks are the units that receive the treatment). HUR84 does not discuss regression on a dose; the unit-of-treatment logic is carried over (extension flagged by the earlier author).
   Reading: Read in full by the earlier author (UBC PDF, pdftotext, two-column order scrambled; passage located by keyword); I re-checked the quoted sentence against the saved extract src/hur.txt.

3. **Brief exactly as in `ASSIGNMENT.json`**:
   - id: W46
   - claim: Mussel growth increases with the amount of food supplement given to a tank: the regression slope of growth on the supplement dose is positive, at the one-sided 0.05 level.
   - data keys:
  - `dose` (12,) axis: tanks, float: supplement dose assigned to each tank
  - `growth` (12, 8) axes: (tanks, individual mussels per tank), float: shell growth of each measured mussel, in the tank given by the first axis
   - sizes: 12 tanks, 8 mussels per tank (96 growth values).

4. **Mapping of the twins to the documented error**: Faulty: ordinary least-squares regression of all 96 mussel growth values on the tank dose repeated for each mussel (df 94), one-sided 0.05 on a positive slope; the individual mussels are treated as independent replicates although the dose is applied to tanks (HUR84 pseudoreplication; regression on a dose is an extension of the documented ANOVA/t-test setting, flagged in the private note). Fixed: regression of the 12 tank means on the dose (df 10), same slope test and level. The two twins differ only inside the body of `criterion`; the statistical helpers (a Lanczos log-gamma, a continued-fraction regularised incomplete beta and the t-distribution p-values built on them, written in numpy because scipy is not available; checked against numerical integration of the t density, maximum relative difference 1.2e-12 over df 1 to 298, `work/test_helpers.py`) and the guards are identical in both. Guards return None only for non-finite values, too few values or a zero variance. No randomness is used; the criterion is deterministic.

5. **Pre-checks of the fixed criterion** (plain Python, `work/precheck_fixed.py`, output in `work/precheck_fixed_output.txt`; fixed twin only, 200 samples per stream unless stated): holds in plus 161/200 (undefined 0), in minus 10/200 (undefined 0); on the declared control (permute_dose on plus applied to plus samples) 14/200; on i.i.d. N(0,1) noise of the same shapes 5/200 (undefined 0); on all-zero data (20 samples, guard) 0/20 (undefined 20). Repeatability: two calls on the same data agree. Revisions of the fixed criterion: 0 (first version kept).

6. **Timing** (fixed criterion, mean of 100 calls on plus samples; g mean of 200 plus generations): t = 0.03 ms, g = 0.01 ms, S = 5 (2 worlds + 1 control + 0 premises + 0 relational pairs + 2 probes). Estimate 2 x 200 x (S + 1) x (t + g) = 0.1 s (limit 900 s).

7. **Deviations from the private note, problems, skeleton requests**: none. Extension of the documented setting is flagged in the private note (regression on a dose). In the pre-check the fixed criterion holds in 10/200 (5%) of minus samples and 14/200 (7%) under the control, close to the nominal one-sided 0.05 and within sampling noise for 200 samples; recorded, not changed.
