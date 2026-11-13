# CASE O3a

## 1. Identification
- Case id: O3a
- World id: W08
- Class: O (out of scope); subtype assigned by the designer: O-3

## 2. Source and documented error
- Source key: BAG09
- Passage: BAG09 (Baggerly and Coombes 2009), abstract: "the most common errors are simple (e.g., row or column offsets)"; Fig. 2 caption: expression values obtained by "offsetting" by one row (e.g., replacing 200075_s_at with 200076_at).
- Reading: Read by the earlier author (phase 1), arXiv full text PDF (abstract, Fig. 2 caption, sections 2 and 3). Not re-read by the phase 2 author.

## 3. Brief (exactly as in ASSIGNMENT.json)
```json
{
  "id": "W08",
  "claim": "A five-gene response signature tracks drug sensitivity across the cell-line panel: the Pearson correlation between the signature score (mean of the signature genes, which are columns 5 to 9 of expr counting from 1) and the measured sensitivity is at least 0.5.",
  "data_keys": [
    {
      "key": "expr",
      "shape": "(cell_lines, 20)",
      "dtype": "float",
      "meaning": "log expression of 20 genes per cell line, genes in the panel's list order (the five signature genes are columns 5 to 9, counting from 1); rows are cell lines"
    },
    {
      "key": "sensitivity",
      "shape": "(cell_lines,)",
      "dtype": "float",
      "meaning": "measured drug sensitivity (higher = more sensitive) per cell line, rows in the panel's order"
    }
  ],
  "sizes": "60 cell lines; 20 genes"
}
```

## 4. Mapping of the criteria to the documented error and its correction
Faulty: the signature score is the mean of the gene columns offset by one position in the gene list, columns 6 to 10 counting from 1 (index 5:10) instead of the named columns 5 to 9; the claim holds if the Pearson correlation of that score with the sensitivity is >= 0.5 (the threshold of the claim). The one-position offset along the gene axis is the error BAG09 documents. Fixed: the score from the named columns 5 to 9 (index 4:9), same Pearson r and threshold.

## 5. Pre-checks of the fixed criterion (plain Python, work/precheck_fixed.py, seed 777)
- plus: holds in 284/300 (0.947)
- minus: holds in 0/300 (0.000)
- declared control (applied to plus samples): holds in 0/300 (0.000)
- my approximation of the noise probe (float arrays N(0,1), bool arrays fair coin), 100 samples: holds in 0/100
- zero probe (all-zero arrays, bool False), 100 samples: holds in 0/100 (100 UNDEFINED by the guard)
- Same input evaluated twice gave the same answer (repeatable).
- Revisions of the fixed criterion: 0 (the faulty criterion was never run).

## 6. Timing
- t (mean of 50 calls of the fixed criterion on plus samples) = 0.041 ms; g (mean of 50 plus generations) = 0.023 ms
- S = 5 (2 worlds + 1 control + 0 premises + 0 relational pairs + 2 probes)
- Estimate 2 x 200 x (S + 1) x (t + g) = 0.2 s (limit 900 s)

## 7. Deviations, problems, skeleton requests
The private note expects the faulty criterion to usually fail in plus because the offset genes 'carry no signal'. Reading the skeleton generator (not running any faulty code) the signature genes are columns 5 to 9 and the offset window 6 to 10 shares four of the five, so the note's expectation may not hold; this is a property of the skeleton, the faulty criterion was written as documented and not changed. No skeleton request.
