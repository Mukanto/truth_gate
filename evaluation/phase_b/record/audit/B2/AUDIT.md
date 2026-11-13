# Fidelity audit, class B-2 (cases b2-01 to b2-12)

Auditor: blind fidelity auditor (fresh agent). Read: AUDIT_PHASE.md, PREREG_PHASE_B.md, SOURCES.md, REVISIONS-post-freeze.md, the B2 class folder (ASSIGNMENT, CASE.md, skeleton, faulty, fixed for all 12; PRIVATE.json, LOG.md, quotes.tsv, new34.txt, SIM03 extract) and the b2-* entries of STEP5_MECH_CHECK.json. No criterion was called on any data and no gate was run. Only text comparisons were run: unified diff of faulty against fixed, string equality of skeleton, faulty and fixed outside the criterion body (equal in all 12), and a regex for banned stems over the briefs (no hit). I did not run any helper computation.

## b2-01 (SIM03, L1.1): PASS

- (a) yes. Faulty builds gene selection (top 5 by |t|), pooled-sd weights and a nearest-centroid rule on all 20 samples and scores the same 20 samples: the resubstitution estimate of the SIM03 passage (20 profiles, 10 per class, 98.2% zero misclassifications under no difference; quote found in SIM03_openalex_abstract.txt).
- (b) yes. Fixed redoes selection, weights and rule inside leave-one-out with the left-out sample removed first: the fully cross-validated correction SIM03 describes; nothing else changed.
- (c) yes. The diff is the single prediction line replaced by the LOO loop; both files equal the skeleton outside the criterion body (text comparison).
- (d) yes. Only allowed guards: np.isfinite check, class counts too small, zero variance (x.std>0), each returning None; the mechanical comparisons listed by the designer are exactly these; no test for noise, zeros or shuffle.
- (e) yes. No banned stem in the brief (own regex over the whole brief JSON); the claim is positive and gives only statistic and threshold, no negation of the claim.
- (f) yes. SIM03 simulation: 20 profiles, 10 per class; brief says 20 samples, 10 per class (matches). 6000 genes reduced to the cap of 60 (P-2 case 2).
- (g) yes. Same accuracy statistic, threshold 0.80, same fit() helper; fixed costs 20 fits instead of 1, inherent in the correction and timed (2 s).
- Note: Source read only through the designer's reconstruction text; nearest centroid and the 5-gene rule are author choices not in the text.
- The criterion returns True exactly when the estimated score reaches the brief's threshold and None only on the allowed guards. Class and subtype follow the section 1 rules: agreed.

## b2-02 (SIM03, L1.1): PASS

- (a) yes. Faulty fits ridge logistic regression on all 30 patients and computes AUC on the same patients: the resubstitution estimate defined in the SIM03 passage.
- (b) yes. Fixed refits the whole model with each fold removed first (5-fold, pooled out-of-fold scores, same AUC): the cross-validated correction SIM03 names.
- (c) yes. The diff is only the AUC line replaced by the 5-fold loop; _folds, _auc, _logit identical.
- (d) yes. Only allowed guards: np.isfinite check, class counts too small, zero variance (x.std>0), each returning None; the mechanical comparisons listed by the designer are exactly these; no test for noise, zeros or shuffle. The Newton-step test |step|<1e-8 is a convergence criterion, not a look at the input.
- (e) yes. No banned stem in the brief (own regex over the whole brief JSON); the claim is positive and gives only statistic and threshold, no negation of the claim.
- (f) yes. SIM03 states no sizes for such a model; it says class-prediction studies on fewer than 50 specimens are common and cites a 5-year breast-cancer outcome example. 30 patients, 20 markers are of that order (P-2 case 1: not documented by the source).
- (g) yes. Same AUC statistic, threshold 0.75, same logistic fit; 5 fits against 1.
- The criterion returns True exactly when the estimated score reaches the brief's threshold and None only on the allowed guards. Class and subtype follow the section 1 rules: agreed.

## b2-03 (AMB02, L1.3): PASS

- (a) yes. Faulty pre-reduces to 20 genes by |t| and runs forward selection by leave-one-out error on all 62 tissues, then reports 1 minus the internal LOO error of the final 3-gene Fisher rule: the CV1IE of AMB02 with selection bias (3 genes as documented). Code read: select() returns the LOO error of the selected set.
- (b) yes. Fixed repeats pre-reduction and forward selection inside each training fold of a 10-fold cross-validation and scores the held-out fold (CV10E external to selection): the AMB02 correction.
- (c) yes. The diff replaces only the last two lines; select(), lda_predict(), lda_loo_errors() identical.
- (d) yes. Only allowed guards: np.isfinite check, class counts too small, zero variance (x.std>0), each returning None; the mechanical comparisons listed by the designer are exactly these; no test for noise, zeros or shuffle.
- (e) yes. No banned stem in the brief (own regex over the whole brief JSON); the claim is positive and gives only statistic and threshold, no negation of the claim.
- (f) yes. AMB02 colon data: 62 tissues (40 cancer, 22 normal) as in the brief (my own knowledge of this data set and the author's full-text note); 2000 genes reduced to the cap of 60 (P-2 case 2).
- (g) yes. Same accuracy statistic, threshold 0.80, same select(); fixed runs select() 10 times on 56 rows, faulty once. The cost difference comes from the correction itself and the costlier twin (fixed, 63 s estimate per its CASE.md) is the timed one.
- Note: Fixed holds in only 39% of plus draws (pre-check): skeleton-bound, entry P-3.
- The criterion returns True exactly when the estimated score reaches the brief's threshold and None only on the allowed guards. Class and subtype follow the section 1 rules: agreed.

## b2-04 (AMB02, L1.3): PASS

- (a) yes. Faulty runs recursive feature elimination to 8 genes on all 72 patients, then scores with leave-one-out of the 8-gene rule (CV1IE): the AMB02 backward-elimination example with the selection outside the loop.
- (b) yes. Fixed repeats RFE inside each training fold of a 10-fold cross-validation and pools out-of-fold scores: cross-validation external to selection.
- (c) yes. The diff replaces only the evaluation block; rfe(), rule(), lam=70 identical in both twins.
- (d) yes. Only allowed guards: np.isfinite check, class counts too small, zero variance (x.std>0), each returning None; the mechanical comparisons listed by the designer are exactly these; no test for noise, zeros or shuffle.
- (e) yes. No banned stem in the brief (own regex over the whole brief JSON); the claim is positive and gives only statistic and threshold, no negation of the claim.
- (f) yes. AMB02 leukaemia data: 72 patients (47/25) as in the brief; 7129 genes reduced to the cap of 60 (P-2 case 2).
- (g) yes. Same AUC statistic, threshold 0.80, same rfe/rule; cost 1 RFE plus 72 small fits against 10 RFEs plus 10 fits.
- Note: The ridge penalty lam=70 was revised after a fixed pre-check (plus rate 0.22 to 0.675) and mirrored in the faulty; identical in both twins, so not a (c) defect.
- The criterion returns True exactly when the estimated score reaches the brief's threshold and None only on the allowed guards. Class and subtype follow the section 1 rules: agreed.

## b2-05 (KAP23, L1.2): PASS

- (a) yes. Faulty fills unobserved entries with the mean of observed values within the row's own outcome class, over all rows, before cross-validation: label-dependent imputation before the split (KAP23 L1.2, Appendix B.4).
- (b) yes. Fixed fills with the training-fold mean of observed values (label-free), recomputed per fold, test rows filled with training means.
- (c) yes. The diff replaces only the imputation block and the per-fold fill; folds, logit, AUC identical.
- (d) yes. Only allowed guards: np.isfinite check, class counts too small, zero variance (x.std>0), each returning None; the mechanical comparisons listed by the designer are exactly these; no test for noise, zeros or shuffle. The obs_means None return (an indicator with no observed value) is an empty-selection guard, present in both twins.
- (e) yes. No banned stem in the brief (own regex over the whole brief JSON); the claim is positive and gives only statistic and threshold, no negation of the claim.
- (f) yes. KAP23's civil-war data (17.4% missing, per the author's quote) are far larger than the cap; 250 rows, 12 indicators, 20% unobserved are reduced to the cap and of the source's order (P-2 case 2). The 15% onset rate is much higher than real onset rates: author adaptation to the 300-row cap, accepted under P-2 but flagged.
- (g) yes. Same AUC statistic, threshold 0.75, same logistic fit and folds.
- The criterion returns True exactly when the estimated score reaches the brief's threshold and None only on the allowed guards. Class and subtype follow the section 1 rules: agreed.

## b2-06 (KAP23, L1.2): PASS

- (a) yes. Faulty creates SMOTE-style interpolated positives on the whole data to balance classes, then cross-validates and scores balanced accuracy on the augmented rows: synthetic points derived from a test positive end up in training (KAP23 L1.2 passage, Blagus and Lusa).
- (b) yes. Fixed cross-validates on original rows, oversamples inside the training folds only and scores the untouched original test rows.
- (c) yes. The diff is the placement of smote() and the rows scored; smote(), _knn(), balanced() identical.
- (d) yes. Only allowed guards: np.isfinite check, class counts too small, zero variance (x.std>0), each returning None; the mechanical comparisons listed by the designer are exactly these; no test for noise, zeros or shuffle.
- (e) yes. No banned stem in the brief (own regex over the whole brief JSON); the claim is positive and gives only statistic and threshold, no negation of the claim.
- (f) yes. Source data are high-dimensional and large; 100 samples, 30 markers, 20% positive are reduced to the cap (P-2 case 2); KAP23 gives no figures for these.
- (g) yes. Same balanced-accuracy statistic, threshold 0.75, 3-NN, same oversampler.
- The criterion returns True exactly when the estimated score reaches the brief's threshold and None only on the allowed guards. Class and subtype follow the section 1 rules: agreed.

## b2-07 (KAP23, L1.4): PASS

- (a) yes. Faulty runs 10-fold cross-validated 1-NN on all 200 rows including exact repeated entries, so a test row has its twin in training: KAP23 L1.4 passage.
- (b) yes. Fixed collapses identical rows to one (np.unique on the feature rows) before the same 10-fold evaluation: removal of duplicates, the standard correction.
- (c) yes. The diff is 4 inserted lines (dedupe); everything else identical.
- (d) yes. Only allowed guards: np.isfinite check, class counts too small, zero variance (x.std>0), each returning None; the mechanical comparisons listed by the designer are exactly these; no test for noise, zeros or shuffle. The dedupe (np.unique) is the documented correction and acts only on repeated rows, not on whether data look like noise or zeros; guards sit after the dedupe in the fixed twin, a consequence of the correction.
- (e) yes. No banned stem in the brief (own regex over the whole brief JSON); the claim is positive and gives only statistic and threshold, no negation of the claim.
- (f) yes. KAP23 gives no sizes: 200 rows, 15 measurements, a quarter repeated are of the small-data order (P-2 case 1: not documented by the source).
- (g) yes. Same accuracy statistic, threshold 0.75, 1-NN, 10 folds; fixed is slightly cheaper (fewer rows).
- Brief remark: The brief states that some patients were entered more than once; no banned term; it describes the data, not the procedure.
- The criterion returns True exactly when the estimated score reaches the brief's threshold and None only on the allowed guards. Class and subtype follow the section 1 rules: agreed.

## b2-08 (KAP23, L1.4): PASS

- (a) yes. Faulty copies randomly drawn fraud rows with replacement to class balance on all data, then 5-fold 1-NN and F1 over the augmented rows: copies of a test row sit in training (KAP23 L1.4 via the tie rule for oversampling by copying).
- (b) yes. Fixed oversamples the training folds only and scores F1 on untouched original test rows.
- (c) yes. The diff is the placement of copy_up() and the rows scored; helpers identical.
- (d) yes. Only allowed guards: np.isfinite check, class counts too small, zero variance (x.std>0), each returning None; the mechanical comparisons listed by the designer are exactly these; no test for noise, zeros or shuffle.
- (e) yes. No banned stem in the brief (own regex over the whole brief JSON); the claim is positive and gives only statistic and threshold, no negation of the claim.
- (f) yes. KAP23 gives no sizes: 150 transactions, 10 features, 12% fraud are of the small-data order (P-2 case 1: not documented by the source).
- (g) yes. Same F1 statistic, threshold 0.60, 1-NN, 5 folds, same copy_up.
- The criterion returns True exactly when the estimated score reaches the brief's threshold and None only on the allowed guards. Class and subtype follow the section 1 rules: agreed.

## b2-09 (KAP23, L3.1): PASS

- (a) yes. Faulty runs shuffled 5-fold cross-validation on time-ordered rows, so training contains later years than test: KAP23 Appendix B.5 passage.
- (b) yes. Fixed trains on the first 70% of rows and scores AUC on the last 30%: chronological split, as the source corrects.
- (c) yes. The diff replaces only the evaluation block; _auc, _logit, lam, thr identical.
- (d) yes. Only allowed guards: np.isfinite check, class counts too small, zero variance (x.std>0), each returning None; the mechanical comparisons listed by the designer are exactly these; no test for noise, zeros or shuffle. The extra count guard on the chronological train and test parts (at least 2 per class) is a too-small-selection guard returning None, part of the new split.
- (e) yes. No banned stem in the brief (own regex over the whole brief JSON); the claim is positive and gives only statistic and threshold, no negation of the claim.
- (f) yes. KAP23 civil-war data are larger than the cap; 200 rows, 8 indicators reduced to the cap (P-2 case 2); 15% onset prevalence is an adaptation (see b2-05).
- (g) yes. Same AUC statistic, threshold 0.75, same logistic fit; one fit against five.
- Note: Fixed holds in about 42% of plus draws and returns None in 7.5%: skeleton-bound, entry P-3.
- The criterion returns True exactly when the estimated score reaches the brief's threshold and None only on the allowed guards. Class and subtype follow the section 1 rules: agreed.

## b2-10 (KAP23, L3.1): PASS

- (a) yes. Faulty runs shuffled 5-fold cross-validated ridge R^2 on time-ordered weekly rows: KAP23 L3.1 passage (future data in training).
- (b) yes. Fixed fits on the first 100 weeks and scores R^2 on the last 50: chronological split.
- (c) yes. The diff replaces only the evaluation block; _ridge, lam, thr, r2 identical. The R^2 baseline (overall mean against test mean) differs as an unavoidable part of the split.
- (d) yes. Only allowed guards: np.isfinite check, class counts too small, zero variance (x.std>0), each returning None; the mechanical comparisons listed by the designer are exactly these; no test for noise, zeros or shuffle. The variance guard on the test part y[te] is an allowed zero-variance guard.
- (e) yes. No banned stem in the brief (own regex over the whole brief JSON); the claim is positive and gives only statistic and threshold, no negation of the claim.
- (f) yes. KAP23 documents the mechanism only, no sizes: 150 weeks, 6 indicators (P-2 case 1: not documented by the source).
- (g) yes. Same R^2 statistic, threshold 0.30, same ridge; one fit against five.
- Note: Fixed holds in only 43% of plus draws: skeleton-bound, entry P-3.
- The criterion returns True exactly when the estimated score reaches the brief's threshold and None only on the allowed guards. Class and subtype follow the section 1 rules: agreed.

## b2-11 (KAP23, L3.2): PASS

- (a) yes. Faulty flattens patches to rows with the patient label repeated and uses shuffled 5-fold folds over patch rows, so patches of one patient are in training and test: KAP23 L3.2 (Oner et al.) passage.
- (b) yes. Fixed forms folds over patients and repeats them over each patient's patches (np.repeat matches the patient-major row order of the reshape): patient-grouped cross-validation.
- (c) yes. The diff is a single line (fold construction); all else identical.
- (d) yes. Only allowed guards: np.isfinite check, class counts too small, zero variance (x.std>0), each returning None; the mechanical comparisons listed by the designer are exactly these; no test for noise, zeros or shuffle.
- (e) yes. No banned stem in the brief (own regex over the whole brief JSON); the claim is positive and gives only statistic and threshold, no negation of the claim.
- (f) yes. KAP23 gives no sizes: 40 patients, 6 patches, 20 features; flattened 240 rows within the cap (P-2 case 1: not documented by the source).
- (g) yes. Same patch-level AUC statistic, threshold 0.75, same logit; identical cost.
- The criterion returns True exactly when the estimated score reaches the brief's threshold and None only on the allowed guards. Class and subtype follow the section 1 rules: agreed.

## b2-12 (KAP23, L3.2): PASS

- (a) yes. Faulty flattens patients across hospitals and shuffles rows into 5 folds, so patients of the same hospital are in training and test, while the claim concerns new hospitals: KAP23 L3.2 passage (same people or units).
- (b) yes. Fixed forms folds over the hospital axis (np.isin on the hospital index) so a hospital is never split: the block cross-validation KAP23 names.
- (c) yes. The diff is two lines (fold construction); all else identical.
- (d) yes. Only allowed guards: np.isfinite check, class counts too small, zero variance (x.std>0), each returning None; the mechanical comparisons listed by the designer are exactly these; no test for noise, zeros or shuffle.
- (e) yes. No banned stem in the brief (own regex over the whole brief JSON); the claim is positive and gives only statistic and threshold, no negation of the claim.
- (f) yes. KAP23 gives no sizes: 12 hospitals x 20 patients, 15 characteristics (P-2 case 1: not documented by the source).
- (g) yes. Same R^2 statistic, threshold 0.40, same ridge; identical cost.
- The criterion returns True exactly when the estimated score reaches the brief's threshold and None only on the allowed guards. Class and subtype follow the section 1 rules: agreed.

## Class and subtype remarks
No disagreement. b2-01 is L1.1 (no test set; it also selects genes on all data, but no cross-validation exists there, so the L1.3 tie rule does not apply). b2-06 (synthesised rows) is L1.2 and b2-08 (copied rows) is L1.4, per the tie rule. Subtype minima met (L1.1: 2, L1.3: 2, L1.4: 2, L3.1: 2, L3.2: 2); sources SIM03 2, AMB02 2, KAP23 8.

## Item (f), entry P-2 lists
- Sizes not documented by the source (P-2 case 1): b2-02, b2-07, b2-08, b2-10, b2-11, b2-12 (compared with the order of the settings the sources describe and with the caps).
- Sizes reduced to the cap (P-2 case 2): b2-01 (6000 genes to 60; the 20 samples match), b2-03 (2000 genes to 60; 62 tissues match), b2-04 (7129 genes to 60; 72 patients match), b2-05, b2-06, b2-09 (source data far larger).
- Flagged adaptation: onset prevalence of 15% in b2-05 and b2-09 (real civil-war onsets are rare); accepted as a consequence of the 300-row cap, but the report should say so.

## Other observations (they do not change any answer)
- Fixed criteria that rarely hold in plus: b2-03 (0.39), b2-04 (0.675 after a ridge penalty revision), b2-09 (0.425), b2-10 (0.43). Entry P-3 applies; a failed clean pass would be skeleton-bound.
- No banned stem in any brief; no brief negates its claim.
- Result: 12 pairs pass, 0 fail.
