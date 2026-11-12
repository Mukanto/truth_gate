# Checklist before the freeze

Part of the [methods protocol](PROTOCOL.md). Every box must be ticked, or the reason it cannot be ticked written next to it,
before the freeze manifest is written.

- [ ] **Tautology question** answered: the result is not decided by definitions, by the event rules that carry the target,
      or by the criterion itself. If it is, an analytic check replaces the experiment.
- [ ] **Known and prospective parts** are separated in the pre-registration.
- [ ] **Criteria, verdict mapping and the meaning of UNDEFINED** are written; the pre-registration is hashed and the time is
      recorded.
- [ ] **Interpretations** are numbered; for those that could change the verdict, the opposite reading and the sensitivity
      arm are recorded.
- [ ] For every criterion there is a **negative control** that can make it fail; none can pass by being empty (UNDEFINED).
- [ ] The **fidelity check** tests the new code path against an independent implementation, not only the case that reduces
      to the old code.
- [ ] The **minus world** changes the data the criterion reads.
- [ ] **Tolerances** are above the numerical resolution and the noise ceiling.
- [ ] **D4 smoke test** is clean: every criterion is defined, reachable (can both hold and fail) and covered, tested with
      synthetic input; no verdict value was read.
- [ ] **Nobody has seen the real result.**
- [ ] The **manifest** is written and the files are read-only; the runner verifies the manifest before it starts.
- [ ] The **model predicts each estimated component** separately; no single product formula is applied to a combined estimator.
- [ ] **Both bounds** of every band are reachable under the model; one-sided tests are labelled as such.
- [ ] **Directional hypotheses are identified:** generic unmodelled error does not by itself produce the predicted direction.
- [ ] **Run-to-run drift** is measured (repeat run or repeated subset), and the tolerances sit above it.
- [ ] The **power** of each confirmatory test is computed for the expected effect size.
- [ ] Each run is labelled as a **model test** or a **data replicate** (same inputs).
