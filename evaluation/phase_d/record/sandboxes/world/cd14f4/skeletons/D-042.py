"""D-042: A nearest-neighbour regression (one neighbour, Euclidean distance on standardised descriptors) of the response y on the descriptors X predicts y for new compounds with a Pearson correlation between predicted and observed y of at least 0.30."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control


N_RECORDS = 1200
N_FEATURES = 20
# Records per compound: 300 compounds measured once, 150 twice, 100 three times, 75 four times (625 compounds).
# Replicate records of a compound share its descriptor vector exactly (descriptors are computed from structure).
RECORD_COUNTS = (1, 2, 3, 4)
COMPOUNDS_WITH_COUNT = (300, 150, 100, 75)
N_SERIES = 60                 # chemical series (analogue clusters) in descriptor space
LATENT_DIM = 6                # effective dimension of the descriptor space
WITHIN_SERIES_SD = 0.35       # spread of analogues around their series centre (latent units)
SIGNAL_SHARE = 0.85           # share of each standardised descriptor's variance carried by the latent space
G_SD = 0.973                  # population SD of the raw structure-activity surface below (offline Monte Carlo)
VAR_SAR, VAR_COMPOUND, VAR_ASSAY = 0.60, 0.25, 0.25   # activity variance components (pIC50 units squared)
PIC50_MEAN = 6.0
# Continuous descriptors: MW, logP, TPSA, partial-charge range, hydrophobic surface fraction, Kier flexibility,
# Balaban J, Fsp3, molar refractivity, polarizability, dipole moment, HOMO, LUMO, globularity, surface area,
# volume, complexity, logS, pKa, shape anisotropy.
DESC_MEAN = np.array([350.0, 3.0, 80.0, 0.9, 0.45, 6.0, 1.8, 0.35, 95.0, 35.0,
                      4.0, -9.0, -0.5, 0.2, 450.0, 320.0, 450.0, -4.0, 7.0, 0.4])
DESC_SD = np.array([80.0, 1.2, 25.0, 0.2, 0.1, 1.8, 0.3, 0.12, 20.0, 8.0,
                    1.5, 0.4, 0.6, 0.05, 80.0, 60.0, 120.0, 1.0, 2.0, 0.1])


def _shuffled(rng, x):
    """Permute the first axis; never returns the input unchanged."""
    y = x[rng.permutation(x.shape[0])]
    if np.array_equal(y, x):
        y = np.roll(x, 1, axis=0)
    return y


def _sar(z):
    """Raw structure-activity surface on the latent descriptor space."""
    s2 = 1.0 + WITHIN_SERIES_SD ** 2
    return (0.6 * z[:, 0] - 0.45 * z[:, 1] + 0.35 * z[:, 2] + 0.25 * z[:, 0] * z[:, 3]
            - 0.2 * (z[:, 1] ** 2 - s2))


def _draw(rng, informative):
    """One compound data set. Returns (data, truth); truth holds the compound of each record and its SAR value."""
    counts = np.repeat(np.array(RECORD_COUNTS), np.array(COMPOUNDS_WITH_COUNT))
    counts = counts[rng.permutation(counts.size)]
    n_comp = counts.size
    weight = np.exp(0.7 * rng.standard_normal(N_SERIES))
    series = rng.choice(N_SERIES, size=n_comp, p=weight / weight.sum())
    centres = rng.standard_normal((N_SERIES, LATENT_DIM))
    z = centres[series] + WITHIN_SERIES_SD * rng.standard_normal((n_comp, LATENT_DIM))
    # each descriptor loads on two or three latent dimensions
    mask = rng.random((LATENT_DIM, N_FEATURES)) < 0.4
    mask[rng.integers(0, LATENT_DIM, N_FEATURES), np.arange(N_FEATURES)] = True
    loading = mask * rng.normal(0.0, 1.0, (LATENT_DIM, N_FEATURES))
    loading = loading * np.sqrt(SIGNAL_SHARE / ((1.0 + WITHIN_SERIES_SD ** 2) * np.sum(loading ** 2, axis=0)))
    desc_std = z @ loading + np.sqrt(1.0 - SIGNAL_SHARE) * rng.standard_normal((n_comp, N_FEATURES))
    desc = DESC_MEAN + DESC_SD * desc_std
    sar = np.sqrt(VAR_SAR) * _sar(z) / G_SD
    shuffle = rng.permutation(n_comp)
    used = sar if informative else sar[shuffle]
    compound_activity = PIC50_MEAN + used + np.sqrt(VAR_COMPOUND) * rng.standard_normal(n_comp)
    compound_of_record = np.repeat(np.arange(n_comp), counts)
    compound_of_record = compound_of_record[rng.permutation(compound_of_record.size)]
    y = compound_activity[compound_of_record] + np.sqrt(VAR_ASSAY) * rng.standard_normal(N_RECORDS)
    data = {"X": desc[compound_of_record], "y": y}
    return data, {"compound": compound_of_record, "sar": sar, "used": used}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _draw(rng, True)[0]


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _draw(rng, False)[0]


def criterion(d):
    """Data keys (rows = 1200 compound records): X (1200, 20) float64, 20 continuous molecular descriptors
    recorded for each compound record, in natural units (MW, logP, TPSA, partial-charge range, hydrophobic surface
    fraction, Kier flexibility, Balaban J, Fsp3, molar refractivity, polarizability, dipole moment, HOMO, LUMO,
    globularity, surface area, volume, complexity, logS, pKa, shape anisotropy); y (1200,) float64, continuous
    activity response (pIC50-like) measured for each compound record.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def _activity_permuted_between_compounds(d, rng):
    """Move each compound's set of responses to another compound with the same number of records."""
    x, y = d["X"], d["y"]
    _, inverse, counts = np.unique(x, axis=0, return_inverse=True, return_counts=True)
    inverse = inverse.reshape(-1)
    order = np.argsort(inverse, kind="stable")
    starts = np.concatenate(([0], np.cumsum(counts)[:-1]))
    new = y.copy()
    for k in np.unique(counts):
        comps = np.flatnonzero(counts == k)
        if comps.size < 2:
            continue
        target = comps[rng.permutation(comps.size)]
        rec_a = order[(starts[comps][:, None] + np.arange(k)).ravel()]
        rec_b = order[(starts[target][:, None] + np.arange(k)).ravel()]
        new[rec_a] = y[rec_b]
    if np.array_equal(new, y):
        new = np.roll(y, 1)
    return {**d, "y": new}


def _y_permuted(d, rng):
    return {**d, "y": _shuffled(rng, d["y"])}


STUDY = Study(
    name="D-042",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="activity carries no descriptor information: each compound's structure-activity "
                              "value is taken from a randomly permuted compound (marginal of y, compound-level and "
                              "assay variance, replicate structure and descriptor space unchanged)"),
    },
    controls=[
        Control("activity_permuted_between_compounds", ["C"], transform=_activity_permuted_between_compounds),
        Control("y_permuted", ["C"], transform=_y_permuted),
    ],
)
