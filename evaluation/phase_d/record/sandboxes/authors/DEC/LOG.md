# LOG, author DEC (decoys B-1 and B-6)

Interruption: work stopped once on an API usage limit and was resumed on the coordinator's instruction (same rules). No file outside the sandbox was read. The sandbox also holds `scratch/check_stats.py`.

## Briefs written (12: 8 cases + 4 reserves)

| local_id | source | class | tag | family | reserve |
|---|---|---|---|---|---|
| DEC-01 | KRI09 | B-1 | select-then-test-same-data | proportion | no |
| DEC-02 | VUL09 | B-1 | select-then-test-same-data | correlation | no |
| DEC-03 | MOR03 | B-1 | extreme-group-change | proportion | no |
| DEC-04 | BAR05 | B-1 | split-by-baseline-compare-change | mean | no |
| DEC-05 | NIE11 | B-6 | significant-here-not-there | proportion | no |
| DEC-06 | HUR84 | B-6 | units-not-independent | proportion | no |
| DEC-07 | LAZ10 | B-6 | units-not-independent | regression-slope | no |
| DEC-08 | LAZ18 | B-6 | units-not-independent | correlation | no |
| DEC-R1 | KRI10 | B-1 | select-then-test-same-data | correlation | yes |
| DEC-R2 | MAK19 | B-1 | split-by-baseline-compare-change | proportion | yes |
| DEC-R3 | MAK19 | B-6 | significant-here-not-there | mean | yes |
| DEC-R4 | HUR84 | B-6 | units-not-independent | proportion | yes |

## Drafts abandoned (3)

1. VUL09 with R-squared (variance of the trait explained by the region's mean activation): abandoned because choosing voxels on all subjects and then scoring a fit sits next to B-2 (feature selection on all data), which wins the tie-break. Replaced by correlation.
2. KRI09 pattern-information example (decoding accuracy after choosing voxels): abandoned, a classification score belongs to B-2.
3. LAZ10 rotarod day slope within animals (10 rats, 3 days): abandoned, a pooled regression with a within-animal predictor is conservative, not too liberal, so the error would not appear. Replaced by a dose that varies between animals.

## Rules I could not satisfy

- VUL09: every family the source allows other than the three used earlier (R-squared, proportion, other) was unusable or duplicated (see abandoned draft 1, and DEC-01 is proportion); I used correlation, the source's own statistic, and said so in the private note.
- Structure statistic for DEC-05 (NIE11) is null: no statistic of the data has the same expected value in the claim-true and claim-false versions (the error depends on the common effect size). Said so in the private note.
- Several "source states none" note values (DEC-02, 03, 04, 06, 08, R1, R2, R3, R4) because the readable parts of the sources give no number; each has its reason in the note.
- The briefs do not say how patients were assigned to treatment (DEC-04), because that would state how units are related; the world author has to build a world where the fixed contrast is meaningful.

## Structure statistic checks (the one allowed use of code)

Script `scratch/check_stats.py` read BRIEFS.json and PRIVATE.json, generated random arrays with each brief's shapes (normal floats, Bernoulli(0.5) bools), executed each `structure_statistic.code` and printed type and value. Run once, after both files were written. Result: every statistic returned a finite Python float (DEC-01 1500.0, DEC-02 1000.0, DEC-03 0.029, DEC-04 -0.073, DEC-06 0.008, DEC-07 -0.001, DEC-08 -0.066, DEC-R1 1000.0, DEC-R2 -0.004, DEC-R3 0.087, DEC-R4 -0.064; DEC-05 has none). A grep of BRIEFS.json for the banned terms found none.

## Sources read, and how

All reads went through WebFetch (a summarising tool: I received its answers to my prompts, not the raw pages) and WebSearch. The tool also saved some PDFs to its own results folder on this machine; I did not open them.

- KRI09: PMC full text (summary of examples, simulation sizes, quotes).
- KRI10: PMC full text (summary).
- MOR03: PMC full text (summary: examples, the passage).
- BAR05: abstract only (publisher page); PubMed page and two copies of the full text unreadable or empty.
- VUL09: abstract through Europe PMC; full-text PDF unreadable.
- NIE11: abstract through Europe PMC (review figures); journal page redirected and not followed.
- HUR84: abstract as reproduced by search summaries and SOURCES_D; the three PDF copies are scans without text, so the full text was not read. Forms of pseudoreplication (simple, sacrificial, temporal) were taken from secondary summaries returned by WebSearch.
- LAZ10: full text through Europe PMC XML, first 100000 of 166051 characters.
- LAZ18: PMC full text (summary).
- MAK19: PMC full text, first 100000 of 204772 characters.

## URLs

1. https://pmc.ncbi.nlm.nih.gov/articles/PMC2841687/ (KRI09, read)
2. https://pmc.ncbi.nlm.nih.gov/articles/PMC2896926/ (a wrong paper, nothing used)
3. https://pmc.ncbi.nlm.nih.gov/articles/PMC1126032/ (verification page, nothing read)
4. https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.1038/jcbfm.2010.86&format=json&resultType=lite
5. https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.1136/bmj.326.7398.1083&format=json&resultType=lite
6. https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.1093/ije/dyh299&format=json&resultType=lite
7. https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.1186/1471-2202-11-5&format=json&resultType=lite
8. https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.1371/journal.pbio.2005282&format=json&resultType=lite
9. https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.7554/eLife.48175&format=json&resultType=lite
10. https://pmc.ncbi.nlm.nih.gov/articles/PMC2949251/ (KRI10, read)
11. https://pmc.ncbi.nlm.nih.gov/articles/PMC1125994/ (MOR03, read)
12. https://pmc.ncbi.nlm.nih.gov/articles/PMC2817684/ (LAZ10, verification page)
13. https://pmc.ncbi.nlm.nih.gov/articles/PMC5902037/ (LAZ18, read)
14. https://pmc.ncbi.nlm.nih.gov/articles/PMC6785265/ (MAK19, read in part)
15. https://bmcneurosci.biomedcentral.com/articles/10.1186/1471-2202-11-5 (redirect)
16. https://pubmed.ncbi.nlm.nih.gov/15333621/ (cookie page)
17. https://academic.oup.com/ije/article/34/1/215/625737 (BAR05 abstract)
18. https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.1111/j.1745-6924.2009.01125.x&format=json&resultType=lite
19. https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.1038/nn.2886&format=json&resultType=core (NIE11 abstract)
20. https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.2307/1942661&format=json&resultType=core (no hits)
21. https://link.springer.com/article/10.1186/1471-2202-11-5 (redirect, not followed)
22. https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=EXT_ID:26158964%20AND%20SRC:MED&format=json&resultType=core (VUL09 abstract)
23. WebSearch: "Hurlbert 1984 Pseudoreplication and the design of ecological field experiments abstract"
24. https://www.ebi.ac.uk/europepmc/webservices/rest/PMC2817684/fullTextXML (LAZ10, read in part)
25. https://www.zoology.ubc.ca/~bio501/R/readings/hurlbert%201984%20ecol%20monogr%20-%20pseudoreplication.pdf (HUR84 scan, unreadable)
26. https://biomedical-sciences.ed.ac.uk/sites/default/files/2024-08/Hurlbert%20article%201984.pdf (unreadable)
27. https://groups.nceas.ucsb.edu/flow-experiments/documents/theory-and-concepts/hurlbert.1984.EcoMono.pdf/at_download/file (unreadable)
28. https://zendy.io/title/10.2307/1942661 (empty)
29. https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.1016/j.tree.2009.07.001%20OR%20%22Hurlbert%22%20AND%20%22pseudoreplication%22&format=json&resultType=lite&pageSize=3 (irrelevant result, nothing used)
30. http://www.edvul.com/pdf/VulHarrisWinkielmanPashler-PPS-2009.pdf (404)
31. WebSearch: "Hurlbert pseudoreplication temporal / sacrificial / simple pseudoreplication" (secondary sources)
32. WebSearch: "Vul Harris Winkielman Pashler 2009 ... nonindependence error simulation ..."
33. https://pages.ucsd.edu/~pwinkiel/vul-etal_correlations-main-2009.pdf (unreadable)
34. WebSearch: "Barnett van der Pols Dobson 2005 ... pdf eprints.qut.edu.au"
35. https://www.nature.com/articles/nn.2886 (redirect, not followed)
36. https://typeset.io/pdf/regression-to-the-mean-what-it-is-and-how-to-deal-with-it-2d43x2i6ei.pdf (redirect)
37. https://scispace.com/pdf/regression-to-the-mean-what-it-is-and-how-to-deal-with-it-2d43x2i6ei.pdf (empty)

Nothing was fetched from any GitHub repository of the tool or from material of its evaluations. No ctx_* tool, no other agent, no git.

## Repair (structure value of three notes)

Request: the structure value of DEC-01, DEC-02 and DEC-R1, each a statistic set by the brief (it reports the number of voxels), had a note value that cannot occur at the brief's sizes. Changed only `structure_statistic.note_value` and `note_value_source` in PRIVATE.json:
- DEC-01: note_value 18000.0 -> 1500.0 (the brief's 1500 voxels; the source's 18000 is mentioned in the source field text only as context).
- DEC-02: note_value 10000.0 -> 1000.0 (the brief's 1000 voxels).
- DEC-R1: note_value 30000.0 -> 1000.0 (the brief's 1000 voxels).
The code, direction, null_value, set_by_brief, the briefs and all other fields are unchanged. I saw no count, rate or test result from any later check; the request quoted only the failing items.
