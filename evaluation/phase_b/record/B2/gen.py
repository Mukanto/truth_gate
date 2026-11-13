import json, re
B=[]; P=[]
def add(i,claim,keys,sizes,src,passage,faulty,fixed,sub,notes):
    B.append(dict(local_id=i,claim=claim,data_keys=[dict(key=k,shape=s,dtype=d,meaning=m) for k,s,d,m in keys],sizes=sizes))
    P.append(dict(local_id=i,source=src,passage=passage,faulty=faulty,fixed=fixed,subtype=sub,notes=notes))
SIMQ1="SIM03 via OpenAlex reconstruction: \"The resubstitution estimate of the error is biased for small datasets (11,12); our simulation confirms this, with 98.2% of the simulated datasets resulting in zero misclassifications, even though no true underlying difference existed between the two groups.\""
SIMQ2="SIM03 via OpenAlex reconstruction: \"We also computed the resubstitution estimate of the error rate (this estimate results from building the predictor on the full dataset and then reapplying it to each specimen for classification purposes). [...] Consequently, it is essential to obtain an unbiased estimate of the true error rate of the predictor (i.e., the probability of incorrectly classifying a randomly selected future case).\""
AMBQ="AMB02 (PMC124442, full text read): \"But, if it is calculated within the feature-selection process, there is a selection bias in it when it is used as an estimate of the prediction error. [...] it is essential that cross-validation or the bootstrap be used external to the gene-selection process.\""
add("b2-01","A classifier built from the expression levels of 60 genes recognises tumour tissue among new tissue samples with accuracy of at least 0.80.",
 [("expr","(samples, genes)","float","log expression level of each gene in each tissue sample"),("tumour","(samples,)","bool","True if the sample is tumour tissue, False if normal")],
 "20 samples (10 per class), 60 genes (SIM03 simulation: 20 profiles of 6000 genes, 10 per class; genes capped at 60).",
 "SIM03",SIMQ1,
 "SIM03 resubstitution estimate: build the predictor on all 20 samples (select informative genes, weight them, apply the rule) and reapply it to the same 20 samples; accuracy = 1 - resubstitution error. Source reports 20 specimens, 6000 genes, 10 per class, and that 98.2% of null datasets gave zero misclassifications. Not reported in the text read (supplement not available): classifier and gene-selection threshold; mine: nearest centroid on the 5 genes with largest absolute t statistic.",
 "SIM03 correction: leave-one-out cross-validation in which gene selection, weighting and the rule are all redone with the left-out specimen removed first (source: median 11 misclassifications of 20 under no difference); accuracy = 1 - that error.",
 "L1.1","Source-reported: n=20, 10 per class, resubstitution vs fully cross-validated leave-one-out. Author choices: 60-gene cap, nearest centroid, top 5 genes by t, accuracy threshold 0.80.")
add("b2-02","A logistic model using 20 baseline markers predicts which patients will relapse within five years, in new patients, with AUC of at least 0.75.",
 [("markers","(patients, markers)","float","standardised baseline marker values for each patient"),("relapse","(patients,)","bool","True if the patient relapsed within five years")],
 "30 patients, 20 markers (SIM03: class prediction studies on fewer than 50 specimens are common; prognostic setting follows its van't Veer breast-cancer example, metastasis within 5 years versus disease-free at 5 years).",
 "SIM03",SIMQ2,
 "SIM03 resubstitution estimate: fit logistic regression (few Newton steps, small ridge) on all 30 patients and compute AUC on the same patients.",
 "Cross-validation that refits the whole predictor with each left-out group removed first (SIM03: leave-one-out or other cross-validation methods are nearly unbiased); AUC from pooled out-of-fold scores, here 5-fold.",
 "L1.1","Source-reported: resubstitution definition, small-n prognostic setting, fully cross-validated correction. Author choices: logistic regression, n=30, 20 markers, 5 folds, AUC. Differs from b2-01 in statistic, model, n, no gene-selection step.")
add("b2-03","The expression levels of 60 genes predict cancer versus normal status in new tissue samples with accuracy of at least 0.80.",
 [("expr","(tissues, genes)","float","log expression of each gene in each tissue"),("cancer","(tissues,)","bool","True if the tissue is cancerous")],
 "62 tissues (40 cancer, 22 normal), 60 genes (AMB02 colon data: n = 62, p = 2,000; capped at 60).",
 "AMB02",AMBQ,
 "AMB02 section Forward Selection with Fisher's Rule: Fisher's linear discriminant rule; genes pre-reduced (source: top 400 of 2000; here top 20 of 60 as a scaled analogue); sequential forward selection with the decision to add a gene based on leave-one-out CV error, using all 62 tissues and no test set; the reported error is the internal leave-one-out error CV1IE of the 3-gene rule (source: minimum 6.5% at three genes). Claim holds if 1 - error >= 0.80. Ridge-regularised LDA in numpy (source notes the covariance is singular for n small).",
 "AMB02 correction: 10-fold cross-validation external to the selection (CV10E; source about 15% for more than seven genes), the pre-reduction and forward selection repeated inside each training fold; accuracy = 1 - CV10E.",
 "L1.3","Source-reported parameters: Fisher LDA, leave-one-out inside forward selection, 3 genes at the CV1IE minimum, external 10-fold. Adaptations not in source: pre-filter 20 instead of 400, ridge for LDA, gene cap 60.")
add("b2-04","Patients with leukaemia subtype A can be told from subtype B using 60 gene expression values, with AUC of at least 0.80 in new patients.",
 [("expr","(patients, genes)","float","log expression of each gene for each patient"),("subtype_a","(patients,)","bool","True for subtype A, False for subtype B")],
 "72 patients (47 subtype A, 25 subtype B), 60 genes (AMB02 leukaemia data: n = 72, p = 7,129; capped at 60).",
 "AMB02","AMB02 (PMC124442) Discussion: \"although the feature vectors have been generated independently of the class labels, we can form an SVM rule that has not only an average zero AE but also an average CV1IE error close to zero for a subset of 128 genes and about 10% for only eight genes in the selected subset.\"",
 "AMB02 section Backward Elimination with SVM (RFE of Guyon et al.): linear classifier with recursive elimination by weight magnitude down to 8 genes on all 72 patients (source: eight-gene subset), then the leave-one-out (CV1IE) scores of the 8-gene rule give the AUC. Linear SVM replaced by a ridge linear classifier in numpy (adaptation, not in source).",
 "External 10-fold cross-validation (CV10E): RFE repeated inside each training fold; AUC from pooled out-of-fold scores.",
 "L1.3","Source-reported: RFE, an 8-gene subset, leave-one-out internal vs 10-fold external, leukaemia 47 ALL / 25 AML. Adaptations: ridge instead of SVM, 60-gene cap. Differs from b2-03 in classifier, selection procedure (backward), statistic, n.")
add("b2-05","Using 12 country-level indicators, the model identifies which country-years will see a civil war onset, with AUC of at least 0.75 in new country-years.",
 [("x","(rows, indicators)","float","indicator values, one row per country-year; entries flagged as unobserved hold 0"),("observed","(rows, indicators)","bool","True where the indicator was recorded"),("onset","(rows,)","bool","True if a civil war began in that country-year")],
 "250 country-years, 12 indicators, about 15% onsets and about 20% of entries unobserved.",
 "KAP23","KAP23 Sec 2.4 L1.2 (verified): \"Using the entire dataset for any pre-processing steps such as imputation or over/under sampling.\" Appendix B.4: \"Correcting the imputation method dramatically reduces the performance of the ML models proposed.\"",
 "Fill unobserved entries of each indicator with the mean of its observed values within the row's own outcome class (label-dependent imputation over all rows), then compute cross-validated AUC of a logistic regression.",
 "Fill unobserved entries with the training-fold mean of the observed values (label-free), recomputed in each fold; AUC from pooled out-of-fold scores.",
 "L1.2","Source uses random-forest imputation that uses the outcome, on the whole data; class-conditional mean is a simple numpy analogue (stated). Rows treated as exchangeable; no time order, to keep L3.1 out. Missingness carried by a bool mask to avoid NaN (finite-value guard).")
add("b2-06","In a screening cohort where about one sample in five is positive, a nearest-neighbour rule on 30 biomarkers attains balanced accuracy of at least 0.75 on new samples.",
 [("biomarkers","(samples, markers)","float","standardised biomarker values"),("positive","(samples,)","bool","True for a positive sample")],
 "100 samples (about 20 positive), 30 biomarkers (high-dimensional source data capped).",
 "KAP23","KAP23 Sec 2.4 L1.2 (verified in full text): \"For instance, using oversampling before splitting the data into training and test sets leads to an imperfect separation between the training and test sets since data generated using oversampling from the training set will also be present in the test set.\" Table 1 lists Blagus and Lusa 2015 (bioinformatics, 6 papers).",
 "Oversample positives by SMOTE-style interpolation between random pairs of positive rows up to class balance over the whole data, then 5-fold cross-validate 3-NN and report balanced accuracy.",
 "Cross-validate on the original rows; oversample the training folds only; test folds untouched.",
 "L1.2","Synthesising rows -> L1.2 by the prereg tie rule. Synthetic points interpolate between positives, so a test positive has synthetic near neighbours derived from itself.")
add("b2-07","From 15 clinical measurements recorded in a patient registry, a nearest-neighbour rule predicts diagnosis in new patients with accuracy of at least 0.75. Some patients were entered more than once.",
 [("records","(rows, measurements)","float","clinical measurements, one row per registry entry"),("diagnosis","(rows,)","bool","True if the patient has the diagnosis")],
 "200 rows, 15 measurements; about a quarter of the rows repeat an earlier entry exactly, with its diagnosis.",
 "KAP23","KAP23 Sec 2.4 L1.4 (verified): \"If a dataset with duplicates is used for the purposes of training and evaluating an ML model, the same data could exist in the training as well as test set.\"",
 "Run 10-fold cross-validation of 1-NN accuracy over all rows including repeated entries.",
 "Collapse repeated rows to one before cross-validation (or keep repeats of a case together in a fold).",
 "L1.4","Brief states the repeats because they are a property of the data; wording does not mention splitting. Statistic accuracy, small n.")
add("b2-08","In a fraud-screening data set where about 12% of transactions are fraudulent, a nearest-neighbour rule on 10 transaction features achieves an F1 score of at least 0.60 for fraud on new transactions.",
 [("features","(transactions, features)","float","standardised transaction features"),("fraud","(transactions,)","bool","True for a fraudulent transaction")],
 "150 transactions (about 18 fraudulent), 10 features.",
 "KAP23","KAP23 Sec 2.4 L1.2 (verified): \"using oversampling before splitting the data into training and test sets leads to an imperfect separation between the training and test sets\"; L1.4: \"the same data could exist in the training as well as test set.\" Prereg tie rule: oversampling by copying rows is L1.4.",
 "Copy fraud rows (sampling with replacement) until classes are balanced on the whole data, then 5-fold cross-validate 1-NN and compute fraud F1 on the rows of each fold.",
 "Oversample training folds only; compute F1 on untouched original test rows.",
 "L1.4","Duplicates arise from oversampling, not from the data; differs from b2-07 in pipeline step, statistic (F1), class imbalance.")
add("b2-09","From 8 yearly indicators, the model predicts civil war onset in future country-years with AUC of at least 0.75.",
 [("x","(years, indicators)","float","indicator values, one country-year per row, rows in time order"),("onset","(years,)","bool","True if a civil war began in that year")],
 "200 rows in time order, 8 indicators, about 15% onsets.",
 "KAP23","KAP23 Appendix B.5 (verified): \"When the dataset contains temporal data, the training dataset could contain data from a later date than the test dataset because of being shuffled.\"",
 "Shuffle rows and run 5-fold cross-validated logistic AUC.",
 "Chronological split: fit on the first 70% of rows, compute AUC on the last 30% (or expanding-window folds).",
 "L3.1","Source's corrected split: year < 1988 train, rest test. Binary outcome, AUC.")
add("b2-10","Using 6 weekly indicators, a ridge regression forecasts next-week hospital admissions in future weeks with R^2 of at least 0.30.",
 [("indicators","(weeks, indicators)","float","weekly indicator values, rows in time order"),("admissions_next","(weeks,)","float","admissions in the following week")],
 "150 weeks in time order, 6 indicators.",
 "KAP23","KAP23 Sec 2.4 L3.1 (verified): \"If the test set contains data from before the training set, the model is built using data from the future that it should not have access to during training, and can cause leakage.\"",
 "Shuffle rows, 5-fold cross-validated ridge R^2.",
 "Fit on the first 100 weeks, compute R^2 on the last 50.",
 "L3.1","Continuous outcome, R^2, weekly series; differs from b2-09 in statistic, structure, size. The hospital setting is an illustration; the source documents only the mechanism.")
add("b2-11","From 20 image features of tissue patches, the model identifies the gene mutation status of new patients with AUC of at least 0.75.",
 [("patches","(patients, patches, features)","float","image features of each tissue patch of each patient"),("mutated","(patients,)","bool","True if the patient's tumour carries the mutation")],
 "40 patients, 6 patches per patient (240 rows when flattened), 20 features.",
 "KAP23","KAP23 Sec 2.4 L3.2 (verified): \"Oner et al. 2020 find that a recent study on histopathology uses different observations of the same patient in the training and test sets.\" (The claim is about new patients.)",
 "Flatten to 240 patch rows with the patient label repeated, shuffle, 5-fold cross-validated logistic AUC.",
 "Folds over the patient axis: patches of one patient never in both training and test.",
 "L3.2","Shared unit = patient. Patient-level or patch-level AUC left to the criterion author.")
add("b2-12","From 15 patient characteristics, ridge regression predicts length of stay in patients from new hospitals with R^2 of at least 0.40.",
 [("x","(hospitals, patients, characteristics)","float","characteristics of each patient in each hospital"),("stay","(hospitals, patients)","float","length of stay in days")],
 "12 hospitals, 20 patients each (240 rows when flattened), 15 characteristics.",
 "KAP23","KAP23 Sec 2.4 L3.2 (verified): \"In the extreme (but unfortunately common) case, train and test samples come from the same people or units.\" Remedy named there: block cross validation (Roberts 2017, Valavi 2021).",
 "Flatten to 240 rows, shuffle, 5-fold cross-validated ridge R^2.",
 "Leave-hospitals-out folds along the hospital axis.",
 "L3.2","Shared unit = site; continuous R^2 differs from b2-11.")
json.dump(B,open("BRIEFS.json","w"),indent=1)
json.dump(P,open("PRIVATE.json","w"),indent=1)
bad=re.compile(r"circular|double dip|leak|pseudorepl|coupl|spurious|non-?independ|regression to the mean|selection bias|overfit|inflat|contaminat|optimis|split|select|held-out|cross-val",re.I)
for b in B:
    m=bad.search(json.dumps(b))
    if m: print("BAD",b["local_id"],m.group())
print(len(B))

NEUTRAL={
"b2-01":"20 samples (10 per class), 60 genes.",
"b2-02":"30 patients, 20 markers.",
"b2-03":"62 tissues (40 cancer, 22 normal), 60 genes.",
"b2-04":"72 patients (47 subtype A, 25 subtype B), 60 genes.",
"b2-05":"250 country-years, 12 indicators, about 15% onsets and about 20% of entries unobserved.",
"b2-06":"100 samples (about 20 positive), 30 biomarkers.",
"b2-07":"200 rows, 15 measurements; about a quarter of the rows repeat an earlier entry exactly, with its diagnosis.",
"b2-08":"150 transactions (about 18 fraudulent), 10 features.",
"b2-09":"200 rows in time order, 8 indicators, about 15% onsets.",
"b2-10":"150 weeks in time order, 6 indicators.",
"b2-11":"40 patients, 6 patches per patient, 20 features.",
"b2-12":"12 hospitals, 20 patients each, 15 characteristics.",
}
for b,p in zip(B,P):
    p["notes"]=("Sizes note: "+b["sizes"]+" | "+p["notes"])
    b["sizes"]=NEUTRAL[b["local_id"]]
json.dump(B,open("BRIEFS.json","w"),indent=1)
json.dump(P,open("PRIVATE.json","w"),indent=1)
src=re.compile(r"KAP23|AMB02|SIM03|source|Kapoor|Ambroise|Simon|arXiv",re.I)
for b in B:
    m=src.search(json.dumps(b))
    if m: print("SRC",b["local_id"],m.group())
