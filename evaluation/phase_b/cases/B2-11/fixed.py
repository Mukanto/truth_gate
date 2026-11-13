"""W06: From 20 image features of tissue patches, the model identifies the gene mutation status of new patients with AUC of at least 0.75."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

P, K, F = 40, 6, 20


def _gen(rng, eff):
    mut = rng.permutation(np.arange(P) < 16)                   # 16 mutated patients
    u = rng.standard_normal((P, F))                            # patient-level random effect, shared by all patches
    e = rng.standard_normal((P, K, F))                         # patch-level noise
    shift = np.zeros(F)
    shift[:6] = 0.9                                            # six informative features
    patches = u[:, None, :] + e + eff * mut[:, None, None] * shift[None, None, :]
    return {"patches": patches, "mutated": mut.astype(bool)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: patches (40, 6, 20) image features of each tissue patch of each patient, axes (patients, patches, features);
    mutated (40,) bool, True if the patient's tumour carries the mutation.
    Holds when the claim is supported by the data. Written by someone else."""
    def _auc(s, y):
        p, q = s[y], s[~y]
        diff = p[:, None] - q[None, :]
        return float(((diff > 0).sum() + 0.5 * (diff == 0).sum()) / (p.size * q.size))

    def _folds(y, k, rng):
        # stratified random fold labels 0..k-1
        f = np.empty(y.size, dtype=int)
        off = 0
        for c in (True, False):
            idx = np.flatnonzero(y == c)
            f[rng.permutation(idx)] = (np.arange(idx.size) + off) % k
            off += idx.size
        return f

    def _logit(xt, yt, lam):
        # ridge logistic regression (Newton / IRLS), unpenalised intercept
        n, p = xt.shape
        a = np.column_stack([np.ones(n), xt])
        pen = lam * np.eye(p + 1)
        pen[0, 0] = 0.0
        t = yt.astype(float)
        w = np.zeros(p + 1)
        for _ in range(30):
            mu = 1.0 / (1.0 + np.exp(-np.clip(a @ w, -30.0, 30.0)))
            g = a.T @ (mu - t) + pen @ w
            h = (a.T * np.maximum(mu * (1.0 - mu), 1e-6)) @ a + pen
            step = np.linalg.solve(h, g)
            w = w - step
            if np.max(np.abs(step)) < 1e-8:
                break
        return w

    pt = np.asarray(d["patches"], dtype=float)
    mut = np.asarray(d["mutated"]).astype(bool)
    if not np.all(np.isfinite(pt)):
        return None
    n_pat, n_patch, n_feat = pt.shape
    x = pt.reshape(n_pat * n_patch, n_feat)          # one row per patch
    y = np.repeat(mut, n_patch)                       # the patient's status on each of its patches
    if mut.sum() < 5 or (~mut).sum() < 5 or not np.all(x.std(axis=0) > 0):
        return None
    lam = 1.0        # ridge penalty of the logistic model
    thr = 0.75       # claimed AUC

    rng = np.random.default_rng(11)
    fold = np.repeat(_folds(mut, 5, rng), n_patch)    # folds are formed over patients; all patches of a patient go together
    s = np.zeros(y.size)
    for k in range(5):
        te = fold == k
        w = _logit(x[~te], y[~te], lam)
        s[te] = w[0] + x[te] @ w[1:]
    return bool(_auc(s, y) >= thr)


def permute_mutation_across_patients(d, rng):
    return {**d, "mutated": d["mutated"][rng.permutation(P)]}


STUDY = Study(
    name="W06",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the mutation shifts six features by 0.9 sd -> shift 0; patient random effects, patch noise, group sizes and nesting unchanged"),
    },
    controls=[Control("permute_mutation_across_patients", ["C"], transform=permute_mutation_across_patients)],
)
