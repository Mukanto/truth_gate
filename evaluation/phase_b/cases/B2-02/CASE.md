# CASE b2-02

1. Case id b2-02; world id W35; class B-2; subtype L1.1; source SIM03.

2. **Source and passage.** SIM03

   The earlier author read it through the designer's OpenAlex reconstruction of the paper (`SIM03_openalex_abstract.txt`, about 3,500 words, not the journal PDF). I re-read the quoted passages in that file and they are there; I did not open the paper itself.

   Passage as recorded by the earlier author:

   SIM03 via OpenAlex reconstruction: "We also computed the resubstitution estimate of the error rate (this estimate results from building the predictor on the full dataset and then reapplying it to each specimen for classification purposes). [...] Consequently, it is essential to obtain an unbiased estimate of the true error rate of the predictor (i.e., the probability of incorrectly classifying a randomly selected future case)."

3. **Brief, exactly as in ASSIGNMENT.json:**

```json
{
  "id": "W35",
  "claim": "A logistic model using 20 baseline markers predicts which patients will relapse within five years, in new patients, with AUC of at least 0.75.",
  "data_keys": [
    {
      "key": "markers",
      "shape": "(patients, markers)",
      "dtype": "float",
      "meaning": "standardised baseline marker values for each patient"
    },
    {
      "key": "relapse",
      "shape": "(patients,)",
      "dtype": "bool",
      "meaning": "True if the patient relapsed within five years"
    }
  ],
  "sizes": "30 patients, 20 markers."
}
```

4. **Faulty and fixed criterion.** Faulty: ridge logistic regression (Newton steps, penalty 1, standardised markers as given) fitted on all 30 patients and AUC computed on the same patients (SIM03's definition of the resubstitution estimate). Fixed: 5-fold stratified cross-validation in which the model is refitted without each held-out fold, AUC from the pooled out-of-fold scores; same model, same statistic, same threshold 0.75. SIM03 names leave-one-out and other cross-validation methods as nearly unbiased. The setting (n=30, 20 markers, logistic model, AUC, 5 folds) is the earlier author's choice; the source documents the setting only qualitatively.

5. **Pre-checks of the fixed criterion** (plain Python, `work\precheck_fixed.py`, output in `work\precheck_final.txt`; plus/minus draws with `rng = default_rng(2)`, 200 samples each; noise probe = float arrays N(0,1), bool arrays Bernoulli(0.5), 100 samples; zeros probe 3 samples):

```
b2-02 plus True 0.900  False 0.100  None 0.000  (n=200)
b2-02 minus True 0.035  False 0.965  None 0.000  (n=200)
b2-02 noise probe True 0.030  False 0.970  None 0.000  (n=100)
b2-02 zeros probe [None, None, None]
b2-02 deterministic: True
b2-02 timing t=0.0009 s  g=0.0000 s  S=5  estimate=2 s
```

   Revisions of the fixed criterion: 0 (no change of the analysis after the first version).

6. **Timing** (fixed, mean of 30 calls on plus samples): t = 0.0009 s, g = 0.0000 s, S = 5 (2 worlds + 1 control + 0 premises + 0 relational pairs + 2 probes); estimate 2 x 200 x (S+1) x (t+g) = 2 s (limit 900 s).

7. **Deviations from the private note, problems, skeleton requests:** None. Ridge penalty 1.0 (the note said 'small ridge'), up to 30 Newton steps with a convergence test (the note said 'few'). Penalty sweep (1, 5, 20) on fixed copies, 200 plus samples each, gave plus 0.87, 0.915, 0.90, so the default 1.0 was kept. Skeleton requests: none.

Faulty criterion: never run or simulated; only an `ast.parse` syntax check and a static name analysis (`symtable`, no execution) were done on it. Truth_Gate was not run.
