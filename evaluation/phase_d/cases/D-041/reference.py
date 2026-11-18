"""D-041: The country-year indicators in X identify the onset of civil war in new country-years: the area under the ROC curve of a ridge-penalised logistic regression (penalty 1.0 on standardised indicators) of the onset y on X is at least 0.75."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N, P, K = 1400, 25, 3
N_POS = 56        # 4% onsets
COMM = 0.25       # share of each indicator's variance carried by 3 latent factors
DELTA = 0.5 * np.where(np.arange(P) % 2 == 0, 1.0, -1.0)   # class mean difference per indicator (plus)
_LD = np.sin(np.arange(1, P + 1)[:, None] * (np.arange(K)[None, :] + 1.09) * 0.87 + 0.3)
LOAD = _LD * (np.sqrt(COMM) / np.sqrt((_LD ** 2).sum(axis=1, keepdims=True)))
# missingness: column rates 0.05..0.55 (mean 0.30), multiplied by a country-year propensity with mean 1
RATE = np.linspace(0.05, 0.55, P)[(np.arange(P) * 7) % P]


def _draw(rng):
    lab = rng.permutation(N) < N_POS
    Fl = rng.standard_normal((N, K))
    Xc = Fl @ LOAD.T + np.sqrt(1.0 - COMM) * rng.standard_normal((N, P))
    Xc = Xc + lab[:, None] * DELTA[None, :]
    prop = rng.gamma(3.0, 1.0 / 3.0, size=(N, 1))
    miss = rng.random((N, P)) < np.minimum(RATE[None, :] * prop, 0.97)
    X = np.where(miss, np.nan, Xc)
    return X, lab


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    X, lab = _draw(rng)
    return {"X": X, "y": lab}


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    X, lab = _draw(rng)
    return {"X": X, "y": lab[rng.permutation(N)]}


def criterion(d):
    """Data keys: X (samples, features) = (1400, 25), 25 continuous country-year indicators, NaN where not recorded;
    y (samples,) = (1400,), bool, True where a civil war onset occurred in the country-year.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def permute_y(d, rng):
    return {"X": np.array(d["X"]), "y": d["y"][rng.permutation(N)]}


STUDY = Study(
    name="D-041",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the onset labels are reassigned to other country-years (permuted), so y carries no information on X; the onset count, X and the missingness are unchanged"),
    },
    controls=[Control("D-041", ["C"], transform=permute_y)],
)
