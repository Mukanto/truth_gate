"""W43: Across 90 farms, a farm that applies more fertilizer per hectare obtains a higher crop yield per hectare: the standardised regression slope (both variables z-scored) of yield per hectare on fertilizer per hectare is at least 0.3."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

N = 90


def _gen(rng, eff):
    area = np.exp(np.log(50.0) + 1.0 * rng.standard_normal(N))            # true cropped area, hectares
    zf = rng.standard_normal(N)
    e = rng.standard_normal(N)
    err = rng.standard_normal(N)
    fert_ha = 90.0 * np.exp(0.5 * zf)                                     # kg N per hectare
    sd_res = np.sqrt(0.09 - eff * 0.16 ** 2)                              # same total log variance of yield per hectare in both worlds
    yield_ha = 5.0 * np.exp(eff * 0.16 * zf + sd_res * e)                 # tonnes per hectare
    area_rep = area * np.exp(0.15 * err)                                  # the recorded area carries a 15% error
    return {"yield_total": yield_ha * area, "fertilizer_total": fert_ha * area, "farm_area": area_rep}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: yield_total (90,) total annual crop harvest of the farm, tonnes; fertilizer_total (90,) total annual
    fertilizer applied on the farm, kg of nitrogen; farm_area (90,) cropped area of the farm, hectares.
    Holds when the claim is supported by the data. Written by someone else."""
    def z(x):
        return (x - x.mean()) / x.std()

    yt = np.asarray(d["yield_total"], dtype=float)
    ft = np.asarray(d["fertilizer_total"], dtype=float)
    area = np.asarray(d["farm_area"], dtype=float)
    if not (np.all(np.isfinite(yt)) and np.all(np.isfinite(ft)) and np.all(np.isfinite(area))):
        return None
    if np.std(yt) == 0 or np.std(ft) == 0 or np.std(area) == 0:
        return None
    zy, zf, za = z(yt), z(ft), z(area)
    X = np.column_stack([np.ones(len(zy)), zf, za])
    coef = np.linalg.lstsq(X, zy, rcond=None)[0]     # yield on fertilizer with the area as a covariate
    return bool(coef[1] >= 0.3)


def permute_yield_per_hectare(d, rng):
    y_ha = d["yield_total"] / d["farm_area"]
    return {**d, "yield_total": y_ha[rng.permutation(N)] * d["farm_area"]}


STUDY = Study(
    name="W43",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="yield per hectare rises with fertilizer per hectare (0.16 log units per sd, correlation about 0.5) -> independent of it (same variance); very unequal farm sizes (which make the totals correlate), the 15% error in the recorded area and all spreads unchanged"),
    },
    controls=[Control("permute_yield_per_hectare", ["C"], transform=permute_yield_per_hectare)],
)
