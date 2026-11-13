# B1-07 (W15)

1. **Case**: B1-07; world id W15; class B-1; subtype: (none); source key MAK19.

2. **Documented error** (MAK19): MAK19, 'Circular analysis': 'circular analysis is used to divide ... or reduce (e.g. defining a region of interest ...) the complete dataset using a selection criterion that is retrospective and inherently relevant to the statistical outcome.' KRI09 Introduction lists 'inferential analysis performed for a statistically selected subset of genes'. The tumour/normal panel is my instance.
   Reading: Read by the earlier author as the Europe PMC full-text XML (PMC6785265), section 'Circular analysis'. I did not re-read it.

3. **Brief (exactly as in ASSIGNMENT.json)**
   * claim: In a panel of 60 candidate genes, the genes that differ between tumour and normal tissue have a mean absolute log2 fold change of at least 0.5, in 20 tumour and 20 normal samples.
   * data keys:
  * `expr` (samples, genes) float: log2 expression level, one value per sample and gene
  * `tumour` (samples,) bool: True for tumour samples (20), False for normal (20)
   * sizes: 40 samples (20 + 20), 60 genes.

4. **Mapping.** Faulty: per gene Welch t on all 40 samples, genes with two-sided p < 0.05 kept, mean over the kept genes of the absolute difference in group means >= 0.5 (computed as the difference signed by the direction found in the same data, which equals the absolute difference). This is the biased effect size of a statistically selected subset of genes (MAK19 'Circular analysis'; KRI09 Introduction). Fixed: samples split into halves, balanced by tumour/normal (alternating within each group); genes are chosen in one half, and the mean difference is taken in the other half multiplied by the sign found in the selecting half, in both directions, averaged; same Welch test, same p, same >= 0.5.

5. **Pre-checks of the fixed criterion** (plain Python, `fixed.py` only; samples drawn with a generator seeded 12345; `work/precheck.py`, output in `work/precheck_round1.txt`). Revisions of the fixed criterion: 0.

   | stream | samples | holds | rate | undefined (None) |
   |---|---|---|---|---|
| plus | 200 | 181 | 0.905 | 0 |
| minus | 200 | 0 | 0.000 | 0 |
| control:permute_tumour_labels | 200 | 1 | 0.005 | 1 |
| probe: i.i.d. N(0,1) noise | 100 | 4 | 0.040 | 0 |
| probe: zeros | 10 | 0 | 0.000 | 10 |

   Controls are the skeleton's own transforms applied to `plus` samples. The noise probe replaces every array by i.i.d. N(0,1) (bool arrays by fair coin flips: my reading of the probe, not the gate's code); the zero probe uses all-zero arrays. The criterion gave the same answer on repeated calls: True.

6. **Timing** (fixed criterion): t = 0.00177 s per call (mean of 30 plus samples), g = 6e-05 s per plus generation, S = 5 (2 worlds + 1 control + 0 premises + 0 relational pairs + 2 probes); estimate 2 x 200 x (S + 1) x (t + g) = 4.4 s (limit 900 s).

7. **Deviations from the private note, problems, skeleton requests.** The note had one direction (A selects, B evaluates); I used both directions averaged. The tumour/normal panel is the earlier author's instance. Randomness: none (the criterion is deterministic). Skeleton requests: none.
