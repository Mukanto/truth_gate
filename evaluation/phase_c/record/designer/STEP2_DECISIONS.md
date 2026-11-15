# Phase C step 2 (designer): brief checks, readings and decisions

PREREG_PHASE_C §4 item 2. Mechanical checks by `designer/step2_check.py` (report `STEP2_REPORT.json`); the brief half of
items (h) and (i) read by the designer against the verbatim "what a brief may state" text and the estimand lines.

## Mechanical results (first pass, 2026-11-13)

| Class | Briefs | Per source | Addendum pairs | Independent read sources | Term check | Overlap marks |
|---|---|---|---|---|---|---|
| B-1 | 12 | MOR03 3, KRI10 3, KRI09 2, MAK19 2, VUL09 1, BAR05 1 | 6 | MOR03, KRI09, MAK19, VUL09, BAR05 | clean | 4 (B1-07~B1-01, B1-09~B1-04, B1-11~B1-07, B1-12~B1-11) |
| B-2 | 12 | KAP23 7, VAR06 4, AMB02 1 | 4 | KAP23, VAR06, AMB02 | clean | 6 (B2-02~B2-07, B2-03~B2-07, B2-04~B2-09, B2-05~B2-10, B2-06~B2-11, B2-12~B2-03) |
| B-3 | 12 | CUR13 4, PEA97 3, ARC81 3, KRO93 2 | 4 | CUR13, PEA97, ARC81, KRO93 | clean | 5 (B3-05~B3-05, B3-06~B3-05, B3-07~B3-07, B3-09~B3-01, B3-12~B3-09) |
| B-6 | 12 | LAZ18 4, NIE11 3, HUR84 2, LAZ10 2, MAK19 1 | 4 | NIE11, HUR84, LAZ10, MAK19 | clean | 5 (B6-05~B6-01, B6-07~B6-01, B6-08~B6-04, B6-10~B6-07, B6-11~B6-08) |
| O | 6 | KAP23 2, SIM11 2, BAG09 1, HER14 1 | — | — | clean | 4 (O1-B~O1a, O2-A~O2a, O2-B~O2a, O3-B~O3b) |

B-2 subtypes: L1.1 1, L1.3 5, L1.4 2, L3.1 2, L3.2 2 (minima met). Overlap marks are by the mechanical key (source, tag,
family) against `PHASE_B_TABLE.json`; the class tables count them on the pairs that enter them.

## Readings (brief half of (h) and (i))

All 54 briefs were read. Every brief has an estimand line naming the faulty and the fixed quantity. Claims that name
a subgroup, region, window, reading, adjusted-for quantity or test (B1-01..B1-12, B3-01..B3-12, B6-05..B6-12) do so
where their estimand line says the estimand requires it; no brief states an extra fact about how rows, units, splits,
repetitions or variables are related, ordered, duplicated, shared or selected beyond the axis names ("days in
chronological order", "sessions in order", "dates in order", "time samples in order" are axes named as time in order);
no key names a variable by its role in the error (the O author asked about `severity_rating` and `on_signature`: both
name what was measured). Claims that name the statistic's definition ("estimated by 5-fold cross-validation", "the first
10 principal components", "uses three genes", "on later days", "new patients") state what the claim itself states.

Class and subtype checked against PB §1: oversampling by copying rows is L1.4 (B2-02, B2-03); PCA on all rows and a
biased test sample are O-1 (O1-A, O1-B); a change correlated with its own baseline without selection is B-3 (B3-08);
a split by a baseline reading followed by a comparison of changes is B-1 (B1-02, B1-10).

## Rejections (one return per author)

* B-2: B2-08 (genes 6000), B2-09 (4000), B2-10 (6000), B2-12 (2000) violate §2 "at most 1000 rows (or units) along any
  axis". Returned once to the B-2 author; nothing else returned.

## Questions raised by authors (designer's answers; none changes a brief)

* B-6: B6-09 family `other` (Mann–Whitney U, a rank test) is correct under the definitions. Whether B6-11 (LAZ10's
  repeated-measures point applied to a correlation) is the documented error is audit item (a), not a step-2 reason.
* B-3: settings of the ARC81 and KRO93 pairs are the author's applications of abstract-level descriptions (marked in the
  notes), as in Phase B; whether they are the documented error with documented parameters, and whether the sizes fit, is
  audit items (a) and (f).
* B-2: SIM03 not used (passage not readable); the class has 3 independent read sources without it.

## Honour-system events (recorded, no brief changed)

* B-3: one unfiltered `ctx_search` of the shared context-mode store (see `REVISIONS-post-freeze.md` P-1; the designer
  read the returned chunks: public bibliographic search results only).
* B-1: wrote derived plain-text files (its fetched source texts) to the session scratchpad outside its sandbox, which
  the rule "write only inside your sandbox folder" forbids; no other agent was given that folder.
* O and B-2: the harness saved fetched PDFs to its own tool-results folder outside the sandbox (an automatic side effect
  of the fetch tool, reported by both authors).
* All five used only sandbox files and online sources by their logs; the designer checked the tool lists of the five
  transcripts (Read, Glob, Grep, Write, Edit, Bash, WebFetch, WebSearch, ToolSearch and context-mode tools; no agent was
  started).
