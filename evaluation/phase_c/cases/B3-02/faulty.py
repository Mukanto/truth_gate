"""C53: Among adults, 24-hour urinary albumin excretion increases with age after accounting for 24-hour urinary creatinine excretion: the partial correlation between albumin excretion and age, given creatinine excretion, is at least 0.15."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_PARTICIPANTS = 800
AGE_MEAN = 50.0
AGE_SD = 15.0
CREATININE_AT_MEAN_AGE = 1400.0   # mg per 24 h
CREATININE_PER_YEAR = -9.0        # creatinine excretion falls with age (muscle mass)
CREATININE_SD = 300.0             # body size, sex, diet, completeness of the collection
ALBUMIN_MEDIAN = 9.0              # mg per 24 h
ALBUMIN_CREATININE_EXPONENT = 0.7 # albumin excretion scales with creatinine excretion (body size, completeness)
ALBUMIN_AGE_EFFECT = 0.135        # change of log albumin per SD of age
ALBUMIN_LOG_SD = 0.40             # other between-person variation of log albumin


def _age(rng):
    return np.clip(rng.normal(AGE_MEAN, AGE_SD, size=N_PARTICIPANTS), 18.0, 90.0)


def _generate(rng, albumin_follows_age):
    age = _age(rng)
    other_age = _age(rng)
    creatinine = CREATININE_AT_MEAN_AGE + CREATININE_PER_YEAR * (age - AGE_MEAN)
    creatinine = np.clip(creatinine + rng.normal(0.0, CREATININE_SD, size=N_PARTICIPANTS), 350.0, None)
    log_noise = rng.normal(0.0, ALBUMIN_LOG_SD, size=N_PARTICIPANTS)
    source = age if albumin_follows_age else other_age
    log_albumin = (
        np.log(ALBUMIN_MEDIAN)
        + ALBUMIN_CREATININE_EXPONENT * np.log(creatinine / CREATININE_AT_MEAN_AGE)
        + ALBUMIN_AGE_EFFECT * (source - AGE_MEAN) / AGE_SD
        + log_noise
    )
    return {"albumin_excretion": np.exp(log_albumin), "creatinine_excretion": creatinine, "age": age}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _generate(rng, True)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _generate(rng, False)


def permute_age(d, rng):
    return {**d, "age": d["age"][rng.permutation(d["age"].shape[0])]}


def criterion(d):
    """Data keys: albumin_excretion, float array of shape (800,) = (participants,): urinary albumin excreted over 24
    hours, in mg per 24 h, for each participant; creatinine_excretion, float array of shape (800,): urinary creatinine
    excreted over 24 hours, in mg per 24 h, for each participant; age, float array of shape (800,): age of each
    participant, in years.
    Holds when the claim is supported by the data. Written by someone else."""
    alb = np.asarray(d["albumin_excretion"], dtype=float)
    cre = np.asarray(d["creatinine_excretion"], dtype=float)
    age = np.asarray(d["age"], dtype=float)

    def partial_r(x, y, covs):
        n = x.shape[0]
        Z = np.column_stack([np.ones(n)] + list(covs))
        if n < Z.shape[1] + 2:
            return None
        rx = x - Z @ np.linalg.lstsq(Z, x, rcond=None)[0]
        ry = y - Z @ np.linalg.lstsq(Z, y, rcond=None)[0]
        sx = float(rx @ rx)
        sy = float(ry @ ry)
        cx = float(np.sum((x - x.mean()) ** 2))
        cy = float(np.sum((y - y.mean()) ** 2))
        if not (cx > 0.0 and cy > 0.0) or sx <= 1e-12 * cx or sy <= 1e-12 * cy:
            return None
        r = float(rx @ ry) / np.sqrt(sx * sy)
        return r if np.isfinite(r) else None

    if not (np.all(np.isfinite(alb)) and np.all(np.isfinite(cre)) and np.all(np.isfinite(age))):
        return None
    # Pearson correlation of age with the albumin / creatinine quotient
    with np.errstate(divide="ignore", invalid="ignore"):
        quotient = alb / cre
    if not np.all(np.isfinite(quotient)):
        return None
    r = partial_r(age, quotient, [])
    if r is None:
        return None
    return bool(r >= 0.15)


STUDY = Study(
    name="C53",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="albumin excretion has no dependence on age beyond what creatinine excretion carries (the age term of albumin is replaced by an independent draw from the age distribution); the fall of creatinine with age, the albumin-creatinine relation and all distributions are unchanged"),
    },
    controls=[Control("permute_age_across_participants", ["C"], transform=permute_age)],
)
