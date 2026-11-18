"""D-008: Within patients, oxygen consumption rises with oxygen delivery: the mean over patients of the within-patient slope of oxygen consumption on oxygen delivery is at least 0.1 mL/min per mL/min."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_PATIENTS = 40
N_OCCASIONS = 6
PLUS_MEAN_SLOPE = 0.20      # true mean within-patient slope of VO2 on DO2 (mL/min per mL/min)
SLOPE_SD = 0.05             # between-patient SD of the true slope
CO_WITHIN_LOG_SD = 0.13     # occasion-to-occasion true variation of cardiac output (log scale)
CAO2_WITHIN_LOG_SD = 0.05   # occasion-to-occasion true variation of arterial O2 content (log scale)
METABOLIC_CV = 0.05         # occasion-to-occasion VO2 variation unrelated to delivery
CO_ERROR_LOG_SD = 0.07      # thermodilution measurement error (mean of triplicate)
CAO2_ERROR_LOG_SD = 0.02    # co-oximetry measurement error
CVO2_ERROR_SD = 0.3         # mL O2/dL, mixed venous content measurement error
GAS_ERROR_LOG_SD = 0.05     # indirect calorimetry measurement error


def _simulate(rng, mean_slope):
    n, m = N_PATIENTS, N_OCCASIONS
    co_base = 5.5 * np.exp(rng.normal(0.0, 0.25, n))
    cao2_base = np.clip(rng.normal(13.8, 1.8, n), 9.0, 19.0)
    extraction_base = np.clip(rng.normal(0.27, 0.04, n), 0.18, 0.38)
    do2_base = 10.0 * co_base * cao2_base
    vo2_base = extraction_base * do2_base
    slope = mean_slope + SLOPE_SD * rng.standard_normal(n)
    co = co_base[:, None] * np.exp(CO_WITHIN_LOG_SD * rng.standard_normal((n, m)))
    cao2 = cao2_base[:, None] * np.exp(CAO2_WITHIN_LOG_SD * rng.standard_normal((n, m)))
    do2 = 10.0 * co * cao2
    vo2 = (vo2_base[:, None] + slope[:, None] * (do2 - do2_base[:, None])
           + METABOLIC_CV * vo2_base[:, None] * rng.standard_normal((n, m)))
    vo2 = np.minimum(vo2, 0.85 * do2)
    cvo2 = cao2 - vo2 / (10.0 * co)
    lung_vo2 = np.clip(rng.normal(8.0, 3.0, n), 0.0, None)
    co_meas = co * np.exp(CO_ERROR_LOG_SD * rng.standard_normal((n, m)))
    cao2_meas = cao2 * np.exp(CAO2_ERROR_LOG_SD * rng.standard_normal((n, m)))
    cvo2_meas = np.maximum(cvo2 + CVO2_ERROR_SD * rng.standard_normal((n, m)), 0.5)
    vo2_gas = (vo2 + lung_vo2[:, None]) * np.exp(GAS_ERROR_LOG_SD * rng.standard_normal((n, m)))
    return {
        "cardiac_output": np.asarray(co_meas, dtype=np.float64),
        "arterial_o2_content": np.asarray(cao2_meas, dtype=np.float64),
        "venous_o2_content": np.asarray(cvo2_meas, dtype=np.float64),
        "vo2_expired_gas": np.asarray(vo2_gas, dtype=np.float64),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _simulate(rng, PLUS_MEAN_SLOPE)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _simulate(rng, 0.0)


# >>> PHASE D INSERTED CRITERION BODY (begin) >>>
def _flat(a):
    """True when all entries of the array are equal (zero variance)."""
    return bool(np.max(a) == np.min(a))


def criterion(d):
    """Claim: within patients, oxygen consumption rises with oxygen delivery; the mean over patients of the
    within-patient slope of oxygen consumption on oxygen delivery is at least 0.1 mL/min per mL/min.

    d['cardiac_output']      : (patients, occasions) float, cardiac output of each patient at each
                               measurement occasion, in L/min
    d['arterial_o2_content'] : (patients, occasions) float, oxygen content of arterial blood of each
                               patient at each occasion, in mL O2 per dL
    d['venous_o2_content']   : (patients, occasions) float, oxygen content of mixed venous blood of each
                               patient at each occasion, in mL O2 per dL
    d['vo2_expired_gas']     : (patients, occasions) float, oxygen consumption of each patient at each
                               occasion measured from expired-gas analysis, in mL/min

    Oxygen delivery is cardiac_output * arterial_o2_content * 10 (mL/min). Patients whose delivery has no
    variance across occasions are not counted.
    Returns True / False; None when a value is not finite, fewer than 2 occasions, or no patient can be
    counted.
    """
    co = np.asarray(d['cardiac_output'], dtype=float)
    ca = np.asarray(d['arterial_o2_content'], dtype=float)
    cv = np.asarray(d['venous_o2_content'], dtype=float)
    vo = np.asarray(d['vo2_expired_gas'], dtype=float)
    if not (np.all(np.isfinite(co)) and np.all(np.isfinite(ca)) and np.all(np.isfinite(cv))
            and np.all(np.isfinite(vo))):
        return None
    n, m = co.shape
    if n < 1 or m < 2:
        return None
    do2 = co * ca * 10.0
    vo2 = vo
    ok = np.max(do2, axis=1) > np.min(do2, axis=1)
    if not np.any(ok):
        return None
    xc = do2 - np.mean(do2, axis=1, keepdims=True)
    yc = vo2 - np.mean(vo2, axis=1, keepdims=True)
    slopes = np.sum(xc * yc, axis=1)[ok] / np.sum(xc * xc, axis=1)[ok]
    stat = float(np.mean(slopes))
    if not np.isfinite(stat):
        return None
    return bool(stat >= 0.1)
# <<< PHASE D INSERTED CRITERION BODY (end) <<<


def _permute_vo2_within_patient(d, rng):
    return {**d, "vo2_expired_gas": rng.permuted(d["vo2_expired_gas"], axis=1)}


STUDY = Study(
    name="D-008",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="mean within-patient slope of true O2 consumption on true O2 delivery set from 0.20 to 0 (supply independence); between-patient slope SD, between-patient VO2-DO2 association, metabolic noise and all measurement errors unchanged"),
    },
    controls=[Control("vo2_permuted_across_occasions_within_patient", ["C"],
                      transform=_permute_vo2_within_patient)],
    relational=[("cardiac_output", "vo2_expired_gas")],
)
