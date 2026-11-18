"""D-008: Within patients, oxygen consumption rises with oxygen delivery: the mean over patients of the within-patient slope of oxygen consumption on oxygen delivery is at least 0.1 mL/min per mL/min."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_PAT = 40
N_OCC = 6
CO_MEDIAN = 5.5
CO_BETWEEN_SD = 0.25
CO_WITHIN_SD = 0.20
CO_ERR_SD = 0.15
CA_MEDIAN = 17.5
CA_BETWEEN_SD = 0.12
CA_WITHIN_SD = 0.075
CA_ERR_SD = 0.03
VO2_MEDIAN = 250.0
VO2_BETWEEN_SD = 0.20
VO2_NOISE_SD = 15.0
VO2_ERR_SD = 0.07
CV_ASSAY_SD = 0.3
BETA_REL_SD = 0.33


def _gen(rng, beta_mean):
    co_bar = CO_MEDIAN * np.exp(CO_BETWEEN_SD * rng.standard_normal((N_PAT, 1)))
    ca_bar = CA_MEDIAN * np.exp(CA_BETWEEN_SD * rng.standard_normal((N_PAT, 1)))
    co_true = co_bar * np.exp(CO_WITHIN_SD * rng.standard_normal((N_PAT, N_OCC)))
    ca_true = ca_bar * np.exp(CA_WITHIN_SD * rng.standard_normal((N_PAT, N_OCC)))
    co_obs = co_true * np.exp(CO_ERR_SD * rng.standard_normal((N_PAT, N_OCC)))
    ca_obs = ca_true * np.exp(CA_ERR_SD * rng.standard_normal((N_PAT, N_OCC)))
    do2 = 10.0 * co_true * ca_true
    do2_dev = do2 - do2.mean(axis=1, keepdims=True)
    vo2_bar = VO2_MEDIAN * np.exp(VO2_BETWEEN_SD * rng.standard_normal((N_PAT, 1)))
    beta = beta_mean * (1.0 + BETA_REL_SD * rng.standard_normal((N_PAT, 1)))
    vo2_true = vo2_bar + beta * do2_dev + VO2_NOISE_SD * rng.standard_normal((N_PAT, N_OCC))
    vo2_true = np.maximum(vo2_true, 60.0)
    cv_true = ca_true - vo2_true / (10.0 * co_true)
    cv_obs = np.maximum(cv_true + CV_ASSAY_SD * rng.standard_normal((N_PAT, N_OCC)), 2.0)
    vo2_obs = vo2_true * np.exp(VO2_ERR_SD * rng.standard_normal((N_PAT, N_OCC)))
    return {
        "cardiac_output": np.asarray(co_obs, dtype=float),
        "arterial_o2_content": np.asarray(ca_obs, dtype=float),
        "venous_o2_content": np.asarray(cv_obs, dtype=float),
        "vo2_expired_gas": np.asarray(vo2_obs, dtype=float),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 0.18)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


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


def permute_vo2_across_patients(d, rng):
    out = {k: np.asarray(v, dtype=float) for k, v in d.items()}
    perm = rng.permutation(out["vo2_expired_gas"].shape[0])
    out["vo2_expired_gas"] = out["vo2_expired_gas"][perm]
    return out


STUDY = Study(
    name="D-008",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="within-patient slope of true oxygen consumption on true oxygen delivery set from a mean of 0.18 (relative SD 0.33) to 0"),
    },
    controls=[Control("permute_vo2_across_patients", ["C"], transform=permute_vo2_across_patients)],
)
