"""ghz_core.py -- shared library of the GHZ-on-Heron study (qiskit + numpy, no network, no hardware).

Implements PREREG.md:
  section 3  (D-2 error-blind selection, D-3 circuit and transpilation, D-5 POP/PAR, D-6 MIX controls, D-4/D-7 grid and budget)
  section 4  (estimators and the joint multinomial bootstrap)
  section 5  (model M, built from a qiskit Target / the calibration snapshot)
  section 7  (K3 integrity assert, freeze manifest verification)

Everything that depends on the device goes through a JSON-serialisable *snapshot* of the Target, so the selection, the
model and the analysis can be recomputed offline from the saved snapshot (target_from_snapshot).
Nothing here touches QiskitRuntimeService, an account file or the network.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from collections import deque

import numpy as np
from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister, transpile
from qiskit.circuit import Delay, Measure, Parameter
from qiskit.circuit.duration import duration_in_dt
from qiskit.circuit.library import CZGate, RZGate, SXGate, XGate
from qiskit.transpiler import InstructionProperties, PassManager, QubitProperties, Target
from qiskit.transpiler.passes import ALAPScheduleAnalysis

# ----------------------------------------------------------------------------------------------------------- constants
GRID = (4, 8, 16, 32, 48)          # D-4
MIX_NS = (8, 32)                   # D-6
SHOTS = 2000                       # D-4
SEED = 20261112                    # D-3 (transpiler) and section 4 (bootstrap)
BOOT_B = 2000                      # section 4
DEFAULT_REP_DELAY = 250e-6         # seconds; used only if the target / backend does not give one
EDGE_ERROR_LIMIT = 0.5             # D-2
EXPECTED_CIRCUITS = 317            # D-7
EXPECTED_SHOTS = 634000            # D-7
SNAPSHOT_SCHEMA = "ghz_heron_snapshot_v1"
REQUIRED_FROZEN = ("PREREG.md", "ghz_core.py", "ghz_study.py", "ghz_run.py", "ghz_analyze.py")


class IntegrityError(RuntimeError):
    """K3: a circuit does not have the n - 1 two-qubit gates on the tree edges (routing happened)."""


class FreezeError(RuntimeError):
    """The freeze manifest is absent, malformed, or does not match the files."""


# -------------------------------------------------------------------------------------------------------------- hashing
def canonical_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def snapshot_hash(snapshot: dict) -> str:
    return sha256_text(canonical_json(snapshot))


def sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def verify_freeze(root, manifest_name="FREEZE_GHZ.json", required=REQUIRED_FROZEN):
    """Refuse (FreezeError) unless FREEZE_GHZ.json exists and every listed file matches its SHA-256.

    Manifest format: {"files": {name: sha256, ...}}; extra keys (format, core_sha256 of protocol/tools/freeze.py) are allowed.
    A manifest that does not list every file in ``required`` is also refused (it would not protect the study).
    """
    path = os.path.join(root, manifest_name)
    if not os.path.isfile(path):
        raise FreezeError(f"{manifest_name} not found in {root}: refusing to run before the freeze")
    try:
        with open(path, "r", encoding="utf-8") as fh:
            manifest = json.load(fh)
        files = manifest["files"]
        assert isinstance(files, dict) and files
    except Exception as exc:  # noqa: BLE001
        raise FreezeError(f"{manifest_name} is malformed ({type(exc).__name__})") from None
    norm = {str(k).replace("\\", "/"): v for k, v in files.items()}
    missing = [r for r in required if r not in norm]
    if missing:
        raise FreezeError(f"{manifest_name} does not list required files: {missing}")
    bad = []
    for name, digest in norm.items():
        fpath = os.path.join(root, *name.split("/"))
        if not os.path.isfile(fpath):
            bad.append(f"{name} (missing)")
        elif sha256_file(fpath) != digest:
            bad.append(f"{name} (hash mismatch)")
    if bad:
        raise FreezeError("freeze verification failed: " + ", ".join(bad))
    return True


# ---------------------------------------------------------------------------------------------------------- snapshot
def _num(x):
    """float or None (None for missing / nan / inf)."""
    if x is None:
        return None
    try:
        x = float(x)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def _op_props(target, name, qargs):
    """{"error":..., "duration":...} for (name, qargs) in the target, or None if the target does not have it."""
    if name not in target.operation_names:
        return None
    table = target[name]
    if qargs not in table:
        return None
    p = table[qargs]
    if p is None:
        return {"error": None, "duration": None}
    return {"error": _num(p.error), "duration": _num(p.duration)}


def snapshot_from_target(target, backend_name, faulty_qubits=(), faulty_gates=(), rep_delay=None, utc=None,
                         processor_type=None):
    """Serialise the parts of a Target that the study needs. Returns (snapshot dict, sha256 hex).

    ``faulty_qubits`` / ``faulty_gates`` ([(name, qubits), ...]) come from backend.properties() when available (operational
    flags); ``utc`` is the timestamp string recorded in the snapshot (part of the hash).
    """
    nq = target.num_qubits
    faulty_qubits = sorted(int(q) for q in faulty_qubits)
    faulty = set(faulty_qubits)
    qprops = target.qubit_properties
    qubits = []
    for q in range(nq):
        qp = qprops[q] if qprops is not None else None
        qubits.append({
            "t1": _num(getattr(qp, "t1", None)),
            "t2": _num(getattr(qp, "t2", None)),
            "operational": q not in faulty,
            "measure": _op_props(target, "measure", (q,)),
            "sx": _op_props(target, "sx", (q,)),
            "x": _op_props(target, "x", (q,)),
        })
    edges = []
    if "cz" in target.operation_names:
        for (a, b), p in sorted(target["cz"].items()):
            if a is None or b is None:
                continue
            edges.append([int(a), int(b), _num(getattr(p, "error", None)), _num(getattr(p, "duration", None))])
    snap = {
        "schema": SNAPSHOT_SCHEMA,
        "backend": str(backend_name),
        "num_qubits": int(nq),
        "dt": _num(target.dt),
        "utc": utc,
        "processor_type": dict(processor_type) if processor_type else None,
        "rep_delay": _num(rep_delay),
        "timing": {
            "granularity": int(target.granularity),
            "min_length": int(target.min_length),
            "pulse_alignment": int(target.pulse_alignment),
            "acquire_alignment": int(target.acquire_alignment),
        },
        "faulty_qubits": faulty_qubits,
        "faulty_gates": sorted([[str(n), [int(x) for x in qs]] for n, qs in faulty_gates]),
        "qubits": qubits,
        "edges": edges,
    }
    return snap, snapshot_hash(snap)


def snapshot_from_backend(backend, utc=None):
    """Snapshot of a (fake or real) backend; reads backend.target and, if available, backend.properties() flags."""
    faulty_q, faulty_g = [], []
    try:
        props = backend.properties()
        if props is not None:
            faulty_q = list(props.faulty_qubits())
            faulty_g = [(g.gate, list(g.qubits)) for g in props.faulty_gates()]
    except Exception:  # noqa: BLE001  (properties() may be unavailable; the target alone is then used)
        pass
    rep = getattr(backend, "default_rep_delay", None)
    ptype = getattr(backend, "processor_type", None)
    return snapshot_from_target(backend.target, backend.name, faulty_q, faulty_g, rep_delay=rep, utc=utc,
                                processor_type=ptype)


def target_from_snapshot(snap) -> Target:
    """Rebuild a Target (cz, sx, x, rz, measure, delay; durations, errors, T1/T2) from a snapshot."""
    nq = snap["num_qubits"]
    tm = snap["timing"]
    qprops = [QubitProperties(t1=q["t1"], t2=q["t2"]) for q in snap["qubits"]]
    tg = Target(num_qubits=nq, dt=snap["dt"], granularity=tm["granularity"], min_length=tm["min_length"],
                pulse_alignment=tm["pulse_alignment"], acquire_alignment=tm["acquire_alignment"],
                qubit_properties=qprops)
    theta, tdelay = Parameter("theta"), Parameter("t")
    tg.add_instruction(RZGate(theta), {(q,): InstructionProperties(duration=0.0, error=0.0) for q in range(nq)})
    for name, gate in (("sx", SXGate()), ("x", XGate())):
        d = {(i,): InstructionProperties(duration=q[name]["duration"], error=q[name]["error"])
             for i, q in enumerate(snap["qubits"]) if q[name] is not None}
        tg.add_instruction(gate, d)
    tg.add_instruction(Measure(), {(i,): InstructionProperties(duration=q["measure"]["duration"],
                                                                 error=q["measure"]["error"])
                                   for i, q in enumerate(snap["qubits"]) if q["measure"] is not None})
    tg.add_instruction(Delay(tdelay), {(q,): None for q in range(nq)})
    tg.add_instruction(CZGate(), {(a, b): InstructionProperties(duration=dur, error=err) for a, b, err, dur in snap["edges"]})
    return tg


# ---------------------------------------------------------------------------------------------- D-2 selection (error-blind)
def operational_graph(snap):
    """Adjacency {qubit: sorted neighbour list} of the operational graph G (D-2).

    Qubit excluded: flagged non-operational, or readout error / T2 / sx / measure missing.
    Edge excluded: an endpoint excluded, a cz flagged faulty, no cz entry, or any listed direction with a missing error or
    error >= 0.5.
    """
    ok = set()
    for i, q in enumerate(snap["qubits"]):
        if not q.get("operational", True):
            continue
        if q["t2"] is None or q["measure"] is None or q["measure"]["error"] is None or q["sx"] is None:
            continue
        ok.add(i)
    faulty_edges = {frozenset(qs) for name, qs in snap.get("faulty_gates", []) if name == "cz" and len(qs) == 2}
    per_edge = {}
    for a, b, err, _dur in snap["edges"]:
        per_edge.setdefault(frozenset((a, b)), []).append(err)
    adj = {i: set() for i in ok}
    for e, errs in per_edge.items():
        if len(e) != 2 or e in faulty_edges:
            continue
        a, b = sorted(e)
        if a not in ok or b not in ok:
            continue
        if any(x is None or x >= EDGE_ERROR_LIMIT for x in errs):
            continue
        adj[a].add(b)
        adj[b].add(a)
    return {i: sorted(v) for i, v in sorted(adj.items())}


def _bfs_distances(adj, src):
    dist = {src: 0}
    queue = deque([src])
    while queue:
        u = queue.popleft()
        for v in adj[u]:
            if v not in dist:
                dist[v] = dist[u] + 1
                queue.append(v)
    return dist


def select_root(adj):
    """Root = highest closeness centrality in the largest connected component; ties -> lowest index.

    Closeness (N-1)/sum(dist) is maximal iff the integer distance sum is minimal, so integers are compared (no float ties).
    Components of equal size: the one containing the lowest qubit index.
    """
    seen, comps = set(), []
    for s in adj:
        if s in seen:
            continue
        d = _bfs_distances(adj, s)
        seen.update(d)
        comps.append(sorted(d))
    if not comps:
        raise ValueError("operational graph is empty")
    comp = max(comps, key=lambda c: (len(c), -c[0]))
    best = None
    for u in comp:
        total = sum(_bfs_distances(adj, u).values())
        if best is None or total < best[0]:
            best = (total, u)
    return best[1]


def bfs_order(adj, root):
    """BFS order from root, neighbours in ascending index. Returns (order list, parent dict)."""
    order, parent = [root], {root: None}
    queue = deque([root])
    while queue:
        u = queue.popleft()
        for v in adj[u]:
            if v not in parent:
                parent[v] = u
                order.append(v)
                queue.append(v)
    return order, parent


def selection(snap, n):
    """(S_n, T_n, parents): S_n physical qubits in BFS order; T_n list of (parent, child) physical edges;
    parents[i] = logical index of the parent of logical qubit i (parents[0] = None)."""
    adj = operational_graph(snap)
    root = select_root(adj)
    order, parent = bfs_order(adj, root)
    if len(order) < n:
        raise ValueError(f"largest operational component has {len(order)} qubits < n = {n}")
    S = order[:n]
    index = {q: i for i, q in enumerate(S)}
    T = [(parent[q], q) for q in S[1:]]
    parents = [None] + [index[parent[q]] for q in S[1:]]
    return S, T, parents


# ---------------------------------------------------------------------------------------------------------- D-3/5/6 circuits
def circuit_name(family, n, kind, j=None):
    return f"{family}{n}_POP" if kind == "POP" else f"{family}{n}_PAR{j}"


def build_circuit(n, parents, kind, j=None, mix=False):
    """Logical GHZ_n (POP or PAR_j) or its mixture twin (mid-circuit root measurement into register 'mid').

    Qubit i is the i-th qubit of S_n (BFS order); data bits go to register 'meas'.
    """
    q = QuantumRegister(n, "q")
    meas = ClassicalRegister(n, "meas")
    regs = [q, meas]
    mid = None
    if mix:
        mid = ClassicalRegister(1, "mid")
        regs.append(mid)
    qc = QuantumCircuit(*regs, name=circuit_name("MIX" if mix else "GHZ", n, kind, j))
    qc.h(0)
    if mix:
        qc.measure(0, mid[0])
    for i in range(1, n):
        qc.cx(parents[i], i)
    if kind == "PAR":
        phi = j * math.pi / (n + 1)
        for i in range(n):
            qc.rz(-phi, i)
            qc.h(i)
    elif kind != "POP":
        raise ValueError(kind)
    qc.measure(range(n), meas)
    return qc


def check_integrity(tc, n, S, T):
    """K3: exactly n-1 two-qubit gates, on exactly the edges of T_n, touching only qubits of S_n."""
    twoq = []
    touched = set()
    for inst in tc.data:
        if inst.operation.name == "barrier":
            continue
        qs = tuple(tc.find_bit(x).index for x in inst.qubits)
        touched.update(qs)
        if inst.operation.num_qubits == 2:
            twoq.append(frozenset(qs))
    if len(twoq) != n - 1:
        raise IntegrityError(f"{tc.name}: {len(twoq)} two-qubit gates, expected {n - 1} (routing?)")
    if set(twoq) != {frozenset(e) for e in T} or len(set(twoq)) != n - 1:
        raise IntegrityError(f"{tc.name}: two-qubit gates are not the tree edges T_n")
    if not touched <= set(S):
        raise IntegrityError(f"{tc.name}: gates outside S_n: {sorted(touched - set(S))}")


def transpile_checked(qc, n, S, T, target):
    """D-3: transpile with initial_layout = S_n, optimization_level=1, seed_transpiler=SEED; then the integrity assert."""
    tc = transpile(qc, target=target, initial_layout=list(S), optimization_level=1, seed_transpiler=SEED)
    check_integrity(tc, n, S, T)
    return tc


def circuit_plan(grid=GRID, mix_ns=MIX_NS):
    """The ordered list of (family, n, kind, j) of PREREG D-7: GHZ for each n (POP, PAR_0..PAR_{2n+1}), then MIX."""
    plan = []
    for fam, ns in (("GHZ", grid), ("MIX", mix_ns)):
        for n in ns:
            plan.append((fam, n, "POP", None))
            plan.extend((fam, n, "PAR", j) for j in range(2 * n + 2))
    return plan


def build_all(snap, target, grid=GRID, mix_ns=MIX_NS):
    """Build + transpile + integrity-check every circuit. Returns a list of entries in submission order.

    entry = {name, family, n, j, kind, S, T, circuit (transpiled)}
    """
    sel = {n: selection(snap, n) for n in sorted(set(grid) | set(mix_ns))}
    entries = []
    for fam, n, kind, j in circuit_plan(grid, mix_ns):
        S, T, parents = sel[n]
        qc = build_circuit(n, parents, kind, j, mix=(fam == "MIX"))
        tc = transpile_checked(qc, n, S, T, target)
        entries.append({"name": qc.name, "family": fam, "n": n, "j": j, "kind": kind, "S": S, "T": T, "circuit": tc})
    return entries


def manifest_of(entries):
    return [{"index": i, "name": e["name"], "family": e["family"], "n": e["n"], "kind": e["kind"], "j": e["j"]}
            for i, e in enumerate(entries)]


# ------------------------------------------------------------------------------------------------------ budget / time
def estimate_time(entries, target, rep_delay=None, shots=SHOTS):
    """Rough quantum time in seconds: sum over circuits of shots * (rep_delay + circuit duration).

    Circuit duration = QuantumCircuit.estimate_duration(target) (critical path with the target's durations).
    Returns (total_seconds, rep_delay_used, max_circuit_duration).
    """
    rd = DEFAULT_REP_DELAY if rep_delay is None else rep_delay
    total, longest = 0.0, 0.0
    for e in entries:
        dur = float(e["circuit"].estimate_duration(target, unit="s"))
        longest = max(longest, dur)
        total += shots * (rd + dur)
    return total, rd, longest


# ----------------------------------------------------------------------------------------------------------- model M
def idle_times(tc, target, qubits):
    """Idle time (seconds) per qubit of an ALAP-scheduled copy of ``tc`` (the transpiled POP_n).

    idle = (start of the qubit's measurement) - (start of its first non-virtual operation) - (sum of its own gate durations).
    Scheduling: qiskit ALAPScheduleAnalysis(target=target) on a PassManager; the circuit itself is not modified.
    """
    pm = PassManager([ALAPScheduleAnalysis(target=target)])
    pm.run(tc)
    nst = pm.property_set["node_start_time"]
    dt = target.dt
    first, own, meas_start = {}, {}, {}
    for node, start in nst.items():
        op = node.op
        name = op.name
        if name in ("barrier", "delay"):
            continue
        qs = tuple(tc.find_bit(x).index for x in node.qargs)
        if name == "measure":
            q = qs[0]
            meas_start[q] = max(meas_start.get(q, -1), start)
            continue
        props = target[name][qs]
        dur = duration_in_dt(props.duration or 0.0, dt)
        if dur <= 0:
            continue  # virtual (rz): no time, no error
        for q in qs:
            first[q] = min(first.get(q, start), start)
            own[q] = own.get(q, 0) + dur
    out = []
    for q in qubits:
        if q not in meas_start:
            raise ValueError(f"qubit {q} has no measurement in the scheduled circuit")
        if q not in first:
            out.append(0.0)
            continue
        out.append(max(0, meas_start[q] - first[q] - own[q]) * dt)
    return out


def model_components(tc, target, S):
    """Everything that enters F_pred(n) for the transpiled POP circuit ``tc`` on the qubits S (= S_n)."""
    cz_err, g1_err = [], []
    for inst in tc.data:
        name = inst.operation.name
        if name in ("measure", "barrier", "delay", "rz"):   # rz is virtual (error 0)
            continue
        qs = tuple(tc.find_bit(x).index for x in inst.qubits)
        err = target[name][qs].error
        if err is None:
            raise ValueError(f"missing error for {name}{qs}")
        (cz_err if len(qs) == 2 else g1_err).append(float(err))
    ro_err = [float(target["measure"][(q,)].error) for q in S]
    t2 = [float(target.qubit_properties[q].t2) for q in S]
    idle = idle_times(tc, target, S)
    comp = {"S": list(S), "cz_err": cz_err, "g1_err": g1_err, "ro_err": ro_err, "t2": t2, "idle": idle}
    comp["F_pred"] = f_pred_from_components(comp)
    return comp


def f_pred_from_components(comp):
    """F_pred = prod(1-eps_2q) * prod(1-eps_ro) * prod(1-eps_1q) * prod exp(-idle/T2)   (PREREG section 5)."""
    logf = 0.0
    for key in ("cz_err", "g1_err", "ro_err"):
        for e in comp[key]:
            logf += math.log1p(-e) if e < 1.0 else -math.inf
    for t, t2 in zip(comp["idle"], comp["t2"]):
        logf -= t / t2
    return float(math.exp(logf))


def model_all(entries, target, grid=GRID):
    """{n: components} from the transpiled GHZ POP circuits."""
    out = {}
    for e in entries:
        if e["family"] == "GHZ" and e["kind"] == "POP" and e["n"] in grid:
            out[e["n"]] = model_components(e["circuit"], target, e["S"])
    return out


# --------------------------------------------------------------------------------------------------------- estimators
def _clean(bits):
    return bits.replace(" ", "")


def pop_counts(meas_counts, n):
    """(N(0^n), N(1^n), N_other, shots) from a bitstring->count dict of the data register."""
    n0 = n1 = tot = 0
    for bits, c in meas_counts.items():
        b = _clean(bits)
        tot += c
        if b == "0" * n:
            n0 += c
        elif b == "1" * n:
            n1 += c
    return n0, n1, tot - n0 - n1, tot


def parity_counts(meas_counts):
    """(N_even, N_odd, shots): outcomes with an even / odd number of 1s among the data bits."""
    ev = od = 0
    for bits, c in meas_counts.items():
        if _clean(bits).count("1") % 2:
            od += c
        else:
            ev += c
    return ev, od, ev + od


def phis(n):
    return np.arange(2 * n + 2) * math.pi / (n + 1)


def coherence_from_parities(parities, n):
    """C_n = (2/(2n+2)) |sum_j parity_j exp(i n phi_j)|. ``parities`` may be (..., 2n+2); returns (...)."""
    par = np.asarray(parities, dtype=float)
    ph = np.exp(1j * n * phis(n))
    return (2.0 / (2 * n + 2)) * np.abs(par @ ph)


def point_estimates(counts, n, family="GHZ"):
    """P, parities (2n+2,), C, F for one (family, n) from raw counts {circuit_name: {"meas": {...}, ...}}."""
    pop = counts[circuit_name(family, n, "POP")]["meas"]
    n0, n1, _o, tot = pop_counts(pop, n)
    P = (n0 + n1) / tot
    par = []
    for j in range(2 * n + 2):
        ev, od, t = parity_counts(counts[circuit_name(family, n, "PAR", j)]["meas"])
        par.append((ev - od) / t)
    par = np.array(par)
    C = float(coherence_from_parities(par, n))
    return {"P": P, "parity": par, "C": C, "F": (P + C) / 2.0}


def bootstrap_group(counts, n, family, B, rng):
    """Joint multinomial bootstrap for one (family, n): every circuit's counts are resampled (B draws each, same replicate
    index across the circuits of this group). Categories are reduced to what the estimators read: POP -> (0^n, 1^n, other),
    PAR -> (even, odd); a multinomial over the reduced categories has exactly the distribution of the full-outcome
    multinomial after aggregation. Returns {"P": (B,), "C": (B,), "F": (B,)}."""
    pop = counts[circuit_name(family, n, "POP")]["meas"]
    n0, n1, no, tot = pop_counts(pop, n)
    pv = np.array([n0, n1, no], dtype=float) / tot
    draw = rng.multinomial(tot, pv / pv.sum(), size=B)
    P = (draw[:, 0] + draw[:, 1]) / tot
    par = np.empty((B, 2 * n + 2))
    for j in range(2 * n + 2):
        ev, od, t = parity_counts(counts[circuit_name(family, n, "PAR", j)]["meas"])
        d = rng.multinomial(t, np.array([ev, od], dtype=float) / t, size=B)
        par[:, j] = (d[:, 0] - d[:, 1]) / t
    C = coherence_from_parities(par, n)
    return {"P": P, "C": C, "F": (P + C) / 2.0}


def ci95(x, axis=0):
    return np.percentile(x, 2.5, axis=axis), np.percentile(x, 97.5, axis=axis)


def analyze_counts(counts, grid=GRID, mix_ns=MIX_NS, B=BOOT_B, seed=SEED):
    """All estimators of PREREG section 4.

    One np.random.default_rng(seed); draws are made in the order: GHZ n ascending (POP, PAR_0..), then MIX n ascending.
    Returns arrays over ``grid`` (P, C, F_hat, F_boot (B,5), P_boot, C_boot, ci) and per-n MIX dicts.
    """
    rng = np.random.default_rng(seed)
    P, C, F = [], [], []
    Pb, Cb, Fb = [], [], []
    for n in grid:
        est = point_estimates(counts, n, "GHZ")
        bt = bootstrap_group(counts, n, "GHZ", B, rng)
        P.append(est["P"]); C.append(est["C"]); F.append(est["F"])
        Pb.append(bt["P"]); Cb.append(bt["C"]); Fb.append(bt["F"])
    F_boot = np.stack(Fb, axis=1)
    lo, hi = ci95(F_boot)
    out = {"n": np.array(grid), "P": np.array(P), "C": np.array(C), "F_hat": np.array(F), "F_boot": F_boot,
           "P_boot": np.stack(Pb, axis=1), "C_boot": np.stack(Cb, axis=1), "F_lo": lo, "F_hi": hi, "mix": {}}
    for n in mix_ns:
        est = point_estimates(counts, n, "MIX")
        bt = bootstrap_group(counts, n, "MIX", B, rng)
        flo, fhi = ci95(bt["F"])
        clo, chi = ci95(bt["C"])
        out["mix"][n] = {"P": est["P"], "C": est["C"], "F": est["F"], "C_boot": bt["C"], "F_boot": bt["F"],
                         "F_lo": float(flo), "F_hi": float(fhi), "C_lo": float(clo), "C_hi": float(chi)}
    return out


def split_registers(bitstring, cregs):
    """Split a raw simulator bitstring into {register name: bits}. ``cregs`` = list of (name, size) in the order the
    registers were added to the circuit; qiskit prints the last-added register leftmost."""
    s = bitstring.replace(" ", "")
    out, pos = {}, 0
    for name, size in reversed(cregs):
        out[name] = s[pos:pos + size]
        pos += size
    return out


def counts_by_register(raw_counts, circuit):
    """{"meas": {bits: n}, "mid": {...}} from a simulator counts dict for ``circuit``."""
    cregs = [(r.name, r.size) for r in circuit.cregs]
    out = {name: {} for name, _ in cregs}
    for bits, c in raw_counts.items():
        for name, part in split_registers(bits, cregs).items():
            out[name][part] = out[name].get(part, 0) + c
    return out
