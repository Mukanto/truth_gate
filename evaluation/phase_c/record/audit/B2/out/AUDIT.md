# Fidelity audit, Phase C, class B-2 (blind auditor)

Date: 2026-11-15. Auditor: a fresh agent that wrote none of the cases, working under `AUDIT_PHASE_C.md`.
No criterion was called on any data, and Truth_Gate was not run (no version). Two helper computations were run in isolation:
(1) a Python one-liner that evaluates the guard arithmetic `n - (-(n) // k)` and its nested form for the integers 0 to 6
(no criterion imported, nothing from the cases executed), and (2) a script that scans the brief text in each
`ASSIGNMENT.json` for the banned terms of PB section 4 and compares each brief with its copy in `MECH_CHECK.json`.

## Result

**9 pairs pass and 3 fail.** All three failures are on item (c), from the same arithmetic slip in a guard, and each can be
fixed in the criterion bodies.

| Case | Subtype | Source | a | b | c | d | e | f | g | h | i | Overall |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B2-01 | L1.1 | KAP23 | yes | yes | **no** | yes | yes | yes | yes | yes | yes | fail |
| B2-02 | L1.4 | KAP23 | yes | yes | yes | yes | yes | yes | yes | yes | yes | pass |
| B2-03 | L1.4 | KAP23 | yes | yes | yes | yes | yes | yes | yes | yes | yes | pass |
| B2-04 | L3.1 | KAP23 | yes | yes | yes | yes | yes | yes | yes | yes | yes | pass |
| B2-05 | L3.1 | KAP23 | yes | yes | yes | yes | yes | yes | yes | yes | yes | pass |
| B2-06 | L3.2 | KAP23 | yes | yes | **no** | yes | yes | yes | yes | yes | yes | fail |
| B2-07 | L3.2 | KAP23 | yes | yes | yes | yes | yes | yes | yes | yes | yes | pass |
| B2-08 | L1.3 | VAR06 | yes | yes | yes | yes | yes | yes | yes | yes | yes | pass |
| B2-09 | L1.3 | VAR06 | yes | yes | yes | yes | yes | yes | yes | yes | yes | pass |
| B2-10 | L1.3 | VAR06 | yes | yes | **no** | yes | yes | yes | yes | yes | yes | fail |
| B2-11 | L1.3 | VAR06 | yes | yes | yes | yes | yes | yes | yes | yes | yes | pass |
| B2-12 | L1.3 | AMB02 | yes | yes | yes | yes | yes | yes | yes | yes | yes | pass |

## The defect behind the three "no" answers

Several bodies write "the smallest class count in a training fold", n − ceil(n/k), as `n - (-(n) // k)`. Python applies the
unary minus before `//`, so `-(n) // k` means `(-n) // k`, which equals −ceil(n/k). The expression therefore computes
**n + ceil(n/k)**, not n − ceil(n/k). Evaluated in isolation:

| n per class | `n - (-(n)//5)` | intended n − ceil(n/5) | `n - (-(n)//10)` | nested form (k = 10) | intended nested |
|---|---|---|---|---|---|
| 0 | 0 | 0 | 0 | 0 | 0 |
| 1 | 2 | 0 | 2 | 3 | 0 |
| 2 | 3 | 1 | 3 | 4 | 0 |
| 3 | 4 | 2 | 4 | 5 | 1 |
| 4 | 5 | 3 | 5 | 6 | 2 |

So every guard written this way with `< 2` returns `None` only for an empty class, and the `< 3` form (B2-10) returns `None`
only below 2 per class.

* **B2-01 and B2-06.** The faulty guard is `min(n_pos, n_neg) < 2`, which returns None below 2 per class. The fixed guard
  returns None only for an empty class. CASE.md states the fixed minimum as at least 2 per class in every 5-fold training set
  (at least 3 per class), and for B2-06 it says that both twins use the same patient-level minimum. In the code the fixed
  guard is *laxer* than the faulty one, the reverse of what the correction's structure implies. The twins therefore differ
  in a line that is neither the error nor its correction.
* **B2-10.** The faulty guard `min(n_pos, n_neg) < 3` returns None below 3 per class. The fixed guard returns None only below
  2 per class, although the stated minimum is at least 3 per class in every outer training set (at least 4 per class).
  Same kind of difference.

**Severity.** Low. Answered by the text of (c), it is a "no". The difference matters only at 1 member of a class (B2-01, B2-06)
or 2 members (B2-10). That never happens in the declared worlds: about 45 onsets of 896 rows, 32 of 80 patients, and 20 of
40 samples. It also cannot happen under the permutation controls or the shuffle probe, which keep the class counts. Under the
zeros probe (all-False labels) both twins return None. Under the noise probe such small class counts are vanishingly
unlikely.

**Repair (criterion bodies only).** Write the minimum correctly, for example `n_pos - (-(-n_pos // k))`, so that the fixed
guard is the stated fold minimum. Alternatively, use one and the same guard in both bodies. A guard difference that does
follow from the fold structure (fixed stricter than faulty) would be acceptable under (c) as part of the correction.

**The same slip in the passing pairs (no item changes).** B2-02, B2-03 and B2-12 use the identical expression in both twins.
In B2-08, B2-09 and B2-11 the faulty uses the single form and the fixed the nested form, and both return None only for an
empty class. The twins behave identically, so (c) is "yes". Each guard returns None less often than CASE.md states, but
only for an empty class, which is still an allowed guard, so (d) is "yes". If such a guard is reached with 1 to 3 members of
a class, a training fold can lack that class and the criterion still returns a bool. This cannot happen at the declared
class sizes. It is recorded here for the report; it is not a repair request, because only pairs with a "no" are returned
(PB section 5.3).

## Per-pair notes

**B2-01 (KAP23, L1.1).** Faulty: a ridge logistic regression (λ = 1, standardised) is fitted on all 896 country-years and
scored on the same rows. This is the "No test set" text of KAP23 section 2.4 (read online). Fixed: stratified 5-fold CV of
the same fit, with the held-out scores pooled into one AUC. Item (f): KAP23 Table A6 gives the Muchlinski et al.
out-of-sample test set as 896 rows with 19 positives. The 30 indicators are fewer than Muchlinski's 90 variables, but KAP23
B.2 says 70 of those 90 have no values in the test set, so 30 lies within the source's range. This reduction was the
author's choice ("keep the fit fast") and the timing rule did not require it. It lowers the in-sample optimism, so it works
against detection, not for it. The fixed CV is random over country-years and not grouped by country. That is consistent with
the claim ("new country-years") and the estimand. **Fails (c)** (guard, above).

**B2-02 and B2-03 (KAP23, L1.4 by the tie rule).** Faulty: copy-oversampling of the smaller class on the whole data, then
stratified 5-fold CV, with the statistic computed over held-out rows that include copies. Fixed: the same oversampler
applied to each training fold only, scored on untouched original rows. In revision 2 the oversampler was changed to "copy
the smaller class, whichever it is". This is the standard random-oversampler definition (balance the classes), mirrored in
both twins. It does not inspect whether the input looks like noise. It changes behaviour only where the positive class is
the majority, which does not happen in the declared worlds. I judge it not gate-aware. The part-1 note had asked for a
classifier that can exploit exact copies (1-NN or an unregularised fit). The bodies use a ridge logistic regression because
the fixed version with 5-NN was weak in `plus`. KAP23 names no classifier, so (a) holds. CASE.md itself warns that a
logistic regression leaks little through copies. A miss here would read as "error too small in the declared worlds at this
size".

**B2-04 and B2-05 (KAP23, L3.1).** Faulty: shuffled 5-fold CV of a time series (15-NN classifier in B2-04, OLS regression
in B2-05). KAP23 B.5 describes this ("the training dataset could contain data from a later date than the test dataset
because of being shuffled"). Fixed: expanding-window forward evaluation over 6 contiguous blocks. B2-05: with an OLS
regression on contemporaneous drivers that carry no information in `minus`, shuffled folds can barely profit from
proximity in time, so the faulty criterion may behave like the fixed one in these worlds (CASE.md says so too). The error
is present; its size in these worlds is small. The model is fixed by the claim ("a regression").

**B2-06 and B2-07 (KAP23, L3.2).** Faulty: rows pooled (patches or sessions) with random fold assignment over rows, so a
patient's or participant's observations sit in training and test. This matches KAP23's text on Oner et al. 2020 and the
same people or units in both sets. Fixed: whole patients or participants assigned to folds (block CV, as KAP23 names).
**B2-06 fails (c)** (guard, above). B2-07 uses OLS, a low-capacity model, so the leak through stable participant
measurements is limited (stated in CASE.md).

**B2-08 and B2-09 (VAR06, L1.3 per the addendum).** These parameters were confirmed in the VAR06 full text (Europe PMC):
Δ between 0.01 and 1, 10-fold CV, ties going to the larger Δ, and 40 samples (20 per class) of 6000 features. Table 1
gives the shrunken-centroid null case as mean CV error 37.8% against a true error of 50.0%. The PAM implementation follows
the Tibshirani form: s0 is the median of the gene-wise SDs, m_k = sqrt(1/n_k − 1/n), soft thresholding, priors. Faulty: the
maximum over the 20-value grid of the 10-fold CV accuracy (B2-08) or the pooled CV AUC (B2-09; AUC replaces the source's
error rate, a stated variant). Fixed: nested CV, with an outer stratified 10-fold loop and an inner 10-fold loop that tunes Δ.

**B2-10 (VAR06, L1.3).** VAR06's SVM setting was confirmed online: the top 3 t-statistic features are reselected inside
every LOOCV fit, C runs from 2^-5 to 2^15, γ from 2^-15 to 2^3, and the C and γ grid is tuned by LOOCV. Two substitutions are
stated in CASE.md and were anticipated in the note: a closed-form Gaussian kernel ridge classifier replaces the SVM, and a
5 × 5 grid replaces the full grid on the same ranges. VAR06 itself notes that tuning over fewer parameters "may potentially
reduce" the bias, so these choices can only make the faulty error smaller than documented. Item (a) holds. **Fails (c)**
(guard, above).

**B2-11 (VAR06, L1.3).** The tuned quantity is the panel size k (1 to 100 genes), with genes ranked inside every fold in
both twins. Only the tuning of k on the estimation data differs. This is within the addendum's reading: "features or
classifier parameters" selected on the data of the error estimate.

**B2-12 (AMB02, L1.3).** Faulty: the top 3 genes are ranked on all 62 tissues before a 10-fold CV. The AMB02 abstract,
read online through Europe PMC, documents this: the CV "is not external to the selection process" and 10-fold CV is
recommended. Fixed: the ranking is repeated inside every training fold (external CV). The single changed line is the
position of `rank_genes`.

## Items checked across all pairs

* **(d) and MECH_CHECK.** I judged every listed comparison.
  * The class-count guards are allowed guards.
  * `np.max(np.abs(step)) < 1e-8` (B2-01, 02, 03, 06) is the Newton optimiser's stopping rule on the step size and does not
    inspect the input.
  * `pred.size < 3 or not (pred.std() > 0 and y.std() > 0)` (B2-07) is allowed: the correlation is defined from 3 pairs
    with positive variances.
  * `int(scored.sum()) < 2` (B2-05, fixed) is allowed: R-squared needs 2 scored weeks.
  * `... > 0` in B2-12 line 81 is the nearest-centroid decision rule.
  * The unlisted replacements `np.where(sd > 0, sd, 1)`, `np.where(sp > 0, sp, inf)`, `np.where(den > 0, den, 1)` and
    `np.maximum(lam, 0)` are numerical safeguards identical in both twins.
  * No body tests whether the data look like noise, zeros or a shuffle. Every body reads only its own data and `np`.
* **(e).** No banned term occurs in any brief (my own scan agrees with the designer's script), and no brief says what
  "claim false" means. Each `ASSIGNMENT.json` brief is identical to its copy in `MECH_CHECK.json`.
* **Return value.** In all 12 pairs each criterion returns `True` exactly when its statistic reaches the brief's
  threshold (point estimate ≥ threshold, the same rule in both twins), and `None` only from the guards.
* **(g) and cost.** For the VAR06 pairs the fixed criterion costs about 10× more fits. That extra cost is the nested CV,
  which is the correction itself, so (g) is read as "comparable apart from the error".

## Class and subtype remarks (PB section 1)

All 12 pairs meet the B-2 rule: a prediction score claimed for new data, with test information entering the evaluation. I
disagree with no subtype.

* B2-01 is L1.1.
* B2-02 and B2-03 are L1.4 (oversampling by copying rows, by the tie rule).
* B2-04 and B2-05 are L3.1.
* B2-06 and B2-07 are L3.2.
* B2-12 is L1.3 (feature selection on all data).
* B2-08 to B2-11 are L1.3 as `SOURCES_ADDENDUM.md` fixes it for VAR06 (classifier parameters, and in B2-11 the panel size).
  This is not a disagreement.

**What the failures mean for the class if they are not repaired** (for the designer):

* B2-01 is the only L1.1 pair. Losing it would miss the L1.1 ≥ 1 minimum.
* B2-06 is one of the two L3.2 pairs. Losing it would miss the L3.2 ≥ 2 minimum.
* B2-10 is one of the four VAR06 (addendum) pairs. Losing it would give "new-source minimum not met".

The three independent read sources are KAP23, VAR06 and AMB02 (AMB02 read in its abstract). They all survive among the
passing pairs.

## Sizes "not documented by the source" and sizes "reduced"

* **Sizes not documented by the source** (P-2 reading 1; compared with the setting the source and the note describe):
  * B2-02 (400 × 12, clinical cohort)
  * B2-03 (1000 × 50, at the unit cap)
  * B2-04 (500 days × 10)
  * B2-05 (400 weeks × 8)
  * B2-06 (80 × 10 × 20, pathology cohort)
  * B2-07 (40 × 4 × 10, repeated-measures study)
  * B2-12 (the AMB02 abstract gives no sizes; 62 tissues matches the colon data set the source uses, from general knowledge)
* **Reduced to the cap** (P-2 reading 2; gene axis capped at 1000):
  * B2-08, B2-09, B2-10, B2-11: 6000 → 1000 genes. The 40 samples are the source's (confirmed online).
  * B2-12: 2000 → 1000 genes.
* **Reduced for timing:** none (no size request was made).
  * B2-01's indicator count (30, against Muchlinski's 90 variables) is an author choice within the source's range, not
    required by the timing rule.
  * B2-10's coarser parameter grid (5 × 5) was chosen for timing. It is a parameter, not a size.

## Other observations (no item changes)

* The `CASE.md` files do not yet carry the overlap mark, the mechanism tag and statistic family, or the size ratio that
  PREREG_PHASE_C section 3 lists. These are presumably added by the designer.
* Per the part-1 LOG, the brief thresholds were set near the faulty values that the source reports under the null (for
  example, VAR06 null accuracy of about 0.58 to 0.62). This also makes several fixed criteria weak in `minus` (B2-08,
  B2-10, B2-11 at 0.17 to 0.30). It is a brief design choice outside items (a) to (i), and PREREG_PHASE_C section 2 keeps
  such weak fixed criteria in the table.

## What I read

* **Sandbox files:**
  * `AUDIT_PHASE_C.md`, `PREREG_PHASE_C.md`, `PREREG_PHASE_B.md`, `P2_READING.md`, `SOURCES.md`, `SOURCES_ADDENDUM.md`,
    `MECH_CHECK.json`
  * `agent_docs/GATE.md` (searched for the probe lines only)
  * `class/LOG.md`, `class/PRIVATE.json`
  * For each of the 12 cases: `ASSIGNMENT.json`, `CASE.md`, `faulty.py`, and `fixed.py` (through the full diff against
    `faulty.py`, plus direct reads of parts of B2-04 and B2-05 fixed). `skeleton.py` was diffed against `faulty.py`; only
    the stub line differs.
* **URLs** (fetched with `ctx_fetch_and_index` under labels `zq7auditB2x-*`, searched only with that source filter):
  * https://www.ebi.ac.uk/europepmc/webservices/rest/PMC1397873/fullTextXML (VAR06 full text)
  * https://ar5iv.labs.arxiv.org/html/2207.07048 (KAP23 full text)
  * https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.1073/pnas.102102699&format=json&resultType=core (AMB02 record with abstract)
