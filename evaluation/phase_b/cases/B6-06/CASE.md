# B6-06

1. **Case**: B6-06; world id W39; class B-6; subtype (none); source assigned by the designer: HUR84.

2. **Source and documenting passage**: HUR84. HUR84, section "Temporal pseudoreplication": "This differs from simple pseudoreplication only in that the multiple samples from each experimental unit are not taken simultaneously but rather sequentially over each of several dates (Fig. 5C). Dates are then taken to represent replicated treatments ..."
   Reading: Read in full by the earlier author (UBC PDF, pdftotext, two-column order scrambled; passage located by keyword); I re-checked the quoted sentence against the saved extract src/hur.txt.

3. **Brief exactly as in `ASSIGNMENT.json`**:
   - id: W39
   - claim: Mowing raises plant species richness in grassland: mean species richness in mown plots is higher than in unmown plots, at the two-sided 0.05 level.
   - data keys:
  - `richness_mown` (6, 12) axes: (plots, monthly surveys), float: species count in each mown plot at each monthly survey, in time order
  - `richness_unmown` (6, 12) axes: (plots, monthly surveys), float: species count in each unmown plot at each monthly survey, in time order
   - sizes: 6 plots per treatment, 12 monthly surveys per plot (144 values in total).

4. **Mapping of the twins to the documented error**: Faulty: all 72 plot-by-survey values per treatment are pooled and compared with a two-sample Student t-test (two-sided 0.05, mown higher), so the repeated surveys of the same plot count as replicates: HUR84 "temporal pseudoreplication". Fixed: surveys are averaged within plot and the same t-test is applied to the 6 versus 6 plot means (df 10). The two twins differ only inside the body of `criterion`; the statistical helpers (a Lanczos log-gamma, a continued-fraction regularised incomplete beta and the t-distribution p-values built on them, written in numpy because scipy is not available; checked against numerical integration of the t density, maximum relative difference 1.2e-12 over df 1 to 298, `work/test_helpers.py`) and the guards are identical in both. Guards return None only for non-finite values, too few values or a zero variance. No randomness is used; the criterion is deterministic.

5. **Pre-checks of the fixed criterion** (plain Python, `work/precheck_fixed.py`, output in `work/precheck_fixed_output.txt`; fixed twin only, 200 samples per stream unless stated): holds in plus 185/200 (undefined 0), in minus 3/200 (undefined 0); on the declared control (reassign_plots on plus applied to plus samples) 8/200; on i.i.d. N(0,1) noise of the same shapes 3/200 (undefined 0); on all-zero data (20 samples, guard) 0/20 (undefined 20). Repeatability: two calls on the same data agree. Revisions of the fixed criterion: 0 (first version kept).

6. **Timing** (fixed criterion, mean of 100 calls on plus samples; g mean of 200 plus generations): t = 0.04 ms, g = 0.08 ms, S = 5 (2 worlds + 1 control + 0 premises + 0 relational pairs + 2 probes). Estimate 2 x 200 x (S + 1) x (t + g) = 0.3 s (limit 900 s).

7. **Deviations from the private note, problems, skeleton requests**: none.
