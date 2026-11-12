# Blind review 1 of the spec 0.6 draft (fresh agent, 2026-11-12)

The reviewer read the draft v1 and the 0.3 code (`study.py`, `checks.py`, `guard.py`, `certificate.py`, `cli.py`,
`minus.py`, `probes.py`, `sampling.py`). It did not run anything and did not see the designer's reasoning. Its
findings, condensed; the designer's responses are in `spec-0.6-REVISIONS.md`.

1. **Critical (§11, §5).** `study_verdict` raises the verdict to NOT_FALSIFIABLE for any study-level flag
   (`checks.py:90-95`). Study-level "info" flags (`K6_EXTERNAL_UNGUARDED`, `EXTERNAL_DIED`) would fail every
   external-command study, and the "capping" `SUGGESTED_UNREVIEWED` would give NOT_FALSIFIABLE, not WEAK.
2. **Critical (§5).** Replies carry no request id. After a timeout the process stays alive and a late reply is read as
   the answer to the next request; every later outcome shifts by one. Stray stdout lines desync the stream too.
3. **Major (§5).** The guard is armed before `load_study` and stays armed through both evaluations
   (`certificate.py:272-289`); `subprocess.Popen` is blocked while armed (`guard.py:23-30`). Compiling, copying and
   spawning must move outside the armed block; the draft does not say so. File reads and `python` references need to
   happen before arming or be allow-listed. Hashing of `python` reference sources is unspecified.
4. **Major (§9, §11, §13).** Tests assert `kapi_version == "0.3.0"` and `spec_version == "0.5"`, and `BODY_FIELDS`
   requires `kapi_version`. Schema 2 breaks them; "import paths only" is not enough.
5. **Major (§7).** K8 and the Bonferroni family (`count_comparisons`, `checks.py:355-366`): a shared family changes
   K2–K5 bounds, a separate one leaves the overall alpha uncontrolled; the draft says both. Deterministic "any change"
   is too strict: a seeded bootstrap on permuted rows can flip at a float edge.
6. **Major (§8).** `suggest` adds `relabel` for every `str` column, which breaks any criterion that selects by name.
   `SUGGESTED_UNREVIEWED` is cleared by deleting a key, and the default CI `fail-on` lets WEAK pass.
7. **Major (§14 A3).** Unreachable: command criteria always carry `K6_EXTERNAL_UNGUARDED`; serialising the data reads
   every key, so `K2_MINUS_UNREAD` can differ; JS and numpy sums differ in the last bit; JSON `1.0` becomes `1`.
8. **Major (§14 A1).** No recorded 0.3 baseline. The `kapi` shim imported under the armed guard is outside the
   allow-list in a source checkout (`guard.py:62-72`), which would raise a `K6_LEAK_ATTEMPT` 0.3 never had.
9. **Major (§14 A2).** Vacuous: the rewriter may use `python` references everywhere.
10. **Major (§14 Phase B).** "Not FALSIFIABLE or WEAK" counts UNDEFINED, UNTESTED and loader errors as detections; the
    firing flag need not match the class; classes chosen for the mechanism are circular; B-4 is the existing
    identical-minus check; n = 8 is thin; case authorship is not independent of the designer.
11. **Major (§3.3).** File sampling under-specified: n, row alignment in JSON/NPZ, CSV dialect (`TRUE`, `NA`, BOM,
    delimiter, decimal comma), `int` with missing cells, OS-dependent sort order for `files`.
12. **Major (§3.3, §6).** Random mutations in deterministic studies give different draws at indices 0, 1, 2 and raise
    `NONDETERMINISTIC` (`checks.py:700-711`).
13. **Major (§3.3).** Pairing of derived minus worlds is undocumented; a no-op mutation can change dtype and hide
    `K2_MINUS_IDENTICAL`; `stale` rng and cycles unspecified.
14. **Major (§4).** Probes turn int columns into floats, so `==` patterns become UNDEFINED under probes;
    `largest_true` with `==` over float grids contradicts the float-equality ban; a typo inside `any_of` is hidden;
    `pattern_stats` needs a side channel and a rule for which calls count.
15. **Major (§5 codec).** Seeds above 2⁵³ are lossy in JS and R; `["NaN"]` is ambiguous; empty lists and large ints
    have no rule.
16. **Major (§5 environment).** The restricted `PATH` is undefined; redirecting `HOME` breaks R and Julia libraries;
    packages are not hashed; Windows timeouts need threads; grandchildren survive; flushing is not stated; `.cmd`
    shims need `cmd.exe`.
17. **Minor (§3.3, §12).** `provenance` is a free-text attestation; a bootstrap of the real data makes plus and minus
    hold and fail by construction. `badge` reads quick certificates and does not check `body_sha256`.
18. **Minor (§5).** Process state carries across the two evaluations; only the reproducibility check can catch it.
19. **Minor (§14.1).** The A4 pair uses lambdas, which a manifest cannot hold.

**Scope (reviewer's advice):** defer `stale`, `copy`, `relabel`, `files`, the Action, pre-commit, `badge`, `explain`,
YAML/Parquet, the package rename, `ci_excludes` bootstrap and `all_of`/`any_of`; keep a thin core.

**Sound as written (reviewer):** §2.4, §3 parsing rules, §5 argv/no-restart/stderr policy, the `largest_true` UNDEFINED
rule and the float-equality ban (apart from 14), §6 copy-on-write, §8 no active criterion, §12, §13, §14.1 numerically.
