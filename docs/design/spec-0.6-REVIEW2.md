# Blind review 2 of the spec 0.6 draft v2 (fresh agent, 2026-11-12)

The reviewer read draft v2, review 1 and the 0.3 code and tests. It did not see the revision log. Condensed.

## Status of the review 1 findings

Resolved: 1, 2, 3, 6, 13, 15, 16, 17, 18. Partly: 4 (test edits incomplete), 5 (K8 stream model and denominators
undefined), 7 (A3 exemption unmeasurable; missing `node` not handled), 8 (A1 contradicts changed `non_claims`), 9 (pattern
criteria cannot carry `tolerances`), 10 (point thresholds at n = 10; authorship), 11 (key table incomplete;
deterministic sampling), 12 (file bootstrap in deterministic mode), 14 (`pattern_stats` side channel; `equals`). New
problem: 19 (A4 manifest incomplete).

## New findings

1. **Critical (§1.1, §11, A1).** `non_claims` is in the hashed body and its text names "Kapı" (`certificate.py:22-27`);
   `StudyError` messages name `kapi.Study` (`study.py:261`). A1 fails as written, or its strip list is widened after
   the results.
2. **Major (§1.1).** The list of engine changes is incomplete: the `pattern_stats` side channel needs stream identity
   and would make run 1 and run 2 bodies differ (false `K6_NONREPRODUCIBLE`); flag sets, `BODY_FIELDS`,
   `validate_envelope`, `format_table` and exit 7 are unlisted; the package rule "no `subprocess` import"
   (`tests/test_package.py:14`) is dropped without being named.
3. **Major (§7).** K8 does not fit `make_sample`/`collect` (`checks.py:377, 430`); in deterministic mode its independent
   draws would raise `NONDETERMINISTIC` (`checks.py:704-711`) unless exempted; §6 and §7 contradict on deterministic
   draws.
4. **Major (§7).** The K8 rate is undefined (pooled or per stream; family count); the built-in invariance raises `m`
   for every exchangeable manifest, so A2 manifests with it differ from their Python originals.
5. **Major (§3.2, A2).** Pattern criteria cannot carry `tolerances`; example 03 declares one, so a rewrite silently
   drops `K2_UNRESOLVABLE` checking and A2 still passes.
6. **Major (§3.2, §3.3).** Deterministic file sampling undefined; world keys missing from the key table under
   "unknown key is an error"; the boundary between exit 4 (manifest error) and a certificate with exit 3 (`StudyError`)
   is not stated.
7. **Major (§5).** Handshake, missing or unhashable executable outcomes unstated; the stderr tail is read while the
   guard is armed (a blocked `open`); Windows cleanup can fail with a surviving grandchild; the stderr byte length is
   machine-dependent and breaks `verify`; exit 7 on every patch release.
8. **Major (§5, §11, honesty).** Command criteria are unguarded and the only disclosure is a note no verdict reads; a
   green FALSIFIABLE badge can be earned with the guard void.
9. **Major (A3).** The near-threshold exemption has no count limit and no defined statistic for non-pattern criteria;
   a skipped Node run is not declared a failure.
10. **Major (Phase B).** Point thresholds at n = 10 (8/10 passes with a Wilson lower bound near 0.49); `HIGH_RATE:*` is
    too broad; case authors have read the documentation; no comparator; sources unverified.
11. **Major (§4).** `largest_true` when the primary curve has no qualifying value, and NaN in `y`; `equals` is equality
    on data values; `ci_excludes` quantile method, default `B`, generator, pairing and `stat` for differences; the
    precedence of a missing key inside `any_of`.
12. **Major (§14.1).** The A4 manifest has no world paths or `rows`; the faulty criterion's minus rate (about 0.16)
    already gives `K2_HIGH_SIZE`, so K8 would not change its verdict; no false-positive case.
13. **Minor.** Baseline mode (full or quick) unstated.
14. **Minor (§8).** `suggest` bootstraps DATA, usually the real data; only the free-text provenance guards against it.
15. **Minor.** TOML datetimes, `nan` and `inf` are unspecified.

**Readiness (reviewer):** not ready to freeze; ten minimum changes listed (all covered above).
