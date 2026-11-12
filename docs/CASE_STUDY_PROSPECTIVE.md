# Case study: one prospective use of Kapı

> **Name.** Truth_Gate was called Kapı (Turkish for "gate") until its first public release on 2026-11-12. This
> record keeps the name used at the time. The Python package is still imported as `kapi`.


This is a case study, not an evaluation. It is one study, so it gives no rates. It shows what the gate caught, what it
missed, and why the methods protocol in [`../protocol/PROTOCOL.md`](../protocol/PROTOCOL.md) asks for more than a gate.

## The study, abstractly

A deterministic, low-dimensional geometric model with an update law. The question:

> Is a fixed point attracting within N cycles, while the transients stay inside the model's construct?

Three criteria were pre-registered:

* the local multiplier of the update law at the fixed point has magnitude below 1;
* every start that stays in the construct is within a tolerance of the fixed point after N cycles;
* the whole grid of starts stays in the construct.

The local multiplier was already known before the study (that part was *known*, not prospective). The prospective part
was the global behaviour on a grid of starts. The pre-registration said so explicitly (protocol rule 1.2).

A generic version of the synthetic-world study that Kapı ran for this question is in
[`../examples/convergence_criteria`](../examples/convergence_criteria/README.md). It contains no part of the real
model.

## The flow

1. **Pre-register.** Question, criteria, tolerances, grid, number of cycles, what UNDEFINED means, a table that maps every
   combination of criterion outcomes to one verdict, and numbered interpretations.
2. **First certificate.** Kapı was run on synthetic worlds only. The real model was not run before the freeze, because the
   certificate would have revealed the result.
3. **Revisions with reasons.** Each flag was either fixed or rejected with a written reason (see below).
4. **Freeze.** A SHA-256 manifest of the pre-registration, the study files and the runner; files marked read-only; the
   runner refuses to start unless the manifest verifies.
5. **Run.** The frozen runner ran the real model. The pre-registered table was reported as it was.
6. **Blind audit.** A fresh auditor session read the pre-registration and the code, but not the certificates or the
   revision log. Each finding had to name a location and a concrete failure scenario.
7. **Compare.** The audit findings were compared with what Kapı had flagged. Any audit claim that could change the verdict
   was recomputed independently, by a separate route.

## What happened, in numbers

**First certificate.** Kapı raised 10 flags.

* **6 were real and were fixed:** missing controls, a bug in a control transform, and a `minus` world that could not
  fail one criterion.
* **4 were rejected, each with a written reason:** the generic vacuity probes (noise and all-zero data) applied to a
  precomputed scalar, and to a criterion that is conditional on a subset of the data. These probes replace every array
  in the data; a criterion that reads a single precomputed scalar, or that returns UNDEFINED when no start qualifies,
  then holds or is undefined for reasons unrelated to the criterion. The rule behind the decision: a mandatory flag is
  not filled with a cosmetic control, and a rejected flag needs its reason on record.

**Blind audit.** The auditor made 8 substantive findings. Kapı had fully flagged **0** of them and partially touched
**2**.

**Final certificates.** The one criterion that ended with a clean certificate still carried 3 audit caveats:

* the result depended on a model interpretation;
* the synthetic world was unrealistic;
* the decision rested on two grid points.

## What this says about the gate

Kapı did what it is built to do: it found problems in the logic of the criteria and in the controls (6 real flags). It
did not find any of the substantive problems the audit found, because those were about the interpretation of the model
and the controls of the real run, which the gate never sees.

## The lesson that changed the protocol

The qualifier attached to the study's verdict depended on a single numbered interpretation. This was found only by the
blind audit; nobody had noticed the dependence before it.

For that reason the protocol now requires, for every interpretation that can change the verdict, its **opposite
reading** and a **sensitivity arm**: a pre-registered run (or recomputation) under the other reading, with the verdict
mapping stated in advance (protocol rule 1.4, and the interpretations section of the pre-registration template).
