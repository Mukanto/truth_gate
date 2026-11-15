# Kapı specification

> **Name.** Truth_Gate was called Kapı (Turkish for "gate") until its first public release on 2026-11-12. This
> record keeps the name used at the time. The Python package is still imported as `kapi`.

---

# Kapı v0 — Specification

- **Spec version:** 0.3 (2026-11-05). **FROZEN** by the author's decision to freeze it as it stood.

## 1. Purpose and non-claims

Kapı answers one question about a pre-registered study **before** it is frozen and **without touching real data**:

> Can each acceptance criterion actually fail, does it test the premises it claims to test, and does it distinguish the study from its negative controls?

The output is a hash-addressed **certificate** that can be attached to an existing lock (PRML/Falsify, MethodSeal, or a plain SHA-256 freeze).

Non-claims (printed in every certificate):
1. A FALSIFIABLE certificate does not mean the hypothesis is true or that the study is well designed in every respect.
2. All checks are relative to the synthetic worlds, premise mutators and controls that the study declares. Weak declarations give weak certificates; the certificate lists them so a reviewer can judge.
3. Kapı does not modify or repair criteria. It only reports.

## 2. Terminology

**Criterion outcome** (returned by user code for one data sample):
- `HOLDS`: the criterion supports the hypothesis on this sample.
- `FAILS`: it does not.
- `UNDEFINED`: it cannot be evaluated (exception, `None`, NaN, empty set, wrong type).

The word PASS is deliberately not used, because "the run completed" and "the criterion holds" must never share a label (a lesson from an earlier study).

**Gate verdict**, per criterion component and per study:
- `FALSIFIABLE`: every mandatory check passed and all targets were met.
- `WEAK`: every mandatory check passed, but a target was missed, a check was inconclusive, or a control was waived with a reason.
- `NOT_FALSIFIABLE`: at least one mandatory check failed.
- `UNDEFINED`: the criterion could not be evaluated in the declared worlds (K1 failed), or the study could not be loaded.

Severity order: `FALSIFIABLE` < `WEAK` < `NOT_FALSIFIABLE` < `UNDEFINED`. The study verdict is the most severe component verdict, raised to at least `NOT_FALSIFIABLE` by any study-level flag (§5.8).

## 3. Study definition (public API)

A study is a Python file that defines a module-level object `STUDY` of type `kapi.Study`. All user callables are pure functions of their arguments. Data is a `dict[str, numpy.ndarray]`.

```python
from kapi import Study, Criterion, World, Premise, Control, Budget, Targets

STUDY = Study(
    name: str,
    criteria: list[Criterion],
    worlds: dict[str, World],          # must contain "plus" and "minus"; "null" optional
    premises: list[Premise] = [],
    controls: list[Control] = [],
    regimes: list[str] = ["all"],      # every regime must be covered by >= 1 criterion
    deterministic: bool = False,
    budget: Budget = Budget(),         # samples=200, quick_samples=20, base_seed=20261105
    targets: Targets = Targets(),      # power=0.8, size=0.05, alpha_family=0.05
    allow_paths: list[str] = [],       # static read-only files the study may open (e.g. a config); hashed into the certificate
    relational: list[tuple[str, str]] = [],  # optional key pairs for the optional shuffle probe
)

World(generate: Callable[[np.random.Generator], dict[str, np.ndarray]],
      derived_from: str | None = None, change: str = "")
# "minus" should be derived from "plus" by a declared single change; stored as text in the certificate.

Criterion(id: str, fn: Callable[[dict], bool | None | dict[str, bool | None]],
          regime: str = "all", components: list[str] | None = None,
          tolerances: dict[str, tuple[float, float]] = {},   # name -> (value, scale)
          control_waiver: str | None = None)                 # reason if no negative control applies

Premise(id: str, mutate: Callable[[dict, np.random.Generator], dict],
        role: Literal["tested", "assumed"], criteria: list[str],
        magnitude: tuple[float, float] | None = None)        # (value, scale) of the perturbation, if numeric

Control(id: str, criteria: list[str],
        transform: Callable[[dict, np.random.Generator], dict] | None = None,
        world: World | None = None)                          # exactly one of transform / world
```

Return-value rules for `Criterion.fn`:
- `True` or `numpy.bool_(True)` → HOLDS; `False` → FAILS; `None` → UNDEFINED.
- Any other type → UNDEFINED with flag `BAD_RETURN`.
- If `components` is given, `fn` must return a dict with exactly those keys; each component is treated as a separate sub-criterion `id:component` for K1–K5. Missing or extra keys → flag `COMPONENT_MISMATCH` (K7).
- Exceptions inside `fn`, `generate`, `mutate` or `transform` produce UNDEFINED. The exception type name is recorded; the message is not.

Construction-time validation (raises `kapi.StudyError` → study verdict UNDEFINED):
- duplicate ids;
- unknown criterion ids in premises or controls;
- missing `plus` or `minus` world;
- a control with both or neither of `transform` / `world`;
- regime names in criteria that are not declared in `regimes`.

## 4. Sampling and the statistical primitive

**Seeds.** Sample `i` of a stream named `s` uses `numpy.random.default_rng(numpy.random.SeedSequence([base_seed, zlib.crc32(s.encode()), i]))`. Stream names:
- `world:<name>`
- `premise:<id>` (mutation applied to the `plus` sample with the same `i`; the mutation rng uses stream `premise-rng:<id>`)
- `control:<id>`
- `probe:<name>`

The same `plus` sample `i` is reused across premise, control (transform kind) and probe streams, so comparisons are paired by construction. Pairing is not used in the statistics in v0.

**Sample count.** `n = budget.samples` (default 200). Quick mode uses `n = budget.quick_samples` (default 20), and the certificate is marked `"mode": "quick"` (not certifiable). Deterministic studies use `n = 1` (§4.3).

### 4.1 Wilson bounds
For `k` HOLDS out of `n` evaluations (UNDEFINED counts as not-HOLDS unless stated otherwise), one-sided Wilson score bounds at level `a` use `z = NormalDist().inv_cdf(1 - a)` from the Python standard library.

### 4.2 "Significantly lower" — SL(A, B)
`SL(A, B)` is true if and only if `wilson_upper(A, a) < wilson_lower(B, a)`, where `a = alpha_family / (2 * m)` and `m` is the total number of SL comparisons made in the certificate (Bonferroni). This is the only inferential primitive in v0. Wider intervals make SL harder to establish, which produces more flags; that is the safe direction for a gate.

### 4.3 Deterministic mode
If `deterministic=True`:
- every stream is sampled once (`i = 0`);
- `SL(A, B)` is true iff the outcome of A is in {FAILS, UNDEFINED} and the outcome of B is HOLDS;
- determinism is verified by also evaluating every **user-derived** stream at `i = 1` and `i = 2`. Any differing outcome → study flag `NONDETERMINISTIC`. User-derived streams are worlds, premises, controls and `probe:zeros`.
- **Kapı's own random probes** (`probe:noise` and every `probe:shuffle:*`) are evaluated at `i = 0, 1, 2` and are excluded from the determinism check. Their single outcome is:
  - HOLDS if any of the three draws HOLDS;
  - otherwise UNDEFINED if at least two draws are UNDEFINED;
  - otherwise FAILS.

  This conservative rule raises more K5 flags than a single draw would. It exists because the noise is Kapı's randomness, not the user's (D4 finding, §14).

## 5. Checks

Each check produces flags. Every flag is listed with its scope: C = per criterion component, S = study-level.

### 5.1 K1 — Definedness
- Evaluate each criterion component on `n` samples of `plus` and of `minus` (and of `null`, if declared).
- If any outcome is UNDEFINED → flag `K1_UNDEFINED` (C); the component verdict is UNDEFINED. [Since 0.5 (spec 0.7), only a hard UNDEFINED outcome (a failure) or abstention on more than half of the `plus` samples gives `K1_UNDEFINED`; see [`GATE.md`](GATE.md).]
- The certificate records the counts and exception type names.

### 5.2 K2 — Two-sided reachability, separation, resolution
- `K2_HOLDS_UNREACHABLE` (C): zero HOLDS in `plus`.
- `K2_FAILS_UNREACHABLE` (C): zero non-HOLDS in `minus`.
- `K2_NO_SEPARATION` (C): not `SL(minus, plus)`.
- `K2_UNRESOLVABLE` (C, or per premise): for any declared `(value, scale)` in `Criterion.tolerances` or `Premise.magnitude`, the declaration fails if any of these holds:
  - `value == 0`;
  - `value` or `scale` is not finite;
  - `float64(scale) + float64(value) == float64(scale)`.

  A premise with an unresolvable magnitude also fails K3 for every criterion it lists.
- Targets (not mandatory). These produce `WEAK`, not `NOT_FALSIFIABLE`. They use the same per-bound level `a` as SL (§4.2), so a target counts as missed only when the miss is significant:
  - `K2_LOW_POWER` (C): `wilson_upper(plus, a) < targets.power`;
  - `K2_HIGH_SIZE` (C): `wilson_lower(minus, a) > targets.size`.

  Deterministic mode skips both.
- **High-rate rule (all comparison streams).** For every stream X that must satisfy SL against `plus` (tested premise, control, probe, null, shuffle): if `wilson_lower(X, a) > targets.size`, raise the capping flag `HIGH_RATE:<stream>` (C). This catches criteria that are statistically separated but still hold often where they should not. Example: a control that holds in 80% of samples. Deterministic mode skips this rule.

### 5.3 K3 — Premise map
For each premise P and each listed criterion component c:
- compute the HOLDS rate under `mutate(plus sample)`;
- for `role == "tested"`, require `SL(premise:P, plus)`; otherwise flag `K3_PREMISE_NOT_TESTED` (C);
- for `role == "assumed"`, no requirement; the rate difference is reported in the premise map.

If more than 50% of the mutated samples are UNDEFINED, the result is `K3_INCONCLUSIVE` (C). This caps the verdict at WEAK and replaces the NOT_TESTED decision, because crashing on mutated data must not count as sensitivity.

The **premise map** is a table premises × components of rate differences `rate(plus) − rate(premise:P)`. It is always written to the certificate.

### 5.4 K4 — Negative-control specificity
- Each criterion component must be listed by at least one control, unless the criterion has a `control_waiver` reason:
  - no control and no waiver → `K4_NO_CONTROL` (C, mandatory);
  - waiver → `K4_WAIVED` (C); caps the verdict at WEAK; the reason is printed in the certificate.
- For each listed control, the control arm is `transform(plus sample)` or a sample of `control.world`. Require `SL(control:N, plus)`; otherwise flag `K4_CONTROL_ALSO_HOLDS` (C, mandatory).
- More than 50% UNDEFINED in the control arm → `K4_INCONCLUSIVE` (C, caps at WEAK).

### 5.5 K5 — Vacuity probes (cannot be disabled)
Two generic probes are always run. Each is applied to every key of the `plus` sample:
- `probe:noise`: numeric float/int arrays are replaced by i.i.d. N(0, 1) float64 noise of the same shape; boolean arrays by Bernoulli(0.5); other dtypes are left unchanged and listed in the certificate.
- `probe:zeros`: numeric arrays are replaced by zeros of the same shape (float64); boolean arrays by False; other dtypes unchanged.

Rules:
- For each probe, require `SL(probe, plus)`. Otherwise flag `K5_HOLDS_ON_NOISE` or `K5_HOLDS_ON_DEGENERATE` (C, mandatory).
- If `null` is declared, also require `SL(null, plus)`; otherwise flag `K5_HOLDS_ON_NULL` (C, mandatory).
- If `relational` pairs are declared, the optional probe `probe:shuffle:<a>,<b>` permutes the first axis of `b` relative to `a`. It requires SL; failure → `K5_HOLDS_ON_SHUFFLE` (C, mandatory once declared).
- More than 50% UNDEFINED under a probe → `K5_INCONCLUSIVE:<probe>` (C, caps at WEAK).

### 5.6 K6 — No leakage; reproducibility
- **Leak guard.** Before the study module is imported, Kapı installs (once per process) a `sys.addaudithook` hook and arms it. While armed, the hook intercepts these events:
  - `open` with a path argument (int file descriptors are ignored);
  - `os.listdir`, `os.scandir`;
  - `socket.connect`, `socket.getaddrinfo`;
  - `subprocess.Popen`, `os.system`, `os.exec`, `os.posix_spawn`, `os.spawn`.

  The allow-list:
  - the study file itself (exact resolved path);
  - resolved paths in `Study.allow_paths` (exact files, not directories), which are added to the allow-list after the study object is constructed. Each listed file is hashed. A study that opens such a file at import time fails to load;
  - the `kapi` package directory;
  - `sys.prefix`, `sys.base_prefix`, `sys.exec_prefix`;
  - `site.getsitepackages()` and `site.getusersitepackages()`.

  Any other intercepted event is recorded as `{event, target}` and blocked with `PermissionError`. Any recorded event → study flag `K6_LEAK_ATTEMPT` (S). `sys.dont_write_bytecode` is set to True while armed. The guard is disarmed after the run, but the hook stays installed for the rest of the process.

  Known limitation (printed in the certificate): `allow_paths` are declared by the user and cannot be audited for content beyond hashing. A reviewer must inspect them. Studies are single files in v0. Importing local helper modules is not supported, because the study's directory is not on the allow-list.

- **Reproducibility.** The complete evaluation (all streams, all checks) is computed twice in the same process. If the canonical result bodies (§7) differ → study flag `K6_NONREPRODUCIBLE` (S). This catches unseeded global randomness and hidden state.

### 5.7 K7 — Coverage
- `K7_REGIME_UNCOVERED` (S): a declared regime has no criterion.
- `K7_COMPONENT_MISMATCH` (S): a criterion returned keys different from its declared components on any sample. The outcome of a missing component is UNDEFINED.

### 5.8 Verdict mapping
For each criterion component:
1. `K1_UNDEFINED` → UNDEFINED. [Since 0.5 (spec 0.7), only a hard UNDEFINED outcome (a failure) or abstention on more than half of the `plus` samples gives `K1_UNDEFINED`; see [`GATE.md`](GATE.md).]
2. Otherwise, any mandatory flag → NOT_FALSIFIABLE. The mandatory flags are: `K2_HOLDS_UNREACHABLE`, `K2_FAILS_UNREACHABLE`, `K2_NO_SEPARATION`, `K2_UNRESOLVABLE`, `K3_PREMISE_NOT_TESTED`, `K4_NO_CONTROL`, `K4_CONTROL_ALSO_HOLDS`, `K5_HOLDS_ON_NOISE`, `K5_HOLDS_ON_DEGENERATE`, `K5_HOLDS_ON_NULL`, `K5_HOLDS_ON_SHUFFLE`.
3. Otherwise, any capping flag → WEAK. The capping flags are: `K2_LOW_POWER`, `K2_HIGH_SIZE`, `HIGH_RATE:*`, `K3_INCONCLUSIVE`, `K4_WAIVED`, `K4_INCONCLUSIVE`, `K5_INCONCLUSIVE:*`.
4. Otherwise → FALSIFIABLE.

Study verdict:
- Take the most severe component verdict.
- If any study-level flag is present (`K6_LEAK_ATTEMPT`, `K6_NONREPRODUCIBLE`, `K7_REGIME_UNCOVERED`, `K7_COMPONENT_MISMATCH`, `NONDETERMINISTIC`), raise the verdict to at least NOT_FALSIFIABLE.
- `StudyError` or a failure to load the study → UNDEFINED.

## 6. Generic-probe data handling
- "Numeric" means `numpy.issubdtype(dtype, numpy.number)`; booleans are handled separately.
- Shapes are preserved; probes never change keys.
- The probe rng is the stream `probe:<name>` with the same `i` as the `plus` sample.

## 7. Certificate
- **Canonical body:** `json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)` encoded as UTF-8. `body_sha256` is the SHA-256 of these bytes.
- **Body fields:**
  - `kapi_version`, `spec_version`
  - `python_version`, `numpy_version`
  - `mode` (`full` | `quick`)
  - `study`: `name`, `module_sha256`, `allowed_files` (list of `{path, sha256}`), `deterministic`, `budget`, `targets`, `regimes`, world `change` texts, premise roles and magnitudes, control kinds, criterion tolerances, waivers
  - `m_comparisons`, `alpha_per_bound`
  - `components`: list of `{id, regime, verdict, flags, counts: {stream: {holds, undefined, n}}, bounds: {stream: {lower, upper}}}`
  - `premise_map`
  - `study_flags`, `leak_log`
  - `verdict`, `non_claims` (§1 text)
- **Envelope:** `{ "body": ..., "body_sha256": ..., "created_utc": ... }`. The timestamp is outside the hashed body, so identical inputs give identical hashes.

## 8. CLI
- `python -m kapi check STUDY.py [--out CERT.json] [--quick]` prints a table (component, verdict, flags), writes the certificate (default `STUDY.kapi.json` next to the study only if `--out` is not given — **in tests and smoke runs always pass `--out` to a scratch directory**), and exits with:
  - 0 FALSIFIABLE
  - 1 WEAK
  - 2 NOT_FALSIFIABLE
  - 3 UNDEFINED
  - 4 usage error
- `python -m kapi verify CERT.json STUDY.py` re-runs in the mode recorded in the certificate and compares `body_sha256`. Exit 0 if equal, 5 if different.

## 9. Implementation constraints
- Python ≥ 3.11 (target 3.14), standard library and `numpy` only. No network. No optimizer, no fitting inside Kapı.
- Package layout:
  - `kapi/`: `__init__.py`, `study.py`, `sampling.py`, `stats.py`, `probes.py`, `checks.py`, `guard.py`, `certificate.py`, `cli.py`, `__main__.py`
  - `tests/`
  - `README.md`, `pyproject.toml`
- Pure functions where possible. The only global state is the audit hook and its armed flag.
- No file is written anywhere except the explicit `--out` path. Tests write only to a temporary directory.

## 10. Out of scope for v0
- Post-run labelling of real results (v0.2).
- Metamorphic invariance declarations (sign or scale invariance).
- PRML or MethodSeal integration code (documentation example only, in a later phase).
- Claude Code hook (later phase).
- Parallel execution.
- Non-array data types.
- Multi-file studies (local helper modules).

## 13. Known weaknesses (printed in README)
- Worlds, mutators and controls are user-declared. Mitigations:
  - the `derived_from`/`change` declaration for `minus`;
  - the probes that cannot be disabled;
  - every declaration is visible in the certificate.
- A criterion written to recognise the generic probes (for example "return False if the data look like N(0, 1) noise") can evade K5. The `minus` world, K3 and K4 are the remaining defences, and code review is required.
- Monte Carlo cost grows with `samples × streams`.

---

# Kapı v0.2 — Specification (delta to spec 0.3)

- **Spec version:** 0.4 (2026-11-05). **FROZEN** by the author's decision to freeze it as it stood.
- **Base:** spec 0.3, frozen 2026-11-05. SHA16 88074F1D26CA24B7. Everything in 0.3 holds unless this file changes it. Section numbers below refer to 0.3.
- **Author decisions (2026-11-05):**
  - The v0.2 design.
  - The declared α is mandatory (Δ1).
- **Drafting-session defaults** (the author did not object): Δ2 and Δ4.4.

## Δ1 — The declared α is mandatory (author decision)
`Targets.size` is the false-positive rate the study claims (its α). README and certificate call it "declared α".

Rule (unchanged from 0.3 §5.2): `wilson_lower(X, a) > targets.size`, with the same per-bound level `a` as SL (0.3 §4.2; `m` is unchanged). Only the classification changes:
- `K2_HIGH_SIZE` (stream `minus`) moves from capping to **mandatory**.
- `HIGH_RATE:<stream>` (tested premise, control, probe, null, shuffle) moves from capping to **mandatory**.
- `K2_LOW_POWER` **stays capping** (WEAK). Low power wastes effort but does not create false claims; exceeding the declared α does.
- Deterministic mode is unchanged: both rate rules are skipped there, as in 0.3.

New 0.3 §5.8 lists:
- **mandatory** = 0.3 mandatory ∪ {`K2_HIGH_SIZE`, `HIGH_RATE:*`};
- **capping** = {`K2_LOW_POWER`, `K3_INCONCLUSIVE`, `K4_WAIVED`, `K4_INCONCLUSIVE`, `K5_INCONCLUSIVE:*`}.

## Δ2 — Cascade suppression (drafting-session default)
If a component has zero HOLDS in `plus`, it raises `K2_HOLDS_UNREACHABLE`. The following SL-derived flags carry no information in that case, so they are **not raised** for that component:
- `K2_NO_SEPARATION`, `K2_LOW_POWER`;
- `K3_PREMISE_NOT_TESTED`, only when raised by the SL test;
- `K4_CONTROL_ALSO_HOLDS`;
- `K5_HOLDS_ON_NOISE`, `K5_HOLDS_ON_DEGENERATE`, `K5_HOLDS_ON_NULL`, `K5_HOLDS_ON_SHUFFLE`.

Instead, the component record gets `"suppressed_by": "K2_HOLDS_UNREACHABLE"` and `"suppressed": [sorted names that would have been raised]`.

Kept unchanged:
- `K3_PREMISE_NOT_TESTED` caused by an unresolvable magnitude (0.3 §5.2);
- every non-SL flag (`K1_*`, `K2_UNRESOLVABLE`, `K2_FAILS_UNREACHABLE`, `K2_HIGH_SIZE`, `HIGH_RATE:*`, `K4_NO_CONTROL`, `K4_WAIVED`, inconclusive flags);
- all study-level flags.

The verdict cannot change, because `K2_HOLDS_UNREACHABLE` is mandatory. In deterministic mode the same rule applies when the `plus` outcome is not HOLDS.

## Δ3 — Versions and certificate
- `kapi_version = "0.2.0"` and `spec_version = "0.4"` (after freeze; `"0.4-draft"` before).
- New component fields `suppressed_by` and `suppressed`. They are present only when suppression happened.
- 0.3 §7 is otherwise unchanged.

## Δ5 — Known weaknesses (additions to 0.3 §13)
- **Stricter rule, two-sided risk.** Δ1 makes Kapı stricter. A sound study with a poorly chosen declared α (too small for its own design) will now get NOT_FALSIFIABLE. The remedy is to declare the α the design actually has. This is intended.
- **Information is moved, not deleted.** With Δ2, a reviewer sees fewer flags on studies whose criterion never holds. The suppressed list keeps that information in the certificate.

---

# Kapı v0.3 — Specification (delta to spec 0.4)

- **Spec version:** 0.5 (2026-11-11). **FROZEN** by the author's decision to freeze it as it stood.
- **Base:** spec 0.4 (`kapi_v0_2_spec.md`, frozen 2026-11-05), which is itself a delta to spec 0.3 (`kapi_v0_spec.md`). Everything in 0.3 and 0.4 holds unless this file changes it. Section numbers below refer to 0.3 unless marked "0.4 Δn".
- **Author decisions (2026-11-11):**
  - The v0.3 design.
  - Scope: only Δ1, the inert world check. The other proposed deltas (direction check, `plus` role, world-building guide) were not chosen.
  - Verdict for a world defect: a new verdict, UNTESTED.
  - Rule: UNTESTED only if all data is identical. UNTESTED requires identity in **all** keys. If only the keys the criterion reads are unchanged, the verdict is unchanged and an informational flag is added.

## Δ1 — Identical-minus check

### Δ1.1 Which samples are compared
- **Deterministic mode:** the `plus` sample and the `minus` sample at `i = 0`. Both are already generated; no extra cost.
- **Stochastic mode:** one extra **paired** `minus` sample is generated with the `plus` stream's generator: `minus.generate(rng)` where `rng` is the generator of stream `world:plus`, `i = 0` (0.3 §4, "Seeds"). It is compared with the `plus` sample at `i = 0`. The paired sample is used only for Δ1. It is not counted in any rate, bound or SL comparison.
- The comparison is made once per study evaluation. Under K6 reproducibility it is made in both passes, like every other check.

### Δ1.2 Identity
The two samples are **identical** iff they have the same set of keys and every key's values are equal under this rule (applied recursively):
- `numpy` arrays and Python numbers (converted with `numpy.asarray`): same shape, same dtype, and `numpy.array_equal(a, b, equal_nan=True)` for float and complex dtypes, `numpy.array_equal(a, b)` otherwise;
- `dict`: same keys and equal values;
- `list` and `tuple`: same length and equal items;
- anything else: `a == b` evaluates to `True`. If the comparison raises an exception or does not return a plain bool, the values count as **not** equal.

Equality is exact. No tolerance. (A world change that alters data only below float resolution is not detected. That is the safe direction: no false UNTESTED.)

### Δ1.3 Keys read by a criterion
For the informational flag (Δ1.4), Kapı records which top-level keys each criterion reads.
- The criterion is called once more on each of the two compared samples. The sample is wrapped in a `dict` subclass that records keys accessed through `__getitem__`, `get` and `__contains__`.
- Any whole-mapping access (`__iter__`, `keys`, `items`, `values`, `copy`, `len`, `dict(d)`, `**d`, `==`) marks the sample as **all keys read**.
- These extra calls only record keys. Their outcomes are not used. All counted evaluations keep receiving plain `dict` samples, as in 0.3.
- If a recording call raises, the keys recorded up to that point are kept and the criterion is treated as "all keys read". This is conservative: it can only suppress `K2_MINUS_UNREAD`.
- `read_keys` = the union over both samples.

### Δ1.4 Flags
Both flags have scope C (per component). Every component of a criterion receives the same result.
- **`K2_MINUS_IDENTICAL`** (new kind: **untested**): the compared samples are identical (Δ1.2).
- **`K2_MINUS_UNREAD`** (**informational**; no effect on the verdict). Raised iff all of these hold:
  - the samples are not identical;
  - `read_keys` is non-empty and not "all keys";
  - every key in `read_keys` is present in both samples with equal values.

  The certificate lists the keys that changed (Δ3). A criterion that reads no key at all never receives this flag.

### Δ1.5 Suppression when the minus is identical
If `K2_MINUS_IDENTICAL` is raised, the following flags of that component are **not raised**, because a `minus` that equals `plus` carries no information about them:
- `K2_FAILS_UNREACHABLE`, `K2_NO_SEPARATION`, `K2_HIGH_SIZE`.

They are listed in the new component field `suppressed_minus` (sorted). The 0.4 Δ2 fields `suppressed_by` and `suppressed` keep their meaning and are filled independently. If `plus` never holds, 0.4 Δ2 applies as before. `K2_HOLDS_UNREACHABLE` is mandatory, so the verdict is then NOT_FALSIFIABLE (Δ2, step 2).

Every other flag is kept. In particular, K5 probes still run on the `plus` sample, so a vacuous criterion still gets `K5_HOLDS_ON_*` and therefore NOT_FALSIFIABLE.

## Δ2 — New verdict UNTESTED (author decision)
Meaning: "The `minus` world did not change the data, so Kapı could not test whether this criterion can fail. Fix the world." UNTESTED does not pass the gate, and it does not say the criterion is unfalsifiable.

Verdict mapping (replaces 0.3 §5.8 for components):
1. `K1_UNDEFINED` → UNDEFINED.
2. Otherwise, any raised (not suppressed) mandatory flag → NOT_FALSIFIABLE. The mandatory list is the one in 0.4 Δ1.
3. Otherwise, `K2_MINUS_IDENTICAL` → **UNTESTED**.
4. Otherwise, any capping flag → WEAK.
5. Otherwise → FALSIFIABLE.

- **Severity order** (for the study verdict, "most severe component"): FALSIFIABLE < WEAK < UNTESTED < NOT_FALSIFIABLE < UNDEFINED.
- Study-level flags still raise the study verdict to at least NOT_FALSIFIABLE (0.3 §5.8).
- **CLI exit code:** 6 = UNTESTED. Codes 0–5 are unchanged (0.3 §8).

## Δ3 — Versions and certificate
- `kapi_version = "0.3.0"`, `spec_version = "0.5"` (after the freeze; `"0.5-draft"` before).
- New component field `minus_check`, always present:
  - `identical` (bool);
  - `read_keys`: a sorted list of key names, or the string `"ALL"`;
  - `changed_keys`: sorted keys whose values differ, plus keys present in only one sample;
  - `paired`: `true` in stochastic mode (paired draw), `false` in deterministic mode.
- New component field `suppressed_minus`, present only when Δ1.5 suppressed something.
- A new `known_limitations` entry states the Δ1 limits (Δ5).
- 0.3 §7 and 0.4 Δ3 are otherwise unchanged.

## Δ5 — Known weaknesses (additions to 0.3 §13 and 0.4 Δ5)
- **Detects only exact identity.** A `minus` that changes data in an irrelevant way, or only below float resolution, is not UNTESTED. Kapı then reports NOT_FALSIFIABLE, possibly with `K2_MINUS_UNREAD`. Wrong-direction worlds and worlds that change the right key by too little are not detected at all. 
- **Stochastic mode depends on pairing.** A stochastic `minus` that ignores its declared change but consumes the generator differently from `plus` is not detected.
- **A same-generator minus is now UNTESTED.** A stochastic `minus` whose generator is the `plus` generator (same distribution, same use of the generator) is identical under pairing. v0.2 reported it as NOT_FALSIFIABLE with `K2_NO_SEPARATION`. v0.3 raises `K2_MINUS_IDENTICAL` and suppresses `K2_NO_SEPARATION`, so the verdict is UNTESTED unless another mandatory flag is raised. The toy `toy_no_separation` stays NOT_FALSIFIABLE through `K5_HOLDS_ON_NOISE`, `K4_CONTROL_ALSO_HOLDS` and `HIGH_RATE:*`. This is intended by the author's decision (identical data = world defect).
- **Key recording is shallow.** Only top-level keys are recorded. Reading a nested value counts as reading its top-level key.
- **UNTESTED can hide a criterion defect.** When the `minus` is identical, the criterion's own falsifiability is unknown. That is the reason UNTESTED does not pass the gate.
