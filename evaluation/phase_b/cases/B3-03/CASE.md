# B3-03 (W53)

## 1. Identity
Case id B3-03, world id W53, class B-3, subtype: none (B-2 subtypes only), source key ARC81.

## 2. Source and documenting passage
ARC81, Europe PMC abstract (PMID 7212790): "Type 3, the most common type of mathematic coupling, is direct algebraic coupling between two variables, when one or more of the variables is derived and/or calculated."

Who read it, and how: The earlier author read the abstract in full on Europe PMC; the full text was not read by anyone. The clinical settings (Fick VO2/DO2, SVR and cardiac output, right-ventricular volume and ejection fraction, dobutamine) are applications of the documented principle recalled from background knowledge, not quotations of the abstract.

## 3. Brief (exactly as in ASSIGNMENT.json)
Claim: In patients with heart failure, a larger right ventricular end-diastolic volume goes with a lower right ventricular ejection fraction: across 30 patients, the standardised slope (both variables z-scored) of end-diastolic volume index on ejection fraction is at most -0.4.

```json
{
  "id": "W53",
  "claim": "In patients with heart failure, a larger right ventricular end-diastolic volume goes with a lower right ventricular ejection fraction: across 30 patients, the standardised slope (both variables z-scored) of end-diastolic volume index on ejection fraction is at most -0.4.",
  "data_keys": [
    {
      "key": "stroke_volume_index",
      "shape": "(patients,)",
      "dtype": "float",
      "meaning": "stroke volume index, mL/m2, from thermodilution"
    },
    {
      "key": "rvef",
      "shape": "(patients,)",
      "dtype": "float",
      "meaning": "right ventricular ejection fraction, fraction 0-1, from a fast-response thermistor catheter"
    },
    {
      "key": "rv_edv_index_radionuclide",
      "shape": "(patients,)",
      "dtype": "float",
      "meaning": "right ventricular end-diastolic volume index, mL/m2, from gated radionuclide ventriculography done in the same session"
    }
  ],
  "sizes": "30 patients"
}
```

## 4. Mapping of the faulty and the fixed criterion
Faulty: end-diastolic volume index computed as stroke volume index / rvef (both from the thermodilution catheter), then the standardised slope (both z-scored) of that volume on rvef, threshold <= -0.4. The volume contains the ejection fraction as its denominator and so shares its measurement error with the regressor (ARC81 type 3). Fixed: the same standardised slope and threshold using the radionuclide end-diastolic volume index, an independent measurement. The brief does not name which volume key the criterion must use; the faulty criterion uses the derived one, the fixed the independent one.

## 5. Pre-checks of the fixed criterion (plain Python, never Truth_Gate, never the faulty file)
200 plus: holds 170 (0.850). 200 minus: 1 (0.005). Control permute_radionuclide_volume: 2/200 (0.010). Noise probe: 1/200 (0.005). Zeros probe: 5/5 UNDEFINED. Deterministic: yes. Samples drawn with numpy default_rng seeds (plus 1000.., minus 5000.., control 9000.., noise 13000..); script
work/precheck_fixed.py. Number of revisions of the fixed criterion: 1.

## 6. Timing
t = 0.053 ms (mean of 50 calls on plus samples), g = 0.028 ms (mean of 50 plus generations), S = 5 (2 worlds + 1 control + 0 premises
+ 0 relational pairs + 2 probes); estimate 2 x 200 x (S + 1) x (t + g) = 0.19 s (limit 900 s).

## 7. Deviations from the private note, problems, skeleton requests
One revision: np.errstate around the division (see B3-02); no change in values. Skeleton requests: none.
