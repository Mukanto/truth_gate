"""Splice the criterion bodies into faulty.py / fixed.py of each B-3 case (replaces only the NotImplementedError line).
Text manipulation only; nothing is executed or imported from the case files."""
import sys

ROOT = r"C:\Users\user\AppData\Local\Temp\claude\e3156104bf704008\a94a39de-e61e-4069-8597-c7836ecd2de0\scratchpad\phase_b\B3\cases"
LINE = "    raise NotImplementedError\n"

RANK = '''    def rank(x):
        u, inv, cnt = np.unique(x, return_inverse=True, return_counts=True)
        return (np.cumsum(cnt) - (cnt - 1) / 2.0)[inv]
'''

PARTIAL = '''    def partial(a, b, c):
        rab = np.corrcoef(a, b)[0, 1]
        rac = np.corrcoef(a, c)[0, 1]
        rbc = np.corrcoef(b, c)[0, 1]
        den = (1.0 - rac ** 2) * (1.0 - rbc ** 2)
        if not den > 1e-12:
            return None
        return (rab - rac * rbc) / np.sqrt(den)
'''

BODIES = {}

# ---------------------------------------------------------------- B3-01
B01_HEAD = '''    co = np.asarray(d["cardiac_output"], dtype=float)
    hb = np.asarray(d["hemoglobin"], dtype=float)
    sa = np.asarray(d["sao2"], dtype=float)
'''
B01_TAIL = '''    if not (np.all(np.isfinite(do2)) and np.all(np.isfinite(vo2))):
        return None
    if np.std(do2) == 0 or np.std(vo2) == 0:
        return None
    r = np.corrcoef(vo2, do2)[0, 1]
    return bool(r >= 0.5)
'''
BODIES["B3-01"] = (
    B01_HEAD + '''    sv = np.asarray(d["svo2"], dtype=float)
    o2_content = co * hb * 13.4                      # 1.34 mL O2 per g Hb, x10 for g/dL -> g/L
    do2 = o2_content * sa                            # oxygen delivery, mL/min
    vo2 = o2_content * (sa - sv)                     # oxygen consumption by the Fick calculation, mL/min
''' + B01_TAIL,
    B01_HEAD + '''    o2_content = co * hb * 13.4                      # 1.34 mL O2 per g Hb, x10 for g/dL -> g/L
    do2 = o2_content * sa                            # oxygen delivery, mL/min
    vo2 = np.asarray(d["vo2_expired"], dtype=float)  # consumption measured independently (expired gas)
''' + B01_TAIL,
)

# ---------------------------------------------------------------- B3-02
B02_HEAD = RANK + '''    mapp = np.asarray(d["map"], dtype=float)
    cvp = np.asarray(d["cvp"], dtype=float)
    co_th = np.asarray(d["co_thermodilution"], dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        svr = 80.0 * (mapp - cvp) / co_th            # systemic vascular resistance, dyn s/cm5, from thermodilution output
'''
B02_TAIL = '''    if not (np.all(np.isfinite(svr)) and np.all(np.isfinite(co))):
        return None
    if np.std(svr) == 0 or np.std(co) == 0:
        return None
    rho = np.corrcoef(rank(svr), rank(co))[0, 1]
    return bool(rho <= -0.4)
'''
BODIES["B3-02"] = (
    B02_HEAD + '''    co = co_th                                       # the same thermodilution output that enters the resistance
''' + B02_TAIL,
    B02_HEAD + '''    co = np.asarray(d["co_doppler"], dtype=float)    # output measured separately (Doppler)
''' + B02_TAIL,
)

# ---------------------------------------------------------------- B3-03
B03_HEAD = '''    svi = np.asarray(d["stroke_volume_index"], dtype=float)
    ef = np.asarray(d["rvef"], dtype=float)
'''
B03_TAIL = '''    if not (np.all(np.isfinite(edv)) and np.all(np.isfinite(ef))):
        return None
    if np.std(edv) == 0 or np.std(ef) == 0:
        return None
    zx = (ef - ef.mean()) / ef.std()
    zy = (edv - edv.mean()) / edv.std()
    slope = np.sum(zx * zy) / np.sum(zx * zx)
    return bool(slope <= -0.4)
'''
BODIES["B3-03"] = (
    B03_HEAD + '''    with np.errstate(divide="ignore", invalid="ignore"):
        edv = svi / ef                               # end-diastolic volume index = stroke volume index / ejection fraction
''' + B03_TAIL,
    B03_HEAD + '''    edv = np.asarray(d["rv_edv_index_radionuclide"], dtype=float)   # volume measured independently
''' + B03_TAIL,
)

# ---------------------------------------------------------------- B3-04
B04_HEAD = '''    co = np.asarray(d["cardiac_output"], dtype=float)
    hb = np.asarray(d["hemoglobin"], dtype=float)
    sa = np.asarray(d["sao2"], dtype=float)
'''
B04_TAIL = '''    ddo2 = do2[:, 1] - do2[:, 0]
    dvo2 = vo2[:, 1] - vo2[:, 0]
    if not (np.all(np.isfinite(ddo2)) and np.all(np.isfinite(dvo2))):
        return None
    if np.std(ddo2) == 0 or np.std(dvo2) == 0:
        return None
    r = np.corrcoef(ddo2, dvo2)[0, 1]
    return bool(r ** 2 >= 0.25)
'''
BODIES["B3-04"] = (
    B04_HEAD + '''    sv = np.asarray(d["svo2"], dtype=float)
    o2_content = co * hb * 13.4                      # mL O2 per L of blood at full saturation
    do2 = o2_content * sa                            # delivery at each time point, mL/min
    vo2 = o2_content * (sa - sv)                     # Fick consumption at each time point, mL/min
''' + B04_TAIL,
    B04_HEAD + '''    o2_content = co * hb * 13.4                      # mL O2 per L of blood at full saturation
    do2 = o2_content * sa                            # delivery at each time point, mL/min
    vo2 = np.asarray(d["vo2_expired"], dtype=float)  # consumption measured independently (expired gas)
''' + B04_TAIL,
)

# ---------------------------------------------------------------- B3-05
B05_HEAD = '''    fem = np.asarray(d["femur_length"], dtype=float)
    tib = np.asarray(d["tibia_length"], dtype=float)
    vcl = np.asarray(d["vertebral_column_length"], dtype=float)
    if not (np.all(np.isfinite(fem)) and np.all(np.isfinite(tib)) and np.all(np.isfinite(vcl))):
        return None
    if np.std(fem) == 0 or np.std(tib) == 0 or np.std(vcl) == 0:
        return None
'''
BODIES["B3-05"] = (
    B05_HEAD + '''    with np.errstate(divide="ignore", invalid="ignore"):
        fi, ti = fem / vcl, tib / vcl                 # relative lengths (indices with the same denominator)
    if not (np.all(np.isfinite(fi)) and np.all(np.isfinite(ti))) or np.std(fi) == 0 or np.std(ti) == 0:
        return None
    r = np.corrcoef(fi, ti)[0, 1]
    return bool(r >= 0.4)
''',
    B05_HEAD + PARTIAL + '''    r = partial(fem, tib, vcl)                        # partial correlation, vertebral column length held fixed
    if r is None:
        return None
    return bool(r >= 0.4)
''',
)

# ---------------------------------------------------------------- B3-06
B06_HEAD = RANK + '''    co2 = np.asarray(d["co2_emissions_total"], dtype=float)
    gdp = np.asarray(d["gdp_total"], dtype=float)
    pop = np.asarray(d["population"], dtype=float)
    if not (np.all(np.isfinite(co2)) and np.all(np.isfinite(gdp)) and np.all(np.isfinite(pop))):
        return None
    if np.std(co2) == 0 or np.std(gdp) == 0 or np.std(pop) == 0:
        return None
'''
BODIES["B3-06"] = (
    B06_HEAD + '''    with np.errstate(divide="ignore", invalid="ignore"):
        pc_co2 = co2 / pop                           # per-capita emissions
        pc_gdp = gdp / pop                           # per-capita GDP
    if not (np.all(np.isfinite(pc_co2)) and np.all(np.isfinite(pc_gdp))) or np.std(pc_co2) == 0 or np.std(pc_gdp) == 0:
        return None
    rho = np.corrcoef(rank(pc_co2), rank(pc_gdp))[0, 1]
    return bool(rho >= 0.5)
''',
    B06_HEAD + PARTIAL + '''    rho = partial(rank(co2), rank(gdp), rank(pop))   # Spearman partial correlation, population held fixed
    if rho is None:
        return None
    return bool(rho >= 0.5)
''',
)

# ---------------------------------------------------------------- B3-07
B07_HEAD = '''    def z(x):
        return (x - x.mean()) / x.std()

    yt = np.asarray(d["yield_total"], dtype=float)
    ft = np.asarray(d["fertilizer_total"], dtype=float)
    area = np.asarray(d["farm_area"], dtype=float)
    if not (np.all(np.isfinite(yt)) and np.all(np.isfinite(ft)) and np.all(np.isfinite(area))):
        return None
    if np.std(yt) == 0 or np.std(ft) == 0 or np.std(area) == 0:
        return None
'''
BODIES["B3-07"] = (
    B07_HEAD + '''    with np.errstate(divide="ignore", invalid="ignore"):
        y = yt / area                                # yield per hectare
        f = ft / area                                # fertilizer per hectare
    if not (np.all(np.isfinite(y)) and np.all(np.isfinite(f))) or np.std(y) == 0 or np.std(f) == 0:
        return None
    zy, zf = z(y), z(f)
    slope = np.sum(zf * zy) / np.sum(zf * zf)
    return bool(slope >= 0.3)
''',
    B07_HEAD + '''    zy, zf, za = z(yt), z(ft), z(area)
    X = np.column_stack([np.ones(len(zy)), zf, za])
    coef = np.linalg.lstsq(X, zy, rcond=None)[0]     # yield on fertilizer with the area as a covariate
    return bool(coef[1] >= 0.3)
''',
)

# ---------------------------------------------------------------- B3-08
B08_HEAD = '''    vo2 = np.asarray(d["vo2max"], dtype=float)
    pw = np.asarray(d["peak_power"], dtype=float)
    mass = np.asarray(d["body_mass"], dtype=float)
    if not (np.all(np.isfinite(vo2)) and np.all(np.isfinite(pw)) and np.all(np.isfinite(mass))):
        return None
    if np.std(vo2) == 0 or np.std(pw) == 0 or np.std(mass) == 0:
        return None
'''
BODIES["B3-08"] = (
    B08_HEAD + '''    with np.errstate(divide="ignore", invalid="ignore"):
        x = vo2 / mass                               # maximal oxygen uptake per kg
        y = pw / mass                                # peak power per kg
    if np.std(x) == 0 or np.std(y) == 0:
        return None
    r = np.corrcoef(x, y)[0, 1]
    return bool(r ** 2 >= 0.25)
''',
    B08_HEAD + PARTIAL + '''    r = partial(vo2, pw, mass)                       # partial correlation, body mass held fixed
    if r is None:
        return None
    return bool(r ** 2 >= 0.25)
''',
)

# ---------------------------------------------------------------- B3-09
B09_HEAD = '''    def z(x):
        return (x - x.mean()) / x.std()

    inf = np.asarray(d["infections"], dtype=float)
    adm = np.asarray(d["admissions"], dtype=float)
    beds = np.asarray(d["beds"], dtype=float)
    if not (np.all(np.isfinite(inf)) and np.all(np.isfinite(adm)) and np.all(np.isfinite(beds))):
        return None
    if np.std(inf) == 0 or np.std(adm) == 0 or np.std(beds) == 0:
        return None
'''
BODIES["B3-09"] = (
    B09_HEAD + '''    with np.errstate(divide="ignore", invalid="ignore"):
        rate = inf / adm                             # infections per admission
    if not np.all(np.isfinite(rate)) or np.std(rate) == 0:
        return None
    zr, zb = z(rate), z(beds)
    slope = np.sum(zb * zr) / np.sum(zb * zb)
    return bool(slope <= -0.3)
''',
    B09_HEAD + '''    zi, za, zb = z(inf), z(adm), z(beds)
    X = np.column_stack([np.ones(len(zi)), zb, za])
    coef = np.linalg.lstsq(X, zi, rcond=None)[0]     # infections on beds with admissions as a covariate
    return bool(coef[1] <= -0.3)
''',
)

# ---------------------------------------------------------------- B3-10
B10_HEAD = '''    def z(x):
        return (x - x.mean()) / x.std()

    sbp = np.asarray(d["systolic_pressure"], dtype=float)
    hw = np.asarray(d["heart_weight"], dtype=float)
    bw = np.asarray(d["body_weight"], dtype=float)
    if not (np.all(np.isfinite(sbp)) and np.all(np.isfinite(hw)) and np.all(np.isfinite(bw))):
        return None
    if np.std(sbp) == 0 or np.std(hw) == 0 or np.std(bw) == 0:
        return None
'''
BODIES["B3-10"] = (
    B10_HEAD + '''    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = hw / bw                              # heart weight per body weight
    if not np.all(np.isfinite(ratio)) or np.std(ratio) == 0:
        return None
    zs, zr = z(sbp), z(ratio)
    slope = np.sum(zr * zs) / np.sum(zr * zr)
    return bool(slope >= 0.3)
''',
    B10_HEAD + '''    zs, zh, zw = z(sbp), z(hw), z(bw)
    X = np.column_stack([np.ones(len(zs)), zh, zw])
    coef = np.linalg.lstsq(X, zs, rcond=None)[0]     # pressure on heart weight with body weight as a covariate
    return bool(coef[1] >= 0.3)
''',
)

# ---------------------------------------------------------------- B3-11
B11_HEAD = RANK + '''    energy = np.asarray(d["energy_use"], dtype=float)
    area = np.asarray(d["floor_area"], dtype=float)
    occ = np.asarray(d["occupants"], dtype=float)
    if not (np.all(np.isfinite(energy)) and np.all(np.isfinite(area)) and np.all(np.isfinite(occ))):
        return None
    if np.std(energy) == 0 or np.std(area) == 0 or np.std(occ) == 0:
        return None
'''
BODIES["B3-11"] = (
    B11_HEAD + '''    with np.errstate(divide="ignore", invalid="ignore"):
        eui = energy / area                          # energy use per square metre
    if not np.all(np.isfinite(eui)) or np.std(eui) == 0:
        return None
    rho = np.corrcoef(rank(occ), rank(eui))[0, 1]
    return bool(rho <= -0.3)
''',
    B11_HEAD + PARTIAL + '''    rho = partial(rank(occ), rank(energy), rank(area))   # Spearman partial correlation, floor area held fixed
    if rho is None:
        return None
    return bool(rho <= -0.3)
''',
)

# ---------------------------------------------------------------- B3-12
B12_HEAD = '''    leavers = np.asarray(d["leavers"], dtype=float)
    hc = np.asarray(d["headcount"], dtype=float)
    pay = np.asarray(d["payroll"], dtype=float)
    if not (np.all(np.isfinite(leavers)) and np.all(np.isfinite(hc)) and np.all(np.isfinite(pay))):
        return None
    if np.std(leavers) == 0 or np.std(hc) == 0 or np.std(pay) == 0:
        return None
'''
BODIES["B3-12"] = (
    B12_HEAD + '''    with np.errstate(divide="ignore", invalid="ignore"):
        rate = leavers / hc                          # turnover rate, leavers per employee
    if not np.all(np.isfinite(rate)) or np.std(rate) == 0:
        return None
    r = np.corrcoef(pay, rate)[0, 1]
    return bool(r ** 2 >= 0.1)
''',
    B12_HEAD + PARTIAL + '''    r = partial(leavers, pay, hc)                    # partial R squared of payroll, headcount held fixed
    if r is None:
        return None
    return bool(r ** 2 >= 0.1)
''',
)


def splice(case, which, body):
    path = f"{ROOT}\\{case}\\{which}.py"
    with open(path, encoding="utf-8", newline="") as fh:
        text = fh.read()
    assert text.count(LINE) == 1, (case, which)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text.replace(LINE, body))


if __name__ == "__main__":
    cases = sys.argv[1:] or sorted(BODIES)
    for c in cases:
        f, x = BODIES[c]
        splice(c, "faulty", f)
        splice(c, "fixed", x)
        print("spliced", c)
