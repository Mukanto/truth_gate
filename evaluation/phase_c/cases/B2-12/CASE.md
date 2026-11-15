# CASE B2-12

## 1. Identity
Case id B2-12; world id C07; class B-2; subtype L1.3; source key AMB02.

## 2. Source and documenting passage
AMB02 abstract (Europe PMC record): earlier error estimates did not account for selection bias, because the same samples were used for gene selection and testing, or because gene selection was not repeated within each cross-validation step (as read by the part-1 author).

Who read it and how: AMB02 (Ambroise and McLachlan 2002). Read by the part-1 brief author as the Europe PMC abstract record (https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.1073/pnas.102102699&format=json&resultType=core) and search snippets only; the full text was blocked. I (part 2) read nothing of it.

## 3. The brief (as in ASSIGNMENT.json)
```json
{
  "id": "C07",
  "claim": "A classifier that uses three genes distinguishes tumour from normal colon tissue with an accuracy of at least 0.70 on new tissue samples.",
  "data_keys": [
    {
      "key": "expression",
      "shape": "(tissues, genes)",
      "dtype": "float",
      "meaning": "expression level of each gene in each colon tissue sample"
    },
    {
      "key": "tumour",
      "shape": "(tissues,)",
      "dtype": "bool",
      "meaning": "True when the tissue sample is tumour tissue"
    }
  ],
  "sizes": "tissues = 62; genes = 1000"
}
```

## 4. Mapping
Faulty: the genes are ranked by the pooled-variance two-sample t statistic on all 62 tissues, the top 3 kept, and the accuracy of a nearest-centroid classifier on those 3 genes is estimated by stratified 10-fold CV (the gene choice made before the CV, on all tissues). Fixed: external CV: the ranking and the choice of the top 3 genes are repeated inside every training fold; accuracy pooled over the held-out tissues. Same classifier, folds and threshold (accuracy >= 0.70).

Estimand line. Faulty: CV accuracy of a 3-gene classifier whose genes were chosen with all tissues, including the held-out ones. Fixed: accuracy on tissues not used to choose the genes or fit the classifier (the whole procedure).

Allowed-guard minimum used. Both: at least 2 tissues of each class in every training fold of the 10-fold structure (at least 3 per class in the data; also what the t statistic needs); non-finite expression gives None.

## 5. Pre-checks of the fixed criterion (plain Python, scratch scripts in work\; the faulty criterion was never run, only syntax-checked)
n = 100: plus 100, minus 2, control 1, noise 1, zeros None 100. Final, n = 200: plus 200/200, minus 0/200, control 8/200 (0.04), noise 2/200, zeros 200 None.

Number of revisions of the fixed criterion: 0.

## 6. Timing (final fixed criterion)
t = 0.0022 s (mean of 200 calls on plus samples), g = 0.0009 s (mean plus generation), S = 6 (2 worlds + 2 control(s)/relational pair(s) + 2 probes), estimate 2 x 200 x (S + 1) x (t + g) = 9 s (limit 900 s). No size request needed.

## 7. Deviations, problems, skeleton requests
The classifier (nearest centroid on the standardised 3 genes) is my choice (the note says 'a classifier'). Gene axis 1000 (skeleton) instead of the source's 2000. The source was read only as an abstract by the part-1 author, which the note flags.

Skeleton requests: none.

## Designer lines (PREREG_PHASE_C §3; added by the designer after the fidelity audit)

- Overlap with Phase B: yes, Phase B case B2-03.
- Mechanism tag / statistic family (private note): L1.3 / classification.
- Allowed-guard minimum (private note): at least 2 tissues per class in every fitting set and at least 1 tissue in each scored set (two classes needed for the t statistic: at least 2 per class).
- Size ratio (brief size to source size): source states none (as read; the author's 62 x 2000 from memory is unverified).
- The estimand line is in item 4 (criterion author).
