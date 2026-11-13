# B3-12 (W11)

## 1. Identity
Case id B3-12, world id W11, class B-3, subtype: none (B-2 subtypes only), source key KRO93.

## 2. Source and documenting passage
KRO93, abstract (IDEAS/RePEc): "The consequences of using a single ratio as either the dependent or one of the independent variables in a multiple-regression analysis are described. It is shown that the use of ratios in regression analyses can lead to incorrect or misleading inferences."

Who read it, and how: The earlier author read the abstract in full; the JSTOR full text was not read by anyone. The specific mechanisms (predictor correlated with the denominator, outcome related to the denominator) and the correction used here (ratio-free regression with the denominator as a covariate) are recalled from background knowledge of Kronmal's argument.

## 3. Brief (exactly as in ASSIGNMENT.json)
Claim: Firms with a larger payroll have lower staff turnover rates: across 250 firms, the proportion of variance in the annual turnover rate (leavers per employee) explained by the payroll (R squared of a simple linear regression) is at least 0.1.

```json
{
  "id": "W11",
  "claim": "Firms with a larger payroll have lower staff turnover rates: across 250 firms, the proportion of variance in the annual turnover rate (leavers per employee) explained by the payroll (R squared of a simple linear regression) is at least 0.1.",
  "data_keys": [
    {
      "key": "leavers",
      "shape": "(firms,)",
      "dtype": "float",
      "meaning": "number of employees who left the firm during the year"
    },
    {
      "key": "headcount",
      "shape": "(firms,)",
      "dtype": "float",
      "meaning": "average number of employees during the year"
    },
    {
      "key": "payroll",
      "shape": "(firms,)",
      "dtype": "float",
      "meaning": "total annual payroll, millions of currency units"
    }
  ],
  "sizes": "250 firms"
}
```

## 4. Mapping of the faulty and the fixed criterion
Faulty: R squared of the simple regression of the turnover rate (leavers / headcount) on payroll, threshold >= 0.1: ratio outcome whose denominator (headcount) grows with the predictor (Kronmal 1993; the firm setting and R squared are this project's application). Fixed: partial R squared of payroll in the regression of leavers on payroll and headcount (squared partial correlation of leavers and payroll holding headcount fixed), threshold >= 0.1.

## 5. Pre-checks of the fixed criterion (plain Python, never Truth_Gate, never the faulty file)
200 plus: holds 1 (0.005). 200 minus: 7 (0.035). Control permute_payroll: 0/200. Noise probe: 0/200. Zeros probe: 5/5 UNDEFINED. Deterministic: yes. Samples drawn with numpy default_rng seeds (plus 1000.., minus 5000.., control 9000.., noise 13000..); script
work/precheck_fixed.py. Number of revisions of the fixed criterion: 1.

## 6. Timing
t = 0.098 ms (mean of 50 calls on plus samples), g = 0.048 ms (mean of 50 plus generations), S = 5 (2 worlds + 1 control + 0 premises
+ 0 relational pairs + 2 probes); estimate 2 x 200 x (S + 1) x (t + g) = 0.35 s (limit 900 s).

## 7. Deviations from the private note, problems, skeleton requests
One revision: np.errstate around the division. Observation, not a change: the fixed criterion almost never holds in plus. In the skeleton the true rate depends on headcount only, and payroll is headcount x a wage that is independent of the rate, so payroll carries no information about leavers beyond headcount even in plus (partial R squared mean 0.012, sd 0.020 over 400 plus samples); the claim is true in plus only through the denominator. No correction in Kronmal's ratio-free form can hold in plus. No skeleton request filed (the criterion could be written); the designer may want to know. Skeleton requests: none.
