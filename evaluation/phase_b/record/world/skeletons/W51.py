"""W51: In adult rats, a heavier heart relative to body weight goes with higher systolic blood pressure: across 60 rats, the standardised regression slope (variables z-scored) of systolic pressure on heart weight per body weight is at least 0.3."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

N = 60


def _gen(rng, eff):
    zb = rng.standard_normal(N)
    zr = rng.standard_normal(N)
    e = rng.standard_normal(N)
    bw = 350.0 * np.exp(0.10 * zb)                                        # g
    ratio = 0.0031 * np.exp(0.08 * zr)                                    # relative heart weight, independent of body weight
    hw = ratio * bw                                                       # g
    sbp = 130.0 + eff * 7.5 * zr + 10.0 * zb + 9.0 * e                    # pressure also rises with body weight (age), both worlds
    return {"systolic_pressure": sbp, "heart_weight": hw, "body_weight": bw}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: systolic_pressure (60,) systolic blood pressure, mmHg, by tail-cuff; heart_weight (60,) wet heart weight at
    necropsy, g; body_weight (60,) body weight at necropsy, g.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def permute_relative_heart_weight(d, rng):
    ratio = d["heart_weight"] / d["body_weight"]
    return {**d, "heart_weight": ratio[rng.permutation(N)] * d["body_weight"]}


STUDY = Study(
    name="W51",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="pressure rises with relative heart weight (7.5 mmHg per sd, correlation about 0.5) -> no dependence on relative heart weight; pressure still rises with body weight (10 mmHg per sd) so absolute heart weight (proportional to body weight) still correlates with pressure at about 0.6"),
    },
    controls=[Control("permute_relative_heart_weight", ["C"], transform=permute_relative_heart_weight)],
)
