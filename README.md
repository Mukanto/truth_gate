# Truth_Gate

**A kit for running computational studies whose results cannot quietly bend their own criteria.**

You state in advance what would count as success or failure, then you run the model, simulation, ML pipeline or
hardware experiment. The hard part is keeping that promise when the people (or AI agents) who design the study can
easily see the result before they commit, and when a criterion that cannot fail looks exactly like one that passed.
Truth_Gate has three parts:

| Part | What it is | Where |
|---|---|---|
| **Methods protocol** | 16 rules for before, during and after a run. Each rule comes with the real failure that produced it. A one-page checklist for the freeze. | [`protocol/`](protocol/PROTOCOL.md) |
| **Templates and tools** | A pre-registration template, a prompt for a blind auditor, a SHA-256 freeze tool, and a runner that refuses to start unless the freeze verifies. Standard library only. | [`protocol/templates/`](protocol/templates/), [`protocol/tools/`](protocol/tools/freeze.py) |
| **The gate** | A Python tool that does *mutation testing for acceptance criteria*. Before the study is frozen, and without real data, it runs each criterion on synthetic worlds, deliberately broken controls, noise and all-zero data, and writes a hash-addressed certificate saying whether each criterion can actually fail. | [`kapi/`](kapi/), reference in [`docs/GATE.md`](docs/GATE.md) |

The name refers to the gate a claim has to pass before a test of it can tell you anything about the truth. A
certificate is not a verdict on truth (see [Limits](#limits)).

Version 0.3.0, MIT license. Until its first public release the project was called *Kapı* (Turkish for "gate"). In 0.3
the Python package is still imported as `kapi`, and the certificates record `kapi_version`. The older records in
`docs/` and the hardware case studies keep the old name.

## Who it is for

* Anyone who runs a model or an experiment against criteria stated in advance: simulations, numerical methods, machine
  learning evaluations, hardware experiments.
* **Especially when an AI agent writes the code.** An agent can see a result before you commit to the criteria, and it
  is good at producing criteria that pass. The protocol was developed in exactly that setting, and it assigns separate
  roles to the designer, the coder, a blind auditor and a verifier.
* Reviewers who want to check whether a study's criteria could have failed at all.

## A worked example: GHZ states on a 156-qubit IBM processor

Two pre-registered runs on an IBM Heron r2 processor, testing whether an error model built from the device's own
calibration predicts the measured quality of n-qubit GHZ states. Everything is in the repository: the
pre-registrations, the revision logs, the certificates, the freeze manifests, the raw counts, the calibration
snapshots, the transpiled circuits, the blind audits and the reports ([`examples/ghz_heron/`](examples/ghz_heron/REPORT.md),
[`examples/ghz_heron_run2/`](examples/ghz_heron_run2/REPORT.md)).

* **Before any hardware time was used,** the gate found 10 real defects in the criteria, and all were fixed. Among
  them: missing negative controls, a criterion that held on random data, a vacuous `0 = 0` equality, and a control of
  the wrong size.
* **After run 1,** a blind audit by a fresh agent found the decisive problem. The error model applied readout error
  once to a fidelity whose coherence part loses it twice. Correcting it reverses two of the three verdicts. The
  verdicts were reported as pre-registered, together with the flaw. The gate could not have seen this, because the
  defect was in the model, not in the logic of the criteria.
* **Run 2 tested the corrected model.** Its audit found that the device had not been recalibrated, so the run was a
  data replicate and not a model test. It also found that run-to-run drift exceeded the shot-noise intervals and that
  one test was underpowered. Each finding became a protocol rule.
* **What stands:**
  * Genuine multipartite entanglement without error mitigation up to 16 qubits (24 at the threshold on point values).
  * Large-state fidelities replicate across runs: F(16) ≈ 0.61, F(32) ≈ 0.385, F(48) ≈ 0.245.
  * The calibration-based model overpredicts fidelity by 5–16%, even when it is made consistent with the estimator.

The lesson matches the other cases: **the gate catches defects in the logic of criteria, and the rest of the protocol
(blind audit, independent recomputation) catches what the gate cannot see.** That is why they are published together.

## Getting started

### Use the protocol (no code needed)

1. Read [`protocol/PROTOCOL.md`](protocol/PROTOCOL.md) once. Keep [`protocol/CHECKLIST.md`](protocol/CHECKLIST.md) open.
2. Copy [`PREREG_TEMPLATE.md`](protocol/templates/PREREG_TEMPLATE.md). Write the criteria, the negative controls and
   both readings of every interpretation **before anything is run**. Keep what you already know separate from what
   the study is meant to find out.
3. Optionally, write the criteria as a gate study and run the gate (below). Fix each flag, or reject it with a written
   reason, and keep the certificates.
4. Freeze the files that define the study:

   ```text
   python protocol/tools/freeze.py write PREREG.md study.py run.py run_guarded.py -o FREEZE.json
   python protocol/tools/freeze.py verify FREEZE.json
   ```

5. Run through [`run_guarded.py`](protocol/templates/run_guarded.py) (copy it next to your study), which refuses to
   start unless the freeze verifies and the entry script is in it, and checks the freeze again afterwards:
   `python run_guarded.py FREEZE.json run.py`.
6. Report the pre-registered table unchanged. Give the frozen files and the raw outputs to a fresh auditor with
   [`BLIND_AUDIT_PROMPT.md`](protocol/templates/BLIND_AUDIT_PROMPT.md). Recompute by a separate route every claim that
   could change a verdict.

### Run the gate

Python 3.11 or newer and `numpy`. No network, no optimizer, no fitting.

```text
pip install -e .
python -m kapi check examples/02_inert_minus_world/faulty.py --out cert.json
python -m kapi verify cert.json examples/02_inert_minus_world/faulty.py
```

The first command prints a table and writes `cert.json`. Here the verdict is `UNTESTED` (exit code 6), because the
`minus` world is a copy of the `plus` world, so the gate could not test whether the criterion can fail. `fixed.py` in the
same folder is `FALSIFIABLE`. The second command re-runs the study and compares the certificate hash. All examples are
listed in [`examples/README.md`](examples/README.md).

A study is one Python file:

```python
import numpy as np
from kapi import Study, Criterion, World, Control

STUDY = Study(
    name="mean of x is positive",
    criteria=[Criterion("mean_gt_1", lambda d: bool(np.mean(d["x"]) > 1.0))],
    worlds={
        "plus":  World(lambda rng: {"x": rng.normal(2.0, 1.0, 40)}),               # the criterion should hold
        "minus": World(lambda rng: {"x": rng.normal(0.0, 1.0, 40)},                # one declared change: it should fail
                       derived_from="plus", change="mean 2 -> 0"),
    },
    controls=[Control("negate", ["mean_gt_1"], transform=lambda d, rng: {"x": -d["x"]})],  # breaks the theory
)
```

The gate runs seven checks:

| Check | Question |
|---|---|
| K1 | Is the criterion defined in every declared world? |
| K2 | Can it hold in `plus`, fail in `minus`, and tell them apart? |
| K3 | Does each premise it claims to test actually move it? |
| K4 | Does it fail under a control that breaks the theory? |
| K5 | Does it refuse to hold on random noise and on all-zero data? (cannot be disabled) |
| K6 | Does the study stay away from files, the network and processes, and is it reproducible? |
| K7 | Is every regime covered, and does each criterion return what it declares? |

The verdicts are `FALSIFIABLE`, `WEAK`, `UNTESTED`, `NOT_FALSIFIABLE` and `UNDEFINED`. The full reference (the study
API, every flag, the leak guard, the certificate format) is in [`docs/GATE.md`](docs/GATE.md). The formal rules and
statistics are in [`docs/SPEC.md`](docs/SPEC.md).

## What the evidence says

The full account, with every number, is in [`docs/EVALUATION.md`](docs/EVALUATION.md). In short:

* **On synthetic test cases, the gate did what was pre-registered, with two failures.** In v0, 6 of 7 pre-registered
  criteria held. The one that failed scored 51/52, and the designer had defined it wrongly. In v0.2 all 9 held. In
  v0.3, 8 of 9 held. The one that failed scored 41/42: a regression case became UNTESTED by design, and the
  pre-registered rule counts that as a miss.
* **A retrospective pilot was bad news.** Twenty-five past studies were converted blind into gate studies and run with
  v0.2. Four pre-registered criteria failed. A case review traced 35 of the 37 flagged clean units to how the converter
  built the synthetic worlds, not to defects in the criteria. This motivated v0.3.
* **Three prospective case studies:** one numerical study and the two hardware runs above. In each, the gate caught
  real defects in the logic of the criteria before the freeze (6, 8 and 2 fixed flags). In each, the decisive defect
  lay outside its scope and was found by the blind audit and independent recomputation. Three cases give no rates.
* **The evaluation is not independent.** The test cases were written by AI sessions that knew the spec, from the same
  model family that wrote the code. There is no human-authored external benchmark yet; building one is part of 0.4.

## Limits

What the gate is not:

* It is not a proof that a hypothesis is true. A FALSIFIABLE certificate does not mean the hypothesis is true or that
  the study is well designed in every respect.
* It does not modify or repair criteria. It only reports.
* It does not see your model, your data or your run, so it cannot find flaws in how a model is interpreted or in how
  the real run is controlled.

What follows from that:

* **The gate sees only the worlds you declare.** Whether a criterion really tests a claim is a semantic property of
  the criterion, and no general program can decide such properties (Rice's theorem is the closest formal analogue).
  The gate narrows the question to something it can check: can the criterion fail in the worlds you declared, and does
  it resist generic noise? Everything it records is visible in the certificate, so a reviewer can judge the
  declarations. The blind audit covers the rest.
* **Writing synthetic worlds and turning criteria into Python functions takes time,** and a weak `minus` world gives a
  weak certificate. 0.4 is aimed at this.
* **Known weaknesses.** A criterion written to recognise the generic probes (for example "return False if the data
  look like N(0, 1) noise") can evade K5. The `minus` world, K3 and K4 are the remaining defences, and code review is
  required.
* **Python only.** Your study can be in any language, but the gate's criteria and worlds are Python in 0.3.
* The gate's other technical limitations (exact-identity detection of the `minus` world, the strict declared alpha,
  probes on precomputed quantities, the leak guard not being a sandbox) are listed in
  [`docs/GATE.md`](docs/GATE.md#known-limitations-of-the-gate).

## Roadmap: 0.4 (planned, not built)

* **Language-agnostic core.** Worlds as data files (CSV, JSON, Parquet, NPZ) or as a generator command written in any
  language. Criteria either as ready-made YAML patterns (threshold, rate, mean difference, confidence interval,
  "largest n such that"), with no code, or as a command in any language that reads JSON on stdin and prints `HOLDS`,
  `FAILS` or `UNDEFINED`.
* **Automatic mutation worlds.** You give one realistic example dataset and name the columns the claim rests on. The
  gate derives the `minus` worlds and controls from a mutation library built from the failures behind the protocol: remove
  the effect, shuffle labels, swap columns, unit errors (×1000, a stray ε), constant data, added noise, subsampling,
  stale calibration.
* **Easier to adopt.** A one-line install (`pipx`), a GitHub Action that checks the pre-registration and the freeze on
  pull requests and adds a badge, a pre-commit hook, and a template repository with the pre-registration, freeze and
  audit prompt ready to use.
* **The new name in code.** The package becomes `truth_gate`, with `kapi` kept as an alias so that existing studies,
  frozen examples and certificates keep working.
* **Stronger evidence.** An external test set built from documented real errors in published research, where the
  correct answer comes from the literature, not from us. The evaluation criteria will be pre-registered before the set
  is built, and the result reported as coverage per error class.

Feedback is welcome as issues, especially real cases in which the gate caught, or missed, a defect.

## Repository layout

```text
protocol/     PROTOCOL.md, CHECKLIST.md, templates (pre-registration, blind audit prompt, guarded runner), freeze tool
kapi/         the gate, imported as kapi in 0.3 (study, sampling, stats, probes, checks, minus, guard, certificate, cli)
examples/     faulty/fixed study pairs, a convergence-criteria study, and the two GHZ hardware runs
docs/         GATE.md, SPEC.md, EVALUATION.md, CASE_STUDY_PROSPECTIVE.md
evaluation/   the evaluation case sets (hashed, unchanged) and their runners
eval/         the evaluation harness (computes the pre-registered criteria from a results table)
tests/        unit tests and toy studies (python -B -m unittest discover -s tests)
```

## How this was built

Truth_Gate was designed by its author together with an AI assistant (Claude), which drafted the specs, designed the case
studies and wrote the code under the author's review. The independent evaluation sets E2, E4 and E5 were written by a
separate AI session from the spec text, without the implementation. The hardware runs were submitted from the author's
account with the author's approval. The evaluation is therefore not independent of the model family; see
[What the evidence says](#what-the-evidence-says).

## License

MIT. See [`LICENSE`](LICENSE).
