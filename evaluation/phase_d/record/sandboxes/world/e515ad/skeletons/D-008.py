"""D-008: Within patients, oxygen consumption rises with oxygen delivery: the mean over patients of the within-patient slope of oxygen consumption on oxygen delivery is at least 0.1 mL/min per mL/min."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_PAT = 40
N_OCC = 6
SLOPE_MEAN = 0.20  # true within-patient dVO2/dDO2 (mL/min per mL/min)
SLOPE_SD = 0.08  # between-patient SD of the true slope


def _icu(rng, slope_mean, slope_sd):
    """Critically ill patients measured at 6 occasions during a protocol that raises cardiac output.

    True physiology: DO2 = 10 * CO * CaO2; VO2 depends on DO2 through a patient-specific slope;
    mixed venous content follows the Fick relation CvO2 = CaO2 - VO2 / (10 * CO). Measurements
    carry realistic error: thermodilution CO ~7%, blood-gas contents 0.25 mL/dL, expired-gas VO2 ~5%.
    """
    n, t = N_PAT, N_OCC
    step = (np.arange(t) - (t - 1) / 2.0) / ((t - 1) / 2.0)
    co_base = np.clip(rng.normal(6.0, 1.2, (n, 1)), 3.5, 10.0)
    co_gain = rng.normal(0.6, 0.25, (n, 1))
    co_true = np.clip(co_base + co_gain * step + rng.normal(0.0, 0.5, (n, t)), 2.5, 12.0)
    hb = np.clip(rng.normal(10.5, 1.2, (n, 1)) + rng.normal(0.0, 0.3, (n, t)), 7.0, 15.0)
    sao2 = np.clip(rng.normal(0.955, 0.015, (n, 1)) + rng.normal(0.0, 0.01, (n, t)), 0.85, 0.995)
    pao2 = np.clip(rng.normal(85.0, 12.0, (n, 1)) + rng.normal(0.0, 8.0, (n, t)), 55.0, 160.0)
    cao2_true = 1.34 * hb * sao2 + 0.0031 * pao2
    do2_true = 10.0 * co_true * cao2_true
    do2_dev = do2_true - do2_true.mean(axis=1, keepdims=True)
    vo2_base = np.clip(rng.normal(240.0, 40.0, (n, 1)), 150.0, 350.0)
    slope = slope_mean + slope_sd * rng.standard_normal((n, 1))
    vo2_true = vo2_base + slope * do2_dev + rng.normal(0.0, 10.0, (n, t))
    cvo2_true = np.maximum(cao2_true - vo2_true / (10.0 * co_true), 1.5)
    co_meas = co_true * (1.0 + 0.07 * rng.standard_normal((n, t)))
    cao2_meas = cao2_true + rng.normal(0.0, 0.25, (n, t))
    cvo2_meas = cvo2_true + rng.normal(0.0, 0.25, (n, t))
    vo2_gas = vo2_true * (1.0 + 0.05 * rng.standard_normal((n, t)))
    return {
        "cardiac_output": co_meas.astype(np.float64),
        "arterial_o2_content": cao2_meas.astype(np.float64),
        "venous_o2_content": cvo2_meas.astype(np.float64),
        "vo2_expired_gas": vo2_gas.astype(np.float64),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _icu(rng, SLOPE_MEAN, SLOPE_SD)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _icu(rng, 0.0, 0.0)


def criterion(d):
    """Data keys: cardiac_output (40, 6) float, cardiac output of each patient at each measurement occasion, in L/min;
    arterial_o2_content (40, 6) float, oxygen content of arterial blood of each patient at each occasion, in mL O2 per dL;
    venous_o2_content (40, 6) float, oxygen content of mixed venous blood of each patient at each occasion, in mL O2 per dL;
    vo2_expired_gas (40, 6) float, oxygen consumption of each patient at each occasion measured from expired-gas analysis, in mL/min.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def _shuffle_vo2_within_patient(d, rng):
    v = d["vo2_expired_gas"]
    idx = np.argsort(rng.random(v.shape), axis=1)
    return {**d, "vo2_expired_gas": np.take_along_axis(v, idx, axis=1)}


STUDY = Study(
    name="D-008",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="true within-patient slope of VO2 on DO2 set to 0 in every patient (supply independence); CO, contents, errors unchanged, CvO2 follows Fick"),
    },
    controls=[Control("vo2_shuffled_within_patient", ["C"], transform=_shuffle_vo2_within_patient)],
)
