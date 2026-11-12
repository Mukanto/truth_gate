# Truth_Gate: gate reference

This page is the full reference for the gate. The overview, the protocol and the evidence are in the [README](../README.md); the formal rules and statistics are in [`SPEC.md`](SPEC.md) (0.3). The manifest format of 0.4 (studies without Python code, criteria in any language) is in [`MANIFEST.md`](MANIFEST.md). Version 0.4 follows spec 0.6; the design record is in [`design/`](design/).

## Quick start

```text
pip install -e .
python -m kapi check examples/02_inert_minus_world/faulty.py --out cert.json
python -m kapi verify cert.json examples/02_inert_minus_world/faulty.py
```

The first command prints a table and writes `cert.json`. For this example the verdict is `UNTESTED` (exit code 6),
because the `minus` world is a copy of the `plus` world. Compare with `fixed.py` in the same folder, which is
`FALSIFIABLE`. The second command re-runs the study and compares the certificate hash (exit code 0 if identical).
All examples and their verdicts are in [`../examples/README.md`](../examples/README.md).

```text
python -m kapi check STUDY.py --out CERT.json           # full run, writes the certificate
python -m kapi check STUDY.py --out CERT.json --quick   # 20 samples per stream; marked "quick", not certifiable
python -m kapi verify CERT.json STUDY.py                # re-run in the recorded mode, compare body_sha256
```

Without `--out` the certificate is written next to the study as `STUDY.kapi.json`. From Python:
`truth_gate.run_gate("STUDY.py", quick=False)` (or `kapi.run_gate`) returns the certificate envelope as a dict.

In 0.4 the command is `truth-gate` (also `python -m truth_gate`). `python -m kapi` runs the same command line, and the
package `kapi` re-exports the names of `truth_gate`; it is deprecated and stays at least until 1.0. `check` also takes a
manifest, `truth-gate check truthgate.toml`; see [`MANIFEST.md`](MANIFEST.md).

| Command | Does |
|---|---|
| `check TARGET [--out CERT] [--quick]` | runs the gate on a Python study (`.py`) or a manifest (`.toml`, `.json`); the table ends with the study notes |
| `verify CERT TARGET` | re-runs the study in the recorded mode and compares `body_sha256` |
| `suggest DATA.csv [--outcome COL] [--group COL --reference VALUE] [--effect COL ...] [--exchangeable] [--out FILE]` | writes a starter manifest from one dataset, which must not be the real study data |
| `init [DIR] [--ci]` | writes `PREREG.md`, `truthgate.toml`, `BLIND_AUDIT_PROMPT.md`, `run_guarded.py` and, with `--ci`, `.github/workflows/truth-gate.yml`; never overwrites a file |
| `freeze write FILE... -o FREEZE.json`, `freeze verify FREEZE.json` | the semantics of `protocol/tools/freeze.py`, which stays |
| `badge CERT [--out FILE]` | a shields.io endpoint JSON for a full-mode certificate |
| `explain FLAG` | what a flag or study note means, its usual cause and the protocol rule behind it |

### In CI and pre-commit

The repository root holds a composite GitHub Action (`action.yml`) and `.pre-commit-hooks.yaml`.

```yaml
- uses: Mukanto/truth_gate@v0.4.0
  with:
    target: truthgate.toml
    freeze: FREEZE.json          # optional
    quick: "false"
    fail-on: "NOT_FALSIFIABLE,UNDEFINED,UNTESTED"
```

The Action runs `check`, runs `freeze verify` if `freeze` is given, writes the result table and the study notes to the
job summary, sets the step output `certificate` (the path of the certificate) and uploads the certificate as an
artifact. It fails the job when the verdict is in `fail-on`, and **always** when any component carries
`SUGGESTED_UNREVIEWED`, whatever `fail-on` says. Its exit code is 4 for rejected inputs or a manifest error (no
certificate), 5 for a broken freeze, the code of `check` for a verdict in `fail-on` (1, 2, 3, 6) and 1 for
`SUGGESTED_UNREVIEWED`. The logic is in `truth_gate/ci.py`. The hooks are `truth-gate-freeze` (a freeze manifest given
in `args`, run on every commit, because a frozen file can change while its manifest does not) and `truth-gate-check`
(the quick mode on every changed `truthgate.toml` or `truthgate.json`). `truth-gate-check` calls a wrapper,
`python -m truth_gate.ci --pre-commit FILE...` (R-27): pre-commit may pass several files in one call, so the wrapper
checks each file in quick mode, writes the certificates to a temporary folder that it deletes afterwards (never next to
a manifest, so a commit cannot pick one up), prints one line per file (`FILE: VERDICT (exit N)`, or the reason there is
no verdict) and exits with the most severe code: 4 first, then 5, then the worst verdict (UNDEFINED, NOT_FALSIFIABLE,
UNTESTED, WEAK). Quick mode is not certifiable.

Run the unit tests from the repository root:

```text
python -B -m unittest discover -s tests
```

## Writing a study

A study is one Python file that defines a module-level `STUDY`. All callables are pure functions of their arguments; data
is a `dict[str, numpy.ndarray]`.

```python
import numpy as np
from kapi import Study, Criterion, World, Premise, Control, Budget, Targets

STUDY = Study(
    name="mean of x is positive",
    criteria=[Criterion("mean_gt_1", lambda d: bool(np.mean(d["x"]) > 1.0))],
    worlds={
        "plus":  World(lambda rng: {"x": rng.normal(2.0, 1.0, 40)}),
        "minus": World(lambda rng: {"x": rng.normal(0.0, 1.0, 40)}, derived_from="plus", change="mean 2 -> 0"),
        "null":  World(lambda rng: {"x": rng.normal(0.0, 1.0, 40)}),            # optional
    },
    premises=[Premise("shift", lambda d, rng: {"x": d["x"] - 2.0}, "tested", ["mean_gt_1"], magnitude=(2.0, 2.0))],
    controls=[Control("negate", ["mean_gt_1"], transform=lambda d, rng: {"x": -d["x"]})],
    budget=Budget(samples=100),
)
```

| Object | Fields |
|---|---|
| `Study` | `name`, `criteria`, `worlds` (must contain `plus` and `minus`; `null` optional), `premises=[]`, `controls=[]`, `regimes=["all"]`, `deterministic=False`, `budget=Budget()`, `targets=Targets()`, `allow_paths=[]`, `relational=[]` |
| `World` | `generate(rng) -> dict`, `derived_from=None`, `change=""` (declare how `minus` differs from `plus`; the text goes into the certificate) |
| `Criterion` | `id`, `fn(data) -> bool \| None \| dict`, `regime="all"`, `components=None`, `tolerances={}` (name -> `(value, scale)`), `control_waiver=None` |
| `Premise` | `id`, `mutate(data, rng) -> dict`, `role` (`"tested"` or `"assumed"`), `criteria`, `magnitude=None` (`(value, scale)`) |
| `Control` | `id`, `criteria`, exactly one of `transform(data, rng) -> dict` or `world` |
| `Budget` | `samples=200`, `quick_samples=20`, `base_seed=20261105` |
| `Targets` | `power=0.8`, `size=0.05` (the **declared alpha**: the false-positive rate the study claims), `alpha_family=0.05` |

* `fn` returns `True` (HOLDS), `False` (FAILS) or `None` (UNDEFINED). Any other type is UNDEFINED with the informational
  flag `BAD_RETURN`. With `components=[...]` the function returns a dict with exactly those keys; each component is
  judged separately as `id:component`.
* Exceptions in `fn`, `generate`, `mutate` or `transform` give UNDEFINED. The exception type name is recorded, never the
  message.
* `plus` is the world in which the criteria should hold. `minus` is `plus` with one declared change that should make
  them fail. `controls` break the theory on purpose; a criterion that still holds under its control is not testing
  the theory. `premises` perturb one assumption at a time.
* `deterministic=True` samples every stream once and compares outcomes directly instead of using Wilson bounds. Use it
  for deterministic models.
* `allow_paths` lists static read-only files the study may open. They are hashed into the certificate.
* `relational=[("a", "b")]` enables the shuffle probe, which permutes the first axis of `b` relative to `a`.

Since 0.4 a study can also be written as a manifest, with no Python code: worlds from data files, criteria from
patterns or from programs in any language, mutations from a library, and invariances for K8. A manifest is compiled into
the objects above and run by the same engine. The reference is [`MANIFEST.md`](MANIFEST.md).

The full rules, including the statistics and every interpretation that was fixed during implementation, are in
[`SPEC.md`](SPEC.md).

## The checks

| Check | What it does |
|---|---|
| **K1** definedness | Every criterion must be defined (not an exception or `None`) on `plus`, `minus` and `null` samples. |
| **K2** reachability, separation, resolution | The criterion must be able to hold in `plus`, fail in `minus`, and hold significantly more often in `plus` than in `minus`. Declared tolerances and magnitudes must be resolvable in float64. A `minus` world identical to `plus` gives UNTESTED. |
| **K3** premise map | A premise declared as `tested` must make the criterion hold significantly less often. The rate change per premise is written to the certificate. |
| **K4** negative controls | Every criterion needs a control that breaks the theory, and the criterion must not hold under it. A waiver with a written reason is allowed and caps the verdict at WEAK. |
| **K5** vacuity probes | The criterion must not hold on random noise or on all-zero data of the same shape (probes that cannot be disabled), nor on the `null` world or after a shuffle if you declare those. |
| **K6** leak guard and reproducibility | The study may not read files outside its allow-list, use the network or start a process. Two evaluations in one process must give the same result. |
| **K7** coverage | Every declared regime has a criterion, and a criterion returns exactly its declared components. |
| **K8** invariance (0.4) | A transformation that the study declares to leave the outcome unchanged (row order for exchangeable rows, a change of units for a scale-free criterion) must not change any criterion outcome. See [K8](#k8-invariance). |

## Verdicts and exit codes

| Verdict | Meaning | `check` exit code |
|---|---|---|
| `FALSIFIABLE` | every mandatory check passed and all targets were met | 0 |
| `WEAK` | mandatory checks passed, but a target was missed, a check was inconclusive, or a control was waived | 1 |
| `NOT_FALSIFIABLE` | at least one mandatory check failed | 2 |
| `UNDEFINED` | the criterion could not be evaluated in the declared worlds (K1), or the study could not be loaded | 3 |
| `UNTESTED` | the `minus` world did not change the data, so the gate could not test whether the criterion can fail. Fix the world. It does not pass the gate, and it does not say the criterion is unfalsifiable | 6 |

Other exit codes:

| Code | Meaning |
|---|---|
| 4 | usage error, or an error found from the manifest text and the environment alone (TOML syntax, unknown key, type, path, data file, executable, failed handshake): no certificate is written |
| 5 | `verify`: the certificate hash differs (the study changed, the certificate was altered, or the study is not reproducible); `badge`: the certificate body does not match its own hash |
| 7 | `verify`: the certificate was made by another tool version. The study is **not** re-run. Use the matching git tag (for example `v0.3.0`) to verify it. The version is part of the hashed body, so this applies to patch releases too |

`verify` exits with 0 for an identical certificate hash. It checks the certificate's own `body_sha256` first (exit 5 if
the body was altered), then the tool version (exit 7), and only then re-runs the study.

The boundary between exit 4 and exit 3: errors found from the manifest text and the environment alone give exit 4 and
no certificate. Errors found while building or validating the `Study` (no criterion, a duplicate id, a control without
criteria, an unknown criterion id in an invariance, a `python` reference that does not load) give a certificate with
the verdict UNDEFINED and exit 3, as in 0.3. `freeze` keeps the exit codes of the standalone script (0, 1, 2).

Severity order: FALSIFIABLE < WEAK < UNTESTED < NOT_FALSIFIABLE < UNDEFINED. The study verdict is the most severe
component verdict, raised to at least NOT_FALSIFIABLE by any study-level flag. A criterion outcome is `HOLDS`, `FAILS` or
`UNDEFINED`; the word PASS is deliberately not used, because "the run completed" and "the criterion holds" must never
share a label.

## The leak guard

The point of the gate is to run **before** you know the real result, so the study file must not be able to peek at it.
Before the study module is executed, the gate installs a `sys.addaudithook` hook and arms it. While armed it blocks, with
`PermissionError`, and records: opening a file, `os.listdir`, `os.scandir`, `socket.connect`, `socket.getaddrinfo`,
`subprocess.Popen`, `os.system`, `os.exec*`, `os.posix_spawn` and `os.spawn*`. Allowed: the study file, files in
`Study.allow_paths`, the `truth_gate` and `kapi` packages, the Python installation and site-packages. Any blocked attempt raises the
study flag `K6_LEAK_ATTEMPT` and makes the verdict at least NOT_FALSIFIABLE. The guard is an accident detector, not a
sandbox: deliberate evasion (ctypes, native extensions) is out of scope. A study must be a single file in this version (a manifest may reference `python` files, each allow-listed and hashed).

**The guard does not cover external programs.** A command criterion (`command = [...]`) runs in another process, which
the guard cannot see: it may read any file the operating system lets it read. The program runs in a private working
folder with a restricted environment, but that is protection against accidents, not against evasion. The study note
`K6_EXTERNAL_UNGUARDED` lists the commands, and the table, the Action summary and the badge show it. The certificate
records the argv, the SHA-256 of the executable and of every `[external] uses` file; the libraries a program loads
(R packages, `node_modules`) are not hashed.

## The certificate

`check` writes an envelope `{"body": ..., "body_sha256": ..., "created_utc": ...}`. `body_sha256` is the SHA-256 of
`json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)` encoded as UTF-8. The
timestamp is outside the hashed body, so identical inputs give identical hashes.

The body records: the tool and its version (`tool`, `tool_version`; 0.3 had `kapi_version`), the spec version
(`spec_version`, `"0.6"` in 0.4), the kind of input (`input_kind`: `python` or `manifest`), Python and numpy; the mode (`full` or `quick`); the study
(`module_sha256`, the hashes of allowed files, budget, targets, regimes, every world with its `derived_from` and `change`
text, premises, controls, criteria with tolerances and waivers); and, per criterion component, the verdict, the flags,
the HOLDS/UNDEFINED counts and Wilson bounds per stream, and `minus_check` (whether `minus` was identical to `plus`,
which keys the criterion reads, which keys changed). It also holds the premise map, the study flags, the leak log, the
verdict and the `non_claims`. Details are in [`SPEC.md`](SPEC.md).

**Schema 2 (0.4)** adds these fields. The hash rule is unchanged.

| Field | Content |
|---|---|
| `tool`, `tool_version`, `spec_version`, `input_kind` | replace `kapi_version`; see above |
| `manifest` | for a manifest: `sha256` of the manifest bytes; `parsed`, its parsed form (canonical JSON); `data_files`, `python_files` and `uses_files`, each with its SHA-256; `provenance`, the text of every file world; `commands`, every command's argv and the SHA-256 of its resolved executable |
| `mutations` | the ops of every world, control, premise and invariance |
| `k8`, `m_k8`, `k8_statement` | per (invariance, component, world): `pairs`, `defined`, `changes`, `undefined`, `wilson_lower` and the `level`; `m_k8`; and, when K8 ran, the statement "study-wide family-wise error rate at most 2 · alpha_family" |
| `pattern_stats` | for every pattern criterion and each of the streams `plus`, `minus` and `null`: the 5%, 50% and 95% quantiles of the statistic it computes, its thresholds and the number of finite values. It never changes a verdict |
| `suggested_unreviewed` | the number of declarations that still carry `origin = "suggested"` |
| `study_notes` | informational study-level notes (see below); no verdict rule reads them. Each note is `{"note": NAME, "commands": [argv, ...]}` |
| `non_claims`, `known_limitations` | six non-claims (the three of 0.3 with "The gate" for "Kapı", plus: generated and suggested declarations are generic; a file world is only as independent as its provenance; the leak guard does not cover external programs) and five known limitations (the three of 0.3, plus: libraries of external programs are not hashed; on Windows killing an external program does not kill what it started) |

A 0.3 certificate (`kapi_version`, no `tool`) is not verified by 0.4: `verify` exits with 7 and names the tag to use.

To attach a certificate to a freeze: store the `body_sha256` (or the whole file) next to your pre-registration and
include the study file in your freeze manifest (see [`../protocol/`](../protocol/)). `kapi verify` then re-runs the study and
tells anyone whether the certificate still matches.

## Flag reference

Scope: C = per criterion component, S = study level. Classes: **mandatory** (NOT_FALSIFIABLE), **capping** (at most
WEAK), **untested** (UNTESTED), **study-level** (at least NOT_FALSIFIABLE), **info** (recorded only). The statistical
primitive is the one-sided Wilson score bound; `SL(A, B)` ("significantly lower") means `wilson_upper(A) <
wilson_lower(B)` at a Bonferroni-corrected level.

| Flag | Class | Meaning |
|---|---|---|
| `K1_UNDEFINED` | K1 | some outcome on `plus`, `minus` or `null` was UNDEFINED; verdict UNDEFINED |
| `K2_HOLDS_UNREACHABLE` | mandatory | the criterion never holds in `plus` |
| `K2_FAILS_UNREACHABLE` | mandatory | the criterion never fails in `minus` |
| `K2_NO_SEPARATION` | mandatory | not `SL(minus, plus)`: the worlds are not distinguished |
| `K2_UNRESOLVABLE` | mandatory | a declared `(value, scale)` is zero, non-finite or below float64 resolution |
| `K2_MINUS_IDENTICAL` | untested | `minus` and `plus` samples are identical; verdict UNTESTED unless a mandatory flag applies |
| `K2_MINUS_UNREAD` | info | `minus` changed only data the criterion does not read |
| `K2_LOW_POWER` | capping | the criterion holds in `plus` significantly less often than `targets.power` |
| `K2_HIGH_SIZE` | mandatory | the criterion holds in `minus` significantly more often than the declared alpha |
| `HIGH_RATE:<stream>` | mandatory | a control, probe, premise, null or shuffle stream holds significantly more often than the declared alpha |
| `K3_PREMISE_NOT_TESTED` | mandatory | a `tested` premise does not significantly lower the rate, or its magnitude is unresolvable |
| `K3_INCONCLUSIVE` | capping | more than 50% of the mutated samples are UNDEFINED |
| `K4_NO_CONTROL` | mandatory | no control lists this criterion and there is no waiver |
| `K4_WAIVED` | capping | `control_waiver` is set; the reason is printed |
| `K4_CONTROL_ALSO_HOLDS` | mandatory | a listed control is not significantly lower than `plus` |
| `K4_INCONCLUSIVE` | capping | more than 50% UNDEFINED in a control arm |
| `K5_HOLDS_ON_NOISE` | mandatory | the criterion holds on i.i.d. N(0, 1) noise of the same shape |
| `K5_HOLDS_ON_DEGENERATE` | mandatory | the criterion holds on all-zero data |
| `K5_HOLDS_ON_NULL` | mandatory | the declared `null` world is not significantly lower than `plus` |
| `K5_HOLDS_ON_SHUFFLE` | mandatory | the criterion survives shuffling the declared `relational` pair |
| `K5_INCONCLUSIVE:<probe>` | capping | more than 50% UNDEFINED under a probe |
| `K6_LEAK_ATTEMPT` | study-level | blocked file, directory, network or process access |
| `K6_NONREPRODUCIBLE` | study-level | two evaluations in one process differed (unseeded randomness, hidden state) |
| `K7_REGIME_UNCOVERED` | study-level | a declared regime has no criterion |
| `K7_COMPONENT_MISMATCH` | study-level | a criterion returned keys different from its declared components |
| `NONDETERMINISTIC` | study-level | deterministic mode only: a user-derived stream gave different outcomes at sample indices 0, 1, 2 |
| `BAD_RETURN` | info | `fn` returned something other than bool/None (treated as UNDEFINED) |
| `K8_NOT_INVARIANT` | mandatory (0.4) | a declared invariance changes the outcome too often: the one-sided Wilson lower bound of the change rate exceeds `targets.size` in `plus` or in `minus` |
| `K8_INCONCLUSIVE` | capping (0.4) | more than 50% of the before/after pairs of an invariance have an UNDEFINED side in `plus` or in `minus` |
| `K8_SOME_CHANGES` | info (0.4) | at least one outcome changed under an invariance, but the rate is not significantly above `targets.size` |
| `SUGGESTED_UNREVIEWED` | capping (0.4), on every component | a declaration still carries `origin = "suggested"`: it was written by `truth-gate suggest` and nobody has reviewed it. The GitHub Action fails whenever it is present |

K8 flags and `SUGGESTED_UNREVIEWED` are added after the suppression rules below and are never suppressed.

### Study notes

Study notes are in the body list `study_notes`. They are information: **no verdict rule reads them**. `truth-gate check`
prints them at the end of the table.

| Note | Meaning |
|---|---|
| `K6_EXTERNAL_UNGUARDED` | the study has command criteria, which run in other programs that the leak guard cannot see. The commands are listed. The badge reads "(unguarded)" |
| `EXTERNAL_DIED` | an external program died, timed out or broke the protocol during the run; every later request to it was UNDEFINED, and that reaches the verdict through K1 |

When a criterion never holds in `plus`, the flags that only compare against `plus` carry no information and are
suppressed (listed in `suppressed_by`/`suppressed`). When `minus` is identical to `plus`, `K2_FAILS_UNREACHABLE`,
`K2_NO_SEPARATION` and `K2_HIGH_SIZE` are suppressed (listed in `suppressed_minus`). Suppression never changes a verdict
in the first case; in the second it is exactly what makes the verdict UNTESTED instead of NOT_FALSIFIABLE.


## K8: invariance

An invariance declares a transformation that, by the study's own logic, must not change any criterion outcome: the row
order of exchangeable rows, or a consistent change of units for a scale-free criterion. K8 checks it in a separate pass
after the two evaluations of K1-K7, under the armed guard. It never feeds samples or outcomes back into K1-K7.

* **Declaring it.** `[data] rows_exchangeable = true` adds the built-in invariance `builtin:permute_rows` for every
  criterion; it cannot be removed. The default is `false`, because time series and ordered grids are not exchangeable.
  Other invariances are `[[invariances]]` tables with a mandatory `reason`. See [`MANIFEST.md`](MANIFEST.md).
* **Pairs.** For each invariance, each criterion component and each of the worlds `plus` and `minus`: in a stochastic
  study the counted samples of the world are regenerated with the engine's seeds, and each is evaluated before and after
  one transformation drawn from the gate's own stream `k8:<invariance>:<world>`. In a deterministic study the one sample
  is evaluated once untransformed and after `budget.samples` transformations (`quick_samples` in quick mode). A pair with
  an UNDEFINED side is counted apart.
* **Test.** For each (invariance, component, world) the rate of changed outcomes among the defined pairs is tested
  with the one-sided Wilson lower bound. K8 has **its own Bonferroni family**: `m_K8` is 2 times the number of
  (invariance, component) pairs, and each test runs at level `alpha_family / m_K8`. The K1-K7 family is unchanged.
* **Flags.** `K8_NOT_INVARIANT` when the lower bound exceeds `targets.size` in either world; `K8_SOME_CHANGES` (info)
  when a test has at least one change and no `K8_NOT_INVARIANT`; `K8_INCONCLUSIVE` when more than 50% of a test's pairs
  have an UNDEFINED side. A component can carry `K8_SOME_CHANGES` from one test and `K8_NOT_INVARIANT` from another.
* **Error rate.** The study-wide family-wise error rate is at most `2 · alpha_family`: the two families each hold
  `alpha_family`. The certificate says so when K8 ran. A study without invariances has no K8 pass and keeps
  `alpha_family`.
* **Requirements.** Every invariance needs row-aligned keys on both `plus` and `minus` (otherwise exit 4, naming the
  world), and an invariance that names an unknown or repeated criterion id, or repeats an invariance id, is a
  load error (exit 3).

## Known limitations of the gate

* **Worlds, mutators and controls are declared by you.** Mitigations: the `derived_from`/`change` declaration for
  `minus`, the probes that cannot be disabled, and every declaration being visible in the certificate. Review them.
* **Known weaknesses.** A criterion written to recognise the generic probes (for example "return False if the data
  look like N(0, 1) noise") can evade K5. The `minus` world, K3 and K4 are the remaining defences, and code review is
  required.
* **The identical-minus check (v0.3) detects only exact identity.** A `minus` that changes data in an irrelevant way,
  only below float resolution, in the wrong direction, or by too little is not UNTESTED. In stochastic mode it depends on
  pairing: a `minus` that ignores its declared change but consumes the random generator differently from `plus` is not
  detected. Key recording is shallow (top-level keys only). UNTESTED can hide a criterion defect, which is why it does
  not pass the gate.
* **The declared alpha is strict.** `K2_HIGH_SIZE` and `HIGH_RATE:*` are mandatory, so a sound study with a poorly chosen
  declared alpha gets NOT_FALSIFIABLE. Declare the alpha your design actually has.
* **Probes on precomputed quantities.** The generic probes replace every array in the data. If a criterion reads a
  single precomputed scalar (for example a multiplier), the noise and zero probes can make it hold or be undefined for
  reasons unrelated to the criterion. See [`../examples/convergence_criteria`](../examples/convergence_criteria).
* `allow_paths` are declared by the user and cannot be audited beyond hashing. Studies are single files; local helper
  modules cannot be imported. The leak guard is not a sandbox.
* **External programs** (command criteria) are not covered by the leak guard. They are hashed by executable and
  `uses` files only; the libraries they load are not hashed. On Windows, killing a program does not kill the programs it
  started. A program that carries state between requests shows up as `K6_NONREPRODUCIBLE`.
* **K8 doubles the error budget.** With invariances declared, the study-wide family-wise error rate is at most
  `2 · alpha_family`, not `alpha_family`.
* **`suggest` must not be fed the real data.** A plus world built from the real data makes the plus and minus checks
  circular; `provenance` makes the claim visible in the certificate, but the gate cannot tell a synthetic file from the
  real data. Generated mutations and suggested declarations are generic; they do not know your domain, which is why they
  carry `origin = "suggested"` until you review them.
* Monte Carlo cost grows with `samples x streams`.
* Tiny denominators: several evaluation criteria rest on a handful of cases and are reported as they are.
