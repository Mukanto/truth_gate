# B6-02 (world C38)

## 1. Identification
Case id B6-02; world id C38; class B-6; subtype None; source key LAZ18; mechanism tag `units-not-independent`; statistic family `proportion`.

## 2. Source and documenting passage
LAZ18, section "Cell culture experiments": "treatments are applied simultaneously to all cells in a well, not independently to each cell ... Thus, a well, culture dish, or another plastic container is the appropriate EU for cell culture experiments."

Read by: full text (PMC5902037 via PMC and Europe PMC) by the part 1 author, see LOG.md 'Sources read and how'. The part 2 author did not fetch any URL for this case (the private note's passage was used; no source was re-read).

## 3. The brief (as in ASSIGNMENT.json)
Claim: The compound raises the share of cells that respond to stimulation: the proportion of responding cells is higher in treated wells than in untreated wells, and a test of the difference between the two groups gives two-sided p < 0.05.

Data keys:
  * `responded`, shape (wells, cells), bool: whether each imaged cell of each well showed a calcium response to the stimulus
  * `treated`, shape (wells,), bool: whether the well was given the compound before stimulation

Sizes: wells = 12; cells = 150 (responded: 12 x 150 = 1800 values; treated: 12 values)

## 4. Mapping
Faulty: Welch two-sample t test on the cell-level 0/1 responses (cells as replicates, 1800 values; equivalent to the two-proportion z test of the note to within the t/normal difference at about 1800 df), two-sided p < 0.05 and treated proportion higher. Fixed: proportion of responding cells per well, the same Welch test on the 12 well proportions (LAZ18 'reduce the data to a single value for each EU'). The only code difference is the two lines that build x and y.

Estimand line. Fixed: difference between treated and untreated groups in the mean well-level response proportion, well as replicate. Faulty: difference between group-level pooled cell proportions, cell as replicate.

Allowed-guard minimum (same in both twins): 2 wells per group, at least 1 cell per well; non-finite values; zero standard error (both groups without variation).

No randomness is used by either criterion (no `rng`); both are deterministic. The p value of Student's t is computed with a numpy-only incomplete-beta helper written inside the criterion body (no new import); it was tested against `scipy.stats.t.sf` on 2238 points (largest relative error 3.9e-11, `work/helper_test_log.txt`).

## 5. Pre-checks of the fixed criterion (plain Python, never Truth_Gate; the faulty criterion was never run)
Number of revisions of the fixed criterion: 0. The twin check `work/verify_twins.py` (text and AST only) confirmed that both files equal the skeleton outside the body, that the body reads no module-level name except `np`, and that it has no import.

Run 1 (400 samples per stream, seed 20261115):
```
B6-02 C38  plus 369/400=0.922 (None 0)  minus 7/400=0.018 (None 0)  control(reassign_wells_to_treatment) 15/400=0.037 (None 0)  noise 9/400=0.022 (None 6)  zeros 0/20=0.000 (None 20)
   scipy reference disagreements on 800 samples: 0
   timing t=0.058 ms  g=0.015 ms  S=5  estimate=0.17 s  (calls 100)
```
Run 2, final structure (1000 samples per stream, seed 20261115):
```
B6-02 C38  plus 913/1000=0.913 (None 0)  minus 22/1000=0.022 (None 0)  control(reassign_wells_to_treatment) 27/1000=0.027 (None 0)  noise 29/1000=0.029 (None 8)  zeros 0/20=0.000 (None 20)
   scipy reference disagreements on 2000 samples: 0
   timing t=0.056 ms  g=0.015 ms  S=5  estimate=0.17 s  (calls 100)
```
Each line gives the share of samples on which the fixed criterion returned True (None counted separately) on plus, minus, the declared control applied to plus samples, a noise probe (normal values, fair coin for bool), an all-zero probe (20 samples) and, where declared, the shuffle probe; the scipy line counts disagreements between the fixed criterion and an independent scipy implementation of the same decision on plus and minus samples. The noise and zero probes were built by hand from the description in `agent_docs/GATE.md`.

## 6. Timing (final fixed criterion)
t = 0.056 ms (mean of 100 calls on plus samples); g = 0.015 ms (mean of 100 plus generations); S = 5 (worlds + controls + premises + relational pairs, plus 2); estimate 2 x 200 x (S + 1) x (t + g) = 0.17 s (limit 900 s). No timing remedy needed.

## 7. Deviations, problems, skeleton requests
The note names a two-proportion z test for the faulty criterion; the faulty criterion here applies the same Welch t function as the fixed one to the cell-level 0/1 responses, so that the twins differ only in the unit (cell versus well). The two tests are numerically near-identical at 1800 values. The error (cells as replicates, N = wells x cells) and every parameter (alpha 0.05, two-sided, treated higher) are those of the note.

Skeleton requests: none. SIZE REQUEST: none.

## Designer lines (PREREG_PHASE_C §3; added by the designer after the fidelity audit)

- Overlap with Phase B: no (addendum source).
- Mechanism tag / statistic family (private note): units-not-independent / proportion.
- Allowed-guard minimum (private note): 2 wells per group (smallest size for a Welch t statistic on well proportions); at least 1 cell per well; non-finite not applicable for bool, zero-variance guard returns None. Same in both twins.
- Size ratio (brief size to source size): source states none.
- The estimand line is in item 4 (criterion author).
