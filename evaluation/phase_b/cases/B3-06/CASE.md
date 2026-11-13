# B3-06 (W17)

## 1. Identity
Case id B3-06, world id W17, class B-3, subtype: none (B-2 subtypes only), source key PEA97.

## 2. Source and documenting passage
PEA97, Proposition III (OCR copy; section (4) 'To find the coefficient of correlation of two indices'): the OCR text reads "The particular case that if likely to occur is when u and v are indices with the same denominator" (sic, OCR 'if' for 'is'); the formula is given for x1/x3 and x2/x3.

Who read it, and how: The earlier author read the full text of Pearson 1897 via the archive.org OCR copy (saved in src/pea.txt; I re-checked the quoted lines there). The settings other than skeletal indices are later applications of Proposition III recalled from background knowledge, not in Pearson 1897.

## 3. Brief (exactly as in ASSIGNMENT.json)
Claim: Wealthier countries emit more carbon dioxide per person: across 150 countries, the Spearman rank correlation between per-capita carbon dioxide emissions and per-capita gross domestic product is at least 0.5.

```json
{
  "id": "W17",
  "claim": "Wealthier countries emit more carbon dioxide per person: across 150 countries, the Spearman rank correlation between per-capita carbon dioxide emissions and per-capita gross domestic product is at least 0.5.",
  "data_keys": [
    {
      "key": "co2_emissions_total",
      "shape": "(countries,)",
      "dtype": "float",
      "meaning": "annual national carbon dioxide emissions, megatonnes"
    },
    {
      "key": "gdp_total",
      "shape": "(countries,)",
      "dtype": "float",
      "meaning": "national gross domestic product, billions of US dollars (purchasing-power adjusted)"
    },
    {
      "key": "population",
      "shape": "(countries,)",
      "dtype": "float",
      "meaning": "national population, millions"
    }
  ],
  "sizes": "150 countries"
}
```

## 4. Mapping of the faulty and the fixed criterion
Faulty: Spearman rank correlation of per-capita emissions (total / population) with per-capita GDP (total / population), threshold >= 0.5. Both indices share the population denominator (Pearson's Proposition III; the per-capita economic setting is a later application). Fixed: Spearman partial correlation (partial correlation of the ranks) of the two totals holding the rank of population fixed, same threshold 0.5. The earlier note proposed logs; ranks are used instead because logs of N(0,1) noise-probe data are undefined and would make the fixed criterion UNDEFINED under the probe.

## 5. Pre-checks of the fixed criterion (plain Python, never Truth_Gate, never the faulty file)
200 plus: holds 200 (1.000). 200 minus: 0. Control permute_per_capita_emissions: 0/200. Noise probe: 0/200. Zeros probe: 5/5 UNDEFINED. Deterministic: yes. Samples drawn with numpy default_rng seeds (plus 1000.., minus 5000.., control 9000.., noise 13000..); script
work/precheck_fixed.py. Number of revisions of the fixed criterion: 1.

## 6. Timing
t = 0.151 ms (mean of 50 calls on plus samples), g = 0.023 ms (mean of 50 plus generations), S = 5 (2 worlds + 1 control + 0 premises
+ 0 relational pairs + 2 probes); estimate 2 x 200 x (S + 1) x (t + g) = 0.42 s (limit 900 s).

## 7. Deviations from the private note, problems, skeleton requests
One revision: np.errstate around the divisions. Deviation from the note: ranks instead of logs for the partial correlation (reason above). Skeleton requests: none.
