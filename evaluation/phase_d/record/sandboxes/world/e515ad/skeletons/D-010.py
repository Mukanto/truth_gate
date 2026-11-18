"""D-010: The postal district and the three covariates together predict the outcome y for new patients: the Pearson correlation between predicted and observed y is at least 0.25."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N = 1200
K = 150
DISTRICT_SD = 0.224  # SD of district effects on the standardised outcome (ICC about 0.05)
NOISE_SD = 0.925  # individual residual SD on the standardised outcome


def _cohort(rng):
    """Patients in unequally populated districts; covariates shift by district; returns data and signal."""
    w = rng.gamma(3.0, 1.0, K)
    w = w / w.sum()
    district = rng.choice(K, size=N, p=w)
    category = np.zeros((N, K), dtype=bool)
    category[np.arange(N), district] = True
    age_shift = rng.normal(0.0, 4.0, K)
    bmi_shift = rng.normal(0.0, 0.05, K)
    effect = rng.normal(0.0, DISTRICT_SD, K)
    age = np.clip(52.0 + age_shift[district] + 14.0 * rng.standard_normal(N), 18.0, 92.0)
    bmi = np.exp(np.log(26.5) + bmi_shift[district] + 0.16 * rng.standard_normal(N))
    sbp = 92.0 + 0.45 * age + 0.6 * bmi + rng.normal(0.0, 13.0, N)
    covariates = np.column_stack([age, bmi, sbp])
    signal = (0.18 * (age - 52.0) / 14.6 + 0.15 * (bmi - 26.8) / 4.4 + 0.12 * (sbp - 131.5) / 14.8
              + effect[district])
    return category, covariates, signal


def _generate(rng, linked):
    """When not linked, y is driven by the signal of an independent cohort (same distribution)."""
    category, covariates, signal = _cohort(rng)
    _, _, other_signal = _cohort(rng)
    eps = rng.standard_normal(N)
    s = signal if linked else other_signal
    y = 50.0 + 10.0 * (s + NOISE_SD * eps)
    return {"category": category, "covariates": covariates.astype(np.float64), "y": y.astype(np.float64)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _generate(rng, True)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _generate(rng, False)


def criterion(d):
    """Data keys: category (1200, 150) bool, True where the patient's home postal district is the district of that column;
    covariates (1200, 3) float, three continuous covariates per patient (age, body-mass index, systolic pressure);
    y (1200,) float, continuous health outcome of each patient.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def _shuffle_y(d, rng):
    return {**d, "y": d["y"][rng.permutation(N)]}


STUDY = Study(
    name="D-010",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="y driven by the district and covariate signal of an independent cohort (no predictive information; marginals unchanged)"),
    },
    controls=[Control("y_shuffled_across_patients", ["C"], transform=_shuffle_y)],
)
