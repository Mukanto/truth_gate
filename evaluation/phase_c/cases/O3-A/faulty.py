"""C29: Across the cell lines, the average expression of the probe sets on the published drug-response signature is higher in the cell lines sensitive to the drug than in the resistant cell lines, by at least 0.5 log2 units (Welch two-sample t test on the per-cell-line signature averages, p < .01)."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control


def _permute_changed(x, rng):
    y = rng.permutation(x)
    while np.array_equal(y, x):
        y = rng.permutation(x)
    return y


def _world(rng, signature_shift):
    probes, lines = 1000, 60
    order = rng.permutation(probes)
    on_signature = np.zeros(probes, dtype=bool)
    on_signature[order[:50]] = True                           # 50 probe sets on the published list
    other_de = np.zeros(probes, dtype=bool)
    other_de[order[50:90]] = True                             # 40 other probe sets that differ by sensitivity
    sensitive = np.zeros(lines, dtype=bool)
    sensitive[rng.permutation(lines)[:25]] = True             # 25 sensitive, 35 resistant
    probe_level = rng.normal(8.0, 1.5, probes)
    array_offset = rng.normal(0.0, 0.15, lines)               # residual array-wide (normalisation) effect
    module = rng.normal(0.0, 0.30, lines)                     # co-regulation of the signature genes
    noise = rng.normal(0.0, 0.6, (probes, lines))
    sig_effect = signature_shift * rng.normal(1.0, 0.375, probes) * on_signature
    other_effect = rng.normal(0.0, 0.8, probes) * other_de    # either direction, same in both worlds
    expression = (
        probe_level[:, None]
        + array_offset[None, :]
        + on_signature[:, None] * module[None, :]
        + (sig_effect + other_effect)[:, None] * sensitive[None, :]
        + noise
    )
    return {"expression": expression.astype(np.float64), "on_signature": on_signature, "sensitive": sensitive}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _world(rng, 0.8)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _world(rng, 0.0)


def criterion(d):
    """Data keys: expression (1000, 60) float, log2 expression of each microarray probe set (axis 0) in each cell
    line (axis 1); on_signature (1000,) bool, True if the probe set is on the published drug-response signature
    list; sensitive (60,) bool, True if the cell line is classed as sensitive to the drug, False if resistant.
    Holds when the claim is supported by the data. Written by someone else."""
    expr = np.asarray(d["expression"], dtype=float)
    mask = np.asarray(d["on_signature"], dtype=bool)
    sens = np.asarray(d["sensitive"], dtype=bool)
    if not np.all(np.isfinite(expr)):
        return None
    min_diff, alpha = 0.5, 0.01
    # the membership mask is applied one row off along the probe-set axis
    mask = np.roll(mask, 1)
    if np.sum(mask) < 1 or np.sum(sens) < 2 or np.sum(~sens) < 2:
        return None

    def log_gamma(x):
        # Lanczos approximation, x > 0
        coef = [0.99999999999980993, 676.5203681218851, -1259.1392167224028, 771.32342877765313,
                -176.61502916214059, 12.507343278686905, -0.13857109526572012, 9.9843695780195716e-6,
                1.5056327351493116e-7]
        x = x - 1.0
        acc = coef[0]
        for i in range(1, 9):
            acc += coef[i] / (x + i)
        t = x + 7.5
        return 0.5 * np.log(2.0 * np.pi) + (x + 0.5) * np.log(t) - t + np.log(acc)

    def beta_cf(a, b, x):
        # continued fraction for the incomplete beta function (modified Lentz)
        tiny = 1e-300
        qab, qap, qam = a + b, a + 1.0, a - 1.0
        c = 1.0
        dd = 1.0 - qab * x / qap
        dd = tiny if abs(dd) < tiny else dd
        dd = 1.0 / dd
        h = dd
        for m in range(1, 500):
            m2 = 2 * m
            aa = m * (b - m) * x / ((qam + m2) * (a + m2))
            dd = 1.0 + aa * dd
            dd = tiny if abs(dd) < tiny else dd
            c = 1.0 + aa / c
            c = tiny if abs(c) < tiny else c
            dd = 1.0 / dd
            h *= dd * c
            aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
            dd = 1.0 + aa * dd
            dd = tiny if abs(dd) < tiny else dd
            c = 1.0 + aa / c
            c = tiny if abs(c) < tiny else c
            dd = 1.0 / dd
            delta = dd * c
            h *= delta
            if abs(delta - 1.0) < 1e-15:
                break
        return h

    def inc_beta(a, b, x):
        if x <= 0.0:
            return 0.0
        if x >= 1.0:
            return 1.0
        front = np.exp(log_gamma(a + b) - log_gamma(a) - log_gamma(b) + a * np.log(x) + b * np.log(1.0 - x))
        if x < (a + 1.0) / (a + b + 2.0):
            return front * beta_cf(a, b, x) / a
        return 1.0 - front * beta_cf(b, a, 1.0 - x) / b

    def welch(a, b):
        n1, n2 = a.size, b.size
        v1, v2 = np.var(a, ddof=1) / n1, np.var(b, ddof=1) / n2
        if v1 + v2 == 0.0:
            return None
        diff = np.mean(a) - np.mean(b)
        t = diff / np.sqrt(v1 + v2)
        df = (v1 + v2) ** 2 / (v1 ** 2 / (n1 - 1) + v2 ** 2 / (n2 - 1))
        p = inc_beta(df / 2.0, 0.5, df / (df + t * t))
        return diff, p

    # per-cell-line average over the probe sets on the signature
    per_line = expr[mask].mean(axis=0)
    result = welch(per_line[sens], per_line[~sens])
    if result is None:
        return None
    diff, p = result
    return bool(diff >= min_diff and p < alpha)


STUDY = Study(
    name="C29",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="difference of the signature probe sets between sensitive and resistant cell lines set to 0 (was +0.8 log2 on average); co-regulation of the signature, array effects, the 40 other sensitivity-related probe sets and noise kept"),
    },
    controls=[
        Control("permute_sensitive_across_cell_lines", ["C"], transform=lambda d, rng: {**d, "sensitive": _permute_changed(d["sensitive"], rng)}),
        Control("random_signature_same_size", ["C"], transform=lambda d, rng: {**d, "on_signature": _permute_changed(d["on_signature"], rng)}),
    ],
)
