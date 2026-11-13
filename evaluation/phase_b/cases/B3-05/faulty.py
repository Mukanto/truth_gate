"""W01: Across 120 adult human skeletons, femur length relative to vertebral column length and tibia length relative to vertebral column length are positively related: the Pearson correlation between the two relative lengths is at least 0.4."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

N = 120


def _gen(rng, shared):
    g = 0.06 * rng.standard_normal(N)            # overall body size, scales all three bones
    lf = rng.standard_normal(N)                  # limb-proportion factor of the femur
    lt0 = rng.standard_normal(N)                 # independent limb factor of the tibia
    ef = rng.standard_normal(N)
    et = rng.standard_normal(N)
    ev = rng.standard_normal(N)
    lt = shared * lf + (1.0 - shared) * lt0      # plus: same factor as the femur; minus: independent
    femur = 450.0 * np.exp(g + 0.025 * lf + 0.03 * ef)
    tibia = 370.0 * np.exp(g + 0.025 * lt + 0.03 * et)
    vcl = 700.0 * np.exp(g + 0.03 * ev)          # column-length error is the shared denominator
    return {"femur_length": femur, "tibia_length": tibia, "vertebral_column_length": vcl}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: femur_length (120,) maximum femur length, mm; tibia_length (120,) maximum tibia length, mm;
    vertebral_column_length (120,) length of the articulated vertebral column, mm.
    Holds when the claim is supported by the data. Written by someone else."""
    fem = np.asarray(d["femur_length"], dtype=float)
    tib = np.asarray(d["tibia_length"], dtype=float)
    vcl = np.asarray(d["vertebral_column_length"], dtype=float)
    if not (np.all(np.isfinite(fem)) and np.all(np.isfinite(tib)) and np.all(np.isfinite(vcl))):
        return None
    if np.std(fem) == 0 or np.std(tib) == 0 or np.std(vcl) == 0:
        return None
    with np.errstate(divide="ignore", invalid="ignore"):
        fi, ti = fem / vcl, tib / vcl                 # relative lengths (indices with the same denominator)
    if not (np.all(np.isfinite(fi)) and np.all(np.isfinite(ti))) or np.std(fi) == 0 or np.std(ti) == 0:
        return None
    r = np.corrcoef(fi, ti)[0, 1]
    return bool(r >= 0.4)


def permute_tibia(d, rng):
    return {**d, "tibia_length": d["tibia_length"][rng.permutation(N)]}


STUDY = Study(
    name="W01",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the femur and tibia share a limb-proportion factor (relative-length correlation about 0.6) -> the factors are independent (each keeps its variance); the shared column-length error and body size are unchanged"),
    },
    controls=[Control("permute_tibia", ["C"], transform=permute_tibia)],
)
