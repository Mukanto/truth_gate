"""C48: A kernel-based classifier built from the 1000 gene-expression measurements separates the two tumour classes with an accuracy of at least 0.60 on new samples."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_SAMPLES = 40
N_GENES = 1000
N_CLASS_B = 20
N_DIFFERENTIAL = 50
DELTA = 0.8          # class difference of a differential gene, in units of that gene's SD
N_FACTORS = 3        # hidden batch / purity factors shared by all genes
FACTOR_LOADING_SD = 0.1


def _generate(rng, effect):
    class_b = np.zeros(N_SAMPLES, dtype=bool)
    class_b[rng.permutation(N_SAMPLES)[:N_CLASS_B]] = True
    baseline = rng.normal(7.0, 1.5, size=N_GENES)
    gene_sd = rng.uniform(0.5, 1.5, size=N_GENES)
    differential = rng.permutation(N_GENES)[:N_DIFFERENTIAL]
    sign = np.where(rng.random(N_DIFFERENTIAL) < 0.5, -1.0, 1.0)
    loadings = rng.normal(0.0, FACTOR_LOADING_SD, size=(N_FACTORS, N_GENES))
    scores = rng.normal(size=(N_SAMPLES, N_FACTORS))
    noise = rng.normal(size=(N_SAMPLES, N_GENES))
    shift = np.zeros(N_GENES)
    shift[differential] = effect * DELTA * sign
    z = noise + scores @ loadings + (class_b[:, None] - 0.5) * shift
    return {"expression": baseline + gene_sd * z, "class_b": class_b}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _generate(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _generate(rng, 0.0)


def permute_classes(d, rng):
    return {**d, "class_b": d["class_b"][rng.permutation(d["class_b"].shape[0])]}


def criterion(d):
    """Data keys: expression, float array of shape (40, 1000) = (samples, genes): expression level of each gene in
    each tumour sample; class_b, bool array of shape (40,) = (samples,): True when the sample belongs to the second
    tumour class.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


STUDY = Study(
    name="C48",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the expression difference between the two tumour classes is set to zero for every gene: expression carries no information about the class (gene baselines, gene variances and hidden factors unchanged)"),
    },
    controls=[Control("permute_class_across_samples", ["C"], transform=permute_classes)],
)
