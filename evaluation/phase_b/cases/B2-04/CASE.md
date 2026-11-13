# CASE b2-04

1. Case id b2-04; world id W27; class B-2; subtype L1.3; source AMB02.

2. **Source and passage.** AMB02

   The earlier author read the full text (PMC124442). I did not re-read it in this phase.

   Passage as recorded by the earlier author:

   AMB02 (PMC124442) Discussion: "although the feature vectors have been generated independently of the class labels, we can form an SVM rule that has not only an average zero AE but also an average CV1IE error close to zero for a subset of 128 genes and about 10% for only eight genes in the selected subset."

3. **Brief, exactly as in ASSIGNMENT.json:**

```json
{
  "id": "W27",
  "claim": "Patients with leukaemia subtype A can be told from subtype B using 60 gene expression values, with AUC of at least 0.80 in new patients.",
  "data_keys": [
    {
      "key": "expr",
      "shape": "(patients, genes)",
      "dtype": "float",
      "meaning": "log expression of each gene for each patient"
    },
    {
      "key": "subtype_a",
      "shape": "(patients,)",
      "dtype": "bool",
      "meaning": "True for subtype A, False for subtype B"
    }
  ],
  "sizes": "72 patients (47 subtype A, 25 subtype B), 60 genes."
}
```

4. **Faulty and fixed criterion.** Faulty: AMB02's backward elimination (recursive feature elimination of Guyon et al.) on all 72 patients, one gene at a time by smallest absolute weight of a ridge linear classifier, down to 8 genes (the source's eight-gene subset); the AUC of the 8-gene rule is computed from its leave-one-out scores (CV1IE of the source), claim holds if AUC >= 0.80. Fixed: external 10-fold stratified cross-validation (CV10E): the elimination is repeated inside each training fold, the 8-gene rule fitted on the training fold and scored on the held-out fold, AUC from the pooled out-of-fold scores. The linear SVM of the source is replaced by a ridge classifier (earlier author's adaptation); gene cap 60 (source 7129).

5. **Pre-checks of the fixed criterion** (plain Python, `work\precheck_fixed.py`, output in `work\precheck_final.txt`; plus/minus draws with `rng = default_rng(2)`, 200 samples each; noise probe = float arrays N(0,1), bool arrays Bernoulli(0.5), 100 samples; zeros probe 3 samples):

```
b2-04 plus True 0.675  False 0.325  None 0.000  (n=200)
b2-04 minus True 0.005  False 0.995  None 0.000  (n=200)
b2-04 noise probe True 0.000  False 1.000  None 0.000  (n=100)
b2-04 zeros probe [None, None, None]
b2-04 deterministic: True
b2-04 timing t=0.0220 s  g=0.0001 s  S=5  estimate=53 s
```

   Revisions of the fixed criterion: 1 revision of the fixed (ridge penalty 1.0 -> 70.0), mirrored in the faulty. Reason: with 60 genes and about 65 training patients (p close to n) a penalty of 1 on standardised genes hardly regularises, the weights used for elimination are noisy, and the fixed held in only 22% (200 samples, seed 77) / 34% (100 samples, seed 1) of plus samples. Sweep on fixed copies, 200 plus and 200 minus samples each (`work\explore_param.py`): penalty 1 -> plus 0.22, minus 0.00; 10 -> 0.415, 0.00; 30 -> 0.53, 0.005; 65 -> 0.59, 0.00; 150 -> 0.66, 0.00. I chose 70 (order of the number of patients) on the p-close-to-n argument and did not take the largest value; the penalty is a property of the classifier, the same in both files, and does not touch the documented error (selection on all data) or its correction (selection inside the folds).

6. **Timing** (fixed, mean of 30 calls on plus samples): t = 0.0220 s, g = 0.0001 s, S = 5 (2 worlds + 1 control + 0 premises + 0 relational pairs + 2 probes); estimate 2 x 200 x (S+1) x (t+g) = 53 s (limit 900 s).

7. **Deviations from the private note, problems, skeleton requests:** One revision of the fixed (and the mirrored faulty): ridge penalty 1.0 -> 70.0, see item 5. The note gave no penalty (ridge classifier in place of the SVM). The fixed holds in 67.5% of plus samples after the revision. Skeleton requests: none.

Faulty criterion: never run or simulated; only an `ast.parse` syntax check and a static name analysis (`symtable`, no execution) were done on it. Truth_Gate was not run.
