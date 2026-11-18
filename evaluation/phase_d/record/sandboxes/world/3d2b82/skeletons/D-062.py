"""D-062: In at least 60% of the species, femur length and humerus length are positively associated after accounting for body length: within the species, the partial correlation between femur length and humerus length, given body length, is at least 0.2."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

_S = 12
_N = 30
_SITES = 3


def _generate(rng, rho_scale):
    # Species differ strongly in size (log-uniform mean head-and-body length 70-300 mm).
    log_mean_bl = rng.uniform(np.log(70.0), np.log(300.0), _S)
    # Species limb proportions, correlated across species (shared locomotor ecology).
    zf = rng.standard_normal(_S)
    zh = 0.6 * zf + 0.8 * rng.standard_normal(_S)
    ratio_f = 0.19 * np.exp(0.12 * zf)
    ratio_h = 0.15 * np.exp(0.12 * zh)
    slope_f = 0.90 + 0.05 * rng.standard_normal(_S)
    slope_h = 0.85 + 0.05 * rng.standard_normal(_S)
    # Individuals from 3 sampling sites per species (10 each): site differences in body size.
    site = np.repeat(0.03 * rng.standard_normal((_S, _SITES)), _N // _SITES, axis=1)
    dl = site + 0.07 * rng.standard_normal((_S, _N))       # log deviation of body length from species mean
    body_length = np.exp(log_mean_bl[:, None] + dl)
    # Within-species residual (size-independent) correlation of femur and humerus.
    rho = np.clip(0.38 + 0.15 * rng.standard_normal(_S), 0.0, 0.8) * rho_scale
    e1 = rng.standard_normal((_S, _N))
    e2 = rng.standard_normal((_S, _N))
    res_f = 0.045 * e1
    res_h = 0.050 * (rho[:, None] * e1 + np.sqrt(1.0 - rho[:, None] ** 2) * e2)
    mean_bl = np.exp(log_mean_bl)[:, None]
    femur = ratio_f[:, None] * mean_bl * np.exp(slope_f[:, None] * dl + res_f)
    humerus = ratio_h[:, None] * mean_bl * np.exp(slope_h[:, None] * dl + res_h)
    return {"femur": femur.astype(np.float64), "humerus": humerus.astype(np.float64),
            "body_length": body_length.astype(np.float64)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _generate(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _generate(rng, 0.0)


def criterion(d):
    """Data keys: femur (12, 30) float, femur length in mm, rows are the 12 species, columns the 30 individuals
    sampled per species; humerus (12, 30) float, humerus length in mm of the same individuals;
    body_length (12, 30) float, head-and-body length in mm of the same individuals.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def _permute_humerus_within_species(d, rng):
    h = d["humerus"]
    s, n = h.shape
    idx = np.argsort(rng.random((s, n)), axis=1)
    ident = np.all(idx == np.arange(n)[None, :], axis=1)
    idx[ident] = np.roll(np.arange(n), 1)
    return {**d, "humerus": np.take_along_axis(h, idx, axis=1)}


STUDY = Study(
    name="D-062",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="within-species residual correlation of femur and humerus given body length set to 0 in every species; allometry, species and site structure unchanged"),
    },
    controls=[Control("humerus_permuted_within_species", ["C"], transform=_permute_humerus_within_species)],
    relational=[("femur", "humerus")],
)
