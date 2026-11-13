# B3-01 (W29)

## 1. Identity
Case id B3-01, world id W29, class B-3, subtype: none (B-2 subtypes only), source key ARC81.

## 2. Source and documenting passage
ARC81, Europe PMC abstract (PMID 7212790): "Type 2 coupling is the functional relationship between two calculated variables which have one or more common component variables." "The common problem in each type of mathematic coupling is that one variable either directly or indirectly contains the whole or components of the second variable."

Who read it, and how: The earlier author read the abstract in full on Europe PMC; the full text was not read by anyone. The clinical settings (Fick VO2/DO2, SVR and cardiac output, right-ventricular volume and ejection fraction, dobutamine) are applications of the documented principle recalled from background knowledge, not quotations of the abstract.

## 3. Brief (exactly as in ASSIGNMENT.json)
Claim: In critically ill adults, oxygen consumption rises with oxygen delivery: across 40 patients, the Pearson correlation between oxygen consumption and oxygen delivery is at least 0.5.

```json
{
  "id": "W29",
  "claim": "In critically ill adults, oxygen consumption rises with oxygen delivery: across 40 patients, the Pearson correlation between oxygen consumption and oxygen delivery is at least 0.5.",
  "data_keys": [
    {
      "key": "cardiac_output",
      "shape": "(patients,)",
      "dtype": "float",
      "meaning": "cardiac output, L/min, from thermodilution"
    },
    {
      "key": "hemoglobin",
      "shape": "(patients,)",
      "dtype": "float",
      "meaning": "blood hemoglobin concentration, g/dL"
    },
    {
      "key": "sao2",
      "shape": "(patients,)",
      "dtype": "float",
      "meaning": "arterial oxygen saturation, fraction 0-1"
    },
    {
      "key": "svo2",
      "shape": "(patients,)",
      "dtype": "float",
      "meaning": "mixed venous oxygen saturation, fraction 0-1"
    },
    {
      "key": "vo2_expired",
      "shape": "(patients,)",
      "dtype": "float",
      "meaning": "oxygen consumption, mL/min, measured by expired-gas analysis at the same time as the haemodynamic measurements"
    }
  ],
  "sizes": "40 patients"
}
```

## 4. Mapping of the faulty and the fixed criterion
Faulty: oxygen consumption is obtained by the Fick calculation VO2 = CO x Hb x 13.4 x (SaO2 - SvO2) (13.4 = 1.34 mL O2 per g Hb x 10; the standard constant) and Pearson-correlated with delivery DO2 = CO x Hb x 13.4 x SaO2, threshold r >= 0.5 as in the brief. The two derived variables contain the same measured components (cardiac output, haemoglobin, SaO2) and so share their measurement errors: the type 2 coupling of ARC81 (common component variables). Fixed: the same Pearson statistic and threshold, with consumption taken from the independently measured expired-gas value vo2_expired, whose error is not shared with the delivery terms (the correction named in the earlier author's note); the Fick lines are the only thing removed.

## 5. Pre-checks of the fixed criterion (plain Python, never Truth_Gate, never the faulty file)
200 plus samples: holds 190 (0.950). 200 minus: 0 (0.000). Control permute_vo2_expired on plus: 0/200. Noise probe (i.i.d. N(0,1), same shapes): 0/200. Zeros probe: 5/5 UNDEFINED (None, zero variance guard). Deterministic: yes. Samples drawn with numpy default_rng seeds (plus 1000.., minus 5000.., control 9000.., noise 13000..); script
work/precheck_fixed.py. Number of revisions of the fixed criterion: 0.

## 6. Timing
t = 0.040 ms (mean of 50 calls on plus samples), g = 0.053 ms (mean of 50 plus generations), S = 5 (2 worlds + 1 control + 0 premises
+ 0 relational pairs + 2 probes); estimate 2 x 200 x (S + 1) x (t + g) = 0.22 s (limit 900 s).

## 7. Deviations from the private note, problems, skeleton requests
None. Skeleton requests: none.
