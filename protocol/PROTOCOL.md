# Methods protocol for pre-registered computational studies

This protocol is the core of the practices that found major defects in a real study (see
[`../docs/CASE_STUDY_PROSPECTIVE.md`](../docs/CASE_STUDY_PROSPECTIVE.md)). Next to each rule is a short note on the
incident that produced it. The notes are generic on purpose.

It is written for studies where a model or algorithm is run against pre-stated acceptance criteria, where the people
(or AI agents) who design the study could easily see the result before they commit to the criteria. The gate in Truth_Gate
([`../README.md`](../README.md)) automates part of the checking of controls, worlds and reachability (steps 1.5, 1.7 and 1.10, and
section 5). It does not replace the rest.

## Roles

* **Author.** Owns the theory decisions. If the author delegates a decision, it is written into the decision register
  with the label "assistant (by delegation)", so it can be reviewed and reversed.
* **Designer.** Writes the pre-registration, the criteria and the synthetic worlds.
* **Coder.** Writes the code. Does not compute the real result before the freeze.
* **Auditor.** A fresh agent session, or an independent reviewer session (Tenkit). Does not see the designer's
  certificates, the revision log or the designer's interpretations.
* **Verifier.** Recomputes, by a separate route, every claim (the designer's or the auditor's) that could change the
  verdict.

One person may fill several roles, except that the auditor must not be the designer.

## 1. Before the run

1. **The tautology question.** Is the result decided by definitions, by the event rules that carry the target, or by
   the criterion itself? If so, do an analytic check, not an experiment. *(Earlier studies had a criterion whose
   targets were computed from the very labels it was compared with, a direction criterion that could not tell a path
   from its mirror image, and a component decided by the way it was defined.)*
2. **Separate the known from the prospective.** The pre-registration lists separately the part whose result is already
   known. *(In one study the local multiplier of the update law was already known; the prospective part was the global
   behaviour on a grid of starts.)* A replicate on the same inputs (for example the same device calibration) tests the
   data, not the model's predictions; say which one a run is. *(A second hardware run on an unchanged calibration was
   planned as a model test and turned out to be a data replicate.)*
3. **The pre-registration file.** It contains the items below. The file is hashed and the time is recorded.
   * 2 to 4 primary criteria;
   * tolerances, grid and number of cycles;
   * what UNDEFINED means;
   * the verdict mapping: every combination of criterion outcomes goes to exactly one verdict;
   * numbered interpretations.
4. **Write the opposite reading of every interpretation.** If an interpretation can change the verdict, put its
   sensitivity arm into the pre-registration. *(In the prospective study, the verdict's qualifier depended entirely on
   one interpretation, and only the blind audit found it.)*
5. **A negative control is mandatory.** At least one arm violates the theory.
   * If the control also holds, the result is only an existence demonstration. *(In one realization study every
     negative control also succeeded, 6/6.)*
   * Every criterion needs a control that can actually make it fail.
   * A control cannot "pass" by being UNDEFINED. *(In one audit, a control's second criterion passed because there was
     nothing to evaluate.)*
6. **The fidelity check tests the new code.** Testing the case that reduces to the old code is not enough. Compare the
   newly added path with an independent implementation, for example where the old and new parameter differ, or where
   state is carried between cycles. *(An audit found a fidelity check that only covered the old-code case.)*
7. **The minus world changes the data the criterion reads.** If it does not, the criterion was not tested. *(In a
   retrospective pilot, the minus world of one study was bit-for-bit identical to the plus world in 22 of 22 data
   keys. This is where the gate's UNTESTED verdict (v0.3) came from.)*
8. **One change at a time.** If two changes cannot be avoided, add a control that separates them. *(In one study the
   verdict was decided by the tolerance, not by the symmetry that was the question.)*
9. **Tolerances sit above the numerical resolution and the noise ceiling.** *(In one chain of studies a 2-degree jitter
   made strict tolerances unreachable even for the nominal polygon. In float64, 1 + 1e-25 = 1.)* The noise ceiling
   includes run-to-run drift: measure it with a repeat run or a cheap repeated subset before setting a tolerance.
   *(Between two hardware runs 25 minutes apart, small-state fidelity moved by about 0.02, several times the shot-noise
   interval, and a pre-registered 0.05 band was missed by 0.005.)*
10. **Smoke test before the freeze ("D4").** For each criterion and each hypothesis, print only the following, never
    the verdict value:
    * is it defined;
    * is it reachable (can it both hold and fail);
    * is it covered.

    Reachability is computed from synthetic input, not from the real verdict. *(One study had three specification
    defects; a review found a `--quick` mode that read a results file.)*
11. **Blindness.** Before the freeze nobody computes the real result. Verification uses only values whose result is
    already known. The automated checker runs on synthetic worlds. *(Had the gate run the real model, the certificate would
    have shown the result before the freeze.)*
12. **Freeze.** Write a SHA-256 manifest and mark the files read-only. The runner refuses to start if the manifest does
    not verify. ([`tools/freeze.py`](tools/freeze.py), [`templates/run_guarded.py`](templates/run_guarded.py).)
13. **Predict the quantity you estimate.** If the estimator combines components (for example population and coherence), derive
    the model's prediction for each component separately. A single product formula applied to the combination can be the wrong
    function of the error rates. *(In a hardware study the model applied readout error once to a fidelity whose coherence part
    loses it twice. That mismatch, not the device, decided two of three verdicts. Only the blind audit found it.)*
14. **Both bounds of a band must be reachable.** If the model cannot reach one bound (a ratio band whose upper end exceeds what the
    prediction allows), the test is one-sided. Say so, or drop the bound.
15. **A directional hypothesis must be identified.** If every unmodelled error pushes the result in the predicted direction, the
    test does not isolate the cause it names. Add an arm that separates the named cause from generic underestimation.
    List the error classes that could produce the direction, and check each one, not only the convenient ones.
16. **Compute the power of every confirmatory test** for the effect size you expect, from the planned sample. An
    underpowered FAILS reads "not demonstrated", not "refuted". *(A replication test had about 25–30% power for the
    effect seen in the first run.)*

## 2. The run

* After the run, the manifest hashes are checked again.
* If a family that contains an optimizer comes out as "did not hold", first rule out an optimizer artifact, for
  example with more restarts.

## 3. After the run

1. **Report the pre-registered table as it is:** rule, result, verdict. The thresholds do not change. Additional
   analyses carry the label "exploratory".
2. **Independent recomputation.** Every number that could change the verdict is recomputed by a separate route,
   preferably with the original code and at high precision.
3. **Blind audit.** Each finding gives a file and line (or a pre-registration section) and a concrete failure scenario.
   Any claim by the auditor that could change the verdict is recomputed by the verifier.
4. **Labels.** Label each statement by where it comes from: the author's decision, a measurement or direct statement
   from a source, or the assistant's reading. A grid result is written as a grid result. An approximate equality is not
   written as exact.
5. **State your own mistakes plainly, and do not change the criterion.** *(In the gate's v0 evaluation the criterion P4
   was defined wrongly by the designer. It scored 51/52 and stayed "failed".)*
6. **After a surprising result, first explain it in plain words.** Do not widen a definition until the result fits, and
   do not pile up decision questions for the author. *(A lesson from one study's review.)*

## 4. The repair loop

* Before a repair is applied, test it against the whole text:
  * closed lists;
  * the scope of labels;
  * where a definition comes from;
  * the variants that an attribution covers.

  *(In several review rounds the new defects were in the sentences written to repair earlier findings.)*
* An auditor's proposal is not the author's approval.
* Before adding a control in response to an audit, check that the failure it guards against can affect the estimator.
  *(A bit-order control was added to a study whose estimator is invariant under any permutation of bits.)*

## 5. Automated checkers (the gate and similar)

* **What they catch:** defects in the logic of criteria: a missing control, a code bug, a criterion that was never
  tested, an inert minus world.
* **What they cannot see:** the interpretation of the model, the controls of the real run, the meaning of a criterion.
* **Rule:** a mandatory flag is not filled with a cosmetic control. If a flag is rejected, the reason is written down.
* *(In the prospective study the gate raised 10 flags, 6 of them real defects. Of the audit's 8 substantive findings it
  flagged none fully.)*

## Checklist before the freeze

The same list is in [`CHECKLIST.md`](CHECKLIST.md).

- [ ] The tautology question is answered.
- [ ] Known and prospective parts are separated.
- [ ] Criteria, verdict mapping and the meaning of UNDEFINED are written; the pre-registration is hashed.
- [ ] Interpretations are numbered; for those that could change the verdict, the sensitivity arm is recorded.
- [ ] For every criterion there is a negative control that can make it fail; none can pass by being empty.
- [ ] The fidelity check tests the new code path against an independent implementation.
- [ ] The minus world changes the data the criterion reads.
- [ ] Tolerances are above the numerical resolution and the noise ceiling.
- [ ] D4 is clean: defined, reachable and covered, tested with synthetic input.
- [ ] Nobody has seen the real result.
- [ ] The manifest is written and the files are read-only; the runner verifies the manifest.
- [ ] The model predicts each estimated component separately (no product formula applied to a combined estimator).
- [ ] Both bounds of every band are reachable under the model; one-sided tests are labelled as such.
- [ ] Directional hypotheses are identified: generic unmodelled error does not produce the predicted direction by itself.
- [ ] Run-to-run drift is measured and the tolerances sit above it.
- [ ] The power of each confirmatory test is computed for the expected effect.
- [ ] Each run is labelled as a model test or a data replicate.
