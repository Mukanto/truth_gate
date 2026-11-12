# Truth_Gate: manifest reference

A manifest describes a study without Python code: where the worlds come from, what the criteria are, what breaks the
theory on purpose, and what must not change the result. `truth-gate check truthgate.toml` compiles it into the objects
of the 0.3 engine ([`GATE.md`](GATE.md)) and runs the same checks, plus K8. This page is the reference. The design
record is [`design/spec-0.6.md`](design/spec-0.6.md); where a later decision refined the spec, this page documents the
implemented behaviour, and the entry (R-n) is named in [`design/spec-0.6-REVISIONS-post-freeze.md`](design/spec-0.6-REVISIONS-post-freeze.md).

A Python study file keeps working as before, and gives the same verdicts, flags and counts as 0.3.

## Contents

1. [Example](#1-example)
2. [File format and general rules](#2-file-format-and-general-rules)
3. [Tables and keys](#3-tables-and-keys)
4. [Worlds](#4-worlds)
5. [Criteria: patterns](#5-criteria-patterns)
6. [Criteria: commands in any language (`tg-line/1`)](#6-criteria-commands-in-any-language-tg-line1)
7. [Mutations](#7-mutations)
8. [Controls and premises](#8-controls-and-premises)
9. [Invariances and K8](#9-invariances-and-k8)
10. [`suggest`: a starter manifest](#10-suggest-a-starter-manifest)
11. [Errors and exit codes](#11-errors-and-exit-codes)

## 1. Example

This is `tests/manifests/trial_example.toml` (with `synthetic_trial.csv` next to it).

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

## 2. File format and general rules

* The file is `truthgate.toml` by convention. TOML is read with the standard library. A `.json` file with the same
  structure is accepted. UTF-8; a byte-order mark is ignored.
* Paths are relative to the manifest's folder.
* **Unknown keys are a validation error** (exit 4, naming the key). So are TOML datetimes anywhere and non-finite
  numbers in any argument.
* Roles in `[data.columns]` (`outcome`, `effect`, `group`, `label`, `calibration`, `grid`, `id`, `covariate`) are used only
  by `suggest`. They never change a verdict rule.
* `origin` may appear on a world, criterion, control, premise or invariance. The only allowed value is `"suggested"`
  (R-9): it says that `truth-gate suggest` wrote the declaration and nobody has reviewed it. While any declaration
  carries it, every component gets the capping flag `SUGGESTED_UNREVIEWED` (verdict at most WEAK). Deleting the key
  states that you reviewed the declaration. A typo such as `origin = "suggest"` is a validation error.

## 3. Tables and keys

| Table | Allowed keys |
|---|---|
| `[study]` | `name` (required), `regimes = ["all"]`, `deterministic = false`, `allow_paths = []` (static read-only files the study may open; hashed), `relational = []` (pairs of keys for the shuffle probe) |
| `[data]` | `rows_exchangeable = false`, `rows` (list of row-aligned keys), `columns` (table: key to `{ type, role }`; `type` is `float`, `int`, `bool` or `str`) |
| `[worlds.<name>]` | one source: `file` (with `provenance` required; optional `resample`, `fraction`, `delimiter`), or `python`, or `derive` (with `mutations`); `change` (required for `minus`); `origin`. `plus` and `minus` are required, `null` is optional, other names are allowed |
| `[[criteria]]` | `id`; one of `pattern` (plus that pattern's arguments), `command` (an argv list), `python` (`"file.py:function"`); optional `regime`, `control_waiver`, `tolerances` (table: name to `[value, scale]`), `components` (command and python criteria only), `origin` |
| `[[controls]]` | `id`, `criteria`; one of `mutations`, `world`, `python`; `origin` |
| `[[premises]]` | `id`, `role` (`tested` or `assumed`), `criteria`; one of `mutations`, `python`; optional `magnitude = [value, scale]`; `origin` |
| `[[invariances]]` | `id`, `criteria`, `mutations`, `reason` (required text), `origin` |
| `[budget]` | `samples` (200), `quick_samples` (20), `base_seed` (20261105) |
| `[targets]` | `power` (0.8), `size` (0.05, the declared alpha), `alpha_family` (0.05) |
| `[external]` | `uses = []` (files copied into the programs' working folder and hashed), `env = []` (extra variable names passed through), `startup_timeout_s = 120`, `request_timeout_s = 60` |

The meaning of `regimes`, `deterministic`, `tolerances`, `control_waiver`, `components`, premises, controls, budget and
targets is that of 0.3 ([`GATE.md`](GATE.md#writing-a-study)).

* A `python` reference is `"file.py:function"`. The file is loaded under the leak guard, allow-listed and hashed.
  The signatures: a world `function(rng) -> dict`; a criterion `function(data) -> bool | None | dict`; a control
  `transform(data, rng) -> dict` (R-12); a premise `mutate(data, rng) -> dict`.
* A control with `world = "<name>"` uses data drawn from that world instead of a transformation of `plus`.
* Missing `plus` or `minus`, an invalid premise `role`, no criterion, duplicate ids and a control without criteria are
  0.3's own validation errors: a certificate with the verdict UNDEFINED and exit code 3 (R-5).

## 4. Worlds

**Row-aligned keys.** For a CSV world every column is row-aligned. For every other world the row-aligned keys are those in
`[data] rows`, and they must share their first-axis length. Row operations (bootstrap, `subsample`, `shuffle`,
`permute_rows`, `null_effect` and every invariance) on a world without row-aligned keys are a validation error (exit 4,
naming the world). Every invariance, the built-in one included, needs row-aligned keys on both `plus` and `minus` (R-23).

### `file = "path"`

CSV, JSON (an object of arrays) or NPZ. `provenance` (free text) is **required** and is written into the certificate,
because the gate cannot tell a synthetic file from the real data. A missing provenance, an empty one, or `"TODO"` (what
`suggest` writes) is a validation error. The files `uses` and `allow_paths` must lie inside the manifest's folder
(R-16); `provenance`, `resample`, `fraction` and `delimiter` are valid only in `file` worlds (R-12).

**CSV rules.**

| Rule | |
|---|---|
| Encoding and header | UTF-8; a byte-order mark is ignored; a header row is required |
| Delimiter | `,` unless `delimiter` is given |
| Decimal separator | `.` only |
| Missing values | an empty cell, `NA`, `NaN` or `nan`. Blank lines after the last data line are ignored; a blank line between data lines is a missing value in a single-column file and a validation error (exit 4) in a multi-column file (R-31) |
| Declared type | enforced. A value that does not parse is a validation error. A declared `int` column may not contain missing values |
| Undeclared type | `bool` if every value is one of `true`, `false`, `TRUE`, `FALSE`, `True`, `False`; else float64 if every value is a number or missing (missing becomes NaN); else `str`. Auto-detection never produces `int` |
| A declared column missing from the file | exit 4 (R-12) |

**Sampling.**

| `resample` | Stochastic study | Deterministic study |
|---|---|---|
| `"bootstrap"` (default) | n rows with replacement, n = the table length; one row index for all row-aligned keys | not allowed |
| `"subsample"` | `round(fraction * n)` rows without replacement; `fraction` in (0, 1) | not allowed |
| `"none"` | not allowed | every sample is the table itself (the default there) |

Keys that are not row-aligned are copied into every sample unchanged. JSON and NPZ row resampling needs `[data] rows`.

### `python = "file.py:function"`

`function(rng) -> dict` of numpy arrays.

### `derive = "<world>"` with `mutations = [...]`

A sample of the parent world, then each mutation in order ([section 7](#7-mutations)). `derived_from` is set to the
parent. A derivation cycle is a validation error.

**Pairing (0.3 behaviour, kept).** For the identical-minus check, the paired minus sample is drawn with the plus
generator, so the parent sample equals the plus sample and only the mutations differ. The counted minus samples use the
minus stream's own generator, so their parent samples are independent draws.

## 5. Criteria: patterns

Each pattern returns HOLDS, FAILS or UNDEFINED.

**Common rules.**

* Before any part of a pattern is evaluated, every key it references (including all parts of `all_of` and `any_of`) is
  looked up. A missing key **raises an error**, so the whole criterion is UNDEFINED, as for any exception in 0.3.
* A pattern is UNDEFINED when a selection is empty, a value it uses is not finite, a denominator is zero, or the types do
  not fit (for example a mean of a `str` column).
* Statistics flatten n-dimensional arrays.
* `op` is one of `>`, `>=`, `<`, `<=`. `==` exists only for `stat = "count"` and in `largest_true`, where both sides are
  integers or literal grid values.
* `stat` is one of `mean`, `median`, `min`, `max`, `sum`, `std` (ddof = 1; UNDEFINED below 2 values), `quantile` (needs
  `q` in [0, 1]; numpy's default linear method), `first`, `last`, `count`, `fraction_true` (bool data).
* **Selections.** `<arg>_where = { column = ..., equals = ... }` (only for `str` and `bool` columns) or
  `{ column = ..., op = ..., value = ... }` (numeric columns); `<arg>_index = [...]` keeps the listed positions. A
  selection applies to its own argument only. `_where` and `_index` together on one argument are a validation error (R-12).
  An empty selection (for `count` too) and an `_index` position outside the array make that leaf UNDEFINED, so Kleene logic
  still applies inside `all_of`/`any_of` and `pattern_stats` drops only that leaf's value (R-32).
* Any criterion kind may declare `tolerances`; K2 checks them as in 0.3.

| Pattern | Arguments | HOLDS when |
|---|---|---|
| `threshold` | `x`, `stat`, `op`, `value` | `stat(x) op value` |
| `difference` | `a`, `b`, `stat`, `op`, `value`, `paired = false` | `stat(a) - stat(b) op value`; with `paired`, `stat(a - b)` elementwise (unequal lengths: UNDEFINED) |
| `ratio_band` | `a`, `b`, `stat`, `lo`, `hi` | `lo <= stat(a) / stat(b) <= hi`; both bounds are required; a zero denominator is UNDEFINED |
| `within` | `a`, `b`, `tol`, `mode = "stat"` or `"all"`, `stat` | `stat`: abs(stat(a) - stat(b)) <= tol; `all`: abs(a_i - b_i) <= tol for every selected i |
| `rate` | `condition = {column, op, value}`, `op`, `value`, optional `where` or `index` | (fraction of the selected rows meeting `condition`) `op value`. The selection key is unprefixed and applies to the rows of the condition column (R-3) |
| `ci_excludes` | `x` with `stat`, or `a` and `b` (a difference of means; `paired = false`); `level = 0.95`, `side` (`above` or `below`), `value`; either `replicates = "<key>"`, or the internal bootstrap with `B = 2000` and `seed = 0` | the central `level` percentile interval (numpy's default linear method) lies entirely above (or below) `value`. With `replicates`, the arguments `x`, `a`, `b`, `stat`, `B` and `seed` are not allowed (R-6) |
| `largest_true` | `grid` (a literal list in the manifest, positional), `y`, `op`, `threshold`; `compare_to` = `{ y = ..., op = ..., threshold = ... }` (a second curve) or `{ value = ... }` (a literal grid value); `cmp` (`==`, `>=`, `<=`), required (R-7) | `y` is read by position against `grid` (a length mismatch is UNDEFINED). The largest grid value where `y op threshold`, compared with the reference by `cmp`. **UNDEFINED when either side has no qualifying grid value, or when any `y` value is not finite** (a vacuous `0 = 0` cannot hold) |
| `monotone` | `x` (ordering), `y`, `direction` (`increasing` or `decreasing`), `strict = false`, `tol = 0` | `y` ordered by `x` moves in `direction`. Let v be the largest step against `direction`. `strict = false`: HOLDS iff v <= tol. `strict = true`: HOLDS iff v < tol. With `tol = 0` these are "non-decreasing" and "strictly increasing" (R-8). Ties in `x` are ordered against `direction` (`y` descending for `increasing`), so the result does not depend on row order (R-30) |
| `all_of`, `any_of` | `of = [ {pattern...}, ... ]` | Kleene logic. `all_of`: FAILS if any part FAILS, else UNDEFINED if any part is UNDEFINED, else HOLDS. `any_of`: HOLDS if any part HOLDS, else UNDEFINED if any part is UNDEFINED, else FAILS |

**The internal bootstrap of `ci_excludes`** uses `numpy.random.default_rng(seed)` and resamples positions of the sorted
values (each group sorted separately; with `paired`, pairs sorted lexicographically and resampled as pairs). The
criterion is therefore a pure function of the data and does not depend on row order.

**`pattern_stats`.** After the two evaluations the gate regenerates the counted samples of the `plus`, `minus` and `null`
streams (the same samples K1-K7 saw; sample index 0 in a deterministic study). For every pattern criterion and each
stream it records the 5%, 50% and 95% quantiles of the statistic it computes, its thresholds and the number of finite
values (UNDEFINED samples are excluded). Parts of `all_of` and `any_of` are recorded separately, keyed by their position
path (`"0"`, `"1.0"`). The numbers go into the certificate and never change a verdict. They help you see how far the
statistic is from the threshold in each world.

## 6. Criteria: commands in any language (`tg-line/1`)

A criterion can be a program in any language. The gate sends a sample, the program returns an outcome. An example in
Node is in [`../examples/node_criterion/`](../examples/node_criterion/README.md).

```toml
[[criteria]]
id = "effect"
command = ["node", "criterion.js"]       # an argv list, never a shell string

[external]
uses = ["criterion.js", "tg_line.js"]    # copied into the program's working folder and hashed
```

**Process.**

* `command` is an argv list. `argv[0]` is resolved with the inherited `PATH`, then with `os.path.realpath`, and the
  result must be a readable file. A bare name is resolved with `PATH`; a relative name with a path separator is resolved
  against the manifest's folder (R-17). On Windows it must be an `.exe` or `.com`: a `.cmd` or `.bat` file is rejected
  with a hint to call the interpreter directly (for example `["node", "criteria.js"]`).
* One process per distinct argv, started before the leak guard is armed. It serves both evaluations and the K8 pass.
  State it carries between requests is exposed by the reproducibility check as `K6_NONREPRODUCIBLE` when it changes an
  outcome. A dead process is not restarted.
* **Working folder:** a fresh temporary folder holding copies of the `[external] uses` files and the `allow_paths`, with
  their relative layout. A `uses` or `allow_paths` file outside the manifest's folder is exit 4 (R-16).
* **Environment:** `PATH`, `HOME`, `USERPROFILE`, `APPDATA`, `LOCALAPPDATA`, `SYSTEMROOT`, `TEMP` and `TMP` are passed
  through, plus `LANG = C.UTF-8`, `TG_PROTOCOL = tg-line/1` and the names in `[external] env`. Nothing else.
* On POSIX the process starts in its own session and a kill reaches its process group. On Windows only the process
  itself is killed; programs it started may survive. Shutdown and kill never wait on a pipe or on a reader thread (a
  grandchild that inherited the pipes cannot hang the gate): `check` finishes and writes its certificate, and a working
  folder that cannot be deleted (a surviving grandchild may hold it) is a warning.
* The executable is resolved with `PATH`; its **realpath is validated and hashed** (the certificate records that hash),
  while the process is **started with the `PATH`-resolved path**, so a symlinked `python` of a virtual environment keeps
  its environment (R-28).
* Standard error goes to a temporary file. After the guard is disarmed, the last 20 lines of a failed process are printed
  to the terminal. Nothing from standard error enters the certificate.
* The program writes one line per reply and flushes it. Logs go to standard error.

**Messages** (one JSON object per line, UTF-8). `rid` is an integer that increases by one with every request.

| Request from the gate | Expected reply |
|---|---|
| `{"op": "hello", "tg": "tg-line/1", "rid": 0}` | `{"ok": true, "tg": "tg-line/1", "rid": 0}` within `startup_timeout_s` |
| `{"op": "criterion", "id": "C2", "rid": k, "types": {...}, "data": {...}}` | `{"rid": k, "outcome": "HOLDS"}` (or `"FAILS"`, `"UNDEFINED"`); with components, `{"rid": k, "outcome": {"name": "HOLDS", ...}}`; or `{"rid": k, "error": "text"}` |
| `{"op": "bye", "rid": k}` | none required; the process exits |

**Failures.**

| Event | Result |
|---|---|
| `{"rid": k, "error": ...}` | that one outcome is UNDEFINED (`ExternalError`); the process keeps serving. A reply with both `outcome` and `error` counts as an error (R-14) |
| a timeout (`request_timeout_s`), a line that is not JSON, a wrong or missing `rid`, or a reply with neither `outcome` nor `error` | the process is **killed**. The outcome is `ExternalTimeout` or `ExternalProtocolError`; every later request to that argv is UNDEFINED (`ExternalDied`); the study note `EXTERNAL_DIED` is added |
| the process dies (EOF, write error) while a reply is awaited | `ExternalDied`, like every later request (R-13) |
| `outcome` is not one of `HOLDS`, `FAILS`, `UNDEFINED` | the process is not killed (the `rid` matches, so nothing can shift); the value counts as an invalid return: `BAD_RETURN` and UNDEFINED (R-14) |
| a missing or unhashable executable, a `.cmd`/`.bat` on Windows, or a failed handshake | exit 4, no certificate |

A killed process cannot answer late, so replies can never shift. The UNDEFINED outcomes reach the verdict through K1.

**Read-key recording.** 0.3 calls each criterion once more on a recording dictionary to learn which keys it reads. For a
command criterion that is a real request, and the adapter serialises every key, so all keys count as read and
`K2_MINUS_UNREAD` is never raised for command criteria.

**Data codec (gate to program).** `data` is a JSON object of arrays as nested lists. `types` gives, for every key, its
dtype (`float`, `int`, `bool`, `str`) and shape, so empty arrays are unambiguous. Non-finite floats are sent as the
strings `"NaN"`, `"Infinity"` and `"-Infinity"`. Integers outside +-2^53 are an encoding error (that outcome is UNDEFINED),
because JavaScript and R would lose precision.

**What is guarded, hashed and disclosed.** The leak guard cannot see inside another process. The study note
`K6_EXTERNAL_UNGUARDED` lists the commands (`{"note": "K6_EXTERNAL_UNGUARDED", "commands": [[argv...], ...]}`, R-15); the
CLI table, the Action summary and the badge show it, and a non-claim states it. The certificate records the argv, the
SHA-256 of every `uses` file and of the resolved executable. Libraries the program loads (R packages, `node_modules`) are
not hashed. The gate isolates external programs against accidents, not against deliberate evasion.

**Put the analysis inside the criterion.** The gate can only test what the criterion computes. If a criterion compares a
precomputed accuracy with 0.7, no probe reaches the pipeline that produced it. If the criterion runs the pipeline
(selection, fitting, evaluation) on the data it is given, a circular selection or a leak makes it hold on noise, and K4
and K5 catch it. With `tg-line/1` the pipeline can stay in R, Julia or any other language.

## 7. Mutations

A mutation is an inline table `{ op = "...", ... }`, applied to a copy of the sample, never in place. A mutation that
references a missing key or does not fit the data raises an error, which the engine turns into UNDEFINED. Ops marked
with a dagger accept a `where` selection (same rules as in [section 5](#5-criteria-patterns)) that limits them to some rows.

| Op | Arguments | Effect | Models |
|---|---|---|---|
| `shuffle` | `column` or `columns` (exactly one of them) | permutes the first axis of the listed keys, **jointly**, relative to all others | association that is not there; labels unrelated to outcomes |
| `swap` | `a`, `b` | exchanges two arrays of the same shape | mixed-up columns |
| `scale` (dagger) | `column`, `factor` | multiplies by `factor` | unit errors |
| `offset` (dagger) | `column`, `value` | adds `value` | zero-point and baseline errors; a stray epsilon |
| `constant` (dagger) | `column`, `value` or `stat` (`mean`, `median`, `first`) | replaces the values by one value; `mean` and `median` of an `int` column give a float64 column (R-29) | no variation; an effect set to zero |
| `noise` (dagger) | `column`, `sd` or `rel_sd` (relative to the column's standard deviation) | adds N(0, sd) | measurement noise; robustness |
| `subsample` | `fraction` | keeps `round(fraction * n)` random rows, without replacement | small-sample fragility |
| `null_effect` | `outcome`, `group`, `reference` | replaces the outcomes of all non-reference rows by values drawn with replacement from the reference rows | "the claimed group difference is absent" |
| `reverse` | `column` | reverses the first axis | a direction test that cannot tell a path from its mirror image |
| `sign_flip` (dagger) | `column` | multiplies by -1 | sign conventions; direction claims |
| `permute_rows` | none | permutes all row-aligned keys jointly (associations kept) | dependence on row order |

**Rules.**

* **dtype.** `scale` with an integer factor, `offset` with an integer value and `sign_flip` keep an `int` column `int`;
  otherwise an `int` column becomes float64. Every other op keeps the dtype.
* **No-op parameters are validation errors:** `factor = 1`, `offset` with `value = 0`, `fraction = 1`, `sd = 0`,
  `rel_sd = 0`.
* `constant` with `stat`, and `noise` with `rel_sd`, each combined with `where`, are validation errors (R-4): whether the
  statistic comes from all rows or the selected rows is undefined.
* `subsample` keeps rows in table order (R-12).
* **Random draws of declared mutations.** In a stochastic study a mutation draws from the generator of the stream and
  sample it runs in. In a deterministic study it draws from a generator seeded by the base seed and `<kind>:<id>` (for
  example `control:negated`, `world:minus`), identical at every sample index, so the 0.3 determinism check stays
  meaningful (R-11). K8's own transformation draws are a different matter ([section 9](#9-invariances-and-k8)).

Whether a mutation should break the claim or leave it intact follows from where it is used: in `minus` (the criterion
should fail), in a control (the theory is broken; the criterion must not hold), in a premise, or in an invariance (the
outcome must not change). The certificate lists the ops of every declaration.

## 8. Controls and premises

* A **control** breaks the theory on purpose. The criteria it lists must not hold under it (K4). Every criterion needs a
  control that can make it fail, or a written `control_waiver` (which caps the verdict at WEAK).
* A **premise** perturbs one assumption. With `role = "tested"` the criteria it lists must hold significantly less often
  under it (K3); `magnitude = [value, scale]` must be resolvable in float64.
* Both take `mutations`, or a `python` reference. A control may also take `world`.
* Row operations in a control or premise need row-aligned keys in the `plus` world.

## 9. Invariances and K8

```toml
[data]
rows_exchangeable = true       # adds the built-in invariance builtin:permute_rows for every criterion

[[invariances]]
id = "units_mm"
criteria = ["C1"]
mutations = [ { op = "scale", column = "length", factor = 1000 } ]
reason = "C1 is a ratio, so the unit of length must not matter"
```

An invariance declares a transformation that, by the study's own logic, must not change any criterion outcome. `reason`
is required text. With `rows_exchangeable = true` the built-in invariance `builtin:permute_rows` (R-20) is added for every
criterion and cannot be removed; a user invariance with that id is a duplicate-id error. The default is `false`, because
time series and ordered grids are not exchangeable.

K8 runs as a separate pass after the two evaluations, under the armed guard; it never feeds anything back into K1-K7.
For each invariance, each criterion component and each of the worlds `plus` and `minus`:

* **Stochastic study:** the counted samples of that world in the current mode are regenerated with the engine's seeds;
  each is evaluated before and after one transformation drawn from the gate's stream `k8:<invariance>:<world>`, with the
  sample index as the third seed element (R-18).
* **Deterministic study:** the one sample is evaluated once untransformed and after `budget.samples` transformations
  (`quick_samples` in quick mode).
* Pairs with an UNDEFINED side are counted apart.

K8 has its own Bonferroni family: `m_K8` is 2 times the number of (invariance, component) pairs, and each test uses the
one-sided Wilson lower bound at level `alpha_family / m_K8`. The study-wide family-wise error rate is therefore at most
`2 * alpha_family`; the certificate states this when K8 ran.

| Flag | When |
|---|---|
| `K8_NOT_INVARIANT` | mandatory: for either world, the Wilson lower bound of the change rate exceeds `targets.size` |
| `K8_SOME_CHANGES` | info: a (invariance, world) test has at least one change and no `K8_NOT_INVARIANT` (R-21) |
| `K8_INCONCLUSIVE` | capping: for either world, more than 50% of the pairs have an UNDEFINED side |

Every invariance needs row-aligned keys on both `plus` and `minus` (R-23). An unknown or repeated criterion id, or a
duplicate invariance id, is a `StudyError`: a certificate and exit 3 (R-19).

## 10. `suggest`: a starter manifest

```text
truth-gate suggest DATA.csv [--outcome COL] [--group COL --reference VALUE] [--effect COL ...]
                            [--exchangeable] [--out truthgate.toml]
```

`DATA.csv` must be a realistic synthetic or pilot dataset, **not the real study data**. `suggest` prints this warning
and writes it as a comment at the top of the manifest, because a plus world built from the real data makes the plus and
minus checks circular. It writes:

* `[data]` with the inferred types and the given roles (an integer group column is declared `int`);
* `plus` as a bootstrap of DATA, with `provenance = "TODO"`, which is a validation error until you replace it;
* a `minus` world: `null_effect` when `--group`, `--reference` and `--outcome` are given. Otherwise **one joint
  `shuffle` with `columns = [...]`** of all `--effect` columns (R-22): a joint shuffle breaks the effect columns'
  relation to the rest and keeps their relation to each other, so one change is made at a time. The other candidates are
  comments;
* controls: `shuffle` of the group (else the outcome) column, and `sign_flip` of the effect columns. Controls are written
  with `criteria = []` and a TODO comment;
* `rows_exchangeable = true` only with `--exchangeable`;
* **no active criterion**: every pattern appears as a commented template with the column names filled in.

Every generated declaration carries `origin = "suggested"`, which caps every component at WEAK
(`SUGGESTED_UNREVIEWED`) and fails the GitHub Action. The manifest runs only after `provenance` is set (exit 4 until
then) and a criterion is added (exit 3 with the zero-criteria error until then).

`suggest` reads CSV only. A missing group, reference or outcome in an incomplete combination, no minus candidate, or an
existing `--out` file is exit 4; it never overwrites.

## 11. Errors and exit codes

| Where the problem is found | Result |
|---|---|
| the manifest text and the environment: TOML or JSON syntax, an unknown key, a wrong type, a path, a data file, an executable, a handshake | exit 4, no certificate |
| building or validating the `Study`: 0.3's own validation, a `python` reference that does not load, a K8 declaration problem | a certificate with the verdict UNDEFINED, exit 3 |
| the gate itself | exit 0, 1, 2, 6 for FALSIFIABLE, WEAK, NOT_FALSIFIABLE, UNTESTED; exit 3 for UNDEFINED |
| `verify` on a certificate made by another tool version | exit 7; the study is not re-run |

The codes are listed with the verdicts in [`GATE.md`](GATE.md#verdicts-and-exit-codes).

**Not in 0.4 (moved to 0.5):** worlds, controls and premises produced by external programs; the mutations `copy`,
`stale` and `relabel`; `files = glob` worlds; YAML and Parquet input.
