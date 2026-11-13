# B3-04 (W45)

## 1. Identity
Case id B3-04, world id W45, class B-3, subtype: none (B-2 subtypes only), source key ARC81.

## 2. Source and documenting passage
ARC81, Europe PMC abstract (PMID 7212790): "Type 1 coupling involves directional changes in two variables which are mathematically coupled." (together with the Type 2 sentence on common component variables)

Who read it, and how: The earlier author read the abstract in full on Europe PMC; the full text was not read by anyone. The clinical settings (Fick VO2/DO2, SVR and cardiac output, right-ventricular volume and ejection fraction, dobutamine) are applications of the documented principle recalled from background knowledge, not quotations of the abstract.

## 3. Brief (exactly as in ASSIGNMENT.json)
Claim: A dobutamine infusion in critically ill adults raises oxygen consumption in proportion to the rise in oxygen delivery: across 24 patients, the proportion of variance in the change in oxygen consumption explained by the change in oxygen delivery (R squared of a simple linear regression) is at least 0.25.

```json
{
  "id": "W45",
  "claim": "A dobutamine infusion in critically ill adults raises oxygen consumption in proportion to the rise in oxygen delivery: across 24 patients, the proportion of variance in the change in oxygen consumption explained by the change in oxygen delivery (R squared of a simple linear regression) is at least 0.25.",
  "data_keys": [
    {
      "key": "cardiac_output",
      "shape": "(patients, 2)",
      "dtype": "float",
      "meaning": "cardiac output, L/min, by thermodilution; axis 1 = [before infusion, during infusion]"
    },
    {
      "key": "hemoglobin",
      "shape": "(patients, 2)",
      "dtype": "float",
      "meaning": "blood hemoglobin concentration, g/dL; axis 1 = [before, during]"
    },
    {
      "key": "sao2",
      "shape": "(patients, 2)",
      "dtype": "float",
      "meaning": "arterial oxygen saturation, fraction 0-1; axis 1 = [before, during]"
    },
    {
      "key": "svo2",
      "shape": "(patients, 2)",
      "dtype": "float",
      "meaning": "mixed venous oxygen saturation, fraction 0-1; axis 1 = [before, during]"
    },
    {
      "key": "vo2_expired",
      "shape": "(patients, 2)",
      "dtype": "float",
      "meaning": "oxygen consumption, mL/min, from expired-gas analysis; axis 1 = [before, during]"
    }
  ],
  "sizes": "24 patients, 2 time points each"
}
```

## 4. Mapping of the faulty and the fixed criterion
Faulty: per patient, change in consumption (Fick, from CO, Hb, SaO2, SvO2) and change in delivery (from CO, Hb, SaO2) between before and during infusion; R squared of the simple regression of the first on the second, threshold >= 0.25. The two change scores contain the same changes in cardiac output, haemoglobin and saturation (ARC81 type 1 and type 2 coupling of changes). Fixed: same R squared and threshold with the change in the independently measured vo2_expired in place of the Fick change.

## 5. Pre-checks of the fixed criterion (plain Python, never Truth_Gate, never the faulty file)
200 plus: holds 180 (0.900). 200 minus: 2 (0.010). Control permute_vo2_expired: 3/200 (0.015). Noise probe: 2/200 (0.010). Zeros probe: 5/5 UNDEFINED. Deterministic: yes. Samples drawn with numpy default_rng seeds (plus 1000.., minus 5000.., control 9000.., noise 13000..); script
work/precheck_fixed.py. Number of revisions of the fixed criterion: 0.

## 6. Timing
t = 0.044 ms (mean of 50 calls on plus samples), g = 0.073 ms (mean of 50 plus generations), S = 5 (2 worlds + 1 control + 0 premises
+ 0 relational pairs + 2 probes); estimate 2 x 200 x (S + 1) x (t + g) = 0.28 s (limit 900 s).

## 7. Deviations from the private note, problems, skeleton requests
None. Skeleton requests: none.
