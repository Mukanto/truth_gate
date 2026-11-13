# Examples

Each example is a study file that the gate can check. Run everything from the repository root. Pass `--out` so that
certificates go where you want them (the default is a `STUDY.kapi.json` file next to the study; `certs/`, `cert.json` and
`*.kapi.json` are ignored by git). `kapi` does not create the output folder, so create `certs/` first.

```text
mkdir certs
python -m kapi check examples/01_tautology/faulty.py --out certs/01_faulty.json
python -m kapi verify certs/01_faulty.json examples/01_tautology/faulty.py
```

`check` prints a table and exits with a code that depends on the verdict (0 FALSIFIABLE, 1 WEAK, 2 NOT_FALSIFIABLE,
3 UNDEFINED, 6 UNTESTED). `verify` re-runs the study and exits 0 if the certificate hash is identical.

The three pairs below are a **faulty** study with one planted flaw, and a **fixed** twin that differs only in that flaw.
They are copies of cases from the evaluation sets in [`../evaluation/cases`](../evaluation/cases) (with an internal
origin note removed from the first pair), so the verdicts below are what the evaluation expects.

| Study | What is wrong | Verdict | Exit | Flags |
|---|---|---|---|---|
| [`01_tautology/faulty.py`](01_tautology/faulty.py) | The criterion computes its targets from the labels and compares them with the same rule applied to the same labels. It never reads `observed`. It holds whatever the data are. | `NOT_FALSIFIABLE` | 2 | `K5_HOLDS_ON_NOISE`, `K5_HOLDS_ON_DEGENERATE`, `K2_FAILS_UNREACHABLE`, `K2_NO_SEPARATION`, `K2_HIGH_SIZE`, `K4_CONTROL_ALSO_HOLDS`, `HIGH_RATE:*`, `K2_MINUS_UNREAD` (info) |
| [`01_tautology/fixed.py`](01_tautology/fixed.py) | The criterion compares `observed` with the rule. | `FALSIFIABLE` | 0 | none |
| [`02_inert_minus_world/faulty.py`](02_inert_minus_world/faulty.py) | The `minus` world is declared as "spring constant 40 -> 20 N/m" but is a copy of `plus`. The gate cannot tell whether the criterion can fail. | `UNTESTED` | 6 | `K2_MINUS_IDENTICAL` |
| [`02_inert_minus_world/fixed.py`](02_inert_minus_world/fixed.py) | The `minus` world really uses 20 N/m. | `FALSIFIABLE` | 0 | none |
| [`03_unit_epsilon_bug/faulty.py`](03_unit_epsilon_bug/faulty.py) | The offset that should switch the illumination off is multiplied by `EPS` (1e-12) instead of the unit `UNIT`, so `minus` is `plus` shifted by 3e-12. The data differ, so this is not UNTESTED; the criterion never fails. | `NOT_FALSIFIABLE` | 2 | `K2_FAILS_UNREACHABLE`, `K2_NO_SEPARATION`, `K2_HIGH_SIZE` |
| [`03_unit_epsilon_bug/fixed.py`](03_unit_epsilon_bug/fixed.py) | The offset is `LEVEL * UNIT`. | `FALSIFIABLE` | 0 | none |
| [`convergence_criteria/study.py`](convergence_criteria/study.py) | A generic synthetic-world study with three criteria and three controls (see below). | `NOT_FALSIFIABLE` (C1), `WEAK` (C2), `FALSIFIABLE` (C3); study verdict `NOT_FALSIFIABLE` | 2 | C1: `K5_HOLDS_ON_NOISE`, `K5_HOLDS_ON_DEGENERATE`; C2: `K5_INCONCLUSIVE:noise`, `K5_INCONCLUSIVE:zeros` |

The verdicts above were produced by `python -m kapi check` with this version (0.4.1) of the package (`truth-gate check`
gives the same); the certificates are reproducible (`verify` exits 0).

### A criterion in another language: [`node_criterion/`](node_criterion/README.md)

A manifest study whose criterion is a Node program that speaks the line protocol `tg-line/1` (the gate sends each
sample as one JSON line, the program answers `HOLDS`, `FAILS` or `UNDEFINED`). It needs `node` on `PATH`. Run it with
`truth-gate check examples/node_criterion/truthgate.toml --out node_example.json`. The certificate carries the study
note `K6_EXTERNAL_UNGUARDED`, because the leak guard cannot see inside another program. The manifest format is in
[`../docs/MANIFEST.md`](../docs/MANIFEST.md).

### A real hardware run: [`ghz_heron/`](ghz_heron/)

A complete pre-registered study on a 156-qubit IBM Heron r2 processor. It runs from pre-registration through gate certificates,
revisions with reasons, freeze, the hardware run, analysis and blind audit. Start with
[`ghz_heron/REPORT.md`](ghz_heron/REPORT.md). The raw counts, calibration snapshot and transpiled circuits are in
`ghz_heron/run/`.

[`ghz_heron_run2/`](ghz_heron_run2/REPORT.md) is the follow-up: a corrected model, pre-registered and run on new shots. It is a data replicate (the calibration was unchanged), and its audit added four rules to the protocol.

To check that the frozen files are unchanged, run `python protocol/tools/freeze.py verify examples/ghz_heron/FREEZE_GHZ.json`
(and `examples/ghz_heron_run2/FREEZE_GHZ2.json`). After a clone it prints `WRITABLE` warnings, because git does not
keep read-only flags; the hashes are what count, and `FREEZE OK` means they all match.

## What to look at

* **01, the tautology.** The faulty twin has the most flags. The two vacuity probes (K5) are what expose it: the
  criterion holds on random noise and on all-zero data, because it never looks at the data. Note also the information
  flag `K2_MINUS_UNREAD`: the `minus` world changed `observed`, which the criterion does not read.
* **02, the inert `minus` world.** This is the case the `UNTESTED` verdict was added for. Only one flag is raised. The gate does
  not say that the criterion is bad; it says the test of the criterion was not a test. The remedy is in the world, not
  in the criterion.
* **03, the unit/epsilon bug.** A typo in a unit factor produces a `minus` world that is *almost* identical to `plus`.
  The gate's identical-minus check is exact, so this is not UNTESTED but `NOT_FALSIFIABLE`. That is a known limit: the check
  detects only exact identity.
* **convergence_criteria.** A generic version of the synthetic-world study used in the prospective case study
  ([`../docs/CASE_STUDY_PROSPECTIVE.md`](../docs/CASE_STUDY_PROSPECTIVE.md)). Its certificate is not clean, on purpose:
  the four flags come from the gate's generic probes applied to a precomputed scalar (C1) and to a criterion that is
  undefined when no start qualifies (C2). Read the README in that folder for why those flags are accepted in the real
  study, with a written reason, and not "fixed" with a cosmetic control. C3 is clean.
