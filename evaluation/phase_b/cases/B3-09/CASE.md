# B3-09 (W23)

## 1. Identity
Case id B3-09, world id W23, class B-3, subtype: none (B-2 subtypes only), source key KRO93.

## 2. Source and documenting passage
KRO93, abstract (IDEAS/RePEc): "The consequences of using a single ratio as either the dependent or one of the independent variables in a multiple-regression analysis are described. It is shown that the use of ratios in regression analyses can lead to incorrect or misleading inferences."

Who read it, and how: The earlier author read the abstract in full; the JSTOR full text was not read by anyone. The specific mechanisms (predictor correlated with the denominator, outcome related to the denominator) and the correction used here (ratio-free regression with the denominator as a covariate) are recalled from background knowledge of Kronmal's argument.

## 3. Brief (exactly as in ASSIGNMENT.json)
Claim: Larger hospitals have lower hospital-acquired infection rates per admission: across 100 hospitals, the standardised regression slope (variables z-scored) of infections per admission on the number of beds is at most -0.3.

```json
{
  "id": "W23",
  "claim": "Larger hospitals have lower hospital-acquired infection rates per admission: across 100 hospitals, the standardised regression slope (variables z-scored) of infections per admission on the number of beds is at most -0.3.",
  "data_keys": [
    {
      "key": "infections",
      "shape": "(hospitals,)",
      "dtype": "float",
      "meaning": "number of hospital-acquired infections recorded in one year"
    },
    {
      "key": "admissions",
      "shape": "(hospitals,)",
      "dtype": "float",
      "meaning": "number of patient admissions in the same year"
    },
    {
      "key": "beds",
      "shape": "(hospitals,)",
      "dtype": "float",
      "meaning": "number of staffed beds"
    }
  ],
  "sizes": "100 hospitals"
}
```

## 4. Mapping of the faulty and the fixed criterion
Faulty: standardised slope of infections per admission on beds (z-scored), threshold <= -0.3: a ratio as the dependent variable whose denominator (admissions) is proportional to the predictor, the situation Kronmal's abstract describes as leading to misleading inferences. Fixed: standardised coefficient of beds in the regression of infections on beds with admissions as a covariate (all z-scored), threshold <= -0.3: the ratio-free form.

## 5. Pre-checks of the fixed criterion (plain Python, never Truth_Gate, never the faulty file)
200 plus: holds 99 (0.495). 200 minus: 33 (0.165). Control permute_beds: 0/200. Noise probe: 0/200. Zeros probe: 5/5 UNDEFINED. Deterministic: yes. Samples drawn with numpy default_rng seeds (plus 1000.., minus 5000.., control 9000.., noise 13000..); script
work/precheck_fixed.py. Number of revisions of the fixed criterion: 1.

## 6. Timing
t = 0.072 ms (mean of 50 calls on plus samples), g = 0.035 ms (mean of 50 plus generations), S = 5 (2 worlds + 1 control + 0 premises
+ 0 relational pairs + 2 probes); estimate 2 x 200 x (S + 1) x (t + g) = 0.26 s (limit 900 s).

## 7. Deviations from the private note, problems, skeleton requests
One revision: np.errstate around the division. Observation, not a change: the fixed criterion fails in about half of plus and holds in 16.5% of minus. In the skeleton admissions are almost proportional to beds (log error 0.15), so the two covariates are highly collinear and the standardised coefficient of beds is very variable: mean -0.363 (sd 0.372) in plus and 0.008 (sd 0.316) in minus over 400 samples (work/estimates_fixed_stats.py), against a threshold of -0.3. Not bent. Skeleton requests: none.
