# Fidelity audit, Phase C, class O (O-1 to O-3)

Blind fidelity auditor of class O, 2026-11-15. Six pairs: O1-A, O1-B (O-1, KAP23), O2-A, O2-B (O-2, SIM11), O3-A (O-3,
BAG09), O3-B (O-3, HER14). I wrote none of the cases. **No criterion was called on any data and Truth_Gate was not run.**
No study file was imported or executed. I parsed them as text and AST only, to compare the twins with the skeleton and to
list the keys they read.

## Result

| Pair | a | b | c | d | e | f | g | h | i | overall |
|---|---|---|---|---|---|---|---|---|---|---|
| O1-A | yes | yes | yes | yes | yes | yes | yes | yes | yes | pass |
| O1-B | yes | yes | yes | yes | yes | yes | yes | yes | yes | pass |
| O2-A | yes | yes | yes | yes | yes | yes | yes | yes | yes | pass |
| O2-B | yes | yes | yes | yes | yes | yes | yes | yes | yes | pass |
| O3-A | yes | yes | yes | yes | yes | yes | yes | yes | yes | pass |
| O3-B | yes | yes | yes | yes | yes | yes | yes | yes | yes | pass |

**6 pass, 0 fail.** There is no repair request. The one-line reasons for each item are in `AUDIT.json`.

## Checks done for all pairs

* **Twins and skeleton.** I used a scripted AST/text comparison. Both twins equal `skeleton.py` once the criterion body
  is replaced by the stub. Each file has exactly one `Criterion("C", criterion)` with no components. Imports are only
  `numpy` and `truth_gate`. This agrees with `MECH_CHECK.json` (`issues: []` for every pair).
* **Term check (e).** I ran a scripted case-insensitive search of every string in each brief (claim, keys, meanings, size
  names) for the PB §4 terms and their inflections. Nothing matched. No brief says what "claim false" means. The only
  hit on a negation word was "False if resistant" in O3-A's `sensitive` key, which describes the dtype.
* **Return value.** In every pair the fixed criterion returns `True` exactly when the claim, with its statistic and
  threshold, is supported:
  * O1-A: R² ≥ 0.15.
  * O1-B: balanced accuracy ≥ 0.70.
  * O2-A and O2-B: positive difference and two-sided pooled p < .05.
  * O3-A: difference ≥ 0.5 and two-sided Welch p < .01.
  * O3-B: gap ≤ −2.
* **Helper computation (declared).** `scratch\helper_pvalues.py` holds re-typed copies of the two p-value routines found
  in the bodies:
  * the Abramowitz–Stegun 26.7.3/26.7.4 Student routine, in O2-A and O2-B;
  * the Lanczos and incomplete-beta Welch routine, in O3-A.

  I evaluated both at tabulated critical values (df 1, 2, 5, 18, 38, 98 at .05; df 30, 38 at .01; plus two trivial
  points). Both reproduce the known p values to six decimals. I ran the script with `py -I` in the scratch folder. It
  imports no study file and calls no criterion.

## Pair notes (beyond the JSON reasons)

* **O1-A, item (d): the guard minimum of 15.** One could argue the strict minimum is 14: with n = 14, every training fold
  has 11 rows, which exactly identifies the 11 regression parameters. I read "smallest size at which the statistic is
  defined" the way the pre-registration's own example reads it. That example gives 3 pairs for a correlation, although
  r can be computed (±1) from 2. So "defined" means at least one residual degree of freedom. Here that is 12 training
  rows, and 15 is the smallest n at which `array_split` leaves 12 training rows in every fold. On that reading the
  minimum is allowed.

  The guard cannot matter in practice. Every world and every probe has 300 rows, because the probes keep the shape.
* **O1-B, item (d).** The guard is "n < 10 or fewer than 2 of either class". On the same reading this is below the
  defined size:
  * 2 per class is what puts both classes in every training fold;
  * an unpenalised logistic fit on 30 measures is degenerate (separable data) below about 32 training rows.

  With the faulty band, the selection keeps about 280 of 400 rows on every declared world and probe.
* **O1-B, item (a): where the band sits.** The 30 percent band is the note's declared choice; KAP23 gives no width. The
  band covers the 35th to 65th percentiles of the rating. In this skeleton about 35 percent of children are diagnosed, so
  the diagnosis boundary sits near the 64th percentile of the rating. The band therefore removes the children just below
  the boundary (hard negatives) but keeps those just above it.

  The documented error is present: the evaluation set excludes intermediate cases and is no longer representative. Its
  size in these worlds is probably smaller than with a band centred on the boundary. This is not a fidelity defect.
* **O2-A, item (a): the third test.** The third test uses the raw average of liking (0 to 100) and willingness to pay
  (about 8 units), following SIM11's wording "the average of these two variables". In SIM11 both variables were
  standard normal, so there the raw and standardised averages are the same.

  In this world the average is dominated by liking. The third test nearly repeats the first, so the faulty's effective
  flexibility is closer to two tests. The documented procedure is present; its size is probably reduced.
* **O2-B.** The fixed criterion tests at `min(len(control), len(treatment))`, which is all 50 per condition under the
  brief and every declared stream.
* **O3-B, item (a): which five rows are dropped.**
  * The note says "first five" country rows.
  * The code drops the last five, following the footnote's "lines 30 to 44 instead of 30 to 49".
  * HER14 says the omitted countries were the alphabetically first five.

  The author logged this choice. The skeleton's country rows are exchangeable draws and the brief states no order, so
  the two readings are statistically identical.
* **O3-B, item (d): abstention on the probes.** No noise or zero value exceeds 90. Both twins therefore abstain through
  the allowed empty-selection guard on every noise and zeros probe sample. This comes from the claim's 90 boundary, it is
  the same in both twins, and it is not a probe test. A capping `K5_INCONCLUSIVE` on these probes is likely for both
  twins (descriptive; it changes no item).

## Class and subtype remarks (PB §1; they change nothing)

* **O1-A (O-1, KAP23 L1.2 without labels).** Agree. PB §1 lists "PCA on all data" under O-1. No B-2 rule applies,
  because the pre-processing uses no labels.
* **O1-B (O-1, KAP23 L3.3).** Agree. The selection uses data, but the statistic is a prediction score, so B-1 is
  excluded. No test information enters training, so it is not B-2.
* **O2-A and O2-B (O-2, SIM11): disagreement of reading, reported.** O-2 is named "flexibility outside the criterion".
  In these pairs the choice among analyses (three tests; repeated looks) happens *inside* the criterion. Read by its
  general clause, B-6 covers both faulty criteria: "an inferential rule whose false-positive rate exceeds its nominal
  level in a world without the effect". If the two mechanisms after the colon are read as an exhaustive list, B-6 does
  not apply. In that case the designer's O-2 follows PB §1's O-2 row, which names SIM11 and this mechanism.
* **O3-A and O3-B (O-3).** Agree, with one remark. PB §1 says "in the real data", but here the offset and the range
  error are written into the criterion's analysis code. No B rule applies: neither a shift to adjacent rows nor dropping
  five exchangeable rows uses the data to select, and neither raises the false-positive rate in a world without the
  effect.

## Sizes (item (f), read with `P2_READING.md` and the Phase C size rule)

* **Sizes not documented by the source:**
  * O1-A: 300 × 80, compared with a clinical biomarker-panel cohort as the note argues. KAP23's L1.2 entry states no
    size.
  * O1-B: 400 × 30, compared with a clinic referral cohort. KAP23's L3.3 entry and the Bone et al. example as read state
    no size.
* **Reduced to the cap:**
  * O3-A: the probe-set axis is 1000, against BAG09's arrays of 12 558 to 22 283 probe sets.
  * The 60 cell lines are the NCI-60 panel the source uses.
* **Reduced for timing:** none.
* **Source sizes used:**
  * O2-A: 20 per cell (SIM11 Table 1).
  * O2-B: first look at 10, maximum 50 per condition (SIM11 Figure 1).
  * O3-B: 20 countries × 64 years (1946 to 2009; HER14/RR).

All arrays are at most 1000 along any axis; the largest array has 60 000 values.

## Other observations

* The brief author reports that GHZ26 (named in PB §1 for O-3) has no reference in `SOURCES.md` or
  `SOURCES_ADDENDUM.md` and was not used. Both O-3 pairs rest on BAG09 and HER14. Reported; no audit item depends on it.
* For HER14 I read the PERI working paper WP322 (April 2013, same authors and title), as the brief author did. I did not
  open the journal version in CJE 38(2), so the wording of the quoted passages may differ slightly from the journal text.

## What I read

* **Sandbox files:**
  * `AUDIT_PHASE_C.md`, `PREREG_PHASE_C.md`, `PREREG_PHASE_B.md`, `P2_READING.md`, `SOURCES.md`, `SOURCES_ADDENDUM.md`
    and `MECH_CHECK.json`.
  * `class\LOG.md` and `class\PRIVATE.json`.
  * For each of the six cases: `ASSIGNMENT.json`, `CASE.md`, `skeleton.py`, `faulty.py` and `fixed.py`.
  * `agent_docs\GATE.md`: lines 100 to 169 and 320 to 364, plus a search for probe terms.
* **Source extracts:** the class folder holds none.
* **URLs.** Each was fetched with `ctx_fetch_and_index`, under labels `auditO-pc-*`, and again inside a sandboxed script
  for text extraction:
  * https://ar5iv.labs.arxiv.org/html/2207.07048 (KAP23, sec. 2.4 [L1.2] and [L3.3])
  * https://ar5iv.labs.arxiv.org/html/1010.1092 (BAG09, sec. 3.2 and 3.9)
  * https://pdf.stafforini.com/simmons-2011-falsepositive-psychology-undisclosed.pdf (SIM11, Table 1 and its note, Figure 1 text)
  * http://peri.umass.edu/wp-content/uploads/joomla/images/WP322.pdf (HER14 working paper, sec. 2 and footnote 5)
* **`ctx_search`:** I called it once, with the filter `source: "auditO-pc-KAP23"`, a label I indexed in this run.
* **Not used:** I made no `ctx_batch_execute` or `ctx_index` call and used no harness scratchpad. Nothing else on the
  machine was read.
