"""C02: Within crustacean species, claw length rises with abdomen length after accounting for total body length: across species, the mean of the within-species coefficients of abdomen length in a linear regression of claw length on abdomen length and body length is at least 0.15."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control


def _gen(rng, coef):
    s, n = 15, 40
    size = rng.uniform(40.0, 120.0, (s, 1))                    # typical body length of the species, mm
    body = size * (1.0 + 0.12 * rng.normal(0.0, 1.0, (s, n)))
    abd_ratio = rng.uniform(0.35, 0.50, (s, 1))
    abd_dev = 0.03 * size * rng.normal(0.0, 1.0, (s, n))       # abdomen length not explained by body length
    abdomen = abd_ratio * body + abd_dev
    b_abd = coef * (1.0 + 0.2 * rng.normal(0.0, 1.0, (s, 1)))  # within-species coefficient of abdomen length
    b_body = rng.uniform(0.25, 0.40, (s, 1))                   # claw length per mm of body length
    claw = 0.05 * size + b_body * body + b_abd * abd_dev + 0.02 * size * rng.normal(0.0, 1.0, (s, n))
    return {"abdomen_length": abdomen, "claw_length": claw, "body_length": body}


def plus(rng):
    """The claim is true: mean within-species coefficient of abdomen length 0.35 (species SD 0.07)."""
    return _gen(rng, 0.35)


def minus(rng):
    """The claim is false: abdomen length has coefficient 0 given body length; claw still scales with body."""
    return _gen(rng, 0.0)


def _permute_abdomen(d, rng):
    return {**d, "abdomen_length": rng.permuted(d["abdomen_length"], axis=1)}


def criterion(d):
    """Data keys: abdomen_length, float (15 species, 40 individuals), abdomen length of each individual in mm;
    claw_length, float (15, 40), length of the larger claw in mm; body_length, float (15, 40), total body
    length in mm.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


STUDY = Study(
    name="C02",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="within-species coefficient of abdomen length (given body length) set to zero in every species"),
    },
    controls=[Control("permute_abdomen_within_species", ["C"], transform=_permute_abdomen)],
)
