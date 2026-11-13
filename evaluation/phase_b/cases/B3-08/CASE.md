# B3-08 (W24)

## 1. Identity
Case id B3-08, world id W24, class B-3, subtype: none (B-2 subtypes only), source key PEA97.

## 2. Source and documenting passage
PEA97, Proposition III (OCR copy; section (4) 'To find the coefficient of correlation of two indices'): the OCR text reads "The particular case that if likely to occur is when u and v are indices with the same denominator" (sic, OCR 'if' for 'is'); the formula is given for x1/x3 and x2/x3.

Who read it, and how: The earlier author read the full text of Pearson 1897 via the archive.org OCR copy (saved in src/pea.txt; I re-checked the quoted lines there). The settings other than skeletal indices are later applications of Proposition III recalled from background knowledge, not in Pearson 1897.

## 3. Brief (exactly as in ASSIGNMENT.json)
Claim: In trained athletes, aerobic capacity per kilogram of body mass goes with sprint power per kilogram of body mass: across 30 athletes, the proportion of variance in peak power per kilogram explained by maximal oxygen uptake per kilogram (R squared of a simple linear regression) is at least 0.25.

```json
{
  "id": "W24",
  "claim": "In trained athletes, aerobic capacity per kilogram of body mass goes with sprint power per kilogram of body mass: across 30 athletes, the proportion of variance in peak power per kilogram explained by maximal oxygen uptake per kilogram (R squared of a simple linear regression) is at least 0.25.",
  "data_keys": [
    {
      "key": "vo2max",
      "shape": "(athletes,)",
      "dtype": "float",
      "meaning": "maximal oxygen uptake, L/min, from an incremental treadmill test"
    },
    {
      "key": "peak_power",
      "shape": "(athletes,)",
      "dtype": "float",
      "meaning": "peak power output in a 10-second cycle sprint, W"
    },
    {
      "key": "body_mass",
      "shape": "(athletes,)",
      "dtype": "float",
      "meaning": "body mass, kg"
    }
  ],
  "sizes": "30 athletes"
}
```

## 4. Mapping of the faulty and the fixed criterion
Faulty: R squared of the simple regression of peak power per kg on maximal oxygen uptake per kg, threshold >= 0.25; both ratios share the body-mass denominator and both fall with body size (Pearson's Proposition III; the body-mass setting is a later application). Fixed: squared partial correlation of peak_power and vo2max holding body_mass fixed, same threshold 0.25 and the same unsigned R squared.

## 5. Pre-checks of the fixed criterion (plain Python, never Truth_Gate, never the faulty file)
200 plus: holds 113 (0.565). 200 minus: 3 (0.015). Control permute_power_per_kg: 3/200 (0.015). Noise probe: 0/200. Zeros probe: 5/5 UNDEFINED. Deterministic: yes. Samples drawn with numpy default_rng seeds (plus 1000.., minus 5000.., control 9000.., noise 13000..); script
work/precheck_fixed.py. Number of revisions of the fixed criterion: 1.

## 6. Timing
t = 0.088 ms (mean of 50 calls on plus samples), g = 0.023 ms (mean of 50 plus generations), S = 5 (2 worlds + 1 control + 0 premises
+ 0 relational pairs + 2 probes); estimate 2 x 200 x (S + 1) x (t + g) = 0.27 s (limit 900 s).

## 7. Deviations from the private note, problems, skeleton requests
One revision: np.errstate around the divisions. Observation, not a change: the fixed criterion fails in 43% of plus samples. In the skeleton the size-independent correlation in plus is 0.5, so the squared partial correlation has mean 0.267 (sd 0.138 over 400 samples), about at the threshold; many samples fall below it. Not bent. Skeleton requests: none.
