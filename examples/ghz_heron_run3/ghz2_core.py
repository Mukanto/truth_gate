"""ghz2_core.py -- shared library of the GHZ run-2 study (qiskit + numpy, no network, no hardware).

Adapted from run 1 (../ghz_heron/ghz_core.py, frozen, read-only).  Implements PREREG.md (run 2):
  section 1  (D-1..D-7: error-blind selection, circuits, grid n = 4, 8, 16, 24, 32, 48, budget 368 circuits / 736000 shots)
  section 2  (estimators; joint multinomial bootstrap B = 2000, seed 20261113, returning P, C, F replicates)
  section 3  (model M2: P_pred, C_pred, F_pred predicted separately; reference arm = run 1's model M, reported only)
  section 5  (K3 integrity assert, freeze manifest FREEZE_GHZ2.json)
  section 6  (I-1: C with Re instead of |.|, reported as a sensitivity)

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
GRID = (4, 8, 16, 24, 32, 48)      # D-4 (run 2: 24 added)
MIX_NS = (8, 32)                   # D-6
SHOTS = 2000                       # D-4
SEED = 20261112                    # D-3 (transpiler seed, as in run 1)
BOOT_SEED = 20261113               # section 2 (bootstrap)
BOOT_B = 2000                      # section 2
DEFAULT_REP_DELAY = 250e-6         # seconds; used only if the target / backend does not give one
EDGE_ERROR_LIMIT = 0.5             # D-2
EXPECTED_CIRCUITS = 368            # D-7
EXPECTED_SHOTS = 736000            # D-7
MAX_QUANTUM_SECONDS = 300.0        # D-7: a rough estimate above this means the run is not submitted
SNAPSHOT_SCHEMA = "ghz_heron_snapshot_v1"
REQUIRED_FROZEN = ("PREREG.md", "ghz2_core.py", "ghz2_study.py", "ghz2_run.py", "ghz2_analyze.py")


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


def verify_freeze(root, manifest_name="FREEZE_GHZ2.json", required=REQUIRED_FROZEN):
    """Refuse (FreezeError) unless FREEZE_GHZ2.json exists and every listed file matches its SHA-256.

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


def build_circuit(n, parents, kind, j=None, mix=False, flip=()):
    """Logical GHZ_n (POP or PAR_j) or its mixture twin (mid-circuit root measurement into register 'mid').

    Qubit i is the i-th qubit of S_n (BFS order); data bits go to register 'meas'.
    ``flip`` (logical qubit indices) puts an X on those qubits right before the final measurement; it is used only by the
    K2 bit-order positive control (ghz2_d4.py) and is empty for every circuit of the run.
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
    for i in flip:
        qc.x(i)
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


# ------------------------------------------------------------------------------------------------------ model M2 / M
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


def _one_q_errors(tc, target):
    """(cz errors, 1q errors) of the transpiled circuit ``tc`` (rz is virtual: error 0; measure/delay/barrier skipped)."""
    cz_err, g1_err = [], []
    for inst in tc.data:
        name = inst.operation.name
        if name in ("measure", "barrier", "delay", "rz"):
            continue
        qs = tuple(tc.find_bit(x).index for x in inst.qubits)
        err = target[name][qs].error
        if err is None:
            raise ValueError(f"missing error for {name}{qs}")
        (cz_err if len(qs) == 2 else g1_err).append(float(err))
    return cz_err, g1_err


def model_components(tc_pop, tc_par0, target, S):
    """Everything that enters M2 (PREREG section 3) and the reference model M for one n.

    tc_pop  : transpiled GHZ_n POP circuit (cz tree, 1q gates of POP, scheduling for the idle times)
    tc_par0 : transpiled GHZ_n PAR_{n,0} circuit (1q gates of the basis change for G_par)
    S       : the qubits S_n
    """
    cz_err, g1_pop = _one_q_errors(tc_pop, target)
    cz_par, g1_par = _one_q_errors(tc_par0, target)
    if sorted(cz_par) != sorted(cz_err):
        raise ValueError("POP and PAR_0 circuits have different cz errors (different two-qubit gates)")
    comp = {
        "S": list(S), "cz_err": cz_err, "g1_pop_err": g1_pop, "g1_par_err": g1_par,
        "ro_err": [float(target["measure"][(q,)].error) for q in S],
        "t1": [float(target.qubit_properties[q].t1) for q in S],
        "t2": [float(target.qubit_properties[q].t2) for q in S],
        "idle": idle_times(tc_pop, target, S),
    }
    comp.update(m2_from_components(comp))
    return comp


def _prod1m(errs, k=1.0):
    out = 1.0
    for e in errs:
        out *= 1.0 - k * e
    return out


def m2_from_components(comp):
    """M2 (PREREG section 3) and the reference model M from the component lists.

    G_pop = prod_tree(1-eps_cz) prod_{1q in POP}(1-eps_1q);  G_par likewise with the 1q gates of PAR_0.
    P_pred = G_pop prod_q(1-eps_ro) * (1 + prod_q exp(-t_q/T1))/2
    C_pred = G_par prod_q(1-2 eps_ro) prod_q exp(-t_q/T2)
    F_pred = (P_pred + C_pred)/2
    F_M    = run 1's model: prod_tree(1-eps_cz) prod_q(1-eps_ro) prod_{1q in POP}(1-eps_1q) prod_q exp(-t_q/T2)
    """
    tree = _prod1m(comp["cz_err"])
    g_pop = tree * _prod1m(comp["g1_pop_err"])
    g_par = tree * _prod1m(comp["g1_par_err"])
    ro1 = _prod1m(comp["ro_err"])
    ro2 = _prod1m(comp["ro_err"], 2.0)
    t1_term = math.exp(-sum(t / t1 for t, t1 in zip(comp["idle"], comp["t1"])))
    t2_term = math.exp(-sum(t / t2 for t, t2 in zip(comp["idle"], comp["t2"])))
    p_pred = g_pop * ro1 * 0.5 * (1.0 + t1_term)
    c_pred = g_par * ro2 * t2_term
    return {"P_pred": float(p_pred), "C_pred": float(c_pred), "F_pred": float((p_pred + c_pred) / 2.0),
            "F_M": float(g_pop * ro1 * t2_term)}


def model_all(entries, target, grid=GRID):
    """{n: components} from the transpiled GHZ POP and PAR_0 circuits."""
    pop = {e["n"]: e for e in entries if e["family"] == "GHZ" and e["kind"] == "POP"}
    par0 = {e["n"]: e for e in entries if e["family"] == "GHZ" and e["kind"] == "PAR" and e["j"] == 0}
    return {n: model_components(pop[n]["circuit"], par0[n]["circuit"], target, pop[n]["S"]) for n in grid}


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


def coherence_re_from_parities(parities, n):
    """Sensitivity I-1: the same sum with Re (nominal phase) instead of |.|; can be negative."""
    par = np.asarray(parities, dtype=float)
    ph = np.exp(1j * n * phis(n))
    return (2.0 / (2 * n + 2)) * np.real(par @ ph)


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
    return {"P": P, "parity": par, "C": C, "C_re": float(coherence_re_from_parities(par, n)), "F": (P + C) / 2.0}


def bootstrap_group(counts, n, family, B, rng):
    """Joint multinomial bootstrap for one (family, n): every circuit's counts are resampled (B draws each, same replicate
    index across the circuits of this group). Categories are reduced to what the estimators read: POP -> (0^n, 1^n, other),
    PAR -> (even, odd); a multinomial over the reduced categories has exactly the distribution of the full-outcome
    multinomial after aggregation. Returns {"P": (B,), "C": (B,), "F": (B,), "C_re": (B,)}."""
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
    return {"P": P, "C": C, "F": (P + C) / 2.0, "C_re": coherence_re_from_parities(par, n)}


def ci95(x, axis=0):
    return np.percentile(x, 2.5, axis=axis), np.percentile(x, 97.5, axis=axis)


def analyze_counts(counts, grid=GRID, mix_ns=MIX_NS, B=BOOT_B, seed=BOOT_SEED):
    """All estimators of PREREG section 2 (+ the Re sensitivity of section 6).

    One np.random.default_rng(seed); draws are made in the order: GHZ n ascending (POP, PAR_0..), then MIX n ascending.
    Returns arrays over ``grid``: P, C, C_re, F_hat and the bootstrap replicates P_boot, C_boot, F_boot, C_re_boot (B, len(grid))
    with 95% percentile intervals (*_lo, *_hi), and per-n MIX dicts.
    """
    rng = np.random.default_rng(seed)
    cols = {"P": [], "C": [], "C_re": [], "F": []}
    boots = {"P": [], "C": [], "F": [], "C_re": []}
    for n in grid:
        est = point_estimates(counts, n, "GHZ")
        bt = bootstrap_group(counts, n, "GHZ", B, rng)
        for k in cols:
            cols[k].append(est[k])
        for k in boots:
            boots[k].append(bt[k])
    out = {"n": np.array(grid), "P": np.array(cols["P"]), "C": np.array(cols["C"]), "C_re": np.array(cols["C_re"]),
           "F_hat": np.array(cols["F"]), "mix": {}}
    for k, name in (("P", "P_boot"), ("C", "C_boot"), ("F", "F_boot"), ("C_re", "C_re_boot")):
        out[name] = np.stack(boots[k], axis=1)
    for k, pre in (("P", "P"), ("C", "C"), ("F", "F"), ("C_re", "C_re")):
        lo, hi = ci95(out[pre + "_boot"])
        out[pre + "_lo"], out[pre + "_hi"] = lo, hi
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
