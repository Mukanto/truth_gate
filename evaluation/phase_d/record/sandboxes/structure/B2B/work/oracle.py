# Parameter-based oracle effect sizes of the generators (no world samples are analysed).
import math, numpy as np
Phi = lambda x: 0.5 * (1 + math.erf(x / math.sqrt(2)))
# --- family A
def a_fam(cid, N, P, BLOCK, DP, prev=0.10):
    auc = Phi(DP / math.sqrt(2)); ba = Phi(DP / 2)
    t = DP / 2 + math.log((1 - prev) / prev) / DP   # Bayes threshold in sd units from the negative mean
    sens = Phi(DP - t); fpr = 1 - Phi(t)
    tp = prev * sens; fp = (1 - prev) * fpr; prec = tp / (tp + fp); f1 = 2 * prec * sens / (prec + sens)
    print(f"{cid}: d'={DP} oracle AUC {auc:.3f} BA(mid-threshold) {ba:.3f} | at prior-optimal threshold: sens {sens:.3f} F1 {f1:.3f}")
a_fam("D-003", 1000, 15, 5, 1.6); a_fam("D-035", 1500, 20, 5, 1.7); a_fam("D-043", 400, 8, 4, 2.8); a_fam("D-049", 600, 12, 4, 2.4)
# --- family B : actual Mahalanobis distance for random parameter draws
def b_fam(cid, N, NPOS, KC, DP, reps=3):
    rng = np.random.default_rng(5); P = 2000; K = 8
    out = []
    for _ in range(reps):
        lam = (rng.random((P, K)) < 0.10) * rng.normal(0, 0.5, (P, K))
        sd = 0.45 * np.exp(0.25 * rng.normal(size=P))
        S = lam @ lam.T + np.diag(sd ** 2) + 0.15 ** 2 * np.ones((P, P))
        dlt = lam[:, :KC].sum(axis=1) * DP / math.sqrt(KC)
        out.append(math.sqrt(dlt @ np.linalg.solve(S, dlt)))
    d = float(np.mean(out)); pi = NPOS / N
    err = (1 - pi) * (1 - Phi(d / 2 + math.log(pi / (1 - pi)) / d * -1 if False else d / 2)) 
    print(f"{cid}: target d'={DP}, expression-space Mahalanobis d' (mean of {reps} parameter draws) {d:.2f}, oracle AUC {Phi(d/math.sqrt(2)):.3f}, oracle balanced error {1-Phi(d/2):.3f}")
b_fam("D-011", 72, 25, 3, 3.4); b_fam("D-013", 40, 20, 3, 2.4); b_fam("D-024", 62, 40, 3, 2.8); b_fam("D-070", 120, 42, 2, 1.4)
# --- D-007
s, r = 0.7, 0.7
print("D-007: oracle R2 log scale", r * r, " raw months", (math.exp(s * s * r * r) - 1) / (math.exp(s * s) - 1))
print("D-064: oracle R2 = 0.25+0.12 = 0.37, oracle r", math.sqrt(0.37))
print("D-034: oracle R2 0.75 -> oracle RMSE/sd", math.sqrt(0.25), "; D-059 oracle R2 0.55")
# --- D-018
link = np.array((0.8, 0, 0.8, 0.7, 0, 0, 0.7, 0, 0.7, 0)); sg = np.array((1, 1, -1, 1, 1, -1, 1, -1, 1, 1.0))
dl = 2 * link * sg * math.sqrt(0.30)
Sc = np.diag(0.30 * (1 - link ** 2) + 0.20 + 0.35) + 0.15 * np.outer(sg, sg)
d = math.sqrt(dl @ np.linalg.solve(Sc, dl))
print(f"D-018: record-level d'={d:.2f}, oracle record AUC {Phi(d/math.sqrt(2)):.3f}")
Ssub = np.diag(0.30 * (1 - link ** 2) + (0.20 + 0.35) / 60) + 0.15 / 60 * np.outer(sg, sg)
d2 = math.sqrt(dl @ np.linalg.solve(Ssub, dl)); print(f"       subject-mean d'={d2:.2f}, oracle subject-level AUC {Phi(d2/math.sqrt(2)):.3f}")
# --- D-058
DP = 3.6; pi = 0.2
t = DP / 2 + math.log((1 - pi) / pi) / DP
err = pi * (1 - Phi(DP - t)) + (1 - pi) * (1 - Phi(t))
print(f"D-058: d'={DP}; oracle error at walking share 0.2: {err:.3f}; majority-class error 0.2")
print("D-065: oracle R2 0.35 -> pooled oracle r", math.sqrt(0.35))
