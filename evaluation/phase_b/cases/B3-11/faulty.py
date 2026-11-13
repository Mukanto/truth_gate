"""W02: Buildings with more occupants use less energy per square metre of floor area: across 150 office buildings, the Spearman rank correlation between the number of occupants and annual energy use per square metre is at most -0.3."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

N = 150


def _gen(rng, eff):
    za = rng.standard_normal(N)
    zd = rng.standard_normal(N)
    e = rng.standard_normal(N)
    la = np.log(8000.0) + 0.8 * za                      # log floor area
    lo = la + np.log(0.02) + 0.35 * zd                  # log occupants: about one person per 50 m2
    zo = (lo - lo.mean()) / lo.std()
    # log energy intensity (kWh/m2/yr): a mild scale effect of floor area in both worlds, and the occupant effect
    leui = np.log(180.0) - 0.08 * za - eff * 0.12 * zo + 0.30 * e
    area = np.exp(la)
    occ = np.maximum(np.round(np.exp(lo)), 5.0)
    energy = np.exp(leui) * area / 1000.0               # MWh
    return {"energy_use": energy, "floor_area": area, "occupants": occ}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: energy_use (150,) annual metered energy use, MWh; floor_area (150,) gross floor area, m2;
    occupants (150,) typical number of occupants (headcount).
    Holds when the claim is supported by the data. Written by someone else."""
    def rank(x):
        u, inv, cnt = np.unique(x, return_inverse=True, return_counts=True)
        return (np.cumsum(cnt) - (cnt - 1) / 2.0)[inv]
    energy = np.asarray(d["energy_use"], dtype=float)
    area = np.asarray(d["floor_area"], dtype=float)
    occ = np.asarray(d["occupants"], dtype=float)
    if not (np.all(np.isfinite(energy)) and np.all(np.isfinite(area)) and np.all(np.isfinite(occ))):
        return None
    if np.std(energy) == 0 or np.std(area) == 0 or np.std(occ) == 0:
        return None
    with np.errstate(divide="ignore", invalid="ignore"):
        eui = energy / area                          # energy use per square metre
    if not np.all(np.isfinite(eui)) or np.std(eui) == 0:
        return None
    rho = np.corrcoef(rank(occ), rank(eui))[0, 1]
    return bool(rho <= -0.3)


def permute_occupants(d, rng):
    return {**d, "occupants": d["occupants"][rng.permutation(N)]}


STUDY = Study(
    name="W02",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="direct effect of occupant count on energy intensity (-0.12 log units per sd) -> 0; the area-driven scale effect on intensity, the occupants-area link and all noise are unchanged"),
    },
    controls=[Control("permute_occupants", ["C"], transform=permute_occupants)],
)
