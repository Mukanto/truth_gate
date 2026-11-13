# Spec 0.7: decisions after the freeze

Spec 0.7 is frozen (`FREEZE_SPEC_0.7.json`, core `F1B7E1B1516CE72E`). Points that the frozen text leaves open are decided
here, with reasons, before the code or result they could affect. Decisions by Claude under the author's delegation.

## R-1 (2026-11-13, before R0): studies with unseeded randomness in R1

Four studies of the A1 set use unseeded randomness on purpose; their 0.4.1 certificates carry `K6_NONREPRODUCIBLE`, and
their counts differ from run to run. Section 6 R1 compares counts and bounds exactly, which no run can meet for them. As
in Phase A's A1 (spec 0.6, section 14), R1 compares for these studies only the verdict and the sets of component and
study flags (with section 4 applied to the flags); they are listed as a separate line next to the deterministic studies.

## R-2 (2026-11-13, after R0, before any code): known effect on an older evaluation case

R0 (`evaluation/baseline_v041/`, `FREEZE_BASELINE_V041.json`, core `71A4B1AEFBCF77AA`) recorded 267 studies with v0.4.1.
Classified from the 0.4.1 certificates by `compare_r1.py`: 251 components under section 4 item 1, 6 under item 2 (hard
UNDEFINED or plus majority), 11 under item 3 (soft only), 3 in the BAD_RETURN/mismatch group, plus the R-1 and
deterministic lines. Ten of the eleven item-3 components are the Phase B components of `spec-0.7-R2-prediction.json`.
The eleventh is `evaluation/cases/E2/E2-07_faulty.py` (v0.2 evaluation set): its planted flaw is a criterion that returns
`None` instead of `False` when no peak is detected, so it abstains on all 200 `minus` samples. 0.4.1 made it UNDEFINED
(the v0.2 evaluation counted that as a detection). Under spec 0.7 the abstentions count as no claim and
`K1_ABSTAINED_MAJORITY:world:minus` caps it at WEAK. This follows from the author's decision (abstention counting) and is
what R1 expects; it is reported in the 0.5.0 release notes and in the evaluation of 0.5 as "one older evaluation case
moves from UNDEFINED to WEAK".

## R-3 (2026-11-13, during implementation, before the official R1): hard count of a combined deterministic probe

Section 2.4 says how `hard_undefined` is counted per stream but not for the random probes of a deterministic study
(noise and shuffle), whose three draws are combined into one outcome with `n = 1`. The implementation counts
`hard_undefined = 1` when the combined outcome is UNDEFINED and at least one of its UNDEFINED draws is hard, and 0
otherwise (`checks.stream_stats`). This keeps `hard_undefined <= undefined` on every stream. These probe streams are not
K1 streams, so the rule changes no K1 flag and no verdict; it affects only the recorded counts of those probes. The
implementer chose it while implementing (it was not a stop); the designer accepts it here, before the official R1.
The blind code audit (`spec-0.7-CODE_AUDIT.md`, finding 1) found that `errors` of these streams still counted draw 0
only (as in 0.4.1), so the error counts did not add up to `hard_undefined` as 2.4 requires. The rule is completed:
for a random probe in deterministic mode, `errors` holds exactly one entry, the cause of the first hard UNDEFINED draw,
when the combined outcome is UNDEFINED and hard, and no entry otherwise. Alternatives considered by the audit ("all
UNDEFINED draws hard", "draw 0 decides", "always soft") give the same verdicts in every case and differ only in these
two fields. The `errors` of these streams are not part of a section 4 result. In the R0 set one such stream has an
error (`tests/toy_studies/toy_det_noise_two_undefined.py`, `probe:noise`: the first draw raises and the combined outcome
is UNDEFINED), and the completed rule records the same entry there as 0.4.1 (`ValueError: 1`) (designer's check of
the development run and of the 0.4.1 certificates), so R1 is not affected.

## R-4 (2026-11-13, before the official R1): what "run on the released 0.5.0" means for R1 and R2

Section 6 runs R1 and R2 "on the released 0.5.0". R1 is a necessary condition, so it must be known before the release is
public. The order is: the release commit is made and tagged `v0.5.0` locally (not pushed); R1 and R2 are run from a
clean worktree of that tag, in full mode with default settings, with the frozen `compare_r1.py` and the frozen
prediction; the designer checks both with a separate script. Only if R1 holds is the author asked to approve the push of
the commit and the tag. If R1 fails, the local tag is deleted (it was never public), the defect is fixed, and R1 and R2
are run again on the new tag; both runs are reported. The development R1 that the implementer ran from the working tree
(`scratchpad/r1_dev`) is not the official run.
