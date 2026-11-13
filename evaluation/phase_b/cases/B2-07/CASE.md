# CASE b2-07

1. Case id b2-07; world id W04; class B-2; subtype L1.4; source KAP23.

2. **Source and passage.** KAP23

   The earlier author read it through the ar5iv HTML version of arXiv 2207.07048 by targeted section search (Sec 2.4, Appendix B.4 and B.5); the quote is recorded in `quotes.tsv` as verified. I did not re-read it in this phase.

   Passage as recorded by the earlier author:

   KAP23 Sec 2.4 L1.4 (verified): "If a dataset with duplicates is used for the purposes of training and evaluating an ML model, the same data could exist in the training as well as test set."

3. **Brief, exactly as in ASSIGNMENT.json:**

```json
{
  "id": "W04",
  "claim": "From 15 clinical measurements recorded in a patient registry, a nearest-neighbour rule predicts diagnosis in new patients with accuracy of at least 0.75. Some patients were entered more than once.",
  "data_keys": [
    {
      "key": "records",
      "shape": "(rows, measurements)",
      "dtype": "float",
      "meaning": "clinical measurements, one row per registry entry"
    },
    {
      "key": "diagnosis",
      "shape": "(rows,)",
      "dtype": "bool",
      "meaning": "True if the patient has the diagnosis"
    }
  ],
  "sizes": "200 rows, 15 measurements; about a quarter of the rows repeat an earlier entry exactly, with its diagnosis."
}
```

4. **Faulty and fixed criterion.** Faulty: 10-fold stratified cross-validation of a 1-nearest-neighbour rule over all 200 rows, repeated entries included, claim holds if accuracy >= 0.75. This is KAP23 L1.4: with duplicates, the same data can be in the training and the test set. Fixed: identical rows are first collapsed to one (first occurrence kept), then the same cross-validation and threshold. (The alternative of keeping repeats of a case in one fold was not used.)

5. **Pre-checks of the fixed criterion** (plain Python, `work\precheck_fixed.py`, output in `work\precheck_final.txt`; plus/minus draws with `rng = default_rng(2)`, 200 samples each; noise probe = float arrays N(0,1), bool arrays Bernoulli(0.5), 100 samples; zeros probe 3 samples):

```
b2-07 plus True 0.940  False 0.060  None 0.000  (n=200)
b2-07 minus True 0.000  False 1.000  None 0.000  (n=200)
b2-07 noise probe True 0.000  False 1.000  None 0.000  (n=100)
b2-07 zeros probe [None, None, None]
b2-07 deterministic: True
b2-07 timing t=0.0013 s  g=0.0001 s  S=5  estimate=3 s
```

   Revisions of the fixed criterion: 0 (no change of the analysis after the first version).

6. **Timing** (fixed, mean of 30 calls on plus samples): t = 0.0013 s, g = 0.0001 s, S = 5 (2 worlds + 1 control + 0 premises + 0 relational pairs + 2 probes); estimate 2 x 200 x (S+1) x (t+g) = 3 s (limit 900 s).

7. **Deviations from the private note, problems, skeleton requests:** None. Fixed holds in about 94% of plus samples. Skeleton requests: none.

Faulty criterion: never run or simulated; only an `ast.parse` syntax check and a static name analysis (`symtable`, no execution) were done on it. Truth_Gate was not run.
