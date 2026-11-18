"""D-042: A nearest-neighbour regression (one neighbour, Euclidean distance on standardised descriptors) of the response y on the descriptors X predicts y for new compounds with a Pearson correlation between predicted and observed y of at least 0.30."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_REC = 1200         # compound records
N_CMP = 900          # unique compounds (the other 300 records are replicate measurements)
P = 20
N_LAT = 4            # latent physico-chemical dimensions
N_SER = 60           # congeneric series (scaffolds)
P_SERIES = 0.8       # share of compounds that belong to a series; the rest are singletons
SRC_P = np.array([0.3, 0.2, 0.15, 0.1, 0.1, 0.07, 0.05, 0.03])   # assay sources of the records
SRC_SD = 0.3         # assay source offset, log units
REP_SD = 0.45        # replicate measurement noise, log units
SERIES_SD = 0.8      # series-level activity
IDIO_SD = 0.5        # compound-specific activity not explained by descriptors (activity cliffs)


def _loadings():
    W = np.zeros((P, N_LAT))
    W[0:6, 0] = [0.9, 0.8, 0.7, 0.75, 0.6, 0.5]
    W[4:11, 1] = [0.4, 0.5, 0.85, 0.8, 0.6, 0.5, 0.45]
    W[10:16, 2] = [0.5, 0.85, 0.8, 0.7, 0.6, 0.5]
    W[15:20, 3] = [0.5, 0.8, 0.75, 0.7, 0.6]
    return W


def _scaled(raw, cov, sd):
    return raw * (sd / np.sqrt(raw @ cov @ raw))


W = _loadings()
COV_DESC = 1.1225 * W @ W.T + 0.4225 * np.eye(P)     # covariance of the latent descriptors
COV_WITHIN = 0.1225 * W @ W.T + 0.0625 * np.eye(P)   # covariance of within-series deviations
GAMMA_GLOBAL = _scaled(np.array([0, 0, 0, 0, 0, 0, 1.0, 0.6, 0, 0, 0, -0.8, -0.5, 0, 0, 0, 0.4, 0, 0, 0],
                                dtype=np.float64), COV_DESC, 0.3)
GAMMA_LOCAL = _scaled(np.array([0.5, 0, -0.4, 0, 0.3, 0, 0.6, 0, 0, -0.5, 0, 0.4, 0, 0, 0.3, 0, -0.3, 0, 0.5, 0],
                               dtype=np.float64), COV_WITHIN, 0.4)
MEANS = np.array([380.0, 27.0, 330.0, 5.0, 0.4, 2.5, 3.0, 1.2, 0.9, 7.5,
                  75.0, 1.8, 5.2, 0.6, 2.1, 2.4, 0.35, 1.6, 9.0, 0.25])
SDS = np.array([80.0, 6.0, 70.0, 2.0, 0.15, 0.8, 1.2, 0.5, 0.4, 2.5,
                25.0, 1.0, 1.8, 0.2, 0.9, 1.0, 0.12, 0.7, 3.0, 0.1])


def _world(rng, effect):
    in_series = rng.random(N_CMP) < P_SERIES
    sw = np.exp(rng.normal(0.0, 0.5, N_SER))
    series = rng.choice(N_SER, N_CMP, p=sw / sw.sum())
    centre = rng.standard_normal((N_SER, N_LAT)) @ W.T + 0.6 * rng.standard_normal((N_SER, P))
    single = rng.standard_normal((N_CMP, N_LAT)) @ W.T + 0.6 * rng.standard_normal((N_CMP, P))
    within = 0.35 * (rng.standard_normal((N_CMP, N_LAT)) @ W.T) + 0.25 * rng.standard_normal((N_CMP, P))
    desc = np.where(in_series[:, None], centre[series], single) + within
    level = np.where(in_series, SERIES_SD * rng.standard_normal(N_SER)[series], SERIES_SD * rng.standard_normal(N_CMP))
    activity = 6.0 + level + desc @ GAMMA_GLOBAL + within @ GAMMA_LOCAL + IDIO_SD * rng.standard_normal(N_CMP)
    # in minus the compound-level activities are reassigned at random across the unique compounds
    reassign = rng.permutation(N_CMP)
    act = activity if effect else activity[reassign]
    pop = np.exp(rng.standard_normal(N_CMP))
    extra = rng.choice(N_CMP, N_REC - N_CMP, p=pop / pop.sum())
    compound = np.concatenate([np.arange(N_CMP), extra])[rng.permutation(N_REC)]
    src = rng.choice(SRC_P.shape[0], N_REC, p=SRC_P)
    src_off = SRC_SD * rng.standard_normal(SRC_P.shape[0])
    y = act[compound] + src_off[src] + REP_SD * rng.standard_normal(N_REC)
    X = MEANS + SDS * desc[compound]
    return {"X": np.asarray(X, dtype=np.float64), "y": np.asarray(y, dtype=np.float64)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _world(rng, True)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _world(rng, False)


def criterion(d):
    """Data keys: X (1200, 20) float64, 20 continuous molecular descriptors (columns) of each compound record (rows);
    y (1200,) float64, continuous activity response measured for each compound record.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def _shuffle_compound_means(d, rng):
    _, inv = np.unique(d["X"], axis=0, return_inverse=True)
    inv = np.asarray(inv).ravel()
    m = int(inv.max()) + 1
    counts = np.bincount(inv, minlength=m)
    means = np.bincount(inv, weights=d["y"], minlength=m) / counts
    p = rng.permutation(m)
    if np.all(p == np.arange(m)):
        p = np.roll(p, 1)
    y = d["y"] - means[inv] + means[p][inv]
    return {**d, "y": y}


STUDY = Study(
    name="D-042",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="compound activities reassigned at random across unique compounds: descriptors carry no information on activity"),
    },
    controls=[Control("compound_mean_activity_shuffled_across_compounds", ["C"], transform=_shuffle_compound_means)],
    relational=[("X", "y")],
)
