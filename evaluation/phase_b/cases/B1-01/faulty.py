"""W05: In a 60-voxel region of ventral visual cortex, the voxels that respond more to faces than to houses show a mean face-minus-house response of at least 0.30 percent signal change. The claim holds when this mean (taken per subject and then averaged over the 20 subjects) is at least 0.30 and significantly above zero (one-sided one-sample t-test across subjects, p < 0.05)."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

S, R, V = 20, 2, 60


def _gen(rng, eff):
    u = rng.random((S, V))
    face_sel = u < 0.40                                   # truly face-selective voxels (per subject)
    house_sel = (u >= 0.40) & (u < 0.55)                  # truly house-selective voxels, present in both worlds
    amp = 0.45 + 0.15 * rng.standard_normal((S, V))
    mu = eff * face_sel * amp - house_sel * (0.35 + 0.1 * rng.standard_normal((S, V)))
    base = 1.0 + 0.5 * rng.standard_normal((S, 1, V))     # voxel responsiveness shared by faces and houses
    off = 0.2 * rng.standard_normal((S, R, 1))            # run-level offset
    face = base + off + mu[:, None, :] / 2.0 + 0.45 * rng.standard_normal((S, R, V))
    house = base + off - mu[:, None, :] / 2.0 + 0.45 * rng.standard_normal((S, R, V))
    return {"face": face, "house": house}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: face (20, 2, 60) percent signal change to face pictures, axes (subjects, runs, voxels);
    house (20, 2, 60) percent signal change to house pictures, same layout.
    Holds when the claim is supported by the data. Written by someone else."""
    def _lg(z):
        c = (0.99999999999980993, 676.5203681218851, -1259.1392167224028, 771.32342877765313,
             -176.61502916214059, 12.507343278686905, -0.13857109526572012,
             9.9843695780195716e-6, 1.5056327351493116e-7)
        z = z - 1.0
        x = c[0]
        for i in range(1, 9):
            x += c[i] / (z + i)
        t = z + 7.5
        return 0.5 * np.log(2.0 * np.pi) + (z + 0.5) * np.log(t) - t + np.log(x)

    def _cf(a, b, x):
        tiny = 1e-300
        qab, qap, qam = a + b, a + 1.0, a - 1.0
        c = 1.0
        dd = 1.0 - qab * x / qap
        dd = 1.0 / (dd if abs(dd) > tiny else tiny)
        h = dd
        for m in range(1, 400):
            m2 = 2 * m
            aa = m * (b - m) * x / ((qam + m2) * (a + m2))
            dd = 1.0 + aa * dd
            dd = 1.0 / (dd if abs(dd) > tiny else tiny)
            c = 1.0 + aa / c
            c = c if abs(c) > tiny else tiny
            h *= dd * c
            aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
            dd = 1.0 + aa * dd
            dd = 1.0 / (dd if abs(dd) > tiny else tiny)
            c = 1.0 + aa / c
            c = c if abs(c) > tiny else tiny
            de = dd * c
            h *= de
            if abs(de - 1.0) < 1e-13:
                break
        return h

    def _ib(x, a, b):
        # regularized incomplete beta function I_x(a, b)
        if x <= 0.0:
            return 0.0
        if x >= 1.0:
            return 1.0
        bt = np.exp(_lg(a + b) - _lg(a) - _lg(b) + a * np.log(x) + b * np.log(1.0 - x))
        if x < (a + 1.0) / (a + b + 2.0):
            return float(bt * _cf(a, b, x) / a)
        return float(1.0 - bt * _cf(b, a, 1.0 - x) / b)

    def _tsf(t, df):
        # one-sided upper-tail probability of Student's t
        t = float(t)
        if t == 0.0:
            return 0.5
        p = 0.5 * _ib(df / (df + t * t), 0.5 * df, 0.5)
        return p if t > 0 else 1.0 - p

    face = np.asarray(d["face"], dtype=float)
    house = np.asarray(d["house"], dtype=float)
    if not (np.all(np.isfinite(face)) and np.all(np.isfinite(house))):
        return None
    c = face - house                                           # (subjects, runs, voxels)
    zc = 1.6449                                                # one-sided p < 0.05, uncorrected
    folds = [(c.mean(axis=1), c.mean(axis=1))]
    vals = []
    for sel_map, ev_map in folds:
        scale = np.sqrt(np.mean(sel_map ** 2))
        if not scale > 0:
            return None
        sel = sel_map > zc * scale                             # voxels that respond more to faces than to houses
        cnt = sel.sum(axis=1)
        m = np.where(cnt > 0, np.where(sel, ev_map, 0.0).sum(axis=1) / np.maximum(cnt, 1), np.nan)
        vals.append(m)
    stack = np.vstack(vals)
    okm = np.isfinite(stack)
    k = okm.sum(axis=0)
    per = np.where(okm, stack, 0.0).sum(axis=0) / np.maximum(k, 1)
    x = per[k > 0]                                             # per-subject mean over the voxels
    if len(x) < 5:
        return None
    sd = x.std(ddof=1)
    if not sd > 0:
        return None
    t = x.mean() / (sd / np.sqrt(len(x)))
    return bool(x.mean() >= 0.30 and _tsf(t, len(x) - 1) < 0.05)


def scramble_voxels_in_run_2(d, rng):
    face = d["face"].copy()
    house = d["house"].copy()
    for s in range(S):
        p = rng.permutation(V)
        face[s, 1] = face[s, 1][p]
        house[s, 1] = house[s, 1][p]
    return {**d, "face": face, "house": house}


STUDY = Study(
    name="W05",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="true face-over-house selectivity of the face-selective voxels (about 0.45 percent signal change in 40% of voxels) -> 0; house-selective voxels, voxel baselines and all noise unchanged"),
    },
    controls=[Control("scramble_voxels_in_run_2", ["C"], transform=scramble_voxels_in_run_2)],
)
