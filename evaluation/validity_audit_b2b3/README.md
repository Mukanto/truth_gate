# Validity audit of the B-2 and B-3 cases (Phases B and C), post hoc

The classes B-2 (procedure-level leakage) and B-3 (coupling by construction) failed the pre-registered bar in Phase B
and in Phase C. This audit asks how much of that result describes the gate, and how much describes the cases. It asks
three questions of every B-2 and B-3 pair:

- **(a)** Do the declared worlds contain the structure that the error exploits?
- **(b)** Does the faulty criterion represent the documented error, and does a detection come from it?
- **(c)** Is the fixed criterion a clean test of the claim?

**It is post hoc and changes no pre-registered result.** B-2 and B-3 still FAIL in both phases.

## How it was made

- **Auditors.** Two fresh agents (Claude Opus), one per phase: 24 Phase B pairs and 22 Phase C pairs. They ran in a
  separate Claude session that does not load this project's notes. Neither had seen the evaluation's reports.
- **What they had.** Each worked from a task folder holding:
  - the pre-registration, the expected flags, the sources and the world author's instructions;
  - the case files and the binding certificates;
  - a copy of the gate.
- **Order.** Each wrote its own audit (Part 1) before opening the evaluation's report and post-run audit. It then added a
  comparison (Part 2).
- **Checks by the designer.** Each agent's transcript was checked: no other agent, no network, no git, and reads only
  inside its folder apart from the one allowed interpreter. The first read of the withheld folder came after Part 1 was
  written (Phase B step 63, after steps 56–62; Phase C step 56, after steps 51–55). The copied inputs were unchanged
  afterwards (SHA-256: 185 of 185 and 174 of 174). The transcripts are not published.
- **Files.**
  - Instructions: [`phase_b/INSTRUCTIONS.md`](phase_b/INSTRUCTIONS.md), [`phase_c/INSTRUCTIONS.md`](phase_c/INSTRUCTIONS.md).
  - Outputs: `AUDIT_PHASE_B.md` / `.json` and `AUDIT_PHASE_C.md` / `.json`.
  - The auditors' scripts: `phase_b/scripts/`, `phase_c/scripts/`. Their paths are those of the task folders.

## Result (the auditors' attributions)

Each scored miss and each failed clean pass is attributed to one of:
- the **tool**;
- the case's **world** (the structure is missing or weak);
- the case's **size** (the structure is present, but the data are too small for it to show);
- the **error** (not represented);
- the **fixed** criterion (not clean);
- **mixed**.

| Phase, class | Pairs | Misses: tool / world / size / mixed | Failed clean passes: fixed / mixed | Detections not from the error | Pairs judged adequate: detected / clean |
|---|---|---|---|---|---|
| B, B-2 | 12 | 1 (B2-06) / 3 / 1 / 0 | 0 / 1 (B2-09) | 0 | 8: 7 / 8 |
| B, B-3 | 12 | 0 / 4 / 0 / 0 | 4 / 0 | 0 | 5: 5 / 5 |
| C, B-2 | 12 | 0 / 1 / 3 / 1 (B2-05) | 4 / 0 | 4 (B2-08 to B2-11) | 3: 3 / 3 |
| C, B-3 | 10 | 0 / 2 / 0 / 0 | 1 / 1 (B3-12) | 2 (B3-04, B3-12) | 6: 6 / 6 |

- **(a) Worlds.** In 10 of the 16 misses the declared `minus` world lacks the structure or carries it only weakly; in one
  more it is part of the cause. Phase B: B2-09, B2-10, B2-12, B3-06, B3-09, B3-10, B3-12. Phase C: B2-04, B3-02, B3-03,
  and partly B2-05.
- **(b) The error.** The faulty criteria implement the documented errors; only Phase C's B2-05 is judged partly off.
  Two things limit the detections:
  - In five pairs the error is present and raises the statistic, but not past the claim's threshold at the brief's
    size, so the faulty criterion makes no false claim. These are Phase B's B2-03 and B2-06 and Phase C's B2-03, B2-06
    and B2-07.
  - In Phase C, six detections would also occur with the fixed criterion. They do not show the error.
- **(c) The fixed criteria.** 10 of the 11 failed clean passes come from a fixed criterion that is not a correct test
  of the claim on the declared worlds. The causes:
  - a threshold without a test at 40 samples (B2-08 to B2-11);
  - a point estimate against a threshold (B3-04);
  - an ordinary t test on autocorrelated months (B3-12);
  - partialling a noisy proxy of a common size factor (Phase B: B3-05);
  - a raw-scale regression where a log-scale one would have been clean (Phase B: B3-07);
  - a correction that cannot hold in `plus`, because it removes the path through which `plus` makes the claim true
    (Phase B: B3-11, B3-12).

  The eleventh is Phase B's B2-09, where the fixed criterion's allowed guard met 0.4.0's K1 rule. Under 0.5.0 that twin
  would be WEAK.
- **The gate.** At most one miss and one failed clean pass involve the gate, and both come from its design:
  - the outcome-level scope (Phase B's B2-06);
  - the 0.4.0 K1 rule, changed in 0.5 (Phase B's B2-09).
- **Adequate pairs.** On the pairs the auditors judged adequate, the gate detected 21 of 22 errors and passed 22 of 22
  corrections. This count is selected after the fact, is small, and is not a class verdict.

### Where the two auditors differ: an error below the claim's threshold

The same mechanism got two labels. The error raises the statistic, but at the brief's size not past the claim's
threshold, so the faulty criterion never holds where the claim is false.
- The Phase B auditor called it a **tool** limit (B2-06): "an outcome-level check cannot see a sub-threshold inflation".
- The Phase C auditor called it **case-size** (B2-03, B2-06, B2-07).

Both readings are defensible. The gate tests decisions, not statistics: a criterion whose error never changes its
decision at the study's size makes no false claim that the gate could catch. Phase D treats this as a scope limit to be
measured, not as a pass or a miss.

## The designer's verification

Every finding that changes a statement in the reports was rechecked with the designer's own scripts (`designer/`) or
against the case files.

| Finding | Check | Result |
|---|---|---|
| Phase C B2-03: copies leak; the threshold decides | `verify_c.py` | Faulty balanced accuracy on `minus`: mean 0.597, q95 0.629 (threshold 0.65, 2 of 200 hold). Fixed: 0.502. |
| Phase C B2-06: the leak lifts the AUC | `verify_c.py` | Faulty mean 0.643, q95 0.703 (threshold 0.75, 0 of 200). Fixed: 0.499. |
| Phase C B3-12: the excess comes from the AR(1) waves, not the season | `verify_c.py`, 2000 samples | Fixed holds in `minus` 0.107 as declared, 0.188 without the season, 0.017 without the waves. |
| Phase B B2-06: the leak operates, the threshold is not crossed | `verify_b.py` | Faulty mean 0.614 (the audit says 0.620), q95 0.675 (threshold 0.75, 0 of 200). Fixed: 0.496. |
| Phase B B3-07: the 15% error is in the recorded area only | `phase_b/cases/B3-07/faulty.py` lines 16–17 | Confirmed: the totals use the true area. |
| Wilson bound of 8 of 12 printed as 0.432 | `verify_b.py` | 0.431492, so 0.431. |

The other Part 2 points are the auditors' readings, labelled as such in their files.

## Limits

- **Post hoc.** The attribution categories and the questions were set by the designer after the results were known.
- **One reader per phase.** Each phase had one auditor, a model of the same family that wrote the gate and the cases.
  No human domain reader took part.
- **Small subsets.** The adequate subsets are small and selected after the fact. They cannot stand in for a class
  verdict.
- **Overlap.** Phases B and C share sources: 19 Phase C pairs overlap a Phase B case.

The reports carry dated correction notes for the verified points (`../phase_b/REPORT.md`, `../phase_c/REPORT.md`, both
2026-11-17).
