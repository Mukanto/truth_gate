# Post-repair fidelity audit, Phase C, class B-2 (B2-01, B2-06, B2-10)

Date: 2026-11-15. Auditor: the same blind fidelity auditor, under `AUDIT_PHASE_C.md` (PREREG_PHASE_C section 5, PB
section 5.3). Only the three repaired pairs were audited again, on all nine items. `AUDIT.json` and `AUDIT.md` are
unchanged.

No criterion was called on any data, and Truth_Gate was not run (no version). One helper computation was run in isolation:
a Python one-liner that evaluates the repaired guard expressions `n - (-(-(n) // k))` for k = 5 and 10 on the integers 0 to
8 and compares them with n - ceil(n/k). Nothing from the cases was imported or executed.

## Result

**All three repaired pairs pass all nine items.**

| Case | a | b | c | d | e | f | g | h | i | Overall |
|---|---|---|---|---|---|---|---|---|---|---|
| B2-01 | yes | yes | yes | yes | yes | yes | yes | yes | yes | pass |
| B2-06 | yes | yes | yes | yes | yes | yes | yes | yes | yes | pass |
| B2-10 | yes | yes | yes | yes | yes | yes | yes | yes | yes | pass |

## What changed

I diffed each pair's `prerepair/` files against the new ones, the new twins against each other, and both twins against
`skeleton.py`:

* **B2-01.** Only line 80 of `fixed.py` changed: the guard is now
  `min((n_pos - (-(-(n_pos) // 5))), (n_neg - (-(-(n_neg) // 5)))) < 2`. `faulty.py` is byte-identical to its pre-repair
  version.
* **B2-06.** Only line 62 changed, in both bodies, to that same guard. The twins now differ only in the fold assignment
  (patch-level in the faulty, patient-level in the fixed).
* **B2-10.** Only line 57 of `fixed.py` changed:
  `min((n_pos - (-(-(n_pos) // 10))), (n_neg - (-(-(n_neg) // 10)))) < 3`. `faulty.py` is byte-identical to its pre-repair
  version.
* **Skeleton.** In all three pairs both twins still equal the frozen skeleton outside the criterion body (only the stub
  line is replaced). The updated `MECH_CHECK.json` reports no issues and the same briefs.

## Guard arithmetic

`-(n) // k` is `(-n) // k`, which equals −ceil(n/k). The negation of that is ceil(n/k), so the new expression is
n − ceil(n/k). In my helper evaluation it matched n − ceil(n/k) for every n from 0 to 8.

| Pair and twin | Returns None for | Minimum enforced | Where the minimum comes from |
|---|---|---|---|
| B2-01 fixed | n ≤ 2 per class | ≥ 3 per class | ≥ 2 per class in every training fold of the stratified 5-fold split (`strat_folds` puts at most ceil(n/5) of a class in one fold) |
| B2-01 faulty | n ≤ 1 per class | ≥ 2 per class | ≥ 2 per class in its single fitting set |
| B2-06, both twins | ≤ 2 patients of a class | ≥ 3 patients per class | ≥ 2 patients per class in every training fold of the patient-level 5-fold split |
| B2-10 fixed | n ≤ 3 per class | ≥ 4 per class | ≥ 3 per class in every outer training set, so each inner LOO fitting set keeps the 2 per group the t statistic needs |
| B2-10 faulty | n ≤ 2 per class | ≥ 3 per class | each LOO fitting set keeps 2 per class |

In every case the code now enforces what section 4 of the case's CASE.md states.

## Item judgements

* **Item (c), B2-01 and B2-10.** The twins still differ in their guards. Now the fixed guard is the stricter one, and the
  difference follows from the corrected procedure's own fold structure. I count it as part of the correction, as
  `AUDIT.md` said a structure-derived difference would be.
* **Item (c), B2-06.** The twins share one guard line, so no difference beyond the error remains.
* **Item (d), B2-06: the faulty guard.** The faulty fits on patch-level folds. Its fitting sets contain patches of
  practically every patient, so on its own structure it would need only 2 patients per class, not 3. The patient-level
  minimum is still accepted, for three reasons:
  * The private note states one minimum for the pair ("in each fitting set at least 2 patients per class"), and it is the
    minimum of the claim's statistic computed correctly. The faulty criterion estimates that same quantity in the
    documented wrong way (PREREG_PHASE_C section 2, estimand).
  * The guard is identical in both twins, so item (c) is clean.
  * It cannot fire on any gate stream: the worlds always have 32 of 80 patients malignant, the permutation control keeps
    the counts, the zeros probe returns None through the empty class in both twins, and under the noise probe 2 or fewer
    patients of one class has negligible probability.
  * It is not gate-aware in the sense of (d). I record the reading here so the designer can see it.
* **MECH_CHECK.** I judged every listed comparison:
  * the class-count guards are allowed guards;
  * `np.max(np.abs(step)) < 1e-8` (B2-01, B2-06) is the Newton optimiser's stopping rule and inspects no input.
* **Items (a), (b), (e), (f), (g), (h), (i).** Unchanged from `AUDIT.md`. The documented error, the correction, the brief,
  the sizes, the statistic, the threshold and the decision rule are all untouched by the repair. The timing estimates stay
  under 900 s (14 s, 6 s, 567 s).
* **Return value.** Each criterion still returns `True` exactly when its statistic reaches the brief's threshold.

## Outside this re-audit (unchanged)

The repair-round LOG records that the same precedence slip remains in the fixed guards of B2-02, B2-03, B2-08, B2-09, B2-11
and B2-12, and leaves it to the coordinator. As `AUDIT.md` says, those guards return None only for an empty class. Their
twins behave identically, and no item changes for those pairs.

## What I read for the re-audit

* `class/LOG.md` (the "Repair round" section)
* `MECH_CHECK.json` (the entries for B2-01, B2-06 and B2-10)
* For B2-01, B2-06 and B2-10:
  * the new `faulty.py`, `fixed.py` and `CASE.md`, through full diffs against `prerepair/` and against each other
  * the `prerepair/` copies of `faulty.py`, `fixed.py` and `CASE.md`
  * `skeleton.py` (diffed against both twins)
  * `ASSIGNMENT.json` (compared with MECH_CHECK)
* No new URL was fetched. The source checks from the first audit stand: VAR06 full text and the AMB02 record through Europe
  PMC, and KAP23 through ar5iv.
