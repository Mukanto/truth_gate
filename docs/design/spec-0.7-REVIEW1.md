# Review 1 of spec 0.7 (Truth_Gate 0.5), DRAFT v1

Blind review. Read: `docs/design/spec-0.7.md`, `docs/SPEC.md` (0.3 core, 0.4 and 0.5 deltas), `docs/design/spec-0.6.md`,
`docs/GATE.md`, `evaluation/phase_b/REPORT.md`, and `truth_gate/checks.py`, `stats.py`, `study.py`, `manifest.py`,
`certificate.py`, `minus.py`. For finding 1 I also read the UNDEFINED counts out of the Phase B 0.4.0 certificates
(`evaluation/phase_b/run/certs/v040/*/*.json`, read-only, the gate was not run). Nothing else was modified.

Counts: **3 blocking, 5 major, 7 minor** (15 findings).

---

## Blocking

### 1. At the default threshold the rule rescues one of the ten motivating studies (blocking, needs an author decision)

Passage (section 0 and 2.1): "K1 made five flagged faulty criteria and five fixed criteria UNDEFINED ... below a
threshold on the rate of UNDEFINED outcomes, K1 does not decide the verdict"; "`Targets.max_undefined` ... default
`0.05`", range `[0, 0.5]`.

Why it matters. The UNDEFINED rates in the 0.4.0 certificates (HOLDS-defining stream, u out of 200) are:

| File | u on `minus` | u on `plus` | rescued at 0.05 | at 0.2 | at 0.5 |
|---|---|---|---|---|---|
| B1-04 faulty | 173 (0.865) | 0 | no | no | no |
| B1-04 fixed | 137 (0.685) | 0 | no | no | no |
| B1-05 faulty | 171 (0.855) | 3 | no | no | no |
| B1-05 fixed | 166 (0.83) | 12 | no | no | no |
| B1-06 faulty | 32 (0.16) | 0 | no | yes | yes |
| B1-06 fixed | 71 (0.355) | 2 | no | no | yes |
| B1-07 faulty | 4 (0.02) | 0 | **yes** | yes | yes |
| B1-08 faulty | 68 (0.34) | 0 | no | no | yes |
| B1-08 fixed | 75 (0.375) | 0 | no | no | yes |
| B2-09 fixed | 6 (0.03) | 17 (0.085) | no (plus) | yes | yes |

At the default, 1 of 10 changes; at the range maximum, 6 of 10. B1-04 and B1-05 (both faulty and fixed) cannot be
reached by any legal value. So the draft's own Section 0 motivation is not served by its own rule, R2 will show
almost no change, and the author is deciding on the wording "a threshold" without knowing this. The cause is that the
UNDEFINED outcomes are not rare noise: they are the guard's normal behaviour in `minus` ("empty selection"), correlated
with the absence of an effect. Excluding them also biases the remaining defined samples toward "an effect was found"
(selection on the outcome), which raises the `minus` rate of a well-behaved fixed criterion; the threshold is the only
protection.

Fix. Put the table above (or a sentence with the counts) into section 0 as the known expected effect, labelled
development data, and ask the author to confirm one of: (a) accept that 0.5 only repairs the low-rate cases
(B1-07-like) and say so in the user text; (b) choose a different treatment of UNDEFINED on `minus` and `null`, e.g.
count it as not-HOLDS over `n` (no claim is made, so no false positive; this is already the 0.4 rule for premises,
controls and probes) with the rate shown, and keep exclusion only for `plus`; note that (b) would lose the B1-04-like
detections that rest on "27 of 27 defined samples hold"; (c) a verdict-level treatment (finding 6, alternative C).
The draft must not freeze before the author has seen this.

### 2. Hard UNDEFINED outcomes (exceptions, generator failures, external-process failures, BAD_RETURN) become tolerated (blocking)

Passage (1, 2.2): "`u_s` UNDEFINED" with no distinction of cause; section 2.2 rule 1/3 apply to every UNDEFINED. Section 2.3
last bullet and section 0 say only "UNDEFINED samples are left out".

Why it matters. In the engine `UNDEFINED` is produced by (i) a deliberate `None`, (ii) an exception in `fn`
(`evaluate_criterion`), (iii) an exception in `generate` (the sample has `data=None`, so every criterion is UNDEFINED
on that index), (iv) a wrong return type (`BAD_RETURN`, spec 0.3 interpretation 5: "Its UNDEFINED outcomes already
trigger K1 in plus/minus"), (v) external programs: after `ExternalDied`/`ExternalTimeout`/`ExternalProtocolError`
"every later request to that argv is UNDEFINED" and `docs/GATE.md` says this "reaches the verdict through K1"
(spec 0.6 section 6, GATE.md study note `EXTERNAL_DIED`). The author's decision (and the Phase B evidence) concerns (i)
only. Under the draft, a world generator that crashes in 5% of samples, a criterion with a KeyError bug in 5% of
samples, or an external criterion that dies at sample 191 of 200 all keep K1 quiet and are reported with an information
flag. The last one breaks a documented guarantee, which the draft says nothing about. The existing `errors` record
already separates exception names per stream, so the information is available.

Fix. Define "soft UNDEFINED": a deliberate `None` (including a pattern UNDEFINED and a missing component caused by the
criterion returning `None`). Everything else is "hard UNDEFINED" (exception in `fn`, `generate` failure, `BAD_RETURN`,
any `External*` error, a missing key in a dict return). Rule: `r_s` and the tolerance are computed over soft
UNDEFINED only, and any hard UNDEFINED on a K1 stream gives `K1_UNDEFINED` exactly as in 0.4. Add the field
`counts[stream].hard_undefined`, one test per cause, and a note in GATE.md. If the designer prefers to keep one
category, then state the loss explicitly (a K1 hole for EXTERNAL_DIED) and require `EXTERNAL_DIED` to force
`K1_UNDEFINED`.

### 3. Statistics and flags are unspecified when K1_UNDEFINED is raised; R1 with `max_undefined = 0` cannot be met as written (blocking)

Passage (2.2 rule 1 vs 3): "If `r_s > max_undefined` ... `K1_UNDEFINED` ... Otherwise ... 3. In every statistic that reads a
K1 stream ... counts `h_s` HOLDS out of `d_s`. Rule 1 and the range of 2.1 guarantee `d_s >= n_s / 2 > 0`." And R1: "with
`max_undefined = 0` ... for every study ... same verdict, flags and counts".

Why it matters. In the code (`_component_record`) all flags are computed for every component, also for a component that
ends up UNDEFINED, and they are written to the certificate (`flags`, `bounds`). Rule 3 is stated only for the case
where rule 1 did not fire. When K1 fires, `d_s` can be 0 (Wilson with `n = 0` gives (0, 1); `rate` divides by n) or
tiny, and an implementer must choose between the 0.4 computation (UNDEFINED as not-HOLDS over `n`) and the new one.
Only the first makes R1 true for `max_undefined = 0` ("the same flags").

Fix. Add to 2.2: "When rule 1 fires for any K1 stream of the component, all statistics, flags, bounds and counts of
that component are computed as in 0.4.1 (UNDEFINED counts as not-HOLDS over `n_s`), and `defined`, `undefined_rate`
are still recorded. The defined-count computation of rule 3 applies only when no K1 stream exceeds the threshold."
State that `bounds` of a K1 stream are on `n` in that case, and say which basis each component's bounds used (see
finding 15).

---

## Major

### 4. Selective `None` can hide false positives; the information flag is not strong enough (major)

Passage (2.2 rule 2, 2.5): "Information flags never enter a verdict rule"; "The verdict is computed from the primary
flags only." Section 2.5 raises `K1_UNDEFINED_SENSITIVE` (C) as information.

Why it matters. A criterion (or a hurried author) that returns `None` on up to `max_undefined` of the `minus` samples
that would HOLD (a false positive) lowers the `minus` rate by up to `max_undefined` in absolute terms (for example a
true rate 0.15 shows as 0.105), and the same on `null`; returning `None` on `plus` samples that would FAIL raises the
`plus` rate and so improves every `SL(X, plus)`. The draft's bound ("move any rate by at most r/(1-r) <= 0.0527") is
a bound on the shift, not on the damage: 0.05 absolute is of the order of a Wilson half-width at n = 200 (about 0.045
at p = 0.05, z of about 2.7) and several half-widths at larger n, so it can decide `K2_HIGH_SIZE`, `HIGH_RATE:world:null`
and `K2_NO_SEPARATION`. The sensitivity flag would show it, but only as information, and the verdict stays
FALSIFIABLE; GATE.md users reading a green exit code never see it. Also `max_undefined` is declared by the same author
whose criterion is evaluated, up to 0.5.

Fix. Make `K1_UNDEFINED_SENSITIVE` a **capping** flag (WEAK). This is safe for the evaluation (a clean pass is
FALSIFIABLE or WEAK) and costs nothing in the case it exists for. Print every non-default `max_undefined`, and every
K1 information flag, in the CLI/CI table (not only in the JSON). Reduce the upper limit of `max_undefined` (0.2 is
enough for every case in finding 1 that a rate rule can reach and still lets the author pick) or require the value to
be recorded in `known_limitations` when it exceeds the default. Add an adversarial test to section 5: a faulty criterion
with a 0.15 `minus` rate that returns `None` on part of the holding samples, which must not end FALSIFIABLE.

### 5. The sensitivity analysis (2.5) has unspecified or one-sided parts (major)

Passages: "UNDEFINED counted as HOLDS on `minus` and `null`, and as FAILS on `plus` (all over `n_s`). If this
recomputation raises a mandatory flag that the primary computation did not raise ..."

Why it matters, one item each:
* Which flags are recomputed: the list of 2.3 includes capping flags (`K2_LOW_POWER`), and the second sentence says
  "mandatory". `K2_LOW_POWER` and `HIGH_RATE:*` (mandatory by prefix) must be decided by name.
* Suppression: the primary flags after cascade suppression (plus never holds) and after identical-minus suppression
  (`suppressed_minus`) are what is compared; the draft does not say that the recomputation applies the same two
  suppressions, so for `K2_MINUS_IDENTICAL` studies it would raise flags the engine deliberately drops.
* Direction: the analysis only asks "could the left-out samples make it worse", but exclusion can also make a clean
  criterion look worse than counting UNDEFINED as not-HOLDS (the 0.4 treatment of every other stream). That case (a
  mandatory flag raised only because of the exclusion, e.g. `K2_HIGH_SIZE` from h/d) is not reported, although it is
  exactly the false-NOT_FALSIFIABLE risk finding 1 describes.
* Joint worst case: all three K1 streams are moved at once; that is fine for an information/capping flag but should
  be said (it can flag more often than any single stream could cause).
* Bonferroni: the recomputation adds comparisons outside the family `m`; say that they use the same `a` and are not
  counted, because they never change a verdict flag (if finding 4 is adopted, they cap at WEAK).
* The certificate field `k1_sensitive` should hold the flag names as strings in a sorted list, and the draft should say
  whether `K1_UNDEFINED_SENSITIVE` appears on a component whose primary flags already include the same mandatory flag
  (it should not; the text says "did not raise", fine, but name the post-suppression set).

Fix. Specify the flag set (all mandatory flags plus capping `K2_LOW_POWER`), the suppression order, and add the
reverse report `K1_UNDEFINED_EXCLUSION_DECIDES` (info): the flags raised by the primary computation but not by the
"UNDEFINED counts as not-HOLDS over n" computation (0.4 style). If that is too much, at least record the 0.4-style
counts so a reviewer can compute it.

### 6. The 0.05 default and the point-rate rule are not justified as written; alternatives are not discussed (major)

Passage (2.1): "The default equals the default declared size (`targets.size = 0.05`): leaving out at most that share ...
can move any rate on a K1 stream by at most `r / (1 - r) <= 0.0527`, the same order as the size tolerance the gate
already grants."

Why it matters. (a) `size` is a false-positive rate on `minus`; `max_undefined` is a data-loss fraction on three streams.
Equal numbers are a coincidence, not a reason. (b) The bound is loose and mislabelled: the shift between the primary
rate h/d and the unfavourable (h+u)/n is u(d-h)/(nd) <= r(1-p), and between h/d and h/n it is r p; so at most r. (c) The
tolerance does not scale with the statistical resolution: the gate's `K2_HIGH_SIZE` margin shrinks with n, the
allowed shift stays 0.05. (d) In Phase B the designer knew the rates before choosing 0.05 (finding 1, 11); that
should be said so the value is not presented as independent of the data. (e) A point rate is reasonable for the bias
argument (the left-out samples are exactly counted), but the draft does not say that the population rate of
UNDEFINED is not estimated or used.

Alternatives to state and reject (or adopt):
* A: default 0 (the 0.4 rule), opt-in per study. Zero compatibility risk, no pre-registration burden, but nobody
  benefits unless they read the guide.
* B: an absolute count, e.g. `u_s <= ceil(max_undefined * n)` fixed as an integer in the certificate (removes float
  comparison issues, finding 10).
* C: no threshold, but treat the K1 streams as bounds: compute the verdict under the favourable and the unfavourable
  assignment; if they differ, cap at WEAK (partial identification). It is more principled than a threshold and
  needs the machinery of 2.5 anyway; it would also not hide a high-rate case (it stays WEAK, not UNDEFINED).
* D: tie the threshold to the Wilson half-width at the study's n.

Fix. Replace the justification with the shift bound r (or drop it), state that 0.05 is a design choice informed by
the Phase B counts, and add the alternatives with one line each of why they are not chosen.

### 7. Compatibility claim (section 4) and regression criterion R1 are not testable as written (major)

Passages (4): "same verdict, flags, counts and bounds as with 0.4.1 (the certificate differs in `tool_version`,
`spec_version`, the recorded target, the per-stream `defined`/`undefined_rate` fields and the two renamed texts where
they occur)". (R1): "The list of studies whose result differs at the default must equal the list of studies with such
UNDEFINED outcomes."

Why it matters.
* "Such UNDEFINED outcomes" is read either as "any UNDEFINED on a K1 stream" or "UNDEFINED within the threshold". The two
  lists differ: a study above the threshold is UNDEFINED in 0.4.1 and in 0.5.0 (same result, so not in the first
  list). The equality is true only if "result" includes the information flag (any component with 0 < r <= threshold gets
  `K1_UNDEFINED_RATE`); the draft excludes information flags elsewhere (expected-flag lists). Define it.
* Section 4 omits: `known_limitations` always gains a sentence (certificate differs for every study), the premise-map
  rounding if rates change (finding 14), and, in 0.4.1, K1-stream outcomes whose component is UNDEFINED.
* R1's `max_undefined = 0` "set by a test harness, not by editing the files": `Targets` is a frozen dataclass built from
  the manifest or study file; the mechanism (environment variable, API argument, monkeypatch of the default) is
  unspecified, and a variable that changes certificates is a hidden knob. Also at `max_undefined = 0` the
  certificate field `max_undefined` (0 vs 0.0 for the hash, finding 10) differs from 0.4.1 by definition, so the field
  list that R1 compares must be given.
* The regression baseline is 0.4.1, the Phase B table is 0.4.0 (`R2`); state that 0.4.0 and 0.4.1 give the same
  verdicts on the 108 files (the Phase B report ran 0.4.0 and 0.3.0), or compare both.
* Deterministic studies are unchanged by rule 2.4, so R1 should list them as a separate check.

Fix. Define: "result" = per component the verdict, the sorted flag list and the `holds`/`undefined`/`n` counts and the
`bounds`; the comparison ignores `tool_version`, `spec_version`, `known_limitations`, `study.targets.max_undefined`
and the new per-stream fields. State the set explicitly: `D` (differs at default) = components with 0 < r_s <= threshold on
a K1 stream, no hard UNDEFINED (finding 2), non-deterministic; require D exactly, and require identical results elsewhere
including components above the threshold. Give the harness mechanism (a documented, certificate-recorded keyword of
`run_gate`, for example `max_undefined_override`, or a generated copy of the study with the target set).

### 8. Evaluation section: R3 and the Fable claim (major)

Passages (6, R3): "the world author is **Fable** ... a different model line from the Opus and Sonnet models ... **but from the
same vendor and family** ... Its design choices (reuse of the 54 Phase B briefs or new briefs, sizes) are fixed in
that document, not here."

Why it matters.
* **Reuse of Phase B briefs must be decided now.** The rule was designed after seeing those cases (R2 says so). A reuse of
  the 54 briefs, even with a new world author, is the same briefs with the same planted errors and the same Phase B
  awareness problem (the world author inferred the error in 45 of 54 briefs, report 6 and P-1); and any rule effect there
  is partly a result of the designer having seen them. An R3 on reused briefs is not external evidence of the 0.5 rule,
  only of the world-author change. Say now: new briefs, or reuse reported only as a development replicate.
* **What changed is only the world author.** Criterion authors, brief authors, auditors and designer remain
  Opus/Sonnet (the same family that wrote the gate). Fable from the same vendor supports at most "the result does
  not depend on which Claude model wrote the worlds"; it does not support "independent of the gate's authors" or any
  claim about errors that nobody anticipated. The sentence in the draft says this; the claims that R3 will make
  must be restricted in the spec: no use of the word "external" without the qualifier, and the model id and date of
  the Fable runs recorded.
* **Primary endpoint missing.** Since 9 of 10 UNDEFINED cases stay UNDEFINED (finding 1), a Phase C with the same
  guards will contain almost no component that the rule changes; the evaluation has no power for the claim the rule
  exists for. What must be fixed here: the primary comparison (paired 0.4.1 vs 0.5.0 on the same files: counts of
  UNDEFINED components, rescued detections and clean passes, new false clean passes and new NOT_FALSIFIABLE on fixed
  twins), the denominators, and a rule for "no change" outcomes (a reported null, not a failure of 0.5). What may be
  fixed in the PREREG: number of briefs, sources, class list.
* **R3 must forbid tuning**: `max_undefined` stays at its default (no value other than the frozen default is run
  after any Phase C result), and criterion authors are told to use or not to use guards in a way fixed beforehand
  (otherwise their choice of returning `None` decides the outcome).
* **Safety evaluation is missing.** Section 5 tests the gating but nothing evaluates gaming. Add R4 (not an
  external study): the adversarial criteria of finding 4 as a unit-level test set, written before the code.

Fix. State: Phase C uses new briefs only; endpoints as above; the "same family" sentence is repeated in the claims
the report may make; `max_undefined` is frozen at 0.05; R4 added.

---

## Minor

### 9. Mixed denominators and asymmetric treatment between K1 streams and other streams (minor)

Passage (2.2 last paragraph, 2.3): non-K1 streams keep "UNDEFINED counts as not-HOLDS"; K1 streams use `d_s`.

Why it matters. `SL(X, plus)` for a probe or control compares a numerator over `n` with the `plus` over `d`. For a
`plus` sample whose generation failed, all derived streams count the index as not-HOLDS while `plus` drops it.
Phase B shows the same guard acting differently on neighbouring streams (the zero-variance guard gives
`K5_INCONCLUSIVE:zeros` in 41 fixed files while a K1 stream would now be left out). The behaviour is deliberate in the
draft but undocumented as such. Fix: one paragraph stating the asymmetry and the reason (K1 is about the criterion being
defined where the study makes a claim; probes ask whether it holds when it should not) and that mixed bases are
accepted. Also premise_map (finding 14).

### 10. `max_undefined` value handling (minor)

Passages (2.1): "finite numbers with `0 <= max_undefined <= 0.5` ... bool ... NaN, inf, string".

* Certificate: `vars(study.targets)` records the value as given, so `0` and `0.0` give different bodies and `bool` is a
  Python int; convert to float and record the float, and say `True` is rejected (as `_is_real` already does for
  the other targets).
* The comparison `r_s > max_undefined` is `u/n > max_undefined` in IEEE division; `max_undefined * n` would give
  7.000000000000001 for 0.07 x 100. State the expression, or use integers (finding 6, alternative B).
* A `.py` study raises `StudyError` (verdict UNDEFINED, exit 3); a manifest gives exit 4. The draft says both; fine, but the
  manifest parser's `check_keys(t, "targets", [], ["power", "size", "alpha_family"])` and its number reader must add the key
  and its range, and the manifest `Targets(**manifest.targets)` construction at `manifest.py:627` sends it through
  `_validate`.
* `explain` and the init/scaffold templates should list the target.

### 11. R2 label and expectation (minor)

Passage (R2): "labelled **development data, not evidence**". Correct label. Missing: say that the default 0.05 was
chosen after the UNDEFINED rates were known, that raising it to rescue more of the ten files would be post-hoc fitting
(it is not allowed after R2 is read), and add the expected result from finding 1 (1 of 10 changes) as a plain
statement, so that R2 is not read as a rescue result. Also R2 and R1 use the same 108 files; say that R1 and R2 are the
same runs with different questions.

### 12. Implementation details that the draft leaves open (minor)

* `K2_FAILS_UNREACHABLE` in code is `minus.holds == minus.n` (spec 0.3: "zero non-HOLDS in `minus`"); the draft's "f_minus = 0"
  is the same on defined counts. Say "`h_minus == d_minus`" to match the code.
* Information flags are matched by exact name in `INFORMATIONAL_FLAGS` and by `explain`; `K1_UNDEFINED_RATE:<stream>`
  and `K1_UNDEFINED_SENSITIVE` need an informational prefix list (like `CAPPING_PREFIXES`), `explain` parsing of the
  colon-containing key, and a check that `component_verdict` (which tests the exact string `"K1_UNDEFINED"`) is not
  fooled by the new names.
* `StreamStats` currently carries `holds`, `undefined`, `n`; the K1-stream view for rule 3 is `StreamStats(h, 0, d)`
  while the certificate keeps the raw counts. State that the certificate `counts` are raw and `bounds`/flags use the
  view, and that the K6 reproducibility comparison is of the certificate body (it includes the new fields).
* The identical-minus analysis (`minus.analyse`) calls the criterion on `plus` and an extra paired `minus`; its flags
  and the `suppressed_minus` list are unchanged, correct, but the draft should say that the extra call is not a counted
  sample (it already says nothing about it).

### 13. Section 3 (names) claims and scope (minor)

Passage: "These texts end up in certificate bodies". The `StudyError` text is recorded (`load_error` keeps the message
for `StudyError`), but the leak-guard `PermissionError` message is not recorded (only the exception type name is), so
the claim is true for one of the two. Check before keeping it as a reason for a minor-version change. Also Section 0 says
"one rule", Section 3 adds a renaming: say plainly that these are two independent changes, and keep both out of R1's
comparison fields (a study with a leak attempt does not differ in its flags).

### 14. Other statements marked "unchanged" that change slightly (minor)

* `premise_map` rates are `plus.rate - st.rate` with `rate = holds / n`; with rule 3 the `plus` rate should be
  `h/d` for consistency with the SL it supports, or the map stays on raw counts (say which). It changes the certificate
  only when u > 0.
* K8: unchanged, and its own `defined`/`undefined` accounting (pairs with an UNDEFINED side counted apart) is
  consistent, but a component with 5% UNDEFINED now keeps its K8 flags where in 0.4.1 it was UNDEFINED; say so.
* Quick mode (n = 20 by default): 5% is one sample. The rule applies, the certificate is not certifiable, nothing
  else changes; say it. Deterministic mode: also not affected by `max_undefined` for `K1_UNDEFINED_SENSITIVE`; say so.

### 15. Documentation and user-visible effects (minor)

* `GATE.md` says K1 failure and `EXTERNAL_DIED` "reach the verdict through K1"; after the change those texts must be
  rewritten (see finding 2), and the CI summary and exit codes must say where the information flags appear (an
  information flag alone does not change the exit code).
* Certificate: add `bounds_basis` per K1 stream (`"defined"` or `"n"`) so that a third party can recompute the bounds
  from `counts` without reading the spec; the draft's "`bounds` of K1 streams are computed on the defined counts"
  is correct only when finding 3 has been fixed.
* Name space: the spec numbering (spec 0.7 for tool 0.5.0, spec 0.6 for 0.4.x) is consistent but worth one sentence in
  section 0 for readers.

---

## Verdict

**Needs another review round, after fixes.** Findings 1 to 3 must be resolved (1 requires an author decision, the
others are specification changes), and findings 4 to 8 change the design (capping sensitivity flag, hard/soft UNDEFINED,
the R1 definition, the Phase C reuse decision); the result is different enough from DRAFT v1 that a short targeted
second review is warranted before the SHA-256 freeze.
