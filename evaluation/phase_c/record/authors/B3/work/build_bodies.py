# Scratch builder (Part 2): replaces the single line "    raise NotImplementedError" of criterion(d) in the
# faulty.py / fixed.py copies of every B-3 skeleton. Nothing else in the files is touched.
# The faulty bodies are never executed by the author; only a syntax check is run on them.
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "cases"
MARK = "    raise NotImplementedError\n"

# ---------------------------------------------------------------- shared helper texts (same in both versions)
T_SF = '''
def t_sf(t, df):
    # one-sided tail P(T > t) of Student's t with df degrees of freedom (substitution x = sqrt(df) * tan(theta))
    top = np.pi / 2.0

    def tail(a):
        th = np.linspace(a, top, 4001)
        f = np.cos(th) ** (df - 1.0)
        return float(np.sum(f[:-1] + f[1:]) * (top - a) / 8000.0)

    p = tail(float(np.arctan(abs(t) / np.sqrt(df)))) / (2.0 * tail(0.0))
    return p if t >= 0 else 1.0 - p
'''

# OLS: coefficient of the first predictor, its t statistic and the residual degrees of freedom.
OLS_T = '''
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
'''

# OLS: coefficient of the first predictor only.
SLOPE = '''
def slope(y, cols):
    n = y.shape[0]
    X = np.column_stack([np.ones(n)] + list(cols))
    if n < X.shape[1] + 1:
        return None
    x = X[:, 1]
    rest = np.delete(X, 1, axis=1)
    r = x - rest @ np.linalg.lstsq(rest, x, rcond=None)[0]
    rr = float(r @ r)
    css = float(np.sum((x - x.mean()) ** 2))
    if not (css > 0.0) or rr <= 1e-10 * css:
        return None
    beta = float(r @ y) / rr
    return beta if np.isfinite(beta) else None
'''

# Pearson correlation of x and y after removing a (possibly empty) list of covariates.
PARTIAL_R = '''
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
'''

R2 = '''
def flat(a):
    return not (float(np.sum((a - a.mean()) ** 2)) > 0.0)


def r2(y, cols):
    n = y.shape[0]
    X = np.column_stack([np.ones(n)] + list(cols))
    tss = float(np.sum((y - y.mean()) ** 2))
    if n < X.shape[1] + 1 or not (tss > 0.0):
        return None
    res = y - X @ np.linalg.lstsq(X, y, rcond=None)[0]
    return 1.0 - float(res @ res) / tss
'''

AUC = '''
def auc(score, label):
    pos = score[label]
    neg = np.sort(score[~label])
    if pos.size == 0 or neg.size == 0:
        return None
    lo = np.searchsorted(neg, pos, side="left")
    hi = np.searchsorted(neg, pos, side="right")
    return float(np.sum(lo + 0.5 * (hi - lo)) / (pos.size * neg.size))
'''


def fin(*names):
    return "if not (" + " and ".join(f"np.all(np.isfinite({n}))" for n in names) + "):\n    return None\n"


BODIES = {}

# ---------------------------------------------------------------- B3-01
B01_HEAD = '''
heart = np.asarray(d["heart_weight"], dtype=float)
mass = np.asarray(d["body_mass"], dtype=float)
treated = np.asarray(d["treated"], dtype=bool).astype(float)
'''
BODIES["B3-01"] = (
    # faulty
    B01_HEAD + T_SF + OLS_T + '''
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
''',
    # fixed
    B01_HEAD + T_SF + OLS_T + '''
if not (np.all(np.isfinite(heart)) and np.all(np.isfinite(mass))):
    return None
# analysis of covariance: heart weight on treatment status and body mass; one-sided t test of the treatment coefficient
out = ols_t(heart, [treated, mass])
if out is None:
    return None
beta, t, df = out
return bool(beta > 0.0 and t_sf(t, df) < 0.05)
''')

# ---------------------------------------------------------------- B3-02
B02_HEAD = '''
alb = np.asarray(d["albumin_excretion"], dtype=float)
cre = np.asarray(d["creatinine_excretion"], dtype=float)
age = np.asarray(d["age"], dtype=float)
'''
BODIES["B3-02"] = (
    B02_HEAD + PARTIAL_R + '''
if not (np.all(np.isfinite(alb)) and np.all(np.isfinite(cre)) and np.all(np.isfinite(age))):
    return None
# Pearson correlation of age with the albumin / creatinine quotient
with np.errstate(divide="ignore", invalid="ignore"):
    quotient = alb / cre
if not np.all(np.isfinite(quotient)):
    return None
r = partial_r(age, quotient, [])
if r is None:
    return None
return bool(r >= 0.15)
''',
    B02_HEAD + PARTIAL_R + '''
if not (np.all(np.isfinite(alb)) and np.all(np.isfinite(cre)) and np.all(np.isfinite(age))):
    return None
# partial correlation of albumin excretion and age given creatinine excretion
r = partial_r(alb, age, [cre])
if r is None:
    return None
return bool(r >= 0.15)
''')

# ---------------------------------------------------------------- B3-03
B03_HEAD = '''
lvm = np.asarray(d["lv_mass"], dtype=float)
bsa = np.asarray(d["body_surface_area"], dtype=float)
sbp = np.asarray(d["systolic_bp"], dtype=float)
'''
BODIES["B3-03"] = (
    B03_HEAD + R2 + '''
if not (np.all(np.isfinite(lvm)) and np.all(np.isfinite(bsa)) and np.all(np.isfinite(sbp))):
    return None
# R-squared of systolic pressure regressed on the quotient left ventricular mass / body surface area
with np.errstate(divide="ignore", invalid="ignore"):
    quotient = lvm / bsa
if not np.all(np.isfinite(quotient)) or flat(quotient) or flat(sbp):
    return None
value = r2(sbp, [quotient])
if value is None or not np.isfinite(value):
    return None
return bool(value >= 0.05)
''',
    B03_HEAD + R2 + '''
if not (np.all(np.isfinite(lvm)) and np.all(np.isfinite(bsa)) and np.all(np.isfinite(sbp))):
    return None
# gain in R-squared when left ventricular mass is added to the regression of systolic pressure on body surface area
if flat(lvm) or flat(bsa) or flat(sbp):
    return None
full = r2(sbp, [bsa, lvm])
reduced = r2(sbp, [bsa])
if full is None or reduced is None or not np.isfinite(full - reduced):
    return None
return bool(full - reduced >= 0.05)
''')

# ---------------------------------------------------------------- B3-04
B04_HEAD = '''
liver = np.asarray(d["liver_weight"], dtype=float)
kidney = np.asarray(d["kidney_weight"], dtype=float)
mass = np.asarray(d["body_mass"], dtype=float)
'''
BODIES["B3-04"] = (
    B04_HEAD + SLOPE + '''
if not (np.all(np.isfinite(liver)) and np.all(np.isfinite(kidney)) and np.all(np.isfinite(mass))):
    return None
# slope of liver weight / body mass on kidney weight / body mass
with np.errstate(divide="ignore", invalid="ignore"):
    y = liver / mass
    x = kidney / mass
if not (np.all(np.isfinite(y)) and np.all(np.isfinite(x))):
    return None
b = slope(y, [x])
if b is None:
    return None
return bool(b >= 0.25)
''',
    B04_HEAD + SLOPE + '''
if not (np.all(np.isfinite(liver)) and np.all(np.isfinite(kidney)) and np.all(np.isfinite(mass))):
    return None
# coefficient of kidney weight in the regression of liver weight on kidney weight and body mass
b = slope(liver, [kidney, mass])
if b is None:
    return None
return bool(b >= 0.25)
''')

# ---------------------------------------------------------------- B3-05
B05_HEAD = '''
femur = np.asarray(d["femur_length"], dtype=float)
tibia = np.asarray(d["tibia_length"], dtype=float)
humerus = np.asarray(d["humerus_length"], dtype=float)
'''
BODIES["B3-05"] = (
    B05_HEAD + PARTIAL_R + '''
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
''',
    B05_HEAD + PARTIAL_R + '''
if not (np.all(np.isfinite(femur)) and np.all(np.isfinite(tibia)) and np.all(np.isfinite(humerus))):
    return None
# partial correlation between femur length and tibia length given humerus length
r = partial_r(femur, tibia, [humerus])
if r is None:
    return None
return bool(r >= 0.3)
''')

# ---------------------------------------------------------------- B3-06
B06_HEAD = '''
true = np.asarray(d["true_value"], dtype=float)
est = np.asarray(d["estimates"], dtype=float)
'''
BODIES["B3-06"] = (
    B06_HEAD + PARTIAL_R + '''
if not (np.all(np.isfinite(true)) and np.all(np.isfinite(est))):
    return None
k = est.shape[1]
if k < 2:
    return None
# relative error of each observer on each trial: (estimate - true value) / true value
with np.errstate(divide="ignore", invalid="ignore"):
    rel = (est - true[:, None]) / true[:, None]
if not np.all(np.isfinite(rel)):
    return None
vals = []
for i in range(k):
    for j in range(i + 1, k):
        r = partial_r(rel[:, i], rel[:, j], [])
        if r is None:
            return None
        vals.append(r)
return bool(np.mean(vals) >= 0.2)
''',
    B06_HEAD + PARTIAL_R + '''
if not (np.all(np.isfinite(true)) and np.all(np.isfinite(est))):
    return None
k = est.shape[1]
if k < 2:
    return None
# partial correlation of each pair of observers' estimates given the true value
vals = []
for i in range(k):
    for j in range(i + 1, k):
        r = partial_r(est[:, i], est[:, j], [true])
        if r is None:
            return None
        vals.append(r)
return bool(np.mean(vals) >= 0.2)
''')

# ---------------------------------------------------------------- B3-07
B07_HEAD = '''
abd = np.asarray(d["abdomen_length"], dtype=float)
claw = np.asarray(d["claw_length"], dtype=float)
body = np.asarray(d["body_length"], dtype=float)
'''
BODIES["B3-07"] = (
    B07_HEAD + SLOPE + '''
if not (np.all(np.isfinite(abd)) and np.all(np.isfinite(claw)) and np.all(np.isfinite(body))):
    return None
# per species: slope of claw length / body length on abdomen length / body length
with np.errstate(divide="ignore", invalid="ignore"):
    y = claw / body
    x = abd / body
if not (np.all(np.isfinite(y)) and np.all(np.isfinite(x))):
    return None
coefs = []
for s in range(y.shape[0]):
    b = slope(y[s], [x[s]])
    if b is None:
        return None
    coefs.append(b)
return bool(np.mean(coefs) >= 0.15)
''',
    B07_HEAD + SLOPE + '''
if not (np.all(np.isfinite(abd)) and np.all(np.isfinite(claw)) and np.all(np.isfinite(body))):
    return None
# per species: coefficient of abdomen length in the regression of claw length on abdomen length and body length
coefs = []
for s in range(claw.shape[0]):
    b = slope(claw[s], [abd[s], body[s]])
    if b is None:
        return None
    coefs.append(b)
return bool(np.mean(coefs) >= 0.15)
''')

# ---------------------------------------------------------------- B3-08
B08_HEAD = '''
first = np.asarray(d["sbp_baseline_first"], dtype=float)
second = np.asarray(d["sbp_baseline_second"], dtype=float)
week12 = np.asarray(d["sbp_week12"], dtype=float)
'''
BODIES["B3-08"] = (
    B08_HEAD + PARTIAL_R + '''
if not (np.all(np.isfinite(first)) and np.all(np.isfinite(second)) and np.all(np.isfinite(week12))):
    return None
# correlation between the fall (first baseline reading minus week-12 reading) and the first baseline reading
fall = first - week12
r = partial_r(fall, first, [])
if r is None:
    return None
return bool(r >= 0.3)
''',
    B08_HEAD + PARTIAL_R + '''
if not (np.all(np.isfinite(first)) and np.all(np.isfinite(second)) and np.all(np.isfinite(week12))):
    return None
# correlation between the fall (first baseline reading minus week-12 reading) and the second baseline reading
fall = first - week12
r = partial_r(fall, second, [])
if r is None:
    return None
return bool(r >= 0.3)
''')

# ---------------------------------------------------------------- B3-09
B09_HEAD = '''
co = np.asarray(d["cardiac_output"], dtype=float)
ca = np.asarray(d["arterial_o2_content"], dtype=float)
cv = np.asarray(d["venous_o2_content"], dtype=float)
vo2_expired = np.asarray(d["o2_uptake_expired"], dtype=float)
'''
BODIES["B3-09"] = (
    B09_HEAD + PARTIAL_R + '''
if not (np.all(np.isfinite(co)) and np.all(np.isfinite(ca)) and np.all(np.isfinite(cv)) and np.all(np.isfinite(vo2_expired))):
    return None
# correlation between oxygen delivery and the uptake calculated from cardiac output and the arteriovenous content difference
delivery = co * ca
uptake = co * (ca - cv)
r = partial_r(delivery, uptake, [])
if r is None:
    return None
return bool(r >= 0.3)
''',
    B09_HEAD + PARTIAL_R + '''
if not (np.all(np.isfinite(co)) and np.all(np.isfinite(ca)) and np.all(np.isfinite(cv)) and np.all(np.isfinite(vo2_expired))):
    return None
# correlation between oxygen delivery and the uptake measured by expired-gas analysis
delivery = co * ca
r = partial_r(delivery, vo2_expired, [])
if r is None:
    return None
return bool(r >= 0.3)
''')

# ---------------------------------------------------------------- B3-10
B10_HEAD = '''
items = np.asarray(d["item_scores"], dtype=float)
'''
BODIES["B3-10"] = (
    B10_HEAD + AUC + '''
if not np.all(np.isfinite(items)):
    return None
# label: total over all eight items at least 12; AUC of the item 1 score for that label
label = items.sum(axis=1) >= 12.0
a = auc(items[:, 0], label)
if a is None:
    return None
return bool(a >= 0.65)
''',
    B10_HEAD + AUC + '''
if not np.all(np.isfinite(items)):
    return None
# label: total over items 2 to 8 at least 12; AUC of the item 1 score for that label
label = items[:, 1:].sum(axis=1) >= 12.0
a = auc(items[:, 0], label)
if a is None:
    return None
return bool(a >= 0.65)
''')

# ---------------------------------------------------------------- B3-11
B11_HEAD = '''
ga = np.asarray(d["gene_a_expression"], dtype=float)
gb = np.asarray(d["gene_b_expression"], dtype=float)
gc = np.asarray(d["gene_c_expression"], dtype=float)
'''
BODIES["B3-11"] = (
    B11_HEAD + R2 + '''
if not (np.all(np.isfinite(ga)) and np.all(np.isfinite(gb)) and np.all(np.isfinite(gc))):
    return None
# R-squared of gene B / gene C regressed on gene A / gene C
with np.errstate(divide="ignore", invalid="ignore"):
    y = gb / gc
    x = ga / gc
if not (np.all(np.isfinite(y)) and np.all(np.isfinite(x))) or flat(y) or flat(x):
    return None
value = r2(y, [x])
if value is None or not np.isfinite(value):
    return None
return bool(value >= 0.05)
''',
    B11_HEAD + R2 + '''
if not (np.all(np.isfinite(ga)) and np.all(np.isfinite(gb)) and np.all(np.isfinite(gc))):
    return None
# gain in R-squared when gene A is added to the regression of gene B on gene C
if flat(ga) or flat(gb) or flat(gc):
    return None
full = r2(gb, [gc, ga])
reduced = r2(gb, [gc])
if full is None or reduced is None or not np.isfinite(full - reduced):
    return None
return bool(full - reduced >= 0.05)
''')

# ---------------------------------------------------------------- B3-12
B12_HEAD = '''
adm = np.asarray(d["admissions"], dtype=float)
pop = np.asarray(d["population"], dtype=float)
time = np.asarray(d["time_years"], dtype=float)
'''
BODIES["B3-12"] = (
    B12_HEAD + T_SF + OLS_T + '''
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
''',
    B12_HEAD + T_SF + OLS_T + '''
if not (np.all(np.isfinite(adm)) and np.all(np.isfinite(pop)) and np.all(np.isfinite(time))):
    return None
# one-sided t test of the time coefficient in the regression of admissions on time and population
out = ols_t(adm, [time, pop])
if out is None:
    return None
beta, t, df = out
return bool(beta > 0.0 and t_sf(t, df) < 0.05)
''')


def render(body):
    return textwrap.indent(body.strip("\n") + "\n", "    ")


def main():
    for cid, (faulty, fixed) in BODIES.items():
        for name, body in (("faulty.py", faulty), ("fixed.py", fixed)):
            skel = (ROOT / cid / "skeleton.py").read_text(encoding="utf-8")
            assert skel.count(MARK) == 1, (cid, name)
            out = skel.replace(MARK, render(body))
            (ROOT / cid / name).write_text(out, encoding="utf-8", newline="\n")
        print("built", cid)


if __name__ == "__main__":
    main()
