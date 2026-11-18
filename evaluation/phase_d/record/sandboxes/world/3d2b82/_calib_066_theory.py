# Design calculation for D-066 (no data, no classifier run on generated data):
# expected 1-NN sensitivity/specificity under an idealised Gaussian shift model, computed from the
# exact distance distributions (noncentral chi-square) and the first-arrival integral.
import math
import numpy as np

GRID = np.linspace(1e-6, 160.0, 6000)


def _pois_w(lam, jmax):
    j = np.arange(jmax)
    lw = -lam / 2 + j * math.log(max(lam / 2, 1e-300)) - np.array([math.lgamma(x + 1) for x in j])
    return np.exp(lw)


def ncx2_cdf_pdf(k, lam, x):
    a = k / 2.0
    hx = x / 2.0
    # P(a, hx) by series
    total = np.ones_like(hx)
    cur = np.ones_like(hx)
    for n in range(1, 600):
        cur = cur * hx / (a + n)
        total = total + cur
    P = np.exp(a * np.log(hx) - hx - math.lgamma(a + 1)) * total
    jmax = int(lam / 2 + 12 * math.sqrt(lam / 2 + 1) + 30)
    w = _pois_w(lam, jmax)
    cdf = np.zeros_like(x)
    pdf = np.zeros_like(x)
    Pj = P.copy()
    for j in range(jmax):
        aj = a + j
        nu = k + 2 * j
        dens = np.exp((nu / 2 - 1) * np.log(x) - x / 2 - (nu / 2) * math.log(2) - math.lgamma(nu / 2))
        cdf += w[j] * Pj
        pdf += w[j] * dens
        Pj = Pj - np.exp(aj * np.log(hx) - hx - math.lgamma(aj + 1))
        Pj = np.maximum(Pj, 0.0)
    return np.clip(cdf, 0, 1), pdf


def p_nn_same(k, lam_same, lam_other, n_same, n_other, scale=1.0):
    x = GRID
    F1, f1 = ncx2_cdf_pdf(k, lam_same, x)
    F0, _ = ncx2_cdf_pdf(k, lam_other, x)
    integrand = n_same * f1 * np.exp((n_same - 1) * np.log1p(-np.minimum(F1, 1 - 1e-16))
                                     + n_other * np.log1p(-np.minimum(F0, 1 - 1e-16)))
    return float(np.trapezoid(integrand, x))


def ba(k, delta2, n1, n0, reps, seed=1, c=1.0):
    rng = np.random.default_rng(seed)
    d = math.sqrt(delta2 / c)  # shift in effective units
    sens = []
    spec = []
    for _ in range(reps):
        z1 = rng.standard_normal()
        R = rng.chisquare(k - 1)
        A = (z1 ** 2 + R)  # dist^2 param to own class centre
        B = ((d + z1) ** 2 + R)  # to the other class centre
        sens.append(p_nn_same(k, A, B, n1, n0))
        z1 = rng.standard_normal()
        R = rng.chisquare(k - 1)
        A = (z1 ** 2 + R)
        B = ((d - z1) ** 2 + R)
        spec.append(p_nn_same(k, A, B, n0, n1))
    s, p = float(np.mean(sens)), float(np.mean(spec))
    return s, p, (s + p) / 2


if __name__ == "__main__":
    for (k, c) in [(15, 1.0), (11, 1.36)]:
        for delta2 in [9, 12, 15]:
            for (n1, n0) in [(56, 744), (35, 465)]:
                s, p, b = ba(k, delta2, n1, n0, reps=100, c=c)
                print(f"k={k} c={c} D2={delta2} n1={n1} n0={n0}: sens={s:.3f} spec={p:.3f} BA={b:.3f}")
