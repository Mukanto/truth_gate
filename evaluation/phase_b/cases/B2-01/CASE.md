# CASE b2-01

1. Case id b2-01; world id W38; class B-2; subtype L1.1; source SIM03.

2. **Source and passage.** SIM03

   The earlier author read it through the designer's OpenAlex reconstruction of the paper (`SIM03_openalex_abstract.txt`, about 3,500 words, not the journal PDF). I re-read the quoted passages in that file and they are there; I did not open the paper itself.

   Passage as recorded by the earlier author:

   SIM03 via OpenAlex reconstruction: "The resubstitution estimate of the error is biased for small datasets (11,12); our simulation confirms this, with 98.2% of the simulated datasets resulting in zero misclassifications, even though no true underlying difference existed between the two groups."

3. **Brief, exactly as in ASSIGNMENT.json:**

```json
{
  "id": "W38",
  "claim": "A classifier built from the expression levels of 60 genes recognises tumour tissue among new tissue samples with accuracy of at least 0.80.",
  "data_keys": [
    {
      "key": "expr",
      "shape": "(samples, genes)",
      "dtype": "float",
      "meaning": "log expression level of each gene in each tissue sample"
    },
    {
      "key": "tumour",
      "shape": "(samples,)",
      "dtype": "bool",
      "meaning": "True if the sample is tumour tissue, False if normal"
    }
  ],
  "sizes": "20 samples (10 per class), 60 genes."
}
```

4. **Faulty and fixed criterion.** Faulty: gene selection (5 genes with the largest absolute two-sample t), per-gene weights (pooled within-class sd) and the nearest-centroid rule are built on all 20 samples and applied to the same 20 samples; accuracy = 1 - resubstitution error, claim holds if accuracy >= 0.80 (the brief's threshold). This is the resubstitution estimate of SIM03 (20 specimens, 10 per class, expression profiles of genes with no class difference; 98.2% of such datasets gave zero misclassifications). Fixed: the same `fit` (selection, weights, rule) is redone with the left-out sample removed first, leave-one-out over the 20 samples; same accuracy statistic and threshold. SIM03 states that all three steps must be inside the cross-validation. Not documented in the source and chosen by the earlier author: nearest centroid, 5 genes, the 60-gene cap (6000 in the source).

5. **Pre-checks of the fixed criterion** (plain Python, `work\precheck_fixed.py`, output in `work\precheck_final.txt`; plus/minus draws with `rng = default_rng(2)`, 200 samples each; noise probe = float arrays N(0,1), bool arrays Bernoulli(0.5), 100 samples; zeros probe 3 samples):

```
b2-01 plus True 0.895  False 0.105  None 0.000  (n=200)
b2-01 minus True 0.055  False 0.945  None 0.000  (n=200)
b2-01 noise probe True 0.050  False 0.950  None 0.000  (n=100)
b2-01 zeros probe [None, None, None]
b2-01 deterministic: True
b2-01 timing t=0.0009 s  g=0.0000 s  S=5  estimate=2 s
```

   Revisions of the fixed criterion: 0 (no change of the analysis after the first version).

6. **Timing** (fixed, mean of 30 calls on plus samples): t = 0.0009 s, g = 0.0000 s, S = 5 (2 worlds + 1 control + 0 premises + 0 relational pairs + 2 probes); estimate 2 x 200 x (S+1) x (t+g) = 2 s (limit 900 s).

7. **Deviations from the private note, problems, skeleton requests:** None. The nearest-centroid rule uses per-gene pooled sd as scale (a detail the note did not fix). Skeleton requests: none.

Faulty criterion: never run or simulated; only an `ast.parse` syntax check and a static name analysis (`symtable`, no execution) were done on it. Truth_Gate was not run.
