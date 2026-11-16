"""ghz3_d4.py -- pre-freeze checks, simulator and run-1 and run-2 data only (PREREG.md run 3: section 1 D-7, section 4 rule 14 and power,
section 5 K2, section 8 step 1).  Derived from ghz2_d4.py.

  Budget    : circuit count (expected 368), shot total (expected 736000), rough quantum time on FakeKingston durations.
  K2        : noiseless AerSimulator(method="matrix_product_state") on the exact transpiled circuits from FakeKingston
              (classical registers kept).  F_sim >= 0.98 for every n and C_mix,sim <= 0.05.  2000 shots, fixed seed.
              The Re-phase coherence is printed too (sensitivity I-1; ~1 expected on noiseless GHZ).
  Bit order : positive control kept as in run 2 (uninformative for P and C, which are invariant under bit permutations; kept
              because this file stays as close to ghz2_d4.py as possible).  POP_8 gets an X on the LAST / FIRST data qubit.
              Reported in certs/k2_sim.json; NOT part of K2's pass condition (PREREG v3 section 5).
              This K2 is the DESIGN CHECK on FakeKingston's circuits; the binding K2 runs in the analysis on run/circuits.qpy.
  D4        : for H1-H4, "defined / reachable / covered" on synthetic inputs only (never hardware):
                defined   = the criterion returns True/False (not None, no exception) on the synthetic plus and minus worlds
                reachable = both HOLDS and FAILS occur on some synthetic input
                covered   = the criterion is in a Truth_Gate STUDY (H1-H3: ghz2_study.py, H4: ghz3_study_h4.py) and is the one
                            ghz3_analyze.py applies, and the analysis applies no criterion that is in no study
  Rule 14   : on FakeKingston, F_pred + 0.05 < 1 at n = 4 and n = 8 (H1's band is reachable in both directions), and every
              F_pred lies in (0, 1) (H4: F_boot/F_pred can exceed 1, so H4 can fail).
  Power     : PREREG v3 section 4 (rule 16), written to certs/power.json: the SAME function as --submit uses
              (ghz3_run.compute_power), on run 2's snapshot and M2 predictions as a design-time stand-in; offline, deterministic
              seed, only run-1 and run-2 data files.  Not used to read the result (the analysis reads run/power_run3.json).
This is a simulator check, not a result.  The K2 outcome is written to certs/k2_sim.json.  No network, no account.
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
import ghz3_run
import ghz3_study_h4

HERE = os.path.dirname(os.path.abspath(__file__))
RUN1_DIR = os.path.normpath(os.path.join(HERE, "..", "ghz_heron"))
RUN2_DIR = os.path.normpath(os.path.join(HERE, "..", "ghz_heron_run2"))
SIM_SEED = 20261113
F_SIM_MIN = 0.98
C_MIX_SIM_MAX = 0.05
BIT_ORDER_N = 8
BIT_ORDER_MASS_MIN = 0.99
BIT_ORDER_P_MAX = 0.01

POWER_SEED = 20261116
POWER_DATASETS = 2000
POWER_MIN = 0.8


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
    and the counts must be concentrated on exactly the two shifted strings (kept from run 2; uninformative for P and C)."""
    print("== K2 bit-order positive control (POP_8 with an X before measurement; kept, reported as uninformative) ==")
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
    """defined / reachable / covered for H1-H4 on synthetic inputs."""
    import ghz3_analyze  # the criteria the analysis applies

    print("== D4 (synthetic inputs only) ==")
    rng_seed = 7
    worlds = {}
    for i in range(40):
        rng = np.random.default_rng([rng_seed, i])
        worlds.setdefault("ghz2", []).extend([("plus", ghz2_study.plus_world(rng)), ("minus", ghz2_study.minus_world(rng))])
        rng = np.random.default_rng([rng_seed, i])
        worlds.setdefault("ghz3", []).extend([("plus", ghz3_study_h4.plus_world(rng)), ("minus", ghz3_study_h4.minus_world(rng))])
    studies = {"ghz2": ghz2_study.STUDY, "ghz3": ghz3_study_h4.STUDY}
    in_study = {c.id: k for k, s in studies.items() for c in s.criteria}
    applied = set(ghz3_analyze.CRITERIA)
    all_ok = True
    for cid, fn in ghz3_analyze.CRITERIA.items():
        key = in_study.get(cid)
        samples = worlds[key] if key else []
        outs = []
        for _w, d in samples:
            try:
                outs.append(fn(d))
            except Exception:  # noqa: BLE001
                outs.append("EXC")
        defined = bool(samples) and all(o in (True, False) for o in outs)
        reachable = (True in outs) and (False in outs)
        covered = key is not None and cid in applied and applied == set(in_study)
        all_ok &= defined and reachable and covered
        print(f"{cid.split('_')[0]}: defined={'yes' if defined else 'NO'} reachable={'yes' if reachable else 'NO'} "
              f"covered={'yes' if covered else 'NO'}")
    return all_ok


def rule14(entries, target):
    model = core.model_all(entries, target)
    ok = all(model[n]["F_pred"] + 0.05 < 1.0 for n in (4, 8))
    inside = all(0.0 < model[n]["F_pred"] < 1.0 for n in core.GRID)
    print("== Rule 14 (FakeKingston) ==")
    print(f"F_pred(4) = {model[4]['F_pred']:.4f}, F_pred(8) = {model[8]['F_pred']:.4f}; "
          f"F_pred + 0.05 < 1 at n = 4 and 8: {'yes' if ok else 'no'}")
    print(f"every F_pred in (0, 1) (H4: F_boot/F_pred can exceed 1): {'yes' if inside else 'no'}")
    return bool(ok and inside)


# ------------------------------------------------------------------------------------------------------------- power
def power():
    """certs/power.json: ghz3_run.compute_power on run 2's M2 predictions (design-time stand-in), same method as at submission."""
    return ghz3_run.design_time_power(RUN1_DIR, RUN2_DIR, HERE, POWER_DATASETS, POWER_SEED)


def power_report(pw):
    print("== Power (PREREG v3 section 4, rule 16; design-time stand-in on run 2's snapshot; "
          f"{pw['n_datasets']} datasets, seed {pw['seed']}) ==")
    print(f"drift sigma_rel: P {pw['sigma_rel']['P']:.4f}, C {pw['sigma_rel']['C']:.4f}")
    print(f"power of H1 (truth F_pred - 0.03 at n = 4, 8): {pw['power']['H1']:.3f}   power of H4 (run-2 ratios): {pw['power']['H4']:.3f}")
    print("expected outcome under run-2 ratios (not power):")
    for cid, v in pw["expected_outcome"].items():
        print(f"  {cid.split('_')[0]}: P(HOLDS)={v['P_HOLDS']:.3f}  P(FAILS)={v['P_FAILS']:.3f}  P(UNDEFINED)={v['P_UNDEFINED']:.3f}")
    for m, v in pw["sensitivity"].items():
        print(f"sensitivity {m}: power H1 {v['power_H1']:.3f}, power H4 {v['power_H4']:.3f}")


def main():
    backend, snap, entries, b_ok = budget_and_circuits()
    k2_main, detail = k2(entries)
    bo_ok, bo_detail = bit_order_control(snap, backend.target)
    k2_ok = bool(k2_main)               # PREREG v3 section 5: the bit-order control is reported, not part of K2's pass condition
    os.makedirs(os.path.join(HERE, "certs"), exist_ok=True)
    with open(os.path.join(HERE, "certs", "k2_sim.json"), "w", encoding="utf-8") as fh:
        json.dump({"pass": k2_ok, "shots": core.SHOTS, "seed": SIM_SEED, "detail": detail,
                   "bit_order_control": {"pass": bool(bo_ok), "detail": bo_detail,
                                         "note": "reported only, not part of K2's pass condition; uninformative: P and C are "
                                                 "invariant under bit permutations"}},
                  fh, indent=1)
    d4_ok = d4()
    r14 = rule14(entries, backend.target)
    pw = power()
    with open(os.path.join(HERE, "certs", "power.json"), "w", encoding="utf-8") as fh:
        json.dump(pw, fh, indent=1)
    power_report(pw)
    print(f"SUMMARY: budget={'OK' if b_ok else 'FAIL'} K2={'PASS' if k2_ok else 'FAIL'} (bit-order control "
          f"{'pass' if bo_ok else 'FAIL'}, reported only) D4={'OK' if d4_ok else 'FAIL'} "
          f"rule14={'yes' if r14 else 'no'}; wrote certs/k2_sim.json and certs/power.json")
    return 0 if (b_ok and k2_ok and d4_ok and r14) else 1


if __name__ == "__main__":
    sys.exit(main())
