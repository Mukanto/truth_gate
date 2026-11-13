# CASE O1b

## 1. Identification
- Case id: O1b
- World id: W33
- Class: O (out of scope); subtype assigned by the designer: O-1

## 2. Source and documented error
- Source key: KAP23
- Passage: KAP23, section 2.4, type L1.2: "Using the entire dataset for any pre-processing steps such as imputation or over/under sampling." The paper's example is label-dependent; the label-free variant (standardisation and PCA on all rows) is the one used here, per the O-1 class definition in PREREG section 1 ("scaling, unsupervised imputation, PCA on all data").
- Reading: Read by the earlier author (phase 1), ar5iv full text of section 2.4. Not re-read by the phase 2 author.

## 3. Brief (exactly as in ASSIGNMENT.json)
```json
{
  "id": "W33",
  "claim": "Using the leading principal components of the tumour expression profile, a nearest-centroid classifier tells responders from non-responders with an accuracy of at least 0.70 on new tumours (the claim holds when the accuracy estimate is >= 0.70).",
  "data_keys": [
    {
      "key": "expr",
      "shape": "(tumours, 60)",
      "dtype": "float",
      "meaning": "log expression of 60 genes per tumour, on arbitrary instrument scales"
    },
    {
      "key": "responder",
      "shape": "(tumours,)",
      "dtype": "bool",
      "meaning": "True if the tumour responded to the drug"
    }
  ],
  "sizes": "120 tumours; 60 genes"
}
```

## 4. Mapping of the criteria to the documented error and its correction
Faulty: every gene is standardised and a PCA (top 5 components, SVD) is fitted on all 120 tumours, train and test rows together; a nearest-centroid classifier (Euclidean, in the 5-component space) is fitted on the first 72 tumours and scored on the remaining 48; the claim holds when accuracy >= 0.70. This is the label-free pre-processing leak: the test rows influence the means, scales and axes. Parameters: 5 components is the private note's value (the brief says 'leading principal components' and does not give a number; the source documents no values); 72/48 split is my choice. Fixed: the standardisation and the PCA are fitted on the 72 training rows only and applied to the test rows; everything else is identical.

## 5. Pre-checks of the fixed criterion (plain Python, work/precheck_fixed.py, seed 777)
- plus: holds in 261/300 (0.870)
- minus: holds in 2/300 (0.007)
- declared control (applied to plus samples): holds in 1/300 (0.003)
- my approximation of the noise probe (float arrays N(0,1), bool arrays fair coin), 100 samples: holds in 0/100
- zero probe (all-zero arrays, bool False), 100 samples: holds in 0/100 (100 UNDEFINED by the guard)
- Same input evaluated twice gave the same answer (repeatable).
- Revisions of the fixed criterion: 0 (the faulty criterion was never run).

## 6. Timing
- t (mean of 50 calls of the fixed criterion on plus samples) = 1.164 ms; g (mean of 50 plus generations) = 0.088 ms
- S = 5 (2 worlds + 1 control + 0 premises + 0 relational pairs + 2 probes)
- Estimate 2 x 200 x (S + 1) x (t + g) = 3.0 s (limit 900 s)

## 7. Deviations, problems, skeleton requests
Private note gave no split; I chose 72/48 (60/40, as in O1a) before looking at any rate. Expected invisible effect as the note says. No skeleton request.
