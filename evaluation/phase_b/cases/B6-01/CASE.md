# B6-01

1. **Case**: B6-01; world id W32; class B-6; subtype (none); source assigned by the designer: NIE11.

2. **Source and documenting passage**: NIE11. NIE11 (Nieuwenhuis et al. 2011, Nat Neurosci 14:1105), p. 1105: "To support this claim, they needed to report a statistically significant interaction (between amount of training and type of mice), but instead they reported that one effect was statistically significant, whereas the other effect was not." (Fig. 1b; MAK19 Fig. 1B uses 20 per group.)
   Reading: Read in full by the earlier author (author-hosted PDF, whole text); I re-checked the quoted sentence against the saved extract src/nie.txt and src/nie2.txt.

3. **Brief exactly as in `ASSIGNMENT.json`**:
   - id: W32
   - claim: A training programme improves test scores more in the trained group than in the untrained group: the mean pre-to-post gain among trained participants is larger than the mean pre-to-post gain among untrained participants, at the two-sided 0.05 level.
   - data keys:
  - `pre_trained` (20,) axis: participants, float: score before the programme, trained group, one value per participant
  - `post_trained` (20,) axis: participants (same order as pre_trained), float: score after the programme, same trained participants
  - `pre_untrained` (20,) axis: participants, float: score before, untrained group, one value per participant
  - `post_untrained` (20,) axis: participants (same order as pre_untrained), float: score after, same untrained participants
   - sizes: 20 participants per group (40 in total).

4. **Mapping of the twins to the documented error**: Faulty: two separate one-sample t-tests (two-sided, alpha 0.05) on the per-participant gains (post - pre), one per group; the claim "holds" when the trained gain is significantly positive, the untrained gain is not significant, and the trained mean gain is larger. This is the "significant in one group, not in the other" rule that NIE11 documents (Fig. 1b); alpha 0.05 is the level stated in the brief and the usual level in the source. Fixed: the direct interaction test NIE11 asks for, a Welch t-test on the gains of the two groups (two-sided 0.05, trained larger), the same data and the same alpha. The two twins differ only inside the body of `criterion`; the statistical helpers (a Lanczos log-gamma, a continued-fraction regularised incomplete beta and the t-distribution p-values built on them, written in numpy because scipy is not available; checked against numerical integration of the t density, maximum relative difference 1.2e-12 over df 1 to 298, `work/test_helpers.py`) and the guards are identical in both. Guards return None only for non-finite values, too few values or a zero variance. No randomness is used; the criterion is deterministic.

5. **Pre-checks of the fixed criterion** (plain Python, `work/precheck_fixed.py`, output in `work/precheck_fixed_output.txt`; fixed twin only, 200 samples per stream unless stated): holds in plus 165/200 (undefined 0), in minus 1/200 (undefined 0); on the declared control (reshuffle_participants on plus applied to plus samples) 4/200; on i.i.d. N(0,1) noise of the same shapes 5/200 (undefined 0); on all-zero data (20 samples, guard) 0/20 (undefined 20). Repeatability: two calls on the same data agree. Revisions of the fixed criterion: 0 (first version kept).

6. **Timing** (fixed criterion, mean of 100 calls on plus samples; g mean of 200 plus generations): t = 0.04 ms, g = 0.01 ms, S = 5 (2 worlds + 1 control + 0 premises + 0 relational pairs + 2 probes). Estimate 2 x 200 x (S + 1) x (t + g) = 0.1 s (limit 900 s).

7. **Deviations from the private note, problems, skeleton requests**: none
