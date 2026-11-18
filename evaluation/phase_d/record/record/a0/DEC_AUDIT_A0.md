# Audit A0

- D-012: (l): yes ; approved_value=0.3. 0.3 within-plot ICC is a moderate, realistic value for quadrats within a plot; source states none; consistent with 10 plots x 30 quadrats.
- D-016: (l): yes ; approved_value=0.3. 0.3 litter ICC is a realistic moderate litter effect for 14 litters x 4 pups; source states none.
- D-021: (l): yes ; approved_value=0.3. 0.3 within-plot correlation across 12 dates of 8 plots is realistic and consistent with the setting; source states none.
- D-028: (l): no ; approved_value=None. 10000 voxels is realistic for whole-brain maps but contradicts the brief (1000 voxels, set_by_brief true) and exceeds the 2000-per-axis limit, so it cannot be realised in this setting.
- D-030: (l): yes ; approved_value=0.7. 0.7 split-half correlation of neuron rates across the 400 neurons (20 trials per half) is plausible; source states none.
- D-032: (l): n/a ; approved_value=None. structure statistic is null.
- D-033: (l): no ; approved_value=None. 30000 voxels is realistic for whole-brain maps but contradicts the brief (1000 voxels, set_by_brief true) and exceeds the 2000-per-axis limit.
- D-046: (l): yes ; approved_value=0.83. 0.83 matches LAZ10 PMC full text (Europe PMC XML PMC2817684: 'giving IC = 0.83', Figure 1 simulation, 2 rats x 10 measurements); value and location match.
- D-047: (l): yes ; approved_value=0.6. 0.6 screening-to-entry test-retest correlation of a self-reported symptom score is realistic; source states none.
- D-052: (l): yes ; approved_value=0.693. log(2)=0.693 (SD ratio 2) is a realistic variability difference consistent with the source's 'higher variance in one group'; source states none.
- D-061: (l): yes ; approved_value=18000.0. 18000 = 30x30x20 voxels, matches the quote in the KRI09 PMC text (pmc.ncbi.nlm.nih.gov/articles/PMC2841687: 'simulated ... 30 by 30 by 20 voxels and 200 time points'). Remark for part A: the brief has 1500 voxels, so the statistic on the brief's data cannot equal 18000 (set_by_brief true); items (f)/(m)/(p) will need to handle this.
- D-069: (l): yes ; approved_value=0.7. 0.7 baseline-to-6-month correlation of clinic systolic pressure in untreated patients is a realistic test-retest value; source states none.

URLs read:
- https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=EXT_ID:20074371 (lookup)
- https://www.ebi.ac.uk/europepmc/webservices/rest/PMC2817684/fullTextXML (LAZ10)
- https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.1038/nn.2303 (lookup)
- https://pmc.ncbi.nlm.nih.gov/articles/PMC2841687/ (KRI09)

Files read: FIDELITY_AUDIT_D.md, class\*rief.json, PRIVATE.json, PASSAGE.md. No helper computation except text grep of downloaded pages (scratch removed).

## Revision

First answers kept above (D-028 no, D-033 no, D-061 yes with 18000). After the brief author's revision:
- D-028: (l): yes; approved_value=1000.0. Revised value 1000 equals the brief's voxel count (set by the brief, within 2000 per axis); a reduced map keeps the many-candidates, few-subjects structure the source describes; source states no count.
- D-033: (l): yes; approved_value=1000.0. Revised value 1000 equals the brief's voxel count (within 2000 per axis); a reduced map still has many candidates for 60 trials; source states no count.
- D-061: (l): yes; approved_value=1500.0. Revised value 1500 equals the brief's voxel count, now honestly labelled as set by the brief; it no longer claims the source's 18000, which the sizes do not reproduce (reduced for timing; flag for part A (f)).

No new URLs read.
