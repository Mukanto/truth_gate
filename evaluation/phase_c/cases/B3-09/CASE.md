# CASE B3-09

## 1. Identity
Case id B3-09; world id C04; class B-3; subtype none (n/a).

## 2. Source and documenting passage
Source key ARC81. Passage (as recorded in the part-1 private note): Abstract: 'Type 2 coupling is the functional relationship between two calculated variables which have one or more common component variables.' (Europe PMC record, PMID 7212790; abstract only.)
Read by the part-1 author of this class (the earlier agent in the same role), as the note and `LOG.md` part 1 state (Europe PMC / EconPapers / archive.org OCR records). In part 2 I did not fetch any source or URL; I relied on the note.

## 3. Brief (as in ASSIGNMENT.json)
Claim: Across critically ill patients, whole-body oxygen uptake measured by expired-gas analysis is positively correlated with systemic oxygen delivery (cardiac output times arterial oxygen content): the Pearson correlation is at least 0.3.
Data keys:
  * `cardiac_output` (patients,) float: Cardiac output of each patient by thermodilution, in L/min.
  * `arterial_o2_content` (patients,) float: Arterial blood oxygen content of each patient, in mL O2 per dL.
  * `venous_o2_content` (patients,) float: Mixed venous blood oxygen content of each patient, in mL O2 per dL.
  * `o2_uptake_expired` (patients,) float: Whole-body oxygen uptake of each patient from expired-gas analysis, in mL/min.
Sizes: patients = 60; cardiac_output, arterial_o2_content, venous_o2_content and o2_uptake_expired each have shape (60,).

## 4. Mapping
Documented error (note): Pearson correlation across patients between oxygen delivery (cardiac_output times arterial_o2_content) and oxygen uptake calculated from the same cardiac output (cardiac_output times (arterial_o2_content minus venous_o2_content)); claim holds when r >= 0.3. Documented parameter: both calculated variables contain cardiac output, which carries its own measurement error.
Documented correction (note): Pearson correlation between oxygen delivery (cardiac_output times arterial_o2_content) and o2_uptake_expired, the uptake measured by expired-gas analysis; claim holds when r >= 0.3.
As implemented. Faulty: Pearson correlation between oxygen delivery (cardiac_output * arterial_o2_content) and the uptake calculated from the same cardiac output, cardiac_output * (arterial_o2_content - venous_o2_content), holds when r >= 0.3. Fixed: Pearson correlation between the same delivery and o2_uptake_expired, holds when >= 0.3. The constant 10 of the unit conversion does not change a correlation and is left out.
Guards as coded: n >= 3 in both; zero variance -> None; non-finite -> None.
No randomness is used by either criterion (no `rng` is created); the answer is a function of the data only.
Estimand line (from the note): Fixed: relation between oxygen delivery and an uptake measure that does not contain cardiac output. Faulty: relation between delivery and an uptake calculated from cardiac output.
Mechanism tag shared-measured-component, statistic family correlation (note).

## 5. Pre-checks of the fixed criterion (plain Python, `work/precheck_fixed.py`, output in `work/precheck_fixed_run1.txt`)
Run 1, 300 samples per stream, seeds fixed in the script; fixed criterion only, the faulty file was never imported or run.
* plus: holds 300/300, fails 0/300, None 0/300 (rate 1.000)
* minus: holds 5/300, fails 295/300, None 0/300 (rate 0.017)
* control permute_uptake_across_patients: holds 1/300, fails 299/300, None 0/300 (rate 0.003)
* noise probe (i.i.d. N(0,1) / Bernoulli(0.5) per array, as GATE.md describes): holds 5/300, fails 295/300, None 0/300 (rate 0.017)
* zeros probe: 1 sample, None (zero variance guard)
Number of revisions of the fixed criterion: 0.

## 6. Timing (fixed criterion, mean of 40 calls on plus samples; plus generation mean of 40 calls)
t = 0.040 ms, g = 0.042 ms, S = 5 (worlds 2 + controls + premises + relational pairs, plus 2), estimate 2 x 200 x (S + 1) x (t + g) = 0.2 s (limit 900 s). No speed change was needed.

## 7. Deviations, problems, skeleton requests
The faulty criterion does not read o2_uptake_expired and the fixed criterion does not read venous_o2_content (as planned in the note).
Skeleton requests: none. Size requests: none.

## Designer lines (PREREG_PHASE_C §3; added by the designer after the fidelity audit)

- Overlap with Phase B: yes, Phase B case B3-01.
- Mechanism tag / statistic family (private note): shared-measured-component / correlation.
- Allowed-guard minimum (private note): 3 patients (Pearson correlation); zero variance of delivery or of the uptake -> None; non-finite -> None.
- Size ratio (brief size to source size): source states none.
- The estimand line is in item 4 (criterion author).
