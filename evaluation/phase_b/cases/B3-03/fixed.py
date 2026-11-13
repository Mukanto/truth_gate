"""W53: In patients with heart failure, a larger right ventricular end-diastolic volume goes with a lower right ventricular ejection fraction: across 30 patients, the standardised slope (both variables z-scored) of end-diastolic volume index on ejection fraction is at most -0.4."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

N = 30


def _gen(rng, r):
    ze = rng.standard_normal(N)
    zh = r * ze + np.sqrt(1.0 - r ** 2) * rng.standard_normal(N)          # r = -0.65 in plus, 0 in minus
    ef = np.clip(0.32 + 0.09 * ze, 0.12, 0.60)                            # true ejection fraction
    edv = 110.0 * np.exp(0.25 * zh)                                       # true end-diastolic volume index, mL/m2
    sv = edv * ef                                                         # true stroke volume index
    svi = sv * np.exp(0.10 * rng.standard_normal(N))                      # thermodilution stroke volume index
    rvef = np.clip(ef + 0.04 * rng.standard_normal(N), 0.08, 0.70)        # thermistor ejection fraction
    edv_rn = edv * np.exp(0.10 * rng.standard_normal(N))                  # radionuclide volume, independent error
    return {"stroke_volume_index": svi, "rvef": rvef, "rv_edv_index_radionuclide": edv_rn}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, -0.65)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: stroke_volume_index (30,) stroke volume index, mL/m2, from thermodilution; rvef (30,) right ventricular
    ejection fraction, fraction 0-1, from a fast-response thermistor catheter; rv_edv_index_radionuclide (30,) right
    ventricular end-diastolic volume index, mL/m2, from gated radionuclide ventriculography done in the same session.
    Holds when the claim is supported by the data. Written by someone else."""
    svi = np.asarray(d["stroke_volume_index"], dtype=float)
    ef = np.asarray(d["rvef"], dtype=float)
    edv = np.asarray(d["rv_edv_index_radionuclide"], dtype=float)   # volume measured independently
    if not (np.all(np.isfinite(edv)) and np.all(np.isfinite(ef))):
        return None
    if np.std(edv) == 0 or np.std(ef) == 0:
        return None
    zx = (ef - ef.mean()) / ef.std()
    zy = (edv - edv.mean()) / edv.std()
    slope = np.sum(zx * zy) / np.sum(zx * zx)
    return bool(slope <= -0.4)


def permute_radionuclide_volume(d, rng):
    return {**d, "rv_edv_index_radionuclide": d["rv_edv_index_radionuclide"][rng.permutation(N)]}


STUDY = Study(
    name="W53",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="true correlation between log end-diastolic volume and ejection fraction -0.65 -> 0; stroke volume remains volume x fraction, thermodilution (10%) and thermistor (0.04) errors, the independent radionuclide error (10%) and all spreads unchanged"),
    },
    controls=[Control("permute_radionuclide_volume", ["C"], transform=permute_radionuclide_volume)],
)
