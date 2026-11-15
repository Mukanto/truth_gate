"""C25: Over a ten-year record, monthly hospital admissions rose after accounting for catchment population: in a linear regression of monthly admissions on time and catchment population, the coefficient of time is positive and significant at the one-sided 5% level (t test)."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control


def _permute_changed(x, rng):
    y = rng.permutation(x)
    while np.array_equal(y, x):
        y = rng.permutation(x)
    return y


def _ar1(rng, n, phi, sd):
    # stationary first-order autoregressive series with marginal standard deviation sd
    shocks = rng.normal(0.0, sd * np.sqrt(1.0 - phi * phi), n)
    out = np.empty(n)
    out[0] = rng.normal(0.0, sd)
    for i in range(1, n):
        out[i] = phi * out[i - 1] + shocks[i]
    return out


def _world(rng, trend_per_year):
    months = 120
    time_years = np.arange(months) / 12.0
    # catchment population (thousands): slow growth plus persistent deviations (boundary and estimate revisions)
    population = 250.0 + 1.5 * time_years + _ar1(rng, months, 0.9, 4.0)
    season = 80.0 * np.cos(2.0 * np.pi * np.arange(months) / 12.0)      # winter peak
    waves = _ar1(rng, months, 0.6, 55.0)                                # persistent excess (epidemic waves)
    month_noise = rng.normal(0.0, 20.0, months)
    admissions = 8.0 * population + trend_per_year * time_years + season + waves + month_noise
    admissions = np.round(admissions)
    return {
        "admissions": admissions.astype(np.float64),
        "population": population.astype(np.float64),
        "time_years": time_years.astype(np.float64),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _world(rng, 20.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _world(rng, 0.0)


def criterion(d):
    """Data keys: admissions (120,) float, number of hospital admissions in each month; population (120,) float,
    catchment population in each month, in thousands; time_years (120,) float, time of each month in years since
    the start of the record. The three arrays are aligned by month, in time order.
    Holds when the claim is supported by the data. Written by someone else."""
    adm = np.asarray(d["admissions"], dtype=float)
    pop = np.asarray(d["population"], dtype=float)
    time = np.asarray(d["time_years"], dtype=float)

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

    if not (np.all(np.isfinite(adm)) and np.all(np.isfinite(pop)) and np.all(np.isfinite(time))):
        return None
    # one-sided t test of the time coefficient in the regression of admissions / population on time
    with np.errstate(divide="ignore", invalid="ignore"):
        rate = adm / pop
    if not np.all(np.isfinite(rate)):
        return None
    out = ols_t(rate, [time])
    if out is None:
        return None
    beta, t, df = out
    return bool(beta > 0.0 and t_sf(t, df) < 0.05)


STUDY = Study(
    name="C25",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="time trend of admissions at given population set to 0 (was +20 admissions per month per year); population growth, the admission rate per head, seasonality and autocorrelated month-to-month variation kept"),
    },
    controls=[
        Control("permute_time_across_months", ["C"], transform=lambda d, rng: {**d, "time_years": _permute_changed(d["time_years"], rng)}),
        Control("reverse_time", ["C"], transform=lambda d, rng: {**d, "time_years": d["time_years"][::-1].copy()}),
    ],
)
