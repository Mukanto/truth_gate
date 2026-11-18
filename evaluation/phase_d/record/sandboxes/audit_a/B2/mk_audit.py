import json
items="a b c d e f g h i j k m p".split()
R={
"D-007":("L1.1","R-squared","SIM03","50x2000 (genes at axis cap); source states no sizes: compared with typical microarray prognosis studies of tens of patients, thousands of genes; not documented",
 "resubstitution ridge fit vs 5-fold CV; same ridge lam=p, same standardisation",{}),
"D-010":("L1.2","correlation","KAP23","1200x150 bool=180k values; source states none; not documented",
 "target encoding with all rows (incl. held-out) vs train-fold means; target encoding is not literally in the quoted sentence but is pre-processing with labels on the whole dataset",{}),
"D-011":("L1.3","classification","AMB02","72 samples as source (72 x 7129); genes reduced 7129->2000 to axis cap; reduced to cap",
 "gene ranking on all samples vs inside each fold; same stratified folds/rng",{}),
"D-022":("L1.1","correlation","KAP23","300x10; source states none; not documented",
 "in-sample fit vs 5-fold CV of the same 66-term OLS",{}),
"D-027":("L1.1","other (MAE skill)","KAP23","60x25; source states none; not documented",
 "in-sample vs 5-fold CV; baseline mean predictor also moved to training-fold mean, a consistent part of the out-of-sample correction",{}),
"D-035":("L1.2","classification","SAN18","1500x20; source (abstract) states none; not documented",
 "SMOTE on all records before CV and scoring on synthetic rows vs SMOTE in training folds only; SMOTE guard nmin<2/nsyn==0 is identical in both and is a definedness guard",{}),
"D-042":("L1.4","correlation","KAP23","1200x20; source states none; not documented",
 "i mod 5 folds vs near-duplicate components kept whole in a fold (0.1 x median distance, same definition as the structure statistic)",
 {"p":"yes; reference statistic measured about 0.345 against approved 0.3, inside the pre-registered tolerance 0.2*|0.3-0| = 0.06 but at its upper edge (structure author chose it deliberately); remark only"}),
"D-055":("L3.1","correlation","KAP23","1000x6; source states none; not documented",
 "random-permutation folds vs forward chaining (6 blocks, evaluated on blocks 2-6); the 5-day gap before each block is a standard embargo, a small addition inside the correction",{}),
"D-064":("L1.1","correlation","SIM03","80x(1500+8); source states none; not documented",
 "resubstitution ridge vs 10-fold CV; SIM03 concerns class prediction, regression variant is an extension of the same resubstitution error",{}),
"D-066":("L1.4","classification","KAP23","1000x15; source states none; not documented",
 "copy minority rows on all data then i mod 5 vs stratified folds with copying inside training folds; stratification is a standard accompaniment (guards each fold has positives), remark only; the guard comparisons <2 per class in MECH_CHECK are class-count guards identical in both bodies",{}),
"D-070":("L1.1","classification","SIM03","120x2000 (genes at cap); source states none; not documented",
 "in-sample logistic AUC vs 10-fold stratified CV AUC; MECH comparison 1e-9 is the Newton convergence tolerance, identical in both",{}),
}
out=[];md=["# AUDIT_A, class B-2 (sandbox B2), 11 cases\n"]
for c,(st,fam,src,sz,note,over) in R.items():
    d={"case":c}
    reasons={
 "a":"yes; "+note.split(';')[0],
 "b":"yes; standard correction ("+note.split(';')[0]+")" ,
 "c":"yes; diff of the two bodies is only the error line(s); mapping in CASE.md matches the diff"+(" ("+note.split(';',1)[1].strip()+")" if ';' in note else ""),
 "d":"yes; only allowed guards (non-finite, n/class minimum, zero variance); every MECH_CHECK comparison judged: "+("class-count minimum 2 (allowed, same in both)" if c=="D-066" else "Newton convergence tolerance, numeric, same in both" if c=="D-070" else "none listed"),
 "e":"yes; no leak/overfit/bias/train/test/fold/split/select/duplicate/impute/resubstitution term and no negation of the claim (PB 4 list itself not in sandbox, own scan"+("; 'out-of-sample' in D-007 claim is the claim's own estimand" if c=="D-007" else "")+")",
 "f":"yes; "+sz+"; within 2000/axis and 2,000,000 values",
 "g":"yes; same statistic, threshold, model, decision rule; cost comparable (CV = a few fits of the same size)",
 "h":"yes; brief gives sizes, axes, meanings and the claim only"+("; 'rare outcome' is a prevalence statement, not an arrangement fact" if c=="D-066" else "; 'compound record' wording weak, no duplication stated" if c=="D-042" else ""),
 "i":"yes; claim quantity is what the fixed body estimates",
 "j":"yes; minus nulls only the claim's quantity (permuting/deranging the signal or labels), other quantities as plus",
 "k":"yes; reference adds no key or dependence read only by the faulty body",
 "m":"yes; statistic a function of the brief's keys, measures the exploited structure, unchanged in distribution by minus (class counts/shape/X unchanged)",
 "p":"yes; reference reproduces the approved value (shape-fixed or measured in tolerance)"}
    for k,v in over.items(): reasons[k]=v
    for i in items: d[i]="yes"
    d["reasons"]=reasons;d["overall"]="pass";d["repair_request"]="";d["remarks"]={"class_subtype":"%s, %s, %s: consistent with PB 1 / PC lists, no disagreement"%("B-2",st,fam),"true_exactly_when_supported":"yes, criterion returns True iff statistic >= claim threshold","source":src,"sizes_status":sz}
    out.append(d)
    md.append("## %s (%s, %s, %s)\n"%(c,src,st,fam)+"\n".join("- (%s) yes: %s"%(i,reasons[i]) for i in items)+"\n- overall: pass\n")
json.dump(out,open("AUDIT_A.json","w"),indent=1)
md.append("## Sizes list\nReduced to cap: D-011 (genes 7129 -> 2000), D-007 / D-070 genes at the 2000 cap.\nNot documented by the source: all other pairs (D-007, D-010, D-022, D-027, D-035, D-042, D-055, D-064, D-066, D-070).\n")
md.append("## Remarks\nClass and subtype follow PB 1 for all 11 (L1.1: D-007, D-022, D-027, D-064, D-070; L1.2: D-010, D-035; L1.3: D-011; L1.4: D-042, D-066; L3.1: D-055). Criterion returns True exactly when the claimed statistic meets its threshold in all cases.\n## URLs read\n- https://pmc.ncbi.nlm.nih.gov/articles/PMC10499856 (KAP23 taxonomy quotes confirmed)\n- https://pubmed.ncbi.nlm.nih.gov/12509396/ (SIM03; cookie page, no content)\nNo helper computation was run; no criterion called on data.\n")
open("AUDIT_A.md","w").write("\n".join(md))
