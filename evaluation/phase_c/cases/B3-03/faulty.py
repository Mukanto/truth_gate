"""C39: In patients attending a hypertension clinic, left ventricular mass adds explanatory power for systolic blood pressure beyond body surface area: the gain in R-squared when left ventricular mass is added to a linear regression of systolic pressure on body surface area is at least 0.05."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_PATIENTS = 300
BSA_MEAN = 1.92
BSA_SD = 0.20
LVM_MEAN = 185.0
LVM_PER_BSA_SD = 22.0     # g of left ventricular mass per SD of body surface area
LVM_RESID_SD = 38.0       # g, variation of left ventricular mass not explained by body size
SBP_MEAN = 152.0
SBP_PER_BSA_SD = 3.0      # mmHg per SD of body surface area
SBP_PER_RESID_SD = 7.0    # mmHg per SD of size-independent left ventricular mass
SBP_NOISE_SD = 17.5


def _clinic(rng, linked):
    bsa = np.clip(rng.normal(BSA_MEAN, BSA_SD, N_PATIENTS), 1.35, 2.60)
    size = (bsa - BSA_MEAN) / BSA_SD
    resid = rng.normal(0.0, 1.0, N_PATIENTS)
    unrelated = rng.normal(0.0, 1.0, N_PATIENTS)
    lv_mass = np.clip(LVM_MEAN + LVM_PER_BSA_SD * size + LVM_RESID_SD * resid, 70.0, None)
    driver = resid if linked else unrelated
    sbp = SBP_MEAN + SBP_PER_BSA_SD * size + SBP_PER_RESID_SD * driver + rng.normal(0.0, SBP_NOISE_SD, N_PATIENTS)
    return {
        "lv_mass": lv_mass.astype(np.float64),
        "body_surface_area": bsa.astype(np.float64),
        "systolic_bp": sbp.astype(np.float64),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _clinic(rng, True)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _clinic(rng, False)


def _permute_lv_mass(d, rng):
    return {**d, "lv_mass": rng.permutation(d["lv_mass"])}


def _permute_lv_residual(d, rng):
    # keeps the relation of left ventricular mass to body size, and deals the rest of it out at random
    slope, intercept = np.polyfit(d["body_surface_area"], d["lv_mass"], 1)
    fitted = intercept + slope * d["body_surface_area"]
    return {**d, "lv_mass": fitted + rng.permutation(d["lv_mass"] - fitted)}


def criterion(d):
    """Data keys: lv_mass, float (300,), left ventricular mass of each patient from echocardiography, in g;
    body_surface_area, float (300,), body surface area of each patient, in square metres; systolic_bp, float (300,),
    resting systolic blood pressure of each patient, in mmHg.
    Holds when the claim is supported by the data. Written by someone else."""
    lvm = np.asarray(d["lv_mass"], dtype=float)
    bsa = np.asarray(d["body_surface_area"], dtype=float)
    sbp = np.asarray(d["systolic_bp"], dtype=float)

    def flat(a):
        return not (float(np.sum((a - a.mean()) ** 2)) > 0.0)


    def r2(y, cols):
        n = y.shape[0]
        X = np.column_stack([np.ones(n)] + list(cols))
        tss = float(np.sum((y - y.mean()) ** 2))
        if n < X.shape[1] + 1 or not (tss > 0.0):
            return None
        res = y - X @ np.linalg.lstsq(X, y, rcond=None)[0]
        return 1.0 - float(res @ res) / tss

    if not (np.all(np.isfinite(lvm)) and np.all(np.isfinite(bsa)) and np.all(np.isfinite(sbp))):
        return None
    # R-squared of systolic pressure regressed on the quotient left ventricular mass / body surface area
    with np.errstate(divide="ignore", invalid="ignore"):
        quotient = lvm / bsa
    if not np.all(np.isfinite(quotient)) or flat(quotient) or flat(sbp):
        return None
    value = r2(sbp, [quotient])
    if value is None or not np.isfinite(value):
        return None
    return bool(value >= 0.05)


STUDY = Study(
    name="C39",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the relation of systolic pressure to left ventricular mass beyond body surface area is set to 0 (that share of the pressure variance comes from an unrelated source of the same size)"),
    },
    controls=[
        Control("permute_lv_mass", ["C"], transform=_permute_lv_mass),
        Control("permute_lv_mass_residual", ["C"], transform=_permute_lv_residual),
    ],
)
