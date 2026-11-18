"""D-054: Gene-expression features discriminate cases from controls in new subjects: the area under the ROC curve of a linear classifier (ridge regression on the diagnosis coded as plus or minus one, penalty 10 on standardised features) that uses 20 of the 1000 expression features to recover the diagnosis y is at least 0.65."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N, P = 80, 1000
NM, MS = 50, 20      # 50 co-expression modules of 20 genes
LOADM = 0.6          # module loading: correlation 0.36 between genes of a module
DELTA = 0.65         # case-control mean difference in the genes of two modules (plus)
DE_MODULES = (3, 17)
SHIFT = np.where(np.isin(np.arange(P) // MS, np.array(DE_MODULES)), DELTA, 0.0)


def _draw(rng):
    lab = rng.permutation(N) < N // 2
    M = rng.standard_normal((N, NM))
    E = rng.standard_normal((N, P))
    X = LOADM * np.repeat(M, MS, axis=1) + np.sqrt(1.0 - LOADM ** 2) * E
    X = X + (lab.astype(float) - 0.5)[:, None] * SHIFT[None, :]
    return np.ascontiguousarray(X), lab


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    X, lab = _draw(rng)
    return {"X": X, "y": lab}


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    X, lab = _draw(rng)
    return {"X": X, "y": lab[rng.permutation(N)]}


def criterion(d):
    """Data keys: X (samples, features) = (80, 1000), expression level of 1000 genes per subject;
    y (samples,) = (80,), bool, True where the subject has the diagnosis (40 cases, 40 controls).
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def permute_y(d, rng):
    return {"X": np.array(d["X"]), "y": d["y"][rng.permutation(N)]}


STUDY = Study(
    name="D-054",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the diagnosis labels are reassigned to other subjects (permuted), so y carries no information on X; the case/control split, X and its group-shifted gene modules are unchanged"),
    },
    controls=[Control("D-054", ["C"], transform=permute_y)],
)
