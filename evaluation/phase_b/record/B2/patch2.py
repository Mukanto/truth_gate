s=open("gen.py",encoding="utf-8").read()
def rep(a,b):
    global s
    assert a in s,a[:70]
    s=s.replace(a,b)
Q='\\"'
# passages
i=s.index('SIMQ="NOT VERIFIED'); j=s.index('\n',i)
s=s[:i]+'SIMQ1="SIM03 via OpenAlex reconstruction: '+Q+'The resubstitution estimate of the error is biased for small datasets (11,12); our simulation confirms this, with 98.2% of the simulated datasets resulting in zero misclassifications, even though no true underlying difference existed between the two groups.'+Q+'"\nSIMQ2="SIM03 via OpenAlex reconstruction: '+Q+'We also computed the resubstitution estimate of the error rate (this estimate results from building the predictor on the full dataset and then reapplying it to each specimen for classification purposes). [...] Consequently, it is essential to obtain an unbiased estimate of the true error rate of the predictor (i.e., the probability of incorrectly classifying a randomly selected future case).'+Q+'"'+s[j:]
# b2-01
a=s.index('add("b2-01"'); b=s.index('add("b2-02"')
n1='''add("b2-01","A classifier built from the expression levels of 60 genes recognises tumour tissue among new tissue samples with accuracy of at least 0.80.",
 [("expr","(samples, genes)","float","log expression level of each gene in each tissue sample"),("tumour","(samples,)","bool","True if the sample is tumour tissue, False if normal")],
 "20 samples (10 per class), 60 genes (SIM03 simulation: 20 profiles of 6000 genes, 10 per class; genes capped at 60).",
 "SIM03",SIMQ1,
 "SIM03 resubstitution estimate: build the predictor on all 20 samples (select informative genes, weight them, apply the rule) and reapply it to the same 20 samples; accuracy = 1 - resubstitution error. Source reports 20 specimens, 6000 genes, 10 per class, and that 98.2% of null datasets gave zero misclassifications. Not reported in the text read (supplement not available): classifier and gene-selection threshold; mine: nearest centroid on the 5 genes with largest absolute t statistic.",
 "SIM03 correction: leave-one-out cross-validation in which gene selection, weighting and the rule are all redone with the left-out specimen removed first (source: median 11 misclassifications of 20 under no difference); accuracy = 1 - that error.",
 "L1.1","Source-reported: n=20, 10 per class, resubstitution vs fully cross-validated leave-one-out. Author choices: 60-gene cap, nearest centroid, top 5 genes by t, accuracy threshold 0.80.")
'''
s=s[:a]+n1+s[b:]
# b2-02
a=s.index('add("b2-02"'); b=s.index('add("b2-03"')
n2='''add("b2-02","A logistic model using 20 baseline markers predicts which patients will relapse within five years, in new patients, with AUC of at least 0.75.",
 [("markers","(patients, markers)","float","standardised baseline marker values for each patient"),("relapse","(patients,)","bool","True if the patient relapsed within five years")],
 "30 patients, 20 markers (SIM03: class prediction studies on fewer than 50 specimens are common; prognostic setting follows its van't Veer breast-cancer example, metastasis within 5 years versus disease-free at 5 years).",
 "SIM03",SIMQ2,
 "SIM03 resubstitution estimate: fit logistic regression (few Newton steps, small ridge) on all 30 patients and compute AUC on the same patients.",
 "Cross-validation that refits the whole predictor with each left-out group removed first (SIM03: leave-one-out or other cross-validation methods are nearly unbiased); AUC from pooled out-of-fold scores, here 5-fold.",
 "L1.1","Source-reported: resubstitution definition, small-n prognostic setting, fully cross-validated correction. Author choices: logistic regression, n=30, 20 markers, 5 folds, AUC. Differs from b2-01 in statistic, model, n, no gene-selection step.")
'''
s=s[:a]+n2+s[b:]
open("gen.py","w",encoding="utf-8").write(s)
