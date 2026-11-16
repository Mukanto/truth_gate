#!/usr/bin/env python
"""Independent recomputation of the main numbers of GHZ run 3.

Written from the specifications only (run 3 PREREG, run 2 PREREG sections 2-3, run 1 PREREG
sections 3-4) and the raw files of run 3's run/ folder. It does not import or read any of the
study's analysis/run/core code and never touches RESULTS_GHZ3.*.

Run:  E:/Claude Projects/.venv-qiskit/Scripts/python.exe -I recompute_run3.py
Needs numpy; qiskit is used only for the (optional) circuit/phase identification check.
"""
import json
import math
import sys
from pathlib import Path

import numpy as np

BASE = Path(__file__).resolve().parents[1]          # .../examples
RUN3 = BASE / "ghz_heron_run3" / "run"
RUN2 = BASE / "ghz_heron_run2"
RUN1 = BASE / "ghz_heron"

GRID = [4, 8, 16, 24, 32, 48]
SHOTS = 2000
B = 2000
SEED = 20261117        # my own seed (the study's is 20261113); chosen arbitrarily


def load(p):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def hdr(t):
    print("\n" + "=" * 100 + "\n" + t + "\n" + "=" * 100)


# --------------------------------------------------------------------------------------
# 0. Circuit identification
# --------------------------------------------------------------------------------------
counts = load(RUN3 / "counts.json")
job = load(RUN3 / "job.json")
model3 = load(RUN3 / "model.json")
model2 = load(RUN2 / "run" / "model.json")
circ = counts["circuits"]

hdr("0. CIRCUIT IDENTIFICATION")
manifest = job["manifest"]
# manifest entry: {index, name, family (GHZ|MIX), n, kind (POP|PAR), j (None | 0..2n+1)}
assert [m["name"] for m in manifest] == counts["order"], "manifest order != counts order"
assert set(m["name"] for m in manifest) == set(circ), "manifest names != counts keys"
assert counts["shots"] == SHOTS
by = {}   # (family, n) -> {"POP": name, "PAR": {j: name}}
for m in manifest:
    d = by.setdefault((m["family"], m["n"]), {"POP": None, "PAR": {}})
    if m["kind"] == "POP":
        d["POP"] = m["name"]
    else:
        d["PAR"][m["j"]] = m["name"]
for (fam, n), d in sorted(by.items()):
    js = sorted(d["PAR"])
    assert js == list(range(2 * n + 2)), (fam, n, "PAR j set")
    # every circuit: 'meas' register length n, total counts == shots
    for nm in [d["POP"]] + [d["PAR"][j] for j in js]:
        meas = circ[nm]["meas"]
        assert all(len(k) == n for k in meas), (nm, "bit-string length")
        assert sum(meas.values()) == SHOTS, (nm, "total counts")
        if fam == "MIX":
            assert sum(circ[nm]["mid"].values()) == SHOTS
    print(f"{fam:3s} n={n:2d}: 1 POP + {len(js)} PAR (j=0..{js[-1]}), 'meas' bit-strings length n, totals == {SHOTS}"
          + ("  [+ 'mid' register = mid-circuit root bit, ignored]" if fam == "MIX" else ""))
print(f"total circuits: {len(manifest)} (expected 368 = 6+276 GHZ + 2+84 MIX)")
print("identification rule: circuit names GHZ<n>_POP / GHZ<n>_PAR<j> / MIX<n>_POP / MIX<n>_PAR<j> in counts.json,\n"
      "  cross-checked against job.json['manifest'] (family, n, kind, j) and the order of circuits.qpy.")

# --- phases from circuits.qpy (optional) ---------------------------------------------
PHASE_REPORT = []
try:
    from qiskit import qpy
    from qiskit.quantum_info import Statevector
    from qiskit import QuantumCircuit

    with open(RUN3 / "circuits.qpy", "rb") as f:
        qcs = qpy.load(f)
    names = [c.name for c in qcs]
    assert names == counts["order"], "qpy order != counts order"
    qc_by = dict(zip(names, qcs))

    def two_pi_mod(x):
        return (x + math.pi) % (2 * math.pi) - math.pi

    # Root qubit = S_n[0].  Its last gates are  rz(pi/2 - phi), sx, rz(pi/2)  (= H . Rz(-phi) up to phase).
    bad = 0
    nchk = 0
    for (fam, n), d in sorted(by.items()):
        root = model3["components"][str(n)]["S"][0] if str(n) in model3["components"] else \
            model3["components"]["48"]["S"][0]
        for j, nm in d["PAR"].items():
            c = qc_by[nm]
            ops = [(i.operation.name, [c.find_bit(q).index for q in i.qubits], i.operation.params) for i in c.data]
            rootops = [(o, p) for o, qs, p in ops if qs == [root] and o in ("rz", "sx")]
            # find last 'sx' on the root, take the rz right before it
            k = max(i for i, (o, _) in enumerate(rootops) if o == "sx")
            a = float(rootops[k - 1][1][0])
            phi = two_pi_mod(math.pi / 2 - a)
            want = two_pi_mod(j * math.pi / (n + 1))
            nchk += 1
            if abs(two_pi_mod(phi - want)) > 1e-9:
                bad += 1
    print(f"phase check from circuits.qpy (root qubit, last rz before final sx, phi = pi/2 - angle): "
          f"{nchk} PAR circuits, mismatches vs phi_j = j*pi/(n+1): {bad}")

    # Ideal (noiseless) statevector check of the parity convention for n = 4 and 8
    for n in (4, 8):
        S = model3["components"][str(n)]["S"]
        idx = {q: i for i, q in enumerate(S)}
        worst = 0.0
        worst_neg = 0.0
        for j, nm in by[("GHZ", n)]["PAR"].items():
            c = qc_by[nm]
            sub = QuantumCircuit(n)
            for ins in c.data:
                o = ins.operation.name
                if o in ("measure", "barrier"):
                    continue
                qs = [idx[c.find_bit(q).index] for q in ins.qubits]
                sub.append(ins.operation, qs)
            pr = Statevector.from_instruction(sub).probabilities()
            sign = np.array([(-1) ** bin(i).count("1") for i in range(2 ** n)])
            par = float(pr @ sign)
            phi = j * math.pi / (n + 1)
            worst = max(worst, abs(par - math.cos(n * phi)))
            worst_neg = max(worst_neg, abs(par + math.cos(n * phi)))
        print(f"ideal GHZ{n}: max|parity_ideal - cos(n*phi_j)| = {worst:.2e}   (vs -cos: {worst_neg:.2e})")
        PHASE_REPORT.append((n, worst))
except Exception as e:  # qiskit unavailable or something unexpected: not needed for the numbers
    print("qpy-based check skipped/failed:", repr(e))

# --------------------------------------------------------------------------------------
# 1. Point estimates
# --------------------------------------------------------------------------------------
def pop_counts(name):
    meas = circ[name]["meas"]
    n = len(next(iter(meas)))
    return meas.get("0" * n, 0) + meas.get("1" * n, 0)


def odd_counts(name):
    meas = circ[name]["meas"]
    return sum(v for k, v in meas.items() if k.count("1") % 2 == 1)


def phases(n):
    return np.arange(2 * n + 2) * math.pi / (n + 1)


def estimators_from(N01, odd, n):
    """N01 scalar or (B,), odd (..., 2n+2) -> P, C(|.|), C_re."""
    parity = 1.0 - 2.0 * np.asarray(odd) / SHOTS
    z = parity @ np.exp(1j * n * phases(n))
    C = (2.0 / (2 * n + 2)) * np.abs(z)
    Cre = (2.0 / (2 * n + 2)) * np.real(z)
    return np.asarray(N01) / SHOTS, C, Cre


data = {}   # (fam, n) -> dict
for (fam, n), d in by.items():
    N01 = pop_counts(d["POP"])
    odd = np.array([odd_counts(d["PAR"][j]) for j in range(2 * n + 2)])
    P, C, Cre = estimators_from(N01, odd, n)
    data[(fam, n)] = dict(N01=N01, odd=odd, P=float(P), C=float(C), Cre=float(Cre), F=float((P + C) / 2),
                          parity=1 - 2 * odd / SHOTS)

# --------------------------------------------------------------------------------------
# 2. M2 predictions from the components
# --------------------------------------------------------------------------------------
def m2(comp):
    """M2 (run 2 PREREG section 3). All components are per-n lists from model.json."""
    cz = np.array(comp["cz_err"])
    g_pop = np.prod(1 - np.array(comp["g1_pop_err"]))
    g_par = np.prod(1 - np.array(comp["g1_par_err"]))
    ro = np.array(comp["ro_err"])
    t1 = np.array(comp["t1"])
    t2 = np.array(comp["t2"])
    idle = np.array(comp["idle"])
    n = len(comp["S"])
    assert len(cz) == n - 1 and len(ro) == n and len(t1) == n and len(t2) == n and len(idle) == n
    tree = np.prod(1 - cz)
    P = tree * g_pop * np.prod(1 - ro) * 0.5 * (1 + np.prod(np.exp(-idle / t1)))
    C = tree * g_par * np.prod(1 - 2 * ro) * np.prod(np.exp(-idle / t2))
    return float(P), float(C), float((P + C) / 2)


pred3 = {n: m2(model3["components"][str(n)]) for n in GRID}
pred2 = {n: m2(model2["components"][str(n)]) for n in GRID}
P_pred = np.array([pred3[n][0] for n in GRID])
C_pred = np.array([pred3[n][1] for n in GRID])
F_pred = np.array([pred3[n][2] for n in GRID])

hdr("2. M2 PREDICTIONS (computed here from run/model.json components)")
mx = {"P": 0.0, "C": 0.0, "F": 0.0}
for n in GRID:
    comp = model3["components"][str(n)]
    p, c, f = pred3[n]
    mx["P"] = max(mx["P"], abs(p - comp["P_pred"]))
    mx["C"] = max(mx["C"], abs(c - comp["C_pred"]))
    mx["F"] = max(mx["F"], abs(f - comp["F_pred"]))
    print(f"n={n:2d}  P_pred={p:.6f}  C_pred={c:.6f}  F_pred={f:.6f}   (model.json: {comp['P_pred']:.6f} {comp['C_pred']:.6f} {comp['F_pred']:.6f})")
print(f"max |mine - model.json fields|: P {mx['P']:.3e}  C {mx['C']:.3e}  F {mx['F']:.3e}")

# --------------------------------------------------------------------------------------
# 3. Bootstrap
# --------------------------------------------------------------------------------------
# Each circuit's counts are resampled multinomially (2000 shots).  P depends on the circuit's
# outcomes only through the category {all-0, all-1} vs the rest, and each parity on the
# even/odd category, so lumping the categories gives exactly the same joint distribution of the
# statistics as resampling all observed bit-strings: P ~ Binomial(2000, N01/2000), each
# odd_j ~ Binomial(2000, odd_j/2000), all independent (circuits are independent).
rng = np.random.default_rng(SEED)
boot = {}
for key in sorted(by):
    fam, n = key
    d = data[key]
    N01b = rng.binomial(SHOTS, d["N01"] / SHOTS, size=B)
    oddb = rng.binomial(SHOTS, d["odd"] / SHOTS, size=(B, 2 * n + 2))
    Pb, Cb, Creb = estimators_from(N01b, oddb, n)
    boot[key] = dict(P=Pb, C=Cb, Cre=Creb, F=(Pb + Cb) / 2)


def ci(x):
    return np.percentile(x, [2.5, 97.5])


# sanity: true multinomial over the observed bit-strings for n = 4, 8 gives the same spread
def full_multinomial_sd(n, reps=1000):
    r = np.random.default_rng(SEED + 1)
    d = by[("GHZ", n)]
    pops = circ[d["POP"]]["meas"]
    keys = list(pops)
    p0 = np.array([pops[k] for k in keys]) / SHOTS
    is01 = np.array([k in ("0" * n, "1" * n) for k in keys])
    out = []
    pars = []
    for j in range(2 * n + 2):
        m = circ[d["PAR"][j]]["meas"]
        ks = list(m)
        pars.append((np.array([m[k] for k in ks]) / SHOTS, np.array([k.count("1") % 2 for k in ks])))
    for _ in range(reps):
        N01 = r.multinomial(SHOTS, p0)[is01].sum()
        odd = np.array([r.multinomial(SHOTS, pp)[od == 1].sum() for pp, od in pars])
        P, C, _c = estimators_from(N01, odd, n)
        out.append((P + C) / 2)
    return float(np.std(out))


hdr("3. BOOTSTRAP (own implementation)")
print(f"B = {B}, numpy default_rng seed = {SEED}, joint per n: POP + all PAR circuits resampled independently "
      f"(2000-shot multinomial, categories lumped as explained in the code)")
for n in (4, 8):
    print(f"  check n={n}: sd(F_boot) lumped = {np.std(boot[('GHZ', n)]['F']):.5f}   "
          f"full multinomial over observed bit-strings (1000 reps) = {full_multinomial_sd(n):.5f}")

# --------------------------------------------------------------------------------------
# 1 (print). Fidelity table
# --------------------------------------------------------------------------------------
hdr("1. P, C, F per n (GHZ circuits)  [95% percentile CI from my bootstrap]")
P_hat = np.array([data[("GHZ", n)]["P"] for n in GRID])
C_hat = np.array([data[("GHZ", n)]["C"] for n in GRID])
F_hat = np.array([data[("GHZ", n)]["F"] for n in GRID])
Cre_hat = np.array([data[("GHZ", n)]["Cre"] for n in GRID])
Pb = np.stack([boot[("GHZ", n)]["P"] for n in GRID], 1)
Cb = np.stack([boot[("GHZ", n)]["C"] for n in GRID], 1)
Fb = np.stack([boot[("GHZ", n)]["F"] for n in GRID], 1)
Creb = np.stack([boot[("GHZ", n)]["Cre"] for n in GRID], 1)
print(f"{'n':>3} {'P':>8} {'P CI':>19} {'C':>8} {'C CI':>19} {'F':>8} {'F CI':>19} {'C(Re)':>8} {'C(Re) CI':>19}")
for i, n in enumerate(GRID):
    pc, cc_, fc, rc = ci(Pb[:, i]), ci(Cb[:, i]), ci(Fb[:, i]), ci(Creb[:, i])
    print(f"{n:>3} {P_hat[i]:8.4f} [{pc[0]:.4f},{pc[1]:.4f}] {C_hat[i]:8.4f} [{cc_[0]:.4f},{cc_[1]:.4f}] "
          f"{F_hat[i]:8.4f} [{fc[0]:.4f},{fc[1]:.4f}] {Cre_hat[i]:8.4f} [{rc[0]:.4f},{rc[1]:.4f}]")
print("\nraw ingredients: N(0^n)+N(1^n), and parities j=0..2n+1 (first 6 shown)")
for n in GRID:
    d = data[("GHZ", n)]
    print(f"  n={n:2d}: N01={d['N01']:4d}/2000  parity[:6]={np.round(d['parity'][:6], 4).tolist()}")

hdr("PREDICTIONS IN USE vs MEASURED, R(n) = F/F_pred")
print(f"{'n':>3} {'P_pred':>8} {'C_pred':>8} {'F_pred':>8} {'F_hat':>8} {'R':>7}  R 95% CI (boot, F_boot/F_pred)")
R3 = F_hat / F_pred
for i, n in enumerate(GRID):
    r = ci(Fb[:, i] / F_pred[i])
    print(f"{n:>3} {P_pred[i]:8.4f} {C_pred[i]:8.4f} {F_pred[i]:8.4f} {F_hat[i]:8.4f} {R3[i]:7.4f}  [{r[0]:.4f},{r[1]:.4f}]")

# --------------------------------------------------------------------------------------
# 4. Criteria
# --------------------------------------------------------------------------------------
hdr("4. CRITERIA (run 3 PREREG section 4)")
ix = {n: i for i, n in enumerate(GRID)}

# H1
if any(not (0 < F_pred[ix[n]] < 1) for n in (4, 8)):
    h1 = "UNDEFINED"
else:
    dev = {n: abs(F_hat[ix[n]] - F_pred[ix[n]]) for n in (4, 8)}
    h1 = "HOLDS" if all(v <= 0.05 for v in dev.values()) else "FAILS"
print(f"H1  |F_hat - F_pred|: n=4: {abs(F_hat[0]-F_pred[0]):.4f}   n=8: {abs(F_hat[1]-F_pred[1]):.4f}   (band 0.05)  -> {h1}")
print(f"    rule-14 check: F_pred+0.05<1 at n=4: {F_pred[0]+0.05<1}, n=8: {F_pred[1]+0.05<1}")


# H4
def verdict_h4():
    if np.any(~((F_pred > 0) & (F_pred < 1))) or np.any(Fb <= 0):
        return "UNDEFINED", None
    q = np.percentile(Fb / F_pred, 97.5, axis=0)
    return ("HOLDS" if np.all(q < 1) else "FAILS"), q


h4, q4 = verdict_h4()
print("H4  q97.5 of F_boot/F_pred per n: " + "  ".join(f"n={n}: {q4[i]:.4f}" for i, n in enumerate(GRID)))
print(f"    max over n = {q4.max():.4f}  (must be < 1 at every n)  margins 1-q: "
      + " ".join(f"{1-q4[i]:+.4f}" for i in range(6)) + f"   -> {h4}")

# H2
n_meas = max([n for n in GRID if F_hat[ix[n]] > 0.5], default=0)
n_pred = max([n for n in GRID if F_pred[ix[n]] > 0.5], default=0)
if n_pred == 0 or np.any(~((F_pred > 0) & (F_pred < 1))):
    h2 = "UNDEFINED"
else:
    h2 = "HOLDS" if n_meas == n_pred else "FAILS"
print(f"H2  n_meas (F_hat>0.5) = {n_meas}   n_pred (F_pred>0.5) = {n_pred}   -> {h2}")
lo = np.percentile(Fb, 2.5, axis=0)
print(f"    CI-based reach (largest n with F CI_low > 0.5): {max([n for n in GRID if lo[ix[n]] > 0.5], default=0)}   "
      f"(F_hat(24)={F_hat[ix[24]]:.4f}, F_pred(24)={F_pred[ix[24]]:.4f})")

# H3
Pb_ok = np.all(Pb[:, [ix[32], ix[48]]] > 0) and np.all(Cb[:, [ix[32], ix[48]]] > 0)
if not Pb_ok or np.any(P_pred[[ix[32], ix[48]]] <= 0) or np.any(C_pred[[ix[32], ix[48]]] <= 0):
    h3 = "UNDEFINED"
    q3 = {}
else:
    q3 = {}
    for n in (32, 48):
        i = ix[n]
        stat = np.log(Pb[:, i] / P_pred[i]) - np.log(Cb[:, i] / C_pred[i])
        q3[n] = float(np.percentile(stat, 97.5))
    h3 = "HOLDS" if all(v < 0 for v in q3.values()) else "FAILS"
for n, v in q3.items():
    i = ix[n]
    pt = math.log(P_hat[i] / P_pred[i]) - math.log(C_hat[i] / C_pred[i])
    print(f"H3  n={n}: point ln(P/P_pred) - ln(C/C_pred) = {pt:+.4f}   q97.5 of boot = {v:+.4f}")
print(f"    -> {h3}   (<0 required at both n)")

print("\nVERDICTS:  H1 =", h1, " H4 =", h4, " H2 =", h2, " H3 =", h3)
print("(readings 'fails' vs 'not demonstrated' and 'within drift' depend on power/drift files; not recomputed here)")

# --------------------------------------------------------------------------------------
# 5. R table and C-1
# --------------------------------------------------------------------------------------
hdr("5. R(n) = F/F_pred, runs side by side (descriptive); C-1")
r2 = load(RUN2 / "RESULTS_GHZ2.json")
r1 = load(RUN1 / "RESULTS_GHZ.json")
R2 = {t["n"]: t["R"] for t in r2["table"]}
R1 = {t["n"]: t["R"] for t in r1["table"]}
print(f"{'n':>3} {'run1 R (stored; run-1 model M)':>32} {'run2 R (stored)':>16} {'run3 R (mine)':>14}")
for i, n in enumerate(GRID):
    a = f"{R1[n]:.4f}" if n in R1 else "   -"
    b = f"{R2[n]:.4f}" if n in R2 else "   -"
    print(f"{n:>3} {a:>32} {b:>16} {R3[i]:14.4f}")

F2 = np.array([pred2[n][2] for n in GRID])
dF = F_pred - F2
print("\nC-1: M2 inputs of the n=48 component, run 3 vs run 2 (relative tolerance 1e-6, elementwise):")
c48a, c48b = model3["components"]["48"], model2["components"]["48"]
changed = []
for k in ("S", "cz_err", "g1_pop_err", "g1_par_err", "ro_err", "t1", "t2", "idle"):
    a, b = np.array(c48a[k], dtype=float), np.array(c48b[k], dtype=float)
    if a.shape != b.shape:
        nd, ch = max(a.size, b.size), True
    else:
        nd = int(np.sum(~np.isclose(a, b, rtol=1e-6, atol=0.0)))
        ch = nd > 0
    changed.append(ch)
    print(f"  {k:11s} differing elements: {nd:3d} / {a.size}  -> {'CHANGED' if ch else 'same'}")
device_differs = r2["backend"] != counts["backend"]
print(f"  device run 2: {r2['backend']}, run 3: {counts['backend']}; inputs changed: {sum(changed)} of 8")
print(f"{'n':>3} {'F_pred run3':>12} {'F_pred run2':>12} {'dF_pred':>10}")
for i, n in enumerate(GRID):
    print(f"{n:>3} {F_pred[i]:12.6f} {F2[i]:12.6f} {dF[i]:+10.6f}")
mx_all = float(np.max(np.abs(dF)))
mx_48 = float(max(abs(dF[0]), abs(dF[1])))
cond_a = device_differs or any(changed)
cond_b = mx_all >= 0.02
print(f"max_n |dF_pred| = {mx_all:.6f}   max over n=4,8 = {mx_48:.6f}   threshold 0.02")
print(f"C-1: (a) device/input differs = {cond_a}; (b) max|dF| >= 0.02 = {cond_b}  -> C-1 {'HOLDS' if cond_a and cond_b else 'FAILS'};"
      f"  Q1 is a model test (max over n=4,8 >= 0.02): {mx_48 >= 0.02}")
cc = load(RUN3 / "calibration_check.json")
print(f"(compare run/calibration_check.json: max_abs_delta_F_pred = {cc['max_abs_delta_F_pred']:.12f}, "
      f"q1 = {cc['q1_max_abs_delta_F_pred_4_8']:.12f}, n_inputs_changed = {cc['n_inputs_changed']}; "
      f"mine: {mx_all:.12f}, {mx_48:.12f}, {sum(changed)})")

# --------------------------------------------------------------------------------------
# 6. K1
# --------------------------------------------------------------------------------------
hdr("6. K1 (MIX controls): C_mix point and 97.5th percentile of its bootstrap (<= 0.05 passes)")
k1_ok = True
for n in (8, 32):
    d, bt = data[("MIX", n)], boot[("MIX", n)]
    q = float(np.percentile(bt["C"], 97.5))
    ok = q <= 0.05
    k1_ok &= ok
    print(f"MIX_{n}: P_mix = {d['P']:.4f}   C_mix = {d['C']:.5f}   q97.5(C_mix_boot) = {q:.5f}   -> {'pass' if ok else 'FAIL'}")
print("K1:", "PASS" if k1_ok else "FAIL")

# --------------------------------------------------------------------------------------
# 7. Crossing of F = 0.5
# --------------------------------------------------------------------------------------
hdr("7. Interpolated crossing of F = 0.5 (linear in n between grid points)")
grid = np.array(GRID, float)


def crossing(F):
    idxs = [i for i in range(6) if F[i] > 0.5]
    if not idxs:
        return float("nan")
    i = max(idxs)
    if i == 5:
        return float("inf")
    return float(grid[i] + (F[i] - 0.5) / (F[i] - F[i + 1]) * (grid[i + 1] - grid[i]))


x_hat = crossing(F_hat)
x_pred = crossing(F_pred)
xb = np.array([crossing(r) for r in Fb])
fin = xb[np.isfinite(xb)]
_i = max(i for i in range(6) if F_hat[i] > 0.5)
print(f"measured F: crossing at n = {x_hat:.3f}   (between n={GRID[_i]} F={F_hat[_i]:.4f} "
      f"and n={GRID[_i + 1]} F={F_hat[_i + 1]:.4f})")
print(f"predicted F: crossing at n = {x_pred:.3f}")
print(f"bootstrap crossing: {fin.size}/{xb.size} finite replicates; 95% interval [{np.percentile(fin, 2.5):.2f}, {np.percentile(fin, 97.5):.2f}]"
      f"; median {np.median(fin):.2f}")
print("  (definition per replicate: largest grid n with F>0.5, linear interpolation to the next grid point)")

# --------------------------------------------------------------------------------------
# 8. Execution-time calibration check of 3 (lightweight, S_48 inputs only)
# --------------------------------------------------------------------------------------
hdr("8. Execution-time calibration (PREREG section 3), lightweight recheck of the S_48 inputs")
ex = load(RUN3 / "execution_calibration_20261116T112310Z.json")
sub = load(RUN3 / "snapshot_ibm_kingston_20261116T111730Z.json")["snapshot"]
S48 = model3["components"]["48"]["S"]
Sset = set(S48)


def cmp_snap(a, b):
    n_bad, n_cmp = 0, 0
    for q in S48:
        qa, qb = a["qubits"][q], b["qubits"][q]
        vals = [(qa["t1"], qb["t1"]), (qa["t2"], qb["t2"]),
                (qa["measure"]["error"], qb["measure"]["error"]), (qa["measure"]["duration"], qb["measure"]["duration"]),
                (qa["sx"]["error"], qb["sx"]["error"]), (qa["sx"]["duration"], qb["sx"]["duration"])]
        for x, y in vals:
            n_cmp += 1
            n_bad += not math.isclose(x, y, rel_tol=1e-6, abs_tol=0.0)
    ea = {(e[0], e[1]): (e[2], e[3]) for e in a["edges"] if e[0] in Sset and e[1] in Sset}
    eb = {(e[0], e[1]): (e[2], e[3]) for e in b["edges"] if e[0] in Sset and e[1] in Sset}
    assert ea.keys() == eb.keys()
    for k in ea:
        for x, y in zip(ea[k], eb[k]):
            n_cmp += 1
            n_bad += not math.isclose(x, y, rel_tol=1e-6, abs_tol=0.0)
    return n_bad, n_cmp


def max_date(dates):
    ds = []
    for q in S48:
        qd = dates["qubits"][str(q)]
        ds += [qd["T1"], qd["T2"], qd["readout_error"]]
    for g in dates["gates"]:
        if g["gate"] in ("sx", "x", "cz", "rz", "measure") and all(x in Sset for x in g["qubits"]):
            ds.append(g["date"])
    return max(ds)


print(f"submission snapshot utc {job['submitted_utc']}; job running from {ex['execution_start_utc']}; "
      f"current-calibration fetch {ex['current']['retrieved_utc']}")
for label, snap, dates in (("execution-time snapshot (top-level 'snapshot')", ex["snapshot"], ex["dates"]),
                           ("current calibration at fetch ('current')", ex["current"]["snapshot"], ex["current"]["dates"])):
    nb, nc = cmp_snap(sub, snap)
    print(f"  {label}: values differing from submission snapshot: {nb}/{nc}; latest M2-input calibration date: {max_date(dates)}")
print("  => if 0 differ and all dates precede submission (2026-11-16T11:17:30Z), the snapshot's predictions are the ones in use.")

# --------------------------------------------------------------------------------------
hdr("SUMMARY")
print("Verdicts: H1 =", h1, "| H4 =", h4, "| H2 =", h2, "| H3 =", h3, "| K1 =", "PASS" if k1_ok else "FAIL",
      "| C-1 =", "HOLDS" if cond_a and cond_b else "FAILS")
