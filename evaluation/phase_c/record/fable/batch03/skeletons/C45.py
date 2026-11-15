"""C45: The training programme improves task accuracy more than the control activity: the mean change in accuracy (post minus pre) is larger in the trained group than in the control group, and a two-sample t test of the difference between the two groups' mean changes gives two-sided p < 0.05."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_SUBJ = 40
N_TRAINED = 20
N_TRIALS = 120          # trials behind each accuracy value
ABILITY_MEAN = 0.70
ABILITY_SD = 0.07
GAIN_CONTROL = 0.035    # practice effect of taking the task twice
GAIN_TRAINED = 0.105    # practice effect plus training effect
GAIN_SD = 0.03          # individual variation of the true gain


def _experiment(rng, gain_trained):
    trained = np.zeros(N_SUBJ, dtype=bool)
    trained[rng.choice(N_SUBJ, N_TRAINED, replace=False)] = True
    ability = np.clip(rng.normal(ABILITY_MEAN, ABILITY_SD, N_SUBJ), 0.40, 0.90)
    gain = np.where(trained, gain_trained, GAIN_CONTROL) + rng.normal(0.0, GAIN_SD, N_SUBJ)
    after = np.clip(ability + gain, 0.02, 0.98)
    pre = rng.binomial(N_TRIALS, ability) / N_TRIALS
    post = rng.binomial(N_TRIALS, after) / N_TRIALS
    return {"pre": pre.astype(np.float64), "post": post.astype(np.float64), "trained": trained}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _experiment(rng, GAIN_TRAINED)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _experiment(rng, GAIN_CONTROL)


def _permute_trained(d, rng):
    return {**d, "trained": rng.permutation(d["trained"])}


def criterion(d):
    """Data keys: pre, float (40,), task accuracy (proportion correct) of each subject before the programme; post,
    float (40,), task accuracy (proportion correct) of each subject after the programme; trained, bool (40,),
    whether the subject took part in the training programme (true) or in the control activity (false).
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


STUDY = Study(
    name="C45",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the training effect is set to 0: the trained group's expected gain equals the control group's (0.105 -> 0.035)"),
    },
    controls=[Control("permute_trained", ["C"], transform=_permute_trained)],
)
