# CASE O1a

## 1. Identification
- Case id: O1a
- World id: W54
- Class: O (out of scope); subtype assigned by the designer: O-1

## 2. Source and documented error
- Source key: KAP23
- Passage: KAP23 (Kapoor and Narayanan 2023), section 2.4, type L2: "If the model has access to features that should not be legitimately available for use in the modeling exercise, this could result in leakage. One instance when this can happen is if a feature is a proxy for the outcome variable." (the paper's example: anti-hypertensive drug use as a predictor of hypertension).
- Reading: Read by the earlier author (phase 1), ar5iv full text of section 2.4 (see LOG.md, 'Revision after coordinator message'). Not re-read by the phase 2 author.

## 3. Brief (exactly as in ASSIGNMENT.json)
```json
{
  "id": "W54",
  "claim": "Using the recorded patient variables, a linear classifier identifies sepsis cases with an accuracy of at least 0.75 on new patients (the claim holds when the accuracy estimate is >= 0.75).",
  "data_keys": [
    {
      "key": "vars",
      "shape": "(patients, 12)",
      "dtype": "float",
      "meaning": "12 recorded variables per patient: vital signs and laboratory values at admission, age, and the number of doses of the targeted therapy recorded during the stay"
    },
    {
      "key": "sepsis",
      "shape": "(patients,)",
      "dtype": "bool",
      "meaning": "True if the patient received a sepsis diagnosis"
    }
  ],
  "sizes": "250 patients; 12 variables"
}
```

## 4. Mapping of the criteria to the documented error and its correction
Faulty: a least-squares linear classifier (0/1 labels, intercept, threshold 0.5) is fitted on the first 150 patients and its accuracy is measured on the remaining 100, using all 12 variables, including column 11, the number of targeted-therapy doses recorded during the stay, which is a proxy for the diagnosis (the L2 error: a feature that should not be legitimately available). The split and the fit are clean, so the leakage is at the data level. Parameters: the accuracy threshold 0.75 is the claim's; the split 150/100 and the least-squares classifier are my choice (the brief says 'a linear classifier' on 'new patients'; the source documents no values). Fixed: the same pipeline with column 11 dropped (11 variables available at admission); same statistic (test accuracy), same threshold, same decision rule.

## 5. Pre-checks of the fixed criterion (plain Python, work/precheck_fixed.py, seed 777)
- plus: holds in 280/300 (0.933)
- minus: holds in 23/300 (0.077)
- declared control (applied to plus samples): holds in 16/300 (0.053)
- my approximation of the noise probe (float arrays N(0,1), bool arrays fair coin), 100 samples: holds in 0/100
- zero probe (all-zero arrays, bool False), 100 samples: holds in 0/100 (100 UNDEFINED by the guard)
- Same input evaluated twice gave the same answer (repeatable).
- Revisions of the fixed criterion: 0 (the faulty criterion was never run).

## 6. Timing
- t (mean of 50 calls of the fixed criterion on plus samples) = 0.052 ms; g (mean of 50 plus generations) = 0.042 ms
- S = 5 (2 worlds + 1 control + 0 premises + 0 relational pairs + 2 probes)
- Estimate 2 x 200 x (S + 1) x (t + g) = 0.2 s (limit 900 s)

## 7. Deviations, problems, skeleton requests
Private note said 'fixed block of rows'; I chose 150 train / 100 test and a least-squares classifier before looking at any rate. The fixed criterion holds in 0.933 of plus and 0.077 of minus (chance accuracy near the 0.70 base rate with 100 test rows; a feature of the skeleton's 30% prevalence, not changed). No skeleton request.
