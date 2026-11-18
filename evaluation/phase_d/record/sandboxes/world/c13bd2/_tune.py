import numpy as np

# ---------- D-022: mean and SD of the signal function under the stationary marginal of z
LAM = np.array([0.6, 0.55, 0.5, 0.6, 0.45, 0.5, 0.4, 0.0, 0.0, 0.0])
GAM = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.55, 0.6, 0.5])
R = np.outer(LAM, LAM) + np.outer(GAM, GAM) + np.diag(1 - LAM**2 - GAM**2)
rng = np.random.default_rng(1)
Lc = np.linalg.cholesky(R)
z = rng.standard_normal((4_000_000, 10)) @ Lc.T
f = (0.45*z[:,0] - 0.35*z[:,1]**2 + 0.30*z[:,2]*z[:,3] + 0.25*z[:,4] - 0.20*z[:,0]*z[:,5]
     + 0.15*z[:,6]**2 - 0.20*z[:,8] + 0.15*z[:,7]*z[:,9])
print("D-022 F_MEAN %.4f F_SD %.4f" % (f.mean(), f.std()))
print("D-022 reading corr range", np.round(R[np.triu_indices(10,1)].max(),3))

# ---------- D-027: population R^2 of y on X
def load27():
    L = np.zeros((25, 3))
    L[0:9, 0] = np.linspace(0.75, 0.5, 9)
    L[9:17, 1] = np.linspace(0.7, 0.45, 8)
    L[17:23, 2] = np.linspace(0.65, 0.45, 6)
    L[5:9, 2] += 0.25
    L[13:17, 0] += 0.2
    return L
L = load27()
h2 = (L**2).sum(1)
ST = L @ L.T + np.diag(1 - h2)
SX = ST + (0.09 + 0.09) * np.eye(25)
beta = np.zeros(25)
beta[[0, 3, 6, 10, 12, 18, 21, 24]] = [0.35, 0.25, 0.15, -0.30, 0.20, 0.25, -0.20, 0.20]
sig_var = beta @ ST @ beta
expl = (ST @ beta) @ np.linalg.solve(SX, ST @ beta)
# want expl / (sig_var + s2) = 0.70
s2 = expl / 0.70 - sig_var
print("D-027 h2 range", h2.min().round(3), h2.max().round(3), "beta'ST beta", round(sig_var,4),
      "explained", round(expl,4), "sigma", round(np.sqrt(s2),4), "R2 if X=T", round(sig_var/(sig_var+s2),3))

# ---------- D-035: Mahalanobis distance of the class shift
def load35():
    L = np.zeros((20, 3))
    L[0:7, 0] = [0.65, 0.6, 0.6, 0.55, 0.55, 0.5, 0.5]
    L[7:13, 1] = [0.6, 0.6, 0.55, 0.55, 0.5, 0.45]
    L[13:18, 2] = [0.6, 0.55, 0.5, 0.5, 0.45]
    L[3:5, 1] += 0.2
    return L
L = load35()
h2 = (L**2).sum(1)
S = L @ L.T + np.diag(1 - h2) + 0.04 * np.eye(20)
s = np.array([0.45,0.35,0.30,0.25,0,0,0, 0.35,0.30,0,0,0,0, 0.30,0.20,0,0,0, 0.30,0.15])
from statistics import NormalDist
for k in [1.0, 1.1, 1.2, 1.3]:
    D = np.sqrt((k*s) @ np.linalg.solve(S, k*s))
    print("D-035 k", k, "Delta %.3f  max balanced acc %.3f" % (D, NormalDist().cdf(D/2)))

# ---------- D-042: descriptor covariance and SAR scaling
def load42():
    W = np.zeros((20, 4))
    W[0:6, 0] = [0.9, 0.8, 0.7, 0.75, 0.6, 0.5]
    W[4:11, 1] = [0.4, 0.5, 0.85, 0.8, 0.6, 0.5, 0.45]
    W[10:16, 2] = [0.5, 0.85, 0.8, 0.7, 0.6, 0.5]
    W[15:20, 3] = [0.5, 0.8, 0.75, 0.7, 0.6]
    return W
W = load42()
Sd = 1.1225 * W @ W.T + 0.4225 * np.eye(20)
Sw = 0.1225 * W @ W.T + 0.0625 * np.eye(20)
print("D-042 desc sd range", np.sqrt(np.diag(Sd)).min().round(3), np.sqrt(np.diag(Sd)).max().round(3))
# expected squared distances (unstandardised) within series vs between series
print("D-042 E d2 within series", round(2*np.trace(Sw),2), " between", round(2*np.trace(Sd),2))
