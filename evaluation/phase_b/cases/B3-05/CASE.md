# B3-05 (W01)

## 1. Identity
Case id B3-05, world id W01, class B-3, subtype: none (B-2 subtypes only), source key PEA97.

## 2. Source and documenting passage
PEA97 p. 490-491 (archive.org OCR copy of Proc. R. Soc. 60:489-498): "Form the proper fractions x/y and z/y for each triplet, and correlation will be found between these indices." For femur/humerus and tibia/humerus: "a correlation of about 0.4 to 0.5 between these indices had the bones been sorted absolutely at random."

Who read it, and how: The earlier author read the full text of Pearson 1897 via the archive.org OCR copy (saved in src/pea.txt; I re-checked the quoted lines there). The settings other than skeletal indices are later applications of Proposition III recalled from background knowledge, not in Pearson 1897.

## 3. Brief (exactly as in ASSIGNMENT.json)
Claim: Across 120 adult human skeletons, femur length relative to vertebral column length and tibia length relative to vertebral column length are positively related: the Pearson correlation between the two relative lengths is at least 0.4.

```json
{
  "id": "W01",
  "claim": "Across 120 adult human skeletons, femur length relative to vertebral column length and tibia length relative to vertebral column length are positively related: the Pearson correlation between the two relative lengths is at least 0.4.",
  "data_keys": [
    {
      "key": "femur_length",
      "shape": "(skeletons,)",
      "dtype": "float",
      "meaning": "maximum femur length, mm"
    },
    {
      "key": "tibia_length",
      "shape": "(skeletons,)",
      "dtype": "float",
      "meaning": "maximum tibia length, mm"
    },
    {
      "key": "vertebral_column_length",
      "shape": "(skeletons,)",
      "dtype": "float",
      "meaning": "length of the articulated vertebral column, mm"
    }
  ],
  "sizes": "120 skeletons"
}
```

## 4. Mapping of the faulty and the fixed criterion
Faulty: Pearson correlation between femur/vertebral-column-length and tibia/vertebral-column-length, threshold >= 0.4. With independent absolute lengths and a varying common denominator the index correlation is about 0.4 to 0.5 at equal coefficients of variation (documented in Pearson 1897; here the humerus of the paper is replaced by the vertebral column, same structure). Fixed: Pearson partial correlation of femur and tibia lengths holding vertebral column length fixed (the partial correlation is the standard correction), same threshold 0.4. Scale: raw values, as in the faulty criterion.

## 5. Pre-checks of the fixed criterion (plain Python, never Truth_Gate, never the faulty file)
200 plus: holds 200 (1.000). 200 minus: 34 (0.170). Control permute_tibia: 0/200. Noise probe: 0/200. Zeros probe: 5/5 UNDEFINED. Deterministic: yes. Samples drawn with numpy default_rng seeds (plus 1000.., minus 5000.., control 9000.., noise 13000..); script
work/precheck_fixed.py. Number of revisions of the fixed criterion: 1.

## 6. Timing
t = 0.086 ms (mean of 50 calls on plus samples), g = 0.026 ms (mean of 50 plus generations), S = 5 (2 worlds + 1 control + 0 premises
+ 0 relational pairs + 2 probes); estimate 2 x 200 x (S + 1) x (t + g) = 0.27 s (limit 900 s).

## 7. Deviations from the private note, problems, skeleton requests
One revision: np.errstate around the divisions (no change in values). Observation, not a change: in minus the fixed criterion holds in 17% of samples. The skeleton keeps a shared body-size factor and a noisy shared column length in minus, so even the partial correlation leaves a residual correlation (mean partial correlation 0.317, sd 0.083 over 400 minus samples, descriptive script work/estimates_fixed_stats.py), not far below the 0.4 threshold. Not bent. Skeleton requests: none.
