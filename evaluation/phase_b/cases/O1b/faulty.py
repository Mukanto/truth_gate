"""W33: Using the leading principal components of the tumour expression profile, a nearest-centroid classifier tells responders from non-responders with an accuracy of at least 0.70 on new tumours (the claim holds when the accuracy estimate is >= 0.70)."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

N, G = 120, 60


def _gen(rng, gamma):
    f = rng.standard_normal(N)                               # response-related program (dominant co-expression axis)
    g = rng.standard_normal(N)                               # nuisance (batch) program
    latent = gamma * f + rng.standard_normal(N)
    resp = latent > 0.1257 * np.sqrt(1.0 + gamma ** 2)       # about 45% responders in both worlds
    e = rng.standard_normal((N, G))
    z = np.empty((N, G))
    z[:, :20] = 0.8 * f[:, None] + 0.6 * e[:, :20]
    z[:, 20:40] = 0.85 * g[:, None] + np.sqrt(1.0 - 0.85 ** 2) * e[:, 20:40]
    z[:, 40:] = e[:, 40:]
    z = z[:, rng.permutation(G)]                             # genes in arbitrary order
    scale = 10.0 ** rng.uniform(-0.7, 0.7, G)                # arbitrary instrument scale per gene (0.2 to 5)
    off = 5.0 + 2.0 * rng.standard_normal(G)
    return {"expr": off[None, :] + scale[None, :] * z, "responder": resp.astype(bool)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 1.2)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: expr (120, 60) log expression of 60 genes per tumour, on arbitrary instrument scales, axes (tumours, genes);
    responder (120,) bool, True if the tumour responded to the drug.
    Holds when the claim is supported by the data. Written by someone else."""
    x = np.asarray(d["expr"], dtype=float)
    y = np.asarray(d["responder"]).astype(bool)
    n_train = 72  # fixed block: the first 72 tumours train the classifier, the remaining ones score it
    if not (np.isfinite(x).all() and x.shape[0] > n_train):
        return None
    # standardisation and PCA are fitted on all rows, test rows included
    fit = x
    mu = fit.mean(axis=0)
    sd = fit.std(axis=0)
    if sd.min() <= 1e-12:
        return None
    zfit = (fit - mu) / sd
    vt = np.linalg.svd(zfit, full_matrices=False)[2]
    comp = vt[:5].T  # top 5 principal axes
    s = ((x - mu) / sd) @ comp
    ytr = y[:n_train]
    yte = y[n_train:]
    if ytr.all() or not ytr.any():
        return None
    c1 = s[:n_train][ytr].mean(axis=0)
    c0 = s[:n_train][~ytr].mean(axis=0)
    st = s[n_train:]
    pred = np.sum((st - c1) ** 2, axis=1) < np.sum((st - c0) ** 2, axis=1)  # nearest centroid
    acc = float(np.mean(pred == yte))
    return bool(acc >= 0.70)


def permute_responder(d, rng):
    return {**d, "responder": d["responder"][rng.permutation(N)]}


STUDY = Study(
    name="W33",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="response depends on the dominant expression program (probit coefficient 1.2, ideal accuracy about 0.78) -> response independent of the expression data (45% responders as before); the two co-expression programs, the arbitrary per-gene scales and the sample size unchanged"),
    },
    controls=[Control("permute_responder", ["C"], transform=permute_responder)],
)
