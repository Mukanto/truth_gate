# AUDIT_A0 (item l)

Helper computation: none beyond reading files and arithmetic. No criterion run.

URLs read:
- https://www.ebi.ac.uk/europepmc/webservices/rest/PMC1397873/fullTextXML
- https://pmc.ncbi.nlm.nih.gov/articles/PMC124442/
- https://www.ebi.ac.uk/europepmc/webservices/rest/PMC124442/fullTextXML (HTTP 500, nothing read)
- https://www.pnas.org/doi/full/10.1073/pnas.102102699 (blocked page, nothing read)

| case | l | approved_value | reason |
|---|---|---|---|
| D-003 | yes | 9.0 | Source states no ratio; 9.0 (90/10) is a typical imbalance for the oversampling setting; ~100 events in 1000 records is workable. |
| D-004 | yes | 0.8 | Source states none; lag-1 autocorrelation 0.8 is typical of slowly varying daily predictors; consistent with the daily panel setting. |
| D-005 | yes | 1.5 | Brief's own size: 150 features / 100 samples = 1.5, matches brief dims (100,150); realistic for a biomarker panel. |
| D-007 | yes | 40.0 | Brief's own ratio 2000 genes / 50 patients = 40 matches dims (50,2000); typical microarray prognosis setting. |
| D-010 | yes | 0.125 | 150 districts / 1200 patients = 0.125 matches dims (1200,150); realistic (about 8 patients per district). |
| D-011 | no | None | Quote is right (PMC124442: n=72, p=7,129, leukaemia; 7129/72=99.0), but the brief has 72x2000 and the statistic is shape[1]/shape[0], which is 27.78 on the brief's data; 99.0 cannot occur in the brief's setting. Realistic value would be 2000/72=27.78. |
| D-013 | no | None | Quote is right (PMC1397873 Methods: 40 samples, 6000 features; 150), but the brief has 40x2000 and the statistic is shape[1]/shape[0] = 50 on the brief's data; 150 cannot occur in the brief's setting. Consistent value would be 50. |
| D-014 | yes | 0.25 | Source states no rate; 25% missing is a typical rate for a laboratory panel; claim and 20 lab values consistent. |
| D-018 | yes | 0.3 | Source states none; between-subject ICC 0.3 is a moderate, realistic share for repeated sensor recordings. |
| D-022 | yes | 0.2167 | Brief's own size: (10*13/2)/300 = 0.2167 matches dims (300,10). |
| D-024 | yes | 32.26 | Verified in PMC124442: colon n=62, p=2,000; 2000/62=32.26 matches brief dims (62,2000). |
| D-027 | yes | 0.4167 | Brief's own size: 25/60 = 0.4167 matches dims (60,25). |
| D-029 | yes | 0.3 | Source gives no duplicate share; 30% near-identical partners is high but plausible for a registry with repeated entries; consistent with the setting. |
| D-034 | yes | 0.6 | Source states none; lag-7 autocorrelation 0.6 is typical of daily hydro-meteorological drivers. |
| D-035 | yes | 9.0 | Source states no ratio; 9.0 (90/10) is typical for an imbalanced-data setting; 150 positives in 1500. |
| D-039 | yes | 0.9 | Source states none; lag-1 autocorrelation 0.9 is plausible for slowly varying monthly series. |
| D-041 | yes | 0.3 | Source gives no rate; 30% missing is realistic for country-year indicators. |
| D-042 | yes | 0.3 | Source gives no duplicate share; 30% is high but plausible for compound records with repeated entries. |
| D-043 | yes | 0.1 | Source states no ratio; minority share 0.1 is typical (40 positives in 400). |
| D-044 | yes | 0.5 | Source states none; ICC 0.5 is a moderate, realistic within-subject share for trial features. |
| D-049 | yes | 0.1 | Source states no ratio; minority share 0.1 is typical (60 positives in 600). |
| D-054 | yes | 12.5 | Brief's own size: 1000/80 = 12.5 matches dims (80,1000); realistic. |
| D-055 | yes | 0.8 | Source states none; lag-1 autocorrelation 0.8 typical of slowly varying daily predictors. |
| D-058 | yes | 0.3 | Source states none; ICC 0.3 plausible for windowed features across subjects. |
| D-059 | yes | 0.7 | Source states none; lag-1 autocorrelation 0.7 plausible for monthly environmental series. |
| D-060 | yes | 5.0 | Brief's own size: 500/100 = 5.0 matches dims (100,500). |
| D-064 | yes | 18.75 | Brief's own ratio 1500/80 = 18.75 matches dims (80,1500). |
| D-065 | yes | 0.3 | Source states none; between-site ICC 0.3 is a typical share of variance. |
| D-066 | yes | 0.08 | Source gives no share; 8% minority is a realistic rare-outcome rate (80 in 1000). |
| D-070 | yes | 16.67 | Brief's own ratio 2000/120 = 16.67 matches dims (120,2000). |

## Revision (D-011, D-013)

The brief author revised the structure value of both cases. The table above keeps my first answers.

| case | first answer | revised value | new answer | reason |
|---|---|---|---|---|
| D-011 | no (value 99.0 not attainable at 72x2000) | 27.78 | yes | 2000/72 = 27.78 is the statistic at the brief's dims; the source ratio 99.0 is stated as not occurring at these sizes. |
| D-013 | no (value 150 not attainable at 40x2000) | 50.0 | yes | 2000/40 = 50 is the statistic at the brief's dims; the source ratio 150 is stated as not occurring at these sizes. |

Totals after revision: 30 yes, 0 no, 0 n/a. No URLs read in this revision.
