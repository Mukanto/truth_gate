# Phase D tools, round 5: fixes from review 3b (designer's specification, 2026-11-17)

Review 3b is `E:\Independent\tasks\phase_d_review3b\out\REVIEW3B.md`. It found 0 blocking, 0 major and 8 minor
findings, and judged the set freezable after small fixes. The designer accepted every finding; this file lists the
tool changes. Work only in `E:\Claude Projects\Kapi\phase_d_private\tools\`. Do not read or touch `recompute_d/`. Do
not edit `tests/acceptance_d/EXPECTED.md` or `EXPECTED.json`, and do not change the rule in `attributable.py`. Mark
changed lines `# D-R5-<n>`, and write tests for every item.

## 1. Free names by Python scoping (R3B-1): `mech_check_bodies.py`, `assemble.py`

- **Resolve names by Python's scoping rules.** Use the standard library `symtable` module, or an AST pass with one
  scope for each function, lambda and comprehension. A name bound only inside a comprehension, a nested function or a
  lambda parameter is not local to the enclosing function.
- **Test the skeleton's top-level names before the builtin test,** in the same order as PC's
  `mech_check_twins.check_body` (lines 188–191). A builtin that a skeleton redefines must therefore be reported as
  "reads module-level name".
- **Tests.** Each of these four bodies must get a name issue from `check_body` (given the skeleton names) and be refused
  by `assemble`. The skeleton is `toy_case.REFERENCE` with `THRESHOLD = 0.9` and `def max(*a): return 99` added at
  top level.

  ```python
  HEAD = "import numpy as np\n\n\n"
  # comprehension variable reused after the comprehension
  HEAD + "def criterion(d):\n    sizes = [N for N in range(3)]\n    return bool(len(d['x']) > N)\n"
  # name bound only in a nested function
  HEAD + "def criterion(d):\n    def helper():\n        THRESHOLD = 0.1\n        return THRESHOLD\n    return bool(np.mean(d['x']) > THRESHOLD)\n"
  # name bound only as a lambda parameter
  HEAD + "def criterion(d):\n    f = lambda THRESHOLD: THRESHOLD\n    return bool(np.mean(d['x']) > THRESHOLD)\n"
  # builtin shadowed by a skeleton function
  HEAD + "def criterion(d):\n    return bool(max(1, 2) > 50)\n"
  ```

  Also keep a body that uses comprehensions, nested helpers and lambdas legitimately, and check that it passes.

## 2. V1-stage errors (R3B-2): `validity_check.py`

- When the V1 stage errs, also record `v1_error_share`: the share of the 1000 `minus` samples on which either twin
  erred.
- Add the field `v1_final_drop_label`, which follows the draft's new rule:
  - when `v1_error_share ≤ 0.05` and `v1_rate_label` is V1a or V1b, it is that label;
  - in every other case it is null.
- When `v1_final_drop_label` is set, the pair is dropped with that label, and the error-repair row does not apply.
- Tests:
  - 1 exception in 1000 samples with a V1a rate gives `v1_final_drop_label` "V1a";
  - 60 exceptions in 1000 samples give `v1_final_drop_label` null.

## 3. Log location and earlier runs (R3B-3): `validity_check.py`, `check_validity_log_d.py`

- **The log has a fixed location,** `<parent of the case folder>/validity_log.jsonl`.
  - `validity_check.py` writes only there, and `--log` is removed or must equal that path.
  - `check_validity_log_d.py` reads `<cases>/validity_log.jsonl`, and refuses any other path.
- **`check_validity_log_d.py` lists every standard run with `case == id`, in log order, for each pair.**
  - **Final drops.** Refuse the pair, with the reason "earlier final drop", when an earlier decisive run on other hashes
    ended in a final drop. A final drop is one of these:
    - a V1, V2 or timing failure computed without an error in that stage;
    - a non-null `v1_final_drop_label`.
  - **Repairs.** `FREEZE_VALIDITY.json` gets a per-pair list `"repairs": [{"file", "reason", "after_run_sha256"}]`.
    Refuse the pair when the number of earlier decisive runs on other hashes exceeds the number of its repairs.
- Update the schema in the docstring.
- Tests:
  - the reviewer's probe: a decisive V1b drop on hashes H1, an edit of `reference.py`, then a passing decisive run on
    H2, must be refused;
  - a legitimate repair (an error on H1, one repair listed, a pass on H2) must pass.

## 4. Which per-arm timing run decides (R3B-4): `validity_check.py`, `check_validity_log_d.py`

- **Decisive marking.** In `--arm` mode, the first non-dev run on a given (skeleton hash, fixed-body hash) is logged
  with `"decisive": true`, and later runs on the same hashes with `"decisive": false`.
- **New option** `check_validity_log_d.py --timing-arms TIMING_ARMS.json`.
  - The file holds a list of `{"id", "arm", "skeleton_sha256", "body_sha256", "estimate_s", "redo": bool}`, written by
    the designer.
  - The check confirms that each entry matches a decisive `timing_arm` log run with the same hashes and the same
    estimate.
  - It also confirms that `redo` is true exactly when that estimate is above 1800 s.
- Tests.

## 5. Stale passages (R3B-6)

- In `miss_label.py`, `TEXTS["b"]` and its docstring line become: "the error's minus rate stayed below the gate's flag
  threshold".
- In `mech_check_bodies.py`, the docstring item that lists the summary calls refers to `SUMMARY_CALLS` and
  `BUILTIN_SUMMARY_CALLS` instead of the old list.
- In `check_skeletons_d.py`, "3 item 8" becomes "3 item 9".
- In `validity_check.py`, a full run also hashes `mech_check_bodies.py` and `check_skeletons_d.py` among the imported
  tool siblings.

## 6. Run and report

- Run the full suite with `py -I -B -m unittest discover -s tests` from `tools/`, and leave no `__pycache__`.
- Report:
  - the files changed;
  - the test count and pass/fail;
  - every interpretation you made.
