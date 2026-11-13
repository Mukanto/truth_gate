# B3-11 (W02)

## 1. Identity
Case id B3-11, world id W02, class B-3, subtype: none (B-2 subtypes only), source key KRO93.

## 2. Source and documenting passage
KRO93, abstract (IDEAS/RePEc): "The consequences of using a single ratio as either the dependent or one of the independent variables in a multiple-regression analysis are described. It is shown that the use of ratios in regression analyses can lead to incorrect or misleading inferences."

Who read it, and how: The earlier author read the abstract in full; the JSTOR full text was not read by anyone. The specific mechanisms (predictor correlated with the denominator, outcome related to the denominator) and the correction used here (ratio-free regression with the denominator as a covariate) are recalled from background knowledge of Kronmal's argument.

## 3. Brief (exactly as in ASSIGNMENT.json)
Claim: Buildings with more occupants use less energy per square metre of floor area: across 150 office buildings, the Spearman rank correlation between the number of occupants and annual energy use per square metre is at most -0.3.

```json
{
  "id": "W02",
  "claim": "Buildings with more occupants use less energy per square metre of floor area: across 150 office buildings, the Spearman rank correlation between the number of occupants and annual energy use per square metre is at most -0.3.",
  "data_keys": [
    {
      "key": "energy_use",
      "shape": "(buildings,)",
      "dtype": "float",
      "meaning": "annual metered energy use, MWh"
    },
    {
      "key": "floor_area",
      "shape": "(buildings,)",
      "dtype": "float",
      "meaning": "gross floor area, square metres"
    },
    {
      "key": "occupants",
      "shape": "(buildings,)",
      "dtype": "float",
      "meaning": "typical number of occupants (headcount)"
    }
  ],
  "sizes": "150 buildings"
}
```

## 4. Mapping of the faulty and the fixed criterion
Faulty: Spearman correlation of occupants with energy use per square metre, threshold <= -0.3: a ratio with the floor-area denominator as outcome, while occupants grow with floor area (Kronmal 1993, ratio as dependent variable; the Spearman form and the building setting are this project's application). Fixed: Spearman partial correlation (partial correlation of the ranks) of energy_use and occupants holding floor_area fixed, same threshold -0.3.

## 5. Pre-checks of the fixed criterion (plain Python, never Truth_Gate, never the faulty file)
200 plus: holds 1 (0.005). 200 minus: 0. Control permute_occupants: 0/200. Noise probe: 0/200. Zeros probe: 5/5 UNDEFINED. Deterministic: yes. Samples drawn with numpy default_rng seeds (plus 1000.., minus 5000.., control 9000.., noise 13000..); script
work/precheck_fixed.py. Number of revisions of the fixed criterion: 1.

## 6. Timing
t = 0.213 ms (mean of 50 calls on plus samples), g = 0.039 ms (mean of 50 plus generations), S = 5 (2 worlds + 1 control + 0 premises
+ 0 relational pairs + 2 probes); estimate 2 x 200 x (S + 1) x (t + g) = 0.60 s (limit 900 s).

## 7. Deviations from the private note, problems, skeleton requests
One revision: np.errstate around the division. Deviation from the note: ranks instead of logs (logs undefined on noise-probe data). Observation, not a change: the fixed criterion almost never holds in plus. In the skeleton the direct occupant effect on intensity is -0.12 log units per sd, so the partial rank correlation after holding area fixed has mean -0.125 (sd 0.090 over 400 plus samples; work/estimates_fixed_stats.py), well short of -0.3; most of the faulty statistic's strength in plus comes from the area-driven scale effect and the occupants-area link, which the skeleton also keeps in minus. This is the largest skeleton-side limit in the set: the correction cannot hold in plus. No skeleton request filed (the criterion could be written); the designer may want to know. Skeleton requests: none.
