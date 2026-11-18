# Designer's checks of the briefs (PREREG_PHASE_D section 3 item 2), 2026-11-18

Five brief authors wrote 72 briefs: B-2 30 (20 pairs, 10 reserves), B-3 30 (20, 10), decoys 12 (8, 4).

**Mechanical checks** (`designer/brief_mech_check.py`): no problem found. The script checked:
- counts per source and subtype or tag, which equal `TASK.json` (pairs plus reserves) for every author;
- the closed lists of tags and families, with subtype = tag for B-2;
- that every note field is present, including the estimand and the model family;
- the structure statistic: its fields, its direction against the sign of note − null, and null only for a decoy;
- that dtypes are only float and bool;
- that every axis has an integer size;
- the size limits: at most 2000 per axis and 2 000 000 values per array.

**Term check** (`tools/term_check_d.py`): 0 hits in all five files.

**"What a brief may state", PB §1's class rules and the within-class difference rule.** The designer read every claim
and key and rejected no brief.

Readings recorded:
- **Missing values.** Keys stating that an unmeasured value is NaN (B2A-03, B2A-R2) describe what the key holds, not
  how rows relate.
- **Rarity.** "Rare outcome" (B2A-R4) describes the outcome, not a relation between rows.
- **Time order and repeat readings.**
  - "In time order" or "in age order" in a key's meaning (B2B-08, B2B-14, B3A-07, B3B-06, B3B-13, DEC-R4) carries the
    same information as an axis named in order, which the rule allows.
  - Keys for a second, independent reading (the B-3 retest keys) are allowed by the instruction file's B-3 estimand rule
    ("keys for the independent measurement where the documented correction uses one"). Where the fixed analysis does not
    read such a key, it serves the structure statistic.
- **Selections stated in claims.** Claims that state a selection (DEC-01, DEC-02, DEC-03, DEC-R1, DEC-R2) do so because
  the claim's estimand is about the selected units: the rule's part (iii), "what the claim itself states".
- **Difference rule, close pairs.** These pairs share a statistic family and differ in the data structure: the
  independent measurement used by the correction (expired-gas oxygen uptake against a second cardiac-output
  determination) and the subjects (patients against dogs).
  - B3A-04 and B3B-08 (Fick oxygen delivery and consumption, correlation);
  - B3A-08 and B3B-09 (within-unit slope).

  B3A-01 and B3B-01 (partial correlation given a common size measure) differ in the sample-size regime (300 skulls
  against 2000 beetles) and in the data.
- **Reserves.** B2B-13 (AUC, gene expression, L1.3) is close to B2A-05 (AUC, gene expression, L1.3; 72 against 80
  samples). If B2B-13 is ever used to replace a pair while B2A-05 is in the set, the difference rule is checked again
  at that point.

**Author runs.** Every brief author ran on the Sonnet line (`record/AUTHOR_RUN.md`). There was no agent-starting or
context-mode tool call, no path outside the author's sandbox, and no URL of the project's repository or evaluations.
Inputs are unchanged (`MANIFEST_authors.json`).
