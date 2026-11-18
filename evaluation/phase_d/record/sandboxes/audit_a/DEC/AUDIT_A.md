# Fidelity audit, part A, decoy class (D-012, D-046, D-047, D-052)

Result: 3 pairs pass (D-012, D-047, D-052), 1 fails (D-046, item h). Detail with one-line reasons is in `AUDIT_A.json`.

## Per case

| case | a | b | c | d | e | f | g | h | i | j | k | m | p | overall |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| D-012 | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | pass |
| D-046 | yes | yes | yes | yes | yes | yes | yes | **no** | yes | yes | yes | yes | yes | fail |
| D-047 | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | pass |
| D-052 | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes | pass |

- **D-012** (HUR84, B-6 units-not-independent). Faulty: 300 quadrats pooled in a two-proportion z test. Fixed: Welch on 10 plot occupancies. Structure: beta-binomial ICC 1/(2.333+1) = 0.3 = approved. (d) the fixed body's six listed comparisons are numerical internals of the incomplete-beta routine.
- **D-046** (LAZ10, B-6 units-not-independent). Bodies and reference are sound (a to g, i to p yes). Failure: (h). The brief says "Ten animals each received a different dose of a drug", which states that the dose values are all distinct across animals: a fact about how a variable is arranged across units, not within the sizes, axis names, key meanings or the claim. It is borderline and harmless in effect, but the instruction says to answer by the text. A brief defect cannot be repaired.
- **D-047** (MOR03, B-1 extreme-group-change). Faulty measures change from the flagging screening score, fixed from the entry score. A one-line diff. The two listed comparisons are the claim's own 0.5 threshold, identical in both bodies. Structure: reliability 0.6 = approved.
- **D-052** (MAK19, B-6 significant-here-not-there; reserve). Faulty: significant in young and not significant in old (one-sample tests). Fixed: Welch direct test. Structure: |log sd ratio| = ln 2 = 0.693 = approved.

## Remarks without yes or no

- The criterion returns `True` exactly when the claim, with its statistic and threshold, is supported: D-012 fixed yes (diff >= 0.10 and Welch p < 0.05); D-046 fixed yes (one-sided slope test p < 0.05); D-047 fixed yes (proportion >= 0.5, no test in the claim); D-052 fixed yes (one-sided Welch p < 0.05, young minus old). The faulty bodies differ by design.
- Class and subtype or tag follow PB §1 and PC's lists as far as I can read them from the case files: D-012, D-046 B-6 units-not-independent; D-047 B-1 extreme-group-change; D-052 B-6 significant-here-not-there. No disagreement. (I did not have PB §1 itself; I judged against the mechanism described in each note.)

## Pairs with sizes "not documented by the source" or "reduced for timing"

- Not documented by the source: D-012 (HUR84, abstract only), D-047 (MOR03, no sample size).
- Reduced for timing or the cap: none.
- D-046 (10 rats; 2 rats x 100 CA3 cells) and D-052 (groups of 20) are documented by their sources.

## What I read

Files in my sandbox: `FIDELITY_AUDIT_D.md`, `P2_READING_D.md`, `PREREG_PHASE_D.md`, `SOURCES_D.md`, the first lines of `SOURCES.md`, and in `class\` for each of the four cases `brief.json`, `PRIVATE.json`, `PASSAGE.md`, `CASE.md`, `faulty_body.py`, `fixed_body.py`, `reference.py`, `MECH_CHECK.json`, `STRUCTURE_LOG.md`, plus `class\logs\DEC\BRIEF_LOG.md` and `LOG.md` (the brief author's and criterion author's parts). I did not open `agent_docs\`.

Helper computations: none beyond reading ICC and reliability values by hand arithmetic. I called no criterion on data, ran no gate, saw no validity result. A `diff` of the two body files was used as text comparison only. Downloaded copies (LAZ10 XML, MOR03 page) were kept in a temporary sandbox folder and removed.

## URLs read

1. https://www.ebi.ac.uk/europepmc/webservices/rest/PMC2817684/fullTextXML (LAZ10 full text: 2 rats x 100 CA3 cells example; ICC = 0.83)
2. https://pmc.ncbi.nlm.nih.gov/articles/PMC1125994/ (MOR03 full text: patients with the worst clinical scores show the largest placebo effect)
