"""C12: Across adult skeletons, femur length and tibia length are positively associated after accounting for humerus length: the partial correlation between femur length and tibia length, given humerus length, is at least 0.3."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control


def _gen(rng, rho):
    n = 1000
    male = rng.random(n) < 0.5
    humerus = np.where(male, 335.0, 308.0) + rng.normal(0.0, 14.0, n)
    z1 = rng.normal(0.0, 1.0, n)
    z2 = rng.normal(0.0, 1.0, n)
    femur = 445.0 + 1.05 * (humerus - 322.0) + 14.0 * z1
    tibia = 368.0 + 0.95 * (humerus - 322.0) + 13.0 * (rho * z1 + np.sqrt(1.0 - rho * rho) * z2)
    return {"femur_length": femur, "tibia_length": tibia, "humerus_length": humerus}


def plus(rng):
    """The claim is true: given humerus length, femur and tibia length correlate 0.5."""
    return _gen(rng, 0.5)


def minus(rng):
    """The claim is false: given humerus length, femur and tibia are uncorrelated; both still scale with it."""
    return _gen(rng, 0.0)


def _permute_tibia(d, rng):
    # Exchange tibia lengths among skeletons with neighbouring humerus lengths (blocks of 10).
    x = d["tibia_length"]
    order = np.argsort(d["humerus_length"], kind="stable")
    blocks = np.roll(x[order].reshape(-1, 10), int(rng.integers(1, 10)), axis=1)
    out = np.empty_like(x)
    out[order] = blocks.reshape(-1)
    return {**d, "tibia_length": out}


def criterion(d):
    """Data keys: femur_length, float (1000 skeletons,), maximum length of the femur in mm; tibia_length,
    float (1000,), maximum length of the tibia in mm; humerus_length, float (1000,), maximum length of the
    humerus in mm.
    Holds when the claim is supported by the data. Written by someone else."""
    femur = np.asarray(d["femur_length"], dtype=float)
    tibia = np.asarray(d["tibia_length"], dtype=float)
    humerus = np.asarray(d["humerus_length"], dtype=float)

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

    if not (np.all(np.isfinite(femur)) and np.all(np.isfinite(tibia)) and np.all(np.isfinite(humerus))):
        return None
    # Pearson correlation between femur / humerus and tibia / humerus
    with np.errstate(divide="ignore", invalid="ignore"):
        a = femur / humerus
        b = tibia / humerus
    if not (np.all(np.isfinite(a)) and np.all(np.isfinite(b))):
        return None
    r = partial_r(a, b, [])
    if r is None:
        return None
    return bool(r >= 0.3)


STUDY = Study(
    name="C12",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="partial correlation of femur and tibia length given humerus length set to zero"),
    },
    controls=[Control("permute_tibia_within_humerus_blocks", ["C"], transform=_permute_tibia)],
)
