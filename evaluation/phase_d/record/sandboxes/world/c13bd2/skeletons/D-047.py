"""D-047: 600 patients with menopausal hot flushes received a treatment. Symptom severity (scale 0 to 100, higher is worse) was scored at a screening visit, again at entry on the day treatment began, and again 12 weeks later. Claim: among patients whose screening score was at least 60, at least half have a week-12 score that is 10 or more points below their entry score (proportion of at least 0.5)."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N = 600
N_SITE = 20          # sites of 30 consecutive patients
TRAIT_MEAN = 52.0    # mean stable severity
TRAIT_SD = 11.0      # between-patient SD of stable severity
SITE_SD = 3.0        # site rater offset, constant across visits
FLUCT_SD = 8.0       # symptom fluctuation (Ornstein-Uhlenbeck, time constant 4 weeks)
TAU_WEEKS = 4.0
RATE_SD = 5.0        # rating error at each visit
GAIN_MEAN = 14.0     # mean true improvement from entry to week 12 (the claimed effect)
GAIN_SD = 8.0        # between-patient SD of the true change


def _world(rng, effect):
    site = np.repeat(np.arange(N_SITE), N // N_SITE)
    site_off = rng.normal(0.0, SITE_SD, N_SITE)[site]
    trait = rng.normal(TRAIT_MEAN, TRAIT_SD, N)
    r1 = np.exp(-2.0 / TAU_WEEKS)      # screening (week -2) to entry (week 0)
    r2 = np.exp(-12.0 / TAU_WEEKS)     # entry to week 12
    f_s = rng.standard_normal(N)
    f_e = r1 * f_s + np.sqrt(1.0 - r1 * r1) * rng.standard_normal(N)
    f_12 = r2 * f_e + np.sqrt(1.0 - r2 * r2) * rng.standard_normal(N)
    m = rng.standard_normal((3, N))
    change = GAIN_SD * rng.standard_normal(N) + (GAIN_MEAN if effect else 0.0)
    base = trait + site_off
    screening = base + FLUCT_SD * f_s + RATE_SD * m[0]
    entry = base + FLUCT_SD * f_e + RATE_SD * m[1]
    week12 = base + FLUCT_SD * f_12 + RATE_SD * m[2] - change
    return {
        "screening": np.asarray(np.clip(screening, 0.0, 100.0), dtype=np.float64),
        "entry": np.asarray(np.clip(entry, 0.0, 100.0), dtype=np.float64),
        "week12": np.asarray(np.clip(week12, 0.0, 100.0), dtype=np.float64),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _world(rng, True)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _world(rng, False)


def criterion(d):
    """Data keys (one value per patient, 600 patients, all float64, scale 0-100, higher is worse):
    screening (600,), symptom severity at the screening visit; entry (600,), severity at entry, the day treatment
    began; week12 (600,), severity 12 weeks after treatment began.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def _swap_entry_week12(d, rng):
    swap = rng.random(d["entry"].shape[0]) < 0.5
    if not np.any(swap & (d["entry"] != d["week12"])):
        swap[int(np.argmax(d["entry"] != d["week12"]))] = True
    return {
        **d,
        "entry": np.where(swap, d["week12"], d["entry"]),
        "week12": np.where(swap, d["entry"], d["week12"]),
    }


STUDY = Study(
    name="D-047",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="mean true change from entry to week 12 set to 0 (between-patient spread of change kept)"),
    },
    controls=[Control("entry_and_week12_swapped_at_random_within_patient", ["C"], transform=_swap_entry_week12)],
)
