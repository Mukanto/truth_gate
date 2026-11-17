# Independent recomputation of the attributable rule: comparison (designer, 2026-11-17)

- **Recomputation.** A fresh kodlayici agent wrote it from `inputs/RULE.md` alone (draft 3 §5, lines 341–375, as they
  stood before the T3-12 precisions and the review-3 changes were added; the
  acceptance paragraph with the Phase C fixture table was withheld). It did not have access to `tools/` and did not see
  `EXPECTED.md`. The acceptance folders were given under neutral ids P01–P13; the map is `MAP_P_ids.json` (P14–P20
  added for round 4).
- **Inputs.** Unchanged after the task: 85 of 85 files match `MANIFEST_recompute_d.json` (in this folder).
- **Transcript.** No path outside `recompute_d/`. One deviation: a read-only `git -C . status --short` inside
  `recompute_d/`, which is not a repository, so it had no effect.

## Result

| Set | Pairs | Hand (`EXPECTED.md`) = recomputation = tool | Attributable / generic / declared |
|---|---|---|---|
| Acceptance | 13 | 13 of 13 equal on attributable, generic, declared and the qualifying streams | 4 / 1 / 3 |
| Phase C B-2 and B-3 | 22 | 22 of 22 equal (recomputation = tool), on the same fields | 10 / 7 / 8 |

- The Phase C result equals the designer's fixture (`fixture_attributable_pc_output.txt`): the same ten pairs are
  attributable, with B3-04 and B3-05 generic only.
- Comparison script: `designer/compare_recompute.py`. It ran `tools/attributable.py` on every
  pair and gave 0 differences.

## Round 4 (after review 3)

- Seven acceptance pairs were added (R3-6). The designer ran the agent's `recompute.py` unchanged (byte-identical
  copy, SHA-256 in `round4/README.md`) on all 20 acceptance pairs (P14–P20 under new neutral ids) and the 22 Phase C
  pairs, in `round4/`. The agent itself did not see the seven new pairs.
- `designer/compare_recompute.py` now reads the hand-written outcomes from `tools/tests/acceptance_d/EXPECTED.json`.
  Its output is in `designer/compare_recompute_output.txt`: hand = recomputation = tool on 20 of 20 acceptance pairs,
  and recomputation = tool on 22 of 22 Phase C pairs; 0 differences.
- One convention is aligned in the comparison, not in either scoring. On P19 (`faulty_not_nf_with_rate_flag`, faulty
  verdict UNDEFINED), the agent's script lists `world:minus` as a stream-level qualifier, with attributable false and a
  note, as its `NOTES.md` item 12 says. Section 5 defines qualifying streams only for an attributable detection, so the
  comparison treats the qualifying streams of a non-attributable pair as empty. All three agree on attributable,
  generic and declared for every pair.
- `tests/test_acceptance_d_expected.py` asserts the tool against `EXPECTED.json` on all 20 pairs; the full tool suite
  (380 tests) passes.
