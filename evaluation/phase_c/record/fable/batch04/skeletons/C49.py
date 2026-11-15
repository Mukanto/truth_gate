"""C49: Among children referred for a developmental assessment, a logistic regression on the speech measures identifies the children who received a diagnosis with a balanced accuracy of at least 0.70 for new children, estimated by 5-fold cross-validation."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_CHILDREN = 400
N_MEASURES = 30
# Loading of every speech measure on a general factor (age, talkativeness, recording quality).
GENERAL_LOADING = 0.40
# Loading of each speech measure on the child's symptom liability (10 informative measures, mixed signs).
LIABILITY_LOADING = np.array([0.45, -0.45, 0.45, 0.45, -0.45, 0.45, -0.45, 0.45, 0.45, -0.45] + [0.0] * 20)
UNIQUE_SD = np.sqrt(1.0 - GENERAL_LOADING ** 2 - LIABILITY_LOADING ** 2)
MEASURE_SCALE = np.linspace(0.3, 4.0, N_MEASURES)
MEASURE_OFFSET = np.linspace(10.0, -3.0, N_MEASURES)
ASSESSMENT_SD = 0.6      # part of the clinical picture that is not in the liability shared with speech
DIAGNOSIS_CUT = 0.45     # about 35% of referred children receive the diagnosis


def _generate(rng, speech_carries_liability):
    liability = rng.normal(size=N_CHILDREN)
    unrelated = rng.normal(size=N_CHILDREN)
    clinical = liability + ASSESSMENT_SD * rng.normal(size=N_CHILDREN)
    general = rng.normal(size=(N_CHILDREN, 1))
    unique = rng.normal(size=(N_CHILDREN, N_MEASURES))
    rating_noise = rng.normal(0.0, 0.8, size=N_CHILDREN)
    diagnosis = clinical > DIAGNOSIS_CUT
    severity = np.clip(4.3 + 1.5 * clinical + rating_noise, 0.0, 10.0)
    source = liability if speech_carries_liability else unrelated
    z = GENERAL_LOADING * general + source[:, None] * LIABILITY_LOADING + UNIQUE_SD * unique
    return {
        "speech_measures": MEASURE_OFFSET + MEASURE_SCALE * z,
        "diagnosis": diagnosis,
        "severity_rating": severity,
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _generate(rng, True)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _generate(rng, False)


def permute_speech(d, rng):
    return {**d, "speech_measures": d["speech_measures"][rng.permutation(d["speech_measures"].shape[0])]}


def permute_diagnosis(d, rng):
    return {**d, "diagnosis": d["diagnosis"][rng.permutation(d["diagnosis"].shape[0])]}


def criterion(d):
    """Data keys: speech_measures, float array of shape (400, 30) = (children, measures): acoustic and conversational
    measures computed from a recorded speech sample of each child; diagnosis, bool array of shape (400,) = (children,):
    True if the child received the diagnosis at the end of the assessment; severity_rating, float array of shape
    (400,) = (children,): clinician's overall symptom severity rating of the child on a continuous 0 to 10 scale,
    higher means more severe.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


STUDY = Study(
    name="C49",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the speech measures no longer depend on the child's symptom liability: they carry no information about the diagnosis (same distribution of the speech measures; diagnosis, severity rating and their relation unchanged)"),
    },
    controls=[
        Control("permute_speech_across_children", ["C"], transform=permute_speech),
        Control("permute_diagnosis_across_children", ["C"], transform=permute_diagnosis),
    ],
)
