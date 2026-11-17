# tests/acceptance_d: expected outcomes (written by the designer, by hand)

Written on 2026-11-17 from the text of `PREREG_PHASE_D_draft3.md` §5 ("Rate flags and their streams", "Attributable
detection", "Generic and declared") and the inputs in each folder (`faulty.json`, `fixed.json`, `expected_flags.json`).
Nothing here was taken from `tools/attributable.py` or its output. Fisher p is the one-sided exact test, faulty count
greater than fixed count, each out of n = 200. The values were computed with the designer's own hypergeometric sum
(`designer/fisher_hand.py`, frozen with its output), not with the tool.

The rule as applied here:
1. The faulty verdict must be NOT_FALSIFIABLE, and the faulty twin must have no load error.
2. Take the faulty flags that are both expected (`expected_flags.json`) and rate flags, and map each to its stream or
   streams with the §5 table. For `K4_CONTROL_ALSO_HOLDS` and `K5_HOLDS_ON_SHUFFLE`, the streams are those with
   `bounds[s].upper ≥ bounds[world:plus].lower`.
3. A stream s qualifies when:
   - (a) the fixed twin carries no rate flag on s, mapped with the same table on the fixed twin's own bounds;
   - (b) Fisher p < 0.05;
   - the fixed twin has no load error and `hard_undefined = 0` on s.
4. The pair is attributable when at least one stream qualifies. It is **generic** when `probe:noise` qualifies, and
   **declared** when a qualifying stream other than `probe:noise` exists.

Exclusions are listed: a fixed load error, a fixed hard UNDEFINED on s, and a faulty load error.

| Folder | Faulty expected rate flags → streams | Fixed rate flags on those streams | Counts F / X | Fisher p | (a) | (b) | Qualifying streams | Attributable | Generic | Declared | Listed exclusion |
|---|---|---|---|---|---|---|---|---|---|---|---|
| a_true_b_false | K2_HIGH_SIZE → world:minus | none | 18 / 17 | 0.50 | yes | no | none | **no** | no | no | none |
| a_false_k2_high_size | K2_HIGH_SIZE → world:minus | K2_HIGH_SIZE | 60 / 30 | 2.4e-4 | no | yes | none | **no** | no | no | none |
| a_false_high_rate_control | HIGH_RATE:control:permute_y → control:permute_y | HIGH_RATE:control:permute_y | 80 / 40 | 9.2e-6 | no | yes | none | **no** | no | no | none |
| a_false_high_rate_noise | HIGH_RATE:probe:noise → probe:noise | HIGH_RATE:probe:noise | 70 / 35 | 5.0e-5 | no | yes | none | **no** | no | no | none |
| a_false_k5_holds_on_null | HIGH_RATE:world:null, K5_HOLDS_ON_NULL → world:null | K5_HOLDS_ON_NULL | 30 / 14 | 0.0079 | no | yes | none | **no** | no | no | none |
| a_false_shuffle | HIGH_RATE:probe:shuffle:x,y → probe:shuffle:x,y | HIGH_RATE:probe:shuffle:x,y | 90 / 45 | 1.4e-6 | no | yes | none | **no** | no | no | none |
| k4_two_controls_one_meets_bounds | K4_CONTROL_ALSO_HOLDS → control:permute_y only (upper 0.150 ≥ 0.096; permute_x upper 0.050 < 0.096) | none (fixed K4 maps to permute_x only: permute_y upper 0.041 < 0.096) | 17 / 1 | 5.3e-5 | yes | yes | control:permute_y | **yes** | no | yes | none |
| shuffle_two_pairs | K5_HOLDS_ON_SHUFFLE → probe:shuffle:x,y only (upper 0.152 ≥ 0.095; y,x upper 0.051 < 0.095) | none (fixed K5 shuffle maps to y,x only: x,y upper 0.043 < 0.095) | 17 / 1 | 5.3e-5 | yes | yes | probe:shuffle:x,y | **yes** | no | yes | none |
| fixed_load_error | K2_HIGH_SIZE → world:minus | (fixed load error) | 60 / — | — | — | — | none | **no** | no | no | fixed load error (SyntaxError) |
| faulty_load_error | (faulty load error; verdict UNDEFINED) | — | — / 4 | — | — | — | none | **no** | no | no | faulty load error, not a detection |
| fixed_hard_undefined | K2_HIGH_SIZE → world:minus | none (fixed flag K1_UNDEFINED is not a rate flag) | 60 / 6 | 1.8e-14 | yes | yes | none: world:minus excluded, fixed `hard_undefined = 50` | **no** | no | no | fixed hard UNDEFINED on world:minus |
| generic_only_k5_holds_on_noise | K5_HOLDS_ON_NOISE → probe:noise | none | 17 / 1 | 5.3e-5 | yes | yes | probe:noise | **yes** | yes | no | none |
| declared_only | K2_HIGH_SIZE → world:minus | none | 60 / 6 | 1.8e-14 | yes | yes | world:minus | **yes** | no | yes | none |

Totals: 4 attributable (k4_two_controls_one_meets_bounds, shuffle_two_pairs, generic_only_k5_holds_on_noise,
declared_only); 9 not attributable. Generic: 1. Declared: 3. Listed exclusions: 3.

Notes:
- In fixed_hard_undefined, the hard-UNDEFINED rule alone decides the outcome. Without it, world:minus would qualify
  (60 / 6, fixed carries no rate flag on world:minus).
- In both k4_two_controls_one_meets_bounds and shuffle_two_pairs, the fixed twin carries the same flag name as the
  faulty twin. The flag maps to a different stream, so (a) holds. A rule that compared flag names instead of streams
  would wrongly give "no".
- In a_false_k5_holds_on_null, the fixed `K5_HOLDS_ON_NULL` is a rate flag on world:null under the §5 table, so (a)
  fails even though the fixed twin has no `HIGH_RATE:world:null`.

## Added after review 3 (R3-6): seven more paths, written by hand on 2026-11-17

Same rule and method as above, applied to the text of `PREREG_PHASE_D_draft4.md` §5. The Fisher p values are computed
with `designer/fisher_hand.py`.

| Folder | Faulty expected rate flags → streams | Fixed rate flags on those streams | Counts F / X | Fisher p | (a) | (b) | Qualifying streams | Attributable | Generic | Declared | Listed exclusion |
|---|---|---|---|---|---|---|---|---|---|---|---|
| k2_no_separation_only | none: `K2_NO_SEPARATION` is expected but not a rate flag; `K2_LOW_POWER` is neither | — | — | — | — | — | none | **no** (PB-detected) | no | no | none |
| faulty_not_nf_with_rate_flag | (faulty verdict UNDEFINED, not NOT_FALSIFIABLE) | — | 60 / 6 on world:minus | — | — | — | none | **no** | no | no | none |
| faulty_nf_unexpected_mandatory | none: `K5_HOLDS_ON_DEGENERATE` is not expected | — | — | — | — | — | none | **no** (not PB-detected) | no | no | none |
| generic_and_declared | HIGH_RATE:probe:noise → probe:noise; K2_HIGH_SIZE → world:minus | none | 70 / 2; 60 / 6 | 5.1e-22; 1.8e-14 | yes; yes | yes; yes | probe:noise, world:minus | **yes** | yes | yes | none |
| fixed_missing_stream | HIGH_RATE:control:permute_x → control:permute_x | (no count on permute_x in the fixed twin) | 80 / — | — | — | — | none | **no** | no | no | fixed has no count on control:permute_x |
| fixed_hard_undefined_other_stream | K2_HIGH_SIZE → world:minus | none (fixed `K1_UNDEFINED` is not a rate flag; its hard UNDEFINED is on world:null only) | 60 / 6 | 1.8e-14 | yes | yes | world:minus | **yes** | no | yes | none for world:minus (fixed hard UNDEFINED on world:null, not a candidate) |
| fixed_k4_blocks_high_rate_control | HIGH_RATE:control:permute_y → permute_y; K4_CONTROL_ALSO_HOLDS → permute_y (upper 0.488 ≥ 0.098) | K4_CONTROL_ALSO_HOLDS → permute_y (fixed upper 0.148 ≥ fixed plus lower 0.098) | 80 / 17 | 4.4e-14 | no | yes | none | **no** | no | no | none |

Totals over all 20 folders: 6 attributable (adds generic_and_declared and fixed_hard_undefined_other_stream);
generic 2; declared 5; 14 not attributable.
