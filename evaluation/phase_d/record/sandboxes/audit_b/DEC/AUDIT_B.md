# AUDIT_B (part B, item o)

| Case | X | Y |
|---|---|---|
| D-012 | yes | yes |
| D-047 | yes | yes |
| D-052 | yes | yes |

## Reasons
**D-012**
- X: yes. Keys are only `occupied` and `exclosure`; no variable is named by its role in the error. The hidden `copy_assignment` gives minus the same plot-level structure as plus (same size as the fencing effect), alongside AR(1) correlation of neighbouring quadrats. This is realistic dependence, not an extra key for one body.
- Y: yes. Logit model with plot SD and AR(1) micro-habitat variation; minus only zeroes the fence effect.

**D-047**
- X: yes. Site offsets, OU fluctuation and rating error are ordinary realistic dependence; only the three brief keys.
- Y: yes. Stable severity plus iid visit error. Remark: the minus `change` string contains "regression to the mean after screening selection", which names the error phenomenon in a descriptive string. No variable or key is named by its role, so I judge it not a leak. The author or the next reader may want to remove the phrase.

**D-052**
- X: yes. Shared ability across pre and post, equal gain SD in both groups, minus equalises the mean gain only.
- Y: yes. Group-specific ability SD, small baseline-gain slope and measurement error are ordinary; improvement variances come out nearly equal across groups (a helper estimate by hand, nothing run). `relational=[("post","young")]` is a study-level declaration, not a key or an aimed dependence.

## Read
Files in the sandbox `DEC\` folder: `FIDELITY_AUDIT_D.md`; for D-012, D-047, D-052 in `class\cases\`: `brief.json`, `PRIVATE.json`, `PASSAGE.md`, `CASE.md`, `X.py`, `Y.py`, `reference.py` (for context). Not read: faulty/fixed bodies, MECH_CHECK, STRUCTURE_LOG, logs (not needed for item o).
URLs read: none.
