s=open("gen.py",encoding="utf-8").read()
def rep(a,b):
    global s
    assert a in s,a[:60]
    s=s.replace(a,b)
rep('SIMQ="SIM03 abstract: class-prediction performance assessed on the data used to build the rule; independent validation required."',
 'SIMQ="NOT VERIFIED: the JNCI paper (doi 10.1093/jnci/95.1.14) could not be opened (publisher 403; no abstract via Europe PMC, Crossref or Semantic Scholar). Content is taken from the designer SOURCES.md summary only: class-prediction performance assessed on the data used to build the rule; independent validation required."')
rep('AMBQ="AMB02 abstract: genes selected on the full data, then error estimated by cross-validation on the same data; correction is cross-validation external to the selection."',
 'AMBQ="AMB02 (PMC124442, full text read): \\"But, if it is calculated within the feature-selection process, there is a selection bias in it when it is used as an estimate of the prediction error. [...] it is essential that cross-validation or the bootstrap be used external to the gene-selection process.\\""')
rep('claim holds if accuracy >= 0.80."','claim holds if accuracy >= 0.80. Classifier and sizes are author choices, not checked against SIM03 (not verified)."')
rep('"L1.1","n < p regime','"L1.1","Parameters not verified against SIM03 (source unreadable). n < p regime')
rep('"L1.1","Different statistic','"L1.1","Parameters not verified against SIM03. Different statistic')
a=s.index('add("b2-03"'); b=s.index('add("b2-05"')
new=open("new34.txt",encoding="utf-8").read().replace("\q",chr(92)+chr(34))
s=s[:a]+new+s[b:]
for o,n in [l.split("\t") for l in open("quotes.tsv",encoding="utf-8").read().split("\n") if l.strip()]:
    rep(o,n.replace("\\q",'\\"'))
open("gen.py","w",encoding="utf-8").write(s)
