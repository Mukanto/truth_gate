"""Runs of the FIXED bodies on arrays generated here (keys, shapes, dtypes of each brief).

Run 1 (smoke): independent log-normal arrays, 3 repeats per case: runs, returns bool/None, timing.
Run 2 (direction): per case one array built so that the fixed estimand clearly satisfies the claim and one where it
clearly does not, to confirm sign and direction conventions. Not a rate, not tuned.
Only fixed_body.py files are loaded. The faulty bodies are never opened by this script.
Usage: py -I run_fixed.py
"""
import importlib.util
import os
import sys
import time

import numpy as np

ROOT = r"E:\Claude Projects\Kapi\phase_d_work\criterion\B3A\half\cases"


def load(cid):
    path = os.path.join(ROOT, cid, "fixed_body.py")
    spec = importlib.util.spec_from_file_location("fixed_" + cid.replace("-", "_"), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.criterion


def ln(rng, shape, mean, cv):
    s = np.sqrt(np.log(1 + cv ** 2))
    return mean * np.exp(rng.normal(-0.5 * s * s, s, shape))


# ---------------- smoke arrays (independent, random) ----------------
def smoke(cid, rng):
    if cid == "D-040":
        return {"breadth": ln(rng, 300, 140, .05), "height": ln(rng, 300, 130, .05), "length": ln(rng, 300, 180, .05)}
    if cid == "D-017":
        return {"fvc": ln(rng, 600, 4, .2), "height": ln(rng, 600, 170, .06), "smoker": rng.random(600) < .3}
    if cid == "D-053":
        return {"bmi_baseline": ln(rng, 500, 15, .08), "bmi_baseline_retest": ln(rng, 500, 15, .08),
                "bmi_followup": ln(rng, 500, 19, .1)}
    if cid == "D-071":
        return {"cardiac_output": ln(rng, 120, 5, .3), "arterial_o2_content": ln(rng, 120, 19, .12),
                "venous_o2_content": ln(rng, 120, 14, .12), "vo2_expired_gas": ln(rng, 120, 250, .2)}
    if cid == "D-062":
        return {"femur": ln(rng, (12, 30), 40, .08), "humerus": ln(rng, (12, 30), 35, .08),
                "body_length": ln(rng, (12, 30), 100, .08)}
    if cid == "D-038":
        return {"lung_cancer_deaths": ln(rng, 150, 20, 1), "cigarettes_sold": ln(rng, 150, 500, 1),
                "population": ln(rng, 150, 40, 1)}
    if cid == "D-006":
        return {"bmi": ln(rng, (500, 6), 16, .1)}
    if cid == "D-008":
        sh = (40, 6)
        return {"cardiac_output": ln(rng, sh, 5, .3), "arterial_o2_content": ln(rng, sh, 19, .1),
                "venous_o2_content": ln(rng, sh, 14, .1), "vo2_expired_gas": ln(rng, sh, 250, .2)}
    if cid == "D-067":
        return {"kidney_weight": ln(rng, 60, 2, .15), "heart_weight": ln(rng, 60, 1.2, .15),
                "body_mass": ln(rng, 60, 300, .15)}
    if cid == "D-050":
        return {"liver_mass": ln(rng, 80, 12, .15), "age_days": ln(rng, 80, 100, .3), "body_mass": ln(rng, 80, 300, .15)}
    if cid == "D-020":
        return {"liver_weight": ln(rng, 1500, 1.5, .15), "heart_weight": ln(rng, 1500, .15, .15),
                "body_mass": ln(rng, 1500, 25, .15)}
    if cid == "D-031":
        return {"offences": ln(rng, 500, 2000, 1), "median_age": ln(rng, 500, 38, .1), "population": ln(rng, 500, 200, 1)}
    if cid == "D-037":
        return {"bmi_baseline": ln(rng, 500, 15, .08), "bmi_followup": ln(rng, 500, 19, .1),
                "bmi_retest": ln(rng, (100, 2), 15, .08)}
    if cid == "D-015":
        return {"bmi_baseline": ln(rng, 500, 15, .08), "bmi_baseline_retest": ln(rng, 500, 15, .08),
                "bmi_followup": ln(rng, 500, 19, .1)}
    if cid == "D-036":
        return {"mean_arterial_pressure": ln(rng, 100, 90, .1), "central_venous_pressure": ln(rng, 100, 8, .2),
                "co_thermodilution": ln(rng, 100, 5, .3), "co_fick": ln(rng, 100, 5, .3)}


# ---------------- direction arrays (claim clearly met / clearly not met) ----------------
def direction(cid, rng, true):
    if cid == "D-040":
        n = 300
        w = rng.normal(0, 1, n)
        g = w if true else rng.normal(0, 1, n)
        return {"breadth": 140 + 5 * rng.normal(0, 1, n) * .5 + 4 * w, "height": 130 + 3 * rng.normal(0, 1, n) * .5 + 4 * g,
                "length": 180 + 8 * rng.normal(0, 1, n)}
    if cid == "D-017":
        n = 600
        sm = rng.random(n) < .3
        h = 170 + 10 * rng.normal(0, 1, n) - 3 * sm
        c = -0.6 if true else 0.0
        return {"fvc": 1.0 + .018 * h + c * sm + rng.normal(0, .3, n), "height": h, "smoker": sm}
    if cid == "D-053":
        n = 500
        t1 = 15 + 1.2 * rng.normal(0, 1, n)
        ch = 2 - 1.0 * (t1 - 15) + .3 * rng.normal(0, 1, n) if true else 2 + rng.normal(0, 1, n)
        return {"bmi_baseline": t1 + .3 * rng.normal(0, 1, n), "bmi_baseline_retest": t1 + .3 * rng.normal(0, 1, n),
                "bmi_followup": t1 + ch + .3 * rng.normal(0, 1, n)}
    if cid == "D-071":
        n = 120
        co = ln(rng, n, 5, .3)
        ca = ln(rng, n, 19, .12)
        do2 = co * ca * 10
        vo2 = (.25 * do2 if true else ln(rng, n, 240, .2)) + rng.normal(0, 10, n)
        cv = ca - vo2 / (10 * co)
        return {"cardiac_output": co, "arterial_o2_content": ca, "venous_o2_content": cv,
                "vo2_expired_gas": vo2 + rng.normal(0, 5, n)}
    if cid == "D-062":
        S, I = 12, 30
        zs = 100 + 8 * rng.normal(0, 1, (S, I))
        w = rng.normal(0, 1, (S, I))
        w2 = w if true else rng.normal(0, 1, (S, I))
        return {"femur": 40 + 3 * w + .5 * rng.normal(0, 1, (S, I)), "humerus": 35 + 3 * w2 + .5 * rng.normal(0, 1, (S, I)),
                "body_length": zs}
    if cid == "D-038":
        n = 150
        pop = ln(rng, n, 40, 1)
        sales = pop * 12 * np.exp(rng.normal(0, .4, n))
        g = 0.01 if true else 0.0
        return {"lung_cancer_deaths": 2 + .3 * pop + g * sales + rng.normal(0, 1, n), "cigarettes_sold": sales,
                "population": pop}
    if cid == "D-006":
        n, m = 500, 6
        b0 = 15 + 1.2 * rng.normal(0, 1, n)
        b1 = (.4 - .12 * (b0 - 15) if true else .4 + 0 * b0) + .1 * rng.normal(0, 1, n)
        t = np.arange(m)
        return {"bmi": b0[:, None] + b1[:, None] * t[None, :] + .3 * rng.normal(0, 1, (n, m))}
    if cid == "D-008":
        n, m = 40, 6
        co = ln(rng, (n, m), 5, .25)
        ca = ln(rng, (n, m), 19, .08)
        do2 = co * ca * 10
        a = rng.normal(100, 30, (n, 1))
        vo2 = a + (.25 if true else 0.0) * do2 + rng.normal(0, 8, (n, m))
        cv = ca - vo2 / (10 * co)
        return {"cardiac_output": co, "arterial_o2_content": ca, "venous_o2_content": cv,
                "vo2_expired_gas": vo2 + rng.normal(0, 4, (n, m))}
    if cid == "D-067":
        n = 60
        body = 300 + 40 * rng.normal(0, 1, n)
        heart = 1.2 + .15 * rng.normal(0, 1, n)
        g = 1.0 if true else 0.0
        return {"kidney_weight": 0.5 + .004 * body + g * heart + .1 * rng.normal(0, 1, n), "heart_weight": heart,
                "body_mass": body}
    if cid == "D-050":
        n = 80
        age = 100 + 20 * rng.normal(0, 1, n)
        body = 150 + 1.5 * age + 15 * rng.normal(0, 1, n)
        g = .15 if true else 0.0
        return {"liver_mass": 2 + .03 * body + g * age + .5 * rng.normal(0, 1, n), "age_days": age, "body_mass": body}
    if cid == "D-020":
        n = 1500
        body = 25 + 3 * rng.normal(0, 1, n)
        heart = .15 + .02 * rng.normal(0, 1, n)
        g = 40.0 if true else 0.0
        return {"liver_weight": .3 + .04 * body + g * heart + .1 * rng.normal(0, 1, n), "heart_weight": heart,
                "body_mass": body}
    if cid == "D-031":
        n = 500
        pop = ln(rng, n, 200, 1)
        age = 38 + 1.5 * np.log(pop / 200) + 2 * rng.normal(0, 1, n)
        g = .08 if true else 0.0
        return {"offences": 5 * pop ** .9 * np.exp(g * age + .1 * rng.normal(0, 1, n)), "median_age": age,
                "population": pop}
    if cid == "D-037":
        n = 500
        t1 = 15 + 1.2 * rng.normal(0, 1, n)
        ch = (2 - .6 * (t1 - 15) if true else 2 + 0 * t1) + .3 * rng.normal(0, 1, n)
        return {"bmi_baseline": t1 + .3 * rng.normal(0, 1, n), "bmi_followup": t1 + ch + .3 * rng.normal(0, 1, n),
                "bmi_retest": 15 + 1.2 * rng.normal(0, 1, (100, 1)) + .3 * rng.normal(0, 1, (100, 2))}
    if cid == "D-015":
        n = 500
        t1 = 15 + 1.2 * rng.normal(0, 1, n)
        ch = 2 - 1.0 * (t1 - 15) + .3 * rng.normal(0, 1, n) if true else 2 + rng.normal(0, 1, n)
        return {"bmi_baseline": t1 + .3 * rng.normal(0, 1, n), "bmi_baseline_retest": t1 + .3 * rng.normal(0, 1, n),
                "bmi_followup": t1 + ch + .3 * rng.normal(0, 1, n)}
    if cid == "D-036":
        n = 100
        co = ln(rng, n, 5, .3)
        svr = (1200 * (5 / co) if true else ln(rng, n, 1200, .3)) * np.exp(.1 * rng.normal(0, 1, n))
        drop = co * svr / 80
        return {"mean_arterial_pressure": 8 + drop, "central_venous_pressure": np.full(n, 8.0) + 0 * drop,
                "co_thermodilution": co * np.exp(.1 * rng.normal(0, 1, n)),
                "co_fick": co * np.exp(.1 * rng.normal(0, 1, n))}


def main():
    cids = sorted(os.listdir(ROOT))
    print("== run 1: smoke ==")
    for cid in cids:
        f = load(cid)
        times = []
        outs = []
        for rep in range(3):
            d = smoke(cid, np.random.default_rng(1000 + rep))
            t0 = time.perf_counter()
            o = f(d)
            times.append(time.perf_counter() - t0)
            outs.append(o)
        print(cid, "types", sorted({type(o).__name__ for o in outs}), "max_time_s %.5f" % max(times))
    print("== run 2: direction ==")
    for cid in cids:
        f = load(cid)
        rt = f(direction(cid, np.random.default_rng(7), True))
        rf = f(direction(cid, np.random.default_rng(8), False))
        print(cid, "claim-met array ->", rt, "| claim-not-met array ->", rf)


if __name__ == "__main__":
    main()
