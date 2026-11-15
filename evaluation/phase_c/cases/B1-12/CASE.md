# CASE B1-12 (world C11)

## 1. Identification
Case id B1-12; world id C11; class B-1; subtype None.
Mechanism tag: extreme-group-change. Statistic family: proportion.
Allowed-guard minimum (private note): 1 patient after the cut (a proportion is defined from 1).
Size ratio (brief size to source size): source states none (see the sizes note of the private note: Abstract states no sizes).

## 2. Source and documenting passage
Source key: BAR05.
Passage (from the private note of the brief author): Abstract: "The effect of RTM in a sample becomes more noticeable with increasing measurement error and when follow-up measurements are only examined on a sub-sample selected using a baseline value." (abstract via Europe PMC search record; full text not accessible)
Read by the brief author (Part 1) from the URLs in `LOG.md`; I (Part 2 author) did not re-read the source and used the note's quotation.

## 3. The brief (as in `ASSIGNMENT.json`)
Claim: Among patients whose symptom score at the screening visit was at least 60, at least 40% improve by 10 points or more between the start of the programme and the 6-month follow-up (score at the start minus score at 6 months of at least 10); the claim is that the proportion of such patients is at least 0.40.

Data keys:
  * `score_screen`, float, (patients,): symptom score of each patient at the screening visit (higher is worse)
  * `score_start`, float, (patients,): symptom score of each patient at the start of the programme
  * `score_6m`, float, (patients,): symptom score of each patient at the 6-month follow-up

Sizes: {"patients": 500}

## 4. Mapping
Faulty: keeps patients with score_start >= 60 and requires the proportion with score_start minus score_6m >= 10 to be >= 0.40. Fixed: keeps patients with score_screen >= 60 and requires the same proportion >= 0.40 (BAR05, abstract: baseline-selected sub-sample).

Estimand line. Claim names the screening score and the start and 6-month scores because the estimand is the improvement share among patients who qualified at screening. Faulty: share improving by 10 points among patients chosen by the very score the improvement is measured from. Fixed: the same share among patients chosen by the independent screening score.
(Estimand of the two statistics as in the private note; faulty estimates it in the documented wrong way, fixed estimates the claim's quantity.)
Faulty: share improving by 10 points among patients chosen by the very score the improvement is measured from. Fixed: the same share among patients chosen by the independent screening score.

Both twins are generated from the same helper text (a quadrature Student-t upper tail written with numpy only, checked against scipy in `work/test_sf.py`, absolute error below 3e-5 for 1 to 600 degrees of freedom), and the twin bodies differ only in the lines that carry the error and its correction. No randomness is used in either criterion. Returns: True or False; None only for a non-finite input, an empty selection or one below the stated minimum, or a zero variance.

## 5. Pre-checks of the fixed criterion (plain Python, 200 samples per stream, my own seeds; the faulty criterion was never run)
  * plus: holds 200, fails 0, None 0, exceptions 0 (n = 200)
  * minus: holds 0, fails 200, None 0, exceptions 0 (n = 200)
  * control:exchange_start_and_6_month_scores: holds 0, fails 200, None 0, exceptions 0 (n = 200)
  * probe:noise: holds 0, fails 0, None 200, exceptions 0 (n = 200)
  * probe:zeros: holds 0, fails 0, None 5, exceptions 0 (n = 5)
  * Cross-check: the decision of the fixed criterion was compared with an independent scipy re-implementation of the same rule on 60 plus and 60 minus samples (`work/crosscheck_fixed.py`): 0 disagreements of 120.
Number of revisions of the fixed criterion: 0 (the first version was kept after the pre-check). Pre-check script: `work/precheck_fixed.py`; the probes follow `agent_docs/GATE.md` (noise: N(0,1), bool as coin flips; zeros).

## 6. Timing (final fixed criterion)
t = 0.000016 s (mean of 30 calls on plus samples), g = 0.000036 s (mean plus generation, 30 samples), S = 5 (worlds + controls + premises + relational pairs, plus 2), estimate 2 x 200 x (S + 1) x (t + g) = 0.1 s (limit 900 s).

## 7. Deviations, problems, skeleton requests
none
Skeleton requests: none. Size requests: none.

(The designer adds the overlap line and the size ratio.)

## Designer lines (PREREG_PHASE_C §3; added by the designer after the fidelity audit)

- Overlap with Phase B: yes, Phase B case B1-11.
- Mechanism tag / statistic family (private note): extreme-group-change / proportion.
- Allowed-guard minimum (private note): 1 patient after the cut (a proportion is defined from 1)
- Size ratio (brief size to source size): source states none.
- The estimand line is in item 4 (criterion author).
