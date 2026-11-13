# CASE b2-03

1. Case id b2-03; world id W36; class B-2; subtype L1.3; source AMB02.

2. **Source and passage.** AMB02

   The earlier author read the full text (PMC124442). I did not re-read it in this phase.

   Passage as recorded by the earlier author:

   AMB02 (PMC124442, full text read): "But, if it is calculated within the feature-selection process, there is a selection bias in it when it is used as an estimate of the prediction error. [...] it is essential that cross-validation or the bootstrap be used external to the gene-selection process."

3. **Brief, exactly as in ASSIGNMENT.json:**

```json
{
  "id": "W36",
  "claim": "The expression levels of 60 genes predict cancer versus normal status in new tissue samples with accuracy of at least 0.80.",
  "data_keys": [
    {
      "key": "expr",
      "shape": "(tissues, genes)",
      "dtype": "float",
      "meaning": "log expression of each gene in each tissue"
    },
    {
      "key": "cancer",
      "shape": "(tissues,)",
      "dtype": "bool",
      "meaning": "True if the tissue is cancerous"
    }
  ],
  "sizes": "62 tissues (40 cancer, 22 normal), 60 genes."
}
```

4. **Faulty and fixed criterion.** Faulty: AMB02's forward selection with Fisher's linear discriminant rule on all 62 tissues: pre-reduction to the 20 genes with the largest |t| (source: 400 of 2000), then three steps, each adding the gene that gives the smallest leave-one-out error of the rule; the reported error is the leave-one-out error of the final 3-gene rule (CV1IE of the source, whose minimum was at three genes) and the claim holds when 1 - error >= 0.80. Fixed: 10-fold stratified cross-validation external to the selection (CV10E of the source): pre-reduction and the whole forward selection, with its internal leave-one-out, are repeated on each training fold, the rule is fitted on the training fold and applied to the held-out fold; accuracy pooled over folds, same threshold. Adaptations from the source (ridge on the pooled covariance, pre-filter 20, gene cap 60, class prior in the rule) were stated by the earlier author.

5. **Pre-checks of the fixed criterion** (plain Python, `work\precheck_fixed.py`, output in `work\precheck_final.txt`; plus/minus draws with `rng = default_rng(2)`, 200 samples each; noise probe = float arrays N(0,1), bool arrays Bernoulli(0.5), 100 samples; zeros probe 3 samples):

```
b2-03 plus True 0.390  False 0.610  None 0.000  (n=200)
b2-03 minus True 0.000  False 1.000  None 0.000  (n=200)
b2-03 noise probe True 0.000  False 1.000  None 0.000  (n=100)
b2-03 zeros probe [None, None, None]
b2-03 deterministic: True
b2-03 timing t=0.0261 s  g=0.0001 s  S=5  estimate=63 s
```

   Revisions of the fixed criterion: 0 (no change of the analysis after the first version).

6. **Timing** (fixed, mean of 30 calls on plus samples): t = 0.0261 s, g = 0.0001 s, S = 5 (2 worlds + 1 control + 0 premises + 0 relational pairs + 2 probes); estimate 2 x 200 x (S+1) x (t+g) = 63 s (limit 900 s).

7. **Deviations from the private note, problems, skeleton requests:** None. Observation for the audit: the fixed criterion holds in only about 39% of plus samples (3 selected genes, as the note and the source's minimum at three genes), so a clean pass of the fixed file depends on how the gate treats a criterion with this power. Not changed (the number of genes is a documented parameter of the faulty error). Skeleton requests: none.

Faulty criterion: never run or simulated; only an `ast.parse` syntax check and a static name analysis (`symtable`, no execution) were done on it. Truth_Gate was not run.
