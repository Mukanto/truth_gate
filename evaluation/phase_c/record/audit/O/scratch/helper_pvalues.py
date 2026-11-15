"""Auditor helper (class O, Phase C). Re-typed copies of the two p-value helpers that appear inside the criterion
bodies (O2-A/O2-B: Student t by Abramowitz-Stegun 26.7.3/26.7.4; O3-A: Welch via regularised incomplete beta),
evaluated at tabulated critical values whose two-sided p is known. No study file is imported; no criterion is called."""
import math


def p_two_sided_student(t, df):
    theta = math.atan(abs(t) / math.sqrt(df))
    c, s = math.cos(theta), math.sin(theta)
    if df % 2 == 0:
        term, tot = 1.0, 1.0
        for k in range(2, df - 1, 2):
            term *= c * c * (k - 1) / k
            tot += term
        inside = s * tot
    elif df == 1:
        inside = 2.0 * theta / math.pi
    else:
        term, tot = c, c
        for k in range(3, df - 1, 2):
            term *= c * c * (k - 1) / k
            tot += term
        inside = (2.0 / math.pi) * (theta + s * tot)
    return 1.0 - inside


def log_gamma(x):
    coef = [0.99999999999980993, 676.5203681218851, -1259.1392167224028, 771.32342877765313,
            -176.61502916214059, 12.507343278686905, -0.13857109526572012, 9.9843695780195716e-6,
            1.5056327351493116e-7]
    x = x - 1.0
    acc = coef[0]
    for i in range(1, 9):
        acc += coef[i] / (x + i)
    t = x + 7.5
    return 0.5 * math.log(2.0 * math.pi) + (x + 0.5) * math.log(t) - t + math.log(acc)


def beta_cf(a, b, x):
    tiny = 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c = 1.0
    dd = 1.0 - qab * x / qap
    dd = tiny if abs(dd) < tiny else dd
    dd = 1.0 / dd
    h = dd
    for m in range(1, 500):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        dd = 1.0 + aa * dd
        dd = tiny if abs(dd) < tiny else dd
        c = 1.0 + aa / c
        c = tiny if abs(c) < tiny else c
        dd = 1.0 / dd
        h *= dd * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        dd = 1.0 + aa * dd
        dd = tiny if abs(dd) < tiny else dd
        c = 1.0 + aa / c
        c = tiny if abs(c) < tiny else c
        dd = 1.0 / dd
        delta = dd * c
        h *= delta
        if abs(delta - 1.0) < 1e-15:
            break
    return h


def inc_beta(a, b, x):
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    front = math.exp(log_gamma(a + b) - log_gamma(a) - log_gamma(b) + a * math.log(x) + b * math.log(1.0 - x))
    if x < (a + 1.0) / (a + b + 2.0):
        return front * beta_cf(a, b, x) / a
    return 1.0 - front * beta_cf(b, a, 1.0 - x) / b


def p_t_beta(t, df):
    return inc_beta(df / 2.0, 0.5, df / (df + t * t))


# tabulated two-sided critical values: (df, t, two-sided p)
TABLE = [(1, 12.706205, 0.05), (2, 4.302653, 0.05), (5, 2.570582, 0.05), (18, 2.100922, 0.05),
         (38, 2.024394, 0.05), (98, 1.984467, 0.05), (30, 2.749996, 0.01), (38, 2.711558, 0.01),
         (1, 1.0, 0.5), (4, 0.0, 1.0)]
for df, t, p in TABLE:
    a = p_two_sided_student(t, df)
    b = p_t_beta(t, df)
    print(f"df={df:3d} t={t:9.6f} expected p={p:.4f}  student-helper={a:.6f}  beta-helper={b:.6f}")
# non-integer df (Welch) cross-check: the beta form at df and df+1e-9 must agree; at df = 38 it must equal the Student form
print("beta at df 37.5, t 2.03:", p_t_beta(2.03, 37.5), " beta at df 38:", p_t_beta(2.03, 38), " student at 38:", p_two_sided_student(2.03, 38))
