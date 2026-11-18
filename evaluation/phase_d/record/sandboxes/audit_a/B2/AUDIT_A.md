# AUDIT_A, class B-2 (sandbox B2), 11 cases

## D-007 (SIM03, L1.1, R-squared)
- (a) yes: yes; resubstitution ridge fit vs 5-fold CV
- (b) yes: yes; standard correction (resubstitution ridge fit vs 5-fold CV)
- (c) yes: yes; diff of the two bodies is only the error line(s); mapping in CASE.md matches the diff (same ridge lam=p, same standardisation)
- (d) yes: yes; only allowed guards (non-finite, n/class minimum, zero variance); every MECH_CHECK comparison judged: none listed
- (e) yes: yes; no leak/overfit/bias/train/test/fold/split/select/duplicate/impute/resubstitution term and no negation of the claim (PB 4 list itself not in sandbox, own scan; 'out-of-sample' in D-007 claim is the claim's own estimand)
- (f) yes: yes; 50x2000 (genes at axis cap); source states no sizes: compared with typical microarray prognosis studies of tens of patients, thousands of genes; not documented; within 2000/axis and 2,000,000 values
- (g) yes: yes; same statistic, threshold, model, decision rule; cost comparable (CV = a few fits of the same size)
- (h) yes: yes; brief gives sizes, axes, meanings and the claim only
- (i) yes: yes; claim quantity is what the fixed body estimates
- (j) yes: yes; minus nulls only the claim's quantity (permuting/deranging the signal or labels), other quantities as plus
- (k) yes: yes; reference adds no key or dependence read only by the faulty body
- (m) yes: yes; statistic a function of the brief's keys, measures the exploited structure, unchanged in distribution by minus (class counts/shape/X unchanged)
- (p) yes: yes; reference reproduces the approved value (shape-fixed or measured in tolerance)
- overall: pass

## D-010 (KAP23, L1.2, correlation)
- (a) yes: yes; target encoding with all rows (incl. held-out) vs train-fold means
- (b) yes: yes; standard correction (target encoding with all rows (incl. held-out) vs train-fold means)
- (c) yes: yes; diff of the two bodies is only the error line(s); mapping in CASE.md matches the diff (target encoding is not literally in the quoted sentence but is pre-processing with labels on the whole dataset)
- (d) yes: yes; only allowed guards (non-finite, n/class minimum, zero variance); every MECH_CHECK comparison judged: none listed
- (e) yes: yes; no leak/overfit/bias/train/test/fold/split/select/duplicate/impute/resubstitution term and no negation of the claim (PB 4 list itself not in sandbox, own scan)
- (f) yes: yes; 1200x150 bool=180k values; source states none; not documented; within 2000/axis and 2,000,000 values
- (g) yes: yes; same statistic, threshold, model, decision rule; cost comparable (CV = a few fits of the same size)
- (h) yes: yes; brief gives sizes, axes, meanings and the claim only
- (i) yes: yes; claim quantity is what the fixed body estimates
- (j) yes: yes; minus nulls only the claim's quantity (permuting/deranging the signal or labels), other quantities as plus
- (k) yes: yes; reference adds no key or dependence read only by the faulty body
- (m) yes: yes; statistic a function of the brief's keys, measures the exploited structure, unchanged in distribution by minus (class counts/shape/X unchanged)
- (p) yes: yes; reference reproduces the approved value (shape-fixed or measured in tolerance)
- overall: pass

## D-011 (AMB02, L1.3, classification)
- (a) yes: yes; gene ranking on all samples vs inside each fold
- (b) yes: yes; standard correction (gene ranking on all samples vs inside each fold)
- (c) yes: yes; diff of the two bodies is only the error line(s); mapping in CASE.md matches the diff (same stratified folds/rng)
- (d) yes: yes; only allowed guards (non-finite, n/class minimum, zero variance); every MECH_CHECK comparison judged: none listed
- (e) yes: yes; no leak/overfit/bias/train/test/fold/split/select/duplicate/impute/resubstitution term and no negation of the claim (PB 4 list itself not in sandbox, own scan)
- (f) yes: yes; 72 samples as source (72 x 7129); genes reduced 7129->2000 to axis cap; reduced to cap; within 2000/axis and 2,000,000 values
- (g) yes: yes; same statistic, threshold, model, decision rule; cost comparable (CV = a few fits of the same size)
- (h) yes: yes; brief gives sizes, axes, meanings and the claim only
- (i) yes: yes; claim quantity is what the fixed body estimates
- (j) yes: yes; minus nulls only the claim's quantity (permuting/deranging the signal or labels), other quantities as plus
- (k) yes: yes; reference adds no key or dependence read only by the faulty body
- (m) yes: yes; statistic a function of the brief's keys, measures the exploited structure, unchanged in distribution by minus (class counts/shape/X unchanged)
- (p) yes: yes; reference reproduces the approved value (shape-fixed or measured in tolerance)
- overall: pass

## D-022 (KAP23, L1.1, correlation)
- (a) yes: yes; in-sample fit vs 5-fold CV of the same 66-term OLS
- (b) yes: yes; standard correction (in-sample fit vs 5-fold CV of the same 66-term OLS)
- (c) yes: yes; diff of the two bodies is only the error line(s); mapping in CASE.md matches the diff
- (d) yes: yes; only allowed guards (non-finite, n/class minimum, zero variance); every MECH_CHECK comparison judged: none listed
- (e) yes: yes; no leak/overfit/bias/train/test/fold/split/select/duplicate/impute/resubstitution term and no negation of the claim (PB 4 list itself not in sandbox, own scan)
- (f) yes: yes; 300x10; source states none; not documented; within 2000/axis and 2,000,000 values
- (g) yes: yes; same statistic, threshold, model, decision rule; cost comparable (CV = a few fits of the same size)
- (h) yes: yes; brief gives sizes, axes, meanings and the claim only
- (i) yes: yes; claim quantity is what the fixed body estimates
- (j) yes: yes; minus nulls only the claim's quantity (permuting/deranging the signal or labels), other quantities as plus
- (k) yes: yes; reference adds no key or dependence read only by the faulty body
- (m) yes: yes; statistic a function of the brief's keys, measures the exploited structure, unchanged in distribution by minus (class counts/shape/X unchanged)
- (p) yes: yes; reference reproduces the approved value (shape-fixed or measured in tolerance)
- overall: pass

## D-027 (KAP23, L1.1, other (MAE skill))
- (a) yes: yes; in-sample vs 5-fold CV
- (b) yes: yes; standard correction (in-sample vs 5-fold CV)
- (c) yes: yes; diff of the two bodies is only the error line(s); mapping in CASE.md matches the diff (baseline mean predictor also moved to training-fold mean, a consistent part of the out-of-sample correction)
- (d) yes: yes; only allowed guards (non-finite, n/class minimum, zero variance); every MECH_CHECK comparison judged: none listed
- (e) yes: yes; no leak/overfit/bias/train/test/fold/split/select/duplicate/impute/resubstitution term and no negation of the claim (PB 4 list itself not in sandbox, own scan)
- (f) yes: yes; 60x25; source states none; not documented; within 2000/axis and 2,000,000 values
- (g) yes: yes; same statistic, threshold, model, decision rule; cost comparable (CV = a few fits of the same size)
- (h) yes: yes; brief gives sizes, axes, meanings and the claim only
- (i) yes: yes; claim quantity is what the fixed body estimates
- (j) yes: yes; minus nulls only the claim's quantity (permuting/deranging the signal or labels), other quantities as plus
- (k) yes: yes; reference adds no key or dependence read only by the faulty body
- (m) yes: yes; statistic a function of the brief's keys, measures the exploited structure, unchanged in distribution by minus (class counts/shape/X unchanged)
- (p) yes: yes; reference reproduces the approved value (shape-fixed or measured in tolerance)
- overall: pass

## D-035 (SAN18, L1.2, classification)
- (a) yes: yes; SMOTE on all records before CV and scoring on synthetic rows vs SMOTE in training folds only
- (b) yes: yes; standard correction (SMOTE on all records before CV and scoring on synthetic rows vs SMOTE in training folds only)
- (c) yes: yes; diff of the two bodies is only the error line(s); mapping in CASE.md matches the diff (SMOTE guard nmin<2/nsyn==0 is identical in both and is a definedness guard)
- (d) yes: yes; only allowed guards (non-finite, n/class minimum, zero variance); every MECH_CHECK comparison judged: none listed
- (e) yes: yes; no leak/overfit/bias/train/test/fold/split/select/duplicate/impute/resubstitution term and no negation of the claim (PB 4 list itself not in sandbox, own scan)
- (f) yes: yes; 1500x20; source (abstract) states none; not documented; within 2000/axis and 2,000,000 values
- (g) yes: yes; same statistic, threshold, model, decision rule; cost comparable (CV = a few fits of the same size)
- (h) yes: yes; brief gives sizes, axes, meanings and the claim only
- (i) yes: yes; claim quantity is what the fixed body estimates
- (j) yes: yes; minus nulls only the claim's quantity (permuting/deranging the signal or labels), other quantities as plus
- (k) yes: yes; reference adds no key or dependence read only by the faulty body
- (m) yes: yes; statistic a function of the brief's keys, measures the exploited structure, unchanged in distribution by minus (class counts/shape/X unchanged)
- (p) yes: yes; reference reproduces the approved value (shape-fixed or measured in tolerance)
- overall: pass

## D-042 (KAP23, L1.4, correlation)
- (a) yes: yes; i mod 5 folds vs near-duplicate components kept whole in a fold (0.1 x median distance, same definition as the structure statistic)
- (b) yes: yes; standard correction (i mod 5 folds vs near-duplicate components kept whole in a fold (0.1 x median distance, same definition as the structure statistic))
- (c) yes: yes; diff of the two bodies is only the error line(s); mapping in CASE.md matches the diff
- (d) yes: yes; only allowed guards (non-finite, n/class minimum, zero variance); every MECH_CHECK comparison judged: none listed
- (e) yes: yes; no leak/overfit/bias/train/test/fold/split/select/duplicate/impute/resubstitution term and no negation of the claim (PB 4 list itself not in sandbox, own scan)
- (f) yes: yes; 1200x20; source states none; not documented; within 2000/axis and 2,000,000 values
- (g) yes: yes; same statistic, threshold, model, decision rule; cost comparable (CV = a few fits of the same size)
- (h) yes: yes; brief gives sizes, axes, meanings and the claim only; 'compound record' wording weak, no duplication stated
- (i) yes: yes; claim quantity is what the fixed body estimates
- (j) yes: yes; minus nulls only the claim's quantity (permuting/deranging the signal or labels), other quantities as plus
- (k) yes: yes; reference adds no key or dependence read only by the faulty body
- (m) yes: yes; statistic a function of the brief's keys, measures the exploited structure, unchanged in distribution by minus (class counts/shape/X unchanged)
- (p) yes: yes; reference statistic measured about 0.345 against approved 0.3, inside the pre-registered tolerance 0.2*|0.3-0| = 0.06 but at its upper edge (structure author chose it deliberately); remark only
- overall: pass

## D-055 (KAP23, L3.1, correlation)
- (a) yes: yes; random-permutation folds vs forward chaining (6 blocks, evaluated on blocks 2-6)
- (b) yes: yes; standard correction (random-permutation folds vs forward chaining (6 blocks, evaluated on blocks 2-6))
- (c) yes: yes; diff of the two bodies is only the error line(s); mapping in CASE.md matches the diff (the 5-day gap before each block is a standard embargo, a small addition inside the correction)
- (d) yes: yes; only allowed guards (non-finite, n/class minimum, zero variance); every MECH_CHECK comparison judged: none listed
- (e) yes: yes; no leak/overfit/bias/train/test/fold/split/select/duplicate/impute/resubstitution term and no negation of the claim (PB 4 list itself not in sandbox, own scan)
- (f) yes: yes; 1000x6; source states none; not documented; within 2000/axis and 2,000,000 values
- (g) yes: yes; same statistic, threshold, model, decision rule; cost comparable (CV = a few fits of the same size)
- (h) yes: yes; brief gives sizes, axes, meanings and the claim only
- (i) yes: yes; claim quantity is what the fixed body estimates
- (j) yes: yes; minus nulls only the claim's quantity (permuting/deranging the signal or labels), other quantities as plus
- (k) yes: yes; reference adds no key or dependence read only by the faulty body
- (m) yes: yes; statistic a function of the brief's keys, measures the exploited structure, unchanged in distribution by minus (class counts/shape/X unchanged)
- (p) yes: yes; reference reproduces the approved value (shape-fixed or measured in tolerance)
- overall: pass

## D-064 (SIM03, L1.1, correlation)
- (a) yes: yes; resubstitution ridge vs 10-fold CV
- (b) yes: yes; standard correction (resubstitution ridge vs 10-fold CV)
- (c) yes: yes; diff of the two bodies is only the error line(s); mapping in CASE.md matches the diff (SIM03 concerns class prediction, regression variant is an extension of the same resubstitution error)
- (d) yes: yes; only allowed guards (non-finite, n/class minimum, zero variance); every MECH_CHECK comparison judged: none listed
- (e) yes: yes; no leak/overfit/bias/train/test/fold/split/select/duplicate/impute/resubstitution term and no negation of the claim (PB 4 list itself not in sandbox, own scan)
- (f) yes: yes; 80x(1500+8); source states none; not documented; within 2000/axis and 2,000,000 values
- (g) yes: yes; same statistic, threshold, model, decision rule; cost comparable (CV = a few fits of the same size)
- (h) yes: yes; brief gives sizes, axes, meanings and the claim only
- (i) yes: yes; claim quantity is what the fixed body estimates
- (j) yes: yes; minus nulls only the claim's quantity (permuting/deranging the signal or labels), other quantities as plus
- (k) yes: yes; reference adds no key or dependence read only by the faulty body
- (m) yes: yes; statistic a function of the brief's keys, measures the exploited structure, unchanged in distribution by minus (class counts/shape/X unchanged)
- (p) yes: yes; reference reproduces the approved value (shape-fixed or measured in tolerance)
- overall: pass

## D-066 (KAP23, L1.4, classification)
- (a) yes: yes; copy minority rows on all data then i mod 5 vs stratified folds with copying inside training folds
- (b) yes: yes; standard correction (copy minority rows on all data then i mod 5 vs stratified folds with copying inside training folds)
- (c) yes: yes; diff of the two bodies is only the error line(s); mapping in CASE.md matches the diff (stratification is a standard accompaniment (guards each fold has positives), remark only; the guard comparisons <2 per class in MECH_CHECK are class-count guards identical in both bodies)
- (d) yes: yes; only allowed guards (non-finite, n/class minimum, zero variance); every MECH_CHECK comparison judged: class-count minimum 2 (allowed, same in both)
- (e) yes: yes; no leak/overfit/bias/train/test/fold/split/select/duplicate/impute/resubstitution term and no negation of the claim (PB 4 list itself not in sandbox, own scan)
- (f) yes: yes; 1000x15; source states none; not documented; within 2000/axis and 2,000,000 values
- (g) yes: yes; same statistic, threshold, model, decision rule; cost comparable (CV = a few fits of the same size)
- (h) yes: yes; brief gives sizes, axes, meanings and the claim only; 'rare outcome' is a prevalence statement, not an arrangement fact
- (i) yes: yes; claim quantity is what the fixed body estimates
- (j) yes: yes; minus nulls only the claim's quantity (permuting/deranging the signal or labels), other quantities as plus
- (k) yes: yes; reference adds no key or dependence read only by the faulty body
- (m) yes: yes; statistic a function of the brief's keys, measures the exploited structure, unchanged in distribution by minus (class counts/shape/X unchanged)
- (p) yes: yes; reference reproduces the approved value (shape-fixed or measured in tolerance)
- overall: pass

## D-070 (SIM03, L1.1, classification)
- (a) yes: yes; in-sample logistic AUC vs 10-fold stratified CV AUC
- (b) yes: yes; standard correction (in-sample logistic AUC vs 10-fold stratified CV AUC)
- (c) yes: yes; diff of the two bodies is only the error line(s); mapping in CASE.md matches the diff (MECH comparison 1e-9 is the Newton convergence tolerance, identical in both)
- (d) yes: yes; only allowed guards (non-finite, n/class minimum, zero variance); every MECH_CHECK comparison judged: Newton convergence tolerance, numeric, same in both
- (e) yes: yes; no leak/overfit/bias/train/test/fold/split/select/duplicate/impute/resubstitution term and no negation of the claim (PB 4 list itself not in sandbox, own scan)
- (f) yes: yes; 120x2000 (genes at cap); source states none; not documented; within 2000/axis and 2,000,000 values
- (g) yes: yes; same statistic, threshold, model, decision rule; cost comparable (CV = a few fits of the same size)
- (h) yes: yes; brief gives sizes, axes, meanings and the claim only
- (i) yes: yes; claim quantity is what the fixed body estimates
- (j) yes: yes; minus nulls only the claim's quantity (permuting/deranging the signal or labels), other quantities as plus
- (k) yes: yes; reference adds no key or dependence read only by the faulty body
- (m) yes: yes; statistic a function of the brief's keys, measures the exploited structure, unchanged in distribution by minus (class counts/shape/X unchanged)
- (p) yes: yes; reference reproduces the approved value (shape-fixed or measured in tolerance)
- overall: pass

## Sizes list
Reduced to cap: D-011 (genes 7129 -> 2000), D-007 / D-070 genes at the 2000 cap.
Not documented by the source: all other pairs (D-007, D-010, D-022, D-027, D-035, D-042, D-055, D-064, D-066, D-070).

## Remarks
Class and subtype follow PB 1 for all 11 (L1.1: D-007, D-022, D-027, D-064, D-070; L1.2: D-010, D-035; L1.3: D-011; L1.4: D-042, D-066; L3.1: D-055). Criterion returns True exactly when the claimed statistic meets its threshold in all cases.
## URLs read
- https://pmc.ncbi.nlm.nih.gov/articles/PMC10499856 (KAP23 taxonomy quotes confirmed)
- https://pubmed.ncbi.nlm.nih.gov/12509396/ (SIM03; cookie page, no content)
No helper computation was run; no criterion called on data.
