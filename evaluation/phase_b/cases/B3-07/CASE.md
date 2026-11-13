# B3-07 (W43)

## 1. Identity
Case id B3-07, world id W43, class B-3, subtype: none (B-2 subtypes only), source key PEA97.

## 2. Source and documenting passage
PEA97, Proposition III (OCR copy; section (4) 'To find the coefficient of correlation of two indices'): the OCR text reads "The particular case that if likely to occur is when u and v are indices with the same denominator" (sic, OCR 'if' for 'is'); the formula is given for x1/x3 and x2/x3.

Who read it, and how: The earlier author read the full text of Pearson 1897 via the archive.org OCR copy (saved in src/pea.txt; I re-checked the quoted lines there). The settings other than skeletal indices are later applications of Proposition III recalled from background knowledge, not in Pearson 1897.

## 3. Brief (exactly as in ASSIGNMENT.json)
Claim: Across 90 farms, a farm that applies more fertilizer per hectare obtains a higher crop yield per hectare: the standardised regression slope (both variables z-scored) of yield per hectare on fertilizer per hectare is at least 0.3.

```json
{
  "id": "W43",
  "claim": "Across 90 farms, a farm that applies more fertilizer per hectare obtains a higher crop yield per hectare: the standardised regression slope (both variables z-scored) of yield per hectare on fertilizer per hectare is at least 0.3.",
  "data_keys": [
    {
      "key": "yield_total",
      "shape": "(farms,)",
      "dtype": "float",
      "meaning": "total annual crop harvest of the farm, tonnes"
    },
    {
      "key": "fertilizer_total",
      "shape": "(farms,)",
      "dtype": "float",
      "meaning": "total annual fertilizer applied on the farm, kg of nitrogen"
    },
    {
      "key": "farm_area",
      "shape": "(farms,)",
      "dtype": "float",
      "meaning": "cropped area of the farm, hectares"
    }
  ],
  "sizes": "90 farms"
}
```

## 4. Mapping of the faulty and the fixed criterion
Faulty: standardised slope (both z-scored) of yield per hectare on fertilizer per hectare, threshold >= 0.3, both ratios built from totals divided by the same recorded area (shared denominator and its recorded error; Pearson's Proposition III applied to a regression). Fixed: standardised partial coefficient of fertilizer_total in the regression of yield_total on fertilizer_total and farm_area (all three z-scored, ordinary least squares with intercept), threshold 0.3: the ratio-free form with the denominator as covariate, in raw units as the faulty criterion.

## 5. Pre-checks of the fixed criterion (plain Python, never Truth_Gate, never the faulty file)
200 plus: holds 145 (0.725). 200 minus: 31 (0.155). Control permute_yield_per_hectare: 13/200 (0.065). Noise probe: 0/200. Zeros probe: 5/5 UNDEFINED. Deterministic: yes. Samples drawn with numpy default_rng seeds (plus 1000.., minus 5000.., control 9000.., noise 13000..); script
work/precheck_fixed.py. Number of revisions of the fixed criterion: 1.

## 6. Timing
t = 0.072 ms (mean of 50 calls on plus samples), g = 0.021 ms (mean of 50 plus generations), S = 5 (2 worlds + 1 control + 0 premises
+ 0 relational pairs + 2 probes); estimate 2 x 200 x (S + 1) x (t + g) = 0.22 s (limit 900 s).

## 7. Deviations from the private note, problems, skeleton requests
One revision: np.errstate around the divisions. Observation, not a change: the fixed criterion fails in 27% of plus samples and holds in 15.5% of minus samples. The skeleton records the area with a 15% error, so the total fertilizer acts as a second proxy of the true area and the coefficient keeps a positive residual in minus; the fixed statistic over 400 samples has mean 0.390 (sd 0.148) in plus and 0.078 (sd 0.175) in minus (work/estimates_fixed_stats.py), against the 0.3 threshold. Not bent. Skeleton requests: none.
