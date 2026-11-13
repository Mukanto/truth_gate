# CASE b2-09

1. Case id b2-09; world id W14; class B-2; subtype L3.1; source KAP23.

2. **Source and passage.** KAP23

   The earlier author read it through the ar5iv HTML version of arXiv 2207.07048 by targeted section search (Sec 2.4, Appendix B.4 and B.5); the quote is recorded in `quotes.tsv` as verified. I did not re-read it in this phase.

   Passage as recorded by the earlier author:

   KAP23 Appendix B.5 (verified): "When the dataset contains temporal data, the training dataset could contain data from a later date than the test dataset because of being shuffled."

3. **Brief, exactly as in ASSIGNMENT.json:**

```json
{
  "id": "W14",
  "claim": "From 8 yearly indicators, the model predicts civil war onset in future country-years with AUC of at least 0.75.",
  "data_keys": [
    {
      "key": "x",
      "shape": "(years, indicators)",
      "dtype": "float",
      "meaning": "indicator values, one country-year per row, rows in time order"
    },
    {
      "key": "onset",
      "shape": "(years,)",
      "dtype": "bool",
      "meaning": "True if a civil war began in that year"
    }
  ],
  "sizes": "200 rows in time order, 8 indicators, about 15% onsets."
}
```

4. **Faulty and fixed criterion.** Faulty: rows are assigned to 5 stratified folds at random irrespective of their order in time, ridge logistic regression, AUC from pooled out-of-fold scores >= 0.75; training data then contain later years than the test data (KAP23 L3.1, Appendix B.5: the training set could contain data from a later date than the test set because of being shuffled). Fixed: chronological split, fit on the first 70% of the rows (140), AUC on the last 30% (60 rows); same model and statistic, same threshold. The source's own corrected split (earlier years train, later years test) is of the same kind.

5. **Pre-checks of the fixed criterion** (plain Python, `work\precheck_fixed.py`, output in `work\precheck_final.txt`; plus/minus draws with `rng = default_rng(2)`, 200 samples each; noise probe = float arrays N(0,1), bool arrays Bernoulli(0.5), 100 samples; zeros probe 3 samples):

```
b2-09 plus True 0.425  False 0.500  None 0.075  (n=200)
b2-09 minus True 0.030  False 0.960  None 0.010  (n=200)
b2-09 noise probe True 0.000  False 1.000  None 0.000  (n=100)
b2-09 zeros probe [None, None, None]
b2-09 deterministic: True
b2-09 timing t=0.0002 s  g=0.0010 s  S=5  estimate=3 s
```

   Revisions of the fixed criterion: 0 (no change of the analysis after the first version).

6. **Timing** (fixed, mean of 30 calls on plus samples): t = 0.0002 s, g = 0.0010 s, S = 5 (2 worlds + 1 control + 0 premises + 0 relational pairs + 2 probes); estimate 2 x 200 x (S+1) x (t+g) = 3 s (limit 900 s).

7. **Deviations from the private note, problems, skeleton requests:** None. Observation: the fixed returns None (guard: a class missing in the training or the test part) in 7.5% of plus samples and 1% of minus samples, because onsets cluster in time; and it holds in only about 42% of plus samples. Not changed; expanding-window folds (the note's alternative) would have changed the structure relative to the faulty 5-fold design. Skeleton requests: none.

Faulty criterion: never run or simulated; only an `ast.parse` syntax check and a static name analysis (`symtable`, no execution) were done on it. Truth_Gate was not run.
