# Truth_Gate 0.4: specification (spec 0.6)

Status: **v3.1, 2026-11-12, FROZEN (see `FREEZE_SPEC_0.6.json`).** Designer: Claude, under the author's delegation. v2 answered blind
review 1, v3 answered blind review 2 and v3.1 the targeted review 3 (`spec-0.6-REVIEW1.md` to `REVIEW3.md`); every change and its reason
is in `spec-0.6-REVISIONS.md`. After the freeze this text is implemented without change; later changes go through
the revision log.

## 0. Goals and non-goals

The author's goals (2026-11-12):

* **G1, any language.** A study's criteria can be written in any language.
* **G2, less labour.** Common criteria are written without code. Synthetic worlds and controls can be derived from
  one realistic dataset.
* **G3, easy adoption.** One-line install, a CI action, a pre-commit hook, a scaffold for new studies.
* **G4, stronger evidence.** An external, literature-grounded test set with pre-registered criteria (section 14).
* **G5, the new name in code.** The package becomes `truth_gate`.

Non-goals:

* The gate still never sees the real data or the real result, and it never uses the network.
* It does not decide whether a criterion is scientifically meaningful (a semantic property; no general program
  decides it). It checks what can be checked against declared worlds.
* It is not a sandbox. External programs are isolated against accidents, not against deliberate evasion.

Deferred to 0.5: worlds, controls and premises produced by external programs; the mutations `copy`, `stale` and
`relabel`; `files = glob` worlds; YAML and Parquet input.

## 1. Architecture

### 1.1 A manifest compiler in front of the 0.3 engine

```text
truthgate.toml ──► parser ──► Study object (0.3 types) ──► engine K1–K7 (0.3, twice) ──► K8 pass ──► pattern_stats pass ──► certificate
                    │            ▲
                    ├─ data readers   worlds:    file / python / derive + mutations
                    ├─ patterns       criteria:  pattern / command / python
                    ├─ mutations      controls, premises, invariances: mutations / world (controls only) / python
                    └─ external processes for command criteria (protocol tg-line/1, section 5)
```

A manifest is compiled into the `Study`, `World`, `Criterion`, `Premise` and `Control` objects of 0.3. A Python study
file keeps working as before.

**What changes in the engine, exactly.** The K1–K7 machinery (`make_sample`, `collect`, the statistics, the
suppression rules, the probes, the identical-minus analysis, the determinism check, the run-1/run-2 reproducibility
comparison) does not change. The complete list of changes:

1. the orchestrator gains a manifest path (section 1.2);
2. after the two evaluations and their comparison, two **separate passes** run: K8 (section 7) and `pattern_stats`
   (section 4). They add flags and fields to the body; they never feed back into K1–K7;
3. the component verdict is computed from the component's K1–K7 flags (after the 0.3 cascade and identical-minus
   suppression) plus its K8 flags and `SUGGESTED_UNREVIEWED`, with the 0.3 verdict function and the new flag classes.
   K8 flags and `SUGGESTED_UNREVIEWED` are added after suppression and are never suppressed;
4. a new body list `study_notes` holds informational study-level notes; **no verdict rule reads it**;
5. flag tables, `BODY_FIELDS`, envelope validation, the CLI table output (it prints the notes) and exit code 7 are
   extended for schema 2;
6. in deterministic studies, declared mutations draw from a generator that does not depend on the sample index
   (section 6);
7. the leak guard's allow-list contains both package folders, `truth_gate` and the `kapi` shim;
8. the package rule "no module imports `subprocess`" (0.3 test `test_package.py`) is kept for every module **except**
   `truth_gate/external.py`, and a test asserts that `external` is the only exception.

Existing error messages, flag names and texts other than `non_claims` and `known_limitations` stay byte-identical.
Criterion A1 (section 14) checks that none of these changes alters the result of a 0.3 study.

### 1.2 Orchestration of a manifest run

1. **Before the guard is armed:** parse and validate the manifest; read every data file into memory and hash it; copy
   the `[external] uses` files into a fresh temporary working folder and hash them; resolve and hash each command's
   executable; start one process per distinct argv and complete the handshake. Any failure here (a manifest error, a
   missing or unhashable executable, a `.cmd`/`.bat` on Windows, a failed handshake) exits with code 4 and no
   certificate.
2. **Under the armed guard:** load the `python` reference files (each is allow-listed, hashed, and subject to the guard
   like a 0.3 study file) and build and validate the `Study` object. Any error in this step, including 0.3's own
   validation errors (no criterion, duplicate ids, a control without criteria), is a `StudyError`: the certificate says
   UNDEFINED and the exit code is 3, as in 0.3. Then evaluate the study twice and compare, exactly as 0.3 does; run the
   K8 and `pattern_stats` passes; take the guard log a third time and append it to `leak_log` (a blocked access in these
   passes raises `K6_LEAK_ATTEMPT` as usual).

**The boundary between exit 4 and exit 3:** errors found from the manifest text and the environment alone (TOML, keys,
types, paths, data files, executables, handshake) give exit 4 and no certificate; errors found while building or
validating the `Study` give a certificate with exit 3.
3. **After leaving the guard:** send `bye` to each process, wait 5 s, kill what remains, print the stderr tails of failed
   processes, delete the working folder (a failure to delete is a warning).

Killing a process never starts a new one (`Popen.kill`, or `os.killpg` for a POSIX process group), so it is allowed
while the guard is armed.

## 2. Compatibility and naming

1. **Package `truth_gate`.** A shim package `kapi` re-exports the public names of `truth_gate` (the same objects), and
   `python -m kapi` runs the same command line. The shim emits no warning. It is documented as deprecated and stays at
   least until 1.0.
2. **Python study files run unchanged** and give the same verdicts, flags and counts as 0.3 (criterion A1).
3. **Certificate schema 2.** `kapi_version` is replaced by `tool = "truth-gate"` and `tool_version`. `spec_version` is
   `"0.6"`. The hash rule is unchanged. New fields are listed in section 11.
4. **Verifying an old certificate.** `verify` on a certificate whose `tool` is missing (made by Kapı 0.3) or whose
   `tool_version` differs from the running version exits with code **7**, printing which version made it and that the
   matching git tag (for example `v0.3.0`) must be used. It never re-runs the study under another version. Because the
   version is part of the hashed body, this applies to patch releases too.

## 3. The manifest

File name `truthgate.toml` by convention. TOML is read with the standard library (`tomllib`). A `.json` file with the
same structure is accepted. Paths are relative to the manifest's folder. **Unknown keys are a validation error**
(exit 4, naming the key). TOML datetimes anywhere, and non-finite numbers in any argument, are validation errors.

### 3.1 Example: a group-difference claim

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

### 3.2 Tables and keys (complete)

| Table | Allowed keys |
|---|---|
| `[study]` | `name` (required), `regimes = ["all"]`, `deterministic = false`, `allow_paths = []`, `relational = []` (pairs) |
| `[data]` | `rows_exchangeable = false`, `rows` (list of row-aligned keys), `columns` (table: key → `{ type, role }`, `type` in `float`, `int`, `bool`, `str`; `role` in `outcome`, `effect`, `group`, `label`, `calibration`, `grid`, `id`, `covariate`) |
| `[worlds.<name>]` | one source: `file` (with `provenance` required, optional `resample`, `fraction`, `delimiter`), or `python`, or `derive` (with `mutations`); `change` (required for `minus`); `origin`. `plus` and `minus` are required, `null` optional, other names allowed. |
| `[[criteria]]` | `id`; one of `pattern` (plus that pattern's arguments, section 4), `command` (argv list), `python` (`"file.py:function"`); optional `regime`, `control_waiver`, `tolerances` (table: name → `[value, scale]`), `components` (command and python only), `origin` |
| `[[controls]]` | `id`, `criteria`; one of `mutations`, `world`, `python`; `origin` |
| `[[premises]]` | `id`, `role` (`tested` or `assumed`), `criteria`; one of `mutations`, `python`; optional `magnitude = [value, scale]`; `origin` |
| `[[invariances]]` | `id`, `criteria`, `mutations`, `reason` (required text), `origin` |
| `[budget]` | `samples`, `quick_samples`, `base_seed` (as 0.3) |
| `[targets]` | `power`, `size`, `alpha_family` (as 0.3) |
| `[external]` | `uses = []` (files copied into the working folder and hashed), `env = []` (extra variable names passed through), `startup_timeout_s = 120`, `request_timeout_s = 60` |

Roles are used only by `suggest`; they never change a verdict rule. Declared types are enforced when data are read.
**Row-aligned keys:** for CSV worlds every column; for every other world the keys in `[data] rows`, which must share
their first-axis length. Row operations (bootstrap, `subsample`, `shuffle`, `permute_rows`, `null_effect`, and the
built-in invariance) on a world without row-aligned keys are a validation error.

### 3.3 World sources

* **`file = "path"`**: CSV, JSON (an object of arrays) or NPZ. `provenance` (free text) is **required** and is written
  into the certificate, because the gate cannot tell a synthetic file from the real data.
  * **CSV dialect.** UTF-8; a byte-order mark is ignored; a header row is required; delimiter `,` unless `delimiter` is
    given; decimal separator `.` only. Missing values: an empty cell, `NA`, `NaN`, `nan`.
  * **Column types.** A declared type is enforced; a value that does not parse is a validation error; a declared `int`
    column may not contain missing values. Undeclared: `bool` if every value is one of `true`, `false`, `TRUE`,
    `FALSE`, `True`, `False`; else float64 if every value is a number or missing (missing becomes NaN); else `str`.
    Auto-detection never produces `int`.
  * **Sampling.** In a stochastic study `resample` is `"bootstrap"` (default: n rows with replacement, n = the table
    length, one row index for all row-aligned keys) or `"subsample"` (`round(fraction · n)` rows without replacement,
    `fraction` in (0, 1)). In a deterministic study `resample` must be `"none"` (the default there): every sample is the
    table itself. Keys that are not row-aligned are copied into every sample unchanged.
* **`python = "file.py:function"`**: `function(rng) -> dict`, loaded under the guard like a 0.3 study file.
* **`derive = "<world>"` and `mutations = [...]`**: a sample of the parent world, then each mutation in order (section
  6). `derived_from` is set to the parent. Derivation cycles are a validation error.
  * **Pairing (0.3 behaviour, kept).** For the identical-minus check, 0.3 draws the paired minus sample with the plus
    generator, so the parent sample equals the plus sample and only the mutations differ. The counted minus samples use
    the minus stream's own generator, so their parent samples are independent draws.

## 4. Criterion patterns

Each pattern returns HOLDS, FAILS or UNDEFINED.

**Common rules.**

* Before any part of a pattern is evaluated, every key it references (including all parts of `all_of`/`any_of`) is
  looked up; a missing key **raises an error**, so the whole criterion is UNDEFINED, as for any exception in 0.3.
* A pattern is UNDEFINED when a selection is empty, a value it uses is not finite, a denominator is zero, or the types
  do not fit (for example a mean of a `str` column).
* Statistics flatten n-dimensional arrays.
* `op` is one of `>`, `>=`, `<`, `<=`. **`==` exists only for `stat = "count"` and in `largest_true`**, where both
  sides are integers or literal grid values.
* `stat` is one of `mean`, `median`, `min`, `max`, `sum`, `std` (ddof = 1; UNDEFINED below 2 values), `quantile` (needs
  `q`; numpy's default linear method), `first`, `last`, `count`, `fraction_true` (bool data).
* Selections: `<arg>_where = { column = ..., equals = ... }` (only for `str` and `bool` columns), or
  `{ column = ..., op = ..., value = ... }` (numeric columns); `<arg>_index = [...]` keeps the listed positions. A
  selection applies to its own argument only.
* Any criterion kind, patterns included, may declare `tolerances`; they are checked by K2 as in 0.3.

| Pattern | Arguments | HOLDS when |
|---|---|---|
| `threshold` | `x`, `stat`, `op`, `value` | `stat(x) op value` |
| `difference` | `a`, `b`, `stat`, `op`, `value`, `paired = false` | `stat(a) − stat(b) op value`; with `paired`, `stat(a − b)` elementwise (unequal lengths: UNDEFINED) |
| `ratio_band` | `a`, `b`, `stat`, `lo`, `hi` | `lo ≤ stat(a) / stat(b) ≤ hi` (both bounds required) |
| `within` | `a`, `b`, `tol`, `mode = "stat"` or `"all"`, `stat` | `stat`: \|stat(a) − stat(b)\| ≤ tol; `all`: \|aᵢ − bᵢ\| ≤ tol for every selected i |
| `rate` | `condition = {column, op, value}`, `op`, `value` | (fraction of selected rows meeting `condition`) `op value` |
| `ci_excludes` | `x` with `stat`, or `a` and `b` (a difference of means; `paired = false`); `level = 0.95`, `side` (`above` or `below`), `value`; either `replicates = "<key>"` or the internal bootstrap with `B = 2000` and `seed = 0` | the central `level` percentile interval (numpy's default linear method) lies entirely above (or below) `value`. The internal bootstrap uses `numpy.random.default_rng(seed)` and resamples positions of the **sorted** values (each group sorted separately; with `paired`, pairs sorted lexicographically and resampled as pairs), so the criterion is a pure function of the data and independent of row order. |
| `largest_true` | `grid` (a **literal list** in the manifest, positional), `y`, `op`, `threshold`; `compare_to` = `{ y = ..., op = ..., threshold = ... }` (a second curve) or `{ value = ... }` (a literal grid value); `cmp` (`==`, `>=`, `<=`) | `y` is read by position against `grid` (length mismatch: UNDEFINED). The largest grid value where `y op threshold`, compared with the reference by `cmp`. **UNDEFINED when either side has no qualifying grid value, or when any `y` value is not finite** (a vacuous `0 = 0` cannot hold; GHZ lesson). |
| `monotone` | `x` (ordering), `y`, `direction` (`increasing` or `decreasing`), `strict = false`, `tol = 0` | `y` ordered by `x` moves in `direction`, allowing steps of up to `tol` against it |
| `all_of`, `any_of` | `of = [ {pattern...}, ... ]` | Kleene logic. `all_of`: FAILS if any part FAILS, else UNDEFINED if any part is UNDEFINED, else HOLDS. `any_of`: HOLDS if any part HOLDS, else UNDEFINED if any part is UNDEFINED, else FAILS. |

**`pattern_stats` (a separate pass).** After the two evaluations, the gate regenerates the counted samples of the
`plus`, `minus` and `null` streams with the engine's own seeds and sample function (`stream_rng`, `make_sample`; the
same samples K1–K7 saw): indices below `sample_count` of the mode, or index 0 in a deterministic study. For every
pattern criterion and each of these streams it records the 5%, 50% and 95% quantiles (numpy's linear method, stored as
float64 without rounding) of the statistic(s) it computes, its thresholds, and the number of finite values. Parts of
`all_of`/`any_of` are recorded separately, keyed by their position path (`"0"`, `"1.0"`, ...). UNDEFINED samples are
excluded. The pass runs once and is added to the body after the reproducibility comparison. It never changes a
verdict.

## 5. Command criteria: protocol `tg-line/1`

A criterion can be a program in any language. In 0.4 the data flow one way: the gate sends a sample, the program
returns an outcome.

**Process.**

* `command` is an argv list (never a shell string). `argv[0]` is resolved with the inherited `PATH`, then with
  `os.path.realpath`, and the result must be a readable file; on Windows it must be an `.exe` or `.com`. A `.cmd` or
  `.bat` file is rejected with a hint to call the interpreter directly (for example `["node", "criteria.js"]`).
* One process per distinct argv, started before the guard is armed (section 1.2). It serves both evaluations and the
  K8 pass. State it carries between requests is therefore exposed by the reproducibility check as
  `K6_NONREPRODUCIBLE` when it changes an outcome. A dead process is not restarted.
* **Working folder:** a fresh temporary folder holding copies of the `[external] uses` files and the `allow_paths`,
  with their relative layout. A relative path to a real result file therefore does not resolve by accident.
* **Environment:** `PATH`, `HOME`, `USERPROFILE`, `APPDATA`, `LOCALAPPDATA`, `SYSTEMROOT`, `TEMP` and `TMP` are passed
  through with their current values (so that R, Julia and Node find their libraries), plus `LANG = C.UTF-8`,
  `TG_PROTOCOL = tg-line/1` and the names in `[external] env`. Nothing else.
* On POSIX the process starts in its own session and a kill reaches its process group. On Windows only the process
  itself is killed; grandchildren may survive (documented limit).
* Standard error goes to a temporary file; after the guard is disarmed, the last 20 lines of a failed process are
  printed to the terminal. Nothing from standard error enters the certificate.
* The program writes one line per reply and flushes it. Logs go to standard error.

**Messages** (one JSON object per line, UTF-8). `rid` is an integer that increases by one with every request.

| Request from the gate | Expected reply |
|---|---|
| `{"op": "hello", "tg": "tg-line/1", "rid": 0}` | `{"ok": true, "tg": "tg-line/1", "rid": 0}` within `startup_timeout_s` |
| `{"op": "criterion", "id": "C2", "rid": k, "types": {...}, "data": {...}}` | `{"rid": k, "outcome": "HOLDS"}` (or `FAILS`, `UNDEFINED`); with components, `{"rid": k, "outcome": {"name": "HOLDS", ...}}`; or `{"rid": k, "error": "text"}` |
| `{"op": "bye", "rid": k}` | none required; the process exits |

**Failures.**

* `{"rid": k, "error": ...}` makes that one outcome UNDEFINED, recorded as `ExternalError`. The process keeps serving.
* A timeout (`request_timeout_s`, enforced with a reader thread on every platform), a line that is not JSON, a wrong or
  missing `rid`, or a reply with neither `outcome` nor `error` **kills the process**. That outcome is recorded as
  `ExternalTimeout` or `ExternalProtocolError`; every later request to that argv is UNDEFINED (`ExternalDied`), and the
  note `EXTERNAL_DIED` is added to `study_notes`. A killed process cannot answer late, so replies can never shift.
* The UNDEFINED outcomes reach the verdict through K1, as in 0.3.

**Read-key recording.** 0.3 calls each criterion once more on a recording dictionary to learn which keys it reads.
For a command criterion this is a real request, and the adapter serialises every key, so all keys count as read and
`K2_MINUS_UNREAD` is never raised for command criteria.

**Data codec (gate to program).** `data` is a JSON object of arrays as nested lists. `types` gives, for every key, its
dtype (`float`, `int`, `bool`, `str`) and shape, so empty arrays are unambiguous. Non-finite floats are sent as the
strings `"NaN"`, `"Infinity"` and `"-Infinity"`. Integers outside ±2⁵³ are an encoding error (that outcome is
UNDEFINED), because JavaScript and R would lose precision.

**What is guarded, hashed and disclosed.** The leak guard cannot see inside another process. The study note
`K6_EXTERNAL_UNGUARDED` lists the commands; the CLI table, the Action summary and the badge show it (section 9), and
a non-claim states it (section 11). The certificate records the argv, the SHA-256 of every `uses` file and of the
resolved executable. Libraries the program loads (R packages, `node_modules`) are not hashed (documented limit).

## 6. Mutation library

A mutation is an inline table `{ op = "...", ... }`, applied to a copy of the sample, never in place. A mutation that
references a missing key or does not fit the data raises an error, which the engine turns into UNDEFINED. Ops marked
† accept a `where` selection (same rules as in section 4) that limits them to some rows.

| Op | Arguments | Effect | Models |
|---|---|---|---|
| `shuffle` | `column` or `columns` | permutes the first axis of the listed keys (jointly) relative to all others | association that is not there; labels unrelated to outcomes |
| `swap` | `a`, `b` | exchanges two arrays of the same shape | mixed-up columns |
| `scale` † | `column`, `factor` | multiplies by `factor` | unit errors |
| `offset` † | `column`, `value` | adds `value` | zero-point and baseline errors; a stray ε |
| `constant` † | `column`, `value` or `stat` (`mean`, `median`, `first`) | replaces the values by one value | no variation; an effect set to zero |
| `noise` † | `column`, `sd` or `rel_sd` (relative to the column's standard deviation) | adds N(0, sd) | measurement noise; robustness |
| `subsample` | `fraction` | keeps `round(fraction · n)` random rows, without replacement | small-sample fragility |
| `null_effect` | `outcome`, `group`, `reference` | replaces the outcomes of all non-reference rows by values drawn with replacement from the reference rows | "the claimed group difference is absent" |
| `reverse` | `column` | reverses the first axis | a direction test that cannot tell a path from its mirror image |
| `sign_flip` † | `column` | multiplies by −1 | sign conventions; direction claims |
| `permute_rows` | none | permutes all row-aligned keys jointly (associations kept) | dependence on row order |

**Rules.**

* **dtype.** `scale` with an integer factor, `offset` with an integer value and `sign_flip` keep an `int` column `int`;
  otherwise an `int` column becomes float64. Every other op keeps the dtype.
* **No-op parameters are validation errors:** `factor = 1`, `offset` `value = 0`, `fraction = 1`, `sd = 0`,
  `rel_sd = 0`.
* **Random draws of declared mutations.** In a stochastic study a mutation draws from the generator of the stream and
  sample it runs in. In a deterministic study it draws from a generator seeded by the base seed and the declaration id,
  identical at every sample index, so the 0.3 determinism check stays meaningful. (K8's own transformation draws are a
  different matter, section 7.)

Whether a mutation should break the claim or leave it intact follows from where it is used: in `minus` (the criterion
should fail), in a control (the theory is broken; the criterion must not hold), in a premise, or in an invariance (the
outcome must not change). The certificate lists the ops of every declaration.

## 7. K8: invariance (a separate pass)

An invariance declares a transformation that, by the study's own logic, must not change any criterion outcome (row
order for exchangeable rows; a consistent change of units for a scale-free criterion).

* **When.** After the two evaluations and their comparison, under the armed guard. K8 never feeds samples or outcomes
  back into K1–K7, and its draws are not part of the 0.3 determinism check.
* **Pairs.** For each invariance, each listed criterion component and each of the worlds `plus` and `minus`:
  * stochastic study: the counted samples of that world in the current mode (`sample_count`) are regenerated with the
    engine's seeds; each is evaluated before and after one transformation drawn from the gate's stream
    `k8:<invariance>:<world>:<i>`;
  * deterministic study: the one sample is evaluated once untransformed and after `budget.samples` transformations
    (`quick_samples` in quick mode), each drawn from `k8:<invariance>:<world>:<j>`.
  Pairs with an UNDEFINED side are counted apart.
* **Rate and family.** For each (invariance, component, world) the rate of changed outcomes among the defined pairs is
  tested on its own. K8 has **its own Bonferroni family**: `m_K8` = 2 × the number of (invariance, component) pairs,
  and each test uses the one-sided Wilson lower bound at level `alpha_family / m_K8`. The K1–K7 family is unchanged.
  The study-wide family-wise error rate is therefore at most `2 · alpha_family`; the certificate states this.
* **Flags (per component).** `K8_NOT_INVARIANT` (mandatory): for either world, the Wilson lower bound of the change
  rate exceeds `targets.size`. `K8_SOME_CHANGES` (info): at least one change, below that threshold.
  `K8_INCONCLUSIVE` (capping): for either world, more than 50% of the pairs have an UNDEFINED side.
* **Built-in invariance.** With `rows_exchangeable = true`, a `permute_rows` invariance is added for every criterion and
  cannot be removed. The default is `false`, because time series and ordered grids are not exchangeable.

## 8. `suggest`: a starter manifest from one dataset

```text
truth-gate suggest DATA.csv [--outcome COL] [--group COL --reference VALUE] [--effect COL ...]
                            [--exchangeable] [--out truthgate.toml]
```

It prints, and writes as a comment at the top of the manifest, a warning that DATA must be a realistic synthetic or
pilot dataset, **not the real study data**. It writes:

* `[data]` with the inferred types and the given roles;
* `plus` as a bootstrap of DATA, with `provenance = "TODO"`, which is a validation error until it is replaced;
* a `minus` world: `null_effect` when `--group` and `--outcome` are given, otherwise `shuffle` of each `--effect`
  column, with the other candidates as comments;
* controls: `shuffle` of the group or outcome column, and `sign_flip` of effect columns;
* `rows_exchangeable = true` only with `--exchangeable`;
* **no active criterion.** Every pattern appears as a commented template with the column names filled in.

Every generated declaration carries `origin = "suggested"`. While any declaration carries it, every component gets the
capping flag **`SUGGESTED_UNREVIEWED`** (at most WEAK). Deleting the key states that a declaration has been reviewed.
The GitHub Action fails whenever this flag is present, whatever its `fail-on` setting says.

## 9. Command line

`truth-gate` (also `python -m truth_gate` and `python -m kapi`):

| Command | Does |
|---|---|
| `check TARGET [--out CERT] [--quick]` | TARGET is a 0.3 Python study (`.py`) or a manifest (`.toml`, `.json`). The table output ends with the study notes. |
| `verify CERT TARGET` | as in 0.3; exit 7 on a tool version mismatch (section 2.4) |
| `suggest DATA ...` | section 8 |
| `init [DIR] [--ci]` | writes `PREREG.md`, `truthgate.toml` (a minimal example), `BLIND_AUDIT_PROMPT.md`, `run_guarded.py` and, with `--ci`, `.github/workflows/truth-gate.yml`. Never overwrites a file (exit 4 with the list of existing files). |
| `freeze write ...`, `freeze verify ...` | the semantics of `protocol/tools/freeze.py`, unchanged; the standalone script stays and must give byte-identical manifests |
| `badge CERT [--out FILE]` | checks `body_sha256` (a mismatch exits 5) and refuses a quick-mode certificate (exit 4); writes a shields.io endpoint JSON `{"schemaVersion": 1, "label": "truth gate", "message": ..., "color": ...}`. Message: the verdict, with " (unguarded)" appended when the note `K6_EXTERNAL_UNGUARDED` is present. Colour: `brightgreen` for FALSIFIABLE, `green` for FALSIFIABLE (unguarded), `yellow` for WEAK, `red` otherwise. |
| `explain FLAG` | prints what a flag or note means, what usually causes it, and the protocol rule behind it; covers every flag and note |

Exit codes as in 0.3 (0, 1, 2, 3, 4, 5, 6) plus 7.

## 10. Distribution

* `pyproject.toml`: distribution `truth-gate`, packages `truth_gate` and `kapi`, console script `truth-gate`, one
  dependency (`numpy`).
* Install without PyPI: `pipx install git+https://github.com/Mukanto/truth_gate`. Publishing on PyPI needs the
  author's account and approval and is not part of this spec.
* **GitHub Action** (`action.yml` at the repository root, composite). Inputs: `target`, `freeze` (optional manifest
  path), `quick = false`, `fail-on = "NOT_FALSIFIABLE,UNDEFINED,UNTESTED"`. Steps: set up Python (pinned action
  version), install the action's own checkout, run `check`, run `freeze verify` if given, write the table and the study
  notes to `$GITHUB_STEP_SUMMARY`, upload the certificate as an artifact, and fail on a `fail-on` verdict or on
  `SUGGESTED_UNREVIEWED`. The logic lives in `truth_gate.ci` and is unit-tested with a fake environment.
* **pre-commit** (`.pre-commit-hooks.yaml`): `truth-gate-freeze` (verifies the freeze manifests passed as arguments)
  and `truth-gate-check` (a quick check of changed manifests).

## 11. Certificate additions

* `tool`, `tool_version`, `spec_version = "0.6"`, `input_kind` (`python` or `manifest`).
* `manifest`: the SHA-256 of the manifest bytes; its parsed form as canonical JSON; every data file, `uses` file and
  `python` reference file with its SHA-256; the `provenance` texts; every command (argv and executable SHA-256).
* `mutations`: the ops of every world, control, premise and invariance.
* `k8`: per (invariance, component, world) the pair counts, changes, UNDEFINED pairs and Wilson bound; `m_k8`; and the
  statement "study-wide family-wise error rate at most 2 · alpha_family" when K8 ran.
* `pattern_stats` (section 4), `suggested_unreviewed` (a count), `study_notes`.
* `non_claims`: the three of 0.3 (with "Kapı" replaced by "The gate") plus three new ones:
  * "Generated mutations and suggested declarations are generic; they do not know your domain."
  * "A file world is only as independent as its provenance; a plus world built from the real data makes the plus and
    minus checks circular."
  * "The leak guard does not cover external programs; a study note lists them."
* `known_limitations`: the three of 0.3 unchanged, plus: "External programs are hashed by executable and `uses` files
  only; the libraries they load are not hashed." and "On Windows, killing an external program does not kill programs it
  started."

New flags and notes:

| Name | Kind |
|---|---|
| `K8_NOT_INVARIANT` | flag, mandatory |
| `K8_INCONCLUSIVE` | flag, capping |
| `K8_SOME_CHANGES` | flag, info |
| `SUGGESTED_UNREVIEWED` | flag, capping, on every component |
| `K6_EXTERNAL_UNGUARDED` | study note (never affects a verdict; shown in the table, the Action and the badge) |
| `EXTERNAL_DIED` | study note (the UNDEFINED outcomes act through K1) |

## 12. User guidance that follows from the design

* **Put the analysis inside the criterion.** The gate can only test what the criterion computes. If a criterion
  compares a precomputed accuracy with 0.7, no probe reaches the pipeline that produced it. If the criterion runs the
  pipeline (selection, fitting, evaluation) on the data it is given, a circular selection or a leak makes it hold on
  noise, and K4 and K5 catch it. With `tg-line/1` the pipeline can stay in R, Julia or any other language.
* The `plus` file must be realistic and must not be the real data. `provenance` makes that claim visible.

## 13. Tests required of the implementation

* **The 388 tests of 0.3 pass.** Permitted edits: import paths and the `PACKAGE`/`MODULES` paths of
  `test_package.py`; assertions on `kapi_version`, `spec_version`, the certificate's field list and the number and text
  of `non_claims`; tables of exit codes. The no-`subprocess` rule stays and is extended as in section 1.1 (8). Every
  edited assertion is listed in the implementation report.
* Unit tests: every pattern (a truth table including each UNDEFINED condition and the missing-key rule inside
  `any_of`); every mutation (shapes, row alignment, dtype rules, no-op validation, seeded determinism in both modes, no
  in-place change); the codec (NaN, infinities, bool, str, empty and nested arrays, the ±2⁵³ rule); the protocol
  (handshake, error reply, timeout, malformed line, wrong `rid`, death, components); every validation error class and
  the exit 4 / exit 3 boundary; K8 in both modes, including its separate family and that it leaves K1–K7 output
  unchanged; `pattern_stats` equals a direct recomputation; `suggest` output parses, exits 4 until `provenance` is set, then
  reaches exactly the zero-criteria `StudyError` (exit 3), and runs once a criterion is added; `init` never overwrites; `freeze` byte-identical to the standalone script; `badge` (hash
  check, quick refusal, unguarded label); `explain` covers every flag and note; `ci` with a fake environment.
* Cross-language tests run when `node` is on `PATH` and are reported as skipped otherwise (A3 itself does not allow a
  skip; section 14).

## 14. Pre-registered evaluation of 0.4

Written before implementation. "HOLDS" here is about the tool, not about a study.

**Baseline.** Before implementation step (a):

* **The study list.** Every `.py` file under `examples/`, `evaluation/cases/` and `tests/toy_studies/` (recursive) that
  assigns a module-level `STUDY` is an A1 study. The list, with each file's SHA-256, is written to
  `baseline_v030/STUDIES.json`. These files are not modified by 0.4 (their `from kapi import ...` works through the
  shim).
* **The run.** The `kapi` package of tag `v0.3.0` is exported to a separate folder and put on the import path; each
  study is run from its place in the repository (the same absolute path the 0.4 runs will use), in full mode, with the
  implementation environment's Python and numpy. One certificate body per study goes to `baseline_v030/`.

**A1 strip rule (fixed now).** Before comparison, remove from both bodies: `kapi_version`, `tool`, `tool_version`,
`spec_version`, `non_claims`, `known_limitations` (wherever they appear), and every field that is new in schema 2
(`input_kind`, `manifest`, `mutations`, `k8`, `m_k8`, `pattern_stats`, `suggested_unreviewed`, `study_notes`). Nothing
else is removed. For a Python study, `describe_study` gains no keys. **Exception, fixed now:** for a study whose
baseline body carries `K6_NONREPRODUCIBLE` (it uses unseeded randomness on purpose, so its counts differ between any
two runs), A1 compares the verdict and the sets of component and study flags only.

**Phase A, internal (before release):**

| id | Claim | HOLDS when |
|---|---|---|
| A1 | Python studies behave exactly as in 0.3 | for every Python study in `examples/`, `evaluation/cases/` and `tests/toy_studies/`, the stripped 0.4 body equals the stripped baseline body |
| A2 | Manifests reproduce hand-written studies | the examples 01, 02, 03 and `convergence_criteria`, rewritten as manifests, give the same verdict, the same flags and the same tolerance declarations as the Python originals. **Required coverage:** the criterion of example 03 (both twins) and criterion C3 of `convergence_criteria` are patterns; every control and every premise of examples 01–03 is a mutation. Worlds may be `python` references. No manifest declares `rows_exchangeable` or invariances. |
| A3 | Any language gives the same answer | the criteria of examples 01–03 as Node programs, with the same worlds as the A2 manifests: the same verdict, the same flags apart from `K2_MINUS_UNREAD`, and the same per-stream HOLDS and UNDEFINED counts. A missing `node` is a failure of A3, not a skip. |
| A4 | K8 catches order dependence and changes the verdict | the planted pair in 14.1: the faulty twin is NOT_FALSIFIABLE and `K8_NOT_INVARIANT` is its only mandatory flag; the fixed twin is FALSIFIABLE with no K8 flag |

**Phase B, external evidence (runs on the frozen 0.4.0; its own pre-registration, frozen before any case is built).**
This section fixes its principles:

* **Error classes in scope,** chosen because the gate's mechanism reaches them when the analysis is inside the
  criterion. This choice is the claimed scope, not evidence of breadth:
  * B-1 circular analysis ("double dipping"): selection and test on the same data, so the criterion holds on noise;
  * B-2 data leakage in machine-learning evaluation: a held-out score that stays high when labels are shuffled;
  * B-3 tautological criteria: a target computed from the labels it is compared with;
  * B-5 unit and scale errors in criteria whose thresholds carry units.
  * B-4 (inert or mirror-blind tests) is reported apart as a known-mechanism class, because the identical-minus check
    was built for it.
* **Out-of-scope classes** stay in the set (for example model misspecification such as the GHZ readout error). They
  are expected to be missed and are reported without a threshold.
* **Cases** come from errors documented in the literature. Candidate sources, to be verified before the Phase B freeze:
  Kriegeskorte et al. 2009 on circular analysis; Vul et al. 2009 on inflated correlations; Kapoor and Narayanan 2023
  on leakage. Each case is a minimal faulty study and a corrected twin, written by a session that has the public
  documentation and the papers but not the implementation. The authors are models that have read the documentation;
  this limit is stated in the report, and a human reader with domain knowledge is sought.
* **Expected flags** are fixed per class in the Phase B pre-registration, naming specific flags and streams (no
  wildcards; for example `K5_HOLDS_ON_NOISE`, `K5_HOLDS_ON_SHUFFLE`, `K4_CONTROL_ALSO_HOLDS`, `HIGH_RATE:probe:noise`).
* **Metrics per class:** detection = the faulty twin is NOT_FALSIFIABLE **and** carries at least one expected flag;
  UNDEFINED, UNTESTED and load errors count as misses. Clean pass = the corrected twin is FALSIFIABLE or WEAK.
* **Thresholds:** for each in-scope class, at least 10 pairs, and the one-sided 95% Wilson lower bound of detection and
  of clean pass both at least 0.6 (so 9/10 passes and 8/10 fails).
* **Comparators, reported:** the 0.3.0 tool on the same cases (Python cases only) and a trivial "flag everything"
  baseline (detection 1, clean pass 0).

### 14.1 The planted pair for A4

A helper file `a4_worlds.py` defines `plus(rng)` returning `{"x": rng.normal(1.4, 1.0, 40)}` and `minus(rng)` returning
`{"x": rng.normal(0.0, 1.0, 40)}`. The faulty manifest:

```toml
[study]
name = "A4 faulty: reads the first 10 rows of an exchangeable table"

[data]
rows_exchangeable = true
rows = ["x"]

[worlds.plus]
python = "a4_worlds.py:plus"

[worlds.minus]
python = "a4_worlds.py:minus"
change = "mean 1.4 -> 0"

[[criteria]]
id = "C"
pattern = "threshold"
x = "x"
x_index = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
stat = "mean"
op = ">"
value = 1.0

[[controls]]
id = "negated"
criteria = ["C"]
mutations = [ { op = "sign_flip", column = "x" } ]
```

The fixed manifest is identical without `x_index`. Expected from a simulation made while writing this section (not a
criterion): the faulty twin holds in about 0.90 of plus samples and 0.0007 of minus samples, and changes under row
permutation in about 0.17 of plus samples; the fixed twin holds in about 0.99 of plus samples and is invariant.

## 15. Work plan

1. Drafts v1–v3.1, three blind reviews, revisions with reasons, freeze (done).
2. Record the baseline (section 14).
3. Implementation by the coding agent in steps, each with its tests: (a) rename, shim, guard allow-list, schema 2 and
   A1; (b) manifest, data readers, patterns, mutations, `pattern_stats`; (c) `tg-line/1` and the Node example; (d) K8,
   `suggest`, `init`, `badge`, `explain`, `freeze`; (e) Action and pre-commit; documentation.
4. Phase A, independent recomputation, blind audit of the code.
5. Release 0.4.0 (pushing and tagging need the author's approval). Then Phase B.

## 16. Decisions taken under delegation (open to the author's objection)

* TOML as the main format (standard library); JSON accepted; YAML deferred.
* The K1–K7 machinery untouched; K8 and `pattern_stats` as separate passes; K8 with its own family, so the study-wide
  family-wise error rate is at most 2 · alpha_family.
* One persistent process per argv, with request ids and kill-on-failure.
* `suggest` never writes an active criterion, and suggested declarations cap the verdict until reviewed.
* Unguarded external programs are disclosed in the table, the Action and the badge, not capped.
* Release after Phase A; Phase B on the frozen release.
