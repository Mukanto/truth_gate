# CASE b2-10

1. Case id b2-10; world id W37; class B-2; subtype L3.1; source KAP23.

2. **Source and passage.** KAP23

   The earlier author read it through the ar5iv HTML version of arXiv 2207.07048 by targeted section search (Sec 2.4, Appendix B.4 and B.5); the quote is recorded in `quotes.tsv` as verified. I did not re-read it in this phase.

   Passage as recorded by the earlier author:

   KAP23 Sec 2.4 L3.1 (verified): "If the test set contains data from before the training set, the model is built using data from the future that it should not have access to during training, and can cause leakage."

3. **Brief, exactly as in ASSIGNMENT.json:**

```json
{
  "id": "W37",
  "claim": "Using 6 weekly indicators, a ridge regression forecasts next-week hospital admissions in future weeks with R^2 of at least 0.30.",
  "data_keys": [
    {
      "key": "indicators",
      "shape": "(weeks, indicators)",
      "dtype": "float",
      "meaning": "weekly indicator values, rows in time order"
    },
    {
      "key": "admissions_next",
      "shape": "(weeks,)",
      "dtype": "float",
      "meaning": "admissions in the following week"
    }
  ],
  "sizes": "150 weeks in time order, 6 indicators."
}
```

4. **Faulty and fixed criterion.** Faulty: rows (weeks) are shuffled into 5 folds, ridge regression on standardised indicators, R^2 of the pooled out-of-fold predictions >= 0.30 (KAP23 L3.1: a test set earlier than the training set means the model is built with data from the future). Fixed: fit on the first 100 weeks, R^2 on the last 50 weeks (about the mean of those 50); same model, same statistic, same threshold. The weekly hospital setting is the world author's; the source documents only the mechanism.

5. **Pre-checks of the fixed criterion** (plain Python, `work\precheck_fixed.py`, output in `work\precheck_final.txt`; plus/minus draws with `rng = default_rng(2)`, 200 samples each; noise probe = float arrays N(0,1), bool arrays Bernoulli(0.5), 100 samples; zeros probe 3 samples):

```
b2-10 plus True 0.430  False 0.570  None 0.000  (n=200)
b2-10 minus True 0.000  False 1.000  None 0.000  (n=200)
b2-10 noise probe True 0.000  False 1.000  None 0.000  (n=100)
b2-10 zeros probe [None, None, None]
b2-10 deterministic: True
b2-10 timing t=0.0001 s  g=0.0010 s  S=5  estimate=3 s
```

   Revisions of the fixed criterion: 0 (no change of the analysis after the first version).

6. **Timing** (fixed, mean of 30 calls on plus samples): t = 0.0001 s, g = 0.0010 s, S = 5 (2 worlds + 1 control + 0 premises + 0 relational pairs + 2 probes); estimate 2 x 200 x (S+1) x (t+g) = 3 s (limit 900 s).

7. **Deviations from the private note, problems, skeleton requests:** None. Observation: the fixed holds in about 43% of plus samples (ideal forward R^2 of the skeleton is about 0.45 against the brief's threshold 0.30, with 50 test weeks). Penalty sweep on fixed copies (1, 10, 100) gave plus 0.415, 0.445, 0.445 on 200 samples, so the default 1.0 was kept. Skeleton requests: none.

Faulty criterion: never run or simulated; only an `ast.parse` syntax check and a static name analysis (`symtable`, no execution) were done on it. Truth_Gate was not run.
