# CASE b2-11

1. Case id b2-11; world id W06; class B-2; subtype L3.2; source KAP23.

2. **Source and passage.** KAP23

   The earlier author read it through the ar5iv HTML version of arXiv 2207.07048 by targeted section search (Sec 2.4, Appendix B.4 and B.5); the quote is recorded in `quotes.tsv` as verified. I did not re-read it in this phase.

   Passage as recorded by the earlier author:

   KAP23 Sec 2.4 L3.2 (verified): "Oner et al. 2020 find that a recent study on histopathology uses different observations of the same patient in the training and test sets." (The claim is about new patients.)

3. **Brief, exactly as in ASSIGNMENT.json:**

```json
{
  "id": "W06",
  "claim": "From 20 image features of tissue patches, the model identifies the gene mutation status of new patients with AUC of at least 0.75.",
  "data_keys": [
    {
      "key": "patches",
      "shape": "(patients, patches, features)",
      "dtype": "float",
      "meaning": "image features of each tissue patch of each patient"
    },
    {
      "key": "mutated",
      "shape": "(patients,)",
      "dtype": "bool",
      "meaning": "True if the patient's tumour carries the mutation"
    }
  ],
  "sizes": "40 patients, 6 patches per patient, 20 features."
}
```

4. **Faulty and fixed criterion.** Faulty: patch rows (40 patients x 6 patches = 240 rows, the patient's status repeated on each patch) are shuffled into 5 stratified folds, ridge logistic regression, patch-level AUC from pooled out-of-fold scores >= 0.75; patches of one patient are then in both training and test sets (KAP23 L3.2, Oner et al. 2020). Fixed: the folds are formed over the patient axis (5 folds of 8 patients, stratified by mutation status) and all patches of a patient go to the same fold; same model, statistic (patch-level AUC; patient-level versus patch-level was left to the criterion author by the earlier note) and threshold.

5. **Pre-checks of the fixed criterion** (plain Python, `work\precheck_fixed.py`, output in `work\precheck_final.txt`; plus/minus draws with `rng = default_rng(2)`, 200 samples each; noise probe = float arrays N(0,1), bool arrays Bernoulli(0.5), 100 samples; zeros probe 3 samples):

```
b2-11 plus True 0.620  False 0.380  None 0.000  (n=200)
b2-11 minus True 0.005  False 0.995  None 0.000  (n=200)
b2-11 noise probe True 0.000  False 1.000  None 0.000  (n=100)
b2-11 zeros probe [None, None, None]
b2-11 deterministic: True
b2-11 timing t=0.0013 s  g=0.0001 s  S=5  estimate=3 s
```

   Revisions of the fixed criterion: 0 (no change of the analysis after the first version).

6. **Timing** (fixed, mean of 30 calls on plus samples): t = 0.0013 s, g = 0.0001 s, S = 5 (2 worlds + 1 control + 0 premises + 0 relational pairs + 2 probes); estimate 2 x 200 x (S+1) x (t+g) = 3 s (limit 900 s).

7. **Deviations from the private note, problems, skeleton requests:** None. Fixed holds in about 62% of plus samples. Skeleton requests: none.

Faulty criterion: never run or simulated; only an `ast.parse` syntax check and a static name analysis (`symtable`, no execution) were done on it. Truth_Gate was not run.
