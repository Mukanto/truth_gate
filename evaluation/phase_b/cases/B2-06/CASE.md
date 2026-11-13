# CASE b2-06

1. Case id b2-06; world id W18; class B-2; subtype L1.2; source KAP23.

2. **Source and passage.** KAP23

   The earlier author read it through the ar5iv HTML version of arXiv 2207.07048 by targeted section search (Sec 2.4, Appendix B.4 and B.5); the quote is recorded in `quotes.tsv` as verified. I did not re-read it in this phase.

   Passage as recorded by the earlier author:

   KAP23 Sec 2.4 L1.2 (verified in full text): "For instance, using oversampling before splitting the data into training and test sets leads to an imperfect separation between the training and test sets since data generated using oversampling from the training set will also be present in the test set." Table 1 lists Blagus and Lusa 2015 (bioinformatics, 6 papers).

3. **Brief, exactly as in ASSIGNMENT.json:**

```json
{
  "id": "W18",
  "claim": "In a screening cohort where about one sample in five is positive, a nearest-neighbour rule on 30 biomarkers attains balanced accuracy of at least 0.75 on new samples.",
  "data_keys": [
    {
      "key": "biomarkers",
      "shape": "(samples, markers)",
      "dtype": "float",
      "meaning": "standardised biomarker values"
    },
    {
      "key": "positive",
      "shape": "(samples,)",
      "dtype": "bool",
      "meaning": "True for a positive sample"
    }
  ],
  "sizes": "100 samples (about 20 positive), 30 biomarkers."
}
```

4. **Faulty and fixed criterion.** Faulty: SMOTE-style oversampling is applied to the whole data before splitting: synthetic positives are interpolations (random fraction) between two different random positive rows, added until the classes are balanced; then 5-fold stratified cross-validation of a 3-nearest-neighbour rule over all rows (real and synthetic) and balanced accuracy (mean of sensitivity and specificity, pooled over folds) >= 0.75. This is KAP23 L1.2: oversampling before the split puts data generated from the training set into the test set. Fixed: cross-validation over the original rows only; the oversampling (same procedure) is applied to the training folds only and the test folds stay untouched; balanced accuracy on the original rows, same threshold. Interpolation between random pairs (not between nearest neighbours) is the earlier author's simplification.

5. **Pre-checks of the fixed criterion** (plain Python, `work\precheck_fixed.py`, output in `work\precheck_final.txt`; plus/minus draws with `rng = default_rng(2)`, 200 samples each; noise probe = float arrays N(0,1), bool arrays Bernoulli(0.5), 100 samples; zeros probe 3 samples):

```
b2-06 plus True 1.000  False 0.000  None 0.000  (n=200)
b2-06 minus True 0.000  False 1.000  None 0.000  (n=200)
b2-06 noise probe True 0.000  False 1.000  None 0.000  (n=100)
b2-06 zeros probe [None, None, None]
b2-06 deterministic: True
b2-06 timing t=0.0025 s  g=0.0001 s  S=5  estimate=6 s
```

   Revisions of the fixed criterion: 1 revision of both files: robustness fix of the number of synthetic rows (max(., 0)), found because the pre-check's noise probe crashed. No change of the analysis.

6. **Timing** (fixed, mean of 30 calls on plus samples): t = 0.0025 s, g = 0.0001 s, S = 5 (2 worlds + 1 control + 0 premises + 0 relational pairs + 2 probes); estimate 2 x 200 x (S+1) x (t+g) = 6 s (limit 900 s).

7. **Deviations from the private note, problems, skeleton requests:** Robustness fix, not an analysis change: the number of synthetic rows is max(n_negative - n_positive, 0), because the noise probe (Bernoulli 0.5 labels) can give more positives than negatives (the first version crashed on that probe in the pre-check). Otherwise none. In plus the fixed holds in 100% of the samples (ceiling), a property of the skeleton. Skeleton requests: none.

Faulty criterion: never run or simulated; only an `ast.parse` syntax check and a static name analysis (`symtable`, no execution) were done on it. Truth_Gate was not run.
