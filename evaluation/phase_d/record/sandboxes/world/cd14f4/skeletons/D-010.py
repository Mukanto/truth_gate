"""D-010: The postal district and the three covariates together predict the outcome y for new patients: the Pearson correlation between predicted and observed y is at least 0.25."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control


N_SAMPLES = 1200
N_DISTRICTS = 150
TAU = 0.28                    # SD of district effects on the outcome (outcome-SD units)
B_AGE, B_BMI, B_SBP = 0.16, 0.11, 0.13   # outcome change per covariate SD (outcome-SD units)
SD_NOISE = 0.904              # individual outcome variation not explained (total outcome variance about 1)
Y_MEAN, Y_SCALE = 50.0, 10.0


def _shuffled(rng, x):
    """Permute the first axis; never returns the input unchanged."""
    y = x[rng.permutation(x.shape[0])]
    if np.array_equal(y, x):
        y = np.roll(x, 1, axis=0)
    return y


def _draw(rng, informative):
    """One cohort. Returns (data, truth); truth holds the predictable part of y for checks."""
    n, k = N_SAMPLES, N_DISTRICTS
    weight = np.exp(0.6 * rng.standard_normal(k))          # districts differ in population size
    district = rng.choice(k, size=n, p=weight / weight.sum())
    category = np.zeros((n, k), dtype=bool)
    category[np.arange(n), district] = True
    deprivation = rng.standard_normal(k)                   # area deprivation: raises BMI, pressure and y
    district_effect = TAU * (0.6 * deprivation + 0.8 * rng.standard_normal(k))
    age_shift = 2.0 * rng.standard_normal(k)
    z = rng.standard_normal((n, 3))
    age = 55.0 + age_shift[district] + 12.0 * z[:, 0]
    bmi = 27.0 + 1.0 * deprivation[district] + 4.5 * (0.15 * z[:, 0] + np.sqrt(1.0 - 0.0225) * z[:, 1])
    sbp = 122.0 + 0.45 * (age - 55.0) + 0.9 * (bmi - 27.0) + 2.5 * deprivation[district] + 14.0 * z[:, 2]
    covariates = np.column_stack([age, bmi, sbp])
    signal = (B_AGE * (age - 55.0) / 12.2 + B_BMI * (bmi - 27.0) / 4.6 + B_SBP * (sbp - 122.0) / 16.3
              + district_effect[district])
    shuffle = rng.permutation(n)
    used = signal if informative else signal[shuffle]
    y = Y_MEAN + Y_SCALE * (used + SD_NOISE * rng.standard_normal(n))
    data = {"category": category, "covariates": covariates, "y": y}
    return data, {"signal": signal, "used": used}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _draw(rng, True)[0]


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _draw(rng, False)[0]


def criterion(d):
    """Data keys (rows = 1200 patients): category (1200, 150) bool, one-hot home postal district (exactly one
    True per row; a district may have no patient); covariates (1200, 3) float64, columns age in years,
    body-mass index in kg/m2, systolic pressure in mmHg; y (1200,) float64, continuous health outcome.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def _y_permuted(d, rng):
    return {**d, "y": _shuffled(rng, d["y"])}


STUDY = Study(
    name="D-010",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="y carries no information from district or covariates: each patient's predictable "
                              "part of y (covariate + district effect) is taken from a randomly permuted patient "
                              "(marginal of y, noise, district sizes and covariate structure unchanged)"),
    },
    controls=[Control("y_permuted", ["C"], transform=_y_permuted)],
)
