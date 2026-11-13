# B3-02 (W26)

## 1. Identity
Case id B3-02, world id W26, class B-3, subtype: none (B-2 subtypes only), source key ARC81.

## 2. Source and documenting passage
ARC81, Europe PMC abstract (PMID 7212790): "Type 3, the most common type of mathematic coupling, is direct algebraic coupling between two variables, when one or more of the variables is derived and/or calculated."

Who read it, and how: The earlier author read the abstract in full on Europe PMC; the full text was not read by anyone. The clinical settings (Fick VO2/DO2, SVR and cardiac output, right-ventricular volume and ejection fraction, dobutamine) are applications of the documented principle recalled from background knowledge, not quotations of the abstract.

## 3. Brief (exactly as in ASSIGNMENT.json)
Claim: In critically ill adults, systemic vascular resistance falls as cardiac output rises: across 100 patients, the Spearman rank correlation between systemic vascular resistance and cardiac output is at most -0.4.

```json
{
  "id": "W26",
  "claim": "In critically ill adults, systemic vascular resistance falls as cardiac output rises: across 100 patients, the Spearman rank correlation between systemic vascular resistance and cardiac output is at most -0.4.",
  "data_keys": [
    {
      "key": "map",
      "shape": "(patients,)",
      "dtype": "float",
      "meaning": "mean arterial pressure, mmHg"
    },
    {
      "key": "cvp",
      "shape": "(patients,)",
      "dtype": "float",
      "meaning": "central venous pressure, mmHg"
    },
    {
      "key": "co_thermodilution",
      "shape": "(patients,)",
      "dtype": "float",
      "meaning": "cardiac output, L/min, by pulmonary-artery thermodilution"
    },
    {
      "key": "co_doppler",
      "shape": "(patients,)",
      "dtype": "float",
      "meaning": "cardiac output, L/min, by echocardiographic Doppler, measured at the same time by a separate operator"
    }
  ],
  "sizes": "100 patients"
}
```

## 4. Mapping of the faulty and the fixed criterion
Faulty: SVR = 80 x (MAP - CVP) / CO_thermodilution, then Spearman rank correlation of SVR with the same thermodilution output (threshold <= -0.4). The output measured with error appears in the denominator of the derived variable and again as the other variable (ARC81 type 3, direct algebraic coupling), so error in CO produces a negative association by itself. Fixed: same SVR (from thermodilution CO), same Spearman statistic and threshold, correlated with the separately measured Doppler output co_doppler, whose error is independent.

## 5. Pre-checks of the fixed criterion (plain Python, never Truth_Gate, never the faulty file)
200 plus: holds 198 (0.990). 200 minus: 0. Control permute_resistance: 0/200. Noise probe: 0/200. Zeros probe: 5/5 UNDEFINED. Deterministic: yes. Samples drawn with numpy default_rng seeds (plus 1000.., minus 5000.., control 9000.., noise 13000..); script
work/precheck_fixed.py. Number of revisions of the fixed criterion: 1.

## 6. Timing
t = 0.083 ms (mean of 50 calls on plus samples), g = 0.032 ms (mean of 50 plus generations), S = 5 (2 worlds + 1 control + 0 premises
+ 0 relational pairs + 2 probes); estimate 2 x 200 x (S + 1) x (t + g) = 0.28 s (limit 900 s).

## 7. Deviations from the private note, problems, skeleton requests
One revision after the first pre-check: the division is wrapped in np.errstate (RuntimeWarning on 0/0 in the zeros probe). No change of values or decisions (rates identical before and after). Skeleton requests: none.
