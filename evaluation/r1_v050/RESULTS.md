# Truth_Gate 0.5.0: official R1 and R2 (spec 0.7, section 6; post-freeze R-1 to R-4)

Run on 2026-11-13 from a clean worktree of tag `v0.5.0` (commit `5661709`), full mode, default settings, one check at
a time, before the release was pushed (R-4). Python 3.14.2, numpy 2.4.1. 267 studies, 244 s, no recording failure.

* `record_r1_v050.py`: the recorder (a copy of the frozen R0 recorder with the tag and the output folder changed); it
  verified `FREEZE_BASELINE_V041.json` and every study's SHA-256 against the R0 index before running.
* `certs/`, `STUDIES_V050.json`: the 0.5.0 certificates and their index.
* `R1_REPORT.json`: the frozen comparison script `evaluation/baseline_v041/compare_r1.py`, run as
  `py evaluation/baseline_v041/compare_r1.py compare evaluation/r1_v050/certs --report evaluation/r1_v050/R1_REPORT.json`.
* `designer_check.py`, `designer_check_output.txt`: the designer's separate check, written from the spec text without
  reading `compare_r1.py`.

## R1 (necessary): holds

Components are classified from the 0.4.1 certificates only (section 6).

| Group | Components | Result |
|---|---|---|
| Section 4 item 1 (no UNDEFINED on a K1 stream) | 251 | 251 identical results |
| Item 2 (hard UNDEFINED, or abstention on more than half of `plus`) | 6 | 6 identical results |
| Item 3 (abstention only) | 11 | 11 as section 4 prescribes |
| `BAD_RETURN` / `K7_COMPONENT_MISMATCH` group | 3 | `hard_undefined >= E` in all 3 |
| R-1 unseeded studies (verdict and flag sets only) | 4 studies, 4 components | 4 match |
| Deterministic studies (within the groups above) | 35 studies, 37 components | 37 match |
| Item 4 (study verdict) | 267 studies | 0 differ |

`hard_undefined` equals the 0.4.1 error count `E` on the K1 streams for every component of items 1 to 3, and on every
stream of every certificate the `errors` counts add up to `hard_undefined` (designer's check). The two scripts agree.
The eleven item-3 components are the ten Phase B components of R2 and `evaluation/cases/E2/E2-07_faulty.py`, which moves
from UNDEFINED to WEAK as R-2 recorded before any code was written.

## R2 (Phase B rerun, development data, not evidence): as predicted

All ten components of `docs/design/spec-0.7-R2-prediction.json` have the predicted verdict and flags: the five faulty
twins NOT_FALSIFIABLE, the five fixed twins WEAK. The rule was chosen after these cases were seen; R2 checks only that
the implementation does what the frozen prediction says.
