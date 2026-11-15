# CASE B1-03 (world C50)

## 1. Identification
Case id B1-03; world id C50; class B-1; subtype None.
Mechanism tag: extreme-group-change. Statistic family: mean.
Allowed-guard minimum (private note): 2 patients after the cut for the paired t statistic.
Size ratio (brief size to source size): source states none (see the sizes note of the private note: Source states no sizes).

## 2. Source and documenting passage
Source key: MOR03.
Passage (from the private note of the brief author): Diagnostic tests section: "Because of this chance effect, there is a high probability that subsequent measurements will spontaneously regress towards the mean value. This misleads clinicians and patients into thinking that treatment has been effective when the treatment was either not required or ineffective." Solution: serial measurements. (PMC1125994, full text)
Read by the brief author (Part 1) from the URLs in `LOG.md`; I (Part 2 author) did not re-read the source and used the note's quotation.

## 3. The brief (as in `ASSIGNMENT.json`)
Claim: Among patients whose first systolic blood-pressure reading was at least 160 mmHg, antihypertensive treatment lowers systolic pressure: the mean fall from the second reading (taken before treatment began) to the third reading (taken after 8 weeks of treatment) is at least 8 mmHg, and a one-sided paired t test of the fall is significant at the 0.05 level.

Data keys:
  * `sbp`, float, (patients, readings): systolic blood pressure in mmHg; readings in time order: reading 1 at the screening visit, reading 2 at the pre-treatment visit, reading 3 after 8 weeks of treatment

Sizes: {"patients": 250, "readings": 3}

## 4. Mapping
Faulty: keeps patients whose reading 2 (column 1 of sbp) is >= 160 mmHg and tests the fall from reading 2 to reading 3 (mean fall >= 8, one-sided paired t test at 0.05). Fixed: keeps patients whose reading 1 (column 0, the screening reading) is >= 160 and tests the same fall with the same threshold and test (MOR03, diagnostic-tests section: serial measurements).

Estimand line. Claim names the screening reading and the two later readings because the estimand is the fall in patients who qualified at the first reading. Faulty: mean fall from reading 2 to reading 3 among patients chosen by reading 2 (the starting value of the fall). Fixed: mean fall from reading 2 to reading 3 among patients chosen by reading 1.
(Estimand of the two statistics as in the private note; faulty estimates it in the documented wrong way, fixed estimates the claim's quantity.)
Faulty: mean fall from reading 2 to reading 3 among patients chosen by reading 2. Fixed: mean fall from reading 2 to reading 3 among patients chosen by reading 1.

Both twins are generated from the same helper text (a quadrature Student-t upper tail written with numpy only, checked against scipy in `work/test_sf.py`, absolute error below 3e-5 for 1 to 600 degrees of freedom), and the twin bodies differ only in the lines that carry the error and its correction. No randomness is used in either criterion. Returns: True or False; None only for a non-finite input, an empty selection or one below the stated minimum, or a zero variance.

## 5. Pre-checks of the fixed criterion (plain Python, 200 samples per stream, my own seeds; the faulty criterion was never run)
  * plus: holds 196, fails 4, None 0, exceptions 0 (n = 200)
  * minus: holds 0, fails 200, None 0, exceptions 0 (n = 200)
  * control:swap_readings_2_and_3_at_random_within_patient: holds 0, fails 200, None 0, exceptions 0 (n = 200)
  * probe:noise: holds 0, fails 0, None 200, exceptions 0 (n = 200)
  * probe:zeros: holds 0, fails 0, None 5, exceptions 0 (n = 5)
  * Cross-check: the decision of the fixed criterion was compared with an independent scipy re-implementation of the same rule on 60 plus and 60 minus samples (`work/crosscheck_fixed.py`): 0 disagreements of 120.
Number of revisions of the fixed criterion: 0 (the first version was kept after the pre-check). Pre-check script: `work/precheck_fixed.py`; the probes follow `agent_docs/GATE.md` (noise: N(0,1), bool as coin flips; zeros).

## 6. Timing (final fixed criterion)
t = 0.000071 s (mean of 30 calls on plus samples), g = 0.000021 s (mean plus generation, 30 samples), S = 5 (worlds + controls + premises + relational pairs, plus 2), estimate 2 x 200 x (S + 1) x (t + g) = 0.2 s (limit 900 s).

## 7. Deviations, problems, skeleton requests
none
Skeleton requests: none. Size requests: none.

(The designer adds the overlap line and the size ratio.)

## Designer lines (PREREG_PHASE_C §3; added by the designer after the fidelity audit)

- Overlap with Phase B: no (addendum source).
- Mechanism tag / statistic family (private note): extreme-group-change / mean.
- Allowed-guard minimum (private note): 2 patients after the cut for the paired t statistic
- Size ratio (brief size to source size): source states none.
- The estimand line is in item 4 (criterion author).
