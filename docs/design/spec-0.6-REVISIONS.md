# Revisions to the spec 0.6 draft

Each revision gives the finding it answers (see `spec-0.6-REVIEW1.md`), the change and the reason. Decisions by Claude
under the author's delegation. The designer re-checked findings 1, 3, 5 and 12 in the code before accepting them
(`checks.py:90-95`, `certificate.py:272-289`, `guard.py:20-35`, `checks.py:355-366`, `checks.py:695-715`).

## Draft v1 → v2 (2026-11-12)

| # | Finding | Change | Reason |
|---|---|---|---|
| 1 | Study-level info flags escalate the verdict | New certificate list `study_notes` (never read by any verdict rule) for `K6_EXTERNAL_UNGUARDED` and `EXTERNAL_DIED`. `SUGGESTED_UNREVIEWED` becomes a per-component capping flag on every component. "Engine unchanged" restated precisely (§0, §1.1). | Verified in code. The claim "engine unchanged" was too strong; the honest statement lists the exact engine changes and lets A1 prove that none of them alters a 0.3 study. |
| 2 | No request id; desync after timeout | Every request carries `rid`; a reply must echo it. A timeout, a wrong `rid`, a non-JSON line or a missing key kills the process and is handled as its death (§5). Logs go to stderr. | A killed process cannot answer late, so a shift is impossible. Strictness is cheaper than resynchronisation. |
| 3 | Guard armed before load; spawn blocked | Orchestration fixed (§1.2): parse, read data files, copy `uses`, hash, spawn and handshake **before** arming; evaluate twice under the guard; shut processes down after leaving it. `python` reference files are loaded under the guard, allow-listed and hashed. Kill uses `Popen.kill` / `os.killpg` (no new process). | Verified in code. |
| 4 | Schema 2 breaks tests | §13 lists the permitted test edits (imports; the version, spec and schema fields; exit code tables). A1 compares bodies with those fields removed. | The tests encode 0.3's schema; changing the schema requires changing exactly those assertions and no others. |
| 5 | K8 and Bonferroni; deterministic strictness | K8 comparisons join the family the way controls do (`m` grows with declared invariances). In deterministic mode K8 draws `budget.samples` transformations of the one sample and uses the stochastic rule. `ci_excludes` bootstraps sorted values, so it is invariant under row order (§4, §7). | Joining the family keeps the family-wise alpha controlled, exactly as declaring a control does in 0.3; a 0.3 study declares no invariance, so A1 is unaffected. |
| 6 | `suggest` relabel; CI lets WEAK pass | `suggest` writes no `relabel` (and `relabel` is deferred). The Action fails whenever `SUGGESTED_UNREVIEWED` is present, whatever `fail-on` says (§8, §10). | The friction must survive CI. |
| 7 | A3 unreachable | A3 compares verdicts and non-info flags (excluding `K2_MINUS_UNREAD`), and counts except samples whose Python-side statistic lies within a pre-registered distance of the threshold; those are counted and reported (§14). Commands return outcomes only in 0.4, so no data dtype comes back. | Defines equality in a way that is achievable and still sharp. |
| 8 | No A1 baseline; shim under the guard | Before step (a), the 0.3.0 results are recorded from tag `v0.3.0` in the implementation environment (`baseline_v030/`). The guard allow-list includes both package folders (§1.1, §14). | A comparison needs a fixed reference recorded before the change. |
| 9 | A2 vacuous | Pre-registered coverage: the criteria of example 03 (both twins) and C3 of `convergence_criteria` must be patterns; every control and premise of examples 01–03 must be mutations (§14). | Written before any manifest exists, so it cannot be tuned. |
| 10 | Phase B can pass for the wrong reason | Detection requires NOT_FALSIFIABLE **and** at least one flag from the class's pre-registered expected set. UNDEFINED, UNTESTED and load errors count as misses. At least 10 pairs per class. B-4 is reported apart as a known-mechanism class. Sources are verified before the Phase B freeze. The circularity of choosing in-scope classes is stated, and out-of-scope classes stay in the set (§14). | Conservative counting; a faulty twin cannot "detect itself". |
| 11 | File sampling | Rules fixed: n = table length; JSON/NPZ row resampling needs `[data] rows`; CSV dialect, missing values and `int` rules specified; `files` deferred (§3.3). | Removes every open question the reviewer listed. |
| 12 | Random mutations in deterministic mode | In a deterministic study every mutation draws from a generator seeded by the base seed and the declaration id, the same at every sample index (§6). | Verified in code: only the gate's own probes are exempt from `NONDETERMINISTIC`. |
| 13 | Derive pairing, dtype, stale | Pairing documented (§3.3); dtype rules for mutations and validation errors for no-op parameters (§6); `stale` deferred. | A no-op mutation should be rejected loudly, not detected late. |
| 14 | Probes and patterns | `==` only on `count` and on `largest_true`, whose grid is a literal list in the manifest (positional, as in the GHZ lesson). A missing key raises, so the whole criterion is UNDEFINED (no hiding inside `any_of`). Statistics flatten n-D arrays. `pattern_stats` defined: evaluation 1, counted samples only, UNDEFINED excluded, n recorded (§4). | Removes the type dependence on probes. |
| 15 | Codec | `generate`/`transform` deferred to 0.5 (no seeds sent). Requests carry a `types` map; int values beyond ±2⁵³ are an encoding error (§5). | One-way data flow removes most codec ambiguity. |
| 16 | Environment | Pass-through list defined (PATH and the user's home and app-data variables kept, so R and Julia libraries work); working folder stays temporary; packages are not hashed (stated as a limit); reader thread for timeouts; on Windows `argv[0]` must resolve to an executable, not a `.cmd`/`.bat`; POSIX process groups; flushing required (§5). | Practical for G1 while keeping the accident defence of the temporary folder. |
| 17 | Provenance; badge | New non-claim on provenance; `badge` refuses quick certificates and checks `body_sha256` (§9, §11). | A bootstrap of the real data makes the plus/minus checks circular, and the certificate must say so. |
| 18 | State across evaluations | Stated as deliberate: one process serves both evaluations, so carried state shows up as `K6_NONREPRODUCIBLE` (§5). | |
| 19 | A4 lambdas | The A4 pair is written as patterns (`threshold` with `stat = "first"` versus `stat = "mean"`) (§14.1). | |
| S | Scope | Deferred to 0.5: command worlds and transforms, `copy`, `stale`, `relabel`, `files`, YAML, Parquet. Kept: the rename (the author asked for it), the Action, pre-commit, `badge`, `explain`, `ci_excludes`, `all_of`/`any_of` (each now specified). Release 0.4.0 after Phase A; Phase B runs on the frozen 0.4.0 and is reported when done. | Keeps 0.4 shippable without dropping what the author asked for. |

## Draft v2 → v3 (2026-11-12)

Answers `spec-0.6-REVIEW2.md`. The designer re-checked findings 1 and 2 in the code (`certificate.py:22-27`,
`study.py:261`, `tests/test_package.py:12-14`, `checks.py:377-711`) and simulated the new A4 pair (faulty: holds
0.896 in plus, changes under row permutation in 0.168 of samples, holds 0.0007 in minus; fixed: holds 0.994).

| # | Finding | Change | Reason |
|---|---|---|---|
| 1 | A1 vs changed body text | A1's strip list fixed now: version and schema fields, `non_claims`, `known_limitations` and every schema-2 field. Existing error messages stay byte-identical. | Fixed before any result, so it cannot be tuned. |
| 2 | Engine change list incomplete | §1.1 completed (flag tables, `BODY_FIELDS`, envelope validation, table output, exit 7). `pattern_stats` and K8 become **separate passes after the two evaluations**, so the K1–K7 machinery and the run-1/run-2 comparison are untouched. The no-`subprocess` rule is kept for every module except `external`, with a test. | The root cause of findings 2–4 was fitting new streams into the engine. A separate pass removes it. |
| 3, 4 | K8 stream model, rate, family | K8 is a post-engine pass with its **own Bonferroni family** (2 comparisons per invariance and component: plus and minus tested separately). The study-wide family-wise error is then at most `2 · alpha_family`, which is stated. K8 draws are the gate's own and never enter the determinism check. The K1–K7 `m` is unchanged, so `rows_exchangeable` cannot change A2. | Honest and simple; a shared family would require engine changes. |
| 5 | Pattern tolerances | Every criterion kind may carry `tolerances`. A2 requires the same tolerance declarations as the originals. | |
| 6 | File sampling, key table, exit boundary | Deterministic studies require `resample = "none"`. §3.2 lists every key of every table. Boundary: anything detectable from the manifest and the environment before user code runs → exit 4, no certificate; errors while loading `python` references → certificate, UNDEFINED, exit 3 (as 0.3). | |
| 7 | Process failures, Windows, stderr | Missing, unhashable or non-executable `argv[0]`, and a failed handshake → exit 4 before arming. The stderr tail is printed after the guard is disarmed. Cleanup failures are warnings. The stderr length is no longer recorded. Exit 7 on any version difference is kept and documented (the version is part of the hashed body, so a patch release cannot reproduce the hash). | |
| 8 | Unguarded commands, honesty | The CLI table, the Action summary and the badge show the note. The badge reads "FALSIFIABLE (unguarded)" in a different colour. A third new non-claim says the guard does not cover external programs. | Disclosure where people look, without changing the verdict semantics. |
| 9 | A3 | No exemption: verdict, flags (apart from `K2_MINUS_UNREAD`) and per-stream counts must be identical. If `node` is missing, A3 is a failure, not a skip. | Sharp and measurable. |
| 10 | Phase B | Thresholds on the one-sided 95% Wilson lower bound: ≥ 0.6 for detection and clean pass, n ≥ 10 per class (9/10 passes, 8/10 fails). Expected flags are named per class, with specific streams, no wildcards. Comparators reported: the 0.3.0 tool and a "flag everything" baseline. Authorship limits stated; human reviewer sought. | |
| 11 | Pattern semantics | `largest_true` is UNDEFINED if either side has no qualifying value, and on any non-finite `y`. `equals` only on `str` and `bool` columns. `ci_excludes`: numpy's default (linear) percentile, `B = 2000`, `numpy.random.default_rng(seed)`; differences only of means; `paired = true` resamples sorted pairs. Missing keys are checked before any part is evaluated. | |
| 12 | A4 | New planted pair (mean of the first 10 rows versus mean of all rows; plus N(1.4, 1), minus N(0, 1)). Pre-registered: faulty NOT_FALSIFIABLE with `K8_NOT_INVARIANT` as its only mandatory flag; fixed FALSIFIABLE with no K8 flag. The manifest is complete. | Now K8 must change a verdict, and a false positive is checked. |
| 13 | Baseline mode | Full mode for every study. | |
| 14 | `suggest` on real data | `suggest` prints a warning that DATA must not be the real study data, writes it as a comment, and leaves `provenance = "TODO"`. | |
| 15 | TOML values | Datetimes anywhere and non-finite numbers in arguments are validation errors. | |

## Draft v3 → v3.1, frozen (2026-11-12)

Answers `spec-0.6-REVIEW3.md`. The designer confirmed B-7 in the code (`tests/toy_studies/toy_nonreproducible.py:8`
uses `np.random.random`; three leak toys exist).

| # | Change |
|---|---|
| B-7 (blocking) | A1 baseline rules fixed: the study list is every file under the three folders that assigns a module-level `STUDY`, written with SHA-256 to `baseline_v030/STUDIES.json` before step (a); the 0.3.0 package is exported from the tag and the studies run from their repository paths; for a study whose baseline carries `K6_NONREPRODUCIBLE`, A1 compares verdict and flag sets only; `describe_study` gains no keys for Python studies. |
| B-1 | K8 flags and `SUGGESTED_UNREVIEWED` are added after the 0.3 suppression rules and are never suppressed. |
| B-2 | Errors while building or validating the `Study` (including 0.3's own validation) give a certificate with exit 3; manifest-text and environment errors give exit 4. `suggest` output: exit 4 until `provenance` is set, then the zero-criteria `StudyError` (exit 3). |
| B-3 | `pattern_stats` uses `stream_rng`/`make_sample`, the mode's `sample_count`, numpy's linear quantiles stored without rounding, parts keyed by position path. |
| B-4 | K8 uses the mode's sample counts. |
| B-5 | A third guard log after the post-engine passes is appended to `leak_log`. |
| B-6 | Read-key recording sends a real request to command criteria; all keys count as read; `K2_MINUS_UNREAD` never applies to them. |
| B-10 | `badge` exits 5 on a hash mismatch. |
| B-11 | Two new `known_limitations` entries specified (library hashing; Windows grandchildren). |
| B-8, B-9, B-12 | No change needed. |

Later changes go to `spec-0.6-REVISIONS-post-freeze.md`.
