# Phase C report: documented errors, worlds by a different Claude model line

Pre-registration: `PREREG_PHASE_C.md` v3 (`FREEZE_PREREG_C.json`, core `0B8CC8F9F726103A`), with Phase B's frozen
pre-registration as "PB". Cases and expected flags: `FREEZE_CASES.json` (core `17F7CDF0E5396542`); pre-run record:
`FREEZE_RECORD.json` (core `C88CC1D9A153B1B6`). The frozen cases were pushed to the public repository as commit `aecd613`
before the gate ran; the runner and the run and report readings P-7 and P-8 (`REVISIONS-post-freeze.md`) were pushed as
`cfba5c6`, also before the run. Run on 2026-11-15 (17:41 to 18:24 UTC): Truth_Gate at tag `v0.5.0` (commit `5661709`)
and at tag `v0.4.1` (`90e8dad`), each from a clean worktree, full mode, every file, one check at a time, default
settings, by `run_phase_c.py`. Every number below comes from `run/RESULTS.json`; the designer recomputed them from the
certificates with a separate script written without reading the runner (`run/recompute_designer.py`, output
`run/recompute_designer_output.txt`), with **0 differences** over the 52 pairs (`run/recompute_compare_output.txt`).

Sections 1 to 6 are the pre-registered results. Section 7 is interpretation, written after the run and labelled as
such. Section 8 lists the limits. Section 9 reports the post-run audit.

**How to read every verdict below (PREREG_PHASE_C §6, I-8).** The worlds and controls of every case were declared by
Fable, a different Claude model line from the one that wrote the gate and the criteria, which was not told the error,
the class or the source. Each class verdict carries the class's shares of the awareness levels P, C and N (resolved
reading, section 4): P counts the declared worlds that may contain what the error exploits.

## 1. Result (Truth_Gate 0.5.0, the pre-registered primary table)

| Class | Pairs | Detections (generic / declared / K2-only) | Clean passes | Wilson lower bound, detection | Wilson lower bound, clean pass | Awareness P / C / N | Verdict |
|---|---|---|---|---|---|---|---|
| B-1 circular analysis | 12 | 12 (7 / 5 / 0) | 11 | 0.816 | 0.699 | 10 / 2 / 0 of 12 | **HOLDS** |
| B-2 procedure-level leakage | 12 | 7 (5 / 2 / 0) | 8 | 0.356 | 0.431 | 10 / 2 / 0 of 12 | **FAILS** |
| B-3 coupling by construction | 10 | 8 (6 / 2 / 0) | 8 | 0.541 | 0.541 | 10 / 0 / 0 of 10 | **FAILS** |
| B-6 inflated-size decision rules | 12 | 10 (0 / 10 / 0) | 12 | 0.601 | 0.816 | 12 / 0 / 0 of 12 | **HOLDS** |
| Out of scope (O-1 to O-3) | 6 | 2 (1 / 1 / 0) | 6 | – | – | 5 / 1 / 0 of 6 | no threshold |

One-sided 95% Wilson bounds; a class holds with at least 10 pairs and both lower bounds at least 0.6. Every in-scope class
kept at least 10 pairs (two B-3 pairs were dropped at the fidelity audit, P-6). B-2 per subtype (descriptive, no
verdict): L1.1 1 detected / 1 clean of 1, L1.3 5 / 1 of 5, L1.4 1 / 2 of 2, L3.1 0 / 2 of 2, L3.2 0 / 2 of 2; no L1.2
pair. B-4 and B-5: no documented cases; no evidence either way.

**Answer to the main question (§0).** Truth_Gate 0.5.0, with worlds and controls declared by a different Claude model
line that was not told the error, met the pre-registered bar for two of the four in-scope classes on errors documented
in the literature:
* B-1 HOLDS: 12 of 12 detections, 11 of 12 clean passes; P 10/12, C 2/12, N 0/12 (declared worlds that may contain what
  the error exploits).
* B-6 HOLDS: 10 of 12 detections, 12 of 12 clean passes; P 12/12, C 0/12, N 0/12 (declared worlds that may contain what
  the error exploits). The detection bound, 0.601, is the smallest that passes with 12 pairs.

It did not meet the bar for:
* B-2 FAILS: 7 of 12 detections, 8 of 12 clean passes; P 10/12, C 2/12, N 0/12 (declared worlds that may contain what
  the error exploits).
* B-3 FAILS: 8 of 10 detections, 8 of 10 clean passes; P 10/10, C 0/10, N 0/10 (declared worlds that may contain what
  the error exploits).

Over the 46 in-scope pairs, 0.5.0 detected 37 faulty criteria and passed 39 fixed ones. Of the 37 detections, 18 are
labelled generic (an expected flag of the gate's own noise probe is among the flags found) and 19 declared (only flags of
the declared streams), by the rule of PB §6. Section 9 lists the detections whose fixed twin carries the same expected
flags.

## 2. Primary comparison: 0.5.0 against 0.4.1 (same files)

Eight study files had a component that 0.4.1 made UNDEFINED, at least the 5 needed, so the comparison is
**informative**. All eight are the faulty and fixed twins of four B-1 pairs (B1-05, B1-06, B1-08, B1-09). The cause in
every one is "soft only": the criteria abstained (returned `None` through an allowed guard) on part of the `minus`
samples, with no hard UNDEFINED and no `plus` majority. Under 0.5.0 the four faulty twins are NOT_FALSIFIABLE with
expected flags and the four fixed twins are WEAK.

| | Detections gained | Clean passes gained | Faulty UNDEFINED -> FALSIFIABLE/WEAK (misses 0.4.1 hid) | Fixed UNDEFINED -> NOT_FALSIFIABLE (false alarms 0.4.1 hid) | Losses |
|---|---|---|---|---|---|
| B-1 | 4 (B1-05, B1-06, B1-08, B1-09) | 4 (the same) | none | none | none |
| B-2, B-3, B-6, O | 0 | 0 | none | none | none |

Both twins of B1-05 carry the capping flag `K1_ABSTAINED_MAJORITY:world:minus`: 101 of the 200 `minus` samples were
abstentions. No timeout and no missing certificate occurred, so every component is comparable. No 0.4.1 detection or
clean pass was lost.

Under 0.4.1 the B-1 table is 8 of 12 detections and 7 of 12 clean passes, so B-1 FAILS under 0.4.1 (P 10/12, C 2/12,
N 0/12; declared worlds that may contain what the error exploits). The four gained pairs change the B-1 verdict between
the versions. The other in-scope tables are identical under the two versions.

## 3. Baselines (same files, 0.5.0 certificates)

| Baseline | B-1 det / clean | B-2 | B-3 | B-6 |
|---|---|---|---|---|
| Truth_Gate 0.4.1 (full table) | 8 / 7 | 7 / 8 | 8 / 8 | 10 / 12 |
| Flag everything | 12 / 0 | 12 / 0 | 10 / 0 | 12 / 0 |
| Noise probe only (detection) | 7 | 5 | 6 | 0 |
| Declared streams only (detection) | 11 | 7 | 7 | 10 |

Flag everything fails every class on the clean pass. 18 of the 37 in-scope detections carry a flag of the noise probe,
which needs no declaration; none is in B-6. In two of them the noise flag does not reflect the planted error: in B1-02
it fires because the faulty twin rarely holds in `plus` (7.4), and in B1-07 the fixed twin holds on noise at the same
rate (7.3); both rest on declared flags as well. In B2-08 to B2-11 the fixed twins carry the noise flag too, at lower
rates. Every B-6 detection came from the declared `minus` world or control. No detection was K2-only. From the 0.4.1 certificates the noise-only line is 4 / 5 / 6 / 0 and the declared-only line 7 / 7 / 7 / 10.

## 4. Awareness of the world author (descriptive)

Two readers classified each world log as P (the log names how `minus` could still support the claim), C (considered,
nothing left in `minus`) or N (no sign); the resolved level is the higher reading. Batch 03 (15 worlds) stopped at a
usage limit after writing its skeletons and before writing its log; per P-4 these count as P in the resolved reading and
are shown separately.

| Level (resolved) | In-scope pairs | Detected (generic / declared) | Clean passes |
|---|---|---|---|
| P | 42 (of which 14 without a log) | 34 (16 / 18) | 36 |
| C | 4 | 3 (2 / 1) | 3 |
| N | 0 | – | – |

Per class (resolved): B-1 P 10, C 2; B-2 P 10, C 2; B-3 P 10; B-6 P 12. The readers disagreed on 8 worlds. Reader 1
alone has N for two B-6 pairs (B6-06, B6-12); reader 2 alone has N for one B-2 pair (B2-03). Out of scope (resolved): P 5,
C 1. Unlike Phase B, where no pair read C was detected (Phase B report, section 3), three of the four in-scope pairs
read C were detected (B1-04, B1-06, B2-10). Limit I-4 applies
unchanged: declared detections depend on the declared worlds containing what the error exploits.

## 5. Overlap with Phase B, new sources, Phase B next to Phase C (descriptive)

19 of the 46 in-scope pairs overlap a Phase B case (same source, mechanism tag and statistic family): B-1 4, B-2 6,
B-3 4, B-6 5. No class has more than half overlapping, so the wording of §1 is not triggered (B-2 is exactly half).
Addendum-source pairs: B-1 6, B-2 4, B-3 4, B-6 4, each at least the required 4.

Without the overlapping pairs (no class keeps 10 pairs, so there is no verdict): B-1 8 of 8 detected and 8 of 8 clean;
B-2 5 of 6 and 2 of 6; B-3 4 of 6 and 5 of 6; B-6 5 of 7 and 7 of 7.

| Class | Phase B (gate 0.4.0; Phase B report, sections 1 and 3): det / clean of 12, verdict, awareness P / C / N | Phase C (gate 0.5.0): det / clean, verdict, awareness P / C / N |
|---|---|---|
| B-1 | 7 / 7, FAILS, 12 / 0 / 0 | 12 / 11 of 12, HOLDS, 10 / 2 / 0 |
| B-2 | 7 / 11, FAILS, 8 / 1 / 3 | 7 / 8 of 12, FAILS, 10 / 2 / 0 |
| B-3 | 8 / 8, FAILS, 10 / 2 / 0 | 8 / 8 of 10, FAILS, 10 / 0 / 0 |
| B-6 | 11 / 11, HOLDS, 11 / 0 / 1 | 10 / 12 of 12, HOLDS, 12 / 0 / 0 |

In both phases P counts declared worlds that may contain what the error exploits. The briefs, worlds, criteria, the size
rule and the gate version all differ between the phases, so the two columns are not a comparison. The B-1 difference
coincides with the gate version: on the Phase C files 0.4.1 gives B-1 8 / 7 (section 2). The temporal and grouped
leakage subtypes L3.1 and L3.2 were detected in 1 of 4 pairs in Phase B and 0 of 4 in Phase C.

## 6. Abstention (0.5.0, descriptive)

Share of samples on which the criteria abstained, over the K1 streams (P-7): B-1 faulty 211 of 4800 (0.044), fixed 187
of 4800 (0.039); every other class 0. Phase B's files under 0.5.0 (the official R1 certificates): B-1 faulty 0.094,
fixed 0.0965; B-2 fixed 0.0048; others 0. Abstention is again confined to B-1, where the allowed guard "empty selection
returns `None`" applies, and it is the only source of the 0.4.1 UNDEFINED components.

## 7. Misses and failed clean passes (interpretation, written after the run)

Rates are HOLDS counts out of 200 samples per stream from the 0.5.0 certificates.

**7.1 Error too small in the declared worlds at this size (pre-registered label, P-7 item 5, P-8 item 4).** Eleven
misses: the faulty twin is WEAK, carries no expected flag, and holds in `minus` at most at the bound 0.0808. In-scope:
* B2-03 (oversampling before the split, 2/200);
* B2-04 and B2-05 (random folds on a time series, 1/200 and 0/200);
* B2-06 and B2-07 (records of one patient or participant on both sides of the split, 0/200 and 12/200);
* B3-02 and B3-03 (ratio statistics whose numerator does not scale through the origin, 2/200 and 0/200);
* B6-04 (animals counted as replicates instead of cages, 7/200).

Out of scope: O1-A, O1-B and O3-B (0/200 each). In these pairs the faulty criterion fails in `minus` at or near the
nominal rate. What the error exploits was not present in the declared worlds strongly enough to show at this size; the
criterion did not hold in `minus` unnoticed. In B2-03, B2-05 and B2-07 the model in both twins (a ridge logistic
regression, ordinary least squares) also lets little leak, as their criterion authors noted before the run (CASE.md
§7): these misses depend on that choice as well as on the worlds. Five of the seven KAP23 pairs in B-2 are here; the subtypes L3.1 and L3.2
were also mostly missed in Phase B (section 5).

**7.2 Misses in which the gate rejected the faulty criterion with a flag outside the list.** B6-06 and O3-A: the
faulty twin is NOT_FALSIFIABLE through `K2_HOLDS_UNREACHABLE` (it never holds in `plus`: 0/200, and also 0/200 in
`minus` and under the controls; on the noise probe B6-06 holds 6/200, O3-A 0/200). That flag is not an expected flag, so
by the pre-registered rule both are misses.
* B6-06: the declared `plus` world gives the patients a mean practice slope of −8 ms per session against −16 for the
  healthy group. The faulty pattern (healthy slope significant, patients' not) therefore never occurs, because the
  patients' own slope is also significant.
* O3-A (out of scope): the off-by-one shift moves the signature mask to adjacent rows, which carry no signal in these
  worlds.

**7.3 Failed clean passes (7).** Each was reported by the criterion author from the pre-checks of the fixed criterion
before the fidelity audit (CASE.md §5 and §7). By rule, a weak fixed criterion is recorded, not bent.
* **B2-08, B2-09, B2-10, B2-11 (VAR06, L1.3; nested cross-validation on 40 samples).** The fixed twin holds in `minus`
  47, 18, 31 and 46 times, and on the noise probe 65, 25, 50 and 39 times. The claim's accuracy or AUC threshold is
  reached by chance at 40 samples. The B2-08 author measured a standard deviation of 0.114 for the nested accuracy on
  `minus` samples, with P(accuracy ≥ 0.60) = 0.24. The failure comes from the threshold of the claim at this sample size,
  which the fixed criterion keeps. It does not come from structure in the worlds: the noise probe has none. The faulty
  twins hold more often in the same streams (`minus` 86, 26, 89, 132), and their detections stand. The fixed twins,
  however, carry the same expected flags at lower rates; in B2-09 the declared streams are nearly equal (`minus` 26
  against 18, control 23 against 20) and only the noise rate differs markedly (67 against 25). The fifth L1.3 pair, B2-12
  (AMB02), passes.
* **B3-04.** Fixed holds in `minus` 32 times and under the control 42 times: the claim's threshold (a coefficient of at
  least 0.25) has a sampling standard deviation of about 0.3 at this size (author's pre-check: 16% and 19%). The faulty
  twin's declared flags come at similar rates (`minus` 46, control 53); only its noise flag (65 against 0) is absent from
  the fixed twin.
* **B3-12.** Fixed holds in `minus` 23 times: the months carry autocorrelated variation that the ordinary t test of the
  claim does not model (author's pre-check: 11.7%). The faulty twin holds in `minus` 25 times. Its detection rests on
  `K2_HIGH_SIZE`, which the fixed twin carries at nearly the same rate, so this detection does not show the planted error.
  It stays in the table (PB §7).
* **B1-07.** Fixed holds on the noise probe 78 times: the orientation index (V − H)/(V + H) is heavy-tailed on N(0, 1)
  noise, where sums near zero or negative occur (author's pre-check: 99/200). The faulty twin carries the same noise flag
  (81/200). Its detection also rests on `K2_HIGH_SIZE` and the control flag (`minus` 200/200 against 2/200 for the fixed
  twin), which the fixed twin does not carry. Phase B's B1-02 failed for the same reason (Phase B report, 5.4 and
  section 7).

**7.4 Notes on single pairs.**
* **B1-02.** The documented error (one 12-month scan both defines the group and starts the second-year change) biases the
  group difference against the direction the claim asserts. The criterion author recorded this before the run. The
  faulty twin holds in `plus` only 10 times (fixed: 200), in `minus` 0 times and on noise once. The gate flags it for not
  separating `plus` from the other streams (`K2_NO_SEPARATION`, `K4_CONTROL_ALSO_HOLDS`, `K5_HOLDS_ON_NOISE`), not for
  holding where the claim is false. The detection is real by the rule, but the error shows as lost power, not as false
  holds.
* **B1-09** was repaired at the fidelity audit: the fixed twin now splits participants instead of sessions. The brief
  author's `PRIVATE.json` still describes the superseded session split in its estimand wording (auditor's note; it names
  the same quantity).
* **B-2 guard expression.** The repair round changed a guard expression (`-(n)//k`) in B2-01, B2-06 and B2-10. The same
  expression remains in six pairs that passed the audit (B2-02, B2-03, B2-08, B2-09, B2-11, B2-12), where both twins'
  guards behave alike and the guard is an allowed one. They were not changed: PB §5.3 repairs only pairs with a "no"
  (P-6).
* **The designer's brief check (step 2)** did not catch the item-(h) defect of B3-10 that the fidelity audit found (a
  meaning text stating the column order). B3-10 and B3-07 (sizes) were dropped, leaving B-3 with 10 pairs.
* **Size ratios** (RESULTS §9). Most sources state no size. Four VAR06 pairs use 1000 of 6000 genes (0.17) and O3-A 1000
  of 12 558 to 22 283 probe sets (0.045 to 0.080), both reduced to the cap of 1000 per axis. B2-01 uses 30 of the source's
  90 indicators (0.33), a choice of the brief, not the cap, which the fidelity audit accepted as within the source's
  models. B6-08 uses 4 tanks per treatment against the source's 2 (ratio 2.0). The rest are about 1.

Section 7 and sections 1, 3, 4, 5 and 8 were corrected after the post-run audit (section 9). The first version said
that the noise probe "found" 18 detections, gave the declared worlds as the only cause of the 7.1 misses, omitted B2-01's
size ratio and the fixed twins that carry the same expected flags (7.3), attributed every all-zeros abstention to the
zero-variance guard, and cited no source for its Phase B statements. The pre-registered table in section 1 is unchanged.

## 8. Limits

* **Who wrote the cases.** Every role is a Claude model. The world author, Fable, is a different Claude model line, not a
  different vendor or family (I-6). The brief and criterion authors, auditors and designer belong to the line that wrote
  the gate, and they read its documentation. No human domain reader was available.
* **Awareness (I-4).** In the resolved reading, 47 of 52 declared worlds may contain what the error exploits (P), 15 of
  them by the no-log rule P-4. The verdicts describe what the gate does when the declared worlds anticipate the artefact.
  They do not show that it finds errors nobody anticipated.
* **B-3 briefs** name the adjusted-for quantity in the claim, as the estimand rule requires (I-6). The B-3 shares are read
  with this in mind.
* **Sizes and sources.** Data were capped at 1000 per axis; four VAR06 pairs and O3-A are reduced to the cap, and B2-01
  uses a third of its source's indicators (7.4). B-2 rests on
  three read sources, seven pairs on KAP23 (I-5). 19 of 46 in-scope pairs overlap Phase B.
* **10 to 12 pairs per class.** With 12 pairs a class needs at least 10 of 12 on both detection and clean pass (10 of 12
  gives the lower bound 0.601). B-6's detection, 10 of 12, sits on this edge: one detection less would change its
  verdict. The intervals are the result; the verdicts summarise them.
* **The B-1 verdict depends on 0.5.0's abstention rule** (section 2): under 0.4.1 the same files fail. The pre-registered
  primary table is the 0.5.0 one.
* **No fixed file is FALSIFIABLE.** Every certificate carries `K5_INCONCLUSIVE:zeros`: allowed guards make the criteria
  abstain on the all-zeros probe (zero variance; in B1-01, B1-03, B1-12 and O3-B an empty selection, because no unit
  passes the claim's cut on all-zero data), so a clean pass is WEAK at best. As in Phase B, this limits what a
  clean pass can show.
* **Process events.** These are recorded in `REVISIONS-post-freeze.md` (P-1 to P-8): the shared context-mode store and
  the session scratchpad; usage-limit stops of the world authors (attempt 1 entirely, batches 03 and 04 in attempt 2) and
  of the auditors; batch 03 without a world log; one repair round with four repaired pairs and two dropped.

## 9. Post-run blind audit (PREREG_PHASE_C §7, as PB §7)

A fresh agent (Claude Opus 5.5, the line that wrote the gate) that wrote nothing in this evaluation answered three
questions per pair (`run/POSTRUN_AUDIT.json`, `run/POSTRUN_AUDIT.md`; instructions in `POSTRUN_AUDIT_INSTRUCTIONS_C.md`).
It was started by a separate Claude session that does not load the designer's notes, and it worked only on read-only
copies of the frozen cases, the certificates, the record, the public documentation and the first version of this
report. It ran no gate. Its transcript shows one model, no other agent, no context-mode call, reads only inside its task
folder, and writes only its two outputs and scratch files; the copies were unchanged afterwards (SHA-256).

| Class | (i) detection follows from the error: yes / no / n/a | (ii) failed clean pass comes from the skeleton: yes / no | (iii) sign that a brief steered the worlds: yes |
|---|---|---|---|
| B-1 | 12 / 0 / 0 | 0 / 1 (B1-07) | 0 |
| B-2 | 7 / 0 / 5 | 0 / 4 (B2-08 to B2-11) | 0 |
| B-3 | 7 / 1 (B3-12) / 2 | 2 (B3-04, B3-12) / 0 | 1 (B3-09) |
| B-6 | 10 / 0 / 2 | – | 0 |
| Out of scope | 2 / 0 / 4 | – | 2 (O1-B, O2-A) |

* **(i)** One detection does not follow from the planted error: B3-12, whose only expected flag `K2_HIGH_SIZE` the fixed
  twin carries for the same reason (7.3). The auditor qualifies five more "yes" answers. In B2-08, B2-10, B2-11, B2-09 and
  B3-04 the fixed twin is also NOT_FALSIFIABLE with the same expected flags, at a third to a half of the faulty rate in
  the first three, at nearly equal rates on the declared streams in B2-09 and B3-04. Under a strict reading ("would the
  pair be detected with the fixed criterion?") these five and B3-12 would count as detected without the error: 4 of B-2's
  7 detections and 2 of B-3's 8. *Post hoc, not a pre-registered number;* none of them is in B-1 or B-6, and the table is
  unchanged. Two B-1 detections reach the error by another route: B1-02 through lost power in `plus`, B1-07 through its
  declared flags, while its noise flag is shared with the fixed twin.
* **(ii)** Of the seven failed clean passes, five come from the fixed criterion, which is the documented correction but
  keeps the claim's rule: B1-07 (a ratio index on sign-indefinite noise) and B2-08 to B2-11 (a threshold without a test at
  40 samples, failing on noise as well). Two come from the skeleton: B3-04 (little kidney variation against the liver
  noise) and B3-12 (autocorrelated, seasonal residuals under an ordinary t test).
* **(iii)** Beyond the awareness already recorded (I-4, I-6), three pairs show steering:
  * In B3-09, a key read only by the faulty criterion (`venous_o2_content`) was made consistent with the measured cardiac
    output. It supports `K2_HIGH_SIZE` (34/200); the detection would stand without it (noise 199/200, control 200/200).
  * In O2-A the world author kept a treatment effect on the willingness-to-pay outcomes, read only by the faulty rule, in
    `minus`. The detection (65/200) rests entirely on it.
  * In O1-B a control was built around a key read only by the faulty criterion. The pair was missed.

  Phase B's auditor flagged the overlapping O1a and O2a cases for steering too. These pairs stay in the table.
* **Statements of the first version** that the files contradicted or did not support (five, plus one omission): B2-01's
  size ratio; "found by the noise probe" for B1-02 and B1-07; the declared worlds as the only cause of three 7.1 misses;
  the zero-variance guard as the only cause of the all-zeros abstentions; Phase B statements without a source; and the
  fixed twins that carry the same flags. The designer checked each against the files and corrected the text (see the
  end of section 7). The pre-registered table in section 1 is unchanged.

## 10. Correction notes from the validity audit (2026-11-17)

A post hoc validity audit of the B-2 and B-3 pairs ([`../validity_audit_b2b3/`](../validity_audit_b2b3/README.md)) was
made by a fresh agent that had not seen this report. The designer rechecked the points below with the scripts in
`../validity_audit_b2b3/designer/`. They change explanations, not the pre-registered result.

- **Section 1.** The B-2 clean-pass Wilson lower bound is 0.431, not 0.432 (8 of 12 gives 0.431492). Corrected in the
  table.
- **Section 7.1, B2-03, B2-06 and B2-07.** The statement that what the error exploits "was not present in the declared
  worlds strongly enough" does not fit these three pairs. The structure is present, and the error raises the faulty
  statistic on the gate's `minus` samples, but the claim's threshold sits above the faulty twin's 95th percentile and
  decides:
  - B2-03: balanced accuracy mean 0.597 against 0.502 for the fixed twin; 95th percentile 0.629 against the threshold
    0.65.
  - B2-06: AUC mean 0.643 against 0.499; 95th percentile 0.703 against 0.75.
  - B2-07: the audit reports a mean correlation of 0.115 against −0.042 (not rechecked).

  The text fits B2-04, B3-02 and B3-03, where the audit finds the structure missing or weak. B2-06 uses the same ridge
  logistic model as B2-03 and belongs in the list of model-dependent misses. The post-run audit's "the copies carry
  almost no weight" (B2-03) and "gave no lift" (B2-06) are contradicted by these numbers.
- **Sections 7.3 and 9, B3-12.** The fixed twin's excess size comes from the autocorrelated waves, not the season. On
  2000 `minus` samples it holds:
  - 0.107 as declared;
  - 0.188 without the season term;
  - 0.017 without the waves.

  The season makes the ordinary t test more conservative. "Autocorrelated, seasonal residuals" should read
  "autocorrelated residuals".
- **Further points.** These are the audit's readings, not rechecked by the designer; see `AUDIT_PHASE_C.md`, Part 2:
  - B3-04 and B2-08 to B2-11 share one mechanism (a threshold without a test, with a null spread comparable to the
    threshold), yet section 9 files the first under the skeleton and the others under the claim's rule.
  - "Their detections stand" (7.3) holds for B2-08, B2-10 and B2-11. If the fixed twin's 95th percentile were the
    threshold, the faulty twin would hold in `minus` 27, 28 and 48 times of 200, where a flag needs 18. It does not
    hold for B2-09 (10 of 200).
- **Its summary (post hoc).** No miss and no failed clean pass of B-2 or B-3 is attributed to the gate's behaviour:
  - Misses: 3 from size (above), 3 from worlds without the structure (B2-04, B3-02, B3-03), 1 mixed (B2-05).
  - Failed clean passes: 6, all from fixed criteria that are not clean tests on the declared worlds. The same six pairs
    are the detections that do not show the error.
