"""C19: Across 16 participants, activation in the brain region whose response relates to the personality trait is correlated with the trait: the mean, over the voxels of that region, of the voxel-wise correlations (across participants) between activation and trait score is at least 0.5."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control


def _permute_changed(x, rng):
    y = rng.permutation(x)
    while np.array_equal(y, x):
        y = rng.permutation(x)
    return y


def _world(rng, trait_drives_region):
    subjects, voxels = 16, 1000
    trait_z = rng.normal(0.0, 1.0, subjects)
    other_z = rng.normal(0.0, 1.0, subjects)        # a subject variable unrelated to the trait
    trait = 50.0 + 10.0 * trait_z
    region = np.zeros(voxels, dtype=bool)           # a functional region of 150 voxels, location not given
    region[rng.permutation(voxels)[:150]] = True
    driver = trait_z if trait_drives_region else other_z
    # stable subject-by-voxel differences (same in both sessions): test-retest structure
    stable = np.sqrt(0.3) * rng.normal(0.0, 1.0, (subjects, voxels))
    signal = 1.134 * driver[:, None] * region[None, :]   # population correlation 0.75 inside the region
    sessions = []
    for _ in range(2):
        global_shift = np.sqrt(0.1) * rng.normal(0.0, 1.0, (subjects, 1))   # whole-brain session effect
        noise = np.sqrt(0.6) * rng.normal(0.0, 1.0, (subjects, voxels))
        sessions.append(signal + stable + global_shift + noise)
    return {
        "act_session1": sessions[0].astype(np.float64),
        "act_session2": sessions[1].astype(np.float64),
        "trait": trait.astype(np.float64),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _world(rng, True)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _world(rng, False)


def criterion(d):
    """Data keys: act_session1 (16, 1000) float, activation of each voxel (axis 1) in each participant (axis 0) in
    the first scanning session; act_session2 (16, 1000) float, the same voxels and participants in a second
    session; trait (16,) float, questionnaire score on the personality trait for each participant.
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
    s1 = np.asarray(d["act_session1"], dtype=float)
    s2 = np.asarray(d["act_session2"], dtype=float)
    y = np.asarray(d["trait"], dtype=float)
    if not all(np.all(np.isfinite(x)) for x in (s1, s2, y)):
        return None
    n = y.size
    if n < 3:
        return None
    x = (s1 + s2) / 2.0
    sel = np.arange(n // 2)
    est = np.arange(n // 2, n)
    if sel.size < 3 or est.size < 3:
        return None

    def _corr(rows):
        # correlation of every voxel (columns of x) with the trait over the given participants; None for a zero variance
        yc = y[rows] - y[rows].mean()
        xc = x[rows] - x[rows].mean(axis=0)
        syy = (yc ** 2).sum()
        sxx = (xc ** 2).sum(axis=0)
        if not (syy > 0.0 and np.all(sxx > 0.0)):
            return None
        return (yc @ xc) / np.sqrt(syy * sxx)

    r_sel = _corr(sel)
    if r_sel is None:
        return None
    df = sel.size - 2.0
    chosen = _sf(r_sel * np.sqrt(df) / np.sqrt(1.0 - r_sel ** 2), df) < 0.005
    if not chosen.any():
        return None
    r_est = _corr(est)
    if r_est is None:
        return None
    return bool(r_est[chosen].mean() >= 0.5)


STUDY = Study(
    name="C19",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="no voxel relates to the trait: the common driver of the region is a subject variable independent of the trait (population correlation 0, was 0.75); region size, variances, test-retest structure and noise kept"),
    },
    controls=[
        Control("permute_trait_across_participants", ["C"], transform=lambda d, rng: {**d, "trait": _permute_changed(d["trait"], rng)}),
    ],
)
