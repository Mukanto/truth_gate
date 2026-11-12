# Truth_Gate: gate reference

This page is the full reference for the gate. The overview, the protocol and the evidence are in the [README](../README.md); the formal rules and statistics are in [`SPEC.md`](SPEC.md).

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
`kapi.run_gate("STUDY.py", quick=False)` returns the certificate envelope as a dict.

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

## Verdicts and exit codes

| Verdict | Meaning | `check` exit code |
|---|---|---|
| `FALSIFIABLE` | every mandatory check passed and all targets were met | 0 |
| `WEAK` | mandatory checks passed, but a target was missed, a check was inconclusive, or a control was waived | 1 |
| `NOT_FALSIFIABLE` | at least one mandatory check failed | 2 |
| `UNDEFINED` | the criterion could not be evaluated in the declared worlds (K1), or the study could not be loaded | 3 |
| `UNTESTED` | the `minus` world did not change the data, so the gate could not test whether the criterion can fail. Fix the world. It does not pass the gate, and it does not say the criterion is unfalsifiable | 6 |

Usage errors exit with 4. `verify` exits with 0 for an identical certificate hash and 5 for a different one (the study
changed, the certificate was altered, or the study is not reproducible).

Severity order: FALSIFIABLE < WEAK < UNTESTED < NOT_FALSIFIABLE < UNDEFINED. The study verdict is the most severe
component verdict, raised to at least NOT_FALSIFIABLE by any study-level flag. A criterion outcome is `HOLDS`, `FAILS` or
`UNDEFINED`; the word PASS is deliberately not used, because "the run completed" and "the criterion holds" must never
share a label.

## The leak guard

The point of the gate is to run **before** you know the real result, so the study file must not be able to peek at it.
Before the study module is executed, the gate installs a `sys.addaudithook` hook and arms it. While armed it blocks, with
`PermissionError`, and records: opening a file, `os.listdir`, `os.scandir`, `socket.connect`, `socket.getaddrinfo`,
`subprocess.Popen`, `os.system`, `os.exec*`, `os.posix_spawn` and `os.spawn*`. Allowed: the study file, files in
`Study.allow_paths`, the `kapi` package, the Python installation and site-packages. Any blocked attempt raises the
study flag `K6_LEAK_ATTEMPT` and makes the verdict at least NOT_FALSIFIABLE. The guard is an accident detector, not a
sandbox: deliberate evasion (ctypes, native extensions) is out of scope. A study must be a single file in this version.

## The certificate

`check` writes an envelope `{"body": ..., "body_sha256": ..., "created_utc": ...}`. `body_sha256` is the SHA-256 of
`json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)` encoded as UTF-8. The
timestamp is outside the hashed body, so identical inputs give identical hashes.

The body records: the versions of the package (`kapi_version`), the spec, Python and numpy; the mode (`full` or `quick`); the study
(`module_sha256`, the hashes of allowed files, budget, targets, regimes, every world with its `derived_from` and `change`
text, premises, controls, criteria with tolerances and waivers); and, per criterion component, the verdict, the flags,
the HOLDS/UNDEFINED counts and Wilson bounds per stream, and `minus_check` (whether `minus` was identical to `plus`,
which keys the criterion reads, which keys changed). It also holds the premise map, the study flags, the leak log, the
verdict and the three `non_claims`. Details are in [`SPEC.md`](SPEC.md).

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

When a criterion never holds in `plus`, the flags that only compare against `plus` carry no information and are
suppressed (listed in `suppressed_by`/`suppressed`). When `minus` is identical to `plus`, `K2_FAILS_UNREACHABLE`,
`K2_NO_SEPARATION` and `K2_HIGH_SIZE` are suppressed (listed in `suppressed_minus`). Suppression never changes a verdict
in the first case; in the second it is exactly what makes the verdict UNTESTED instead of NOT_FALSIFIABLE.


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
* Monte Carlo cost grows with `samples x streams`.
* Tiny denominators: several evaluation criteria rest on a handful of cases and are reported as they are.
