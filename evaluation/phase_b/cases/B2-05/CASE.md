# CASE b2-05

1. Case id b2-05; world id W16; class B-2; subtype L1.2; source KAP23.

2. **Source and passage.** KAP23

   The earlier author read it through the ar5iv HTML version of arXiv 2207.07048 by targeted section search (Sec 2.4, Appendix B.4 and B.5); the quote is recorded in `quotes.tsv` as verified. I did not re-read it in this phase.

   Passage as recorded by the earlier author:

   KAP23 Sec 2.4 L1.2 (verified): "Using the entire dataset for any pre-processing steps such as imputation or over/under sampling." Appendix B.4: "Correcting the imputation method dramatically reduces the performance of the ML models proposed."

3. **Brief, exactly as in ASSIGNMENT.json:**

```json
{
  "id": "W16",
  "claim": "Using 12 country-level indicators, the model identifies which country-years will see a civil war onset, with AUC of at least 0.75 in new country-years.",
  "data_keys": [
    {
      "key": "x",
      "shape": "(rows, indicators)",
      "dtype": "float",
      "meaning": "indicator values, one row per country-year; entries flagged as unobserved hold 0"
    },
    {
      "key": "observed",
      "shape": "(rows, indicators)",
      "dtype": "bool",
      "meaning": "True where the indicator was recorded"
    },
    {
      "key": "onset",
      "shape": "(rows,)",
      "dtype": "bool",
      "meaning": "True if a civil war began in that country-year"
    }
  ],
  "sizes": "250 country-years, 12 indicators, about 15% onsets and about 20% of entries unobserved."
}
```

4. **Faulty and fixed criterion.** Faulty: before any split, unobserved entries of each indicator are filled with the mean of the observed values of that indicator among rows with the same outcome (class-conditional mean over all rows), then 5-fold stratified cross-validation of a ridge logistic regression, AUC from pooled out-of-fold scores, claim holds if AUC >= 0.75. This is the label-using pre-processing of KAP23 L1.2 (imputation on the entire dataset, with a method that uses the outcome; Appendix B.4: correcting the imputation dramatically reduces performance). Fixed: unobserved entries are filled with the mean of the observed values of the training fold (no use of the outcome), recomputed in each fold and applied to the training and the held-out rows of that fold; same logistic model, folds, statistic and threshold. The class-conditional mean is the earlier author's numpy stand-in for the outcome-using random-forest imputation of the source.

5. **Pre-checks of the fixed criterion** (plain Python, `work\precheck_fixed.py`, output in `work\precheck_final.txt`; plus/minus draws with `rng = default_rng(2)`, 200 samples each; noise probe = float arrays N(0,1), bool arrays Bernoulli(0.5), 100 samples; zeros probe 3 samples):

```
b2-05 plus True 0.680  False 0.320  None 0.000  (n=200)
b2-05 minus True 0.000  False 1.000  None 0.000  (n=200)
b2-05 noise probe True 0.000  False 1.000  None 0.000  (n=100)
b2-05 zeros probe [None, None, None]
b2-05 deterministic: True
b2-05 timing t=0.0013 s  g=0.0001 s  S=5  estimate=3 s
```

   Revisions of the fixed criterion: 0 (no change of the analysis after the first version).

6. **Timing** (fixed, mean of 30 calls on plus samples): t = 0.0013 s, g = 0.0001 s, S = 5 (2 worlds + 1 control + 0 premises + 0 relational pairs + 2 probes); estimate 2 x 200 x (S+1) x (t+g) = 3 s (limit 900 s).

7. **Deviations from the private note, problems, skeleton requests:** None. Fold count (5), penalty (1.0) and stratification are mine (the note says 'cross-validated AUC of a logistic regression'). Fixed holds in about 68% of plus samples. Skeleton requests: none.

Faulty criterion: never run or simulated; only an `ast.parse` syntax check and a static name analysis (`symtable`, no execution) were done on it. Truth_Gate was not run.
