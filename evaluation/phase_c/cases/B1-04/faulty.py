"""C05: In each participant's own region of visual cortex that responds more to faces than to houses, the response to faces exceeds the response to bodies: across the 12 participants the mean difference (faces minus bodies) of the response in that region is at least 0.3 percent signal change, and a one-sided paired t test across participants is significant at the 0.05 level."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control


def _gen(rng, gap):
    s, r, v = 12, 8, 300
    n_face = rng.integers(30, 51, s)                                  # size of each participant's face region
    rank = np.argsort(np.argsort(rng.random((s, v)), axis=1), axis=1)
    face_roi = rank < n_face[:, None]                                 # location differs between participants
    house_roi = rank >= v - 40                                        # house-preferring voxels
    base = rng.normal(0.5, 0.25, (s, v))                              # response common to all categories
    face_sel = np.maximum(rng.normal(1.1, 0.2, (s, 1)) + rng.normal(0.0, 0.2, (s, v)), 0.3)
    gap_s = gap * (1.0 + 0.25 * rng.normal(0.0, 1.0, (s, 1)))         # faces minus bodies inside the region
    mu_faces = base + face_roi * face_sel
    mu_bodies = base + face_roi * (face_sel - gap_s)
    mu_houses = base + 0.8 * house_roi
    drift = rng.normal(0.0, 0.2, (s, r, 1))                           # run-wise shift shared by all conditions
    noise = rng.normal(0.0, 0.7, (3, s, r, v))
    return {
        "resp_faces": mu_faces[:, None, :] + drift + noise[0],
        "resp_bodies": mu_bodies[:, None, :] + drift + noise[1],
        "resp_houses": mu_houses[:, None, :] + drift + noise[2],
    }


def plus(rng):
    """The claim is true: inside the face region faces exceed bodies by 0.7 (faces exceed houses by 1.1)."""
    return _gen(rng, 0.7)


def minus(rng):
    """The claim is false: inside the face region bodies respond like faces; faces still exceed houses."""
    return _gen(rng, 0.0)


def _swap_faces_bodies(d, rng):
    s, r, _ = d["resp_faces"].shape
    swap = rng.random((s, r, 1)) < 0.5
    swap[0, 0, 0] = True
    return {
        **d,
        "resp_faces": np.where(swap, d["resp_bodies"], d["resp_faces"]),
        "resp_bodies": np.where(swap, d["resp_faces"], d["resp_bodies"]),
    }


def criterion(d):
    """Data keys: resp_faces, float (12 subjects, 8 runs, 300 voxels), response to face images (percent signal
    change) of each visual-cortex voxel in each scanning run of each participant; resp_bodies, float
    (12, 8, 300), response to body images, same layout; resp_houses, float (12, 8, 300), response to house
    images, same layout.
    Holds when the claim is supported by the data. Written by someone else."""
    def _sf(t, df):
        # upper-tail probability of Student's t: integral of cos(x)**(df-1) over [arctan(t/sqrt(df)), pi/2], trapezoid rule
        t = np.asarray(t, dtype=float)
        df = np.broadcast_to(np.asarray(df, dtype=float), t.shape)
        u = np.linspace(0.0, 1.0, 1001)

        def tail(lo):
            x = lo[..., None] + (np.pi / 2.0 - lo[..., None]) * u
            f = np.cos(x) ** (df[..., None] - 1.0)
            return (f.sum(-1) - 0.5 * (f[..., 0] + f[..., -1])) * (np.pi / 2.0 - lo) / (len(u) - 1)

        ang = np.arctan(np.abs(t) / np.sqrt(df))
        upper = tail(ang) / (2.0 * tail(np.zeros_like(ang)))
        return np.where(t >= 0.0, upper, 1.0 - upper)
    def _ttest1(x):
        # one-sample (or paired-difference) t test of mean(x) > 0: (mean, one-sided p); None when the variance is zero
        sd = x.std(ddof=1)
        if not sd > 0.0:
            return None
        return x.mean(), float(_sf(x.mean() / (sd / np.sqrt(x.size)), x.size - 1.0))
    f = np.asarray(d["resp_faces"], dtype=float)
    b = np.asarray(d["resp_bodies"], dtype=float)
    h = np.asarray(d["resp_houses"], dtype=float)
    if not all(np.all(np.isfinite(x)) for x in (f, b, h)):
        return None
    runs = f.shape[1]
    sel_runs = np.arange(runs)
    est_runs = np.arange(runs)
    if sel_runs.size < 2 or est_runs.size < 1:
        return None
    contrast = f[:, sel_runs, :] - h[:, sel_runs, :]
    sd = contrast.std(axis=1, ddof=1)
    if not np.all(sd > 0.0):
        return None
    t = contrast.mean(axis=1) / (sd / np.sqrt(sel_runs.size))
    region = t > 2.0
    size = region.sum(axis=1)
    keep = size > 0
    if keep.sum() < 2:
        return None
    diff = (f[:, est_runs, :] - b[:, est_runs, :]).mean(axis=1)
    per = ((diff * region).sum(axis=1))[keep] / size[keep]
    r = _ttest1(per)
    if r is None:
        return None
    return bool(r[0] >= 0.3 and r[1] < 0.05)


STUDY = Study(
    name="C05",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="faces-minus-bodies difference inside the face-selective region set to zero (bodies raised to the face response)"),
    },
    controls=[Control("swap_face_body_labels_per_run", ["C"], transform=_swap_faces_bodies)],
)
