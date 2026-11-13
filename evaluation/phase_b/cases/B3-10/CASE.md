# B3-10 (W51)

## 1. Identity
Case id B3-10, world id W51, class B-3, subtype: none (B-2 subtypes only), source key KRO93.

## 2. Source and documenting passage
KRO93, abstract (IDEAS/RePEc): "The consequences of using a single ratio as either the dependent or one of the independent variables in a multiple-regression analysis are described. It is shown that the use of ratios in regression analyses can lead to incorrect or misleading inferences."

Who read it, and how: The earlier author read the abstract in full; the JSTOR full text was not read by anyone. The specific mechanisms (predictor correlated with the denominator, outcome related to the denominator) and the correction used here (ratio-free regression with the denominator as a covariate) are recalled from background knowledge of Kronmal's argument.

## 3. Brief (exactly as in ASSIGNMENT.json)
Claim: In adult rats, a heavier heart relative to body weight goes with higher systolic blood pressure: across 60 rats, the standardised regression slope (variables z-scored) of systolic pressure on heart weight per body weight is at least 0.3.

```json
{
  "id": "W51",
  "claim": "In adult rats, a heavier heart relative to body weight goes with higher systolic blood pressure: across 60 rats, the standardised regression slope (variables z-scored) of systolic pressure on heart weight per body weight is at least 0.3.",
  "data_keys": [
    {
      "key": "systolic_pressure",
      "shape": "(rats,)",
      "dtype": "float",
      "meaning": "systolic blood pressure, mmHg, by tail-cuff"
    },
    {
      "key": "heart_weight",
      "shape": "(rats,)",
      "dtype": "float",
      "meaning": "wet heart weight at necropsy, g"
    },
    {
      "key": "body_weight",
      "shape": "(rats,)",
      "dtype": "float",
      "meaning": "body weight at necropsy, g"
    }
  ],
  "sizes": "60 rats"
}
```

## 4. Mapping of the faulty and the fixed criterion
Faulty: standardised slope of systolic pressure on heart weight / body weight (z-scored), threshold >= 0.3: a ratio as predictor whose denominator (body weight) itself drives the outcome, so the ratio carries the body-weight effect (Kronmal 1993, ratio as an independent variable). Fixed: standardised coefficient of heart_weight in the regression of pressure on heart weight with body weight as a covariate, threshold >= 0.3.

## 5. Pre-checks of the fixed criterion (plain Python, never Truth_Gate, never the faulty file)
200 plus: holds 200 (1.000). 200 minus: 5 (0.025). Control permute_relative_heart_weight: 7/200 (0.035). Noise probe: 3/200 (0.015). Zeros probe: 5/5 UNDEFINED. Deterministic: yes. Samples drawn with numpy default_rng seeds (plus 1000.., minus 5000.., control 9000.., noise 13000..); script
work/precheck_fixed.py. Number of revisions of the fixed criterion: 1.

## 6. Timing
t = 0.071 ms (mean of 50 calls on plus samples), g = 0.018 ms (mean of 50 plus generations), S = 5 (2 worlds + 1 control + 0 premises
+ 0 relational pairs + 2 probes); estimate 2 x 200 x (S + 1) x (t + g) = 0.21 s (limit 900 s).

## 7. Deviations from the private note, problems, skeleton requests
One revision: np.errstate around the division; no change in values. Skeleton requests: none.
