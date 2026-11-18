"""D-056: Among 3 groups of 25 rats each, mean resting oxygen uptake differs between the groups once body mass is accounted for: the analysis-of-covariance F test of the group effect on oxygen uptake, with body mass as the covariate, has a p-value below 0.05."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_GROUPS = 3
N_ANIMALS = 25
N_DAYS = 5                                     # measurement days; animal j of every group is measured on day j // 5
MASS_MEAN = np.array([295.0, 315.0, 335.0])    # group mean body mass (g)
MASS_LOG_SD = 0.10                             # within-group CV of body mass about 10%
VO2_REF = 5.0                                  # resting VO2 (mL O2/min) of a 315 g rat
MASS_REF = 315.0
EXPONENT = 0.67                                # intraspecific mass exponent
GROUP_EFFECT = np.array([0.05, -0.05, 0.0])    # mass-adjusted group effects on log VO2 (about +5%, -5%, 0)
DAY_SD = 0.03
BIO_SD = 0.09
MEAS_SD = 0.04


def _generate(rng, effect):
    log_mass = np.log(MASS_MEAN)[:, None] + MASS_LOG_SD * rng.standard_normal((N_GROUPS, N_ANIMALS))
    day_effect = DAY_SD * rng.standard_normal(N_DAYS)
    day_of_animal = np.arange(N_ANIMALS) // (N_ANIMALS // N_DAYS)
    bio = BIO_SD * rng.standard_normal((N_GROUPS, N_ANIMALS))
    meas = MEAS_SD * rng.standard_normal((N_GROUPS, N_ANIMALS))
    log_vo2 = (np.log(VO2_REF) + EXPONENT * (log_mass - np.log(MASS_REF)) + effect[:, None]
               + day_effect[day_of_animal][None, :] + bio + meas)
    return {
        "oxygen_uptake": np.asarray(np.exp(log_vo2), dtype=np.float64),
        "body_mass": np.asarray(np.exp(log_mass), dtype=np.float64),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes.

    Mass-adjusted resting VO2 differs between groups by +5%, -5% and 0 (Cohen's f about 0.4 on the residual scale).
    VO2 follows mass^0.67; the groups also differ in body mass (295, 315, 335 g), and a day-to-day calibration
    drift is shared by the animals measured on the same day."""
    return _generate(rng, GROUP_EFFECT)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes.

    Mass-adjusted group effects are all 0; the group differences in body mass, the allometry and all noise are as
    in plus, so raw VO2 still differs between groups through body mass."""
    return _generate(rng, np.zeros(N_GROUPS))


# >>> PHASE D INSERTED CRITERION BODY (begin) >>>
def lgam(z):
    c = [0.99999999999980993, 676.5203681218851, -1259.1392167224028, 771.32342877765313,
         -176.61502916214059, 12.507343278686905, -0.13857109526572012, 9.9843695780195716e-6,
         1.5056327351493116e-7]
    z = z - 1.0
    s = c[0]
    for i in range(1, 9):
        s = s + c[i] / (z + i)
    t = z + 7.5
    return 0.5 * np.log(2.0 * np.pi) + (z + 0.5) * np.log(t) - t + np.log(s)


def betacf(a, b, x):
    tiny = 1e-300
    qab = a + b
    qap = a + 1.0
    qam = a - 1.0
    c = 1.0
    dd = 1.0 - qab * x / qap
    if abs(dd) < tiny:
        dd = tiny
    dd = 1.0 / dd
    h = dd
    for m in range(1, 1000):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        dd = 1.0 + aa * dd
        if abs(dd) < tiny:
            dd = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        dd = 1.0 / dd
        h = h * dd * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        dd = 1.0 + aa * dd
        if abs(dd) < tiny:
            dd = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        dd = 1.0 / dd
        de = dd * c
        h = h * de
        if abs(de - 1.0) < 3e-16:
            break
    return h


def betainc(a, b, x):
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    bt = np.exp(lgam(a + b) - lgam(a) - lgam(b) + a * np.log(x) + b * np.log(1.0 - x))
    if x < (a + 1.0) / (a + b + 2.0):
        return float(bt * betacf(a, b, x) / a)
    return float(1.0 - bt * betacf(b, a, 1.0 - x) / b)


def t_two_sided_p(t, df):
    return betainc(0.5 * df, 0.5, df / (df + t * t))


def f_upper_p(f, d1, d2):
    f = max(f, 0.0)
    return betainc(0.5 * d2, 0.5 * d1, d2 / (d2 + d1 * f))


def rss_of(X, y):
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    res = y - X @ beta
    return float(np.sum(res * res))


def nested_f_p(y, X0, X1):
    n = y.shape[0]
    d1 = X1.shape[1] - X0.shape[1]
    d2 = n - X1.shape[1]
    r0 = rss_of(X0, y)
    r1 = rss_of(X1, y)
    if r1 == 0.0:
        return None
    return f_upper_p(((r0 - r1) / d1) / (r1 / d2), d1, d2)


def criterion(d):
    """Claim: Among 3 groups of 25 rats each, mean resting oxygen uptake differs between the groups once body mass is accounted for: the analysis-of-covariance F test of the group effect on oxygen uptake, with body mass as the covariate, has a p-value below 0.05.

    d: dict of numpy arrays, with the keys
      oxygen_uptake  (groups, animals)  float: resting oxygen uptake of each rat in each group, in mL O2 per min
      body_mass  (groups, animals)  float: body mass of each rat in each group, in g

    Returns True when the claim is supported, False when it is not, None when the statistic is not
    defined (non-finite values, too small a sample, zero variance).
    """
    o2 = np.asarray(d['oxygen_uptake'], dtype=float)
    m = np.asarray(d['body_mass'], dtype=float)
    ng = o2.shape[0]
    na = o2.shape[1]
    n = ng * na
    if ng < 2 or na < 1 or n < 5:
        return None
    if not (np.all(np.isfinite(o2)) and np.all(np.isfinite(m))):
        return None
    dum = np.zeros((n, ng - 1))
    for i in range(1, ng):
        dum[i * na:(i + 1) * na, i - 1] = 1.0
    one = np.ones((n, 1))
    if np.ptp(m) == 0:
        return None
    y = o2.reshape(n)
    X0 = np.hstack([one, m.reshape(n, 1)])
    X1 = np.hstack([one, m.reshape(n, 1), dum])
    if not (np.all(np.isfinite(y)) and np.all(np.isfinite(X0))):
        return None
    if np.ptp(y) == 0:
        return None
    p = nested_f_p(y, X0, X1)
    if p is None:
        return None
    return bool(p < 0.05)
# <<< PHASE D INSERTED CRITERION BODY (end) <<<


def _permute_animals_across_groups(d, rng):
    vo2 = d["oxygen_uptake"].reshape(-1)
    mass = d["body_mass"].reshape(-1)
    order = rng.permutation(vo2.shape[0])
    if np.array_equal(order, np.arange(vo2.shape[0])):
        order = np.roll(order, 1)
    shape = d["oxygen_uptake"].shape
    return {**d, "oxygen_uptake": vo2[order].reshape(shape), "body_mass": mass[order].reshape(shape)}


STUDY = Study(
    name="D-056",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="mass-adjusted group effects on log VO2 set to 0 (+0.05, -0.05, 0 -> 0, 0, 0); group mass differences kept"),
    },
    controls=[Control("animals_permuted_across_groups_with_their_mass", ["C"], transform=_permute_animals_across_groups)],
)
