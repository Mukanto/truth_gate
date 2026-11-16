# GHZ run 3: the blind reviews before the freeze

Three reviews of `../ghz_heron_run3/` were made before its freeze (`FREEZE_GHZ3.json`). Each was made by a fresh agent
(Claude Opus 5.5) that wrote no part of the study and had not seen any earlier review except where stated. Each worked
on read-only copies, started by a separate Claude session that does not load the designer's notes. None of the agents
ran anything against the IBM service.

| Review | Instructions | Output | Result |
|---|---|---|---|
| Pre-freeze review of v1 | `PREFREEZE_REVIEW_INSTRUCTIONS.md` | `REVIEW.md`, `REVIEW.json` | 2 blocking, 8 major, 10 minor; not freezable as is |
| Second look at v2 (the agent was given the first review) | `SECOND_LOOK_INSTRUCTIONS.md` | `SECOND_LOOK.md`, `SECOND_LOOK.json` | 16 of 20 fixed, 4 partly; 4 new major, 5 minor |
| Third look at v3 (the agent was given both earlier reviews) | `THIRD_LOOK_INSTRUCTIONS.md` | `THIRD_LOOK.md`, `THIRD_LOOK.json` | all earlier findings fixed; 8 new minor; freezable as is |

The designer's response to every finding is in `../ghz_heron_run3/REVISIONS.md`. The 8 minor findings of the third look
were fixed before the freeze.

The paths in these files are those of the reviewers' task folders, not of this repository.
