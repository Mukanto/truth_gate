"""C09: Across trials of an estimation task, the estimates of the three observers are positively associated after accounting for the true value of the quantity: the mean, over the three pairs of observers, of the partial correlation between the two observers' estimates given the true value is at least 0.2."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control


def _gen(rng, rho):
    t, o = 200, 3
    true_value = rng.uniform(20.0, 100.0, t)
    gain = rng.uniform(0.75, 1.0, o)                             # each observer compresses the range a little
    offset = (1.0 - gain) * 60.0 + rng.normal(0.0, 3.0, o)       # each observer's constant bias
    shared = rng.normal(0.0, 1.0, (t, 1))                        # trial-specific error common to the observers
    own = rng.normal(0.0, 1.0, (t, o))
    err = 8.0 * (np.sqrt(rho) * shared + np.sqrt(1.0 - rho) * own)
    return {"true_value": true_value, "estimates": offset[None, :] + gain[None, :] * true_value[:, None] + err}


def plus(rng):
    """The claim is true: the observers' errors around the true value correlate 0.45 across trials."""
    return _gen(rng, 0.45)


def minus(rng):
    """The claim is false: the observers' errors are independent; each still tracks the true value as in plus."""
    return _gen(rng, 0.0)


def _decouple_observers(d, rng):
    # Within blocks of 10 trials with neighbouring true values, shift observers 2 and 3 by different
    # amounts: each estimate keeps its relation to the true value but loses its trial partner.
    est = d["estimates"]
    order = np.argsort(d["true_value"], kind="stable")
    blocks = est[order].reshape(-1, 10, est.shape[1]).copy()
    k = rng.permutation(9)[:2] + 1
    blocks[:, :, 1] = np.roll(blocks[:, :, 1], int(k[0]), axis=1)
    blocks[:, :, 2] = np.roll(blocks[:, :, 2], int(k[1]), axis=1)
    out = np.empty_like(est)
    out[order] = blocks.reshape(est.shape)
    return {**d, "estimates": out}


def criterion(d):
    """Data keys: true_value, float (200 trials,), actual value of the quantity presented on each trial, in
    arbitrary units; estimates, float (200 trials, 3 observers), estimate of the quantity made by each
    observer on each trial, in the same units as true_value.
    Holds when the claim is supported by the data. Written by someone else."""
    true = np.asarray(d["true_value"], dtype=float)
    est = np.asarray(d["estimates"], dtype=float)

    def partial_r(x, y, covs):
        n = x.shape[0]
        Z = np.column_stack([np.ones(n)] + list(covs))
        if n < Z.shape[1] + 2:
            return None
        rx = x - Z @ np.linalg.lstsq(Z, x, rcond=None)[0]
        ry = y - Z @ np.linalg.lstsq(Z, y, rcond=None)[0]
        sx = float(rx @ rx)
        sy = float(ry @ ry)
        cx = float(np.sum((x - x.mean()) ** 2))
        cy = float(np.sum((y - y.mean()) ** 2))
        if not (cx > 0.0 and cy > 0.0) or sx <= 1e-12 * cx or sy <= 1e-12 * cy:
            return None
        r = float(rx @ ry) / np.sqrt(sx * sy)
        return r if np.isfinite(r) else None

    if not (np.all(np.isfinite(true)) and np.all(np.isfinite(est))):
        return None
    k = est.shape[1]
    if k < 2:
        return None
    # partial correlation of each pair of observers' estimates given the true value
    vals = []
    for i in range(k):
        for j in range(i + 1, k):
            r = partial_r(est[:, i], est[:, j], [true])
            if r is None:
                return None
            vals.append(r)
    return bool(np.mean(vals) >= 0.2)


STUDY = Study(
    name="C09",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="correlation between the observers' errors around the true value set to zero"),
    },
    controls=[Control("decouple_observers_within_true_value_blocks", ["C"], transform=_decouple_observers)],
)
