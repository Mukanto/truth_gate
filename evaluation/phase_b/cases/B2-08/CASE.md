# CASE b2-08

1. Case id b2-08; world id W30; class B-2; subtype L1.4; source KAP23.

2. **Source and passage.** KAP23

   The earlier author read it through the ar5iv HTML version of arXiv 2207.07048 by targeted section search (Sec 2.4, Appendix B.4 and B.5); the quote is recorded in `quotes.tsv` as verified. I did not re-read it in this phase.

   Passage as recorded by the earlier author:

   KAP23 Sec 2.4 L1.2 (verified): "using oversampling before splitting the data into training and test sets leads to an imperfect separation between the training and test sets"; L1.4: "the same data could exist in the training as well as test set." Prereg tie rule: oversampling by copying rows is L1.4.

3. **Brief, exactly as in ASSIGNMENT.json:**

```json
{
  "id": "W30",
  "claim": "In a fraud-screening data set where about 12% of transactions are fraudulent, a nearest-neighbour rule on 10 transaction features achieves an F1 score of at least 0.60 for fraud on new transactions.",
  "data_keys": [
    {
      "key": "features",
      "shape": "(transactions, features)",
      "dtype": "float",
      "meaning": "standardised transaction features"
    },
    {
      "key": "fraud",
      "shape": "(transactions,)",
      "dtype": "bool",
      "meaning": "True for a fraudulent transaction"
    }
  ],
  "sizes": "150 transactions (about 18 fraudulent), 10 features."
}
```

4. **Faulty and fixed criterion.** Faulty: fraud rows are copied (drawn with replacement) until the classes are balanced over the whole data, then 5-fold stratified cross-validation of a 1-nearest-neighbour rule over all rows including the copies, fraud F1 (pooled over the folds) >= 0.60. By the prereg tie rule oversampling by copying is KAP23 L1.4 (the same data in the training and the test set; the L1.2 text on oversampling before the split). Fixed: cross-validation over the original rows, the copying done in the training folds only, F1 computed on the untouched original test rows (pooled over folds); same rule, folds, statistic and threshold. F1 is computed from the pooled predictions of all folds (the earlier note said 'on the rows of each fold'; with about 18 frauds per sample a per-fold F1 would often be undefined).

5. **Pre-checks of the fixed criterion** (plain Python, `work\precheck_fixed.py`, output in `work\precheck_final.txt`; plus/minus draws with `rng = default_rng(2)`, 200 samples each; noise probe = float arrays N(0,1), bool arrays Bernoulli(0.5), 100 samples; zeros probe 3 samples):

```
b2-08 plus True 0.950  False 0.050  None 0.000  (n=200)
b2-08 minus True 0.000  False 1.000  None 0.000  (n=200)
b2-08 noise probe True 0.110  False 0.890  None 0.000  (n=100)
b2-08 zeros probe [None, None, None]
b2-08 deterministic: True
b2-08 timing t=0.0019 s  g=0.0000 s  S=5  estimate=5 s
```

   Revisions of the fixed criterion: 1 revision of both files: same robustness fix as b2-06.

6. **Timing** (fixed, mean of 30 calls on plus samples): t = 0.0019 s, g = 0.0000 s, S = 5 (2 worlds + 1 control + 0 premises + 0 relational pairs + 2 probes); estimate 2 x 200 x (S+1) x (t+g) = 5 s (limit 900 s).

7. **Deviations from the private note, problems, skeleton requests:** Same robustness fix as b2-06, applied preemptively here after the b2-06 crash (number of copies max(n_negative - n_positive, 0)). F1 pooled over the folds, see item 4. Observation: with Bernoulli(0.5) labels in my own noise probe the fixed holds at about 5% (n=1000, `work\noise_extra.txt`), although 100-sample checks showed 8% and 11% on two seeds. Skeleton requests: none.

Faulty criterion: never run or simulated; only an `ast.parse` syntax check and a static name analysis (`symtable`, no execution) were done on it. Truth_Gate was not run.
