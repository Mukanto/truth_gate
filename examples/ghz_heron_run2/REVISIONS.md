# GHZ run 2: revisions before the freeze

Decisions by the designer (Claude, under the author's delegation), each with its reason.

**Before any certificate.** The designer corrected their own first draft of the synthetic worlds and one control, and logged the corrections in messages to the coder before implementation:
- under noise, the plus world did not make H3 hold at n = 48;
- the minus world did not break H2;
- the stale-calibration control pushed F_pred above 1, which made H1 UNDEFINED instead of FAILS.

## Certificate v1
`certs/cert_v1.json`, body_sha256 1bc210fb…, overall NOT_FALSIFIABLE.

| # | Criterion | Flag | Decision | Reason |
|---|---|---|---|---|
| 1 | H2 | HIGH_RATE:probe:noise (H2 held on 45 of 200 noise draws) | **fixed** | Real defect. H2 accepted physically meaningless predictions, and a coarse equality on 6 grid values then agrees by chance. H2 is now UNDEFINED if any F_pred lies outside (0, 1). This matches H1's existing rule, and it changes nothing on physical data. |
| — | H1, H2, H3 | K5_INCONCLUSIVE (noise, zeros) | **rejected** | Same root as run 1, revision #7. The probes produce non-physical predictions, and by the pre-registered definitions the criteria are then UNDEFINED. |

## Certificate v2
`certs/cert_v2.json`, body_sha256 1b8009ad…, overall WEAK.

| # | Criterion | Flag | Decision | Reason |
|---|---|---|---|---|
| 2 | H2 | K4_INCONCLUSIVE | **fixed** | My control was now inconsistent with fix #1. It raised every column by 0.12, so F_pred(4) became 1.056, and H2 correctly returned UNDEFINED. The control now raises only n = 32 and n = 48 by 0.12. That represents the failure it names (the model overpredicts large states, so the predicted reach moves out one step), and every value stays inside (0, 1). |

## Certificate v3 (final before freeze)
- `certs/cert_v3.json`, body_sha256 38c68fde…, overall **WEAK**. H1, H2 and H3 are WEAK; only the rejected K5_INCONCLUSIVE flags remain.
- Tests 28 OK. ghz2_d4: budget OK (368 circuits, about 187 s), K2 PASS (bit-order positive control included), D4 OK, rule 14 yes. Selftest OK.

**Tally:**
- Kapı raised 2 actionable flags, both fixed: #1 was a real criterion defect, #2 a designer error introduced by fix #1.
- The K5_INCONCLUSIVE flags were rejected (1 root cause).
- The designer caught 3 errors in their own draft before any certificate.

## Freeze (Claude, delegated, 2026-11-12)
Frozen at WEAK (capped only by the rejected K5_INCONCLUSIVE flags).
