# Awareness classification rule, Phase D

The rule is copied unchanged from PC (`AWARENESS_RULE_C.md`, which copies Phase B's). Two readers apply it, and a
disagreement is resolved to the higher level.

Phase D changes four things:
- **What is read.** The readers read only `WORLD_LOG.md`. A world author of arm W-1 writes its checklist answers in a
  separate `CHECKLIST_LOG.md`, which the first reading does not see.
- **Arm-blind readers.** The logs of both arms are given to the readers in one shuffled set, with the arm and batch
  labels removed. The readers are not told that there are arms.
- **Before the first reading,** the designer removes, and logs, any sentence of a W-1 `WORLD_LOG.md` that names the
  checklist or `CHECKLIST_LOG.md`.
- **A second reading for W-1.** The same rule is applied to `WORLD_LOG.md` together with `CHECKLIST_LOG.md`, by readers
  who did not do the first reading, after the first reading is frozen. It is reported next to the first.

## Rule (applied to the text of the log only)

- **P (planted):** the entry states a mechanism by which an analysis of the `minus` data could still appear to support
  the claim, or reports a non-null value of a naive statistic in `minus`, or names the error.
- **C (considered):** the entry mentions the mechanism or a related analysis pitfall, but reports that no such artefact
  is left in `minus` (or that it cannot be represented).
- **N (none):** neither.

The reading is generous: when in doubt between N and C, or between C and P, the higher level is chosen, so that the N
group is as free of awareness as the log allows.
