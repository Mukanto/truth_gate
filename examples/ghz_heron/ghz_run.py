"""ghz_run.py -- runner of the GHZ-on-Heron study, for the author (PREREG.md sections 3 D-1/D-3/D-7, 7 K3, 10 steps 4-5).

Modes
  --selftest        FakeKingston only: snapshot, selection, build + transpile all circuits, integrity (K3), model M, QPY
                    round trip, a tiny noiseless pipeline check.  No freeze needed, no account, no network.
  --dry-run         (freeze verified)  load the saved IBM account, list the operational >=156-qubit backends, pick the
                    least busy Heron r2 one (D-1; Heron r2 by processor_type if present, else num_qubits == 156), build and transpile every circuit, print counts and a rough
                    quantum-time estimate.  Does NOT submit.
  --submit          (freeze verified)  everything in --dry-run, then save the snapshot + hash, circuits.qpy and model.json,
                    and submit ONE SamplerV2 job (2000 shots, dynamical decoupling off, twirling off); writes run/job.json.
  --fetch [JOBID]   (freeze verified)  retrieve the result, save raw counts per circuit and register to run/counts.json,
                    check that the totals equal the shots (K3).

Hardware / network is only touched inside the *_service helpers below (QiskitRuntimeService is imported lazily, and only
after the freeze has been verified).  No credential is ever printed or stored by this script.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
import time

import ghz_core as core

HERE = os.path.dirname(os.path.abspath(__file__))
RUN_DIR = "run"
MIN_QUBITS = 156


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _fmt_s(seconds):
    return f"{seconds:.1f} s = {seconds / 60:.2f} min"


# --------------------------------------------------------------------------------------------------- shared reporting
def build_and_report(snap, target, rep_delay):
    """Build + transpile (integrity-checked) every circuit, print the budget; returns (entries, model, est_seconds)."""
    entries = core.build_all(snap, target)
    n_circ = len(entries)
    shots_total = n_circ * core.SHOTS
    est, rd, longest = core.estimate_time(entries, target, rep_delay)
    model = core.model_all(entries, target)
    print(f"circuits: {n_circ} (expected {core.EXPECTED_CIRCUITS})   shots per circuit: {core.SHOTS}   "
          f"shot total: {shots_total} (expected {core.EXPECTED_SHOTS})")
    print(f"K3 integrity: every circuit has n-1 two-qubit gates on the tree edges ({n_circ}/{n_circ} checked)")
    print(f"rep_delay used: {rd * 1e6:.1f} us   longest circuit: {longest * 1e6:.2f} us")
    print(f"rough quantum time = sum over circuits of shots*(rep_delay+circuit duration) = {_fmt_s(est)}")
    print("model F_pred(n): " + "  ".join(f"n={n}: {model[n]['F_pred']:.4f}" for n in core.GRID))
    for n in core.GRID:
        S = model[n]["S"]
        print(f"  S_{n}: root={S[0]} size={len(S)} last3={S[-3:]}")
    if n_circ != core.EXPECTED_CIRCUITS or shots_total != core.EXPECTED_SHOTS:
        raise core.IntegrityError("circuit / shot count differs from PREREG D-7")
    return entries, model, est


# ---------------------------------------------------------------------------------------------------------- selftest
def cmd_selftest():
    """FakeKingston only (offline). Returns 0 on success."""
    import numpy as np
    from qiskit import qpy
    from qiskit_aer import AerSimulator
    from qiskit_ibm_runtime.fake_provider import FakeKingston

    t0 = time.time()
    backend = FakeKingston()
    snap, h = core.snapshot_from_backend(backend, utc="SELFTEST")
    print(f"[selftest] backend {backend.name}: {snap['num_qubits']} qubits, snapshot sha256 {h[:16]}")
    adj = core.operational_graph(snap)
    print(f"[selftest] operational graph: {len(adj)} qubits; root {core.select_root(adj)}")
    entries, model, _est = build_and_report(snap, backend.target, getattr(backend, "default_rep_delay", None))

    # model from the snapshot-rebuilt target must equal the model from the real target (analysis path == submit path)
    tgt2 = core.target_from_snapshot(snap)
    model2 = core.model_all(entries, tgt2)
    same = all(abs(model[n]["F_pred"] - model2[n]["F_pred"]) < 1e-12 for n in core.GRID)
    print(f"[selftest] F_pred from target == F_pred from snapshot-rebuilt target: {same}")
    if not same:
        return 1

    # QPY round trip
    import io
    buf = io.BytesIO()
    qpy.dump([e["circuit"] for e in entries], buf)
    buf.seek(0)
    back = qpy.load(buf)
    ok = len(back) == len(entries) and all(a.name == b["circuit"].name for a, b in zip(back, entries))
    print(f"[selftest] QPY round trip of {len(back)} circuits: {ok}")
    if not ok:
        return 1

    # tiny noiseless pipeline check on n = 4 (same estimators as the analysis)
    sim = AerSimulator(method="matrix_product_state", seed_simulator=1)
    sub = [e for e in entries if e["n"] == 4 and e["family"] == "GHZ"]
    res = sim.run([e["circuit"] for e in sub], shots=core.SHOTS).result()
    counts = {e["name"]: core.counts_by_register(res.get_counts(i), e["circuit"]) for i, e in enumerate(sub)}
    est4 = core.point_estimates(counts, 4, "GHZ")
    print(f"[selftest] noiseless n=4 pipeline: P={est4['P']:.4f} C={est4['C']:.4f} F={est4['F']:.4f} (expect ~1)")
    if est4["F"] < 0.95:
        return 1
    print(f"[selftest] OK   wall time {time.time() - t0:.1f} s")
    return 0


# ------------------------------------------------------------------------------------------ account / hardware helpers
def _service():
    """The ONLY place that instantiates QiskitRuntimeService (default saved account; nothing is read or printed here)."""
    from qiskit_ibm_runtime import QiskitRuntimeService
    return QiskitRuntimeService()


def heron_r2_basis(backend):
    """(is_heron_r2, basis). PREREG D-1 (v2): Heron r2 by ``processor_type`` (family Heron, revision 2) when that field is
    present; otherwise num_qubits == 156 (``"num_qubits_fallback"``)."""
    ptype = getattr(backend, "processor_type", None)
    if ptype:
        ok = str(ptype.get("family", "")).lower() == "heron" and str(ptype.get("revision", "")) == "2"
        return bool(ok), "processor_type"
    return backend.num_qubits == 156, "num_qubits_fallback"


def pick_backend(service):
    """D-1: among the operational >=156-qubit non-simulator backends visible to the account, the Heron r2 one (see
    heron_r2_basis) with the fewest pending jobs (ties: name). Prints the candidate list and the basis of the choice.
    Returns (backend, basis)."""
    backs = service.backends(simulator=False, operational=True, min_num_qubits=MIN_QUBITS)
    rows = []
    for b in backs:
        st = b.status()
        ok, basis = heron_r2_basis(b)
        rows.append({"backend": b, "name": b.name, "n": b.num_qubits, "pending": st.pending_jobs,
                     "operational": bool(st.operational), "heron_r2": ok, "basis": basis})
    rows.sort(key=lambda r: (r["pending"], r["name"]))
    print(f"operational non-simulator backends with >= {MIN_QUBITS} qubits: {len(rows)}")
    for r in rows:
        tag = ("Heron r2" if r["heron_r2"] else "not Heron r2") + f" (basis: {r['basis']})"
        print(f"  {r['name']:<20} qubits={r['n']:<4} pending_jobs={r['pending']:<5} {tag}")
    cand = [r for r in rows if r["operational"] and r["heron_r2"]]
    if not cand:
        raise SystemExit("no operational Heron r2 backend with >= 156 qubits is visible to this account; not selecting any")
    chosen = cand[0]
    print(f"SELECTED (D-1, least busy Heron r2): {chosen['name']} (pending_jobs={chosen['pending']}, "
          f"basis: {chosen['basis']})")
    return chosen["backend"], chosen["basis"]


def cmd_dry_run(root):
    service = _service()
    backend, basis = pick_backend(service)
    utc = utc_now()
    snap, h = core.snapshot_from_backend(backend, utc=utc)
    print(f"backend choice basis: {basis}")
    print(f"snapshot (not saved in --dry-run): {backend.name} {utc} sha256 {h[:16]}")
    build_and_report(snap, backend.target, snap["rep_delay"])
    print("dry run only: nothing was submitted.")
    return 0


def cmd_submit(root):
    from qiskit import qpy
    from qiskit_ibm_runtime import SamplerV2

    run_dir = os.path.join(root, RUN_DIR)
    job_path = os.path.join(run_dir, "job.json")
    if os.path.exists(job_path):
        raise SystemExit(f"{job_path} already exists: a job was already submitted from this folder; refusing to submit again")
    service = _service()
    backend, basis = pick_backend(service)
    utc = utc_now()
    snap, h = core.snapshot_from_backend(backend, utc=utc)
    entries, model, est = build_and_report(snap, backend.target, snap["rep_delay"])

    # K3, before submitting: integrity done in build_all; snapshot saved and hashed; freeze verified by main()
    os.makedirs(run_dir, exist_ok=True)
    snap_name = f"snapshot_{backend.name}_{utc}.json"
    with open(os.path.join(run_dir, snap_name), "w", encoding="utf-8") as fh:
        json.dump({"sha256": h, "snapshot": snap}, fh, indent=1, sort_keys=True)
    with open(os.path.join(run_dir, "circuits.qpy"), "wb") as fh:
        qpy.dump([e["circuit"] for e in entries], fh)
    with open(os.path.join(run_dir, "model.json"), "w", encoding="utf-8") as fh:
        json.dump({"snapshot_sha256": h, "grid": list(core.GRID), "components": {str(n): model[n] for n in core.GRID}},
                  fh, indent=1)
    print(f"saved run/{snap_name} (sha256 {h}), run/circuits.qpy, run/model.json")

    sampler = SamplerV2(mode=backend)
    sampler.options.dynamical_decoupling.enable = False
    sampler.options.twirling.enable_gates = False
    sampler.options.twirling.enable_measure = False
    job = sampler.run([(e["circuit"],) for e in entries], shots=core.SHOTS)
    job_id = job.job_id()
    with open(job_path, "w", encoding="utf-8") as fh:
        json.dump({
            "job_id": job_id, "backend": backend.name, "backend_choice_basis": basis, "submitted_utc": utc, "snapshot_file": snap_name,
            "snapshot_sha256": h, "shots": core.SHOTS, "n_circuits": len(entries),
            "dynamical_decoupling": False, "twirling": False, "est_quantum_seconds": est,
            "manifest": core.manifest_of(entries),
        }, fh, indent=1)
    print(f"SUBMITTED job {job_id} on {backend.name}; wrote run/job.json")
    return 0


def cmd_fetch(root, job_id=None):
    run_dir = os.path.join(root, RUN_DIR)
    with open(os.path.join(run_dir, "job.json"), "r", encoding="utf-8") as fh:
        meta = json.load(fh)
    job_id = job_id or meta["job_id"]
    service = _service()
    job = service.job(job_id)
    print(f"job {job_id}: status {job.status()}")
    result = job.result()
    manifest = meta["manifest"]
    if len(result) != len(manifest):
        raise SystemExit(f"result has {len(result)} pubs, manifest has {len(manifest)}")
    circuits, order, bad = {}, [], []
    for entry, pub in zip(manifest, result):
        regs = {}
        for reg in ("meas", "mid"):
            if hasattr(pub.data, reg):
                regs[reg] = {str(k): int(v) for k, v in getattr(pub.data, reg).get_counts().items()}
        total = {r: sum(c.values()) for r, c in regs.items()}
        if any(t != meta["shots"] for t in total.values()) or "meas" not in regs:
            bad.append(entry["name"])
        circuits[entry["name"]] = regs
        order.append(entry["name"])
    out = {"job_id": job_id, "backend": meta["backend"], "shots": meta["shots"], "order": order,
           "k3_count_totals_ok": not bad, "bad_circuits": bad, "circuits": circuits}
    with open(os.path.join(run_dir, "counts.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh)
    print(f"saved run/counts.json ({len(circuits)} circuits)")
    print("K3 count totals == shots: " + ("OK" if not bad else f"FAILED for {bad[:5]}{' ...' if len(bad) > 5 else ''}"))
    return 0 if not bad else 2


# ------------------------------------------------------------------------------------------------------------- main
def main(argv=None, root=HERE):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--submit", action="store_true")
    g.add_argument("--fetch", nargs="?", const="", metavar="JOBID")
    args = ap.parse_args(argv)
    if args.selftest:
        return cmd_selftest()
    try:
        core.verify_freeze(root)
    except core.FreezeError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 3
    print("freeze manifest verified")
    if args.dry_run:
        return cmd_dry_run(root)
    if args.submit:
        return cmd_submit(root)
    return cmd_fetch(root, args.fetch or None)


if __name__ == "__main__":
    sys.exit(main())
