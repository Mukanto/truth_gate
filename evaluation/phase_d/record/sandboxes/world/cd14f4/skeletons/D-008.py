"""D-008: Within patients, oxygen consumption rises with oxygen delivery: the mean over patients of the within-patient slope of oxygen consumption on oxygen delivery is at least 0.1 mL/min per mL/min."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control


N_PATIENTS = 40
N_OCCASIONS = 6
SLOPE_MEAN = 0.20       # mean true within-patient slope of VO2 on DO2 (mL/min per mL/min)
SLOPE_SD = 0.08         # between-patient SD of the true slope
CO_ERROR_CV = 0.08      # thermodilution cardiac-output measurement error (relative SD)
CONTENT_ERROR_SD = 0.25  # co-oximetry error of arterial and mixed venous O2 content (mL/dL)
GAS_ERROR_CV = 0.05     # expired-gas (indirect calorimetry) VO2 measurement error (relative SD)


def _within_patient_order(rng, n, t):
    """An independent random ordering of the occasions of each patient (rows of an index array)."""
    return np.argsort(rng.random((n, t)), axis=1)


def _draw(rng, slope_mean):
    """One study. Returns (data, truth); truth holds the true DO2 / VO2 for checks."""
    n, t = N_PATIENTS, N_OCCASIONS
    size = rng.standard_normal(n)                          # body size: raises both cardiac output and VO2
    co_state = rng.standard_normal(n)
    co_mean = 5.5 * np.exp(0.15 * size + 0.15 * co_state)  # L/min
    co_true = co_mean[:, None] * np.exp(0.15 * rng.standard_normal((n, t)))   # fluid / inotrope changes
    hb = np.maximum(10.5 + 1.3 * rng.standard_normal(n), 7.5)[:, None] + 0.4 * rng.standard_normal((n, t))
    sao2 = np.minimum(0.96 + 0.015 * rng.standard_normal((n, t)), 0.995)
    pao2 = np.maximum(90.0 + 15.0 * rng.standard_normal((n, t)), 55.0)
    cao2_true = 1.34 * hb * sao2 + 0.003 * pao2          # mL O2 / dL
    do2_true = 10.0 * co_true * cao2_true                 # mL O2 / min
    vo2_mean = 210.0 * np.exp(0.15 * size + 0.10 * rng.standard_normal(n))
    slope = slope_mean + SLOPE_SD * rng.standard_normal(n)
    do2_dev = do2_true - do2_true.mean(axis=1, keepdims=True)
    vo2_true = vo2_mean[:, None] + slope[:, None] * do2_dev + 10.0 * rng.standard_normal((n, t))
    cvo2_true = cao2_true - vo2_true / (10.0 * co_true)  # Fick principle
    cardiac_output = co_true * np.exp(CO_ERROR_CV * rng.standard_normal((n, t)))
    arterial = cao2_true + CONTENT_ERROR_SD * rng.standard_normal((n, t))
    venous = cvo2_true + CONTENT_ERROR_SD * rng.standard_normal((n, t))
    vo2_gas = vo2_true * (1.0 + GAS_ERROR_CV * rng.standard_normal((n, t)))
    data = {
        "cardiac_output": cardiac_output,
        "arterial_o2_content": arterial,
        "venous_o2_content": venous,
        "vo2_expired_gas": vo2_gas,
    }
    return data, {"do2_true": do2_true, "vo2_true": vo2_true, "slope": slope}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _draw(rng, SLOPE_MEAN)[0]


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _draw(rng, 0.0)[0]


def criterion(d):
    """Data keys (rows = 40 patients, columns = 6 measurement occasions, all float64):
    cardiac_output (40, 6), thermodilution cardiac output in L/min;
    arterial_o2_content (40, 6), arterial blood O2 content in mL O2 per dL;
    venous_o2_content (40, 6), mixed venous blood O2 content in mL O2 per dL;
    vo2_expired_gas (40, 6), oxygen consumption from expired-gas analysis in mL/min.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def _vo2_occasions_permuted(d, rng):
    n, t = d["vo2_expired_gas"].shape
    order = _within_patient_order(rng, n, t)
    return {**d, "vo2_expired_gas": np.take_along_axis(d["vo2_expired_gas"], order, axis=1)}


def _delivery_occasions_permuted(d, rng):
    n, t = d["cardiac_output"].shape
    order = _within_patient_order(rng, n, t)
    return {
        **d,
        "cardiac_output": np.take_along_axis(d["cardiac_output"], order, axis=1),
        "arterial_o2_content": np.take_along_axis(d["arterial_o2_content"], order, axis=1),
    }


STUDY = Study(
    name="D-008",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="mean true within-patient slope of VO2 on DO2 set from 0.20 to 0 (between-patient "
                              "slope spread, body-size link between patients, all measurement errors and the Fick "
                              "relation unchanged)"),
    },
    controls=[
        Control("vo2_occasions_permuted_within_patient", ["C"], transform=_vo2_occasions_permuted),
        Control("delivery_occasions_permuted_within_patient", ["C"], transform=_delivery_occasions_permuted),
    ],
)
