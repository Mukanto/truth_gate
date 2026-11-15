# Fidelity audit, Phase C, class B-1 (12 pairs)

Blind fidelity auditor of class B-1, working from `AUDIT_PHASE_C.md` (PREREG_PHASE_C §5). I wrote none of the cases.
I called neither criterion on any data, ran no world, and ran no Truth_Gate. The case files were read as text only:
a helper script printed each faulty body and the faulty-to-fixed diff and checked the skeleton prefix and suffix, without
importing the study files.

**Result: 11 pass, 1 fails (B1-09, item (b)).**

| case | source | a | b | c | d | e | f | g | h | i | overall |
|---|---|---|---|---|---|---|---|---|---|---|---|
| B1-01 | MOR03 | yes | yes | yes | yes | yes | yes | yes | yes | yes | pass |
| B1-02 | MOR03 | yes | yes | yes | yes | yes | yes | yes | yes | yes | pass (see remark R1) |
| B1-03 | MOR03 | yes | yes | yes | yes | yes | yes | yes | yes | yes | pass |
| B1-04 | KRI10 | yes | yes | yes | yes | yes | yes | yes | yes | yes | pass |
| B1-05 | KRI10 | yes | yes | yes | yes | yes | yes | yes | yes | yes | pass |
| B1-06 | KRI10 | yes | yes | yes | yes | yes | yes | yes | yes | yes | pass |
| B1-07 | KRI09 | yes | yes | yes | yes | yes | yes | yes | yes | yes | pass |
| B1-08 | KRI09 | yes | yes | yes | yes | yes | yes | yes | yes | yes | pass |
| B1-09 | VUL09 | yes | **no** | yes | yes | yes | yes | yes | yes | yes | **fail** |
| B1-10 | MAK19 | yes | yes | yes | yes | yes | yes | yes | yes | yes | pass |
| B1-11 | MAK19 | yes | yes | yes | yes | yes | yes | yes | yes | yes | pass |
| B1-12 | BAR05 | yes | yes | yes | yes | yes | yes | yes | yes | yes | pass |

## Checks common to all pairs

* **Twins and skeleton.** In all 24 files, the text before and after the replaced `raise NotImplementedError` line is
  byte-identical to `skeleton.py`. This agrees with `MECH_CHECK.json`, which lists no issues. Each `ASSIGNMENT.json`
  brief is identical to the one in `MECH_CHECK.json`, and the claim appears verbatim in the skeleton docstring.
* **Shared helper.** Both twins of every pair contain the same Student-t upper-tail quadrature. I re-typed it in an
  isolated script (`scratch\check_tail.py`, `scratch\acc_tail.py`) and evaluated it only on textbook values and against an
  incomplete-beta reference. Up to 1000 degrees of freedom the absolute error is at most 5e-5 (2.8e-5 at 600 df). Every
  twin uses fewer degrees of freedom than that. The helper loses accuracy only at very large df (1e6), which no twin reaches.
  The helper is the same in both twins, so it cannot affect (c) or (g).
* **(e) Term check.** I re-ran the PB §4 term list over every brief (claim, keys, meanings, sizes) and found no hit.
  The word "false" appears only in the boolean key meanings of B1-01, B1-08 and B1-11 ("False if to placebo", "False on
  control trials", "False for a control participant"). No brief says what "claim false" means.
* **(d) MECH_CHECK listings.** I judged each listed comparison as follows:
  * B1-02 l.91: 2 per group. This is the note's minimum and the smallest size for Welch.
  * B1-04 l.92: 2 participants with a non-empty region. This is the minimum for a paired t.
  * B1-07 l.86 and B1-09 l.98: these compare the claim's own statistic with its threshold. They do not inspect the input.
  * B1-11 l.90: an empty-group guard in the selection half.
  * B1-12 l.45: an empty-selection guard. A proportion is defined from 1.

  The unlisted guards are all of three kinds: non-finite values; a size below the smallest at which the statistic is
  defined (2 for t statistics, 3 for a correlation, a slope p value or R-squared); or a zero variance (some of these
  guards trigger on any single zero-variance voxel, electrode or neuron). They all return `None` and match the guard
  minima in the private notes. No branch tests whether the data look like noise, zeros or a shuffle.
* **Does each fixed criterion return True exactly when the claim, with its statistic and threshold, is supported?**
  Yes for all 12, with two qualifications:
  * B1-04: participants with an empty region are left out of the across-participant test, although the claim says
    "across the 12 participants". The note's guard minimum describes this; it is minor.
  * B1-09: the fixed criterion's selection is not independent of its estimate (see below).
* **Passages.** I located the KRI09, KRI10 and MAK19 passages in the class source extracts (`class\src\*.txt`), and I
  confirmed the VUL09 and BAR05 abstract passages online. I could not re-open MOR03 (B1-01 to B1-03) online: PMC returned
  a browser check, which I did not bypass, and BMJ and Europe PMC returned errors. For those three pairs I relied on the
  private notes' quotations. `SOURCES_ADDENDUM.md` (read by the designer) supports B1-01's passage in substance.

## Per pair

**B1-01 (MOR03), pass.**
* *Faulty:* keeps women whose start index is at least 20 and tests the within-arm fall of the active arm only. MOR03's
  placebo passage attributes this fall to regression in both arms.
* *Fixed:* compares the same selected women between arms with Welch's t, which is the standard randomised-control
  correction. The test helper differs between the twins only because the error and its correction require it.
* *(h):* the key meaning "randomised to active hormone therapy" is borderline. I read it as naming the measured
  allocation variable, not as a statement about how rows are related or selected. I report it for the designer.
* *(f):* 300 women, the size of a typical two-arm symptom trial.

**B1-02 (MOR03), pass, with remark R1.**
* *Faulty:* groups women by the sign of the first-year change measured with scan 1 and starts the second-year change
  from that same scan. This is the MOR03 Figure 1 analysis.
* *Fixed:* starts the second-year change from the second 12-month scan, which is a standard
  independent-measurement correction. The twins differ in one line.
* *(f):* 600 women, of the order of osteoporosis-trial cohorts.
* **R1, error direction.** The documented bias makes first-year losers look like second-year gainers, so it pushes the
  rose-minus-fell difference *against* the claim. I estimated its size analytically from the skeleton's constants
  (scan CV 1.5 %, first-year SD 2.5; nothing was run or simulated):
  * The shared scan shifts the difference by about −1.2 percentage points.
  * The faulty difference is then about +0.1 pp in `plus` and about −1.2 pp in `minus`, against a threshold of +0.5.

  The faulty twin is therefore expected to hold in neither world. This pair cannot show a criterion that holds where
  the claim is false, and a miss on it would come from the brief's claim direction, not from the gate. CASE.md §7 says
  the same. None of the nine items covers direction, so the verdict stands, but the designer should read this pair's
  result with R1 in mind.

**B1-03 (MOR03), pass.**
* *Faulty:* selects patients on reading 2, which is also the baseline of the tested fall.
* *Fixed:* selects on the screening reading (reading 1), as the claim states. This is the serial-measurement
  correction. The twins differ in one line.
* *(f):* 250 patients × 3 readings, a clinic cohort.

**B1-04 (KRI10), pass.**
* *Faulty:* defines each participant's region by faces > houses and tests faces > bodies in the same runs. The shared
  faces term makes this circular (KRI10 Q7; KRI09 Example 2).
* *Fixed:* defines the region on even-numbered runs and tests on odd-numbered runs. For a subject-specific region,
  KRI10 Q7 (EV) requires only independent data from the same subjects.
* *(f):* 12 × 8 × 300. The 300 voxels are at the small end for a visual-cortex mask and below the cap, and the note
  gives no reason. Fewer selectable null voxels does not favour detection.

**B1-05 (KRI10), pass.**
* *Faulty:* selects voxels at p < 0.001 uncorrected on all 40 participants and estimates in the same participants.
  KRI10 (TN) calls this threshold pervasive.
* *Fixed:* selects on participants 0–19 and estimates on 20–39. KRI10 Q7 requires independent subjects for a
  group-level region claim.
* *(f):* 40 participants. The 1000 voxels are at the cap.

**B1-06 (KRI10), pass.** The single-participant selection and slope use the same trials in the faulty twin. The fixed
twin uses KRI10's half-the-data recipe with even and odd trials. *(f):* 240 trials × 500 voxels.

**B1-07 (KRI09), pass.** The faulty twin selects neurons and measures their index on the same trials. The fixed twin
selects on odd-numbered trials and measures on even-numbered trials. *(f):* 250 neurons × 15 presentations.

**B1-08 (KRI09), pass.**
* *Faulty:* selects electrodes and computes R-squared on the same trials.
* *Fixed:* uses an odd/even trial split.
* *Class:* R-squared here is an explained variance, not a prediction score, so the pair stays in B-1.
* *(f):* 100 trials × 64 electrodes.

**B1-09 (VUL09), fail on (b).**
* *Faulty:* averages the two sessions, keeps voxels whose across-participant correlation with the trait has one-sided
  p < 0.005, and reports their mean correlation. This is exactly VUL09's strategy. (a), (c), (d), (e), (f), (g), (h)
  and (i) are yes.
* *Fixed:* selects on session 1 and estimates on session 2 of the **same 16 participants.** For an across-participant
  correlation, the selection exploits two things that are identical in both sessions: the chance alignment of each
  participant's stable activation with the trait vector, and the trait vector itself. KRI10 Q7 states that this split
  is not independent for group-level inference:
  * TN: "splitting an individual's data ... does not yield independence at the group level".
  * ML and RP give the same answer.
  * EV, who is VUL09's first author, says a group-level region effect must be validated "with independent subjects".
* *A possible counter-reading:* MAK19 also allows splits "at the trial level" in general. That does not apply here,
  because the noise being recruited lies at the participant level.
* *Consequence:* the correction is partial. CASE.md §7 already attributes the fixed twin's 11/200 minus holds to this
  carry-over.
* *Repair (criterion body, fixed twin only):* select the voxels and estimate the correlation on different participants.
  For example, apply the same p < 0.005 rule on one half of the participants, with sessions averaged as in the faulty
  twin, and compute the mean correlation on the other half; or use a leave-participants-out scheme. Keep the 0.5
  threshold, the guards and the faulty body unchanged, and update the CASE.md estimand and mapping lines. This is not a
  brief, skeleton or size defect: the brief's 16 participants and two sessions allow a participant split.

**B1-10 (MAK19), pass.** The faulty twin ranks neurons by the pre-manipulation rate, which is the baseline of the change.
The fixed twin ranks by the resting recording, as the claim states; this is MAK19's "different dataset for the
sub-groups". The twins differ in one line. *(f):* 240 neurons.

**B1-11 (MAK19), pass.** The faulty twin chooses the window of largest group difference and tests it on the same
participants. The fixed twin chooses on even-indexed participants and tests on odd-indexed ones (MAK19's
participant-level division). *(f):* 60 × 200.

**B1-12 (BAR05), pass.** The faulty twin selects on the start score, which is also the baseline of the improvement
(BAR05 abstract). The fixed twin selects on the separate screening score, as the claim states. The twins differ in one
line. *(f):* 500 patients.

## Other remarks (no yes/no)

* **B1-07.** The fixed twin holds on about half of the N(0,1) noise-probe samples (CASE.md: 99/200). The cause is the
  claim's own ratio index on near-zero denominators. The allowed guards do not cover this case. The fixed twin may fail
  its clean pass for a reason unrelated to the correction.
* **Abstention.** The fixed twins of B1-05 and B1-08 abstain often in `minus` (empty selection). These are allowed
  guards.
* **Private notes without the §2 size reason.** For a source that states no sizes, PREREG_PHASE_C §2 asks the private
  note to give either the largest size within the timing estimate or a reason why a smaller size is realistic. Most
  notes give neither: B1-02, B1-03, B1-04, B1-05 (participants), B1-06, B1-07, B1-10, B1-11 and B1-12. B1-01 ("a
  realistic two-arm trial"), B1-08 ("a typical 64-channel cap") and B1-09 give a reason. I answered (f) by P-2 reading
  1, comparing each size with the setting myself (comparisons above); this is a note-completeness point for the designer.

## Class and subtype (PB §1)

All 12 pairs are B-1 with no subtype, and I agree with each. No pair uses a prediction score, which would make it B-2.

B1-02 and B1-10 group units on a reading that is also the baseline of the compared change. That fits B-3 ("a change
score against its own baseline") as well as B-1 ("improvement of units selected for extreme values of the same noisy
measurement"). PB §1 precedence puts B-1 before B-3, so both stay B-1. I have no disagreement.

## Size lists

* **Sizes not documented by the source** (P-2 reading 1): all 12 pairs, B1-01 to B1-12. None of the six sources (MOR03,
  KRI10, KRI09, VUL09 abstract, MAK19, BAR05 abstract) states sizes for the documented setting.
* **At the cap, with real counts far larger** (P-2 reading 2): B1-05 (1000 voxels) and B1-09 (1000 voxels).
* **Reduced for timing:** none. No size request was made, and the largest timing estimates are about 93 s (B1-05) and
  about 91 s (B1-09).

## What I read

* **Sandbox files:**
  * `AUDIT_PHASE_C.md`, `PREREG_PHASE_C.md`, `PREREG_PHASE_B.md`, `P2_READING.md`, `SOURCES.md`,
    `SOURCES_ADDENDUM.md`, `MECH_CHECK.json`.
  * `class\LOG.md` and `class\PRIVATE.json`.
  * For all 12 cases: `ASSIGNMENT.json`, `skeleton.py`, and `faulty.py` / `fixed.py` as text through the diff helper.
  * `CASE.md`: in full for B1-01; the mapping and §7 sections for the others.
  * `class\src\kri09.txt`, `kri10.txt`, `mak19.txt`, searched for the quoted passages.
* **Not read:** `agent_docs\`.
* **URLs (all logged):**
  * https://api.semanticscholar.org/graph/v1/paper/DOI:10.1111/j.1745-6924.2009.01125.x?fields=title,openAccessPdf,externalIds (VUL09 metadata)
  * https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.1111/j.1745-6924.2009.01125.x&format=json&resultType=core (VUL09 abstract; passage confirmed)
  * https://escholarship.org/content/qt51d4r5tn/qt51d4r5tn.pdf?t=lnrk38 (HTTP 403)
  * https://escholarship.org/uc/item/51d4r5tn (HTTP 403)
  * https://www.ebi.ac.uk/europepmc/webservices/rest/PMC1125994/fullTextXML (HTTP 500)
  * https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.1093/ije/dyh299&format=json&resultType=core (BAR05 abstract; passage confirmed)
  * https://pmc.ncbi.nlm.nih.gov/articles/PMC1125994/ (browser-check page, not bypassed, no content)
  * https://www.bmj.com/content/326/7398/1083 (HTTP 403)
* **Helper computations, all in `scratch\`:**
  * `show_case.py`: text diff and prefix/suffix check.
  * `check_tail.py` and `acc_tail.py`: the re-typed t-tail on known values.
  * The B1-02 bias estimate is analytic and was not simulated.
