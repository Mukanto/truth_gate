# Changelog

Each release implements one frozen specification (see `docs/SPEC.md`). The package version is `kapi_version` in the
certificate; the spec version is `spec_version`.

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
