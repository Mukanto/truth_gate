# B6-02

1. **Case**: B6-02; world id W48; class B-6; subtype (none); source assigned by the designer: NIE11.

2. **Source and documenting passage**: NIE11. NIE11, p. 1105: "Similarly, claims about differences in activation across brain regions must be supported by a significant interaction between brain region and the factor underlying the contrast of interest." (drug versus placebo is among the comparisons the text lists; Fig. 1d, repeated measures.)
   Reading: Read in full by the earlier author (author-hosted PDF, whole text); I re-checked the quoted sentence against the saved extract src/nie.txt and src/nie2.txt.

3. **Brief exactly as in `ASSIGNMENT.json`**:
   - id: W48
   - claim: A drug changes the evoked response more in visual cortex than in auditory cortex: the drug-minus-placebo difference in response amplitude is larger in the visual region than in the auditory region across 16 participants, at the two-sided 0.05 level.
   - data keys:
  - `visual_placebo` (16,) axis: participants, float: evoked amplitude in visual region under placebo
  - `visual_drug` (16,) axis: participants (same order), float: evoked amplitude in visual region under drug
  - `auditory_placebo` (16,) axis: participants (same order), float: evoked amplitude in auditory region under placebo
  - `auditory_drug` (16,) axis: participants (same order), float: evoked amplitude in auditory region under drug
   - sizes: 16 participants, every participant measured in both regions and both conditions.

4. **Mapping of the twins to the documented error**: Faulty: separate paired (one-sample on the difference) t-tests of drug minus placebo in the visual and in the auditory region (two-sided 0.05); the claim holds when the visual effect is significantly positive, the auditory effect is not significant and the visual mean effect is larger (the "significant here, not there" rule of NIE11, brain-region example). Fixed: one paired t-test on the difference of differences ((vis_drug - vis_pl) - (aud_drug - aud_pl)) across the 16 participants, two-sided 0.05, visual larger (the region by drug interaction NIE11 requires). The two twins differ only inside the body of `criterion`; the statistical helpers (a Lanczos log-gamma, a continued-fraction regularised incomplete beta and the t-distribution p-values built on them, written in numpy because scipy is not available; checked against numerical integration of the t density, maximum relative difference 1.2e-12 over df 1 to 298, `work/test_helpers.py`) and the guards are identical in both. Guards return None only for non-finite values, too few values or a zero variance. No randomness is used; the criterion is deterministic.

5. **Pre-checks of the fixed criterion** (plain Python, `work/precheck_fixed.py`, output in `work/precheck_fixed_output.txt`; fixed twin only, 200 samples per stream unless stated): holds in plus 158/200 (undefined 0), in minus 3/200 (undefined 0); on the declared control (swap_regions on plus applied to plus samples) 4/200; on i.i.d. N(0,1) noise of the same shapes 9/200 (undefined 0); on all-zero data (20 samples, guard) 0/20 (undefined 20). Repeatability: two calls on the same data agree. Revisions of the fixed criterion: 0 (first version kept).

6. **Timing** (fixed criterion, mean of 100 calls on plus samples; g mean of 200 plus generations): t = 0.03 ms, g = 0.01 ms, S = 5 (2 worlds + 1 control + 0 premises + 0 relational pairs + 2 probes). Estimate 2 x 200 x (S + 1) x (t + g) = 0.1 s (limit 900 s).

7. **Deviations from the private note, problems, skeleton requests**: none. The private note did not state a direction check; I added the direction (visual mean effect larger) to the faulty criterion and the sign (visual larger) to the fixed one, because the claim is directional.
