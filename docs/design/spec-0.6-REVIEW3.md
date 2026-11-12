# Targeted review 3 of the spec 0.6 draft v3 (fresh agent, 2026-11-12)

A final pre-freeze review of the review-2 items and of the parts v3 rewrote. The reviewer did not see the revision log.
Condensed.

**Review 2 items:** 2, 3, 4, 5, 7, 8, 9, 10, 11, 12, 13, 14, 15 resolved; 1 and 6 partly. The reviewer re-ran the A4
simulation (faulty holds about 0.90 in plus and 0.0008 in minus; K8 change rate about 0.17 gives a Wilson lower bound
about 0.12 at level 0.025; no `K2_HIGH_SIZE` or `K2_LOW_POWER`) and checked the Phase B Wilson numbers (9/10 about 0.65,
8/10 about 0.54).

**New findings on the rewritten parts:**

* **B-7, blocking (A1).** A1 is unreachable for some studies as written: `tests/toy_studies/toy_nonreproducible.py`
  uses unseeded randomness, so its counts differ between two runs of the same code; the leak toys record absolute
  paths, so the baseline must run at the same path; the study list is not enumerated (`examples/ghz_heron/*.py` holds
  non-study scripts).
* Non-blocking: B-1 whether K8 flags pass through the 0.3 suppression rules; B-2 the exit 4/exit 3 boundary for 0.3's
  own `Study` validation errors, and `suggest` output with no criterion cannot "run"; B-3 `pattern_stats` in quick mode,
  quantile storage, `all_of`/`any_of` layout; B-4 K8 sample count in quick mode; B-5 the guard log of the post-engine
  passes; B-6 the extra read-key request for command criteria; B-8 A2/A3 coverage reachable (C3 as a pattern
  unverified); B-9 the A4 manifest is valid; B-10 exit code of `badge` on a hash mismatch; B-11 new
  `known_limitations` text unspecified; B-12 Phase B thresholds consistent.

**Verdict:** one blocking change (B-7); settle the rest in the revision log.
