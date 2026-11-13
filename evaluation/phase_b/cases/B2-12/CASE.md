# CASE b2-12

1. Case id b2-12; world id W49; class B-2; subtype L3.2; source KAP23.

2. **Source and passage.** KAP23

   The earlier author read it through the ar5iv HTML version of arXiv 2207.07048 by targeted section search (Sec 2.4, Appendix B.4 and B.5); the quote is recorded in `quotes.tsv` as verified. I did not re-read it in this phase.

   Passage as recorded by the earlier author:

   KAP23 Sec 2.4 L3.2 (verified): "In the extreme (but unfortunately common) case, train and test samples come from the same people or units." Remedy named there: block cross validation (Roberts 2017, Valavi 2021).

3. **Brief, exactly as in ASSIGNMENT.json:**

```json
{
  "id": "W49",
  "claim": "From 15 patient characteristics, ridge regression predicts length of stay in patients from new hospitals with R^2 of at least 0.40.",
  "data_keys": [
    {
      "key": "x",
      "shape": "(hospitals, patients, characteristics)",
      "dtype": "float",
      "meaning": "characteristics of each patient in each hospital"
    },
    {
      "key": "stay",
      "shape": "(hospitals, patients)",
      "dtype": "float",
      "meaning": "length of stay in days"
    }
  ],
  "sizes": "12 hospitals, 20 patients each, 15 characteristics."
}
```

4. **Faulty and fixed criterion.** Faulty: the 240 patient rows are flattened and shuffled into 5 folds, ridge regression on standardised characteristics, R^2 of the pooled out-of-fold predictions >= 0.40; patients of one hospital are then in both training and test (KAP23 L3.2: train and test samples come from the same units; remedy named: block cross-validation). Fixed: 5 folds formed over hospitals (hospital groups of 3, 3, 2, 2, 2; a hospital is never split), same model, statistic and threshold 0.40.

5. **Pre-checks of the fixed criterion** (plain Python, `work\precheck_fixed.py`, output in `work\precheck_final.txt`; plus/minus draws with `rng = default_rng(2)`, 200 samples each; noise probe = float arrays N(0,1), bool arrays Bernoulli(0.5), 100 samples; zeros probe 3 samples):

```
b2-12 plus True 0.595  False 0.405  None 0.000  (n=200)
b2-12 minus True 0.000  False 1.000  None 0.000  (n=200)
b2-12 noise probe True 0.000  False 1.000  None 0.000  (n=100)
b2-12 zeros probe [None, None, None]
b2-12 deterministic: True
b2-12 timing t=0.0005 s  g=0.0000 s  S=5  estimate=1 s
```

   Revisions of the fixed criterion: 0 (no change of the analysis after the first version).

6. **Timing** (fixed, mean of 30 calls on plus samples): t = 0.0005 s, g = 0.0000 s, S = 5 (2 worlds + 1 control + 0 premises + 0 relational pairs + 2 probes); estimate 2 x 200 x (S+1) x (t+g) = 1 s (limit 900 s).

7. **Deviations from the private note, problems, skeleton requests:** 5 hospital folds instead of leave-one-hospital-out (the note said 'leave-hospitals-out folds'), so that faulty and fixed have the same number of folds. Fixed holds in about 60% of plus samples; penalty sweep on fixed copies (1, 20, 100) gave plus 0.565, 0.57, 0.45. Skeleton requests: none.

Faulty criterion: never run or simulated; only an `ast.parse` syntax check and a static name analysis (`symtable`, no execution) were done on it. Truth_Gate was not run.
