# CASE O2b

## 1. Identification
- Case id: O2b
- World id: W03
- Class: O (out of scope); subtype assigned by the designer: O-2

## 2. Source and documented error
- Source key: SIM11
- Passage: SIM11, text on optional stopping: the researcher "collects 20 observations per condition and then tests for significance"; "if the result is nonsignificant, the researcher collects 10 additional observations per condition, and then again tests for significance."
- Reading: Read by the earlier author (phase 1), full text PDF. Not re-read by the phase 2 author.

## 3. Brief (exactly as in ASSIGNMENT.json)
```json
{
  "id": "W03",
  "claim": "Participants who received the treatment score higher than controls on the outcome: a one-sided Welch t test of treated versus control gives p < 0.05 once recruitment of the planned sample is complete.",
  "data_keys": [
    {
      "key": "treated",
      "shape": "(participants_treated,)",
      "dtype": "float",
      "meaning": "outcome score of each treated participant, rows in order of recruitment"
    },
    {
      "key": "control",
      "shape": "(participants_control,)",
      "dtype": "float",
      "meaning": "outcome score of each control participant, rows in order of recruitment"
    }
  ],
  "sizes": "planned sample 30 participants per group"
}
```

## 4. Mapping of the criteria to the documented error and its correction
Faulty: one-sided Welch tests at the first 20 per group (first 20 rows of each array, rows are in recruitment order) and again at 30 per group; the claim holds if either p is below 0.05 (the stopping point is chosen after seeing both). Parameters: 20 then 30 per cell (SIM11; the private note corrected an earlier 20/25/30 draft to the two looks of the source), threshold 0.05. Fixed: a single test at the planned 30 per group, same test and threshold. Both use the same numpy Welch/t-tail code as O2a.

## 5. Pre-checks of the fixed criterion (plain Python, work/precheck_fixed.py, seed 777)
- plus: holds in 273/300 (0.910)
- minus: holds in 19/300 (0.063)
- declared control (applied to plus samples): holds in 20/300 (0.067)
- my approximation of the noise probe (float arrays N(0,1), bool arrays fair coin), 100 samples: holds in 3/100
- zero probe (all-zero arrays, bool False), 100 samples: holds in 0/100 (100 UNDEFINED by the guard)
- Same input evaluated twice gave the same answer (repeatable).
- Revisions of the fixed criterion: 0 (the faulty criterion was never run).

## 6. Timing
- t (mean of 50 calls of the fixed criterion on plus samples) = 0.045 ms; g (mean of 50 plus generations) = 0.007 ms
- S = 5 (2 worlds + 1 control + 0 premises + 0 relational pairs + 2 probes)
- Estimate 2 x 200 x (S + 1) x (t + g) = 0.1 s (limit 900 s)

## 7. Deviations, problems, skeleton requests
None. Same incomplete-beta helper as O2a (checked in work/helper_test.py). No skeleton request.
