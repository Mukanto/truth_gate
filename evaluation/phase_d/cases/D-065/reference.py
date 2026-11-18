"""D-065: Habitat measurements predict vegetation cover at new sites: the Pearson correlation between predicted and observed cover is at least 0.40."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

S = 40
M = 20
V = 6
ICC = 0.30
RHOU = 0.30
RHOE = 0.25
SGN = (1.0, 1.0, -1.0, 1.0, -1.0, 1.0)
BETA = (0.7, 0.4, 0.5, 0.0, -0.3, 0.3)
R2 = 0.35
U_SITE = 0.20

def derange(rng, n):
    """Index array that gives every unit the value of a different unit."""
    order = rng.permutation(n)
    idx = np.empty(n, dtype=np.int64)
    idx[order] = np.roll(order, -1)
    return idx


def gen(rng):
    """Habitat: a site effect (share ICC of each variable's variance, variables correlated RHOU across sites)
    plus plot-level variation (correlated RHOE across variables). Cover: a linear response to the standardised
    habitat (variance share R2), a site-level residual (share U_SITE that habitat does not explain) and
    plot-level noise. The null cover is that of another site."""
    sg = np.array(SGN)
    gs = rng.normal(size=(S, 1))
    u = np.sqrt(RHOU) * gs * sg + np.sqrt(1.0 - RHOU) * rng.normal(size=(S, V))
    qp = rng.normal(size=(S, M, 1))
    e = np.sqrt(RHOE) * qp * sg + np.sqrt(1.0 - RHOE) * rng.normal(size=(S, M, V))
    h = np.sqrt(ICC) * u[:, None, :] + np.sqrt(1.0 - ICC) * e
    cu = RHOU * np.outer(sg, sg)
    ce = RHOE * np.outer(sg, sg)
    cc = ICC * cu + (1.0 - ICC) * ce
    np.fill_diagonal(cc, 1.0)
    beta = np.array(BETA)
    scale = np.sqrt(R2 / (beta @ cc @ beta))
    z = (h @ beta) * scale + np.sqrt(U_SITE) * rng.normal(size=(S, 1)) \
        + np.sqrt(1.0 - R2 - U_SITE) * rng.normal(size=(S, M))
    cover = np.clip(45.0 + 18.0 * z, 0.0, 100.0)
    col = np.arange(V)
    hab = 3.0 * np.cos(1.9 * col) + (1.0 + 0.5 * np.sin(1.3 * col)) * h
    idx = derange(rng, S)
    return hab, cover, cover[idx]


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    hab, cover, _ = gen(rng)
    return {"habitat": hab, "cover": cover}


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    hab, _, cover = gen(rng)
    return {"habitat": hab, "cover": cover}


def control(d, rng):
    """Gives every site the cover values of another site."""
    out = {k: np.array(v) for k, v in d.items()}
    out["cover"] = d["cover"][derange(rng, S)]
    return out


def criterion(d):
    """Data keys: habitat (sites, plots, variables) float64: habitat measurements of each plot at each site; cover (sites, plots) float64: vegetation cover measured in each plot.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


STUDY = Study(
    name="D-065",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="each site gets the cover values of another site (independent of the habitat); site structure of cover and all distributions unchanged"),
    },
    controls=[Control("D-065", ["C"], transform=control)],
)
