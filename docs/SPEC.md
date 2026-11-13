# Kapı specification

> **Name.** Truth_Gate was called Kapı (Turkish for "gate") until its first public release on 2026-11-12. This
> record keeps the name used at the time. The Python package is still imported as `kapi`.

> **This is an edited copy for publication.** It contains three frozen documents in order: the v0 specification
> (spec 0.3), the v0.2 delta (spec 0.4) and the v0.3 delta (spec 0.5). Private project names, local paths, the
> Turkish decision quotes and the details of the private pilot were removed or replaced by neutral wording; the
> technical content (rules, flags, verdict mapping, evaluation criteria) was not changed. Section numbers inside a
> delta refer to the v0 document.
>
> SHA-256 (first 16 hex digits) of the frozen originals, which are not published:
>
> | Original | Spec version | SHA-256 (first 16 hex) |
> |---|---|---|
> | v0 specification | 0.3 | `88074F1D26CA24B7` |
> | v0.2 delta | 0.4 | `FD9BCC3DC377F441` |
> | v0.3 delta | 0.5 | `17E1B57F90914BD9` |
>
> The released package (`kapi`, version 0.3.0) implements spec 0.5.

---

# Kapı v0 — Specification

- **Spec version:** 0.3 (2026-11-05). **FROZEN** by the author's decision to freeze it as it stood.
- **Freeze rule:** This file is frozen (SHA-256 recorded in a freeze record) after the D4 pre-freeze smoke test (§11) and **before any evaluation case (§12) is executed**. After the freeze, changes go to a new spec version with a deviation note; results are reported against the frozen version.
- **Roles:** The author owns product decisions. An AI assistant (the drafting session) wrote this spec and reviewed all code. Implementation was delegated to a coding subagent. An independent reviewer session (Tenkit) authored evaluation set E2.

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
- Every check is individually unit-tested (§11). Tests use only toy studies written for the tests; they must not use or imitate evaluation cases (§12).
- No file is written anywhere except the explicit `--out` path. Tests write only to a temporary directory.

## 10. Out of scope for v0
- Post-run labelling of real results (v0.2).
- Metamorphic invariance declarations (sign or scale invariance).
- PRML or MethodSeal integration code (documentation example only, in a later phase).
- Claude Code hook (later phase).
- Parallel execution.
- Non-array data types.
- Multi-file studies (local helper modules).

## 11. D4 pre-freeze smoke test (for this spec and the evaluation harness)
Run after implementation and before the freeze. Print only "defined / reachable / covered". Never print evaluation results, and never run evaluation cases.
1. **Defined:** every check computes on toy studies in stochastic and deterministic modes; the certificate validates against §7; the CLI exit codes work.
2. **Reachable:**
   - for each of the four verdicts, at least one toy study produces it;
   - for each flag in §5, at least one toy study raises it and one does not;
   - for each evaluation criterion P1–P4 (§12.4), both outcomes are reachable when computed on **synthetic mock result tables** (not real gate outputs on evaluation cases).
3. **Covered:**
   - every check K1–K7 has tests;
   - every flag is documented in the README;
   - every evaluation case in §12 has a declared expected check and a fixed twin.
4. If anything fails, fix the spec or code before freezing and record the fix and its reason here (§14).

## 12. Evaluation (pre-registered; frozen with this file)

### 12.1 Sets
- **E1, retrospective (self-authored).** Ten fault/fixed pairs reconstructed from documented incidents. The faulty version must be flagged with the expected check; the fixed twin must not be NOT_FALSIFIABLE or UNDEFINED.

| Case | Origin | Faulty version | Expected check(s) | Fixed twin |
|---|---|---|---|---|
| E1-01 | earlier study (tolerance below float resolution) | HOLDS iff \|mean(x) − μ₀\| < 1e-40, with scale 0.735 | K2_UNRESOLVABLE (and K2_HOLDS_UNREACHABLE) | tolerance 1e-3 |
| E1-02 | earlier study (uncovered regime) | regimes early and late, criterion only for early | K7_REGIME_UNCOVERED | criterion added for late |
| E1-03 | earlier study (component mismatch) | components time and position declared, only time returned | K7_COMPONENT_MISMATCH | both returned |
| E1-04 | earlier study (interpolating fit) | "flexible model fits with loss < ε" (interpolating fit) | K4_CONTROL_ALSO_HOLDS (and K2_NO_SEPARATION) | fixed-form theory model with no free parameters |
| E1-05 | earlier review (results-file leak) | criterion reads a results file to decide | K6_LEAK_ATTEMPT | no file access |
| E1-06 | earlier review (precision note) | tested premise mutation of magnitude 1e-25 at scale 1 | K2_UNRESOLVABLE or K3_PREMISE_NOT_TESTED | magnitude 1e-6, verdict flips |
| E1-07 | earlier study (dominant tolerance) | angle criterion whose tolerance dominates; geometry premise (tested) does not flip | K3_PREMISE_NOT_TESTED | tolerance at which geometry break flips |
| E1-08 | earlier study (self-labelled targets) | targets defined by the same labels the criterion checks | K5_HOLDS_ON_NOISE or K5_HOLDS_ON_DEGENERATE | targets computed from data |
| E1-09 | earlier study (direction invariance) | direction criterion invariant under path swap (mirror-symmetric field) | K3_PREMISE_NOT_TESTED | chiral statistic |
| E1-10 | earlier study (run-completed label) | HOLDS when execution completes regardless of residual | K2_FAILS_UNREACHABLE or K2_NO_SEPARATION | requires true residual ≤ tolerance |

- **E2, independent.** At least 12 fault/fixed pairs covering at least 6 fault types. Each case states its expected check(s). The set is authored from §3, §5 and §12 of this spec only; the reviewer session does not see the implementation. The set is hashed and the hash recorded before Kapı is run on it. If the reviewer session is not used (author's decision), E2 is reported as "not run" and P1b/P2b are not evaluated.
- **E3, external.** Two pairs reconstructed from published cases:
  - **E3-01 (Wu 2026, arXiv 2610.22445).** The constant reduction passes a closure criterion. Faulty version: the criterion is "closure error < ε" for a candidate reduction of a slow–fast system. Expected check: K5_HOLDS_ON_DEGENERATE or K5_HOLDS_ON_NOISE. Fixed twin: closure AND observable preservation.
  - **E3-02 (same paper, linear CKA).** Faulty version: correspondence validity judged by linear CKA > τ, which is invariant to a random rotation of the proposed map. Expected check: K3_PREMISE_NOT_TESTED, with the premise "the correspondence is correct" mutated by a random rotation. Fixed twin: held-out prediction R² under the proposed map.

### 12.2 Procedure
1. Kapı is implemented and unit-tested on toy studies only.
2. The drafting session reviews the code; D4 (§11) is run.
3. The code is hashed and frozen together with this spec.
4. The E1 and E3 case files are then written from the table above without modifying Kapı. They are hashed before the first run.
5. E2 is received from the reviewer session and its hash recorded.
6. Each case is run once in full mode. Primary results come from the frozen Kapı version only.
7. A bug found during evaluation is fixed in a new version; results with that version are labelled secondary.

### 12.3 Detection rule
A faulty case is **detected** if the study verdict is NOT_FALSIFIABLE or UNDEFINED **and** at least one of its expected checks appears among the raised flags. A fixed twin is **cleared** if its verdict is FALSIFIABLE or WEAK.

### 12.4 Primary criteria
- **P1a:** detected faulty cases / all faulty cases (E1 ∪ E2 ∪ E3) ≥ 0.90.
- **P1b:** the same rate restricted to E2 ≥ 0.80.
- **P1c:** no fault type (E2 types; E1 and E3 count by expected check) has zero detections.
- **P2a:** cleared fixed twins / all fixed twins ≥ 0.90. **P2b:** the same rate restricted to E2 ≥ 0.80.
- **P3:** every case whose expected check is K6_LEAK_ATTEMPT is detected (rate = 1.0).
- **P4:** every case run twice with `verify` gives an identical `body_sha256` (rate = 1.0).

Each criterion is reported as Held (`Tuttu`) or Failed (`Tutmadı`) with counts. Small denominators are reported as they are; no pooling hides a failed subset.

### 12.5 Reference baselines (sanity, not criteria)
- An "always NOT_FALSIFIABLE" gate meets P1 and fails P2.
- An "always FALSIFIABLE" gate meets P2 and fails P1.

Both are computed on the mock tables in D4 to show that the evaluation can distinguish them.

### 12.6 Exploratory (labelled as such)
- Confusion table of expected versus raised checks.
- Frequency of WEAK.
- Run time per case.
- Any additional flags raised on fixed twins.

## 13. Known weaknesses (printed in README)
- Worlds, mutators and controls are user-declared. Mitigations:
  - the `derived_from`/`change` declaration for `minus`;
  - the probes that cannot be disabled;
  - every declaration is visible in the certificate.
- A criterion written to recognise the generic probes (for example "return False if the data look like N(0, 1) noise") can evade K5. The `minus` world, K3 and K4 are the remaining defences, and code review is required.
- E1 is self-authored, which is why E2 and E3 exist.
- Monte Carlo cost grows with `samples × streams`.

## 14. Change log
- 0.1-draft (2026-11-05): first draft by the drafting session. Not frozen.
- 0.2-draft (2026-11-05, the drafting session's self-review before delegation):
  - targets use significance at level `a`, so random fluctuation does not raise WEAK;
  - new capping rule `HIGH_RATE:<stream>`;
  - `allow_paths` restricted to static files; studies are single files in v0;
  - probe-evasion weakness added to §13.
- 0.3-draft (2026-11-05, after implementation review; D4 finding, before freeze):
  - **§4.3 changed.** Deterministic mode had used one noise draw and had included Kapı's own random probes in the determinism check, which could raise NONDETERMINISTIC for a deterministic study. Kapı's random probes now use three draws (HOLDS if any draw holds) and are excluded from the determinism check.
  - **Implementation interpretations adopted** (the conservative reading in every case):
    1. Directory listings by the import machinery of `sys.path` entries are not leaks; any other listing outside the allow-list is a leak.
    2. Study files are loaded with `compile` + `exec` from the bytes read before arming, not through the import system.
    3. Relative `allow_paths` resolve against the study's directory; a missing file is a `StudyError`.
    4. A load failure records `load_error` (type only; message only for `StudyError`). A leak during import gives UNDEFINED plus `K6_LEAK_ATTEMPT`.
    5. `BAD_RETURN` is informational. Its UNDEFINED outcomes already trigger K1 in `plus`/`minus` and the inconclusive caps elsewhere. [Since 0.5 (spec 0.7), only a hard UNDEFINED outcome (a failure) or abstention on more than half of the `plus` samples gives `K1_UNDEFINED`; see [`GATE.md`](GATE.md).]
    6. `K7_COMPONENT_MISMATCH` is study-level; extra keys count as a mismatch; a missing component is UNDEFINED.
    7. A non-empty `control_waiver` raises `K4_WAIVED` even when controls are listed.
    8. `K3_INCONCLUSIVE` also applies to assumed premises. A tested premise with an unresolvable magnitude always gets `K3_PREMISE_NOT_TESTED`.
    9. K4/K5 inconclusive flags are added alongside the SL-based flags; only K3 replaces its decision.
    10. `HIGH_RATE` applies to tested premises, controls, probes, null and shuffle, not to assumed premises.
    11. `m` is computed from the declaration only.
    12. Extra construction checks: empty criteria, non-positive budget, out-of-range targets, empty components, unknown roles.
    13. Extra body fields: `errors`, `unresolvable`, `known_limitations`, `study_flag_details`, `probe_unchanged_keys`, `load_error`; bounds rounded to 12 decimals.
    14. Harness: an expected check matches an equal flag or the prefix of a parametrised flag; P1c counts E2 by `fault_type` and E1/E3 by expected check; the P4 denominator is two runs-pairs per case.
  - E1-06 expected checks written as alternatives.
- **D4 run (2026-11-05, on 0.3-draft code; 275 unit tests OK):**
  - Defined: all checks in both modes, certificate, CLI.
  - Reachable: all 25 flag families raised and not raised; all four verdicts; P1a–P4 both outcomes, computed on synthetic mock tables; P1b/P2b "not evaluated" without E2; both baselines fail as intended.
  - Covered: every flag in the README; E1 has 10 complete rows; E3 has 2 cases; no evaluation case files exist.
  - Two first-pass "no" results came from the smoke script itself, not from Kapı: a text search for "Tuttu" missed tests that use constants, and escaped pipes broke the table parse. Both were replaced by direct computation. No spec or code change was needed.
- **0.3 (2026-11-05): frozen.** Only the version labels changed ("0.3-draft" → "0.3" in this header, `kapi/certificate.py`, `kapi/__init__.py` and two tests). The full suite was rerun before hashing.

---

# Kapı v0.2 — Specification (delta to spec 0.3)

- **Spec version:** 0.4 (2026-11-05). **FROZEN** by the author's decision to freeze it as it stood.
- **Base:** spec 0.3, frozen 2026-11-05. SHA16 88074F1D26CA24B7. Everything in 0.3 holds unless this file changes it. Section numbers below refer to 0.3.
- **Why v0.2:** The v0 evaluation gave P1a–P3 Held and P4 Failed. It produced three findings:
  1. Inflated false-positive rates (the p-hacking / multiplicity class) received only WEAK.
  2. When `plus` never holds, misleading downstream flags cascade.
  3. P4 was ill-defined for studies whose fault is non-reproducibility.
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

## Δ4 — Evaluation of v0.2 (pre-registered; frozen with this file)

### Δ4.1 Sets
- **R (regression).** The v0 sets E1E3 (`CASES_SHA256.json` D012088E5128DDD5) and E2 (E6EAD83AD9FC934B), unchanged. Their v0 outcomes are known, so R is a regression check only. It is not evidence of detection power.
- **E4 (new, independent).**
  - **Size:** at least 16 fault/fixed pairs in at least 6 fault types.
  - **False-positive inflation:** at least 4 pairs belong to this class (`fault_class: "fp_inflation"`). Examples: multiple comparisons without correction, optional stopping, threshold or outcome chosen after looking, subgroup fishing. Their expected checks include `K2_HIGH_SIZE` or a `HIGH_RATE:*` family.
  - **Weak twins:** at least 4 pairs whose fixed twin is designed to be legitimately **WEAK** (`expect_fixed: "WEAK"`; for example a valid but underpowered design).
  - **Adversarial:** at least 2 pairs.
  - **Authoring:** E4 is written from the public spec texts only (0.3 §1–§5 and §12, this delta, README). The author has no access to the implementation. The set is hashed before its first run.

### Δ4.2 Detection and clearance
Unchanged from 0.3 §12.3:
- A faulty case is detected if its verdict is NOT_FALSIFIABLE or UNDEFINED and at least one expected check is raised.
- A fixed twin is cleared if its verdict is FALSIFIABLE or WEAK.
- An expected check written as a family (`HIGH_RATE`) matches any `HIGH_RATE:<stream>`.

### Δ4.3 Primary criteria (E4 unless stated)
- **P1a:** detected / faulty ≥ 0.90.
- **P1b:** detection within `fp_inflation` ≥ 0.80.
- **P1c:** no E4 fault type has zero detections.
- **P2:** cleared / fixed ≥ 0.90.
- **P3:** every E4 case whose expected checks include `K6_LEAK_ATTEMPT` is detected (1.0). If there is none: "not evaluated".
- **P4′ (replaces P4):** each file in R ∪ E4 is run twice.
  - If the first run's flags contain `K6_NONREPRODUCIBLE` or `NONDETERMINISTIC`, the file passes iff both runs contain that flag and have the same verdict.
  - Otherwise it passes iff both runs have the same `body_sha256`.
  - Pass rate = 1.0.
- **P5 (WEAK path):** among pairs with `expect_fixed: "WEAK"`, the fixed twin's verdict is exactly WEAK in ≥ 0.80 of them. With fewer than 4 such pairs: "not evaluated".
- **R1:** every R faulty case is detected (1.0).
- **R2:** every R fixed twin is cleared (1.0).

Each criterion is reported as Held (`Tuttu`) or Failed (`Tutmadı`) with counts. Small denominators are reported as they are. Exploratory analyses are labelled as such.

### Δ4.4 Procedure (drafting-session default; same discipline as 0.3 §12.2)
1. Implement v0.2 with toy studies only.
2. The drafting session reviews the code.
3. Run D4: defined / reachable / covered. Include reachability of Δ1 (`K2_HIGH_SIZE` → NOT_FALSIFIABLE) and of Δ2 (suppression raised and not raised), and both outcomes of P1b, P4′, P5, R1 and R2 on mock tables.
4. Freeze this file and the code (freeze record).
5. Hash E4.
6. Run R and E4 once, in full mode, with a new runner (`evaluation/run_eval_v02.py`). The v0 runner stays untouched.

## Δ5 — Known weaknesses (additions to 0.3 §13)
- **Stricter rule, two-sided risk.** Δ1 makes Kapı stricter. A sound study with a poorly chosen declared α (too small for its own design) will now get NOT_FALSIFIABLE. The remedy is to declare the α the design actually has. This is intended.
- **Information is moved, not deleted.** With Δ2, a reviewer sees fewer flags on studies whose criterion never holds. The suppressed list keeps that information in the certificate.

## Δ6 — Change log
- 0.4-draft (2026-11-05): first draft by the drafting session, after the author's decisions. Not frozen.
- **Implementation review (2026-11-05):** The Δ1 and Δ2 code matches this delta. A coded assertion forbids suppression from changing a verdict.
  - Interpretations adopted: the kept unresolvable-magnitude `K3_PREMISE_NOT_TESTED` is not listed in `suppressed`; suppression also triggers when `plus` is entirely UNDEFINED (zero HOLDS); `suppressed_by`/`suppressed` appear only if something was suppressed; P4′ input lists are named `faulty_runs`/`fixed_runs`; regression rows use `set` = R-E1/R-E2/R-E3.
  - Three files written with CRLF line endings were normalised to LF.
- **D4 run (2026-11-05):** 30/30 defined / reachable / covered.
  - 328 unit tests and 18 runner tests OK.
  - Reachable: Δ1 (`K2_HIGH_SIZE` and `HIGH_RATE` → NOT_FALSIFIABLE, `K2_LOW_POWER` → WEAK); Δ2 (suppression raised and not raised, stochastic and deterministic; unresolvable K3 kept); P1a–R2 both outcomes on synthetic mock tables, with P3/P5 "not evaluated" cases.
  - Covered: regression sets intact; no E4 yet.
  - The v0 runner test in the main tree now fails by design, because the main tree is no longer the v0 freeze. The frozen v0 tree passes its own runner and unit tests.
- **0.4 (2026-11-05): frozen.** Only the version labels changed ("0.4-draft" → "0.4" in this header, `kapi/certificate.py`, `kapi/__init__.py`, the README, the v0.2 harness and runner docstrings, and five tests). Both test suites were rerun before hashing.

---

# Kapı v0.3 — Specification (delta to spec 0.4)

- **Spec version:** 0.5 (2026-11-11). **FROZEN** by the author's decision to freeze it as it stood.
- **Base:** spec 0.4 (`kapi_v0_2_spec.md`, frozen 2026-11-05), which is itself a delta to spec 0.3 (`kapi_v0_spec.md`). Everything in 0.3 and 0.4 holds unless this file changes it. Section numbers below refer to 0.3 unless marked "0.4 Δn".
- **Why v0.3:** In a retrospective pilot on converted past studies, Kapı v0.2 cleared 7 of 75 clean criteria. A case review found that 35 of the 37 clean units flagged by K2 were flagged because of how the worlds were built, not because of the criteria. One pattern is mechanically detectable: a `minus` world whose data are identical to `plus`. In one pilot study all 22 data keys of the `minus` world were bit-identical to `plus` (measured outside Kapı). v0.2 reports such a case as NOT_FALSIFIABLE, which blames the criterion for a defect of the world.
- **Author decisions (2026-11-11):**
  - The v0.3 design.
  - Scope: only Δ1, the inert world check. The other proposed deltas (direction check, `plus` role, world-building guide) were not chosen.
  - Verdict for a world defect: a new verdict, UNTESTED.
  - Rule: UNTESTED only if all data is identical. UNTESTED requires identity in **all** keys. If only the keys the criterion reads are unchanged, the verdict is unchanged and an informational flag is added. Reason: otherwise a criterion that ignores the changed quantity (case E1-10) would be reported as a world defect.
  - E5 author: the independent reviewer session.
- **Drafting-session defaults** (open to objection before the freeze): exact equality (Δ1.2), the paired draw in stochastic mode (Δ1.1), the read-key recording rules (Δ1.3), the severity position of UNTESTED and exit code 6 (Δ2), the certificate field names (Δ3), the evaluation design (Δ4).

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

## Δ4 — Evaluation of v0.3 (pre-registered; frozen with this file)

### Δ4.1 Sets
- **R (regression).** E1E3 (`CASES_SHA256.json` D012088E5128DDD5), E2 (E6EAD83AD9FC934B) and E4 (C61A4856D7AF100E), unchanged. Their v0.2 outcomes are known, so R is a regression check only.
- **E5 (new, independent; author: the independent reviewer session).** Written from the public texts only: 0.3 §1–§5 and §12, 0.4, this delta and the README. No access to the implementation. Hashed before the first run. Each case states `case_type`, the expected verdict and the expected checks. Composition:
  - **W (identical minus), at least 5 pairs.** The faulty case has a `minus` that is identical to `plus` in the sense of Δ1.1–Δ1.2: expected **UNTESTED** with `K2_MINUS_IDENTICAL`. Its fixed twin has a working `minus`: expected FALSIFIABLE or WEAK. Both modes must appear, with at least 2 deterministic and 2 stochastic pairs.
  - **U (unread change), at least 4 pairs.** `minus` changes a quantity that the faulty criterion does not read (as in E1-10): expected **NOT_FALSIFIABLE** with `K2_FAILS_UNREACHABLE` or `K2_NO_SEPARATION`, and `K2_MINUS_UNREAD`. Fixed twin: the criterion reads the changed quantity; expected FALSIFIABLE or WEAK.
  - **T (traps), at least 3 cases.** An identical `minus` combined with a criterion that is vacuous for another reason (for example it holds on noise): expected **NOT_FALSIFIABLE** with the other mandatory flag, **not** UNTESTED.
  - **N (near-identical), at least 2 pairs.** `minus` differs from `plus` only slightly or only in one key that the criterion does not read: expected **not** UNTESTED (the faulty case is NOT_FALSIFIABLE with `K2_FAILS_UNREACHABLE` or `K2_NO_SEPARATION`).

### Δ4.2 Detection and clearance
- A **W** faulty case is **detected** iff its verdict is UNTESTED and `K2_MINUS_IDENTICAL` is raised.
- A **U, T or N** faulty case is **detected** iff its verdict is NOT_FALSIFIABLE or UNDEFINED and at least one expected check is raised (0.3 §12.3). An informational flag never counts as an expected check for detection.
- A fixed twin is **cleared** iff its verdict is FALSIFIABLE or WEAK.
- R cases use the 0.3 §12.3 rule unchanged. An R faulty case that becomes UNTESTED counts as **not** detected. Such cases are also listed separately in the report, with their `minus_check`. This listing is a reporting rule only; the count does not change.

### Δ4.3 Primary criteria
- **Q1 (identical minus):** detected W / all W faulty ≥ 0.90.
- **Q2 (no masking):** every U faulty case is detected, and none is UNTESTED (rate 1.0).
- **Q3 (traps):** every T case is NOT_FALSIFIABLE or UNDEFINED and not UNTESTED (rate 1.0).
- **Q4 (exactness):** every N faulty case is detected, and none is UNTESTED (rate 1.0).
- **Q5 (informational flag):** `K2_MINUS_UNREAD` is raised on ≥ 0.80 of U faulty cases.
- **Q6 (clearance):** cleared fixed twins / all E5 fixed twins ≥ 0.90.
- **P4′ (reproducibility):** as in 0.4 Δ4.3, over R ∪ E5 (rate 1.0).
- **R1:** every R faulty case is detected (1.0). **R2:** every R fixed twin is cleared (1.0).

Each criterion is reported as Held (`Tuttu`) or Failed (`Tutmadı`) with counts. Small denominators are reported as they are. Fewer cases than the minimum for a type → that criterion is "not evaluated".

### Δ4.4 Exploratory (labelled as such; not evidence)
Exploratory re-runs on converted past studies and a listing of regression cases whose verdict changed between v0.2 and v0.3 were planned. They motivated the design, so they are not evidence and are not reported here. The retrospective pilot is summarised in `docs/EVALUATION.md`.

### Δ4.5 Procedure (drafting-session default; same discipline as 0.4 Δ4.4)
1. Archive the frozen v0.2 tree read-only and verify it against its freeze record. This lets v0.2 certificates be reproduced.
2. Implement v0.3, testing on toy studies only.
3. The drafting session reviews the code.
4. Run D4: defined / reachable / covered.
   - Reachable: `K2_MINUS_IDENTICAL` raised and not raised (both modes); UNTESTED reached; exit code 6; `K2_MINUS_UNREAD` raised and not raised (including "reads nothing" and "all keys"); Δ1.5 suppression with and without `K2_HOLDS_UNREACHABLE`; a T-type toy reaching NOT_FALSIFIABLE.
   - Q1–Q6, R1, R2 and P4′: both outcomes on synthetic mock tables.
5. The author freezes this file and the code (freeze record).
6. Send the E5 task to the independent reviewer session.
7. Hash E5.
8. Run R and E5 once, in full mode, with a new runner (`evaluation/run_eval_v03.py`). The earlier runners and archives stay untouched.

## Δ5 — Known weaknesses (additions to 0.3 §13 and 0.4 Δ5)
- **Detects only exact identity.** A `minus` that changes data in an irrelevant way, or only below float resolution, is not UNTESTED. Kapı then reports NOT_FALSIFIABLE, possibly with `K2_MINUS_UNREAD`. Wrong-direction worlds and worlds that change the right key by too little are not detected at all. 
- **Stochastic mode depends on pairing.** A stochastic `minus` that ignores its declared change but consumes the generator differently from `plus` is not detected.
- **A same-generator minus is now UNTESTED.** A stochastic `minus` whose generator is the `plus` generator (same distribution, same use of the generator) is identical under pairing. v0.2 reported it as NOT_FALSIFIABLE with `K2_NO_SEPARATION`. v0.3 raises `K2_MINUS_IDENTICAL` and suppresses `K2_NO_SEPARATION`, so the verdict is UNTESTED unless another mandatory flag is raised. The toy `toy_no_separation` stays NOT_FALSIFIABLE through `K5_HOLDS_ON_NOISE`, `K4_CONTROL_ALSO_HOLDS` and `HIGH_RATE:*`. This is intended by the author's decision (identical data = world defect). It was found in the toy `toy_no_separation` during implementation. Any regression case built this way loses its R1 detection (Δ4.2).
- **Key recording is shallow.** Only top-level keys are recorded. Reading a nested value counts as reading its top-level key.
- **UNTESTED can hide a criterion defect.** When the `minus` is identical, the criterion's own falsifiability is unknown. That is the reason UNTESTED does not pass the gate.

## Δ6 — Change log
- 0.5-draft (2026-11-11): first draft by the drafting session, after the author's decisions. Not frozen.
- **Implementation (2026-11-11, coding subagent; drafting-session review the same day).**
  - **v0.2 archive:** the frozen v0.2 tree was archived read-only and matches its freeze record. Its suites pass (328 unit and 18 runner tests).
  - **New and changed code:**
    - new module `kapi/minus.py`;
    - changes in `kapi/checks.py`, `kapi/cli.py`, `kapi/certificate.py`, `kapi/__init__.py`, `pyproject.toml` and the README;
    - `kapi/study.py`, `sampling.py`, `guard.py`, `probes.py`, `stats.py` and `__main__.py` are byte-identical to v0.2, so the study API is unchanged.
  - **Drafting-session review:**
    - `minus.py` matches Δ1.2–Δ1.4.
    - In `checks.py`, the paired draw is stochastic only and is made after the counted samples. Δ1.5 is applied before the verdict, and the 0.4 Δ2 assertion still holds.
    - The harness detection rules match Δ4.2–Δ4.3.
  - **Plan conflict:** the existing toy `toy_no_separation` has a same-generator minus. It now raises `K2_MINUS_IDENTICAL`, and `K2_NO_SEPARATION` is suppressed (see Δ5), which broke two old tests. Its verdict stays NOT_FALSIFIABLE through other mandatory flags. Drafting-session decision: both tests point to a new toy, `toy_no_separation_distinct`, whose minus really differs. One explicit test documents the changed behaviour of the old toy. The old toy file is unchanged.
  - **The frozen v0.2 runner test** (`evaluation/test_run_eval_v02.py`) fails in the main tree by design, because it asserts the v0.2 version strings. The archived copy passes. The same thing happened to the v0 runner at v0.2.
  - **Interpretations adopted** (conservative in every case):
    1. If either compared sample cannot be generated, the samples are not identical, nothing is recorded and no flag is raised.
    2. `list` and `tuple` are never equal to each other.
    3. Object-dtype arrays use `numpy.array_equal`; an exception means not equal. "Plain bool" means `isinstance(r, bool)`.
    4. Dict methods not named in Δ1.3 (mutation, `repr`, `__ne__`, `__reversed__`, `|`) also count as "all keys read". A key is recorded before the access, even when the access raises `KeyError`.
    5. `read_keys` are converted to `str` and sorted.
    6. 0.4 Δ2 and Δ1.5 are computed independently from the same pre-suppression flag set, so a flag may appear in both `suppressed` and `suppressed_minus`. The verdict is taken after Δ1.5.
    7. The paired draw and the recording calls run after the counted samples, so stateful worlds are not disturbed. Deterministic mode reuses the stored `i = 0` minus sample.
    8. All components of a criterion share one `minus_check`.
    9. The value test inside `K2_MINUS_UNREAD` uses Δ1.2 equality.
    10. `pyproject.toml` version is 0.3.0.
    11. E5 manifest format:
        - one record per file, with `case_id`, `case_type`, `role` (faulty/fixed), `expected_verdict`, `expected_checks` and `file`;
        - exactly one faulty record per case, and at most one fixed record (T cases have none);
        - R sets keep the v0.2 format.
    12. Harness rules:
        - informational flags (`K2_MINUS_UNREAD`, `BAD_RETURN`) are dropped from expected checks before detection;
        - Q3 looks at the verdict only;
        - Q6 is "not evaluated" only with zero fixed twins;
        - the mode composition (at least 2 deterministic and 2 stochastic W pairs) is reported under `bookkeeping`, not as a criterion;
        - a T case without a fixed twin contributes one file to P4′.
    13. `run_eval_v03.py` reuses `verify_freeze`, `load_set`, `run_cases` and `_side` from `run_eval_v02.py` by import; that file is unchanged.
    14. Exit code 5 stays reserved for `verify`; code 6 is used only by `check`.
- **D4 run (2026-11-11, on 0.5-draft code; rerun by the drafting session):** 47/47 defined / reachable / covered.
  - Tests: 484 main-tree unit tests and 26 v0.3 runner tests OK. The archived v0.2 suites (328 + 18) also pass.
  - Reachable:
    - `K2_MINUS_IDENTICAL` raised and not raised in both modes, and not raised when one key changed;
    - UNTESTED in both modes, and exit code 6;
    - the verdict order (K1 > mandatory > UNTESTED > capping);
    - `K2_MINUS_UNREAD` raised and not raised, including "reads nothing", "all keys" and deterministic mode;
    - Δ1.5 suppression with and without `K2_HOLDS_UNREACHABLE`;
    - a T-type toy reaching NOT_FALSIFIABLE;
    - Q1–Q6, P4′, R1 and R2: both outcomes, plus "not evaluated", on synthetic mock tables.
  - Covered: README documents both flags, UNTESTED, `minus_check`, `suppressed_minus`, exit code 6 and the Δ5 weaknesses; the archived v0.2 tree matches its freeze record; no E5 set exists yet.
- **0.5 (2026-11-11): frozen** by the author's decision to freeze it as it stood. Only the version labels changed ("0.5-draft" → "0.5" in this header, `kapi/certificate.py`, the README and the tests that assert the label). The suites and D4 were rerun before hashing.
