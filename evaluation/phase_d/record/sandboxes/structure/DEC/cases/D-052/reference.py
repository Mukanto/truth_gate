"""D-052: Forty participants, 20 young and 20 old, completed a training programme, and a performance score was recorded before and after it. Claim: the mean improvement (after minus before) is larger in young than in old participants, judged by a one-sided test of the difference between the two groups' mean improvements at the 0.05 level."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_PER_GROUP = 20
N_PARTICIPANTS = 40
PRE_MEAN_YOUNG = 55.0
PRE_MEAN_OLD = 48.0
PRE_SD = 10.0
SD_IMP_YOUNG = 6.0
SD_IMP_OLD = 12.0
MEAN_IMP_YOUNG_PLUS = 8.0
MEAN_IMP_OLD_PLUS = 1.0
MEAN_IMP_NULL = 4.5


def _world(rng, mean_young, mean_old):
    young = np.zeros(N_PARTICIPANTS, dtype=bool)
    young[rng.permutation(N_PARTICIPANTS)[:N_PER_GROUP]] = True
    pre = np.where(young, PRE_MEAN_YOUNG, PRE_MEAN_OLD) + PRE_SD * rng.standard_normal(N_PARTICIPANTS)
    imp = (np.where(young, mean_young, mean_old)
           + np.where(young, SD_IMP_YOUNG, SD_IMP_OLD) * rng.standard_normal(N_PARTICIPANTS))
    post = pre + imp
    return {"pre": pre.astype(float), "post": post.astype(float), "young": young}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _world(rng, MEAN_IMP_YOUNG_PLUS, MEAN_IMP_OLD_PLUS)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _world(rng, MEAN_IMP_NULL, MEAN_IMP_NULL)


def criterion(d):
    """Data keys: pre (40,) float, performance score before the programme;
    post (40,) float, performance score after the programme;
    young (40,) bool, True for young participants (20), False for old participants (20).
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def _break(d, rng):
    lab = np.asarray(d["young"], dtype=bool)
    new = lab[rng.permutation(lab.size)]
    if np.array_equal(new, lab):
        new = lab.copy()
        i = int(np.argmax(lab))
        j = int(np.argmax(~lab))
        new[i] = lab[j]
        new[j] = lab[i]
    return {"pre": np.array(d["pre"], dtype=float), "post": np.array(d["post"], dtype=float), "young": new}


STUDY = Study(
    name="D-052",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the age-group difference in mean improvement is set to 0 (8.0 vs 1.0 in plus; both groups at the pooled mean 4.5); improvement sd (6 young, 12 old), baseline scores and group sizes unchanged"),
    },
    controls=[Control("D-052", ["C"], transform=lambda d, rng: _break(d, rng))],
)
