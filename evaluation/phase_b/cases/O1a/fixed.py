"""W54: Using the recorded patient variables, a linear classifier identifies sepsis cases with an accuracy of at least 0.75 on new patients (the claim holds when the accuracy estimate is >= 0.75)."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

N, K = 250, 12


def _gen(rng, eff):
    sepsis = rng.random(N) < 0.30
    x = rng.standard_normal((N, K))
    x[:, :7] += eff * 0.65 * sepsis[:, None]                              # seven admission variables carry real information
    doses = rng.poisson(np.where(sepsis, 3.5, 0.3)).astype(float)         # doses of the targeted therapy, recorded after diagnosis
    x[:, 11] = doses
    return {"vars": x, "sepsis": sepsis.astype(bool)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: vars (250, 12) 12 recorded variables per patient: columns 0 to 10 are vital signs and laboratory values at
    admission and age, column 11 is the number of doses of the targeted therapy recorded during the stay;
    sepsis (250,) bool, True if the patient received a sepsis diagnosis (about 30%).
    Holds when the claim is supported by the data. Written by someone else."""
    x = np.asarray(d["vars"], dtype=float)
    y = np.asarray(d["sepsis"]).astype(bool)
    n_train = 150  # fixed block: the first 150 patients fit the classifier, the remaining ones score it
    if not (np.isfinite(x).all() and x.shape[0] > n_train):
        return None
    # the 11 variables available at admission; column 11 (therapy doses recorded during the stay) is left out
    use = x[:, :11]
    ytr = y[:n_train]
    yte = y[n_train:]
    if ytr.all() or not ytr.any():
        return None
    a_tr = np.column_stack([np.ones(n_train), use[:n_train]])
    w = np.linalg.lstsq(a_tr, ytr.astype(float), rcond=None)[0]  # linear classifier: least squares on 0/1 labels
    a_te = np.column_stack([np.ones(use.shape[0] - n_train), use[n_train:]])
    pred = (a_te @ w) > 0.5
    acc = float(np.mean(pred == yte))
    return bool(acc >= 0.75)


def permute_sepsis(d, rng):
    return {**d, "sepsis": d["sepsis"][rng.permutation(N)]}


STUDY = Study(
    name="W54",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="seven admission variables shifted 0.65 sd in sepsis (admission-only accuracy about 0.8) -> the admission variables carry no information; the therapy-dose count (about 3.5 doses in sepsis cases, 0.3 otherwise, recorded after the diagnosis) is unchanged"),
    },
    controls=[Control("permute_sepsis", ["C"], transform=permute_sepsis)],
)
