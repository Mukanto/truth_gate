"""C16: In adult rats, animals given the drug have a larger heart weight than untreated animals after accounting for body mass: in a linear regression of heart weight on treatment status and body mass, the coefficient of treatment status is positive and significant at the one-sided 5% level (t test)."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control


def _permute_changed(x, rng):
    y = rng.permutation(x)
    while np.array_equal(y, x):
        y = rng.permutation(x)
    return y


def _world(rng, drug_effect_mg):
    n = 48
    treated = np.zeros(n, dtype=bool)
    treated[rng.permutation(n)[:24]] = True
    # the drug slows weight gain a little (both worlds): treated animals are about 25 g lighter
    body_mass = rng.normal(410.0, 35.0, n) - 25.0 * treated
    # allometric line with a non-zero intercept, plus individual scatter
    heart_weight = 240.0 + 2.2 * body_mass + drug_effect_mg * treated + rng.normal(0.0, 65.0, n)
    return {
        "heart_weight": heart_weight.astype(np.float64),
        "body_mass": body_mass.astype(np.float64),
        "treated": treated,
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _world(rng, 65.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _world(rng, 0.0)


def criterion(d):
    """Data keys: heart_weight (48,) float, wet heart weight of each animal in mg; body_mass (48,) float,
    body mass of each animal in g; treated (48,) bool, True for animals given the drug.
    Holds when the claim is supported by the data. Written by someone else."""
    heart = np.asarray(d["heart_weight"], dtype=float)
    mass = np.asarray(d["body_mass"], dtype=float)
    treated = np.asarray(d["treated"], dtype=bool).astype(float)

    def t_sf(t, df):
        # one-sided tail P(T > t) of Student's t with df degrees of freedom (substitution x = sqrt(df) * tan(theta))
        top = np.pi / 2.0

        def tail(a):
            th = np.linspace(a, top, 4001)
            f = np.cos(th) ** (df - 1.0)
            return float(np.sum(f[:-1] + f[1:]) * (top - a) / 8000.0)

        p = tail(float(np.arctan(abs(t) / np.sqrt(df)))) / (2.0 * tail(0.0))
        return p if t >= 0 else 1.0 - p

    def ols_t(y, cols):
        n = y.shape[0]
        X = np.column_stack([np.ones(n)] + list(cols))
        df = n - X.shape[1]
        if df < 1:
            return None
        x = X[:, 1]
        rest = np.delete(X, 1, axis=1)
        r = x - rest @ np.linalg.lstsq(rest, x, rcond=None)[0]
        rr = float(r @ r)
        css = float(np.sum((x - x.mean()) ** 2))
        if not (css > 0.0) or rr <= 1e-10 * css:
            return None
        res = y - X @ np.linalg.lstsq(X, y, rcond=None)[0]
        rss = float(res @ res)
        tss = float(np.sum((y - y.mean()) ** 2))
        if not (tss > 0.0) or rss <= 1e-12 * tss:
            return None
        beta = float(r @ y) / rr
        t = beta / np.sqrt(rss / df / rr)
        if not (np.isfinite(beta) and np.isfinite(t)):
            return None
        return beta, t, df

    if not (np.all(np.isfinite(heart)) and np.all(np.isfinite(mass))):
        return None
    # one-sided t test of treated versus untreated on the quotient heart weight / body mass
    with np.errstate(divide="ignore", invalid="ignore"):
        quotient = heart / mass
    if not np.all(np.isfinite(quotient)):
        return None
    out = ols_t(quotient, [treated])
    if out is None:
        return None
    beta, t, df = out
    return bool(beta > 0.0 and t_sf(t, df) < 0.05)


STUDY = Study(
    name="C16",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="direct effect of the drug on heart weight at given body mass set to 0 mg (was +65 mg); the effect of the drug on body mass is kept"),
    },
    controls=[
        Control("permute_treated", ["C"], transform=lambda d, rng: {**d, "treated": _permute_changed(d["treated"], rng)}),
    ],
)
