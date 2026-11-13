# Changelog

Each release implements one frozen specification (`docs/SPEC.md` for 0.1 to 0.3, `docs/design/spec-0.6.md` for 0.4, `docs/design/spec-0.7.md` for 0.5). The
package version is `tool_version` in the certificate (`kapi_version` up to 0.3); the spec version is `spec_version`.

## 0.5.0 (spec 0.7, 2026-11-13)

Implements `docs/design/spec-0.7.md` (frozen, `FREEZE_SPEC_0.7.json`). Post-freeze decisions of the implementation are in
`docs/design/spec-0.7-REVISIONS-post-freeze.md` (R-1, R-2).

**Changed**

- **K1 separates abstention from failure.** A criterion's own UNDEFINED outcome (soft: `None`, also as a whole return or a
  dict value; a pattern that is UNDEFINED by its own rules; a command's `"UNDEFINED"`) counts as no claim. Every other
  UNDEFINED outcome is hard (an exception including a pattern's missing key and the leak guard's `PermissionError`, a failed
  or invalid world generation, a wrong return type including `NaN`, a missing declared component, every command failure).
  `K1_UNDEFINED` (verdict UNDEFINED, as before) now fires for a hard UNDEFINED on `plus`, `minus` or `null`, or when the
  criterion abstains on more than half of the `plus` samples (`2 * abstentions > n`; 100 vs 101 of 200, 10 vs 11 in quick
  mode). Otherwise the information flag `K1_ABSTAINED:<stream>` is recorded for every K1 stream with an abstention, and the
  capping flag `K1_ABSTAINED_MAJORITY:<stream>` (verdict at most WEAK, never suppressed) when `world:minus` or `world:null`
  has more than half abstentions. The same rules apply in deterministic mode (an abstention on `minus` or `null` is a rate
  of 1) and in quick mode.
- **Every other statistic is unchanged.** `None` counts as not-HOLDS exactly as before, so K2 to K5, the premise map,
  `pattern_stats` and the suppression rules give the 0.4.1 numbers. K8 keeps its rule; its limitation (abstentions on the
  "before" side can hide changes on up to half of the pairs) is documented in `known_limitations`.
- **Certificate.** `spec_version` `"0.7"`, `tool_version` `"0.5.0"`. `counts[stream]` gains `hard_undefined`; `errors`
  gains the names `BAD_RETURN` and `MISSING_COMPONENT`, so the error counts of a stream add up to its `hard_undefined`. For the random probes (noise, shuffle) of a deterministic study, whose three draws are combined into one outcome, `hard_undefined` is 1 when the combined outcome is UNDEFINED and one of its UNDEFINED draws is hard, and `errors` then has one entry, the cause of the first hard draw (post-freeze R-3); otherwise neither is recorded.
  Validation checks `holds + undefined <= n` and `hard_undefined <= undefined`. `known_limitations` has two more sentences.
  `verify` on a 0.4.x certificate exits 7.
- `explain` has entries for `K1_ABSTAINED`, `K1_ABSTAINED_MAJORITY` and both causes of `K1_UNDEFINED`.
- Names: the `StudyError` text is `STUDY is not a truth_gate.Study` (it is recorded in `load_error`), and the leak guard
  message is `truth_gate leak guard blocked <event>`. The default certificate name stays `STUDY.kapi.json`.

**User-visible effect.** A component that 0.4.1 made UNDEFINED only because its criterion returned `None` is now judged by
its other flags and can be FALSIFIABLE, WEAK or NOT_FALSIFIABLE. A CI job that failed on such an UNDEFINED (exit 3) may
now pass, or fail on a mandatory flag that 0.4.1 had already computed. A 0.4.1 detection or clean pass cannot change.
One older evaluation case, `evaluation/cases/E2/E2-07_faulty.py`, moves from UNDEFINED to WEAK: its criterion returns
`None` instead of `False` when no peak is detected, so it abstains on all `minus` samples and
`K1_ABSTAINED_MAJORITY:world:minus` caps it at WEAK (R-2; the v0.2 evaluation counted the UNDEFINED as a detection).

**Guidance.** Return `None` when the analysis has nothing to claim (for example an empty selection); let a genuine error
raise. A criterion that catches its own exceptions and returns `None` turns a failure into an abstention. A command
program must answer an uncaught exception with `error`, not `"UNDEFINED"`.

**Not in 0.5** (moved to 0.6): command worlds and transforms, the mutations `copy`, `stale` and `relabel`, `files = glob`
worlds, YAML and Parquet input.

## 0.4.1 (spec 0.6, 2026-11-13)

The command's help and error messages use the name Truth_Gate / `truth-gate` instead of Kapı / `kapi`. No change to
verdicts, flags, counts or the spec. Certificates now carry `tool_version` `0.4.1`, so `verify` on a 0.4.0 certificate
exits 7 and names tag `v0.4.0`, as for any other version (R-2).

## Evaluation, Phase B (2026-11-13)

No change to the package or the spec. The pre-registered external evaluation of 0.4.0 on errors documented in the
literature ran on the frozen cases (`evaluation/phase_b/`): one in-scope class of four held (B-6, inflated-size decision
rules, 11/12 detected and 11/12 clean); B-1, B-2 and B-3 failed. Report: `evaluation/phase_b/REPORT.md`; summary in
`docs/EVALUATION.md`.

## 0.4.0 (spec 0.6, 2026-11-12)

Post-freeze decisions of the implementation are in `docs/design/spec-0.6-REVISIONS-post-freeze.md` (R-1 to R-34).

**Changed**

- **The package is `truth_gate`** and the command is `truth-gate` (also `python -m truth_gate`). The package `kapi` and
  `python -m kapi` remain as a deprecated alias that re-exports the same objects; no warning is emitted, and it stays at
  least until 1.0. Python study files run unchanged and give the same verdicts, flags and counts as 0.3.
- **Certificate schema 2.** `kapi_version` is replaced by `tool` and `tool_version`; `spec_version` is `"0.6"`. New
  fields: `input_kind`, `manifest`, `mutations`, `k8`, `m_k8`, `k8_statement`, `pattern_stats`, `suggested_unreviewed`,
  `study_notes`. `non_claims` has six entries and `known_limitations` five. The hash rule is unchanged.
- **Exit code 7.** `verify` on a certificate made by another tool version (including every 0.3 certificate) exits with 7
  and names the git tag to use; it never re-runs the study. The certificate's own `body_sha256` is checked first (exit 5).
- The leak guard's allow-list holds both package folders. The table output ends with the study notes.

**Added**

- **Manifest studies** (`truthgate.toml` or `.json`): file worlds (CSV, JSON, NPZ) with required `provenance`, derived
  worlds, ten criterion patterns (`threshold`, `difference`, `ratio_band`, `within`, `rate`, `ci_excludes`,
  `largest_true`, `monotone`, `all_of`, `any_of`), eleven mutations, controls, premises. Errors in the manifest text exit
  with 4 and write no certificate; errors in the compiled study give a certificate and exit 3. `docs/MANIFEST.md` is the
  reference.
- **Criteria in any language** (`command = [...]`, protocol `tg-line/1`), with the study notes `K6_EXTERNAL_UNGUARDED` and
  `EXTERNAL_DIED`. `examples/node_criterion/` is a Node example.
- **K8, invariance**, a separate pass with its own Bonferroni family (study-wide family-wise error rate at most
  `2 · alpha_family`), with the flags `K8_NOT_INVARIANT`, `K8_INCONCLUSIVE` and `K8_SOME_CHANGES` and the built-in
  row-permutation check for `rows_exchangeable = true`.
- `pattern_stats`: quantiles of every pattern's statistic in the plus, minus and null streams, recorded in the
  certificate. It never changes a verdict.
- **`suggest`** (a starter manifest from one dataset; the minus fallback with several `--effect` columns is one joint
  `shuffle`, R-22), `init` (with `--ci`), `freeze write` and `freeze verify` in the package, `badge`, `explain`.
- The flag `SUGGESTED_UNREVIEWED` (capping, on every component) while a declaration carries `origin = "suggested"`.
- **GitHub Action** (`action.yml`, composite; its two actions are pinned by commit SHA) and **pre-commit hooks**
  (`.pre-commit-hooks.yaml`: `truth-gate-freeze`, `truth-gate-check`). The Action logic is `truth_gate/ci.py`, unit-tested
  with a fake environment; the Action itself has not been run on GitHub.

**Deferred to 0.5**

- Worlds, controls and premises produced by external programs (command worlds and transforms).
- The mutations `copy`, `stale` and `relabel`.
- `files = glob` worlds.
- YAML and Parquet input.

**Evidence.** Phase A of the 0.4 evaluation (spec 0.6, section 14): all four pre-registered criteria held (A1 159 of 159
older studies unchanged; A2 7 of 7 manifests equal to the hand-written studies; A3 6 of 6 Node criteria equal to Python;
A4 K8 caught a planted order dependence and changed its verdict). Details in `docs/EVALUATION.md`.
Phase B, an external test set built from documented errors in published research, runs on the frozen 0.4.0 and is
reported when it is done.

## Repository, first public release (2026-11-12)

No change to the `kapi` package or the spec.

- **New name: Truth_Gate** (formerly Kapı). The distribution name is `truth-gate`; in 0.3 the package is still
  imported as `kapi` and certificates record `kapi_version`, so the frozen examples and their certificates stay valid.
  Older records in `docs/` keep the old name and say so at the top.
- The README is now an overview of the whole kit: the methods protocol, the templates and tools, and the gate. The
  gate's full reference (study API, checks, verdicts, leak guard, certificate, flag reference, limitations) moved to
  `docs/GATE.md`. The test that every flag is documented now reads `docs/GATE.md`.
- Two pre-registered hardware case studies added: `examples/ghz_heron/` and `examples/ghz_heron_run2/`, with raw
  counts, calibration snapshots, transpiled circuits, freeze manifests, certificates, blind audits and reports.
- `.gitattributes` turns off line-ending conversion, because freeze manifests hash raw bytes. `.gitignore` ignores
  `certs/` only at the repository root, so that the certificates listed in the example freeze manifests are kept.
- A 0.4 roadmap in the README (planned, not built).

## 0.3.0 (spec 0.5, 2026-11-11)

- **New verdict `UNTESTED`.** When the `minus` world is identical to the `plus` world (exact equality of all data),
  Kapı cannot test whether the criterion can fail. The flag is `K2_MINUS_IDENTICAL`; the exit code of `check` is 6.
  UNTESTED does not pass the gate, and it does not say the criterion is unfalsifiable.
- When the `minus` world is identical, `K2_FAILS_UNREACHABLE`, `K2_NO_SEPARATION` and `K2_HIGH_SIZE` are not raised
  for that criterion (they carry no information); they are listed in `suppressed_minus`. The K5 probes still run, so a
  vacuous criterion is still NOT_FALSIFIABLE.
- New informational flag `K2_MINUS_UNREAD`: the `minus` world changed only data that the criterion does not read.
  No effect on the verdict.
- New certificate fields `minus_check` (always present) and `suppressed_minus` (only when something was suppressed).
- Why: in a retrospective pilot, most flagged clean criteria were flagged because of how the test worlds were built,
  not because of the criteria. An inert `minus` world was the one pattern that can be detected mechanically.
- Known cost: a regression case whose declared change was not implemented is now UNTESTED instead of
  NOT_FALSIFIABLE (see `docs/EVALUATION.md`, R1).

## 0.2.0 (spec 0.4, 2026-11-05)

- **The declared α is mandatory.** `K2_HIGH_SIZE` and `HIGH_RATE:<stream>` changed from capping (WEAK) to mandatory
  (NOT_FALSIFIABLE). `K2_LOW_POWER` stays capping. `Targets.size` is now documented as the declared α.
- **Cascade suppression.** If a criterion never holds in `plus` (`K2_HOLDS_UNREACHABLE`), the flags that depend on
  a significant comparison with `plus` are no longer raised for it. They are listed in `suppressed_by` and
  `suppressed`. The verdict cannot change.
- New evaluation set E4 (independent) and a reproducibility criterion P4' that replaces the badly defined P4.
- Why: v0 gave only WEAK to inflated false-positive rates, and misleading downstream flags cascaded when a criterion
  could never hold.

## 0.1.0 (spec 0.3, 2026-11-05)

- First frozen version. Checks K1 (definedness), K2 (reachability, separation, resolution), K3 (premise map),
  K4 (negative controls), K5 (vacuity probes), K6 (leak guard, reproducibility) and K7 (coverage).
- Verdicts FALSIFIABLE, WEAK, NOT_FALSIFIABLE, UNDEFINED. Hash-addressed JSON certificate. Command line
  `check` and `verify`. Deterministic and stochastic modes.
- Evaluation sets E1 (self-authored), E2 (independent) and E3 (reconstructed from published cases).
