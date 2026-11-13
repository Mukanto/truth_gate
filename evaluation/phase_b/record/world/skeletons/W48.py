"""W48: A drug changes the evoked response more in visual cortex than in auditory cortex: the drug-minus-placebo difference in response amplitude is larger in the visual region than in the auditory region across 16 participants, at the two-sided 0.05 level."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

N = 16


def _gen(rng, d_vis, d_aud):
    b0 = rng.standard_normal(N)
    b1 = 0.4 * b0 + np.sqrt(1.0 - 0.4 ** 2) * rng.standard_normal(N)       # region baselines correlate 0.4
    zv = rng.standard_normal(N)
    za = 0.3 * zv + np.sqrt(1.0 - 0.3 ** 2) * rng.standard_normal(N)       # individual drug responses correlate 0.3
    n = 0.25 * rng.standard_normal((4, N))
    vis_base = 3.0 + 1.0 * b0
    aud_base = 2.5 + 1.0 * b1
    visual_placebo = vis_base + n[0]
    visual_drug = vis_base + d_vis + 0.3 * zv + n[1]
    auditory_placebo = aud_base + n[2]
    auditory_drug = aud_base + d_aud + 0.3 * za + n[3]
    return {"visual_placebo": visual_placebo, "visual_drug": visual_drug, "auditory_placebo": auditory_placebo, "auditory_drug": auditory_drug}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 0.6, 0.15)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.375, 0.375)


def criterion(d):
    """Data keys: visual_placebo (16,) evoked amplitude in visual region under placebo, axis participants;
    visual_drug (16,) same participants, visual region under drug; auditory_placebo (16,) auditory region under placebo;
    auditory_drug (16,) auditory region under drug. Every participant is measured in both regions and both conditions.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def swap_regions(d, rng):
    m = rng.random(N) < 0.5
    return {**d,
            "visual_placebo": np.where(m, d["auditory_placebo"], d["visual_placebo"]),
            "visual_drug": np.where(m, d["auditory_drug"], d["visual_drug"]),
            "auditory_placebo": np.where(m, d["visual_placebo"], d["auditory_placebo"]),
            "auditory_drug": np.where(m, d["visual_drug"], d["auditory_drug"])}


STUDY = Study(
    name="W48",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="mean drug effect 0.6 (visual) and 0.15 (auditory) -> 0.375 in both regions (equal, so each region alone still shows a drug effect); baselines, individual response variability, noise and 16 participants unchanged"),
    },
    controls=[Control("swap_regions", ["C"], transform=swap_regions)],
)
