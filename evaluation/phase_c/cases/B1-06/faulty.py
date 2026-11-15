"""C06: In the voxels of this participant's visual cortex whose responses follow stimulus contrast, the response rises with contrast: the regression slope of the voxel-averaged response (percent signal change) on stimulus contrast across the 240 trials is at least 0.2 percent signal change per unit of contrast, with a one-sided p value below 0.05."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control


def _gen(rng, slope):
    t, v = 240, 500
    levels = np.repeat(np.array([0.0625, 0.125, 0.25, 0.5, 1.0]), t // 5)
    contrast = rng.permutation(levels)                           # 48 trials per contrast level
    responsive = rng.permutation(v) < 80                         # voxels that follow contrast
    gain = np.where(responsive, slope * rng.uniform(0.6, 1.4, v), 0.0)
    baseline = rng.normal(0.3, 0.2, v)                           # response to any stimulus
    shared = rng.normal(0.0, 0.25, (t, 1))                       # trial-wise fluctuation common to all voxels
    response = baseline[None, :] + contrast[:, None] * gain[None, :] + shared + rng.normal(0.0, 1.0, (t, v))
    return {"response": response, "contrast": contrast}


def plus(rng):
    """The claim is true: 80 of the 500 voxels rise by about 1.0 percent signal change per unit contrast."""
    return _gen(rng, 1.0)


def minus(rng):
    """The claim is false: no voxel's response depends on contrast; noise structure as in plus."""
    return _gen(rng, 0.0)


def _permute_contrast(d, rng):
    n = d["contrast"].shape[0]
    return {**d, "contrast": d["contrast"][rng.permutation(n)]}


def criterion(d):
    """Data keys: response, float (240 trials, 500 voxels), response of each visual-cortex voxel on each trial
    in percent signal change; contrast, float (240,), stimulus contrast shown on each trial, in units where
    full contrast equals 1.
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
    resp = np.asarray(d["response"], dtype=float)
    con = np.asarray(d["contrast"], dtype=float)
    if not (np.all(np.isfinite(resp)) and np.all(np.isfinite(con))):
        return None
    n = con.size
    sel = np.arange(n)
    est = np.arange(n)
    if sel.size < 3 or est.size < 3:
        return None
    cs = con[sel] - con[sel].mean()
    xs = resp[sel] - resp[sel].mean(axis=0)
    css = (cs ** 2).sum()
    xss = (xs ** 2).sum(axis=0)
    if not (css > 0.0 and np.all(xss > 0.0)):
        return None
    corr = (cs @ xs) / np.sqrt(css * xss)
    df = sel.size - 2.0
    region = _sf(corr * np.sqrt(df) / np.sqrt(1.0 - corr ** 2), df) < 0.01
    if not region.any():
        return None
    avg = resp[est][:, region].mean(axis=1)
    ce = con[est] - con[est].mean()
    ye = avg - avg.mean()
    cee = (ce ** 2).sum()
    if not cee > 0.0:
        return None
    slope = (ce @ ye) / cee
    rss = ((ye - slope * ce) ** 2).sum()
    se = np.sqrt(rss / (est.size - 2.0) / cee)
    if not se > 0.0:
        return None
    p = float(_sf(slope / se, est.size - 2.0))
    return bool(slope >= 0.2 and p < 0.05)


STUDY = Study(
    name="C06",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="slope of response on contrast set to zero in every voxel"),
    },
    controls=[Control("permute_contrast_across_trials", ["C"], transform=_permute_contrast)],
    relational=[("response", "contrast")],
)
