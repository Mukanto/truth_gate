"""C15: Scores on the task and on the symptom scale are more strongly related in group A than in group B: the Pearson correlation between task score and symptom score is higher in group A than in group B, and a Fisher z test of the difference between the two correlations gives two-sided p < 0.05."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control


def _gen(rng, r_a, r_b):
    n = 40
    group_a = np.zeros(n, dtype=bool)
    group_a[rng.permutation(n)[:20]] = True                      # 20 participants per group
    r = np.where(group_a, r_a, r_b)
    z1 = rng.normal(0.0, 1.0, n)
    z2 = rng.normal(0.0, 1.0, n)
    task = np.where(group_a, 56.0, 50.0) + 9.0 * z1
    symptom = np.where(group_a, 24.0, 14.0) + 7.0 * (r * z1 + np.sqrt(1.0 - r * r) * z2)
    return {"task_score": task, "symptom_score": symptom, "group_a": group_a}


def plus(rng):
    """The claim is true: the correlation is 0.8 in group A and 0.0 in group B."""
    return _gen(rng, 0.8, 0.0)


def minus(rng):
    """The claim is false: the correlation is the same in both groups (0.4, the plus average)."""
    return _gen(rng, 0.4, 0.4)


def _permute_groups(d, rng):
    return {**d, "group_a": d["group_a"][rng.permutation(d["group_a"].shape[0])]}


def criterion(d):
    """Data keys: task_score, float (40 participants,), score of each participant on the experimental task;
    symptom_score, float (40,), score of each participant on the symptom questionnaire; group_a, bool (40,),
    whether the participant belongs to group A (True) or group B (False).
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


STUDY = Study(
    name="C15",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="difference between the two groups' task-symptom correlations set to zero (both 0.4, their plus average)"),
    },
    controls=[Control("permute_group_labels", ["C"], transform=_permute_groups)],
)
