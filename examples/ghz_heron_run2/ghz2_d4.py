"""ghz2_d4.py -- pre-freeze checks, simulator only (PREREG.md section 1 D-7, section 4 rule 14, section 5 K2, section 8 step 1).

  Budget    : circuit count (expected 368), shot total (expected 736000), rough quantum time on FakeKingston durations.
  K2        : noiseless AerSimulator(method="matrix_product_state") on the exact transpiled circuits from FakeKingston
              (classical registers kept).  F_sim >= 0.98 for every n and C_mix,sim <= 0.05.  2000 shots, fixed seed.
              The Re-phase coherence is printed too (sensitivity I-1; ~1 expected on noiseless GHZ).
  Bit order : positive control (audit F8).  POP_8 gets an X on the LAST data qubit of S_8 before the measurement, and a second
              copy an X on the FIRST data qubit.  Noiseless simulation; the estimator's POP pattern must report P ~ 0 and the
              counts must sit on exactly the two shifted strings (qiskit bit order: leftmost character = highest clbit index).
              A reversed register / bit order would put the mass on the other pair and fail.
  D4        : for H1-H3, "defined / reachable / covered" on synthetic inputs only (never hardware):
                defined   = the criterion returns True/False (not None, no exception) on the synthetic plus and minus worlds
                reachable = both HOLDS and FAILS occur on some synthetic input
                covered   = the criterion is in the Kapi STUDY and is the one ghz2_analyze.py applies
  Rule 14   : on FakeKingston, F_pred + 0.05 < 1 at n = 4 and n = 8 (so H1's band is reachable in both directions).
This is a simulator check, not a result.  The K2 outcome (including the bit-order control) is written to certs/k2_sim.json.
No network, no account.
"""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np
from qiskit_aer import AerSimulator
from qiskit_ibm_runtime.fake_provider import FakeKingston

import ghz2_core as core
import ghz2_study

HERE = os.path.dirname(os.path.abspath(__file__))
SIM_SEED = 20261113
F_SIM_MIN = 0.98
C_MIX_SIM_MAX = 0.05
BIT_ORDER_N = 8
BIT_ORDER_MASS_MIN = 0.99
BIT_ORDER_P_MAX = 0.01


def budget_and_circuits():
    backend = FakeKingston()
    snap, h = core.snapshot_from_backend(backend, utc="D4")
    entries = core.build_all(snap, backend.target)
    shots_total = len(entries) * core.SHOTS
    est, rd, longest = core.estimate_time(entries, backend.target, getattr(backend, "default_rep_delay", None))
    print("== Budget ==")
    print(f"circuits: {len(entries)} (expected {core.EXPECTED_CIRCUITS}): {'OK' if len(entries) == core.EXPECTED_CIRCUITS else 'MISMATCH'}")
    print(f"shot total: {shots_total} (expected {core.EXPECTED_SHOTS}): {'OK' if shots_total == core.EXPECTED_SHOTS else 'MISMATCH'}")
    print(f"rough quantum time (FakeKingston durations, rep_delay {rd * 1e6:.0f} us, longest circuit {longest * 1e6:.2f} us): "
          f"{est:.1f} s = {est / 60:.2f} min ({'within' if est <= core.MAX_QUANTUM_SECONDS else 'EXCEEDS'} the "
          f"{core.MAX_QUANTUM_SECONDS:.0f} s limit)")
    ok = (len(entries) == core.EXPECTED_CIRCUITS and shots_total == core.EXPECTED_SHOTS
          and est <= core.MAX_QUANTUM_SECONDS)
    return backend, snap, entries, ok


def k2(entries):
    print("== K2 (noiseless MPS simulation of the exact transpiled circuits) ==")
    t0 = time.time()
    sim = AerSimulator(method="matrix_product_state")
    circuits = [e["circuit"] for e in entries]
    res = sim.run(circuits, shots=core.SHOTS, seed_simulator=SIM_SEED).result()
    counts = {e["name"]: core.counts_by_register(res.get_counts(i), e["circuit"]) for i, e in enumerate(entries)}
    ok = True
    detail = {"F_sim": {}, "C_mix_sim": {}}
    for n in core.GRID:
        est = core.point_estimates(counts, n, "GHZ")
        good = est["F"] >= F_SIM_MIN
        ok &= good
        detail["F_sim"][str(n)] = est["F"]
        print(f"n={n:<3} F_sim={est['F']:.4f} P={est['P']:.4f} C={est['C']:.4f} C_re={est['C_re']:.4f}  "
              f"{'pass' if good else 'FAIL'} (>= {F_SIM_MIN})")
    for n in core.MIX_NS:
        est = core.point_estimates(counts, n, "MIX")
        good = est["C"] <= C_MIX_SIM_MAX
        ok &= good
        detail["C_mix_sim"][str(n)] = est["C"]
        print(f"MIX n={n:<3} C_mix_sim={est['C']:.4f} F_mix_sim={est['F']:.4f} P={est['P']:.4f}  "
              f"{'pass' if good else 'FAIL'} (<= {C_MIX_SIM_MAX})")
    print(f"K2 estimator fidelity: {'PASS' if ok else 'FAIL'}   (sim time {time.time() - t0:.1f} s; simulator check, not a result)")
    return ok, detail


def expected_pair(n, k):
    """The two data bitstrings (qiskit order, leftmost = clbit n-1) of GHZ_n with an X on logical qubit k."""
    a = "".join("1" if i == k else "0" for i in reversed(range(n)))
    b = "".join("0" if i == k else "1" for i in reversed(range(n)))
    return {a, b}


def bit_order_control(snap, target):
    """POP_8 with an X on the last / the first data qubit before measurement; the estimator's POP pattern must report P ~ 0
    and the counts must be concentrated on exactly the two shifted strings."""
    print("== K2 bit-order positive control (POP_8 with an X before measurement) ==")
    n = BIT_ORDER_N
    S, T, parents = core.selection(snap, n)
    sim = AerSimulator(method="matrix_product_state")
    ok = True
    detail = {}
    pairs = {}
    for label, k in (("last data qubit", n - 1), ("first data qubit", 0)):
        qc = core.build_circuit(n, parents, "POP", flip=(k,))
        tc = core.transpile_checked(qc, n, S, T, target)
        raw = sim.run(tc, shots=core.SHOTS, seed_simulator=SIM_SEED).result().get_counts()
        reg = core.counts_by_register(raw, tc)["meas"]
        n0, n1, no, tot = core.pop_counts(reg, n)
        P = (n0 + n1) / tot
        exp = expected_pair(n, k)
        pairs[label] = exp
        top2 = set(sorted(reg, key=reg.get, reverse=True)[:2])
        mass = sum(reg.get(b, 0) for b in exp) / tot
        good = P <= BIT_ORDER_P_MAX and mass >= BIT_ORDER_MASS_MIN and top2 == exp
        ok &= good
        detail[label] = {"P": P, "mass_on_expected_pair": mass, "expected": sorted(exp), "top2": sorted(top2)}
        print(f"X on {label:<17}: P={P:.4f}  mass on {sorted(exp)} = {mass:.4f}  top2={sorted(top2)}  "
              f"{'pass' if good else 'FAIL'}")
    distinct = pairs["last data qubit"] != pairs["first data qubit"]
    ok &= distinct
    print(f"the two expected pairs differ (a reversed bit order would be detected): {'yes' if distinct else 'NO'}")
    print(f"K2 bit-order control: {'PASS' if ok else 'FAIL'}")
    return ok, detail


def d4():
    """defined / reachable / covered for H1-H3 on synthetic inputs."""
    import ghz2_analyze  # the criteria the analysis applies

    print("== D4 (synthetic inputs only) ==")
    rng_seed = 7
    samples = []
    for i in range(40):
        rng = np.random.default_rng([rng_seed, i])
        samples.append(("plus", ghz2_study.plus_world(rng)))
        samples.append(("minus", ghz2_study.minus_world(rng)))
    in_study = {c.id for c in ghz2_study.STUDY.criteria}
    applied = set(ghz2_analyze.CRITERIA)
    all_ok = True
    for cid, fn in ghz2_analyze.CRITERIA.items():
        outs = []
        for _w, d in samples:
            try:
                outs.append(fn(d))
            except Exception:  # noqa: BLE001
                outs.append("EXC")
        defined = all(o in (True, False) for o in outs)
        reachable = (True in outs) and (False in outs)
        covered = cid in in_study and cid in applied and applied == in_study
        all_ok &= defined and reachable and covered
        print(f"{cid.split('_')[0]}: defined={'yes' if defined else 'NO'} reachable={'yes' if reachable else 'NO'} "
              f"covered={'yes' if covered else 'NO'}")
    return all_ok


def rule14(entries, target):
    model = core.model_all(entries, target)
    ok = all(model[n]["F_pred"] + 0.05 < 1.0 for n in (4, 8))
    print("== Rule 14 (FakeKingston) ==")
    print(f"F_pred(4) = {model[4]['F_pred']:.4f}, F_pred(8) = {model[8]['F_pred']:.4f}; "
          f"F_pred + 0.05 < 1 at n = 4 and 8: {'yes' if ok else 'no'}")
    return ok


def main():
    backend, snap, entries, b_ok = budget_and_circuits()
    k2_main, detail = k2(entries)
    bo_ok, bo_detail = bit_order_control(snap, backend.target)
    k2_ok = bool(k2_main and bo_ok)
    os.makedirs(os.path.join(HERE, "certs"), exist_ok=True)
    with open(os.path.join(HERE, "certs", "k2_sim.json"), "w", encoding="utf-8") as fh:
        json.dump({"pass": k2_ok, "shots": core.SHOTS, "seed": SIM_SEED, "detail": detail,
                   "bit_order_control": {"pass": bool(bo_ok), "detail": bo_detail}}, fh, indent=1)
    d4_ok = d4()
    r14 = rule14(entries, backend.target)
    print(f"SUMMARY: budget={'OK' if b_ok else 'FAIL'} K2={'PASS' if k2_ok else 'FAIL'} D4={'OK' if d4_ok else 'FAIL'} "
          f"rule14={'yes' if r14 else 'no'}")
    return 0 if (b_ok and k2_ok and d4_ok and r14) else 1


if __name__ == "__main__":
    sys.exit(main())
