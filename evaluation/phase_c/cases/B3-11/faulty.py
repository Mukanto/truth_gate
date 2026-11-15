"""C24: Across tumour samples, the expression of gene A and the expression of gene B are positively related after accounting for the expression of gene C: the gain in R-squared when gene A expression is added to a linear regression of gene B expression on gene C expression is at least 0.05."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control


def _permute_changed(x, rng):
    y = rng.permutation(x)
    while np.array_equal(y, x):
        y = rng.permutation(x)
    return y


def _world(rng, a_linked_to_b):
    n = 96
    gene_c = 100.0 * np.exp(rng.normal(0.0, 0.4, n))     # right-skewed signal of gene C
    a_own = rng.gamma(4.0, 7.5, n)                       # variation of gene A not explained by gene C
    unrelated = rng.gamma(4.0, 7.5, n)                   # a variable with the same distribution, unrelated to A
    b_own = rng.gamma(4.0, 10.0, n)
    gene_a = 20.0 + 0.5 * gene_c + a_own                 # A follows C in both worlds
    source = a_own if a_linked_to_b else unrelated
    gene_b = 30.0 + 0.6 * gene_c + 0.75 * (source - 30.0) + b_own   # B follows C in both worlds
    return {
        "gene_a_expression": gene_a.astype(np.float64),
        "gene_b_expression": gene_b.astype(np.float64),
        "gene_c_expression": gene_c.astype(np.float64),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _world(rng, True)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _world(rng, False)


def criterion(d):
    """Data keys: gene_a_expression (96,) float, quantitative PCR expression signal of gene A in each tumour
    sample, arbitrary linear units; gene_b_expression (96,) float, the same for gene B; gene_c_expression (96,)
    float, the same for gene C. The three arrays are aligned by sample.
    Holds when the claim is supported by the data. Written by someone else."""
    ga = np.asarray(d["gene_a_expression"], dtype=float)
    gb = np.asarray(d["gene_b_expression"], dtype=float)
    gc = np.asarray(d["gene_c_expression"], dtype=float)

    def flat(a):
        return not (float(np.sum((a - a.mean()) ** 2)) > 0.0)


    def r2(y, cols):
        n = y.shape[0]
        X = np.column_stack([np.ones(n)] + list(cols))
        tss = float(np.sum((y - y.mean()) ** 2))
        if n < X.shape[1] + 1 or not (tss > 0.0):
            return None
        res = y - X @ np.linalg.lstsq(X, y, rcond=None)[0]
        return 1.0 - float(res @ res) / tss

    if not (np.all(np.isfinite(ga)) and np.all(np.isfinite(gb)) and np.all(np.isfinite(gc))):
        return None
    # R-squared of gene B / gene C regressed on gene A / gene C
    with np.errstate(divide="ignore", invalid="ignore"):
        y = gb / gc
        x = ga / gc
    if not (np.all(np.isfinite(y)) and np.all(np.isfinite(x))) or flat(y) or flat(x):
        return None
    value = r2(y, [x])
    if value is None or not np.isfinite(value):
        return None
    return bool(value >= 0.05)


STUDY = Study(
    name="C24",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="relation of gene B to gene A at fixed gene C set to none (partial slope 0, was 0.75; expected R-squared gain 0, was about 0.10): the same term in gene B now comes from a variable independent of gene A; the dependence of A and of B on C and all marginal distributions kept"),
    },
    controls=[
        Control("permute_gene_a_across_samples", ["C"], transform=lambda d, rng: {**d, "gene_a_expression": _permute_changed(d["gene_a_expression"], rng)}),
    ],
)
