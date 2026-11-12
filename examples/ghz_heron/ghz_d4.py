"""ghz_d4.py -- pre-freeze checks, simulator only (PREREG.md sections 3 D-7, 7 K2, 10 step 1; protocol D4).

  Budget : circuit count (expected 317), shot total (expected 634000), rough quantum time on FakeKingston durations.
  K2     : noiseless AerSimulator(method="matrix_product_state") on the exact transpiled circuits from FakeKingston
           (classical registers kept).  F_sim >= 0.98 for every n and C_mix,sim <= 0.05.  2000 shots, fixed seed.
           This is a simulator check of the estimators, not a result.  The outcome is also written to certs/k2_sim.json.
  D4     : for G1-G3, "defined / reachable / covered" on synthetic inputs only (never hardware):
             defined   = the criterion returns True/False (not None, no exception) on the synthetic plus and minus worlds
             reachable = both HOLDS and FAILS occur on some synthetic input
             covered   = the criterion is in the Kapi STUDY and is the one ghz_analyze.py applies
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

import ghz_core as core
import ghz_study

HERE = os.path.dirname(os.path.abspath(__file__))
SIM_SEED = 20261112
F_SIM_MIN = 0.98
C_MIX_SIM_MAX = 0.05


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
          f"{est:.1f} s = {est / 60:.2f} min")
    ok = len(entries) == core.EXPECTED_CIRCUITS and shots_total == core.EXPECTED_SHOTS
    return entries, ok


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
        print(f"n={n:<3} F_sim={est['F']:.4f} P={est['P']:.4f} C={est['C']:.4f}  {'pass' if good else 'FAIL'} (>= {F_SIM_MIN})")
    for n in core.MIX_NS:
        est = core.point_estimates(counts, n, "MIX")
        good = est["C"] <= C_MIX_SIM_MAX
        ok &= good
        detail["C_mix_sim"][str(n)] = est["C"]
        print(f"MIX n={n:<3} C_mix_sim={est['C']:.4f} F_mix_sim={est['F']:.4f} P={est['P']:.4f}  "
              f"{'pass' if good else 'FAIL'} (<= {C_MIX_SIM_MAX})")
    print(f"K2: {'PASS' if ok else 'FAIL'}   (sim time {time.time() - t0:.1f} s; simulator check, not a result)")
    os.makedirs(os.path.join(HERE, "certs"), exist_ok=True)
    with open(os.path.join(HERE, "certs", "k2_sim.json"), "w", encoding="utf-8") as fh:
        json.dump({"pass": bool(ok), "shots": core.SHOTS, "seed": SIM_SEED, "detail": detail}, fh, indent=1)
    return ok


def d4():
    """defined / reachable / covered for G1-G3 on synthetic inputs."""
    import ghz_analyze  # the criteria the analysis applies

    print("== D4 (synthetic inputs only) ==")
    rng_seed = 7
    samples = []
    for i in range(40):
        rng = np.random.default_rng([rng_seed, i])
        samples.append(("plus", ghz_study.plus_world(rng)))
        samples.append(("minus", ghz_study.minus_world(rng)))
    in_study = {c.id for c in ghz_study.STUDY.criteria}
    applied = set(ghz_analyze.CRITERIA)
    all_ok = True
    for cid, fn in ghz_analyze.CRITERIA.items():
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


def main():
    entries, b_ok = budget_and_circuits()
    k2_ok = k2(entries)
    d4_ok = d4()
    print(f"SUMMARY: budget={'OK' if b_ok else 'FAIL'} K2={'PASS' if k2_ok else 'FAIL'} D4={'OK' if d4_ok else 'FAIL'}")
    return 0 if (b_ok and k2_ok and d4_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
