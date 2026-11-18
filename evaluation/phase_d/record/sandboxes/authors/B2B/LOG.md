# LOG, author B2B (B-2, half B)

Task: 10 cases and 5 reserves (TASK.json). Briefs B2B-01 to B2B-10 are the cases; B2B-11 to B2B-15 are the reserves
(one each for SIM03 L1.1, SAN18 L1.4, AMB02 L1.3, ROB17 L3.1, SAE17 L3.2), as `TASK.json` lists them.

## Files read (all inside the sandbox)

BRIEF_AUTHOR_D.md, TASK.json, SOURCES.md, SOURCES_D.md, agent_docs/README_TOOL.md, agent_docs/MANIFEST.md,
agent_docs/GATE.md (full), agent_docs/SCAN_REVIEW.json (first 40 lines), agent_docs/SPEC.md (headings only).

## Sources read online, and how

The WebFetch tool returns a summary produced by a small model, not the page text. Every "quote" in PRIVATE.json
that comes from an online read is therefore a summary of that read, and I say so in the notes where it matters.

| Key | What I read | How |
|---|---|---|
| AMB02 | Europe PMC full text PMC124442 (datasets, error rates, label-permuted null sets) | full text, as summarised by the tool; the PMC mirror was blocked by a browser check, the Europe PMC page worked |
| SIM03 | OpenAlex record (a paraphrase of the text; Europe PMC had no abstract; PubMed blocked by a cookie page) | tool paraphrase of the OpenAlex inverted index; figures (98% zero errors in the no-difference simulation, 27% vs 41% in a breast cancer example) are unverified |
| VAR06 | Europe PMC full-text XML PMC1397873 | full text, as summarised by the tool |
| SAN18 | OpenAlex abstract (tool paraphrase) and SOURCES_D | abstract only; full text not open |
| ROB17 | OpenAlex abstract reconstructed from the inverted index | abstract only |
| SAE17 | Europe PMC full-text XML PMC5441397 | full text, as summarised by the tool |

## URLs

1. https://pmc.ncbi.nlm.nih.gov/articles/PMC5441397/ (blocked by a browser-verification page; nothing read)
2. https://pmc.ncbi.nlm.nih.gov/articles/PMC1397873/ (blocked by a browser-verification page; nothing read)
3. https://pmc.ncbi.nlm.nih.gov/articles/PMC124442/ (read)
4. https://www.ebi.ac.uk/europepmc/webservices/rest/PMC5441397/fullTextXML (read)
5. https://www.ebi.ac.uk/europepmc/webservices/rest/PMC1397873/fullTextXML (read)
6. https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.1093/jnci/95.1.14&resultType=core&format=json (no abstract)
7. https://api.openalex.org/works/doi:10.1109/MCI.2018.2866730 (read)
8. https://api.openalex.org/works/doi:10.1111/ecog.02881 (read)
9. https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.1073/pnas.102102699&resultType=core&format=json (read)
10. https://pubmed.ncbi.nlm.nih.gov/?term=10.1093%2Fjnci%2F95.1.14%5Bdoi%5D&format=abstract (blocked by a cookie page)
11. https://api.openalex.org/works/doi:10.1093/jnci/95.1.14 (read)

No GitHub page of the tool and no published evaluation material was fetched. No `ctx_*` tool was called. No other agent
was started. Git was not used. WebSearch was loaded but not used.

## Briefs drafted (15) and abandoned (0)

| id | source | subtype | family | statistic | data structure | sizes |
|---|---|---|---|---|---|---|
| B2B-01 | SIM03 | L1.1 | R-squared | out-of-sample R-squared | patients x genes, continuous survival | 50 x 2000 |
| B2B-02 | SIM03 | L1.1 | correlation | predicted-observed Pearson r | two predictor blocks | 80 x (1500 + 8) |
| B2B-03 | SAN18 | L1.2 | classification | F1, positive class | records x variables (SMOTE) | 600 x 12 |
| B2B-04 | SAN18 | L1.2 | classification | balanced accuracy | records x variables (SMOTE) | 1500 x 20 |
| B2B-05 | SAN18 | L1.4 | classification | sensitivity | records x variables (row copies) | 400 x 8 |
| B2B-06 | AMB02 | L1.3 | classification | error rate | tissues x genes (colon-like) | 62 x 2000 |
| B2B-07 | VAR06 | L1.3 | classification | error rate, tuned parameter | samples x genes | 40 x 2000 |
| B2B-08 | ROB17 | L3.1 | R-squared | out-of-sample R-squared | monthly series | 600 x 10 |
| B2B-09 | ROB17 | L3.2 | correlation | predicted-observed Pearson r | sites x plots x variables | 40 x 20 x 6 |
| B2B-10 | SAE17 | L3.2 | classification | error rate | subjects x windows x features, label per window | 30 x 30 x 40 |
| B2B-11 (reserve) | SIM03 | L1.1 | classification | AUC | patients x genes, binary relapse | 120 x 2000 |
| B2B-12 (reserve) | SAN18 | L1.4 | classification | AUC | records x variables (row copies) | 1000 x 15 |
| B2B-13 (reserve) | AMB02 | L1.3 | classification | AUC | samples x genes (leukaemia-like) | 72 x 2000 |
| B2B-14 (reserve) | ROB17 | L3.1 | other (RMSE / SD) | scaled root-mean-square error | daily series | 1500 x 6 |
| B2B-15 (reserve) | SAE17 | L3.2 | classification | AUC | subjects x records x variables, label per subject | 16 x 60 x 10 |

Revisions during drafting (no brief was abandoned):
- The first draft of B2B-01, B2B-07, B2B-11 and B2B-13 had 5000, 3000, 3000 and 7129 genes; the check of the size limits
  (at most 2000 per axis) caught this, and all four were cut to 2000 genes (B2B-13 keeps the source's 72 samples).
  The notes and note values were changed to match.
- B2B-04 was planned with a random forest and written with a 5-nearest-neighbour classifier after a rough cost estimate
  (no file ever held the forest version).

## Runs of code

1. `scratch\check_stats.py` (the structure-statistic check, allowed): builds arrays from each brief's shapes and sizes
   with random normal values (booleans with probability 0.2), asserts the size limits (at most 2000 per axis, 2 000 000
   values per array), runs each `stat(d)`.
   - First run: assertion failure on B2B-01 (5000 genes), the cause of the revision above.
   - Second run, all 15 statistics returned a finite float: B2B-01 40.0; 02 18.75; 03 0.193; 04 4.79; 05 0.2275; 06 32.26;
     07 50.0; 08 0.0046; 09 0.0003; 10 -0.0013; 11 16.67; 12 4.10; 13 27.78; 14 -0.0022; 15 -0.0008.
2. One inline Python run to rewrite the gene counts and text in `PRIVATE.json` (file editing, no analysis).
3. A text search of `BRIEFS.json` for the banned terms and for the words split, train, select, fold, oversampl,
   cross-valid: no match.

## Choices of statistic family, and where I could not move away from classification

The earlier combinations were (SIM03, L1.1, classification), (AMB02, L1.3, classification) and (VAR06, L1.3,
classification).
- SIM03: I used R-squared (B2B-01) and correlation (B2B-02) through the prognostic variant with a continuous outcome that
  the paper's title covers; the paper's own simulation is two-class, so the reserve B2B-11 stays classification (AUC).
- AMB02 and VAR06: the sources report only classification error rates, so I could not use another family while staying
  inside a setting they describe. The cases differ from each other in statistic (error rate vs AUC), sizes and step.
- SAN18: all cases are classification (imbalanced classification is the whole topic); they differ in statistic, sizes and
  duplication vs synthesis.
- ROB17 and SAE17: ROB17 uses R-squared, correlation and "other"; SAE17 stays classification (the source's own setting).

## Rules found hard to satisfy

- The source's own sizes exceed the limit of 2000 units on an axis for the leukaemia data (7129 genes) and VAR06 (6000
  features); I used 2000 and say so in the sizes notes.
- SAN18's exploited structure (a small positive class) cannot be stated in a brief; the claim speaks of "the positive
  class" only, and the world author may not make it rare. This is recorded in the private notes of B2B-03.
- For SIM03 I could read no abstract text or sizes (the record in Europe PMC has none and PubMed was blocked); the
  note values for B2B-01, B2B-02 and B2B-11 therefore all say "source states none".

## Repairs

Repair request 1 (2026-11-18), two notes; only `structure_statistic.note_value` and `note_value_source` changed:
- B2B-13, item (l): the note value 99.0 (7129 genes / 72 samples, the source's setting) cannot occur in the brief's
  setting, where the statistic genes/samples is 2000/72. New `note_value` 27.78; the source now says the value is set by the
  brief and gives the brief-size computation.
- B2B-07, item (l): the note value 150.0 (6000 / 40) cannot occur at the brief's 40 x 2000. New `note_value` 50.0, with
  the same kind of `note_value_source`.
- The brief, sizes, statistic code and every other field are unchanged. The other statistics set by the brief (B2B-01, 02,
  06, 11) already carried their value at the brief's sizes.
- I saw no count, rate or test result in the request.
