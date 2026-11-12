# Pre-registration: <STUDY NAME>

Fill in every section. Write "none" rather than leaving a section empty. When this file is complete, hash it
(`python protocol/tools/freeze.py write ...`) and record the time. After the freeze nothing in it changes; a change goes
into a new version with a deviation note.

- **Author:** <name or role>
- **Date written:** <YYYY-MM-DD>
- **Version:** <1>

## 1. Question

One or two sentences. What is being asked, and about which model or algorithm?

> <question>

## 2. Known and prospective

Rule 1.2 of the protocol. Which parts of the result are already known to anyone involved, and which part is prospective?

| Part | Known or prospective | Why |
|---|---|---|
| <part> | known / prospective | <for example "the local multiplier was computed last year" / "the global behaviour has not been run"> |

The tautology question (rule 1.1): is any criterion decided by definitions, by the event rules that carry the target, or
by the criterion itself?

> <answer, and what was done about it>

## 3. Criteria

Two to four primary criteria. Everything about HOLDS, FAILS and UNDEFINED is stated here, before any run.

| Id | Claim | HOLDS when | FAILS when | UNDEFINED when |
|---|---|---|---|---|
| C1 | <claim> | <rule, with numbers> | <rule> | <rule> |
| C2 | | | | |
| C3 | | | | |

What UNDEFINED means for the verdict (for example "UNDEFINED never counts as HOLDS"):

> <rule>

## 4. Verdict mapping

Every combination of criterion outcomes goes to exactly one verdict. List all combinations, or give a rule that covers
all of them and says so.

| C1 | C2 | C3 | Verdict |
|---|---|---|---|
| HOLDS | HOLDS | HOLDS | <verdict> |
| ... | | | |

Wording that may be used for each verdict in the report:

> <verdict: sentence>

## 5. Interpretations

Number each interpretation (a reading of the model, of a term, of a data convention). For any interpretation that could
change the verdict, write its opposite reading and the sensitivity arm that will be reported.

| No. | Interpretation | Opposite reading | Can it change the verdict? | Sensitivity arm (what is run or recomputed under the opposite reading) | Verdict under the opposite reading |
|---|---|---|---|---|---|
| I-1 | <text> | <text> | yes / no | <arm> | <verdict, from section 4> |
| I-2 | | | | | |

## 6. Controls

**Fidelity controls.** They show that the code does what the model says. They test the *new* code path against an
independent implementation, not only the case that reduces to the old code.

| Id | What is compared | Independent implementation | Pass rule |
|---|---|---|---|
| F1 | <new path> | <how it is computed independently> | <numeric rule> |

**Detector controls (negative controls).** At least one arm violates the theory. Each criterion has a control that can
make it fail. A control cannot pass by being UNDEFINED.

| Id | Criterion it controls | How it violates the theory | Expected outcome |
|---|---|---|---|
| N1 | C1 | <how> | FAILS |

## 7. Grid, N and tolerances

| Item | Value | Why this value |
|---|---|---|
| Grid of starts / conditions | | |
| Number of cycles N | | |
| Tolerances | | above numerical resolution and noise ceiling? |
| Random seeds | | |
| Optimizer restarts (if any) | | |

## 8. Run plan

* **Gate:** the study file for the gate is `<file>`. It runs on synthetic worlds only. Certificate: `<file>`.
* **Smoke test (D4):** <what is printed: defined / reachable / covered; no verdict values>.
* **Real run:** `<runner>`, started with `run_guarded.py`. Output: `<file>`.
* **Re-check after the run:** manifest verified again; the pre-registered table reported as it is.
* **Independent recomputation:** <which numbers, by which route>.
* **Blind audit:** <who, which files they may see>.

## 9. Freeze

* **Files in the manifest:** <pre-registration, study files, runner, data files>
* **Manifest:** `FREEZE.json`, written with `freeze.py write`.
* **Frozen on:** <date and time>
* **Manifest core hash:** <paste core_sha256>
* **Nobody has seen the real result:** <yes / no; if no, explain>

Signed off by: <author> on <date>
