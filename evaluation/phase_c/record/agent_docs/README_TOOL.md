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
| **The gate** | A Python tool that does *mutation testing for acceptance criteria*. Before the study is frozen, and without real data, it runs each criterion on synthetic worlds, deliberately broken controls, noise and all-zero data, and writes a hash-addressed certificate saying whether each criterion can actually fail. Since 0.4 a study can be a manifest with no Python code, and a criterion can be a program in any language. | [`truth_gate/`](truth_gate/), reference in [`docs/GATE.md`](docs/GATE.md) and [`docs/MANIFEST.md`](docs/MANIFEST.md) |

The name refers to the gate a claim has to pass before a test of it can tell you anything about the truth. A
certificate is not a verdict on truth (see [Limits](#limits)).

Version 0.5.0 (spec 0.7), MIT license. Until its first public release the project was called *Kapı* (Turkish for
"gate"). Since 0.4 the package is `truth_gate` and the command is `truth-gate`. The package `kapi` and `python -m kapi`
remain as a deprecated alias (they stay at least until 1.0), so existing studies and the frozen examples keep working.
Certificates now record `tool` and `tool_version` instead of `kapi_version`; a 0.3 certificate is verified with the
`v0.3.0` tag (`verify` exits with 7 and says so). The older records in `docs/` and the hardware case studies keep the old
name.

## Who it is for

* Anyone who runs a model or an experiment against criteria stated in advance: simulations, numerical methods, machine
  learning evaluations, hardware experiments.
* **Especially when an AI agent writes the code.** An agent can see a result before you commit to the criteria, and it
  is good at producing criteria that pass. The protocol was developed in exactly that setting, and it assigns separate
  roles to the designer, the coder, a blind auditor and a verifier.
* Reviewers who want to check whether a study's criteria could have failed at all.

## Getting started

### Run the gate

Python 3.11 or newer and `numpy`. No network, no optimizer, no fitting. Install it with `pipx install
git+https://github.com/Mukanto/truth_gate`, or from a clone with `pip install -e .`.

```text
truth-gate check examples/02_inert_minus_world/faulty.py --out cert.json
truth-gate verify cert.json examples/02_inert_minus_world/faulty.py
```

The first command prints a table and writes `cert.json`. Here the verdict is `UNTESTED` (exit code 6), because the
`minus` world is a copy of the `plus` world, so the gate could not test whether the criterion can fail. `fixed.py` in the
same folder is `FALSIFIABLE`. The second command re-runs the study and compares the certificate hash. All examples are
listed in [`examples/README.md`](examples/README.md).

### Quick start without Python code

A study can be a manifest: a TOML file with the data, the claim and the ways it should break. This is
`tests/manifests/trial_example.toml`, with `synthetic_trial.csv` next to it.

```toml
[study]
name = "the new fertiliser raises mean yield by at least 0.5 t/ha"

[data]
rows_exchangeable = true            # rows are i.i.d. plots, so their order must not matter (adds a K8 check)
[data.columns]
plot  = { type = "str",   role = "id" }
group = { type = "str",   role = "group" }
yield = { type = "float", role = "outcome" }

[worlds.plus]
file = "synthetic_trial.csv"        # a realistic dataset in which the claim is true; never the real data
provenance = "simulated from last season's control plots plus a 0.8 t/ha effect"

[worlds.minus]
derive = "plus"
change = "no effect: treated yields are drawn from control plots"
mutations = [ { op = "null_effect", outcome = "yield", group = "group", reference = "control" } ]

[[criteria]]
id = "C1"
pattern = "difference"
a = "yield"
a_where = { column = "group", equals = "treated" }
b = "yield"
b_where = { column = "group", equals = "control" }
stat = "mean"
op = ">="
value = 0.5

[[controls]]
id = "labels_shuffled"
criteria = ["C1"]
mutations = [ { op = "shuffle", column = "group" } ]
```

```text
truth-gate check tests/manifests/trial_example.toml
```

The criterion is a ready-made pattern (`threshold`, `difference`, `ratio_band`, `within`, `rate`, `ci_excludes`,
`largest_true`, `monotone`, `all_of`, `any_of`). The `minus` world and the control are made from the `plus` data by
mutations (`shuffle`, `null_effect`, `scale`, `offset`, `constant`, `noise`, `subsample`, `swap`, `reverse`, `sign_flip`,
`permute_rows`). With `rows_exchangeable = true` the gate also checks that the row order does not change the outcome
(K8). The whole format is in [`docs/MANIFEST.md`](docs/MANIFEST.md).

**A criterion in any language.** A criterion can also be a program: `command = ["node", "criterion.js"]` (an argv list).
The gate sends it each sample as one JSON line (protocol `tg-line/1`); it answers `HOLDS`, `FAILS` or `UNDEFINED`. R,
Julia and Node all work the same way. A complete example in Node is in
[`examples/node_criterion/`](examples/node_criterion/README.md). The leak guard cannot see inside another program, so
the certificate carries the study note `K6_EXTERNAL_UNGUARDED` (see [Limits](#limits)).

**Starting from a dataset.** `truth-gate suggest pilot.csv --outcome yield --group group --reference control` writes a
starter manifest with a `minus` world and controls, and no criterion. Every generated declaration carries
`origin = "suggested"`, which caps the verdict at WEAK until you review it. Feed it a realistic synthetic or pilot
dataset, never the real study data.

### The command line

| Command | Does |
|---|---|
| `check TARGET [--out CERT] [--quick]` | runs the gate on a Python study or a manifest and writes the certificate |
| `verify CERT TARGET` | re-runs the study and compares the certificate hash (exit 7 if another version made it) |
| `suggest DATA.csv ...` | writes a starter manifest from one dataset |
| `init [DIR] [--ci]` | writes `PREREG.md`, `truthgate.toml`, `BLIND_AUDIT_PROMPT.md`, `run_guarded.py` and, with `--ci`, the workflow |
| `freeze write ...`, `freeze verify ...` | the SHA-256 freeze tool of [`protocol/tools/freeze.py`](protocol/tools/freeze.py), in the package |
| `badge CERT [--out FILE]` | a shields.io endpoint JSON for a full-mode certificate |
| `explain FLAG` | what a flag or note means and the protocol rule behind it |

### In CI

```yaml
- uses: actions/checkout@v4
- uses: Mukanto/truth_gate@v0.5.0
  with:
    target: truthgate.toml
    freeze: FREEZE.json                                  # optional
    quick: "false"
    fail-on: "NOT_FALSIFIABLE,UNDEFINED,UNTESTED"
```

The Action writes the result table and the study notes to the job summary and uploads the certificate. It always fails
the job when a declaration still carries `origin = "suggested"` (`SUGGESTED_UNREVIEWED`), whatever `fail-on` says.
`truth-gate init --ci` writes this workflow. The pre-commit hooks `truth-gate-freeze` and `truth-gate-check` are in
[`.pre-commit-hooks.yaml`](.pre-commit-hooks.yaml). The Action is tested with a fake environment; it has not been run on
GitHub yet.

### A study in Python

A study can still be one Python file:

```python
import numpy as np
from truth_gate import Study, Criterion, World, Control

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

The gate runs eight checks:

| Check | Question |
|---|---|
| K1 | Does the criterion fail, or abstain on most `plus` samples, in a declared world? (An abstention elsewhere counts as no claim.) |
| K2 | Can it hold in `plus`, fail in `minus`, and tell them apart? |
| K3 | Does each premise it claims to test actually move it? |
| K4 | Does it fail under a control that breaks the theory? |
| K5 | Does it refuse to hold on random noise and on all-zero data? (cannot be disabled) |
| K6 | Does the study stay away from files, the network and processes, and is it reproducible? |
| K7 | Is every regime covered, and does each criterion return what it declares? |
| K8 | Does a transformation that must not matter (row order, units) leave every outcome unchanged? (only for declared invariances) |

The verdicts are `FALSIFIABLE`, `WEAK`, `UNTESTED`, `NOT_FALSIFIABLE` and `UNDEFINED`. The full reference (the study
API, every flag, K8, the leak guard, the certificate format) is in [`docs/GATE.md`](docs/GATE.md), the manifest format in
[`docs/MANIFEST.md`](docs/MANIFEST.md). The formal rules and statistics of 0.3 are in [`docs/SPEC.md`](docs/SPEC.md); the
design of 0.4 is in [`docs/design/spec-0.6.md`](docs/design/spec-0.6.md).

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
* **Writing synthetic worlds takes time,** and a weak `minus` world gives a weak certificate. 0.4 reduces the labour
  (patterns, mutations, `suggest`), but the mutations are generic: they do not know your domain, and they do not replace
  a `minus` world that models your claim.
* **Known weaknesses.** A criterion written to recognise the generic probes (for example "return False if the data
  look like N(0, 1) noise") can evade K5. The `minus` world, K3 and K4 are the remaining defences, and code review is
  required.
* **Criteria in any language, worlds not yet.** Criteria can be programs in any language (`tg-line/1`). Worlds,
  controls and premises written as programs are not in 0.4: worlds come from data files, from Python or from mutations.
* **External programs are not covered by the leak guard.** A command criterion runs in another process; the guard
  cannot see what it reads. The certificate says so (the note `K6_EXTERNAL_UNGUARDED` and a non-claim), and the badge
  reads "(unguarded)". The gate records the hash of the executable and of the files the program uses; the libraries it
  loads (R packages, `node_modules`) are not hashed.
* **The GitHub Action installs from PyPI without hash pinning.** It installs numpy (and the build tools needed to
  install the package) from PyPI without pinning their hashes, so a compromised dependency would not be noticed by the
  Action.
* **K8 doubles the error budget.** When invariances are declared, the study-wide family-wise error rate is at most
  `2 · alpha_family`, because K8 has its own Bonferroni family. The certificate states this.
* **`suggest` must not be fed the real data.** A plus world built from the real data makes the plus and minus checks
  circular, and the gate cannot tell a synthetic file from the real data. `provenance` is required and goes into the
  certificate, so a reviewer can see the claim.
* The gate's other technical limitations (exact-identity detection of the `minus` world, the strict declared alpha,
  probes on precomputed quantities, the leak guard not being a sandbox) are listed in
  [`docs/GATE.md`](docs/GATE.md#known-limitations-of-the-gate).
