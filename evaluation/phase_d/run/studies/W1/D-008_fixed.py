"""D-008: Within patients, oxygen consumption rises with oxygen delivery: the mean over patients of the within-patient slope of oxygen consumption on oxygen delivery is at least 0.1 mL/min per mL/min."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_PAT = 40
N_OCC = 6
SLOPE_MEAN = 0.25    # true mean within-patient slope of VO2 on DO2 (mL/min per mL/min)
SLOPE_SD = 0.08      # between-patient SD of the true slope
CO_CV = 0.15         # within-patient variation of cardiac output (fluids, inotropes)
HB_SD = 0.5          # within-patient SD of haemoglobin, g/dL
SAT_SD = 0.012       # within-patient SD of arterial saturation
MET_SD = 15.0        # within-patient metabolic fluctuation of VO2, mL/min
CO_ERR = 0.06        # thermodilution measurement error (CV)
HB_ERR = 0.02        # haemoglobin measurement error (CV), one value used for both contents
SAO2_ERR = 0.008
SVO2_ERR = 0.015
VO2_ERR = 0.06       # expired-gas VO2 measurement error (CV)
DISSOLVED_A = 0.27   # 0.003 x PaO2 (about 90 mmHg), mL O2/dL
DISSOLVED_V = 0.12   # 0.003 x PvO2 (about 40 mmHg), mL O2/dL


def _ar1(rng, shape, rho):
    e = rng.standard_normal(shape)
    out = np.empty(shape)
    out[:, 0] = e[:, 0]
    s = np.sqrt(1.0 - rho * rho)
    for t in range(1, shape[1]):
        out[:, t] = rho * out[:, t - 1] + s * e[:, t]
    return out


def _delivery(co_mean, hb_mean, sat_mean, co_dev, hb_dev, sat_dev):
    co = co_mean[:, None] * np.exp(CO_CV * co_dev)
    hb = hb_mean[:, None] + HB_SD * hb_dev
    sao2 = np.clip(sat_mean[:, None] + SAT_SD * sat_dev, 0.85, 0.995)
    cao2 = 1.34 * hb * sao2 + DISSOLVED_A
    return co, hb, sao2, cao2, 10.0 * co * cao2


def _world(rng, effect):
    n, k = N_PAT, N_OCC
    bsa = np.clip(rng.normal(1.9, 0.2, n), 1.5, 2.4)
    ci = np.clip(rng.normal(3.3, 0.6, n), 2.3, 5.0)
    hb_mean = np.clip(rng.normal(10.5, 1.3, n), 8.0, 14.0)
    sat_mean = np.clip(rng.normal(0.955, 0.015, n), 0.90, 0.99)
    vo2i = np.clip(rng.normal(135.0, 18.0, n), 100.0, 175.0)
    slope = rng.normal(SLOPE_MEAN, SLOPE_SD, n)
    co_mean = ci * bsa
    co, hb, sao2, cao2, do2 = _delivery(co_mean, hb_mean, sat_mean,
                                        _ar1(rng, (n, k), 0.4), _ar1(rng, (n, k), 0.6), _ar1(rng, (n, k), 0.3))
    # an independent copy of the delivery fluctuations (same process): drives VO2 in minus
    _, _, _, _, do2_copy = _delivery(co_mean, hb_mean, sat_mean,
                                     _ar1(rng, (n, k), 0.4), _ar1(rng, (n, k), 0.6), _ar1(rng, (n, k), 0.3))
    met = _ar1(rng, (n, k), 0.5)
    do2_usual = (10.0 * co_mean * (1.34 * hb_mean * sat_mean + DISSOLVED_A))[:, None]
    drive = do2 if effect else do2_copy
    vo2 = (vo2i * bsa)[:, None] + slope[:, None] * (drive - do2_usual) + MET_SD * met
    # true venous content from the Fick principle, venous saturation kept physiological
    cvo2 = cao2 - vo2 / (10.0 * co)
    svo2 = np.clip((cvo2 - DISSOLVED_V) / (1.34 * hb), 0.30, sao2 - 0.05)
    # measurements
    co_m = co * np.exp(CO_ERR * rng.standard_normal((n, k)))
    hb_m = hb * np.exp(HB_ERR * rng.standard_normal((n, k)))
    sao2_m = np.clip(sao2 + SAO2_ERR * rng.standard_normal((n, k)), 0.80, 1.0)
    svo2_m = np.clip(svo2 + SVO2_ERR * rng.standard_normal((n, k)), 0.20, 0.99)
    cao2_m = 1.34 * hb_m * sao2_m + DISSOLVED_A
    cvo2_m = 1.34 * hb_m * svo2_m + DISSOLVED_V
    vo2_gas = vo2 * np.exp(VO2_ERR * rng.standard_normal((n, k)))
    return {
        "cardiac_output": np.asarray(co_m, dtype=np.float64),
        "arterial_o2_content": np.asarray(cao2_m, dtype=np.float64),
        "venous_o2_content": np.asarray(cvo2_m, dtype=np.float64),
        "vo2_expired_gas": np.asarray(vo2_gas, dtype=np.float64),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _world(rng, True)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _world(rng, False)


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


def _shuffle_consumption_within_patient(d, rng):
    n, k = d["vo2_expired_gas"].shape
    idx = np.argsort(rng.random((n, k)), axis=1)
    if np.all(idx == np.arange(k)):
        idx[0] = np.roll(idx[0], 1)
    return {
        **d,
        "vo2_expired_gas": np.take_along_axis(d["vo2_expired_gas"], idx, axis=1),
        "venous_o2_content": np.take_along_axis(d["venous_o2_content"], idx, axis=1),
    }


STUDY = Study(
    name="D-008",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="true VO2 driven by an independent copy of the DO2 fluctuations: within-patient VO2-DO2 slope 0"),
    },
    controls=[Control("consumption_shuffled_across_occasions_within_patient", ["C"],
                      transform=_shuffle_consumption_within_patient)],
)
