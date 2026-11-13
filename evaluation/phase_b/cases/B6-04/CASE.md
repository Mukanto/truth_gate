# B6-04

1. **Case**: B6-04; world id W25; class B-6; subtype (none); source assigned by the designer: HUR84.

2. **Source and documenting passage**: HUR84. HUR84 (Hurlbert 1984, Ecol Monogr 54:187), section "Sacrificial pseudoreplication": "...where the data for replicates are pooled prior to statistical analysis ... or where the two or more samples or measurements taken from each experimental unit are treated as independent replicates (Fig. 5B)." (the aquaria example has four treated and four control units.)
   Reading: Read in full by the earlier author (UBC PDF, pdftotext, two-column order scrambled; passage located by keyword); I re-checked the quoted sentence against the saved extract src/hur.txt.

3. **Brief exactly as in `ASSIGNMENT.json`**:
   - id: W25
   - claim: Adding nutrients to experimental ponds raises algal biomass: mean biomass in the fertilised ponds is higher than in the unfertilised ponds, at the two-sided 0.05 level.
   - data keys:
  - `biomass_fertilised` (4, 10) axes: (ponds, water samples per pond), float: algal biomass per water sample, fertilised ponds
  - `biomass_unfertilised` (4, 10) axes: (ponds, water samples per pond), float: algal biomass per water sample, unfertilised ponds
   - sizes: 4 ponds per treatment, 10 water samples per pond (80 values in total).

4. **Mapping of the twins to the documented error**: Faulty: the 40 water samples of each treatment are pooled (80 values in all) and compared with a two-sample Student t-test (two-sided 0.05, direction fertilised higher), so the samples are treated as independent replicates: HUR84 "simple pseudoreplication" (Fig. 5B), with the typical layout of 4 units per treatment (the aquaria example). Fixed: samples are averaged within pond and the same t-test is applied to the 4 versus 4 pond means (df 6), the experimental units. The two twins differ only inside the body of `criterion`; the statistical helpers (a Lanczos log-gamma, a continued-fraction regularised incomplete beta and the t-distribution p-values built on them, written in numpy because scipy is not available; checked against numerical integration of the t density, maximum relative difference 1.2e-12 over df 1 to 298, `work/test_helpers.py`) and the guards are identical in both. Guards return None only for non-finite values, too few values or a zero variance. No randomness is used; the criterion is deterministic.

5. **Pre-checks of the fixed criterion** (plain Python, `work/precheck_fixed.py`, output in `work/precheck_fixed_output.txt`; fixed twin only, 200 samples per stream unless stated): holds in plus 122/200 (undefined 0), in minus 3/200 (undefined 0); on the declared control (reassign_ponds on plus applied to plus samples) 5/200; on i.i.d. N(0,1) noise of the same shapes 5/200 (undefined 0); on all-zero data (20 samples, guard) 0/20 (undefined 20). Repeatability: two calls on the same data agree. Revisions of the fixed criterion: 0 (first version kept).

6. **Timing** (fixed criterion, mean of 100 calls on plus samples; g mean of 200 plus generations): t = 0.04 ms, g = 0.01 ms, S = 5 (2 worlds + 1 control + 0 premises + 0 relational pairs + 2 probes). Estimate 2 x 200 x (S + 1) x (t + g) = 0.1 s (limit 900 s).

7. **Deviations from the private note, problems, skeleton requests**: No log transform in either twin (the claim is about mean biomass and the private note says t-test on pond means). The fixed criterion has limited power in plus (see pre-check); recorded, not changed. Two-sample test: Student pooled variance in both twins.
