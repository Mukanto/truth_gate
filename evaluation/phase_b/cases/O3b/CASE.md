# CASE O3b

## 1. Identification
- Case id: O3b
- World id: W47
- Class: O (out of scope); subtype assigned by the designer: O-3

## 2. Source and documented error
- Source key: HER14
- Passage: HER14 (Herndon, Ash and Pollin; PERI working paper 322), 'Spreadsheet coding error': "A coding error in the RR working spreadsheet entirely excludes five countries, Australia, Austria, Belgium, Canada, and Denmark, from the analysis." Also in the paper: countries "equally weighted by country"; early years of Australia, Canada and New Zealand excluded.
- Reading: Read by the earlier author (phase 1), the PERI WP322 PDF via pdftotext (sections on the spreadsheet coding error, exclusions and weighting). Not re-read by the phase 2 author. The critique is disputed by the original authors (SOURCES.md).

## 3. Brief (exactly as in ASSIGNMENT.json)
```json
{
  "id": "W47",
  "claim": "Economic growth is lower in country-years with high public debt: mean annual real GDP growth in country-years with debt above 90% of GDP is at least 1.5 percentage points below mean growth in country-years with debt at or below 90%.",
  "data_keys": [
    {
      "key": "growth",
      "shape": "(countries, years)",
      "dtype": "float",
      "meaning": "annual real GDP growth, percent, for each country and year"
    },
    {
      "key": "debt",
      "shape": "(countries, years)",
      "dtype": "float",
      "meaning": "public debt as percent of GDP, same layout as growth"
    }
  ],
  "sizes": "20 countries x 15 years = 300 country-years"
}
```

## 4. Mapping of the criteria to the documented error and its correction
Faulty: the first five country rows (alphabetical, the five of the spreadsheet error) are left out entirely, the first four years of one further country row (row 13, the position of New Zealand in an alphabetical list of the 20 countries) are left out, each remaining country's mean growth is computed within the high-debt (> 90%) and the low-debt (<= 90%) bin, the country means are averaged with equal weight (countries empty in a bin are dropped), and the claim holds if high minus low <= -1.5 (the claim's threshold). These are the three documented choices: spreadsheet exclusion, selective exclusion of early years, equal weighting by country. Fixed: all 20 countries and all years, pooled country-year means per bin, same difference and threshold.

## 5. Pre-checks of the fixed criterion (plain Python, work/precheck_fixed.py, seed 777)
- plus: holds in 300/300 (1.000)
- minus: holds in 46/300 (0.153)
- declared control (applied to plus samples): holds in 12/300 (0.040)
- my approximation of the noise probe (float arrays N(0,1), bool arrays fair coin), 100 samples: holds in 0/100 (100 UNDEFINED by the guard: no value above 90)
- zero probe (all-zero arrays, bool False), 100 samples: holds in 0/100 (100 UNDEFINED by the guard)
- Same input evaluated twice gave the same answer (repeatable).
- Revisions of the fixed criterion: 0 (the faulty criterion was never run).

## 6. Timing
- t (mean of 50 calls of the fixed criterion on plus samples) = 0.015 ms; g (mean of 50 plus generations) = 0.109 ms
- S = 5 (2 worlds + 1 control + 0 premises + 0 relational pairs + 2 probes)
- Estimate 2 x 200 x (S + 1) x (t + g) = 0.3 s (limit 900 s)

## 7. Deviations, problems, skeleton requests
Guard: the criterion returns None when a bin is empty (no country-year above 90, as in the noise and zero probes). The faulty and fixed statistics differ in two documented respects (exclusions and weighting); the weighting is part of the documented error, and both are mirrored in the structure (a mask plus a per-bin mean). The fixed criterion holds in 0.153 of minus because the skeleton's minus world keeps the correlation between country growth and country debt level and the reverse causation; recorded, not changed. No skeleton request.
