"""C47: A classifier built from the 20 image features of a tissue patch identifies malignant tissue in patches from new patients with an area under the ROC curve of at least 0.75."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_PATIENTS = 80
N_PATCHES = 10
N_FEATURES = 20
N_MALIGNANT = 32
# Shift of each feature in malignant tissue, in units of the patch-level noise SD (6 informative features).
SIGNATURE = np.array([0.9, -0.9, 0.9, 0.9, -0.9, 0.9] + [0.0] * 14)
# Loading of each feature on staining intensity (a slide-level and a patch-level nuisance factor).
STAIN_LOADING = np.linspace(0.6, -0.4, N_FEATURES)
PATIENT_SD = 0.8
FEATURE_SCALE = np.linspace(0.5, 3.0, N_FEATURES)
FEATURE_OFFSET = np.linspace(-2.0, 5.0, N_FEATURES)


def _generate(rng, effect):
    malignant = np.zeros(N_PATIENTS, dtype=bool)
    malignant[rng.permutation(N_PATIENTS)[:N_MALIGNANT]] = True
    patient_shift = rng.normal(0.0, PATIENT_SD, size=(N_PATIENTS, 1, N_FEATURES))
    slide_stain = rng.normal(0.0, 0.7, size=(N_PATIENTS, 1, 1))
    patch_stain = rng.normal(0.0, 0.5, size=(N_PATIENTS, N_PATCHES, 1))
    patch_noise = rng.normal(size=(N_PATIENTS, N_PATCHES, N_FEATURES))
    strength = rng.uniform(0.6, 1.4, size=(N_PATIENTS, N_PATCHES, 1))
    tumour = effect * malignant[:, None, None] * strength * SIGNATURE
    z = patient_shift + (slide_stain + patch_stain) * STAIN_LOADING + patch_noise + tumour
    return {"patch_features": FEATURE_OFFSET + FEATURE_SCALE * z, "malignant": malignant}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _generate(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _generate(rng, 0.0)


def permute_labels(d, rng):
    return {**d, "malignant": d["malignant"][rng.permutation(d["malignant"].shape[0])]}


def criterion(d):
    """Data keys: patch_features, float array of shape (80, 10, 20) = (patients, patches, features): 20 image features
    of each tissue patch of each patient; malignant, bool array of shape (80,) = (patients,): True when the patient's
    tissue is malignant (all 10 patches of a patient share the patient's label).
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


STUDY = Study(
    name="C47",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the feature shift of malignant tissue is set to zero: patch features carry no information about malignancy (patient-level and staining variability unchanged)"),
    },
    controls=[Control("permute_malignancy_across_patients", ["C"], transform=permute_labels)],
)
