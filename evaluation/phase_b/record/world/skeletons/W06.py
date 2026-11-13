"""W06: From 20 image features of tissue patches, the model identifies the gene mutation status of new patients with AUC of at least 0.75."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

P, K, F = 40, 6, 20


def _gen(rng, eff):
    mut = rng.permutation(np.arange(P) < 16)                   # 16 mutated patients
    u = rng.standard_normal((P, F))                            # patient-level random effect, shared by all patches
    e = rng.standard_normal((P, K, F))                         # patch-level noise
    shift = np.zeros(F)
    shift[:6] = 0.9                                            # six informative features
    patches = u[:, None, :] + e + eff * mut[:, None, None] * shift[None, None, :]
    return {"patches": patches, "mutated": mut.astype(bool)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: patches (40, 6, 20) image features of each tissue patch of each patient, axes (patients, patches, features);
    mutated (40,) bool, True if the patient's tumour carries the mutation.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def permute_mutation_across_patients(d, rng):
    return {**d, "mutated": d["mutated"][rng.permutation(P)]}


STUDY = Study(
    name="W06",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the mutation shifts six features by 0.9 sd -> shift 0; patient random effects, patch noise, group sizes and nesting unchanged"),
    },
    controls=[Control("permute_mutation_across_patients", ["C"], transform=permute_mutation_across_patients)],
)
