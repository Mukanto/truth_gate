"""C26: A shrunken-centroid classifier built from the 1000 gene-expression measurements separates the two tumour classes with an accuracy of at least 0.60 on new samples."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control


def _permute_changed(x, rng):
    y = rng.permutation(x)
    while np.array_equal(y, x):
        y = rng.permutation(x)
    return y


def _world(rng, class_shift_sd):
    samples, genes = 40, 1000
    class_b = np.zeros(samples, dtype=bool)
    class_b[rng.permutation(samples)[:20]] = True              # 20 samples per class
    gene_level = rng.normal(8.0, 1.5, genes)                   # baseline log2 expression of each gene
    gene_sd = rng.uniform(0.3, 1.0, genes)
    # three sample-level factors (batch, purity, proliferation) shared by all genes, unrelated to class
    factors = rng.normal(0.0, 1.0, (samples, 3))
    loadings = rng.normal(0.0, 0.25, (genes, 3))
    z = factors @ loadings.T + 0.9 * rng.normal(0.0, 1.0, (samples, genes))
    # 50 genes differ between the classes, half up and half down
    marker = rng.permutation(genes)[:50]
    sign = np.where(np.arange(50) % 2 == 0, 1.0, -1.0)
    shift = np.zeros(genes)
    shift[marker] = class_shift_sd * sign
    z = z + class_b[:, None] * shift[None, :]
    expression = gene_level[None, :] + gene_sd[None, :] * z
    return {"expression": expression.astype(np.float64), "class_b": class_b}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _world(rng, 0.8)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _world(rng, 0.0)


def criterion(d):
    """Data keys: expression (40, 1000) float, expression level (log2) of each gene (axis 1) in each tumour
    sample (axis 0); class_b (40,) bool, True when the sample belongs to the second tumour class.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


STUDY = Study(
    name="C26",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="no gene differs between the two classes: class shift of the 50 marker genes set to 0 (was 0.8 within-class SD); class sizes, gene levels, gene variances and sample-level factors kept"),
    },
    controls=[
        Control("permute_class_across_samples", ["C"], transform=lambda d, rng: {**d, "class_b": _permute_changed(d["class_b"], rng)}),
    ],
)
