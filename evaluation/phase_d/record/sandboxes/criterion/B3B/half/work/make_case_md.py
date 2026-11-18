"""Writes CASE.md for every case of half B3B (text only; runs nothing from the generated bodies)."""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
HALF = os.path.dirname(HERE)
BRIEFS = {b['local_id']: b for b in json.load(open(os.path.join(HALF, 'BRIEFS.json'), encoding='utf-8'))}
PRIV = {p['local_id']: p for p in json.load(open(os.path.join(HALF, 'PRIVATE.json'), encoding='utf-8'))}
IDS = json.load(open(os.path.join(HALF, 'CASE_IDS.json'), encoding='utf-8'))

# timings and results of work\check_fixed.py (random arrays N(10,2) / Bernoulli(0.5), seed 0)
RUN1 = {
    'B3B-01': ('False', '0.4 ms'), 'B3B-02': ('False', '1.0 ms'), 'B3B-03': ('False', '0.2 ms'),
    'B3B-04': ('False', '0.2 ms'), 'B3B-05': ('False', '0.1 ms'), 'B3B-06': ('None (corrected variance not positive: pure noise)', '0.2 ms'),
    'B3B-07': ('False', '0.1 ms'), 'B3B-08': ('True', '0.1 ms'), 'B3B-09': ('True', '0.1 ms'),
    'B3B-10': ('None (corrected variance not positive: pure noise)', '0.1 ms'), 'B3B-11': ('False', '0.8 ms'),
    'B3B-12': ('False', '0.2 ms'), 'B3B-13': ('True', '0.1 ms'), 'B3B-14': ('False', '0.2 ms'),
    'B3B-15': ('False', '0.1 ms'),
}

# error lines in faulty_body.py, correction lines in fixed_body.py (checked against `diff` of the two files)
LINES = {
    'B3B-01': ('29-30', '29-33'), 'B3B-02': ('30-32', '30-31'), 'B3B-03': ('106-107', '106-109'),
    'B3B-04': ('113-115', '113-117'), 'B3B-05': ('30', '30'), 'B3B-06': ('25', '25-26 and 32-35'),
    'B3B-07': ('30', '30'), 'B3B-08': ('25-32 and 35', '25-36 (insertion 33-36)'),
    'B3B-09': ('30-33 and 36', '30-36 (insertion 34-36)'), 'B3B-10': ('25-29 and 32', '25-33 (insertion 30-34)'),
    'B3B-11': ('29', '29-32'), 'B3B-12': ('105-106', '105-108'), 'B3B-13': ('25', '25-26 and 33-37'),
    'B3B-14': ('26-31 and 34', '26-35 (insertion 32-35)'), 'B3B-15': ('25', '25'),
}

MAPPING = {
    'B3B-01': (
        'Lines {f}: the two size-standardised ratios u = head_width / body_length and v = wing_length / body_length are '
        'correlated (the Y = X1/X2, Z = X3/X2 setting of ATC76, with the common denominator body_length). Parameters: '
        'none beyond the setting; the source gives the spurious correlation as a function of the denominator CV (0.0 up to '
        '0.99), the threshold 0.30 is the claim\'s.',
        'Lines {x}: body_length (with intercept) is regressed out of head_width and of wing_length (np.linalg.lstsq); u and v '
        'are the residuals; the shared line `return bool(corr(u, v) >= 0.30)` is unchanged. The partial correlation is the '
        'correlation of these residuals.',
        'Partial correlation of head width and wing length given body length (head width and wing length net of the linear '
        'effect of body length).'),
    'B3B-02': (
        'Lines {f}: within each population, wing_length / body_length is regressed on head_width / body_length (intercept + '
        'ratio, simple OLS); coefficient index 1 is taken (Y = X1/X2, Z = X3/X2).',
        'Lines {x}: within each population, wing_length is regressed on head_width and body_length (intercept, two predictors); '
        'coefficient index 1 (head_width) is taken. The loop, the per-population guards, the mean over populations and the '
        'threshold 0.30 are shared.',
        'Mean over populations of the within-population partial slope of wing length on head width at fixed body length.'),
    'B3B-03': (
        'Lines {f}: the response is the ratio peak_force / body_mass and the design is intercept + treated indicator; the '
        'treated coefficient and its two-sided t-test (n-2 df) are taken. This is the Student two-sample t test on the ratio '
        '(the private note allows Student or Welch). The ratio analysis is the error named by CUR13 (ratio is meaningful only '
        'for a line through the origin).',
        'Lines {x}: the response is peak_force and the design is intercept + treated + body_mass (analysis of covariance, '
        'common slope); the treated coefficient and its two-sided t-test (n-3 df) are taken. The decision line '
        '(coefficient > 0 and p < 0.05) and the helper are shared.',
        'Difference in peak force between treated and untreated mice at equal body mass.'),
    'B3B-04': (
        'Lines {f}: the response is the ratio oxygen_uptake / body_mass; the F test compares group means (X1 = intercept + group '
        'dummies) with the grand mean (X0 = intercept): one-way ANOVA on the ratio. Error named by CUR13.',
        'Lines {x}: the response is oxygen_uptake; X0 = intercept + body_mass, X1 = intercept + body_mass + group dummies: the '
        'analysis-of-covariance F test of the group effect (common slope, intercept per group). The nested-model F helper, the '
        'p < 0.05 decision are shared.',
        'Difference between groups in oxygen uptake at equal body mass.'),
    'B3B-05': (
        'Line {f}: the baseline reading b is the correlate of the change (follow-up minus baseline): coupled correlation of '
        'change with baseline (TU07: mathematical coupling).',
        'Line {x}: the mean of the baseline and follow-up readings is the correlate (Oldham\'s method, TU07). The shared line '
        '`return bool(corr(chg, x) <= -0.30)` is unchanged. baseline_score_retest is read by neither body (as the private '
        'note states).',
        'Association between change and the average level of the two readings.'),
    'B3B-06': (
        'Line {f}: the regressor is the observed first reading x[:, 0]; the regressand is the least-squares slope b_i of each '
        'individual (computed in lines 20-24 of both files); the slope is cov(u, b) / var(u) with ddof 1 (shared lines). The '
        'naive regression of estimated rate of change on observed initial value is the error (BLO77: "straightforward '
        'regression computations will yield biased results").',
        'Lines {x}: the regressor is the fitted level at the first visit a_i (intercept of the individual line, time 0); the '
        'pooled residual variance s2 = SSR / (n (m - 2)) is estimated from residuals about each individual\'s own line; Var(a) '
        'is reduced by s2 (1/m + tbar^2 / Sxx) and Cov(a, b) is increased by s2 tbar / Sxx (the covariance of the estimated '
        'intercept and slope is -s2 tbar / Sxx). The slope is adjusted Cov / adjusted Var(a) (the shared lines compute '
        'cc / v). Times are 0, 1, ..., m - 1 (annual visits, in time order).',
        'Slope of the true rate of change on the true initial value (second-order moments adjusted for measurement error).'),
    'B3B-07': (
        'Line {f}: the regressor of the change is the baseline depth; the R-squared is the squared correlation (shared line '
        '`return bool(r * r >= 0.15)`), equal to the R-squared of the simple regression.',
        'Line {x}: the regressor is the mean of baseline and follow-up depth (Oldham\'s method, TU04, as R-squared). '
        'baseline_depth_retest is read by neither body.',
        'Variance of the change explained by the average level of the two readings.'),
    'B3B-08': (
        'Lines {f}: VO2 = 10 CO (CaO2 - CvO2) and DO2 = 10 CO CaO2 are computed from the first cardiac output determination '
        'and their raw sample variances and covariance (np.cov, ddof 1) give the correlation; no correction for the error of '
        'CO that enters both (STR87). 10 converts L/min x mL/dL to mL/min.',
        'Lines {x}: s2 = var(CO - CO_2, ddof 1) / 2 is the error variance of CO from the independent repeat; the first-order '
        'Taylor error terms k^2 s2 mean(D^2), k^2 s2 mean(Ca^2), k^2 s2 mean(D Ca) (D = Ca - Cv) are subtracted from Var(VO2), '
        'Var(DO2) and Cov(VO2, DO2); the correlation is formed from the corrected moments (shared lines). Errors of the two '
        'contents are taken as negligible, the documented simplification (no repeat key for them).',
        'Correlation between error-free oxygen consumption and delivery.'),
    'B3B-09': (
        'Lines {f}: per dog, VO2 and DO2 are computed from the first CO determination and the OLS slope of VO2 on DO2 over the '
        '8 steps is raw Cov / raw Var(DO2); the slopes are averaged (no correction for the CO error, STR87).',
        'Lines {x}: per dog, s2 = var(CO - CO_2, ddof 1) / 2 over the 8 steps (pooled across steps within dog) and the error '
        'terms k^2 s2 mean(D Ca) and k^2 s2 mean(Ca^2) are subtracted from the numerator and the denominator of the slope; '
        'the mean over dogs and the threshold 0.15 are shared.',
        'Mean within-dog slope of error-free oxygen consumption on error-free delivery.'),
    'B3B-10': (
        'Lines {f}: D = arterial - venous content and the arterial content (first determinations) are correlated from raw '
        'moments; no correction for the arterial error present in both (MOR86).',
        'Lines {x}: s_a2 = var(Ca - Ca_2, ddof 1) / 2 and s_v2 = var(Cv - Cv_2, ddof 1) / 2 from the repeats; corrected '
        'Cov(D, Ca) = Cov - s_a2, corrected Var(Ca) = Var(Ca) - s_a2, corrected Var(D) = Var(D) - s_a2 - s_v2; correlation '
        'from the corrected moments (shared lines). Additive independent errors, as chosen in the private note.',
        'Correlation between the true content difference and the true arterial content.'),
    'B3B-11': (
        'Line {f}: the six dimensions are divided by body_length (ratios); the first-component share of variance of their '
        'covariance matrix is the statistic (shared helper `first_share`).',
        'Lines {x}: each dimension is regressed on body_length (intercept) and the residuals form the matrix; the same '
        '`first_share` helper and threshold 0.40 follow.',
        'First-component share of variance among the dimensions after the linear effect of body length is removed.'),
    'B3B-12': (
        'Lines {f}: the response is the paired difference of the ratios force_drug / area_drug - force_vehicle / area_vehicle '
        'and the design is the intercept alone; the intercept t test (n-1 df) is the paired t test. Error named by CUR13.',
        'Lines {x}: the response is force_drug - force_vehicle and the design is intercept + (area_drug - area_vehicle) '
        '(paired analysis of covariance); the intercept coefficient and its two-sided t test (n-2 df) are taken. The decision '
        'line (intercept > 0 and p < 0.05) and the helper are shared.',
        'Mean paired difference in force at equal area.'),
    'B3B-13': (
        'Line {f}: the observed first reading x[:, 0] is the correlate of the estimated individual slope (3 readings); '
        'Pearson correlation from raw moments (shared).',
        'Lines {x}: as in B3B-06 with m = 3: a_i is the fitted level at the first visit, s2 = SSR / (n (m - 2)) (one degree '
        'of freedom per individual), Var(a) - s2 (1/m + tbar^2 / Sxx), Var(b) - s2 / Sxx, Cov(a, b) + s2 tbar / Sxx; the '
        'correlation is formed from the corrected moments (shared lines).',
        'Correlation between the true rate of change and the true initial value.'),
    'B3B-14': (
        'Lines {f}: VO2 = 10 CO (CaO2 - CvO2) is regressed on the first CO determination; R-squared = raw Cov^2 / (Var(VO2) '
        'Var(CO)) (= R-squared of the simple regression); no correction for the CO error on both sides (STR87).',
        'Lines {x}: s2 = var(CO - CO_2, ddof 1) / 2; first-order Taylor terms k^2 s2 mean(D^2), s2 and k s2 mean(D) are '
        'subtracted from Var(VO2), Var(CO) and Cov(VO2, CO); the corrected R-squared is the square of the corrected '
        'correlation (shared decision line). Content errors taken as negligible (documented simplification).',
        'Variance of the error-free consumption explained by the error-free cardiac output.'),
    'B3B-15': (
        'Line {f}: the within-trial regressor of the change is the baseline attachment loss; slopes are computed per trial '
        '(shared lines) and averaged.',
        'Line {x}: the regressor is the mean of baseline and follow-up attachment loss (Oldham\'s variable, TU04); the per-trial '
        'slopes, their mean and the threshold -0.20 are shared. The retest key is read by neither body.',
        'Mean within-trial slope of change on the average level of the two measurements.'),
}

DEVIATIONS = {
    'B3B-01': 'none',
    'B3B-02': 'none',
    'B3B-03': 'Faulty uses the Student (pooled) test, which the note allows ("Student or Welch"); it is computed as the t test of the indicator coefficient in an OLS regression, the same helper as the fixed analysis. The t p-value is computed in numpy only (continued-fraction incomplete beta, Lanczos log-gamma), because only `import numpy as np` is allowed; it was compared with scipy.stats.t in scratch (worst relative error 1.1e-13). An empty treatment group is guarded as an empty selection. Problems: none.',
    'B3B-04': 'The F p-value is computed in numpy only (see B3B-03; compared with scipy.stats.f in scratch, same worst error). Problems: none.',
    'B3B-05': 'none',
    'B3B-06': 'The private note does not say what happens when the adjusted variance of the true initial value is not positive; the fixed body returns None then (line `if not v > 0.0`, shared with the faulty body, where it is the zero-variance guard). I read it as the same guard as in the note of B3B-13 and request confirmation (it extends "zero variance" to "variance not positive after correction"). The fitted intercept (level at time 0 of the individual line), not the raw first reading, is the corrected initial value, as the note says.',
    'B3B-07': 'none',
    'B3B-08': 'The private note lists no None rule for B3B-08; the shared line `if not (v > 0.0 and w > 0.0)` returns None when a corrected variance is not positive (the note of B3B-09, B3B-10 and B3B-14 has that rule). For the faulty body the same line is the zero-variance guard. This reads "zero variance" as "variance not positive after correction"; I request confirmation. Content errors are taken as negligible (the note\'s documented simplification).',
    'B3B-09': 'The None rule "a corrected variance is not positive" is applied to the corrected Var(DO2) of every dog (any non-positive value gives None for the whole criterion); same reading of "zero variance" as in B3B-06, confirmation requested. Content errors negligible, as in the note.',
    'B3B-10': 'The None rule "a corrected variance is not positive" is in the shared line `if not (v > 0.0 and w > 0.0)` (only two of the three corrected variances are used in the denominator; the covariance has no sign constraint). Same reading of "zero variance" as in B3B-06; confirmation requested.',
    'B3B-11': 'none',
    'B3B-12': 'Same numpy-only t p-value as B3B-03. Problems: none.',
    'B3B-13': 'The None rule "a corrected variance is not positive" covers both corrected Var(a) and Var(b); same reading of "zero variance" as in B3B-06, confirmation requested.',
    'B3B-14': 'The None rule is the shared line `if not (v > 0.0 and w > 0.0)`; same reading of "zero variance" as in B3B-06, confirmation requested. Content errors negligible, as in the note.',
    'B3B-15': 'none',
}

TAGMAP = {
    'ratio-shared-denominator': 'ratio-shared-denominator', 'ratio-vs-denominator-proxy': 'ratio-vs-denominator-proxy',
    'change-vs-baseline': 'change-vs-baseline', 'shared-measured-component': 'shared-measured-component',
}

P_VALUE_NOTE = {'B3B-03', 'B3B-04', 'B3B-12'}


def guard_lines(lid, which):
    text = open(os.path.join(HALF, 'cases', IDS[lid], which + '_body.py'), encoding='utf-8').read().split('\n')
    start = max(i for i, l in enumerate(text) if l.startswith('def criterion'))
    out = {'min': [], 'finite': [], 'zero': []}
    for i in range(start, len(text)):
        l = text[i]
        if re.match(r'^\s+if .*(<\s*\d|\.any\(g\)|np\.all\(g\))', l) and 'p <' not in l and 'rss' not in l:
            out['min'].append(str(i + 1))
        if 'isfinite' in l and l.strip().startswith('if'):
            out['finite'].append(str(i + 1))
        if ('ptp' in l or '> 0.0' in l or '== 0' in l) and l.strip().startswith('if'):
            out['zero'].append(str(i + 1))
    return out


def build(lid):
    cid = IDS[lid]
    b, p = BRIEFS[lid], PRIV[lid]
    f, x = LINES[lid]
    mf, mx, est = MAPPING[lid]
    gf, gx = guard_lines(lid, 'faulty'), guard_lines(lid, 'fixed')
    keys = '\n'.join('  - `%s` %s %s: %s' % (k['key'], k['shape'], k['dtype'], k['meaning']) for k in b['data_keys'])
    sizes = ', '.join('%s = %s' % (a, c) for a, c in b['sizes'].items())
    res, tms = RUN1[lid]
    pv = ''
    if lid in P_VALUE_NOTE:
        pv = ('- Helper check (scratch): the t and F tail-probability helpers of this file, run on a grid of (statistic, df) '
              'pairs, agree with scipy.stats to a worst relative error of 1.1e-13 (`work\\verify_fixed.py`).\n')
    case_role = 'reserve' if lid in ('B3B-11', 'B3B-12', 'B3B-13', 'B3B-14', 'B3B-15') else 'case'
    s = f'''# {cid} ({lid}, {case_role})

## 1. Identity
- Case id: {cid} (local id {lid} of half B3B).
- Class: B-3, coupling by construction (half B). Mechanism tag: `{p['mechanism_tag']}`. Statistic family: `{p['statistic_family']}`. Subtype: {p['subtype']}.

## 2. Source and documenting passage
- Source key: {p['source']}.
- Passage: {p['passage']}
- Read by: the brief author, through the abstract (saved in `half\\fetched\\`); I (criterion author) confirmed the passage in the saved abstract. No URL was fetched by me.

## 3. The brief
- Claim: {b['claim']}
- Data keys:
{keys}
- Sizes: {sizes}.

## 4. Mapping
- **Faulty, `faulty_body.py`.** {mf.format(f=f, x=x)}
- **Fixed, `fixed_body.py`.** {mx.format(f=f, x=x)}
- Error lines: faulty {f}; correction lines: fixed {x}. All other lines are identical in the two files (checked with `diff`; the files are generated from one template by `work\\make_bodies.py`).
- **Estimand** (the quantity the claim is about): {est}

## 5. Allowed guards used (minimum: {p['guard_minimum']})
- Minimum size: faulty line(s) {', '.join(gf['min']) or '-'}; fixed line(s) {', '.join(gx['min']) or '-'}. The minimum is {p['guard_minimum']} (the private note's `guard_minimum`).
- Non-finite values: faulty line(s) {', '.join(gf['finite']) or '-'}; fixed line(s) {', '.join(gx['finite']) or '-'} (inputs, and derived quantities where a division can produce them).
- Zero variance / non-positive corrected variance: faulty line(s) {', '.join(gf['zero']) or '-'}; fixed line(s) {', '.join(gx['zero']) or '-'}.
- No other branch inspects the data. No randomness is used (no generator is created; the same data give the same answer).

## 6. Runs of the fixed body (own arrays, no world)
- Form check (`work\\check_fixed.py`, own AST script): module level holds only `import numpy as np` and function definitions; `criterion(d)` has no default and no annotation; no decorators, `global` or `nonlocal`; every name read is a parameter, a local, a file function, `np` or a builtin; no `np.random`. Result: no errors.
- Run 1 (`work\\check_fixed.py`): one run on random arrays with the brief's keys and shapes (normal(10, 2); bool with p = 0.5), seed 0: result {res}, type bool or None; a repeat on a copy gave the same result; time {tms}.
- Run 2 (`work\\verify_fixed.py`): one run per threshold on a dataset generated for the check (latent-variable data with the brief's keys and shapes), with the last threshold literal of the file replaced in memory; the answer flips from one value to the other exactly at the reference value of the statistic computed by independent code (scipy / np.polyfit / per-individual loops, written from the private note); at ref -/+ eps, eps = max(1e-9, 1e-7 |ref|) (p-value cases: relative 1e-6). Result: flip as expected. No rate was computed and nothing was tuned.
{pv}- Number of revisions of the fixed body after its first version: 0.
- The faulty body was never run or imported; its only check is the `ast.parse` syntax check (passed).

## 7. Deviations from the private note and problems
- {DEVIATIONS[lid]}
'''
    return s


if __name__ == '__main__':
    for lid in sorted(BRIEFS):
        path = os.path.join(HALF, 'cases', IDS[lid], 'CASE.md')
        with open(path, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(build(lid))
        print('wrote', path)
