"""C03: Across subjects, mean resting heart rate and mean salivary cortisol (each subject's mean over the recording days) are positively correlated: the Pearson correlation between the two subject means is positive, and a test of that correlation gives two-sided p < 0.05."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control


def _gen(rng, r):
    s, days = 16, 10
    z1 = rng.normal(0.0, 1.0, s)
    z2 = rng.normal(0.0, 1.0, s)
    hr_trait = 66.0 + 8.0 * z1                                         # subject's habitual heart rate
    cort_trait = 15.0 + 3.5 * (r * z1 + np.sqrt(1.0 - r * r) * z2)     # subject's habitual cortisol
    e1 = rng.normal(0.0, 1.0, (s, days))
    e2 = rng.normal(0.0, 1.0, (s, days))
    heart_rate = hr_trait[:, None] + 4.0 * e1
    # day-to-day fluctuations are weakly shared within a subject (0.3) in both worlds
    cortisol = cort_trait[:, None] + 3.5 * (0.3 * e1 + np.sqrt(1.0 - 0.09) * e2)
    return {"heart_rate": heart_rate, "cortisol": np.maximum(cortisol, 1.0)}


def plus(rng):
    """The claim is true: the subjects' habitual levels correlate 0.75 (about 0.70 between observed means)."""
    return _gen(rng, 0.75)


def minus(rng):
    """The claim is false: the subjects' habitual levels are uncorrelated; day-level structure as in plus."""
    return _gen(rng, 0.0)


def _permute_subjects(d, rng):
    n = d["cortisol"].shape[0]
    return {**d, "cortisol": d["cortisol"][rng.permutation(n)]}


def criterion(d):
    """Data keys: heart_rate, float (16 subjects, 10 days), resting heart rate in beats per minute of each
    subject on each recording day; cortisol, float (16, 10), morning salivary cortisol concentration of each
    subject on each recording day.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


STUDY = Study(
    name="C03",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="between-subject correlation of habitual heart rate and habitual cortisol set to zero"),
    },
    controls=[Control("permute_cortisol_subjects", ["C"], transform=_permute_subjects)],
    relational=[("heart_rate", "cortisol")],
)
