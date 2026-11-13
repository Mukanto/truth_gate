# CASE O2a

## 1. Identification
- Case id: O2a
- World id: W40
- Class: O (out of scope); subtype assigned by the designer: O-2

## 2. Source and documented error
- Source key: SIM11
- Passage: SIM11 (Simmons, Nelson and Simonsohn 2011), Table 1 and the text on the first rows: Situation A, "two dependent variables (r = .50)", with three tests: one on each dependent variable and one on their average, 20 observations per cell, 15,000 simulated samples.
- Reading: Read by the earlier author (phase 1), full text PDF (UBC course copy), Table 1 and the text of the first two rows. Not re-read by the phase 2 author.

## 3. Brief (exactly as in ASSIGNMENT.json)
```json
{
  "id": "W40",
  "claim": "Participants in the treated group score higher than controls on the study's primary outcome (outcome measure 1): a one-sided Welch t test on measure 1 gives p < 0.05.",
  "data_keys": [
    {
      "key": "treated",
      "shape": "(participants_treated, 2)",
      "dtype": "float",
      "meaning": "the two outcome measures (columns: measure 1 = primary, measure 2 = secondary; correlated, r about 0.5) for each treated participant"
    },
    {
      "key": "control",
      "shape": "(participants_control, 2)",
      "dtype": "float",
      "meaning": "the same two outcome measures for each control participant"
    }
  ],
  "sizes": "20 participants per group"
}
```

## 4. Mapping of the criteria to the documented error and its correction
Faulty: one-sided Welch t tests on measure 1, on measure 2 and on the average of the two measures; the claim holds if the smallest of the three p values is below 0.05 (the analysis that is reported is chosen after seeing all three). Parameters are those of SIM11 Situation A (two correlated DVs, r about 0.5, 20 per cell, threshold 0.05) and are fixed by the skeleton. Fixed: the planned primary analysis only, a one-sided Welch test on measure 1 at 0.05. Both use the same hand-written numpy Welch/t-tail code (the exact tail via the regularised incomplete beta function; no scipy).

## 5. Pre-checks of the fixed criterion (plain Python, work/precheck_fixed.py, seed 777)
- plus: holds in 256/300 (0.853)
- minus: holds in 20/300 (0.067)
- declared control (applied to plus samples): holds in 10/300 (0.033)
- my approximation of the noise probe (float arrays N(0,1), bool arrays fair coin), 100 samples: holds in 5/100
- zero probe (all-zero arrays, bool False), 100 samples: holds in 0/100 (100 UNDEFINED by the guard)
- Same input evaluated twice gave the same answer (repeatable).
- Revisions of the fixed criterion: 0 (the faulty criterion was never run).

## 6. Timing
- t (mean of 50 calls of the fixed criterion on plus samples) = 0.063 ms; g (mean of 50 plus generations) = 0.014 ms
- S = 5 (2 worlds + 1 control + 0 premises + 0 relational pairs + 2 probes)
- Estimate 2 x 200 x (S + 1) x (t + g) = 0.2 s (limit 900 s)

## 7. Deviations, problems, skeleton requests
The t tail is computed with an incomplete-beta routine written inside the criterion; it was checked against the tabulated one-sided 5% critical values for df 1, 2, 10, 20, 38, 58, 1000 (agreement to 1e-7) in work/helper_test.py. None otherwise; no skeleton request.
